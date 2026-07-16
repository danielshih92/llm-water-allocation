import json
import re
from typing import Any, Dict, List

from judge_prompt import ALLOWED_FAILURE_LABELS


SCORE_KEYS = [
    "strategy_quality_score",
    "survival_risk_management_score",
    "budget_efficiency_score",
    "opponent_supply_adaptation_score",
    "temporal_planning_score",
    "reasoning_code_trace_consistency_score",
    "implementation_quality_score",
    "judge_confidence",
]

SCORE_ALIASES = {
    "survival_risk_management_score": "risk_management_score",
    "budget_efficiency_score": "budget_management_score",
    "opponent_supply_adaptation_score": "opponent_awareness_score",
    "reasoning_code_trace_consistency_score": "reasoning_policy_consistency",
}

REQUIRED_SCORE_KEYS = SCORE_KEYS[:-1]
REQUIRED_OUTPUT_KEYS = {
    "primary_failure_mode",
    "failure_labels",
    "short_diagnosis",
}


def _default_output(reason: str = "Judge response could not be parsed.") -> Dict[str, Any]:
    return {
        "strategy_quality_score": 1,
        "survival_risk_management_score": 1,
        "budget_efficiency_score": 1,
        "opponent_supply_adaptation_score": 1,
        "temporal_planning_score": 1,
        "reasoning_code_trace_consistency_score": 1,
        "implementation_quality_score": 1,
        "primary_failure_mode": "format_failure",
        "failure_labels": ["format_failure"],
        "failure_annotations": [],
        "strengths": [],
        "weaknesses": [reason],
        "evidence_summary": "",
        "short_diagnosis": reason,
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


def _normalize_days(days: Any) -> List[Any]:
    if not isinstance(days, list):
        return []
    out: List[Any] = []
    for value in days[:10]:
        try:
            out.append(int(value))
        except Exception:
            text = str(value).strip()
            if text:
                out.append(text)
    return out


def _normalize_failure_annotations(annotations: Any, fallback_labels: List[str]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    if isinstance(annotations, list):
        for item in annotations[:8]:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).strip()
            if label not in ALLOWED_FAILURE_LABELS:
                continue
            normalized.append(
                {
                    "label": label,
                    "severity": _to_int_score(item.get("severity", 1), 1),
                    "confidence": _to_int_score(item.get("confidence", 1), 1),
                    "evidence_days": _normalize_days(item.get("evidence_days", [])),
                    "rationale": str(item.get("rationale", "")).strip(),
                }
            )

    if normalized:
        return normalized

    return [
        {
            "label": label,
            "severity": 1,
            "confidence": 1,
            "evidence_days": [],
            "rationale": "",
        }
        for label in fallback_labels
        if label != "none"
    ]


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

    missing_score_keys = [
        key
        for key in REQUIRED_SCORE_KEYS
        if key not in parsed
        and not (key in SCORE_ALIASES and SCORE_ALIASES[key] in parsed)
    ]
    missing_output_keys = sorted(REQUIRED_OUTPUT_KEYS.difference(parsed))
    if missing_score_keys or missing_output_keys:
        missing = missing_score_keys + missing_output_keys
        return _default_output(
            "Judge response is missing required fields: " + ", ".join(missing)
        )

    normalized = dict(default)

    for key in SCORE_KEYS:
        value = parsed.get(key)
        if value is None and key in SCORE_ALIASES:
            value = parsed.get(SCORE_ALIASES[key])
        normalized[key] = _to_int_score(value, default[key])

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
            "failure_annotations": _normalize_failure_annotations(
                parsed.get("failure_annotations", []),
                failure_labels,
            ),
            "strengths": [str(x) for x in strengths[:8]],
            "weaknesses": [str(x) for x in weaknesses[:8]],
            "evidence_summary": str(parsed.get("evidence_summary", "")).strip(),
            "short_diagnosis": str(parsed.get("short_diagnosis", "")).strip(),
        }
    )

    if not normalized["short_diagnosis"]:
        normalized["short_diagnosis"] = "No diagnosis provided."

    return normalized
