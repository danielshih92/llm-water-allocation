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
        self_previous_code: str = "",
        history: Optional[Dict[str, Any]] = None,
        opponent_info_mode: Optional[str] = None,
        show_opponent_code: Optional[bool] = None,
    ) -> str:

        history_payload: Dict[str, Any] = {}
        previous_final_results: Dict[str, Any] = {}
        if history and isinstance(history, dict):
            last_meta_round = history.get("last_meta_round")
            if last_meta_round is not None:
                history_payload["previous_meta_round_index"] = last_meta_round

            agent_summaries = history.get("agent_summaries")
            if isinstance(agent_summaries, dict):
                for agent_id in sorted(agent_summaries):
                    summary = agent_summaries.get(agent_id)
                    if not isinstance(summary, dict):
                        continue

                    previous_final_results[agent_id] = {
                        "valid": bool(summary.get("valid", False)),
                        "survival_days": summary.get("survival_days"),
                    }

        
        if show_opponent_code is None:
            show_opponent_code = config.REVEAL_OPPONENT_CODE

        opponent_info_mode = normalize_opponent_info_mode(opponent_info_mode)

        state_block = json.dumps(game_state or {}, indent=2)      
        profile_block = json.dumps(agent_profile or {}, indent=2)  
        players_block = json.dumps(
            game_state.get("players", []) if isinstance(game_state, dict) else [],
            indent=2,
        )

        supply_range = game_state.get("supply_range", [10, 20]) if isinstance(game_state, dict) else [10, 20]
        episode_days = game_state.get("episode_days", 20) if isinstance(game_state, dict) else 20

        try:
            min_supply = int(supply_range[0])
            max_supply = int(supply_range[1])
        except Exception:
            min_supply = 10
            max_supply = 20

        try:
            episode_days = int(episode_days)
        except Exception:
            episode_days = 20

        if episode_days <= 0:
            episode_days = 20

        opponent_code_section = ""

        if opponent_info_mode == "full_code_access" and show_opponent_code and opponent_code:
            opponent_block = json.dumps(opponent_code or {}, indent=2)

            opponent_code_section = (
                f"=== PREVIOUS META-ROUND OPPONENT STRATEGY CODE ===\n"
                f"Historical code only (from previous meta-round), not current-day hidden bids.\n"
                f"Use it to infer robust tendencies and risks; avoid brittle overfitting.\n"
                f"{opponent_block}\n\n"
            )

        self_previous_code_section = ""
        if self_previous_code:
            self_previous_code_section = (
                f"=== YOUR PREVIOUS META-ROUND STRATEGY CODE ===\n"
                f"Historical code only (from your own previous meta-round submission), not current-day hidden bids.\n"
                f"Use it to preserve useful structure when appropriate, fix weaknesses, and make substantial changes "
                f"when the prior strategy appears brittle or poorly calibrated.\n"
                f"{self_previous_code}\n\n"
            )

        latest_meta_context_section = ""
        if history_payload:
            latest_meta_context_section = (
                f"LATEST METAROUND INDEX (NON-OUTCOME METADATA):\n"
                f"{json.dumps(history_payload, indent=2)}\n\n"
            )

        previous_final_results_section = ""
        if previous_final_results:
            previous_final_results_section = (
                f"=== LAST META-ROUND FINAL RESULTS ===\n"
                f"The following results are from the last meta-round.\n"
                f"Each survival_days value is the number of simulation days that agent survived.\n"
                f"{json.dumps(previous_final_results, indent=2)}\n\n"
            )

        all_agents_static_section = ""
        if isinstance(game_state, dict) and game_state.get("players"):
            all_agents_static_section = (
                "ALL AGENTS INITIAL STATIC PROFILE (KNOWN BEFORE SIMULATION):\n"
                "Public setup constants: agent_id, water_requirement, daily_salary.\n"
                f"{players_block}\n\n"
            )

        intro_line = (
            "You are participating in the Water Allocation Challenge programmatic game.\n"
            f"Episode length is {episode_days} simulation days per meta-round; your submission is strategy code only.\n"
            "Daily supply is randomly sampled in [MIN_SUPPLY, MAX_SUPPLY].\n"
            "Initial state: HP=8, max HP=10, no_water_days=1.\n"
            "Each day: alive agents get salary, then submit simultaneous bids (current-day opponent bids are hidden).\n"
            "Allocation rule: a winner must fit remaining supply by water_requirement.\n"
            "Winner update: HP += 2 (cap 10), budget -= bid, no_water_days = 1.\n"
            "Non-winner update: HP -= no_water_days, then no_water_days += 1.\n"
            "Death rule: HP <= 0 means dead. Tie-break at same bid: lower water_requirement first.\n"
        )

        has_last_meta_round_context = bool(
            self_previous_code_section
            or opponent_code_section
            or previous_final_results_section
            or latest_meta_context_section
        )

        if opponent_info_mode == "full_code_access":
            if has_last_meta_round_context:
                context_line = (
                    "Last meta-round strategy code and final survival results may be provided below. "
                    "Assume other agents may also adapt across meta-rounds; avoid one-step exploitation.\n"
                )
            else:
                context_line = (
                    "No last meta-round information is available yet. Generate an initial robust "
                    "survival-oriented strategy.\n"
                )
            reasoning_focus = (
                "Keep reasoning under 100 words. Focus on improving your previous strategy, robust interpretation "
                "of opponent code and prior survival results, calibrated bidding, budget discipline, and avoiding "
                "unnecessary overbidding.\n"
            )
        else:
            if has_last_meta_round_context:
                context_line = (
                    "Last meta-round self strategy code and final survival results may be provided below, alongside "
                    "your profile, current meta-round state, game rules, and runtime opponents_status inside get_bid.\n"
                )
            else:
                context_line = (
                    "No last meta-round information is available yet. Generate an initial robust "
                    "survival-oriented strategy using your profile, current meta-round state, game rules, "
                    "and runtime opponents_status inside get_bid.\n"
                )
            reasoning_focus = (
                "Keep reasoning under 60 words. Focus on improving your previous strategy, interpreting prior "
                "survival results, budget-safe reasoning, calibrated risk control, and survival.\n"
            )

        return (
            # ============================================================
            # Reasoning Prompt
            # ============================================================
            f"{intro_line}"
            f"{context_line}"
            "Analyze the available context to generate a robust survival-oriented bidding strategy.\n\n"

            f"Your Profile:\n{profile_block}\n\n"
            f"Current Meta-Round State:\n{state_block}\n\n"
            f"{all_agents_static_section}"
            f"{self_previous_code_section}"
            f"{opponent_code_section}"
            f"{previous_final_results_section}"
            f"{latest_meta_context_section}"

            # ============================================================
            # Code Prompt
            # ============================================================
            "After brief reasoning, generate executable Python code.\n\n"

            "CRITICAL PYTHON RULES:\n"
            "1. Function MUST be exactly: def get_bid(day_context, my_status, opponents_status):\n"
            "2. day_context format:\n"
            f"   - day_context['day']: int, current simulation day index (1..{episode_days}).\n"
            "   - day_context['supply']: float, current day total water supply.\n"
            "3. my_status format:\n"
            "   - my_status['hp']: int, current HP.\n"
            "   - my_status['budget']: float, current budget after salary accrual.\n"
            "   - my_status['no_water_days']: int, current no-water counter for today's failure penalty.\n"
            "4. opponents_status format:\n"
            "   - Dictionary keyed by opponent agent_id.\n"
            "   - Each opponent record may include these fields, but validation tests can omit optional fields:\n"
            "     ['agent_id', 'hp', 'budget', 'no_water_days', 'alive', 'water_requirement', 'daily_salary', 'last_bid', 'last_status', 'last_hp_after', 'last_budget_after', 'trace_history'].\n"
            "   - Always use .get(..., fallback) for opponent fields; never assume optional fields exist.\n"
            "5. Field semantics and value types:\n"
            "   - alive: truth value.\n"
            "   - last_bid: float, opponent bid from previous simulation day (or 0.0 if unavailable).\n"
            "   - last_status: text value or None. Typical values are 'alive' or 'dead'.\n"
            "   - last_hp_after: int or null, opponent HP after previous day resolution.\n"
            "   - last_budget_after: float or null, opponent budget after previous day resolution.\n"
            "6. trace_history format and meaning:\n"
            "   - A compact list containing the opponent's recent up-to-2 resolved day records.\n"
            "   - Each record has ['day', 'bid', 'supply', 'hp_after', 'budget_after', 'status'].\n"
            "   - status is a string: 'alive' or 'dead'.\n"
            "7. trace_history extraction example (one opponent):\n"
            "   trace_history = [\n"
            "     {'day': 4, 'bid': 42.0, 'supply': 16.0, 'hp_after': 8, 'budget_after': 120.0, 'status': 'alive'},\n"
            "     {'day': 5, 'bid': 30.0, 'supply': 11.0, 'hp_after': 7, 'budget_after': 160.0, 'status': 'alive'}\n"
            "   ]\n"
            "   Use trace_history[-1]['bid'] for the most recent resolved-day bid.\n"
            "8. Bidding is simultaneous. Current-day opponent bids are hidden.\n\n"
            "9. RESTRICTED PYTHON RUNTIME:\n"
            "   - Available builtins only: min, max, abs, round, float, int, len, sum, any, all, isinstance, dict, list, tuple, range, sorted, enumerate.\n"
            "   - The math module is available as math, but imports are forbidden.\n"
            "   - Do NOT use: bool, str, type, hasattr, set, zip, map, filter, reversed, open, eval, exec, compile, globals, locals, vars.\n"
            "   - Do NOT use import/from, file/network access, dunder names, or attributes containing double underscores.\n"
            "   - Do NOT use float('inf'), float('-inf'), NaN, or infinity checks that require unavailable helpers.\n\n"
            "10. CRITICAL INDEX RULE: In Python, list/array indices MUST be integers. Since day_context['supply'] is passed as a float (e.g., 19.0), any mathematical operations like floor division (e.g., supply // WATER_REQ) will produce a FLOAT (e.g., 1.0). You MUST explicitly wrap ALL list indices or subscript selectors with int() (e.g., my_list[int(target_index)]) to strictly prevent float index RuntimeErrors.\n\n"
            "11. FINAL BID RULE: The returned value must always be a finite float in [0.0, budget]. If you apply any minimum bid or urgency floor, clamp to budget AFTER that floor.\n"
            "   Safe final pattern:\n"
            "   bid = max(0.0, bid)\n"
            "   bid = min(budget, bid)\n"
            "   return float(bid)\n\n"

            "12. Minimal Safe Data-Access Example only. This demonstrates robust extraction of fields and types. Do NOT copy it as the final strategy.\n"
            "def get_bid(day_context, my_status, opponents_status):\n"
            "    day = int(day_context.get('day', 1))\n"
            "    supply = float(day_context.get('supply', 0.0))\n"
            "    hp = int(my_status.get('hp', 0))\n"
            "    budget = float(my_status.get('budget', 0.0))\n"
            "    no_water_days = int(my_status.get('no_water_days', 0))\n\n"
            "    last_bids = []\n"
            "    alive_opponents = 0\n"
            "    for opp_id, opp in (opponents_status or {}).items():\n"
            "        if opp.get('alive', False):\n"
            "            alive_opponents += 1\n"
            "        last_bid = float(opp.get('last_bid', 0.0) or 0.0)\n"
            "        last_bids.append(last_bid)\n"
            "        trace = opp.get('trace_history', [])\n"
            "        if trace:\n"
            "            recent = trace[-1]\n"
            "            recent_status = recent.get('status')  # 'alive' or 'dead'\n"
            "            _ = recent_status\n\n"
            "    baseline = 0.0\n"
            "    if budget > 0:\n"
            "        baseline = min(budget, max(0.0, budget * 0.4))\n"
            "    return float(max(0.0, min(budget, baseline)))\n\n"

            "13. DO NOT use undefined variables.\n"
            "14. DO NOT use markdown code fences (```).\n\n"

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
