One-click run and export

This guide shows how to run meta-rounds and export res/ outputs with a single script.

Prerequisites
- You are in the Alympics/ folder.
- Python dependencies are installed (matplotlib is needed for plots).

Script location
- scripts/run_and_export.sh

## Batch run (permutations)
1) Run a slice of permutations:
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120

2) Select opponent info mode:
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120 --opponent-info-mode outcome_only

Quick start (single run)
1) Make the script executable:
   chmod +x scripts/run_and_export.sh

2) Run with defaults:
   ./scripts/run_and_export.sh

Default values (run_and_export.sh)
- SCENARIO=low
- META_ROUNDS=3
- BACKEND=mock
- SEED=42
- EXPERIMENT_ID=exp1
- OPPONENT_INFO_MODE=full_code_access

Available options (run_and_export.sh)
- SCENARIO: low, medium, high
- BACKEND: mock, openai
- OPPONENT_INFO_MODE: full_code_access, outcome_only, no_opponent_info

Customize via environment variables (run_and_export.sh)
- Example:
   SCENARIO=low META_ROUNDS=10 BACKEND=openai SEED=42 EXPERIMENT_ID=exp1 OPPONENT_INFO_MODE=outcome_only ./scripts/run_and_export.sh

What it does (run_and_export.sh)
1) Runs meta-rounds and writes a log JSON in log/.
2) Finds the newest log for the chosen experiment id.
3) Exports res/{experiment_id}/inference and res/{experiment_id}/plots.

Output locations (run_and_export.sh)
- Log JSON: log/meta_round_YYYYmmdd_HHMM_<EXPERIMENT_ID>.json
- Res outputs: res/<EXPERIMENT_ID>/inference and res/<EXPERIMENT_ID>/plots

Notes
- For batch runs, BACKEND in this file does not apply. Batch uses per-agent model specs in run_all_permutations.py.
- If you use BACKEND=openai, set OPENAI_API_KEY in your environment.
- If no log is found for the experiment id, the script exits with an error.
- OPPONENT_INFO_MODE only affects the LLM prompt context between meta-rounds.
- For batch runs, use --opponent-info-mode in run_all_permutations.py to override config defaults.

Batch run notes
- Batch uses per-agent backends/models defined in [Alympics/src/run_all_permutations.py](Alympics/src/run_all_permutations.py).
- Supported backends in batch depend on the entries in the MODELS list (openai, gemini, deepseek).
