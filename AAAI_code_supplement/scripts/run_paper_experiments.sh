#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_ROOT="${1:-$ROOT/generated_outputs}"

export PYTHONPATH="$ROOT"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/wacbench-matplotlib}"
export PYTHONDONTWRITEBYTECODE=1

python3 -m wacbench.run_batch \
  --config "$ROOT/configs/paper.json" \
  --condition OF \
  --output-dir "$OUTPUT_ROOT" \
  --batch-name paper_OF \
  --no-plots

python3 -m wacbench.run_batch \
  --config "$ROOT/configs/paper.json" \
  --condition OPF \
  --output-dir "$OUTPUT_ROOT" \
  --batch-name paper_OPF \
  --no-plots
