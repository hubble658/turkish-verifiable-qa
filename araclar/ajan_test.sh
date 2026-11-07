#!/usr/bin/env bash
# Ajan terminal testi (test bolumu, 200 gorev), model basina ayri kosu. Batch olamaz: gorevler kum havuzunda cok turlu calisir.
# Ayarlar degerlendirme protokolunu izler (README -> "Degerlendirme protokolu"): dusunen modellerde tur basina 32.000 token,
# Qwen dusunen temperature 0,6 / top_p 0,95, digerleri temperature 0. Puan: bitiste checks (ikili), LLM hakem yok.
# Gerekenler: pip install -r ajan_eval/requirements.txt, Linux'ta bwrap (bubblewrap).
# Kullanim (depo kokunden):
#   ONAY=1 DEEPINFRA_API_KEY=... bash araclar/ajan_test.sh <qwen|qwen_dusunmesiz|gemma|oss> <cikti_klasoru>
#   ONAY=1 COSMOS_URL=http://localhost:8000/v1 bash araclar/ajan_test.sh cosmos <cikti_klasoru>
#   ORNEK=10: aile oranini koruyan 10 gorevlik pilot; BUTCE=<USD>: harcama siniri (varsayilan 10); PY: python yorumlayicisi
set -euo pipefail
[ "${ONAY:-}" = "1" ] || { echo "Bu betik para harcar: ONAY=1 olmadan calismaz."; exit 1; }
MODEL="${1:?model adi gerekli}"
CIKTI="$(mkdir -p "${2:?cikti klasoru gerekli}" && cd "$2" && pwd)"
PY="${PY:-python3}"
cd "$(dirname "$0")/../ajan_eval"
DI=https://api.deepinfra.com/v1/openai
ORTAK=(--split test --sandbox bwrap --paralel 5 --butce "${BUTCE:-10}")
EK=()
SON=""
if [ -n "${ORNEK:-}" ]; then EK=(--ornek "$ORNEK"); SON="_pilot"; fi
kos() { # ad model url protokol ek...
  local ad=$1 model=$2 url=$3 protokol=$4; shift 4
  PYTHONPATH=. "$PY" -m verifiable_dataset.terminal.sweep --model "$model" --base-url "$url" --protocol "$protokol" \
    "${ORTAK[@]}" "${EK[@]}" "$@" --out "$CIKTI/ajan_${ad}${SON}.jsonl"
}
export OPENAI_API_KEY="${DEEPINFRA_API_KEY:-yerel}"
case "$MODEL" in
  qwen)            kos qwen Qwen/Qwen3.5-9B "$DI" native --sicaklik 0.6 --top-p 0.95 --max-tokens 32000 ;;
  qwen_dusunmesiz) kos qwen_dusunmesiz Qwen/Qwen3.5-9B "$DI" native --reasoning-effort none --sicaklik 0 --max-tokens 16000 ;;
  gemma)           kos gemma google/gemma-4-31B-it "$DI" native --reasoning-effort high --sicaklik 0 --max-tokens 32000 ;;
  oss)             kos oss openai/gpt-oss-120b "$DI" native --reasoning-effort high --sicaklik 0 --max-tokens 32000 ;;
  cosmos)          kos cosmos ytu-ce-cosmos/Turkish-Gemma-9b-v0.1 "${COSMOS_URL:?}" text --sicaklik 0 --max-tokens 2048 ;;
  *) echo "bilinmeyen model: $MODEL"; exit 1 ;;
esac
