# -*- coding: utf-8 -*-
"""Kategoriye gore, bir modelin serbest metin cevabinin dogru olup olmadigina
karar veren toleranslı degerlendiriciler. score_qwen.py bunu kullanir."""
import json
import re
import xml.etree.ElementTree as ET

from gen_xml import infer_shape, xml_to_obj

# Bosluk/dar-bosluk ( ,  ) binlik ayiracli sayilar (ör. "63 350 767 616",
# Nemotron bu bicimi sik kullaniyor) -- ilk alternatif bunu yakalar, yoksa
# ikinci (eski) alternatife duser. Alternatifi ONCE koymak, ayni baslangic
# pozisyonunda regex motorunun bosluk-grupluyu tercih etmesini saglar; "\d{3}"
# zorunlulugu rastgele bosluklu metni yanlislikla sayi sanmayi engeller.
NUM_RE = re.compile(
    r"-?\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?(?:[eE][+-]?\d+)?"
    r"|-?\d[\d.,]*(?:[eE][+-]?\d+)?"
)
FRAC_RE = re.compile(r"-?\d+\s*/\s*\d+")
# Nemotron kesirleri sik sik LaTeX "\frac{1}{12}" / "\dfrac{5}{13}" bicimiyle
# yaziyor -- FRAC_RE'nin beklediği "a/b" duz-slash bicimiyle eslesmiyordu,
# dogru kesir cevabi taninmadan extract_last_number'a duserek yanlis bir sayi
# (parca payi/paydasi ayri sayi sanilarak) cikariliyordu. Puanlamadan ONCE
# metni "a/b" bicimine cevirerek mevcut FRAC_RE/frac_matches mantigini
# degistirmeden calistiriyoruz.
LATEX_FRAC_RE = re.compile(r"\\d?frac\{(-?\d+)\}\{(-?\d+)\}")


def delatex_frac(text: str) -> str:
    return LATEX_FRAC_RE.sub(lambda m: f"{m.group(1)}/{m.group(2)}", text)
# "2.86×10^5" / "2,86 x 10^5" bicimli bilimsel gosterim -- modeller "anlamli
# rakam"a yuvarlarken sik kullaniyor, NUM_RE bunu YAKALAMIYORDU (sadece "e5"
# sonekini taniyordu, "×10^5"i degil) -> dogru cevap yanlislikla eleniyordu.
# Us kismi bazen UNICODE UST SIMGE rakamlarla geliyor ("10⁵") -- \d bunlari
# yakalamiyor (kategori Nd degil, No), o yuzden ikinci grup ayrica ust simge
# karakterleri de kabul ediyor; extract_last_number cevirip float'a ceviriyor.
SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
# Nemotron LaTeX bicimini sik kullaniyor: "\times" (kelime, "×" sembolu DEGIL --
# "x/X" da eslemiyordu cunku "times" kelimesinde harf 'x' yok) ve us kismini
# "10^{5}" gibi SUSLU PARANTEZLE sarmalıyor -- ikisi de eski regex'te
# YAKALANMIYORDU, dogru cevap "5" gibi anlamsiz bir parcaya indirgeniyordu.
SCI_RE = re.compile(r"(-?\d[\d.,]*)\s*(?:[×xX]|\\times)\s*10\s*\^?\s*\{?(-?\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)\}?")


def _to_float(tok: str):
    """Hem Ingilizce (1,234.56) hem Turkce (1.234,56 / 14666,67) ondalik
    bicimini kabul eder. Eskiden HER virgulu koru koru siliyordu -- bu, model
    Turkce ondalik virgul kullaninca (cok yaygin) '14666,67' -> '1466667' gibi
    sessizce YANLIS bir sayi uretiyordu."""
    tok = tok.strip()
    if not tok:
        return None
    # Bosluk / dar-bosluk / NBSP binlik ayiraci -- her zaman ondalik degil
    # (ondalik zaten . ya da , ile gelir), o yuzden dogrudan silinebilir.
    tok = re.sub(r"[  \xa0]", "", tok)
    if not tok:
        return None
    has_comma, has_dot = "," in tok, "." in tok
    if has_comma and has_dot:
        # en sagdaki ayirici ondalik ayiracidir (TR: "1.234,56", EN: "1,234.56")
        if tok.rfind(",") > tok.rfind("."):
            tok = tok.replace(".", "").replace(",", ".")
        else:
            tok = tok.replace(",", "")
    elif has_comma:
        tok = tok.replace(",", ".")
    elif tok.count(".") > 1:
        tok = tok.replace(".", "")  # "274.726.912" -> binlik ayiracidir, ondalik yok
    try:
        return float(tok)
    except ValueError:
        return None


def extract_last_number(text: str):
    """Metindeki EN SONDAKI sayiyi doner -- "a/b" kesir bicimi de (ör.
    "312/115 mol/L") ayri bir sayi cifti olarak degil, tek deger olarak
    degerlendirilir; hangisi metinde daha SONRA geciyorsa o kazanir."""
    text = delatex_frac(text)
    # (end_pos, oncelik, deger) -- oncelik: sci/frac eslesmesi kendi icinde bir
    # duz sayiyi de icerdigi icin ("×10^5" sonundaki "5" NUM_RE'ye de sayi gibi
    # gorunuyor) ayni end_pos'ta esitlik olursa sci/frac (oncelik=1) KAZANMALI,
    # yoksa parcali "5" gibi anlamsiz bir deger secilebiliyordu.
    candidates = []
    m_frac = list(FRAC_RE.finditer(text))
    if m_frac:
        m = m_frac[-1]
        n, d = m.group(0).replace(" ", "").split("/")
        nf, df = _to_float(n), _to_float(d)
        if nf is not None and df not in (None, 0):
            candidates.append((m.end(), 1, nf / df))
    m_sci = list(SCI_RE.finditer(text))
    if m_sci:
        m = m_sci[-1]
        base, exp = _to_float(m.group(1)), _to_float(m.group(2).translate(SUPERSCRIPT_MAP))
        if base is not None and exp is not None:
            candidates.append((m.end(), 1, base * (10 ** exp)))
    m_num = list(NUM_RE.finditer(text))
    if m_num:
        m = m_num[-1]
        val = _to_float(m.group(0))
        if val is not None:
            candidates.append((m.end(), 0, val))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[-1][2]


def numeric_close(model_text: str, gold_cevap: str, tolerans_yuzde: float = 0.5):
    gold_val = extract_last_number(gold_cevap)
    model_val = extract_last_number(model_text)
    if gold_val is None or model_val is None:
        return False
    if gold_val == 0:
        return abs(model_val) < 1e-6
    return abs(model_val - gold_val) / abs(gold_val) * 100 <= max(tolerans_yuzde, 1.0)


def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[().,]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def grade_matris(rec, model_text):
    gold = rec["cevap"]
    if gold.startswith("x="):
        m = re.search(r"x\s*=\s*(-?[\d.]+).*?y\s*=\s*(-?[\d.]+)", model_text, re.IGNORECASE | re.DOTALL)
        if not m:
            return False
        gx, gy = re.search(r"x=(-?[\d.]+)", gold).group(1), re.search(r"y=(-?[\d.]+)", gold).group(1)
        return abs(float(m.group(1)) - float(gx)) < 0.01 and abs(float(m.group(2)) - float(gy)) < 0.01
    if "/" in gold and re.match(r"^-?\d+/\d+$", gold):
        num, den = gold.split("/")
        gold_val = float(num) / float(den)
        # modelin cevabinda da "a/b" bicimli bir kesir olabilir -- extract_last_number
        # "1/5" icindeki "1" ve "5"i AYRI sayi olarak gorup yanlis (son) sayiyi alirdi.
        frac_matches = re.findall(r"-?\d+\s*/\s*\d+", delatex_frac(model_text))
        if frac_matches:
            mn, md = frac_matches[-1].replace(" ", "").split("/")
            model_val = float(mn) / float(md)
        else:
            model_val = extract_last_number(model_text)
        return model_val is not None and abs(model_val - gold_val) < 0.01
    return numeric_close(model_text, gold, tolerans_yuzde=1.0)


def grade_numeric_unit(rec, model_text):
    return numeric_close(model_text, rec["cevap"], rec.get("tolerans_yuzde", 1.0))


# bunlar SADECE birim/etiket kelimesi -- sayi/gun-adi/tarih dogruysa ama model
# CEVAP satirinda bu YALIN birim kelimesini yazmadiysa (ör. "CEVAP: 8" yerine
# "CEVAP: 8 yaş") YANLIS sayilmamali; asil bilgi (8) zaten dogru.
_TARIH_ATLANABILIR_BIRIM = {"yaş", "gün", "hafta", "kat"}


def grade_tarih(rec, model_text):
    # parantez ici (ör. "(Çarşamba)") sadece dogrulama amacli bonus bilgi --
    # soru bunu ayrica istemedigi surece modelden bunu da yazmasini ZORUNLU KILMA.
    # 2026-10-30: (1) varsa yalniz son "CEVAP:" satiri okunur -- eskiden butun metin taraniyordu, muhakemede
    # gecen herhangi bir tarih eslesmeye sayiliyordu; (2) alt dizge degil SOZCUK eslesmesi -- "8 yas" altini
    # "98765.4321" cevabinda "8" alt dizge oldugu icin dogru sayiliyordu (ters sinamada 2.100'un 170'i).
    # Sayi sozcugu birebir esit olmali; sozcukte Turkce ek tolere edilir ("mart" ~ "mart'ta").
    gold_ana = re.sub(r"\([^)]*\)", "", rec["cevap"])
    tokens = [t for t in normalize_text(gold_ana).split(" ") if t]
    satirlar = re.findall(r"^[\s*_#]*CEVAP\s*:\s*(.+?)[\s*_]*$", model_text, flags=re.IGNORECASE | re.MULTILINE)
    body = re.sub(r"\([^)]*\)", " ", satirlar[-1] if satirlar else model_text)
    body_tokens = [t for t in re.split(r"[\s/;]+", normalize_text(body).replace("*", " ")) if t]

    def var(t):
        if re.fullmatch(r"\d+", t):
            return any(re.fullmatch(rf"0*{int(t)}(?:['’][a-zçğıöşü]+)?\.?", b) for b in body_tokens)
        return any(b == t or b.startswith(t) for b in body_tokens)

    eksik = [t for t in tokens if not var(t)]
    return all(t in _TARIH_ATLANABILIR_BIRIM for t in eksik)


# Turkce Excel arayuzu fonksiyonlari kendi yerel adiyla yazar (EGER, ORTALAMA,
# EGERSAY...) -- modeller de genelde bunu kullaniyor. Ingilizce altin cevapla
# adil karsilastirma icin normalize ederken TR -> EN cevriliyor.
_EXCEL_TR_EN = {
    "EGER": "IF", "ORTALAMA": "AVERAGE", "TOPLA": "SUM", "SAYEGER": "COUNTIF",
    "EGERSAY": "COUNTIF",  # Turkce Excel'in gercek COUNTIF adi (SAYEGER yalniz eski takma ad)
    "ETOPLA": "SUMIF", "EGERORTALAMA": "AVERAGEIF", "YUVARLA": "ROUND",
    "MAK": "MAX", "MIN": "MIN", "BAGDEGSAY": "COUNT", "TOPLACARPIM": "SUMPRODUCT",
    # excel_veritabani (sayfa-arasi arama) icin eklenenler
    "DUSEYARA": "VLOOKUP", "INDIS": "INDEX", "KACINCI": "MATCH", "CAPRAZARA": "XLOOKUP",
    "COKETOPLA": "SUMIFS", "COKEGERSAY": "COUNTIFS", "COKEGERORTALAMA": "AVERAGEIFS",
    "COKEGERMAK": "MAXIFS", "COKEGERMIN": "MINIFS", "EGERHATA": "IFERROR", "EGERYOKSA": "IFNA",
    "FILTRE": "FILTER", "MUTLAK": "ABS", "BAGDEGDOLUSAY": "COUNTA",
    "ARA": "LOOKUP", "YATAYARA": "HLOOKUP", "ALTTOPLAM": "SUBTOTAL", "KACINCIX": "XMATCH",
    "ESAYIYSA": "ISNUMBER", "YADA": "OR", "VE": "AND", "BUYUK": "LARGE", "KUCUK": "SMALL",
    "SIRALA": "SORT", "SIRALAOLCUT": "SORTBY", "ELEMAN": "CHOOSE", "EHATALIYSA": "ISERROR", "EYOKSA": "ISNA",
    "SATIRSAY": "ROWS", "SUTUNSAY": "COLUMNS",
    # zor-2 pilotu (gruplayip secme, medyan)
    "DOLAYLI": "INDIRECT", "BENZERSIZ": "UNIQUE", "ORTANCA": "MEDIAN", "DEGIL": "NOT", "SIRALI": "SEQUENCE", "SATIR": "ROW",
}


# Ingilizce -> Turkce Excel (gercek yerel adlar; cevap_tr alani icin)
_EXCEL_EN_TR = {
    "IF": "EĞER", "AVERAGE": "ORTALAMA", "SUM": "TOPLA", "COUNTIF": "EĞERSAY", "SUMIF": "ETOPLA",
    "AVERAGEIF": "EĞERORTALAMA", "ROUND": "YUVARLA", "MAX": "MAK", "MIN": "MİN", "COUNT": "BAĞ_DEĞ_SAY",
    "SUMPRODUCT": "TOPLA.ÇARPIM", "VLOOKUP": "DÜŞEYARA", "INDEX": "İNDİS", "MATCH": "KAÇINCI",
    "XLOOKUP": "ÇAPRAZARA", "SUMIFS": "ÇOKETOPLA", "COUNTIFS": "ÇOKEĞERSAY", "AVERAGEIFS": "ÇOKEĞERORTALAMA",
    "MAXIFS": "ÇOKEĞERMAK", "MINIFS": "ÇOKEĞERMİN", "IFERROR": "EĞERHATA", "IFNA": "EĞERYOKSA",
    "FILTER": "FİLTRE", "ABS": "MUTLAK", "COUNTA": "BAĞ_DEĞ_DOLU_SAY", "LOOKUP": "ARA",
    "LARGE": "BÜYÜK", "SMALL": "KÜÇÜK", "SORT": "SIRALA", "SORTBY": "SIRALAÖLÇÜT", "CHOOSE": "ELEMAN",
    "LET": "LET", "ISNUMBER": "ESAYIYSA",
    "UNIQUE": "BENZERSİZ", "MEDIAN": "ORTANCA", "AND": "VE", "OR": "YADA", "NOT": "DEĞİL", "ROW": "SATIR",
}


# Excel sorularinda istenen yazim (22 Ekim 2026 karari): gold `cevap` Ingilizce Excel formulu, soru bunu
# acikca ister. `cevap_tr` ek alan olarak kalir; puanlayici Turkce yazimi da kabul etmeye devam eder.
EXCEL_DIL_CUMLESI = ("Formülü İngilizce Excel yazımıyla verin (İngilizce fonksiyon adları, örneğin SUM, IF; "
                     "bağımsız değişken ayracı virgül, ondalık ayracı nokta).")


def excel_dil_ekle(soru: str) -> str:
    """Dil cumlesini sorunun ilk paragrafinin (tablodan once) sonuna ekler."""
    if EXCEL_DIL_CUMLESI in soru:
        return soru
    ilk, _, kalan = soru.partition("\n\n")
    return f"{ilk} {EXCEL_DIL_CUMLESI}" + (f"\n\n{kalan}" if kalan else "")


def en_to_tr_formul(f: str) -> str:
    """Ingilizce Excel formulunu Turkce yerel Excel yazimina cevirir: fonksiyon
    adlari, TRUE/FALSE -> DOĞRU/YANLIŞ, "," -> ";", ondalik nokta -> virgul (sayilarda
    ve ">1.89" gibi olcut metinlerinde). Sayfa adlari ve diger metinler aynen kalir."""
    from excel_motor import tokenize
    out = []
    for kind, tok in tokenize(f.lstrip("=")):
        if kind == "func":
            tok = _EXCEL_EN_TR.get(tok.upper(), tok)
        elif kind == "bool":
            tok = "DOĞRU" if tok == "TRUE" else "YANLIŞ"
        elif kind == "num":
            tok = tok.replace(".", ",")
        elif kind == "str" and re.fullmatch(r'"(?:<>|<=|>=|<|>|=)?-?\d+\.\d+"', tok):
            tok = tok.replace(".", ",")
        elif tok == ",":
            tok = ";"
        out.append(tok)
    return "=" + "".join(out)


def _tr_to_en_formula(s: str) -> str:
    s = s.upper()
    s = (s.replace("İ", "I").replace("Ğ", "G").replace("Ş", "S")
           .replace("Ç", "C").replace("Ö", "O").replace("Ü", "U"))
    s = s.replace("TOPLA.CARPIM", "TOPLACARPIM").replace("BAG_DEG_SAY", "BAGDEGSAY")
    # "SAY.EGER" (COUNTIF) once dot-stripilmeli, yoksa "EGER" (IF) kurali icindeki
    # kelime "SAY.EGER"i de yanlislikla "SAY.IF"e cevirir (dict sirasinda EGER
    # kurali once calisiyor, o zamana kadar dot hala oradaysa \bEGER\b iceride eslesiyor).
    s = s.replace("SAY.EGER", "SAYEGER")
    for tr, en in _EXCEL_TR_EN.items():
        s = re.sub(rf"\b{tr}\b", en, s)
    s = s.replace(";", ",")  # TR Excel arguman ayraci ";" -- EN'de ","
    return s


def _eval_excel_arith(formula: str):
    """SAF ARITMETIK (fonksiyon cagrisi YOK) tek-hucre-referansli bir Excel formulunu
    ("=C10*(1+20/100)", "=C10*1,2" gibi) test degeriyle sayisal olarak degerlendirir.
    Model, matematiksel olarak esdeger ama farkli yazilmis bir formul verdiginde
    (ör. carpani onceden hesaplayip "*1.2" yazmak, gold'un "*(1+20/100)" ac,ik
    bicimine karsi) saf metin karsilastirmasi bunlari YANLIS sayiyordu -- bu, o
    esdegerligi dogrudan hesaplayarak kontrol eder. Fonksiyon cagrisi (COUNTIF, IF,
    vs) iceren ya da birden fazla/hic hucre referansi olmayan formuller icin None
    doner (bu checker'in kapsami disinda, ust seviye substring karsilastirmasina
    birakilir)."""
    # excel_formulu artik TAM metin aliyor (score_deepinfra.py) -- formul metnin
    # ORTASINDA gomulu olabilir ("...formul: =C2*1.1\n\nCEVAP: 2380" gibi, model
    # CEVAP satirina formul yerine hesaplanmis sonucu yazdiginda). Once metindeki
    # SON "=...formul-benzeri..." parcasini bul, sonra onu degerlendir.
    text = formula.upper().replace("`", "").replace("**", "")
    formula_matches = re.findall(r"=[A-Z0-9.,()+\-*/% \t]+", text)
    if not formula_matches:
        return None
    s = formula_matches[-1].strip()[1:]  # bastaki "=" at
    if re.search(r"[A-ZİĞŞÇÖÜ]{2,}\s*\(", s):
        return None  # fonksiyon cagrisi var, bu checker'a uygun degil
    cell_refs = set(re.findall(r"\b[A-Z]{1,2}\d{1,4}\b", s))
    if len(cell_refs) != 1:
        return None
    ref = cell_refs.pop()
    expr = re.sub(rf"\b{ref}\b", "1000", s)
    expr = expr.replace(",", ".").replace("%", "/100")
    # model_text genelde "CEVAP:" sonrasinin TAMAMI (markdown "**" gibi kirintilarla
    # birlikte) -- formul bittikten sonraki gecersiz kuyruk karakterlerini atmak icin
    # baştan gecerli aritmetik run'ini al, tum string'in gecerli olmasini BEKLEME.
    m = re.match(r"[\d.\s+\-*/()]+", expr)
    if not m or not m.group(0).strip():
        return None
    try:
        return ref.upper(), eval(m.group(0), {"__builtins__": {}}, {})
    except Exception:
        return None


def _grade_excel_metin(rec, model_text, sadece_eslesme=False):
    def norm(s):
        return re.sub(r"\s+", "", _tr_to_en_formula(s))
    gold = norm(rec["cevap"])
    # findall + SON eslesme: model_text artik TAM metin (score_deepinfra.py'de
    # excel_formulu da json/xml gibi tam-metin istisnasina alindi) -- akil
    # yurutmede erken/yanlis bir formul denemesi olabilir, modelin nihai/son
    # yazdigi formul daha guvenilir bir aday.
    matches = re.findall(r"=[A-ZİĞŞÇÖÜ.]+\([^\n]*", model_text.upper())
    m = matches[-1] if matches else None
    raw_candidate = m if m else model_text
    candidate = norm(raw_candidate)
    if gold in candidate:
        return True
    if sadece_eslesme:
        return False
    gold_eval = _eval_excel_arith(rec["cevap"])
    if gold_eval is not None:
        cand_eval = _eval_excel_arith(raw_candidate)
        if cand_eval is not None:
            gold_ref, gold_val = gold_eval
            cand_ref, cand_val = cand_eval
            if gold_ref == cand_ref and abs(cand_val - gold_val) < 1e-6:
                return True
    # metinsel IF sonucu (=IF(...,"Yuksek","Dusuk")) gibi durumlarda beklenen sonucu da kontrol et
    beklenen = str(rec.get("beklenen_sonuc", ""))
    if beklenen and beklenen.strip('"') and (normalize_text(beklenen) in normalize_text(model_text)
                                             or _sayi_yazilmis(model_text, beklenen)):
        return gold.split("(")[0] in candidate  # en azindan dogru fonksiyon adi kullanilmis mi
    return False


def _sayi_yazilmis(model_text: str, beklenen: str) -> bool:
    """Metindeki bir sayi, kendi yazildigi basamakta beklenen degere esit mi
    (5321.0875 icin "5321.09" ya da "5321,088" kabul; bir birimlik yuvarlama farki
    toleransi)."""
    from decimal import Decimal, InvalidOperation
    try:
        g = Decimal(beklenen)
    except InvalidOperation:
        return False
    for tok in NUM_RE.findall(model_text):
        t = tok.replace(" ", "").replace("\u00a0", "").replace("\u202f", "")
        if "," in t and "." in t:
            t = t.replace(",", "") if t.rfind(".") > t.rfind(",") else t.replace(".", "").replace(",", ".")
        elif "," in t:
            t = t.replace(",", ".")
        try:
            x = Decimal(t)
        except InvalidOperation:
            continue
        k = -x.as_tuple().exponent if x.as_tuple().exponent < 0 else 0
        if abs(x - g) <= Decimal(1).scaleb(-k) and k >= min(2, -g.as_tuple().exponent if g.as_tuple().exponent < 0 else 0):
            return True
    return False


# ---------------- calistirarak puanlama (excel_formulu + excel_veritabani ortak) ----------------

def _deger_esit(v, bek: str) -> bool:
    """Sayilarda goreli 1e-9 (LibreOffice yedeginin 15 basamak float gürültüsü),
    metinde Turkce harf katlamali esitlik."""
    from decimal import Decimal, InvalidOperation
    from excel_motor import tr_fold
    try:
        b = Decimal(bek)
    except InvalidOperation:
        return isinstance(v, str) and tr_fold(v) == tr_fold(bek)
    return isinstance(v, Decimal) and abs(v - b) <= Decimal("1e-9") * max(Decimal(1), abs(b))


def _kabul_degerleri(rec, kt):
    """Bir kitap icin kabul edilen gold degerleri: kayitli deger (Excel kurali:
    sifirdan uzaga) + gold formul tam yarim degerde baska bir motorun kuraliyla
    (cifte yuvarlama / asagi) hesaplansaydi cikacak degerler. Esitlik (tam yarim)
    yoksa uc kural ayni sonucu verir, yani tolerans yalniz o durumda devreye girer."""
    from decimal import ROUND_HALF_DOWN, ROUND_HALF_EVEN
    from excel_motor import Calisma, ExcelHata, fmt_excel
    kabul = [kt["beklenen_sonuc"]]
    if "ROUND" in rec["cevap"].upper():
        for kural in (ROUND_HALF_EVEN, ROUND_HALF_DOWN):
            try:
                v = Calisma(kt["sayfalar"], kt["varsayilan_sayfa"]).hesapla(_excel_db_normalize(rec["cevap"]), yuvarlama=kural)
            except (ExcelHata, NotImplementedError):
                continue
            kabul.append(v if isinstance(v, str) else fmt_excel(v, 10))
    return kabul


_EXCEL_KITAP_ONBELLEK = {}


def _excel_formulu_kitaplari(rec):
    """excel_formulu kaydi icin: soru metnindeki tablo + 2 pertürbe tablo (B/C/D
    sutunlari gen_excel.py ile ayni araliklardan yeniden cekilir, A ve satir sayisi
    sabit; tohum kayit id'sinden). Gold formul her kitapta motorla hesaplanir."""
    if rec["id"] in _EXCEL_KITAP_ONBELLEK:
        return _EXCEL_KITAP_ONBELLEK[rec["id"]]
    import random
    import zlib
    from excel_dogrula import tablo_oku
    from excel_motor import Calisma, ExcelHata, fmt_excel
    from gen_excel import BOLGELER

    org = tablo_oku(rec["soru"])
    rng = random.Random(zlib.crc32(rec["id"].encode()))
    tablolar = [("orijinal", org)]
    n = len(org) - 1
    if n > 1:  # dongusel kaydirma: sabit hucre adresiyle "dogru" cikan cevaplari kesin bozar
        kay = [org[0]] + [[org[1 + i][0], org[1 + (i + 1) % n][1], org[1 + (i + 1) % n][2], org[1 + (i + 2) % n][3]]
                          for i in range(n)]
        try:
            Calisma({"S": kay}).hesapla(rec["cevap"])
            tablolar.append(("kaydirma", kay))
        except ExcelHata:
            pass
    # sinir kitaplari: tek hucreli formullerde (=IF(B7>200,...)) basvurulan hucre
    # formuldeki esik sayisina ve bir fazlasina esitlenir (> / >= karisikligini yakalar)
    tekler = sorted(set(re.findall(r"(?<![:A-Z$])\$?([BC])\$?(\d+)(?![:\d])", rec["cevap"])))
    esikler = [int(x) for x in re.findall(r"(?<![A-Z\d.])(\d+)(?![\d.])", re.sub(r"[A-Z]+\d+", "", rec["cevap"]))]
    for kol, satir in tekler:
        for t in esikler:
            if t < 2:
                continue
            for deger in (t, t + 1):
                tb = [list(r) for r in org]
                tb[int(satir) - 1][1 if kol == "B" else 2] = deger
                tablolar.append((f"sinir_{kol}{satir}_{deger}", tb))
    # yuvarlama kitaplari: =ROUND(AVERAGE(C2:Cn),d) icin C2 ayarlanarak yuvarlanacak deger
    # birimin 0.2 ve 0.8'ine oturtulur -> ROUNDUP/ROUNDDOWN/TRUNC kesin ayrisir
    m = re.fullmatch(r"=ROUND\(AVERAGE\(C2:C(\d+)\),(\d+)\)", rec["cevap"])
    if m:
        from decimal import Decimal, ROUND_FLOOR
        son, d = int(m.group(1)), int(m.group(2))
        birim = Decimal(1).scaleb(-d)
        vals = [Decimal(str(r[2])) for r in org[1:son]]
        ort = sum(vals) / len(vals)
        for pay in ("0.2", "0.8"):
            hedef_ort = (ort / birim).to_integral_value(ROUND_FLOOR) * birim + Decimal(pay) * birim
            tb = [list(r) for r in org]
            tb[1][2] = float(vals[0] + (hedef_ort - ort) * len(vals))
            tablolar.append((f"yuvarlama_{pay}", tb))
    # kriter kitabi: formuldeki bolge metni araligin ILK ve SON satirina yazilir
    # (=AVERAGEIF(D4:D13,...) gibi eksik aralikli cevaplari yakalar)
    for L in re.findall(r'"([^"]+)"', rec["cevap"]):
        if L in BOLGELER:
            tb = [list(r) for r in org]
            tb[1][3] = tb[-1][3] = L
            tablolar.append((f"kriter_{L}", tb))
    hedef = len(tablolar) + 6  # + 6 rastgele kitap (toplamsal sorularda tesadüfi esitligi seyreltir)
    while len(tablolar) < hedef:
        for _ in range(50):
            # kitaplarin yarisinda fiyat 4 basamakli: ortalama tesadüfen 2 basamakta "tam" cikip
            # ROUNDUP/ROUNDDOWN'u ROUND'dan ayirt edilemez kilmasin
            bas = 4 if len(tablolar) % 2 else 2
            t = [org[0]] + [[r[0], rng.randint(5, 400), round(rng.uniform(50, 5000), bas), rng.choice(BOLGELER)] for r in org[1:]]
            try:
                Calisma({"S": t}).hesapla(rec["cevap"])
                break
            except ExcelHata:  # ör. AVERAGEIF esleşmesiz kaldi
                continue
        tablolar.append((f"perturbe_{len(tablolar)}", t))
    kitaplar = []
    for etiket, t in tablolar:
        v = Calisma({"S": t}).hesapla(rec["cevap"])
        kitaplar.append({"etiket": etiket, "varsayilan_sayfa": "S", "sayfalar": {"S": t},
                         "beklenen_sonuc": fmt_excel(v, 10) if not isinstance(v, str) else v})
    _EXCEL_KITAP_ONBELLEK[rec["id"]] = kitaplar
    return kitaplar


def grade_excel(rec, model_text):
    """1) gold formulle metin eslesmesi (eski yol, hizli); 2) modelin formulu
    calistirilabiliyorsa karar CALISTIRARAK verilir: soru tablosu + 2 pertürbe
    tabloda gold formulle ayni sonuc (ROUND'lu sorularda bir birim tolerans);
    3) formul cozumlenemiyorsa eski yedek kontroller."""
    if _grade_excel_metin(rec, model_text, sadece_eslesme=True):
        return True
    aday = _excel_db_aday(model_text)
    if aday:
        sanal = {"calisma_kitaplari": _excel_formulu_kitaplari(rec), "cevap": rec["cevap"]}
        karar = _kitaplarda_dogru(sanal, aday)
        if karar is not None:
            return karar
    return _grade_excel_metin(rec, model_text)


# ---------------- excel_veritabani: calistirarak puanlama ----------------
# Ayrik (cok sayfali) sorularda dogru formul tek degil (INDEX/MATCH, VLOOKUP,
# XLOOKUP, SUMPRODUCT...) -- metin karsilastirmasi yerine modelin formulu kayittaki
# calisma kitaplarinda (orijinal + pertürbe) calistirilir, her birinde kayitli
# sonucla esit olmali. Pertürbe kitaplarda satir sirasi, olcu degerleri ve
# (ayrikta) anahtar kodlari degistigi icin sabit hucre adresi/sabit sayi yazan
# cevaplar elenir.

def _excel_db_normalize(f: str) -> str:
    """Model formulunu motorun anladigi bicime getirir: Turkce fonksiyon adlari ->
    Ingilizce (_EXCEL_TR_EN), DOGRU/YANLIS -> TRUE/FALSE, TR ayraci ";" -> ","
    (o durumda ondalik virgul -> nokta). Tirnak icindeki metinlere ve sayfa
    adlarina dokunulmaz."""
    parcalar = re.split(r'("(?:[^"]|"")*")', f)
    tr_ayrac = any(";" in p for p in parcalar[0::2])
    out = []
    for i, p in enumerate(parcalar):
        if i % 2:
            # TR olcut metni ">1,89" -> ">1.89" (yalniz ";" ayracli, yani TR yerel formulde)
            if tr_ayrac and re.fullmatch(r'"(?:<>|<=|>=|<|>|=)?-?\d+,\d+"', p):
                p = p.replace(",", ".")
            out.append(p)
            continue
        def _fn(m):
            ad = m.group(1)
            ana = ad.upper()
            for a, b in zip("İIĞŞÇÖÜ", "IIGSCOU"):
                ana = ana.replace(a, b)
            ana = ana.replace(".", "").replace("_", "")
            return _EXCEL_TR_EN.get(ana, ad) + m.group(2)
        p = re.sub(r"(?<![\w!'])([^\W\d][\w.]*)(\s*\()", _fn, p)
        p = re.sub(r"(?<![\w!'.])(DOĞRU|DOGRU)(?![\w(!])", "TRUE", p, flags=re.I)
        p = re.sub(r"(?<![\w!'.])(YANLIŞ|YANLIS)(?![\w(!])", "FALSE", p, flags=re.I)
        if tr_ayrac:
            p = re.sub(r"(?<=\d),(?=\d)", ".", p).replace(";", ",")
        out.append(p)
    return "".join(out).strip()


def _excel_db_aday(model_text: str):
    """Model metnindeki son formulu cikarir (CEVAP: satiri varsa once orasi)."""
    text = model_text.replace("`", "").replace("**", "")
    m = re.findall(r"CEVAP\s*:\s*(=[^\n]+)", text, flags=re.I)
    adaylar = m or re.findall(r"(=\s*[^\W\d][\w.]*\s*\([^\n]*|=\s*\$?[A-Z]{1,2}\$?\d+[^\n]*)", text)
    return adaylar[-1].strip() if adaylar else None


def excel_db_degerlendir(rec, formul: str, beklenen_kontrol=None):
    """Formulu kaydin tum calisma kitaplarinda calistirir -> [deger|hata]. Motor
    fonksiyonu desteklemiyorsa ya da cozumleyemiyorsa LibreOffice'e (dizi kipi)
    duser. Kuyruktaki fazlaliklar ("... formulu kullanilir.") icin sondan
    kirpilarak cozumlenebilir en uzun on ek aranir."""
    from excel_motor import Calisma, ExcelHata, libreoffice_hesapla, lo_sonuc_dec, tokenize

    def _kitap(kt):
        sayfalar = dict(kt["sayfalar"])
        if len(sayfalar) > 1:
            sayfalar["_formul_sayfasi"] = [[None]]  # ciplak referans bos sayfaya gider
            return sayfalar, "_formul_sayfasi"
        return sayfalar, kt["varsayilan_sayfa"]

    f = _excel_db_normalize(formul)
    adaylar = [f]
    if ";" not in formul and re.search(r"\d,\d", f):
        # ";" olmadan ondalik virgul (=C2*1,18): ondalik okumasi da denenir
        adaylar.append(re.sub(r"(?<=\d),(?=\d)", ".", f))
    # kuyruk metni ("... formulu kullanilir.") yalniz BOSLUKTAN kirpilir; karakter
    # karakter kirpmak "=C2*1,10"u "=C2*1" gibi baska gecerli bir formule cevirebiliyordu
    for i in range(len(f) - 1, 1, -1):
        if f[i].isspace():
            adaylar.append(f[:i].rstrip(" .,;:"))
    adaylar.append(f.rstrip(" .,;:"))
    secilen = None
    if beklenen_kontrol is not None:
        for a in adaylar[:2]:  # tam formul ve ondalik okumasi: dogru olan tercih edilir
            try:
                sh, ana = _kitap(rec["calisma_kitaplari"][0])
                if beklenen_kontrol(Calisma(sh, ana).hesapla(a), rec["calisma_kitaplari"][0]):
                    adaylar = [a]
                    break
            except Exception:
                continue
    for a in adaylar:
        try:
            tokenize(a.lstrip("="))
            sh, ana = _kitap(rec["calisma_kitaplari"][0])
            Calisma(sh, ana).hesapla(a)
            secilen = a
            break
        except ExcelHata:
            secilen = a
            break
        except NotImplementedError:
            secilen = ("lo", a)
            break
        except Exception:
            continue
    if secilen is None:
        return None, None
    if isinstance(secilen, tuple):
        a = secilen[1]
        isler = [(*_kitap(kt), a) for kt in rec["calisma_kitaplari"]]
        return a, [lo_sonuc_dec(x) for x in libreoffice_hesapla(isler, dizi=True)]
    sonuc = []
    for kt in rec["calisma_kitaplari"]:
        sh, ana = _kitap(kt)
        try:
            sonuc.append(Calisma(sh, ana).hesapla(secilen))
        except ExcelHata as e:
            sonuc.append(e.kod)
    return secilen, sonuc


def _kitaplarda_dogru(rec, aday: str):
    """Aday formulu kaydin calisma kitaplarinda calistirir. None = formul
    cozumlenemedi (karar verilemez); aksi halde tum kitaplarda dogru mu."""
    from excel_motor import tokenize

    formul, degerler = excel_db_degerlendir(
        rec, aday, lambda v, kt: any(_deger_esit(v, b) for b in _kabul_degerleri(rec, kt)))
    if not degerler:
        return None
    # en az bir hucre/aralik referansi sart (sabit sayi/metin yazan cevaplar)
    if not any(k == "ref" for k, t in tokenize(formul.lstrip("="))):
        return False
    return all(any(_deger_esit(v, b) for b in _kabul_degerleri(rec, kt))
               for v, kt in zip(degerler, rec["calisma_kitaplari"]))


def grade_excel_db(rec, model_text):
    from excel_motor import tokenize

    aday = _excel_db_aday(model_text)
    if not aday:
        return False
    formul, _ = excel_db_degerlendir(rec, aday)
    # ayrik/birlesik sette tek hucre de yetmez: en az bir ARALIK sart
    if formul is None or not any(k == "ref" and ":" in t for k, t in tokenize(formul.lstrip("="))):
        return False
    return bool(_kitaplarda_dogru(rec, aday))


def _extract_json_obj(text: str):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _deep_close(a, b, tol=0.01):
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_deep_close(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_deep_close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= max(abs(b) * tol, 0.01)
    sa, sb = str(a).strip().lower(), str(b).strip().lower()
    fa, fb = _to_float(sa), _to_float(sb)
    if fa is not None and fb is not None:
        return abs(fa - fb) <= max(abs(fb) * tol, 0.01)
    return sa == sb


def grade_json(rec, model_text):
    gold = json.loads(rec["cevap"])
    model_obj = _extract_json_obj(model_text)
    if model_obj is None:
        return False
    return _deep_close(model_obj, gold)


def grade_xml(rec, model_text):
    gold_xml = rec["cevap"]
    root_tag_m = re.match(r"<(\w+)>", gold_xml.strip())
    if not root_tag_m:
        return False
    root_tag = root_tag_m.group(1)
    m = re.search(rf"<{root_tag}>.*</{root_tag}>", model_text, re.DOTALL)
    if not m:
        return False
    try:
        gold_root = ET.fromstring(gold_xml)
        model_root = ET.fromstring(m.group(0))
    except ET.ParseError:
        return False
    gold_obj = xml_to_obj(gold_root, infer_shape_from_xml(gold_root))
    try:
        model_obj = xml_to_obj(model_root, infer_shape_from_xml(gold_root))
    except Exception:
        return False
    return _deep_close(model_obj, gold_obj)


def infer_shape_from_xml(elem):
    """gen_xml.infer_shape dict uzerinden calisiyordu (elimizde deger vardi);
    burada elimizde sadece XML var, o yuzden agac uzerinden tur cikariyoruz --
    yaprak degerler hep str olarak kiyaslanir (deep_close string'e de bakiyor)."""
    shape = {}
    for child in elem:
        if len(child):
            grandchildren = list(child)
            if len(grandchildren) and all(gc.tag == grandchildren[0].tag for gc in grandchildren):
                shape[child.tag] = [infer_shape_from_xml(grandchildren[0])]
            else:
                shape[child.tag] = infer_shape_from_xml(child)
        else:
            shape[child.tag] = str
    return shape


GRADERS = {
    "matris_islemleri": grade_matris,
    "birim_donusumu": grade_numeric_unit,
    "tarih_hesaplama": grade_tarih,
    "excel_formulu": grade_excel,
    "excel_veritabani": grade_excel_db,
    "fizik_hesabi": grade_numeric_unit,
    "kimya_hesabi": grade_numeric_unit,
    "json_uretimi": grade_json,
    "xml_uretimi": grade_xml,
}


def grade(rec, model_text: str) -> bool:
    try:
        return GRADERS[rec["kategori"]](rec, model_text)
    except Exception:
        return False
