# ============================================================
# Experiment: exp_113
# Agent: Alex
# Source: exp_113
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

    budget = my_status.get('budget', 0)
    hp = my_status.get('hp', 0)
    no_water_days = my_status.get('no_water_days', 0)
    supply = day_context.get('supply', MIN_SUPPLY)
    day = day_context.get('day', 1)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        base = DAILY_SALARY * 0.22
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.55
        return min(budget, max(0, base))

    player_count = 1 + len(alive_opponents)
    expected_share = float(supply) / float(player_count)

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            bid = prev.get('bid')
            if isinstance(bid, (int, float)):
                prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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

    if expected_share < WATER_REQ / 2.0:
        danger += 2
    elif expected_share < WATER_REQ:
        danger += 1

    pressure = 0
    if highest_prev >= DAILY_SALARY * 0.9:
        pressure += 3
    elif highest_prev >= DAILY_SALARY * 0.7:
        pressure += 2
    elif highest_prev >= DAILY_SALARY * 0.45:
        pressure += 1

    if urgent_opponents >= len(alive_opponents) / 2.0:
        pressure += 1
    if rich_opponents >= len(alive_opponents) / 2.0:
        pressure += 1

    if danger >= 5:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 2.0)
    elif danger >= 3:
        bid = max(DAILY_SALARY * 0.72, highest_prev + 1.0 if highest_prev > 0 else DAILY_SALARY * 0.72)
    else:
        if expected_share >= WATER_REQ and pressure == 0:
            bid = DAILY_SALARY * 0.28
        elif pressure >= 3:
            bid = DAILY_SALARY * 0.38 if hp > 4 else DAILY_SALARY * 0.82
        elif pressure >= 1:
            bid = max(DAILY_SALARY * 0.48, avg_prev + 1.0)
        else:
            bid = DAILY_SALARY * 0.4

    if day >= 8 and hp > 4 and no_water_days == 0:
        bid *= 0.9

    reserve_floor = 0
    if hp <= 3 or no_water_days >= 1:
        reserve_floor = DAILY_SALARY * 0.65

    bid = max(bid, reserve_floor)
    bid = min(budget, bid)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    weak_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 90:
                    aggressive_count += 1
                if bid <= 40:
                    weak_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

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
    elif hp <= 6:
        urgency += 0.2

    if no_water >= 2:
        urgency += 0.9
    elif no_water >= 1:
        urgency += 0.45

    urgency += scarcity * 0.6

    if urgency >= 1.5:
        target = max(78.0, highest_prev + 2.0)
    elif urgency >= 0.9:
        target = max(52.0 + 18.0 * scarcity, min(highest_prev + 1.0, 88.0))
    else:
        if supply >= 22:
            target = 24.0 + 6.0 * (1.0 if avg_prev > 60 else 0.0)
        elif supply >= 19:
            target = 32.0 + 8.0 * scarcity
        else:
            target = 42.0 + 12.0 * scarcity

        if aggressive_count >= 2 and hp > 4 and no_water == 0:
            target = min(target, 34.0)

        if weak_count >= 2 and highest_prev < 50:
            target = max(target, highest_prev + 1.5)

    if day >= 8:
        target += 6.0
    if day >= 10:
        target += 8.0

    reserve_floor = 0.0
    if hp > 4 and no_water == 0:
        reserve_floor = DAILY_SALARY * 0.35

    affordable = max(0.0, budget - reserve_floor)
    if urgency >= 1.5:
        affordable = budget

    bid = min(target, affordable if affordable > 0 else budget)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, max(85.0, highest_prev + 3.0)))

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 100:
                    dangerous_prev.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

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
        urgency += 1

    if supply <= 17:
        urgency += 2
    elif supply <= 20:
        urgency += 1

    if day >= 8:
        urgency += 1

    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if urgency >= 6:
        bid = max(110.0, high_prev + 3.0)
    elif urgency >= 4:
        if high_prev >= 120:
            bid = 108.0
        else:
            bid = max(82.0, avg_prev * 0.78 + 6.0)
    elif urgency >= 2:
        if dangerous_prev and supply >= 20 and hp > 4:
            bid = 28.0
        else:
            bid = max(42.0, min(78.0, avg_prev * 0.55 + 4.0))
    else:
        if high_prev >= 110:
            bid = 18.0 if supply >= 19 else 32.0
        else:
            bid = 26.0 if supply >= 20 else 38.0

    if budget < bid:
        bid = budget

    min_guard = 0.0
    if hp <= 2 or no_water_days >= 2:
        min_guard = min(budget, 95.0)
    elif hp <= 4 or supply <= 17:
        min_guard = min(budget, 60.0)

    if bid < min_guard:
        bid = min_guard

    if bid < 0:
        bid = 0.0
    return float(bid)
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
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    rich_aggressive = 0
    urgent_opponents = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))
        if opp.get('budget', 0) >= 300:
            if prev and prev.get('bid') is not None and float(prev.get('bid', 0.0)) >= 120:
                rich_aggressive += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22
    my_urgent = hp <= 2 or no_water_days >= 1
    moderate_urgent = hp <= 4

    base = DAILY_SALARY * 0.42

    if loose_supply:
        base -= 8
    elif tight_supply:
        base += 10

    if rich_aggressive >= 2:
        base -= 6
    if urgent_opponents >= 1:
        base += 6

    if highest_prev_bid >= 170:
        if my_urgent:
            bid = DAILY_SALARY * 1.15
        elif moderate_urgent and tight_supply:
            bid = DAILY_SALARY * 0.95
        else:
            bid = DAILY_SALARY * 0.28
    elif highest_prev_bid >= 120:
        if my_urgent:
            bid = min(highest_prev_bid + 3.0, DAILY_SALARY * 1.2)
        elif moderate_urgent:
            bid = DAILY_SALARY * 0.82
        else:
            bid = DAILY_SALARY * 0.38
    elif highest_prev_bid > 0:
        target = max(base, avg_prev_bid + 2.5)
        if my_urgent:
            target = max(target, highest_prev_bid + 4.0)
        elif moderate_urgent:
            target = max(target, highest_prev_bid * 0.92)
        bid = target
    else:
        if my_urgent:
            bid = DAILY_SALARY * 0.9
        elif moderate_urgent:
            bid = DAILY_SALARY * 0.62
        else:
            bid = base

    remaining_days = max(0, 10 - int(day))
    reserve_floor = remaining_days * 18
    if not my_urgent and budget < reserve_floor + bid:
        bid = max(12.0, min(bid, budget - reserve_floor))

    if my_urgent:
        bid = max(bid, DAILY_SALARY * 0.78)

    bid = max(0.0, min(float(bid), float(budget)))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.85))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    serious_bids = []
    needy_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            needy_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > 0:
                    serious_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(serious_bids) / len(serious_bids) if serious_bids else 0.0

    units = int(supply / WATER_REQ)
    scarcity = units <= 1

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 3
    elif no_water_days == 1:
        urgency += 1
    if day >= 8:
        urgency += 1

    if scarcity:
        urgency += 2

    pressure = 0
    if highest_prev >= 110:
        pressure = 3
    elif highest_prev >= 90:
        pressure = 2
    elif highest_prev >= 60:
        pressure = 1

    if needy_count >= 1:
        pressure += 1
    if rich_count >= 2:
        pressure += 1

    target = 0.0

    if urgency >= 5:
        if highest_prev > 0:
            target = highest_prev + 4.0
        else:
            target = DAILY_SALARY * 0.95
    elif urgency >= 3:
        if scarcity:
            if highest_prev > 0:
                target = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
            else:
                target = DAILY_SALARY * 0.82
        else:
            if avg_prev > 0:
                target = max(DAILY_SALARY * 0.68, avg_prev + 1.5)
            else:
                target = DAILY_SALARY * 0.62
    else:
        if scarcity:
            if pressure >= 3:
                target = DAILY_SALARY * 0.28
            elif pressure == 2:
                target = DAILY_SALARY * 0.42
            else:
                target = DAILY_SALARY * 0.55
        else:
            if pressure >= 3:
                target = DAILY_SALARY * 0.22
            elif pressure == 2:
                target = DAILY_SALARY * 0.34
            else:
                target = DAILY_SALARY * 0.46

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if days_left >= 3 and urgency < 5:
        reserve_floor = DAILY_SALARY * 1.2
    if budget <= reserve_floor:
        target = min(target, DAILY_SALARY * 0.45 if urgency < 4 else DAILY_SALARY * 0.8)

    if hp >= 8 and no_water_days == 0 and scarcity and pressure >= 2:
        target = min(target, DAILY_SALARY * 0.25)

    bid = min(float(budget), float(target))
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return max(0.0, min(budget, 45.0))
        return max(0.0, min(budget, 18.0))

    prev_bids = []
    pressure_bids = []
    rich_live = 0
    desperate_live = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_live += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_live += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 0 and opp.get('hp', 10) > 0:
                pressure_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    live_pressure = max(pressure_bids) if pressure_bids else highest_prev

    units = supply / float(WATER_REQ)
    crowded = units < 1.6
    medium_tight = units < 1.9

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
        urgency += 1
    if day >= 8:
        urgency += 1

    if urgency >= 5:
        base = 0.92 * DAILY_SALARY
        if crowded:
            base = max(base, live_pressure + 4.0)
        return max(0.0, min(budget, base))

    if urgency >= 3:
        if crowded:
            bid = max(0.72 * DAILY_SALARY, min(0.95 * DAILY_SALARY, live_pressure + 2.5))
        elif medium_tight:
            bid = max(0.58 * DAILY_SALARY, min(0.82 * DAILY_SALARY, live_pressure * 0.72 + 2.0))
        else:
            bid = max(0.42 * DAILY_SALARY, min(0.68 * DAILY_SALARY, live_pressure * 0.55 + 1.5))
        return max(0.0, min(budget, bid))

    if crowded:
        if live_pressure >= 120:
            bid = 16.0
        elif live_pressure >= 80:
            bid = 22.0
        else:
            bid = max(24.0, min(40.0, live_pressure * 0.45 + 3.0))
    elif medium_tight:
        if live_pressure >= 120:
            bid = 14.0
        elif live_pressure >= 80:
            bid = 18.0
        else:
            bid = max(16.0, min(30.0, live_pressure * 0.35 + 2.0))
    else:
        bid = 12.0

    if desperate_live >= 2:
        bid += 4.0
    elif desperate_live == 1:
        bid += 2.0

    if rich_live >= 3 and live_pressure > 90:
        bid = min(bid, 20.0)

    if budget < 25:
        bid = min(bid, max(8.0, budget * 0.75))

    return max(0.0, min(budget, bid))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threats = 0
    urgent_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_threats += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

    tight_supply = supply <= 17
    roomy_supply = supply >= 22

    survival_mode = (hp <= 2) or (no_water >= 1)
    caution_mode = (hp <= 4)

    if survival_mode:
        if tight_supply:
            bid = max(92.0, second_prev + 3.0)
        else:
            bid = max(78.0, min(highest_prev * 0.72, 108.0))
        return float(min(budget, bid))

    if roomy_supply and hp >= 6 and no_water == 0:
        bid = 8.0 if rich_threats >= 2 else 14.0
        if highest_prev < 60:
            bid = max(bid, highest_prev + 1.0)
        return float(min(budget, bid))

    if tight_supply:
        if rich_threats >= 2:
            bid = 32.0 if hp >= 7 else 68.0
        else:
            bid = max(40.0, second_prev + 2.0)
        if caution_mode:
            bid = max(bid, 72.0)
        return float(min(budget, bid))

    if highest_prev >= 140:
        bid = 20.0 if hp >= 6 else 74.0
    elif highest_prev >= 110:
        bid = 24.0 if hp >= 7 else 70.0
    elif highest_prev >= 70:
        bid = max(38.0, second_prev + 1.5)
    else:
        bid = max(28.0, highest_prev + 2.0)

    if urgent_opponents >= 2 and hp >= 6 and no_water == 0:
        bid *= 0.85

    reserve_target = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    max_spend = budget
    if budget > reserve_target:
        max_spend = budget

    return float(min(max_spend, bid))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_pressure = 0
    rich_competitors = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 250:
                rich_competitors += 1
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                urgent_pressure += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.6
    elif hp <= 6:
        danger += 0.3

    if no_water_days >= 2:
        danger += 1.0
    elif no_water_days >= 1:
        danger += 0.5

    demand_units = 1 + len(alive_opponents)
    likely_tight = 1 if supply < demand_units * WATER_REQ else 0

    if hp <= 2 or no_water_days >= 2:
        bid = max(92.0, highest_prev + 2.5, DAILY_SALARY * 1.45)
    elif likely_tight:
        bid = max(78.0 + 18.0 * scarcity, avg_prev + 3.0, highest_prev * 0.96)
    else:
        bid = 28.0 + 18.0 * scarcity + 6.0 * urgent_pressure
        if highest_prev > 0:
            bid = max(bid, min(highest_prev - 8.0, 72.0))

    if day >= 8:
        bid += 6.0 * danger
    else:
        bid += 3.0 * danger

    if rich_competitors >= 2 and scarcity > 0.5:
        bid += 6.0

    if supply >= 23 and hp >= 7 and no_water_days == 0:
        bid *= 0.72
    elif supply >= 21 and hp >= 6 and no_water_days == 0:
        bid *= 0.82

    max_safe = budget
    if day <= 3:
        max_safe = min(max_safe, 95.0)
    elif day <= 6:
        max_safe = min(max_safe, 105.0)
    else:
        max_safe = min(max_safe, 120.0)

    if budget < 140:
        max_safe = min(max_safe, budget * 0.72 + 8.0)

    bid = min(bid, max_safe)
    bid = max(0.0, bid)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    weak_opp_count = 0
    rich_opp_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                weak_opp_count += 1
            if opp.get('budget', 0) >= 140:
                rich_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 1.0
    if supply <= 16:
        scarcity = 1.25
    elif supply >= 22:
        scarcity = 0.9

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 2:
        urgency = 2
    elif hp <= 6 or no_water >= 1:
        urgency = 1

    if urgency == 3:
        bid = max(0.95 * DAILY_SALARY, highest_prev + 4.0, avg_prev + 8.0)
    elif urgency == 2:
        bid = max(0.72 * DAILY_SALARY, highest_prev + 2.0)
    elif urgency == 1:
        if highest_prev >= 120:
            bid = 0.42 * DAILY_SALARY
        else:
            bid = max(0.5 * DAILY_SALARY, avg_prev * 0.9 + 3.0)
    else:
        if supply <= 16 and rich_opp_count >= 2:
            bid = 0.18 * DAILY_SALARY
        elif highest_prev >= 120:
            bid = 0.28 * DAILY_SALARY
        else:
            bid = max(0.34 * DAILY_SALARY, avg_prev * 0.6)

    if weak_opp_count >= 2 and urgency <= 1:
        bid *= 0.9

    bid *= scarcity

    if day >= 8:
        bid *= 1.08

    reserve_floor = 0.0
    if hp > 4:
        reserve_floor = 20.0
    max_affordable = max(0.0, budget - reserve_floor)
    if urgency >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    aggressive_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 90:
                    aggressive_bids.append(bid)

    if not alive:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    live_count = len(alive)

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water_days >= 1:
        danger += 2

    target = 0.0

    if danger >= 3:
        target = max(62.0, max_prev + 2.0)
    elif danger == 2:
        if tight_supply:
            target = max(54.0, max_prev + 1.0)
        else:
            target = max(44.0, avg_prev * 0.72)
    else:
        if tight_supply:
            if aggressive_bids:
                target = max(36.0, min(max_prev * 0.72, 88.0))
            else:
                target = max(32.0, avg_prev * 0.8)
        elif medium_supply:
            target = max(24.0, avg_prev * 0.5)
        else:
            target = 16.0 + 1.5 * max(0, live_count - 2)

    if day >= 8 and hp > 6 and budget < 140:
        target *= 0.85
    if day >= 8 and danger >= 2:
        target = max(target, 58.0)

    if budget < DAILY_SALARY:
        target = min(target, budget * 0.92)
    else:
        target = min(target, budget * 0.75)

    if hp <= 2:
        target = max(target, min(budget, 66.0))

    if target < 0:
        target = 0.0
    if target > budget:
        target = budget

    return float(round(target, 2))
"""
