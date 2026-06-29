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
   python3 src/run.py --scenario low --meta-rounds 10 --backend-mode uniform --backend gemini --backend-model gemini-3.5-flash

Batch run (permutations)
1) Run a slice of permutations:
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120

2) Select opponent info mode:
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120 --opponent-info-mode full_code_access

3) Run multiple slices into the same batch folder:
   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120 --no-plots --batch-name batch_004 --opponent-info-mode full_code_access

   python3 src/run_all_permutations.py --slice-start 1 --slice-end 3 --no-plots --batch-name batch_016_full_code_access_med --meta-rounds 3 --opponent-info-mode full_code_access --seed 42 --scenario medium

   python3 src/run_all_permutations.py --slice-start 1 --slice-end 3 --no-plots --batch-name batch_015_no_opp_info_med --meta-rounds 2 --opponent-info-mode full_code_access --seed 42 --scenario medium

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
- --opponent-info-mode: full_code_access | no_opponent_info
- --no-plots, --compact-meta-log

Key flags (run_all_permutations.py)
- --slice-start, --slice-end: permutation slice range
- --meta-rounds: number of meta-rounds per experiment
- --seed: base random seed (optional, default None)
- --no-plots: skip plots
- --opponent-info-mode: full_code_access | no_opponent_info
- --batch-name: reuse a specific batch folder name

What scripts output
- Single runs: log/<experiment_id>/meta_round_*.json, backend_config.json, agent_averages.json, daily_metric_plots/
- Batch runs: log/batch_<timestamp>/exp_###/ (each exp contains the same outputs)

Notes
- If you use OpenAI or DeepSeek, set OPENAI_API_KEY or DEEPSEEK_API_KEY in your environment.
- OPPONENT_INFO_MODE only affects the LLM prompt context between meta-rounds.
- When using --batch-name, exp numbering follows slice indices (e.g., slice 20-40 -> exp_020 to exp_040).

---(common Command)
tmux bash:
tmux new -s alympics
tmux new -s alympics_v2
tmux ls
tmux attach -t alympics
source venv/bin/activate

---
python temp/batch_table_plot.py --log-dir log --batch test_all_the_same_prompt_fixed_v2_water_demand_high --meta-first-round false
python temp/exp_plot.py --log-dir log --batch batch_016_full_code_access_med --exp exp_001


---
batch_009之後的實驗所使用的code是有被大力refactor過的
batch_012有被refactor第二次
batch_014refactor第三次