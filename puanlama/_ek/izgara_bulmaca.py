"""Izgara/graf bulmacaları: istem ve puanlayıcı.

sudoku / futoshiki: CEVAP'tan sonraki n×n ızgara kurallara (satır, sütun, kutu / eşitsizlik) ve verilen ipuçlarına
uyuyorsa doğru (çözüm tek olduğu için bu altınla aynıdır, ama altına bakılmadan denetlenir).
hayat_oyunu: ızgara altınla birebir. labirent / graf: CEVAP satırındaki ilk tam sayı.
"""
import json
import re

ISTEM = (
    "Aşağıdaki bulmacayı adım adım çöz. Açıklamandan SONRA cevabını \"CEVAP:\" ile başlat. Cevap tek bir sayıysa "
    "aynı satıra yaz (\"CEVAP: 17\"); ızgara isteniyorsa CEVAP satırından sonraki satırlara yaz.\n\n{soru}"
)
CEVAP_RE = re.compile(r"^[\s*_#>]*CEVAP\s*:", re.I | re.M)


def _orijinal(satir):
    o = satir.get("orijinal", satir.get("meta"))
    return json.loads(o) if isinstance(o, str) else o


def istem(satir):
    return ISTEM.format(soru=satir["soru"])


def _son_cevap(metin):
    m = list(CEVAP_RE.finditer(metin or ""))
    return None if not m else metin[m[-1].end():]


def izgara_oku(parca, n):
    satirlar = []
    for l in parca.splitlines():
        rak = re.findall(r"\d", l)
        if len(rak) == n:
            satirlar.append([int(x) for x in rak])
            if len(satirlar) == n:
                return satirlar
        elif satirlar and rak:
            satirlar = []  # bozuk satır: baştan say
    return None


def _latin(g, n):
    hedef = set(range(1, n + 1))
    return all(set(r) == hedef for r in g) and all({g[i][c] for i in range(n)} == hedef for c in range(n))


def sudoku_gecerli(g, o):
    n = o["n"]
    kr, kc = (2, 3) if n == 6 else (3, 3)
    if not _latin(g, n):
        return False
    for br in range(0, n, kr):
        for bc in range(0, n, kc):
            if {g[r][c] for r in range(br, br + kr) for c in range(bc, bc + kc)} != set(range(1, n + 1)):
                return False
    return all(not v or g[r][c] == v for r, row in enumerate(o["verilen"]) for c, v in enumerate(row))


def futoshiki_gecerli(g, o):
    n = o["n"]
    if not _latin(g, n):
        return False
    if any(v and g[r][c] != v for r, row in enumerate(o["verilen"]) for c, v in enumerate(row)):
        return False
    return all(g[a][b] < g[x][y] for (a, b), (x, y) in o["esitsiz"])


def puanla(satir, metin):
    parca = _son_cevap(metin)
    if parca is None:
        return False
    alt, o = satir["alt_tip"], _orijinal(satir)
    if alt in ("labirent", "graf"):
        m = re.search(r"-?\d+", parca.splitlines()[0] if parca.strip() else "") or re.search(r"-?\d+", parca)
        return bool(m) and int(m.group()) == int(satir["cevap"])
    n = o["n"]
    g = izgara_oku(parca, n)
    if g is None:
        return False
    if alt == "sudoku":
        return sudoku_gecerli(g, o)
    if alt == "futoshiki":
        return futoshiki_gecerli(g, o)
    return g == [[int(x) for x in r.split()] for r in satir["cevap"].splitlines()]
