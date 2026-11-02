# -*- coding: utf-8 -*-
"""bulmaca_dataset.jsonl sorularini modellere sormak icin ortak prompt sablonu
ve Turkce-farkinda skorlama yardimcilari.

score_via_*.py scriptleri (vLLM/Cosmos T1, DashScope/Qwen, ...) arasinda ayni
degerlendirme mantigini paylasmak icin buraya cikarildi -- boylece farkli
modellere atilan sorular ayni sekilde skorlanir ve sonuclar adil sekilde
karsilastirilabilir.
"""
import collections
import json
import os
import re

INSTRUCTION = (
    "Asagidaki mantik bulmacasini dikkatlice coz. Adim adim akil yurutebilirsin, "
    "ama cevabini MUTLAKA en son satirda tam olarak su formatta ver:\n"
    "CEVAP: <kisa cevap>\n\n"
)

TR_MAP = str.maketrans({"İ": "i", "I": "ı"})


def tr_lower(s):
    return s.translate(TR_MAP).lower()


def norm_token(s):
    s = tr_lower(str(s).strip())
    s = re.sub(r"[\.\!\?]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


# akrabalik.py'nin relation() fonksiyonu hep 3. tekil iyelik ekli halini
# dondurur ("torunu", "amcası"...); modeller sikca ek olmadan ("torun", "amca")
# cevap veriyor -- anlamca ayni sey, bu yuzden lenient_match'te esitliyoruz.
# (exact_match kasitli olarak katı kaliyor, bu esitleme sadece lenient icin.)
AKRABALIK_CANON = {
    "baba": "babası", "babası": "babası",
    "anne": "annesi", "annesi": "annesi",
    "oğul": "oğlu", "oğlu": "oğlu",
    "kız": "kızı", "kızı": "kızı",
    "erkek kardeş": "erkek kardeşi", "erkek kardeşi": "erkek kardeşi",
    "kız kardeş": "kız kardeşi", "kız kardeşi": "kız kardeşi",
    "dede": "dedesi", "dedesi": "dedesi",
    "babaanne": "babaannesi", "babaannesi": "babaannesi",
    "anneanne": "anneannesi", "anneannesi": "anneannesi",
    "torun": "torunu", "torunu": "torunu",
    "amca": "amcası", "amcası": "amcası",
    "dayı": "dayısı", "dayısı": "dayısı",
    "hala": "halası", "halası": "halası",
    "teyze": "teyzesi", "teyzesi": "teyzesi",
    "yeğen": "yeğeni", "yeğeni": "yeğeni",
    "kuzen": "kuzeni", "kuzeni": "kuzeni",
}


_AKRABALIK_KOKLER = ("baba", "anne", "oğl", "oğul", "kız", "kardeş", "dede", "torun", "amca", "dayı", "hala",
                     "teyze", "yeğen", "kuzen")


def _akrabalik_terimi(raw):
    """2026-11-02: cumle halindeki cevaptan tek akrabalik terimi. Dusunen V4-Flash cevabi sikca cumleyle
    yaziyor ("Erkek torunu", "Mehmet, Selin'in erkek yeğenidir.", "Yeğenidir.") ve eski kural yalniz
    cevabin tamamini esliyordu: 100 akrabalik sorusunun 51'i boyle reddedildi. Ek-fiil (-dir) ve cinsiyet
    niteleyicisi (erkek/kız + terim) atilir; "erkek/kız kardeşi" tek terimdir. Cevapta tam olarak BIR terim
    geciyorsa ve "değil" yoksa o terim doner, yoksa None (eski davranis)."""
    w = [re.sub(r"(?<=[aeıioöuü])[dt][ıiuü]r$", "", x) for x in re.findall(r"[a-zçğıöşü]+", tr_lower(str(raw)))]
    if "değil" in w:
        return None
    # zincir ifade ("annesinin babası" = dedesi): ek almis akrabalik koku varsa karar verilmez
    if any(x.startswith(_AKRABALIK_KOKLER) and x not in AKRABALIK_CANON and x not in ("erkek", "kız", "kardeş", "kardeşi")
           for x in w):
        return None
    bulunan, i = set(), 0
    while i < len(w):
        if w[i] in ("erkek", "kız") and i + 1 < len(w) and w[i + 1] in ("kardeş", "kardeşi"):
            bulunan.add(AKRABALIK_CANON[f"{w[i]} {w[i + 1]}"])
            i += 2
            continue
        if w[i] in ("erkek", "kız") and i + 1 < len(w) and w[i + 1] in AKRABALIK_CANON:
            i += 1  # cinsiyet niteleyicisi: "erkek torunu", "kız yeğeni"
            continue
        if w[i] in AKRABALIK_CANON and " " not in w[i]:
            bulunan.add(AKRABALIK_CANON[w[i]])
        i += 1
    return bulunan.pop() if len(bulunan) == 1 else None


# nesne_takip.py'nin ROOMS sözlüğündeki oda adları (kapalı, küçük sözcük
# dağarcığı - bkz. bulmaca_pkg/tr_utils.py). final_obj/final_container/
# counterfactual cevaplari yalin (nominatif) oda adidir, ama model sikca
# bulunma hali ekiyle ("balkonda") ya da fazladan aciklamayla ("Banyodaki
# valizin icinde") cevap veriyor - Turkce'de bu ekler koke ekleniyor,
# koku bozmuyor, bu yuzden "kok, cevapta gecer mi" kontrolu guvenli.
_ROOM_NAMES = {"mutfak", "salon", "yatak odası", "banyo", "çalışma odası",
               "balkon", "koridor", "antre"}

# sahiplik_zinciri.py'nin ITEMS sozlugundeki nesne adlari: "ne_gonderdi"
# sorusunun altin cevabi yalin (nominatif) haldir ("kitap"), model sikca
# belirtme haliyle cevap verir ("kitabi") - unsuz yumusamasi (p->b) oldugu
# icin bir alt-dizi kontrolu yetmez, kucuk bir esleme tablosu gerekir.
_SAHIPLIK_ITEM_ACC = {"kitap": "kitabı", "paket": "paketi", "mektup": "mektubu",
                       "anahtar": "anahtarı", "telefon": "telefonu", "dosya": "dosyayı"}


def norm_answer_set(rec, raw):
    """Liste tipi cevaplari (dogrucu_yalanci, siralama-neighbors) siradan bagimsiz kumeye,
    akrabalik cevaplarini iyelik-eki-bagimsiz kanonik forma cevirir.

    Not: meta'ya degil, sadece type + cevabin (gold_answer) sekline bakar --
    boylece hem canli skorlamada hem de kaydedilmis sonuclar.jsonl'dan
    (meta'siz) geriye donuk yeniden skorlamada calisir."""
    t = rec["type"]
    gold = rec.get("answer", rec.get("gold_answer", ""))

    if t == "akrabalik":
        return AKRABALIK_CANON.get(norm_token(raw)) or _akrabalik_terimi(raw) or norm_token(raw)

    # 2026-11-02 (dusunen V4-Flash benchmark'i): tipografik kesme isareti ("Aslı’dan") asagidaki kesme
    # isareti kuralina girmiyordu; sayacta "2 top" / "Sadece sarı" reddediliyordu.
    if isinstance(raw, str):
        raw = raw.replace("’", "'").replace("‘", "'")
    if t == "sayac_takip":
        raw = re.sub(r"^\s*(sadece|yalnızca|yalnız)\s+", "", tr_lower(str(raw)))
        if re.fullmatch(r"\d+", str(gold)):
            sayilar = re.findall(r"\d+", raw)
            if len(sayilar) == 1:  # "2 top", "1 kırmızı kalem"; birden cok sayi varsa karar verilmez
                return sayilar[0]

    is_list_answer = (t == "dogrucu_yalanci") or (t == "siralama" and " ve " in str(gold)) \
        or (t == "sayac_takip" and "," in str(gold))
    if is_list_answer:
        parts = [norm_token(p) for p in re.split(r",| ve ", str(raw)) if p.strip()]
        return frozenset(parts)

    if t == "yon" and "km" in str(gold).lower():
        m = re.search(r"-?\d+", str(raw))
        return m.group(0) if m else norm_token(raw)

    if t == "zaman_aritmetigi" and re.fullmatch(r"\d{1,2}:\d{2}", str(gold)):
        m = re.search(r"(\d{1,2})[:.](\d{2})", str(raw))
        if m:
            return f"{int(m.group(1)):02d}:{m.group(2)}"
        return norm_token(raw)

    # "fark" sorusu: altin cevap ciplak bir sayidir ("30"), model sikca
    # birim ekler ("30 dakika") -- ilk sayiyi cikarip karsilastir.
    if t == "zaman_aritmetigi" and re.fullmatch(r"\d+", str(gold)):
        m = re.search(r"\d+", str(raw))
        return m.group(0) if m else norm_token(raw)

    if t == "nesne_takip" and str(gold) in _ROOM_NAMES:
        gold_n, raw_n = norm_token(gold), norm_token(raw)
        return gold_n if gold_n in raw_n else raw_n

    if t == "sahiplik_zinciri" and str(gold) in _SAHIPLIK_ITEM_ACC:
        if norm_token(raw) == norm_token(_SAHIPLIK_ITEM_ACC[gold]):
            return norm_token(gold)
        return norm_token(raw)

    # genel duzeltme: ozel isim + hal eki hep kesme isaretiyle yazilir
    # ("Ayşe'den") - altin cevap yalin adsa, kesme isaretinden onceki kismi
    # karsilastir (bu, "Ali" gibi kisa bir adin baska bir adin ICINDE
    # rastlantisal olarak gecmesinden -- ör. "Halil" -- kaynaklanabilecek
    # yanlis pozitiften kacinmak icin alt-dizi degil, kesme isaretiyle
    # sinirlanmis tam esleme kullanir).
    if isinstance(raw, str) and "'" in raw:
        prefix = raw.split("'")[0]
        if norm_token(prefix) == norm_token(gold):
            return norm_token(gold)

    return norm_token(raw)


def score_record(rec, model_answer):
    exact = norm_token(model_answer) == norm_token(rec["answer"])
    lenient = norm_answer_set(rec, model_answer) == norm_answer_set(rec, rec["answer"])
    return exact, lenient


def extract_answer(gen_text):
    # Satir basina ceke ediliyor (^...$ + MULTILINE): caselessiz "cevap:" duz yaziya
    # sizip \s* ile bir sonraki satira (asil "CEVAP:" satirina) atlayabiliyordu, bu da
    # yakalanan cevabin icine "CEVAP: " on ekini karistiriyordu (ör. "CEVAP: Buse").
    # [\s*_]* : modeller cevabi sik sik markdown kalinla sarmaliyor ("**CEVAP: 7**") --
    # hem onceki hem sondaki */_ isaretlerini yut, yoksa hic eslesme bulunamayip
    # (asil marker satiri degil) tum metnin son satirina dusuluyordu.
    matches = re.findall(r"^[\s*_]*CEVAP\s*:\s*(.+?)[\s*_]*$", gen_text, flags=re.IGNORECASE | re.MULTILINE)
    if matches:
        return matches[-1].strip()
    tail = gen_text.strip().split("\n")
    return tail[-1].strip() if tail else gen_text.strip()


def load_records(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def select_stratified(records, per_bucket):
    """Her (type, difficulty) kombinasyonundan ilk `per_bucket` kaydi secer.

    Ornek: per_bucket=25 -> her bulmaca tipinden 25 kolay + 25 zor = tip basina 50,
    5 tip icin toplam 250 kayit. Farkli modellerin ayni soru kumesiyle
    karsilastirilabilmesi icin secim deterministiktir (rastgelelik yok)."""
    buckets = collections.defaultdict(list)
    for r in records:
        buckets[(r["type"], r["difficulty"])].append(r)
    selected = []
    for key in sorted(buckets):
        selected.extend(buckets[key][:per_bucket])
    return selected


def load_processed_ids(out_path):
    ids = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                ids.add(json.loads(line)["id"])
    return ids


def write_result(out_f, rec, gen_text, model_answer, exact, lenient):
    out_f.write(json.dumps({
        "id": rec["id"], "type": rec["type"], "difficulty": rec["difficulty"],
        "gold_answer": rec["answer"], "model_raw": gen_text,
        "model_answer": model_answer,
        "exact_match": exact, "lenient_match": lenient,
    }, ensure_ascii=False) + "\n")


def _aggregate(rows):
    n = len(rows)
    return {
        "n": n,
        "exact_match": sum(r["exact_match"] for r in rows) / n,
        "lenient_match": sum(r["lenient_match"] for r in rows) / n,
    }


def _group_by(rows, key):
    buckets = collections.defaultdict(list)
    for r in rows:
        buckets[key(r)].append(r)
    return {k: _aggregate(v) for k, v in sorted(buckets.items())}


def compute_summary(out_path):
    """--out jsonl'daki kayitlardan ozet istatistik sozlugu uretir (None: hic kayit yok).

    Toplam + zorluk (kolay/zor) + tip + tip x zorluk kirilimlarini icerir."""
    rows = []
    with open(out_path, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    if not rows:
        return None

    rows_by_type = collections.defaultdict(list)
    for r in rows:
        rows_by_type[r["type"]].append(r)

    summary = _aggregate(rows)
    summary["by_difficulty"] = _group_by(rows, lambda r: r["difficulty"])
    summary["by_type"] = {}
    for t, type_rows in sorted(rows_by_type.items()):
        entry = _aggregate(type_rows)
        entry["by_difficulty"] = _group_by(type_rows, lambda r: r["difficulty"])
        summary["by_type"][t] = entry

    return summary


def print_summary(out_path, summary_path=None):
    """Ozeti ekrana basar; summary_path verilirse ayrica JSON olarak diske kaydeder."""
    summary = compute_summary(out_path)
    if summary is None:
        return

    print(f"\nToplam {summary['n']} kayit | exact: {summary['exact_match']:.1%} | "
          f"lenient: {summary['lenient_match']:.1%}")
    print("\nZorluk bazinda:")
    for d, s in summary["by_difficulty"].items():
        print(f"  {d:8s} n={s['n']:4d}  exact={s['exact_match']:.1%}  lenient={s['lenient_match']:.1%}")
    print("\nTip bazinda:")
    for t, s in summary["by_type"].items():
        print(f"  {t:20s} n={s['n']:4d}  exact={s['exact_match']:.1%}  lenient={s['lenient_match']:.1%}")
        for d, ds in s["by_difficulty"].items():
            print(f"    {d:8s} n={ds['n']:4d}  exact={ds['exact_match']:.1%}  lenient={ds['lenient_match']:.1%}")

    if summary_path:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\nOzet kaydedildi -> {summary_path}")
