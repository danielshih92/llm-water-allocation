One-click run and export

This guide shows how to run a single experiment or batch permutations.

Prerequisites
- You are in the Alympics/ folder.
- Python dependencies are installed (matplotlib is needed for plots).

Script location
- scripts/run_and_export.sh

Quick start (single run)
1) Make the script executable:
   chmod +x scripts/run_and_export.sh

2) Run with defaults:
   ./scripts/run_and_export.sh

Single experiment (run.py)
1) Per-agent mode (configured in config.py):
   python3 src/run.py --scenario medium --meta-rounds 10 --backend-mode per-agent

2) Uniform mode (override in CLI):
   python3 src/run.py --scenario medium --meta-rounds 10 --backend-mode uniform --backend openai --backend-model gpt-5.4

Batch run (permutations)
1) Run a slice of permutations:
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120

2) Select opponent info mode:
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120 --opponent-info-mode full_code_access

3) Run multiple slices into the same batch folder:
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120 --no-plots --batch-name batch_004 --opponent-info-mode full_code_access
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120 --no-plots --batch-name batch_006_outcome_only --meta-rounds 3 --opponent-info-mode outcome_only

Config-only settings
- All backend/model settings are defined in [Alympics/src/config.py](Alympics/src/config.py).
- For single runs (per-agent), edit AGENT_BACKENDS.
- For batch permutations, edit BATCH_MODELS and AGENTS.

Key flags (run.py)
- --scenario: low, medium, high
- --meta-rounds: number of meta-rounds
- --seed: base random seed (optional)
- --backend-mode: uniform | per-agent
- --backend: mock | openai | gemini | ollama | deepseek (uniform only)
- --backend-model, --backend-temperature, --backend-base-url (uniform only)
- --output-dir: log
- --experiment-id: custom name
- --opponent-info-mode: full_code_access | outcome_only | no_opponent_info
- --no-plots, --compact-meta-log

Key flags (run_all_permutations.py)
- --slice-start, --slice-end: permutation slice range
- --meta-rounds: number of meta-rounds per experiment
- --no-plots: skip plots
- --opponent-info-mode: full_code_access | outcome_only | no_opponent_info
- --batch-name: reuse a specific batch folder name

What scripts output
- Single runs: log/<experiment_id>/meta_round_*.json, backend_config.json, agent_averages.json, daily_metric_plots/
- Batch runs: log/batch_<timestamp>/exp_###/ (each exp contains the same outputs)

Notes
- If you use OpenAI or DeepSeek, set OPENAI_API_KEY or DEEPSEEK_API_KEY in your environment.
- OPPONENT_INFO_MODE only affects the LLM prompt context between meta-rounds.
- When using --batch-name, exp numbering follows slice indices (e.g., slice 20-40 -> exp_020 to exp_040).

---
tmux bash:
tmux new -s alympics
source venv/bin/activate
python ...

---
python temp/batch_table_plot.py --log-dir log --batch batch_005_no_opp_info