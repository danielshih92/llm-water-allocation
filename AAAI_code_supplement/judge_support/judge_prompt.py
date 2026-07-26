import json
from typing import Any, Dict, List


JUDGE_PROMPT_VERSION = "wac-judge-v2-reconstructed-evidence"

ALLOWED_FAILURE_LABELS: List[str] = [
    "none",
    "submission_format_failure",
    "code_execution_failure",
    "overly_conservative_bidding",
    "overbidding_budget_depletion",
    "underbidding_starvation",
    "poor_low_hp_response",
    "poor_supply_adaptation",
    "poor_opponent_awareness",
    "weak_temporal_planning",
    "reasoning_policy_mismatch",
    "policy_trajectory_mismatch",
    "excessive_complexity",
    "budget_inefficiency",
]


GAME_RULES_TEXT = """
Game and evidence rules:

- Every agent starts with HP 8, budget 0, and no_water_days 1. Maximum HP is 10.
- At the start of each day, each living agent receives its daily salary. The
  submitted bid is sanitized to a finite value in [0, budget_before_bid].
- Allocation considers positive bids whose water requirement fits the day's
  total supply. Candidates are ordered by bid descending, water requirement
  ascending, then a deterministic seeded tie-break. They are greedily accepted
  while their requirements fit the remaining supply.
- Only allocation winners pay. A winner's actual_payment equals its sanitized
  bid. A losing bid costs exactly 0, regardless of its numerical size.
- A winner gains 2 HP up to 10 and resets no_water_days to 1. A loser loses HP
  equal to its current no_water_days, then that counter increases by 1.
- When HP becomes non-positive, the simulator marks the agent dead and resets
  its logged budget to 0. budget_before_death_reset preserves the money held
  immediately before that reset. Do not interpret the logged zero as spending.
- Rows after an agent's first dead row are simulator padding and are excluded
  from daily_evidence and all active-day statistics.
- opponent_bids are same-day sanitized bids shown as ex-post evaluation
  evidence. The policy did not know opponents' same-day bids when deciding.
- winning_threshold is an ex-post counterfactual holding all opponent bids
  fixed. "comparison": ">" means the focal bid must be strictly above amount;
  ">=" means an exact tie at amount wins under requirement/tie-break ordering.
  "affordable" is evaluated against budget_before_bid. This threshold is useful
  diagnostic evidence, not information the policy observed in advance.
- The policy observes the current day and supply, its current HP/budget/
  no_water_days, and opponent status/history supplied by the simulator. It
  does not observe future supply.
- This item contains one meta-round. Do not claim cross-meta-round learning or
  adaptation from this item alone.
""".strip()


RUBRIC_TEXT = """
Scoring rubrics:

strategy_quality_score:
1 = incoherent or strategically harmful policy.
2 = weak policy with major survival or resource-management flaws.
3 = acceptable policy that handles common cases but misses important edge cases.
4 = good policy with robust survival, budget, and adaptation behavior.
5 = excellent policy that consistently balances survival, budget, competition, and long-horizon planning.

survival_risk_management_score:
1 = ignores low HP/no-water risk or reacts randomly.
2 = sometimes reacts to danger but often underbids in critical states.
3 = generally escalates under danger, with some missed or excessive responses.
4 = consistently increases protection when HP/no-water risk rises.
5 = anticipates lethal risk early and calibrates bids to avoid preventable deaths.

budget_efficiency_score:
1 = actual payments or hoarding are clearly and repeatedly harmful.
2 = frequent costly overpayment or harmful over-conservation.
3 = reasonable payment behavior with visible inefficiencies.
4 = preserves budget while paying enough in important states.
5 = excellent resource efficiency, avoiding wasteful winner payments and fatal hoarding.

For budget judgments, use actual_payment, payment-to-income evidence, and the
counterfactual winning threshold. Never treat total_submitted_bid, a losing bid,
or a death-triggered budget reset as money spent.

opponent_supply_adaptation_score:
1 = ignores current supply and opponent information available to the policy.
2 = uses only shallow or inconsistent adaptation signals.
3 = adapts to either supply or opponent history/status, but incompletely.
4 = adapts bids to both scarcity and observed competitive signals.
5 = strongly integrates supply, opponent history/status, and plausible competitive thresholds without assuming unavailable future/current information.

temporal_planning_score:
1 = purely current-day/reactive policy.
2 = occasionally considers future days but is mainly short-sighted.
3 = has reserves or late-game logic but fails in some situations.
4 = consistently balances current survival with future budget and remaining days.
5 = strong long-term planning across early, middle, and late episode states.

reasoning_code_trace_consistency_score:
1 = reasoning, code, and observed trajectory strongly contradict each other.
2 = major mismatch between stated strategy and implemented or observed behavior.
3 = broadly aligned but with notable omissions or trajectory surprises.
4 = reasoning, code, and trajectory mostly support the same strategy.
5 = clear, faithful alignment among reasoning, executable code, and observed behavior.

implementation_quality_score:
1 = invalid, unsafe, or non-executable policy.
2 = executable only after substantial repair or with brittle logic.
3 = executable and acceptable but cluttered or fragile.
4 = clean, robust implementation with sensible guards.
5 = simple, robust, and auditable code that implements the stated strategy cleanly.
""".strip()


FAILURE_LABEL_GUIDE = """
Failure-label guidance:

- submission_format_failure: no valid policy submission was admitted after the
  submission/repair process. Do not use this for malformed judge output.
- code_execution_failure: the admitted policy produced observed execution errors.
- overly_conservative_bidding: bids remain needlessly low despite risk and an
  affordable competitive response.
- overbidding_budget_depletion: winner payments are materially excessive and
  damage later options. A high losing bid is not payment and cannot establish it.
- underbidding_starvation: an agent loses water in dangerous states while an
  affordable higher counterfactual bid could have won.
- poor_low_hp_response: the policy fails to respond appropriately as HP or the
  no-water counter becomes dangerous.
- poor_supply_adaptation: bidding fails to react sensibly to current scarcity.
- poor_opponent_awareness: code/behavior makes weak use of opponent history or
  status that was actually available at decision time.
- weak_temporal_planning: the policy mishandles reserves, remaining days, or
  near-future survival tradeoffs.
- reasoning_policy_mismatch: stated reasoning is not faithfully implemented.
- policy_trajectory_mismatch: observed behavior contradicts what the code would
  lead one to expect, after accounting for inputs and execution errors.
- excessive_complexity: unnecessary implementation complexity hurts clarity,
  robustness, or strategic behavior.
- budget_inefficiency: actual winner payments or harmful hoarding are inefficient
  but do not fit the more specific labels above.
- none: no material failure is supported by the supplied evidence.

Labels describe evidence-supported failure patterns, not proven causal effects.
One realized trajectory may be insufficient to establish a general flaw; lower
confidence or avoid a label when the evidence does not support it.
""".strip()


def _truncate_text(value: Any, max_chars: int = 16000) -> str:
    text = str(value) if value is not None else ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def _policy_payload(
    policy: Dict[str, Any],
    status: Dict[str, Any],
) -> Dict[str, Any]:
    final_reasoning_raw = policy.get("final_reasoning", "")
    final_code_raw = policy.get("final_code", "")
    final_reasoning = _truncate_text(final_reasoning_raw)
    final_code = _truncate_text(final_code_raw)
    payload: Dict[str, Any] = {
        "final_reasoning": final_reasoning,
        "final_code": final_code,
    }

    repair_used = bool(status.get("repair_used", 0))
    one_shot_reasoning_raw = policy.get("one_shot_reasoning", "")
    one_shot_code_raw = policy.get("one_shot_code", "")
    one_shot_reasoning = _truncate_text(one_shot_reasoning_raw)
    one_shot_code = _truncate_text(one_shot_code_raw)
    if repair_used and (
        str(one_shot_reasoning_raw) != str(final_reasoning_raw)
        or str(one_shot_code_raw) != str(final_code_raw)
    ):
        payload["pre_repair_submission"] = {
            "reasoning": one_shot_reasoning,
            "code": one_shot_code,
        }
    return payload


def build_judge_prompt(
    item: Dict[str, Any],
    blind_model_names: bool = True,
) -> str:
    policy = item.get("policy", {})
    trajectory = item.get("trajectory", {})
    status = item.get("submission_status", {})
    environment = item.get("environment", {})

    prompt_payload = {
        "environment": {
            "scenario": environment.get("scenario"),
            "supply_range": environment.get("supply_range"),
            "episode_days": environment.get("episode_days"),
            "players": environment.get("players"),
        },
        "submission_status": status,
        "policy": _policy_payload(policy, status),
        "trajectory": {
            "evidence_summary": trajectory.get("evidence_summary", {}),
            "daily_evidence": trajectory.get("daily_evidence", []),
        },
    }
    if not blind_model_names:
        prompt_payload["metadata"] = {
            "model_name": item.get("model_name"),
        }

    return (
        "You are evaluating a code-mediated LLM agent in a repeated water "
        "allocation game. The agent submits a Python policy with signature:\n"
        "def get_bid(day_context, my_status, opponents_status)\n\n"
        "Evaluate strategic quality, reasoning-code consistency, and whether "
        "the observed trajectory is consistent with the policy. Base every "
        "trajectory claim on the reconstructed evidence below.\n\n"
        f"{GAME_RULES_TEXT}\n\n"
        f"{RUBRIC_TEXT}\n\n"
        f"{FAILURE_LABEL_GUIDE}\n\n"
        "If evidence_summary.reconstruction_valid is false, do not make "
        "allocation/payment-dependent claims and reduce judge_confidence.\n"
        "When assigning a trajectory-based failure label, cite concrete "
        "evidence days whenever possible.\n\n"
        "Return JSON only. Do not use markdown, code fences, or commentary "
        "outside JSON.\n\n"
        "Allowed failure labels:\n"
        f"{json.dumps(ALLOWED_FAILURE_LABELS, ensure_ascii=False)}\n\n"
        "Required output schema (all scores, severity, confidence, and "
        "judge_confidence are integers from 1 to 5):\n"
        "{\n"
        "  \"strategy_quality_score\": 1,\n"
        "  \"survival_risk_management_score\": 1,\n"
        "  \"budget_efficiency_score\": 1,\n"
        "  \"opponent_supply_adaptation_score\": 1,\n"
        "  \"temporal_planning_score\": 1,\n"
        "  \"reasoning_code_trace_consistency_score\": 1,\n"
        "  \"implementation_quality_score\": 1,\n"
        "  \"primary_failure_mode\": \"none\",\n"
        "  \"failure_labels\": [\"none\"],\n"
        "  \"failure_annotations\": [\n"
        "    {\n"
        "      \"label\": \"none\",\n"
        "      \"severity\": 1,\n"
        "      \"confidence\": 1,\n"
        "      \"evidence_days\": [],\n"
        "      \"rationale\": \"...\"\n"
        "    }\n"
        "  ],\n"
        "  \"strengths\": [],\n"
        "  \"weaknesses\": [],\n"
        "  \"evidence_summary\": \"...\",\n"
        "  \"short_diagnosis\": \"...\",\n"
        "  \"judge_confidence\": 1\n"
        "}\n\n"
        "Evaluation data:\n"
        f"{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}"
    )
