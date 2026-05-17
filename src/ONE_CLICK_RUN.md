One-click run and export

This guide shows how to run meta-rounds and export res/ outputs with a single script.

Prerequisites
- You are in the Alympics/ folder.
- Python dependencies are installed (matplotlib is needed for plots).

Script location
- scripts/run_and_export.sh

Quick start
1) Make the script executable:
   chmod +x scripts/run_and_export.sh

2) Run with defaults:
   ./scripts/run_and_export.sh

Default values
- SCENARIO=low
- META_ROUNDS=3
- BACKEND=mock
- SEED=42
- EXPERIMENT_ID=exp1

Available options
- SCENARIO: low, medium, high
- BACKEND: mock, openai

Customize via environment variables
- Example:
  SCENARIO=low META_ROUNDS=10 BACKEND=openai SEED=42 EXPERIMENT_ID=exp1 ./scripts/run_and_export.sh

What it does
1) Runs meta-rounds and writes a log JSON in log/.
2) Finds the newest log for the chosen experiment id.
3) Exports res/{experiment_id}/inference and res/{experiment_id}/plots.

Output locations
- Log JSON: log/meta_round_YYYYmmdd_HHMM_<EXPERIMENT_ID>.json
- Res outputs: res/<EXPERIMENT_ID>/inference and res/<EXPERIMENT_ID>/plots

Notes
- If you use BACKEND=openai, set OPENAI_API_KEY in your environment.
- If no log is found for the experiment id, the script exits with an error.
