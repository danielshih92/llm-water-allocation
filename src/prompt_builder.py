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
    ) -> str:

        # ============================================================
        # 核心優化：智慧識別並提取精簡的上一輪對手戰績狀態
        # ============================================================
        filtered_history = {}
        if history and isinstance(history, dict):
            # 🛠️ 修正安全隱患：如果已經是 run.py 包裝好的單輪摘要結構，直接精準提取內層對手字典
            if "opponent_summaries" in history:
                filtered_history = history["opponent_summaries"]
            else:
                # 保持向下相容：如果未來傳入全域歷史大池 (all_meta_history) 也能安全解析
                keys = list(history.keys())
                if keys:
                    try:
                        latest_key = max(
                            keys, 
                            key=lambda x: tuple(int(s) for s in re.findall(r'\d+', x)) if re.findall(r'\d+', x) else (0,)
                        )
                        data = history[latest_key]
                        # 檢查內層是否帶有 summary 殼
                        if isinstance(data, dict) and "summary" in data:
                            filtered_history = data["summary"]
                        else:
                            filtered_history = data
                    except Exception:
                        latest_key = keys[-1]
                        filtered_history = history[latest_key]

        # 將原本臃腫的歷史，替換為只有前一天數據的乾淨區塊
        history_block = json.dumps(filtered_history, indent=2)
        state_block = json.dumps(game_state or {}, indent=2)      # 🌟 [補回] 格式化當前賽局狀態
        profile_block = json.dumps(agent_profile or {}, indent=2)  # 🌟 [補回] 格式化智慧體基本配置

        opponent_code_section = ""

        # 提供當前這一輪正在執行的對手原始碼
        if config.REVEAL_OPPONENT_CODE:
            opponent_block = json.dumps(opponent_code or {}, indent=2)

            opponent_code_section = (
                f"=== CRITICAL: OPPONENT SOURCE CODE ===\n"
                f"Below is the exact Python code currently used by your opponents in this meta-round.\n"
                f"Analyze it to find their tactical flaws:\n"
                f"{opponent_block}\n\n"
            )

        return (
            # ============================================================
            # Reasoning Prompt
            # ============================================================
            "You are participating in the Water Allocation Challenge programmatic game.\n"
            "Analyze the opponent source code and their active states to generate a winning bidding strategy.\n\n"

            f"Your Profile:\n{profile_block}\n\n"
            f"Current Meta-Round State:\n{state_block}\n\n"
            f"{opponent_code_section}"
            
            # 這裡現在只會倒進去「最新一輪」的歷史，其餘舊資料全部被丟棄
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
            "5. Each opponent state has: ['hp', 'budget', 'no_water_days', 'alive', 'water_requirement', 'daily_salary'].\n"
            "6. Each opponent also has 'previous_trace', containing their YESTERDAY behavior: "
            "['day', 'bid', 'supply', 'hp_after', 'budget_after', 'status', 'error'].\n"
            "7. DO NOT use 'recent_traces' or loop through long history. Only look at 'previous_trace' for immediate reaction.\n"
            "8. Bidding is simultaneous. Current-day opponent bids are hidden.\n\n"
            "9. CRITICAL INDEX RULE: In Python, list/array indices MUST be integers. Since day_context['supply'] is passed as a float (e.g., 19.0), any mathematical operations like floor division (e.g., supply // WATER_REQ) will produce a FLOAT (e.g., 1.0). You MUST explicitly wrap ALL list indices or subscript selectors with int() (e.g., my_list[int(target_index)]) to strictly prevent float index RuntimeErrors.\n\n"

            "10. High-Level Game Theory Example:\n"
            "def get_bid(day_context, my_status, opponents_status):\n"
            "    DAILY_SALARY = 70\n"
            "    alive_opponents = [o for o in opponents_status.values() if o['alive']]\n"
            "    if not alive_opponents:\n"
            "        return min(my_status['budget'], DAILY_SALARY * 0.4)\n\n"
            "    # 1. Look at yesterday's situation (Trace)\n"
            "    yesterday_bids = []\n"
            "    for opp in alive_opponents:\n"
            "        prev = opp.get('previous_trace', {})\n"
            "        if prev and prev.get('bid') is not None:\n"
            "            yesterday_bids.append(prev['bid'])\n\n"
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

            "Keep reasoning under 60 words, focusing only on how you exploit their YESTERDAY code/trace.\n"
            "Output valid JSON only.\n"
            "Output format:\n"
            "{\n"
            '  "reasoning": "your short game-theoretic analysis",\n'
            '  "code": "def get_bid(...)"\n'
            "}"
        )