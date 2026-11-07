"""SQL puanlamasi: metinden SQL'e (il/ilce, belediye disi, TURSpider, Cognipeer) ve cikti tahmini.

Karsilastirici sql_arastirma/uretim/bench_belediye_disi.py'deki surumdur (goreli 1e-3 / mutlak 0,011).
benchmark_coz.py'deki eski surumun mutlak 0,5 toleransi kucuk degerlerde gevsekti; burada kullanilmaz.
"""
import json
import re
import sqlite3
import time
from decimal import Decimal, InvalidOperation

from .cognipeer_shim import needs_fetchall, register_shims

SURE_SN = 30  # model SQL'i icin ust sinir; kartezyen birlesimler dakikalarca surebiliyor


# ---------- karsilastirma (bench_belediye_disi.py) ----------

def _ondalik_basamak(x):
    """Altin sayinin yazildigi ondalik basamak (70.7 -> 1, 1213.0 -> 0, 1200.0 -> 0)."""
    if isinstance(x, int):
        return 0
    try:
        return max(0, -Decimal(repr(float(x))).normalize().as_tuple().exponent)
    except (InvalidOperation, ValueError, OverflowError):
        return None


def deger_esit(a, c):
    """a altin, c aday. 2026-10-31: (1) iki tam sayi BIREBIR (eskiden goreli 1e-3: 999 = 1000, tarih-int
    19680831 = 19690101; acgozlu eslesme de bozuluyordu, 19 TURSpider altini kendini reddediyordu);
    (2) ondalikta tolerans altinin yazildigi basamagin yarim biriminden buyuk olamaz (taban 0,011): eskiden
    485418671.76 icin +-485 bin kabul ediliyordu. Yuvarlamamis dogru cevap (70.7123 ~ 70.7) gecer."""
    if a is None or c is None:
        return a is None and c is None
    if isinstance(a, (int, float)) and isinstance(c, (int, float)):
        if isinstance(a, int) and isinstance(c, int):
            return a == c
        d = _ondalik_basamak(a)
        birim = 0.5 * 10 ** -d if d is not None else float("inf")
        buyuk = max(abs(a), abs(c))
        return abs(a - c) <= max(0.011, min(buyuk * 1e-3, birim)) + buyuk * 1e-9
    return str(a) == str(c)


def satir_esit(g, a):
    # indeksle ara: eşleşen değerin kendisi None (NULL) olabilir; next(..., None) onu "bulunamadı" sanıyordu
    kalan = list(a)
    for v in g:
        i = next((j for j, x in enumerate(kalan) if deger_esit(v, x)), -1)
        if i < 0:
            return False
        kalan.pop(i)
    return True


def belirsizlik_toleransli(gold, aday, sira_onemli, ters_altin):
    """Altin, esit degerler yuzunden tarama sirasina bagliysa (ters_altin: ayni altin sorgunun ters taramadaki
    sonucu; ondan farkliysa) iki gecerli sonuc da kabul edilir ve satir sirasi aranmaz. ters_altin
    olusturulamadiysa (None) yalniz siki karsilastirma."""
    if sonuc_eslesiyor(gold, aday, sira_onemli):
        return True
    if ters_altin is None or sonuc_eslesiyor(gold, ters_altin, sira_onemli):
        return False  # altin belirsiz degil
    if len(ters_altin) != len(gold):
        return False  # esit deger belirsizligi satir sayisini degistirmez; degisiyorsa altin bozuk (ör. GROUP BY'siz HAVING)
    return sonuc_eslesiyor(gold, aday, False) or sonuc_eslesiyor(ters_altin, aday, False)


def sonuc_eslesiyor(gold, aday, sira_onemli):
    """Satir sayisi esit; sutun sirasi onemsiz, aday fazladan sutun dondurebilir; satir sirasi yalniz
    sira_onemli ise onemli."""
    if len(gold) != len(aday):
        return False
    if all(satir_esit(g, a) for g, a in zip(gold, aday)):
        return True
    if sira_onemli:
        return False
    kalan = list(aday)
    for g in gold:
        i = next((j for j, a in enumerate(kalan) if satir_esit(g, a)), -1)
        if i < 0:
            return False
        kalan.pop(i)
    return True


def _dis_konumlar(sql):
    """Parantez ve tirnak disindaki SELECT/FROM/ORDER BY/LIMIT/birlesim anahtar sozcukleri: [(sozcuk, bas, son)]."""
    out, derinlik, i, kapanis = [], 0, 0, {"'": "'", '"': '"', "`": "`", "[": "]"}
    anahtar = re.compile(r"\b(SELECT|FROM|ORDER\s+BY|LIMIT|UNION|INTERSECT|EXCEPT)\b", re.I)
    while i < len(sql):
        c = sql[i]
        if c in kapanis:
            j = sql.find(kapanis[c], i + 1)
            if j < 0:
                return out
            i = j + 1
        elif c in "()":
            derinlik += 1 if c == "(" else -1
            i += 1
        else:
            m = anahtar.match(sql, i) if derinlik == 0 else None
            if m:
                out.append((re.sub(r"\s+", " ", m.group(1)).upper(), m.start(), m.end()))
                i = m.end()
            else:
                i += 1
    return out


def _dis_virgul(s):
    """Parantez ve tirnak disindaki virgullerden boler."""
    parca, derinlik, tirnak, bas = [], 0, None, 0
    for i, c in enumerate(s):
        if tirnak:
            tirnak = None if c == tirnak else tirnak
        elif c in "'\"`":
            tirnak = c
        elif c in "()":
            derinlik += 1 if c == "(" else -1
        elif c == "," and derinlik == 0:
            parca.append(s[bas:i])
            bas = i + 1
    return [x.strip() for x in parca + [s[bas:]]]


def limit_gruplari(db_yolu, gold_sql, ekler=None, sure=SURE_SN):
    """Altin en dista ORDER BY ... LIMIT n ise satirlari siralama anahtarina gore gruplar: (gruplar, n). Son grup n. satiri
    icerir ve o anahtardaki tum esit satirlari tasir. Uygulanamazsa None (birlesim, OFFSET, ayristirilamayan altin)."""
    sql = gold_sql.strip().rstrip(";").strip()
    k = _dis_konumlar(sql)
    ad = [x[0] for x in k]
    if any(a in ad for a in ("UNION", "INTERSECT", "EXCEPT")) or ad.count("SELECT") != 1 or ad[0] != "SELECT" \
            or not {"FROM", "ORDER BY", "LIMIT"} <= set(ad):
        return None
    sel, frm, ord_, lim = (next(x for x in k if x[0] == a) for a in ("SELECT", "FROM", "ORDER BY", "LIMIT"))
    m = re.fullmatch(r"\s*(\d+)\s*", sql[lim[2]:])
    if not m or not frm[1] < ord_[1] < lim[1]:
        return None
    n = int(m.group(1))
    secim = sql[sel[2]:frm[1]].strip()
    takma = {}
    for s in _dis_virgul(re.sub(r"^DISTINCT\b", "", secim, flags=re.I).strip()):
        a = re.fullmatch(r"(.+?)\s+AS\s+[\"`\[]?([^\s\"`\]]+)[\"`\]]?", s, re.I | re.S)
        if a:
            takma[a.group(2).lower()] = a.group(1)
    sutunlar = _dis_virgul(re.sub(r"^DISTINCT\b", "", secim, flags=re.I).strip())
    anahtarlar = []
    for s in _dis_virgul(sql[ord_[2]:lim[1]]):
        s = re.sub(r"\s+(ASC|DESC)\s*$", "", s, flags=re.I).strip()
        if re.fullmatch(r"\d+", s):
            if int(s) > len(sutunlar):
                return None
            s = re.sub(r"\s+AS\s+\S+$", "", sutunlar[int(s) - 1], flags=re.I)
        anahtarlar.append(takma.get(s.strip('"`[]').lower(), s))
    ekli = ", ".join(f"({x}) AS __k{i}" for i, x in enumerate(anahtarlar))
    sorgu = f"{sql[:frm[1]].rstrip()}, {ekli} {sql[frm[1]:lim[1]].rstrip()}"
    con = sqlite3.connect(f"file:{db_yolu}?mode=ro", uri=True)
    try:
        for a, yol in (ekler or {}).items():
            con.execute(f"ATTACH DATABASE 'file:{yol}?mode=ro' AS {a}")
        _sinirli(con, sure)
        cur = con.execute(sorgu)
        m_ = len(anahtarlar)
        gruplar, son, sayi, gorulen, tekil = [], object(), 0, set(), bool(re.match(r"DISTINCT\b", secim, re.I))
        for r in cur:
            satir, an = list(r[:-m_]), tuple(r[-m_:])
            if tekil:
                if repr(satir) in gorulen:
                    continue
                gorulen.add(repr(satir))
            if an != son:
                if sayi >= n:
                    break
                gruplar.append([])
                son = an
            gruplar[-1].append(satir)
            sayi += 1
    except Exception:
        return None
    finally:
        con.close()
    return (gruplar, n) if sayi >= n and n > 0 else None


def limit_esitlik_kabul(gold, aday, sira_onemli, g):
    """2026-11-05: altin ORDER BY ... LIMIT n ve n. satirda esit deger varsa altin tek degildir. Kabul: anahtari kesin olan
    satirlarin hepsi + esit gruptan kalan sayida herhangi satir, ya da esit grubun tamami. sira_onemli ise anahtar gruplari
    sirasiyla gelmeli (grup ici sira serbest). g: limit_gruplari sonucu."""
    if g is None:
        return False
    gruplar, n = g
    if not sonuc_eslesiyor(gold, [x for gr in gruplar for x in gr][:n], False):
        return False  # altin bu ayristirmayla yeniden uretilemedi
    onceki = sum(map(len, gruplar[:-1]))
    if len(aday) not in (n, onceki + len(gruplar[-1])):
        return False
    kalan, adet = list(aday), [len(x) for x in gruplar[:-1]] + [len(aday) - onceki]
    if sira_onemli:
        for gr, k in zip(gruplar, adet):
            havuz = list(gr)
            for a in kalan[:k]:
                i = next((j for j, x in enumerate(havuz) if satir_esit(x, a)), -1)
                if i < 0:
                    return False
                havuz.pop(i)
            kalan = kalan[k:]
        return True
    for gr, k in zip(gruplar[:-1], adet[:-1]):
        for x in gr:
            i = next((j for j, a in enumerate(kalan) if satir_esit(x, a)), -1)
            if i < 0:
                return False
            kalan.pop(i)
    havuz = list(gruplar[-1])
    for a in kalan:
        i = next((j for j, x in enumerate(havuz) if satir_esit(x, a)), -1)
        if i < 0:
            return False
        havuz.pop(i)
    return True


def dis_order_by(sql):
    """En distaki sorguda ORDER BY var mi (alt sorgulardakiler sayilmaz)."""
    derinlik = 0
    for m in re.finditer(r"[()]|\bORDER\s+BY\b", sql, re.I):
        if m.group() == "(":
            derinlik += 1
        elif m.group() == ")":
            derinlik -= 1
        elif derinlik == 0:
            return True
    return False


def bool_al(v):
    return v if isinstance(v, bool) else str(v).strip().lower() == "true"


# ---------- model cevabindan SQL (benchmark_coz.extract_sql) ----------

def sql_al(metin):
    m = re.findall(r"```(?:sql|sqlite)?\s*(.*?)```", metin or "", re.S | re.I)
    if m:
        return m[-1].strip()
    # kapanis ``` gelmeden kesilmis olabilir (max_tokens asimi) - acilis isaretini temizle
    metin = re.sub(r"^```(?:sql|sqlite)?\s*", "", (metin or "").strip(), flags=re.I)
    m = re.search(r"^[\s*_]*CEVAP\s*:\s*(.+)", metin, re.I | re.S | re.M)
    return (m.group(1) if m else metin).strip()


def _sinirli(con, sure):
    bitis = time.monotonic() + sure
    con.set_progress_handler(lambda: 1 if time.monotonic() > bitis else 0, 10_000)


def calistir(db_yolu, sql, ekler=None, sure=SURE_SN, ters=False):
    """Salt okunur baglantida calistirir; ekler {ad: yol} ATTACH edilir. Hata/sure asiminda istisna.
    ters=True: PRAGMA reverse_unordered_selects (esit degerlerde sonuc taramaya bagli mi sinamasi)."""
    con = sqlite3.connect(f"file:{db_yolu}?mode=ro", uri=True)
    try:
        for ad, yol in (ekler or {}).items():
            con.execute(f"ATTACH DATABASE 'file:{yol}?mode=ro' AS {ad}")
        if ters:
            con.execute("PRAGMA reverse_unordered_selects=ON")
        _sinirli(con, sure)
        return [list(r) for r in con.execute(sql).fetchall()]
    finally:
        con.close()


# ---------- sema metni (bench_belediye_disi.sema_metni) ----------

ATLA_SUTUN = {"ilce_adi", "koy_adi", "mahalle_adi", "yer_adi", "ulke_adi", "deprem_id", "tarih", "saat", "koy_id",
              "mahalle_id", "yer_id", "dataset", "baslik", "url", "lisans", "tablo"}


def sema_metni(db_yolu, onek=""):
    """CREATE TABLE'lar; <=120 satirlik tablolarin tum satirlari; digerlerinde <=120 farkli degerli metin
    sutunlarinin birebir deger listesi."""
    con = sqlite3.connect(f"file:{db_yolu}?mode=ro", uri=True)
    parcalar = []
    tablolar = con.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE '\\_%' ESCAPE '\\'").fetchall()
    for ad, sql in tablolar:
        parcalar.append(sql.replace(f"CREATE TABLE {ad}", f"CREATE TABLE {onek}{ad}", 1) + ";")
        kolonlar = [r[1] for r in con.execute(f'PRAGMA table_info("{ad}")')]
        if con.execute(f'SELECT COUNT(*) FROM "{ad}"').fetchone()[0] <= 120:
            # küçük sözlük tablosu: satır satır ver (sütun başına ayrı liste kod↔ad eşleşmesini bozuyordu)
            satirlar = con.execute(f'SELECT * FROM "{ad}"').fetchall()
            parcalar.append(f"-- {onek}{ad} TÜM satırları ({', '.join(kolonlar)}):")
            parcalar += ["--   " + " | ".join("NULL" if v is None else str(v) for v in r) for r in satirlar]
            continue
        for _, kol, tip, *_ in con.execute(f'PRAGMA table_info("{ad}")'):
            if (tip or "").upper() != "TEXT" or kol in ATLA_SUTUN:
                continue
            degerler = [r[0] for r in con.execute(f'SELECT DISTINCT "{kol}" FROM "{ad}" WHERE "{kol}" IS NOT NULL ORDER BY 1 LIMIT 121')]
            if len(degerler) <= 120:
                parcalar.append(f"-- {onek}{ad}.{kol} değerleri (birebir yazım): " + " | ".join(map(str, degerler)))
    con.close()
    return "\n".join(parcalar)


# ---------- Cognipeer: gomulu baglam ----------

def _durum(con):
    out = {}
    for ad, in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') "
                           "AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        cur = con.execute(f'SELECT * FROM "{ad}"')
        out[ad.lower()] = ([d[0].lower() for d in cur.description], sorted(map(repr, cur.fetchall())))
    return out


def _baglamda(baglam, sql, sure, ters=False):
    con = sqlite3.connect(":memory:")
    register_shims(con)
    try:
        con.executescript(baglam)
        if ters:
            con.execute("PRAGMA reverse_unordered_selects=ON")
        _sinirli(con, sure)
        cur = con.execute(sql)
        sonuc = [list(r) for r in cur.fetchall()] if needs_fetchall(sql) else None
        con.set_progress_handler(None, 0)
        return sonuc, _durum(con)
    finally:
        con.close()


def puanla_cognipeer(o, gold_sql, metin, sure=SURE_SN):
    """Secme gorevi: sonuc karsilastirilir. Durum degistirme (INSERT/UPDATE/DELETE/DDL): gold ve model
    ifadesi ayni baglamin ayri kopyalarinda calistirilir, tum tablo/gorunumlerin son durumu ayni olmali."""
    try:
        sonuc, durum = _baglamda(o["baglam"], sql_al(metin), sure)
    except Exception:
        return False
    if o["gorev"] == "secme":
        if sonuc is None:
            return False
        sira = bool_al(o["sira_onemli"])
        if sonuc_eslesiyor(o["gercek_sonuc"], sonuc, sira):
            return True
        try:
            ters_altin, _ = _baglamda(o["baglam"], gold_sql, sure, ters=True)
        except Exception:
            return False
        return belirsizlik_toleransli(o["gercek_sonuc"], sonuc, sira, ters_altin)
    _, gold_durum = _baglamda(o["baglam"], gold_sql, sure)
    return durum == gold_durum


# ---------- cikti tahmini: modelin JSON tablosu ----------

_BARE_TOKEN_RE = re.compile(r'([\[,])(\s*)([^\[\],"\s][^\[\],]*)')


def _ciplak_degerleri_tirnakla(s):
    """Modeller bazen dizge degerlerini tirnaksiz yaziyor ([[SERDIVAN, 164222]]); sayi/true/false/null
    olmayan ciplak tokenlar tirnaklanir (degisiklik kalmayana kadar)."""
    def repl(m):
        delim, ws, tok = m.group(1), m.group(2), m.group(3)
        t = tok.strip()
        if re.fullmatch(r"-?\d+(\.\d+)?", t) or t.lower() in ("true", "false", "null"):
            return f"{delim}{ws}{t}"
        return f'{delim}{ws}"{t.replace(chr(34), chr(92) + chr(34))}"'
    prev = None
    while prev != s:
        prev = s
        s = _BARE_TOKEN_RE.sub(repl, s)
    return s


def _parse_json_cikti(text):  # exec_tahmin.parse_json_cikti
    m = re.search(r"\[\s*\[.*?\]\s*\]|\[\s*\]", text, re.S)
    if not m:
        raise ValueError("JSON dizisi bulunamadı")
    ham = m.group(0)
    try:
        return json.loads(ham)
    except json.JSONDecodeError:
        return json.loads(_ciplak_degerleri_tirnakla(ham))


def tablo_ayristir(metin):
    """olc_hesapsiz_yuzde10_batch.ayristir (gevsek surum): kacisli tirnak (\\") ve fazladan dis liste
    ([[[..]]]) tolere edilir; eski ayristirici ilk '[[' den kestigi icin bunlari yanlis sayiyordu
    (2026-10-28: 168 denemenin 8'i). Ek: CEVAP: satiri varsa yalniz ondan sonrasi okunur; adim adim
    cevaplarda ara adimdaki tablo cevap sanilmasin."""
    t = (metin or "").strip().replace('\\"', '"')
    parca = re.split(r"^[\s*_]*CEVAP\s*:", t, flags=re.I | re.M)
    if len(parca) > 1:
        t = parca[-1]
    m = re.search(r"\[.*\]", t, re.S)
    if m:
        try:
            v = json.loads(m.group(0))
            while isinstance(v, list) and len(v) == 1 and isinstance(v[0], list) and v[0] and all(isinstance(x, list) for x in v[0]):
                v = v[0]
            if isinstance(v, list) and all(isinstance(x, list) for x in v):
                return v
        except json.JSONDecodeError:
            pass
    return _parse_json_cikti(t)


# ---------- cikti tahmini: gosterilen tablolardan altin sorgunun ters taramadaki sonucu ----------

def _hucre(x):
    x = x.strip()
    if x in ("NULL", "None", ""):
        return None
    if re.fullmatch(r"-?\d+", x):
        return int(x)
    if re.fullmatch(r"-?\d+\.\d+(?:e[-+]?\d+)?", x):
        return float(x)
    return x


def tablodan_ters_sonuc(tablo_metni, sql, sure=SURE_SN):
    """Markdown tablo dokumunu bellekte SQLite'a yukler, altin sorguyu ters taramayla calistirir. Dokumde
    sorgunun her tablosu yoksa (ör. onceden suzulmus tesisler) None."""
    try:
        con = sqlite3.connect(":memory:")
        for blok in re.split(r"^### Tablo: ", tablo_metni, flags=re.M)[1:]:
            satirlar = blok.strip().split("\n")
            ad = satirlar[0].split("(")[0].strip()
            kolonlar = [k.strip() for k in satirlar[1].strip().strip("|").split("|")]
            con.execute(f'CREATE TABLE "{ad}" ({", ".join(chr(34) + k + chr(34) for k in kolonlar)})')
            veri = [[_hucre(v) for v in s.strip()[1:-1].split("|")] for s in satirlar[3:] if s.startswith("|")]
            con.executemany(f'INSERT INTO "{ad}" VALUES ({", ".join("?" * len(kolonlar))})', veri)
        con.execute("PRAGMA reverse_unordered_selects=ON")
        _sinirli(con, sure)
        return [list(r) for r in con.execute(sql).fetchall()]
    except Exception:
        return None
