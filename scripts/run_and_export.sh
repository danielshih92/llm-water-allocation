#!/usr/bin/env bash
set -e

SCENARIO=${SCENARIO:-low}
META_ROUNDS=${META_ROUNDS:-3}
BACKEND=${BACKEND:-mock}
SEED=${SEED:-42}
EXPERIMENT_ID=${EXPERIMENT_ID:-exp1}

python src/run.py \
  --scenario "$SCENARIO" \
  --meta-rounds "$META_ROUNDS" \
  --backend "$BACKEND" \
  --seed "$SEED" \
  --experiment-id "$EXPERIMENT_ID"

LOG_DIR="log/$EXPERIMENT_ID"
if [[ ! -d "$LOG_DIR" ]]; then
  echo "No log directory found for experiment id: $EXPERIMENT_ID" >&2
  exit 1
fi
if ! ls "$LOG_DIR"/*.json >/dev/null 2>&1; then
  echo "No log files found for experiment id: $EXPERIMENT_ID" >&2
  exit 1
fi

python src/visualize_log.py \
  --log-dir "$LOG_DIR" \
  --mode res \
  --experiment-id "$EXPERIMENT_ID"

echo "Done. res outputs in: res/$EXPERIMENT_ID"
