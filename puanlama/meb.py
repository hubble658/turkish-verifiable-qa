"""MEB (korpus) setleri: kisa sozel cevap. Once kural eslesmesi (korpus/generate_questions.answers_match);
tutmazsa istege bagli LLM hakem (JUDGE_PROMPT, olcumde deepseek-ai/DeepSeek-V3-0324). Bu setlerin altin
cevabi da LLM ile dogrulandi, kesin degildir; raporlarda kesin setlerden ayri verin."""
import json
import re

ISTEM = """Aşağıdaki soruyu lise düzeyindeki bilgine dayanarak cevapla.
Cevabın tek, net, kısa bir ifade olsun. Emin değilsen en olası cevabı yine de ver.

SORU: {soru}

Sadece şu JSON formatında cevap ver: {{"cevap": "..."}}
"""

JUDGE_PROMPT = """İki cevap aynı anlama mı geliyor, karşılaştır. Türkçe çekim/morfoloji
farkları (ör. "sıkışma" ~ "sıkıştırılma"), eş anlamlılık, kavramın ADI ile TANIMININ
birbirini karşılaması (ör. "Avogadro yasası" ~ "eşit hacimlerde eşit tanecik sayısı"),
ya da aynı kavramın farklı teknik terimlerle ifade edilmesi (ör. "referans noktası" ~
"referans çerçevesi", "kayma sürtünmesi" ~ "kinetik sürtünme") -- bunların HEPSİ AYNI
kabul edilir. Biri diğerinden gerçekten farklı bir kavram/değer/mekanizma belirtiyorsa
(ör. "kohezyon" ~ "hidrojen bağı" -- ilki gözlemlenen olgu, ikincisi onun nedeni olan
farklı bir mekanizma) ya da biri "BİLİNMİYOR" ise FARKLI kabul edilir.

SORU: {soru}
CEVAP 1: {cevap1}
CEVAP 2: {cevap2}

Sadece şu JSON formatında cevap ver, "neden" alanını EN FAZLA 10 KELİME tut:
{{"ayni_mi": true/false, "neden": "..."}}
"""


def normalize(s: str) -> str:
    return re.sub(r"[^\wçğıöşü]+", "", s.lower())


_NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def _tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def _sozcukler(s):
    return re.findall(r"[\wçğıöşü]+", _tr_lower(s))


def _icinde(kisa, uzun):
    """kisa'nin sozcukleri uzun'da ardisik geciyor mu; 3+ harfli sozcukte Turkce ek tolere edilir
    ("azalır" ~ "azalırlar"), kisa sozcuk ("C", "su", "O2") birebir olmali."""
    n = len(kisa)
    for i in range(len(uzun) - n + 1):
        if all(u == k or (len(k) >= 3 and u.startswith(k)) for k, u in zip(kisa, uzun[i:i + n])):
            return True
    return False


def answers_match(tahmin: str, altin: str) -> bool:
    """Model cevabinin hizli yolla (hakeme gitmeden) dogru sayilip sayilmayacagi. Ikisi de sayi iceriyorsa
    TAM sayisal esitlik ("8" ~ "98" yanlis-pozitifi, 2026-09-02). Metinde (2026-10-30): parantezler
    atilinca normalize esitlik ("Karbon dioksit" ~ "karbondioksit (CO₂)") ya da altin cevabin SOZCUKLERI
    model cevabinda ardisik geciyor. Eski hali iki yonde harf dizgesi ariyordu: altin "C" iken "c" harfi
    gecen her cevap, "Apolardır" altinina "polar" cevabi dogru sayiliyordu (altin cevaplarin 483'u 3
    karakter ya da daha kisa); kisa model cevabi uzun altinin icinde de aranmaz ("ışık" ≠ "Işık şiddeti").
    Eslesmezse False: hakeme dusulur."""
    if not normalize(tahmin) or not normalize(altin):
        return False
    num_a, num_b = _NUM_RE.search(tahmin), _NUM_RE.search(altin)
    if num_a and num_b:
        try:
            return abs(float(num_a.group().replace(",", ".")) - float(num_b.group().replace(",", "."))) < 1e-6
        except ValueError:
            pass
    parantezsiz = lambda x: normalize(_tr_lower(re.sub(r"\([^)]*\)", " ", x)))
    if parantezsiz(tahmin) and parantezsiz(tahmin) == parantezsiz(altin):
        return True
    st, sa = _sozcukler(tahmin), _sozcukler(re.sub(r"\([^)]*\)", " ", altin))
    return bool(st and sa) and _icinde(sa, st)


def cevap_al(metin):
    m = re.search(r"\{.*\}", metin or "", re.S)
    if m:
        try:
            v = json.loads(m.group(0))
            if isinstance(v, dict) and "cevap" in v:
                return str(v["cevap"])
        except json.JSONDecodeError:
            pass
    m = re.findall(r"^[\s*_]*CEVAP\s*:\s*(.+?)[\s*_]*$", metin or "", re.I | re.M)
    if m:
        return m[-1].strip()
    s = [x for x in (metin or "").strip().splitlines() if x.strip()]
    return s[-1].strip() if s else ""


def puanla(soru, altin, metin, hakem=None):
    """hakem: istege bagli f(istem_metni) -> model cevabi metni. Verilmezse yalniz kural eslesmesi
    (hakemsiz skor alt sinirdir)."""
    tahmin = cevap_al(metin)
    if answers_match(tahmin, altin):
        return True
    if hakem is None or not tahmin:
        return False
    yanit = hakem(JUDGE_PROMPT.format(soru=soru, cevap1=altin, cevap2=tahmin))
    m = re.search(r"\{.*\}", yanit or "", re.S)
    try:
        return bool(json.loads(m.group(0)).get("ayni_mi")) if m else False
    except json.JSONDecodeError:
        return False
