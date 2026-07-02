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
   python3 src/run_all_permutations.py --slice-start 13 --slice-end 13 --no-plots --batch-name batch_028_full_code_access_med_20days --meta-rounds 3 --episode-days 20 --opponent-info-mode full_code_access --seed 42 --scenario medium

   python3 src/run_all_permutations.py --slice-start 1 --slice-end 120 --no-plots --batch-name batch_029_no_opp_info_med_20days --meta-rounds 3 --episode-days 20 --opponent-info-mode no_opponent_info --seed 42 --scenario medium

   python3 src/run_all_permutations.py --slice-start 1 --slice-end 10 --no-plots --batch-name batch_027_full_code_access_gemini-2-5_seed42 --meta-rounds 3 --episode-days 20 --opponent-info-mode full_code_access --seed 42 --scenario medium

Config-only settings
- All backend/model settings are defined in [Alympics/src/config.py](Alympics/src/config.py).
- For single runs (per-agent), edit AGENT_BACKENDS.
- For batch permutations, edit BATCH_MODELS and AGENTS.

Key flags (run.py)
- --scenario: low, medium, high
- --meta-rounds: number of meta-rounds
- --episode-days: number of simulation days per meta-round
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
- --episode-days: number of simulation days per meta-round
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
tmux new -s alympics_v3
tmux ls
tmux attach -t alympics
tmux attach -t alympics_v2
tmux attach -t alympics_v3
tmux display-message -p '#S'

source venv/bin/activate

---(Main table)
python temp/batch_table_plot.py --log-dir log --batch batch_028_full_code_access_med_20days --meta-first-round false
python temp/batch_table_plot.py --log-dir log --batch batch_029_no_opp_info_med_20days --meta-first-round false

python temp/exp_plot.py --log-dir log --batch batch_017_full_code_access_med_20days --exp exp_001


---
batch_009之後的實驗所使用的code是有被大力refactor過的
batch_012有被refactor第二次
batch_014refactor第三次
current used batch *019 020* 022 023 025 026 027

--- (same model compare)
python temp/compare_batch.py \
  --log-dir log \
  --batch-a batch_021_full_code_access_med_20days_deepseek-pro \
  --batch-b batch_022_full_code_access_med_20days_deepseek-flash \
  --output-prefix batch_021vs022

--- (meta round compare)
python3 temp/meta_round_trend.py \
  --batch batch_023_full_code_access_gpt-nano_seed42 \
  --present-name "GPT-5.4 nano" \
  --batch batch_022_full_code_access_deepseek-flash_seed42 \
  --present-name "DeepSeek-V4-flash" \
  --batch batch_025_full_code_access_gpt-5-4_seed42 \
  --present-name "GPT-5.4" \
  --batch batch_026_full_code_access_gemini-3-5_seed42 \
  --present-name "Gemini-3.5" \
  --batch batch_027_full_code_access_gemini-2-5_seed42 \
  --present-name "Gemini-2.5" \
  --output-prefix five_model_test