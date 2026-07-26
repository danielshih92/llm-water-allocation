import json
import math
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

REQUIRED_OUTPUT_KEYS = {
    *SCORE_KEYS,
    "primary_failure_mode",
    "failure_labels",
    "failure_annotations",
    "strengths",
    "weaknesses",
    "evidence_summary",
    "short_diagnosis",
}


class JudgeResponseParseError(ValueError):
    """The judge returned a response that does not satisfy the output schema."""


def _clean_markdown_wrapper(response: str) -> str:
    if not isinstance(response, str) or not response.strip():
        raise JudgeResponseParseError("Judge response is empty.")

    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_score(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise JudgeResponseParseError(
            f"{field_name} must be an integer from 1 to 5."
        )
    try:
        number = float(value)
    except Exception as exc:
        raise JudgeResponseParseError(
            f"{field_name} must be numeric."
        ) from exc
    if (
        not math.isfinite(number)
        or not number.is_integer()
        or number < 1
        or number > 5
    ):
        raise JudgeResponseParseError(
            f"{field_name} must be an integer from 1 to 5."
        )
    return int(number)


def _normalize_labels(labels: Any, primary: str) -> List[str]:
    if not isinstance(labels, list):
        raise JudgeResponseParseError("failure_labels must be a JSON list.")

    normalized: List[str] = []
    for value in labels:
        label = str(value).strip()
        if label not in ALLOWED_FAILURE_LABELS:
            raise JudgeResponseParseError(
                f"Unknown failure label: {label!r}."
            )
        if label not in normalized:
            normalized.append(label)

    if not normalized:
        normalized = [primary]
    elif primary not in normalized:
        normalized.append(primary)

    non_none_labels = [
        label for label in normalized if label != "none"
    ]
    if primary == "none" and non_none_labels:
        raise JudgeResponseParseError(
            "primary_failure_mode cannot be 'none' when failure_labels "
            "contains a failure."
        )
    if non_none_labels:
        normalized = non_none_labels
    return normalized


def _normalize_days(days: Any) -> List[int]:
    if not isinstance(days, list):
        raise JudgeResponseParseError(
            "failure annotation evidence_days must be a JSON list."
        )
    normalized: List[int] = []
    for value in days[:20]:
        if isinstance(value, bool):
            raise JudgeResponseParseError(
                "failure annotation evidence_days must contain integers."
            )
        try:
            numeric_day = float(value)
        except Exception as exc:
            raise JudgeResponseParseError(
                "failure annotation evidence_days must contain integers."
            ) from exc
        if not math.isfinite(numeric_day) or not numeric_day.is_integer():
            raise JudgeResponseParseError(
                "failure annotation evidence_days must contain integers."
            )
        day = int(numeric_day)
        if day <= 0:
            raise JudgeResponseParseError(
                "failure annotation evidence days must be positive."
            )
        normalized.append(day)
    return normalized


def _normalize_failure_annotations(
    annotations: Any,
) -> List[Dict[str, Any]]:
    if not isinstance(annotations, list):
        raise JudgeResponseParseError(
            "failure_annotations must be a JSON list."
        )

    normalized: List[Dict[str, Any]] = []
    for index, item in enumerate(annotations[:20]):
        if not isinstance(item, dict):
            raise JudgeResponseParseError(
                f"failure_annotations[{index}] must be an object."
            )
        label = str(item.get("label", "")).strip()
        if label not in ALLOWED_FAILURE_LABELS:
            raise JudgeResponseParseError(
                f"Unknown failure annotation label: {label!r}."
            )
        rationale = str(item.get("rationale", "")).strip()
        if label != "none" and not rationale:
            raise JudgeResponseParseError(
                f"failure_annotations[{index}].rationale must not be empty."
            )
        normalized.append(
            {
                "label": label,
                "severity": _parse_score(
                    item.get("severity"),
                    f"failure_annotations[{index}].severity",
                ),
                "confidence": _parse_score(
                    item.get("confidence"),
                    f"failure_annotations[{index}].confidence",
                ),
                "evidence_days": _normalize_days(
                    item.get("evidence_days", [])
                ),
                "rationale": rationale,
            }
        )
    return normalized


def _normalize_text_list(value: Any, field_name: str) -> List[str]:
    if not isinstance(value, list):
        raise JudgeResponseParseError(
            f"{field_name} must be a JSON list."
        )
    return [str(item).strip() for item in value[:20] if str(item).strip()]


def parse_judge_response(response: str) -> Dict[str, Any]:
    cleaned = _clean_markdown_wrapper(response)
    try:
        parsed = json.loads(cleaned)
    except Exception as exc:
        raise JudgeResponseParseError(
            "Judge response is not valid JSON."
        ) from exc

    if not isinstance(parsed, dict):
        raise JudgeResponseParseError(
            "Judge response must be a JSON object."
        )

    missing_keys = sorted(REQUIRED_OUTPUT_KEYS.difference(parsed))
    if missing_keys:
        raise JudgeResponseParseError(
            "Judge response is missing required fields: "
            + ", ".join(missing_keys)
        )

    primary = str(parsed.get("primary_failure_mode", "")).strip()
    if primary not in ALLOWED_FAILURE_LABELS:
        raise JudgeResponseParseError(
            f"Unknown primary_failure_mode: {primary!r}."
        )

    failure_labels = _normalize_labels(
        parsed.get("failure_labels"),
        primary,
    )
    failure_annotations = _normalize_failure_annotations(
        parsed.get("failure_annotations")
    )
    annotated_labels = {
        annotation["label"]
        for annotation in failure_annotations
        if annotation["label"] != "none"
    }
    expected_annotated_labels = {
        label for label in failure_labels if label != "none"
    }
    if annotated_labels != expected_annotated_labels:
        raise JudgeResponseParseError(
            "failure_annotations must cover every non-'none' failure "
            "label and must not contain unlisted failure labels."
        )

    normalized: Dict[str, Any] = {
        key: _parse_score(parsed.get(key), key)
        for key in SCORE_KEYS
    }
    normalized.update(
        {
            "primary_failure_mode": primary,
            "failure_labels": failure_labels,
            "failure_annotations": failure_annotations,
            "strengths": _normalize_text_list(
                parsed.get("strengths"),
                "strengths",
            ),
            "weaknesses": _normalize_text_list(
                parsed.get("weaknesses"),
                "weaknesses",
            ),
            "evidence_summary": str(
                parsed.get("evidence_summary", "")
            ).strip(),
            "short_diagnosis": str(
                parsed.get("short_diagnosis", "")
            ).strip(),
        }
    )

    if not normalized["short_diagnosis"]:
        raise JudgeResponseParseError(
            "short_diagnosis must not be empty."
        )
    return normalized
