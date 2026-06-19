import json
import re
from typing import Any, Dict, Optional

import config


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
                history_payload["last_meta_round"] = last_meta_round

            if history.get("self_summary") is not None:
                history_payload["self_summary"] = history.get("self_summary")

            if history.get("opponent_summaries") is not None:
                history_payload["opponent_summaries"] = history.get("opponent_summaries")

            if not history_payload:
                keys = list(history.keys())
                if keys:
                    try:
                        latest_key = max(
                            keys,
                            key=lambda x: tuple(int(s) for s in re.findall(r"\d+", x))
                            if re.findall(r"\d+", x)
                            else (0,),
                        )
                        data = history[latest_key]
                        
                        if isinstance(data, dict) and "summary" in data:
                            history_payload = data["summary"]
                        else:
                            history_payload = data
                    except Exception:
                        latest_key = keys[-1]
                        history_payload = history[latest_key]

        
        if show_opponent_code is None:
            show_opponent_code = config.REVEAL_OPPONENT_CODE

        if opponent_info_mode is None:
            if show_opponent_code:
                opponent_info_mode = "full_code_access"
            elif history_payload.get("opponent_summaries"):
                opponent_info_mode = "outcome_only"
            else:
                opponent_info_mode = "no_opponent_info"

        history_block = json.dumps(history_payload, indent=2)
        state_block = json.dumps(game_state or {}, indent=2)      
        profile_block = json.dumps(agent_profile or {}, indent=2)  

        opponent_code_section = ""

        if show_opponent_code and opponent_code:
            opponent_block = json.dumps(opponent_code or {}, indent=2)

            opponent_code_section = (
                f"=== CRITICAL: OPPONENT SOURCE CODE ===\n"
                f"Below is the exact Python code currently used by your opponents in this meta-round.\n"
                f"Analyze it to find their tactical flaws:\n"
                f"{opponent_block}\n\n"
            )

        intro_line = (
            "You are participating in the Water Allocation Challenge programmatic game.\n"
        )

        if opponent_info_mode == "full_code_access":
            context_line = (
                "You have opponent source code and last meta-round outcomes.\n"
            )
            reasoning_focus = (
                "Keep reasoning under 60 words, focusing on how you exploit their YESTERDAY code/trace.\n"
            )
        elif opponent_info_mode == "outcome_only":
            context_line = (
                "You have last meta-round outcomes for all agents, but no opponent code.\n"
            )
            reasoning_focus = (
                "Keep reasoning under 60 words, focusing on outcome patterns from the last meta-round.\n"
            )
        else:
            context_line = (
                "No opponent info is available; only your own last meta-round outcome is provided.\n"
            )
            reasoning_focus = (
                "Keep reasoning under 60 words, focusing on your own last outcome and survival.\n"
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
            
            f"LATEST METAROUND CONTEXT (YESTERDAY):\n{history_block}\n\n"

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

            "10. High-Level Game Theory Example:\n"
            "def get_bid(day_context, my_status, opponents_status):\n"
            "    DAILY_SALARY = 70\n"
            "    alive_opponents = [o for o in opponents_status.values() if o['alive']]\n"
            "    if not alive_opponents:\n"
            "        return min(my_status['budget'], DAILY_SALARY * 0.4)\n\n"
            "    # 1. Look at yesterday's situation\n"
            "    yesterday_bids = []\n"
            "    for opp in alive_opponents:\n"
            "        last_bid = opp.get('last_bid', 0.0)\n"
            "        if last_bid is not None:\n"
            "            try:\n"
            "                yesterday_bids.append(float(last_bid))\n"
            "            except Exception:\n"
            "                pass\n\n"
            "    # 2. Decision logic based on yesterday's highest pressure\n"
            "    if yesterday_bids:\n"
            "        highest_prev_bid = max(yesterday_bids)\n"
            "        if highest_prev_bid >= DAILY_SALARY * 0.85:\n"
            "            if my_status['hp'] > 3:\n"
            "                return min(my_status['budget'], DAILY_SALARY * 0.3)\n"
            "            return min(my_status['budget'], DAILY_SALARY * 0.95)\n"
            "        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))\n\n"
            "    if my_status['hp'] <= 2:\n"
            "        return min(my_status['budget'], DAILY_SALARY * 0.9)\n"
            "    return min(my_status['budget'], DAILY_SALARY * 0.55)\n\n"

            "11. DO NOT use undefined variables.\n"
            "12. DO NOT use markdown code fences (```).\n\n"

            f"Agent Constants:\n"
            f"WATER_REQ = {agent_profile['water_requirement']}\n"
            f"DAILY_SALARY = {agent_profile['daily_salary']}\n"
            f"MAX_SUPPLY = 25\n"
            f"MIN_SUPPLY = 15\n\n"

            f"{reasoning_focus}"
            "Output valid JSON only.\n"
            "Output format:\n"
            "{\n"
            '  "reasoning": "your short game-theoretic analysis",\n'
            '  "code": "def get_bid(...)"\n'
            "}"
        )