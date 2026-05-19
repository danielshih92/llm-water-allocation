# ============================================================
# Experiment: exp_061
# Agent: Alex
# Source: exp_061
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return max(0, min(budget, 18.0))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 3:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    player_count = len(alive) + 1
    scarcity = player_count * WATER_REQ - supply

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

    if hp <= 2 or no_water >= 2:
        target = max(63.0, highest_prev + 3.0)
    elif hp <= 4 or no_water >= 1:
        target = max(48.0, highest_prev + 2.0, avg_prev + 4.0)
    else:
        if scarcity <= 0:
            target = 20.0
        elif scarcity <= WATER_REQ:
            target = max(28.0, avg_prev + 1.5)
        else:
            target = max(36.0, highest_prev + 1.5)

    if desperate_count >= max(1, len(alive) // 2):
        target += 4.0
    if rich_count >= max(1, len(alive) // 2):
        target += 3.0
    if supply <= 16:
        target += 4.0
    elif supply >= 23:
        target -= 4.0

    reserve_floor = 0.0
    if hp > 4 and no_water == 0:
        reserve_floor = DAILY_SALARY * 0.2

    bid = min(budget, target)
    if budget - bid < reserve_floor:
        bid = max(0.0, budget - reserve_floor)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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
    urgent_opps = 0
    rich_opps = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > 300:
                rich_opps += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opps += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0.0, min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
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

    if danger >= 5:
        bid = max(62.0, max_prev + 3.0)
    elif danger >= 3:
        bid = max(50.0, avg_prev + 4.0)
    else:
        if scarcity == 2:
            bid = max(34.0, avg_prev + 2.0)
        elif scarcity == 1:
            bid = max(24.0, avg_prev * 0.55)
        else:
            bid = 14.0

    if rich_opps >= 1 and scarcity >= 1:
        bid += 4.0
    if urgent_opps >= 2 and danger <= 2:
        bid -= 4.0

    if max_prev >= 120 and danger <= 2:
        bid = min(bid, 22.0)
    elif max_prev >= 80 and scarcity == 0 and danger <= 2:
        bid = min(bid, 18.0)

    if day >= 8:
        if hp >= 6 and budget < 120:
            bid *= 0.8
        elif hp <= 4:
            bid = max(bid, 55.0)

    if budget < 50:
        bid = min(bid, max(8.0, budget * 0.55))
    elif budget < 120:
        bid = min(bid, budget * 0.7)

    bid = max(0.0, min(budget, bid))
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    total_alive = 1 + len(alive)
    capacity = int(supply // WATER_REQ)
    scarcity = capacity < total_alive

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        if opp.get('budget', 0) > budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if prev.get('status') == 'won' and float(bid) >= 90:
                urgent_opp += 0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    my_urgent = hp <= 3 or no_water >= 1
    very_urgent = hp <= 2 or no_water >= 2

    if not alive:
        return float(min(budget, 20.0 if not my_urgent else 55.0))

    if very_urgent:
        target = max(92.0, highest_prev + 3.0)
        if capacity <= 1:
            target = max(target, 118.0)
        return float(min(budget, target))

    if my_urgent:
        if scarcity:
            target = max(78.0, avg_prev + 6.0, highest_prev * 0.92)
            if capacity <= 1:
                target = max(target, 105.0)
            return float(min(budget, target))
        target = max(48.0, avg_prev * 0.72 + 4.0)
        return float(min(budget, target))

    if not scarcity:
        base = 18.0 + 1.5 * no_water
        if highest_prev < 80:
            base = max(base, highest_prev * 0.35)
        else:
            base = max(base, 24.0)
        if day >= 8:
            base += 4.0
        return float(min(budget, base))

    pressure = highest_prev
    if capacity <= 1:
        if urgent_opp >= 2:
            bid = 34.0
        else:
            bid = 28.0 if pressure > 100 else 32.0
        if day >= 8:
            bid += 6.0
        return float(min(budget, bid))

    bid = max(30.0, avg_prev * 0.42 + 3.0)
    if pressure > 120:
        bid = min(bid, 46.0)
    elif pressure > 95:
        bid = min(max(bid, 34.0), 52.0)
    else:
        bid = max(bid, 38.0)

    if rich_opp >= 2 and day <= 4:
        bid -= 4.0
    if day >= 8:
        bid += 5.0

    reserve_floor = DAILY_SALARY * max(0, 10 - day)
    if budget < reserve_floor:
        bid = min(bid, 36.0)

    return float(max(0.0, min(budget, bid)))
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                urgent_opp += 1

    if not alive:
        return float(min(budget, 18.0))

    high_supply = supply >= 22
    low_supply = supply <= 17
    very_risky = hp <= 3 or no_water >= 1

    top_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    target = 0.0

    if very_risky:
        if top_prev > 0:
            target = top_prev + 3.0
        else:
            target = DAILY_SALARY * 0.95
    elif low_supply:
        if top_prev >= 110:
            target = max(78.0, top_prev + 2.0)
        elif top_prev > 0:
            target = max(62.0, top_prev + 2.0)
        else:
            target = 66.0
    elif high_supply:
        if hp >= 7 and no_water == 0:
            target = 22.0
        else:
            target = 38.0
    else:
        if top_prev >= 120:
            target = 36.0 if hp >= 6 and no_water == 0 else 82.0
        elif avg_prev >= 90:
            target = 52.0
        else:
            target = 58.0

    if urgent_opp >= 2 and not very_risky:
        target -= 6.0
    if day >= 8 and hp >= 6 and no_water == 0 and not low_supply:
        target -= 6.0
    if hp <= 2:
        target = max(target, top_prev + 5.0 if top_prev > 0 else 90.0)
    if no_water >= 2:
        target = max(target, top_prev + 8.0 if top_prev > 0 else 110.0)

    target = max(0.0, target)
    return float(min(budget, target))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    strong_prev_bids = []
    weak_count = 0
    desperate_count = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > DAILY_SALARY * 2:
                strong_prev_bids.append(float(bid))
        if opp.get('budget', 0) < DAILY_SALARY * 0.75 or opp.get('hp', 10) <= 2:
            weak_count += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strong_highest_prev = max(strong_prev_bids) if strong_prev_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.55
    elif hp <= 4:
        danger += 0.3
    if no_water >= 2:
        danger += 0.35
    elif no_water >= 1:
        danger += 0.18
    danger += scarcity * 0.28
    if desperate_count >= 2:
        danger += 0.08

    if day >= 8:
        danger += 0.08

    if hp <= 2 or no_water >= 2:
        base = DAILY_SALARY * (0.92 + 0.35 * scarcity)
        target = max(base, strong_highest_prev + 6.0)
    elif scarcity >= 0.7:
        base = DAILY_SALARY * (0.58 + 0.22 * danger)
        target = max(base, strong_highest_prev + 2.5)
    elif scarcity <= 0.25 and hp >= 6 and no_water == 0:
        target = DAILY_SALARY * 0.22
        if strong_highest_prev < DAILY_SALARY * 0.45:
            target = max(target, strong_highest_prev + 1.2)
    else:
        base = DAILY_SALARY * (0.34 + 0.34 * danger)
        target = max(base, min(strong_highest_prev + 1.8, DAILY_SALARY * 0.88))

    if weak_count >= 2 and hp >= 5 and no_water == 0:
        target *= 0.92

    if highest_prev >= 180 and hp >= 5 and no_water == 0:
        target = min(target, DAILY_SALARY * 0.42)

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve = DAILY_SALARY * 0.5

    spend_cap = budget - reserve
    if spend_cap < 0:
        spend_cap = budget * 0.55
    if hp <= 2 or no_water >= 2:
        spend_cap = budget

    bid = min(target, spend_cap, budget)
    if bid < 0:
        bid = 0.0

    if bid > 0 and bid < 1.0:
        bid = min(1.0, budget)

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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(min(budget, max(0.0, base)))

    pressure_bids = []
    aggressive_count = 0
    moderate_count = 0
    needy_count = 0

    for opp in alive_opps:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            needy_count += 1
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            pressure_bids.append(float(bid))
            if bid >= 120:
                aggressive_count += 1
            elif bid >= 50:
                moderate_count += 1

    highest_prev = max(pressure_bids) if pressure_bids else 0.0
    active_prev = [b for b in pressure_bids if b > 0]
    avg_prev = sum(active_prev) / len(active_prev) if active_prev else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    risk = 0
    if hp <= 2:
        risk += 3
    elif hp <= 4:
        risk += 2
    elif hp <= 6:
        risk += 1
    if no_water_days >= 2:
        risk += 3
    elif no_water_days >= 1:
        risk += 2

    if day >= 8:
        risk += 1

    base = DAILY_SALARY * 0.38

    if scarcity == 2:
        base = DAILY_SALARY * 0.72
    elif scarcity == 1:
        base = DAILY_SALARY * 0.55

    if highest_prev >= 180:
        if risk >= 3:
            base = max(base, DAILY_SALARY * 0.82)
        else:
            base = min(base, DAILY_SALARY * 0.34)
    elif highest_prev >= 100:
        if risk >= 2:
            base = max(base, min(DAILY_SALARY * 0.78, avg_prev + 6.0))
        else:
            base = max(base, DAILY_SALARY * 0.46)
    elif highest_prev > 0:
        base = max(base, min(DAILY_SALARY * 0.74, highest_prev + 4.0))

    if aggressive_count >= 1 and risk <= 1 and scarcity == 0:
        base = min(base, DAILY_SALARY * 0.32)

    if moderate_count >= 1 and scarcity >= 1:
        base = max(base, avg_prev + 3.0)

    if needy_count >= 2 and risk >= 2:
        base = max(base, DAILY_SALARY * 0.8)

    reserve_target = 0.0
    days_left = 10 - day
    if days_left > 0:
        reserve_target = days_left * DAILY_SALARY * 0.18

    affordable = budget - reserve_target
    if affordable < 0:
        affordable = budget * 0.5

    bid = min(base, budget, affordable if affordable > 0 else budget)

    if risk >= 4:
        bid = max(bid, min(budget, DAILY_SALARY * 0.92))
    elif risk >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.7))

    if supply >= 23 and risk == 0:
        bid = min(bid, DAILY_SALARY * 0.28)

    if bid < 0:
        bid = 0.0

    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 250:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    days_left = max(0, 10 - day)
    safe_budget = days_left * DAILY_SALARY * 0.42

    if hp <= 2 or no_water_days >= 2:
        bid = max(62.0, highest_prev + 4.0, avg_prev + 8.0)
        return float(min(budget, bid))

    if hp <= 4 or no_water_days >= 1:
        bid = max(46.0, highest_prev + 2.0, avg_prev + 4.0)
        if supply <= 17:
            bid += 8.0
        return float(min(budget, bid))

    base = 24.0 + 14.0 * scarcity

    if highest_prev >= 120:
        base = min(base, 34.0)
    elif highest_prev >= 85:
        base = max(base, 38.0)
    elif highest_prev > 0:
        base = max(base, min(52.0, highest_prev + 1.5))

    if urgent_opp >= 2:
        base += 6.0
    elif urgent_opp == 1:
        base += 3.0

    if rich_opp >= 2 and supply <= 18:
        base += 5.0

    if budget > safe_budget + 120:
        base += 4.0
    elif budget < safe_budget:
        base -= 6.0

    if day >= 8:
        base += 6.0

    if hp >= 8 and supply >= 22 and highest_prev >= 100:
        base = min(base, 22.0)

    bid = max(0.0, min(budget, base))
    return float(bid)
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

    alive = []
    yesterday_bids = []
    desperate_count = 0
    rich_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 300:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid', 0.0)))
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0))

    max_prev = max(yesterday_bids) if yesterday_bids else 0.0
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
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.45

    urgency += scarcity * 0.55
    urgency += desperate_count * 0.08

    if day >= 8:
        urgency += 0.12

    if max_prev >= 180:
        if hp > 4 and no_water_days == 0:
            bid = 12.0 + scarcity * 10.0
        else:
            bid = 62.0 + scarcity * 18.0
    else:
        if urgency >= 1.5:
            bid = max(64.0, min(92.0, max_prev + 4.0))
        elif urgency >= 0.9:
            bid = max(42.0, min(72.0, avg_prev + 3.0, max_prev + 1.5 if max_prev > 0 else 60.0))
        elif urgency >= 0.45:
            bid = 26.0 + scarcity * 12.0
        else:
            bid = 14.0 + scarcity * 8.0

    if rich_count >= 2 and hp > 4 and no_water_days == 0 and supply >= 20:
        bid = min(bid, 20.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 35.0
    max_spend = max(0.0, budget - reserve_floor)

    if hp <= 2 or no_water_days >= 2:
        max_spend = budget

    bid = min(bid, max_spend if max_spend > 0 else budget)
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 140:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

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
        urgency += 2

    if tight_supply:
        urgency += 2
    elif not loose_supply:
        urgency += 1

    urgency += desperate_count

    if urgency >= 6:
        target = max(DAILY_SALARY * 1.35, highest_prev + 4.0, avg_prev + 8.0)
    elif urgency >= 4:
        target = max(DAILY_SALARY * 1.0, highest_prev + 2.0, avg_prev + 4.0)
    elif urgency >= 2:
        target = max(DAILY_SALARY * 0.72, avg_prev * 0.92)
    else:
        target = DAILY_SALARY * 0.42

    if loose_supply and hp >= 6 and no_water == 0:
        target *= 0.75

    if highest_prev >= 180 and urgency <= 3:
        target = min(target, DAILY_SALARY * 0.55)

    if rich_count >= 2 and tight_supply and urgency >= 3:
        target = max(target, highest_prev + 3.0)

    if day >= 8:
        target *= 1.12

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * (10 - day) * 0.18

    affordable = max(0.0, budget - reserve_floor)
    if urgency >= 5:
        affordable = budget

    bid = min(target, affordable)

    if bid < 0:
        bid = 0.0
    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, highest_prev + 2.5, DAILY_SALARY * 2.2))
        bid = min(bid, budget)

    return float(max(0.0, min(budget, bid)))
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

    alive = []
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                urgent_opponents += 1
            if opp.get('budget', 0) > budget:
                rich_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev['bid']))
                except Exception:
                    pass

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    high_supply = supply >= 22
    low_supply = supply <= 17

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    desperation = 0
    if hp <= 2:
        desperation += 4
    elif hp <= 4:
        desperation += 3
    elif hp <= 6:
        desperation += 2
    if no_water_days >= 2:
        desperation += 4
    elif no_water_days >= 1:
        desperation += 2

    market_pressure = 0
    if low_supply:
        market_pressure += 3
    elif supply <= 20:
        market_pressure += 2
    else:
        market_pressure += 1
    market_pressure += min(2, urgent_opponents)
    if highest_prev >= 200:
        market_pressure += 2
    elif highest_prev >= 120:
        market_pressure += 1

    if desperation >= 6:
        target = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif desperation >= 4:
        target = max(DAILY_SALARY * 0.78, avg_prev * 0.9, highest_prev * 0.72)
    else:
        if high_supply and hp >= 7 and no_water_days == 0:
            target = DAILY_SALARY * 0.22
        elif market_pressure >= 5:
            target = max(DAILY_SALARY * 0.62, highest_prev * 0.55)
        elif market_pressure >= 3:
            target = max(DAILY_SALARY * 0.45, avg_prev * 0.45)
        else:
            target = DAILY_SALARY * 0.3

    if highest_prev > 400 and desperation < 4:
        target = min(target, DAILY_SALARY * 0.38)
    elif highest_prev > 220 and desperation < 6:
        target = min(target, DAILY_SALARY * 0.48)

    if rich_opponents >= 2 and low_supply and desperation >= 4:
        target += 8

    if day >= 8 and hp >= 6 and no_water_days == 0:
        target *= 0.9

    reserve = 0.0
    if hp > 4:
        reserve = DAILY_SALARY * 0.25
    if desperation >= 4:
        reserve = 0.0

    bid = min(budget - reserve, target)
    if bid < 0:
        bid = 0.0
    if desperation >= 6:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    return float(max(0.0, min(budget, bid)))
"""
