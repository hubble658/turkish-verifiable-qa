"""Run every task in a directory and report aggregate statistics.

    # saglik kontrolu: her task'in referansi hala geciyor mu (model gerekmez)
    python -m verifiable_dataset.terminal.sweep --reference

    # zorluk kalibrasyonu: her task'a N rollout
    python -m verifiable_dataset.terminal.sweep --model Qwen/Qwen3.5-9B \
        --base-url http://localhost:8000/v1 --rollouts 8 --out data/sweep.jsonl

Kalibrasyon modunda her task bir banda yerlestirilir. GRPO'da bir grubun
butun rollout'lari ayni reward'i alirsa advantage sifir olur, yani 0/N ve
N/N task'lar egitimde ayni sekilde olu agirliktir -- ikisi de isaretlenir.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from verifiable_dataset.terminal.llm import make_client, preflight, resolve_model
from verifiable_dataset.terminal.runner import Episode, run_model, run_reference
from verifiable_dataset.terminal.sandbox import sandbox_hazirla
from verifiable_dataset.terminal.task import Task

# Ogrenme sinyali bu bandin disinda kaybolur.
BAND_LOW, BAND_HIGH = 0.125, 0.875


def discover(envs_dir: Path) -> list[Path]:
    """Find task directories, supporting flat or nested (shell/code) structures."""
    tasks = [
        p.parent for p in envs_dir.glob("*/task.yaml")
        if not p.parent.name.startswith("_")
    ]
    tasks += [
        p.parent for p in envs_dir.glob("*/*/task.yaml")
        if not p.parent.name.startswith("_") and not p.parent.parent.name.startswith("_")
    ]
    return sorted(set(tasks))


def band_of(pass_rate: float, rollouts: int) -> str:
    if rollouts == 1:
        return "-"
    if pass_rate <= BAND_LOW:
        return "OLU-zor"
    if pass_rate >= BAND_HIGH:
        return "OLU-kolay"
    return "BANT"


def summarize(task_id: str, episodes: list[Episode], rollouts: int) -> dict:
    solved = sum(1 for e in episodes if e.solved)
    # Ikili odulun ortalamasi pass rate ile ayni sey oldugu icin ayrica
    # tutulmuyor; kismi oran ise teshis degeri tasiyor: kimsenin
    # cozemedigi ama herkesin yaklastigi bir task, kimsenin hicbir yere
    # varamadigindan cok farkli bir seydir.
    partials = [e.partial for e in episodes]
    turns = [e.turns for e in episodes if e.turns]
    errors = [e.error for e in episodes if e.error]
    pass_rate = solved / len(episodes) if episodes else 0.0
    return {
        "task_id": task_id,
        "rollouts": len(episodes),
        "solved": solved,
        "pass_rate": pass_rate,
        "mean_partial": statistics.mean(partials) if partials else 0.0,
        "mean_turns": statistics.mean(turns) if turns else 0.0,
        "band": band_of(pass_rate, rollouts),
        "errors": errors,
    }


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sandbox", choices=["docker", "singularity", "yerel", "bwrap"],
                        default="docker",
                        help="singularity = HPC (MN5); yerel = Docker'siz "
                             "(Colab), izolasyon yok; bwrap = Docker'siz, ag ve ev dizini kapali")
    parser.add_argument("--envs", default="envs", help="task dizinlerini iceren klasor")
    parser.add_argument("--split", choices=["all", "train", "test"], default="all",
                        help="split.json uzerinden train veya test (holdout) gorevlerini filtrele")
    parser.add_argument("--reference", action="store_true",
                        help="model yerine referans cozumleri calistir (saglik kontrolu)")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key", default="",
                        help="bos birakilirsa .env okunur")
    parser.add_argument("--protocol", choices=["auto", "native", "text"], default="auto")
    parser.add_argument("--rollouts", type=int, default=1)
    parser.add_argument("--only", default="", help="sadece adinda bu gecen task'lari calistir")
    parser.add_argument("--out", default="", help="episode kayitlarini bu JSONL'e yaz")
    parser.add_argument("--istek-araligi", type=float, default=0.0,
                        help="iki API istegi arasinda en az bu kadar saniye bekle")
    parser.add_argument("--butce", type=float, default=0.0,
                        help="harcama bu USD degerine ulasinca yeni gorev baslatma (0: sinir yok)")
    parser.add_argument("--atla", default="", help="bu sweep JSONL'indeki gorevleri atla (onceki kosu)")
    parser.add_argument("--ornek", type=int, default=0,
                        help="aile (shell/code) oranini koruyarak rastgele N gorev sec")
    parser.add_argument("--tohum", type=int, default=20261104)
    parser.add_argument("--paralel", type=int, default=1, help="ayni anda kosan gorev sayisi")
    parser.add_argument("--reasoning-effort", default="",
                        help="her istege eklenir; bos: modelin varsayilani")
    parser.add_argument("--sicaklik", type=float, default=None, help="VDS_TEMPERATURE yerine")
    parser.add_argument("--max-tokens", type=int, default=None, help="VDS_MAX_TOKENS yerine")
    parser.add_argument("--top-p", type=float, default=None, help="her istege eklenir; bos: modelin varsayilani")
    parser.add_argument("--ayrintili", action="store_true",
                        help="her turu, modelin yorumunu ve komut ciktisini bas")
    args = parser.parse_args()

    if args.sicaklik is not None:
        os.environ["VDS_TEMPERATURE"] = str(args.sicaklik)
    if args.max_tokens is not None:
        os.environ["VDS_MAX_TOKENS"] = str(args.max_tokens)
    if args.ayrintili and args.paralel > 1:
        print("--ayrintili ile --paralel birlikte okunamaz cikti verir; --paralel 1 kullan")
        return 2

    ok, info = sandbox_hazirla(args.sandbox)
    if not ok:
        print(f"{args.sandbox} sandbox kullanilamiyor: {info}")
        return 1

    task_dirs = discover(Path(args.envs))
    if args.split in ("train", "test"):
        split_path = Path("data/split.json")
        if split_path.exists():
            with open(split_path, "r", encoding="utf-8") as f:
                s_data = json.load(f)
            split_set = {Path(item["dir"]).resolve() for item in s_data.get(args.split, [])}
            task_dirs = [d for d in task_dirs if d.resolve() in split_set]
            print(f"Split filtresi uygulandi ({args.split}): {len(task_dirs)} gorev secildi.")
        else:
            print(f"Uyari: {split_path} bulunamadi, butun gorevler taranacak.")
    if args.only:
        task_dirs = [d for d in task_dirs if args.only in d.name]
    if args.atla:
        with open(args.atla, encoding="utf-8") as f:
            atlanan = {json.loads(l)["summary"]["task_id"] for l in f if '"summary"' in l[:12]}
        task_dirs = [d for d in task_dirs if d.name not in atlanan]
        print(f"Atlandi: {len(atlanan)}; kalan {len(task_dirs)} gorev")
    if args.ornek and args.ornek < len(task_dirs):
        rnd = random.Random(args.tohum)
        aileler = defaultdict(list)
        for d in task_dirs:
            aileler[d.parent.name].append(d)
        secilen = []
        for ad, ds in sorted(aileler.items()):
            secilen += rnd.sample(ds, round(args.ornek * len(ds) / len(task_dirs)))
        task_dirs = sorted(secilen)
        print(f"Orneklem: {len(task_dirs)} gorev")
    if not task_dirs:
        print(f"{args.envs} altinda task bulunamadi")
        return 1

    client = None
    if not args.reference:
        args.model = resolve_model(args.model)
        if not args.model:
            print("--model verilmedi ve .env'de OPENAI_MODEL_NAME yok")
            return 2
        ok_uc, bilgi_uc = preflight(args.base_url, args.api_key, args.model)
        if not ok_uc:
            print(f"UC KONTROLU BASARISIZ: {bilgi_uc}")
            return 2
        print(f"uc dogrulandi: {bilgi_uc}")
        client = make_client(args.base_url, args.api_key, args.istek_araligi,
                             reasoning_effort=args.reasoning_effort, top_p=args.top_p)

    mode = "referans" if args.reference else f"{args.model} x{args.rollouts}"
    print(f"{len(task_dirs)} task | mod: {mode} | {args.sandbox} {info}\n")

    harcanan = [0.0]
    kilit = threading.Lock()

    def tek_gorev(arg):
        sira, task_dir = arg
        if args.butce:
            with kilit:
                if harcanan[0] >= args.butce:
                    return None, []
        try:
            task = Task.load(task_dir)
        except Exception as e:  # noqa: BLE001 - a broken yaml must not stop the sweep
            print(f"{task_dir.name:32} YUKLENEMEDI  {type(e).__name__}: {str(e)[:80]}")
            return ({"task_id": task_dir.name, "rollouts": 0, "solved": 0,
                     "pass_rate": 0.0, "mean_partial": 0.0, "mean_turns": 0.0,
                     "band": "BOZUK", "errors": [str(e)[:200]]}, [])

        n = 1 if args.reference else args.rollouts
        episodes: list[Episode] = []
        if args.ayrintili:
            cizgi = "=" * 78
            print(f"\n{cizgi}")
            print(f"[{sira}/{len(task_dirs)}] {task.id}   "
                  f"max_turns={task.max_turns}  check={len(task.checks)}")
            print(cizgi)
            print(f"GOREV: {' '.join(task.prompt.split())[:400]}\n")
        for r in range(1, n + 1):
            if args.ayrintili:
                print(f"----- rollout {r}/{n} -----")
            try:
                ep = (run_reference(task, verbose=args.ayrintili) if args.reference
                      else run_model(task, client, args.model, args.protocol,
                                     verbose=args.ayrintili))
            except Exception as e:  # noqa: BLE001 - one bad rollout must not stop the sweep
                ep = Episode(task_id=task.id, solved=False, reward=0.0, turns=0,
                             grade={"passed": 0, "total": 0, "checks": []},
                             error=f"{type(e).__name__}: {e}")
            if args.ayrintili:
                durum = 'COZDU' if ep.solved else 'COZEMEDI'
                print(f"  => {durum}  check {ep.grade.get('passed', 0)}/"
                     f"{ep.grade.get('total', 0)}  kismi={ep.partial:.2f}  tur={ep.turns}")
                for c in ep.grade.get('checks', []):
                    if not c['ok']:
                        print(f"     x {c['name']}: {c['detail'][:150]}")
                if ep.error:
                    print(f"     ! {ep.error[:200]}")
                print()
            episodes.append(ep)
            with kilit:
                harcanan[0] += ep.usage.get("estimated_cost", 0)

        row = summarize(task.id, episodes, n)
        mark = "OK  " if row["pass_rate"] == 1.0 else ("FAIL" if row["pass_rate"] == 0 else "kismi")
        band = "" if args.reference else f"  [{row['band']}]"
        hatalar = "".join(f"\n{'':34}! {err[:100]}" for err in dict.fromkeys(row["errors"]))
        print(f"{task.id:32} {mark} {row['solved']}/{row['rollouts']}  "
              f"kismi={row['mean_partial']:.2f}  tur={row['mean_turns']:.1f}{band}{hatalar}", flush=True)
        return row, episodes

    rows: list[dict] = []
    all_episodes: list[Episode] = []
    calisan = []
    with ThreadPoolExecutor(max_workers=max(1, args.paralel)) as havuz:
        for d, (row, episodes) in zip(task_dirs, havuz.map(tek_gorev, enumerate(task_dirs, start=1))):
            if row is None:
                continue
            calisan.append(d)
            rows.append(row)
            all_episodes.extend(episodes)
    if len(calisan) < len(task_dirs):
        print(f"\nBUTCE SINIRI: {len(task_dirs) - len(calisan)} gorev baslatilmadi "
              f"(harcanan ${harcanan[0]:.4f})")
    task_dirs = calisan

    def kaydet():
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps({"summary": row}, ensure_ascii=False) + "\n")
                for ep in all_episodes:
                    f.write(json.dumps({"episode": ep.to_dict()}, ensure_ascii=False) + "\n")
            print(f"kayitlar -> {out}")

    # -- ozet ---------------------------------------------------------
    print()
    if args.reference:
        gecen = sum(1 for r in rows if r["pass_rate"] == 1.0)
        print(f"SAGLIK: {gecen}/{len(rows)} task referansinda geciyor")
        bozuk = [r["task_id"] for r in rows if r["pass_rate"] < 1.0]
        if bozuk:
            print(f"Referansi gecmeyen task'lar dataset'e giremez: {', '.join(bozuk)}")
        kaydet()
        return 0 if not bozuk else 1

    partials = [r["mean_partial"] for r in rows]
    cozulen = sum(1 for r in rows if r["pass_rate"] == 1.0)
    ortalama_pass = statistics.mean([r["pass_rate"] for r in rows])
    print(f"Cozulen         : {cozulen}/{len(rows)}")
    print(f"Ortalama reward : {ortalama_pass:.3f}  (ikili odul)")
    print(f"Ortalama kismi  : {statistics.mean(partials):.3f}  (teshis)")
    print(f"Ortalama tur    : {statistics.mean([r['mean_turns'] for r in rows]):.1f}")
    girdi = sum(e.usage.get("prompt_tokens", 0) for e in all_episodes)
    cikti = sum(e.usage.get("completion_tokens", 0) for e in all_episodes)
    print(f"Token           : girdi {girdi}  cikti {cikti}  "
          f"maliyet ${sum(e.usage.get('estimated_cost', 0) for e in all_episodes):.4f}")
    print(f"Sifir komutlu   : {sum(1 for e in all_episodes if not e.commands)}/{len(all_episodes)}  (kanarya)")
    print(f"Model hatali    : {sum(1 for e in all_episodes if e.error)}/{len(all_episodes)}")
    aile = defaultdict(list)
    for d, r in zip(task_dirs, rows):
        aile[d.parent.name].append(r["pass_rate"])
        aile[d.parent.name + "/" + d.name.split("-", 3)[-1]].append(r["pass_rate"])
    for ad in sorted(aile):
        print(f"  {ad:34} {len(aile[ad]):4}  %{statistics.mean(aile[ad]) * 100:.1f}")

    if args.rollouts < 4:
        # Tek rollout pass rate hakkinda neredeyse hicbir sey soylemez;
        # bant atamasi yapmak yaniltici olur.
        print(f"\nZorluk bandi olculmedi: kalibrasyon icin --rollouts 4 veya "
              f"daha fazlasi gerekir (su an {args.rollouts}).")
    else:
        for band in ("BANT", "OLU-kolay", "OLU-zor", "BOZUK"):
            ids = [r["task_id"] for r in rows if r["band"] == band]
            if ids:
                print(f"{band:10} {len(ids):3}  {', '.join(ids)}")

        kullanilir = sum(1 for r in rows if r["band"] == "BANT")
        print(f"\nEgitimde ise yarar: {kullanilir}/{len(rows)} "
              f"({kullanilir / len(rows) * 100:.0f}%)")

    kaydet()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
