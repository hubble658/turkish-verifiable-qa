"""Regex seti (regex-tr): istem ve puanlayıcı. pip install regex greenery==4.2.3

regex_yazma (T1): DFA eşdeğerliği (dış lookahead'ler ve (?!.*(.)\\1) dahil), otomata çevrilemeyen cevapta gizli testler; hangi
yolla karar verildiği `puanla_ayrinti`'deki `via` alanındadır. regex_cikarma (T3): gizli mesajlarda finditer listesi birebir.
Tek deneme: kaynaktaki 5 denemeli karşı örnek protokolü ve T2 burada yok. regex_cekirdek kaynağın core.py dosyasından türedi
(5 Kasım 2026 değişiklikleri dosyanın başında); eşdeğerlik süre sınırı SIGALRM kullanır, puanlama iş parçacığında değil ana süreçte ya da ProcessPool'da yapılmalı.
"""
import json
import re

from . import regex_cekirdek as core

T1_ISTEM = """Aşağıdaki tarife uyan metinleri tanıyan bir Python regex'i yaz.
Kurallar:
- Metnin TAMAMI eşleşmeli (re.fullmatch ile denenecek).
- re.ASCII bayrağı açık: \\d, \\w, \\s sadece ASCII karakterlere uyar; Türkçe harfler (ç, ğ, ı, İ, ö, ş, ü) gerekiyorsa açıkça yaz.
- Metinler satır sonu içermez.
Cevabının SON satırı tam olarak şu biçimde olsun:
REGEX: <regex>

Tarif: {soru}"""
T3_ISTEM = """Müşteri mesajlarından bilgi çıkaran bir Python regex'i yaz.
Kurallar:
- Regex her mesaja re.finditer(regex, mesaj, re.ASCII) ile uygulanacak; her eşleşmenin tamamı (group(0)) bir çıktı sayılır.
- Her mesajdan çıkan liste, doğru listeyle birebir aynı olmalı (eksik ya da fazla parça olmamalı).
- re.ASCII açık: \\d, \\w, \\s sadece ASCII karakterlere uyar.
Cevabının SON satırı tam olarak şu biçimde olsun:
REGEX: <regex>

Görev: {soru}"""
REGEX_RE = re.compile(r"^\s*REGEX:\s*(.+?)\s*$", re.M)


def cevap_al(metin):
    m = REGEX_RE.findall(metin or "")
    if not m:
        return None
    rx = m[-1].strip()
    return rx[1:-1] if len(rx) >= 2 and rx[0] == rx[-1] == "`" else rx


def istem(satir):
    return (T3_ISTEM if satir["kategori"] == "regex_cikarma" else T1_ISTEM).format(soru=satir["soru"])


def puanla_ayrinti(satir, metin):
    """{ok, kind, via, ...}. via: dfa | tests; T3'te ve cevap ayıklanamayınca via yoktur."""
    rx = cevap_al(metin)
    if rx is None:
        return {"ok": False, "kind": "bicim"}
    o = satir["orijinal"]
    o = json.loads(o) if isinstance(o, str) else o
    return (core.score_extract if satir["kategori"] == "regex_cikarma" else core.score)(o, rx)


def puanla(satir, metin):
    return puanla_ayrinti(satir, metin)["ok"]
