import json
from typing import Any, Dict, List


ALLOWED_FAILURE_LABELS: List[str] = [
    "none",
    "format_failure",
    "code_execution_failure",
    "overly_conservative_bidding",
    "overbidding_budget_depletion",
    "underbidding_starvation",
    "poor_low_hp_response",
    "poor_supply_adaptation",
    "poor_opponent_awareness",
    "weak_temporal_planning",
    "weak_cross_round_adaptation",
    "reasoning_policy_mismatch",
    "policy_trajectory_mismatch",
    "excessive_complexity",
    "budget_inefficiency",
    "insufficient_competition_awareness",
]


RUBRIC_TEXT = """
Scoring rubrics:

strategy_quality_score:
1 = incoherent or strategically harmful policy.
2 = weak policy with major survival or budget flaws.
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
1 = spends or saves budget in clearly harmful ways.
2 = frequent overbidding or over-conservation.
3 = reasonable budget use with visible inefficiencies.
4 = preserves budget while spending enough in important states.
5 = excellent resource efficiency, avoiding both wasteful overbids and fatal hoarding.

opponent_supply_adaptation_score:
1 = ignores supply scarcity and opponent behavior.
2 = uses only shallow or inconsistent adaptation signals.
3 = adapts to either supply or opponents, but incompletely.
4 = adapts bids to both scarcity and observed/opponent-code competition pressure.
5 = strongly integrates supply, opponent history/code, and competitive thresholds.

temporal_planning_score:
1 = purely current-day/reactive policy.
2 = occasionally considers future days but mainly short-sighted.
3 = has reserves or late-game logic but fails in some situations.
4 = consistently balances current survival with future budget and remaining days.
5 = strong long-term planning across early/mid/late game and meta-round context.

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


def _truncate_text(value: Any, max_chars: int = 16000) -> str:
    text = str(value) if value is not None else ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def build_judge_prompt(item: Dict[str, Any], blind_model_names: bool = True) -> str:
    policy = item.get("policy", {})
    trajectory = item.get("trajectory", {})
    status = item.get("submission_status", {})
    environment = item.get("environment", {})

    prompt_payload = {
        "metadata": {
            "item_id": item.get("item_id"),
            "condition": item.get("condition"),
            "experiment_id": item.get("experiment_id"),
            "meta_round_id": item.get("meta_round_id"),
            "agent_id": item.get("agent_id"),
        },
        "environment": environment,
        "submission_status": status,
        "policy": {
            "one_shot_reasoning": _truncate_text(policy.get("one_shot_reasoning", "")),
            "one_shot_code": _truncate_text(policy.get("one_shot_code", "")),
            "final_reasoning": _truncate_text(policy.get("final_reasoning", "")),
            "final_code": _truncate_text(policy.get("final_code", "")),
        },
        "trajectory": {
            "evidence_summary": trajectory.get("evidence_summary", {}),
            "daily_trace": trajectory.get("daily_trace", []),
            "metrics": trajectory.get("metrics"),
        },
    }

    if not blind_model_names:
        prompt_payload["metadata"]["model_name"] = item.get("model_name")

    return (
        "You are evaluating a code-mediated LLM agent in a repeated water allocation game.\n\n"
        "The agent submits a Python bidding policy:\n"
        "def get_bid(day_context, my_status, opponents_status)\n\n"
        "Evaluate whether the policy is strategically sound, whether the reasoning matches the code, "
        "and whether the code behavior matches the observed trajectory.\n\n"
        "Use the rule-based evidence_summary first, then inspect the raw trace/code when needed. "
        "Treat deterministic metrics as evidence, not as automatic scores. "
        "When a failure label is assigned, cite concrete evidence days whenever possible.\n\n"
        f"{RUBRIC_TEXT}\n\n"
        "Return JSON only.\n"
        "Do not use markdown.\n"
        "Do not use code fences.\n"
        "Do not add commentary outside JSON.\n\n"
        "Allowed failure labels:\n"
        f"{json.dumps(ALLOWED_FAILURE_LABELS, ensure_ascii=False)}\n\n"
        "Required output schema:\n"
        "{\n"
        "  \"strategy_quality_score\": 1,\n"
        "  \"survival_risk_management_score\": 1,\n"
        "  \"budget_efficiency_score\": 1,\n"
        "  \"opponent_supply_adaptation_score\": 1,\n"
        "  \"temporal_planning_score\": 1,\n"
        "  \"reasoning_code_trace_consistency_score\": 1,\n"
        "  \"implementation_quality_score\": 1,\n"
        "  \"primary_failure_mode\": \"none\",\n"
        "  \"failure_labels\": [],\n"
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
