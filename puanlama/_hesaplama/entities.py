# -*- coding: utf-8 -*-
"""JSON ve XML uretimi ortak varlik (entity) uretecleri. Tek bir yerde tanimlanip
hem gen_json.py hem gen_xml.py tarafindan kullanilir -- ayni "gercek veri" (dict),
iki farkli serilestirme + Turkce dogal dil cumlesiyle eslesir. Boylece dogru cevap
LLM'e degil, dogrudan bu dict'e dayanir (kesin dogrulama)."""
import random

ISIMLER = [
    "Ayşe", "Mehmet", "Fatma", "Ali", "Zeynep", "Mustafa", "Elif", "Ahmet", "Emine", "Hüseyin",
    "Hatice", "İbrahim", "Merve", "Yusuf", "Özlem", "Murat", "Esra", "Kemal", "Selin", "Burak",
    "Gül", "Emre", "Sibel", "Cem", "Derya", "Onur", "Pınar", "Serkan", "Aylin", "Tolga",
]
SOYADLAR = [
    "Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir",
    "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek",
]
SEHIRLER = [
    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep", "Kayseri",
    "Eskişehir", "Trabzon", "Samsun", "Denizli", "Mersin", "Diyarbakır", "Van", "Malatya", "Erzurum",
]
# "-de/-da" bulunma hali eki -- unlu uyumuna (ve Gaziantep'te oldugu gibi sert
# unsuz sonrasi t'ye donusumune) gore sehir basina sabit, cunku liste sabit.
SEHIR_LOC = {
    "İstanbul": "'da", "Ankara": "'da", "İzmir": "'de", "Bursa": "'da", "Antalya": "'da",
    "Adana": "'da", "Konya": "'da", "Gaziantep": "'te", "Kayseri": "'de", "Eskişehir": "'de",
    "Trabzon": "'da", "Samsun": "'da", "Denizli": "'de", "Mersin": "'de", "Diyarbakır": "'da",
    "Van": "'da", "Malatya": "'da", "Erzurum": "'da",
}
MESLEKLER = [
    "mühendis", "öğretmen", "doktor", "avukat", "hemşire", "muhasebeci", "yazılımcı", "mimar",
    "eczacı", "polis memuru", "şoför", "aşçı", "gazeteci", "psikolog", "veteriner", "diş hekimi",
]
# meslek basina asgari makul yas (uzun egitim gerektiren meslekte "18 yasinda
# doktor/avukat" gibi sacma ciftler cikmasin diye).
MESLEK_MIN_YAS = {
    "mühendis": 23, "öğretmen": 22, "doktor": 26, "avukat": 24, "hemşire": 21, "muhasebeci": 22,
    "yazılımcı": 20, "mimar": 24, "eczacı": 24, "polis memuru": 21, "şoför": 21, "aşçı": 18,
    "gazeteci": 21, "psikolog": 23, "veteriner": 24, "diş hekimi": 24,
}
# urun -> kategori sabit esleme (once "kategori"yi bagimsiz rastgele secip sonra
# urunu ayri secmek "Kitap kategorisindeki Powerbank" gibi sacma ciftler
# uretiyordu -- artik urun secilince kategorisi otomatik/tutarli geliyor).
URUN_KATEGORI = {
    "Laptop": "Elektronik", "Akıllı Telefon": "Elektronik", "Kablosuz Kulaklık": "Elektronik",
    "Mekanik Klavye": "Elektronik", "Monitör": "Elektronik", "Kablosuz Fare": "Elektronik",
    "Tablet": "Elektronik", "Bluetooth Hoparlör": "Elektronik", "Powerbank": "Elektronik",
    "Akıllı Saat": "Elektronik",
    "Kot Pantolon": "Giyim", "Deri Ceket": "Giyim", "Yün Kazak": "Giyim",
    "Pamuklu Tişört": "Giyim", "Yağmurluk": "Giyim",
    "Termos": "Mutfak", "Tencere Seti": "Mutfak", "Blender": "Mutfak",
    "Kahve Makinesi": "Mutfak", "Bıçak Seti": "Mutfak",
    "Sırt Çantası": "Spor", "Yoga Matı": "Spor", "Dambıl Seti": "Spor",
    "Koşu Ayakkabısı": "Spor", "Kamp Çadırı": "Spor",
    "Roman": "Kitap", "Ansiklopedi": "Kitap", "Ders Kitabı": "Kitap", "Şiir Kitabı": "Kitap",
    "Nemlendirici Krem": "Kozmetik", "Parfüm": "Kozmetik", "Ruj": "Kozmetik", "Şampuan": "Kozmetik",
    "Lego Seti": "Oyuncak", "Puzzle": "Oyuncak", "Uzaktan Kumandalı Araba": "Oyuncak", "Peluş Ayıcık": "Oyuncak",
}
URUNLER = list(URUN_KATEGORI)
KATEGORILER = sorted(set(URUN_KATEGORI.values()))
DERSLER = ["Matematik", "Fizik", "Kimya", "Biyoloji", "Türkçe", "Tarih", "İngilizce", "Bilgisayar Bilimi"]

_TR_ASCII = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
                            "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"})


def ascii_slug(s: str) -> str:
    return s.translate(_TR_ASCII).lower().replace(" ", "")


def rv(rng, lo, hi, decimals=2):
    return round(rng.uniform(lo, hi), decimals)


# ---------------- ORTA: duz (flat) varliklar ----------------

def kisi_profili(rng):
    ad, soyad = rng.choice(ISIMLER), rng.choice(SOYADLAR)
    meslek = rng.choice(MESLEKLER)
    obj = {
        "ad": ad,
        "soyad": soyad,
        "yas": rng.randint(MESLEK_MIN_YAS[meslek], 75),
        "sehir": rng.choice(SEHIRLER),
        "meslek": meslek,
        "medeni_hal": rng.choice(["evli", "bekar"]),
        "email": f"{ascii_slug(ad)}.{ascii_slug(soyad)}@example.com",
    }
    sehir_loc = f"{obj['sehir']}{SEHIR_LOC[obj['sehir']]}"
    cumle = rng.choice([
        f"{obj['ad']} {obj['soyad']}, {obj['yas']} yaşında ve {sehir_loc} yaşıyor. Mesleği {obj['meslek']}, medeni hali {obj['medeni_hal']}. E-posta adresi: {obj['email']}.",
        f"{sehir_loc} yaşayan {obj['ad']} {obj['soyad']} {obj['yas']} yaşında bir {obj['meslek']}. Medeni durumu {obj['medeni_hal']} olan kişinin e-posta adresi {obj['email']}.",
        f"Adı {obj['ad']}, soyadı {obj['soyad']} olan kişi {obj['yas']} yaşında, {obj['meslek']} olarak çalışıyor, {sehir_loc} oturuyor, {obj['medeni_hal']} ve e-postası {obj['email']}.",
    ])
    schema = {
        "type": "object",
        "required": ["ad", "soyad", "yas", "sehir", "meslek", "medeni_hal", "email"],
        "properties": {
            "ad": {"type": "string"}, "soyad": {"type": "string"}, "yas": {"type": "integer"},
            "sehir": {"type": "string"}, "meslek": {"type": "string"},
            "medeni_hal": {"type": "string", "enum": ["evli", "bekar"]}, "email": {"type": "string"},
        },
    }
    return cumle, obj, schema, "kisi"


KATEGORI_FIYAT_ARALIK = {
    "Elektronik": (200, 15000), "Giyim": (100, 2000), "Mutfak": (80, 3000),
    "Spor": (100, 5000), "Kitap": (40, 400), "Kozmetik": (50, 800), "Oyuncak": (50, 1500),
}


def urun_bilgisi(rng):
    urun = rng.choice(URUNLER)
    kategori = URUN_KATEGORI[urun]
    lo, hi = KATEGORI_FIYAT_ARALIK[kategori]
    obj = {
        "urun_adi": urun,
        "kategori": kategori,
        "fiyat_tl": rv(rng, lo, hi, 2),
        "stok_adedi": rng.randint(0, 500),
        "indirimde": rng.choice([True, False]),
    }
    indirim_c = "İndirimde." if obj["indirimde"] else "İndirimde değil."
    cumle = rng.choice([
        f"{obj['urun_adi']} adlı ürün {obj['kategori']} kategorisinde yer alıyor, fiyatı {obj['fiyat_tl']} TL ve stokta {obj['stok_adedi']} adet var. {indirim_c}",
        f"{obj['kategori']} kategorisindeki {obj['urun_adi']}, {obj['fiyat_tl']} TL fiyatla satılıyor. Stok adedi: {obj['stok_adedi']}. {indirim_c}",
    ])
    schema = {
        "type": "object",
        "required": ["urun_adi", "kategori", "fiyat_tl", "stok_adedi", "indirimde"],
        "properties": {
            "urun_adi": {"type": "string"}, "kategori": {"type": "string"},
            "fiyat_tl": {"type": "number"}, "stok_adedi": {"type": "integer"}, "indirimde": {"type": "boolean"},
        },
    }
    return cumle, obj, schema, "urun"


# ---------------- ZOR: ic ice (nested) varliklar ----------------

def siparis_nested(rng):
    ad, soyad = rng.choice(ISIMLER), rng.choice(SOYADLAR)
    n_kalem = rng.randint(2, 4)
    urunler = []
    for urun in rng.sample(URUNLER, n_kalem):
        lo, hi = KATEGORI_FIYAT_ARALIK[URUN_KATEGORI[urun]]
        urunler.append({"urun_adi": urun, "adet": rng.randint(1, 8), "birim_fiyat": rv(rng, lo, hi, 2)})
    toplam = round(sum(u["adet"] * u["birim_fiyat"] for u in urunler), 2)
    obj = {
        "siparis_no": rng.randint(10000, 99999),
        "musteri": {"ad": ad, "soyad": soyad, "sehir": rng.choice(SEHIRLER)},
        "urunler": urunler,
        "toplam_tutar": toplam,
    }
    kalem_cumle = "; ".join(f"{u['adet']} adet {u['urun_adi']} ({u['birim_fiyat']} TL/adet)" for u in urunler)
    cumle = (
        f"Sipariş no {obj['siparis_no']}: {ad} {soyad} ({obj['musteri']['sehir']}) şu ürünleri sipariş etti: "
        f"{kalem_cumle}. Toplam tutar {toplam} TL."
    )
    schema = {
        "type": "object",
        "required": ["siparis_no", "musteri", "urunler", "toplam_tutar"],
        "properties": {
            "siparis_no": {"type": "integer"},
            "musteri": {
                "type": "object", "required": ["ad", "soyad", "sehir"],
                "properties": {"ad": {"type": "string"}, "soyad": {"type": "string"}, "sehir": {"type": "string"}},
            },
            "urunler": {
                "type": "array", "minItems": 1,
                "items": {
                    "type": "object", "required": ["urun_adi", "adet", "birim_fiyat"],
                    "properties": {"urun_adi": {"type": "string"}, "adet": {"type": "integer"}, "birim_fiyat": {"type": "number"}},
                },
            },
            "toplam_tutar": {"type": "number"},
        },
    }
    return cumle, obj, schema, "siparis"


def sinif_kaydi(rng):
    ders = rng.choice(DERSLER)
    ogretmen = f"{rng.choice(ISIMLER)} {rng.choice(SOYADLAR)}"
    n_ogrenci = rng.randint(3, 5)
    ogrenciler = []
    for ad, soyad in [(rng.choice(ISIMLER), rng.choice(SOYADLAR)) for _ in range(n_ogrenci)]:
        ogrenciler.append({"ad": ad, "soyad": soyad, "not_ortalamasi": rv(rng, 30, 100, 1)})
    obj = {"ders_adi": ders, "ogretmen": ogretmen, "ogrenciler": ogrenciler}
    ogr_cumle = "; ".join(f"{o['ad']} {o['soyad']} (not ortalaması {o['not_ortalamasi']})" for o in ogrenciler)
    cumle = f"{ders} dersinin öğretmeni {ogretmen}. Sınıftaki öğrenciler ve not ortalamaları: {ogr_cumle}."
    schema = {
        "type": "object",
        "required": ["ders_adi", "ogretmen", "ogrenciler"],
        "properties": {
            "ders_adi": {"type": "string"}, "ogretmen": {"type": "string"},
            "ogrenciler": {
                "type": "array", "minItems": 1,
                "items": {
                    "type": "object", "required": ["ad", "soyad", "not_ortalamasi"],
                    "properties": {"ad": {"type": "string"}, "soyad": {"type": "string"}, "not_ortalamasi": {"type": "number"}},
                },
            },
        },
    }
    return cumle, obj, schema, "sinif"


ORTA_ENTITIES = [("kisi_profili", kisi_profili), ("urun_bilgisi", urun_bilgisi)]
ZOR_ENTITIES = [("siparis_nested", siparis_nested), ("sinif_kaydi_nested", sinif_kaydi)]
