"""Altin cevap oz-sinamasi: her satirin altin cevabi, modelin yazacagi bicime sokulup kendi puanlayicisindan
gecirilir. Gecmeyen satir ya veri hatasi ya puanlayici hatasidir. MEB setlerinde yalniz kural eslesmesi
sinanir (altin cevap kendisiyle eslesir; hakem cagrilmaz).

Kullanım:
    python3 araclar/altin_sinama.py veri/*.jsonl                 # hepsi
    python3 araclar/altin_sinama.py --ornek 200 veri/*.jsonl     # kategori basina en fazla 200 (sabit tohum)
    python3 araclar/altin_sinama.py --ters veri/*.jsonl          # bariz yanlis cevap reddediliyor mu
Cikti: kategori basina gecen/toplam; gecmeyenler --hatali dosyasina (varsayilan altin_sinama_hatali.jsonl).
"""
import argparse
import gzip
import json
import random
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from puanlama import istem, orijinal, puanla  # noqa: E402


def altin_metin(r):
    k, o, c = r["kategori"], orijinal(r), r["cevap"]
    if r["kaynak"] == "korpus":
        return json.dumps({"cevap": c}, ensure_ascii=False)
    if k == "solver":
        return f"```python\nprint({o['cevap']})\n```" if o["set"] == "kod" else f"<cevap>{o['cevap']}</cevap>"
    if k in ("json_uretimi", "xml_uretimi"):
        return c
    if k == "sql_cikti_tahmini":
        return json.dumps(o["gold"], ensure_ascii=False)
    if r["kaynak"] == "sql":
        return c
    return f"Çözüm.\nCEVAP: {c}"


def yanlis_metin(r):
    """Ters sinama: bariz yanlis cevap; gecen olmamali (her seye dogru diyen puanlayiciyi yakalar)."""
    k, o = r["kategori"], orijinal(r)
    if r["kaynak"] == "korpus":
        return json.dumps({"cevap": "bilmiyorum"}, ensure_ascii=False)
    if k == "solver":
        return f"```python\nprint({o['cevap'] + 1})\n```" if o["set"] == "kod" else f"<cevap>{o['cevap'] + 1}</cevap>"
    if k == "json_uretimi":
        return "{}"
    if k == "xml_uretimi":
        return "<kok/>"
    if k == "sql_cikti_tahmini":
        return "[[0]]"
    if k == "sql_cognipeer":
        return "SELECT 1 WHERE 0" if o["gorev"] == "secme" else "SELECT 1"
    if r["kaynak"] == "sql":
        return "SELECT 1 WHERE 0"
    if k in ("excel_formulu", "excel_veritabani"):
        return "CEVAP: =1"
    return "CEVAP: 98765.4321"


def sina(r, ters=False):
    try:
        istem(r)  # istem kurulabiliyor mu (sema, eslik dosyasi, iskelet)
        if ters:
            return r["kategori"], r["id"], puanla(r, yanlis_metin(r)) is not True, None
        return r["kategori"], r["id"], puanla(r, altin_metin(r)), None
    except Exception as e:  # noqa: BLE001
        return r["kategori"], r["id"], False, f"{type(e).__name__}: {e}"[:300]


def ac(d):
    return gzip.open(d, "rt", encoding="utf-8") if str(d).endswith(".gz") else open(d, encoding="utf-8")


def satirlar(dosyalar, ornek):
    if not ornek:
        for d in dosyalar:
            for l in ac(d):
                yield json.loads(l)
        return
    havuz, gorulen, rng = defaultdict(list), Counter(), random.Random(7)
    for d in dosyalar:
        for l in ac(d):
            r = json.loads(l)
            k = r["kategori"]
            gorulen[k] += 1
            if len(havuz[k]) < ornek:
                havuz[k].append(r)
            elif (j := rng.randrange(gorulen[k])) < ornek:
                havuz[k][j] = r
    for v in havuz.values():
        yield from v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dosyalar", nargs="+")
    ap.add_argument("--ornek", type=int, default=0)
    ap.add_argument("--isci", type=int, default=8)
    ap.add_argument("--hatali", default="altin_sinama_hatali.jsonl")
    ap.add_argument("--ters", action="store_true", help="bariz yanlis cevaplarin REDDEDILDIGINI sina")
    a = ap.parse_args()
    toplam, gecen = Counter(), Counter()
    with ProcessPoolExecutor(a.isci) as ex, \
            open(a.hatali, "w", encoding="utf-8") as fh:
        for k, rid, ok, hata in ex.map(partial(sina, ters=a.ters), satirlar(a.dosyalar, a.ornek), chunksize=64):
            toplam[k] += 1
            gecen[k] += ok is True
            if ok is not True:
                fh.write(json.dumps({"kategori": k, "id": rid, "sonuc": ok, "hata": hata}, ensure_ascii=False) + "\n")
    for k in sorted(toplam):
        print(f"{k:28s} {gecen[k]:6d}/{toplam[k]:<6d} {'' if gecen[k] == toplam[k] else '<-- ' + str(toplam[k] - gecen[k])}")
    print(f"{'TOPLAM':28s} {sum(gecen.values()):6d}/{sum(toplam.values())}")


if __name__ == "__main__":
    main()
