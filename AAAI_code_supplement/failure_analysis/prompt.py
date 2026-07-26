"""Evidence-grounded prompt for strategic failure attribution."""

import json
import math
from typing import Any, Dict, List, Optional

from .taxonomy import (
    ATTRIBUTION_STATUSES,
    CONTEXTUAL_CONTRIBUTORS,
    FAILURE_MODE_DEFINITIONS,
    FAILURE_MODES,
    PROMPT_VERSION,
)


GAME_EVIDENCE_RULES = """
- Every living agent receives salary before bidding. Bids are sanitized to the
  available budget. Only allocation winners pay; losing bids cost zero.
- A winner gains HP and resets no_water_days. A loser loses HP equal to the
  current no_water_days, after which that counter increases.
- budget_before_death_reset is the money held immediately before a dead
  agent's logged budget is reset to zero. Never treat that reset as spending.
- actual_payment is the amount truly paid. A high submitted losing bid is not
  evidence of overpayment or the winner's curse.
- opponent_bids and winning_threshold are ex-post diagnostic evidence. The
  policy did not observe same-day opponent bids or the threshold when acting.
  Do not criticize a policy merely for failing to predict one exact threshold.
- A threshold miss is especially informative when it is affordable, occurs in
  a dangerous state, recurs, and is connected to an identifiable code rule.
- One item covers one agent in one meta-round. Do not infer cross-meta-round
  learning from the item alone.
""".strip()


DECISION_GUIDE = """
Assign exactly one primary failure mode only when the code and trajectory
support a coherent failure chain. Optional contributing modes are limited to two.

Apply these boundaries in order:
1. allocation_context_misreasoning requires an explicit, materially false code
   assumption about supply, requirements, feasible winners, or allocation/ties.
2. emergency_response_failure requires an explicit defect in the risk-to-bid
   mapping: increasing risk lowers the bid, activates too late, or is overridden
   by a branch/cap in a lethal state. Low bidding in danger alone is insufficient.
3. winners_curse_overpayment requires at least one derived
   winner_curse_bridge_candidate: ex-post premium on earlier actual wins must
   be large enough to cover a later critical unaffordable threshold gap. Also
   identify the code mechanism that caused the premium. High total spending or
   a payment above the ex-post threshold alone is insufficient.
4. competitive_threshold_miscalibration requires the opponent-price estimator
   to be the dominant code defect. Under dominant_policy_failure it must create
   repeated or lethal affordable misses. Under mixed_policy_and_context, one
   critical affordable miss may establish a policy contribution when later
   contextual pressure is also materially necessary. One non-critical surprise
   at an exact threshold is insufficient.
5. fatal_undercommitment applies when critical affordable misses are directly
   caused by a reserve, cap, multiplier, or fixed target that kept commitment
   too low despite a broadly sensible risk direction. dominant_policy_failure
   requires repeated or lethal evidence; mixed_policy_and_context may use one
   critical affordable turning point plus a material contextual chain.
   Winner's-curse evidence may coexist as a contributing mechanism; choose the
   primary mode by the mechanism most directly connected to death.
6. If no failure boundary is met and contextual pressure explains death, use
   no_clear_policy_failure. Use insufficient_evidence only when the available
   evidence cannot distinguish the explanations. Neither is a sixth mechanism.

Before choosing the primary label, fill every boundary_checks field. These are
evidence flags rather than a one-to-one encoding of the label. In particular,
mixed attribution may select undercommitment or competitive miscalibration from
one critical affordable miss while repeated_or_lethal_affordable_miss remains
false. Do not set a check true merely because a label appears plausible.

Calibration examples:
- A low-HP branch that lowers the bid or a reserve rule that overrides emergency
  escalation is emergency_response_failure, not fatal_undercommitment.
- A monotonic emergency multiplier whose final bid is still bound by a fixed
  reserve cap can be fatal_undercommitment if it causes a critical affordable miss.
- An early payment premium of 50 followed by a critical unaffordable gap of 30
  can support winners_curse_overpayment; a premium of 10 followed by a gap of 80
  cannot, even if total spending is high.
- A stale opponent median that repeatedly targets prices below affordable
  winning thresholds can be competitive_threshold_miscalibration.
- If no critical affordable miss or winner-curse bridge exists, the code has no
  explicit risk/allocation defect, and context explains death, select
  no_clear_policy_failure. Reserve insufficient_evidence for genuine ambiguity.

Mismatch flags are separate diagnostics, not primary death mechanisms:
- reasoning_policy_mismatch: the stated rationale materially differs from code.
- policy_trajectory_mismatch: observed behavior materially differs from what
  the code should produce for its actual inputs, after accounting for errors.
""".strip()


ATTRIBUTION_GUIDE = """
First decide whether death is attributable to the submitted policy. Death is
an outcome, not automatic evidence of policy failure.

- dominant_policy_failure: one avoidable code mechanism provides the clearest
  explanation of death. Context may still be present but is not equally causal.
- mixed_policy_and_context: an identifiable policy mechanism contributed, but
  disadvantaged role resources, unaffordable competition, scarcity, or an
  opponent outlier was also materially necessary to explain the death.
- no_clear_policy_failure: no avoidable policy mechanism satisfies a failure
  boundary; the trajectory is better explained by contextual pressure. Use a
  null primary_failure_mode and no contributing failure modes. failure_chain
  may describe a trajectory-grounded contextual chain, but code_mechanism must
  remain empty and every boundary check must be false.
- insufficient_evidence: available evidence cannot distinguish policy failure
  from context or competing explanations. Use a null primary_failure_mode.

A low-salary/high-requirement role is contextual evidence, not by itself proof
that the role caused death. Conversely, structural disadvantage does not excuse
an affordable lethal miss caused by explicit code. Use contextual contributors
only when the trajectory shows that they materially constrained survival.
""".strip()


def _safe_number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _is_critical_state(row: Dict[str, Any]) -> bool:
    """Return whether losing water now poses near-term survival danger."""
    hp = _safe_number(row.get("hp_before"))
    no_water = _safe_number(row.get("no_water_days_before"))
    if hp is None or no_water is None:
        return False
    return hp <= 4.0 or no_water >= 3.0 or hp - no_water <= 2.0


def _day(value: Any) -> Optional[int]:
    number = _safe_number(value)
    if number is None or not number.is_integer() or number <= 0:
        return None
    return int(number)


def derive_failure_evidence(item: Dict[str, Any]) -> Dict[str, Any]:
    """Compute conservative, simulator-grounded boundary evidence.

    The judge still decides whether a code mechanism caused the event. These
    fields only prevent labels from being assigned without the required
    trajectory-side evidence.
    """
    trajectory = item.get("trajectory", {})
    rows = trajectory.get("daily_evidence", []) if isinstance(trajectory, dict) else []
    if not isinstance(rows, list):
        rows = []

    affordable_misses: List[Dict[str, Any]] = []
    critical_affordable_misses: List[Dict[str, Any]] = []
    overpayments: List[Dict[str, Any]] = []
    prior_premium = 0.0
    bridge_candidates: List[Dict[str, Any]] = []
    critical_unaffordable_losses: List[Dict[str, Any]] = []

    valid_rows = [row for row in rows if isinstance(row, dict)]
    valid_rows.sort(key=lambda row: _day(row.get("day")) or 10**9)
    for row in valid_rows:
        day = _day(row.get("day"))
        if day is None:
            continue
        threshold = row.get("winning_threshold", {})
        if not isinstance(threshold, dict):
            threshold = {}
        threshold_amount = _safe_number(threshold.get("amount"))
        budget = _safe_number(row.get("budget_before_bid"))
        bid = _safe_number(row.get("bid"))
        payment = _safe_number(row.get("actual_payment")) or 0.0
        won = row.get("won_water") is True
        critical = _is_critical_state(row)

        if not won and threshold.get("reachable") is True and threshold.get("affordable") is True:
            miss = {
                "day": day,
                "critical_state": critical,
                "hp_before": row.get("hp_before"),
                "no_water_days_before": row.get("no_water_days_before"),
                "budget_before_bid": budget,
                "submitted_bid": bid,
                "winning_threshold": threshold_amount,
            }
            affordable_misses.append(miss)
            if critical:
                critical_affordable_misses.append(miss)

        if (
            not won
            and critical
            and threshold.get("reachable") is True
            and threshold.get("affordable") is False
            and threshold_amount is not None
            and budget is not None
        ):
            gap = max(0.0, threshold_amount - budget)
            critical_unaffordable_losses.append(
                {
                    "day": day,
                    "hp_before": row.get("hp_before"),
                    "no_water_days_before": row.get("no_water_days_before"),
                    "budget_before_bid": round(budget, 6),
                    "winning_threshold": round(threshold_amount, 6),
                    "unaffordable_gap": round(gap, 6),
                }
            )
            if gap > 0.0 and prior_premium + 1e-9 >= gap:
                bridge_candidates.append(
                    {
                        "later_loss_day": day,
                        "critical_state": True,
                        "hp_before": row.get("hp_before"),
                        "no_water_days_before": row.get("no_water_days_before"),
                        "budget_before_bid": round(budget, 6),
                        "winning_threshold": round(threshold_amount, 6),
                        "budget_gap": round(gap, 6),
                        "accumulated_prior_ex_post_premium": round(prior_premium, 6),
                    }
                )

        if won and threshold_amount is not None:
            premium = max(0.0, payment - threshold_amount)
            if premium > 0.0:
                prior_premium += premium
                overpayments.append(
                    {
                        "day": day,
                        "actual_payment": round(payment, 6),
                        "winning_threshold": round(threshold_amount, 6),
                        "ex_post_payment_premium": round(premium, 6),
                        "cumulative_ex_post_payment_premium": round(prior_premium, 6),
                    }
                )

    critical_miss_to_next_day_death: List[Dict[str, Any]] = []
    for index, row in enumerate(valid_rows[:-1]):
        threshold = row.get("winning_threshold", {})
        if not isinstance(threshold, dict):
            continue
        if (
            row.get("won_water") is False
            and _is_critical_state(row)
            and threshold.get("reachable") is True
            and threshold.get("affordable") is True
        ):
            next_row = valid_rows[index + 1]
            if next_row.get("won_water") is False and next_row.get("status") == "dead":
                critical_miss_to_next_day_death.append(
                    {
                        "affordable_miss_day": _day(row.get("day")),
                        "death_day": _day(next_row.get("day")),
                        "hp_before_miss": row.get("hp_before"),
                        "no_water_days_before_miss": row.get("no_water_days_before"),
                        "budget_before_miss": row.get("budget_before_bid"),
                        "submitted_bid": row.get("bid"),
                        "winning_threshold": threshold.get("amount"),
                    }
                )

    repeated_or_lethal_miss = (
        len(critical_affordable_misses) >= 2
        or bool(critical_miss_to_next_day_death)
        or any(
            row.get("status") == "dead"
            for row in valid_rows
            if not row.get("won_water")
            and isinstance(row.get("winning_threshold"), dict)
            and row["winning_threshold"].get("affordable") is True
        )
    )

    return {
        "critical_state_rule": (
            "hp_before <= 4 OR no_water_days_before >= 3 OR "
            "hp_before - no_water_days_before <= 2"
        ),
        "affordable_threshold_misses": affordable_misses,
        "critical_affordable_threshold_misses": critical_affordable_misses,
        "critical_unaffordable_threshold_losses": critical_unaffordable_losses,
        "critical_affordable_miss_to_next_day_death": (
            critical_miss_to_next_day_death
        ),
        "repeated_or_lethal_affordable_miss_supported": repeated_or_lethal_miss,
        "overpayment_events": overpayments,
        "winner_curse_bridge_candidates": bridge_candidates,
        "interpretation_limits": [
            "An ex-post premium is not assumed avoidable by the acting policy.",
            "A bridge candidate is necessary but not sufficient for winner's curse.",
            "The judge must still connect the premium and later gap to policy code.",
            "Ex-post thresholds are diagnostic and were not observed at action time.",
        ],
    }


def derive_context_evidence(
    item: Dict[str, Any], boundary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    environment = item.get("environment", {})
    players = environment.get("players", []) if isinstance(environment, dict) else []
    profiles = [player for player in players if isinstance(player, dict)]
    focal_id = str(item.get("agent_id", ""))
    focal = next(
        (profile for profile in profiles if str(profile.get("agent_id")) == focal_id),
        {},
    )
    salaries = sorted(
        value
        for value in (_safe_number(profile.get("daily_salary")) for profile in profiles)
        if value is not None
    )
    requirements = sorted(
        value
        for value in (
            _safe_number(profile.get("water_requirement")) for profile in profiles
        )
        if value is not None
    )
    focal_salary = _safe_number(focal.get("daily_salary"))
    focal_requirement = _safe_number(focal.get("water_requirement"))
    median_salary = salaries[len(salaries) // 2] if salaries else None
    median_requirement = requirements[len(requirements) // 2] if requirements else None
    lower_salary = (
        focal_salary is not None
        and median_salary is not None
        and focal_salary < median_salary
    )
    higher_requirement = (
        focal_requirement is not None
        and median_requirement is not None
        and focal_requirement > median_requirement
    )
    if boundary is None:
        boundary = derive_failure_evidence(item)
    return {
        "focal_profile": focal,
        "salary_values_across_roles": salaries,
        "water_requirement_values_across_roles": requirements,
        "below_median_salary": lower_salary,
        "above_median_water_requirement": higher_requirement,
        "resource_disadvantaged_role_candidate": lower_salary and higher_requirement,
        "critical_unaffordable_loss_count": len(
            boundary["critical_unaffordable_threshold_losses"]
        ),
        "interpretation_limit": (
            "These are contextual indicators only; attribution still requires "
            "a trajectory-grounded causal explanation."
        ),
    }


def _truncate(value: Any, limit: int = 18000) -> str:
    text = str(value) if value is not None else ""
    return text if len(text) <= limit else text[:limit] + "\n...[truncated]"


def _definitions_text() -> str:
    return "\n".join(
        f"- {label}: {FAILURE_MODE_DEFINITIONS[label]}"
        for label in FAILURE_MODES
    )


def build_failure_prompt(item: Dict[str, Any], blind_model_names: bool = True) -> str:
    policy = item.get("policy", {}) if isinstance(item.get("policy"), dict) else {}
    trajectory = (
        item.get("trajectory", {})
        if isinstance(item.get("trajectory"), dict)
        else {}
    )
    environment = (
        item.get("environment", {})
        if isinstance(item.get("environment"), dict)
        else {}
    )
    status = (
        item.get("submission_status", {})
        if isinstance(item.get("submission_status"), dict)
        else {}
    )

    boundary_evidence = derive_failure_evidence(item)
    packet: Dict[str, Any] = {
        "environment": {
            "scenario": environment.get("scenario"),
            "supply_range": environment.get("supply_range"),
            "episode_days": environment.get("episode_days"),
            "players": environment.get("players"),
        },
        "submission_status": status,
        "policy": {
            "reasoning": _truncate(policy.get("final_reasoning", "")),
            "code": _truncate(policy.get("final_code", "")),
        },
        "trajectory": {
            "evidence_summary": trajectory.get("evidence_summary", {}),
            "daily_evidence": trajectory.get("daily_evidence", []),
        },
        "derived_boundary_evidence": boundary_evidence,
        "derived_context_evidence": derive_context_evidence(
            item, boundary_evidence
        ),
    }
    if not blind_model_names:
        packet["metadata"] = {"evaluated_model": item.get("model_name")}

    schema = {
        "attribution_status": "no_clear_policy_failure",
        "primary_failure_mode": None,
        "contributing_failure_modes": [],
        "contextual_contributors": ["unaffordable_competitive_pressure"],
        "contextual_explanation": "How context materially contributed, or empty.",
        "code_mechanism": "",
        "evidence_days": [],
        "failure_chain": [],
        "counterevidence": "Evidence that weakens the selected attribution.",
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
        "short_diagnosis": "Concise evidence-grounded diagnosis.",
    }

    return (
        "You are an evidence-grounded failure analyst for a code-mediated "
        "resource-allocation agent. Do not score overall strategy quality. "
        "Your task is only to identify the dominant failure mechanism, if one "
        "is supported, by jointly reading rationale, executable policy, and "
        "the reconstructed trajectory.\n\n"
        f"Prompt version: {PROMPT_VERSION}\n\n"
        "Game and evidence rules:\n"
        f"{GAME_EVIDENCE_RULES}\n\n"
        "Allowed strategic failure modes:\n"
        f"{_definitions_text()}\n\n"
        f"Decision guide:\n{DECISION_GUIDE}\n\n"
        f"Attribution guide:\n{ATTRIBUTION_GUIDE}\n\n"
        "Allowed attribution statuses:\n"
        f"{json.dumps(ATTRIBUTION_STATUSES)}\n\n"
        "Allowed non-null primary/contributing failure modes:\n"
        f"{json.dumps(FAILURE_MODES)}\n\n"
        "Allowed contextual contributors:\n"
        f"{json.dumps(CONTEXTUAL_CONTRIBUTORS)}\n\n"
        "Return exactly one JSON object and no markdown. confidence must be "
        "an integer from 1 to 5. Required schema:\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
        "Evaluation packet:\n"
        f"{json.dumps(packet, ensure_ascii=False, indent=2)}"
    )
