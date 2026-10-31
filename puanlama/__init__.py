"""Doğrulanabilir Türkçe soru veri seti: istem kurma ve puanlama.

    from puanlama import istem, puanla, orijinal   # paket satiri ya da Hugging Face satiri
    metin = model(istem(satir))          # satir: veri/*.jsonl'dan bir kayit (dict)
    dogru = puanla(satir, metin)         # True / False; Excel'de sure asiminda None

Her kategori, olcumlerde kullanilan istemi ve puanlayiciyi kullanir (ayrinti: KULLANIM.md).
Veritabani klasoru varsayilan olarak paketin `veritabanlari/`'i; VD_VERITABANLARI ile degistirilir.
"""
import json
import multiprocessing as mp
import os
import queue
import signal
import sys
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

from . import meb, solver, sql

PAKET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent / "_hesaplama"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "_bulmaca"))

import bulmaca_scoring  # noqa: E402
from grade import grade  # noqa: E402

EXCEL_SURE_SN = 60
SQL_METIN_KATEGORI = {"sql_il_ilce", "sql_belediye_disi", "sql_turspider"}


def vt_klasoru():
    return Path(os.environ.get("VD_VERITABANLARI", PAKET / "veritabanlari"))


@lru_cache(maxsize=1)
def _dilim_tablolari():
    return json.load(open(PAKET / "veri" / "sql_cikti_tahmini_tablolar.json", encoding="utf-8"))


def _ekler(o):
    e = o.get("ekler") or {}
    return {ad: str(vt_klasoru() / yol) for ad, yol in e.items()}


# ---------------- istemler ----------------

STEP_BY_STEP_PROMPT = (
    "Aşağıdaki soruyu adım adım çöz. Açıklamandan SONRA, en son satırda tam olarak "
    "şu biçimde bitir: \"CEVAP: <senin nihai cevabın>\" (birim varsa cevaba dahil et).\n\n{soru}"
)
JSON_PROMPT = (
    "İstenen JSON çıktısının alan adları ve yapısı AŞAĞIDAKİ İSKELETLE BİREBİR AYNI olmalı "
    "(değerleri metindeki gerçek bilgiyle doldur, iskeletteki <...> yer tutucularını değiştir):\n"
    "{iskelet}\n\nGörev: {soru}\n\nSADECE bu yapıya uygun JSON çıktısını ver, açıklama/markdown kod bloğu ekleme."
)
XML_PROMPT = (
    "İstenen XML çıktısının etiket adları ve yapısı AŞAĞIDAKİ İSKELETLE BİREBİR AYNI olmalı "
    "(değerleri metindeki gerçek bilgiyle doldur, iskeletteki <!--...--> yer tutucularını değiştir):\n"
    "{iskelet}\n\nGörev: {soru}\n\nSADECE bu yapıya uygun XML çıktısını ver, açıklama/markdown kod bloğu ekleme."
)
EXCEL_DB_PROMPT = (
    "Aşağıdaki soruyu adım adım çöz. Açıklamandan SONRA, en son satırda tam olarak şu biçimde bitir: "
    "\"CEVAP: =<formül>\" (yalnız formülü yaz, hesaplanmış sonucu değil).\n\n{soru}"
)
SQL_PROMPT = """Aşağıdaki SQLite şemasına göre, verilen Türkçe soruyu cevaplayan SQL
sorgusunu yaz. SADECE SQL yaz, açıklama/markdown kod bloğu ekleme.

Şema:
{sema}

Soru: {soru}

SQL:"""
COGNIPEER_PROMPT = """Aşağıdaki SQLite veritabanı (tablolar ve içerikleri) üzerinde, verilen Türkçe isteği yerine
getiren TEK bir SQL ifadesi yaz (sorgu ya da INSERT/UPDATE/DELETE/CREATE...). SADECE SQL yaz, açıklama ekleme.

Veritabanı:
{baglam}

İstek: {soru}

SQL:"""
TAHMIN_PROMPT = """Aşağıda bir SQLite veritabanının bazı tablolarının TAM içeriği ve bir SQL
sorgusu var. Bu SQL sorgusunu bu veriye GERÇEKTEN uygularsan çıktı ne olur? Kod çalıştırma,
sadece oku ve kafanda hesapla.

{tablolar}

SQL sorgusu:
```sql
{sql}
```

Çıktıyı SATIR SATIR, her satırı bir liste olarak, SADECE şu JSON formatında ver (başka hiçbir
açıklama, markdown yazma):
[[deger1, deger2, ...], [deger1, deger2, ...], ...]
"""


def _skeleton_obj(obj):  # hesaplama/score_deepinfra.py
    if isinstance(obj, dict):
        return {k: _skeleton_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_skeleton_obj(obj[0])] if obj else []
    if isinstance(obj, bool):
        return "<true/false>"
    if isinstance(obj, int):
        return "<tam sayı>"
    if isinstance(obj, float):
        return "<ondalıklı sayı>"
    return "<metin>"


def _skeleton_xml_elem(elem):
    new = ET.Element(elem.tag)
    children = list(elem)
    if children:
        if len(children) > 1 and all(c.tag == children[0].tag for c in children):
            new.append(_skeleton_xml_elem(children[0]))
        else:
            for c in children:
                new.append(_skeleton_xml_elem(c))
    elif elem.text in ("true", "false"):
        new.text = "<true/false>"
    else:
        new.text = "<deger>"
    return new


@lru_cache(maxsize=None)
def _sema(db, ekler_json):
    s = sql.sema_metni(str(vt_klasoru() / db))
    for ad, yol in json.loads(ekler_json).items():
        s += f"\n-- ATTACH '{yol}' AS {ad}\n" + sql.sema_metni(str(vt_klasoru() / yol), onek=f"{ad}.")
    return s


def tablo_metni(o):
    """Cikti tahmini: tablo dokumu satirda ya da (basit grup) dilim_id ile eslik dosyasinda."""
    return o["tablo_metni"] if o.get("tablo_metni") else _dilim_tablolari()[o["dilim_id"]]


SET_KAYNAK = {"bulmaca": "bulmaca", "meb_tek_ders": "korpus", "meb_capraz": "korpus", "hesaplama": "hesaplama",
              "excel_veritabani": "hesaplama", "solver": "solver"}


def _uyarla(satir):
    """Hugging Face satiri (`set`, `meta`) paket satirina (`kaynak`, `orijinal`) cevrilir."""
    if "orijinal" in satir:
        return satir
    return {**satir, "orijinal": satir["meta"], "kaynak": SET_KAYNAK.get(satir["set"], "sql")}


def orijinal(satir):
    """`orijinal` (HF'de `meta`) alani dosyada JSON metni (HF datasets semasi icin); nesne de kabul edilir."""
    o = _uyarla(satir)["orijinal"]
    return json.loads(o) if isinstance(o, str) else o


def istem(satir):
    satir = _uyarla(satir)
    k, o, soru = satir["kategori"], orijinal(satir), satir["soru"]
    if satir["kaynak"] == "bulmaca":
        return bulmaca_scoring.INSTRUCTION + o["prompt"]
    if satir["kaynak"] == "korpus":
        return meb.ISTEM.format(soru=soru)
    if k == "solver":
        return solver.istem(o, soru)
    if k == "json_uretimi":
        iskelet = json.dumps(_skeleton_obj(json.loads(o["cevap"])), ensure_ascii=False, indent=2)
        return JSON_PROMPT.format(iskelet=iskelet, soru=soru)
    if k == "xml_uretimi":
        iskelet = ET.tostring(_skeleton_xml_elem(ET.fromstring(o["cevap"])), encoding="unicode")
        return XML_PROMPT.format(iskelet=iskelet, soru=soru)
    if k == "excel_veritabani":
        return EXCEL_DB_PROMPT.format(soru=soru)
    if satir["kaynak"] == "hesaplama":
        return STEP_BY_STEP_PROMPT.format(soru=soru)
    if k in SQL_METIN_KATEGORI:
        return SQL_PROMPT.format(sema=_sema(o["db"], json.dumps(o.get("ekler") or {}, sort_keys=True)), soru=soru)
    if k == "sql_cognipeer":
        return COGNIPEER_PROMPT.format(baglam=o["baglam"], soru=soru)
    if k == "sql_cikti_tahmini":
        return TAHMIN_PROMPT.format(tablolar=tablo_metni(o), sql=o["sql"])
    raise KeyError(f"bilinmeyen kategori: {k}")


# ---------------- puanlama ----------------

def _grade_cocuk(r, text, q):
    os.setpgrp()  # LibreOffice yedegi de bu gruba girer; sure dolunca grupca oldurulur
    q.put(grade(r, text))


def grade_sinirli(r, text, sure=EXCEL_SURE_SN):
    """hesaplama/score_excel_db_batch.py: her cevap ayri (fork) surecte; bir formul motorda saatlerce
    donebiliyor (B2:B100000, C:C). Sure dolunca surec grubu (soffice dahil) oldurulur, None doner."""
    q = mp.get_context("fork").Queue()
    p = mp.get_context("fork").Process(target=_grade_cocuk, args=(r, text, q))
    p.start()
    try:
        return q.get(timeout=sure)
    except queue.Empty:
        return None
    finally:
        # yalniz p.kill() soffice'i oksuz birakiyordu (2026-10-27: iki soffice 37 dk %100 CPU)
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            p.kill()  # grup henuz kurulmadiysa
        p.join()


def puanla(satir, metin, hakem=None):
    """True/False; Excel kategorilerinde sure asiminda None. hakem yalniz MEB setlerinde kullanilir
    (bkz. meb.puanla). Paket satiri da Hugging Face satiri da verilebilir."""
    satir = _uyarla(satir)
    k, o = satir["kategori"], orijinal(satir)
    if satir["kaynak"] == "bulmaca":
        kesin, _gevsek = bulmaca_scoring.score_record(o, bulmaca_scoring.extract_answer(metin or ""))
        return kesin
    if satir["kaynak"] == "korpus":
        return meb.puanla(satir["soru"], satir["cevap"], metin, hakem=hakem)
    if k == "solver":
        return solver.puanla(o, metin)
    if k in ("excel_formulu", "excel_veritabani"):
        return grade_sinirli(o, metin or "")
    if satir["kaynak"] == "hesaplama":
        return grade(o, metin or "")
    if k in SQL_METIN_KATEGORI:
        try:
            rows = sql.calistir(str(vt_klasoru() / o["db"]), sql.sql_al(metin), _ekler(o))
        except Exception:
            return False
        return sql.sonuc_eslesiyor(o["gercek_sonuc"], rows, sql.bool_al(o.get("sira_onemli", False)))
    if k == "sql_cognipeer":
        return sql.puanla_cognipeer(o, satir["cevap"], metin)
    if k == "sql_cikti_tahmini":
        try:
            tahmin = sql.tablo_ayristir(metin)
        except Exception:
            return False
        return sql.sonuc_eslesiyor(o["gold"], tahmin, sql.dis_order_by(o["sql"]))
    raise KeyError(f"bilinmeyen kategori: {k}")
