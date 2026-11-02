# -*- coding: utf-8 -*-
"""Son benchmark (2026-11-02): her turden esit sayida soru, ayni ayarla, DeepInfra Batch API.

Tur = kategori; solver `orta` ve `kod` ayri tur. Tur basina N soru (varsayilan 100), tur icindeki alt
gruplar (alt_tip, ders, veritabani, gorev) sirayla dolasilarak secilir; sabit tohum. Secim
`benchmark/alt_kume.jsonl` dosyasina yazilir; baskalari ayni alt kumeyle olcebilir.

KANONIK ALT KUME DOSYANIN KENDISIDIR, `sec` degil: tum turler tek rastgele akisi alfabetik sirayla paylasir; bir
turun havuzu degisince (2026-11-02 Cognipeer duzeltmesi, 716 satir silindi) alfabede ondan sonraki turlerin secimi
de kayar. Bu yuzden dosya `sec`le yeniden uretilmedi: Cognipeer'de silinen 2 soru ayni gorevden 2 soruyla
degistirildi (tohum 20261103) ve Cognipeer `--set sql_cognipeer` ile yeniden olculdu.

Ayar: paketteki istem(), temperature 0, tek deneme. 24B ve düşünmesiz Flash 8.000 token; düşünen Flash
(`flash_dusunen`) onceki olcumlerdeki "guclu model" ayariyla: reasoning_effort=high, 32.000 token. V4-Flash'ta
düşünme varsayilan olarak KAPALI (`flash` = düşünmesiz). MEB setlerinde kural eslesmezse
LLM hakem (JUDGE_PROMPT, deepseek-ai/DeepSeek-V4-Flash-0731) ikinci bir batch ile sorulur.

Kullanim (API anahtari DEEPINFRA_API_KEY ortam degiskeninde):
    python3 araclar/benchmark.py sec
    python3 araclar/benchmark.py gonder --model 24b --dir <calisma klasoru>
    python3 araclar/benchmark.py al     --model 24b --dir <calisma klasoru>   # cevaplari puanlar, hakem batch'ini gonderir
    python3 araclar/benchmark.py hakem  --model 24b --dir <calisma klasoru>   # hakem sonucunu alir, son puanlar
    python3 araclar/benchmark.py rapor  --dir <calisma klasoru>
    # tek seti yeniden olcmek (sonuc dosyasindaki o setin satirlari degistirilir; MEB setleri icin degil):
    python3 araclar/benchmark.py gonder --model 24b --dir <klasor> --set sql_cognipeer   # sonra al --set ...
"""
import argparse
import gzip
import json
import os
import random
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import requests

PAKET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PAKET))
from puanlama import istem, orijinal, puanla  # noqa: E402
from puanlama.meb import JUDGE_PROMPT, answers_match, cevap_al  # noqa: E402

API = "https://api.deepinfra.com/v1/openai"
MODELLER = {"24b": "mistralai/Mistral-Small-3.2-24B-Instruct-2506", "flash": "deepseek-ai/DeepSeek-V4-Flash-0731",
            "flash_dusunen": "deepseek-ai/DeepSeek-V4-Flash-0731"}
EK_AYAR = {"flash_dusunen": {"reasoning_effort": "high", "max_tokens": 32000}}
HAKEM = MODELLER["flash"]
TOHUM = 20261102
ALT_KUME = PAKET / "benchmark" / "alt_kume.jsonl"
MEB_SETLER = {"meb_tek_ders", "meb_capraz"}


def h():
    return {"Authorization": f"Bearer {os.environ['DEEPINFRA_API_KEY']}"}


def satirlar():
    for p in sorted((PAKET / "veri").glob("*.jsonl.gz")):
        for l in gzip.open(p, "rt", encoding="utf-8"):
            yield p.name[: -len(".jsonl.gz")], json.loads(l)


def tur_ve_grup(s, r):
    o = orijinal(r)
    if r["kategori"] == "solver":
        return f"solver_{o['set']}", o.get("aile")
    grup = {"sql_cognipeer": lambda: o.get("gorev"), "sql_belediye": lambda: o.get("db"),
            "sql_istatistik": lambda: o.get("db"), "sql_turspider": lambda: o.get("db"),
            "meb_tek_ders": lambda: o.get("ders"),
            "meb_capraz": lambda: "+".join(sorted(p["ders"] for p in o.get("parcalar", [])))}.get(s)
    return r["kategori"], (grup() if grup else r.get("alt_tip"))


def sec(a):
    gruplar = defaultdict(lambda: defaultdict(list))
    for s, r in satirlar():
        t, g = tur_ve_grup(s, r)
        gruplar[t][str(g)].append((s, r["id"]))
    rnd = random.Random(TOHUM)
    out = []
    for t in sorted(gruplar):
        kova = [rnd.sample(v, len(v)) for _, v in sorted(gruplar[t].items())]
        rnd.shuffle(kova)
        secilen, i = [], 0
        while len(secilen) < a.n and any(kova):  # gruplar sirayla: kucuk grup da temsil edilir
            if kova[i % len(kova)]:
                secilen.append(kova[i % len(kova)].pop())
            i += 1
        out += [{"tur": t, "set": s, "id": i_} for s, i_ in secilen]
    ALT_KUME.parent.mkdir(exist_ok=True)
    ALT_KUME.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8")
    print(len(out), "soru,", len(gruplar), "tur ->", ALT_KUME)
    print(Counter(x["tur"] for x in out))


def alt_kume(set_=None):
    secim = {(x["set"], x["id"]): x["tur"] for x in map(json.loads, open(ALT_KUME, encoding="utf-8"))
             if set_ in (None, x["set"])}
    return [(secim[(s, r["id"])], s, r) for s, r in satirlar() if (s, r["id"]) in secim]


def _ad(a):
    return f"{a.model}_{a.set}" if a.set else a.model


def _batch_gonder(D, ad, istekler):
    p = D / f"girdi_{ad}.jsonl"
    p.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in istekler), encoding="utf-8")
    r = requests.post(f"{API}/files", headers=h(), files={"file": (p.name, open(p, "rb"), "application/jsonl")},
                      data={"purpose": "batch"}, timeout=600)
    r.raise_for_status()
    r = requests.post(f"{API}/batches", headers=h(), json={"input_file_id": r.json()["id"],
                                                           "endpoint": "/v1/chat/completions",
                                                           "completion_window": "24h"}, timeout=120)
    r.raise_for_status()
    (D / f"batch_{ad}.json").write_text(json.dumps(r.json(), indent=1))
    print(ad, len(istekler), "istek:", r.json()["id"], r.json()["status"])


def _batch_al(D, ad):
    """Bitmediyse None; bittiyse {custom_id: (icerik, usage)}."""
    bj = json.loads((D / f"batch_{ad}.json").read_text())
    r = requests.get(f"{API}/batches/{bj['id']}", headers=h(), timeout=60)
    r.raise_for_status()
    d = r.json()
    (D / f"batch_{ad}.json").write_text(json.dumps(d, indent=1))
    print(ad, d["status"], d.get("request_counts"))
    if d["status"] != "completed":
        return None
    cikti = []
    for alan in ("output_file_id", "error_file_id"):
        if d.get(alan):
            r = requests.get(f"{API}/files/{d[alan]}/content", headers=h(), timeout=600)
            r.raise_for_status()
            cikti += [json.loads(l) for l in r.text.splitlines() if l.strip()]
    (D / f"cikti_{ad}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in cikti),
                                         encoding="utf-8")
    out = {}
    for x in cikti:
        body = ((x.get("response") or {}).get("body")) or {}
        ch = (body.get("choices") or [{}])[0]
        out[x["custom_id"]] = ((ch.get("message") or {}).get("content"), body.get("usage") or {},
                               ch.get("finish_reason"))
    return out


def istek(cid, model, metin, max_tokens=8000, ek=None):
    return {"custom_id": cid, "method": "POST", "url": "/v1/chat/completions",
            "body": {"model": model, "max_tokens": max_tokens, "temperature": 0,
                     "messages": [{"role": "user", "content": metin}], **(ek or {})}}


def gonder(a, D):
    if a.set in MEB_SETLER:
        sys.exit("--set MEB setleri icin desteklenmiyor (hakem adimi tum alt kumeyle calisir)")
    _batch_gonder(D, _ad(a), [istek(f"{s}#{r['id']}", MODELLER[a.model], istem(r), ek=EK_AYAR.get(a.model))
                              for _, s, r in alt_kume(a.set)])


def _puanla_is(arg):
    s, r, metin = arg
    try:
        return puanla(r, metin)
    except Exception as e:  # puanlayici hatasi yanlis sayilir, ayrica sayilir
        return f"HATA {type(e).__name__}: {e}"[:200]


def al(a, D):
    cev = _batch_al(D, _ad(a))
    if cev is None:
        return print("henüz bitmedi")
    ak = alt_kume(a.set)
    isler = [(s, r, (cev.get(f"{s}#{r['id']}") or (None,))[0]) for _, s, r in ak]
    with ProcessPoolExecutor(a.isci) as ex:
        sonuc = list(ex.map(_puanla_is, isler, chunksize=4))
    out, hakem_istek = [], []
    for (t, s, r), (_, _, metin), dogru in zip(ak, isler, sonuc):
        icerik, usage, bitis = cev.get(f"{s}#{r['id']}") or (None, {}, None)
        x = {"tur": t, "set": s, "id": r["id"], "dogru": dogru is True, "puanlayici_hatasi": isinstance(dogru, str),
             "zaman_asimi": dogru is None, "bos": not (metin or "").strip(), "bitis": bitis,
             "maliyet": usage.get("estimated_cost") or 0, "cikti_token": usage.get("completion_tokens"),
             "cevap": metin}
        if s in MEB_SETLER and dogru is False and cevap_al(metin):
            x["hakem_bekliyor"] = True
            hakem_istek.append(istek(f"{s}#{r['id']}", HAKEM, JUDGE_PROMPT.format(
                soru=r["soru"], cevap1=r["cevap"], cevap2=cevap_al(metin)), max_tokens=1500))
        out.append(x)
    if a.set:  # yalniz bu setin satirlari degisir
        eski = [json.loads(l) for l in open(D / f"sonuc_{a.model}.jsonl", encoding="utf-8")]
        out = [x for x in eski if x["set"] != a.set] + out
    (D / f"sonuc_{a.model}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out),
                                              encoding="utf-8")
    print(a.model, "dogru", sum(x["dogru"] for x in out), "/", len(out), "hakem bekleyen", len(hakem_istek))
    if hakem_istek:
        _batch_gonder(D, f"hakem_{a.model}", hakem_istek)


def hakem(a, D):
    cev = _batch_al(D, f"hakem_{a.model}")
    if cev is None:
        return print("henüz bitmedi")
    p = D / f"sonuc_{a.model}.jsonl"
    out = [json.loads(l) for l in open(p, encoding="utf-8")]
    import re
    kabul = 0
    for x in out:
        if not x.pop("hakem_bekliyor", False):
            continue
        icerik, usage, _ = cev.get(f"{x['set']}#{x['id']}") or (None, {}, None)
        x["hakem_maliyet"] = usage.get("estimated_cost") or 0
        m = re.search(r"\{.*\}", icerik or "", re.S)
        try:
            x["hakem"] = bool(json.loads(m.group(0)).get("ayni_mi")) if m else False
        except json.JSONDecodeError:
            x["hakem"] = False
        x["dogru"] = x["hakem"]
        kabul += x["hakem"]
    p.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8")
    print(a.model, "hakem kabul", kabul, "| son dogru", sum(x["dogru"] for x in out), "/", len(out))


def rapor(a, D):
    sonuc = {m: [json.loads(l) for l in open(D / f"sonuc_{m}.jsonl", encoding="utf-8")]
             for m in MODELLER if (D / f"sonuc_{m}.jsonl").exists()}
    tablo = {}
    for m, xs in sonuc.items():
        tur, set_ = defaultdict(list), defaultdict(list)
        for x in xs:
            tur[x["tur"]].append(x["dogru"])
            set_[x["set"]].append(x["dogru"])
        oran = lambda d: {k: round(100 * sum(v) / len(v), 1) for k, v in sorted(d.items())}  # noqa: E731
        tur_o, set_o = oran(tur), oran(set_)
        tablo[m] = {"model": MODELLER[m], "soru": len(xs), "tur": tur_o, "set": set_o,
                    "makro_tur": round(sum(tur_o.values()) / len(tur_o), 1),
                    "makro_set": round(sum(set_o.values()) / len(set_o), 1),
                    "mikro": round(100 * sum(x["dogru"] for x in xs) / len(xs), 1),
                    "bos": sum(x["bos"] for x in xs), "kesilen": sum(x["bitis"] == "length" for x in xs),
                    "puanlayici_hatasi": sum(x["puanlayici_hatasi"] for x in xs),
                    "zaman_asimi": sum(x["zaman_asimi"] for x in xs),
                    "maliyet_usd": round(sum(x["maliyet"] + x.get("hakem_maliyet", 0) for x in xs), 4)}
    (PAKET / "benchmark" / "sonuclar.json").write_text(json.dumps(tablo, ensure_ascii=False, indent=1) + "\n",
                                                       encoding="utf-8")
    ms = list(tablo)
    print(f"{'tur':28}" + "".join(f"{m:>8}" for m in ms))
    for t in tablo[ms[0]]["tur"]:
        print(f"{t:28}" + "".join(f"{tablo[m]['tur'].get(t, 0):8.1f}" for m in ms))
    for k in ("makro_tur", "makro_set", "mikro", "bos", "kesilen", "puanlayici_hatasi", "zaman_asimi", "maliyet_usd"):
        print(f"{k:28}" + "".join(f"{tablo[m][k]:>8}" for m in ms))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("komut", choices=["sec", "gonder", "al", "hakem", "rapor"])
    ap.add_argument("--model", choices=list(MODELLER))
    ap.add_argument("--dir")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--set", help="gonder/al: yalniz bu set (sonuc dosyasinda o setin satirlari degisir)")
    ap.add_argument("--isci", type=int, default=8)
    a = ap.parse_args()
    if a.komut == "sec":
        return sec(a)
    D = Path(a.dir).resolve()
    D.mkdir(parents=True, exist_ok=True)
    {"gonder": gonder, "al": al, "hakem": hakem, "rapor": rapor}[a.komut](a, D)


if __name__ == "__main__":
    main()
