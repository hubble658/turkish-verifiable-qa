---
license: cc-by-sa-4.0
language:
- tr
pretty_name: Doğrulanabilir Türkçe Soru Veri Seti
size_categories:
- 100K<n<1M
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
- config_name: sql_belediye_disi
  data_files: veri/sql_belediye_disi.jsonl.gz
- config_name: sql_cikti_tahmini
  data_files: veri/sql_cikti_tahmini.jsonl.gz
- config_name: sql_cognipeer
  data_files: veri/sql_cognipeer.jsonl.gz
- config_name: sql_il_ilce
  data_files: veri/sql_il_ilce.jsonl.gz
- config_name: sql_turspider
  data_files: veri/sql_turspider.jsonl.gz
---

# Doğrulanabilir Türkçe Soru Veri Seti

Cevabı programla kontrol edilebilen **137.997** Türkçe soru: mantık bulmacaları, hesaplama, Excel formülü, optimizasyon, SQL yazma, SQL çıktısı tahmini ve MEB ders kitaplarından kısa cevaplı sorular. Her sorunun yanında altın cevap ve onu puanlayan kod var: Excel ve SQL cevapları çalıştırılarak, sayılar toleransla, bulmacalar normalize eşleşmeyle puanlanır.

Sürüm: 30 Ekim 2026.

## İçerik

| Dosya (`veri/`) | Soru | Köken | Cevabı kim belirler | Modelden istenen |
|---|---:|---|---|---|
| `bulmaca.jsonl.gz` | 3.000 | özgün | Program (çözücü + tek çözüm kontrolü) | Kısa cevap |
| `hesaplama.jsonl.gz` | 14.613 | özgün | Program (formül, sympy, datetime, şema) | Sayı+birim / tarih / matris / JSON / XML / Excel formülü |
| `excel_veritabani.jsonl.gz` | 1.000 | özgün | Program (Python + iki formül motoru + LibreOffice) | Tek Excel formülü |
| `solver.jsonl.gz` | 4.986 | özgün | Program (OR-Tools CP-SAT, kanıtlı en iyi değer) | En iyi değer (`orta`) ya da Python programı (`kod`) |
| `sql_il_ilce.jsonl.gz` | 17.895 | özgün | Gerçek SQLite'ta çalıştırma | SQL sorgusu |
| `sql_belediye_disi.jsonl.gz` | 9.234 | özgün | Gerçek SQLite'ta çalıştırma | SQL sorgusu |
| `sql_cikti_tahmini.jsonl.gz` | 3.424 | özgün | Gerçek SQLite'ta çalıştırma | Verilen SQL'in çıktısı (JSON tablo) |
| `meb_tek_ders.jsonl.gz` | 2.914 | özgün | LLM + kitap pasajı, LLM tutarlılık kontrolü | Kısa cevap |
| `meb_capraz.jsonl.gz` | 3.993 | özgün | LLM + iki ders pasajı, LLM hakem | Kısa cevap |
| `sql_turspider.jsonl.gz` | 7.904 | `turspider_filtreli` | Gerçek SQLite'ta çalıştırma | SQL sorgusu |
| `sql_cognipeer.jsonl.gz` | 69.034 | `cognipeer_filtreli` | Gömülü şemada çalıştırma | SQL ifadesi (sorgu ya da değiştirme) |
| **Toplam** | **137.997** | | | |

**Doğrulama gücü** üç gruba ayrılır, raporlarda ayrı verin:

- **Kesin, özgün (54.152 soru):** Bulmaca, hesaplama, Excel, solver ve bizim SQL setlerimiz. Cevap kodla hesaplanır ya da gerçek veritabanında çalıştırılır.
- **LLM ile doğrulanmış (6.907 soru):** MEB setleri. Altın cevap kitap pasajına dayanır, ama doğruluğu LLM kontrolüne bağlı. Örneklem denetimlerinde düşük oranlı etiket hataları görüldü.
- **Dış setlerden filtrelenmiş (76.938 soru):** TURSpider ve Cognipeer.
  - Altın sonuç bu paket için yeniden çalıştırılarak hesaplandı; bu açıdan kesin.
  - Soru metni ile gold SQL'in uyumu ise kaynak setin kalitesine bağlı. TURSpider insan çevirisi, Cognipeer LLM üretimi.

`koken` alanı her satırda bu ayrımı taşır: `ozgun`, `turspider_filtreli` ya da `cognipeer_filtreli`.

## Satır şeması

Her dosya satır başına bir JSON nesnesi içerir:

| Alan | Anlam |
|---|---|
| `id` | Benzersiz kimlik |
| `kaynak` | `bulmaca`, `hesaplama`, `korpus` (MEB), `solver`, `sql` |
| `kategori` | Alt set (ör. `birim_donusumu`, `sql_il_ilce`, `korpus_capraz_eslestirmeli`) |
| `alt_tip` | Şablon ya da soru tipi |
| `koken` | `ozgun` / `turspider_filtreli` / `cognipeer_filtreli` |
| `zorluk` | **Şimdilik `null`.** Tüm setlere aynı ayarla koşulacak son benchmark'tan doldurulacak |
| `zorluk_uretim` | Üretimdeki etiket. Setler arasında karşılaştırılamaz (bulmacada kolay/zor, hesaplama ve SQL'de orta/zor, TURSpider'da easy…extra, Cognipeer'de karmaşıklık sınıfı; MEB, solver ve çıktı tahmininde `null`) |
| `soru` | Soru metni (istem değil; istem `puanlama.istem` ile kurulur) |
| `cevap` | Altın cevap. SQL yazma setlerinde gold SQL; çıktı tahmininde beklenen tablo |
| `orijinal` | Kaynak kaydın tamamı, **JSON metni olarak** (`json.loads(satir["orijinal"])` ya da `puanlama.orijinal(satir)`). İç yapısı setten sete değiştiği ve tablolarda metin ile sayı karıştığı için metin olarak saklanır. Puanlayıcının ihtiyaç duyduğu ek alanlar burada: `tolerans_yuzde`, `calisma_kitaplari`, `db`, `ekler`, `gercek_sonuc`, `sira_onemli`, `baglam`, `lisans`… |

## Kullanım

Hugging Face'ten:

```python
from datasets import load_dataset
ds = load_dataset("hubble658/turkish-verifiable-qa", "hesaplama", split="train")   # set adı = config
```

Puanlama kodu ve veritabanları depoda; puanlamak için depoyu indirin:

```bash
huggingface-cli download hubble658/turkish-verifiable-qa --repo-type dataset --local-dir turkish-verifiable-qa
cd turkish-verifiable-qa
pip install openpyxl          # yalnız LibreOffice yedeği için; çekirdek puanlama standart kütüphaneyle çalışır
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
- **MEB setleri:** Hızlı eşleşme tutmazsa, isteğe bağlı bir hakem modele danışılır: `puanla(satir, metin, hakem=lambda istem_metni: ...)`. Hakem verilmezse skor bir alt sınırdır.
- **Doğrulama:** `python3 araclar/altin_sinama.py veri/*.jsonl.gz` her satırın altın cevabını kendi puanlayıcısından geçirir. `--ters` bayrağı da bariz yanlış cevapların reddedildiğini sınar. Bu sürümde altın sınama 137.997/137.997 geçiyor. Ters sınamada 7 kabul var; bunların altın cevabı sınamada kullanılan yanlış değere (98.765,4321) gerçekten %0,5'ten yakın.

**Gerekenler:**
- Python ≥ 3.10.
- SQL setleri için `veritabanlari/` (14 SQLite dosyası, ~110 MB, depoda).
- `sql_turspider` için ayrıca indirme betiği.
- LibreOffice isteğe bağlı. Excel motorunun tanımadığı nadir fonksiyonlarda kullanılır; yoksa bu cevaplar yanlış sayılır.
- Solver `kod` seti modelin Python programını yerel olarak çalıştırır: 60 sn işlemci, 2 GB bellek, yasaklı modül listesi. Bu bir kum havuzu değildir, güvenmediğiniz ortamda konteyner içinde çalıştırın.

## Puanlama kuralları (özet)

- **Kapalı kitap.** Modele yalnız istem verilir. Kaynak pasaj, gold formül/SQL ve `orijinal` alanı gösterilmez. Tek istisna solver `kod` seti: orada model kod yazar ve kod çalıştırılır.
- **Hesaplama.** Son sayı `tolerans_yuzde` ile karşılaştırılır. Tarih sorularında son `CEVAP:` satırındaki sözcükler eşleşmeli. JSON/XML türü korunarak birebir karşılaştırılır. Excel formülü tabloda çalıştırılır; Türkçe Excel yazımı da kabul edilir.
- **Excel veritabanı.** Formül 5 çalışma kitabının (asıl + 4 karıştırılmış) hepsinde doğru sonucu vermeli. Her cevap ayrı süreçte 60 sn sınırla puanlanır.
- **Solver.** Tam sayı en iyi değer **birebir** eşit olmalı.
- **SQL yazma.** Model SQL'i salt okunur bağlantıda çalıştırılır (30 sn sınır).
  - Satır sayısı eşit olmalı. Sütun sırası önemsiz, fazladan sütun serbest.
  - Satır sırası yalnız `sira_onemli` ise önemli.
  - Sayılarda göreli 1e-3 ya da mutlak 0,011 tolerans var.
  - **Cognipeer'deki değiştirme görevleri** (INSERT/UPDATE/DELETE/DDL) için gold ve model ifadesi aynı gömülü bağlamın ayrı kopyalarında çalıştırılır; tüm tabloların son durumu aynı olmalı.
- **SQL çıktı tahmini.** Model JSON tabloyu yazar, karşılaştırma SQL yazmayla aynıdır. SQL'de en dışta `ORDER BY` varsa satır sırası önemlidir. Biçim toleransı var: kaçışlı tırnak, fazladan dış liste, tırnaksız metin. `CEVAP:` satırı varsa yalnız o satır okunur.
- **MEB.** Hızlı eşleşme ancak şu iki durumda doğru sayar:
  - parantezler atıldıktan sonra normalize eşitlik,
  - altın cevabın sözcüklerinin model cevabında sırasıyla geçmesi.

  Bunun dışındaki her şey hakeme gider. Hakem istemi: `puanlama/meb.py` → `JUDGE_PROMPT`; ölçümde `deepseek-ai/DeepSeek-V3-0324` kullanıldı.

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

## Bilinen sınırlar

- **Önceki benchmark skorları birbiriyle doğrudan karşılaştırılamaz.** Setler farklı istem, deneme sayısı ve `reasoning_effort` ile ölçüldü. Ayrıca bir kısmı yukarıdaki düzeltmelerden önce alındı. Aynı ayarla tek bir son benchmark planlandı; `zorluk` alanı ondan doldurulacak.
- **`sayac_takip` (bulmaca):** 300 sorunun 116'sının cevabı 0, çünkü hiç anılmayan bir kap soruluyor. Her soruya "0" diyen model bu tipte %39 alır.
- **SQL çıktı tahmininde şablon tekrarı:**
  - Dünya Bankası'nın 598 sorusu 4 SQL iskeletinden geliyor ("gösterge/yıl için ilk N ülke").
  - Hesapsız kesik soruların 238'inin cevabı tek satır.
- **TURSpider:** Spider'ın boş gelen veritabanlarındaki soruların hepsi elendi; bunların çoğu eğitim bölümündeydi (coğrafya, akademisyen, restoranlar, imdb, yelp: 1.619 soru). Spider'da sıra bağı olan `LIMIT` sorgularında birden çok doğru cevap olabilir; puanlayıcı yalnız gold sonucu kabul eder.
- **Cognipeer:** Şema İngilizce, istem Türkçe çeviri. MySQL'e özgü fonksiyonlar SQLite'ta taklit işlevlerle çalışır (`puanlama/cognipeer_shim.py`); model de aynı ortamda değerlendirilir.
- **Manisa:** Lisansı doğrulanamadı (kaynak sayfa 404). Bu sorular pakette; her satır `orijinal.lisans` alanında uyarı taşıyor.

## Lisans ve atıf

Veri seti **CC BY-SA 4.0** ile dağıtılır. TURSpider alt seti CC BY-SA olduğu için "aynı lisansla paylaş" şartı bütüne uygulanır. Diğer kaynakların lisansları bununla birlikte dağıtılabilir; her kaynağa ayrıca atıf yapılmalıdır. Puanlama kodu da aynı lisansla verilir. Kaynaklar ve lisansları:

| Kaynak | Lisans |
|---|---|
| İBB (İstanbul, Kadıköy, Tuzla), Kayseri, Konya, İzmir, Ankara açık veri | CC BY 4.0 (İBB: CC BY 4.0 eşdeğeri) |
| Trabzon, Sakarya açık veri | Belediye açık veri lisansı (ticari kullanım dahil, atıfla) |
| Manisa açık veri | **Doğrulanamadı** |
| Eurostat, Dünya Bankası WDI | CC BY 4.0 |
| Wikidata | CC0 |
| USGS deprem kataloğu | Kamu malı |
| TURSpider (github.com/alibugra/TURSpider) | CC BY-SA 4.0 |
| Cognipeer/synthetic-text-to-sql-tr (HuggingFace) | Apache 2.0 |
| MEB ders kitapları | Alıntılar FSEK m.35 kapsamında. `meb_tek_ders` satırlarının bir kısmında `gerekce` alanı kitaptan tek cümle içeriyor. Kaynak her satırda: "MEB `ders` dersi `sinif`. sınıf ders kitabı" (`orijinal.ders`, `orijinal.sinif`, `orijinal.unite_no`, `orijinal.konu_baslik`) |

Her SQL ve Excel kaydında `lisans` ya da `orijinal.lisans` alanı bulunur.
