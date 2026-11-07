"""Karakter işlemleri seti: istem ve puanlayıcı (metin_islemleri/puanla.py'nin bu üç alt tipe indirilmiş hâli).

Son "CEVAP:" satırı alınır. ters_yazma / sezar: Türkçe küçük harfe çevrilip boşluklar teklenerek birebir.
islem_zinciri: birebir (büyük/küçük harf ve boşluklar dahil; yalnız dış tırnak/ters tırnak sökülür).
"""
import re

ISTEM = (
    "Aşağıdaki soruyu adım adım çöz. Açıklamandan SONRA, en son satırda tam olarak şu biçimde bitir: "
    "\"CEVAP: <senin nihai cevabın>\".\n\n{soru}"
)
CEVAP_RE = re.compile(r"^[\s*_#>]*CEVAP\s*:\s*(.*?)\s*$", re.I | re.M)


def kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def _sok(s):
    s = s.strip()
    if s.startswith("**") and s.endswith("**") and len(s) > 4:
        s = s[2:-2].strip()
    s = s.replace("**", "") if s.startswith("**") or s.endswith("**") else s
    for a, b in (('"', '"'), ("“", "”"), ("'", "'"), ("`", "`"), ("«", "»")):
        if len(s) >= 2 and s.startswith(a) and s.endswith(b):
            s = s[len(a):-len(b)]
    return s.strip() if not s.strip(" ") == "" else s


def istem(satir):
    return ISTEM.format(soru=satir["soru"])


def puanla(satir, metin):
    bul = CEVAP_RE.findall(metin or "")
    if not bul:
        return False
    a, altin = _sok(bul[-1]), satir["cevap"]
    if satir["alt_tip"] == "islem_zinciri":
        return a == altin or a.strip() == altin.strip()
    return re.sub(r"\s+", " ", kucuk(a)).strip(" .") == re.sub(r"\s+", " ", kucuk(altin))
