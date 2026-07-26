"""Runtime defaults.

The paper runner loads its authoritative values from ``configs/paper.json``.
These conservative defaults keep modules importable and make the mock backend
usable without an external configuration file.
"""

REVEAL_OPPONENT_CODE = True
OPPONENT_INFO_MODE = "full_code_access"

OPENAI_ENGINE = "gpt-5.4"
OPENAI_TEMPERATURE = 0.1
OPENAI_SLEEP_TIME = 10
OPENAI_API_TYPE = "openai"
OPENAI_API_BASE = ""
OPENAI_API_VERSION = ""

GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-3.5-flash"
CLAUDE_MODEL = "claude-sonnet-5"
DEEPSEEK_JSON_MODE = True

AGENTS = ["Alex", "Bob", "Cindy", "David", "Eric"]
BATCH_MODELS = [
    {"backend": "openai", "model": "gpt-5.4", "temperature": 0.1},
    {"backend": "deepseek", "model": "deepseek-v4-flash", "temperature": 0.1},
    {"backend": "openai", "model": "gpt-5.4-nano", "temperature": 0.1},
    {"backend": "gemini", "model": "gemini-3.5-flash", "temperature": 0.1},
    {"backend": "claude", "model": "claude-sonnet-5", "temperature": 0.1},
]

BACKEND_MODE = "uniform"
UNIFORM_BACKEND = "mock"
UNIFORM_MODEL = None
UNIFORM_TEMPERATURE = 0.1
UNIFORM_BASE_URL = ""

PER_AGENT_DEFAULT = {
    "backend": "mock",
    "model": None,
    "temperature": 0.1,
    "base_url": "",
}
AGENT_BACKENDS = {}

