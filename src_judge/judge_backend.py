import os
import sys
from dataclasses import dataclass
from typing import Optional

# Allow importing from src/ without modifying the main simulation package.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from agent_interface import create_backend  # noqa: E402


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
        )

    def generate(self, prompt: str) -> str:
        return self.backend.generate(prompt)
