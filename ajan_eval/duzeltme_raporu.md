# Düzeltme raporu: önceki ve sonraki hâl

## gen-k-0101-veri-yapisi (gizli_sart)

top_n'in sırası istemde yoktu.
İsteme eklendi: top_n elemanları en üstteki başta olacak şekilde döndürsün.

## gen-k-0903-yarisma (gizli_sart)

len(idx) aranıyordu.
İsteme eklendi: len(index) kayıtlı Flight sayısını döndürsün.

## gen-k-1046-veri-yapisi (gizli_sart)

add dönüş değeri aranıyordu.
İsteme eklendi: add, token yeni eklendiyse True, zaten varsa False döndürsün.

## gen-k-1136-yarisma (gizli_sart)

Kurucu ve iterator biçimi yazmıyordu.
İsteme eklendi: Kurucu olay satırlarının listesini alsın (EventCounter(lines)); counts tarih→adet sözlüğü olsun; yineleme (tarih, adet) çiftleri versin.

## gen-k-2028-veri-yapisi (gizli_sart)

Dönüş değerleri yazmıyordu.
İsteme eklendi: undo_last ve rollback geri alınan (key, amount) çiftini döndürsün.

## gen-k-8023-yarisma (gizli_sart)

from_file ve edges aranıyordu.
İsteme eklendi: Router.from_file(yol) sınıf metodu dosyadan nesne kursun; komşuluk listesi edges alanında (x, y) anahtarıyla dursun; find_nearest (x, y) alıp (x, y), nearest_for_all nokta listesi alıp (x, y) listesi döndürsün.

## gen-k-8031-yarisma (gizli_sart)

Kontrol istemde adı geçmeyen _handle alanına bakıyor.
İsteme eklendi: Açık dosya nesnesini self._handle alanında tut; __exit__ dosyayı kapatıp bu alanı None yapsın.

## gen-k-8109-yarisma (gizli_sart)

Kurucu ve dönüş biçimi yazmıyordu.
İsteme eklendi: Kurucu vardiya dosyasının yolunu alsın (Planner("shifts.txt")); available adları alfabetik sıralı liste döndürsün.

## gen-k-8113-hata-bul (gizli_sart)

Dönüş biçimi yazmıyordu.
İsteme eklendi: parse_stream dosya benzeri nesne alıp (ip, method, path, status) demetlerinin listesini döndürsün (status int); count_errors da dosya benzeri nesne alsın, IP→sayı sözlüğü döndürsün; hatası olmayan IP sözlükte yer almasın.

## gen-k-8131-yarisma (gizli_sart)

build_sets imzası ve alan adları yazmıyordu.
İsteme eklendi: build_sets(metin, urunler) dosya içeriğini ve ürün listesini alıp StockSets döndürsün; alanlar shared, absent, unique kümeleri olsun (hiçbir satırda geçmeyen, verilen ürün listesine göre).

## gen-k-8138-yarisma (gizli_sart)

Closure adı ve imza yazmıyordu.
İsteme eklendi: make_prefix içindeki iç fonksiyonun adı query olsun; range_balance(yol, i, j) imzasını kullan; içe aktarmalar çalışma dizininden bank paketiyle çalışsın.

## gen-k-8148-veri-yapisi (gizli_sart)

Küçük harf ve dönüş biçimi yazmıyordu.
İsteme eklendi: Kelimeler boşlukla ayrılıp küçük harfe çevrilsin; search belge kimliklerini, words kelimeleri sıralı liste döndürsün; feed (doc_id, text) çiftleri alsın.

## gen-k-8395-hata-bul (gizli_sart)

Negatif k davranışı belirsizdi.
İsteme eklendi: k negatifse boş liste döndürsün.

## gen-k-8439-yarisma (gizli_sart)

oku dönüşü ve kalemler() yazmıyordu.
İsteme eklendi: oku nesnenin kendisini döndürsün (Stok().oku(yol)); bilinmeyen kalem için tutar 0.0 olsun; kalemler() kalem adlarını sıralı liste döndürsün.

## gen-s-0003-karsilastir (altin_yanlis)

Başlıktaki 'kalem' sözcüğü de sayılmış; ortak kalemler gelir ve gider.
Önceki kontrol: `[{"op": "file_content_eq", "path": "sonuc.txt", "value": "3"}]`
Yeni kontrol: `[{"op": "file_content_eq", "path": "sonuc.txt", "value": "2"}]`

## gen-s-0009-birlestir (altin_yanlis)

Altın cut artığıydı ('22},18},...').
İsteme eklendi: sicakliklar.txt dosyasında her satırda yalnız bir sıcaklık değeri olsun.
Önceki kontrol: `[{"op": "file_content_eq", "path": "sicakliklar.txt", "value": "22},18},25},28}"}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "sicakliklar.txt", "value": ["22", "18", "25", "28"]}]`

## gen-s-0009-karsilastir (gizli_sart)

JSON yapısı istemde yoktu.
İsteme eklendi: JSON biçimi: her satır bir nesne olan bir liste, [{"line": "<satırın tamamı>"}].

## gen-s-0016-ayikla (altin_yanlis)

Altında head/tail dosya başlıkları vardı; ayrıca çıktı yeri yazmıyordu.
İsteme eklendi: Çıktıyı çalışma dizininin kökünde (sonuclar.txt) oluştur, alt dizine yazma.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "sonuclar.txt", "value": ["2023-01-01 08:00 Dr.Ayse", "2023-01-01 10:00 Dr.Fatma", "2023-01-01 11:00 Dr.Kazim", "2023-01-01 12:00 Dr.Zeynep", "2023-01-01 13:00 Dr.Ali", "2023-01-01 15:00 Dr.Ayse", "==> hastane/acil/randevular.txt <==", "==> hastane/lab/randevular.txt <==", "==> hastane/poliklinik/randevular.txt <=="]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "sonuclar.txt", "value": ["2023-01-01 08:00 Dr.Ayse", "2023-01-01 10:00 Dr.Fatma", "2023-01-01 11:00 Dr.Kazim", "2023-01-01 12:00 Dr.Zeynep", "2023-01-01 13:00 Dr.Ali", "2023-01-01 15:00 Dr.Ayse"]}]`

## gen-s-0022-donustur (yol_belirsiz)

Model dosyayı kargo/ altına yazdı, kontrol kökte arıyor.
İsteme eklendi: Çıktıyı çalışma dizininin kökünde (toplam.txt) oluştur, alt dizine yazma.

## gen-s-0037-ozetle (altin_yanlis)

Altın iki dosyayı yan yana yapıştırmıştı.
İsteme eklendi: Her log satırı için bir çıktı satırı olsun: "<tarih> <mesaj>"; tarih satırın ilk 10 karakteri, mesaj 21. karakterden satır sonuna kadar olan kısım.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "summary/combined.txt", "value": ["2023-10-01INFO  User1 login 2023-10-01INFO  User2 login", "2023-10-01ERROR Disk full 2023-10-01ERROR Network down", "2023-10-01WARN  CPU high 2023-10-01WARN  RAM low"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "summary/combined.txt", "value": ["2023-10-01 INFO  User1 login", "2023-10-01 ERROR Disk full", "2023-10-01 WARN  CPU high", "2023-10-01 INFO  User2 login", "2023-10-01 ERROR Network down", "2023-10-01 WARN  RAM low"]}]`

## gen-s-0038-toplu-yeniden-adlandir (yol_belirsiz)

Hedef dizinin yeri yazmıyordu.
İsteme eklendi: Çıktıyı çalışma dizininin kökünde (renamed_files dizini) oluştur, alt dizine yazma.

## gen-s-0041-birlestir (altin_yanlis)

Vardiya dosyalarında yalnız 'Day'/'Night' sözcüğü vardı.
İsteme eklendi: merged.txt satırları "<id> <ad> <vardiya>" biçiminde olsun; shift_Day.txt ve shift_Night.txt o vardiyanın merged.txt satırlarını içersin.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "merged.txt", "value": ["101 Alice Night", "102 Bob Day", "103 Charlie Day", "104 David Night"]}, {"op": "file_content_eq", "path": "shift_Day.txt", "value": "Day"}, {"op": "file_content_eq", "path": "shift_Night.txt", "value": "Night"}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "merged.txt", "value": ["101 Alice Night", "102 Bob Day", "103 Charlie Day", "104 David Night"]}, {"op": "file_lines_eq", "path": "shift_Day.txt", "value": ["102 Bob Day", "103 Charlie Day"]}, {"op": "file_lines_eq", "path": "shift_Night.txt", "value": ["101 Alice Night", "104 David Night"]}]`

## gen-s-0046-donustur (gizli_sart)

Altın hesap kodunu da istiyor.
İsteme eklendi: Her satır "<hesap kodu>,<hesap adı>,<tutar>" biçiminde olsun (ör. "101,Cash,1500.00").

## gen-s-0052-onar (gizli_sart)

Dosya biçimi yazmıyordu.
İsteme eklendi: Her dosyada yalnız iki ondalıklı toplam olsun (ör. 35.50).

## gen-s-0071-bol (altin_yanlis)

Altın kesik başlıklı dizin adlarıydı ('Great_Gatsby').
İsteme eklendi: Her kitap için books_processed/<kaynak dosya adı>.json dosyası olsun (ör. book1.json), içeriği {"Title": ..., "Author": ...}.
Önceki kontrol: `[{"op": "dir_entries_eq", "path": "books_processed", "value": ["Great_Gatsby", "Kill_a_Mockingbird", "info.json"]}]`
Yeni kontrol: `[{"op": "dir_entries_eq", "path": "books_processed", "value": ["book1.json", "book2.json", "book3.json"]}, {"op": "json_eq", "path": "books_processed/book1.json", "value": {"Title": "The Great Gatsby", "Author": "F. Scott Fitzgerald"}}, {"op": "json_eq", "path": "books_processed/book2.json", "value": {"Title": "1984", "Author": "George Orwell"}}, {"op": "json_eq", "path": "books_processed/book3.json", "value": {"Title": "To Kill a Mockingbird", "Author": "Harper Lee"}}]`

## gen-s-0080-denetle (altin_yanlis)

Referans ortak kimlikleri yanlış buluyor; altın [] idi, doğrusu notu değişen 102 Bob Johnson.
İsteme eklendi: Her öğrenci {"id": "102", "name": "Ad Soyad", "grade_a": <a dosyasındaki not>, "grade_b": <b dosyasındaki not>} biçiminde olsun.
Önceki kontrol: `[{"op": "json_eq", "path": "sonuc.json", "value": []}]`
Yeni kontrol: `[{"op": "json_eq", "path": "sonuc.json", "value": [{"id": "102", "name": "Bob Johnson", "grade_a": 92, "grade_b": 90}]}]`

## gen-s-0087-yeniden-duzenle (altin_yanlis)

Referans JSON'u awk ile bozuyor; altın 'id, 1,ad,' gibi satırlardı ve dosya sırasına bağlıydı. Çıktının yeri yazmıyordu.
İsteme eklendi: CSV'nin ilk satırı "id,ad,stok,fiyat" başlığı olsun, sonra her ürün bir satır (ör. "1,laptop x1,15,999.99"). Çıktıyı çalışma dizininin kökünde (envanter.csv) oluştur, alt dizine yazma.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "envanter.csv", "value": ["id,ad,stok,fiyat", "id, 1,ad,", "id, 3,ad,", "id, 4,ad,"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "envanter.csv", "value": ["id,ad,stok,fiyat", "1,laptop x1,15,999.99", "2,monitor y2,8,249.99", "3,klavye z3,25,49.99", "4,fare a4,30,19.99"]}]`

## gen-s-0088-donustur (altin_yanlis)

Referans sütunları çevirmiyor; altın girdinin aynısıydı.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "cikti.csv", "value": ["id,hasta_adi,soyadi,doctor,tarih,saat", "1,Ahmet,Yilmaz,Dr.Smith,2023-10-01,09:00", "2,Mehmet,Demir,Dr.Johnson,2023-10-01,10:00", "3,Ayse,Kaya,Dr.Smith,2023-10-01,11:00", "4,Fatma,Ozturk,Dr.Johnson,2023-10-02,09:00", "5,Can,Balci,Dr.Smith,2023-10-02,10:00"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "cikti.csv", "as_set": false, "value": ["saat,tarih,doctor,soyadi,hasta_adi,id", "09:00,2023-10-01,Dr.Smith,Yilmaz,Ahmet,1", "10:00,2023-10-01,Dr.Johnson,Demir,Mehmet,2", "11:00,2023-10-01,Dr.Smith,Kaya,Ayse,3", "09:00,2023-10-02,Dr.Johnson,Ozturk,Fatma,4", "10:00,2023-10-02,Dr.Smith,Balci,Can,5"]}]`

## gen-s-0101-toplu-yeniden-adlandir (gizli_sart)

JSON yapısı istemde yoktu. Çıktının yeri yazmıyordu.
İsteme eklendi: ozet.json biçimi: {"files": [{"name": "<yeni dosya adı>"}]}; ogrenciler dizinindeki bütün dosyalar listelensin. Çıktıyı çalışma dizininin kökünde (ozet.json) oluştur, alt dizine yazma.

## gen-s-0341-ozetle (altin_yanlis)

Referans bir karakter fazla kesiyordu: IST001 → '01'. Doğrusu '001'.
İsteme eklendi: Ölçüm satırından yalnız istasyon kodunun ilk üç harfi çıkarılsın, kalan her şey korunsun (ör. "Istanbul 001 20240101 12.5").
Önceki kontrol: `[{"op": "file_lines_eq", "path": "ozet.txt", "value": ["Istanbul 01 20240101 12.5", "Istanbul 02 20240101 13.0", "Istanbul 03 20240101 11.8", "Ankara 01 20240101 04.2", "Ankara 02 20240101 05.1", "Izmir 01 20240101 18.4", "Izmir 02 20240101 17.9"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "ozet.txt", "as_set": false, "value": ["Istanbul 001 20240101 12.5", "Istanbul 002 20240101 13.0", "Istanbul 003 20240101 11.8", "Ankara 001 20240101 04.2", "Ankara 002 20240101 05.1", "Izmir 001 20240101 18.4", "Izmir 002 20240101 17.9"]}]`

## gen-s-0365-ozetle (altin_yanlis)

Referans yılı yanlış sütundan okuyor; altında yıl yerine 'aaA 4' vardı.
İsteme eklendi: Her iki dosyada da her satır "<ad> <sayı>" biçiminde olsun (ör. "Kitap 6").
Önceki kontrol: `[{"op": "file_lines_eq", "path": "tur_sayilari.txt", "value": ["Dergi 4", "Kitap 6"]}, {"op": "file_lines_eq", "path": "yil_sayilari.txt", "value": ["aaA  4", "aaB  4", "aaC  2"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "tur_sayilari.txt", "value": ["Dergi 4", "Kitap 6"]}, {"op": "file_lines_eq", "path": "yil_sayilari.txt", "value": ["1998 3", "2001 3", "2005 2", "2010 2"]}]`

## gen-s-0564-donustur (gizli_sart)

Dosya adı ve arşiv kökü yazmıyordu; kontrol ./ önekine bağlıydı, gevşetildi.
İstem değişti: `sehir.tsv adlı dosyaya` → `<şehir adı>.tsv adlı dosyaya (ör. ankara/ankara.tsv)`
İsteme eklendi: Arşivin kökünde doğrudan şehir dizinleri olsun (cikti/ öneki olmasın).
Önceki kontrol: `[{"op": "dir_entries_eq", "path": "cikti", "value": ["ankara", "istanbul", "izmir"]}, {"op": "run_stdout_eq", "cmd": "tar -tzf hava.tar.gz | sort", "value": "./\n./ankara/\n./ankara/ankara.tsv\n./istanbul/\n./istanbul/istanbul.tsv\n./izmir/\n./izmir/izmir.tsv"}]`
Yeni kontrol: `[{"op": "dir_entries_eq", "path": "cikti", "value": ["ankara", "istanbul", "izmir"]}, {"op": "run_stdout_eq", "cmd": "tar -tzf hava.tar.gz | sed 's#^\\./##' | grep -v '^$' | sort", "value": "ankara/\nankara/ankara.tsv\nistanbul/\nistanbul/istanbul.tsv\nizmir/\nizmir/izmir.tsv"}]`

## gen-s-0566-bol (altin_yanlis)

Referans JSON'u cut ile ayrıştırıp hiçbir satır bulamıyor; altın '0' ve boş dosyaydı.
Önceki kontrol: `[{"op": "file_content_eq", "path": "bolum_sayisi.txt", "value": "0"}, {"op": "is_file", "path": "bolumler.txt"}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "bolumler.txt", "as_set": false, "value": ["Dermatoloji", "Kardiyoloji", "Noroloji"]}, {"op": "file_content_eq", "path": "bolum_sayisi.txt", "value": "3"}]`

## gen-s-0579-donustur (altin_yanlis)

Referans adet sütununu boş bırakıyordu ('K001,').
İsteme eklendi: İlk satır takip_no,adet başlığı olsun.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "cikti.csv", "value": ["takip_no,adet", "K001,", "K002,", "K003,", "K005,"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "cikti.csv", "value": ["takip_no,adet", "K001,12", "K002,5", "K003,7", "K005,3"]}, {"op": "run_stdout_eq", "cmd": "python3 -c 'print(open(\"cikti.csv\",\"rb\").read().count(bytes([13,10])))'", "value": "5"}]`

## gen-s-3008-donustur (altin_yanlis)

Altında başlık üç kez ve farklı ayırıcıyla vardı.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "birlesik_randevular.csv", "value": ["hasta_id;poliklinik;tarih", "101,Kardiyoloji,2024-03-01", "102,Noroloji,2024-03-01", "103,Kardiyoloji,2024-03-02", "hasta_id,poliklinik,tarih", "104,Ortopedi,2024-03-02", "105,Noroloji,2024-03-03", "106,Kardiyoloji,2024-03-03", "hasta_id,poliklinik,tarih", "107,Ortopedi,2024-03-04", "108,Kardiyoloji,2024-03-04"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "birlesik_randevular.csv", "value": ["hasta_id,poliklinik,tarih", "101,Kardiyoloji,2024-03-01", "102,Noroloji,2024-03-01", "103,Kardiyoloji,2024-03-02", "104,Ortopedi,2024-03-02", "105,Noroloji,2024-03-03", "106,Kardiyoloji,2024-03-03", "107,Ortopedi,2024-03-04", "108,Kardiyoloji,2024-03-04"]}]`

## gen-s-3009-arsivle (yol_belirsiz)

Arşivin ve temiz.txt'nin yeri, arşivde yalnız temiz.txt olacağı yazmıyordu.
İsteme eklendi: Arşivin içinde yalnız temiz.txt olsun. Çıktıyı çalışma dizininin kökünde (kitaplik.tar.gz ve temiz.txt) oluştur, alt dizine yazma.

## gen-s-3025-ayikla (gizli_sart)

JSON anahtarları istemde yoktu.
İsteme eklendi: JSON biçimi: {"<sensör adı>": {"ortalama_sicaklik": <sayı>, "ortalama_nem": <sayı>}}.

## gen-s-3048-donustur (altin_yanlis)

İstem tarih;tur;tutar diyor, altın tur;tutar;tarih idi.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "kalemler.csv", "value": ["alacak;1250.50;2024-01-05", "alacak;2000.00;2024-01-09", "alacak;999.99;2024-01-07", "borc;15.75;2024-01-08", "borc;430.00;2024-01-06"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "kalemler.csv", "as_set": false, "value": ["2024-01-05;alacak;1250.50", "2024-01-06;borc;430.00", "2024-01-07;alacak;999.99", "2024-01-08;borc;15.75", "2024-01-09;alacak;2000.00"]}]`

## gen-s-3065-donustur (gizli_sart)

JSON biçimi yazmıyordu.
İsteme eklendi: JSON biçimi: {"<kod>": {"ad": "<hesap adı>", "toplam": <sayı>}} (ör. {"100": {"ad": "Kasa", "toplam": 2100}}).

## gen-s-3080-ayikla (altin_yanlis)

İkinci dosyanın başlığından sahte kayıt (id 0) türemişti; ayrıca çıktı yeri yazmıyordu.
İstem değişti: `adet ile fiyat sayı olmalı` → `id, adet ve fiyat sayı olmalı`
İsteme eklendi: Çıktıyı çalışma dizininin kökünde (siparisler.json) oluştur, alt dizine yazma.
Önceki kontrol: `[{"op": "json_eq", "path": "siparisler.json", "value": [{"id": 1, "urun": "kebap", "adet": 2, "fiyat": 120}, {"id": 2, "urun": "ayran", "adet": 1, "fiyat": 25}, {"id": 0, "urun": "urun", "adet": 0, "fiyat": 0}, {"id": 3, "urun": "pide", "adet": 3, "fiyat": 90}, {"id": 4, "urun": "salata", "adet": 1, "fiyat": 45}]}]`
Yeni kontrol: `[{"op": "json_eq", "path": "siparisler.json", "value": [{"id": 1, "urun": "kebap", "adet": 2, "fiyat": 120}, {"id": 2, "urun": "ayran", "adet": 1, "fiyat": 25}, {"id": 3, "urun": "pide", "adet": 3, "fiyat": 90}, {"id": 4, "urun": "salata", "adet": 1, "fiyat": 45}]}]`

## gen-s-3081-sirala-sec (altin_yanlis)

İstem puanı istiyor, altın 'ayse' adıydı ve awk sürümüne bağlıydı. En yüksek puan zeynep 19.
Önceki kontrol: `[{"op": "file_content_eq", "path": "vardiya/sonuc.txt", "value": "ayse"}]`
Yeni kontrol: `[{"op": "file_content_eq", "path": "vardiya/sonuc.txt", "value": "19"}]`

## gen-s-3087-donustur (altin_yanlis)

Altında kod ters çevrilmemiş, sütunlar başlıkla uyuşmuyordu; ayrıca çıktı yeri yazmıyordu.
İsteme eklendi: Kod alanını karakter karakter ters çevir (K01 → 10K). Çıktıyı çalışma dizininin kökünde (envanter.csv) oluştur, alt dizine yazma.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "envanter.csv", "value": ["kod,urun,adet", "kalem,K01,12", "silgi,K02,7", "defter,K03,25", "defter,K03,5", "kalem,K01,3"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "envanter.csv", "value": ["kod,urun,adet", "10K,kalem,12", "20K,silgi,7", "30K,defter,25", "30K,defter,5", "10K,kalem,3"]}]`

## gen-s-3096-bol (gizli_sart)

İstemde silme yokken kaynak dosyaların silinmesi aranıyordu; kontrol kaldırıldı, sondaki newline kontrolü eklendi.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "muhasebe/birlesik.txt", "value": ["100 kasa acilis", "200 banka tahsilat", "300 gider kira", "400 gelir satis", "500 gider maas", "600 kasa kapanis", "700 borc devir"]}, {"op": "not_exists", "path": "muhasebe/kalemler_a.txt"}, {"op": "not_exists", "path": "muhasebe/kalemler_b.txt"}, {"op": "not_exists", "path": "muhasebe/kalemler_c.txt"}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "muhasebe/birlesik.txt", "as_set": false, "value": ["100 kasa acilis", "200 banka tahsilat", "300 gider kira", "400 gelir satis", "500 gider maas", "600 kasa kapanis", "700 borc devir"]}, {"op": "run_stdout_eq", "cmd": "python3 -c 'print(open(\"muhasebe/birlesik.txt\",\"rb\").read()[-1]==10)'", "value": "False"}]`

## gen-s-3117-karsilastir (altin_yanlis)

Altında iki sınıfta aynı olan satırlar da vardı; ayrıca çıktı yeri yazmıyordu.
İsteme eklendi: Çıktıyı çalışma dizininin kökünde (farklar.tsv) oluştur, alt dizine yazma.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "farklar.tsv", "value": ["sinif-a\tali\tmatematik\t85", "sinif-a\tayse\tmatematik\t90", "sinif-a\tcan\tfizik\t70", "sinif-a\tdeniz\tkimya\t88", "sinif-b\tali\tmatematik\t85", "sinif-b\tayse\tmatematik\t95", "sinif-b\tcan\tfizik\t70", "sinif-b\tece\tkimya\t60"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "farklar.tsv", "value": ["sinif-a\tayse\tmatematik\t90", "sinif-a\tdeniz\tkimya\t88", "sinif-b\tayse\tmatematik\t95", "sinif-b\tece\tkimya\t60"]}]`

## gen-s-3123-ayikla (altin_yanlis)

Altında kayıtlar paste ile yan yana yapışmıştı.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "iyi_yorumlar.txt", "value": ["Klarnet,4\tKeman,4", "Flut,5\tTrompet,3", "Bateri,3\tBateri,5"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "iyi_yorumlar.txt", "value": ["Flut\t5", "Klarnet\t4", "Trompet\t3", "Bateri\t5", "Keman\t4", "Bateri\t3"]}]`

## gen-s-3127-denetle (kararsiz)

Dosyalar satır sonuyla bitmediği için cat sırası kayıt yutuyordu; altında TRK004 eksikti. beklenen_kodlar.txt setup'ta yoktu; istemdeki dizin adları Türkçe harfle yazılıydı.
İstem değişti: `gönderiler` → `gonderiler`; `kayıt.txt` → `kayit.txt`
Önceki kontrol: `[{"op": "file_lines_eq", "path": "ortak_kodlar.txt", "value": ["TRK002", "TRK006"]}, {"op": "file_lines_eq", "path": "teslim_kodlari.txt", "value": ["TRK002", "TRK006", "TRK008"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "ortak_kodlar.txt", "value": ["TRK002", "TRK004", "TRK006"]}, {"op": "file_lines_eq", "path": "teslim_kodlari.txt", "as_set": false, "value": ["TRK002", "TRK004", "TRK006", "TRK008"]}]`

## gen-s-3129-onar (altin_yanlis)

Altında satır sonları kaybolmuştu; hiçbir satır bozuk olmadığı için çıktı girdinin aynısı.
Önceki kontrol: `[{"op": "file_content_eq", "path": "kayitlar_duzeltilmis.txt", "value": "2024-01-01 12:00 sicaklik=21.5 nem=452024-01-01 13:00 sicaklik=22.1 nem=442024-01-01 14:00 sicaklik=23.0 nem=432024-01-01 15:00 sicaklik=23.4 nem=422024-01-01 16:00 sicaklik=22.8 nem=442024-01-01 17:00 sicaklik=21.9 nem=462024-01-01 18:00 sicaklik=20.5 nem=48"}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "kayitlar_duzeltilmis.txt", "as_set": false, "value": ["2024-01-01 12:00 sicaklik=21.5 nem=45", "2024-01-01 13:00 sicaklik=22.1 nem=44", "2024-01-01 14:00 sicaklik=23.0 nem=43", "2024-01-01 15:00 sicaklik=23.4 nem=42", "2024-01-01 16:00 sicaklik=22.8 nem=44", "2024-01-01 17:00 sicaklik=21.9 nem=46", "2024-01-01 18:00 sicaklik=20.5 nem=48"]}]`

## gen-s-3181-ayikla (altin_yanlis)

Altında notu 50'nin altındaki mehmet:42 vardı.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "gecen.txt", "value": ["zeynep:91", "ayse:85", "elif:73", "can:58", "mehmet:42"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "gecen.txt", "as_set": false, "value": ["zeynep:91", "ayse:85", "elif:73", "can:58"]}]`

## gen-s-3190-ayikla (altin_yanlis)

Referans INI'yi satır satır okuyamıyor; altın boş {} idi.
İsteme eklendi: JSON nesnesinde anahtar şehir adı, değer toplam adet olsun (ör. {"Ankara": 3}).
Önceki kontrol: `[{"op": "json_eq", "path": "sonuc.json", "value": {}}]`
Yeni kontrol: `[{"op": "json_eq", "path": "sonuc.json", "value": {"Ankara": 3, "Izmir": 1, "Bursa": 5}}]`

## gen-s-3235-bol (gizli_sart)

JSON anahtarları istemde yoktu.
İsteme eklendi: JSON biçimi: {"<vardiya>": {"toplam_saat": <sayı>, "personel": ["<ad>"]}}.

## gen-s-4029-denetle (altin_yanlis)

Altında günü 30'u geçmeyen zeynep vardı.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "gecikmis.txt", "value": ["ali", "ayse", "mehmet", "zeynep"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "gecikmis.txt", "as_set": false, "value": ["ali", "ayse", "mehmet"]}]`

## gen-s-4084-ayikla (gizli_sart)

İstem 'geçen' diyor, altın kesişim; ayrıca çıktı yeri yazmıyordu.
İstem değişti: `a.tsv ve b.tsv dosyalarında geçen` → `a.tsv ve b.tsv dosyalarının ikisinde de geçen`
İsteme eklendi: Çıktıyı çalışma dizininin kökünde (ortak.txt) oluştur, alt dizine yazma.

## gen-s-4134-bol (yol_belirsiz)

Çıktının yeri yazmıyordu.
İsteme eklendi: Çıktıyı çalışma dizininin kökünde (kalem-ozet.csv ve en-cok.csv) oluştur, alt dizine yazma.

## gen-s-4141-donustur (altin_yanlis)

Altın hedefte olmayan Bursa'yı da saymıştı (14); doğrusu 10.
Önceki kontrol: `[{"op": "file_content_eq", "path": "kutuphane/toplam.txt", "value": "14"}]`
Yeni kontrol: `[{"op": "file_content_eq", "path": "kutuphane/toplam.txt", "value": "10"}]`

## gen-s-7045-denetle (gizli_sart)

A3 iki ölçümde de var ama beklenen listede yok; süzme açık yazılmamıştı.
İsteme eklendi: Yalnız beklenen_sensorler.txt içinde de bulunan kodlar yazılsın.

## gen-s-7059-grupla-say (gizli_sart)

Ayırıcı yazmıyordu.
İsteme eklendi: Alanlar sekmeyle ayrılsın.

## gen-s-7080-grupla-say (gizli_sart)

Altında istemde olmayan toplam_satir anahtarı vardı; kaldırıldı.
Önceki kontrol: `[{"op": "json_eq", "path": "cikti.json", "value": {"kirmizi": 10, "mavi": 11, "sari": 9, "yesil": 9, "toplam_satir": 9}}]`
Yeni kontrol: `[{"op": "json_eq", "path": "cikti.json", "value": {"kirmizi": 10, "mavi": 11, "sari": 9, "yesil": 9}}]`

## gen-s-7100-denetle (gizli_sart)

JSON yapısı istemde yoktu.
İsteme eklendi: JSON biçimi: [{"sehir": "<şehir>", "toplam_olay": <sayı>, "kayit_sayisi": <sayı>}].

## gen-s-7105-yeniden-duzenle (altin_yanlis)

İstem 'kod, ad, stok' istiyor, altında ad yoktu; 'iki dosyada da yoksa dışarıda kalsın' cümlesi istenen A100 ve A400 ile çelişiyordu.
İstem değişti: `Bir kod iki dosyada da yoksa o ürün dışarıda kalsın; boş` → `Boş`
İsteme eklendi: Dosya içeriği "<kod> <ad> <stok>" biçiminde tek satır olsun (ör. "A100 Kalem 40").
Önceki kontrol: `[{"op": "dir_entries_eq", "path": "stok", "value": ["A100.txt", "A200.txt", "A300.txt", "A400.txt"]}, {"op": "file_content_eq", "path": "stok/A100.txt", "value": "A100 40"}, {"op": "file_content_eq", "path": "stok/A200.txt", "value": "A200 40"}, {"op": "file_content_eq", "path": "stok/A300.txt", "value": "A300 10"}, {"op": "file_content_eq", "path": "stok/A400.txt", "value": "A400 12"}]`
Yeni kontrol: `[{"op": "dir_entries_eq", "path": "stok", "value": ["A100.txt", "A200.txt", "A300.txt", "A400.txt"]}, {"op": "file_content_eq", "path": "stok/A100.txt", "value": "A100 Kalem 40"}, {"op": "file_content_eq", "path": "stok/A200.txt", "value": "A200 Defter 40"}, {"op": "file_content_eq", "path": "stok/A300.txt", "value": "A300 Silgi 10"}, {"op": "file_content_eq", "path": "stok/A400.txt", "value": "A400 Cetvel 12"}]`

## gen-s-7222-ayikla (gizli_sart)

karsilastirma.tsv biçimi istemde yok (altın paste çıktısı); yalnız varlığı denetlenir, diğer iki kontrol aynen.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "bekliyor.tsv", "value": ["kalem\ttutar\tdurum", "kalem03\t30\tbekliyor", "kalem06\t60\tbekliyor", "kalem09\t90\tbekliyor", "kalem12\t120\tbekliyor", "kalem15\t150\tbekliyor", "kalem18\t180\tbekliyor", "kalem21\t210\tbekliyor", "kalem24\t240\tbekliyor", "kalem27\t270\tbekliyor", "elektrik\t300\tbekliyor", "kalem30\t300\tbekliyor", "kalem33\t330\tbekliyor", "kalem36\t360\tbekliyor", "kalem39\t390\tbekliyor", "dogalgaz\t450\tbekliyor"]}, {"op": "file_lines_eq", "path": "karsilastirma.tsv", "value": ["kalem\ttutar\tkalem\ttutar\tdurum", "kalem01\t10\tkalem03\t30\t`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "bekliyor.tsv", "value": ["kalem\ttutar\tdurum", "kalem03\t30\tbekliyor", "kalem06\t60\tbekliyor", "kalem09\t90\tbekliyor", "kalem12\t120\tbekliyor", "kalem15\t150\tbekliyor", "kalem18\t180\tbekliyor", "kalem21\t210\tbekliyor", "kalem24\t240\tbekliyor", "kalem27\t270\tbekliyor", "elektrik\t300\tbekliyor", "kalem30\t300\tbekliyor", "kalem33\t330\tbekliyor", "kalem36\t360\tbekliyor", "kalem39\t390\tbekliyor", "dogalgaz\t450\tbekliyor"]}, {"op": "is_file", "path": "karsilastirma.tsv"}, {"op": "file_lines_eq", "path": "odendi.tsv", "value": ["kalem\ttutar\tdurum", `

## gen-s-7255-donustur (yol_belirsiz)

Çıktının yeri yazmıyordu.
İsteme eklendi: Çıktıyı çalışma dizininin kökünde (randevular.tar.gz ve sonuc.txt) oluştur, alt dizine yazma.

## gen-s-7291-ozetle (gizli_sart)

JSON anahtarları istemde yoktu.
İsteme eklendi: JSON biçimi: {"toplam": <toplam tutar>, "adet": <satır sayısı>}.

## gen-s-7295-ayikla (altin_yanlis)

İstem başlık hariç diyor, altında başlık vardı.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "ayikla.csv", "value": ["gun,vardiya", "Pazartesi,gunduz", "Pazartesi,gece", "Sali,gunduz", "Sali,gece", "Carsamba,gunduz"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "ayikla.csv", "value": ["Pazartesi,gunduz", "Pazartesi,gece", "Sali,gunduz", "Sali,gece", "Carsamba,gunduz"]}]`

## gen-s-7318-grupla-say (altin_yanlis)

İstem sensör başına değer sayısı istiyor (3, 2, 1); altın yalnız sensör sayısıydı.
Önceki kontrol: `[{"op": "file_content_eq", "path": "sonuc.txt", "value": "3"}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "sonuc.txt", "value": ["3", "2", "1"]}]`

## gen-s-7321-ozetle (altin_yanlis)

Altın anlamsızdı ('1200,0'); 'tür ve tutar çifti' ifadesi tur,toplam biçimiyle çelişiyordu.
İstem değişti: `her tür ve tutar çifti için` → `her tür için`
İsteme eklendi: İlk satır tur,toplam başlığı olsun.
Önceki kontrol: `[{"op": "file_lines_eq", "path": "ozet.csv", "value": ["tur,toplam", "1200,0", "3000,0", "5000,0", "700,0"]}]`
Yeni kontrol: `[{"op": "file_lines_eq", "path": "ozet.csv", "as_set": false, "value": ["tur,toplam", "GELIR,32000", "GIDER,7400"]}]`
