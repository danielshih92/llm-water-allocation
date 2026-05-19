# ============================================================
# Experiment: exp_031
# Agent: Alex
# Source: exp_031
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0, min(budget, 18.0))

    players = len(alive) + 1
    units = max(1, int(supply // WATER_REQ))
    scarcity = players - units

    my_urgent = (hp <= 2) or (no_water >= 2)
    my_risky = (hp <= 4) or (no_water >= 1)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    if my_urgent:
        bid = max(58.0, highest_prev + 2.0)
    elif scarcity <= 0:
        bid = 16.0 if hp > 4 else 24.0
    elif scarcity == 1:
        bid = max(24.0, avg_prev + 1.0)
    else:
        bid = max(34.0, highest_prev + 1.5)

    if my_risky:
        bid += 10.0
    if urgent_opp >= units:
        bid += 6.0
    elif urgent_opp == 0 and scarcity <= 1:
        bid -= 4.0

    if budget < 25:
        bid = min(bid, budget)
    else:
        reserve = 0.0
        if hp > 4 and no_water == 0:
            reserve = 10.0
        elif hp > 2:
            reserve = 5.0
        bid = min(bid, max(0.0, budget - reserve))

    if budget <= 0:
        return 0.0
    return max(0.0, min(float(budget), float(bid)))
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = 18.0 if hp > 3 else 42.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_prev_bids = []
    weak_opp_count = 0
    rich_opp_count = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            prev_bids.append(bid)
            opp_hp = float(opp.get('hp', 0))
            opp_nwd = int(opp.get('no_water_days', 0))
            if opp_hp <= 3 or opp_nwd >= 1:
                urgent_prev_bids.append(bid)
        if float(opp.get('hp', 0)) <= 3:
            weak_opp_count += 1
        if float(opp.get('budget', 0)) >= 400:
            rich_opp_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_high = max(urgent_prev_bids) if urgent_prev_bids else highest_prev

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    low_supply = supply <= 17.0
    high_supply = supply >= 22.0

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

    if day >= 8:
        danger += 1

    if danger >= 5:
        bid = max(urgent_high + 3.0, 0.92 * DAILY_SALARY)
        if low_supply:
            bid = max(bid, highest_prev + 6.0)
        return float(max(0.0, min(budget, bid)))

    if danger >= 3:
        bid = max(urgent_high + 2.0, 0.72 * DAILY_SALARY)
        if low_supply:
            bid = max(bid, highest_prev + 4.0)
        if high_supply:
            bid *= 0.9
        return float(max(0.0, min(budget, bid)))

    if low_supply:
        if highest_prev >= 120.0:
            bid = min(highest_prev + 1.5, 0.78 * DAILY_SALARY)
        else:
            bid = 0.6 * DAILY_SALARY
        if rich_opp_count >= 2:
            bid += 4.0
        return float(max(0.0, min(budget, bid)))

    if high_supply:
        bid = 0.24 * DAILY_SALARY
        if weak_opp_count >= 2:
            bid = 0.18 * DAILY_SALARY
        return float(max(0.0, min(budget, bid)))

    bid = 0.42 * DAILY_SALARY
    if highest_prev > 0:
        target = highest_prev * 0.42
        bid = max(bid, min(target, 0.58 * DAILY_SALARY))
    if rich_opp_count >= 2:
        bid += 3.0

    return float(max(0.0, min(budget, bid)))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_budgets = []
    urgent_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    rich_opp = max(opp_budgets) if opp_budgets else 0.0

    if supply >= 23:
        base = 18.0
    elif supply >= 20:
        base = 28.0
    elif supply >= 17:
        base = 42.0
    else:
        base = 58.0

    if highest_prev > 0:
        if highest_prev >= 150:
            base = min(base, 34.0) if hp >= 5 and no_water_days == 0 else max(base, 78.0)
        elif highest_prev >= 110:
            base = max(base, min(highest_prev * 0.58, 72.0))
        else:
            base = max(base, min(highest_prev + 3.0, 68.0))

    if urgent_opp >= 2 and hp >= 5 and no_water_days == 0:
        base *= 0.88

    if rich_opp > 500 and supply <= 18:
        base += 8.0

    if hp <= 2:
        base = max(base, 92.0)
    elif hp <= 4:
        base = max(base, 74.0)

    if no_water_days >= 2:
        base = max(base, 120.0)
    elif no_water_days >= 1:
        base = max(base, 88.0)

    if day >= 8:
        if hp <= 4 or no_water_days >= 1:
            base += 12.0
        else:
            base += 4.0

    if budget < 60:
        base = min(base, budget)
    elif budget < 120:
        base = min(base, max(35.0, budget * 0.72))
    else:
        base = min(base, budget * 0.9)

    bid = max(0.0, min(budget, base))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    eric_bid = None
    cindy_bid = None

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((oid, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                low_id = str(oid).lower()
                if low_id == 'eric':
                    eric_bid = bid
                elif low_id == 'cindy':
                    cindy_bid = bid

    if budget <= 0:
        return 0.0

    if not alive_opps:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    slots = supply / float(WATER_REQ)
    many_slots = slots >= 2.0
    tight_supply = supply <= 17

    if eric_bid is None:
        eric_bid = 64.0
    if cindy_bid is None:
        cindy_bid = 108.0

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water >= 1:
        danger += 2
    if no_water >= 2:
        danger += 2
    if tight_supply:
        danger += 1
    if day >= 8:
        danger += 1

    if danger >= 4:
        target = max(eric_bid + 4.0, DAILY_SALARY * 0.95)
        if tight_supply:
            target = max(target, min(cindy_bid * 0.92, DAILY_SALARY * 1.45))
    elif danger >= 2:
        if many_slots:
            target = max(48.0, eric_bid - 6.0)
        else:
            target = max(58.0, eric_bid + 2.0)
    else:
        if many_slots:
            target = 34.0
        else:
            target = 52.0

    if cindy_bid > 120 and danger < 4:
        target = min(target, eric_bid + 3.0)

    if hp <= 2:
        target = max(target, DAILY_SALARY * 1.05)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.9)

    if budget < target:
        if hp <= 3 or no_water >= 1:
            return float(budget)
        return float(min(budget, max(0.0, target * 0.75)))

    return float(min(budget, target))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_budgets = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0
    richest_opp = max(opp_budgets) if opp_budgets else 0

    supply_tight = (supply <= 17)
    supply_loose = (supply >= 22)
    urgent = (hp <= 4 or no_water_days >= 1)
    critical = (hp <= 2 or no_water_days >= 2)

    if critical:
        bid = max(92.0, highest_prev + 2.0)
        return max(0, min(budget, bid))

    if urgent:
        if supply_tight:
            bid = max(78.0, min(highest_prev + 2.0, 108.0))
        else:
            bid = max(62.0, min(avg_prev + 3.0, 92.0))
        return max(0, min(budget, bid))

    if supply_loose:
        bid = 24.0
        if highest_prev < 40:
            bid = 20.0
        if budget < 140:
            bid = 16.0
        return max(0, min(budget, bid))

    if supply_tight:
        if highest_prev >= 140:
            bid = 58.0
        elif highest_prev >= 110:
            bid = 66.0
        else:
            bid = max(60.0, highest_prev + 1.5)
        if richest_opp < 120:
            bid += 6.0
        return max(0, min(budget, bid))

    bid = 42.0
    if avg_prev > 100:
        bid = 48.0
    elif avg_prev < 60:
        bid = 36.0

    if day >= 8 and hp >= 6:
        bid -= 4.0
    if budget < 100:
        bid -= 6.0

    return max(0, min(budget, bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return max(0.0, float(bid))

    yesterday_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 500:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev.get('bid', 0.0)))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    units = supply / WATER_REQ
    very_tight = units < 1.45
    tight = units < 1.7
    comfortable = units >= 1.9

    survival_mode = hp <= 3 or no_water >= 1
    danger_mode = hp <= 2 or no_water >= 2

    if danger_mode:
        base = DAILY_SALARY * 1.28
    elif survival_mode:
        base = DAILY_SALARY * 1.0
    elif very_tight:
        base = DAILY_SALARY * 0.82
    elif tight:
        base = DAILY_SALARY * 0.62
    elif comfortable:
        base = DAILY_SALARY * 0.38
    else:
        base = DAILY_SALARY * 0.5

    if highest_prev >= 120:
        if survival_mode or very_tight:
            base = max(base, min(150.0, highest_prev + 2.0))
        else:
            base = min(base, DAILY_SALARY * 0.42)
    elif highest_prev >= 80:
        if survival_mode:
            base = max(base, highest_prev + 1.5)
        else:
            base = max(base, avg_prev * 0.72)
    elif highest_prev > 0:
        if tight or survival_mode:
            base = max(base, highest_prev + 1.0)
        else:
            base = max(base, avg_prev * 0.9)

    if rich_count >= 1 and not survival_mode and not very_tight:
        base *= 0.88
    if desperate_count >= 2 and (tight or survival_mode):
        base *= 1.12

    if day >= 8 and hp >= 5 and no_water == 0 and not tight:
        base *= 0.9

    if budget < DAILY_SALARY:
        base = min(base, budget * 0.92)
    elif budget < 2 * DAILY_SALARY and not survival_mode:
        base = min(base, DAILY_SALARY * 0.72)

    bid = min(budget, max(0.0, base))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_pressure = max(0.0, min(1.0, supply_pressure))

    my_urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    base = 20.0 + 18.0 * supply_pressure

    if highest_prev >= 150:
        if critical:
            bid = 112.0 + 12.0 * supply_pressure
        elif my_urgent:
            bid = 86.0 + 10.0 * supply_pressure
        else:
            bid = 24.0 + 8.0 * supply_pressure
    elif highest_prev >= 100:
        if critical:
            bid = 96.0 + 10.0 * supply_pressure
        elif my_urgent:
            bid = 74.0 + 8.0 * supply_pressure
        else:
            bid = 28.0 + 8.0 * supply_pressure
    elif highest_prev >= 60:
        if critical:
            bid = highest_prev + 6.0
        elif my_urgent:
            bid = highest_prev + 2.5
        else:
            bid = max(base, avg_prev * 0.72)
    else:
        if critical:
            bid = 78.0
        elif my_urgent:
            bid = 58.0
        else:
            bid = base

    if rich_opp >= 2 and supply <= 18:
        bid += 8.0
    if urgent_opp >= 2 and not my_urgent:
        bid -= 4.0

    if day >= 8 and hp > 4 and no_water_days == 0:
        bid *= 0.9

    min_safe = 0.0
    if critical:
        min_safe = 72.0
    elif my_urgent:
        min_safe = 52.0

    bid = max(min_safe, bid)
    bid = min(budget, bid)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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
    danger_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    danger_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    high_supply = supply >= 22.0
    low_supply = supply <= 17.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    danger_prev = max(danger_bids) if danger_bids else highest_prev

    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        bid = max(78.0, danger_prev + 6.0)
        if low_supply:
            bid += 10.0
        return float(min(budget, bid))

    if urgent:
        bid = max(58.0, highest_prev + 3.0)
        if low_supply:
            bid += 8.0
        elif high_supply:
            bid -= 6.0
        return float(max(0.0, min(budget, bid)))

    if high_supply:
        bid = 16.0
        if highest_prev <= 25.0:
            bid = max(bid, highest_prev + 1.0)
        elif highest_prev < 55.0:
            bid = 24.0
        else:
            bid = 14.0
    elif low_supply:
        if highest_prev < 45.0:
            bid = max(34.0, highest_prev + 2.0)
        elif highest_prev < 90.0:
            bid = 30.0
        else:
            bid = 22.0
    else:
        if highest_prev < 35.0:
            bid = max(26.0, highest_prev + 2.0)
        elif avg_prev > 90.0:
            bid = 18.0
        else:
            bid = 24.0

    if day >= 8 and budget > DAILY_SALARY * 2:
        bid += 4.0

    safe_cap = budget
    if hp >= 6 and no_water_days == 0:
        safe_cap = min(safe_cap, DAILY_SALARY * 0.65)

    return float(max(0.0, min(safe_cap, bid)))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0

    units = supply / WATER_REQ
    scarcity = units <= 2.05
    very_scarce = units <= 1.2

    prev_bids = []
    dangerous_prev = []
    rich_live = []
    for oid, opp in alive:
        if opp.get('budget', 0) > DAILY_SALARY * 1.2:
            rich_live.append((oid, opp))
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
                dangerous_prev.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    live_pressure = max(dangerous_prev) if dangerous_prev else highest_prev

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    elif hp <= 6:
        urgency += 1
    if no_water >= 2:
        urgency += 3
    elif no_water >= 1:
        urgency += 1
    if very_scarce:
        urgency += 2
    elif scarcity:
        urgency += 1
    if day >= 8:
        urgency += 1

    if not alive:
        if urgency >= 3:
            return min(budget, 35)
        return min(budget, 8)

    if urgency >= 5:
        target = max(92.0, live_pressure + 2.0)
    elif urgency >= 3:
        if live_pressure >= 95:
            target = 96.0
        else:
            target = max(58.0, live_pressure + 1.5)
    else:
        if not scarcity:
            if live_pressure >= 120:
                target = 6.0
            elif live_pressure >= 95:
                target = 12.0
            else:
                target = 18.0
        else:
            if live_pressure >= 120:
                target = 26.0
            elif live_pressure >= 95:
                target = 34.0
            else:
                target = max(28.0, live_pressure * 0.55)

    if len(rich_live) >= 2 and urgency <= 2 and live_pressure >= 100:
        target = min(target, 10.0 if not scarcity else 24.0)

    reserve = 0.0
    if hp <= 4 or no_water >= 1:
        reserve = 0.0
    elif day <= 6:
        reserve = 40.0
    else:
        reserve = 20.0

    affordable = max(0.0, budget - reserve)
    bid = min(target, budget)
    if affordable > 0:
        bid = min(bid, max(affordable, min(budget, 8.0 if urgency <= 2 else target)))

    if urgency >= 4 and budget >= 90:
        bid = max(bid, min(budget, max(90.0, live_pressure + 2.0)))

    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    opp_count = len(alive)
    units = int(supply // WATER_REQ)
    if units < 1:
        units = 1

    sorted_prev = sorted(prev_bids) if prev_bids else []
    highest_prev = sorted_prev[-1] if sorted_prev else 0.0
    second_prev = sorted_prev[-2] if len(sorted_prev) >= 2 else highest_prev
    third_prev = sorted_prev[-3] if len(sorted_prev) >= 3 else second_prev

    urgent = hp <= 3 or no_water >= 2
    pressured = hp <= 5 or no_water >= 1

    cindy_alive = False
    cindy_prev = None
    for oid, opp in alive:
        if oid == 'Cindy':
            cindy_alive = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                cindy_prev = float(prev.get('bid'))
            break

    if units >= opp_count + 1:
        base = 8.0
    elif units >= opp_count:
        base = 18.0
    elif units >= max(1, opp_count - 1):
        base = 42.0
    else:
        base = 58.0

    if cindy_alive and units <= opp_count - 1 and not urgent:
        target_ref = max(second_prev, third_prev)
        bid = max(base, min(88.0, target_ref + 2.0))
    else:
        target_ref = second_prev if cindy_alive and len(sorted_prev) >= 2 else highest_prev
        if urgent:
            bid = max(78.0, min(118.0, target_ref + 6.0))
        elif pressured:
            bid = max(base + 8.0, min(95.0, target_ref + 3.0))
        else:
            bid = max(base, min(82.0, target_ref + 1.5))

    if budget < DAILY_SALARY:
        bid = min(bid, max(12.0, budget * 0.72))
    else:
        reserve = 1 if urgent else 2
        future_floor = reserve * DAILY_SALARY * 0.45
        bid = min(bid, max(0.0, budget - future_floor))

    if urgent and budget > 0:
        bid = max(bid, min(budget, 84.0))

    if hp >= 7 and units <= 1 and cindy_alive and not pressured:
        bid = min(bid, 24.0)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
"""
