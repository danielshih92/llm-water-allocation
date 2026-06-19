

# Whether to reveal opponent strategy code to the LLM
REVEAL_OPPONENT_CODE = True

# Opponent info exposure across meta-rounds:
# full_code_access | outcome_only | no_opponent_info
OPPONENT_INFO_MODE = "full_code_access"

OPENAI_ENGINE = "gpt-5.4"
OPENAI_TEMPERATURE = None
OPENAI_SLEEP_TIME = 10
OPENAI_API_TYPE = "openai"
OPENAI_API_BASE = ""
OPENAI_API_VERSION = ""

# Gemini placeholder config (for future use)
GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-3.5-flash"

# DeepSeek JSON output mode
DEEPSEEK_JSON_MODE = True

# Batch permutation inputs (run_all_permutations.py)
AGENTS = ["Alex", "Bob", "Cindy", "David", "Eric"]
# BATCH_MODELS = [
#     {"backend": "openai", "model": "gpt-5.4"},
#     {"backend": "deepseek", "model": "deepseek-v4-flash"},
#     {"backend": "openai", "model": "gpt-5.4-nano"},
#     {"backend": "gemini", "model": "gemini-3.5-flash"},
#     {"backend": "gemini", "model": "gemini-2.5-flash"},
# ]
BATCH_MODELS = [
    {"backend": "gemini", "model": "gemini-3.5-flash"},
    {"backend": "gemini", "model": "gemini-3.5-flash"},
    {"backend": "gemini", "model": "gemini-3.5-flash"},
    {"backend": "gemini", "model": "gemini-3.5-flash"},
    {"backend": "gemini", "model": "gemini-3.5-flash"},
]

# Backend selection mode: "uniform" (mode 1) or "per-agent" (mode 2)
BACKEND_MODE = "uniform"

# Mode 1: Uniform backend settings (all agents share the same backend/model).
UNIFORM_BACKEND = "openai"  # openai | gemini | mock
UNIFORM_MODEL = None         # e.g., "gpt-4.1-nano" or "gemini-1.5-pro"
UNIFORM_TEMPERATURE = None
UNIFORM_BASE_URL = ""        # OpenAI only; leave blank for default

# Mode 2: Per-agent backend settings.
# PER_AGENT_DEFAULT applies to agents without a specific override.
PER_AGENT_DEFAULT = {
    "backend": "openai",
    "model": OPENAI_ENGINE,
    "temperature": OPENAI_TEMPERATURE,
    "base_url": OPENAI_API_BASE,
}

# Per-agent overrides (only set keys you want to override)
AGENT_BACKENDS = {
    "Alex": {"backend": "openai", "model": "gpt-5.4", "temperature": 0.6},
    "Bob": {"backend": "deepseek", "model": "deepseek-v4-flash", "temperature": 0.6},
    "Cindy": {"backend": "openai", "model": "gpt-5.4-nano", "temperature": 0.6},
    "David": {"backend": "gemini", "model": "gemini-3.1-flash-lite", "temperature": 0.6},
    "Eric": {"backend": "gemini", "model": "gemini-2.5-flash", "temperature": 0.6},
}

# experiment_rocord.md

# exp1:
# Alex - backend: openai, model: gpt-4.1-nano

'''
Example usage:
Mode 1 (uniform): all agents use the same backend/model
1) python src/run.py --scenario low --meta-rounds 1 --backend-mode uniform --backend mock --seed 42
2) python src/run.py --scenario low --meta-rounds 1 --backend-mode uniform --backend openai --backend-model gpt-4.1-nano
3) python src/run.py --scenario low --meta-rounds 1 --backend-mode uniform --backend gemini --backend-model gemini-1.5-pro

Mode 2 (per-agent): per-agent backend/model defined in config
4) python src/run.py --scenario low --meta-rounds 1 --backend-mode per-agent 

Post-processing
5) python src/export_inference.py --log log/meta_round_20260425_0831_exp96.json --experiment-id exp-96
6) python src/export_inference.py --log-dir log --inference-root inference
7) python src/visualize_log.py --log log/meta_round_20260425_0831_exp96.json --output-dir log/plots
'''
# python src/run.py --scenario low --meta-rounds 2 --backend openai --seed 42
# python src/visualize_log.py --log log/meta_round_20260424_0630_exp97.json --output-dir /tmp/wac_plots