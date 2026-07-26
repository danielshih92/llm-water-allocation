"""Prompt-facing failure taxonomy.

The five labels describe strategic mechanisms. Deterministic events such as
death, affordable threshold misses, and actual payments are reconstructed by
the simulator-facing evidence pipeline and are not themselves judge labels.
"""

from typing import Dict, List


PROMPT_VERSION = "wac-failure-analysis-v3-causal-attribution"

FAILURE_MODES: List[str] = [
    "fatal_undercommitment",
    "winners_curse_overpayment",
    "emergency_response_failure",
    "competitive_threshold_miscalibration",
    "allocation_context_misreasoning",
]

ATTRIBUTION_STATUSES: List[str] = [
    "dominant_policy_failure",
    "mixed_policy_and_context",
    "no_clear_policy_failure",
    "insufficient_evidence",
]

INSUFFICIENT_EVIDENCE_LABEL = "insufficient_evidence"
NO_PRIMARY_FAILURE_LABEL = "no_primary_policy_failure"
ALLOWED_PRIMARY_LABELS = FAILURE_MODES + [NO_PRIMARY_FAILURE_LABEL]

CONTEXTUAL_CONTRIBUTORS: List[str] = [
    "resource_disadvantaged_role",
    "unaffordable_competitive_pressure",
    "severe_supply_scarcity",
    "opponent_bid_outlier",
]

FAILURE_MODE_DEFINITIONS: Dict[str, str] = {
    "fatal_undercommitment": (
        "The policy preserves or caps budget too aggressively, repeatedly "
        "or decisively missing a critical affordable win and dying with "
        "material unused budget. The "
        "risk response may point in the right direction, but its absolute "
        "commitment is too low."
    ),
    "winners_curse_overpayment": (
        "The policy pays excessively to secure earlier wins, weakening later "
        "survival options. This operationalizes the winner's curse described "
        "in Alympics: early bidding success can undermine long-term survival "
        "when the winner overpays."
    ),
    "emergency_response_failure": (
        "The mapping from self-risk to action is delayed, inverted, "
        "non-monotonic, or overridden by another branch/cap, so the policy "
        "does not protect itself adequately in a lethal HP/no-water state."
    ),
    "competitive_threshold_miscalibration": (
        "The policy's opponent-price model is materially miscalibrated, "
        "for example because it anchors to stale means/maxima, follows an "
        "outlier, or ignores which opponents are strategically relevant."
    ),
    "allocation_context_misreasoning": (
        "The policy relies on a materially wrong model of allocation context, "
        "including supply, water requirements, feasible winner combinations, "
        "or tie/order implications."
    ),
}
