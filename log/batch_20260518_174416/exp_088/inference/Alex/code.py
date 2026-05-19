# ============================================================
# Experiment: exp_088
# Agent: Alex
# Source: exp_088
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 4:
                rich_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.25)

    competitor_count = len(alive_opponents)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = DAILY_SALARY * (0.42 + 0.28 * scarcity)

    if competitor_count >= 3:
        base += 4
    elif competitor_count == 1:
        base -= 3

    if desperate_count > 0:
        base += min(10, 3 * desperate_count)
    if rich_count >= 2:
        base += 4

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        target = max(avg_prev + 1.0, highest_prev * 0.92)
        base = max(base, target)

        if highest_prev >= DAILY_SALARY * 0.9 and hp > 4 and no_water_days == 0 and supply >= 20:
            base = min(base, DAILY_SALARY * 0.38)
    
    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.95)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.78)

    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.98)
    elif no_water_days == 1:
        base = max(base, DAILY_SALARY * 0.82)

    if day >= 8:
        base += 4

    if budget < DAILY_SALARY * 1.5 and hp > 4 and no_water_days == 0:
        base = min(base, DAILY_SALARY * 0.45)

    bid = max(0, min(budget, base))
    return bid
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(max(0.0, min(budget, 20.0)))

    prev_bids = []
    dangerous_prev = []
    stressed_opponents = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 80:
                dangerous_prev.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            stressed_opponents += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
    if no_water_days >= 1:
        urgency += 0.8

    base = 28.0 + 22.0 * scarcity + 18.0 * urgency

    if supply <= 17:
        target = max(base, highest_prev + 3.0)
    elif supply <= 19:
        target = max(base, avg_prev + 6.0)
    else:
        target = max(base, avg_prev * 0.8 + 4.0)

    if highest_prev >= 110:
        if urgency >= 0.8 or supply <= 17:
            target = max(target, highest_prev + 2.5)
        else:
            target = min(target, 72.0)
    elif highest_prev >= 85:
        if urgency >= 0.8:
            target = max(target, highest_prev + 1.5)

    if stressed_opponents >= len(alive) // 2 + 1:
        target -= 8.0

    if day >= 8 and hp > 4 and no_water_days == 0:
        target -= 6.0

    reserve_floor = 0.0
    days_left = 10 - day
    if days_left > 0:
        reserve_floor = min(budget, days_left * 8.0)

    affordable = max(0.0, budget - reserve_floor * 0.25)
    if urgency >= 0.8:
        affordable = budget

    bid = min(target, affordable, budget)

    if hp <= 2 or no_water_days >= 1:
        bid = max(bid, min(budget, max(78.0, highest_prev + 2.0)))

    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    danger_count = 0
    rich_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if float(opp.get('hp', 0)) <= 4 or int(opp.get('no_water_days', 0)) >= 1:
                danger_count += 1
            if float(opp.get('budget', 0)) >= budget:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return round(min(budget, 8.0), 2)

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 3:
        urgency += 0.55
    elif hp <= 5:
        urgency += 0.3
    if no_water >= 2:
        urgency += 0.5
    elif no_water >= 1:
        urgency += 0.22
    if day >= 8:
        urgency += 0.08

    pressure = 0.18 + 0.42 * scarcity + 0.28 * urgency
    if danger_count >= 2:
        pressure += 0.06
    if rich_count >= 2:
        pressure += 0.04

    target = DAILY_SALARY * pressure

    if max_prev > 0:
        if scarcity >= 0.7 or urgency >= 0.45:
            target = max(target, min(max_prev + 2.0, DAILY_SALARY * 1.12))
        elif max_prev >= 120:
            target = min(target, avg_prev * 0.72)
        else:
            target = max(target, avg_prev * 0.88)

    if supply >= 22 and urgency < 0.3:
        target *= 0.75
    elif supply <= 17:
        target *= 1.18

    if hp <= 2 or no_water >= 2:
        target = max(target, DAILY_SALARY * 0.95)

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left > 0:
        reserve_floor = min(budget * 0.35, days_left * 10.0)
    cap = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water >= 2:
        cap = budget

    bid = min(target, cap if cap > 0 else budget)
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    if bid == 0.0 and (hp <= 3 or no_water >= 1):
        bid = min(budget, DAILY_SALARY * 0.55)

    return round(bid, 2)
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if len(alive_opponents) == 0:
        solo_bid = DAILY_SALARY * 0.2
        if hp <= 2 or no_water_days >= 2:
            solo_bid = DAILY_SALARY * 0.45
        return float(max(0.0, min(budget, solo_bid)))

    prev_bids = []
    aggressive_count = 0
    desperate_count = 0
    rich_aggressive = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 120:
                aggressive_count += 1
            if bid >= 160:
                rich_aggressive += 1
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_pressure = 1.0
    if supply >= 23:
        supply_pressure = 0.72
    elif supply >= 20:
        supply_pressure = 0.84
    elif supply >= 18:
        supply_pressure = 0.96
    else:
        supply_pressure = 1.12

    health_pressure = 0.0
    if hp <= 2 or no_water_days >= 2:
        health_pressure = 55.0
    elif hp <= 4 or no_water_days >= 1:
        health_pressure = 22.0

    bid = 0.0

    if highest_prev >= 160:
        if hp >= 6 and no_water_days == 0 and supply >= 20:
            bid = 58.0
        else:
            bid = 96.0 + health_pressure * 0.35
    elif highest_prev >= 120:
        bid = 74.0 + health_pressure * 0.45
    elif highest_prev >= 80:
        bid = 62.0 + health_pressure * 0.4
    elif highest_prev > 0:
        bid = max(48.0, avg_prev * 0.72) + health_pressure * 0.3
    else:
        bid = 52.0 + health_pressure * 0.3

    if desperate_count >= 2:
        bid += 12.0
    elif desperate_count == 1:
        bid += 6.0

    if aggressive_count >= 2 and hp >= 6 and no_water_days == 0 and supply >= 20:
        bid -= 8.0

    if rich_aggressive >= 1 and hp >= 7 and no_water_days == 0 and supply >= 22:
        bid -= 6.0

    bid *= supply_pressure

    if day >= 8 and hp <= 4:
        bid += 18.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 105.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, 72.0)

    max_safe = budget
    if hp >= 7 and no_water_days == 0:
        max_safe = min(max_safe, DAILY_SALARY * 1.15)
    elif hp >= 5:
        max_safe = min(max_safe, DAILY_SALARY * 1.55)
    else:
        max_safe = min(max_safe, DAILY_SALARY * 2.4)

    bid = max(0.0, min(bid, max_safe))
    return float(round(bid, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    dangerous_prev.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 10.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    active_high = max(dangerous_prev) if dangerous_prev else 0.0

    competitors = 1
    for opp in alive_opponents:
        if opp.get('budget', 0) > 0 and opp.get('hp', 0) > -5:
            competitors += 1

    req_units = int(supply // WATER_REQ)
    scarcity = req_units < competitors
    very_tight = req_units <= 1

    need_score = 0
    if hp <= 2:
        need_score += 4
    elif hp <= 4:
        need_score += 3
    elif hp <= 6:
        need_score += 2
    else:
        need_score += 1

    if no_water_days >= 2:
        need_score += 3
    elif no_water_days >= 1:
        need_score += 1

    if scarcity:
        need_score += 2
    if very_tight:
        need_score += 1

    target = 0.0

    if active_high > 300:
        active_high = 155.0

    if need_score >= 7:
        target = max(150.5, active_high + 2.5)
    elif need_score >= 5:
        target = max(148.0, active_high + 1.5)
    elif need_score >= 3:
        if active_high >= 145:
            target = 146.0
        else:
            target = max(92.0, active_high * 0.72 + 8.0)
    else:
        if highest_prev >= 145:
            target = 58.0
        else:
            target = max(28.0, active_high * 0.38 + 6.0)

    if budget < 80 and need_score < 5:
        target = min(target, 55.0)
    if budget < 40:
        if need_score >= 6:
            target = budget
        else:
            target = min(target, 22.0)

    if hp <= 1 or no_water_days >= 3:
        target = max(target, active_high + 3.0, 155.0)

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 500:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 1.0 - ((float(supply) - 15.0) / 10.0)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water >= 2:
        urgency += 0.7
    elif no_water >= 1:
        urgency += 0.35

    pressure = scarcity * 0.5 + urgency + desperate_count * 0.08 + rich_count * 0.05

    if hp <= 2 or no_water >= 2:
        bid = max(62.0, high_prev + 2.0, avg_prev + 6.0)
    elif pressure >= 1.0:
        bid = max(48.0, min(high_prev + 1.5, 95.0))
    elif pressure >= 0.65:
        bid = max(34.0, min(avg_prev + 2.0, high_prev * 0.72 if high_prev > 0 else 40.0))
    else:
        if supply >= 22:
            bid = 16.0
        elif supply >= 19:
            bid = 22.0
        else:
            bid = 28.0

    if high_prev >= 130.0 and hp >= 5 and no_water == 0:
        bid = min(bid, 30.0 + scarcity * 8.0)

    safe_cap = budget
    if day <= 3:
        safe_cap = min(safe_cap, 85.0)
    elif day <= 6:
        safe_cap = min(safe_cap, 95.0)
    else:
        safe_cap = min(safe_cap, 110.0)

    if hp >= 7 and no_water == 0 and supply >= 21:
        safe_cap = min(safe_cap, 40.0)

    bid = min(bid, safe_cap)
    if bid < 0.0:
        bid = 0.0
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_pressure = 0.0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                opp_pressure = max(opp_pressure, bid)
                if opp.get('budget', 0) > 200 and bid >= 110:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    total_alive = len(alive) + 1
    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < total_alive

    base = 22.0
    if supply >= 24:
        base = 16.0
    elif supply >= 20:
        base = 20.0
    elif supply >= 17:
        base = 26.0
    else:
        base = 34.0

    if scarcity:
        base += 8.0

    if opp_pressure >= 160:
        base -= 4.0
    elif opp_pressure >= 130:
        base -= 2.0
    elif opp_pressure > 0 and opp_pressure < 90:
        base += 6.0

    if rich_aggressive >= 2:
        base -= 3.0

    if hp <= 2 or no_water_days >= 2:
        emergency = max(95.0, opp_pressure + 3.0 if opp_pressure > 0 else 105.0)
        return float(min(budget, emergency))

    if hp <= 4 or no_water_days == 1:
        urgent = max(base + 22.0, min(90.0, opp_pressure * 0.78 if opp_pressure > 0 else 58.0))
        return float(min(budget, urgent))

    if budget < 80:
        return float(min(budget, max(12.0, base - 8.0)))

    if budget > 400 and scarcity and opp_pressure > 0 and opp_pressure < 120:
        base = max(base, opp_pressure + 2.0)

    return float(min(budget, max(8.0, base)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

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
            if opp.get('budget', 0) >= 120:
                rich_opp += 1
            if opp.get('hp', 0) <= 4 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev.get('bid', 0.0)))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = max(0.0, min(1.0, (20.0 - supply) / 5.0))
    pressure = 0.0
    pressure += 0.9 * scarcity
    pressure += 0.2 * max(0, len(alive) - 2)
    pressure += 0.15 * urgent_opp
    pressure += 0.1 * rich_opp

    if hp <= 2 or no_water_days >= 2:
        bid = max(110.0, highest_prev + 8.0, avg_prev + 10.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(88.0, highest_prev + 4.0, avg_prev + 3.0)
    else:
        if highest_prev >= 150.0:
            bid = 28.0 + 10.0 * scarcity
        elif highest_prev >= 110.0:
            bid = 42.0 + 18.0 * pressure
        else:
            bid = 48.0 + 22.0 * pressure
            if scarcity > 0.45:
                bid = max(bid, highest_prev + 2.5)

    if supply >= 23.0 and hp >= 6 and no_water_days == 0:
        bid *= 0.72
    elif supply >= 20.0 and hp >= 5 and no_water_days == 0:
        bid *= 0.85

    reserve = 0.0
    if hp >= 6 and no_water_days == 0:
        reserve = 35.0
    elif hp >= 4:
        reserve = 15.0

    cap = budget - reserve
    if hp <= 3 or no_water_days >= 1:
        cap = budget
    cap = max(0.0, cap)

    bid = min(bid, cap)

    if bid <= 0 and budget > 0:
        bid = min(budget, 8.0)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 120.0 if budget >= 120.0 else budget))

    return float(max(0.0, round(bid, 2)))
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    aggressive_count = 0
    desperate_count = 0
    cindy_like_present = False

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                bid = float(bid)
                prev_bids.append(bid)
                if bid >= 120:
                    aggressive_count += 1
                if bid >= 100:
                    cindy_like_present = True
            if int(opp.get('no_water_days', 0)) >= 2 or float(opp.get('hp', 10)) <= 2:
                desperate_count += 1

    if not alive_opps:
        return min(budget, 20.0)

    tight_supply = supply <= 17.0
    ample_supply = supply >= 22.0

    if prev_bids:
        highest_prev = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        second_prev = 0.0
        avg_prev = 0.0

    urgency = 0
    if hp <= 2 or no_water >= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency == 3:
        bid = max(95.0, highest_prev + 3.0)
        if cindy_like_present:
            bid = max(bid, 118.0)
    elif urgency == 2:
        if tight_supply:
            bid = max(62.0, second_prev + 2.0, avg_prev * 0.9)
        else:
            bid = max(48.0, second_prev + 1.5, avg_prev * 0.75)
    elif urgency == 1:
        if aggressive_count > 0 and not tight_supply:
            bid = 18.0
        else:
            bid = max(28.0, min(55.0, second_prev + 1.0))
    else:
        if aggressive_count > 0:
            bid = 10.0 if ample_supply else 14.0
        elif desperate_count >= 2 and tight_supply:
            bid = 36.0
        else:
            bid = 20.0 if ample_supply else 26.0

    if day >= 8 and hp > 4 and budget < 180:
        bid *= 0.85
    if day >= 8 and urgency >= 2:
        bid *= 1.1

    reserve_floor = 0.0
    if day <= 3:
        reserve_floor = 280.0
    elif day <= 6:
        reserve_floor = 180.0
    else:
        reserve_floor = 80.0

    max_affordable = budget
    if budget > reserve_floor:
        max_affordable = max(0.0, budget - reserve_floor + DAILY_SALARY * 0.35)

    if urgency == 3:
        max_affordable = budget
    elif urgency == 2:
        max_affordable = min(budget, max(max_affordable, budget * 0.6))

    bid = min(bid, max_affordable, budget)
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return max(0.0, min(budget, 18.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    prev_bids = []
    bob_bid = None
    cindy_bid = None
    urgent_opp = False

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if agent_id == 'Bob':
                bob_bid = float(bid)
            if agent_id == 'Cindy':
                cindy_bid = float(bid)
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp = True

    highest_prev = max(prev_bids) if prev_bids else 0.0
    stable_ref = bob_bid if bob_bid is not None else highest_prev

    danger = hp <= 3 or no_water_days >= 1
    very_danger = hp <= 2 or no_water_days >= 2
    tight_supply = slots <= 1

    if very_danger:
        target = max(72.0, stable_ref + 6.0)
        if cindy_bid is not None and cindy_bid < 110:
            target = max(target, cindy_bid + 2.0)
        return max(0.0, min(budget, target))

    if tight_supply:
        if danger:
            target = max(66.0, stable_ref + 2.5)
            return max(0.0, min(budget, target))
        if stable_ref >= 60.0:
            return max(0.0, min(budget, 34.0))
        target = max(58.0, stable_ref + 1.5)
        return max(0.0, min(budget, target))

    if slots >= 2:
        if danger:
            target = max(52.0, stable_ref)
            return max(0.0, min(budget, target))
        if urgent_opp and highest_prev >= 80.0:
            return max(0.0, min(budget, 24.0))
        if stable_ref >= 60.0:
            return max(0.0, min(budget, 28.0))
        return max(0.0, min(budget, 41.0))

    return max(0.0, min(budget, 45.0))
"""
