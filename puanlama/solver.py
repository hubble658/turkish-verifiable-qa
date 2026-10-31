"""Solver (optimizasyon) puanlamasi: konu_agaci/agac_v2/sablon2.py (puanla, kod_kostur), tipler.py
(P_COZ, cevap_al), zor.py (EK, dogru_mu), pilot/pilot.py (sayi_al, esles) parcalari; OR-Tools gerekmez.

set "orta": model en iyi degeri <cevap>…</cevap> icinde yazar; tam sayi, BIREBIR esitlik. (Olcumlerde
            zor.dogru_mu goreli 0,0005 tolerans kullaniyordu: optimum 27.885 iken 27.886 dogru sayiliyordu,
            yani optimuma yakin ama optimal olmayan cozum geciyordu; 2026-10-30 ters sinamasinda 150'nin 38'i.)
set "kod" : model Python programi yazar; yalitilmis surecte (60 sn islemci, 2 GB bellek, yasak modul
            listesi) calistirilir, son yazdirilan tam sayi cevaptir ve altin cevaba BIREBIR esit olmali.
"""
import re
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path

P_COZ = """Aşağıdaki problemi çöz. Kısa çözümünü yaz, en sonda SADECE son cevabı <cevap>…</cevap> etiketi içinde ver.
{ek}
Problem: {soru}"""
EK_OPTIMUM = "Cevap tek bir tam sayı: etikete sadece sayıyı yaz (birim yok).\n"

P_KOD = """Aşağıdaki problemi çözen bir Python 3 programı yaz.
- Yalnızca standart kütüphane kullan (numpy, scipy, ortools, pulp, networkx vb. YOK).
- Program en fazla 60 saniyede bitmeli. Bu boyutta bütün olasılıkları tek tek denemek (kaba kuvvet) günler sürer;
  budamalı arama, dal-sınır, dinamik programlama gibi verimli ve KESİN (en iyiyi garanti eden) bir yöntem kullan.
- Veriyi programın içine yaz. Program sonunda yalnızca cevabı (tek tam sayı) yazdırsın.
Kodu tek bir ```python bloğunda ver.

Problem:
{soru}"""

YASAK_MODUL = re.compile(r"^\s*(?:import|from)\s+(numpy|scipy|ortools|pulp|networkx|pandas|sympy|cvxpy|mip|os|subprocess|socket|shutil|"
                         r"requests|urllib|http|ctypes|multiprocessing|pathlib|signal|importlib|pickle)\b", re.M)


def istem(o, soru):
    if o["set"] == "kod":
        return P_KOD.format(soru=soru)
    return P_COZ.format(soru=soru, ek=EK_OPTIMUM)


def cevap_al(c):
    m = re.findall(r"<cevap>(.*?)</cevap>", c or "", re.S)
    if m:
        return m[-1].strip()
    m = re.findall(r"\\boxed\{((?:[^{}]|\{[^{}]*\})*)\}", c or "")
    if m:
        return m[-1].strip()
    s = [x for x in (c or "").strip().splitlines() if x.strip()]
    return s[-1][-300:] if s else None


def sayi_al(s):
    s = str(s).replace(" ", "")
    m = re.search(r"-?\d+(?:[.,]\d+)?(?:[eE]-?\d+)?(?:/\d+)?", s)
    if not m:
        return None
    t = m.group(0)
    if "/" in t:
        try:
            return float(Fraction(t.replace(",", ".")))
        except (ValueError, ZeroDivisionError):
            return None
    # 1.234,5 / 1,5 gibi Turkce yazimlar
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def kod_kostur(kod, sinir=60):
    """Model kodunu yalitilmis surecte calistir. (durum, cikti_sayisi, sure, mesaj)"""
    if not kod:
        return "kod yok", None, 0, "Yanıtında ```python kod bloğu yok."
    m = YASAK_MODUL.search(kod)
    if m or re.search(r"\b(open|exec|eval|__import__|compile)\s*\(", kod):
        return "yasak", None, 0, f"İzin verilmeyen modül ya da işlev: {m.group(1) if m else 'open/exec/eval'}."

    def sinirla():
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (2048 * 2**20, 2048 * 2**20))
        resource.setrlimit(resource.RLIMIT_CPU, (sinir, sinir))

    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "c.py").write_text(kod, encoding="utf-8")
        t = time.time()
        try:
            p = subprocess.run([sys.executable, "-I", "c.py"], capture_output=True, text=True, timeout=sinir + 10, cwd=d, preexec_fn=sinirla)
        except subprocess.TimeoutExpired:
            return "zaman", None, sinir, f"Program {sinir} saniyede bitmedi."
        sure = time.time() - t
    if p.returncode != 0:
        son = (p.stderr.strip().splitlines() or [""])[-1][:300]
        if p.returncode in (-9, -24, 152) or not son:
            return "zaman", None, sure, f"Program {sinir} saniyelik işlemci sınırını ya da 2 GB bellek sınırını aştı."
        return "hata", None, sure, "Program hata verdi: " + son
    sayilar = re.findall(r"-?\d+", p.stdout)
    if not sayilar:
        return "çıktısız", None, sure, "Program bir sayı yazdırmadı."
    return "ok", int(sayilar[-1]), sure, ""


def kod_al(c):
    m = re.findall(r"```(?:python|py)?\s*\n(.*?)```", c or "", re.S)
    return max(m, key=len) if m else None


def puanla(o, metin):
    if o["set"] == "kod":
        _, v, _, _ = kod_kostur(kod_al(metin))
        return v == o["cevap"]
    t = cevap_al(metin)
    if t is None:
        return False
    if re.fullmatch(r"\s*-?\d{1,3}(?:\.\d{3})+\s*", t):  # Turkce binlik ayirici: 1.234 = 1234
        t = t.replace(".", "")
    a = sayi_al(t)
    return a is not None and a == int(o["cevap"])
