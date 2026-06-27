import json
from typing import Any, Dict, Optional

import config


ALLOWED_OPPONENT_INFO_MODES = {
    "full_code_access",
    "no_opponent_info",
}


def normalize_opponent_info_mode(opponent_info_mode: Optional[str]) -> str:
    mode = opponent_info_mode or config.OPPONENT_INFO_MODE

    if mode == "outcome_only":
        raise ValueError(
            "opponent_info_mode='outcome_only' has been removed. "
            "Use 'full_code_access' or 'no_opponent_info'."
        )

    if mode not in ALLOWED_OPPONENT_INFO_MODES:
        raise ValueError(
            f"Unsupported opponent_info_mode='{mode}'. "
            "Use 'full_code_access' or 'no_opponent_info'."
        )

    return mode


class PromptBuilder:
    def build_combined_prompt(
        self,
        agent_profile: Dict[str, Any],
        game_state: Dict[str, Any],
        opponent_code: Dict[str, str],
        history: Optional[Dict[str, Any]] = None,
        opponent_info_mode: Optional[str] = None,
        show_opponent_code: Optional[bool] = None,
    ) -> str:

        history_payload: Dict[str, Any] = {}
        if history and isinstance(history, dict):
            last_meta_round = history.get("last_meta_round")
            if last_meta_round is not None:
                history_payload["previous_meta_round_index"] = last_meta_round

        
        if show_opponent_code is None:
            show_opponent_code = config.REVEAL_OPPONENT_CODE

        opponent_info_mode = normalize_opponent_info_mode(opponent_info_mode)

        state_block = json.dumps(game_state or {}, indent=2)      
        profile_block = json.dumps(agent_profile or {}, indent=2)  

        supply_range = game_state.get("supply_range", [10, 20]) if isinstance(game_state, dict) else [10, 20]

        try:
            min_supply = int(supply_range[0])
            max_supply = int(supply_range[1])
        except Exception:
            min_supply = 10
            max_supply = 20

        opponent_code_section = ""

        if opponent_info_mode == "full_code_access" and show_opponent_code and opponent_code:
            opponent_block = json.dumps(opponent_code or {}, indent=2)

            opponent_code_section = (
                f"=== PREVIOUS META-ROUND OPPONENT STRATEGY CODE ===\n"
                f"Below is the Python strategy code used by your opponents in the previous meta-round.\n"
                f"This is historical code evidence only. Current-day opponent bids are simultaneous and hidden.\n"
                f"Use the code to infer robust bidding tendencies, possible weaknesses, and potential risks.\n"
                f"Do not overfit to a single opponent rule. Prioritize your own survival, budget discipline, and calibrated risk control.\n"
                f"{opponent_block}\n\n"
            )

        latest_meta_context_section = ""
        if history_payload:
            latest_meta_context_section = (
                f"LATEST METAROUND INDEX (NON-OUTCOME METADATA):\n"
                f"{json.dumps(history_payload, indent=2)}\n\n"
            )

        intro_line = (
            "You are participating in the Water Allocation Challenge programmatic game.\n"
        )

        if opponent_info_mode == "full_code_access":
            context_line = (
                "You have access only to opponents' previous meta-round strategy code. "
                "You do not receive their previous outcomes or performance summaries.\n"
            )
            reasoning_focus = (
                "Keep reasoning under 60 words. Focus on robust interpretation of opponent code, "
                "calibrated bidding, budget discipline, and avoiding unnecessary overbidding.\n"
            )
        else:
            context_line = (
                "No cross-round opponent memory is available. Use only your profile, current meta-round state, "
                "game rules, and the runtime opponent status fields available inside get_bid during the simulation.\n"
            )
            reasoning_focus = (
                "Keep reasoning under 60 words. Focus on budget-safe reasoning, calibrated risk control, and survival.\n"
            )

        return (
            # ============================================================
            # Reasoning Prompt
            # ============================================================
            f"{intro_line}"
            f"{context_line}"
            "Analyze the available context to generate a winning bidding strategy.\n\n"

            f"Your Profile:\n{profile_block}\n\n"
            f"Current Meta-Round State:\n{state_block}\n\n"
            f"{opponent_code_section}"
            f"{latest_meta_context_section}"

            # ============================================================
            # Code Prompt
            # ============================================================
            "After brief reasoning, generate executable Python code.\n\n"

            "CRITICAL PYTHON RULES:\n"
            "1. Function MUST be exactly: def get_bid(day_context, my_status, opponents_status):\n"
            "2. 'day_context' ONLY has fields: ['supply', 'day']\n"
            "3. 'my_status' ONLY has fields: ['hp', 'budget', 'no_water_days']\n"
            "4. 'opponents_status' is a dictionary keyed by opponent agent_id.\n"
            "5. Each opponent state has: ['agent_id', 'hp', 'budget', 'no_water_days', 'alive', 'water_requirement', 'daily_salary', 'last_bid', 'last_status', 'last_hp_after', 'last_budget_after', 'trace_history'].\n"
            "6. 'trace_history' is a compact list of that opponent's recent 2 day records. Each record has: ['day', 'bid', 'supply', 'hp_after', 'budget_after', 'status', 'error'].\n"
            "7. Use 'last_bid', 'last_status', 'last_hp_after', and 'last_budget_after' for quick yesterday information. Use 'trace_history' only when you need the last 2 days of trend analysis.\n"
            "8. Bidding is simultaneous. Current-day opponent bids are hidden.\n\n"
            "9. CRITICAL INDEX RULE: In Python, list/array indices MUST be integers. Since day_context['supply'] is passed as a float (e.g., 19.0), any mathematical operations like floor division (e.g., supply // WATER_REQ) will produce a FLOAT (e.g., 1.0). You MUST explicitly wrap ALL list indices or subscript selectors with int() (e.g., my_list[int(target_index)]) to strictly prevent float index RuntimeErrors.\n\n"

            "10. Minimal Safe Interface Example only. This example only demonstrates valid input handling and budget-safe return values. Do NOT copy it as the final strategy.\n"
            "def get_bid(day_context, my_status, opponents_status):\n"
            "    DAILY_SALARY = 70\n"
            "    hp = float(my_status.get('hp', 0))\n"
            "    budget = float(my_status.get('budget', 0))\n"
            "    no_water_days = int(my_status.get('no_water_days', 0))\n\n"
            "    if budget <= 0:\n"
            "        return 0.0\n\n"
            "    # Basic risk-aware fallback. This is only an interface example,\n"
            "    # not a recommended final strategy.\n"
            "    if hp <= 2 or no_water_days >= 2:\n"
            "        bid = DAILY_SALARY * 0.90\n"
            "    elif hp <= 4 or no_water_days >= 1:\n"
            "        bid = DAILY_SALARY * 0.65\n"
            "    else:\n"
            "        bid = DAILY_SALARY * 0.45\n\n"
            "    return max(0.0, min(budget, bid))\n\n"

            "11. DO NOT use undefined variables.\n"
            "12. DO NOT use markdown code fences (```).\n\n"

            f"Agent Constants:\n"
            f"WATER_REQ = {agent_profile['water_requirement']}\n"
            f"DAILY_SALARY = {agent_profile['daily_salary']}\n"
            f"MAX_SUPPLY = {max_supply}\n"
            f"MIN_SUPPLY = {min_supply}\n\n"

            f"{reasoning_focus}"
            "Output valid JSON only.\n"
            "Output format:\n"
            "{\n"
            '  "reasoning": "your short game-theoretic analysis",\n'
            '  "code": "def get_bid(...)"\n'
            "}"
        )