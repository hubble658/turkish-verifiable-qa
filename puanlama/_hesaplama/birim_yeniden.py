# -*- coding: utf-8 -*-
"""birim_donusumu: altin cevabi SORU METNINDEN yeniden hesaplar (2026-10-31).

Iki amac: (1) bazi altinlar 3 ondaliga yuvarlanmis ("102.51 Pa kac bar?" -> 0.001; kesin 0.0010251, %2.5
fark) -- kesin degeri yazan model %1 toleransla reddediliyordu; (2) soru KB'nin 1000 mi 1024 mu, galonun ABD
mi Ingiliz mi, HP'nin mekanik mi metrik beygir mi oldugunu soylemiyor -- obur tanimla hesaplayan model de
dogru sayilmali. Yeniden hesaplanan standart deger altinla (altinin ondalik hassasiyetinde) tutarli degilse
hicbir ek deger dondurulmez; yani bu modul altin cevabi asla gecersiz kilmaz, yalniz kabul kumesini genisletir.
"""
import re

STANDART = {
    "mm": 1e-3, "cm": 1e-2, "m": 1, "km": 1e3, "inç": 0.0254, "mil": 1609.344, "yarda": 0.9144, "fit": 0.3048,
    "mg": 1e-6, "g": 1e-3, "kg": 1, "ton": 1e3, "ons": 0.028349523125, "libre": 0.45359237,
    "ml": 1e-6, "l": 1e-3, "m³": 1, "galon": 0.003785411784,
    "cm²": 1e-4, "m²": 1, "km²": 1e6, "hektar": 1e4, "dönüm": 1e3,
    "byte": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3, "TB": 1024 ** 4,
    "Pa": 1, "kPa": 1e3, "bar": 1e5, "atm": 101325, "mmHg": 133.322387415,
    "J": 1, "kJ": 1e3, "cal": 4.184, "kcal": 4184, "kWh": 3.6e6,
    "W": 1, "kW": 1e3, "HP": 745.69987158227,
    "sn": 1, "dk": 60, "saat": 3600, "gün": 86400, "hafta": 604800,
}
ALTERNATIF = [  # soruda belirtilmeyen ikinci yaygin tanim
    {"KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12},
    {"galon": 0.00454609},
    {"HP": 735.49875},
]
_U = "|".join(sorted(map(re.escape, STANDART), key=len, reverse=True))
_NU = re.compile(rf"(-?\d+(?:\.\d+)?(?:e[-+]?\d+)?)\s*({_U})(?![\wçğıöşü³²])")


def _hesapla(soru, alt_tip, cevap, F):
    s = soru
    gu = cevap.split()[-1]
    if alt_tip == "sicaklik_zincir":
        return float(re.search(r"(-?[\d.]+)°C", s).group(1)) + 273.15
    if alt_tip == "capraz_hiz":
        (d, du), (t, tu) = _NU.findall(s)[:2]
        v = float(d) * F[du] / (float(t) * F[tu])
        return v * 3.6 if "km/saat" in cevap else v
    q = [(float(x), u) for x, u in _NU.findall(s)]
    if alt_tip == "zincir_2adim":
        return q[0][0] * F[q[0][1]] / F[gu]
    if alt_tip == "ters_problem":
        m = re.search(rf"Bir değer ({_U}) cinsinden ölçülüp ({_U}) birimine çevrildiğinde (\S+) ", s)
        return float(m.group(3)) * F[m.group(2)] / F[m.group(1)]
    if alt_tip == "toplam_capraz_birim":
        return (q[0][0] * F[q[0][1]] + q[1][0] * F[q[1][1]]) / F[gu]
    if alt_tip == "zincir_3adim_fark":
        return abs(q[0][0] * F[q[0][1]] - q[1][0] * F[q[1][1]]) / F[gu]
    if alt_tip == "oran_capraz_birim":
        return q[0][0] * F[q[0][1]] / (q[1][0] * F[q[1][1]])
    if alt_tip == "yuzde_olcek":
        p = float(re.search(r"%(\d+(?:\.\d+)?)", s).group(1))
        isaret = -1 if re.search(r"azalt|küçült|düşür", s) else 1
        return q[0][0] * F[q[0][1]] * (1 + isaret * p / 100) / F[gu]
    return None


def _ondalik(cevap):
    m = re.match(r"\s*-?\d+(?:\.(\d+))?(?:e([-+]?\d+))?", cevap)
    if not m:
        return None, None
    d = len(m.group(1) or "") - int(m.group(2) or 0)
    return float(m.group(0)), d


def ek_altinlar(rec):
    """[kesin standart deger, alternatif tanimli degerler...]; tutarsizlikta []."""
    if rec.get("kategori") != "birim_donusumu" or not rec.get("soru"):
        return []
    try:
        std = _hesapla(rec["soru"], rec["alt_tip"], rec["cevap"], STANDART)
        g, d = _ondalik(rec["cevap"])
        if std is None or g is None:
            return []
        # tutarlilik: standart deger, altinin yazildigi hassasiyette altina yuvarlaniyor mu (+%0.05 pay)
        if abs(std - g) > 0.5 * 10 ** (-d) * 1.0001 + abs(g) * 5e-4:
            return []
        out = [std]
        for alt, tanim in zip(ALTERNATIF, ("1024", "ABD galonu", "745.7")):
            if tanim in rec["soru"]:  # 2026-11-01'den beri soru tanimi yaziyor; obur tanim artik yanlis
                continue
            if not any(re.search(rf"(?<![\wçğıöşü]){re.escape(u)}(?![\wçğıöşü³²])", rec["soru"] + " " + rec["cevap"]) for u in alt):
                continue
            v = _hesapla(rec["soru"], rec["alt_tip"], rec["cevap"], {**STANDART, **alt})
            if v and abs(v - std) > 1e-12 * abs(std):
                out.append(v)
        return out
    except (AttributeError, IndexError, KeyError, ValueError, ZeroDivisionError):
        return []
