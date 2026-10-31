# -*- coding: utf-8 -*-
"""B-grubu (formul-tabanli) sorular icin ortak yardimcilar. Bu kategorilerde
cevap deterministik hesaplandigi icin LLM'e dogrulama sorulmuyor -- sadece
JSONL yazma / id / sayi bicimleme gibi ufak ortak isler burada."""
import json
import random
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CIKTI_DIR = Path(__file__).parent / "cikti"
# paket kopyasi: puanlama icin import edilirken cikti/ klasoru acilmaz (yalniz uretimde Writer kullanir)


def fmt_num(x, max_decimals=4):
    """Sayiyi insan-okunur bicimde yazar: tamsayiysa nokta olmadan, degilse
    gereksiz sondaki sifirlari atarak en fazla max_decimals basamakla. Cok
    kucuk (yuvarlaninca yanlislikla "0" gorunecek) ya da asiri buyuk degerler
    icin bilimsel gosterime duser -- birim donusumunde km<->mg gibi asiri uc
    birim ciftlerinde bu olmadan cevap yanlislikla "0" yazilabiliyordu."""
    if isinstance(x, int):
        return str(x)
    xf = float(x)
    if xf == 0:
        return "0"
    if abs(xf) < 10 ** (-max_decimals) or abs(xf) >= 10**9:
        return f"{xf:.3g}"
    # Python round() float uzerinde cifte-yuvarlama yapar (round(2.675, 2) == 2.67);
    # Excel/LibreOffice ve okul kurali gibi sifirdan uzaga yuvarla: once 15 anlamli
    # basamaga indir (ikili float kalintisini at), sonra Decimal ROUND_HALF_UP.
    r = Decimal(f"{xf:.15g}").quantize(Decimal(1).scaleb(-max_decimals), rounding=ROUND_HALF_UP)
    if r == r.to_integral_value():
        return str(int(r))
    return format(r.normalize(), "f")


class Writer:
    """Bir kategori icin JSONL yazici + (alt_tip, kanonik_params) bazli exact-dedup."""

    def __init__(self, kategori: str, seed: int | None = None):
        self.kategori = kategori
        self.path = CIKTI_DIR / f"{kategori}.jsonl"
        self.f = self.path.open("w", encoding="utf-8")
        self.seen = set()
        self.counts = {}  # (alt_tip, zorluk) -> n
        self.n_total = 0
        self.n_dup_skipped = 0
        self.rng = random.Random(seed)

    def add(self, alt_tip: str, zorluk: str, soru: str, cevap: str, kanonik_key, **extra):
        """kanonik_key: (alt_tip, *parametreler) gibi hashlenebilir bir tuple --
        ayni parametre kombinasyonu ikinci kez gelirse atlanir (exact-dedup)."""
        dedup_key = (alt_tip, kanonik_key)
        if dedup_key in self.seen:
            self.n_dup_skipped += 1
            return False
        self.seen.add(dedup_key)
        self.n_total += 1
        rid = f"{self.kategori}-{alt_tip}-{self.n_total:05d}"
        rec = {
            "id": rid,
            "kategori": self.kategori,
            "alt_tip": alt_tip,
            "zorluk": zorluk,
            "soru": soru,
            "cevap": cevap,
            **extra,
        }
        self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.counts[(alt_tip, zorluk)] = self.counts.get((alt_tip, zorluk), 0) + 1
        return True

    def close(self):
        self.f.close()

    def summary(self):
        lines = [f"== {self.kategori} == toplam {self.n_total} (tekrar oldugu icin atlanan: {self.n_dup_skipped}) -> {self.path}"]
        for (alt_tip, zorluk), n in sorted(self.counts.items()):
            lines.append(f"  {alt_tip:28s} {zorluk:6s} {n}")
        return "\n".join(lines)
