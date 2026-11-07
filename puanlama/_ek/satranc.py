"""Satranç seti: istem ve puanlayıcı.

    from puanla import istem, puanla
    dogru = puanla(satir, model_metni)

Son "CEVAP:" satırındaki ilk yasal hamle alınır (SAN, UCI, uzun cebirsel ya da Türkçe harfli SAN) ve
satırın `kabul_uci` kümesinde mi diye bakılır. Mat sorularında bu küme N hamlede zorlayıcı mat yapan tüm ilk
hamlelerdir (uretim sırasında tam hesaplandı); en_iyi_hamle'de Lichess çözümü + anında mat eden hamleler.
"""
import json
import re
import chess

from .satranc_ortak import hamle_ayristir

ISTEM = (
    "Aşağıdaki satranç sorusunu adım adım çöz. Açıklamandan SONRA, en son satırda tam olarak şu biçimde bitir: "
    "\"CEVAP: <hamle>\". Hamleyi İngilizce harflerle standart cebirsel notasyonda (SAN, ör. Nf3, Qxd5+, O-O, "
    "exd8=Q) ya da UCI biçiminde (ör. g1f3) yaz; yalnız ilk hamleyi ver.\n\n{soru}"
)
CEVAP_RE = re.compile(r"^[\s*_#>]*CEVAP\s*:\s*(.+?)\s*$", re.I | re.M)


def _orijinal(satir):
    o = satir.get("orijinal", satir.get("meta"))
    return json.loads(o) if isinstance(o, str) else o


def istem(satir):
    return ISTEM.format(soru=satir["soru"])


def cevap_hamlesi(board, metin):
    bul = CEVAP_RE.findall(metin or "")
    if not bul:
        return None
    satir = bul[-1].replace("**", "")
    satir = re.sub(r"\d+\s*\.(\s*\.\.)?", " ", satir)  # "35... Re1+" / "1. e4"
    for tok in re.split(r"[\s,;()\[\]/]+", satir):
        mv = hamle_ayristir(board, tok)
        if mv is not None:
            return mv
    return None


def puanla(satir, metin):
    o = _orijinal(satir)
    board = chess.Board(o["fen"])
    mv = cevap_hamlesi(board, metin)
    return mv is not None and mv.uci() in o["kabul_uci"]
