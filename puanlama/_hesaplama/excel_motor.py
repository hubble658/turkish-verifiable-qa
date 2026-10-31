# -*- coding: utf-8 -*-
"""Excel semantigiyle formul degerlendirme -- excel_formulu ve excel_db setlerinin
ortak motoru.

Neden var: eski gen_excel.py beklenen sonucu Python float + round() ile
hesapliyordu. Python round() cifte-yuvarlama (half-to-even) ve ikili float
uzerinde calisir (round(2.675, 2) == 2.67); Excel/LibreOffice ROUND() ise
sifirdan uzaga yuvarlar ve sayiyi once 15 anlamli basamaga indirger
(=ROUND(2.675;2) -> 2.68). Bu modul:

  * excel_round / fmt_excel: Excel kuraliyla yuvarlama ve gosterim (Decimal,
    ROUND_HALF_UP -- Decimal'de HALF_UP "sifirdan uzaga" demektir).
  * Calisma: kucuk bir formul yorumlayicisi (Decimal aritmetigi, cok sayfali
    referans, SUM/AVERAGE/COUNTIF/SUMIFS/VLOOKUP/INDEX/MATCH/XLOOKUP/...).
    Python tarafindaki bagimsiz hesap; gold degeri LibreOffice ile capraz
    dogrulanir.
  * libreoffice_hesapla: formulleri gercek LibreOffice headless'ta toplu
    hesaplatir (openpyxl ile .xlsx yaz -> soffice --convert-to csv; LO
    onbellekte deger olmayan formulleri yuklerken yeniden hesaplar).
"""
import csv
import re
import subprocess
import tempfile
from decimal import Decimal, ROUND_HALF_UP, getcontext
import threading
from pathlib import Path

getcontext().prec = 40


class ExcelHata(Exception):
    """#DIV/0!, #N/A, #VALUE! gibi Excel hata degerleri."""

    def __init__(self, kod):
        super().__init__(kod)
        self.kod = kod


# ---------------- yuvarlama / gosterim ----------------

def to_dec(x) -> Decimal:
    """float/int/str -> Decimal. float'lar Excel gibi 15 anlamli basamaga
    indirgenir (0.1+0.2 -> 0.3), boylece ikili float kalintisi yarim-basamak
    kararini bozmaz."""
    if isinstance(x, Decimal):
        return x
    if isinstance(x, bool):
        return Decimal(int(x))
    if isinstance(x, int):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(f"{x:.15g}")
    return Decimal(str(x))


_YUV = threading.local()  # puanlama: esitlik (tam yarim) kurali gecici degistirilebilir


def excel_round(x, ndigits: int = 0, kural=None) -> Decimal:
    """Excel ROUND(): sifirdan uzaga yuvarlama. Negatif ndigits de destekli.
    kural (ya da Calisma.hesapla(..., yuvarlama=...)) yalniz puanlayicinin "baska
    motor tam yarimda farkli yuvarlasaydi" alternatiflerini uretmesi icindir."""
    kural = kural or getattr(_YUV, "kural", None) or ROUND_HALF_UP
    d = to_dec(x)
    q = Decimal(1).scaleb(-ndigits)  # 10**-ndigits
    return d.quantize(q, rounding=kural) if ndigits >= 0 else \
        (d / q).quantize(Decimal(1), rounding=kural) * q


def fmt_excel(x, max_decimals: int = 4) -> str:
    """Sayiyi en fazla max_decimals basamakla, Excel yuvarlamasiyla, sondaki
    sifirlar atilmis yazar (common.fmt_num ile ayni bicim)."""
    d = excel_round(x, max_decimals)
    if d == d.to_integral_value():
        return str(int(d))
    return format(d.normalize(), "f")


# ---------------- hucre adresleri ----------------

def col_to_idx(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def idx_to_col(i: int) -> str:
    s = ""
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


_CELL = re.compile(r"\$?([A-Z]{1,3})\$?(\d+)")


def parse_cell(ref: str):
    m = _CELL.fullmatch(ref.upper())
    if not m:
        raise ValueError(ref)
    return col_to_idx(m.group(1)), int(m.group(2))


# ---------------- tokenizer ----------------

_TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<str>"(?:[^"]|"")*")
  | (?P<ref>(?:(?:'(?:[^']|'')+'|[^\W\d][\w.]*)!)?(?:\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?|\$?[A-Z]{1,3}:\$?[A-Z]{1,3}(?![\w(])))
  | (?P<num>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
  | (?P<func>[A-Za-z][A-Za-z0-9.]*(?=\())
  | (?P<bool>TRUE|FALSE)(?![\w.(])
  | (?P<name>[^\W\d][\w.]*)
  | (?P<op><>|<=|>=|[-+*/^&=<>%(),:;{}])
""", re.VERBOSE)


def tokenize(s: str):
    pos, out = 0, []
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m:
            raise SyntaxError(f"cozumlenemedi: {s[pos:pos+20]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        out.append((kind, m.group(0)))
    return out


# ---------------- yardimci deger islemleri ----------------

class Aralik:
    """Bir hucre araligi: 2B deger listesi (satir-major)."""

    def __init__(self, rows, r0=None):
        self.rows = rows
        self.r0 = r0  # sayfa araligiysa ilk satir numarasi (ROW icin); hesaplanmis dizide None

    @property
    def flat(self):
        return [v for r in self.rows for v in r]

    @property
    def shape(self):
        return len(self.rows), (len(self.rows[0]) if self.rows else 0)


def _is_num(v):
    return isinstance(v, Decimal)


def _scalar(v):
    if isinstance(v, Aralik):
        if v.shape == (1, 1):
            v = v.rows[0][0]
        else:
            raise ExcelHata("#VALUE!")
    if isinstance(v, ExcelHata):
        raise v
    return v


def _num(v):
    v = _scalar(v)
    if v is None:
        return Decimal(0)
    if isinstance(v, bool):
        return Decimal(int(v))
    if _is_num(v):
        return v
    try:
        return Decimal(str(v).replace(",", "."))
    except Exception:
        raise ExcelHata("#VALUE!")


def _nums_in(args):
    """SUM/AVERAGE/MIN/MAX/COUNT semantigi: araliktaki metin/bos atlanir,
    dogrudan verilen sayilar alinir."""
    out = []
    for a in args:
        if isinstance(a, Aralik):
            for v in a.flat:
                if isinstance(v, ExcelHata):
                    raise v
            out.extend(v for v in a.flat if _is_num(v))
        elif a is not None:
            out.append(_num(a))
    return out


def tr_fold(s) -> str:
    """Turkce farkindalikli harf katlama: Python casefold 'İ'yi 'i̇' (birlesik
    noktali) yapar ve 'I'yi 'i'ye indirir; Excel/LO Turkce yerelde İ<->i, I<->ı."""
    return str(s).replace("İ", "i").replace("I", "ı").lower()


def ascii_fold(s) -> str:
    s = str(s).upper()
    for a, b in zip("İIĞŞÇÖÜ", "IIGSCOU"):
        s = s.replace(a, b)
    return s


def _txt_eq(a, b):
    return tr_fold(a) == tr_fold(b)


def _cmp(a, b, op):
    if a is None:
        a = Decimal(0) if _is_num(b) else ""
    if b is None:
        b = Decimal(0) if _is_num(a) else ""
    if _is_num(a) and _is_num(b):
        x, y = a, b
    elif isinstance(a, str) and isinstance(b, str):
        x, y = tr_fold(a), tr_fold(b)
    else:  # Excel: sayi < metin; esitlik yanlis
        if op in ("=",):
            return False
        if op == "<>":
            return True
        x, y = (0, 1) if _is_num(a) else (1, 0)
    return {"=": x == y, "<>": x != y, "<": x < y, ">": x > y, "<=": x <= y, ">=": x >= y}[op]


def _kriter(crit):
    """COUNTIF/SUMIF kriteri -> predicate. Joker (* ?) bilerek desteklenmez;
    soru ureticisi joker iceren kriter kullanmaz."""
    crit = _scalar(crit)
    if _is_num(crit):
        return lambda v: _is_num(v) and v == crit
    s = str(crit)
    m = re.match(r"^(<>|<=|>=|=|<|>)?(.*)$", s, re.S)
    op, rest = m.group(1) or "=", m.group(2)
    if "*" in rest or "?" in rest or "~" in rest:
        raise NotImplementedError("joker kriter")
    try:
        target = Decimal(rest)
        is_n = True
    except Exception:
        target, is_n = rest, False
    if is_n:
        def p(v):
            if not _is_num(v):
                return op == "<>"
            return _cmp(v, target, op)
        return p
    if rest == "" and op == "=":
        return lambda v: v is None or v == ""
    if op == "=":
        return lambda v: isinstance(v, str) and _txt_eq(v, rest)
    if op == "<>":
        return lambda v: not (isinstance(v, str) and _txt_eq(v, rest))
    return lambda v: isinstance(v, str) and _cmp(v, rest, op)


def _ifs_mask(pairs):
    mask = None
    for rng, crit in pairs:
        p = _kriter(crit)
        m = [p(v) for v in rng.flat]
        mask = m if mask is None else [a and b for a, b in zip(mask, m)]
    return mask


def _lookup_eq(a, b):
    if _is_num(a) and _is_num(b):
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return _txt_eq(a, b)
    return False


def _f_vlookup(key, tbl, col, mode=Decimal(0)):
    key, col = _scalar(key), int(_num(col))
    if _num(mode) != 0:
        raise NotImplementedError("yaklasik VLOOKUP")
    for r in tbl.rows:
        if _lookup_eq(r[0], key):
            return r[col - 1]
    raise ExcelHata("#N/A")


def _f_match(key, rng, mode=Decimal(1)):
    key = _scalar(key)
    if _num(mode) != 0:
        raise NotImplementedError("yaklasik MATCH")
    for i, v in enumerate(rng.flat, start=1):
        if _lookup_eq(v, key):
            return Decimal(i)
    raise ExcelHata("#N/A")


def _f_index(rng, r, c=None):
    if not isinstance(rng, Aralik):
        rng = Aralik([[rng]])
    r = int(_num(r))
    nr, nc = rng.shape
    if c is None:
        if nr == 1:
            return rng.rows[0][r - 1]
        if r == 0:
            return rng
        return rng.rows[r - 1][0] if nc == 1 else Aralik([rng.rows[r - 1]])
    c = int(_num(c))
    if r == 0 and c == 0:
        return rng
    if r == 0:  # tum sutun
        return Aralik([[row[c - 1]] for row in rng.rows])
    if c == 0:  # tum satir
        return Aralik([rng.rows[r - 1]])
    if r > nr or c > nc or r < 0 or c < 0:
        raise ExcelHata("#REF!")
    return rng.rows[r - 1][c - 1]


def _is_testi(v, test):
    """ISNUMBER/ISERROR...: hata degerini yaymaz, sinar (dizi ise eleman bazinda)."""
    if isinstance(v, Aralik):
        if v.shape == (1, 1):
            return test(v.rows[0][0])
        return Aralik([[test(x) for x in r] for r in v.rows])
    return test(v)


def _f_choose(idx, *secenek):
    """CHOOSE: indeks dizi ise ({1,2}) sonuc yayinlanir -> CHOOSE({1,2},A,B) iki sutunlu dizi."""
    def deger(x, i, j):
        if isinstance(x, Aralik):
            nr, nc = x.shape
            return x.rows[i if nr > 1 else 0][j if nc > 1 else 0]
        return x
    hepsi = [idx] + list(secenek)
    nr = max((x.shape[0] for x in hepsi if isinstance(x, Aralik)), default=1)
    nc = max((x.shape[1] for x in hepsi if isinstance(x, Aralik)), default=1)
    if nr == 1 and nc == 1:
        return _scalar(secenek[int(_num(_scalar(idx))) - 1])
    out = [[deger(secenek[int(_num(deger(idx, i, j))) - 1], i, j) for j in range(nc)] for i in range(nr)]
    return Aralik(out)


def _sira_anahtari(v):
    # Excel artan sira: sayilar < metin < mantiksal; bos en sonda
    if v is None:
        return (3, 0)
    if isinstance(v, bool):
        return (2, int(v))
    if _is_num(v):
        return (0, v)
    return (1, tr_fold(v))


def _f_sortby(arr, *ciftler):
    """SORTBY(dizi; gore1; [sira1]; gore2; ...): satirlar, ayni boydaki ölcüt dizilerine gore."""
    if not isinstance(arr, Aralik):
        return arr
    olcutler = []
    i = 0
    while i < len(ciftler):
        by = ciftler[i]
        sira = _num(ciftler[i + 1]) if i + 1 < len(ciftler) else Decimal(1)
        flat = by.flat if isinstance(by, Aralik) else [by]
        if len(flat) != arr.shape[0]:
            raise ExcelHata("#VALUE!")
        olcutler.append((flat, sira < 0))
        i += 2
    idx = list(range(arr.shape[0]))
    for flat, ters in reversed(olcutler):  # kararli siralama: son olcutten ilke
        idx.sort(key=lambda j: _sira_anahtari(flat[j]), reverse=ters)
    return Aralik([arr.rows[j] for j in idx])


def _f_sort(arr, idx=Decimal(1), sira=Decimal(1), sutuna_gore=False):
    if not isinstance(arr, Aralik):
        return arr
    idx, ters = int(_num(idx)), _num(sira) < 0
    if idx < 1 or idx > (arr.shape[0] if sutuna_gore is True else arr.shape[1]):
        raise ExcelHata("#VALUE!")
    if sutuna_gore is True or (not isinstance(sutuna_gore, bool) and _num(sutuna_gore) != 0):
        cols = [list(c) for c in zip(*arr.rows)]
        cols.sort(key=lambda c: _sira_anahtari(c[idx - 1]), reverse=ters)
        return Aralik([list(r) for r in zip(*cols)])
    return Aralik(sorted((list(r) for r in arr.rows), key=lambda r: _sira_anahtari(r[idx - 1]), reverse=ters))


def _f_xlookup(key, look, ret, if_nf=None, *rest):
    key = _scalar(key)
    if rest and any(_num(x) != 0 for x in rest[:1]):
        raise NotImplementedError("XLOOKUP match_mode")
    lf, rf = look.flat, ret.flat
    for i, v in enumerate(lf):
        if _lookup_eq(v, key):
            return rf[i]
    if if_nf is not None:
        return _scalar(if_nf)
    raise ExcelHata("#N/A")


def _kinci(args, k, buyuk):
    xs = sorted(_nums_in([args]), reverse=buyuk)
    k = int(_num(k))
    if k < 1 or k > len(xs):
        raise ExcelHata("#NUM!")
    return xs[k - 1]


def _avg(xs):
    if not xs:
        raise ExcelHata("#DIV/0!")
    return sum(xs) / len(xs)


def _sumproduct(*arrs):
    flats = [a.flat if isinstance(a, Aralik) else [a] for a in arrs]
    if len({len(f) for f in flats}) != 1:
        raise ExcelHata("#VALUE!")
    tot = Decimal(0)
    for vals in zip(*flats):
        for v in vals:
            if isinstance(v, ExcelHata):
                raise v
        p = Decimal(1)
        for v in vals:
            p *= v if _is_num(v) else Decimal(0)  # metin/bos -> 0 (LO/Excel)
        tot += p
    return tot


def _elementwise(a, b, fn):
    """Aralik op Aralik / Aralik op skaler -> eleman bazli Aralik (tek hucreli
    araliklar skaler sayilir)."""
    def multi(x):
        return isinstance(x, Aralik) and x.shape != (1, 1)
    if not multi(a) and not multi(b):
        return fn(_scalar(a), _scalar(b))
    fn0 = fn

    def fn(x, y):  # dizide hata eleman bazinda kalir (Excel: {1;#DIV/0!;...})
        if isinstance(x, ExcelHata):
            return x
        if isinstance(y, ExcelHata):
            return y
        try:
            return fn0(x, y)
        except ExcelHata as e:
            return e
    if multi(a) and multi(b):
        if a.shape != b.shape:
            # Excel yayinlama: boyutlardan biri 1 ise genisler (n x 1 ile 1 x m -> n x m)
            (na, ma), (nb, mb) = a.shape, b.shape
            if na not in (nb, 1) and nb != 1 or ma not in (mb, 1) and mb != 1:
                raise ExcelHata("#VALUE!")
            n, m = max(na, nb), max(ma, mb)
            return Aralik([[fn(a.rows[i if na > 1 else 0][j if ma > 1 else 0], b.rows[i if nb > 1 else 0][j if mb > 1 else 0])
                            for j in range(m)] for i in range(n)])
        return Aralik([[fn(x, y) for x, y in zip(ra, rb)] for ra, rb in zip(a.rows, b.rows)])
    if multi(a):
        bs = _scalar(b)
        return Aralik([[fn(x, bs) for x in r] for r in a.rows])
    as_ = _scalar(a)
    return Aralik([[fn(as_, y) for y in r] for r in b.rows])


def _f_filter(arr, inc, if_empty=None):
    keep = [bool(v) if isinstance(v, bool) else _num(v) != 0 for v in inc.flat]
    if arr.shape[0] == len(keep):
        rows = [r for r, k in zip(arr.rows, keep) if k]
    elif arr.shape[1] == len(keep):
        rows = [[v for v, k in zip(r, keep) if k] for r in arr.rows]
        rows = rows if rows and rows[0] else []
    else:
        raise ExcelHata("#VALUE!")
    if not rows:
        if if_empty is not None:
            return _scalar(if_empty)
        raise ExcelHata("#CALC!")
    return Aralik(rows)


def _f_unique(arr, sutun=False, tek=False):
    """UNIQUE: satirlari (Excel'deki gibi buyuk/kucuk harf duyarsiz) ilk gorulme sirasiyla tekillestirir."""
    if not isinstance(arr, Aralik):
        return arr
    if _bool(sutun):
        raise NotImplementedError("UNIQUE by_col")
    anahtar = lambda r: tuple(tr_fold(v) if isinstance(v, str) else v for v in r)
    say = {}
    for r in arr.rows:
        say[anahtar(r)] = say.get(anahtar(r), 0) + 1
    out, gor = [], set()
    for r in arr.rows:
        k = anahtar(r)
        if k in gor or (_bool(tek) and say[k] > 1):
            continue
        gor.add(k)
        out.append(list(r))
    if not out:
        raise ExcelHata("#CALC!")
    return Aralik(out)


def _f_median(xs):
    if not xs:
        raise ExcelHata("#NUM!")
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _f_stack(diziler, yatay):
    """HSTACK/VSTACK: kisa kalan dizi #N/A ile doldurulur (Excel 365 gibi)."""
    ds = [d.rows if isinstance(d, Aralik) else [[d]] for d in diziler]
    if yatay:
        n = max(len(d) for d in ds)
        return Aralik([sum((list(d[i]) if i < len(d) else [ExcelHata("#N/A")] * len(d[0]) for d in ds), [])
                       for i in range(n)])
    m = max(len(d[0]) for d in ds)
    return Aralik([list(r) + [ExcelHata("#N/A")] * (m - len(r)) for d in ds for r in d])


def _f_take(arr, r=None, c=None):
    if not isinstance(arr, Aralik):
        arr = Aralik([[arr]])
    rows = arr.rows
    if r is not None:
        r = int(_num(r))
        rows = rows[:r] if r >= 0 else rows[r:]
    if c is not None:
        c = int(_num(c))
        rows = [x[:c] if c >= 0 else x[c:] for x in rows]
    if not rows or not rows[0]:
        raise ExcelHata("#CALC!")
    return Aralik([list(x) for x in rows])


def _bool(v):
    v = _scalar(v) if isinstance(v, Aralik) else v
    if isinstance(v, ExcelHata):
        raise v
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    if _is_num(v):
        return v != 0
    raise ExcelHata("#VALUE!")


def _bools_in(args):
    """AND/OR: araliktaki/dizideki tum mantiksal ve sayisal degerler (metin/bos atlanir)."""
    out = []
    for a in args:
        if isinstance(a, Aralik):
            for v in a.flat:
                if isinstance(v, ExcelHata):
                    raise v
                if isinstance(v, bool) or _is_num(v):
                    out.append(v)
        else:
            out.append(a)
    return out


def _sel(rng, mask):
    return [v for v, ok in zip(rng.flat, mask) if ok and _is_num(v)]


def _vec(fn, crit_idx):
    """*IF/*IFS: kriter argumani cok hucreli bir aralik/dizi ise (ör.
    SUMIFS(C:C, A:A, Sayfa!A2:A13)) Excel 365 her kriter hucresi icin ayri sonuc
    dondurur -> Aralik."""
    def wrap(*args):
        idx = [i for i in crit_idx(len(args)) if isinstance(args[i], Aralik) and args[i].shape != (1, 1)]
        if not idx:
            return fn(*args)
        shape = args[idx[0]].shape
        out = []
        # ayni kriter degeri bir kez hesaplanir: B2:B100000 gibi tablonun cok otesine
        # uzanan kriter dizisinde ~100k bos hucre tek sonuca iner (yoksa n^2, saatler)
        onbellek = {}
        for ri in range(shape[0]):
            row = []
            for ci in range(shape[1]):
                a = list(args)
                for i in idx:
                    a[i] = args[i].rows[ri][ci]
                anahtar = tuple((type(a[i]), a[i]) for i in idx)  # tip: TRUE ile 1 karismasin
                if anahtar not in onbellek:
                    try:
                        onbellek[anahtar] = fn(*a)
                    except ExcelHata as e:
                        onbellek[anahtar] = e
                row.append(onbellek[anahtar])
            out.append(row)
        return Aralik(out)
    return wrap


_ODD = lambda n: range(1, n, 2)    # COUNTIFS: (aralik, kriter) ciftleri
_EVEN = lambda n: range(2, n, 2)   # SUMIFS/AVERAGEIFS/MAXIFS: ilk arg toplam araligi
_ONE = lambda n: [1]
_ZERO = lambda n: [0]

_FUNCS = {
    "SUM": lambda *a: sum(_nums_in(a), Decimal(0)),
    "AVERAGE": lambda *a: _avg(_nums_in(a)),
    "MIN": lambda *a: min(_nums_in(a), default=Decimal(0)),
    "MAX": lambda *a: max(_nums_in(a), default=Decimal(0)),
    "COUNT": lambda *a: Decimal(len(_nums_in(a))),
    "COUNTA": lambda *a: Decimal(sum(1 for x in a for v in (x.flat if isinstance(x, Aralik) else [x]) if v not in (None, ""))),
    "ABS": lambda x: abs(_num(x)),
    "ROUND": lambda x, n=Decimal(0): excel_round(_num(x), int(_num(n))),
    "SUMPRODUCT": _sumproduct,
    "COUNTIF": _vec(lambda r, c: Decimal(sum(_ifs_mask([(r, c)]))), _ONE),
    "SUMIF": _vec(lambda r, c, s=None: sum(_sel(s or r, _ifs_mask([(r, c)])), Decimal(0)), _ONE),
    "AVERAGEIF": _vec(lambda r, c, s=None: _avg(_sel(s or r, _ifs_mask([(r, c)]))), _ONE),
    "COUNTIFS": _vec(lambda *a: Decimal(sum(_ifs_mask(list(zip(a[0::2], a[1::2]))))), _ODD),
    "SUMIFS": _vec(lambda s, *a: sum(_sel(s, _ifs_mask(list(zip(a[0::2], a[1::2])))), Decimal(0)), _EVEN),
    "AVERAGEIFS": _vec(lambda s, *a: _avg(_sel(s, _ifs_mask(list(zip(a[0::2], a[1::2]))))), _EVEN),
    "MAXIFS": _vec(lambda s, *a: max(_sel(s, _ifs_mask(list(zip(a[0::2], a[1::2])))), default=Decimal(0)), _EVEN),
    "MINIFS": _vec(lambda s, *a: min(_sel(s, _ifs_mask(list(zip(a[0::2], a[1::2])))), default=Decimal(0)), _EVEN),
    # Excel 365: arama degeri dizi ise sonuc da dizi (ör. VLOOKUP(A2:A13, ...))
    "VLOOKUP": _vec(_f_vlookup, _ZERO),
    "MATCH": _vec(_f_match, _ZERO),
    "INDEX": _vec(_f_index, _ONE),  # Excel 365: satir argumani dizi ise dizi doner
    "LARGE": lambda a, k: _kinci(a, k, True),
    "SMALL": lambda a, k: _kinci(a, k, False),
    "XLOOKUP": _vec(_f_xlookup, _ZERO),
    "FILTER": _f_filter,
    "CHOOSE": _f_choose,
    "SORT": _f_sort,
    "SORTBY": _f_sortby,
    "ISNUMBER": lambda v: _is_testi(v, _is_num),
    "ISTEXT": lambda v: _is_testi(v, lambda x: isinstance(x, str)),
    "ISERROR": lambda v: _is_testi(v, lambda x: isinstance(x, ExcelHata)),
    "ISNA": lambda v: _is_testi(v, lambda x: isinstance(x, ExcelHata) and x.kod == "#N/A"),
    "UNIQUE": lambda a, sutun=False, tek=False: _f_unique(a, sutun, tek),
    "MEDIAN": lambda *a: _f_median(_nums_in(a)),
    "SEQUENCE": lambda r, c=Decimal(1), s=Decimal(1), k=Decimal(1): Aralik(
        [[_num(s) + (i * int(_num(c)) + j) * _num(k) for j in range(int(_num(c)))] for i in range(int(_num(r)))]),
    "AND": lambda *a: all(_bool(v) for v in _bools_in(a)),
    "OR": lambda *a: any(_bool(v) for v in _bools_in(a)),
    "NOT": lambda v: _elementwise(v, None, lambda x, _: not _bool(x)),
    "TAKE": lambda a, r=None, c=None: _f_take(a, r, c),
    "ROW": lambda a: _f_row(a),
    "MMULT": lambda a, b: _f_mmult(a, b),
    "TRANSPOSE": lambda a: Aralik([list(r) for r in zip(*(a.rows if isinstance(a, Aralik) else [[a]]))]),
    "HSTACK": lambda *a: _f_stack(a, True),
    "VSTACK": lambda *a: _f_stack(a, False),
    "ROWS": lambda a: Decimal(a.shape[0] if isinstance(a, Aralik) else 1),
    "COLUMNS": lambda a: Decimal(a.shape[1] if isinstance(a, Aralik) else 1),
}


class _Lambda:
    def __init__(self, params, bas, son, env):
        self.params, self.bas, self.son, self.env = params, bas, son, env


class Calisma:
    """Cok sayfali calisma kitabi. sheets: {sayfa_adi: [[A1, B1, ...], [A2, ...], ...]}
    (satir 1 = baslik). Hucre degerleri int/float/str/None; sayilar Decimal'e cevrilir."""

    def __init__(self, sheets: dict, varsayilan: str | None = None):
        self.sheets = {}
        for ad, rows in sheets.items():
            self.sheets[ad] = [[self._norm(v) for v in r] for r in rows]
        self.varsayilan = varsayilan or next(iter(sheets))

    @staticmethod
    def _norm(v):
        if v is None or isinstance(v, str):
            return v
        return to_dec(v)

    def sayfa(self, ad: str) -> str:
        """Sayfa adini kanonik ada cozer (Excel sayfa adlari harf duyarsizdir)."""
        if ad in self.sheets:
            return ad
        for k in self.sheets:
            if tr_fold(k) == tr_fold(ad):
                return k
        for k in self.sheets:  # "Iller" / "ILCELER" gibi noktasiz yazimlar
            if ascii_fold(k) == ascii_fold(ad):
                return k
        raise ExcelHata("#REF!")

    def _get(self, sheet, c, r):
        rows = self.sheets[sheet]
        if r - 1 < len(rows) and c - 1 < len(rows[r - 1]):
            return rows[r - 1][c - 1]
        return None

    def _ref(self, tok):
        if "!" in tok:
            sh, addr = tok.rsplit("!", 1)
            if sh.startswith("'"):
                sh = sh[1:-1].replace("''", "'")
        else:
            sh, addr = self.varsayilan, tok
        sh = self.sayfa(sh)
        if ":" in addr and not any(ch.isdigit() for ch in addr):
            c1, c2 = (col_to_idx(x.replace("$", "")) for x in addr.split(":"))
            n = len(self.sheets[sh])
            return Aralik([[self._get(sh, c, r) for c in range(c1, c2 + 1)] for r in range(1, n + 1)], r0=1)
        if ":" in addr:
            a, b = addr.split(":")
            (c1, r1), (c2, r2) = parse_cell(a), parse_cell(b)
            return Aralik([[self._get(sh, c, r) for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)], r0=r1)
        c, r = parse_cell(addr)
        return Aralik([[self._get(sh, c, r)]], r0=r)

    # --- recursive descent: karsilastirma < & < +- < */ < ^ < unary < %
    def hesapla(self, formul: str, yuvarlama=None):
        if yuvarlama is not None:
            onceki = getattr(_YUV, "kural", None)
            _YUV.kural = yuvarlama
            try:
                return self.hesapla(formul)
            finally:
                _YUV.kural = onceki
        s = formul.strip()
        if s.startswith("="):
            s = s[1:]
        self._t, self._i = tokenize(s), 0
        v = self._expr()
        if self._i != len(self._t):
            raise SyntaxError(f"fazla token: {self._t[self._i:]}")
        v = _scalar(v)
        return Decimal(0) if v is None else v

    def _peek(self):
        return self._t[self._i] if self._i < len(self._t) else (None, None)

    def _eat(self, val=None):
        k, v = self._peek()
        if val is not None and v != val:
            raise SyntaxError(f"beklenen {val}, gelen {v}")
        self._i += 1
        return k, v

    def _expr(self):
        a = self._concat()
        while self._peek()[1] in ("=", "<>", "<", ">", "<=", ">="):
            op = self._eat()[1]
            a = _elementwise(a, self._concat(), lambda x, y, op=op: _cmp(x, y, op))
        return a

    def _concat(self):
        a = self._add()
        while self._peek()[1] == "&":
            self._eat()
            b = self._add()
            a = _elementwise(a, b, lambda x, y: _txt(x) + _txt(y))  # Excel 365: ">="&A2:A9 dizi verir
        return a

    def _add(self):
        a = self._mul()
        while self._peek()[1] in ("+", "-"):
            op = self._eat()[1]
            b = self._mul()
            a = _elementwise(a, b, (lambda x, y: _num(x) + _num(y)) if op == "+" else (lambda x, y: _num(x) - _num(y)))
        return a

    def _mul(self):
        a = self._pow()
        while self._peek()[1] in ("*", "/"):
            op = self._eat()[1]
            a = _elementwise(a, self._pow(), _carp if op == "*" else _bol)
        return a

    def _pow(self):
        a = self._unary()
        while self._peek()[1] == "^":
            self._eat()
            a = _num(a) ** _num(self._unary())
        return a

    def _unary(self):
        if self._peek()[1] in ("-", "+"):
            op = self._eat()[1]
            v = self._unary()
            return _elementwise(v, Decimal(0), (lambda x, _: -_num(x)) if op == "-" else (lambda x, _: _num(x)))
        v = self._atom()
        while self._peek()[1] == "%":
            self._eat()
            v = _num(v) / 100
        return v

    def _atom(self):
        k, v = self._eat()
        if k == "num":
            return Decimal(v)
        if k == "str":
            return v[1:-1].replace('""', '"')
        if k == "bool":
            return v == "TRUE"
        if k == "ref":
            return self._ref(v)
        if v == "(":
            x = self._expr()
            self._eat(")")
            return x
        if k == "func":
            return self._call(v.upper())
        if k == "name":
            for kapsam in reversed(getattr(self, "_let", [])):
                if v.upper() in kapsam:
                    return kapsam[v.upper()]
            raise ExcelHata("#NAME?")
        if v == "{":  # dizi sabiti: "," sutun, ";" satir ayraci
            rows, row = [], []
            while True:
                isaret = 1
                while self._peek()[1] in ("-", "+"):
                    isaret *= -1 if self._eat()[1] == "-" else 1
                kk, vv = self._eat()
                if kk == "num":
                    row.append(Decimal(vv) * isaret)
                elif kk == "str":
                    row.append(vv[1:-1].replace('""', '"'))
                elif kk == "bool":
                    row.append(vv == "TRUE")
                else:
                    raise SyntaxError(f"dizi sabitinde {vv}")
                ayr = self._eat()[1]
                if ayr == "}":
                    rows.append(row)
                    break
                if ayr == ";":
                    rows.append(row)
                    row = []
                elif ayr != ",":
                    raise SyntaxError(f"dizi sabitinde {ayr}")
            if len({len(r) for r in rows}) != 1:
                raise SyntaxError("dizi sabiti duzensiz")
            return Aralik(rows)
        raise SyntaxError(f"beklenmeyen {v}")

    def _lambda_uygula(self, lam, args):
        """LAMBDA govdesini (token araligi) verilen argumanlarla yeniden degerlendirir."""
        if not isinstance(lam, _Lambda):
            raise ExcelHata("#VALUE!")
        if len(args) != len(lam.params):
            raise ExcelHata("#VALUE!")
        eski_i, eski_let = self._i, getattr(self, "_let", [])
        self._let = lam.env + [dict(zip(lam.params, args))]
        self._i = lam.bas
        try:
            v = self._expr()
            if self._i != lam.son:
                raise SyntaxError("LAMBDA govdesi")
            return v
        finally:
            self._i, self._let = eski_i, eski_let

    def _call(self, name):
        if name == "LAMBDA":  # LAMBDA(p1; p2; govde): govde degerlendirilmeden atlanir, kapanis doner
            self._eat("(")
            params = []
            while True:
                k, v = self._peek()
                nxt = self._t[self._i + 1][1] if self._i + 1 < len(self._t) else None
                if k in ("name", "ref") and nxt in (",", ";"):
                    params.append(v.upper())
                    self._i += 2
                    continue
                break
            bas, derinlik = self._i, 0
            while self._i < len(self._t):
                tv = self._t[self._i][1]
                if tv in ("(", "{"):
                    derinlik += 1
                elif tv in (")", "}"):
                    if derinlik == 0:
                        break
                    derinlik -= 1
                self._i += 1
            son = self._i
            self._eat(")")
            return _Lambda(params, bas, son, list(getattr(self, "_let", [])))
        if name in ("BYROW", "BYCOL", "MAP"):
            self._eat("(")
            args = [self._expr()]
            while self._peek()[1] in (",", ";"):
                self._eat()
                args.append(self._expr())
            self._eat(")")
            lam, diziler = args[-1], args[:-1]

            def tek(*a):
                try:
                    return _scalar(self._lambda_uygula(lam, list(a)))
                except ExcelHata as e:
                    return e
            x = diziler[0]
            if not isinstance(x, Aralik):
                x = Aralik([[x]])
            if name == "BYROW":
                return Aralik([[tek(Aralik([list(r)]))] for r in x.rows])
            if name == "BYCOL":
                return Aralik([[tek(Aralik([[r[j]] for r in x.rows])) for j in range(x.shape[1])]])
            ds = [d if isinstance(d, Aralik) else Aralik([[d]]) for d in diziler]
            return Aralik([[tek(*[d.rows[i][j] if d.shape != (1, 1) else d.rows[0][0] for d in ds])
                            for j in range(x.shape[1])] for i in range(x.shape[0])])
        if name == "LET":  # LET(ad1; deger1; ...; hesap): degerler sirayla baglanir
            self._eat("(")
            if not hasattr(self, "_let"):
                self._let = []
            self._let.append({})
            try:
                while True:
                    k, v = self._peek()
                    nxt = self._t[self._i + 1][1] if self._i + 1 < len(self._t) else None
                    if k == "name" and nxt in (",", ";"):
                        self._eat()
                        self._eat()
                        self._let[-1][v.upper()] = self._expr()
                        self._eat()  # ayrac
                        continue
                    sonuc = self._expr()
                    self._eat(")")
                    return sonuc
            finally:
                self._let.pop()
        if name not in _FUNCS and name not in ("IF", "IFERROR", "IFNA"):
            raise NotImplementedError(name)  # argumanlari degerlendirmeden: LO'ya dusulsun
        self._eat("(")
        # IF / IFERROR tembel degil ama hata yakalama icin argumanlari tek tek degerlendir
        args = []
        if self._peek()[1] != ")":
            while True:
                if name in ("IFERROR", "IF", "IFNA", "ISNUMBER", "ISTEXT", "ISERROR", "ISNA"):
                    try:
                        args.append(self._expr())
                    except ExcelHata as e:
                        args.append(e)
                else:
                    args.append(self._expr())
                if self._peek()[1] in (",", ";"):
                    self._eat()
                    continue
                break
        self._eat(")")
        if name == "IF":
            c = args[0]
            if isinstance(c, ExcelHata):
                raise c
            def _sec(cv, t, f):
                truthy = cv if isinstance(cv, bool) else _num(cv) != 0
                r = t if truthy else f
                if isinstance(r, ExcelHata):
                    raise r
                return r

            def _sec_dizi(cv, t, f):  # dizide hata eleman bazinda kalir (Excel: {1;#DIV/0!;...})
                if isinstance(cv, ExcelHata):
                    return cv
                try:
                    return _sec(cv, t, f)
                except ExcelHata as e:
                    return e
            f_arg = args[2] if len(args) > 2 else False
            if isinstance(c, Aralik) and c.shape != (1, 1):
                def _pick(x, i, j):
                    return x.rows[i][j] if isinstance(x, Aralik) and x.shape != (1, 1) else (_scalar(x) if isinstance(x, Aralik) else x)
                return Aralik([[_sec_dizi(cv, _pick(args[1], i, j), _pick(f_arg, i, j)) for j, cv in enumerate(r)]
                               for i, r in enumerate(c.rows)])
            return _sec(_scalar(c), args[1], f_arg)
        if name in ("IFERROR", "IFNA"):
            def _yakala(v, yedek):
                if isinstance(v, ExcelHata) and (name == "IFERROR" or v.kod == "#N/A"):
                    return yedek
                return v
            x, y = args[0], args[1]
            if isinstance(x, Aralik) and x.shape != (1, 1):  # Excel 365: dizide eleman bazinda
                def _y(i, j):
                    return y.rows[i][j] if isinstance(y, Aralik) and y.shape == x.shape else (_scalar(y) if isinstance(y, Aralik) else y)
                return Aralik([[_yakala(v, _y(i, j)) for j, v in enumerate(r)] for i, r in enumerate(x.rows)])
            sonuc = _yakala(x, y)
            if isinstance(sonuc, ExcelHata):
                raise sonuc
            return sonuc
        if name not in _FUNCS:
            raise NotImplementedError(name)
        return _FUNCS[name](*args)


def _f_row(a):
    """ROW(aralik): satir numaralari dizisi. Yalniz sayfa araligi (hesaplanmis dizide satir yok)."""
    if not isinstance(a, Aralik) or a.r0 is None:
        raise ExcelHata("#VALUE!")
    n = a.shape[0]
    return Decimal(a.r0) if n == 1 else Aralik([[Decimal(a.r0 + i)] for i in range(n)])


def _f_mmult(a, b):
    a = a if isinstance(a, Aralik) else Aralik([[a]])
    b = b if isinstance(b, Aralik) else Aralik([[b]])
    (n, k), (k2, m) = a.shape, b.shape
    if k != k2:
        raise ExcelHata("#VALUE!")
    A = [[_num(1 if v is True else 0 if v is False else v) for v in r] for r in a.rows]
    B = [[_num(1 if v is True else 0 if v is False else v) for v in r] for r in b.rows]
    out = [[sum((A[i][t] * B[t][j] for t in range(k)), Decimal(0)) for j in range(m)] for i in range(n)]
    return out[0][0] if (n, m) == (1, 1) else Aralik(out)


def _carp(x, y):
    return _num(x) * _num(y)


def _bol(x, y):
    y = _num(y)
    if y == 0:
        raise ExcelHata("#DIV/0!")
    return _num(x) / y


def _txt(v):
    v = _scalar(v)
    if v is None:
        return ""
    if _is_num(v):
        return fmt_excel(v, 15)
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    return str(v)


def sonuc_str(v, max_decimals: int = 3) -> str:
    """Formul sonucunu beklenen_sonuc alanina yazilacak bicime cevirir."""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, Decimal):
        return fmt_excel(v, max_decimals)
    return "" if v is None else str(v)


# ---------------- LibreOffice headless ----------------

# Excel 2010 sonrasi fonksiyonlar .xlsx icinde onekle saklanir; openpyxl onek
# eklemez, LibreOffice oneksiz "MAXIFS"i taniyamaz (#NAME?/#N/A).
_XLFN = {f: "_xlfn." + f for f in ("MAXIFS", "MINIFS", "XLOOKUP", "XMATCH", "IFS", "SWITCH", "CONCAT", "TEXTJOIN",
                                    "IFNA", "UNIQUE", "SORT", "SEQUENCE")}
_XLFN["FILTER"] = "_xlfn._xlws.FILTER"


def _prefix_refs(formul: str, onek: str, varsayilan: str) -> str:
    """Formuldeki sayfa adlarini onek+ad, sayfasiz referanslari onek+varsayilan
    ile niteler (tokenizer uzerinden; tirnakli metinlere dokunulmaz)."""
    out = []
    for kind, tok in tokenize(formul):
        if kind == "ref":
            if "!" in tok:
                sh, addr = tok.rsplit("!", 1)
                sh = sh[1:-1].replace("''", "'") if sh.startswith("'") else sh
            else:
                sh, addr = varsayilan, tok
            tok = "'" + (onek + sh).replace("'", "''") + "'!" + addr
        elif kind == "func" and tok.upper() in _XLFN:
            tok = _XLFN[tok.upper()]
        out.append(tok)
    return "".join(out)


def xlsx_yaz(isler, path, max_decimals: int = 10, dizi: bool = False):
    """isler: [(sheets: {ad: rows}, varsayilan_sayfa, formul), ...]. Her is kendi
    sayfa kopyalarina sahip olur (Q{i}_<ad>); ilk sayfa 'Sonuc'un i. satirinda
    A = sabit basamakli metin sonucu (LO csv icin), B = ham formul."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sonuc"
    for i, (sheets, varsayilan, formul) in enumerate(isler, start=1):
        onek = f"Q{i}_"
        for ad, rows in sheets.items():
            sh = wb.create_sheet(onek + ad)
            assert sh.title == onek + ad, "sayfa adi 31 karakteri asiyor"
            for r in rows:
                sh.append([float(v) if isinstance(v, Decimal) else v for v in r])
        f = _prefix_refs(formul.lstrip("="), onek, varsayilan)
        a = f"=IFERROR(IF(ISNUMBER({f}),FIXED({f},{max_decimals},1),{f}),ERROR.TYPE({f})&\"#ERR\")"
        if dizi:  # dizi (CSE) formulu: Excel 365 dinamik dizi semantigini tek hucrede verir
            from openpyxl.worksheet.formula import ArrayFormula
            ws.cell(row=i, column=1).value = ArrayFormula(f"A{i}", a)
            ws.cell(row=i, column=2).value = ArrayFormula(f"B{i}", f"={f}")
        else:
            ws.cell(row=i, column=1, value=a)
            ws.cell(row=i, column=2, value=f"={f}")
    wb.save(path)


def libreoffice_hesapla(isler, max_decimals: int = 10, timeout: int = 900, dizi: bool = False):
    """Formulleri gercek LibreOffice headless'ta tek soffice cagrisiyla hesaplatir.
    Donus: her is icin LO'nun yazdigi metin -- sayilar max_decimals sabit
    basamakla, hatalar "<ERROR.TYPE>#ERR" (2#ERR = #DIV/0!, 7#ERR = #N/A)."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "is.xlsx"
        xlsx_yaz(isler, p, max_decimals, dizi)
        subprocess.run(
            ["soffice", "--headless", "--calc", "--convert-to",
             'csv:Text - txt - csv (StarCalc):44,34,76,1,,0,false,true,false,false,false',
             str(p), "--outdir", td,
             "-env:UserInstallation=file://" + td + "/profil"],  # ayri profil: acik LO oturumuyla cakismasin
            check=True, timeout=timeout, capture_output=True,
        )
        with open(Path(td) / "is.csv", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
    return [r[0] if r else "" for r in rows] + [""] * (len(isler) - len(rows))


def formulas_hesapla(isler):
    """Ayni calisma kitabini `formulas` paketinin (bagimsiz Python Excel motoru)
    ile hesaplatir. Donus: her is icin ham sonuc (float/str/hata metni)."""
    import formulas

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "is.xlsx"
        xlsx_yaz(isler, p)
        sol = formulas.ExcelModel().loads(str(p)).finish().calculate()
    out = []
    for i in range(1, len(isler) + 1):
        key = next(k for k in sol if k.upper().endswith(f"SONUC'!B{i}"))
        v = sol[key].value[0, 0]
        out.append(v.item() if hasattr(v, "item") else str(v))
    return out


def lo_sonuc_dec(s: str):
    """libreoffice_hesapla ciktisini Decimal'e (sayi ise) cevirir."""
    try:
        return Decimal(s)
    except Exception:
        return s
