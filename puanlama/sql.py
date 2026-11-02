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
