"""MEB (korpus) setleri: kisa sozel cevap. Once kural eslesmesi (korpus/generate_questions.answers_match), altinla
ve `orijinal.kabul_edilen` listesindeki esdeger yazimlarla (2026-11-07; korpus/meb_alternatif_batch.py, V4-Flash uretim
+ V4-Pro kati hakem); tutmazsa istege bagli LLM hakem (JUDGE_PROMPT, olcumde deepseek-ai/DeepSeek-V3-0324). Bu setlerin altin
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


# harfe bitisik rakam (CO2, H2O, I1, F2) sayi degil formul/etiket parcasidir
_BAGIMSIZ_SAYI_RE = re.compile(r"(?<![\w.,])-?\d+(?:[.,]\d+)?(?![\wçğıöşü])")
_OLUMSUZ_RE = re.compile(r"\b(değil\w*|hayır|yok|ya da|veya|yahut)\b")
_BIRIM_UZUNLUGU = 5  # "K", "g", "mol", "mmHg", "kat": yalin sayi cevabinda yazilmasa da olur


def _sayilar(s):
    """Metindeki sirasiyla (sira onemli: "3:4" ile "4 > 3", "1/2" ile "2:1" ayni degil)."""
    return [float(x.replace(",", ".")) for x in _BAGIMSIZ_SAYI_RE.findall(s)]


def _isaretler(s):
    """Rakamdan once gelen eksi isaretleri: normalize() isareti sildigi icin "-3E" ~ "3E" oluyordu."""
    return len(re.findall(r"[-−]\s*\d", s))


def answers_match(tahmin: str, altin: str) -> bool:
    """Model cevabinin hizli yolla (hakeme gitmeden) dogru sayilip sayilmayacagi. Bu yol YALNIZ emin oldugunda
    True der; suphede False doner ve karar hakeme kalir (hakemsiz skor alt sinirdir).

    2026-10-31 (onceki surum yalniz ILK sayilari kiyasliyordu; gercek olcumlerde "3/4" ~ "3/1", "1/8" ~ "1/4",
    "atom numarasi 84" ~ "88", "18-30" ~ "18-25", "SO2" ~ "CO2", "H2SO4" ~ "H2O", "polar değildir" ~ "polar"
    dogru sayilmisti):
    - bagimsiz sayilarin TAMAMI (coklu kume) esit olmali; harfe bitisik rakam sayi sayilmaz;
    - sayilar esitse metin de tutmali: altinin sozcukleri cevapta gecmeli ya da cevap yalin sayiysa altinin
      metni kisa bir birim olmali ("298 K" ~ "298");
    - altinda olmayan olumsuzluk / secenek sozcugu (değil, hayır, yok, ya da, veya) cevapta varsa hakeme.
    Metinde: parantezler atilinca normalize esitlik ("Karbon dioksit" ~ "karbondioksit (CO₂)") ya da altin
    cevabin SOZCUKLERI model cevabinda ardisik geciyor (3+ harfli sozcukte Turkce ek tolere)."""
    if not normalize(tahmin) or not normalize(altin):
        return False
    kt, ka = _tr_lower(tahmin), _tr_lower(altin)
    if any(m.group(0) not in ka for m in _OLUMSUZ_RE.finditer(kt)):
        return False
    if _isaretler(tahmin) != _isaretler(altin):
        return False
    if _tr_lower(tahmin).strip() == _tr_lower(altin).strip():
        return True
    psiz = lambda x: re.sub(r"\([^)]*\)", " ", x)
    st, sa = _sozcukler(tahmin), _sozcukler(psiz(altin))

    def sayilar_esit(a, b):
        return len(a) == len(b) and all(abs(x - y) <= 1e-6 for x, y in zip(a, b))

    nt, na = _sayilar(tahmin), _sayilar(psiz(altin))
    if nt or na:
        # cevabin sayilari altinin parantezsiz ya da tam hâliyle tutmali ("karekök(2) katına" kendisiyle eslesir;
        # cevabin parantezi atilmaz: "Vs = (3/2) * Vp" ~ "Vs = Vp * (2N/3N) * (3N/N)" yanlis eslesirdi)
        if not (sayilar_esit(nt, na) or sayilar_esit(nt, _sayilar(altin))):
            return False
        sa_metin = [w for w in sa if not _BAGIMSIZ_SAYI_RE.fullmatch(w)]
        st_metin = [w for w in st if not _BAGIMSIZ_SAYI_RE.fullmatch(w)]
        if not sa_metin:
            return True
        if not st_metin:  # yalin sayi cevabi: altinda yalniz birim ("298 K") ya da tek sozcuk ("259 saniye")
            return len(sa_metin) == 1 or all(len(w) <= _BIRIM_UZUNLUGU for w in sa_metin)
        return _icinde(sa_metin, st_metin) or all(len(w) <= _BIRIM_UZUNLUGU for w in sa_metin) and not set(st_metin) - set(sa_metin)
    parantezsiz = lambda x: normalize(_tr_lower(re.sub(r"\([^)]*\)", " ", x)))
    if parantezsiz(tahmin) and parantezsiz(tahmin) == parantezsiz(altin):
        return True
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


def puanla(soru, altin, metin, hakem=None, kabul=None):
    """hakem: istege bagli f(istem_metni) -> model cevabi metni. Verilmezse yalniz kural eslesmesi
    (hakemsiz skor alt sinirdir). kabul: altinla esdeger ek yazimlar; kural eslesmesi bunlarla da denenir,
    hakem yine yalniz altini gorur."""
    tahmin = cevap_al(metin)
    if any(answers_match(tahmin, a) for a in [altin, *(kabul or [])]):
        return True
    if hakem is None or not tahmin:
        return False
    yanit = hakem(JUDGE_PROMPT.format(soru=soru, cevap1=altin, cevap2=tahmin))
    m = re.search(r"\{.*\}", yanit or "", re.S)
    try:
        return bool(json.loads(m.group(0)).get("ayni_mi")) if m else False
    except json.JSONDecodeError:
        return False
