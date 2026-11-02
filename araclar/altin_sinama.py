"""Altin cevap oz-sinamasi: her satirin altin cevabi, modelin yazacagi bicime sokulup kendi puanlayicisindan
gecirilir. Gecmeyen satir ya veri hatasi ya puanlayici hatasidir. MEB setlerinde yalniz kural eslesmesi
sinanir (altin cevap kendisiyle eslesir; hakem cagrilmaz).

Kullanım:
    python3 araclar/altin_sinama.py veri/*.jsonl                 # hepsi
    python3 araclar/altin_sinama.py --ornek 200 veri/*.jsonl     # kategori basina en fazla 200 (sabit tohum)
    python3 araclar/altin_sinama.py --ters veri/*.jsonl          # bariz yanlis cevap reddediliyor mu
    python3 araclar/altin_sinama.py --yakin veri/*.jsonl         # az bozulmus cevap reddediliyor mu
Cikti: kategori basina gecen/toplam; gecmeyenler --hatali dosyasina (varsayilan altin_sinama_hatali.jsonl).
"""
import argparse
import copy
import gzip
import json
import random
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from puanlama import _uyarla, istem, orijinal, puanla  # noqa: E402


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


def _ilk_sayiyi_boz(s, oran=None):
    """Metindeki ilk bagimsiz sayiyi bozar: tam sayi +1, ondalik *oran (yoksa +1)."""
    m = re.search(r"(?<![\w.])(?<!\d,)-?\d+(?:[.,]\d+)?(?![\w.]|,\d)", s)
    if not m:
        return None
    v = m.group(0).replace(",", ".")
    if float(v) == 0:  # sifirin orani yine sifir
        yeni = "1"
    elif oran:  # fiziksel buyukluk: tam sayi da oransal bozulur (+1, %1 toleransin icinde kalirdi)
        yeni = repr(round(float(v) * oran, 10))
    else:
        yeni = str(int(v) + 1) if "." not in v else repr(round(float(v) + 1, 10))
    return s[:m.start()] + yeni + s[m.end():]


def _sonucu_boz(g):
    g = copy.deepcopy(g)
    for satir in g:
        for i, v in enumerate(satir):
            if isinstance(v, bool):
                continue
            if isinstance(v, int):
                satir[i] = v + 1
                return g
            if isinstance(v, float):
                satir[i] = v * 1.01 + 0.1
                return g
    return None


def yakin_metin(r):
    """Yakin-yanlis sinama (2026-10-31): altin cevabin bir sayisi az miktar bozulur (tam sayi +1, ondalik %5);
    gecen olmamali. Toleransi gevsek puanlayiciyi yakalar (ör. 999 = 1000, %1 toleransla 345 ~ 347).
    Uygulanamayan kategoride None."""
    k, o, c = r["kategori"], orijinal(r), r["cevap"]
    if k in ("birim_donusumu", "fizik_hesabi", "kimya_hesabi"):
        if "^" in c:
            us = re.search(r"\^(-?\d+)", c).group(1)
            return f"CEVAP: {c.replace('^' + us, '^' + str(int(us) - 1))}"
        # birimde %15: soruda belirtilmeyen alternatif tanimlar (KB=1000, Ingiliz galonu...) %10'a kadar fark eder
        b = _ilk_sayiyi_boz(c, 1.15 if k == "birim_donusumu" else 1.05)
        return f"CEVAP: {b}" if b else None
    if k == "matris_islemleri":
        b = _ilk_sayiyi_boz(c) if "/" not in c else re.sub(r"^(-?\d+)", lambda m: str(int(m.group(1)) + 1), c)
        return f"CEVAP: {b}" if b else None
    if k == "tarih_hesaplama" and r["alt_tip"] in ("gun_farki_iki_tarih", "yas_hesabi", "iso_hafta_no"):
        return "CEVAP: " + re.sub(r"^\d+", lambda m: str(int(m.group(0)) + 2), c)
    if k == "json_uretimi":
        return _ilk_sayiyi_boz(c)
    if k == "xml_uretimi":
        m = re.search(r">(-?\d+(?:\.\d+)?)<", c)
        return c[:m.start(1)] + _ilk_sayiyi_boz(m.group(1)) + c[m.end(1):] if m else None
    if k == "sql_cikti_tahmini":
        b = _sonucu_boz(o["gold"])
        return json.dumps(b, ensure_ascii=False) if b else None
    if k == "solver":
        return None  # ters sinama zaten +1 deniyor
    if r["kaynak"] == "korpus":
        b = _ilk_sayiyi_boz(c, 1.05)
        return json.dumps({"cevap": b}, ensure_ascii=False) if b else None
    return None


def sina(r, ters=False, yakin=False):
    r = _uyarla(r)
    try:
        istem(r)  # istem kurulabiliyor mu (sema, eslik dosyasi, iskelet)
        if yakin:
            m = yakin_metin(r)
            return r["kategori"], r["id"], (None if m is None else puanla(r, m) is not True), None
        if ters:
            return r["kategori"], r["id"], puanla(r, yanlis_metin(r)) is not True, None
        return r["kategori"], r["id"], puanla(r, altin_metin(r)), None
    except Exception as e:  # noqa: BLE001
        return r["kategori"], r["id"], False, f"{type(e).__name__}: {e}"[:300]


def ac(d):
    if str(d).endswith(".parquet"):  # Hugging Face surumu
        import pyarrow.parquet as pq
        return (json.dumps(x, ensure_ascii=False) for x in pq.read_table(d).to_pylist())
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
    ap.add_argument("--yakin", action="store_true", help="az bozulmus (yakin-yanlis) cevaplarin REDDEDILDIGINI sina")
    a = ap.parse_args()
    toplam, gecen = Counter(), Counter()
    with ProcessPoolExecutor(a.isci) as ex, \
            open(a.hatali, "w", encoding="utf-8") as fh:
        for k, rid, ok, hata in ex.map(partial(sina, ters=a.ters, yakin=a.yakin), satirlar(a.dosyalar, a.ornek), chunksize=64):
            if ok is None:  # yakin sinama bu satira uygulanamadi
                continue
            toplam[k] += 1
            gecen[k] += ok is True
            if ok is not True:
                fh.write(json.dumps({"kategori": k, "id": rid, "sonuc": ok, "hata": hata}, ensure_ascii=False) + "\n")
    for k in sorted(toplam):
        print(f"{k:28s} {gecen[k]:6d}/{toplam[k]:<6d} {'' if gecen[k] == toplam[k] else '<-- ' + str(toplam[k] - gecen[k])}")
    print(f"{'TOPLAM':28s} {sum(gecen.values()):6d}/{sum(toplam.values())}")


if __name__ == "__main__":
    main()
