#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SMOKE_TMP="$(mktemp -d /tmp/wacbench-smoke.XXXXXX)"
trap 'rm -rf "$SMOKE_TMP"' EXIT

export PYTHONPATH="$ROOT:$ROOT/wacbench:$ROOT/analysis:$ROOT/judge_support"
export MPLCONFIGDIR="$SMOKE_TMP/matplotlib"
export PYTHONDONTWRITEBYTECODE=1

python3 -m unittest discover -s "$ROOT/tests" -p "test*.py" -v
python3 -m unittest discover -s "$ROOT/tests/judge" -p "test*.py" -v
python3 -m unittest discover -s "$ROOT/tests/failure" -p "test*.py" -v

python3 "$ROOT/analysis/non_llm_reference.py" --self-test
python3 "$ROOT/analysis/frozen_opponents.py" --self-test
python3 "$ROOT/analysis/frozen_opponents.py" --parity-check --parity-max-experiments 1
python3 "$ROOT/analysis/delayed_scarcity.py" --self-test
python3 "$ROOT/analysis/counterfactual_planning.py" --self-test
python3 "$ROOT/analysis/risk_sensitivity.py" --self-test

python3 "$ROOT/scripts/check_anonymity.py" --root "$ROOT"
echo "Smoke suite passed."
