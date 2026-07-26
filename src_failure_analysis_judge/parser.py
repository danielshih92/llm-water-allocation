"""Strict parser for failure-only judge responses."""

import json
import math
import re
from typing import Any, Dict, List

from .taxonomy import (
    ATTRIBUTION_STATUSES,
    CONTEXTUAL_CONTRIBUTORS,
    FAILURE_MODES,
)


REQUIRED_KEYS = {
    "attribution_status",
    "primary_failure_mode",
    "contributing_failure_modes",
    "contextual_contributors",
    "contextual_explanation",
    "code_mechanism",
    "evidence_days",
    "failure_chain",
    "counterevidence",
    "boundary_checks",
    "reasoning_policy_mismatch",
    "policy_trajectory_mismatch",
    "confidence",
    "short_diagnosis",
}

BOUNDARY_CHECK_KEYS = {
    "risk_mapping_failure_explicit",
    "winner_curse_bridge_supported",
    "repeated_or_lethal_affordable_miss",
    "opponent_model_dominant",
    "allocation_rule_error_explicit",
}


class FailureJudgeParseError(ValueError):
    """Raised when a judge response violates the required schema."""


def _clean_wrapper(response: str) -> str:
    if not isinstance(response, str) or not response.strip():
        raise FailureJudgeParseError("Judge response is empty.")
    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _required_text(value: Any, field: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise FailureJudgeParseError(f"{field} must not be empty.")
    return text


def _parse_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise FailureJudgeParseError(f"{field} must be a JSON boolean.")
    return value


def _parse_confidence(value: Any) -> int:
    if isinstance(value, bool):
        raise FailureJudgeParseError("confidence must be an integer from 1 to 5.")
    try:
        number = float(value)
    except Exception as exc:
        raise FailureJudgeParseError("confidence must be numeric.") from exc
    if not math.isfinite(number) or not number.is_integer() or not 1 <= number <= 5:
        raise FailureJudgeParseError("confidence must be an integer from 1 to 5.")
    return int(number)


def _parse_days(value: Any) -> List[int]:
    if not isinstance(value, list):
        raise FailureJudgeParseError("evidence_days must be a JSON list.")
    days: List[int] = []
    for raw in value[:20]:
        if isinstance(raw, bool):
            raise FailureJudgeParseError("evidence_days must contain integers.")
        try:
            number = float(raw)
        except Exception as exc:
            raise FailureJudgeParseError("evidence_days must contain integers.") from exc
        if not math.isfinite(number) or not number.is_integer() or number <= 0:
            raise FailureJudgeParseError("evidence_days must contain positive integers.")
        day = int(number)
        if day not in days:
            days.append(day)
    return days


def _parse_text_list(value: Any, field: str, max_items: int) -> List[str]:
    if not isinstance(value, list):
        raise FailureJudgeParseError(f"{field} must be a JSON list.")
    result = [str(item).strip() for item in value[:max_items] if str(item).strip()]
    return result


def _parse_failure_modes(value: Any, primary: Any) -> List[str]:
    labels = _parse_text_list(value, "contributing_failure_modes", 2)
    normalized: List[str] = []
    for label in labels:
        if label not in FAILURE_MODES:
            raise FailureJudgeParseError(
                f"Unknown contributing failure mode: {label!r}."
            )
        if label == primary:
            raise FailureJudgeParseError(
                "A contributing failure mode cannot equal the primary mode."
            )
        if label not in normalized:
            normalized.append(label)
    return normalized


def _parse_contextual_contributors(value: Any) -> List[str]:
    labels = _parse_text_list(value, "contextual_contributors", 4)
    normalized: List[str] = []
    for label in labels:
        if label not in CONTEXTUAL_CONTRIBUTORS:
            raise FailureJudgeParseError(
                f"Unknown contextual contributor: {label!r}."
            )
        if label not in normalized:
            normalized.append(label)
    return normalized


def _parse_boundary_checks(value: Any) -> Dict[str, bool]:
    if not isinstance(value, dict):
        raise FailureJudgeParseError("boundary_checks must be a JSON object.")
    missing = sorted(BOUNDARY_CHECK_KEYS.difference(value))
    if missing:
        raise FailureJudgeParseError(
            "boundary_checks is missing fields: " + ", ".join(missing)
        )
    return {
        key: _parse_bool(value.get(key), f"boundary_checks.{key}")
        for key in sorted(BOUNDARY_CHECK_KEYS)
    }


def _validate_primary_boundary(primary: Any, checks: Dict[str, bool]) -> None:
    required_check = {
        "winners_curse_overpayment": "winner_curse_bridge_supported",
        "emergency_response_failure": "risk_mapping_failure_explicit",
        "competitive_threshold_miscalibration": "opponent_model_dominant",
        "allocation_context_misreasoning": "allocation_rule_error_explicit",
    }.get(primary)
    if required_check and not checks[required_check]:
        raise FailureJudgeParseError(
            f"{primary} requires boundary_checks.{required_check}=true."
        )


def _parse_primary(value: Any) -> Any:
    if value is None:
        return None
    primary = str(value).strip()
    if primary not in FAILURE_MODES:
        raise FailureJudgeParseError(f"Unknown primary failure mode: {primary!r}.")
    return primary


def _validate_attribution_schema(
    status: str,
    primary: Any,
    contributing: List[str],
    contextual: List[str],
    contextual_explanation: str,
    code_mechanism: str,
    chain: List[str],
    checks: Dict[str, bool],
) -> None:
    policy_attributed = status in {
        "dominant_policy_failure",
        "mixed_policy_and_context",
    }
    if policy_attributed:
        if primary is None:
            raise FailureJudgeParseError(
                f"{status} requires a non-null primary_failure_mode."
            )
        if not code_mechanism:
            raise FailureJudgeParseError(
                f"{status} requires a non-empty code_mechanism."
            )
        if len(chain) < 2:
            raise FailureJudgeParseError(
                f"{status} requires at least two failure_chain steps."
            )
        if status == "mixed_policy_and_context" and not contextual:
            raise FailureJudgeParseError(
                "mixed_policy_and_context requires at least one contextual contributor."
            )
        if contextual and not contextual_explanation:
            raise FailureJudgeParseError(
                "Contextual contributors require a non-empty contextual_explanation."
            )
        _validate_primary_boundary(primary, checks)
        return

    if primary is not None or contributing:
        raise FailureJudgeParseError(
            f"{status} requires primary_failure_mode=null and no contributing modes."
        )
    if code_mechanism:
        raise FailureJudgeParseError(f"{status} requires an empty code_mechanism.")
    if any(checks.values()):
        raise FailureJudgeParseError(
            f"{status} requires every boundary check to be false."
        )
    if status == "insufficient_evidence" and chain:
        raise FailureJudgeParseError(
            "insufficient_evidence requires an empty failure_chain."
        )
    if status == "no_clear_policy_failure" and not contextual:
        raise FailureJudgeParseError(
            "no_clear_policy_failure requires at least one contextual contributor."
        )
    if status == "no_clear_policy_failure" and not contextual_explanation:
        raise FailureJudgeParseError(
            "no_clear_policy_failure requires a contextual_explanation."
        )
    if status == "insufficient_evidence" and contextual:
        raise FailureJudgeParseError(
            "insufficient_evidence must not assert contextual contributors."
        )


def parse_failure_response(response: str) -> Dict[str, Any]:
    try:
        payload = json.loads(_clean_wrapper(response))
    except FailureJudgeParseError:
        raise
    except Exception as exc:
        raise FailureJudgeParseError("Judge response is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise FailureJudgeParseError("Judge response must be a JSON object.")
    missing = sorted(REQUIRED_KEYS.difference(payload))
    if missing:
        raise FailureJudgeParseError("Missing required fields: " + ", ".join(missing))

    status = str(payload.get("attribution_status", "")).strip()
    if status not in ATTRIBUTION_STATUSES:
        raise FailureJudgeParseError(f"Unknown attribution status: {status!r}.")
    primary = _parse_primary(payload.get("primary_failure_mode"))

    chain = _parse_text_list(payload.get("failure_chain"), "failure_chain", 6)
    code_mechanism = str(payload.get("code_mechanism", "")).strip()
    contributing = _parse_failure_modes(
        payload.get("contributing_failure_modes"), primary
    )
    contextual = _parse_contextual_contributors(
        payload.get("contextual_contributors")
    )
    contextual_explanation = str(
        payload.get("contextual_explanation", "")
    ).strip()
    boundary_checks = _parse_boundary_checks(payload.get("boundary_checks"))
    _validate_attribution_schema(
        status,
        primary,
        contributing,
        contextual,
        contextual_explanation,
        code_mechanism,
        chain,
        boundary_checks,
    )

    return {
        "attribution_status": status,
        "primary_failure_mode": primary,
        "contributing_failure_modes": contributing,
        "contextual_contributors": contextual,
        "contextual_explanation": contextual_explanation,
        "code_mechanism": code_mechanism,
        "evidence_days": _parse_days(payload.get("evidence_days")),
        "failure_chain": chain,
        "counterevidence": str(payload.get("counterevidence", "")).strip(),
        "boundary_checks": boundary_checks,
        "reasoning_policy_mismatch": _parse_bool(
            payload.get("reasoning_policy_mismatch"),
            "reasoning_policy_mismatch",
        ),
        "policy_trajectory_mismatch": _parse_bool(
            payload.get("policy_trajectory_mismatch"),
            "policy_trajectory_mismatch",
        ),
        "confidence": _parse_confidence(payload.get("confidence")),
        "short_diagnosis": _required_text(
            payload.get("short_diagnosis"), "short_diagnosis"
        ),
    }
