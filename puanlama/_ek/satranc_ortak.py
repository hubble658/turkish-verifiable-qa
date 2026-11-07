"""Satranç seti ortak araçları: hamle ayrıştırma (SAN/UCI/Türkçe harfler), zorlayıcı mat çözücü, tahta metni."""
import re

import chess

# Türkçe taş harfleri: Şah, Vezir, Kale, Fil, At
TR_TAS = {"Ş": "K", "V": "Q", "K": "R", "F": "B", "A": "N"}
TAS_AD = {chess.KING: "Şah", chess.QUEEN: "Vezir", chess.ROOK: "Kale", chess.BISHOP: "Fil",
          chess.KNIGHT: "At", chess.PAWN: "Piyon"}
UNICODE_TAS = {"♔": "K", "♕": "Q", "♖": "R", "♗": "B", "♘": "N", "♚": "K", "♛": "Q", "♜": "R", "♝": "B", "♞": "N"}
UCI_RE = re.compile(r"^([a-h][1-8])-?([a-h][1-8])([qrbnQRBN])?$")


def _temizle(s):
    s = s.strip().strip("`*_.,;:()[]\"'").strip()
    for u, e in UNICODE_TAS.items():
        s = s.replace(u, e)
    s = s.replace("0-0-0", "O-O-O").replace("0-0", "O-O").replace("o-o-o", "O-O-O").replace("o-o", "O-O")
    s = re.sub(r"[+#!?]+$", "", s)
    s = re.sub(r"^\d+\.(\.\.)?\s*", "", s)  # "23. Qxd5" / "23... Qxd5"
    return s.strip()


def hamle_ayristir(board, metin):
    """Tek hamle metnini (SAN, UCI, uzun cebirsel, Türkçe harfli SAN) yasal bir chess.Move'a çevirir; olmazsa None."""
    s = _temizle(metin)
    if not s:
        return None
    adaylar = [s]
    m = re.match(r"^([KQRBNŞVFA])?([a-h][1-8])[-x]([a-h][1-8])(=?[QRBNVKFA])?$", s)  # Ng1-f3, Nf3xe5
    if m:
        terfi = (m.group(4) or "").lstrip("=")
        adaylar.append(m.group(2) + m.group(3) + TR_TAS.get(terfi, terfi).lower())
    for a in adaylar:
        u = UCI_RE.match(a)
        if u:
            try:
                mv = chess.Move.from_uci(u.group(1) + u.group(2) + (u.group(3) or "").lower())
                if mv in board.legal_moves:
                    return mv
                if mv.promotion is None:  # piyon son sıraya: terfi yazılmamışsa vezir varsay
                    mv2 = chess.Move(mv.from_square, mv.to_square, chess.QUEEN)
                    if mv2 in board.legal_moves:
                        return mv2
            except ValueError:
                pass
        try:
            return board.parse_san(a)
        except ValueError:
            pass
    # İngilizce SAN olmadıysa Türkçe harfleri dene (K = kale, Ş = şah)
    tr = s
    if tr and tr[0] in TR_TAS:
        tr = TR_TAS[tr[0]] + tr[1:]
    tr = re.sub(r"=([VKFA])", lambda x: "=" + TR_TAS[x.group(1)], tr)
    if tr != s:
        try:
            return board.parse_san(tr)
        except ValueError:
            pass
    return None


def zorlayici_mat(board, n):
    """Sırası gelen taraf en fazla n hamlede (kendi hamlesi sayısı) zorlayıcı mat yapabiliyor mu?"""
    if n <= 0:
        return False
    hamleler = sorted(board.legal_moves, key=lambda m: (not board.gives_check(m), not board.is_capture(m)))
    for m in hamleler:
        board.push(m)
        try:
            if board.is_checkmate():
                return True
            if n > 1 and not board.is_game_over() and _her_cevap_mat(board, n - 1):
                return True
        finally:
            board.pop()
    return False


def _her_cevap_mat(board, n):
    for r in board.legal_moves:
        board.push(r)
        try:
            if not zorlayici_mat(board, n):
                return False
        finally:
            board.pop()
    return True


def hamle_mat_zorlar(board, mv, n):
    """mv oynandıktan sonra rakip ne yaparsa yapsın toplam en fazla n hamlede mat oluyor mu?"""
    board.push(mv)
    try:
        if board.is_checkmate():
            return True
        if n == 1 or board.is_game_over():
            return False
        return _her_cevap_mat(board, n - 1)
    finally:
        board.pop()


def tas_listesi(board):
    satirlar = []
    for renk, ad in ((chess.WHITE, "Beyaz"), (chess.BLACK, "Siyah")):
        parcalar = []
        for tip in (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN):
            kareler = sorted(chess.square_name(k) for k in board.pieces(tip, renk))
            if kareler:
                parcalar.append(f"{TAS_AD[tip]} {', '.join(kareler)}")
        satirlar.append(f"{ad}: " + "; ".join(parcalar))
    return "\n".join(satirlar)


def tahta_metni(board):
    """8. sıra üstte; büyük harf beyaz, küçük harf siyah (İngilizce harfler), nokta boş kare."""
    satirlar = []
    for sira in range(7, -1, -1):
        hucre = []
        for sutun in range(8):
            p = board.piece_at(chess.square(sutun, sira))
            hucre.append(p.symbol() if p else ".")
        satirlar.append(f"{sira + 1} " + " ".join(hucre))
    satirlar.append("  a b c d e f g h")
    return "\n".join(satirlar)
