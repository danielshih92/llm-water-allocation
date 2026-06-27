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
    "reasoning_policy_mismatch",
    "policy_trajectory_mismatch",
    "excessive_complexity",
    "budget_inefficiency",
    "insufficient_competition_awareness",
]


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
        "Use the following scoring scale:\n"
        "1 = very poor\n"
        "2 = weak\n"
        "3 = acceptable\n"
        "4 = good\n"
        "5 = excellent\n\n"
        "Return JSON only.\n"
        "Do not use markdown.\n"
        "Do not use code fences.\n"
        "Do not add commentary outside JSON.\n\n"
        "Allowed failure labels:\n"
        f"{json.dumps(ALLOWED_FAILURE_LABELS, ensure_ascii=False)}\n\n"
        "Required output schema:\n"
        "{\n"
        "  \"strategy_quality_score\": 1,\n"
        "  \"budget_management_score\": 1,\n"
        "  \"risk_management_score\": 1,\n"
        "  \"supply_adaptation_score\": 1,\n"
        "  \"opponent_awareness_score\": 1,\n"
        "  \"reasoning_policy_consistency\": 1,\n"
        "  \"policy_trajectory_consistency\": 1,\n"
        "  \"implementation_quality_score\": 1,\n"
        "  \"primary_failure_mode\": \"none\",\n"
        "  \"failure_labels\": [],\n"
        "  \"strengths\": [],\n"
        "  \"weaknesses\": [],\n"
        "  \"short_diagnosis\": \"...\",\n"
        "  \"judge_confidence\": 1\n"
        "}\n\n"
        "Evaluation data:\n"
        f"{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}"
    )
