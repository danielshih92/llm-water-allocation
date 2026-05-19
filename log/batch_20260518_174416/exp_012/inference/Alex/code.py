# ============================================================
# Experiment: exp_012
# Agent: Alex
# Source: exp_012
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    total_agents = 1 + len(alive_opponents)
    total_demand = WATER_REQ
    for opp in alive_opponents:
        total_demand += opp.get('water_requirement', WATER_REQ)

    scarcity = 0.0
    if total_demand > 0:
        scarcity = max(0.0, min(1.0, 1.0 - (float(supply) / float(total_demand))))

    prev_bids = []
    desperate_opp = False
    rich_opp_pressure = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp = True
        opp_budget = opp.get('budget', 0)
        opp_salary = opp.get('daily_salary', DAILY_SALARY)
        if opp_budget >= opp_salary * 2:
            rich_opp_pressure = max(rich_opp_pressure, 1.0)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = DAILY_SALARY * 0.55
        avg_prev = DAILY_SALARY * 0.5

    urgency = 0.0
    if hp <= 2:
        urgency += 0.6
    elif hp <= 4:
        urgency += 0.35
    if no_water_days >= 1:
        urgency += 0.25
    urgency += scarcity * 0.45
    if desperate_opp:
        urgency += 0.1
    urgency = max(0.0, min(1.0, urgency))

    if hp <= 2 or no_water_days >= 2:
        target = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
    elif scarcity > 0.45:
        target = max(DAILY_SALARY * 0.72, avg_prev + 1.5, highest_prev * 0.92)
    elif scarcity < 0.2 and hp > 4 and no_water_days == 0:
        target = max(DAILY_SALARY * 0.38, avg_prev * 0.82)
    else:
        target = max(DAILY_SALARY * (0.45 + 0.35 * urgency), avg_prev + 0.8)

    if rich_opp_pressure > 0 and scarcity > 0.35:
        target += 1.0

    reserve_days = 2 if hp > 3 else 1
    reserve = DAILY_SALARY * reserve_days
    max_affordable = budget - reserve
    if max_affordable < DAILY_SALARY * 0.2:
        max_affordable = budget

    bid = min(budget, max_affordable, target)
    floor_bid = 0.0
    if hp <= 3 or no_water_days >= 1:
        floor_bid = min(budget, DAILY_SALARY * 0.55)
    elif scarcity > 0.35:
        floor_bid = min(budget, DAILY_SALARY * 0.42)

    bid = max(floor_bid, bid)
    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    threat_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0)
            prev_bids.append(bid)
            if opp.get('budget', 0) > 0:
                threat_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0
    highest_threat = max(threat_bids) if threat_bids else highest_prev

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    base = DAILY_SALARY * 0.42

    if scarcity == 2:
        base = DAILY_SALARY * 0.72
    elif scarcity == 1:
        base = DAILY_SALARY * 0.56

    if hp <= 2 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.68)

    if urgent_opponents >= 2:
        base += 6.0
    elif urgent_opponents == 1:
        base += 3.0

    if rich_opponents >= 2 and scarcity >= 1:
        base += 4.0

    if highest_threat >= DAILY_SALARY * 1.2:
        if hp >= 5 and no_water_days == 0 and supply >= 20:
            base = min(base, DAILY_SALARY * 0.38)
        else:
            base = max(base, DAILY_SALARY * 0.82)
    elif highest_threat >= DAILY_SALARY * 0.85:
        if hp >= 6 and no_water_days == 0 and supply >= 20:
            base = min(base, DAILY_SALARY * 0.4)
        else:
            base = max(base, highest_threat * 0.78)
    elif highest_threat > 0:
        base = max(base, min(highest_threat + 2.0, DAILY_SALARY * 0.88))
    else:
        base = max(base, avg_prev + 1.5)

    if day >= 8:
        base += 4.0
    if day >= 9 and hp <= 4:
        base += 8.0

    reserve_floor = 0.0
    if day <= 6:
        reserve_floor = DAILY_SALARY * 1.2
    elif day <= 8:
        reserve_floor = DAILY_SALARY * 0.7

    affordable = budget
    if budget > reserve_floor:
        affordable = budget - reserve_floor + min(reserve_floor * 0.25, DAILY_SALARY * 0.3)

    bid = min(base, affordable)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

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

    if supply <= 16:
        danger += 2
    elif supply <= 18:
        danger += 1

    if urgent_opp >= 2:
        danger += 1

    if budget <= DAILY_SALARY * 2:
        conserve = 1
    else:
        conserve = 0

    if danger >= 6:
        target = max(98.0, highest_prev + 2.5)
    elif danger >= 4:
        target = max(88.0, highest_prev + 1.5, avg_prev + 6.0)
    elif danger >= 2:
        target = max(72.0 + 10.0 * scarcity, avg_prev + 2.0)
    else:
        if supply >= 22 and hp >= 7 and no_water_days == 0:
            target = 26.0
        elif supply >= 20:
            target = 38.0
        else:
            target = 52.0 + 10.0 * scarcity

    if highest_prev >= 100:
        if danger <= 2 and hp >= 5:
            target = min(target, 55.0)
        else:
            target = max(target, 101.0)
    elif highest_prev >= 90:
        if danger <= 1 and supply >= 20:
            target = min(target, 50.0)
        else:
            target = max(target, highest_prev + 1.2)
    elif highest_prev >= 75 and danger >= 3:
        target = max(target, highest_prev + 1.0)

    if rich_opp >= 2 and supply <= 17 and danger >= 3:
        target += 4.0

    if conserve and danger <= 2:
        target *= 0.82

    min_safe = 0.0
    if hp <= 2 or no_water_days >= 2:
        min_safe = 95.0
    elif hp <= 4 or no_water_days >= 1:
        min_safe = 78.0

    bid = max(target, min_safe)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    capacity = supply / float(WATER_REQ)
    contested = capacity < (len(alive) + 1)
    very_tight = capacity <= 1.25
    ample = capacity >= 2.0

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= 200:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    my_urgent = hp <= 3 or no_water >= 1
    my_critical = hp <= 2 or no_water >= 2

    if my_critical:
        bid = max(88.0, highest_prev + 3.0)
    elif my_urgent:
        bid = max(76.0, avg_prev + 2.0, highest_prev * 0.92)
    else:
        if very_tight and highest_prev >= 80 and hp >= 6 and no_water == 0:
            bid = 12.0
        elif contested and highest_prev >= 85 and hp >= 5:
            bid = 22.0
        elif ample:
            bid = max(38.0, min(68.0, avg_prev * 0.7 + 3.0))
        else:
            bid = max(30.0, min(72.0, highest_prev * 0.78 + 2.0))

    if urgent_opp >= 2 and not my_urgent and hp >= 5 and contested:
        bid = min(bid, 24.0)

    if rich_opp == 0 and ample and hp >= 4:
        bid = max(bid, 34.0)

    if budget < bid:
        bid = budget

    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_opponents += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

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

    pressure = 0
    if highest_prev >= 110:
        pressure = 3
    elif highest_prev >= 75:
        pressure = 2
    elif highest_prev >= 40:
        pressure = 1

    if highest_prev > budget * 0.9 and danger <= 2:
        return float(min(budget, 12.0 if supply >= 20 else 18.0))

    base = 16.0
    if supply >= 23:
        base = 12.0
    elif supply >= 20:
        base = 15.0
    elif supply >= 17:
        base = 19.0
    else:
        base = 24.0

    bid = base
    bid += scarcity * 8.0
    bid += pressure * 10.0
    bid += danger * 12.0
    bid += urgent_opponents * 3.0

    if rich_opponents >= 2 and scarcity >= 1:
        bid += 8.0

    if avg_prev >= 80 and danger <= 1:
        bid -= 10.0

    if hp >= 8 and no_water_days == 0 and supply >= 20 and highest_prev >= 100:
        bid = min(bid, 18.0)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, highest_prev + 3.0, 72.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, min(highest_prev + 2.0, 78.0), 42.0)
    else:
        if highest_prev > 0:
            bid = max(bid, min(highest_prev + 1.5, 58.0))

    max_safe = budget
    if hp > 4 and no_water_days == 0:
        max_safe = min(max_safe, budget * 0.45 + DAILY_SALARY * 0.25)
    elif hp > 2:
        max_safe = min(max_safe, budget * 0.65 + DAILY_SALARY * 0.35)

    bid = min(bid, max_safe)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive = 0
    rich_alive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > 700:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 80:
                    aggressive += 1

    if not alive:
        return max(0.0, min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity_units = supply / float(WATER_REQ)
    very_tight = scarcity_units < 1.45
    tight = scarcity_units < 1.7

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water >= 2:
        urgency += 4
    elif no_water >= 1:
        urgency += 2
    if day >= 8:
        urgency += 1
    if very_tight:
        urgency += 2
    elif tight:
        urgency += 1

    if urgency >= 7:
        target = max(92.0, max_prev + 4.0)
    elif urgency >= 5:
        target = max(76.0, max_prev * 0.92 + 3.0)
    elif urgency >= 3:
        target = max(52.0, avg_prev * 0.78 + 2.0)
    else:
        if very_tight:
            target = 41.0
        elif tight:
            target = 30.0
        else:
            target = 22.0

    if max_prev >= 120 and urgency <= 3:
        target = min(target, 34.0)
    if aggressive >= 2 and urgency <= 4:
        target = min(target, 36.0)
    if rich_alive >= 2 and urgency <= 2:
        target = min(target, 28.0)

    if hp <= 3 or no_water >= 2:
        target = max(target, 88.0)
    elif hp <= 5 or no_water >= 1:
        target = max(target, 64.0)

    reserve_floor = 0.0
    if day <= 6:
        reserve_floor = DAILY_SALARY * (10 - day) * 0.18
    elif day <= 8:
        reserve_floor = DAILY_SALARY * (10 - day) * 0.1

    spend_cap = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water >= 2:
        spend_cap = budget

    bid = min(target, spend_cap)
    if bid < 0:
        bid = 0.0
    if budget <= 25:
        bid = budget

    return float(max(0.0, min(budget, bid)))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_budgets = []
    urgent_opp = 0

    for opp_id, opp in opponents_status.items():
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

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0
    rich_opps = 0
    for b in opp_budgets:
        if b >= budget:
            rich_opps += 1

    tight_supply = supply <= 17
    ample_supply = supply >= 22
    critical_me = hp <= 3 or no_water_days >= 1
    very_safe = hp >= 8 and no_water_days == 0

    bid = 0.0

    if critical_me:
        if max_prev > 0:
            bid = max(72.0, min(max_prev + 2.5, DAILY_SALARY * 2.0))
        else:
            bid = 95.0
    elif tight_supply:
        if urgent_opp >= 2:
            bid = max(58.0, min(avg_prev * 0.72, 92.0))
        elif max_prev >= 120:
            bid = max(52.0, min(max_prev * 0.62, 88.0))
        else:
            bid = 54.0
    elif ample_supply:
        if very_safe:
            bid = 18.0
        else:
            bid = 28.0
    else:
        if max_prev >= 130:
            bid = 34.0 if very_safe else 46.0
        elif avg_prev >= 100:
            bid = 40.0
        else:
            bid = 32.0

    if rich_opps >= 3 and not critical_me and not tight_supply:
        bid *= 0.9

    if day >= 8:
        if hp >= 6 and no_water_days == 0:
            bid *= 0.9
        else:
            bid *= 1.1

    min_guard = 12.0 if very_safe else 20.0
    bid = max(min_guard, bid)
    bid = min(budget, bid)

    if budget < 25:
        bid = min(bid, budget)

    return max(0, float(round(bid, 2)))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    guaranteed_units = int(supply // WATER_REQ)

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

    if guaranteed_units >= 2:
        base = 48.0
        if danger >= 4:
            base = 74.0
        elif danger >= 2:
            base = 62.0

        target = max(base, avg_prev + 2.0)
        if urgent_opp >= 2:
            target += 4.0
        if rich_opp >= 2:
            target += 2.0
        if budget < 250:
            target -= 6.0
        return float(max(0.0, min(budget, target)))

    base = 22.0
    if danger >= 5:
        base = 86.0
    elif danger >= 3:
        base = 73.0
    elif danger >= 1:
        base = 58.0

    if highest_prev >= 95.0 and danger <= 2:
        target = 18.0
    elif highest_prev >= 80.0 and danger <= 1:
        target = 24.0
    else:
        if danger >= 3:
            target = max(base, highest_prev + 1.6)
        else:
            target = min(base, highest_prev + 0.5) if highest_prev > 0 else base

    if day >= 8 and hp >= 6 and danger <= 1:
        target *= 0.8
    if budget < 180:
        target = min(target, 52.0)
    if budget < 120:
        target = min(target, 38.0)

    return float(max(0.0, min(budget, target)))
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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 900:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    pressure = 0.0
    if highest_prev >= 140:
        pressure += 18
    elif highest_prev >= 130:
        pressure += 12
    elif highest_prev >= 100:
        pressure += 7
    else:
        pressure += 3

    pressure += desperate_count * 4
    pressure += rich_count * 2

    if supply <= 16:
        pressure += 18
    elif supply <= 18:
        pressure += 12
    elif supply >= 23:
        pressure -= 10
    elif supply >= 21:
        pressure -= 5

    urgency = 0.0
    if hp <= 2:
        urgency += 40
    elif hp <= 4:
        urgency += 24
    elif hp <= 6:
        urgency += 12

    if no_water_days >= 2:
        urgency += 35
    elif no_water_days >= 1:
        urgency += 18

    if day >= 8:
        urgency += 8

    base = 62.0 + pressure + urgency

    if supply >= 22 and hp >= 7 and no_water_days == 0:
        base -= 18
    if supply >= 24 and hp >= 9:
        base -= 10

    if highest_prev > 0:
        target = max(base, highest_prev + 2.5)
    else:
        target = base

    if hp <= 2 or no_water_days >= 2:
        target = max(target, 132.0)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, 108.0)

    if budget < 120:
        target = min(target, budget)
    elif budget < 250:
        target = min(target, budget * 0.72)
    elif budget < 450:
        target = min(target, budget * 0.55)
    else:
        target = min(target, budget * 0.32 + 35)

    if supply >= 23 and hp >= 8 and no_water_days == 0:
        target = min(target, 88.0)

    if target < 0:
        target = 0.0
    if target > budget:
        target = float(budget)

    return float(round(target, 2))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    threat_bids = []
    cindy_bid = None
    strongest_pressure = 0.0

    for agent_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
            pressure = float(pbid)
            if opp.get('budget', 0) < DAILY_SALARY * 0.8:
                pressure *= 0.75
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                pressure *= 1.2
            if pressure > strongest_pressure:
                strongest_pressure = pressure
            threat_bids.append(pressure)
        if agent_id == 'Cindy' and pbid is not None:
            cindy_bid = float(pbid)

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0
    max_threat = max(threat_bids) if threat_bids else 0.0

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    scarcity = 1.0 - supply_ratio

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.98
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * (0.78 + 0.12 * scarcity)
    else:
        base = DAILY_SALARY * (0.34 + 0.18 * scarcity)

    if cindy_bid is not None:
        target = cindy_bid + (2.0 if hp <= 4 or no_water_days >= 1 else -18.0 + 10.0 * scarcity)
    elif max_threat > 0:
        target = max_threat + (1.5 if hp <= 4 or no_water_days >= 1 else -12.0 + 8.0 * scarcity)
    else:
        target = base

    bid = max(base, target)

    if hp > 5 and no_water_days == 0 and supply >= 22:
        bid = min(bid, DAILY_SALARY * 0.32)

    if max_prev >= DAILY_SALARY * 1.8 and hp > 4 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.28)

    reserve_days = 3 if day < 8 else 1
    reserve = reserve_days * DAILY_SALARY * 0.45
    spendable = budget - reserve
    if spendable < DAILY_SALARY * 0.2:
        spendable = max(budget * 0.5, 0.0)

    bid = min(bid, spendable)

    if hp <= 3 or no_water_days >= 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.72))

    if day >= 9:
        bid = max(bid, min(budget, DAILY_SALARY * (0.55 + 0.2 * scarcity)))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
"""
