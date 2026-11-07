# -*- coding: utf-8 -*-
"""Test bolumunun tamami icin model olcumu (2026-11-04). 2 Kasim alt kumesine ve sonuclarina dokunmaz.

Kapsam: test bolumu; ajan_terminal ayri (ajan_tam_test.sh, cok turlu).
`neden: attach` 109 satir kosulur ama skora girmez.
Ayar: paketteki istem(), temperature 0, tek deneme (benchmark.py ile ayni).

Akis (hazirla agsizdir; para harcayan komutlar --onay ister. API anahtari DEEPINFRA_API_KEY ortam degiskeninde):
    python3 araclar/tam_test.py hazirla --dir <klasor>             # istek dosyalari + maliyet tahmini
    python3 araclar/tam_test.py pilot   --model qwen --dir <klasor> --onay    # set basina 2 soru, anlik; ayar kontrolu
    python3 araclar/tam_test.py gonder  --model 24b --dir <klasor> --onay     # DeepInfra Batch
    python3 araclar/tam_test.py kos     --model cosmos --dir <klasor> --base-url http://localhost:8000/v1 --onay   # vLLM
    python3 araclar/tam_test.py al      --model 24b --dir <klasor>   # cevaplari puanlar, hakem isteklerini yazar
    python3 araclar/tam_test.py hakem-gonder --model 24b --dir <klasor> --onay   # sonra hakem-al
    python3 araclar/tam_test.py rapor   --dir <klasor>
"""
import argparse
import gzip
import json
import os
import re
import sys
import threading
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark as bm  # noqa: E402
from puanlama import istem, orijinal  # noqa: E402
from puanlama.meb import JUDGE_PROMPT, cevap_al  # noqa: E402

PAKET = bm.PAKET
TEST_KUMESI = PAKET / "benchmark" / "test_kumesi.jsonl"
SONUC = PAKET / "benchmark" / "sonuclar_tam_test.json"
DISARIDA = {"ajan_terminal"}
MODELLER = {"qwen": "Qwen/Qwen3.5-9B", "cosmos": "ytu-ce-cosmos/Turkish-Gemma-9b-v0.1", "24b": bm.MODELLER["24b"],
            "oss": "openai/gpt-oss-120b"}  # V4-Flash uretim ve suzgecte kullanildigi icin buyuk model ekseninden cikti (5 Kasim, kullanici karari)
MAX_TOKEN_VARSAYILAN = 16000  # 2 Kasim: 8.000'de 24B %4, Flash %2 kesildi
MAX_TOKEN = {"oss": 64000}  # 2 Kasim: dusunen Flash 32.000'de solver'in %20'si kesildi, hepsi yanlis sayildi
EK_AYAR = {"qwen": {"reasoning_effort": "none"}, "oss": {"reasoning_effort": "high"}}
FIYAT = {"qwen": (0.10, 0.15), "24b": (0.075, 0.20), "oss": (0.037, 0.17)}  # USD / M token
CIKTI_TAHMIN = {"qwen": 650, "24b": 650, "oss": 4000}  # 2 Kasim ham kayitlari, soru basina (oss: dusunen Flash vekil)
KARAKTER_TOKEN = 2.045  # 2 Kasim ham kayitlarindan olculen karakter/token
HAKEM = bm.HAKEM
COSMOS_BAGLAM = 8192
COSMOS_PAY = 1.15  # karakterden token tahmini kesin degil, baglami asmamak icin pay
COSMOS_EN_AZ_CIKTI = 512


def baslik(s, r):
    if s in ("izgara_bulmaca", "satranc", "solver", "karakter_islemleri"):
        return f"{s}/{r['alt_tip']}"
    if s in ("hesaplama", "bulmaca"):
        return r["kategori"]
    if s == "regex":
        return "regex"
    return s


def test_satirlari():
    secim = {(t["set"], t["id"]): t for t in map(json.loads, open(TEST_KUMESI, encoding="utf-8"))}
    for p in sorted((PAKET / "veri").glob("*.jsonl.gz")):
        s = p.name[: -len(".jsonl.gz")]
        if s in DISARIDA:
            continue
        for l in gzip.open(p, "rt", encoding="utf-8"):
            r = json.loads(l)
            t = secim.get((s, r["id"]))
            if t:
                yield s, r, t["neden"] != "attach"


def istek_olustur(m, s, r):
    """(istek, atlandi_mi). Cosmos baglami 8.192 token: sigmayan istem gonderilmez, sonucta `sigmadi` olarak yazilir."""
    metin = istem(r)
    max_token = MAX_TOKEN.get(m, MAX_TOKEN_VARSAYILAN)
    if m == "cosmos":
        tahmin = int(len(metin) / KARAKTER_TOKEN * COSMOS_PAY)
        max_token = min(max_token, COSMOS_BAGLAM - tahmin)
        if max_token < COSMOS_EN_AZ_CIKTI:
            return None, True
    return bm.istek(f"{s}#{r['id']}", MODELLER[m], metin, max_tokens=max_token, ek=EK_AYAR.get(m)), False


def hazirla(a, D):
    satirlar = list(test_satirlari())
    girdi_token = sum(len(istem(r)) / KARAKTER_TOKEN for _, r, _ in satirlar)
    print(f"{len(satirlar)} satir; skorlanan {sum(x[2] for x in satirlar)}; yaklasik {girdi_token / 1e6:.2f} M girdi token")
    print(Counter(s for s, _, _ in satirlar))
    toplam = 0
    for m in MODELLER:
        yaz, atla = [], []
        for s, r, _ in satirlar:
            ist, atlandi = istek_olustur(m, s, r)
            (atla.append(f"{s}#{r['id']}") if atlandi else yaz.append(ist))
        (D / f"girdi_{m}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in yaz), encoding="utf-8")
        if atla:
            (D / f"sigmadi_{m}.json").write_text(json.dumps(atla, ensure_ascii=False, indent=0), encoding="utf-8")
        if m in FIYAT:
            g, c = FIYAT[m]
            usd = (girdi_token * g + len(yaz) * CIKTI_TAHMIN[m] * c) / 1e6
            toplam += usd
            print(f"{m:15} {len(yaz)} istek  ~${usd:.2f} (liste fiyati, ~{CIKTI_TAHMIN[m]} cikti token/soru)")
        else:
            print(f"{m:15} {len(yaz)} istek, sigmayan {len(atla)} (kiralik GPU, API maliyeti yok)")
    print(f"API toplami ~${toplam:.2f}; MEB hakemi, ajan ve GPU haric")


def _onay(a):
    if not a.onay:
        sys.exit("Bu komut para harcar: --onay olmadan calismaz.")


def _satir_oku(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def gonder(a, D):
    _onay(a)
    if a.model == "cosmos":
        sys.exit("Cosmos API'de yok: kos --base-url")
    bm._batch_gonder(D, a.model, _satir_oku(D / f"girdi_{a.model}.jsonl"))


def kos(a, D):
    """OpenAI uyumlu sunucuda (vLLM) girdi dosyasini kosar; yarim kalirsa kaldigi yerden devam eder."""
    _onay(a)
    cikti = D / f"cikti_{a.model}.jsonl"
    bitti = {x["custom_id"] for x in _satir_oku(cikti) if ((x.get("response") or {}).get("body") or {}).get("choices")} if cikti.exists() else set()
    isler = [x for x in _satir_oku(D / f"girdi_{a.model}.jsonl") if x["custom_id"] not in bitti]
    kilit = threading.Lock()
    print(len(bitti), "bitmis,", len(isler), "kalan")

    def calistir(x):
        try:
            r = requests.post(f"{a.base_url}/chat/completions", json=x["body"], timeout=a.sure)
            govde = r.json() if r.ok else {"error": r.text[:500]}
        except Exception as e:
            govde = {"error": f"{type(e).__name__}: {e}"[:500]}
        with kilit, open(cikti, "a", encoding="utf-8") as c:
            c.write(json.dumps({"custom_id": x["custom_id"], "response": {"body": govde}}, ensure_ascii=False) + "\n")

    with ThreadPoolExecutor(a.paralel) as ex:
        list(ex.map(calistir, isler))


def pilot(a, D):
    """Setlerden birkac soruyu anlik API ile dener; asil cikti dosyasina yazmaz. Duzensiz ayari (dusunme, bos cevap) erken gosterir."""
    _onay(a)
    secilen, say = [], Counter()
    for x in _satir_oku(D / f"girdi_{a.model}.jsonl"):
        s = x["custom_id"].split("#")[0]
        if say[s] < a.ornek:
            say[s] += 1
            secilen.append(x)
    url = a.base_url or bm.API
    bas = bm.h() if not a.base_url else {}
    kayit = []
    for x in secilen:
        r = requests.post(f"{url}/chat/completions", headers=bas, json=x["body"], timeout=a.sure)
        g = r.json() if r.ok else {"error": r.text[:500]}
        ch = (g.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        kayit.append({"custom_id": x["custom_id"], "response": {"body": g}})
        u = g.get("usage") or {}
        print(x["custom_id"][:44].ljust(46), ch.get("finish_reason"), "girdi", u.get("prompt_tokens"), "cikti", u.get("completion_tokens"),
              "dusunme" if msg.get("reasoning_content") or "<think>" in (msg.get("content") or "") else "-", g.get("error", "")[:90])
    (D / f"pilot_{a.model}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in kayit), encoding="utf-8")
    print("toplam USD", round(sum(((x["response"]["body"].get("usage") or {}).get("estimated_cost") or 0) for x in kayit), 5))


def cikti_coz(cikti):
    out = {}
    for x in cikti:  # kos tekrar denediyse son kayit gecerlidir
        body = ((x.get("response") or {}).get("body")) or {}
        ch = (body.get("choices") or [{}])[0]
        out[x["custom_id"]] = ((ch.get("message") or {}).get("content"), body.get("usage") or {}, ch.get("finish_reason"),
                               body.get("error"))
    return out


def batch_al(D, ad):
    """Cikti dosyasi varsa ag kullanmaz; yoksa DeepInfra'dan indirir."""
    p = D / f"cikti_{ad}.jsonl"
    if not p.exists() and bm._batch_al(D, ad) is None:
        return None
    return cikti_coz(_satir_oku(p))


def _regex_via(arg):
    """regex_yazma cevabinin hangi yolla puanlandigi (dfa | tests); iscide calisir, SIGALRM ana is parcaciginda olmali."""
    from puanlama._ek.regex import puanla_ayrinti
    r, metin = arg
    try:
        return puanla_ayrinti(r, metin).get("via")
    except Exception:  # noqa: BLE001  puanlayici hatasi _puanla_is'te sayilir
        return None


def al(a, D):
    cev = batch_al(D, a.model)
    if cev is None:
        return print("henüz bitmedi")
    satirlar = list(test_satirlari())
    sigmadi = set(json.loads((D / f"sigmadi_{a.model}.json").read_text())) if (D / f"sigmadi_{a.model}.json").exists() else set()
    bos = (None, {}, None, None)
    isler = [(s, r, cev.get(f"{s}#{r['id']}", bos)[0]) for s, r, _ in satirlar]
    with ProcessPoolExecutor(a.isci) as ex:
        sonuc = dict(zip(((s, r["id"]) for s, r, _ in isler), ex.map(bm._puanla_is, isler, chunksize=4)))
        rg = [(r, m) for s, r, m in isler if s == "regex" and r["kategori"] == "regex_yazma"]
        via = dict(zip((r["id"] for r, _ in rg), ex.map(_regex_via, rg, chunksize=4)))
    out, hakem_istek = [], []
    for s, r, skorda in satirlar:
        cid = f"{s}#{r['id']}"
        metin, usage, bitis, hata = cev.get(cid, bos)
        dogru = sonuc.get((s, r["id"]))
        x = {"baslik": baslik(s, r), "set": s, "id": r["id"], "skorda": skorda, "dogru": dogru is True,
             "puanlayici_hatasi": isinstance(dogru, str), "zaman_asimi": dogru is None,
             "bos": not (metin or "").strip(), "bitis": bitis, "sigmadi": cid in sigmadi, "istek_hatasi": str(hata)[:200] if hata else None,
             **({"via": via.get(r["id"])} if r["id"] in via else {}),
             "maliyet": usage.get("estimated_cost") or 0, "girdi_token": usage.get("prompt_tokens"),
             "cikti_token": usage.get("completion_tokens"), "cevap": metin}
        if s in bm.MEB_SETLER and dogru is False and cevap_al(metin):
            x["hakem_bekliyor"] = True
            hakem_istek.append(bm.istek(cid, HAKEM, JUDGE_PROMPT.format(soru=r["soru"], cevap1=r["cevap"], cevap2=cevap_al(metin)),
                                        max_tokens=1500))
        out.append(x)
    (D / f"sonuc_{a.model}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8")
    (D / f"girdi_hakem_{a.model}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in hakem_istek), encoding="utf-8")
    print(a.model, "dogru", sum(x["dogru"] for x in out), "/", len(out), "| hakem istegi", len(hakem_istek),
          "| istek hatasi", sum(bool(x["istek_hatasi"]) for x in out), "| sigmadi", sum(x["sigmadi"] for x in out))


def adim_gonder(a, D, ad):
    _onay(a)
    bm._batch_gonder(D, f"{ad}_{a.model}", _satir_oku(D / f"girdi_{ad}_{a.model}.jsonl"))


def hakem_al(a, D):
    cev = batch_al(D, f"hakem_{a.model}")
    if cev is None:
        return print("henüz bitmedi")
    p = D / f"sonuc_{a.model}.jsonl"
    out = _satir_oku(p)
    for x in out:
        if not x.pop("hakem_bekliyor", False):
            continue
        icerik, usage, _, _ = cev.get(f"{x['set']}#{x['id']}", (None, {}, None, None))
        x["hakem_maliyet"] = usage.get("estimated_cost") or 0
        m = re.search(r"\{.*\}", icerik or "", re.S)
        try:
            x["dogru"] = bool(json.loads(m.group(0)).get("ayni_mi")) if m else False
        except json.JSONDecodeError:
            x["dogru"] = False
    p.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8")
    print(a.model, "son dogru", sum(x["dogru"] for x in out), "/", len(out))



def rapor(a, D):
    tablo = {}
    sigmayan = {x for p in D.glob("sigmadi_*.json") for x in json.loads(p.read_text())}
    for m in MODELLER:
        p = D / f"sonuc_{m}.jsonl"
        if not p.exists():
            continue
        xs = [x for x in _satir_oku(p) if x["skorda"]]
        b = defaultdict(list)
        for x in xs:  # sigmayan soru yanlis sayilmaz, baslik kapsami ayrica yazilir; bkz. kapsam
            if x["sigmadi"]:
                continue
            b[x["baslik"]].append(100 * x["dogru"])
        oran = {k: round(sum(v) / len(v), 1) for k, v in sorted(b.items())}
        ortak = defaultdict(list)  # butun modellere sigan sorular: modeller arasi karsilastirma bununla
        for x in xs:
            if f"{x['set']}#{x['id']}" not in sigmayan:
                ortak[x["baslik"]].append(100 * x["dogru"])
        tablo[m] = {"model": MODELLER[m], "soru": len(xs), "baslik": oran, "makro_baslik": round(sum(oran.values()) / len(oran), 1),
                    "makro_ortak_sorular": round(sum(sum(v) / len(v) for v in ortak.values()) / len(ortak), 1),
                    "mikro": round(100 * sum(x["dogru"] for x in xs) / len(xs), 1),
                    "kapsam": {k: len(v) for k, v in sorted(b.items())}, "sigmadi": sum(x["sigmadi"] for x in xs),
                    "bos": sum(x["bos"] and not x["sigmadi"] for x in xs), "kesilen": sum(x["bitis"] == "length" for x in xs),
                    "istek_hatasi": sum(bool(x["istek_hatasi"]) for x in xs), "puanlayici_hatasi": sum(x["puanlayici_hatasi"] for x in xs),
                    "zaman_asimi": sum(x["zaman_asimi"] for x in xs),
                    # dfa kanitlidir; tests yolunda dogru sayilan cevap yalniz gizli metinleri gecmistir, ayri okunur
                    "regex_yol": {yol: {"soru": sum(x.get("via") == yol for x in xs), "dogru": sum(x.get("via") == yol and x["dogru"] for x in xs)}
                                  for yol in ("dfa", "tests")},
                    "maliyet_usd": round(sum(x["maliyet"] + x.get("hakem_maliyet", 0) for x in xs), 4)}
    (Path(a.sonuc) if a.sonuc else SONUC).write_text(json.dumps(tablo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ms = list(tablo)
    print(f"{'baslik':30}" + "".join(f"{m:>14}" for m in ms))
    for t in sorted({k for m in ms for k in tablo[m]["baslik"]}):
        print(f"{t:30}" + "".join(f"{tablo[m]['baslik'].get(t, float('nan')):14.1f}" for m in ms))
    for k in ("makro_baslik", "makro_ortak_sorular", "mikro", "sigmadi", "bos", "kesilen", "istek_hatasi", "puanlayici_hatasi", "zaman_asimi", "maliyet_usd"):
        print(f"{k:30}" + "".join(f"{tablo[m][k]:>14}" for m in ms))
    for yol in ("dfa", "tests"):
        print(f"{'regex ' + yol + ' dogru/soru':30}" + "".join(f"{tablo[m]['regex_yol'][yol]['dogru']}/{tablo[m]['regex_yol'][yol]['soru']:<8}".rjust(14) for m in ms))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("komut", choices=["hazirla", "pilot", "gonder", "kos", "al", "hakem-gonder", "hakem-al", "rapor"])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--model", choices=list(MODELLER))
    ap.add_argument("--onay", action="store_true", help="para harcayan komutlar icin zorunlu")
    ap.add_argument("--base-url")
    ap.add_argument("--ornek", type=int, default=2, help="pilot: set basina soru")
    ap.add_argument("--paralel", type=int, default=8)
    ap.add_argument("--sure", type=int, default=900)
    ap.add_argument("--isci", type=int, default=8)
    ap.add_argument("--sonuc", help="rapor dosyasi (varsayilan benchmark/sonuclar_tam_test.json)")
    a = ap.parse_args()
    D = Path(a.dir).resolve()
    D.mkdir(parents=True, exist_ok=True)
    {"hazirla": hazirla, "pilot": pilot, "gonder": gonder, "kos": kos, "al": al, "rapor": rapor, "hakem-al": hakem_al,
     "hakem-gonder": lambda a, D: adim_gonder(a, D, "hakem")}[a.komut](a, D)


if __name__ == "__main__":
    main()
