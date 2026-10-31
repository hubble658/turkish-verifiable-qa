#!/usr/bin/env bash
# TURSpider veritabanlarini asil kaynaktan indirir: github.com/alibugra/TURSpider (CC BY-SA 4.0).
# Depoya konmadi: futbol_1.sqlite 317 MB, GitHub'in dosya sinirini asiyor. Sabit commit: paketteki
# sql_turspider altin sonuclari bu commit'in veritabanlariyla hesaplandi (166 dosya, md5 ile dogrulandi).
# Kullanım: bash araclar/turspider_indir.sh     -> veritabanlari/turspider/<db_id>/<db_id>.sqlite
set -euo pipefail
COMMIT=49bb962d60bac1718e33113fb8ca4a7824e53bb2
HEDEF="$(cd "$(dirname "$0")/.." && pwd)/veritabanlari/turspider"
GECICI="$(mktemp -d)"
trap 'rm -rf "$GECICI"' EXIT
mkdir -p "$HEDEF"
for parca in database_part1.zip database_part2.zip; do
  curl -fL --retry 3 -o "$GECICI/$parca" "https://github.com/alibugra/TURSpider/raw/$COMMIT/database/$parca"
  unzip -q -o "$GECICI/$parca" -d "$HEDEF"
done
echo "$(find "$HEDEF" -name '*.sqlite' | wc -l) veritabani -> $HEDEF (beklenen 166)"
