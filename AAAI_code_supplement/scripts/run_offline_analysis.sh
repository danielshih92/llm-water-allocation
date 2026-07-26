#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA="$ROOT/data/paper_intermediates"
OUTPUT="$ROOT/outputs"

export PYTHONPATH="$ROOT:$ROOT/wacbench:$ROOT/analysis:$ROOT/judge_support"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/wacbench-matplotlib}"
export PYTHONDONTWRITEBYTECODE=1

mkdir -p "$OUTPUT/main_table"
cp "$DATA/main_table/replay_details.csv" "$OUTPUT/main_table/replay_details.csv"
python3 "$ROOT/analysis/replay_main_table.py" \
  --output-dir "$OUTPUT/main_table" \
  --meta-rounds 1 2 3 \
  --table-meta-rounds 2 3 \
  --resume \
  --trusted-fast-replay

python3 "$ROOT/analysis/adaptation_dynamics.py" \
  --replay-details "$OUTPUT/main_table/replay_details.csv"
python3 "$ROOT/analysis/objective_outcomes.py" \
  --replay-details "$OUTPUT/main_table/replay_details.csv"
python3 "$ROOT/analysis/policy_convergence.py"

python3 "$ROOT/analysis/summarize_reference_replacements.py"
python3 "$ROOT/analysis/plot_reference_results.py"
python3 "$ROOT/analysis/summarize_fosg.py" \
  --input "$DATA/opponent_modeling/frozen_opponent_pairs.csv"

python3 "$ROOT/analysis/delayed_scarcity.py"
python3 "$ROOT/analysis/counterfactual_planning.py"
python3 "$ROOT/analysis/risk_sensitivity.py" \
  --batch "$DATA/logs/OF" \
  --batch "$DATA/logs/OPF"

python3 "$ROOT/failure_analysis/plot_failure_analysis.py" \
  --input-dir "$DATA/failure_analysis" \
  --output-dir "$OUTPUT/failure_analysis"
python3 "$ROOT/analysis/plot_homogeneous_summary.py"

echo "Offline paper analyses were written under $OUTPUT"
