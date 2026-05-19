# ============================================================
# Experiment: exp_116
# Agent: Alex
# Source: exp_116
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    total_alive = 1 + len(alive_opponents)
    affordable_cap = max(0.0, min(float(budget), float(DAILY_SALARY)))

    if affordable_cap <= 0:
        return 0.0

    units_available = float(supply) / float(WATER_REQ)
    scarcity = total_alive - units_available

    prev_bids = []
    desperate_opp = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            desperate_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    emergency = hp <= 2 or no_water_days >= 1
    critical = hp <= 1 or no_water_days >= 2

    if critical:
        bid = min(affordable_cap, DAILY_SALARY * 0.98)
        return float(max(0.0, bid))

    if emergency:
        target = max(DAILY_SALARY * 0.82, highest_prev + 2.0)
        bid = min(affordable_cap, target)
        return float(max(0.0, bid))

    if len(alive_opponents) == 0:
        return float(min(affordable_cap, DAILY_SALARY * 0.35))

    if scarcity <= 0:
        base = DAILY_SALARY * 0.34
    elif scarcity <= 0.5:
        base = DAILY_SALARY * 0.46
    elif scarcity <= 1.0:
        base = DAILY_SALARY * 0.58
    else:
        base = DAILY_SALARY * 0.68

    if highest_prev >= DAILY_SALARY * 0.9:
        if hp >= 4 and no_water_days == 0:
            bid = min(affordable_cap, DAILY_SALARY * 0.28)
        else:
            bid = min(affordable_cap, DAILY_SALARY * 0.88)
        return float(max(0.0, bid))

    if prev_bids:
        if highest_prev < DAILY_SALARY * 0.75:
            base = max(base, highest_prev + 1.5)
        else:
            base = max(base, avg_prev + 1.0)

    if desperate_opp >= max(1, len(alive_opponents) // 2):
        base += 4.0

    if budget < DAILY_SALARY * 2:
        base = min(base, DAILY_SALARY * 0.62)

    bid = min(affordable_cap, base)
    return float(max(0.0, bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    dangerous_prev.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    tight_supply = supply <= 16.0
    ample_supply = supply >= 22.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    danger_prev = max(dangerous_prev) if dangerous_prev else highest_prev

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    elif hp <= 6:
        urgency += 1
    if no_water_days >= 2:
        urgency += 3
    elif no_water_days >= 1:
        urgency += 2
    if tight_supply:
        urgency += 2
    elif not ample_supply:
        urgency += 1

    if day <= 2 and hp >= 8 and not tight_supply:
        base = 24.0 if ample_supply else 32.0
    else:
        if urgency >= 6:
            base = max(63.0, danger_prev + 2.0)
        elif urgency >= 4:
            base = max(52.0, highest_prev + 1.5)
        elif urgency >= 2:
            if highest_prev >= 90.0:
                base = 34.0 if hp > 4 else 58.0
            elif highest_prev >= 60.0:
                base = max(40.0, highest_prev - 6.0)
            else:
                base = max(30.0, highest_prev + 1.0)
        else:
            if ample_supply:
                base = 20.0
            elif highest_prev >= 100.0:
                base = 22.0
            else:
                base = max(24.0, highest_prev * 0.55)

    if budget < DAILY_SALARY:
        base = min(base, budget * 0.92)

    if hp <= 2 or no_water_days >= 2:
        base = max(base, min(budget, 66.0))

    bid = min(budget, max(0.0, base))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_pressure = 0
    weak_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 90:
                    rich_pressure += 1
                if float(bid) <= 35:
                    weak_count += 1

    if not alive:
        return max(0.0, min(float(budget), 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    emergency = False
    if hp <= 3 or no_water_days >= 2:
        emergency = True

    if emergency:
        bid = max(72.0, highest_prev + 3.0)
        if scarcity == 2:
            bid = max(bid, 96.0)
        elif scarcity == 1:
            bid = max(bid, 84.0)
        return max(0.0, min(float(budget), bid))

    if hp >= 8 and no_water_days == 0 and supply >= 22 and rich_pressure >= 1:
        return max(0.0, min(float(budget), 16.0))

    if scarcity == 2:
        if highest_prev >= 100:
            bid = 68.0 if hp >= 7 else 88.0
        else:
            bid = max(60.0, highest_prev + 2.5)
    elif scarcity == 1:
        if highest_prev >= 100:
            bid = 52.0 if hp >= 7 else 74.0
        else:
            bid = max(42.0, avg_prev + 3.0)
    else:
        if rich_pressure >= 2:
            bid = 24.0
        elif highest_prev > 80:
            bid = 28.0
        else:
            bid = max(26.0, min(44.0, avg_prev + 1.5))

    if hp <= 5:
        bid += 12.0
    elif hp <= 7:
        bid += 6.0

    if no_water_days == 1:
        bid += 10.0

    if day >= 8 and hp >= 7:
        bid -= 4.0

    if weak_count >= 2 and scarcity == 0:
        bid -= 4.0

    bid = max(0.0, min(float(budget), bid))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_opp_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_opp_bids.append(float(bid))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    if not alive_opponents:
        base = DAILY_SALARY * (0.22 + 0.18 * scarcity)
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, round(base, 2))))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else highest_prev

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 2
    if supply <= 17:
        danger += 2
    elif supply <= 19:
        danger += 1

    remaining_days = max(1, 10 - day + 1)
    reserve_target = DAILY_SALARY * 0.45 * remaining_days

    if danger >= 5:
        target = max(DAILY_SALARY * 0.92, urgent_prev + 2.5)
    elif danger >= 3:
        target = max(DAILY_SALARY * (0.72 + 0.12 * scarcity), highest_prev + 1.25)
    else:
        if supply >= 23 and hp >= 7 and no_water_days == 0:
            target = DAILY_SALARY * 0.28
        elif supply >= 20:
            target = DAILY_SALARY * (0.38 + 0.08 * scarcity)
        else:
            target = DAILY_SALARY * (0.5 + 0.12 * scarcity)
        if highest_prev > 0 and supply <= 18:
            target = max(target, highest_prev + 0.75)

    if budget < reserve_target and danger <= 2:
        target = min(target, DAILY_SALARY * 0.42)

    if hp <= 1 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.98)

    bid = max(0.0, min(float(budget), round(target, 2)))
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    yesterday_bids = []
    rich_pressure = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_pressure += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days >= 1:
        urgency += 0.35

    urgency += scarcity * 0.7

    if day >= 8:
        urgency += 0.2

    if highest_prev >= 120:
        market_mode = 'irrational_high'
    elif highest_prev >= 80:
        market_mode = 'high'
    elif highest_prev >= 45:
        market_mode = 'medium'
    else:
        market_mode = 'low'

    if urgency >= 1.4:
        bid = 118.0 + 18.0 * scarcity
        if rich_pressure >= 2:
            bid += 8.0
    elif urgency >= 0.8:
        if market_mode == 'irrational_high':
            bid = 86.0 + 10.0 * scarcity
        elif market_mode == 'high':
            bid = max(72.0, min(98.0, avg_prev + 4.0))
        elif market_mode == 'medium':
            bid = max(58.0, highest_prev + 2.5)
        else:
            bid = 52.0 + 10.0 * scarcity
    else:
        if market_mode == 'irrational_high':
            bid = 24.0 + 8.0 * scarcity
        elif market_mode == 'high':
            bid = 34.0 + 8.0 * scarcity
        elif market_mode == 'medium':
            bid = 42.0 + 6.0 * scarcity
        else:
            bid = 38.0 + 5.0 * scarcity

    if supply <= 16:
        bid += 8.0
    elif supply >= 23 and urgency < 0.8:
        bid -= 6.0

    safe_cap = budget
    if hp > 6 and no_water_days == 0:
        safe_cap = min(safe_cap, budget * 0.28 + DAILY_SALARY * 0.35)
    elif hp > 4:
        safe_cap = min(safe_cap, budget * 0.42 + DAILY_SALARY * 0.5)
    else:
        safe_cap = min(safe_cap, budget * 0.75 + DAILY_SALARY * 0.8)

    if day >= 9 and hp <= 4:
        safe_cap = budget

    bid = min(bid, safe_cap)
    bid = max(0.0, min(budget, bid))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_bids = []
    weak_bids = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 100:
                    strong_bids.append(float(bid))
                else:
                    weak_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgent = hp <= 3 or no_water_days >= 2
    semi_urgent = hp <= 5 or no_water_days >= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    weak_anchor = max(weak_bids) if weak_bids else 55.0
    strong_count = len(strong_bids)

    if urgent:
        bid = 110.0 + 25.0 * scarcity
        if highest_prev > bid:
            bid = highest_prev + 3.0
    elif supply >= 22:
        bid = 42.0
        if weak_bids:
            bid = min(65.0, weak_anchor + 2.0)
    elif supply >= 19:
        bid = 58.0 + 8.0 * scarcity
        if weak_bids:
            bid = max(bid, weak_anchor + 2.5)
        if strong_count >= 2 and semi_urgent:
            bid = max(bid, 95.0)
    else:
        bid = 68.0 + 14.0 * scarcity
        if weak_bids:
            bid = max(bid, weak_anchor + 3.0)
        if strong_count >= 2:
            bid = max(bid, 88.0 if not semi_urgent else 108.0)

    if day >= 8:
        bid += 6.0
    if hp >= 8 and supply >= 22 and strong_count >= 2:
        bid -= 8.0
    if budget < 120:
        bid = min(bid, 0.55 * budget)
    elif budget < 200:
        bid = min(bid, 0.7 * budget)

    bid = max(0.0, min(float(budget), bid))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 55.0)
        return min(budget, 18.0)

    total_players = 1 + len(alive_opponents)
    total_req = WATER_REQ
    for req in opp_requirements:
        total_req += req

    scarcity_ratio = float(total_req) / max(1.0, float(supply))
    my_share = float(supply) / max(1.0, float(total_players))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    emergency = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1
    abundant = my_share >= WATER_REQ * 1.2
    very_scarce = scarcity_ratio >= 3.0 or supply <= 16
    scarce = scarcity_ratio >= 2.4 or supply <= 18

    if emergency:
        target = max(92.0, highest_prev + 3.0)
        if very_scarce:
            target = max(target, 108.0)
        return min(budget, target)

    if abundant and hp >= 6 and no_water_days == 0:
        target = 16.0
        if highest_prev < 40:
            target = 14.0
        return min(budget, target)

    if very_scarce:
        if highest_prev >= 110:
            target = 62.0 if hp >= 7 else 98.0
        elif highest_prev >= 90:
            target = highest_prev + 2.5 if pressured else 58.0
        else:
            target = 72.0 if pressured else 48.0
        return min(budget, target)

    if scarce:
        if highest_prev >= 100:
            target = 54.0 if hp >= 7 else 88.0
        elif highest_prev >= 75:
            target = highest_prev + 1.5 if pressured else 46.0
        else:
            target = max(40.0, avg_prev * 0.7)
        return min(budget, target)

    if highest_prev >= 100:
        target = 36.0 if hp >= 6 else 70.0
    elif highest_prev >= 80:
        target = 42.0 if hp >= 6 else highest_prev + 1.0
    elif highest_prev >= 50:
        target = highest_prev + 1.2 if pressured else 38.0
    else:
        target = 30.0 if hp >= 7 else 44.0

    return min(budget, target)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    rich_threat = 0.0
    urgent_opp = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('budget', 0) > rich_threat:
            rich_threat = float(opp.get('budget', 0))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (25.0 - supply) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = 20.0 + 10.0 * scarcity

    if supply >= 22:
        base -= 6.0
    elif supply <= 17:
        base += 10.0

    if highest_prev >= 120.0:
        base -= 4.0
    elif highest_prev >= 90.0:
        base += 3.0
    else:
        base += 1.5

    if avg_prev >= 80.0:
        base += 2.0

    if rich_threat >= 250.0:
        base -= 2.0

    base += 3.0 * urgent_opp

    if hp <= 2 or no_water >= 2:
        bid = max(base, 92.0 + 8.0 * scarcity)
    elif hp <= 4 or no_water >= 1:
        bid = max(base, 58.0 + 10.0 * scarcity)
    else:
        bid = base

    if day >= 8 and hp > 4 and no_water == 0:
        bid -= 4.0

    if budget < 60:
        bid = min(bid, budget)
    elif budget < 120:
        bid = min(bid, 0.72 * budget)
    else:
        bid = min(bid, 0.38 * budget + 8.0)

    floor_bid = 8.0 if hp > 4 and no_water == 0 else 18.0
    bid = max(floor_bid, bid)
    bid = min(budget, bid)

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_opp_bids.append(float(bid))

    if not alive:
        return max(0.0, min(float(budget), DAILY_SALARY * 0.2))

    expected_winners = max(1, int(supply // WATER_REQ))
    scarcity = expected_winners <= 1

    top_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.75
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.7
    urgent_top = max(urgent_opp_bids) if urgent_opp_bids else top_prev

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 2
    if scarcity:
        danger += 2
    if day >= 8:
        danger += 1

    if budget <= 0:
        return 0.0

    if danger >= 6:
        target = max(DAILY_SALARY * 1.15, urgent_top + 2.5)
    elif danger >= 4:
        target = max(DAILY_SALARY * 0.92, top_prev + 1.25)
    elif danger >= 2:
        if scarcity:
            target = max(DAILY_SALARY * 0.72, avg_prev * 0.92)
        else:
            target = max(DAILY_SALARY * 0.48, avg_prev * 0.72)
    else:
        if scarcity:
            target = max(DAILY_SALARY * 0.38, avg_prev * 0.55)
        else:
            target = DAILY_SALARY * 0.22

    if supply >= 24:
        target *= 0.72
    elif supply >= 20:
        target *= 0.88
    elif supply <= 16:
        target *= 1.08

    if hp >= 8 and no_water_days == 0 and not scarcity:
        target *= 0.8

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 70.0
    affordable = max(0.0, float(budget) - reserve_floor)
    if danger >= 4:
        affordable = float(budget)

    bid = min(float(budget), target)
    if affordable > 0:
        bid = min(bid, affordable) if danger < 4 else min(float(budget), target)
    else:
        bid = min(float(budget), DAILY_SALARY * 0.15) if danger < 4 else min(float(budget), target)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(float(budget), DAILY_SALARY * 0.95))

    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    dangerous_bids = []
    distressed_count = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive_opps.append(opp)
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 85:
                dangerous_bids.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            distressed_count += 1
        if prev:
            status = prev.get('status')
            hp_after = prev.get('hp_after')
            if status == 'failed' or (hp_after is not None and hp_after <= 2):
                distressed_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 20.0))

    scarcity = max(0.0, min(1.0, (20.0 - supply) / 5.0))
    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 3 or no_water_days >= 2
    semi_urgent = hp <= 5 or no_water_days >= 1

    if urgent:
        bid = max(96.0, highest_prev + 1.5)
        if supply <= 17:
            bid = max(bid, 101.0)
        return float(min(budget, bid))

    if semi_urgent:
        bid = 72.0 + 18.0 * scarcity
        if dangerous_bids:
            bid = max(bid, min(99.0, highest_prev + 0.8))
        return float(min(budget, bid))

    if supply >= 23 and distressed_count >= 2:
        return float(min(budget, 12.0))

    if supply >= 21:
        if highest_prev >= 95:
            bid = 24.0
        else:
            bid = max(22.0, avg_prev * 0.35)
        return float(min(budget, bid))

    if supply >= 19:
        if highest_prev >= 95:
            bid = 34.0
        else:
            bid = max(30.0, avg_prev * 0.45)
        return float(min(budget, bid))

    if supply >= 17:
        if dangerous_bids:
            bid = 58.0
        else:
            bid = max(46.0, avg_prev * 0.6)
        if day >= 8:
            bid += 6.0
        return float(min(budget, bid))

    bid = 74.0
    if dangerous_bids:
        bid = max(bid, min(92.0, highest_prev * 0.9))
    if day >= 8:
        bid += 8.0
    return float(min(budget, bid))
"""
