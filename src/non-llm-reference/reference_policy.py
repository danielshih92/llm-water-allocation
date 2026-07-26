"""Fixed, interpretable non-LLM policy used for WACBench calibration."""

from __future__ import annotations

from dataclasses import dataclass


POLICY_NAME = "risk-aware pacing heuristic"
SAFE_MULTIPLIER = 0.5
URGENT_MULTIPLIER = 1.0
CRITICAL_MULTIPLIER = 2.0
COMPETITIVE_MARGIN = 1.0


@dataclass(frozen=True)
class RoleParameters:
    agent_id: str
    daily_salary: float
    water_requirement: int


def build_policy_code(role: RoleParameters, episode_days: int = 20) -> str:
    """Return executable policy code with the public role profile embedded.

    The rule is intentionally fixed before evaluation. It performs no search
    and has no access to future supply or current-day opponent bids.
    """
    if episode_days <= 0:
        raise ValueError("episode_days must be positive")
    if role.daily_salary <= 0:
        raise ValueError("daily_salary must be positive")
    if role.water_requirement <= 0:
        raise ValueError("water_requirement must be positive")

    return f'''def get_bid(day_context, my_status, opponents_status):
    # Fixed role information disclosed to every policy before play.
    daily_salary = {float(role.daily_salary)!r}
    episode_days = {int(episode_days)!r}

    day = int(day_context.get("day", 1))
    budget = max(0.0, float(my_status.get("budget", 0.0)))
    hp = float(my_status.get("hp", 0.0))
    no_water_days = max(1, int(my_status.get("no_water_days", 1)))
    if budget <= 0.0:
        return 0.0

    remaining_days = max(1, episode_days - day + 1)
    future_income = daily_salary * float(remaining_days - 1)
    paced_bid = (budget + future_income) / float(remaining_days)

    hp_after_one_loss = hp - float(no_water_days)
    hp_after_two_losses = hp_after_one_loss - float(no_water_days + 1)
    if hp_after_one_loss <= 0.0:
        multiplier = {CRITICAL_MULTIPLIER!r}
    elif hp_after_two_losses <= 0.0:
        multiplier = {URGENT_MULTIPLIER!r}
    else:
        multiplier = {SAFE_MULTIPLIER!r}

    bid = multiplier * paced_bid

    # Under urgent risk, use the median previous-day opponent bid as a
    # transparent estimate of recent competitive pressure.
    if multiplier >= {URGENT_MULTIPLIER!r}:
        recent_bids = []
        for status in (opponents_status or {{}}).values():
            if not status.get("alive", True):
                continue
            last_bid = float(status.get("last_bid", 0.0) or 0.0)
            if last_bid > 0.0:
                recent_bids.append(last_bid)
        recent_bids = sorted(recent_bids)
        if recent_bids:
            middle = len(recent_bids) // 2
            if len(recent_bids) % 2 == 0:
                median_bid = 0.5 * (recent_bids[middle - 1] + recent_bids[middle])
            else:
                median_bid = recent_bids[middle]
            bid = max(bid, median_bid + {COMPETITIVE_MARGIN!r})

    return float(min(budget, max(0.0, bid)))
'''

