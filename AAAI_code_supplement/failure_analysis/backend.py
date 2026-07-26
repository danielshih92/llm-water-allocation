"""Backend wrapper with a failure-analysis-specific system prompt."""

import json
import os
import sys
from dataclasses import dataclass
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "wacbench")

SYSTEM_PROMPT = (
    "You are an evidence-grounded failure analyst. Diagnose only the requested "
    "strategic failure mechanism. Do not assign scalar strategy-quality scores. "
    "Return exactly one valid JSON object with the requested fields, without "
    "markdown or commentary."
)

DEEPSEEK_JUDGE_MAX_TOKENS = 8000


@dataclass
class FailureJudgeBackend:
    backend_name: str
    model: Optional[str]
    temperature: float = 0.0

    def __post_init__(self) -> None:
        if self.backend_name == "mock":
            self.backend = None
            return
        if SRC_DIR not in sys.path:
            sys.path.insert(0, SRC_DIR)
        from agent_interface import create_backend

        self.backend = create_backend(
            self.backend_name,
            model=self.model,
            temperature=self.temperature,
            system_prompt=SYSTEM_PROMPT,
        )
        if self.backend_name == "deepseek":
            # DeepSeek's max_tokens covers both thinking and final content.
            # Failure-analysis prompts are evidence-heavy, so the strategy-
            # generation default (3500) can leave no room for the JSON answer.
            self.backend.max_tokens = DEEPSEEK_JUDGE_MAX_TOKENS

    def generate(self, prompt: str) -> str:
        if self.backend_name == "mock":
            return json.dumps(
                {
                    "attribution_status": "insufficient_evidence",
                    "primary_failure_mode": None,
                    "contributing_failure_modes": [],
                    "contextual_contributors": [],
                    "contextual_explanation": "",
                    "code_mechanism": "",
                    "evidence_days": [],
                    "failure_chain": [],
                    "counterevidence": "Mock backend does not attribute failures.",
                    "boundary_checks": {
                        "allocation_rule_error_explicit": False,
                        "risk_mapping_failure_explicit": False,
                        "winner_curse_bridge_supported": False,
                        "opponent_model_dominant": False,
                        "repeated_or_lethal_affordable_miss": False,
                    },
                    "reasoning_policy_mismatch": False,
                    "policy_trajectory_mismatch": False,
                    "confidence": 1,
                    "short_diagnosis": "Mock failure-analysis response.",
                }
            )
        return self.backend.generate(prompt)
