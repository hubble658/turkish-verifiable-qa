# -*- coding: utf-8 -*-
"""excel_formulu.jsonl denetimi: her sorunun tablosu soru metninden geri okunur,
gold formul (cevap) uc bagimsiz motorla hesaplanir ve kayitli beklenen_sonuc
ile karsilastirilir:
  1. excel_motor.Calisma (Decimal + Excel ROUND kurali)
  2. gercek LibreOffice headless (tum satirlar, tek soffice cagrisi)
  3. `formulas` paketi (orneklem; --formulas-n)
Kullanim: python excel_dogrula.py [--jsonl cikti/excel_formulu.jsonl] [--formulas-n 40]"""
import argparse
import json
import random
import re
from collections import Counter, defaultdict
from decimal import Decimal

from excel_motor import Calisma, ExcelHata, fmt_excel, lo_sonuc_dec, libreoffice_hesapla, formulas_hesapla, sonuc_str, to_dec

BASLIK = ["Ürün", "Satış Adedi", "Birim Fiyat (TL)", "Bölge"]


def tablo_oku(soru: str):
    """Soru metnindeki markdown tablodan sayfa satirlarini (1. satir baslik) cikarir."""
    rows = [BASLIK]
    for line in soru.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|(.*)\|\s*$", line)
        if not m:
            continue
        satir = int(m.group(1))
        assert satir == len(rows) + 1, (satir, len(rows))
        hucre = [c.strip() for c in m.group(2).split("|")]
        rows.append([hucre[0], Decimal(hucre[1]), Decimal(hucre[2]), hucre[3]])
    return rows


def gosterim_basamagi(rec) -> int:
    """gen_excel.py'nin her alt-tip icin kullandigi gosterim basamagi."""
    if rec["alt_tip"] == "ic_ice_ortalama_yuvarlama":
        ondalik = int(re.search(r",(\d)\)$", rec["cevap"]).group(1))
        return max(4, ondalik + 1)
    return 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default="cikti/excel_formulu.jsonl")
    ap.add_argument("--formulas-n", type=int, default=40, help="alt-tip basina formulas orneklemi")
    ap.add_argument("--rapor", default=None, help="farkli satirlari JSONL olarak yaz")
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(args.jsonl, encoding="utf-8")]
    sheets = [tablo_oku(r["soru"]) for r in recs]

    # 1) Decimal motoru
    motor = []
    for r, sh in zip(recs, sheets):
        try:
            motor.append(sonuc_str(Calisma({"S": sh}).hesapla(r["cevap"]), gosterim_basamagi(r)))
        except ExcelHata as e:
            motor.append(e.kod)

    # 2) LibreOffice (hepsi)
    lo_ham = libreoffice_hesapla([({"S": sh}, "S", r["cevap"]) for r, sh in zip(recs, sheets)])
    lo = [sonuc_str(lo_sonuc_dec(s), gosterim_basamagi(r)) if isinstance(lo_sonuc_dec(s), Decimal) else s
          for r, s in zip(recs, lo_ham)]

    # 3) formulas (orneklem)
    rng = random.Random(0)
    by_tip = defaultdict(list)
    for i, r in enumerate(recs):
        by_tip[r["alt_tip"]].append(i)
    orn = sorted(i for idx in by_tip.values() for i in rng.sample(idx, min(args.formulas_n, len(idx))))
    fo_ham = formulas_hesapla([({"S": sheets[i]}, "S", recs[i]["cevap"]) for i in orn])
    fo = {}
    for i, v in zip(orn, fo_ham):
        try:
            fo[i] = sonuc_str(to_dec(float(v)), gosterim_basamagi(recs[i]))
        except (TypeError, ValueError):
            fo[i] = str(v)

    say = defaultdict(Counter)
    farklar = []
    for i, r in enumerate(recs):
        t = r["alt_tip"]
        say[t]["n"] += 1
        kayitli = r["beklenen_sonuc"]
        if motor[i] != kayitli:
            say[t]["motor!=kayitli"] += 1
            farklar.append({"id": r["id"], "cevap": r["cevap"], "kayitli": kayitli, "motor": motor[i], "lo": lo[i]})
        if lo[i] != motor[i]:
            say[t]["lo!=motor"] += 1
            print("LO/MOTOR UYUSMAZLIGI", r["id"], r["cevap"], motor[i], lo[i], lo_ham[i])
        if i in fo:
            say[t]["formulas_n"] += 1
            if fo[i] != motor[i]:
                say[t]["formulas!=motor"] += 1
                print("FORMULAS/MOTOR UYUSMAZLIGI", r["id"], r["cevap"], motor[i], fo[i], fo_ham[orn.index(i)])

    print(f"\n{'alt_tip':30s} {'n':>5s} {'kayitli!=motor':>15s} {'LO!=motor':>10s} {'formulas n/fark':>16s}")
    for t, c in say.items():
        print(f"{t:30s} {c['n']:5d} {c['motor!=kayitli']:15d} {c['lo!=motor']:10d} {c['formulas_n']:>9d}/{c['formulas!=motor']}")
    tot = sum((c for c in say.values()), Counter())
    print(f"{'TOPLAM':30s} {tot['n']:5d} {tot['motor!=kayitli']:15d} {tot['lo!=motor']:10d} {tot['formulas_n']:>9d}/{tot['formulas!=motor']}")
    for f in farklar[:30]:
        print("  FARK", f)
    if args.rapor:
        with open(args.rapor, "w", encoding="utf-8") as fh:
            for f in farklar:
                fh.write(json.dumps(f, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
