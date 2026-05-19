# ============================================================
# Experiment: exp_098
# Agent: Alex
# Source: exp_098
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
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return max(0, min(budget, base))

    prev_bids = []
    distressed_count = 0
    rich_aggressive = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 2:
            distressed_count += 1
        if opp.get('budget', 0) > budget and opp.get('daily_salary', 0) >= DAILY_SALARY:
            rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    if hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * 0.95
    elif no_water_days >= 1:
        bid = DAILY_SALARY * 0.78
    else:
        if supply >= 22:
            bid = DAILY_SALARY * 0.38
        elif supply >= 19:
            bid = DAILY_SALARY * 0.5
        else:
            bid = DAILY_SALARY * 0.62

        if highest_prev >= DAILY_SALARY * 0.9:
            bid = min(bid, DAILY_SALARY * 0.42) if hp >= 4 else max(bid, DAILY_SALARY * 0.88)
        elif highest_prev >= DAILY_SALARY * 0.7:
            bid = max(bid, min(DAILY_SALARY * 0.72, highest_prev + 1.0))
        elif highest_prev > 0:
            bid = max(bid, min(DAILY_SALARY * 0.6, avg_prev + 1.5))

        if distressed_count >= 2 and hp >= 4:
            bid *= 0.9
        if rich_aggressive >= 2 and supply < 18 and hp <= 4:
            bid = max(bid, DAILY_SALARY * 0.82)

    if budget < DAILY_SALARY * 0.6:
        if hp >= 4 and no_water_days == 0:
            bid = min(bid, budget * 0.55)
        else:
            bid = min(bid, max(budget * 0.75, 1))

    return max(0, min(budget, bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    moderate_bids = []
    reckless_bids = []
    urgent_opponents = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if not opp.get('alive'):
            continue
        alive.append(opp)
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
            if bid <= 80:
                moderate_bids.append(bid)
            else:
                reckless_bids.append(bid)

    if budget <= 0:
        return 0.0

    if len(alive) == 0:
        safe = DAILY_SALARY * 0.25
        if hp <= 3 or no_water_days >= 1:
            safe = DAILY_SALARY * 0.45
        return float(min(budget, safe))

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    if moderate_bids:
        anchor = max(moderate_bids)
    elif prev_bids:
        anchor = max(prev_bids) * 0.55
    else:
        anchor = DAILY_SALARY * 0.45

    bid = anchor + 2.0

    if scarcity == 1:
        bid += 6.0
    elif scarcity == 2:
        bid += 14.0

    if urgent_opponents >= 2:
        bid += 5.0
    elif urgent_opponents == 1:
        bid += 2.0

    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.78)
    elif hp >= 8 and scarcity == 0 and reckless_bids:
        bid = min(bid, anchor)

    if budget < DAILY_SALARY * 0.9:
        bid = min(bid, budget * 0.72)
    elif budget < DAILY_SALARY * 1.5:
        bid = min(bid, budget * 0.82)

    floor_bid = 0.0
    if hp <= 2:
        floor_bid = min(budget, DAILY_SALARY * 0.7)
    elif hp <= 4 or no_water_days >= 1:
        floor_bid = min(budget, DAILY_SALARY * 0.55)
    elif scarcity >= 1:
        floor_bid = min(budget, DAILY_SALARY * 0.4)
    else:
        floor_bid = min(budget, DAILY_SALARY * 0.22)

    bid = max(bid, floor_bid)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
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

    alive_opps = []
    prev_bids = []
    urgent_prev_bids = []
    rich_opp_count = 0

    for oid, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive_opps.append(opp)
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_opp_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_prev_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, 18.0))

    high_pressure = max(prev_bids) if prev_bids else 0.0
    urgent_pressure = max(urgent_prev_bids) if urgent_prev_bids else high_pressure

    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_tightness < 0:
        supply_tightness = 0.0
    if supply_tightness > 1:
        supply_tightness = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.7
    elif hp <= 4:
        danger += 0.4
    if no_water >= 2:
        danger += 0.7
    elif no_water >= 1:
        danger += 0.35
    if day >= 8:
        danger += 0.15
    if danger > 1.0:
        danger = 1.0

    base = 18.0 + 24.0 * supply_tightness + 10.0 * min(rich_opp_count, 2)

    if danger >= 0.85:
        target = max(base + 35.0, urgent_pressure + 3.0, 62.0)
    elif danger >= 0.45:
        target = max(base + 18.0, urgent_pressure + 2.0, 42.0)
    else:
        if supply >= 22:
            target = max(12.0, min(base, high_pressure * 0.45 if high_pressure > 0 else 16.0))
        elif supply >= 19:
            target = max(20.0, min(base + 4.0, high_pressure * 0.7 if high_pressure > 0 else 26.0))
        else:
            target = max(base + 10.0, high_pressure + 1.5 if high_pressure > 0 else 34.0)

    if budget < DAILY_SALARY * 0.6 and danger < 0.45:
        target *= 0.82
    elif budget > DAILY_SALARY * 1.8 and (supply <= 18 or danger >= 0.45):
        target += 6.0

    if hp >= 8 and no_water == 0 and supply >= 23:
        target = min(target, 16.0)

    bid = min(float(budget), float(target))
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = DAILY_SALARY * 0.25
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    strong_prev = []
    weak_prev = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = float(prev['bid'])
            prev_bids.append(bid)
            if opp.get('budget', 0) >= 200:
                strong_prev.append(bid)
            else:
                weak_prev.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strong_high = max(strong_prev) if strong_prev else highest_prev
    weak_high = max(weak_prev) if weak_prev else 0.0

    alive_count = len(alive) + 1
    pressure = alive_count * WATER_REQ - supply

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

    if pressure >= WATER_REQ * 2:
        urgency += 2
    elif pressure > 0:
        urgency += 1

    if day >= 8:
        urgency += 1

    if supply >= 24:
        bid = DAILY_SALARY * 0.22
    elif supply >= 21:
        bid = DAILY_SALARY * 0.35
    elif supply >= 18:
        bid = DAILY_SALARY * 0.5
    else:
        bid = DAILY_SALARY * 0.68

    if prev_bids:
        if urgency >= 5:
            target = max(DAILY_SALARY * 0.92, strong_high + 1.0)
            bid = max(bid, target)
        elif urgency >= 3:
            target = max(DAILY_SALARY * 0.72, min(strong_high + 0.75, DAILY_SALARY * 0.95))
            bid = max(bid, target)
        elif pressure > 0:
            target = max(DAILY_SALARY * 0.48, min(weak_high + 0.5, DAILY_SALARY * 0.7))
            bid = max(bid, target)
        else:
            bid = max(bid, min(DAILY_SALARY * 0.42, highest_prev * 0.45 if highest_prev > 0 else DAILY_SALARY * 0.3))

    if hp >= 8 and no_water_days == 0 and supply >= 21:
        bid = min(bid, DAILY_SALARY * 0.38)

    reserve = 0.0
    if hp <= 4 or no_water_days >= 1:
        reserve = 0.0
    elif day <= 3:
        reserve = DAILY_SALARY * 2.0
    else:
        reserve = DAILY_SALARY * 1.0

    affordable = max(0.0, budget - reserve)
    if urgency >= 5:
        affordable = budget
    elif affordable <= 0:
        affordable = min(budget, DAILY_SALARY * 0.45)

    bid = min(bid, affordable, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= budget * 0.9:
                rich_threat += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if len(alive_opponents) == 0:
        if hp <= 2 or no_water >= 2:
            return float(min(budget, 56.0))
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (25.0 - float(supply)) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.28
    if no_water >= 2:
        urgency += 0.45
    elif no_water == 1:
        urgency += 0.18
    urgency += scarcity * 0.22
    if day >= 8:
        urgency += 0.08
    if rich_threat >= 2:
        urgency += 0.06

    if urgency >= 0.9:
        target = max(63.0, highest_prev + 2.0)
    elif urgency >= 0.55:
        target = max(46.0 + 10.0 * scarcity, min(highest_prev + 1.5, 78.0))
    elif urgency >= 0.3:
        target = max(28.0 + 8.0 * scarcity, min(avg_prev * 0.55 + 6.0, 48.0))
    else:
        target = 16.0 + 10.0 * scarcity
        if highest_prev >= 120.0:
            target = min(target, 20.0)

    if budget < 80:
        target = min(target, budget * 0.72)
    elif budget < 140:
        target = min(target, budget * 0.62)
    else:
        target = min(target, budget * 0.5)

    if hp <= 2 or no_water >= 2:
        floor_bid = 40.0
        if target < floor_bid:
            target = floor_bid

    if target < 0:
        target = 0.0
    if target > budget:
        target = budget

    return float(round(target, 2))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    cindy_bid = None
    dangerous_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 60:
                dangerous_count += 1
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if bid is not None and float(bid) > 80:
                cindy_bid = float(bid)

    if cindy_bid is None:
        cindy_bid = 122.7

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    critical = hp <= 3 or no_water >= 2
    strained = hp <= 5 or no_water >= 1

    if critical:
        bid = min(budget, max(95.0, cindy_bid + 2.0))
        return float(max(0.0, bid))

    if slots >= 2:
        if dangerous_count <= 1:
            bid = 22.0
        else:
            bid = 36.0
        if strained:
            bid = max(bid, 48.0)
        if day >= 8:
            bid += 8.0
        return float(max(0.0, min(budget, bid)))

    pressure_bid = max(78.0, cindy_bid - 4.0)
    if strained:
        pressure_bid = max(pressure_bid, cindy_bid + 1.0)
    if day >= 8:
        pressure_bid += 6.0
    return float(max(0.0, min(budget, pressure_bid)))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return float(min(budget, 1.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0
    rich_opp = max(opp_budgets) if opp_budgets else 0.0

    severe_need = hp <= 3 or no_water_days >= 2
    moderate_need = hp <= 5 or no_water_days >= 1

    tight_supply = supply <= 16
    medium_supply = supply <= 20

    if severe_need:
        bid = min(budget, max(95.0, min(145.0, max_prev + 2.0)))
        return float(max(0.0, bid))

    if tight_supply:
        if max_prev >= 140:
            bid = 91.0 if hp >= 7 else 111.0
        else:
            bid = max(72.0, max_prev + 1.5)
        return float(min(budget, max(0.0, bid)))

    if medium_supply:
        if moderate_need:
            if max_prev >= 140:
                bid = 76.0
            else:
                bid = max(58.0, min(88.0, max_prev + 1.0))
        else:
            bid = 41.0 if rich_opp > 500 else 52.0
        return float(min(budget, max(0.0, bid)))

    if hp >= 8 and no_water_days == 0:
        bid = 18.0 if max_prev >= 100 else 28.0
    elif moderate_need:
        bid = 49.0
    else:
        bid = 34.0

    if day >= 8 and hp <= 6:
        bid = max(bid, 63.0)

    return float(min(budget, max(0.0, bid)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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
    opp_budgets = []
    opp_urgent = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                opp_urgent += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_opp_budget = max(opp_budgets) if opp_budgets else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        bid = max(DAILY_SALARY * 1.15, highest_prev + 3.0)
    elif hp <= 4 or no_water >= 1:
        if tight_supply:
            bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.82, avg_prev * 0.92)
    else:
        if highest_prev >= 110:
            bid = DAILY_SALARY * (0.28 if loose_supply else 0.38)
        elif highest_prev >= 90:
            bid = DAILY_SALARY * (0.34 if loose_supply else 0.48)
        else:
            bid = max(DAILY_SALARY * 0.42, highest_prev * 0.72)

    if opp_urgent >= 2 and hp > 4:
        bid *= 0.88
    if tight_supply:
        bid *= 1.12
    if loose_supply:
        bid *= 0.9

    if budget < DAILY_SALARY * 2:
        bid *= 0.82
    elif budget > max_opp_budget + 120 and (hp <= 4 or no_water >= 1):
        bid *= 1.08

    if day >= 8 and hp > 5 and no_water == 0:
        bid *= 0.9

    bid = max(0.0, min(budget, bid))
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
    affordable_threats = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                affordable_threats.append(min(float(bid), float(opp.get('budget', 0))))

    if not alive:
        return float(max(0, min(budget, DAILY_SALARY * 0.35)))

    strongest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_affordable = max(affordable_threats) if affordable_threats else 0.0

    scarcity = WATER_REQ / supply
    urgent = (hp <= 3) or (no_water_days >= 1)
    critical = (hp <= 2) or (no_water_days >= 2)
    ample_supply = supply >= 22
    tight_supply = supply <= 17

    if critical:
        bid = max(DAILY_SALARY * 1.05, strongest_affordable + 2.0)
    elif urgent:
        bid = max(DAILY_SALARY * 0.9, strongest_affordable + 1.5)
    else:
        if ample_supply:
            bid = max(DAILY_SALARY * 0.28, strongest_affordable * 0.55)
        elif tight_supply:
            if strongest_prev >= 160:
                bid = DAILY_SALARY * 0.62
            elif strongest_prev >= 110:
                bid = max(DAILY_SALARY * 0.72, strongest_affordable + 1.0)
            else:
                bid = DAILY_SALARY * 0.68
        else:
            if strongest_prev >= 170:
                bid = DAILY_SALARY * 0.45
            elif strongest_prev >= 120:
                bid = max(DAILY_SALARY * 0.63, strongest_affordable + 1.0)
            else:
                bid = DAILY_SALARY * (0.52 + 0.18 * scarcity)

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.92
    if day >= 8 and urgent:
        bid *= 1.08

    min_safe = 0.0
    if critical:
        min_safe = DAILY_SALARY * 0.85
    elif urgent:
        min_safe = DAILY_SALARY * 0.6

    bid = max(min_safe, bid)
    bid = min(budget, bid)
    if budget <= 0:
        return 0.0
    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, 18.0))

    prev_bids = []
    strong_threat = 0.0
    desperate_threat = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 0:
                if bid > strong_threat:
                    strong_threat = float(bid)
                if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                    if bid > desperate_threat:
                        desperate_threat = float(bid)

    active_rivals = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > 0:
            active_rivals += 1

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2 or no_water_days >= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if active_rivals <= 1:
        base = 12.0 if urgency == 0 else 28.0
    else:
        if scarcity == 2:
            base = 62.0
        elif scarcity == 1:
            base = 44.0
        else:
            base = 24.0

    if prev_bids:
        highest_prev = max(prev_bids)
    else:
        highest_prev = 0.0

    target = base

    if urgency >= 3:
        target = max(target, highest_prev + 3.0, desperate_threat + 2.0, 78.0)
    elif urgency == 2:
        target = max(target, min(highest_prev + 2.0, 95.0), 56.0)
    elif scarcity >= 1:
        target = max(target, min(strong_threat + 1.5, 88.0))
    else:
        if highest_prev >= 120.0:
            target = min(target, 22.0)
        elif highest_prev >= 70.0:
            target = min(max(target, 18.0), 30.0)
        else:
            target = max(target, 20.0)

    if day >= 8 and hp > 4 and no_water_days == 0:
        target *= 0.9
    if day >= 8 and urgency >= 2:
        target *= 1.1

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = 35.0
    elif hp > 2:
        reserve = 20.0

    cap = max(0.0, budget - reserve)
    if urgency >= 2:
        cap = budget

    bid = min(target, cap)

    if urgency >= 3 and bid < min(budget, 65.0):
        bid = min(budget, 65.0)
    if bid < 0:
        bid = 0.0

    return float(round(min(budget, bid), 2))
"""
