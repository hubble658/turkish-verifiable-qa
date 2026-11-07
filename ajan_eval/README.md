# Ajan terminal görevleri: çalıştırma

`veri/ajan_terminal.jsonl.gz` içindeki 1.590 görev (kabuk 884, kod 706) burada çalışır. Model tek metin yazmaz: Türkçe görevi alır,
kum havuzunda komut çalıştırır, bitince çalışma dizini `checks` kurallarıyla denetlenir. Bütün kontroller geçerse 1, değilse 0.
Bu yüzden `puanlama.puanla()` bu sette çalışmaz, Batch API de kullanılamaz.

Satır alanları: `soru` görev istemi, `cevap` örnek çözüm betiği, `orijinal` içinde `setup`, `checks`, `max_turns`, `gorev`, `set`, `bolum`, `duzeltme`.

## Çalıştırma

Gerekenler: `pip install -r requirements.txt`, Linux'ta `bwrap` (bubblewrap) ya da Docker.

```bash
# Referans çözümler (model yok, ücretsiz)
python3 -m verifiable_dataset.terminal.sweep --split test --reference --sandbox bwrap --paralel 5

# Model ölçümü; anahtarı ortam değişkeniyle verin
export OPENAI_API_KEY=...
python3 -m verifiable_dataset.terminal.sweep --split test --model <model> --base-url <openai-uyumlu-url> \
    --protocol native --sandbox bwrap --sicaklik 0 --max-tokens 8000 --paralel 5 --out sonuc.jsonl
```

Metin protokolü gerekiyorsa (araç çağrısı olmayan modeller) `--protocol text`. Harcama sınırı için `--butce <USD>`.

**Değerlendirme protokolü (7 Kasım 2026; ana README → "Değerlendirme protokolü"):** test bölümündeki 200 görev, model başına tek deneme. Düşünen modellerde tur başına `--max-tokens 32000`; `Qwen/Qwen3.5-9B` düşünen `--sicaklik 0.6 --top-p 0.95`, düşünmesiz taban `--reasoning-effort none --sicaklik 0 --max-tokens 16000`; `google/gemma-4-31B-it` ve `openai/gpt-oss-120b` `--reasoning-effort high --sicaklik 0`; Cosmos `--protocol text --sicaklik 0`. Puan bitişteki `checks` (ikili), LLM hakem yok; başarı oranı metin setlerinin ortalamasından ayrı raporlanır. Referans çözümler bu makinede 200/200 geçti (7 Kasım, `bwrap`).

## Bilinen durum

- Bölme `data/split.json`'da: train 1.390 (kabuk 784, kod 606), test 200 (kabuk 100, kod 100). Kaynak bölme kabuk 110 / kod 90 idi; hangi görevlerin yer değiştirdiği dosyadaki `dengeleme` alanında.
- Teste yeni giren 10 kod görevi modelle denenmedi.
- Test 200'de 65 görev düzeltildi; önceki ve sonraki hâl `duzeltme_raporu.md` dosyasında, her satırda da `orijinal.duzeltme` alanında. Bu düzeltmelerin bir kısmı (istemde yazmayan şartlar, çıktı yolu) tartışmalıdır ve gözden geçirilecektir.
- Train 1.390 görev modelle denetlenmedi. Yanlış altın içerebilir, çünkü kontroller örnek çözümün çıktısından türetilmiştir.
- Bwrap kum havuzu host araçlarını kullanır; asıl imaj dosyası yoktur. Araç sürümüne bağlı küçük farklar olabilir.
