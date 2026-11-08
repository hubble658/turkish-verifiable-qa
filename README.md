---
license: cc-by-sa-4.0
language:
- tr
pretty_name: Doğrulanabilir Türkçe Soru Veri Seti
size_categories:
- 10K<n<100K
task_categories:
- question-answering
- text-generation
- table-question-answering
tags:
- verifiable
- reasoning
- text-to-sql
- excel
- logic-puzzles
- turkish
- rlvr
configs:
- config_name: bulmaca
  data_files: veri/bulmaca.jsonl.gz
- config_name: excel_veritabani
  data_files: veri/excel_veritabani.jsonl.gz
- config_name: hesaplama
  data_files: veri/hesaplama.jsonl.gz
- config_name: meb_capraz
  data_files: veri/meb_capraz.jsonl.gz
- config_name: meb_tek_ders
  data_files: veri/meb_tek_ders.jsonl.gz
- config_name: solver
  data_files: veri/solver.jsonl.gz
- config_name: sql_istatistik
  data_files: veri/sql_istatistik.jsonl.gz
- config_name: sql_cikti_tahmini
  data_files: veri/sql_cikti_tahmini.jsonl.gz
- config_name: sql_belediye
  data_files: veri/sql_belediye.jsonl.gz
- config_name: sql_turspider
  data_files: veri/sql_turspider.jsonl.gz
- config_name: satranc
  data_files: veri/satranc.jsonl.gz
- config_name: izgara_bulmaca
  data_files: veri/izgara_bulmaca.jsonl.gz
- config_name: ajan_terminal
  data_files: veri/ajan_terminal.jsonl.gz
- config_name: regex
  data_files: veri/regex.jsonl.gz
- config_name: karakter_islemleri
  data_files: veri/karakter_islemleri.jsonl.gz
---

# Doğrulanabilir Türkçe Soru Veri Seti

Cevabı programla kontrol edilebilen **78.096** Türkçe soru ve görev, 15 set: mantık bulmacaları, hesaplama, Excel formülü, optimizasyon, SQL yazma, SQL çıktısı tahmini, MEB ders kitaplarından kısa cevaplı sorular; ayrıca satranç, ızgara bulmacaları, regex, karakter işlemleri ve çok turlu terminal (ajan) görevleri. Her sorunun yanında altın cevap ve onu puanlayan kod var: Excel ve SQL cevapları çalıştırılarak, sayılar toleransla, bulmacalar normalize eşleşmeyle puanlanır.

Sürüm: 7 Kasım 2026.

> **Yalnız veriyi kullanacaksanız:** Hugging Face sürümü düz bir tablodur. Her satırda modele verilecek hazır istem (`istem`) ve altın cevap (`cevap`) bulunur: https://huggingface.co/datasets/hubble658/turkish-verifiable-qa. HF'de `train` ve `test` ayrı bölümlerdir. Bu depo ise puanlama kodunu, SQL veritabanlarını ve ajan görevlerinin ortamlarını (`ajan_eval/`) içerir. `puanla()` HF satırını da doğrudan kabul eder.

## İçerik

| Dosya (`veri/`) | Soru | Köken | Cevabı kim belirler | Modelden istenen |
|---|---:|---|---|---|
| `bulmaca.jsonl.gz` | 3.000 | özgün | Program (çözücü + tek çözüm kontrolü) | Kısa cevap |
| `hesaplama.jsonl.gz` | 14.613 | özgün | Program (formül, sympy, datetime, şema) | Sayı+birim / tarih / matris / JSON / XML / Excel formülü |
| `excel_veritabani.jsonl.gz` | 1.000 | özgün | Program (Python + iki formül motoru + LibreOffice) | Tek Excel formülü |
| `solver.jsonl.gz` | 4.986 | özgün | Program (OR-Tools CP-SAT, kanıtlı en iyi değer) | En iyi değer (`orta`) ya da Python programı (`kod`) |
| `sql_belediye.jsonl.gz` | 17.785 | özgün | Gerçek SQLite'ta çalıştırma | SQL sorgusu (belediye açık verisi: 9 il/ilçe veritabanı) |
| `sql_istatistik.jsonl.gz` | 9.234 | özgün | Gerçek SQLite'ta çalıştırma | SQL sorgusu (ulusal/uluslararası istatistik: deprem, Eurostat, Dünya Bankası, Wikidata) |
| `sql_cikti_tahmini.jsonl.gz` | 3.321 | özgün | Gerçek SQLite'ta çalıştırma | Verilen SQL'in çıktısı (JSON tablo) |
| `meb_tek_ders.jsonl.gz` | 2.758 | özgün | LLM + kitap pasajı, LLM tutarlılık kontrolü | Kısa cevap |
| `meb_capraz.jsonl.gz` | 3.979 | özgün | LLM + iki ders pasajı, LLM hakem | Kısa cevap |
| `sql_turspider.jsonl.gz` | 7.902 | `dis_kaynak` (TURSpider, CC BY-SA 4.0) | Gerçek SQLite'ta çalıştırma | SQL sorgusu |
| `satranc.jsonl.gz` | 3.000 | `dis_kaynak` (Lichess, CC0) | Lichess çözümü + zorlayıcı-mat çözücü | İlk hamle (SAN/UCI) |
| `izgara_bulmaca.jsonl.gz` | 2.000 | özgün | Program (çözücü, BFS, Dijkstra/Kruskal) | Izgara ya da sayı |
| `ajan_terminal.jsonl.gz` | 1.590 (kabuk 884, kod 706) | özgün | Kum havuzunda çalıştırılıp `checks` kurallarıyla denetlenir; kurallar örnek çözümden türetilmiştir | Çok turlu komut çalıştırma; dosya ya da kod üretimi |
| `regex.jsonl.gz` | 1.728 (yazma 1.695, çıkarma 33) | özgün 1.483 / `dis_kaynak` 245 (StructuredRegex MIT, müşteri mesajları CC BY 4.0) | Program (DFA eşdeğerliği ya da gizli testler) | Python regex'i |
| `karakter_islemleri.jsonl.gz` | 1.200 (Sezar, işlem zinciri, ters yazma; 400'er) | özgün (cümleler GECTurk, Apache-2.0) | Program (Türkçe alfabe ve harf kuralları) | Metin |
| **Toplam** | **78.096** | | | |

**Köken:** `koken` alanı sorunun kaynağını verir: `ozgun` (bu çalışmada üretildi, 66.949 soru) ya da `dis_kaynak` (açık lisanslı dış kaynaktan alındı ya da uyarlandı, 11.147 soru: TURSpider 7.902, satranç 3.000, regex 245). 7 Kasım'a kadar dört değer vardı (`turspider_filtreli`, `hizli_uyarlama`, `hizli_uretim`); iki gruba indirildi. Altın cevabın nasıl belirlendiği tablonun "Cevabı kim belirler" sütununda; altını LLM'e dayanan tek setler MEB setleridir (Bilinen sınırlar). Ajan görevlerinde görevi ve örnek çözümü LLM yazdı, kontroller örnek çözümün çalıştırılmasından türetildi. Dış setlerde altın sonuç bu paket için yeniden çalıştırılarak hesaplandı; soru metniyle SQL'in uyumu kaynak setin kalitesine bağlı (TURSpider insan çevirisi). Cognipeer seti 3 Kasım'da çıkarıldı (aşağıda).

**Karakter işlemleri (4 Kasım):** Türkçe metin üzerinde karakter düzeyinde işlem ölçer, Türkçe dil bilgisini değil. Düşük skorda tokenizasyonun payı olabilir (`belgeler` / YONTEM §23).

## Satır şeması

**Train / test:** Her satırda `bolum` alanı vardır: train 69.925, test 8.171. Modeli `train` ile eğitin, `test` ile ölçün. SQL testi train'de olmayan veritabanlarından oluşur: `sql_belediye` Sakarya + Ankara, `sql_istatistik` Deprem + Wikidata (bunları `ATTACH` eden Eurostat soruları dahil), `sql_turspider` özgün `dev` bölümü (20 veritabanı). Bu veritabanlarından türeyen `sql_cikti_tahmini` satırları ve MEB'de ölçüm sorularıyla aynı konudan ya da pasaj çiftinden olan sorular da testtedir. Karşılaştırılabilir ve ucuz ölçüm için `benchmark/test_kumesi.jsonl` içinde `olcum: true` olan 4.199 satırı kullanın: 42 üretim başlığının her birinden 100 soru ya da görev (MEB tek derste 99; 7 Kasım'da bir şekil bağımlı soru çıkarıldı). Şablondan üretilen setlerde (ör. `hesaplama`, `bulmaca`) aynı şablon iki bölümde de bulunur; bu bilinçlidir, yani test bu setlerde yeni parametreyi ölçer, yeni soru türünü değil. 2 Kasım skorları dört SQL setine aktarılamaz, diğer 22 türde geçerlidir.

**Regex (5 Kasım):** T1'de karar çoğunlukla DFA eşdeğerliğiyle verilir; 20 öğe ve otomata çevrilemeyen cevaplar gizli testlere düşer. Yolu `puanla_ayrinti` içindeki `via` söyler, ayrı raporlayın. Açık sınırlar (T3 gevşek regex, cevap ayıklama, train/test ortak 7 altın): `belgeler` / YONTEM §19.1.

**Ajan terminal görevleri:** Bu sette soru-cevap yerine ortam ve kontrol vardır; `puanla()` çalışmaz, görevler `ajan_eval/` ile çalıştırılır (`ajan_eval/README.md`). Test bölümü `ajan_eval/data/split.json`'dadır (kabuk 100, kod 100). Test 200'de 65 görev düzeltildi (`ajan_eval/duzeltme_raporu.md`), train 1.390 görev modelle denetlenmedi; yanlış altın içerebilir.

Her dosya satır başına bir JSON nesnesi içerir:

| Alan | Anlam |
|---|---|
| `id` | Benzersiz kimlik |
| `kaynak` | `bulmaca`, `hesaplama`, `korpus` (MEB), `solver`, `sql`; ek setlerde set adı (`satranc`, `izgara_bulmaca`, `regex`, `karakter_islemleri`, `ajan_terminal`) |
| `kategori` | Alt set (ör. `birim_donusumu`, `sql_belediye`, `korpus_capraz_eslestirmeli`) |
| `alt_tip` | Şablon ya da soru tipi |
| `bolum` | `train` ya da `test` (kimlikler ve ölçüm alt kümesi `benchmark/test_kumesi.jsonl`) |
| `koken` | `ozgun` (bu çalışmada üretildi) / `dis_kaynak` (dış kaynaktan alındı ya da uyarlandı) |
| `zorluk` | **Şimdilik `null`.** Tüm setlere aynı ayarla koşulacak son benchmark'tan doldurulacak |
| `zorluk_uretim` | Üretimdeki etiket. Setler arasında karşılaştırılamaz (bulmacada kolay/zor, hesaplama ve SQL'de orta/zor, TURSpider'da easy…extra; MEB, solver ve çıktı tahmininde `null`) |
| `soru` | Soru metni (istem değil; istem `puanlama.istem` ile kurulur) |
| `cevap` | Altın cevap. SQL yazma setlerinde gold SQL; çıktı tahmininde beklenen tablo |
| `orijinal` | Kaynak kaydın tamamı, **JSON metni olarak** (`json.loads(satir["orijinal"])` ya da `puanlama.orijinal(satir)`). İç yapısı setten sete değiştiği ve tablolarda metin ile sayı karıştığı için metin olarak saklanır. Puanlayıcının ihtiyaç duyduğu ek alanlar burada: `tolerans_yuzde`, `calisma_kitaplari`, `db`, `ekler`, `gercek_sonuc`, `sira_onemli`, `baglam`, `lisans`… |

## Kullanım

Hugging Face'ten:

```python
from datasets import load_dataset
egitim = load_dataset("hubble658/turkish-verifiable-qa", "hesaplama", split="train")   # set adı = config
test = load_dataset("hubble658/turkish-verifiable-qa", "hesaplama", split="test")
```

Puanlama kodu ve veritabanları bu depoda (HF'de yalnız veri var); puanlamak için depoyu indirin:

```bash
git clone https://github.com/hubble658/turkish-verifiable-qa
cd turkish-verifiable-qa
pip install -r requirements.txt   # chess, greenery, regex, openpyxl, formulas, requests (sürümler sabit)
bash araclar/turspider_indir.sh   # sql_turspider için 166 veritabanı (~470 MB)
```

```python
import gzip, json
from puanlama import istem, puanla

for satir in map(json.loads, gzip.open("veri/hesaplama.jsonl.gz", "rt", encoding="utf-8")):
    metin = model(istem(satir))      # kendi model çağrınız
    dogru = puanla(satir, metin)     # True / False (Excel'de süre aşımında None)
```

- `istem(satir)`: Ölçümlerde kullanılan istemi kurar. SQL setlerinde şemayı veritabanından üretir; çıktı tahmininde tablo dökümünü ekler.
- `puanla(satir, metin)`: Kategoriye göre doğru puanlayıcıyı çağırır.
- **MEB setleri:** Kural eşleşmesi altınla ve `orijinal.kabul_edilen` listesiyle yapılır; tutmazsa yanlış. Puanlama tamamen kurala dayalıdır, LLM hakem kullanılmaz (aynı puanlayıcı GRPO ödülü olarak da kullanılabilsin diye). Hakem parametresi 7 Kasım'da kaldırıldı.
- **Doğrulama:** `python3 araclar/altin_sinama.py veri/*.jsonl.gz` her satırın altın cevabını kendi puanlayıcısından geçirir. `--ters` bayrağı bariz yanlış cevapların, `--yakin` bayrağı az bozulmuş cevapların (tam sayı +1, ondalık %5, birimde %15) reddedildiğini sınar. Bu sürümde (7 Kasım) altın sınama 76.506/76.506 geçiyor, ters sınama 76.499/76.506 (ajan terminal görevleri `ajan_eval/` ile sınanır, bu sayılara girmez). Ters sınamadaki 7 kabul birim dönüşümü (2) ve fizik (5) sorularında; bunların altın cevabı sınamada kullanılan yanlış değere (98.765,4321) gerçekten %0,5'ten yakın.

**Gerekenler:**
- Python ≥ 3.10.
- SQL setleri için `veritabanlari/` (13 SQLite dosyası, ~110 MB, depoda).
- `sql_turspider` için ayrıca indirme betiği.
- `requirements.txt`: `satranc` için python-chess, `regex` için `regex` ve `greenery==4.2.3` (zorunlu; yoksa regex puanlayıcısı açıkça hata verir), Excel için `openpyxl` ve `formulas`. Regex puanlaması iş parçacığında yapılmamalı (SIGALRM), süreç havuzu kullanın.
- LibreOffice isteğe bağlı. Excel motorunun tanımadığı nadir fonksiyonlarda kullanılır; yoksa bu cevaplar yanlış sayılır. Protokol ölçümlerinde kuruluydu (7.3).
- Solver `kod` seti modelin Python programını yerel olarak çalıştırır: 60 sn işlemci, 2 GB bellek, yasaklı modül listesi. Bu bir kum havuzu değildir, güvenmediğiniz ortamda konteyner içinde çalıştırın.

## Puanlama kuralları (özet)

- **Kapalı kitap.** Modele yalnız istem verilir. Kaynak pasaj, gold formül/SQL ve `orijinal` alanı gösterilmez. Tek istisna solver `kod` seti: orada model kod yazar ve kod çalıştırılır.
- **Hesaplama.** Sayı son `CEVAP:` satırından okunur (birim üsleri ve kimyasal formül rakamları sayı sayılmaz: `m/s^2`, `CO2`) ve `tolerans_yuzde` ile karşılaştırılır. Birim dönüşümünde altın, sorudan yeniden hesaplanan kesin değer ve soruda belirtilmeyen ikinci yaygın tanımla (KB = 1000, İngiliz galonu, metrik beygir) bulunan değer de kabul edilir. Matriste tam sayı ve `x=…, y=…` cevapları birebir eşit olmalı. Tarih sorularında son `CEVAP:` satırındaki sözcükler eşleşmeli; `21.03.2019` gibi sayısal yazım da kabul edilir. JSON/XML türü ve değeri korunarak birebir karşılaştırılır. Excel formülü tabloda çalıştırılır; Türkçe Excel yazımı da kabul edilir.
- **Excel veritabanı.** Formül 5 çalışma kitabının (asıl + 4 karıştırılmış) hepsinde doğru sonucu vermeli. Her cevap ayrı süreçte 60 sn sınırla puanlanır.
- **Solver.** Tam sayı en iyi değer **birebir** eşit olmalı.
- **SQL yazma.** Model SQL'i salt okunur bağlantıda çalıştırılır (30 sn sınır).
  - Satır sayısı eşit olmalı. Sütun sırası önemsiz, fazladan sütun serbest.
  - Satır sırası yalnız `sira_onemli` ise önemli.
  - İki tam sayı birebir eşit olmalı. Ondalıkta tolerans mutlak 0,011'dir; büyük değerlerde göreli 1e-3'e kadar çıkar ama altının yazıldığı basamağın yarım birimini geçmez (yuvarlamamış doğru cevap geçer, 485.418.671,76 yerine 485.418.700 geçmez).
  - Altın sorgu eşit değerler yüzünden SQLite'ın tarama sırasına bağlıysa (aynı sorgu `PRAGMA reverse_unordered_selects` ile farklı sonuç veriyorsa) iki geçerli sonuç da kabul edilir ve satır sırası aranmaz.
- **`LIMIT` eşitliği.** Altın `ORDER BY ... LIMIT` ise ve sınırda eşit değer varsa, eşit satırlardan herhangi biri ya da eşit grubun tamamı kabul edilir (`belgeler` / YONTEM §25).
- **SQL çıktı tahmini.** Model JSON tabloyu yazar, karşılaştırma SQL yazmayla aynıdır. SQL'de en dışta `ORDER BY` varsa satır sırası önemlidir; sıralama anahtarında eşitlik varsa (gösterilen tablolarda ters taramayla sınanır) sıra aranmaz. Biçim toleransı var: kaçışlı tırnak, fazladan dış liste, tırnaksız metin. `CEVAP:` satırı varsa yalnız o satır okunur.
- **Bulmaca.** Gevşek eşleşme: sıra (liste cevaplarında), ek ("Mutfakta" ~ "mutfak", "kitabı" ~ "kitap"), saat yazımı (13.45 ~ 13:45) ve birim ("30 dakika" ~ "30") farkı tolere edilir.
- **MEB.** Kural eşleşmesi yalnız emin olduğunda doğru der; emin olmadığı cevap yanlış sayılır (LLM hakem yok):
  - cevaptaki bağımsız sayıların tamamı metindeki sırasıyla ve işaretleriyle altınla aynı olmalı (harfe bitişik rakam, ör. CO2, sayı sayılmaz); sayılar aynıysa metin de tutmalı ("298" ~ "298 K" geçer, "2 mol" ~ "2 L" geçmez),
  - altında olmayan olumsuzluk ya da seçenek sözcüğü (değil, hayır, yok, ya da, veya) varsa eşleşme kabul edilmez,
  - metinde: parantezler atıldıktan sonra normalize eşitlik ya da altın cevabın sözcüklerinin model cevabında sırasıyla geçmesi; sözcükte Türkçe ek iki yönde tolere edilir: cevap ekli ("azalır" ~ "azalırlar") ya da kök hâlinde (8 Kasım: 5+ harfli kök ve bilinen bir ek, "idrar" ~ "idrarla", "karbon" ~ "karbonu"), ünsüz yumuşaması dahil ("esneklik" ~ "esnekliği", "haploid" ~ "haploit"),
  - bu kurallar altının yanında `orijinal.kabul_edilen` listesindeki eşdeğer yazımlarla da denenir (7 Kasım; 5.564 soruda 16.711 yazım, ör. "Karbondioksit" için "CO2", "yarıya iner" için "yarısına iner").

  Bu yüzden MEB skoru, eşdeğer ama listede olmayan yazımları kaçırabilir; skor bu anlamda bir alt sınırdır. Altın cevaplar LLM ile doğrulandığı için MEB skorlarını kesin setlerden ayrı raporlayın.

## Bu sürümde yapılan düzeltmeler (30 Ekim 2026)

Veri:
- **Birim dönüşümü, `ters_problem`:** 300 sorunun 34'ünde altın cevap, sorudaki yuvarlanmış değerden elde edilemiyordu. Örnek: "0,004 hektar kaç m²?" sorusunda kayıtlı cevap 44,8, doğrusu 40. Cevaplar sorudaki değerden yeniden hesaplandı.
- **Birim dönüşümü, `oran_capraz_birim`:** 300 sorunun 89'unun cevabı 0'dı (ör. "263,7 cm², 40,3 hektarın kaç katı?"). Bunlarla birlikte aralık dışındaki 50 soru daha, aynı kimliklerle makul oranlı yeni sorularla değiştirildi.
- **Tekrarlar atıldı:** SQL il/ilçe'de birebir tekrar eden 2.243 satır (aynı soru, aynı veritabanı, aynı sonuç), TURSpider'da 76 satır, birim dönüşümünde 3 satır.
- **SQL çıktı tahmininde İstanbul ağırlığı azaltıldı.** ROUND'lu basit sorguların 3.512'sinin 3.292'si İstanbul'dandı.
  - İstanbul tablo dilimi başına 32 soruyla sınırlandı (990 kaldı).
  - Diğer kaynaklardan 736 kesik tablolu soru eklendi: Dünya Bankası 598, Eurostat 120, İzmir 18.
- **Dış setler yeniden süzüldü.** Sonucu boş çıkan SELECT'ler atıldı (her boş cevap doğru sayılırdı). Bunlara ek olarak Cognipeer'de:
  - zamana bağlı sorgular (`NOW()`, `CURDATE()`, `'now'`) atıldı,
  - veritabanını hiç değiştirmeyen değiştirme ifadeleri atıldı.

Puanlayıcılar (eski skorlar bu yüzden biraz farklı çıkabilir):
- **Tarih:** Altın sözcükler eskiden tüm metinde ve alt dizge olarak aranıyordu. "8 yaş" altını, "98765" cevabında "8" geçtiği için doğru sayılıyordu (ters sınamada 2.100'ün 170'i). Artık yalnız `CEVAP:` satırına, sözcük düzeyinde bakılıyor. Kayıtlı 226 model cevabında yalnız 5'inin sonucu değişti; beşi de gerçekten yanlıştı.
- **MEB hızlı eşleşmesi:** İki yönde harf dizgesi arıyordu. Altın "C" iken "c" harfi geçen her cevap doğru sayılıyordu; altın cevapların 483'ü 3 karakter ya da daha kısa. Ayrıca "Apolardır" altınına verilen "polar" cevabı da doğru geçiyordu.
- **Solver `orta`:** Göreli 0,0005 tolerans optimuma yakın ama optimal olmayan değerleri kabul ediyordu (optimum 27.885 iken 27.886 doğru sayılıyordu). Artık birebir eşitlik aranıyor.
- **SQL çıktı tahmini:** Gevşek ayrıştırıcı pakete alındı. Eski ayrıştırıcı `[[[…]]]` ve `\"` biçimindeki doğru cevapları yanlış sayıyordu (168 denemenin 8'i).
- **Excel:** Süre sınırı (`grade_sinirli`) pakete alındı. Dev aralıklı formüller puanlamayı saatlerce kilitliyordu.

## Doğrulayıcı düzeltmeleri (31 Ekim 2026)

Puanlayıcılar ve altın cevaplar bağımsız olarak yeniden sınandı. Altın cevaplar üretici koddan ayrı yazılmış hesap ve çözücülerle soru metninden yeniden hesaplandı: fizik, kimya, tarih, matris ve bulmaca altınlarında hata çıkmadı. SQL il/ilçe ve istatistik setlerinin hepsi yeniden çalıştırmada aynı sonucu verdi. Puanlayıcılarda şu hatalar düzeltildi:

- **Matris doğrusal sistem:** Tüm metindeki ilk "x =" alınıyordu, yani akıl yürütmedeki ara adım. Kayıtlı 20 doğru cevabın 20'si yanlış sayılmıştı. Artık yalnız son `CEVAP:` satırı okunuyor. Matriste tam sayılar birebir karşılaştırılıyor; eskiden %1 tolerans 345 için 347'yi de kabul ediyordu.
- **Hesaplama sayıları:** Tüm metnin son sayısı alınıyordu (`CEVAP: 17.67 m/s^2` → 2). Artık son `CEVAP:` satırı okunuyor ve birim üsleri sayılmıyor.
- **Birim dönüşümü:** 63 altın cevap 3 ondalığa aşırı yuvarlanmış (102,51 Pa → 0,001 bar; kesini 0,0010251). Soruda KB'nin, galonun ve HP'nin hangi tanımı kullanıldığı yazmıyor. Puanlayıcı soruyu yeniden hesaplayıp kesin değeri ve ikinci yaygın tanımla bulunan değeri de kabul ediyor. 2 Kasım'da tanımlar soruya eklendi (aşağıda); tanımı yazan soruda ikinci tanım artık kabul edilmiyor.
- **Tarih:** `21.03.2019` gibi sayısal yazım kabul ediliyor. "bir önceki gün"de "bir" isteğe bağlı. "İki tarih dahil değil" diyen 146 gün farkı sorusunda iki okuma da kabul ediliyordu; 2 Kasım'da soru ifadesi düzeltildi (aşağıda).
- **JSON/XML:** Sayılarda %1 tolerans vardı; yanlış fiyat ve stok kabul ediliyordu. Artık birebir.
- **Bulmaca:** `puanla` yalnız kesin eşleşmeyi döndürüyordu ve hakemin doğru saydığı 720 cevabın 114'ünü reddediyordu ("Aslı ve Pelin" / "Aslı, Pelin", "13.45" / "13:45"). Artık gevşek eşleşme dönüyor; hakemle 714/720 uyumlu.
- **SQL karşılaştırıcısı:** Tam sayılarda göreli 1e-3 tolerans vardı (999 = 1000; tamsayı tarih 19680831 = 19690101). Artık tam sayılar birebir. Altın sorgu eşit değerler yüzünden taramaya bağlıysa iki geçerli sonuç da kabul ediliyor (Cognipeer 72, çıktı tahmini 66 satır).
- **MEB hızlı eşleşmesi:** Yalnız ilk sayılar karşılaştırılıyordu. Gerçek ölçümlerde "3/4" cevabı "3/1" altınına, "atom numarası 84" cevabı "88" altınına doğru sayılmıştı. Artık bütün sayılar sırasıyla ve işaretleriyle karşılaştırılıyor; olumsuz ya da çok seçenekli cevap hakeme bırakılıyor.

Bu yüzden önceki sürümle alınan matris, bulmaca ve MEB (hakemsiz) skorları bu sürümle karşılaştırılamaz. `araclar/altin_sinama.py` ayrıca `--yakin` kipiyle az bozulmuş cevapların reddedildiğini sınıyor.

## Veri düzeltmeleri (2 Kasım 2026)

Denetimde bulunan sorunlu sorular düzeltildi ya da çıkarıldı (137.784 → 136.941):

- **Birim dönüşümü (544 soru):** KB/MB/GB/TB (1024), galon (ABD) ve HP (745,7 W) tanımı soru sonuna eklendi (165 + 128 + 174 soru). Tanım yazılan soruda öbür tanımla bulunan değer artık kabul edilmiyor. Kesin değerden %0,5'ten fazla sapan 93 altın, sorudan yeniden hesaplanıp 4 anlamlı basamakla yazıldı.
- **Gün farkı (146 soru):** "(iki tarih dahil değil, aradaki gün sayısı) kaç gün geçer?" ifadesi "kaç gün vardır?" oldu; altın düz fark.
- **Bulmaca (630 soru, cevaplar değişmedi):** Zebra'da "X'in evi, Y evi solundadır" → "Y evinin solunda bir yerdedir" ve "mavi ev limonata içmektedir" → "mavi evde oturan kişi …" (446). Doğrucu-yalancıda "Ben ile X aynı türdeniz" → "X ile ben …" (147). Yön sorularında ilgi eki (37).
- **SQL (20 soru silindi):** Altın SQL'i bozuk satırlar: Cognipeer'de GROUP BY'sız HAVING 18, TURSpider'da 2.
- **Cognipeer çevirisi (5.098 soru):** Türkçe çeviri tırnak içindeki SQL değerlerini de çevirmişti ("'Kırmızı Hat' olarak güncelle", altın `'Red Line'`; soruda olup ne altın SQL'de ne veride geçen değer). Bu satırlarda INSERT/UPDATE/DELETE soruları çözülemiyordu (24B %23,7, Flash %21,5; sorunsuz satırlar %71–72). DeepSeek-V4-Flash, İngilizce kaynak soru ve altın SQL'le değerleri birebir geri yazdı; kod denetimi (her tırnak içi değer SQL'de ya da veride geçmeli, geri kalan metin aynı kalmalı) tutmayan ya da modelin "düzeltilemez" dediği 716 satırı sildi, 4.382 satır güncellendi (Cognipeer 69.016 → 68.300). Sonrasında değişiklik soruları %74,0 / %70,8, SELECT %81,7 / %82,2 (kontrol %71,9 / %72,9). Eski çeviri `orijinal.soru_ceviri_eski` alanında. Maliyet $0,20 (+ ölçüm $0,48).
- **MEB (243 soru):** Altın denetiminde (DeepSeek-V4-Flash, önce pasajsız, sonra kaynak pasajla) sorunlu çıkan 243 soru, kaynak pasajla birlikte DeepSeek-V4-Pro'ya düzelttirildi. Düzeltilen soru V4-Flash'a çözdürüldü; cevap yeni altınla kural ya da LLM hakemle eşleşirse kabul edildi, eşleşmezse bir tur daha düzeltildi. 136 soru güncellendi (tek ders 119, çapraz 17); düzeltilemeyen ya da pasajla ilgisiz 107 soru silindi (tek ders 105, çapraz 2). Eski soru ve cevap `orijinal.duzeltme` alanında duruyor.

## MEB temizliği ve kabul edilen yazımlar (7 Kasım 2026)

- **63 soru çıkarıldı** (tek ders 51, çapraz 12): 33'ü şekil, tablo, düzenek ya da seçenekler olmadan çözülemiyordu ("Tabloya göre…", seçeneksiz "aşağıdakilerden hangisi", cevap "1 yönü"); 13'ü görülmeyen metne atıf yapıyordu ("metinde hangi madde belirtilmiştir?"); 4'ü bozuktu; 13'ü örneklem okumasında muğlak (birden çok savunulabilir cevap), öncülü hatalı ya da birbiriyle çelişen sorulardı. Test kümesinden 14, ölçüm alt kümesinden 1 soru düştü; yerlerine soru konmadı (çıkarılanlar `benchmark/*_meb_cikarilan_2026-11-07.jsonl`).
- **Kabul edilen yazımlar:** DeepSeek-V4-Flash her soru için eşdeğer kısa yazımlar önerdi; kod süzgeci (sayısı farklı, karşıt yönlü, "ya da" içeren, kuralca zaten eşleşen adaylar atılır) ve katı istemli DeepSeek-V4-Pro hakemi ("alkol" ~ "etil alkol", "mezür" ~ "pipet" reddedilir) geçenler `orijinal.kabul_edilen`'e yazıldı. 2 Kasım cevaplarında hakemsiz kural 24B'de 67 → 89, Flash'ta 96 → 126, düşünen Flash'ta 101 → 129 doğru buldu (199 cevap); yeni kabullerin hiçbiri hakemin yanlış dediği bir cevap değil. Hakemli skor değişmez; hakemsiz skor (ör. GRPO ödülü) gerçeğe yaklaşır ama yine alt sınırdır.

## Cognipeer çıkarıldı (3 Kasım 2026)

`sql_cognipeer` (68.300 soru) bu sürümden çıkarıldı. Kaynağı `gretelai/synthetic_text_to_sql`'in Türkçe çevirisi; bu set eğitim verisi olarak üretilmiş: soru, şema ve altın SQL'i bir LLM yazmış, kaliteyi 1.000 örnekte GPT-4 hakem puanlamış. Altın SQL'in soruya göre doğruluğunu bağımsız denetlemenin yolu yok; yalnız çalıştığı doğrulanabiliyor. Benchmark'taki 100 Cognipeer sorusunun 30'unu üç model de yanlış yaptı ve elle okumada bunların ~28'i soru, altın ya da çeviri kaynaklıydı (çoğu İngilizce asılda da var):

- değiştirme sorusunda eklenecek değer verilmemiş ("tabloya kayıt ekle" → altın 'David Kim', 'Fatima Patel' ekliyor); 6.159 değiştirme sorusunun 1.244'ünde altındaki metin değeri ne soruda ne veride geçiyor,
- altın yanlış ("toplam misyon sayısı" → `SUM(mission_id)`; "toplam yatak" → hastane sayısı),
- altında istenmeyen sütun ya da sıralama (`RANK()` sütunu, belirtilmemiş `DESC`).

SQL yazma için `sql_belediye`, `sql_istatistik` ve `sql_turspider` kalıyor.

## Değerlendirme protokolü (7 Kasım 2026)

Skorların başkalarınca aynı şekilde alınabilmesi için ölçümler bu kurallarla yapılır. Model sonuçları ölçümler tamamlanınca eklenecek; bu sürümde skor yok.

**Küme.** Ölçüm kümesi: `benchmark/test_kumesi.jsonl` içinde `olcum: true` olan 4.199 satır, hepsi `test` bölümünden. 3.999 metin sorusu (14 set) ve 200 ajan terminal görevi; MEB ölçüme girmediği için değerlendirilen 3.800 metin sorusu, 12 set (aşağıda). Her alt başlıktan ~100 soru alınır; bulmaca, hesaplama, ızgara, satranç, solver, karakter işlemleri, Excel veritabanı ve ajan terminalde test bölümünün tamamı kümededir. SQL setleri, iki MEB seti ve regex 100'er soru (MEB tek ders 99). Birden çok veritabanını bağlayan ATTACH soruları (`neden: attach`) ölçüm kümesinde yok. İsteyen test bölümünün tamamını (8.171) da kullanabilir; ölçüm kümesi testin başlık ortalamasını ve set ortalamasını ±0,5 puan içinde verdi (6 Kasım, Qwen3.5-9B düşünmesiz, 7 Kasım MEB güncellemesinden önceki puanlayıcıyla).

**İstem ve cevap.** İstem `puanlama.istem(satir)`: tek kullanıcı mesajı, sistem mesajı yok, soru başına tek deneme. Puanlanan yalnız modelin cevap metnidir (`message.content`); düşünme metni (`reasoning_content`) puanlanmaz.

**Modeller ve ayarlar.** DeepInfra (OpenAI uyumlu API, Batch); Cosmos kiralık GPU'da vLLM ile.

| Model | Düşünme | Ayar | Çıktı sınırı |
|---|---|---|---:|
| `Qwen/Qwen3.5-9B` | açık (varsayılan) | temperature 0,6, top_p 0,95 (model kartının düşünme modu önerisi) | 32.000 |
| `Qwen/Qwen3.5-9B` (taban) | kapalı | `reasoning_effort: none`, temperature 0 | 16.000 |
| `google/gemma-4-31B-it` | açık | `reasoning_effort: high`, temperature 0 | 32.000 |
| `openai/gpt-oss-120b` | açık | `reasoning_effort: high`, temperature 0 | 32.000 |
| `ytu-ce-cosmos/Turkish-Gemma-9b-v0.1` | yok | temperature 0 | bağlam 8.192 içinde kalan |

Sınıra takılan, boş dönen ya da istek hatası alan cevap yanlış sayılır ve oranı ayrıca raporlanır. Cosmos'un bağlamına sığmayan 63 soru (`sigmadi_cosmos.json`) ona gönderilmez ve onun skoruna girmez. Modeller arası karşılaştırma bu soruların çıkarıldığı ortak kümeyle de verilir.

**Puanlama.** `puanla(satir, metin)`, tamamen kurala dayalı; LLM hakem yok. Puanlayıcı hatası ve zaman aşımı yanlış sayılır, ayrıca raporlanır. Regex'te kararın DFA eşdeğerliğiyle mi gizli testlerle mi verildiği (`via`) ayrı yazılır.

**Skor.** Ana skor **set ortalaması**: 12 metin setinin her biri eşit ağırlıkta. Başlık ortalaması (38 başlık) ve mikro doğruluk ek bilgi olarak verilir. Başlık ortalamasında bulmaca ve hesaplama 38 başlığın 17'sini tuttuğu için skor kolay setlere kayar; bu yüzden ana skor olarak kullanılmaz. Ajan terminal çok turlu olduğu için (`ajan_eval/`) ayrı raporlanır. 100 soruluk bir sette tek modelin 95% güven aralığı en kötü ±10 puandır. Qwen'in düşünen ayarı örneklemeli olduğu için tekrar koşulduğunda set skorları birkaç puan oynayabilir.

**MEB ölçüme girmiyor (9 Kasım).** `meb_tek_ders` ve `meb_capraz` veri setinde duruyor, ama değerlendirmeye ve ana skora alınmıyor. Kısa sözel cevaplar kuralla yalnız yazım düzeyinde karşılaştırılabiliyor: eşdeğer ama farklı yazılmış cevaplar ve birden çok doğru cevaba açık sorular LLM hakem olmadan ayırt edilemiyor (bir denetimde Gemma-4-31B'nin yanlış sayılan MEB cevaplarının ~üçte biri gerçekte doğru çıktı). İsteyen `--meb` ile koşabilir; skoru kurala dayalı alt sınırdır.

**Araç.** `araclar/tam_test.py`: `hazirla` (istek dosyaları ve maliyet tahmini), `gonder` (DeepInfra Batch), `kos` (vLLM), `al` (cevapları indirip puanlar), `rapor` (set ortalaması, başlık ortalaması, kesilme, puanlayıcı hatası; çıktı klasörüne `sonuclar.json` yazar). Varsayılan küme ölçüm kümesidir, `--tam` testin tamamını kullanır. Ortam: Python 3.10, `requirements.txt`; regex puanlaması süreç havuzunda yapılır.

**Adım adım (depo kökünden).** Metin soruları DeepInfra Batch'iyle; anahtar `DEEPINFRA_API_KEY` ortam değişkeninde. Para harcayan komutlar `--onay` ister.

```bash
pip install -r requirements.txt
bash araclar/turspider_indir.sh                                   # sql_turspider veritabanları
export DEEPINFRA_API_KEY=...
python3 araclar/tam_test.py hazirla --dir sonuc --model gemma --tam  # istek dosyası + maliyet tahmini (ağsız)
python3 araclar/tam_test.py gonder  --dir sonuc --model gemma --onay # Batch gönderimi
python3 araclar/tam_test.py al      --dir sonuc --model gemma --tam  # bitince indirir ve puanlar
python3 araclar/tam_test.py rapor   --dir sonuc --tam                # sonuc/sonuclar.json; ölçüm kümesi için --tam'sız
```

Modeller: `qwen`, `qwen_dusunmesiz`, `gemma`, `oss`, `cosmos` (Cosmos: vLLM sunucusu ve `kos --base-url ...`). Başka bir OpenAI uyumlu sunucu için `kos --base-url <url>` kullanılabilir. `--tam` testin tamamı (6.963 metin isteği; ATTACH'li 109 soru koşulur, skora girmez), `--tam`'sız ölçüm kümesi (3.800). MEB varsayılan olarak dışarıda; `--meb` ile eklenir.

Ajan terminal görevleri çok turlu olduğu için ayrı koşulur (Linux, `bwrap`, `pip install -r ajan_eval/requirements.txt`):

```bash
ONAY=1 DEEPINFRA_API_KEY=... ORNEK=10 bash araclar/ajan_test.sh gemma sonuc   # 10 görevlik pilot
ONAY=1 DEEPINFRA_API_KEY=... bash araclar/ajan_test.sh gemma sonuc            # test 200 görev -> sonuc/ajan_gemma.jsonl
```

## Bilinen sınırlar

- **Birim dönüştürme:** Hesaplama sorularında altın cevap, sorunun istediği birimdedir ("kaç Joule'dür?" → J). Paketteki puanlayıcı (`puanla`) birim dönüştürmez: başka birimle yazılmış doğru cevap (ör. 11971 J yerine "11.97 kJ") yanlış sayılır. Benchmark'taki 2.600 cevapta bu durum görülmedi. Kendi puanlayıcınızı kullanıyorsanız birim dönüştürme ekleyebilirsiniz.
- **MEB'de kalıntı sorunlu sorular (~%10, tahmin):** Denetim ve düzeltmeden sonra da kalan sorunlar var. Benchmark'ta düşünen V4-Flash'ın yanlış yaptığı 23 MEB sorusunun ~20'si elle okumada soru kaynaklı çıktı: birden çok doğru cevap ("sumasyon" / "fizyolojik tetanus"), şekle dayalı soru, döngüsel soru ya da yanlış altın (CCU/CCC/CCA/CCG'nin hepsi yalnız prolini şifrelerken altın "AUG kodonu"). Bu sorularda en iyi model de yanlış sayılır; MEB skorlarının tavanı bu yüzden ~%90.
- **Önceki ölçümler** (yöntem belgesindeki pilotlar ve 2 Kasım benchmark'ı) farklı istem, deneme sayısı, `reasoning_effort` ve MEB hakemiyle alındı; değerlendirme protokolüyle karşılaştırılamaz.
- **`sayac_takip` (bulmaca):** Tuzak sorular var: hiç aktarılmamış bir rengin "kaç tane aktarıldı" diye sorulması gibi; cevabı "0" ya da "hiçbiri". 1 Kasım 2026'da bunların oranı %43'ten %15'e indirildi (300 sorunun 46'sı); 82 soru aynı üreticiyle üretilmiş yeni sorularla değiştirildi.
- **SQL çıktı tahmininde şablon tekrarı:**
  - Dünya Bankası'nın 598 sorusu 4 SQL iskeletinden geliyor ("gösterge/yıl için ilk N ülke").
  - Hesapsız kesik soruların 238'inin cevabı tek satır.
- **TURSpider:** Spider'ın boş gelen veritabanlarındaki soruların hepsi elendi; bunların çoğu eğitim bölümündeydi (coğrafya, akademisyen, restoranlar, imdb, yelp: 1.619 soru). Spider'da sıra bağı olan `LIMIT` sorgularında birden çok doğru cevap olabilir; puanlayıcı altının ters taramadaki sonucunu da kabul eder, ama üç ve daha fazla satırlık bağlarda her olası sonucu kapsamaz.
- **Manisa açık verisi çıkarıldı (1 Kasım 2026):** Portaldaki bütün veri setleri `mbb-odl-1.0` lisansıyla işaretli, ancak lisans metni yayımlanmamış (sayfa 404, arşivde de yok). Lisans doğrulanamadığı için Manisa kaynaklı 213 soru (SQL yazma 110, çıktı tahmini 103) ve Manisa veritabanı bu sürüme alınmadı.

## Lisans ve atıf

Veri seti **CC BY-SA 4.0** ile dağıtılır. TURSpider alt seti CC BY-SA olduğu için "aynı lisansla paylaş" şartı bütüne uygulanır. Diğer kaynakların lisansları bununla birlikte dağıtılabilir; her kaynağa ayrıca atıf yapılmalıdır. Puanlama kodu da aynı lisansla verilir. Kaynaklar ve lisansları:

| Kaynak | Lisans |
|---|---|
| İBB (İstanbul, Kadıköy, Tuzla), Kayseri, Konya, İzmir, Ankara açık veri | CC BY 4.0 (İBB: CC BY 4.0 eşdeğeri) |
| Trabzon, Sakarya açık veri | Belediye açık veri lisansı (ticari kullanım dahil, atıfla) |
| Eurostat, Dünya Bankası WDI | CC BY 4.0 |
| Wikidata | CC0 |
| OCHA HDX / HGK il ve ilçe sınırları (SQL istatistik, Excel veritabanı) | CC BY-IGO |
| USGS deprem kataloğu | Kamu malı |
| TURSpider (github.com/alibugra/TURSpider) | CC BY-SA 4.0 |
| Lichess bulmaca veritabanı (`satranc`) | CC0 |
| StructuredRegex (`regex`, 212 soru, Türkçe çeviri) | MIT |
| `emreseyhan/Turkish-customer-service-conversations` (`regex`, 33 soru; IBAN, kart, TCKN değerleri uydurma) | CC BY 4.0 |
| GECTurk (`karakter_islemleri` başlangıç cümleleri) | Apache-2.0 |
| MEB ders kitapları | Alıntılar FSEK m.35 kapsamında. `meb_tek_ders` satırlarının bir kısmında `gerekce` alanı kitaptan tek cümle içeriyor. Kaynak her satırda: "MEB `ders` dersi `sinif`. sınıf ders kitabı" (`orijinal.ders`, `orijinal.sinif`, `orijinal.unite_no`, `orijinal.konu_baslik`) |

Her SQL ve Excel kaydında `lisans` ya da `orijinal.lisans` alanı bulunur.
