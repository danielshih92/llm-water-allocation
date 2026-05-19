# ============================================================
# Experiment: exp_020
# Agent: Alex
# Source: exp_020
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    total_agents = 1 + len(alive_opponents)
    expected_total_need = total_agents * WATER_REQ
    scarcity = supply < expected_total_need

    highest_prev_bid = 0
    urgent_opp_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if isinstance(prev_bid, (int, float)) and prev_bid > highest_prev_bid:
            highest_prev_bid = prev_bid

    my_urgent = hp <= 3 or no_water_days >= 1

    if my_urgent:
        base = DAILY_SALARY * 0.92
        if scarcity:
            base = max(base, highest_prev_bid + 2)
        bid = base
    else:
        if not scarcity:
            bid = DAILY_SALARY * 0.34
            if highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 0.45:
                bid = max(bid, highest_prev_bid + 1)
        else:
            pressure = 0.58 + 0.07 * urgent_opp_count
            if hp >= 7 and no_water_days == 0:
                pressure -= 0.06
            bid = DAILY_SALARY * pressure
            if highest_prev_bid > 0:
                if highest_prev_bid >= DAILY_SALARY * 0.9:
                    bid = min(bid, DAILY_SALARY * 0.72)
                else:
                    bid = max(bid, highest_prev_bid + 1.5)

    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.96)
    elif hp >= 8 and no_water_days == 0 and not scarcity:
        bid = min(bid, DAILY_SALARY * 0.28)

    if budget < bid:
        bid = budget

    if bid < 0:
        bid = 0

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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
    danger_bids = []
    rich_bids = []

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                    danger_bids.append(float(bid))
                if opp.get('budget', 0) >= budget * 0.9:
                    rich_bids.append(float(bid))

    if len(alive) == 0:
        if no_water_days >= 1 or hp <= 3:
            return float(min(budget, 35.0))
        return float(min(budget, 18.0))

    low_supply = supply <= 17
    high_supply = supply >= 22

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    danger_ref = max(danger_bids) if danger_bids else highest_prev
    rich_ref = max(rich_bids) if rich_bids else highest_prev

    urgency = 0
    if no_water_days >= 2:
        urgency = 3
    elif no_water_days >= 1 or hp <= 4:
        urgency = 2
    elif hp <= 7:
        urgency = 1

    if urgency == 3:
        base = max(78.0, danger_ref + 3.0, rich_ref + 2.0)
        if low_supply:
            base += 8.0
        return float(min(budget, base))

    if urgency == 2:
        base = max(62.0, avg_prev + 4.0, danger_ref + 2.0)
        if low_supply:
            base += 6.0
        elif high_supply:
            base -= 4.0
        return float(max(0.0, min(budget, base)))

    if highest_prev >= 85.0:
        base = 16.0 if hp > 6 else 38.0
        if low_supply and hp <= 6:
            base += 8.0
        return float(min(budget, base))

    base = max(26.0, avg_prev * 0.72)
    if rich_ref > 0:
        base = max(base, rich_ref * 0.78)
    if low_supply:
        base += 10.0
    elif high_supply:
        base -= 5.0

    if hp >= 8 and no_water_days == 0:
        base -= 4.0

    if base > budget:
        base = budget
    if base < 0:
        base = 0.0

    return float(base)
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_threat = 0
    desperate_threat = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_threat += 1
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_threat += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    total_players = 1 + len(alive)
    enough_for_two = supply >= 2 * WATER_REQ
    enough_for_three = supply >= 3 * WATER_REQ

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

    if not enough_for_two:
        urgency += 2
    if len(alive) >= 3 and not enough_for_three:
        urgency += 1

    if rich_threat >= 2:
        urgency += 1
    if desperate_threat >= 2:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        target = max(0.95 * DAILY_SALARY, highest_prev + 3.0)
    elif urgency >= 4:
        target = max(0.82 * DAILY_SALARY, avg_prev + 2.0, highest_prev * 0.72)
    elif urgency >= 2:
        if enough_for_two:
            target = max(0.42 * DAILY_SALARY, min(highest_prev * 0.55, 0.68 * DAILY_SALARY))
        else:
            target = max(0.62 * DAILY_SALARY, highest_prev * 0.66)
    else:
        if enough_for_two:
            target = 0.24 * DAILY_SALARY
        else:
            target = 0.45 * DAILY_SALARY

    if highest_prev >= 140:
        if urgency <= 2 and hp >= 5:
            target = min(target, 26.0)
        else:
            target = max(target, 61.0)

    if budget < target:
        if hp <= 2 or no_water >= 1:
            target = budget
        else:
            target = min(budget, target)

    floor_bid = 6.0 if hp >= 6 and no_water == 0 else 12.0
    bid = max(floor_bid, target)
    bid = min(budget, bid)

    if hp <= 1 or no_water >= 2:
        bid = min(budget, max(bid, highest_prev + 4.0, 64.0))

    return float(max(0.0, bid))
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

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.2))

    units = supply / float(WATER_REQ)
    tight = units < (1 + len(alive_opponents) * 0.55)
    very_tight = units < (1 + len(alive_opponents) * 0.4)
    abundant = units >= (1 + len(alive_opponents) * 0.9)

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water >= 2:
        bid = DAILY_SALARY * 0.98
    elif hp <= 4 or no_water >= 1:
        if very_tight:
            bid = max(DAILY_SALARY * 0.9, highest_prev + 6)
        else:
            bid = max(DAILY_SALARY * 0.78, highest_prev + 2)
    else:
        if very_tight:
            bid = max(DAILY_SALARY * 0.88, highest_prev + 4)
        elif tight:
            bid = max(DAILY_SALARY * 0.68, highest_prev + 1.5)
        elif abundant:
            bid = DAILY_SALARY * 0.26
        else:
            bid = DAILY_SALARY * 0.48

    if urgent_opp >= 1 and not abundant:
        bid += 4
    if rich_opp >= 2 and tight:
        bid += 3
    if day >= 8 and hp <= 5:
        bid += 5

    if abundant and hp >= 6 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.4)

    if highest_prev >= DAILY_SALARY * 0.9 and hp >= 5 and no_water == 0 and not very_tight:
        bid = min(bid, DAILY_SALARY * 0.55)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(bid)
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
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, safe_bid)))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    opp_req_pressure = 0.0

    for opp in alive_opponents:
        opp_req_pressure += float(opp.get('water_requirement', WATER_REQ))
        if float(opp.get('budget', 0.0)) >= 180:
            rich_count += 1
        if float(opp.get('hp', 10)) <= 3 or int(opp.get('no_water_days', 0)) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0.0
    if supply <= 16:
        scarcity = 1.0
    elif supply <= 18:
        scarcity = 0.7
    elif supply <= 21:
        scarcity = 0.4
    else:
        scarcity = 0.15

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.65
    elif hp <= 6:
        urgency += 0.35

    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days >= 1:
        urgency += 0.45

    market_pressure = 0.0
    if highest_prev >= 260:
        market_pressure = 1.0
    elif highest_prev >= 210:
        market_pressure = 0.8
    elif highest_prev >= 150:
        market_pressure = 0.55
    elif highest_prev >= 90:
        market_pressure = 0.3
    else:
        market_pressure = 0.1

    opponent_threat = min(1.0, 0.22 * rich_count + 0.18 * desperate_count)

    score = 0.38 * scarcity + 0.34 * urgency + 0.18 * market_pressure + 0.10 * opponent_threat

    if hp >= 8 and no_water_days == 0 and supply >= 22 and highest_prev >= 180:
        score -= 0.18

    if day >= 8:
        score += 0.08
    if day >= 9:
        score += 0.08

    if score < 0.18:
        bid = DAILY_SALARY * 0.28
    elif score < 0.35:
        bid = DAILY_SALARY * 0.48
    elif score < 0.52:
        bid = max(DAILY_SALARY * 0.72, avg_prev * 0.55)
    elif score < 0.72:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    else:
        bid = max(DAILY_SALARY * 1.2, highest_prev + 8.0)

    if scarcity >= 0.7 and urgency >= 0.65:
        bid = max(bid, highest_prev + 10.0, DAILY_SALARY * 1.35)

    reserve = 0.0
    days_left = max(0, 10 - day)
    if days_left >= 3 and hp >= 5:
        reserve = DAILY_SALARY * 0.35
    elif days_left >= 1 and hp >= 3:
        reserve = DAILY_SALARY * 0.15

    max_affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)

    if budget < DAILY_SALARY * 0.5:
        bid = min(bid, budget)

    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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

    alive_opps = []
    prev_bids = []
    rich_aggressive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('budget', 0) >= 400 and opp.get('hp', 0) >= 6:
                rich_aggressive += 1

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.45

    if day >= 8:
        urgency += 0.2

    if supply >= 23:
        base = 8.0
    elif supply >= 21:
        base = 14.0
    elif supply >= 19:
        base = 24.0
    elif supply >= 17:
        base = 42.0
    else:
        base = 68.0

    if highest_prev >= 180:
        pressure_bid = 0.0
    elif highest_prev >= 140:
        pressure_bid = min(highest_prev + 3.0, 120.0)
    elif highest_prev > 0:
        pressure_bid = highest_prev + 2.0
    else:
        pressure_bid = 35.0

    bid = max(base, pressure_bid * (0.35 + 0.45 * scarcity))

    if rich_aggressive >= 2 and urgency < 0.9 and supply >= 19:
        bid *= 0.55

    if urgency >= 1.8:
        bid = max(bid, 135.0 + 25.0 * scarcity)
    elif urgency >= 1.0:
        bid = max(bid, 85.0 + 20.0 * scarcity)

    reserve = 0.0
    if hp > 4 and day <= 7:
        reserve = 35.0
    cap = max(0.0, budget - reserve)
    if urgency >= 1.0:
        cap = budget

    bid = min(bid, cap)
    bid = max(0.0, bid)

    if budget < 25:
        bid = budget

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
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    aggressive_pressure = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                try:
                    b = float(bid)
                    prev_bids.append(b)
                    if b >= 120:
                        aggressive_pressure += 1
                except Exception:
                    pass

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.55
    if no_water >= 2:
        danger += 1.0
    elif no_water == 1:
        danger += 0.45
    danger += 0.35 * scarcity

    if danger >= 1.6:
        target = max(95.0, highest_prev + 4.0)
    elif danger >= 0.9:
        target = max(58.0, min(110.0, highest_prev * 0.55 + 8.0))
    else:
        if highest_prev >= 150:
            target = 16.0 + 10.0 * (1.0 - scarcity)
        elif highest_prev >= 90:
            target = 24.0 + 8.0 * (1.0 - scarcity)
        else:
            target = 34.0 + 10.0 * scarcity + 0.08 * avg_prev

    if aggressive_pressure >= 2 and danger < 1.2:
        target *= 0.72

    if day >= 8 and hp >= 6 and no_water == 0:
        target *= 0.85

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if hp > 4:
        reserve_floor = min(budget * 0.6, days_left * 18.0)

    cap = budget - reserve_floor
    if danger >= 1.2:
        cap = budget
    if cap < 0:
        cap = budget * 0.35

    bid = min(budget, cap, target)

    min_live = 8.0
    if danger >= 0.9:
        min_live = 42.0
    elif scarcity > 0.6:
        min_live = 24.0

    bid = max(min_live, bid)
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0.0)
                prev_bids.append(b)
                if b >= 90:
                    dangerous_prev.append(b)

    if not alive_opps:
        return float(min(budget, 18.0))

    alive_count = len(alive_opps)
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    need = 0.0
    if hp <= 2:
        need += 1.0
    elif hp <= 4:
        need += 0.55
    if no_water_days >= 2:
        need += 1.0
    elif no_water_days == 1:
        need += 0.45

    pressure = 0.0
    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if top_prev >= 120:
            pressure += 0.2
        elif top_prev >= 80:
            pressure += 0.12
        pressure += min(0.18, avg_prev / 700.0)

    if alive_count <= 2:
        pressure += 0.08

    base = 16.0 + 18.0 * scarcity + 10.0 * pressure

    if need >= 1.5:
        bid = 62.0 + 12.0 * scarcity
    elif need >= 0.8:
        bid = 46.0 + 10.0 * scarcity + 6.0 * pressure
    else:
        bid = base

    if supply <= WATER_REQ:
        bid += 12.0
    elif supply <= WATER_REQ * 1.35:
        bid += 6.0

    if dangerous_prev and hp > 4 and no_water_days == 0 and supply >= 20:
        bid -= 6.0

    if day >= 8:
        bid += 6.0 * need + 4.0 * scarcity

    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0 and hp > 3 and no_water_days == 0:
        soft_cap = min(soft_cap, budget / float(reserve_days) + 18.0)

    bid = max(0.0, min(bid, soft_cap, budget))

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 64.0))

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
            alive.append((oid, opp))

    if not alive:
        return max(0.0, min(budget, 18.0))

    slots = int(supply / WATER_REQ)
    if slots < 0:
        slots = 0

    pressure_bids = []
    weak_count = 0
    rich_aggressive = 0
    urgent_opp = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            pressure_bids.append(float(pbid))
        obudget = float(opp.get('budget', 0.0))
        ohp = float(opp.get('hp', 0.0))
        onw = int(opp.get('no_water_days', 0))
        if obudget < 50 or ohp <= 3:
            weak_count += 1
        if obudget >= 120 and pbid is not None and float(pbid) >= 100:
            rich_aggressive += 1
        if onw >= 2 or ohp <= 2:
            urgent_opp += 1

    highest_prev = max(pressure_bids) if pressure_bids else 0.0
    avg_prev = sum(pressure_bids) / len(pressure_bids) if pressure_bids else 0.0

    my_urgent = (no_water >= 2) or (hp <= 2)
    my_semi_urgent = (no_water >= 1) or (hp <= 4)

    if slots >= len(alive) + 1:
        bid = 8.0
    elif my_urgent:
        target = max(118.0, highest_prev + 6.0)
        if rich_aggressive >= 2:
            target = max(target, 132.0)
        bid = target
    elif slots == 0:
        bid = 0.0
    elif slots == 1:
        if rich_aggressive >= 2 and not my_semi_urgent:
            bid = 22.0
        elif highest_prev >= 140:
            bid = 26.0 if not my_semi_urgent else 108.0
        elif highest_prev >= 110:
            bid = 38.0 if not my_semi_urgent else highest_prev + 3.0
        elif highest_prev >= 80:
            bid = 52.0 if not my_semi_urgent else highest_prev + 2.0
        else:
            bid = max(48.0, avg_prev + 4.0)
    else:
        if highest_prev >= 120:
            bid = 72.0 if not my_semi_urgent else 110.0
        elif highest_prev >= 90:
            bid = 68.0
        else:
            bid = 54.0

    if weak_count >= 2 and not my_semi_urgent:
        bid -= 8.0
    if urgent_opp >= slots and my_semi_urgent:
        bid += 10.0

    if budget < 35:
        bid = min(bid, budget)
    elif budget < 80 and not my_urgent:
        bid = min(bid, 62.0)

    if hp >= 8 and no_water == 0 and rich_aggressive >= 2 and slots <= 1:
        bid = min(bid, 28.0)

    if bid < 0:
        bid = 0.0
    return max(0.0, min(float(budget), float(bid)))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = 0.0
    eric_prev = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid > strong_prev:
                    strong_prev = bid
                if agent_id == 'Eric':
                    eric_prev = bid

    if not alive:
        return min(budget, 18.0)

    competitor_count = len(alive) + 1
    scarcity = supply / float(WATER_REQ * competitor_count)

    urgent = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if scarcity < 0.45:
        base = 78.0
    elif scarcity < 0.6:
        base = 60.0
    elif scarcity < 0.8:
        base = 42.0
    else:
        base = 24.0

    if prev_bids:
        target_prev = strong_prev
        if eric_prev is not None and eric_prev >= 70.0:
            target_prev = eric_prev
        if urgent:
            bid = max(base, min(180.0, target_prev + 2.0))
        elif pressured:
            bid = max(base, min(120.0, target_prev * 0.72 + 3.0))
        else:
            if target_prev >= 100.0:
                bid = max(base, 26.0)
            elif target_prev >= 60.0:
                bid = max(base, target_prev * 0.52)
            else:
                bid = max(base, target_prev + 1.5)
    else:
        if urgent:
            bid = 75.0
        elif pressured:
            bid = 48.0
        else:
            bid = base

    if budget < 35.0:
        bid = min(bid, budget)
    elif budget < 80.0:
        bid = min(bid, budget * 0.92)
    else:
        bid = min(bid, budget * 0.68)

    if urgent and budget > 0:
        bid = max(bid, min(budget, 65.0))

    if hp >= 8 and no_water_days == 0 and scarcity > 0.75:
        bid = min(bid, 22.0)

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""
