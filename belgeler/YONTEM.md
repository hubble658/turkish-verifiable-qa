# Doğrulanabilir Türkçe Soru Veri Seti: Yöntem

Son güncelleme: 28 Ekim 2026. Bu belge her alt setin nereden geldiğini, nasıl üretildiğini, cevabın nasıl doğrulandığını, hangi süzgeçlerden geçtiğini ve ne kadara mal olduğunu anlatır. Sayılar dosyalardan sayılarak doğrulandı. Makinece okunabilir özet: `setler.json`. Kullanılan kodların kopyası: `kodlar/`. Veri setini kullanacak/paylaşacak kişi için soru sorma, puanlama ve paket içeriği: `KULLANIM.md`.

## Genel bakış

| Set | Soru | Cevabı kim belirler | LLM'in rolü | Son dosya |
|---|---|---|---|---|
| Bulmaca | 3.000 | Program (çözücü + tek çözüm kontrolü) | Yok | `bulmaca/bulmaca_dataset.jsonl`, `bulmaca/yeni_tipler_dataset.jsonl` |
| Hesaplama | 14.613 | Program (formül, sympy, datetime, şema) | Yok | `hesaplama/cikti/*.jsonl` (birleşikte 3 tekrar atılır, §11) |
| MEB tekli konu | 2.914 | Üretici LLM + kitap pasajı; LLM tutarlılık kontrolü | Soru ve cevabı yazar, kontrol eder | `korpus/verifiable_dataset_v6_son.jsonl` |
| MEB çapraz konu | 3.993 | Üretici LLM + kitap pasajları; LLM hakem | Soru ve cevabı yazar, hakem süzer | `korpus/uretim3k/capraz_son.jsonl` |
| Solver (optimizasyon) | 4.986 | Program (OR-Tools CP-SAT, en iyi değer kanıtlı) | Yalnız meslek kostümü ve giriş paragrafı | `konu_agaci/agac_v2/sablon/uretim5k/sorular.jsonl` |
| SQL: Türkiye açık veri (il/ilçe) | 17.895 (20.138'den 2.243 birebir tekrar atıldı, §11) | Program (gerçek SQLite'a karşı çalıştırılır) | Yok | `sql_arastirma/uretim/*_sorular.jsonl`, `*_zincir_sorular.jsonl` |
| SQL: belediye dışı açık veri (deprem, Eurostat, Dünya Bankası, Wikidata) | 9.234 | Program (gerçek SQLite'a karşı çalıştırılır) | Yok | `sql_arastirma/uretim/*_son.jsonl` (8 dosya) |
| SQL çıktı-tahmini (model SQL yazmıyor, çıktı tahmin ediyor) | 3.424 (İstanbul dengelemesi, §11) | Program (§6/§7'den yeniden paketleme + gerçek SQLite'a karşı çalıştırma) | Yok | `sql_arastirma/uretim/cikti_tahmini/*.jsonl` |
| Excel formülü: veritabanından (zor-3) | 1.000 | Program (formülsüz Python + iki gold formül motorda + LibreOffice; 5 kitapta çalıştırarak puanlama) | Yok | `hesaplama/cikti_veritabani/excel_veritabani_zor3.jsonl` |
| SQL: TURSpider (dış set, filtreli; `koken=turspider_filtreli`) | 7.904 | Gerçek SQLite'ta yeniden çalıştırma | Yok (insan çevirisi) | `sql_arastirma/hazir/turspider.jsonl` |
| SQL: Cognipeer (dış set, filtreli; `koken=cognipeer_filtreli`) | 69.034 | Gömülü şemada yeniden çalıştırma | Kaynak set LLM üretimi | `sql_arastirma/hazir/cognipeer.jsonl` |
| **Toplam** | **137.997** (özgün 61.059 + dış 76.938) | | | |

Pilotlar (toplama girmez): Excel formülü — veritabanından, 30 + 40 + 30 + 100 soru (`hesaplama/pilot/excel_veritabani_*pilot.jsonl`) (§9).

Doğrulama gücüne göre iki grup var:

- **Kesin doğrulanmış, özgün (54.152 soru):** bulmaca, hesaplama, solver, SQL (il/ilçe + belediye dışı + çıktı-tahmini), Excel veritabanı zor-3. Cevap kodla hesaplanır/gerçek veritabanına karşı çalıştırılır; LLM cevabın doğruluğuna karışmaz.
- **Dış setlerden filtrelenmiş (76.938 soru):** TURSpider ve Cognipeer; altın sonuç yeniden çalıştırılarak hesaplandı, soru–SQL uyumu kaynak sete bağlı (§11).
- **LLM ile doğrulanmış (6.907 soru):** MEB tekli ve çapraz. Cevap kitap pasajına dayanır, doğruluğu LLM tutarlılık kontrolü ve hakem modelle sağlanır. Bu güvence kesin değil; örneklem denetimlerinde düşük oranlı etiket hataları görüldü.

Ortak ilkeler:

- **Kolay soru yok.** Hesaplamada tek adımlı sorular bilerek üretilmedi (yalnız orta ve zor). Solver setinde aceleci (açgözlü) çözümün doğru cevabı bulduğu örnekler atıldı.
- **Zorluk "kapalı kitap" ölçülür.** Model yalnız soru metnini görür; kaynak pasaj ya da araç verilmez (solver kodlu set hariç; orada standart Python izinlidir).
- **API:** Bütün LLM çağrıları DeepInfra üzerinden yapıldı (OpenAI uyumlu uç nokta; büyük işler için Batch API). Erken bulmaca ve hesaplama puanlamalarında DashScope (Qwen) kullanıldı.

---

## 1. Bulmaca (3.000)

**Amaç:** Türkçe mantık bulmacaları; cevabı yapısal veriden kesin olarak hesaplanır.

**Tipler ve sayılar:**

| Dosya | Tip | Kolay | Zor | Toplam |
|---|---|---|---|---|
| `bulmaca_dataset.jsonl` | sıralama | 200 | 200 | 400 |
| | zebra (Einstein) | 225 | 225 | 450 |
| | doğrucu/yalancı | 200 | 200 | 400 |
| | akrabalık | 225 | 225 | 450 |
| | yön | 200 | 200 | 400 |
| `yeni_tipler_dataset.jsonl` | nesne takibi | 140 | 60 | 200 |
| | sayaç takibi | 210 | 90 | 300 |
| | zaman aritmetiği | 140 | 60 | 200 |
| | sahiplik zinciri | 140 | 60 | 200 |

**Üretim:** Her tip için ayrı bir Python üreticisi (`bulmaca_pkg/<tip>.py`) var. Üretici, tohum değeriyle (`seed = sıra no`) rastgele bir yapı kurar: kişiler, kısıtlar, aile ağacı ya da olay dizisi. Metni bu yapıdan Türkçe şablonlarla yazar. Zorluk parametreyle ayarlanır; örneğin sıralamada kolay 4 kişi, zor 7 kişi; zebrada 3 ve 4 ev; doğrucu/yalancıda 3 ve 5 kişi. İlk 1.500 + 800 kayıttan sonra, model ölçümünde zorluk gösteren tipler hedefli olarak genişletildi (`extend.py`, +700).

**Doğrulama:** Doğrulama metin üzerinden değil, kayıttaki `meta` yapısından yapılır (kısıt listesi + çözüm).

- Sıralama, zebra ve doğrucu/yalancı: Bütün olası durumlar taranır ve **tam olarak bir çözüm** olduğu kontrol edilir. Birden fazla çözüm varsa kayıt yazılmaz.
- Akrabalık: Cevap aile grafiği üzerinden hesaplanır (amca/dayı, hala/teyze, babaanne/anneanne ayrımı dahil).
- Yön, nesne takibi, sayaç takibi, sahiplik zinciri ve zaman aritmetiği: Olaylar simüle edilerek hesaplanır.
- `main.py --verify`, bütün seti yeniden doğrular (3.000/3.000 geçer).

**Türkçeye özgü katman:** Hal ekleri (yönelme, belirtme, bulunma, "-daki"), belirli/belirsiz nesne ayrımı ve akrabalık terimleri. Ünlü uyumu hataları üretim sırasında elle örneklenerek düzeltildi.

**Zorluk ölçümü:** 180 soruluk tabakalı örneklem (tip × zorluk başına 10), "gerçek eşleşme" ölçütüyle. Kural tabanlı eşleşme + Mistral-Small-24B hakem kullanıldı; hakem kararlarının bir kısmı elle denetlendi.

| Model | Doğru |
|---|---|
| openai/gpt-oss-20b | %76,1 |
| deepseek-ai/DeepSeek-V3 | %72,8 |
| nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B | %92,8 |

Sayaç takibi model boyutundan bağımsız olarak ~%60'ta kaldı. Akrabalık küçük modelde zayıf (%35–40).

**Maliyet:** Üretim yerel ve ücretsiz. Ölçüm toplamı < $0,40.

**Kodlar:** `kodlar/bulmaca/` (üreticiler, `main.py`, `extend.py`, puanlama ve hakem betikleri).

---

## 2. Hesaplama (14.616)

**Amaç:** Formül ya da kural ile kesin cevabı olan çok adımlı hesap ve biçim üretme soruları. LLM üretimde ve doğrulamada kullanılmadı.

| Kategori | Soru | Orta / Zor | Alt tip | Cevap nasıl hesaplanır |
|---|---|---|---|---|
| Birim dönüşümü | 2.400 | 900 / 1.500 | 8 (zincir dönüşüm, ters problem, çapraz birim, sıcaklık zinciri…) | Çarpan zinciri, tam |
| Excel formülü | 2.100 | 900 / 1.200 | 7 (koşullu sayma/toplam, SUMPRODUCT, iç içe ortalama…) | Formül + tablo; sonuç Decimal + Excel ROUND kuralıyla hesaplanır, 2.100'ünün tamamı gerçek LibreOffice'e karşı doğrulandı (aşağıya bakın) |
| Fizik hesabı | 2.400 | 1.200 / 1.200 | 8 (Newton, iş-güç, enerji korunumu, momentum…) | Elle doğrulanmış formül bankası; zor sorular en az 2 formül zincirler |
| JSON üretimi | 1.200 | 600 / 600 | 4 (düz ve iç içe nesneler) | Kayıtla birlikte JSON Schema; üretimde `jsonschema` ile kendini doğrular |
| Kimya hesabı | 1.116 | 128 / 988 | 7 (mol kütlesi, molarite, seyreltme, stokiyometri, pH…) | ~34 gerçek bileşiklik sabit havuz + atom ağırlıkları + denkleştirilmiş tepkimeler |
| Matris işlemleri | 2.100 | 900 / 1.200 | 7 (determinant, ters matris elemanı, iz, doğrusal sistem…) | sympy ile tam (rasyonel) hesap |
| Tarih hesaplama | 2.100 | 900 / 1.200 | 7 (gün farkı, iş günü, saat dilimi, ISO hafta…) | Python `datetime` (artık yıl, ay uzunlukları dahil) |
| XML üretimi | 1.200 | 600 / 600 | 4 | Üretilen XML tekrar ayrıştırılıp kaynak sözlükle tür korunarak birebir karşılaştırılır |

**Üretim:** Her kategori için şablon tabanlı bir üretici (`gen_*.py`) var. Parametreler rastgele, ama gerçekçi aralıklardan seçiliyor. Aynı parametre birleşimi ikinci kez gelirse atlanıyor (`common.py`, kanonik anahtarla tam tekrar ayıklama). Kimya hesabı, uydurma bileşik üretmemek için sabit bir gerçek bileşik havuzu kullanıyor. Bu yüzden bazı alt tipler (mol kütlesi 34, pH 26) birleşim tavanına takıldı. Her kayıtta `dogrulama_yontemi` alanı var (ör. `sympy_exact`, `datetime_exact`, `xml_roundtrip_validation`).

**Kalite:** Üreticiler yazıldıktan sonra örnekler elle okundu. Kontrol edilenler: sayısal doğruluk, Türkçe ek uyumu ("Trabzon'da"), gerçekçilik (ör. 18 yaşında doktor yok, kategoriye uymayan ürün yok).

**Tabloda olmayan bölge düzeltmesi (26 Ekim 2026):** `kosullu_sayma_toplam` sorularının 33/300'ünde sorulan bölge tabloda hiç yoktu, cevap 0'dı (COUNTIF/SUMIF tabloya bakmadan da 0 verir, soru anlamsız). `gen_excel.gen_kosullu_sayma`: bölge yine `BOLGELER`'den çekilir; tabloda yoksa tablodaki bölgelerden belirlenimci olarak (`BOLGELER` sırası mod tablodaki bölge sayısı) yenisi seçilir. Rastgele sayı akışı değişmediği için tohum 21, 300/alt tip ile yeniden üretimde yalnız bu 33 kayıt değişti (2.067 kayıt bayt bayt aynı, kimlikler aynı). Yeniden üretim sonrası cevabı 0 olan soru: 0. `excel_dogrula.py` 2.100 kayıtta kayıtlı≠motor 0, LibreOffice≠motor 0, formulas 280/0. Birleşik dosya yeniden kuruldu (18.135 satır, 33 satır değişti).

**Excel formülü yuvarlama düzeltmesi (20 Ekim 2026):** `beklenen_sonuc` eskiden Python `float` + `round()` ile hesaplanıyordu (`dogrulama_yontemi = python_mirror_excel_semantics`). Python `round()` çifte yuvarlama (half-to-even) yapar ve ikili float üzerinde çalışır (`round(2.675, 2) = 2.67`). Excel/LibreOffice `ROUND()` ise sıfırdan uzağa yuvarlar ve sayıyı önce 15 anlamlı basamağa indirir (`=ROUND(2.675;2) = 2,68`). Denetim (`hesaplama/excel_dogrula.py`): her sorunun tablosu soru metninden geri okundu, gold formül üç bağımsız motorla hesaplandı:

| Motor | Kapsam | Kayıtlı `beklenen_sonuc` ile fark (düzeltme öncesi) | Motorlar arası fark |
|---|---|---|---|
| `excel_motor.py` (Decimal + ROUND_HALF_UP, kendi formül yorumlayıcısı) | 2.100 | 24 | — |
| LibreOffice 7.3.7.2 headless (`.xlsx` → csv, yüklemede yeniden hesap) | 2.100 | 24 (aynı satırlar) | 0 |
| `formulas` 1.3.4 (Python Excel motoru) | 280 (alt tip başına 40) | — | 0 |

24 hatalı satırın alt tiplere dağılımı: `tek_hucre_yuzde_hesabi` 17, `kosullu_ortalama` 5, `temel_istatistik_fonksiyonu` 1, `ic_ice_ortalama_yuvarlama` 1. Hepsi tam yarım basamak durumu: 1 tanesi formülün kendi `ROUND`'u (ortalama tam 3375,25; kayıtlı 3375.2, Excel 3375.3), 23'ü `common.fmt_num()`'un 3 basamaklı gösterim yuvarlaması (ör. `=C3*(1+25/100)` tam 5321,0875; kayıtlı 5321.087, doğrusu 5321.088). Yuvarlama dışında semantik fark bulunmadı (LibreOffice ile 2.100/2.100 aynı). Not: üretici AVERAGEIF'te en az bir eşleşmeyi garanti ediyor (eşleşme yoksa Excel/LO `#DIV/0!` verir); SUMPRODUCT'a metin sütunu girmiyor (LO metni 0 sayar).

Düzeltme: `common.fmt_num()` ve `gen_excel.py`'deki `ROUND` hesabı Decimal + ROUND_HALF_UP'a çevrildi (15 anlamlı basamağa indirgeyerek), set aynı tohumla (21) yeniden üretildi. Yalnız bu 24 satırın `beklenen_sonuc`'u değişti; soru ve formüller birebir aynı. Yeni `dogrulama_yontemi`: `decimal_excel_round+libreoffice_capraz`. Yeniden denetim: 0 fark. `verifiable_data_birlesik.jsonl` yeniden oluşturuldu (yalnız 2.100 Excel kaydının `orijinal` alanı değişti). Puanlayıcı formül metnini karşılaştırdığı ve `beklenen_sonuc`'u yalnız yedek kontrol olarak kullandığı için ölçülen zorluk etkilenmez.

**Türkçe cevap alanı (21 Ekim 2026):** Her kayda `cevap_tr` eklendi: `cevap`'taki İngilizce formülün Türkçe Excel yazımı (`grade.en_to_tr_formul`; ör. `=SUMIF(D2:D11,"Marmara",B2:B11)` → `=ETOPLA(D2:D11;"Marmara";B2:B11)`). Set aynı tohumla yeniden üretildi; değişen tek alan `cevap_tr` (2.100/2.100). Denetim: 2.100/2.100 `cevap_tr` puanlayıcıda doğru, Türkçeden geri çeviri 2.100/2.100 `cevap` ile aynı token dizisi. `verifiable_data_birlesik.jsonl` yeniden oluşturuldu (yalnız 2.100 Excel kaydının `orijinal.cevap_tr` alanı eklendi).

**Soruda istenen yazım (22 Ekim 2026):** Altın cevap (`cevap`) İngilizce Excel formülü olduğundan her sorunun ilk paragrafının sonuna şu cümle eklendi: "Formülü İngilizce Excel yazımıyla verin (İngilizce fonksiyon adları, örneğin SUM, IF; bağımsız değişken ayracı virgül, ondalık ayracı nokta)." (`grade.EXCEL_DIL_CUMLESI`, `gen_excel.py` içinde `excel_dil_ekle`). Gerekçe: dil belirtilmeyince modeller çoğunlukla İngilizce yazıyordu, ama sorunun Türkçe olması ve cevabın dilinin tanımsız kalması belirsizlikti; Türkçe yazım istendiğinde modeller fonksiyon adı uydurdu (§9, Türkçe formül istemi). `cevap_tr` ek alan olarak kalır; puanlayıcı Türkçe yazılmış doğru formülü de kabul etmeye devam eder. Set aynı tohumla (21, alt tip başına 300) yeniden üretildi; yedekle karşılaştırma: değişen tek alan `soru` (2.100/2.100, yalnız eklenen cümle). `verifiable_data_birlesik.jsonl` yeniden oluşturuldu: 18.135 satır, değişen 2.100 (yalnız `excel_formulu`). Not: §2'deki model ölçümleri cümle eklenmeden önceki soru metniyle yapılmıştır.

**Excel formülü puanlaması: çalıştırarak + eşitlik toleransı (21 Ekim 2026):** Eski puanlayıcı modelin formülünü gold formülle metin olarak karşılaştırıyordu. Kayıtlı model cevapları elle incelendi, iki gerçek hata bulundu: (1) Türkçe Excel'in gerçek COUNTIF adı `EĞERSAY` sözlükte yoktu (yalnız var olmayan `SAYEGER`); doğru `=EĞERSAY(D2:D8;"Ege")` cevapları yanlış sayılıyordu (8 cevap). (2) Eşdeğer ama farklı yazılmış formüller reddediliyordu (`=ORTALAMA(EĞER(D2:D10="Karadeniz";C2:C10))`, 4 cevap; `$C$2` mutlak başvuru, `SUMPRODUCT(B*C)` gibi biçimler de aynı riskteydi). Yeni `grade_excel`: önce eski metin eşleşmesi; olmazsa modelin formülü `excel_motor` ile **çalıştırılır** ve gold formülle aynı sonucu vermesi istenir. Sınama kitapları: soru tablosu; döngüsel kaydırma (her hücre başka satırın değerini alır, sabit hücre adresi `=C7` gibi cevapları keser); tek hücreli koşullarda eşik ve eşik+1 değerli sınır kitapları (`>`/`>=`); ROUND alt tipinde yuvarlanacak değeri birimin 0,2 ve 0,8'ine oturtan iki kitap (ROUNDUP/ROUNDDOWN/TRUNC); koşullu sorularda ölçüt metnini aralığın ilk ve son satırına yazan kitap (eksik aralık); 6 rastgele kitap (yarısında 4 basamaklı fiyat). En az bir hücre başvurusu şart; yalnız sayı ya da sabit yazan cevap yanlış. Var olmayan fonksiyon adları (`TOPLAM`, `YUVARLAK`, `ORTALAMA.EĞER`, `TOPLAM.ÇARPIM`…) gerçek Excel'de `#AD?` verdiği için yanlış kalır.

**Tolerans:** Motorlar arası fark yalnız tam yarım değerde çıkar (Excel/LibreOffice sıfırdan uzağa, Python çifte yuvarlama, ikili float bazen aşağı). Gold formülde ROUND varsa her kitapta gold değer üç kuralla (sıfırdan uzağa, çifte, aşağı) hesaplanır ve üçü de kabul edilir; tam yarım yoksa üçü aynıdır, yani tolerans ROUND'u unutmuş ya da ROUNDUP yazmış cevaplara kapı açmaz. Sayılarda ayrıca göreli 1e-9 (LibreOffice yedeğinin float gürültüsü). Sabit "bir birim" toleransı denendi ve reddedildi: ROUND'suz `=AVERAGE(...)` 300/300 geçiyordu.

**Sınama (`hesaplama/excel_puanlama_sinama.py`, 2.100 soru):** doğru biçimler — gold, gold'un Türkçe Excel karşılığı (`;` ayraçlı, `EĞERSAY` dahil), `$` mutlak başvurulu gold — 2.100/2.100 kabul; alt tip başına eşdeğerler (AVERAGEIFS, SUMIF/COUNTIF, ORTALAMA(EĞER()), SUMPRODUCT(B*C), ROUND(SUM/COUNT), C*1,18, ters koşullu EĞER) 300/300 kabul; bilinen yanlış kalıplar (sabit sayı, max/min hücresini sabit yazma, ROUND unutma, ROUNDUP, başka hücre, SUM(B)*SUM(C), hep aynı metni döndüren EĞER, yalnız sayı) hepsinde 0 kabul. Kayıtlı model cevaplarında eski→yeni puanlama: `skor_sonuclari_deepinfra.jsonl` 4 yanlış→doğru, `skor_sonuclari.jsonl` 8 yanlış→doğru, doğru→yanlış 0; hepsi elle doğrulandı. Aynı dosyadaki 260 soruluk ölçümde etkisi: gemma-3-27b-it +3 soru, DeepSeek-V3 +1 soru, Qwen3.8-27B ve Nemotron 0. Not: yukarıdaki %93,8 / %97,3 kayıtlı `ok` alanından; eski puanlayıcıyla yeniden hesap gemma için %91,9 veriyor (Excel dışı kategorilerden gelen, bu düzeltmeden önceye ait bir tutarsızlık; incelenmedi).

`fmt_num()` değişikliği diğer kategorileri de etkiliyor ama diskteki dosyalar yeniden üretilmedi: eski `fmt_num` ile üreticiler diskteki dosyaları birebir veriyor, yenisiyle `birim_donusumu` 8, `fizik_hesabi` 36, `kimya_hesabi` 3 satırda son basamak 0,001 kayıyor (hepsi tam yarım durumu; bu kategoriler ≥%1 toleransla puanlandığı için puanı etkilemez; birim `ters_problem`'deki 1 satırda soru metnindeki sayı da değişiyor). `run_all.py` yeniden çalıştırılırsa bu 47 satır değişir.

**Zorluk ölçümü:** Kategori başına örneklemle ölçüldü; puanlayıcıdaki biçim hataları (LaTeX gösterimi, Excel Türkçe fonksiyon adları, kesir gösterimi) bulunup düzeltildikten sonraki sonuçlar:

| Model | Doğru |
|---|---|
| google/gemma-3-27b-it | %93,8 |
| Nemotron-3-Ultra-550B | %97,3 |

JSON, XML ve kimya büyük ölçüde çözülüyor. Tarih, matris ve fizik daha ayırt edici.

**Maliyet:** Üretim yerel ve ücretsiz. Ölçüm toplamı birkaç dolar.

**Kodlar:** `kodlar/hesaplama/` (`common.py`, `entities.py`, `gen_*.py`, `run_all.py`, `grade.py`, puanlama betikleri, `excel_motor.py` (Decimal Excel motoru + LibreOffice/formulas çapraz hesap), `excel_dogrula.py` (Excel seti denetimi)).

---

## 3. MEB tekli konu (2.914)

**Kaynak:** 12 MEB ortaöğretim ders kitabı: Fizik, Kimya ve Biyoloji, 9–12. sınıf (`kitaplar/{ders}_{sinif}.pdf`). Kitaplar dijital dizgili olduğu için metin `pdftotext` ile doğrudan okundu (OCR yok). `extract.py`, ünite/konu başlıklarını numaralı başlık kalıplarından ayırıp konu bazlı JSON korpus çıkardı (`korpus/{ders}_{sinif}.json`).

**Üretim (v6 hattı, `pipeline_v6_deepinfra.sh`):**

1. Her konu metni ~1.800 karakterlik parçalara bölündü (`chunking.py`).
2. **Üretici:** `deepseek-ai/DeepSeek-V3`. Her parçadan, pasajdaki bilgiye dayanan, tip etiketli sorular yazdı. Tipler: kavram-mekanizma, karşılaştırma, tahmin-uygulama, sayısal çıkarım, süreç sıralama.
3. **Gidiş-dönüş tutarlılık kontrolü:** Aynı model soruyu pasajla birlikte, üretilen cevabı görmeden yeniden cevapladı. İki cevap birebir uyuşmazsa hakem model (aynı model) anlamca eşdeğer olup olmadıklarına karar verdi. Tutarsız sorular (`self_consistent = false`) atıldı.
4. **Yakın kopya ayıklama:** Gömü benzerliğiyle (`BAAI/bge-m3`) yapıldı.

**Süzgeçler ve sayılar:**

| Adım | Soru |
|---|---|
| Ham üretim (12 kitap) | 4.108 |
| Tutarlılık + yerel tekrar + gömü tekrar ayıklama sonrası (`verifiable_dataset_v6.jsonl`) | 3.507 |
| Kısa cevap kuralı sonrası (`…_v6_kisa.jsonl`) | 2.946 |
| Anlamca tekrar ayıklama sonrası (`…_v6_kisa_tekrarsiz.jsonl`) | 2.914 |

- **Kısa cevap kuralı** (`soru_kurallari.py`): Cevap en fazla 5 kelime ve tek parça olmalı. Açıklama isteyen kalıplar ("nasıl açıklanır", "nedeni nedir", "neden?", "ne söylenebilir"…) atıldı.
- **Anlamca tekrar:** Aynı sınıf içinde bge-m3 benzerliği ≥ 0,85 olan çiftler DeepSeek-V4-Flash'a soruldu: aynı soru mu, cevaplar çelişiyor mu? Aynı sorulardan biri tutuldu, çelişkilerde yanlış cevaplı olan atıldı.

**Dağılım:**
- Sınıf: 9 → 689, 10 → 576, 11 → 947, 12 → 702.
- Ders: fizik 1.160, kimya 905, biyoloji 849.

**Zorluk ölçümü:** Mistral-Small-3.2-24B, kapalı kitap, bütün sette: **%69,2** (2.017/2.914). Kayıtta `mistral24b_cevap` ve `mistral24b_dogru` alanları var. Yanlış sayılan 28 cevaplık elle denetimde 1–2 sınırda vaka dışında hepsi gerçek yanlıştı.

**Maliyet:** Üretim $4,06 (log'dan). Tekrar ayıklama ~$0,02. Mistral ölçümü ~$0,4.

**Bilinen sınırlar:**
- Doğruluk LLM tutarlılığına dayanıyor; kesin değil.
- Tip etiketlerinde yazım farkları var ("karşılaştırma" ile "karsilastirma"); birleştirmede normalize edilmeli.
- 76 sorunun (%2,6) cevabı yalnızca "artar", "azalır" ya da "değişmez" (tahminle tutturulabilir).
- Kitapların künyesi (basım yılı, yayınevi) ve kullanım koşulları rapora eklenmeli.

**Kodlar:** `kodlar/meb_tekli/`. Kısa cevap süzgeci ve son birleştirme tek seferlik komutlarla yapıldı; kullanılan kurallar `soru_kurallari.py`'de.

---

## 4. MEB çapraz konu (3.993)

**Amaç:** Farklı derslerden iki konuyu birleştiren sorular. Örneğin bir biyoloji olayının kimya kuralıyla açıklanması.

**Kaynak:** Aynı 12 MEB kitabından çıkarılan korpus.

**Üretim (`run_capraz_deepinfra.py`, istem `secmeli_v4` → `secmeli_v5`):**

1. **Pasaj seçimi:** Her turda modele üç dersten (fizik, kimya, biyoloji) birer konu pasajı verildi. Konular rastgele seçildi, aynı sınıf düzeyinden.
2. **Üretici:** `zai-org/GLM-5.3-Flash`. Farklı derslerden iki pasaj seçip ikisini de gerektiren sorular yazdı: cevap, gerekçe ve seçilen pasajlar.
   - "Ortak ilke uydurma" ve süs bağlantı yasaklandı.
   - Bir dersin senaryo, ötekinin kural olarak kullanılmasına izin verildi.
   - `secmeli_v5`, kısa cevap kurallarını isteme ekledi ve kurala uymayan sorular üretim anında atıldı (`--kisa-cevap`).
3. **Hakem süzgeci** (`hakem_suzgec.py`): `deepseek-ai/DeepSeek-V4-Flash-0731` her soruyu "tut" ya da "ele" diye işaretledi. Hakem şunları gördü: soru, iki kaynak pasaj, etiket cevap, gerekçe ve pasajsız bir çözücünün cevabı.
   - Ele nedenleri: zorlama bağlantı, yanlış etiket, birden çok savunulabilir cevap, eksik bilgi.
   - Ölçüt kullanıcı kararıyla "gevşek" tutuldu: senaryo + kural birleşimi kabul.
4. **Kısa cevap kuralı:** İlk 1.000'lik parti sonradan süzüldü (`kisa_suz.py`).

**Süzgeçler ve sayılar:**

| Adım | Soru |
|---|---|
| Üretilen (iki parti) | 5.723 |
| Hakemden geçen | 4.569 |
| Kısa cevap + tam/yakın tekrar ayıklama sonrası (`capraz_final.jsonl`; aynı sınıf, kelime Jaccard ≥ 0,6) | 4.132 |
| Anlamca tekrar ayıklama sonrası (bge-m3 ≥ 0,85 + V4-Flash kararı; 139 atıldı) | 3.993 |

**Dağılım:**
- Sınıf: 9 → 1.013, 10 → 1.006, 11 → 959, 12 → 1.015.
- Ders çifti: kimya+biyoloji 2.027, fizik+kimya 1.165, fizik+biyoloji 801.
- Tip: tahmin-uygulama 2.055, hesaplama 860, karşılaştırma 577, sebep-sonuç 501.
- İstem: v4 856, v5 3.137.

**Zorluk ölçümü:** Mistral-Small-3.2-24B, kapalı kitap: **%70,3** (2.806/3.993). Hesaplama tipinde yalnız ~%50.

**Maliyet:** Üretim + hakem $7,15. Tekrar ayıklama ~$0,04. Mistral ölçümü ~$0,4.

**Bilinen sınırlar:**
- Cevabın doğruluğu LLM hakemine dayanıyor.
- Önceki denemelerde hakemin "zorlama" bağlantıları kaçırdığı görüldü; bu yüzden ölçüt ve istem birkaç kez revize edildi.
- 509 sorunun (%12,7) cevabı yalnızca "artar", "azalır" ya da "değişmez". Bunlar tahminle tutturulabilir (şans başarısı ~%33–50); zorluk ölçümünü şişirir. Raporda ayrıca belirtilmeli ya da bu sorular ayrı etiketlenmeli.

**Kodlar:** `kodlar/meb_capraz/` (`generate_questions.py` istemleri içerir; `sinif.sh` üretim + hakem döngüsü).

---

## 5. Solver soruları: optimizasyon (4.986)

**Amaç:** Cevabı kesin olarak hesaplanabilen, dikkatli akıl yürütme ya da arama gerektiren gerçekçi planlama soruları. LLM'in kendi bilgisinden bağımsız olarak zorlaştırılabilen bir soru türü.

**Kaynak:**
- **Meslek kostümleri için konu ağacı:** Türkçe Konu Ağacı'nın (`konu_agaci/agac_v2/kanonik_1.jsonl`) "meslek" bağlamlı disiplinlerinden 400'ü kullanıldı. Ağaç: ISCED-F 2013'ün 92 detaylı alanı altında 3.794 disiplin; kaynakları Halk Eğitim kursları, üniversite programları, MEB dersleri, OpenAlex, MeSH, IAB ve Wikipedia. Hugging Face'te gizli olarak yayında: `hubble658/turkce-konu-agaci`.
- **Problem yapıları** programın kendisidir. Dış veri kullanılmadı.

**Aileler:**

| Aile | Soru | Kurallar (her örnekte işe yarayanlar kalır) |
|---|---|---|
| Seçim: adaylardan en değerli alt kümeyi seçmek, en büyük toplam | 1.750 | Bütçe, adet aralığı, ortalama sınırı, en az k kategori, gruptan en fazla m, uyumsuz ikili, bağımlılık |
| Atama: işleri kişilere dağıtmak, en küçük toplam maliyet | 1.743 | Kapasite, yetki/sertifika, kişi başına en fazla iş, uyumsuz işler, birlikte yapılacak işler |
| İş sıralama: tek kaynakta, en küçük ağırlıklı gecikme cezası | 1.493 | Hazır olma zamanı, öncelik, kesin bitiş, bakım arası |

**Setler:**
- **Orta (araçsız), 2.993 soru:** seçim 14/16/18 aday; atama 10–12 iş × 4–5 kişi; iş sıralama 8/9/10 iş.
- **Zor (Python izinli, yalnız standart kütüphane, 60 sn), 1.993 soru:** seçim 60/70/80 aday; atama 30–40 iş × 8–10 kişi; iş sıralama 16/17/18 iş.

Zor setteki boyutlarda kaba kuvvet imkânsız (ör. 2^60 olasılık). Soru, verimli ve kesin bir algoritma yazmayı gerektirir.

**Üretim adımları (`uretim5k.py`, `sablon.py`, `sablon2.py`):**

1. **Kostüm:** `deepseek-ai/DeepSeek-V4-Flash-0731`, her disiplin için JSON yazdı: nesne/kişi/iş adları, birimler, gerçekçi değer aralıkları ve sahne. Uygunluk kontrolünden geçmeyenler atıldı. Disiplin başına bir çağrıyla 10 farklı giriş paragrafı yazıldı; içinde rakam olan paragraflar atıldı.
2. **Örnek kurma:** Program rastgele bir örnek kurar; tohum değeri soru kimliğidir, yani üretim yeniden yapılabilir.
3. **Kesin çözüm:** OR-Tools CP-SAT 9.15 en iyi değeri bulur ve en iyiliği kanıtlar. Kanıtlanamayan örnek atılır.
4. **İşlevsiz kural ayıklama:** Her kural tek tek kaldırılıp problem yeniden çözülür. En iyi değeri değiştirmeyen kural metinden çıkarılır; kalanlar yeniden sınanır. Böylece metindeki her kural cevabı etkiler. En az kural sayısı: seçim/atama 4, sıralama 3.
5. **Tuzak koşulu:** Aceleci bir yöntemin (değer/maliyet oranına göre seçim, en ucuz kişiye atama, en erken teslim sırası) bulduğu değer doğru cevaba eşitse örnek atılır. Cevap 0 da olamaz.
6. **Metin:** Kurallar ve tablolar programdan yazılır (her kural için 3 farklı kalıp; kural sırası karışık). Metin ile cevap arasında uyuşmazlık olamaz. Türkçe büyük/küçük harf dönüşümü (I/İ) ayrıca ele alındı.

**Doğrulama:**
- Solver sonucu küçük örneklerde bağımsız kaba kuvvet koduyla karşılaştırıldı: seçim 15 aday, atama 10×4, sıralama 8 iş. Toplam 16 örneğin hepsi eşleşti.
- Küçük örneklerde, modellerin "en iyiden daha iyi" görünen cevaplarının hep kuralları bozan geçersiz çözümler olduğu görüldü.
- 12 soruda kostümden gelen bozuk "i̇" karakteri düzeltildi.

**Sayılar:**
- 5.000 hedefin 14'ünde solver en iyiyi süresinde kanıtlayamadı → **4.986 soru**.
- 400 disiplin; bütün metinler farklı.
- Kural sayısı: 3 → 1.133, 4 → 2.757, 5 → 868, 6 → 207, 7 → 21.

**Zorluk ölçümü — orta** (200 soruluk tabakalı örneklem, her soru 2 deneme, DeepInfra Batch):
- Düşünen V4-Flash: `reasoning_effort=high`, 32k token. Orta sette kod yok, model doğrudan sayısal/liste cevap verir.

| Set | Aile | Düşünen V4-Flash | Mistral-24B | Flash'ın iki denemede de çözemediği |
|---|---|---|---|---|
| Orta | Seçim | %62 | %1,5 | 6/34 |
| Orta | Atama | %71 | %3 | 5/33 |
| Orta | İş sıralama | %52 | %0 | 9/33 |

**Zorluk ölçümü — zor** (ayrı 50 soruluk örneklem — seçim 17, atama 17, iş sıralama 16 —, her soru 2 deneme, DeepInfra Batch; `olcum_kod5tur.py`):
- Zor sette modelin yazdığı kod kum havuzunda 60 sn sınırla çalıştırıldı. Çalışmayan kod için yalnız çalışma hatası bildirilip **en fazla 4 ek düzeltme turu (toplam 5 deneme)** verildi; cevabın doğruluğu modele hiçbir turda söylenmedi. İlk ölçümde (bu tabloyu değiştiren, tek düzeltme turlu ölçüm) Flash zor sette %12–%29 arasındaydı; 5 tur hakkıyla yeniden ölçüldü, Mistral-24B'ye de aynı 5 tur hakkı verildi.

| Set | Aile | Flash, 1. deneme | Flash, 5 turda | Mistral-24B, 5 turda | Flash'ın hiçbir turda çözemediği | Flash ort. tur |
|---|---|---|---|---|---|---|
| Zor | Seçim | %38,2 | %64,7 | %0 | 3/34 | 2,03 |
| Zor | Atama | %14,7 | %73,5 | %0 | 0/34 | 2,41 |
| Zor | İş sıralama | %68,8 | %87,5 | %0 | 0/32 | 1,25 |

**Ne gördük:**
- Orta set hedefte. Düşünen Flash %52–71 arasında, yani çözülebilir ama kolay değil. 24B neredeyse hiç çözemiyor. Sonuçlar pilotla da tutarlı; sorular istikrarlı biçimde aynı zorlukta çıkıyor.
- Zor sette, 5 tur hakkıyla, üç aile de hedefte: Flash %65–88 arasında çözüyor, yani zor ama yılmıyor. 2 tur hakkıyla ölçülen önceki tabloya göre bütün aileler belirgin yükseldi (özellikle atama %21→%74).
- Düzeltme turları gerçekten işe yarıyor: Flash ortalama 1,25–2,41 tur kullanıyor (yani çoğu soru 1-2 düzeltmede çözülüyor) ve hiçbir turda çözemediği soru sayısı çok düşük (seçimde 3/34, diğer iki ailede 0).
- Mistral-24B, 5 tur hakkına rağmen zor sette hâlâ hiçbir soruyu çözemedi (%0, üç ailede de). Kodları ya çalışma hatası veriyor ya süreyi aşıyor ya da yanlış cevaba varıyor; bu bir ölçüm kusuru değil, 24B'nin bu zorlukta gerçek bir yetersizliği.

**Maliyet:** Üretim (kostüm + giriş) ~$0,20. Orta ölçümü ~$2,9. Zor'un 5-tur ölçümü: ilk deneme $0,639 + düzeltme turları $0,859 = **$1,50** (her iki rakam da dosyadan: `merdiven.jsonl`'daki `maliyet` alanları ve `harcama_duzelt5.json`). Solver üretimi yerelde çalıştı (iki oturumda toplam ~6 saat, 14 çekirdek).

**Bilinen sınırlar:**
- Kural cümleleri şablon kalıplarından geliyor; çeşitlilik sınırlı.
- Zor iş sıralama, düşünen model için görece kolay.
- Kostüm adları LLM yazdığı için az sayıda tuhaf ad olabilir.

**Kodlar:** `kodlar/solver/` (üretim + ölçüm) ve `kodlar/konu_agaci/` (ağacın üretimi). Kopyalar birbirini göreli yollarla içe aktarır; çalıştırmak için asıl klasör düzeni gerekir (`konu_agaci/agac_v2/`, `konu_agaci/pilot/`).

---

## 6. SQL: Türkiye açık veri — il/ilçe veritabanları (20.138)

**Amaç:** Gerçek belediye açık veri portallarından kurulmuş SQLite veritabanlarına karşı, LLM'in İCAT ETMEDİĞİ, Python şablonlarından deterministik kurulan Türkçe soru + gold SQL + gerçek sonuç üçlüleri. Hiçbir soru/SQL/sonuç LLM tarafından yazılmaz ya da doğrulanmaz; her satır gerçek veritabanına karşı çalıştırılıp doğrulanır.

**Kaynak (veritabanı başına lisans):**

| Veritabanı | İlçe sayısı | Lisans |
|---|---|---|
| İstanbul (İBB) | 39 | İBB Açık Veri Lisansı (CC BY 4.0 eşdeğeri) |
| Kayseri | 16 | CC BY 4.0 (Kayseri BB Açık Veri Portalı) |
| Konya | 31 | CC BY 4.0 (Konya BB Açık Veri Portalı) |
| Trabzon | 18 | Trabzon BB Açık Veri Lisansı (ticari kullanım dahil, atıfla) |
| İzmir | 30 | CC BY 4.0 (İzmir BB) |
| Ankara | 25 | CC BY 4.0 (Şeffaf Ankara Açık Veri Lisansı) |
| Manisa | 17 | **DOĞRULANMADI** — mbb-odl-1.0 lisans sayfası 404, her satırda bu uyarı taşınıyor |
| Sakarya | 16 | Sakarya BB Açık Veri Lisansı (ticari kullanım dahil, atıfla) |
| Kadıköy, Tuzla | — (İBB'nin ilçe bazlı yayınları) | CC BY 4.0 (İBB Açık Veri Lisansı — ilçe bazlı yayın) |

**Üretim yöntemi — iki farklı üretici deseni, LLM yok:**

1. **Şablon + parametre/kategori taraması** (`<sehir>_sorular.py`, ortak harness `soru_ortak.uret()`): her soru tipi `t_<ad>(parametreler) -> (soru, sql, alt_tip, zorluk, sira_sutunu, n)` döndürür. `uret()` SQL'i gerçek DB'ye karşı çalıştırır; hata/boş sonuç/LIMIT-sınırında-eşitlik/aynı-şablondan-aynı-cevap durumlarında atlar. Hacim iki şekilde büyütüldü: (a) n/yıl/eşik parametrelerinin TÜM makul kombinasyonu denendi; (b) yüksek-kardinaliteli kategorik sütunlar (tesis türü, ürün adı, hizmet türü…) `itertools.permutations` ile ikili karşılaştırma şablonlarına (`"X sayısı Y'den fazla olan ilçeler"`, SUM CASE + HAVING) sokuldu — bu tek teknik Kayseri ve Trabzon hacminin çoğunu oluşturdu.
2. **Çok-tablolu zincir/"skeleton" üretimi** (`zincir_ortak.py`, İstanbul'un orijinal `skeleton_builder.py`/`uretim_pilotu.py` yönteminin genelleştirilmişi): aynı (varlık_id, yıl) anahtarını paylaşan tabloları `(varlık_id, yıl, deger)` şekline indirip (kategorik tablolar önce `SUM/COUNT ... GROUP BY` ile CTE'ye indirgenir), 2-5'li TÜM tablo kombinasyonlarını × ortak yılları × hangi metriğin sıralama kriteri (odak) × geri kalanların power-set'inin "ortalamanın üzerinde" filtresi (kısıt) olacağını dener, isteğe bağlı `RANK() OVER` eklenir. Dedup SONUCA göre yapılır (SQL metnine göre değil).

**Süzgeç hunisi (örnek — en büyük iki üretici):**

| Aşama | Aday | Üretilen |
|---|---|---|
| Konya zincir (7 metrik, 2-5'li kombinasyon × odak × kısıt power-set × n × window) | 11.584 | 2.632 (düzeltme öncesi 2.740) |
| İzmir zincir (4 mahalle-seviyeli metrik) | 1.192 | 319 (düzeltme öncesi 335) |
| Trabzon "kosullu" (59 tesis türünün 2'li tüm permütasyonu) | — | 2.491 (554 boş, 377 aynı-cevap elendi) |
| Kayseri "kosullu" (28 tesis türünün 2'li tüm permütasyonu) | — | 559 (143 boş, 54 aynı-cevap elendi) |

**Zincir düzeltmesi (21 Ekim 2026; belgeye 26 Ekim'de işlendi):** Konya ve İzmir zincir dosyalarında aynı soru metni farklı cevaplarla tekrar ediyordu (Konya 94 metin / 188 satır, İzmir 14 metin / 28 satır). Sebep: soruda adı geçmeyen bir metrik de INNER JOIN'e giriyor, o metrikte verisi olmayan ilçe/mahalle sessizce düşüyordu. Düzeltme: `zincir_ortak.build_sql(..., yalniz_gecenler=True)` ve `konya_skeleton.py` yalnız soruda geçen metrikleri (odak, kısıt, gösterilen) JOIN'e alıyor; soruya "Yalnız soruda geçen göstergelerin hepsinin o yıl verisi olan ilçeleri/mahalleleri değerlendirin…" eki kondu. Ayrıca `skeleton_builder.py`'de "okuma bilmeyen oranı" → "okuma bilmeyen oranı (%)" (gold yüzde), `izmir_skeleton.py`'de "askıda fatura kapanış sayısı" → "… kaydı sayısı" (gold COUNT(*), tabloda `fatura_adet` de var). Yeniden üretim sonucu: Konya zincir 2.740 → 2.632 (zor 2.540 → 2.432), İzmir zincir 335 → 319 (zor 272 → 256); orta sayıları değişmedi. Yeni dosyalarda tekrar eden soru metni 0; gold SQL'ler gerçek SQLite'a karşı yeniden çalıştırıldı, 2.951 satırda 0 uyuşmazlık (26 Ekim 2026). Eski dosyalar: `sql_arastirma/uretim/yedek_2026-10-21_zincir/`. Not: §8 çıktı-tahmini seti bu düzeltmeden önceki 20.262'lik havuzdan paketlendi.

**Doğrulama:** Program — her satırın `cevap` alanındaki SQL, kayıttan SONRA tekrar gerçek SQLite dosyasına karşı çalıştırılıp `orijinal.gercek_sonuc` ile birebir karşılaştırıldı. Bu oturumda üretilen/değiştirilen HER dosya için bu kontrol **%100 geçti** (0 uyuşmazlık) — İstanbul hariç tüm şehirler ve zincir dosyaları tek tek doğrulandı.

**Sayılar (zorluk dağılımıyla, `*_sorular.jsonl` + `*_zincir_sorular.jsonl` toplamı):**

| Şehir | Toplam | orta | zor |
|---|---|---|---|
| İstanbul | 12.375 | 312 | 12.063 |
| Kayseri | 784 | 674 | 110 |
| Konya | 2.902 | 336 | 2.566 |
| Trabzon | 2.823 | 2.734 | 89 |
| İzmir | 583 | 275 | 308 |
| Ankara | 124 | 100 | 24 |
| Manisa | 110 | 74 | 36 |
| Sakarya | 212 | 67 | 145 |
| Kadıköy | 107 | 43 | 64 |
| Tuzla | 118 | 61 | 57 |
| **Toplam** | **20.138** | | |

**Zorluk ölçümü:** `benchmark_coz.py` ile — solver'a SADECE şema (CREATE TABLE'lar + düşük-kardinaliteli TEXT sütunların gerçek değer envanteri, doğru büyük/küçük harfle) ve soru verilir, gold SQL gösterilmez; 3 deneme/soru; sonuç satır/sütun-sırası bağımsız + sayısal toleranslı karşılaştırılır. Modeller: `mistralai/Mistral-Small-3.2-24B-Instruct-2506` (24B), `deepseek-ai/DeepSeek-V4-Flash-0731` (Flash), `meta-llama/Meta-Llama-3.1-8B-Instruct` (8B).

20 soruluk örneklemlerle 24B+8B ölçümü bu belge yazılırken sürüyordu (`bench_tum_iller.py`); o ana kadar tamamlanan şehirler:

| Şehir | 24B | 8B | Not |
|---|---|---|---|
| Kayseri | %58,3 (35/60) | %13,3 (8/60) | |
| Konya | %20,0 (12/60) | %3,3 (2/60) | Zincir sorularının çoğu burada; 24B zincirin çok-metrik zincirlemesinde zorlanıyor |
| Trabzon | %21,7 (13/60) | %0,0 (0/60) | "Kosullu" (X sayısı Y'den fazla) sorularında 8B hiç başaramadı |

Kalan 6 şehir (İzmir, Ankara, Manisa, Sakarya, Kadıköy, Tuzla) ölçülüyor; sayılar tamamlanınca buraya eklenecek. **Daha önceki (24B+Flash, eski/daha küçük soru havuzuyla) ölçümler** bu oturumda bulunup düzeltilen 3 gerçek hatayı (aşağıda) kapsıyordu: düzeltme sonrası Ankara 24B %70,0→%88,3 / Flash %73,3→%90,0; Konya Flash %71,7→%98,3.

**Sonradan bulunan karşılaştırıcı hatası (2026-10-19):** `benchmark_coz.satir_esit` NULL değeri hiç eşleştiremiyordu; gold'unda NULL olan soru, model doğru yazsa bile her zaman başarısız sayıldı. Etkilenen sorular yalnız Ankara `karar_lag` (25 soru, setin %27'si; LAG'in ilk yılı NULL), Manisa `golet_lag` (1) ve Sakarya `tesissiz` (1). Bu 27 soru düzeltilmiş karşılaştırıcıyla yeniden çözdürüldü (`analiz/null_yeniden.py`, $0,013): eski karşılaştırıcıyla her ikisi %0; düzeltilmişle Ankara 24B %58,7 / Flash %92,0, Manisa 24B ve Flash %100, Sakarya 24B %0 / Flash %100. Yukarıdaki Ankara skorları bu soruları içeren örneklemlerde olduğundan düşük raporlanmış olabilir.

**Bu oturumda bulunan ve düzeltilen 3 gerçek hata sınıfı** (canlı benchmark ile keşfedildi, tahmin değil):
1. **Eksik kimlik/metrik alanı:** SQL'in SELECT ettiği bir sütun (ilçe/mahalle adı ya da sıralama kriterinin kendisi) soru metninin "listeleyin" kısmında açıkça istenmiyordu, sadece ima ediliyordu → model de atlıyordu (İzmir'de 3 şablon, Konya'da ~12 şablon düzeltildi).
2. **SQLite'ın Türkçe harf körlüğü:** `'İlkokul' LIKE '%ilkokul%'` SQLite'ta `0` döner (ASCII-only case-fold); DB'de değerler ALL-CAPS dururken soru metni title-case gösteriyordu. Solver'a verilen şemaya düşük-kardinaliteli sütunların TÜM gerçek değerleri yorum olarak eklendi (Kayseri'de 24B %15,0→%63,3).
3. **Python `.lower()`'ın Türkçe İ/I hatası:** Konya'da tarım ürünü adları soru metnine `.lower()` ile aktarılırken "mısır"→"misir", "kanatlı"→"kanatli" gibi bozuk çıkıyordu; `tr_lower()` yardımcı fonksiyonuyla düzeltildi.

Ayrıca gerçek **model sınırı** olarak kalan (bug değil, doğrudan SQL çalıştırılarak doğrulandı): 24B'nin `yapı_sayısı`/`konut_sayısı` sütunlarını karıştırması, `LAG()`'e gereksiz varsayılan değer koyması, tam sayı bölmesi (`SUM(x)/y` yerine `SUM(x)*1.0/y` gerekirken).

**Sakarya'da bulunan ve düzeltilen 3 şablon hatası (2026-10-20, 20 soruluk Flash-karşı-24B elle karşılaştırmasıyla bulundu — `_karsilastir.py`):**
1. `t_yogunluk`: SELECT nüfus yoğunluğunu hesaplıyordu ama soru metni "listeleyin" kısmında bu sütunu istemiyordu (yukarıdaki İzmir/Konya'daki aynı hata sınıfı) → soru metnine eklendi.
2. `t_evlenme`: aynı eksik-sütun hatası, "binde" oranı için → soru metnine eklendi.
3. `t_evlenme_dusus`: "fark" sütununun işareti (2025-2024, negatif) metinde belirtilmiyordu → açıkça yazıldı.
Üçü de düzeltilip yeniden üretildi, 196/196 satır gerçek DB'ye karşı yeniden doğrulandı.

**Flash<24B ters-skor teşhisi (2026-10-20):** Sakarya/Kayseri'de 24B'nin Flash'tan yüksek çıktığı sorular tek tek incelendi (yukarıdaki "model sınırı" listesine ek, iki yeni örnek):
- **Sakarya, "100 km²'ye düşen cami sayısı" (2 soru, Flash 0/3, 24B 3/3):** Flash `LEFT JOIN tesis_turleri tt ON t.tur_id=tt.tur_id AND tt.tur_adi='Cami'` yazıp `COUNT(t.tesis_id)` ile saydı — filtre JOIN'in ON koşulunda olduğu için COUNT o mahalledeki TÜM tesisleri sayıyor (Adapazarı'nda gerçek 163 cami yerine 448). Genuine, tekrar eden bir Flash SQL-yazım hatası; dataset/soru kusuru değil.
- **Kayseri, "X sayısı Y'den fazla olan ilçeler" (10/10 soru, Flash 10/10, 24B çoğunlukla hata):** 24B tutarlı biçimde `t.tur_adi` yazıyor (tur_adi'yi `tesisler` takma adı `t` üzerinden okumaya çalışıyor), doğrusu `tesis_turleri` takma adı `tt.tur_adi`. 7/10 soruda "no such column: t.tur_adi" hatasıyla çöküyor. Genuine, tekrar eden bir 24B şema-karıştırma hatası.

**Yeniden ölçüm, 9 şehir (21 Ekim 2026, geçerli):** `batch_sehir_v2.py` (DeepInfra Batch API). Önceki ölçüm (`_bench_<sehir>.py`) elle yazılmış şema kullanıyordu; şemadaki tür listeleri "sorularda kullanılanlar" diye kısaltılmıştı ve eksikti (Sakarya `tesis_turleri`nde 'Hastane' ve 'Ücretsiz WiFi Noktası' yok, 20 soruluk örneklemin 5'i bunları soruyordu; Trabzon'da 74 türün 35'i yok, örneklemin 10'u). Ayrıca yalnız şablon dosyasından örnekliyor ve gevşek puan veriyordu. Yeni ölçüm: şema DB'den (`batch_diger_v2.sema_v2`), şablon + zincir havuzundan şehir başına 50 soru (seed 31), `mistralai/Mistral-Small-3.2-24B-Instruct-2506` ve `deepseek-ai/DeepSeek-V4-Flash-0731`, 3 deneme, max_tokens 1500, sıkı puan. Gönderim öncesi: 450 gold SQL bugünkü DB'de aynı sonucu veriyor; her metin sabiti şemada ya da soruda birebir geçiyor.

| Şehir (50 soru × 3) | zincir | 24B | Flash |
|---|---|---|---|
| Konya | 43 | %40,0 | %64,0 |
| Kadıköy | 13 | %71,3 | %86,0 |
| Ankara | 13 | %71,3 | %81,3 |
| Trabzon | 0 | %76,0 | %96,7 |
| Manisa | 0 | %59,3 | %72,0 |
| İzmir | 31 | %38,0 | %46,0 |
| Sakarya | 5 | %68,7 | %81,3 |
| Kayseri | 0 | %58,0 | %94,0 |
| Tuzla | 38 | %54,7 | %81,3 |

Gevşek puan yalnız Tuzla 24B'de farklı (%55,3). Maliyet $1,4084. Ayrıntı: `sql_arastirma/uretim/bench_sehir_v2/`.

**Bu ölçümle bulunan soru hatası (düzeltilmedi):** Zincir gold SQL'i metrikleri INNER JOIN ile bağlıyor; soruda geçen metriklerden birinde o yıl verisi olmayan ilçe/mahalle sonuçtan düşüyor, soru metni bunu söylemiyor (Dünya Bankası zincirindeki "verisi olan ülkeler" notu şehir zincirlerinde yok). Gold'daki `JOIN vN` → `LEFT JOIN vN` yapılınca sonucu değişen zincir sorusu: Konya 43'te 9, İzmir 31'de 13, diğer şehirlerde 0. Flash'ın 0/3 kaldığı zincir sorularının Konya'da 10'da 8'i, İzmir'de 22'de 12'si bu belirsiz sorular (Flash LEFT JOIN yazıp eksik veriyle ilçeyi listeliyor, ör. Konya EREĞLİ). Konya ve İzmir oranları bu yüzden düşük ölçülüyor. İzmir'de ayrıca "askıda fatura kapanış sayısı" belirsiz: gold satır sayıyor (COUNT), tabloda `fatura_adet` sütunu da var.

**Maliyet:** Bu oturumdaki tüm benchmark çağrıları (önceki 24B+Flash turları + sürmekte olan 24B+8B turu) toplamda **$1'in altında** (her tur ~$0,005–$0,015 arası, DeepInfra üzerinden).

**Bilinen sınırlar:**
- Manisa'nın lisansı doğrulanamadı (kaynak sayfası 404); her satırda `orijinal.lisans` bunu açıkça taşıyor.
- "Kosullu" (ikili tür karşılaştırması) şablonu Trabzon'da setin %88'ini, Kayseri'de %71'ini oluşturuyor — yapısal olarak çeşitlilik düşük (hep aynı SQL kalıbı, farklı tür adlarıyla), hacmi yüksek ama soru-tipi çeşitliliği hacimle orantılı değil.
- Kayseri ve Trabzon'da zincir (çok-tablolu) yöntemi uygulanamadı: ikisinde de `ilçe/mahalle + yıl` anahtarını paylaşan 2. bir tablo yok (veriler tek-anlık/yıl etiketsiz).
- `birlesik_acik_veri.sqlite` (birden fazla ilçeyi birleştiren ayrı bir veritabanı) için hiç soru üretici yazılmadı.
- İller arası (örn. "9 ilin tamamında en yüksek nüfuslu ilçe") karşılaştırma tablosu önerildi ama henüz kurulmadı; nüfus referans yılları iller arasında 5 yıla kadar farklı (Ankara 2020, Trabzon 2025) — kurulursa her satırda yıl açıkça etiketlenmeli.
- İstanbul'un orijinal üretici scripti (`uretim_pilotu.py`) dedup'ı SQL metnine göre yapıyor; bu, zincir yöntemiyle SONUCA göre dedup yapan yeni şehirlerle doğrudan karşılaştırılabilir değil (İstanbul'un 97 feasible (kombinasyon,yıl) çifti Konya'nın 151'inden daha az olduğu halde İstanbul daha fazla soru üretti — muhtemelen bu dedup farkından).

**Son dosyalar:** `sql_arastirma/uretim/pilot_sorular_buyuk.jsonl` (İstanbul), `sql_arastirma/uretim/<sehir>_sorular.jsonl` + `<sehir>_zincir_sorular.jsonl` (diğer 9 veritabanı).

**Kodlar:** `kodlar/sql_sehir_acik_veri/` (`soru_ortak.py`, `zincir_ortak.py`, her şehrin `*_sorular.py`/`*_skeleton.py` üreticisi, `benchmark_coz.py` ve `bench_tum_iller.py` ölçüm betikleri, `skeleton_builder.py`/`uretim_pilotu.py` İstanbul'un orijinal üreticisi).

---

## 7. SQL: belediye dışı açık veri — deprem, Eurostat, Dünya Bankası, Wikidata (9.234)

**Amaç:** §6 ile aynı yöntem (LLM yok; soru + gold SQL aynı parametrelerden Python şablonuyla kurulur, SQL gerçek SQLite'a karşı çalıştırılır, dönen sonuç `orijinal.gercek_sonuc`), bu kez belediye portalları dışındaki dört açık kaynaktan kurulan veritabanlarında. DB'lerin içeriği, temizliği ve tuzakları: `sql_arastirma/uretim/BELEDIYE_DISI_DB_RAPORU.md`.

**Kaynak:**

| Veritabanı | Kaynak | Lisans | Kapsam |
|---|---|---|---|
| `deprem_acik_veri.sqlite` | USGS ComCat | Kamu malı | 1973+ M≥4 (4.012) + 1900–1972 tarihsel (450); 81 il / 973 ilçe |
| `eurostat_acik_veri.sqlite` | Eurostat bölgesel istatistikleri (Türkiye verisinin kaynağı TÜİK) | CC BY 4.0 | 81 il (NUTS3), 26 bölge (NUTS2); 1990–2025 |
| `dunyabankasi_acik_veri.sqlite` | World Bank WDI | CC BY 4.0 | 217 ülke × 82 gösterge; 1990–2024 |
| `wikidata_acik_veri.sqlite` | Wikidata (köy/mahalle nüfusunun kaynağı TÜİK ADNKS) | CC0 | köy nüfusu 2012–2024, mahalle 2021, ~20 bin yer |

İl/ilçe sınırları (deprem ve köy ataması için): OCHA/HGK, CC BY-IGO.

**Üretim:** §6'daki iki desen, ortak `soru_ortak.uret()` ve `zincir_ortak.uret_zincir()` ile:

1. **Şablonlar** (`deprem_sorular.py` 17, `eurostat_sorular.py` 27, `dunyabankasi_sorular.py` 12, `wikidata_sorular.py` 16, `capraz_sorular.py` 7 şablon). Pencere fonksiyonu (ROW_NUMBER/RANK/LAG), iki yıllık self-join, NOT EXISTS / EXISTS bileşimleri, il→bölge toplama CTE'leri, Türkiye'nin grup içi sırası, eşik ilk geçiş yılı, SUM CASE ikili karşılaştırmaları (`itertools.permutations`).
2. **Zincir:** Eurostat il+yıl (8 metrik, 2–4'lü, 5 yıl), Eurostat bölge+yıl (7 metrik, 2–4'lü, 5 yıl), Dünya Bankası ülke+yıl (82 göstergeden seçilmiş 12, 2–3'lü, 4 yıl). Dünya Bankası'nda 82 göstergenin hepsiyle 2–5'li kombinasyon milyonlarca aday verdiği için gösterge, kombinasyon boyu ve yıl seyreltildi.
3. **DB'ler arası** (`capraz_sorular.py`): ana DB Eurostat; deprem, Wikidata ve Dünya Bankası DB'leri `ATTACH ... AS deprem / wikidata / dunyabankasi` ile bağlanır (ilk denemedeki tek harfli `d/w/b` adları modellerin tek harfli takma adlarıyla çakıştı; Flash `d.depremler.deprem_id` yazıyordu). Gold SQL bu şema adlarını kullanır, soru metni bağlantıyı söyler, `orijinal.ekler` hangi dosyanın hangi adla bağlanacağını tutar. `soru_ortak.uret()`'e bunun için geriye uyumlu `ekler` / `db_adi` parametreleri eklendi (Sakarya çıktıları yeniden üretilip MD5 ile birebir aynı olduğu doğrulandı).

**Rapordan şablonlara aktarılan veri kuralları:**
- Deprem: denizdeki depremlerin ili yok → "dış merkezi karada olan"; büyüklük türleri karışık → "USGS'e göre büyüklük"; ilçe adı Türkiye genelinde tekil değil → ilçe döndüren her soruda il adı da istenir; tarihsel katalog modernle karıştırılmaz.
- Eurostat: oranlar yalnız iki tabloda da bulunan yıllarla; bölge göstergeleri il nüfusuyla ancak bölge toplamına çevrilerek birleşir; bölgeler İBBS-2 koduyla sorulur.
- Dünya Bankası: yıl her soruda açık; ortalamalar "ağırlıksız"; gelir grubu "bugünkü sınıflandırma"; çıplak "%" birimli göstergeler (faiz, büyüme, kadın vekil oranı…) ikili karşılaştırmaya sokulmadı. Zincir sorularına "yalnız soruda geçen göstergelerin hepsinin o yıl verisi olan ülkeler" notu eklendi (zincir SQL'i INNER JOIN; WDI'de eksik veri yaygın).
- Wikidata: köy nüfusunda 2013/2018/2023 (seçim öncesi geçici adres kaydı) ve 2016–2017 (Gümüşhane toplu kayıt sıçraması) yılları kullanılmadı; "Wikidata'da kayıtlı" ifadesi; nehirler il sorularına alınmadı; seyrek sütunlarda "kayıtlı olanlar arasında".

**Bu turda düşürülen şablonlar (veri sorunu):** ilçe köy/mahalle nüfus payı (Wikidata mahalle kapsamı ilçeden ilçeye çok eksik; Adıyaman merkezde kayıtlı mahalle nüfusu toplamı 3.101); 2023 depremli illerin köy nüfusu değişimi (bu illerin çoğu büyükşehir, köy yok; cevap tek ile iniyordu); "köy payı en düşük iller" (büyükşehirlerde Wikidata'da kalıntı köy kayıtları var, ör. Ankara 2021'de 1.119; liste %0,0 eşitlikleriyle doluydu — benchmark incelemesinde bulundu).

**Bu turda düzeltilen metin hataları:** sayı ekleri ("2014'den 2025'ye" → "2014'ten 2025'e"; `tr_ek.py`, okunuştaki son kelimeye göre ek seçer, 25 test durumu); zincirde "il" için "ilyi" → "ili", "İBBS-2 bölgeler" → "İBBS-2 bölgeleri" (`zincir_ortak.py`'ye geriye uyumlu `varlik_belirtme`, `varlik_cogul`, `yillar`, `id_onek`, `soru_eki` parametreleri).

**Süzgeç hunisi:**

| Üretici | Aday | Boş | Aynı cevap | LIMIT eşitliği | Üretilen |
|---|---|---|---|---|---|
| Eurostat il zinciri | 48.272 | 72 | 31.083 | 286 | 16.831 |
| Eurostat bölge zinciri | 23.184 | 1.936 | 10.139 | 277 | 10.832 |
| Dünya Bankası zinciri | 44.352 | 200 | 6.474 | 1.013 | 36.665 |
| Şablon dosyaları (5 dosya) | — | — | — | — | 6.661 |

**Sayılar:**

| Dosya | Toplam | orta | zor |
|---|---|---|---|
| `deprem_sorular.jsonl` | 406 | 290 | 116 |
| `eurostat_sorular.jsonl` | 995 | 125 | 870 |
| `eurostat_zincir_sorular.jsonl` | 16.831 | 504 | 16.327 |
| `eurostat_bolge_zincir_sorular.jsonl` | 10.832 | 346 | 10.486 |
| `dunyabankasi_sorular.jsonl` | 4.038 | 0 | 4.038 |
| `dunyabankasi_zincir_sorular.jsonl` | 36.665 | 980 | 35.685 |
| `wikidata_sorular.jsonl` | 1.102 | 864 | 238 |
| `capraz_sorular.jsonl` | 120 | 0 | 120 |
| **Toplam** | **70.989** | **3.109** | **67.880** |

**Doğrulama:** Program. `dogrula_sorular.py` her satırın gold SQL'ini salt okunur bağlantıyla (gerekirse `ATTACH`) yeniden çalıştırıp `gercek_sonuc` ile birebir karşılaştırır; zarf alanlarını ve kimlik tekilliğini de denetler. 8 dosyanın 70.989 satırının hepsi geçti (0 hata). Rapordaki elle denenmiş örnekler üretilen cevaplarla tutuyor (ör. Tuşba 95,4 deprem/1000 km²; 2000 sonrası en büyük depremi olan 41 il; Yalova–Ardahan 51,0 puan; Türkiye SGP kişi başı GSYH'de gelir grubunda 58 ülke arasında 1.; 2023 enflasyonda bölge birincileri Lübnan %221,3, Türkiye %53,9).

**Tekrar ayıklama (son set, 9.234):** `birlestir_belediye_disi.py`, kullanıcı kararıyla ("az ve kaliteli"). Üretim dosyaları yerinde kalır; son set `<dosya>_son.jsonl`.
1. Şablon dosyaları: SQL'den `LIMIT` ve RANK sütunu çıkarılınca aynı olan sorular tek soru (ör. "Konya'da en çok deprem görülen 3 ilçe" ⊂ "… 5 ilçe"). Temsilci en büyük n.
2. Zincir: (a) etkisiz filtreli sorular atıldı (`analiz/etkisiz_filtre.py`: filtrelerin hepsi ya da herhangi biri kaldırılınca sonuç aynı; 2.851 soru). (b) Aynı odak metriği + yıl + filtre kümesi + cevabın ilk 3 varlığı → tek soru; kalan farklar kozmetikti (n, sıra numarası, yanında gösterilen ek sütun; ör. 2023 enflasyon sıralamasının 286 kopyası). Temsilci: sıra numaralı > en büyük n > en çok sütun.
Temsilcinin `orijinal.birlesen` alanı birleştirdiği soruların kimliklerini tutar.

| Dosya | Önce | Etkisiz filtre | Son | orta | zor |
|---|---|---|---|---|---|
| deprem | 406 | — | 250 | 166 | 84 |
| eurostat | 995 | — | 887 | 113 | 774 |
| dunyabankasi | 4.038 | — | 3.398 | 0 | 3.398 |
| wikidata | 1.102 | — | 931 | 695 | 236 |
| capraz | 120 | — | 109 | 0 | 109 |
| eurostat il zinciri | 16.831 | 749 | 535 | 0 | 535 |
| eurostat bölge zinciri | 10.832 | 409 | 413 | 0 | 413 |
| dunyabankasi zinciri | 36.665 | 1.693 | 2.711 | 0 | 2.711 |
| **Toplam** | **70.989** | **2.851** | **9.234** | **974** | **8.260** |

Son dosyaların 9.234 satırı `dogrula_sorular.py` ile yeniden doğrulandı (0 hata). Zincir payı %91'den %40'a indi. Yukarıdaki üretim tablosu ve zorluk ölçümü ayıklama öncesi havuza aittir; ölçülen alt küme ayıklamada kullanılan kümelerin temsilcilerinden seçildiği için son seti temsil eder.

**Benzerlik / tekrar analizi** (`sql_arastirma/uretim/analiz/benzerlik.py`, `kumele.py`):

| Dosya | Soru | Seviye 1 | Seviye 2 | Çekirdek |
|---|---|---|---|---|
| deprem | 406 | 250 | 234 | 250 |
| eurostat | 995 | 887 | 742 | 887 |
| eurostat il zinciri | 16.831 | 5.187 | 367 | 367 |
| eurostat bölge zinciri | 10.832 | 3.726 | 314 | 314 |
| dunyabankasi | 4.038 | 3.398 | 1.796 | 3.398 |
| dunyabankasi zinciri | 36.665 | 10.452 | 2.260 | 2.260 |
| wikidata | 1.102 | 931 | 727 | 931 |
| capraz | 120 | 109 | 73 | 109 |
| **Toplam** | **70.989** | **24.940** | **6.513** | **8.516** |

- Seviye 1: SQL'den `LIMIT n` ve RANK sütunu çıkarılınca aynı olan sorular (n=3/5/10 ve pencere varyantları) tek küme.
- Seviye 2: aynı şablon (zincirde aynı odak metriği), aynı yıl, cevabın ilk sütununun ilk 3 değeri aynı.
- Çekirdek: zincirde seviye 2, şablonda seviye 1 (bazı şablonlarda ilk sütun sabit etiket, ör. 'ortalamanın üstü'; seviye 2 farklı soruları birleştirirdi). Temsilciler `analiz/temsilci_<dosya>.json`.
- **Zincir şişkin:** 64.328 zincir sorusu 2.941 cevap listesine iniyor. En büyük küme 248 soru, hepsinin cevabı "Konya, İzmir, Antalya" (2018 tarım katma değeri); "nüfusu ortalamanın üzerinde olan iller arasından" gibi filtreler çoğunlukla cevabı değiştirmiyor (etkisiz kısıt).
- Aynı şablondan iki şablon sorusunun kelime Jaccard ortalaması 0,69–0,93 (yalnız sayı/ad değişiyor). Eurostat il zincirinde ilk cevabın %19,9'u İstanbul, bölge zincirinde %31,9'u İstanbul.

**Zorluk ölçümü (katmanlı alt küme, geçerli ölçüm):** `analiz/bench_altkume.py`. Çekirdekten her şablondan 2, her zincir yapısından (metrik sayısı × kısıt sayısı × pencere) 3 soru: **200 soru, 95 katman**. `mistralai/Mistral-Small-3.2-24B-Instruct-2506` (24B) ve `deepseek-ai/DeepSeek-V4-Flash-0731` (Flash), yalnız şema + soru, 3 deneme; sayısal tolerans göreli 1e-3 / mutlak 0,011; `sira_onemli` ise sıra da aranır.

| | n | 24B | Flash |
|---|---|---|---|
| Deprem | 34 | %74,5 | %96,1 |
| Eurostat (şablon + iki zincir) | 83 | %50,6 | %75,1 |
| Dünya Bankası (şablon + zincir) | 39 | %77,8 | %91,5 |
| Wikidata | 30 | %81,1 | %94,4 |
| DB'ler arası | 14 | %45,2 | %59,5 |
| etiket "orta" | 49 | %94,6 | %94,6 |
| etiket "zor" | 151 | %54,3 | %80,1 |
| şablon | 156 | %64,1 | %84,4 |
| zincir | 44 | %64,4 | %81,1 |

Empirik merdiven (24B ≥2/3 → kolay; değilse Flash ≥2/3 → orta; ikisi de <2/3 → zor): **128 kolay, 47 orta, 25 zor**. 95 katmanın 37'sinde 24B örneklemdeki her soruyu 3/3 çözdü (deprem şablonlarının çoğu, Wikidata şablonlarının çoğu, Dünya Bankası "top/degisim/oran", Dünya Bankası zincirinin 2–3 metrikli kısıtsız/tek kısıtlı yapıları). "orta" etiketi pratikte kolay; yapısal etiket empirik zorluğu ayırmıyor.

İki modelin de başaramadığı 25 sorunun hepsi elle incelendi; kalanlar gerçek model hatası: JOIN çoklaması (bölge değeri il sayısı kadar toplanıyor: otomobil, trafik, müze soruları), "bin baş" birim çevirmesini unutma, yaş grubu tablosunu toplamadan kullanma, Flash'ın 6 soruda ısrarla `toplam_` yerine `toplum_dogurganlik_hizi` yazması.

**Bu ölçümle bulunup düzeltilen 3 bizden kaynaklı hata:**
1. **Şema envanteri kod↔ad eşleşmesini bozuyordu:** küçük sözlük tablolarında (sektör, suç türü, gösterge, araç…) kodlar ve adlar ayrı ayrı alfabetik listeleniyordu; model sıra ile eşleştirip yanlış kod seçiyordu (Flash 'Saldırı' için Yağma'nın kodu ICCS0401'i, 'Yağma' için ICCS0501'i; 24B "Sanayi" için F). ≤120 satırlı tablolar artık satır satır veriliyor. Düzeltme sonrası 24B Dünya Bankası %59,0→%77,8, Eurostat %44,6→%50,6.
2. **Karşılaştırıcıda NULL hatası:** `satir_esit` eşleşen değeri `next(..., None)` ile arıyordu; eşleşen değer NULL ise "bulunamadı" sayılıyor, gold'unda NULL olan soru her zaman başarısız oluyordu. `bench_belediye_disi.py` ve `benchmark_coz.py`'de indeksle arama ile düzeltildi (§6'nın eski ölçümleri bundan etkilenmiş olabilir).
3. **Boş sütun isteyen soru:** 2024 `dogurganlik_top` "annenin ortalama yaşı"nı istiyordu ama bu değer 2024'te kaynak hatası nedeniyle boş; 2024 şablondan çıkarıldı (eurostat 997→995).

**Büyük örneklem ölçümü (21 Ekim 2026, geçerli):** `batch_diger_v2.py` (DeepInfra Batch API). Eurostat, Dünya Bankası ve DB'ler arası setlerin `_son` havuzlarından kaynak başına 100 rastgele soru (seed 31; DB'ler arası havuzu 109). Aynı iki model, yalnız şema + soru, 3 deneme, temperature 0,3, max_tokens 1500. Şema metni DB'den üretilir (`sema_v2`): `yil` sütunu olmayan ≤300 satırlı tablolar satır satır (Dünya Bankası `ulkeler` dahil), diğer tablolarda ≤120 değerli TEXT sütun envanteri; DDL yorumları (birimler: "bin baş", "milyon euro"…) olduğu gibi gider. Gönderim öncesi kontrol: 300 sorunun gold SQL'i bugünkü DB'de aynı sonucu veriyor; gold SQL'deki her metin sabiti şemada ya da soruda birebir geçiyor.

| Set (100 soru × 3) | 24B sıkı | 24B gevşek | Flash sıkı | Flash gevşek |
|---|---|---|---|---|
| Eurostat (şablon + iki zincir) | %42,7 | %49,0 | %73,7 | %73,7 |
| Dünya Bankası (şablon + zincir) | %65,0 | %65,0 | %92,7 | %92,7 |
| DB'ler arası | %67,3 | %68,7 | %73,7 | %73,7 |

"Sıkı": göreli 1e-3 / mutlak 0,011 tolerans + `sira_onemli`; "gevşek": `benchmark_coz.sonuc_eslesiyor` (mutlak 0,5, sıra yok). Kesilen cevap 0. Kalan SQL hataları model kaynaklı: Flash'ın `toplum_dogurganlik_hizi` uydurması (Eurostat'ta 17 deneme), yanlış tabloda sütun arama (`i.nufus`, `i.bolge_kodu`), 24B'nin `in`/`is`/`to` ayrılmış kelimelerini takma ad yapması. Maliyet $0,9032. Ayrıntı: `sql_arastirma/uretim/bench_diger_v2/` (`ozet.json`, `ayrinti.jsonl`, ham `batch_cikti.jsonl`, gönderilen şemalar `sema_*.txt`).

**Geçersiz ölçüm (20 Ekim 2026, kayıt için):** `batch_diger_kaynaklar.py`, kaynak başına 20 soru. Elle yazılmış `_bench_<kaynak>.py` şemalarını kullanıyordu; bu şemalarda virgüllü adlar virgülsüz yazılmıştı (Dünya Bankası'nda 6 gösterge, ör. 'Tarım, ormancılık ve balıkçılık katma değeri'; Eurostat'ta sektör adları, ör. 'Sanayi (inşaat hariç)' yerine 'Sanayi-inşaat hariç'), suç kodları kaymıştı (ICCS0401 = Yağma, şemada 'Zorla girerek hırsızlık'), hayvan birimi yazmıyordu, max_tokens 700 bazı cevapları kesiyordu. Sonuçlar (gevşek puan): Dünya Bankası 24B %30,0 / Flash %73,3, Eurostat %43,3 / %60,0, DB'ler arası %48,3 / %68,3. Yalnız virgül düzeltmesi bile Dünya Bankası Flash'ı 44/60'tan 49/60'a çıkarıyordu.

**İlk ölçüm (geçersiz, kayıt için):** `bench_belediye_disi.py`. Her setin (şablon + zincir) havuzundan 15 rastgele soru (seed 31); `mistralai/Mistral-Small-3.2-24B-Instruct-2506` (24B) ve `deepseek-ai/DeepSeek-V4-Flash-0731` (Flash) yalnız şema + soruyu görür; şema metni `sqlite_master`'dan okunur ve ≤120 farklı değerli TEXT sütunların bütün değerleri yorum olarak eklenir. Her model 3 deneme, sonuç gerçek DB'de çalıştırılıp gold'la karşılaştırılır. Karşılaştırma `benchmark_coz.py`'dekinden sıkı: sayısal tolerans göreli 1e-3 ya da mutlak 0,011 (eski mutlak 0,5 taban, doğurganlık hızı gibi küçük değerlerde yanlışı doğru sayardı); `sira_onemli` olan sorularda satır sırası da aranır.

| Set (15 soru) | 24B | Flash | Not |
|---|---|---|---|
| Deprem | %93,3 | %100 | |
| Eurostat (şablon + iki zincir) | %35,6 | %84,4 | örneklemdeki 6 "sanayi (inşaat hariç)" zincir sorusunun 6'sında 24B 0/3; incelenen örnekte, şemada birebir değer listelendiği hâlde İnşaat (F) sektörünü seçti |
| Dünya Bankası (şablon + zincir) | %51,1 | %97,8 | |
| Wikidata | %82,2 | %100 | örneklemin çoğu "orta" il içi sıralamalar |
| DB'ler arası | %66,7 | %57,8 | şema adı düzeltmesinden önce Flash %35,6–46,7; kalan hatalar JOIN çoklaması (depremli il başına deprem sayısı kadar yer sayıldı) ve takma ad hataları |

0/3 sonuçların hepsi elle incelendi. Bizden kaynaklanan iki sorun bulunup düzeltildi: tek harfli ATTACH adları ve "köy payı en düşük" şablonu. Kalanlar gerçek model hatası (yanlış sektör kodu, JOIN çoklaması, takma ad gölgelemesi). 15 soruluk örneklem küçük; oranlar ±%15 civarında oynayabilir. Ayrıntı: `sql_arastirma/uretim/bench_belediye_disi_tur1.txt`, `bench_belediye_disi_capraz_son.json`.

Bu ilk ölçüm yukarıdaki şema envanteri ve NULL hatalarından etkilendi; geçerli sayılar katmanlı ölçümdekilerdir.

**Maliyet:** Üretim ve doğrulama $0 (LLM yok). Benchmark: ilk ölçüm $0,1207 + çapraz tekrarları $0,0527 + $0,0540 + elle inceleme (~$0,01) + katmanlı ölçüm iki tur $0,3006 + $0,5096 ≈ $1,05; 21 Ekim büyük örneklem ölçümü $0,9032 (20 Ekim geçersiz batch ölçümünün maliyeti kayıtlı değil) → toplam ≈ **$1,95** (DeepInfra).

**Bilinen sınırlar:**
- **Ayıklama öncesi hacmin %91'i (64.328) tek kalıptandı ve büyük ölçüde tekrardı;** son sette zincir 3.659 soru (%40). Zincir soruları hâlâ tek SQL iskeletinin çeşitlemeleri. zincir soruları aynı SQL iskeletinin (metrik CTE'leri + JOIN + "ortalamanın üzerinde" filtresi + isteğe bağlı RANK) farklı metrik/yıl/n birleşimleri. Yapısal çeşitlilik şablon dosyalarında (6.661 soru, 79 şablon). Dünya Bankası zinciri tek başına 36.665; birleştirmede örneklenmesi düşünülebilir.
- Zorluk etiketi yapısal (JOIN sayısı / alt sorgu / pencere); 4 tablo JOIN'li ama mantıkça basit sorular (Dünya Bankası "en yüksek n ülke") "zor" etiketli. Empirik zorluk için yukarıdaki ölçüme bakılmalı.
- Wikidata sayıları gerçek sayılar değil "kayıtlı" sayılar (ör. İstanbul'da 856 cami); mahalle nüfusu kapsamı eksik.
- Dünya Bankası işgücü göstergeleri ILO modellenmiş tahmini; Eurostat ve Dünya Bankası nüfusları farklı tanım (1 Ocak / yıl ortası), aynı soruda karıştırılmadı.
- DB'ler arası sorular üç ek dosyanın aynı klasörde bulunmasını gerektirir (`orijinal.ekler`).
- `benchmark_coz.deger_esit`'in mutlak 0,5 toleransı §6'daki eski ölçümlerde küçük değerli cevapları fazla kabul etmiş olabilir; o ölçümler yeni karşılaştırmayla tekrarlanmadı.

**Son dosyalar:** `sql_arastirma/uretim/{deprem,eurostat,dunyabankasi,wikidata,capraz}_sorular_son.jsonl`, `eurostat_zincir_sorular_son.jsonl`, `eurostat_bolge_zincir_sorular_son.jsonl`, `dunyabankasi_zincir_sorular_son.jsonl` (9.234). Ayıklama öncesi üretim dosyaları (`_son` eki olmadan, 70.989) yerinde duruyor.

**Kodlar:** `kodlar/sql_belediye_disi/`.

---

## 8. Pilot: SQL çıktı-tahmini (soru üretilmedi, yöntem denemesi)

**Amaç:** Farklı bir beceriyi ölçmek — model SQL YAZMIYOR, hazır bir SQL sorgusunu ham veriye (tabloların tam
içeriği, düz metin) karşı kafadan "çalıştırıp" çıktıyı tahmin ediyor (kod çalıştırma yok). Kullanıcı fikri
(2026-10-20): modelin ne kadar veriyi (satır/tablo sayısı) gerçekten anlayıp doğru işleyebildiğini ölçmek.

**Yöntem:** Hiç yeni soru/SQL üretilmedi — §6/§7'nin mevcut (soru, gold SQL, gerçek sonuç) üçlüleri yeniden
kullanıldı (`exec_tahmin.py`). Her kaydın gold SQL'i regex ile FROM/JOIN tablo adlarına ayrıştırılıp o
tabloların SQLite'tan okunan TAM içeriği (satır satır, markdown tablo) + SQL sorgusunun kendisi modele
verildi; model "bu SQL'i bu veriye uygularsan çıktı ne olur" diye JSON dizisi olarak cevap üretti, cevap
gerçek gold sonuçla (§6'nın sıra/sütun-sırası bağımsız, sayısal toleranslı karşılaştırıcısı,
`sonuc_eslesiyor`) karşılaştırıldı.

**Not — ilk hedef kademeler (10-20 / 50-150 / 500+ satır) tutmadı:** Bu projenin en küçük gerçek varlık
tabloları bile (il/ilçe) 16-973 satır; "kısa" asla 10-20 satıra inmiyor çünkü bir soru tek bir küçük
lookup tablosuna (ör. 8 satırlık tesis_turleri) yalnız başına referans vermiyor, hep daha büyük bir ana
tabloyla birlikte geliyor. Kademeler havuzun gerçek dağılımına göre yeniden kalibre edildi (3000 satırın
üstü — esas olarak Dünya Bankası'nın 486.623 satırlık `degerler` tablosu — pratik dışı sayılıp hiç
örneklenmedi):

| Kademe | Referans tablo(ların) toplam satırı | Havuzda kayıt | Örneklem |
|---|---|---|---|
| kısa | 64-128 | 35 | 25 |
| orta | 182-810 | 36 | 25 |
| uzun | 1.560-2.106 | 195 | 25 |

**Harness hatası (bulunup düzeltildi):** Flash sık sık dizge değerleri tırnaksız yazıyordu (ör.
`[[SERDIVAN, 164222], ...]`) — içerik çoğu zaman doğruydu ama JSON geçersizdi. Çıplak tokenları (sayı/
true/false/null olmayanları) otomatik tırnaklayan bir onarıcı eklendi (`_ciplak_degerleri_tirnakla`).

**İlk sonuçlar** (24B + Flash, thinking KAPALI/varsayılan, 3 deneme, DeepInfra):

| Kademe | 24B | Flash (thinking kapalı) |
|---|---|---|
| Kısa | %4,0 | %10,7 |
| Orta | %0,0 | %16,0 |
| Uzun | %0,0 | %2,7 |

**Doğrulama 1 — token limiti mi, yetenek mi?** Kullanıcı bu kadar düşük skordan şüphelendi ("emin misin");
48 çağrı API'nin kendi `finish_reason` ve token sayımı okunarak yeniden kontrol edildi — **0/48 token
limitinden kesildi** (`finish_reason="length"` hiç görülmedi). "Uzun" kademede (2000+ satır, 38-56K giriş
tokeni) bile modeller 55-80 tamamlama tokeniyle bitiriyor, 2000 limitinin çok altında. `max_tokens`'ı
8.000'e, sonra 14.000'e çıkarıp aynı 75 soruyu (1 deneme) tekrar ölçmek de sonucu değiştirmedi (kısa/orta/
uzun hepsi ±%4 içinde kaldı) — düşük skorlar token bütçesinden değil, gerçek bir yetenek sınırından.

**Doğrulama 2 — gerçekten daha büyük bir model bu işi yapabiliyor mu?** Kısa kademede (20 soru, 3 deneme)
iki büyük model denendi: `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B` (projenin hesaplama setinde zaten
%97,3 ile "güçlü model" referansı) ve `deepseek-ai/DeepSeek-V3.2`. Nemotron ilk denemede (`max_tokens=2000`)
**boş cevap verdi** — akıl yürütmesi (`reasoning_content` alanı) tüm bütçeyi tüketiyordu; `max_tokens=14000`
ile **%100,0 (75/75)** çözdü. DeepSeek-V3.2 (büyük ama Nemotron kadar derin akıl yürütmeyen bir model)
%18,7'de kaldı — yani mesele salt model büyüklüğü değil, derin akıl yürütme (reasoning).

**Doğrulama 3 — Flash'ın kendi thinking modu (asıl bulgu, 2026-10-21):** `deepseek-ai/DeepSeek-V4-Flash-0731`
ayrı bir model değil, aynı model `reasoning_effort` parametresiyle thinking moduna geçiyor (solver pilotunun
"Düşünen V4-Flash"ı tam olarak bu). Bu pilotta Flash'a hiç `reasoning_effort` verilmemişti (varsayılan =
kapalı, `reasoning_tokens: 0`). Aynı 75 soru (3 kademe, 1 deneme) `reasoning_effort="high"` ile tekrar
ölçüldü:

| Kademe | Flash, thinking kapalı | Flash, thinking açık (1 deneme, LIMIT'li+LIMIT'siz karışık) |
|---|---|---|
| Kısa | %10,7-12,0 | %84,0 |
| Orta | %12,0-16,0 | %52,0 |
| Uzun | %2,7-4,0 | %76,0 |

Maliyet $0,0969 (75 çağrı, 1 deneme) — thinking kapalı haliyle aynı ölçekte, hatta daha ucuz.

**Doğrulama 4 — tek-deneme gürültüsü ve LIMIT'siz sorular (2026-10-21):** Yukarıdaki tablo iki karışık
etken taşıyordu: (a) LIMIT'siz ("eşleşen TÜM satırları listele") sorular — tek bir satırı atlamak/fazladan
eklemek yeterli yanlış saymaya, LIMIT'li top-N sorularla adil karşılaştırılamaz; (b) 1 deneme — aynı soru
ikinci kez sorulduğunda (aynı prompt, aynı model) sonuç değişebiliyordu (elle doğrulandı). LIMIT'siz sorular
tamamen çıkarılıp (kısa 24, orta 20, uzun 22 LIMIT'li soru kaldı), orta ve uzun 3 deneme ile yeniden ölçüldü:

| Kademe | Flash, thinking açık (LIMIT'li, 3 deneme) |
|---|---|
| Kısa | **%91,7** |
| Orta | **%86,7** |
| Uzun | **%71,2** |

Maliyet $0,39 (66 soru × 3 deneme). Artık satır sayısıyla düzgün, küçük bir düşüş var — ama "orta < uzun"
tersliği kayboldu, o tamamen 1-deneme gürültüsüymüş.

**Tablo sayısına göre kontrollü kırılım — asıl zorluk kaynağı bulundu:**

| Tablo sayısı | Orta | Uzun |
|---|---|---|
| 1 tablo | %94,4 | %100,0 |
| 2 tablo | %75,0 | %74,4 |
| 3 tablo | — | **%0,0 (0/9)** |

2 tabloda orta ve uzun **pratik olarak aynı** (%75,0 / %74,4) — satır sayısı 182-810'dan 1.560-2.106'ya
çıkıyor ama fark yok. Uzun'un genel ortalamasını (%71,2) asıl düşüren, 3 tablolu TEK bir grup (Manisa, gölet
sayımı: `hayvan_icme_suyu_goletleri`+`mahalleler`+`ilceler`, `COUNT(*)`/`COUNT(DISTINCT)` ile agregasyon) —
bu grubun 3 sorusu da 3 denemede de hiç çözülemedi (0/9). Satır/tablo sayısından değil, bu spesifik
**agregasyon/sayma** sorgu türünden — basit "filtrele + sırala + ilk N'i al" kalıbından çok daha zor.

**Doğrulama 5 — tablo-sayısı oranı sabitlenip ölçek büyütülünce (son, kesin bulgu, 2026-10-22):**
Önceki kademelerde tablo-sayısı dağılımı tiere göre farklıydı (orta'da hiç 3-tablolu yoktu). Kullanıcı talebiyle
üç kademe de **aynı orana** (18 iki-tablo + 7 üç-tablo = %72/%28) sabitlendi — orta'nın 151-900 satır aralığında
3-tablolu kombinasyon mevcut veride hiç yoktu, bu yüzden gerçek şemaya uygun 9 yeni soru üretildi
(`ust_bolgeler`+`bolgeler`+bölge-metrik tablosu zinciri — ör. turizm/elektrikli otomobil/hayvan sayıları —,
gerçek eurostat DB'sine karşı çalıştırılıp doğrulandı, `eurostat_orta3t_takviye.jsonl`). Bu dengeli örneklemle
3 deneme, thinking açık, LIMIT'li tekrarlandı:

| Kademe | Sonuç |
|---|---|
| Kısa | %83,3 |
| Orta | %95,0 |
| **Uzun** | **%34,9** |

Uzun'un çöküşü araştırıldı: örneklemindeki **9 Manisa sorusunun hepsi** (tesis tablolarını `mahalleler`+
`ilceler` ile birleştirip `COUNT(*)`/`SUM`/`GROUP BY` ile ilçe başına sayan sorular — eczane, toplanma alanı,
hayvan içme suyu göleti sayımı gibi) **3 denemede de hiç çözülemedi**. Sorgu şekline göre ayırınca:

| Sorgu türü | Kısa | Orta | Uzun |
|---|---|---|---|
| Basit (filtrele+sırala+LIMIT) | %83,3 | %95,0 | %61,1 |
| **Agregasyon (`COUNT`/`SUM`/`GROUP BY`)** | — (örnek yok) | — (örnek yok) | **%0,0 (0/27)** |

Bu, bu pilotun en net bulgusu: **satır/tablo sayısı neredeyse önemsiz** (basit sorgular her ölçekte %61-95);
asıl ayırıcı sorgunun agregasyon içerip içermediği. Agregasyon sorgularında (yüzlerce satırı tek tek sayıp
gruplama) thinking açık Flash bile tutarlı şekilde başarısız — bu örneklemde 27/27 deneme, istisnasız.

**Doğrulama 6 — "basit" kategorisi karışıktı; agregasyon için kademeli ölçek eğrisi (son, tam bulgu,
2026-10-22):** Doğrulama 5'teki "basit" sonuçları (kısa %83,3, orta %95,0, uzun %61,1) incelenince, orta'nın
yüksek çıkmasının satır sayısından değil, **farklı bir alt türden** kaynaklandığı görüldü: kısa ve uzun'un
basit örneklerinin HEPSİ `ROUND` (hesaplanan oran/yüzde) içeriyordu, orta'nınkilerin HİÇBİRİ içermiyordu (düz
sütun okuma). Ayrıca kullanıcı önerisiyle agregasyonun büyük tablolarda mı yoksa her ölçekte mi başarısız
olduğu test edildi: Manisa'nın agregasyon sorgusu gerçek bir alt kümeye (3 ilçe, 94 satır) kesilip aynı soru
tekrar soruldu — **3/3 doğru**. Bu, agregasyonun yetenek değil ölçek sorunu olduğunu gösterdi; bunu doğrulamak
için eksik 4 hücre (gerçek DB'ye karşı doğrulanmış 15 yeni soru, `grid_takviye.jsonl`) dolduruldu — kısa/orta
ölçekte agregasyon (ilçe dilimleri), kısa/uzun ölçekte hesapsız basit sorgu (düz nüfus sütunu, LLM yok):

| Kademe (satır) | Basit, hesapsız | Basit, `ROUND`'lu | Agregasyon |
|---|---|---|---|
| Kısa (~80-105) | %93,3 (n=15) | %83,3 (n=24) | %77,8 (n=9) |
| Orta (~350-650) | %95,0 (n=20) | %86,7 (n=5) | **%16,7 (n=6)** |
| Uzun (~1757-2106) | %93,3 (n=15) | %61,1 (n=12) | **%0,0 (n=27)** |

(Tablo başlangıçta boş bir hücre bırakmıştı — orta'nın 151-900 satır aralığında 2-3 tablolu VE `ROUND`'lu
hiç soru yoktu, ROUND'lu adaylar hep tek tablolu çıkıyordu (ör. `bolge_turizm`'in turist yüzdesi) ve tablo-
sayısı kısıtına (§Doğrulama 5) uymadıkları için örneklem dışında kalmışlardı. `ust_bolgeler`+`bolgeler`+
`bolge_turizm` zincirine yüzde hesabı eklenerek 5 yeni soru üretilip dolduruldu, `grid_orta_roundlu.jsonl`.)

Artık tam bir örüntü var: **basit okuma** satır sayısından pratik olarak bağımsız (%93-95, 80'den 2.106'ya
fark yok); **`ROUND`'lu hesap** kısa ve orta'da birbirine yakın (%83 / %87, küçük örneklemde ayırt edilemez
fark) ve ancak uzun'da (%61) düşüyor — düzenli bir eğim değil, geç başlayan bir düşüş; **agregasyon** satır
sayısıyla birlikte dramatik şekilde çöküyor (%78 → %17 → %0) — yetenek sorunu değil, net bir ölçek eşiği var,
~100 satırda hâlâ büyük ölçüde çalışıyor, ~650 satırda zaten ciddi bozuluyor, ~1.750+ satırda tamamen ölüyor.
Orta'nın ROUND'lu hücresi küçük (n=5) — daha büyük örneklemle doğrulanmadan kesin sayılmamalı.

**Ne gördük (son, tam sonuç):**
- Asıl bulgu: görev modeller için "neredeyse imkansız" değil — Flash'ın thinking'i **kapalıyken** test
  edilmişti. Thinking açılınca basit sorgularda her ölçekte %61-95.
  24B'nin thinking seçeneği yok (dense model); thinking'siz sonucu geçerli kalıyor (%0-4).
- **Zorluk ekseni üç katmanlı**: (1) satır/tablo sayısı — basit-hesapsız sorguda önemsiz, `ROUND`'lu hesapta
  hafif etkili, agregasyonda belirleyici; (2) sorgunun aritmetik gerektirip gerektirmediği (`ROUND` var/yok);
  (3) agregasyon (`COUNT`/`SUM`/`GROUP BY`) içerip içermediği — bu üçü birbirinden ayrı eksenler, tek bir
  "satır sayısı arttıkça zorlaşır" kuralına indirgenemez.
- Agregasyon yetenek sorunu değil ölçek sorunu: aynı sorgu küçük bir dilimde (94 satır) 3/3 çözülüyor, aynı
  sorgu tam veride (1.757 satır) 0/9 — model COUNT/GROUP BY mantığını biliyor, sadece yüzlerce satırı elle
  sayamıyor.
- Token limiti ve model büyüklüğü (Doğrulama 1-2) yanlış izlerdi; gerçek değişken önce thinking'in açık olup
  olmamasıydı (Doğrulama 3), sonra ölçüm gürültüsü/soru karışımıydı (Doğrulama 4-5), son olarak agregasyonun
  ölçekle ilişkisiydi (Doğrulama 6).
- Az sayıda ayrıştırma hatası kaldı (ör. `Expecting ',' delimiter`) — nadir, çıplak tırnak onarıcısının
  yakalamadığı ek bir biçim varyasyonu.

**Maliyet (bu pilotun tüm turları):** İlk ölçüm $0,5651 (450 çağrı) + token-limiti doğrulaması $0,0681 (48
çağrı) + büyük model testi $0,6800 (Nemotron+V3.2, kısa kademe) + 8K-token tekrarı $0,2005 + 14K-token
tekrarı $0,1954 + Flash-thinking ölçümü (1 deneme) $0,0969 + LIMIT'li 3-deneme tekrarı $0,3915 + tablo-oranı
sabit 3-deneme tekrarı $0,3605 + 3x3 kafes takviyesi (15 soru, 3 deneme) $0,0290 + orta-ROUND'lu son hücre
(5 soru, 3 deneme) $0,0138 = **$2,602** (DeepInfra, tüm turlar toplamı). Üretim: 29 yeni soru (9 + 15 + 5)
$0 (LLM yok, Python + gerçek DB).

**Sonuç (kesinleşti):** Flash, **thinking açıkken**, basit okuma ve `ROUND`'lu hesap sorgularında (%61-95)
üretime aday, satır sayısı 2.000'e kadar ciddi bir sorun değil. `COUNT`/`SUM`/`GROUP BY` agregasyon sorguları
**küçük veri dilimlerinde (≤~100 satır) kullanılabilir** (%78) ama orta/büyük ölçekte (≥~350 satır) **üretime
uygun değil** (%0-17) — ya veri hiç büyümeyecek şekilde (küçük alt küme) sınırlanmalı, ya da dataset'e hiç
eklenmemeli. 24B (thinking'i olmayan model) bu görev tipi için hiçbir sorgu türünde uygun değil.

**Kodlar:** `kodlar/sql_exec_tahmin/exec_tahmin.py`, `flash_thinking_test.py`, `flash_thinking_limitli.py`,
`flash_thinking_v2_devam.py`, `uret_orta_3tablo.py` (`eurostat_orta3t_takviye.jsonl`, 9 soru),
`uret_grid_takviye.py` + `olc_grid_takviye.py` (`grid_takviye.jsonl`, 15 soru), `uret_orta_roundlu.py` +
`olc_orta_roundlu.py` (`grid_orta_roundlu.jsonl`, 5 soru — kafes tamamlama, 3 bölüm).

---

## 9. Excel formülü: veritabanından (zor-3 son set 1.000; pilotlar 30 + 40 + 30 + 100 toplama girmez)

**Amaç:** Gerçek açık veri tablolarından, satır/sütun sorusuna Excel formülü istemek. Excel JOIN yapamadığı için aynı veri iki düzende sunulur: **birleşik** (JOIN'lenmiş tek sayfa düz tablo) ve **ayrık** (ham ilişkisel, çok sayfa: kod sütunları + arama tabloları; soru sayfa-arası INDEX/MATCH, VLOOKUP/XLOOKUP ya da SUMIFS zinciri gerektirir). Her mantıksal soru aynı örneklemle iki düzende de üretilir (`cift_id`); iki düzenin zorluğu doğrudan karşılaştırılabilir. LLM üretimde ve doğrulamada kullanılmadı.

**Kaynak:** `sql_arastirma/uretim/` altındaki üç veritabanı (lisanslar kayıtta `lisans` alanında):

| DB | Fakt | Arama tabloları (ayrık düzen) | Ölçüler | Lisans |
|---|---|---|---|---|
| `deprem_acik_veri.sqlite` | depremler | İller (il kodu → ad), Türler (büyüklük türü kodu → ad) | büyüklük, derinlik (km) | USGS ComCat (kamu malı), OCHA HDX il sınırları (CC BY-IGO) |
| `kayseri_acik_veri.sqlite` | mahalleler | İlçeler | nüfus, alan (km²) | CC BY 4.0 (Kayseri BB) |
| `konya_acik_veri.sqlite` | mahalleler + mahalle_yapilari | İlçeler; ayrıca Yapılar sayfası (mahalle kodu → konut sayısı, ilçe kodu yok, satır sırası farklı) | nüfus, konut sayısı | CC BY 4.0 (Konya BB) |

**Üretim (`hesaplama/gen_excel_db.py`, tohum 7):** Soru başına DB'den 4 grup (il/ilçe) × 3–4 kayıt = 12–16 satırlık örneklem çekilir; ayrık düzende arama tablosuna kullanılmayan 2–3 kod da eklenir (Kayseri'de 16 ilçenin tamamı). 7 şablon: `iki_adim_arama` (kaydın bağlı olduğu grup adı), `grup_toplam`, `grup_ortalama_yuvarlama` (ROUND 1–2 basamak), `coklu_kosul_sayma` (grup + eşik), `grupta_en_buyuk_kayit` (grup içinde en büyük ölçünün kaydı), `grup_pay_yuzde`, `iki_boyut_sayma` (yalnız deprem: il + büyüklük türü, ayrıkta iki ayrı arama tablosu). Konya ayrık düzeninde konut sayısı ayrı sayfada olduğu için ilgili sorular `SUMPRODUCT(SUMIFS(Yapılar!…, Yapılar!A…, Mahalleler!A…) * (…))` zinciri ister. Soru metni tabloları "Satır | A: … | B: …" biçiminde verir ve formülün satır sırası/değer değişikliğine dayanıklı tek bir formül olmasını şart koşar.

**Cevabın doğrulanması (kesin):** Gold değer dört bağımsız yoldan hesaplanır, hepsi eşit değilse soru atılır: (1) mantıksal satırlar üzerinde formülsüz doğrudan Python hesabı, (2) birleşik gold formülü, (3) ayrık gold formülü — ikisi de `hesaplama/excel_motor.py` ile (Decimal + Excel ROUND kuralı, §2'deki düzeltmeyle aynı motor), (4) iki formül de gerçek LibreOffice 7.3.7.2 headless'ta, dizi (CSE) kipinde = Excel 365 dinamik dizi semantiği. Her soru için ayrıca 2 **pertürbe çalışma kitabı** üretilir: fakt satırlarının sırası karıştırılır, ölçü değerleri satırlar arasında yer değiştirir, arama tablosunun satır sırası karıştırılır ve ayrıkta anahtar kodları (il/ilçe kodu, tür kodu, mahalle kodu) iki sayfada birden tutarlı bir eşlemeyle yeniden etiketlenir. Pertürbe kitapların gold değeri de aynı dört yolla hesaplanır. Üç kitap da kayıtta `calisma_kitaplari` alanında saklanır.

Geliştirme sırasında LibreOffice çapraz kontrolü iki gerçek sorun yakaladı: (a) openpyxl, Excel 2010 sonrası fonksiyonları (`MAXIFS`, `XLOOKUP`, `FILTER`…) `.xlsx`'e `_xlfn.` öneki olmadan yazıyor, LibreOffice bunları tanımıyor (önek eklendi); (b) dizi kipi olmadan LibreOffice `MAX((koşul)*dizi)` gibi formüllerde örtük kesişim yapıp farklı sonuç veriyor (CSE kipine geçildi). LibreOffice 7.3'te `XLOOKUP` ve `FILTER` yok; gold formüller bunları kullanmaz, model cevaplarında bunlar yalnız motorla değerlendirilir.

**Puanlama (`grade.py` → `grade_excel_db`, kategori `excel_veritabani`):** Ayrık sorularda doğru formül tek değil; metin karşılaştırması yerine modelin son formülü (`CEVAP: =…` satırı) kayıttaki üç çalışma kitabında **çalıştırılır** ve her birinde kayıtlı sonuca eşit olmalı (sayılarda göreli 1e-9, metinde Türkçe harf katlamalı eşitlik). Türkçe fonksiyon adları `_EXCEL_TR_EN` sözlüğüyle çevrilir (sözlüğe DÜŞEYARA, İNDİS, KAÇINCI, ÇAPRAZARA, ÇOKETOPLA, ÇOKEĞERSAY, EĞERHATA, ARA vb. eklendi; eski `excel_formulu` puanlamasına etkisi: kayıtlı 280 model cevabında 0 değişiklik). `;` ayracı ve ondalık virgül, `DOĞRU/YANLIŞ`, tam sütun başvurusu (`A:A`), harf duyarsız/noktasız sayfa adı (`Iller!`) desteklenir. Motorun desteklemediği fonksiyonlarda LibreOffice'e düşülür. En az bir aralık başvurusu şarttır. Pertürbe kitaplar sabit sayı, sabit hücre adresi ve aramak yerine sabit yazılmış kod (`=COUNTIFS(Depremler!C2:C16,46,…)`) içeren cevapları eler. Elle hazırlanmış 22 aday cevaplık sınama (eşdeğer doğru formüller + bilinen yanlış kalıplar) beklendiği gibi sonuçlandı.

**Süzgeç hunisi:** 15 çift denendi → 15 çift (0 belirsiz örneklem — grup içi/tablo geneli eşitlik, pertürbasyon bulunamaması —, 0 LibreOffice uyuşmazlığı; 30 kayıt × 3 kitap = 90 formül değerlendirmesi). Şablon dağılımı (çift): `iki_adim_arama` 4, diğer 5 şablon 2'şer, `iki_boyut_sayma` 1. Kaynak başına 5 çift.

**Zorluk ölçümü (30 soru, kapalı kitap, temperature 0, `hesaplama/score_excel_db.py`):**

| Model | Birleşik | Ayrık | Toplam |
|---|---|---|---|
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 12/15 | 2/15 | 14/30 |
| deepseek-ai/DeepSeek-V4-Flash-0731 | 13/15 | 13/15 | 26/30 |

*Güncel değerler (22 Ekim 2026, aynı kayıtlı cevaplar, düzeltilmiş puanlayıcıyla yeniden puanlandı; `excel_veritabani_pilot_skor.jsonl`):* 24B birleşik 12/15, ayrık 5/15; Flash birleşik 15/15, ayrık 11/15. Fark, aşağıdaki zor pilotlar sırasında düzeltilen puanlayıcı yanlış-negatiflerinden (eksik Türkçe adlar, CHOOSE/SORT/LET vb.) ve ayrık soru metnine eklenen açık kod kuralından önceki/sonraki ölçüm farkından gelir; yukarıdaki tablo ilk ölçümün kaydıdır.

20 yanlışın hepsi elle incelendi; hepsi gerçek model hatası (puanlayıcı hatası bulunmadı). Flash: kapsam dışı kalan aralık (`B2:B14`, 14 veri satırında; orijinalde tesadüfen doğru, pertürbe kitapta yanlış), adı kod sütununda arayan DÜŞEYARA, var olmayan `ORTALAMAIF` adı, sayfalar arası satır sırası eşitliği varsayımı. 24B: 4'ü arama tablosundaki kodu hücre adresiyle/sabit sayıyla yazma (pertürbe kitaplarda düşüyor), kalanı orijinal kitapta da yanlış (kod yerine ad ile koşul, FILTER sonrası yanlış MATCH konumu, var olmayan fonksiyon adları `FİLTER`/`İNDİRGE`, boyutları uyuşmayan SUMIFS aralıkları). Ayrık düzen 24B için belirgin biçimde zor; Flash için iki düzen eşit. Örneklem küçük; oranlar kaba.

**Maliyet:** Üretim yerel, ücretsiz. Ölçüm $0,0171 (60 çağrı, DeepInfra).

**Bilinen sınırlar:** Excel 365 dinamik dizi semantiği esas alındı (Excel 2016'da bazı cevaplar CSE gerektirir). Kriterlerde joker (`*`, `?`) desteklenmez (gold kullanmaz; model kullanırsa motor LibreOffice'e düşer). LibreOffice Türkçe olmayan yerelde çalışıyor; `"Kocasinan"` ile `"KOCASİNAN"` eşleşmesini motor Türkçe kuralla yapar, LibreOffice yedeğinde bu eşleşme farklı olabilir. Gold değerler 10 basamağa kadar tam yazılır (gösterim yuvarlaması yok).

**Soruda istenen yazım (22 Ekim 2026):** Üç pilot dosyasındaki 100 kaydın (30 + 40 + 30) soru metnine, kural cümlesinden sonra §2'deki İngilizce yazım cümlesi eklendi (`gen_excel_db.soru_metni`). Dosyalar yeniden üretilmeden yalnız metin güncellendi (örneklem ve gold aynı kalsın diye); zor-2 için aynı tohumla yeniden üretim yamalı dosyayla bayt bayt aynı çıktı. Yukarıdaki ölçümler cümle eklenmeden önceki metinle yapıldı.

**Cevap alanları (21 Ekim 2026):** `cevap` İngilizce Excel formülü, `cevap_tr` aynı formülün Türkçe Excel yazımı (`grade.en_to_tr_formul`: İNDİS, KAÇINCI, ETOPLA, ÇOKEĞERSAY, TOPLA.ÇARPIM…, `;` ayracı, sayılarda ve `">1,89"` gibi ölçüt metinlerinde ondalık virgül). Denetim: 30/30 `cevap_tr` puanlayıcıda doğru, Türkçeden geri çeviri 30/30 `cevap` ile aynı token dizisi. Bu sırada bulunan puanlayıcı hatası düzeltildi: `;` ayraçlı formülde ölçüt metni içindeki ondalık virgül (`">1,892668"`) çevrilmiyordu.

**Türkçe formül istemi (22 Ekim 2026, `hesaplama/score_excel_tr.py`, `hesaplama/pilot/excel_tr/`):** Aynı sorularda formül Türkçe Excel yazımıyla istendi ("fonksiyonların Türkçe Excel'deki adlarını kullan, `;` ayracı, ondalık virgül"; istemde fonksiyon adı örneği verilmedi). Sorular: `excel_formulu`'dan alt tip başına 10 (tohum 3; 70) + üç Excel veritabanı pilotunun birleşik kayıtları (15 + 20 + 30 = 65). Serbest istem karşılaştırma için aynı ayarlarla (temperature 0); veritabanı pilotlarının serbest cevapları mevcut skor dosyalarından. İki ölçü: doğru (formül çalıştırılarak, `grade.grade`) ve Türkçe yazım uyumu (tüm fonksiyon adları gerçek Türkçe Excel adı, `;` ayracı, ondalık virgül). Maliyet $0,078.

| Model | İstem | Doğru | TR yazım uyumlu | İkisi birden |
|---|---|---|---|---|
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | serbest | 113/135 | 0/135 | 0/135 |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | Türkçe | 30/135 | 31/135 | 28/135 |
| deepseek-ai/DeepSeek-V4-Flash-0731 | serbest | 131/135 | 25/135 | 25/135 |
| deepseek-ai/DeepSeek-V4-Flash-0731 | Türkçe | 105/135 | 110/135 | 103/135 |

Set kırılımı (Türkçe istem, doğru): 24B `excel_formulu` 29/70, veritabanı 1/65; Flash 59/70 ve 46/65. Serbestte doğru olup Türkçede yanlış olanlar: 24B 83 (80'i uydurma ya da İngilizce fonksiyon adı: TOPLAM, TOPLAM.İF, İNDEKS, EŞİT, ÖZET…), Flash 28 (22'si ad hatası: ORTALAMAIF ×9 (doğrusu EĞERORTALAMA), EĞERTOPLA, TOPLA.ÇOK, MEDYAN (doğrusu ORTANCA), ÇOKEĞERTOPLA; 6'sı yazımı doğru ama mantık hatası). Yazımı uyumlu olup yanlış sayılan 12 cevabın hepsi elle incelendi, hepsi gerçek hata (puanlayıcı Türkçe formülleri doğru çalıştırıyor). Not: puanlayıcı fonksiyon adında harf işaretlerini görmezden geldiği için (ÖRTALAMA → ORTALAMA, MIN → MİN) bu tür cevaplar "doğru" sayılır ama yazım uyumu ölçüsünde düşer; gerçek Türkçe Excel'de `#AD?` verir. Sonuç: Türkçe fonksiyon adlarını bilmek iki model için de ayrı bir zorluk; 24B Türkçe Excel adlarını büyük ölçüde bilmiyor, Flash çoğunu biliyor ama EĞERORTALAMA/ORTANCA gibi adlarda uyduruyor.

**İngilizce yazım cümlesiyle yeniden ölçüm (26 Ekim 2026, `score_excel_tr.py calistir ing`, $0,056):** Aynı 135 soru, soru metni cümle eklenmiş haliyle, serbest istem. 24B: doğru 113/135 (`excel_formulu` 64/70, veritabanı 49/65), İngilizce yazıma uygun 130/135; Flash: doğru 133/135 (70/70, 63/65), İngilizce yazıma uygun 135/135. Cümleden önce (serbest) 24B 113, Flash 131 doğruydu; Flash'ın İngilizce yazım oranı 104/135'ten 135/135'e çıktı. 24B'nin `excel_formulu`'daki 5 kaybının 3'ü tekrar döngüsü (4.000 token sınırına kadar cevapsız), 2'si argüman sırası/FILTER hatası; hepsi elle incelendi. Bu sırada bulunan kalite sorunu: `kosullu_sayma_toplam` sorularının 33/300'ünde sorulan bölge tabloda yoktu, gold 0'dı (26 Ekim 2026'da düzeltildi, §2).

**Dosyalar:** `hesaplama/pilot/excel_veritabani_pilot.jsonl` (30), skorlar `hesaplama/pilot/excel_veritabani_pilot_skor.jsonl`; zor pilot `excel_veritabani_zor_pilot.jsonl` (40); zor-2 pilot `excel_veritabani_zor2_pilot.jsonl` (30). Kodlar: `kodlar/excel_veritabani/` (22 Ekim 2026 hâli).

---

**Karar (21 Ekim 2026): veri setine yalnız birleşik düzen girer.** Ayrık düzen üretimde hesaplanmaya devam eder (gold değer ikinci, bağımsız bir formülle doğrulansın diye), ama kayıt olarak yazılmaz (`gen_excel_db.py`, varsayılan; `--ayrik-da` ile ikisi birden).

**Zor şablon pilotu (21 Ekim 2026, `--takim zor`, 20 çift, `hesaplama/pilot/excel_veritabani_zor_pilot.jsonl`):** 5 yeni şablon: `uc_adim_zincir` (deprem → ilçe → il; yeni kaynak `DepremIlce`), `aralik_kosul_sayma` (il + yıl aralığı + büyüklük eşiği), `grup_oran` (nüfus yoğunluğu / konut başına nüfus), `iki_grup_esik_sayma`, `grupta_k_buyuk_kayit` (BÜYÜK(EĞER()) + arama). 25 denemeden 5'i belirsiz örneklem (eşitlik) diye atıldı, 20 çift; LibreOffice uyuşmazlığı 0. Ayrık soru metnine "kodu formüle sabit sayı olarak yazmayın" cümlesi eklendi (önce örtük kuraldı; Flash'ın ayrık hatalarının 11'de 6'sı buydu). Ölçüm (temperature 0, $0,026):

| Model | Birleşik | Ayrık |
|---|---|---|
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 13/20 | 0/20 |
| deepseek-ai/DeepSeek-V4-Flash-0731 | 20/20 | 16/20 |

Flash'ın 4 ayrık hatası elle incelendi, hepsi gerçek (bir satır eksik aralık; başlık satırını da içeren tam sütun `D:D` ile aritmetik → `#VALUE!`; sayfalar arası satır sırası eşitliği varsayımı). Puanlayıcıya bu sırada eklenenler: dizi sabiti `{1,2}`, ELEMAN (CHOOSE), SIRALA/SIRALAÖLÇÜT (SORT/SORTBY), LET, BÜYÜK/KÜÇÜK, `İNDİS(dizi;0;sütun)`, eleman bazlı `&`, ESAYIYSA/EHATALIYSA hata yaymadan; bunlarla 1 yanlış-negatif (Flash'ın doğru SORT/FILTER/CHOOSE cevabı) düzeldi. Not: birleşik düzende Flash 20/20, yani zor şablonlar birleşikte güçlü model için kolay.

**Zor-2 pilotu (22 Ekim 2026, `--takim zor2`, tohum 41, yalnız birleşik, `hesaplama/pilot/excel_veritabani_zor2_pilot.jsonl`, 30 soru):** Amaç birleşik düzeni Flash için zorlaştırmak; tek bir *IF fonksiyonuyla çözülemeyen üç yapı ve büyük tablo (6 grup × 3–6 satır; soru başına 25–34 satır, önceki pilotlarda 12–16). Kaynaklar: Kayseri 12, Konya 11, deprem 7 soru. Şablonlar (10'ar soru):
- `ayni_ad_iki_anahtar`: aynı mahalle adı birden çok ilçede (gerçek veri: Kayseri'de 46, Konya'da 84 ad birden çok ilçede geçiyor; örneğin CUMHURİYET); "X ilçesindeki Y mahallesinin nüfusu / konut sayısı / alanı / yoğunluğu". Tek anahtarlı arama (DÜŞEYARA, KAÇINCI) ilk eşleşmeyi bulur, yanlıştır. Pertürbe kitaplardan birinde yanlış ilçedeki aynı adlı satır doğrusundan önce, birinde sonra gelir ve değerleri her kitapta farklıdır.
- `grup_sec`: gruplayıp seçme; grupların toplam / ortalama / satır sayısı / oran (yoğunluk, konut başına kişi) değerine göre en yüksek ya da en düşük 1. veya 2. grubun adı (deprem için yalnız ortalama ve sayı; büyüklük logaritmik, toplamı anlamsız). Gold `INDEX(SORTBY(UNIQUE(G),SUMIF(G,UNIQUE(G),M),-1),k)`. 2. sıradaki grup sorularında tekilleştirmesiz `BÜYÜK(ETOPLA(G;G;M);2)` yanlıştır (en üst grubun satırları tekrar eder). Pertürbede grup etiketleri karıştırılır ve 3 satır başka gruba taşınır (yalnız permütasyon grup boylarını korur, sayı sorusunu sınamazdı; ilk denemede böyle bir açık bulunup düzeltildi).
- `turetilmis_kosul`: koşul satırda hesaplanan değere ya da grup istatistiğine bağlı: yoğunluk / konut başına kişi eşiği (sayı ya da toplam nüfus; `TOPLA.ÇARPIM`), grubun kendi ortalamasından büyük olanlar (`">"&EĞERORTALAMA(…)`), tablonun medyanından büyük olanlar. Eşik iki komşu oran değerinin arasından yuvarlak bir sayı seçilir, eşitlikte soru atılır. Pertürbe kitaplardan birinde grup ortalaması yerine tablo ortalaması / medyan yerine ortalama kullanan formül farklı sonuç verir (ilk denemede bir soruda bu yanlış formül tesadüfen her kitapta doğruydu; koşul eklendi).

Doğrulama (kesin): formülsüz Python hesabı + iki ayrı gold formül motorda (Excel 365 yazımı `cevap` ve ikinci yazım; örneğin `INDEX/MATCH(1,(A=…)*(B=…),0)`, `SUM(IF(…))`, `MATCH(G,G,0)={1;2;…}` ile tekilleştirme) + ikinci formül LibreOffice 7.3 CSE'de (UNIQUE/SORTBY LibreOffice 7.3'te yok). 4 pertürbe kitap (toplam 5). 34 denemeden 4'ü belirsiz (eşitlik), 30 soru; LibreOffice uyuşmazlığı 0. Puanlayıcı sınaması: gold ve `cevap_tr` 30/30 kabul; tekilleştirmesiz 2. sıra (5 soru), grup ortalaması yerine tablo ortalaması, medyan yerine ortalama, tek anahtarlı arama: hiçbiri kabul edilmedi; her hücreyi sabit konumla döndüren `=INDEX(sütun;i)` 3.878 denemede 0 kabul.

Motor/puanlayıcıya eklenenler: UNIQUE (BENZERSİZ), MEDIAN (ORTANCA), SEQUENCE, AND/OR/NOT, TAKE, LAMBDA + BYROW/BYCOL/MAP; IFERROR/IFNA ve dizi koşullu IF artık eleman bazında (önce dizideki tek hata tüm sonucu hataya çeviriyordu, Excel'de `=TOPLA(EĞERHATA(A2:A4/B2:B4;0))` 3,5 verirken motor #DIV/0! veriyordu). Bu değişikliklerden sonra 2.100 soruluk `excel_formulu` sınaması ve önceki iki pilotun yeniden puanlaması değişmedi. LAMBDA desteği bir yanlış-negatifi düzeltti (Flash'ın doğru `LET(…BYROW(…LAMBDA…))` cevabı).

Ölçüm (temperature 0, aynı istem, $0,020; `excel_veritabani_zor2_pilot_skor.jsonl`):

| Şablon | mistralai/Mistral-Small-3.2-24B-Instruct-2506 | deepseek-ai/DeepSeek-V4-Flash-0731 |
|---|---|---|
| ayni_ad_iki_anahtar | 9/10 | 10/10 |
| grup_sec (1. sıra) | 2/5 | 5/5 |
| grup_sec (2. sıra) | 0/5 | 3/5 |
| turetilmis_kosul | 8/10 | 10/10 |
| Toplam | 19/30 | 28/30 |

Bütün yanlışlar elle incelendi, hepsi gerçek model hatası. Flash'ın 2 hatası: 2. sıradaki grupta tekilleştirme yok (`BÜYÜK(…;2)` / `IF(COUNTIF>0,…)` her zaman doğru koşul). 24B: INDEX(B:B) ile MATCH(B2:B…) arasında bir satır kayma (cevap bazı kitaplarda başlık "İlçe"), `COUNTIFS(C:D,">2")` ile oranı tek sütun gibi sınama, tam sütunda boş satırların 0/0 hatası, uydurma fonksiyonlar (İNDİRGE, SÜREKLİ, FREKANS kullanımı), dizi üzerinde AND, SORT/SORTBY argüman hataları, bir soruda kendini tekrarlayıp cevap yazamama. Sonuç: tek zor yapı Flash'ı belirgin biçimde düşürmüyor; 2. sıradaki grup (3/5) en ayırt edici şablon. Örneklem küçük.

---

**Zor-3 pilotu (26 Ekim 2026, `--takim zor3`, tohum 31, yalnız birleşik, `hesaplama/pilot/excel_veritabani_zor3_pilot.jsonl`, 100 soru):** Zor-2'de Flash yalnız "2. sıradaki grup" sorularında düşüyordu (3/5); zor-3 iki zorluğu üst üste koyar. Tablo 6–8 grup × 4–7 satır (soru başına 24–53 satır). Beş şablon (20'şer soru; kaynak başına Kayseri 35, Konya 35, deprem 30): `filtreli_grup_sec` (satır süzgeci ölçü > eşik, sonra grup toplamı/sayısı, en yüksek 1. ya da 2. grup: `INDEX(SORTBY(UNIQUE(G),SUMIFS(M,G,UNIQUE(G),F,">e"),-1),k)`), `iki_adim_grup` (bir istatistiğe göre en yüksek/en düşük grubu seç, o grupta başka bir istatistik: ortalama (ROUND 2), toplam, en büyük, eşik sayımı), `grup_sayma` (ortalaması tablo ortalamasından büyük / toplamı eşikten büyük / en az n kaydı olan grup sayısı), `filtreli_grupta_k` (grup + satır süzgeci içinde başka ölçüye göre 1. ya da 2. kayıt), `grup_max_birlesim` (her grubun en büyük/en küçük değeri, bunların toplamı ya da ortalaması). Doğrulama zor-2 ile aynı: formülsüz Python + iki gold formül (`cevap` Excel 365, `cevap_alt` LibreOffice'te çalışan yazım) motor + `cevap_alt` LibreOffice 7.3 CSE, 4 pertürbe kitap (grup etiketleri de karıştırılır, 3 satır başka gruba taşınır). Tuzak kitapları (`kitap_uygun`): süzgeci unutan sıralama, tüm tablo istatistiği, satır sayan grup sayımı, tablonun en büyük n değeri en az bir kitapta farklı sonuç verir. Eşikler hiçbir değere eşit olmayan yuvarlak sayılar. **Süzgeç hunisi:** 137 deneme → 100 (37 belirsiz örneklem: eşitlik, az satır, uygun pertürbe bulunamadı), 0 LibreOffice uyuşmazlığı, 100 tekil soru metni.

**Zor-3 zorluk ölçümü (`score_excel_db.py`, temperature 0, reasoning low, 4.000 token, $0,077):** İlk koşu ağ kesintisiyle 200/200 çağrı `Connection reset by peer` aldı ($0), yeniden koşuldu.

| Şablon | 24B | Flash |
|---|---|---|
| filtreli_grup_sec | 2/20 | 16/20 |
| iki_adim_grup | 6/20 | 16/20 |
| grup_sayma | 5/20 | 19/20 |
| filtreli_grupta_k | 3/20 | 20/20 |
| grup_max_birlesim | 4/20 | 13/20 |
| **Toplam** | **20/100** | **84/100** |

Flash'ın 16 yanlışı elle incelendi, hepsi gerçek model hatası: istenen ROUND'u unutma 6 (grup_max_birlesim 5, iki_adim_grup 1), 2. grubu satır bazlı LARGE ile alma (aynı grup iki kez sayılır) 3, UNIQUE dizisiyle satır dizisinin konum kayması 1, tam sütun başvurusunda INDEX'in bir satır kayması 1, aralığın son satırını atlama 1, parantez hatası (`IF` tek argüman) 1, genel minimum (grup değil) 1, tekrar döngüsü (formül yok) 2. 24B'nin orijinalde doğru, pertürbede yanlış 5 cevabı da gerçek hata (`FILTER(a, koşul1, koşul2)`: 3. argüman if_empty, ikinci süzgeç uygulanmıyor; tablo sırasında 2. satır; ROUND unutma).

**Motor eki (26 Ekim 2026, `excel_motor.py`):** İnceleme bir yanlış-negatif buldu: 24B'nin `SUMPRODUCT(--(MMULT(--(UNIQUE(C)=TRANSPOSE(C)),F)/COUNTIF(C,UNIQUE(C))>AVERAGE(F)))` cevabı Excel 365'te doğru, ama motor MMULT bilmiyordu, LibreOffice yedeği de UNIQUE bilmiyor. Eklendi: `MMULT`, `TRANSPOSE`, `ROW` (sayfa aralığının satır numaraları), Excel dizi yayınlaması (n×1 ile 1×m → n×m). Altı sınama formülünde motor = LibreOffice. Yeniden puanlama: önceki dört Excel veritabanı skor dosyasında (400 cevap) değişen tek sonuç bu cevap (24B 19 → 20/100); Türkçe istem ölçümünde (810 cevap) motor kaynaklı değişiklik 0 (değişen 9 sonucun hepsi 33 soru düzeltmesinde metni değişen 00319 ve 00596 sorularına ait eski cevaplar).

**Zor-3 son set (26–27 Ekim 2026, tohum 41 + grup_max_birlesim tohum 42, `hesaplama/cikti_veritabani/excel_veritabani_zor3.jsonl`, 1.000 soru):** 1.357 deneme → 1.000 (357 belirsiz), 0 LibreOffice uyuşmazlığı, 1.000 tekil soru metni, pilotla ortak soru 0. Şablon başına 200; Kayseri 335, Konya 335, deprem 330; tablo 24–53 satır (ortalama 38,5); 175 soru "2. sıradaki" seçim. Kimlikler `excel_veritabani_zor3-NNNN-birlesik`, zorluk `zor`. Zorluk ölçümü (1.000 × `mistralai/Mistral-Small-3.2-24B-Instruct-2506` + `deepseek-ai/DeepSeek-V4-Flash-0731`, temperature 0, reasoning low, 4.000 token) DeepInfra Batch API ile yapıldı (`hesaplama/score_excel_db_batch.py`, `hesaplama/pilot/batch_zor3/`; 2.000/2.000 istek tamamlandı, 0 başarısız). Puanlama çalıştırarak (asıl + 4 pertürbe kitap); sonuçlar `hesaplama/pilot/excel_veritabani_zor3_skor.jsonl`.

| Şablon (200'er) | 24B | Flash |
|---|---|---|
| filtreli_grup_sec | 22 | 131 |
| iki_adim_grup | 59 | 176 |
| grup_sayma | 65 | 171 |
| filtreli_grupta_k | 55 | 193 |
| grup_max_birlesim | 51 | 128 |
| **Toplam** | **252/1.000** | **799/1.000** |

Maliyet $0,7839 (24B $0,2475, Flash $0,5364). **Flash yanlış denetimi (örneklem):** şablon başına 8 (filtreli_grupta_k'da 7, tümü), 39 yanlış elle incelendi; 1 yanlış olumsuz bulundu (0611: `HSTACK` motorda yoktu, LibreOffice 7.3'te de yok → `#NAME?`; motora `HSTACK`/`VSTACK` eklendi, cevap doğruya çevrildi, Flash 798 → 799). Diğerleri gerçek: satır düzeyinde `LARGE` ile 2. grup (aynı grubun tekrarı), `UNIQUE` sırası ile satır sırasının karıştırılması, tablonun son satır(lar)ını aralık dışında bırakma, `B2:B100000` / `C:C` gibi boş satır içeren aralıkta `AVERAGEIF` → `#DIV/0!` (LibreOffice ile de doğrulandı), fazladan `)` (Excel formülü kabul etmez), sabit grup adı yazma, `SORT`/`SORTBY` karışıklığı. Taramayla: Flash'ın 201 yanlışından 55'i soru "2 ondalık basamağa yuvarlanmış" dediği hâlde `ROUND` kullanmıyor (grup_max_birlesim 49, iki_adim_grup 6) — grup_max_birlesim'in düşük puanı büyük ölçüde buradan; 4 cevapta `CEVAP:` satırı yok. Motorun tanımadığı fonksiyon içeren 46 yanlış cevap (iki model; çoğu 24B'nin `FREQUENCY` denemeleri) yeniden puanlandı: değişen yalnız 0611. **Puanlama takılması:** Flash'ın 0423 cevabı `AVERAGEIF(B2:B100000,B2:B100000,…)` ile ~10^10 karşılaştırmaya girdi, puanlama ~3 saat takıldı; motor `*IF/*IFS` dizi kriterinde aynı kriter değerini önbellekler (14 sn) ve `score_excel_db_batch.py` her cevabı ayrı süreçte 60 sn sınırla puanlar (zaman aşımı `ok: null` yazılır; bu koşuda 0 kaldı). **grup_max_birlesim yeniden üretimi (26–27 Ekim 2026):** İlk ölçümde bu şablonun "ortalamayı 2 ondalığa yuvarla" birleşimi zorluğu Excel mantığından değil ROUND unutmaktan alıyordu (Flash'ın 72 yanlışının 49'u). Ortalama birleşimi çıkarıldı; yerine karşı uç (grup en büyüklerinin en küçüğü `MIN(MAXIFS(…UNIQUE…))` / grup en küçüklerinin en büyüğü; `MAX(MAXIFS)` gibi tablonun genel değerine eşit olanlar hariç) kondu, toplam kaldı; deprem verisinde yalnız karşı uç. `gen_excel_db.py --takim zor3 --sablon grup_max_birlesim --n-cift 200 --seed 42`: 202 deneme → 200, 0 LibreOffice uyuşmazlığı; eski 200 kaydın kimlikleri ve kaynak sırası korunarak yerlerine kondu (diğer 800 soru ve ölçümleri değişmedi). Dağılım: `MIN(MAXIFS)` 102, `MAX(MINIFS)` 32, `SUM(MAXIFS)` 42, `SUM(MINIFS)` 24. 1.000 tekil metin, pilotla ortak 0. Ölçüm Batch API ile (`hesaplama/pilot/batch_zor3_gmb/`, 400/400 istek, $0,1852): 24B 71/200, Flash 171/200. 24B'nin bir cevabı (0270, tam sütun `C:C` ile `COUNTIF`) 300 sn'de puanlanamadı; elle incelendi (grup en büyüklerini hesaplamıyor, bir aralığın MIN'i) → yanlış. Flash'ın 29 yanlışından 8'i elle incelendi, hepsi gerçek: satır üzerinden toplama (`SUMPRODUCT(MINIFS(D,B,B))` grubu satır sayısı kadar sayar), `MAX(IF(B=B,…))` ile genel uca düşme, tek hücrede çalışmayan `COUNTIF($B$2:$B2,…)` kalıbı, bir satır eksik aralık, fazladan parantez.

**Son skorlar (1.000 soru, `hesaplama/pilot/excel_veritabani_zor3_skor.jsonl`, eski grup_max_birlesim satırları çıkarıldı; ham cevapları `pilot/batch_zor3/cikti.jsonl`'da):**

| Şablon (200'er) | 24B | Flash |
|---|---|---|
| filtreli_grup_sec | 22 | 131 |
| iki_adim_grup | 59 | 176 |
| grup_sayma | 65 | 171 |
| filtreli_grupta_k | 55 | 193 |
| grup_max_birlesim | 71 | 171 |
| **Toplam** | **272/1.000** | **842/1.000** |

Toplam ölçüm maliyeti $0,9691 (ilk koşu $0,7839 + yeniden üretim ölçümü $0,1852); son skor dosyasındaki cevapların maliyeti $0,8010. Durum: **son set**, toplama girer (27 Ekim 2026).

## 10. SQL çıktı-tahmini — üretim (4.990)

**Amaç:** §8'deki pilotun bulgusunu (Doğrulama 6) üretime çevirmek. Model SQL YAZMIYOR; hazır bir SQL
sorgusu + referans verdiği tabloların TAM ham içeriği veriliyor, model kod çalıştırmadan çıktıyı tahmin
ediyor. §8'de bulunan kurallara göre sadece güvenli bölge üretildi:
- **Basit** (agregasyon yok — `COUNT`/`SUM`/`GROUP BY` içermeyen): satır sayısından pratik olarak bağımsız
  (%93-95 hesapsız, %83-87 `ROUND`'lu), 2.100 satıra kadar test edildi.
- **Agregasyon** (`COUNT`/`SUM`/`GROUP BY` içeren): sadece ~150 satıra kadar güvenli (%78-97); daha büyük
  ölçekte (≥~600 satır) üretime dahil edilmedi.

**Üretim yöntemi — iki ayrı yol, LLM yok:**

1. **Basit (3.578 soru, `uret_cikti_tahmini.py`):** Yeniden üretim değil, yeniden PAKETLEME — §6 (il/ilçe,
   20.262) ve §7 (belediye dışı, 9.234) havuzundaki mevcut (soru, gold SQL, gerçek sonuç) üçlülerinden
   agregasyon içermeyenler (regex: `COUNT`/`SUM(`/`AVG(`/`GROUP BY` yok) ve referans verdiği tabloların
   toplamı ≤3.000 satır olanlar seçildi. Her kaydın SQL'i aynen korunur; NL soru metni yerine "bu SQL'i bu
   veriye uygularsan çıktı ne olur" çerçevesi kullanılır. Aynı (DB, tablo kombinasyonu) birden fazla soruda
   tekrarlandığı için tablo içerikleri **ayrı bir dosyada deduplike** saklanır (3.578 sorudan sadece 60
   benzersiz "dilim").
2. **Agregasyon, küçük dilim (917 soru, 11 kaynak):** Manisa'nın 17 ilçesinden rastgele 2-4'lü
   kombinasyonlar × 4 metrik tablo (gölet sayımı, eczane, toplanma alanı, afet wifi noktası) ile `COUNT`/
   `GROUP BY` sorguları kurulup gerçek DB'ye karşı çalıştırıldı (`uret_agregasyon_dilim.py`, 100 soru,
   1.111 kombinasyon denendi). Aynı yöntem 10 ek kaynağa genelleştirildi (`uret_agregasyon_coklu.py`):
   Sakarya/Kayseri/Trabzon (tesis_turleri — tür filtreli, 6-44 çeşit), İzmir (tesis türleri + eczane +
   askıda fatura), Ankara (`hizmet_kayitlari`, 30 hizmet türü), Konya (itfaiye noktası + ürün/hayvan/
   kooperatif türleri — mahalle-seviyeli ham tablolar, ilçe-seviyeli önceden-toplanmış tablolar hariç
   tutuldu), Deprem (büyüklük eşiğiyle çeşitlenen il-seviyeli sayım), Wikidata (`yerler`, 18 yer türü),
   Kadıköy/Tuzla (tek-şehir, mahalle-seviyeli — sağlık/kültür/yol/eczane/park/toplanma alanı). Toplam 1.067
   kombinasyon üretildi, en yüksek sayımı ≤2 olan **130 trivial soru elendi** (817 kaldı).

**Doğrulama:** Program. Üç üretimin SQL'i de kayıttan SONRA gerçek SQLite dosyasına karşı tekrar
çalıştırılıp kayıtlı sonuçla birebir karşılaştırıldı — **4.495/4.495 satırın hepsi geçti (0 uyuşmazlık)**.

**Kalite kontrolü (örneklem, Flash `reasoning_effort=high`, 3 deneme):** Önce 10-kaynak agregasyon partisi
tek başına ölçüldü: Manisa'nın 100 sorusundan 20'si (**%96,7**, 58/60) ve 10-kaynak partisinin 817
sorusundan 25'i (**%97,3**, 73/75) — ikisi de §8'in ilk tahmininden (%77,8) daha iyi; muhtemelen bu
partilerin daha sıkı sınırlandırılması (≤150 satır, trivial eleme) nedeniyle.

Sonra **üretimin %10'u üzerinden** (sabit seed, `olc_uretim_yuzde10.py`) tüm set tek seferde ölçüldü: basit
358/3.578, agg-Manisa 10/100, agg-10kaynak 82/817. İlk turda (`max_tokens=8000`) basit kategori sadece
**%72,1** (774/1.074 deneme) çıktı — §8'de ölçülen %93-95'in çok altında. Ham model çıktısı incelenince
(`ct_il_ilce_sql_ibb_10574`, 1.677 satır) `content` alanının muhakeme metninin ORTASINDA kesildiği görüldü
("...Let's also verify no district 39 has pct 1.764... Let's") — model `max_tokens` dolana kadar
"düşünüyor" ve asıl JSON çıktısını hiç yazamıyor (Nemotron'da §8'de görülen aynı "muhakeme bütçeyi yiyor"
hatası, Flash'ın kendisinde de — ama sadece basit kategorinin en karmaşık, çok-tablolu/alt-sorgulu
uçlarında). **Düzeltme:** `max_tokens` 16.000'e çıkarılıp `finish_reason` izlendi (`olc_basit_16k.py`, aynı
358 soru/seed). Sonuç **%87,7** (942/1.074) — %72,1'den büyük iyileşme, ama 16.000'de bile 11/1.074 deneme
(%1) hâlâ `finish_reason=length` ile kesiliyor; basit kategorinin kuyruğunda (çok-tablolu self-join/pencere
fonksiyonu benzeri sorgular) §8'in kontrollü 3×3 kafesinde temsil edilmeyen, gerçekten daha zor bir alt küme
var. **Düzeltilmiş %10 testi toplamı:** basit %87,7 (942/1.074) + agg-Manisa %90,0 (27/30) + agg-10kaynak
%92,7 (228/246) = **genel %88,7 (1.197/1.350)**. Toplam maliyet (tüm kalite turları): $3,66.

**Aynı örneklemde iki model (27 Ekim 2026, `olc_kucuk_buyuk_altkume.py` + `olc_roundlu_flash_tekrar.py`):** grup başına 15 soru (tohum 7), 3 deneme. 24B (`max_tokens` 2.000, düşünme yok): hesapsız 3/45, ROUND'lu 0/45, sayma/gruplama 4/90 → **7/180 (%3,9)**. Flash (`reasoning_effort=high`, 16.000 token): hesapsız 45/45, ROUND'lu 43/45, sayma/gruplama 89/90 → **177/180 (%98,3)**. Flash'ın ROUND'lu grubu ilk koşuda 45 denemenin 29'unda cevap dönmeden hata vermişti (240 sn istek zaman aşımı); 600 sn ve 8 paralel çağrıyla aynı 15 soru yeniden ölçüldü, 0 hata, $0,0976 (`cikti_tahmini/kalite_kucuk_roundlu_flash_tekrar.json`). İstem (`exec_tahmin.TAHMIN_PROMPT`) yalnız JSON istiyor, açıklamaya izin vermiyor; 24B'nin ilk skoru "ara adım yazmadan" ölçüldü. 24B'ye aynı 60 soruda adım adım istemle (`olc_24b_adim_adim.py`: önce sorguyu açıkla, satırları tek tek bul, ara sonuçları yaz, son satıra `CEVAP: [[…]]`; 8.000 token, 600 sn) yeniden soruldu: hesapsız 5/45, ROUND'lu 2/45, sayma/gruplama 25/90 → **32/180 (%17,8)**, $0,3245 (`cikti_tahmini/kalite_24b_adim_adim.json`, her deneme kayıtlı). 31 cevapta `CEVAP:` satırı yoktu; 18'inde metindeki son JSON tablosu okundu, hepsi yanlış; 13'ünde hiç tablo yok (Python kodu, yalnız açıklama ya da 8.000 token'da kesilme). Adım adım yazmak en çok küçük tablolardaki sayıma yarıyor (4/90 → 25/90).

**Hesapsız grubunun genişletilmesi (28 Ekim 2026, `uret_hesapsiz_kesik.py`):** İlk üretimde tabloların toplamı 3.000 satırı aşan 603 hesapsız (agregasyonsuz, `ROUND`'suz) sorgu atılmıştı. Bu sorguların SQL'i, büyük tabloların bir kesiğinde yeniden çalıştırıldı: 300 satırı aşan her tablodan rastgele 300 satır (sonuç boşsa 600; soru başına en fazla 10 tohum), küçük arama tabloları tam. Gold bu kesik veriden hesaplanır; modele de yalnız kesik tablolar verilir (`tablo_metni` satırın içinde). Süzgeç: 603 → boş sonuç 98, 40 satırdan uzun 10 → **495**. Tablolar 300–1.881 satır. Denetim: 495 tekil SQL, mevcut setle ortak 0; 60 rastgele soruda tablo metninden kurulan DB'de SQL yeniden çalıştırıldı, 60/60 cevap birebir. Kaynak: Wikidata 255, Trabzon 78, İzmir 71, Kayseri 63, deprem 21, Konya 7. Cevapların 238'i tek satır (birbirine bağlı tablolardan ayrı ayrı rastgele satır alındığından birleşen satır az kalıyor). Dosya: `cikti_tahmini/hesapsiz_kesik_sorular.jsonl`.

**Hesapsız %10 ölçümü (28 Ekim 2026, `olc_hesapsiz_yuzde10_batch.py`, DeepInfra Batch):** 561 hesapsızdan 56 soru (eski 66'dan 7 + yeni 495'ten 49, tohum 7), 3 deneme. Flash (`reasoning_effort=high`, 16.000 token, yalnız JSON istemi): eski 21/21, yeni 131/147, **toplam 152/168 (%90,5)**, 2 deneme 16.000 token'da kesildi. 24B (adım adım istem, 8.000 token): eski 2/21, yeni 11/147, **toplam 13/168 (%7,7)**, 22 deneme kesildi. Maliyet $0,7343. Puanlamada biçim toleransı: Flash 3 cevapta sonucu `[[[...]]]` ya da kaçışlı tırnakla (`\"`) yazmıştı, içerik doğruydu; ayrıştırıcı bunları da okuyacak şekilde genişletildi (144 → 152). Flash'ın kalan yanlışları: yanlış satır seçimi/sıralama, `NOT EXISTS` süzgecini kaçırma, 2 denemede "ORTAHİSAR" yerine "ORTAHISAR" (harf kopyalama hatası, yanlış sayıldı). Sonuçlar: `cikti_tahmini/kalite_hesapsiz_yuzde10.json`.

**Sayılar:**

| Alt küme | Soru | Kaynak | Maliyet |
|---|---|---|---|
| Basit, hesapsız | 66 | §6/§7 yeniden paketleme | $0 |
| Basit, hesapsız, kesik tablo (28 Ekim) | 495 | §6/§7'nin 3.000 satırı aşan hesapsız sorguları, tablolar rastgele 300/600 satıra kesilip yeniden çalıştırıldı | $0 (program, LLM yok) |
| Basit, `ROUND`'lu | 3.512 | §6/§7 yeniden paketleme | $0 |
| Agregasyon, Manisa | 100 | yeni üretim | $0 (program, LLM yok) |
| Agregasyon, 10 ek kaynak | 817 | yeni üretim (Sakarya/Kayseri/Trabzon/İzmir/Ankara/Konya/Deprem/Wikidata/Kadıköy/Tuzla) | $0 (program, LLM yok) |
| **Toplam** | **4.990** | | **$0 üretim + $0,0565 kalite kontrolü** |

**Bilinen sınırlar:**
- Basit kategoride "hesapsız" alt tipi ilk üretimde çok azdı (66) — mevcut havuzda `ROUND` içermeyen
  agregasyonsuz sorgu azdı; çoğu basit sorgu bile bir oran/yüzde hesaplıyor (ROUND'lu 3.512'nin 3.292'si
  İstanbul'un oran şablonlarından). 28 Ekim'de kesik tabloyla 561'e çıkarıldı (aşağıda).
- 3.000 satırın üstündeki basit sorular (tahminen ~2.400, ör. Dünya Bankası'nın 486K satırlık `degerler`
  tablosunu kullanan sorular) kapsanmadı — bu bölge hiç test edilmedi.
- Konya'nın `ilce_*` tablolarının çoğu (muhtarlık talebi, numarataj, GES, itfaiye olayı, katı atık) zaten
  önceden-toplanmış sayım sütunları taşıyor (`talep_sayisi` gibi) — ham satır değil, bu yüzden agregasyon
  üretiminde kullanılmadı (COUNT(*) gerektiren ham-kayıt tabloları: itfaiye noktası, ürün/hayvan/kooperatif
  türleri).
- İzmir'in `askida_fatura_kapanislari` tablosu dengesiz dağılmış — hedeflenen 25 sorudan sadece 7'si
  üretilebildi (3.000 deneme limiti doldu), diğer mahallelerde veri çok seyrek/trivial çıkıyordu.
- `window_rank` alanı korunuyor ama bu üretimde hiç kullanılmadı.
- Basit kategorinin %10 kalite testinde (16.000 token'la) bile 11/1.074 denemenin hâlâ
  `finish_reason=length` ile kesildiği görüldü — çok-tablolu/alt-sorgulu en zor basit sorularda model
  bazen 16.000 token'ı da aşıyor; bu alt küme ayrıca incelenmedi.

**Son dosyalar:** `sql_arastirma/uretim/cikti_tahmini/sorular.jsonl` (3.578) + `dilimler.json` (60
benzersiz tablo dökümü), `agregasyon_sorular.jsonl` (100, Manisa), `agregasyon_sorular_coklu.jsonl`
(817, 10 ek kaynak).

**Kodlar:** `kodlar/sql_exec_tahmin/uret_cikti_tahmini.py`, `uret_agregasyon_dilim.py`,
`uret_agregasyon_coklu.py`, `olc_agregasyon_spot.py`, `olc_agregasyon_coklu_spot.py`,
`olc_uretim_yuzde10.py` (%10 örneklem ölçümü, sabit seed), `olc_basit_16k.py` (basit kategori için
16.000 token'la yeniden ölçüm + `finish_reason` izleme).

---

## Birleştirme durumu

- `verifiable_data_birlesik.jsonl` (30 Ekim 2026: **137.997 satır**, ~350 MB) + eşlik dosyası `verifiable_data_birlesik_tablolar.json` (~1,7 MB); `birlestir.py`. Paylaşım paketi bundan `paket_kur.py` ile kurulur (`paket/`, §11).
- Ortak zarf: `{id, kaynak, kategori, alt_tip, koken, zorluk, zorluk_uretim, soru, cevap, orijinal}`. Kaynağa özel bütün alanlar `orijinal` altında korunur. `zorluk` son ortak benchmark'a kadar `null`; üretim etiketi `zorluk_uretim`'de (setler arası karşılaştırılamaz; solver'ın `orta`/`kod`'u zorluk değil görev türü, `orijinal.set`'te).
- Tekrar ayıklama: aynı (`kategori`, `soru`, `orijinal.db` ya da Cognipeer'de `orijinal.baglam`) ikinci kez gelirse atılır → `verifiable_data_birlesik_tekrar_atilan.jsonl` (2.322: SQL il/ilçe 2.243, TURSpider 76, birim dönüşümü 3).
- **MEB tip adı normalizasyonu:** `v6_son`'daki "karşılaştırma"/"karşilastirma" yazım farkları (19 satır) `KORPUS_TIP_NORMALIZE` ile "karsilastirma"ya indirildi.
- **Tablo verisi (çıktı-tahmini):** basit alt-grupta tablo metni `dilim_id` ile eşlik dosyasına referans verir (paylaşılan pasaj deseni); agregasyon, hesapsız kesik ve ROUND'lu kesik grupları tablo metnini satırda taşır.
- **SQL il/ilçe, belediye dışı, TURSpider:** model SQL yazar; puanlama `orijinal.db` (+ `ekler`) dosyasında salt okunur çalıştırıp `orijinal.gercek_sonuc` ile karşılaştırır. **Cognipeer:** şema ve veri `orijinal.baglam`'da gömülü.
- **Excel veritabanı zor-3:** `calisma_kitaplari` (5 tablo) kayıtta gömülü.

## 11. Paketleme turu (30 Ekim 2026): düzeltmeler, dış setler, paket

Proje kapanışı için yapılan son tur. Önce bütün klasörün yedeği alındı: `~/yedek/verifiable-data_2026-10-30.tar.zst` (28 GiB → 19,4 GiB, `zstd -t` ile sınandı; aynı diskte, dış kopya kullanıcıda).

**Altın cevap öz-sınaması** (`paket/araclar/altin_sinama.py`): her satırın altın cevabı modelin yazacağı biçime sokulup paket puanlayıcısından geçirildi → **137.997/137.997**. Ters sınama (`--ters`, bariz yanlış cevap: `CEVAP: 98765.4321`, `SELECT 1 WHERE 0`, `[[0]]`, `{"cevap": "bilmiyorum"}`, en iyi değer +1…) aşağıdaki veri ve puanlayıcı hatalarını buldu; düzeltmeden sonra 7 kabul kaldı, yedisinin de altın cevabı 98.765,4321'e gerçekten %0,5'ten yakın.

**Veri düzeltmeleri:**

| Set | Sorun | Düzeltme | Satır |
|---|---|---|---|
| birim_donusumu / `ters_problem` | Cevap gizli `v`'den yazılıyordu, sorudaki yuvarlanmış gösterimden değil ("0,004 hektar → kaç m²?" kayıtlı 44,8, doğrusu 40) | `hesaplama/duzelt_ters_problem.py` cevabı sorudaki değerden yeniden hesapladı; `gen_birim.gen_ters` düzeltildi | 34 tolerans dışı (125 metin değişti, 91'i son basamak) |
| birim_donusumu / `oran_capraz_birim` | 2 basamağa yuvarlanan oran uç birim çiftlerinde 0 (89) ya da tek anlamlı basamak / ≥1e6 (50) | `hesaplama/duzelt_oran_sifir.py`: aynı id altında düzeltilmiş `gen_oran` (aralık 0,1–1e6, tohum "oran-duzeltme-2026-10-30") ile yeni soru | 139 |
| SQL il/ilçe | Birebir tekrar (soru, DB ve sonuç aynı; 1.565 grup) | birleştirmede tekrar ayıklama | 2.243 |
| SQL çıktı-tahmini (basit, ROUND'lu) | 3.512'nin 3.292'si İstanbul (37 dilim, tek dilimde 574'e kadar) | `denge_istanbul.py`: İstanbul dilim başına ≤32 (iskelet sıralı dolaşma, tohum 30) → 990; ayrılan 2.302 `cikti_tahmini/sorular_fazla_istanbul.jsonl` | −2.302 |
| SQL çıktı-tahmini | Açığı diğer kaynaklardan kapatma | `uret_roundlu_kesik.py` (aşağıda) | +736 |

**ROUND'lu kesik üretimi** (`sql_arastirma/uretim/uret_roundlu_kesik.py`, LLM yok): `uret_hesapsiz_kesik.py`'nin yöntemi İstanbul dışı kaynakların agregasyonsuz ROUND'lu sorgularına uygulandı. 3.000 satırı aşan aday 1.633 (Dünya Bankası 1.471, Eurostat 144, İzmir 18; Kayseri/Ankara/Manisa/Wikidata/deprem'de bu tip sorgu yok). Rastgele kesik Dünya Bankası'nın 486 bin satırlık `degerler` tablosunda gösterge+yıl süzgecine neredeyse hiç denk gelmiyordu (ilk turda 1.471'den 18). Bu yüzden büyük tablodan K/2 satır sorgunun sonucuna katkı veren satırlardan (`SELECT DISTINCT alias.rowid <gövde>`, ORDER/LIMIT'siz), kalanı rastgele çeldirici alındı. Süzgeç: hata, en az 3 sonuç satırı (hesapsız kesikte 238 tek satırlık cevap çıkmıştı), en çok 40, süzgeci etkisiz LIMIT'siz sorgu. **Huni:** 1.633 → 736 (boş ya da <3 satır 897). Kaynak: Dünya Bankası 598, Eurostat 120, İzmir 18; tablolar 400–1.881 satır; sonuç satırı 10 (565), 5 (134), 3–4 (37). Denetim: 736 tekil SQL; 80 rastgele soruda tablo metninden kurulan DB'de SQL yeniden çalıştırıldı, 80/80 aynı. Sınır: Dünya Bankası'nın 598 sorusu 4 SQL iskeletinden ("gösterge/yıl için ilk N ülke"). Dosya: `cikti_tahmini/roundlu_kesik_sorular.jsonl`. Son çıktı-tahmini seti: basit 1.276 (İstanbul 990, hesapsız 66 dahil) + agregasyon 917 + hesapsız kesik 495 + ROUND'lu kesik 736 = **3.424**.

**Dış setler** (`sql_arastirma/hazir_setler.py`; kullanıcı kararı: TURSpider ve Cognipeer pakete girer, `koken` alanıyla işaretli; BIRDTurk girmez: 80 DB'nin 15'i inik, CC BY-NC-SA). Altın sonuç her satır için yeniden hesaplandı.

| Set | Girdi | Elenen | Kalan |
|---|---|---|---|
| TURSpider (`TURSpider/data/turspider_filtered_clean.csv`, önceki turda çalışmayan 93 atılmıştı) | 9.599 | boş sonuç 1.619 (1.592'si eğitim bölümünde; Spider'ın boş gelen DB'leri: coğrafya 488, akademisyen 477, restoranlar 113, akademik 97, imdb 89…) | 7.980 → birleştirmede tekrar 76 → **7.904** |
| Cognipeer (`data/cognipeer_filtered_clean.parquet`, önceki turun 85.793'ü) | 85.793 | boş istem 13, (istem, bağlam) tekrarı 31, zamana bağlı (`NOW`/`CURDATE`/`'now'`…, sonuç güne göre değişir) 3.695, hata 27, boş SELECT sonucu 10.539, veritabanını değiştirmeyen değiştirme ifadesi 2.454 | **69.034** |

TURSpider veritabanları (166 dosya, `futbol_1` 317 MB) GitHub sınırını aştığı için pakete girmez; `paket/araclar/turspider_indir.sh` sabit commit `49bb962`'den indirir (yerel kopyalar zip'lerle md5 ile birebir aynı, 166/166). Cognipeer'de gold ve model SQL'i aynı MySQL taklit işlevleriyle (`fix_cognipeer.register_shims`) çalışır; değiştirme görevlerinde tüm tablo/görünümlerin son durumu karşılaştırılır.

**Puanlayıcı düzeltmeleri** (paket `puanlama/`; eski skorlar bu yüzden biraz farklı olabilir):

- **Tarih (`grade.grade_tarih`, kaynak `hesaplama/grade.py` da güncellendi):** altın sözcükler tüm metinde ve alt dizge olarak aranıyordu; "8 yaş" altını "98765.4321" cevabında doğru sayılıyordu (ters sınamada 2.100'ün 170'i: `yas_hesabi` 92, `iso_hafta_no` 78). Artık son `CEVAP:` satırı, sözcük düzeyinde (sayı birebir, sözcükte Türkçe ek toleransı). Kayıtlı 226 model cevabında (`skor_sonuclari*.jsonl`) 5 sonuç değişti, beşi de doğru→yanlış ve gerçekten yanlış (gemma: ISO haftası 2/3 ve 42/41; "ertesi gün"ü `CEVAP:` satırına yazmayan 3 cevap).
- **MEB hızlı eşleşmesi (`meb.answers_match`; üretimdeki `korpus/generate_questions.py` değiştirilmedi):** iki yönde harf dizgesi arıyordu; altın "C" iken "c" geçen her cevap, "Apolardır" altınına "polar", "Fizikokimya"ya "kimya" doğru sayılıyordu (altın cevapların 483'ü ≤3 karakter). Yeni: parantezsiz normalize eşitlik ya da altın cevabın sözcüklerinin model cevabında ardışık geçmesi (3+ harfli sözcükte ek toleransı); Türkçe I/ı küçültme. Kayıtlı 5.863 MEB model cevabında: 302 eşleşme hızlı yoldan hakeme düştü (çoğu eksik cevap: "Mitokondrinin iç zarı" ~ "mitokondri"), 57 yeni eşleşme (Türkçe I/ı ve parantez farkı: "Isı enerjisi" ~ "ısı enerjisi").
- **Solver `orta`:** `zor.dogru_mu`'nun göreli 0,0005 toleransı optimuma yakın değerleri kabul ediyordu (27.885 için 27.886; ters sınamada 150 örneğin 38'i). Artık birebir tam sayı eşitliği (Türkçe binlik ayırıcı "27.885" okunur).
- **SQL çıktı-tahmini:** gevşek ayrıştırıcı (`olc_hesapsiz_yuzde10_batch.ayristir`) + `CEVAP:` satırı varsa yalnız o satır. Karşılaştırıcı `bench_belediye_disi` sürümü (göreli 1e-3 / mutlak 0,011); en dışta `ORDER BY` varsa sıra önemli (eski ölçümler `benchmark_coz.sonuc_eslesiyor` ile sırasız ve mutlak 0,5 toleransla alınmıştı).
- **SQL yazma:** salt okunur bağlantı + 30 sn sınır (`set_progress_handler`).
- **Excel:** `score_excel_db_batch.grade_sinirli` (süreç grubu, 60 sn) iki Excel kategorisinde varsayılan.

**Bilinen ama düzeltilmeyen:** `sayac_takip` (bulmaca) 300 sorunun 116'sının cevabı 0 (hiç anılmayan kap soruluyor; "hep 0" diyen model %39 alır; bir kısmı belirsiz: "Burak valize üç yeşil boya ekledi … kaç yeşil boya aktarılmıştır?" → 0). Kullanıcı kararına bırakıldı.

**Paket** (`paket/`, ayrı git deposu; `paket_kur.py` ile kurulur): `veri/<set>.jsonl.gz` (11 dosya, 54 MB), `veri/sql_cikti_tahmini_tablolar.json`, `veri/ozet.json`, `veritabanlari/` (14 SQLite, 110 MB; boş `kadikoy_tuzla_acik_veri.sqlite` girmez), `puanlama/` (tek giriş noktası `istem(satir)` / `puanla(satir, metin)`; hesaplama ve bulmaca modülleri `_hesaplama/`, `_bulmaca/` altında kopya), `araclar/`, `README.md`.

## Rapora eklenmesi gerekenler

- MEB kitaplarının künyeleri ve kullanım koşulları.
- Solver setinde zor iş sıralamanın ayarı (ek kural ya da daha düşük pay).
- Konu ağacı veri setinin yayın durumu (şu an gizli).
