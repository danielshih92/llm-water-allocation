"""Reconstruct judge-facing allocation and budget evidence from compact logs."""

import math
import random
import statistics
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple


START_HP = 8.0
MAX_HP = 10.0
START_NO_WATER_DAYS = 1
FLOAT_TOLERANCE = 1e-6


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        number = float(value)
    except Exception:
        return default
    if not math.isfinite(number):
        return default
    return number


def _round_or_none(value: Any, digits: int = 6) -> Optional[float]:
    number = _safe_float(value)
    if number is None:
        return None
    return round(number, digits)


def _is_close(left: Any, right: Any) -> bool:
    left_number = _safe_float(left)
    right_number = _safe_float(right)
    if left_number is None or right_number is None:
        return left_number is right_number
    return math.isclose(
        left_number,
        right_number,
        rel_tol=1e-9,
        abs_tol=FLOAT_TOLERANCE,
    )


def _trace_by_day(agent: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    rows: Dict[int, Dict[str, Any]] = {}
    trace = agent.get("daily_trace", [])
    if not isinstance(trace, list):
        return rows
    for row in trace:
        if not isinstance(row, dict):
            continue
        try:
            day = int(row.get("day"))
        except Exception:
            continue
        rows[day] = row
    return rows


def replay_winners(
    bids: Dict[str, float],
    profiles: List[Dict[str, Any]],
    supply: float,
    day: int,
) -> List[str]:
    """Replay the simulator's deterministic greedy allocation exactly."""
    supply = float(supply)
    tie_rng = random.Random(f"wac-tie-break-{int(day)}-{supply}")
    candidates: List[Tuple[str, float, float, float]] = []

    for profile in profiles:
        agent_id = str(profile.get("agent_id"))
        bid = _safe_float(bids.get(agent_id), 0.0) or 0.0
        requirement = _safe_float(profile.get("water_requirement"))
        if requirement is None or bid <= 0.0 or requirement > supply:
            continue
        candidates.append(
            (agent_id, bid, requirement, tie_rng.random())
        )

    candidates.sort(key=lambda row: (-row[1], row[2], row[3]))

    winners: List[str] = []
    remaining = supply
    for agent_id, _, requirement, _ in candidates:
        if requirement <= remaining:
            winners.append(agent_id)
            remaining -= requirement
    return winners


def _remaining_supply(
    winners: List[str],
    profile_map: Dict[str, Dict[str, Any]],
    supply: float,
) -> float:
    remaining = float(supply)
    for agent_id in winners:
        requirement = _safe_float(
            profile_map.get(agent_id, {}).get("water_requirement"),
            0.0,
        ) or 0.0
        remaining -= requirement
    return remaining


def _wins_with_bid(
    focal_agent_id: str,
    candidate_bid: float,
    bids: Dict[str, float],
    profiles: List[Dict[str, Any]],
    supply: float,
    day: int,
) -> bool:
    counterfactual_bids = dict(bids)
    counterfactual_bids[focal_agent_id] = candidate_bid
    return focal_agent_id in replay_winners(
        counterfactual_bids,
        profiles,
        supply,
        day,
    )


def find_winning_threshold(
    focal_agent_id: str,
    bids: Dict[str, float],
    profiles: List[Dict[str, Any]],
    supply: float,
    day: int,
    budget_before_bid: float,
) -> Dict[str, Any]:
    """
    Find the lowest counterfactual bid breakpoint that makes the focal agent win.

    The output uses an amount plus a comparison operator because a threshold may
    require bidding strictly above an opponent rather than tying that opponent.
    """
    profile_map = {
        str(profile.get("agent_id")): profile
        for profile in profiles
        if isinstance(profile, dict)
    }
    focal_profile = profile_map.get(str(focal_agent_id), {})
    requirement = _safe_float(focal_profile.get("water_requirement"))
    supply = float(supply)
    budget_before_bid = _safe_float(budget_before_bid, 0.0) or 0.0

    if requirement is None or requirement > supply:
        return {
            "amount": None,
            "comparison": None,
            "affordable": False,
            "reachable": False,
            "reason": "water_requirement_exceeds_supply_or_profile_missing",
        }

    smallest_positive = math.nextafter(0.0, math.inf)
    if _wins_with_bid(
        focal_agent_id,
        smallest_positive,
        bids,
        profiles,
        supply,
        day,
    ):
        return {
            "amount": 0.0,
            "comparison": ">",
            "affordable": budget_before_bid > 0.0,
            "reachable": True,
            "reason": None,
        }

    opponent_levels = set()
    for agent_id, raw_bid in bids.items():
        if str(agent_id) == str(focal_agent_id):
            continue
        bid = _safe_float(raw_bid)
        opponent_requirement = _safe_float(
            profile_map.get(str(agent_id), {}).get("water_requirement")
        )
        if (
            bid is not None
            and bid > 0.0
            and opponent_requirement is not None
            and opponent_requirement <= supply
        ):
            opponent_levels.add(bid)

    for level in sorted(opponent_levels):
        if _wins_with_bid(
            focal_agent_id,
            level,
            bids,
            profiles,
            supply,
            day,
        ):
            return {
                "amount": _round_or_none(level),
                "comparison": ">=",
                "affordable": budget_before_bid >= level,
                "reachable": True,
                "reason": None,
            }

        just_above = math.nextafter(level, math.inf)
        if _wins_with_bid(
            focal_agent_id,
            just_above,
            bids,
            profiles,
            supply,
            day,
        ):
            return {
                "amount": _round_or_none(level),
                "comparison": ">",
                "affordable": budget_before_bid > level,
                "reachable": True,
                "reason": None,
            }

    return {
        "amount": None,
        "comparison": None,
        "affordable": False,
        "reachable": False,
        "reason": "no_winning_bid_found",
    }


def _population_variance(values: List[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return statistics.pvariance(values)


def _entropy(values: List[float]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    return -sum(
        (count / len(values)) * math.log2(count / len(values))
        for count in counts.values()
        if count > 0
    )


def _pearson_correlation(left: List[float], right: List[float]) -> Optional[float]:
    if len(left) != len(right) or len(left) <= 1:
        return None
    left_mean = statistics.mean(left)
    right_mean = statistics.mean(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean)
        for x, y in zip(left, right)
    )
    left_scale = math.sqrt(sum((x - left_mean) ** 2 for x in left))
    right_scale = math.sqrt(sum((y - right_mean) ** 2 for y in right))
    denominator = left_scale * right_scale
    if denominator == 0.0:
        return None
    return numerator / denominator


def reconstruct_record_evidence(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rebuild payment and allocation evidence from an existing compact meta-round log.

    This does not mutate the source record and does not require rerunning agent code.
    """
    environment = record.get("environment", {})
    agents = record.get("agents", [])
    if not isinstance(environment, dict) or not isinstance(agents, list):
        return {
            "reconstruction_valid": False,
            "validation_mismatches": ["missing_environment_or_agents"],
            "agents": {},
        }

    raw_profiles = environment.get("players", [])
    profiles = [
        dict(profile)
        for profile in raw_profiles
        if isinstance(profile, dict) and profile.get("agent_id") is not None
    ]
    if not profiles:
        return {
            "reconstruction_valid": False,
            "validation_mismatches": ["missing_player_profiles"],
            "agents": {},
        }

    profile_map = {
        str(profile.get("agent_id")): profile
        for profile in profiles
    }
    agent_map = {
        str(agent.get("agent_id")): agent
        for agent in agents
        if isinstance(agent, dict) and agent.get("agent_id") is not None
    }
    traces = {
        agent_id: _trace_by_day(agent_map.get(agent_id, {}))
        for agent_id in profile_map
    }

    supply_list = environment.get("supply_list", [])
    episode_days = environment.get("episode_days")
    try:
        episode_days = int(episode_days)
    except Exception:
        episode_days = len(supply_list) if isinstance(supply_list, list) else 0
    if episode_days <= 0:
        episode_days = max(
            (max(rows) for rows in traces.values() if rows),
            default=0,
        )

    alive_at_start = {agent_id: True for agent_id in profile_map}
    previous_budget = {agent_id: 0.0 for agent_id in profile_map}
    previous_hp = {agent_id: START_HP for agent_id in profile_map}
    no_water_days = {
        agent_id: START_NO_WATER_DAYS
        for agent_id in profile_map
    }
    daily_by_agent: Dict[str, List[Dict[str, Any]]] = {
        agent_id: []
        for agent_id in profile_map
    }
    mismatches: List[str] = []
    mismatches_by_agent: Dict[str, List[str]] = {
        agent_id: []
        for agent_id in profile_map
    }

    for day in range(1, episode_days + 1):
        supply = None
        if isinstance(supply_list, list) and day <= len(supply_list):
            supply = _safe_float(supply_list[day - 1])
        if supply is None:
            for rows in traces.values():
                if day in rows:
                    supply = _safe_float(rows[day].get("supply"))
                    if supply is not None:
                        break
        if supply is None:
            mismatches.append(f"day_{day}:missing_supply")
            continue
        supply = float(supply)

        bids: Dict[str, float] = {}
        active_snapshot = dict(alive_at_start)
        for profile in profiles:
            agent_id = str(profile.get("agent_id"))
            if not active_snapshot.get(agent_id, False):
                bids[agent_id] = 0.0
                continue
            row = traces.get(agent_id, {}).get(day)
            if row is None:
                mismatches.append(f"{agent_id}:day_{day}:missing_trace_row")
                mismatches_by_agent[agent_id].append(
                    f"day_{day}:missing_trace_row"
                )
                bids[agent_id] = 0.0
                continue
            bids[agent_id] = _safe_float(row.get("bid"), 0.0) or 0.0

        winners = replay_winners(bids, profiles, supply, day)
        winner_set = set(winners)
        remaining_supply = _remaining_supply(winners, profile_map, supply)

        for profile in profiles:
            agent_id = str(profile.get("agent_id"))
            if not active_snapshot.get(agent_id, False):
                continue

            row = traces.get(agent_id, {}).get(day)
            if row is None:
                alive_at_start[agent_id] = False
                continue

            salary = _safe_float(profile.get("daily_salary"), 0.0) or 0.0
            requirement = _safe_float(profile.get("water_requirement"))
            bid = bids.get(agent_id, 0.0)
            budget_before_bid = previous_budget[agent_id] + salary
            won_water = agent_id in winner_set
            actual_payment = bid if won_water else 0.0
            budget_after_payment = budget_before_bid - actual_payment
            hp_before = previous_hp[agent_id]
            no_water_before = no_water_days[agent_id]
            expected_hp_after = (
                min(MAX_HP, hp_before + 2.0)
                if won_water
                else hp_before - no_water_before
            )
            expected_status = "dead" if expected_hp_after <= 0.0 else "alive"

            logged_hp_after = _safe_float(row.get("hp_after"))
            logged_budget_after = _safe_float(row.get("budget_after"))
            logged_status = str(row.get("status", ""))
            died_today = logged_status == "dead"
            expected_logged_budget = (
                0.0 if died_today else budget_after_payment
            )

            row_mismatches: List[str] = []
            if not _is_close(logged_budget_after, expected_logged_budget):
                row_mismatches.append(
                    "budget_transition_mismatch"
                )
            if not _is_close(logged_hp_after, expected_hp_after):
                row_mismatches.append("hp_transition_mismatch")
            if logged_status != expected_status:
                row_mismatches.append("status_transition_mismatch")

            for mismatch in row_mismatches:
                text = f"{agent_id}:day_{day}:{mismatch}"
                mismatches.append(text)
                mismatches_by_agent[agent_id].append(
                    f"day_{day}:{mismatch}"
                )

            threshold = find_winning_threshold(
                focal_agent_id=agent_id,
                bids=bids,
                profiles=profiles,
                supply=supply,
                day=day,
                budget_before_bid=budget_before_bid,
            )
            threshold_amount = _safe_float(threshold.get("amount"))
            bid_gap = (
                bid - threshold_amount
                if threshold_amount is not None
                else None
            )

            opponent_bids = {
                other_id: {
                    "bid": _round_or_none(other_bid),
                    "alive_at_start": bool(
                        active_snapshot.get(other_id, False)
                    ),
                }
                for other_id, other_bid in bids.items()
                if other_id != agent_id
            }

            daily_by_agent[agent_id].append(
                {
                    "day": day,
                    "supply": _round_or_none(supply),
                    "water_requirement": _round_or_none(requirement),
                    "hp_before": _round_or_none(hp_before),
                    "no_water_days_before": no_water_before,
                    "budget_before_bid": _round_or_none(budget_before_bid),
                    "bid": _round_or_none(bid),
                    "opponent_bids": opponent_bids,
                    "allocation_winners": winners,
                    "remaining_supply_after_allocation": _round_or_none(
                        remaining_supply
                    ),
                    "won_water": won_water,
                    "actual_payment": _round_or_none(actual_payment),
                    "budget_after_payment": _round_or_none(
                        budget_after_payment
                    ),
                    "budget_before_death_reset": (
                        _round_or_none(budget_after_payment)
                        if died_today
                        else None
                    ),
                    "logged_budget_after": _round_or_none(
                        logged_budget_after
                    ),
                    "death_budget_reset_applied": died_today,
                    "hp_after": _round_or_none(logged_hp_after),
                    "status": logged_status,
                    "error": row.get("error"),
                    "winning_threshold": threshold,
                    "bid_gap_from_threshold": _round_or_none(bid_gap),
                    "reconstruction_valid": not row_mismatches,
                }
            )

            if died_today:
                alive_at_start[agent_id] = False
            else:
                previous_budget[agent_id] = (
                    logged_budget_after
                    if logged_budget_after is not None
                    else budget_after_payment
                )
                previous_hp[agent_id] = (
                    logged_hp_after
                    if logged_hp_after is not None
                    else expected_hp_after
                )
                no_water_days[agent_id] = (
                    START_NO_WATER_DAYS
                    if won_water
                    else no_water_before + 1
                )

    agent_outputs: Dict[str, Dict[str, Any]] = {}
    for agent_id, daily_rows in daily_by_agent.items():
        profile = profile_map.get(agent_id, {})
        agent = agent_map.get(agent_id, {})
        metrics = agent.get("metrics")
        if not isinstance(metrics, dict):
            metrics = {}

        bids = [
            _safe_float(row.get("bid"), 0.0) or 0.0
            for row in daily_rows
        ]
        payments = [
            _safe_float(row.get("actual_payment"), 0.0) or 0.0
            for row in daily_rows
        ]
        supplies = [
            _safe_float(row.get("supply"), 0.0) or 0.0
            for row in daily_rows
        ]
        salary = _safe_float(profile.get("daily_salary"), 0.0) or 0.0
        total_income = salary * len(daily_rows)
        death_row = next(
            (
                row
                for row in daily_rows
                if row.get("status") == "dead"
            ),
            None,
        )
        final_row = daily_rows[-1] if daily_rows else {}
        low_hp_days = []
        for row in daily_rows:
            hp_after = _safe_float(row.get("hp_after"))
            if hp_after is not None and hp_after <= 3.0:
                low_hp_days.append(row.get("day"))
        threshold_miss_days = [
            row.get("day")
            for row in daily_rows
            if not row.get("won_water")
            and isinstance(row.get("winning_threshold"), dict)
            and row["winning_threshold"].get("affordable") is True
        ]
        unaffordable_threshold_days = [
            row.get("day")
            for row in daily_rows
            if not row.get("won_water")
            and isinstance(row.get("winning_threshold"), dict)
            and row["winning_threshold"].get("reachable") is True
            and row["winning_threshold"].get("affordable") is False
        ]
        overpayment_amounts = [
            max(
                0.0,
                (_safe_float(row.get("actual_payment"), 0.0) or 0.0)
                - (
                    _safe_float(
                        row.get("winning_threshold", {}).get("amount"),
                        0.0,
                    )
                    or 0.0
                ),
            )
            for row in daily_rows
            if row.get("won_water")
        ]

        early_count = max(1, len(daily_rows) // 3) if daily_rows else 0
        early_payments = payments[:early_count]
        summary = {
            "reconstruction_valid": not mismatches,
            "reconstruction_mismatches": mismatches[:20],
            "agent_specific_reconstruction_mismatches": (
                mismatches_by_agent.get(agent_id, [])[:20]
            ),
            "agent_profile": profile,
            "episode_days": episode_days,
            "active_decision_days": len(daily_rows),
            "survival_days": sum(
                1 for row in daily_rows if row.get("status") == "alive"
            ),
            "death_day": death_row.get("day") if death_row else None,
            "final_status": final_row.get("status"),
            "final_hp": final_row.get("hp_after"),
            "logged_final_budget": final_row.get("logged_budget_after"),
            "final_budget_after_payment": final_row.get(
                "budget_after_payment"
            ),
            "budget_before_death_reset": (
                death_row.get("budget_before_death_reset")
                if death_row
                else None
            ),
            "daily_salary": _round_or_none(salary),
            "water_requirement": _round_or_none(
                profile.get("water_requirement")
            ),
            "total_salary_income_received": _round_or_none(total_income),
            "total_submitted_bid": _round_or_none(sum(bids)),
            "average_submitted_bid_active_days": _round_or_none(
                statistics.mean(bids) if bids else 0.0
            ),
            "bid_variance_active_days": _round_or_none(
                _population_variance(bids)
            ),
            "bid_entropy_active_days": _round_or_none(_entropy(bids)),
            "supply_bid_correlation_active_days": _round_or_none(
                _pearson_correlation(supplies, bids)
            ),
            "total_actual_payment": _round_or_none(sum(payments)),
            "average_actual_payment_active_days": _round_or_none(
                statistics.mean(payments) if payments else 0.0
            ),
            "payment_to_income_ratio": (
                _round_or_none(sum(payments) / total_income)
                if total_income > 0.0
                else None
            ),
            "win_count": sum(
                1 for row in daily_rows if row.get("won_water")
            ),
            "win_rate_active_days": (
                _round_or_none(
                    sum(1 for row in daily_rows if row.get("won_water"))
                    / len(daily_rows)
                )
                if daily_rows
                else None
            ),
            "threshold_miss_days": threshold_miss_days[:20],
            "unaffordable_threshold_days": unaffordable_threshold_days[:20],
            "total_payment_above_threshold": _round_or_none(
                sum(overpayment_amounts)
            ),
            "early_active_day_count": early_count,
            "early_total_actual_payment": _round_or_none(
                sum(early_payments)
            ),
            "min_hp_after": _round_or_none(
                min(
                    (
                        _safe_float(row.get("hp_after"))
                        for row in daily_rows
                        if _safe_float(row.get("hp_after")) is not None
                    ),
                    default=None,
                )
            ),
            "low_hp_days": low_hp_days[:20],
            "strategy_complexity": metrics.get("strategy_complexity"),
            "branch_count": metrics.get("branch_count"),
            "loop_count": metrics.get("loop_count"),
            "function_call_count": metrics.get("function_call_count"),
        }
        agent_outputs[agent_id] = {
            "daily_evidence": daily_rows,
            "summary": summary,
        }

    return {
        "reconstruction_valid": not mismatches,
        "validation_mismatches": mismatches[:100],
        "agents": agent_outputs,
    }
