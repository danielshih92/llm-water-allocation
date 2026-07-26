import os
import sys
from dataclasses import dataclass
from typing import Optional

# Allow importing the packaged simulation without modifying it.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "wacbench")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from agent_interface import create_backend  # noqa: E402


JUDGE_SYSTEM_PROMPT = (
    "You are an evidence-grounded evaluator of code-mediated LLM agents. "
    "Follow the scoring rubric and required output schema in the user prompt. "
    "Return exactly one valid JSON object containing the requested judge fields. "
    "Do not generate Python strategy code. "
    "Do not use markdown, code fences, or commentary outside the JSON object."
)


@dataclass
class JudgeBackend:
    backend_name: str
    model: Optional[str] = None
    temperature: float = 0.0

    def __post_init__(self) -> None:
        self.backend = create_backend(
            self.backend_name,
            model=self.model,
            temperature=self.temperature,
            system_prompt=JUDGE_SYSTEM_PROMPT,
        )

    def generate(self, prompt: str) -> str:
        return self.backend.generate(prompt)
