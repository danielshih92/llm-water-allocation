import json
import re
from typing import Any, Dict, List

from judge_prompt import ALLOWED_FAILURE_LABELS


SCORE_KEYS = [
    "strategy_quality_score",
    "budget_management_score",
    "risk_management_score",
    "supply_adaptation_score",
    "opponent_awareness_score",
    "reasoning_policy_consistency",
    "policy_trajectory_consistency",
    "implementation_quality_score",
    "judge_confidence",
]


def _default_output() -> Dict[str, Any]:
    return {
        "strategy_quality_score": 1,
        "budget_management_score": 1,
        "risk_management_score": 1,
        "supply_adaptation_score": 1,
        "opponent_awareness_score": 1,
        "reasoning_policy_consistency": 1,
        "policy_trajectory_consistency": 1,
        "implementation_quality_score": 1,
        "primary_failure_mode": "format_failure",
        "failure_labels": ["format_failure"],
        "strengths": [],
        "weaknesses": ["Judge response could not be parsed."],
        "short_diagnosis": "Judge response parsing failed.",
        "judge_confidence": 1,
    }


def _clean_markdown_wrapper(response: str) -> str:
    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    return text


def _extract_first_json_object(text: str) -> str:
    if text.startswith("{") and text.endswith("}"):
        return text

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return match.group(0)
    return text


def _to_int_score(value: Any, default: int = 1) -> int:
    try:
        score = int(round(float(value)))
    except Exception:
        return default
    if score < 1:
        return 1
    if score > 5:
        return 5
    return score


def _normalize_labels(labels: Any) -> List[str]:
    if isinstance(labels, str):
        labels = [labels]

    if not isinstance(labels, list):
        return ["format_failure"]

    out = []
    for value in labels:
        label = str(value).strip()
        if label in ALLOWED_FAILURE_LABELS:
            out.append(label)

    if not out:
        return ["none"]

    dedup = []
    for label in out:
        if label not in dedup:
            dedup.append(label)
    return dedup


def parse_judge_response(response: str) -> Dict[str, Any]:
    default = _default_output()

    cleaned = _clean_markdown_wrapper(response)
    json_like = _extract_first_json_object(cleaned)

    parsed: Dict[str, Any]
    try:
        parsed = json.loads(json_like)
        if not isinstance(parsed, dict):
            return default
    except Exception:
        return default

    normalized = dict(default)

    for key in SCORE_KEYS:
        normalized[key] = _to_int_score(parsed.get(key, default[key]), default[key])

    primary_failure_mode = str(parsed.get("primary_failure_mode", "none")).strip()
    if primary_failure_mode not in ALLOWED_FAILURE_LABELS:
        primary_failure_mode = "format_failure"

    failure_labels = _normalize_labels(parsed.get("failure_labels", [primary_failure_mode]))
    if primary_failure_mode not in failure_labels and primary_failure_mode != "none":
        failure_labels.append(primary_failure_mode)

    strengths = parsed.get("strengths", [])
    weaknesses = parsed.get("weaknesses", [])
    if not isinstance(strengths, list):
        strengths = []
    if not isinstance(weaknesses, list):
        weaknesses = []

    normalized.update(
        {
            "primary_failure_mode": primary_failure_mode,
            "failure_labels": failure_labels,
            "strengths": [str(x) for x in strengths[:8]],
            "weaknesses": [str(x) for x in weaknesses[:8]],
            "short_diagnosis": str(parsed.get("short_diagnosis", "")).strip(),
        }
    )

    if not normalized["short_diagnosis"]:
        normalized["short_diagnosis"] = "No diagnosis provided."

    return normalized
