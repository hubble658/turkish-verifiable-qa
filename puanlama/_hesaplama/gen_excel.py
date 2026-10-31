# -*- coding: utf-8 -*-
"""Excel formulu uretimi -- orta/zor, LLM YOK. Her soru icin rastgele kucuk bir
tablo uretilip metne gomuluyor; cevap hem formul metni hem de o formulun
tablo uzerinde python ile hesaplanan beklenen sonucu (capraz dogrulama icin,
gercek bir Excel/LibreOffice motoruyla karsilastirilabilir)."""
import argparse
import random

from common import Writer, fmt_num
from excel_motor import excel_round
from grade import en_to_tr_formul, excel_dil_ekle

URUNLER = ["Laptop", "Telefon", "Kulaklık", "Klavye", "Monitör", "Mouse", "Tablet", "Hoparlör", "Şarj Aleti", "Webcam", "Yazıcı", "Router"]
BOLGELER = ["Ege", "Marmara", "İç Anadolu", "Akdeniz", "Karadeniz"]


def build_table(rng, n_rows):
    urunler = rng.sample(URUNLER, min(n_rows, len(URUNLER)))
    while len(urunler) < n_rows:
        urunler.append(rng.choice(URUNLER))
    rows = []
    for urun in urunler:
        rows.append({
            "urun": urun,
            "adet": rng.randint(5, 400),
            "fiyat": round(rng.uniform(50, 5000), 2),
            "bolge": rng.choice(BOLGELER),
        })
    return rows


def table_text(rows):
    lines = ["| Satır | A: Ürün | B: Satış Adedi | C: Birim Fiyat (TL) | D: Bölge |", "|---|---|---|---|---|"]
    for i, r in enumerate(rows, start=2):
        lines.append(f"| {i} | {r['urun']} | {r['adet']} | {r['fiyat']} | {r['bolge']} |")
    return "\n".join(lines)


def col_range(kol: str, n_rows: int) -> str:
    return f"{kol}2:{kol}{n_rows + 1}"


# ---------------- ORTA ----------------

def gen_temel_istatistik(rng):
    n = rng.randint(6, 12)
    rows = build_table(rng, n)
    kol, ad = rng.choice([("B", "adet"), ("C", "fiyat")])
    fonk, aciklama = rng.choice([
        ("SUM", "toplamını"), ("AVERAGE", "ortalamasını"), ("MAX", "en büyük değerini"),
        ("MIN", "en küçük değerini"), ("COUNT", "kaç adet dolu hücre olduğunu"),
    ])
    aralik = col_range(kol, n)
    formul = f"={fonk}({aralik})"
    vals = [r[ad] for r in rows]
    sonuc = {"SUM": sum(vals), "AVERAGE": sum(vals) / len(vals), "MAX": max(vals), "MIN": min(vals), "COUNT": len(vals)}[fonk]
    soru = (
        f"Aşağıdaki tabloya göre {kol} sütunundaki ({'Satış Adedi' if kol == 'B' else 'Birim Fiyat'}) "
        f"değerlerin {aciklama} veren Excel formülünü {aralik} aralığı için yazınız.\n\n{table_text(rows)}"
    )
    return soru, formul, fmt_num(sonuc, 3), (n, kol, fonk, tuple(vals))


def gen_kosullu_sayma(rng):
    n = rng.randint(7, 12)
    rows = build_table(rng, n)
    bolge = rng.choice(BOLGELER)
    mevcut = sorted({r["bolge"] for r in rows})
    if bolge not in mevcut:
        # tabloda olmayan bolge cevabi 0 yapiyordu (300'de 33, 2026-10-26); rng akisi degismesin diye belirlenimci
        bolge = mevcut[BOLGELER.index(bolge) % len(mevcut)]
    kosul_tip = rng.choice(["COUNTIF", "SUMIF"])
    if kosul_tip == "COUNTIF":
        formul = f'=COUNTIF({col_range("D", n)},"{bolge}")'
        sonuc = sum(1 for r in rows if r["bolge"] == bolge)
        aciklama = f'"{bolge}" bölgesine ait kaç satır olduğunu'
    else:
        formul = f'=SUMIF({col_range("D", n)},"{bolge}",{col_range("B", n)})'
        sonuc = sum(r["adet"] for r in rows if r["bolge"] == bolge)
        aciklama = f'"{bolge}" bölgesindeki satış adetlerinin (B sütunu) toplamını'
    soru = f"Aşağıdaki tabloya göre {aciklama} veren Excel formülünü yazınız.\n\n{table_text(rows)}"
    return soru, formul, fmt_num(sonuc, 3), (n, bolge, kosul_tip, tuple((r["bolge"], r["adet"]) for r in rows))


def gen_tek_hucre_yuzde(rng):
    n = rng.randint(5, 10)
    rows = build_table(rng, n)
    satir = rng.randint(2, n + 1)
    oran = rng.choice([10, 18, 20, 25])
    formul = f"=C{satir}*(1+{oran}/100)"
    fiyat = rows[satir - 2]["fiyat"]
    sonuc = fiyat * (1 + oran / 100)
    soru = (
        f"Aşağıdaki tabloda {satir}. satırdaki ürünün birim fiyatına (C{satir}) %{oran} KDV eklenmiş "
        f"halini hesaplayan Excel formülünü yazınız.\n\n{table_text(rows)}"
    )
    return soru, formul, fmt_num(sonuc, 3), (n, satir, oran, fiyat)


# ---------------- ZOR ----------------

def gen_ic_ice_yuvarlama(rng):
    n = rng.randint(6, 12)
    rows = build_table(rng, n)
    ondalik = rng.choice([0, 1, 2])
    formul = f"=ROUND(AVERAGE({col_range('C', n)}),{ondalik})"
    vals = [r["fiyat"] for r in rows]
    # Excel ROUND sifirdan uzaga yuvarlar; Python round() cifte-yuvarlama yapiyordu
    # (ortalama tam 3375.25 iken 3375.2 yazilmisti, Excel 3375.3 verir).
    sonuc = excel_round(sum(vals) / len(vals), ondalik)
    soru = (
        f"Aşağıdaki tabloya göre C sütunundaki (Birim Fiyat) değerlerin ortalamasını alıp "
        f"{ondalik} ondalık basamağa yuvarlayan TEK bir Excel formülü yazınız.\n\n{table_text(rows)}"
    )
    return soru, formul, fmt_num(sonuc, max(4, ondalik + 1)), (n, ondalik, tuple(vals))


def gen_kosullu_ortalama(rng):
    n = rng.randint(8, 12)
    rows = build_table(rng, n)
    bolge = rng.choice(BOLGELER)
    formul = f'=AVERAGEIF({col_range("D", n)},"{bolge}",{col_range("C", n)})'
    secilenler = [r["fiyat"] for r in rows if r["bolge"] == bolge]
    if not secilenler:
        rows[0]["bolge"] = bolge
        secilenler = [rows[0]["fiyat"]]
    sonuc = sum(secilenler) / len(secilenler)
    soru = (
        f'Aşağıdaki tabloya göre sadece "{bolge}" bölgesindeki satırların birim fiyat (C sütunu) '
        f"ortalamasını veren TEK bir Excel formülü yazınız.\n\n{table_text(rows)}"
    )
    return soru, formul, fmt_num(sonuc, 3), (n, bolge, tuple((r["bolge"], r["fiyat"]) for r in rows))


def gen_carpim_toplami(rng):
    n = rng.randint(6, 12)
    rows = build_table(rng, n)
    formul = f"=SUMPRODUCT({col_range('B', n)},{col_range('C', n)})"
    sonuc = sum(r["adet"] * r["fiyat"] for r in rows)
    soru = (
        "Aşağıdaki tabloya göre her satırda Satış Adedi (B) ile Birim Fiyat'ın (C) çarpılıp "
        "TÜM satırlar için toplanmasıyla elde edilen toplam ciroyu veren TEK bir Excel formülü "
        f"yazınız (yardımcı sütun kullanmadan).\n\n{table_text(rows)}"
    )
    return soru, formul, fmt_num(sonuc, 3), (n, tuple((r["adet"], r["fiyat"]) for r in rows))


def gen_tek_hucre_kosul(rng):
    n = rng.randint(6, 12)
    rows = build_table(rng, n)
    satir = rng.randint(2, n + 1)
    esik = rng.choice([50, 100, 150, 200, 250])
    formul = f'=IF(B{satir}>{esik},"Yüksek","Düşük")'
    adet = rows[satir - 2]["adet"]
    sonuc = "Yüksek" if adet > esik else "Düşük"
    soru = (
        f"Aşağıdaki tabloda B{satir} hücresindeki satış adedi {esik}'den büyükse \"Yüksek\", "
        f"değilse \"Düşük\" yazdıran Excel formülünü yazınız.\n\n{table_text(rows)}"
    )
    return soru, formul, sonuc, (n, satir, esik, adet)


ORTA = [
    ("temel_istatistik_fonksiyonu", gen_temel_istatistik),
    ("kosullu_sayma_toplam", gen_kosullu_sayma),
    ("tek_hucre_yuzde_hesabi", gen_tek_hucre_yuzde),
]
ZOR = [
    ("ic_ice_ortalama_yuvarlama", gen_ic_ice_yuvarlama),
    ("kosullu_ortalama", gen_kosullu_ortalama),
    ("carpim_toplami_sumproduct", gen_carpim_toplami),
    ("tek_hucre_kosul_metin", gen_tek_hucre_kosul),
]


def run(n_per_alt_tip: int, seed: int = 21):
    rng = random.Random(seed)
    w = Writer("excel_formulu", seed=seed)
    for zorluk, grup in (("orta", ORTA), ("zor", ZOR)):
        for alt_tip, fn in grup:
            tries, added = 0, 0
            while added < n_per_alt_tip and tries < n_per_alt_tip * 10:
                tries += 1
                soru, formul, sonuc, key = fn(rng)
                if w.add(alt_tip, zorluk, excel_dil_ekle(soru), formul, key, cevap_tr=en_to_tr_formul(formul), beklenen_sonuc=sonuc, dogrulama_yontemi="decimal_excel_round+libreoffice_capraz"):
                    added += 1
    w.close()
    print(w.summary())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-alt-tip", type=int, default=250)
    ap.add_argument("--seed", type=int, default=21)
    args = ap.parse_args()
    run(args.n_per_alt_tip, args.seed)
