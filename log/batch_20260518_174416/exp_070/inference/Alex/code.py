# ============================================================
# Experiment: exp_070
# Agent: Alex
# Source: exp_070
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    if not alive:
        if hp <= 2 or no_water >= 1:
            return min(budget, 40)
        return min(budget, 18)

    total_players = 1 + len(alive)
    expected_winners = max(1, int(supply // WATER_REQ))
    scarcity = total_players - expected_winners

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_opp += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    if hp <= 2 or no_water >= 2:
        base = 63
    elif hp <= 4 or no_water >= 1:
        base = 49
    else:
        if scarcity <= 0:
            base = 16
        elif scarcity == 1:
            base = 28
        elif scarcity == 2:
            base = 38
        else:
            base = 47

    pressure = 0
    if highest_prev >= 60:
        pressure += 6
    elif highest_prev >= 45:
        pressure += 3
    elif highest_prev > 0:
        pressure += 1

    if avg_prev >= 50:
        pressure += 3
    elif avg_prev >= 35:
        pressure += 1

    pressure += min(6, desperate_opp * 2)
    pressure += min(4, rich_opp)

    bid = base + pressure

    if prev_bids and hp > 2 and no_water == 0:
        target = highest_prev + 2
        if scarcity <= 1:
            target = min(target, 40)
        bid = max(bid, target)

    if scarcity <= 0 and hp > 4 and no_water == 0:
        bid = min(bid, 24)

    if budget < 25:
        if hp <= 2 or no_water >= 1:
            bid = budget
        else:
            bid = min(bid, max(0, budget * 0.6))
    elif budget < bid:
        if hp <= 2 or no_water >= 1:
            bid = budget
        else:
            bid = max(0, min(budget, highest_prev + 1 if highest_prev > 0 else budget * 0.5))

    bid = max(0, min(budget, bid))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    total_players = 1 + len(alive_opponents)
    tightness = float(total_players * WATER_REQ) / max(1.0, supply)

    urgent_prev_bids = []
    all_prev_bids = []
    rich_aggressive = []

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            all_prev_bids.append(float(bid))
            opp_urgent = (opp.get('hp', 10) <= 3) or (opp.get('no_water_days', 0) >= 2)
            if opp_urgent:
                urgent_prev_bids.append(float(bid))
            if opp.get('budget', 0) > budget and float(bid) >= DAILY_SALARY * 0.9:
                rich_aggressive.append(float(bid))

    highest_prev = max(all_prev_bids) if all_prev_bids else 0.0
    highest_urgent_prev = max(urgent_prev_bids) if urgent_prev_bids else highest_prev
    pressure_bid = highest_urgent_prev
    if rich_aggressive:
        pressure_bid = max(pressure_bid, max(rich_aggressive))

    emergency = (hp <= 2) or (no_water_days >= 2)
    caution = (hp <= 4) or (no_water_days >= 1)

    if emergency:
        bid = max(DAILY_SALARY * 0.95, pressure_bid + 2.0)
        return float(max(0.0, min(budget, bid)))

    if tightness >= 2.8:
        if caution:
            bid = max(DAILY_SALARY * 0.82, pressure_bid + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.58, min(pressure_bid + 1.0, DAILY_SALARY * 0.88))
    elif tightness >= 2.2:
        if caution:
            bid = max(DAILY_SALARY * 0.68, min(pressure_bid + 1.0, DAILY_SALARY * 0.82))
        else:
            bid = max(DAILY_SALARY * 0.45, min(pressure_bid * 0.72, DAILY_SALARY * 0.7))
    else:
        if caution:
            bid = DAILY_SALARY * 0.42
        else:
            bid = DAILY_SALARY * 0.22

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.9

    min_safe = 0.0
    if caution and supply <= 18:
        min_safe = DAILY_SALARY * 0.4
    bid = max(bid, min_safe)

    if budget < DAILY_SALARY * 0.5 and not emergency:
        bid = min(bid, budget * 0.55)

    return float(max(0.0, min(budget, bid)))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    weak_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) <= DAILY_SALARY * 1.2 or opp.get('hp', 0) <= 3:
                weak_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= DAILY_SALARY * 1.2:
                    dangerous_prev.append(bid)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.6
    max_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.8

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
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.45

    base = DAILY_SALARY * (0.34 + 0.36 * scarcity)

    if urgency >= 1.5:
        target = max(base, max_prev + 6.0, DAILY_SALARY * 1.05)
    elif urgency >= 0.8:
        target = max(base, avg_prev * 0.78 + 4.0, DAILY_SALARY * 0.72)
    else:
        if scarcity < 0.25 and len(dangerous_prev) >= 2:
            target = DAILY_SALARY * 0.22
        elif scarcity < 0.45 and weak_opponents >= 2:
            target = DAILY_SALARY * 0.28
        else:
            target = max(base, min(avg_prev * 0.62 + 2.0, DAILY_SALARY * 0.68))

    if day >= 8:
        target *= 1.08
    if budget < DAILY_SALARY:
        target = min(target, budget * 0.92)
    elif budget > DAILY_SALARY * 6 and urgency > 0:
        target *= 1.08

    if hp >= 8 and no_water_days == 0 and scarcity < 0.2 and max_prev > DAILY_SALARY * 1.8:
        target = min(target, DAILY_SALARY * 0.2)

    target = max(0.0, min(float(budget), float(target)))
    return float(round(target, 2))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_pressure = 0
    weak_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if bid >= 140:
                    strong_pressure += 1
                if bid <= 60:
                    weak_count += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    # Scarcity estimate: with supply 15-25 and req 13, low supply is much tighter.
    if supply <= 16:
        scarcity = 'high'
    elif supply <= 20:
        scarcity = 'medium'
    else:
        scarcity = 'low'

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    emergency = hp <= 3 or no_water_days >= 2
    caution = hp <= 5 or no_water_days >= 1

    if emergency:
        if scarcity == 'high':
            bid = max(150.0, max_prev + 3.0)
        elif scarcity == 'medium':
            bid = max(120.0, avg_prev + 2.0)
        else:
            bid = max(95.0, avg_prev)
    elif caution:
        if scarcity == 'high':
            bid = max(110.0, avg_prev + 1.5)
        elif scarcity == 'medium':
            bid = 72.0 if max_prev < 100 else max(82.0, avg_prev - 8.0)
        else:
            bid = 38.0 if strong_pressure >= 2 else 52.0
    else:
        if scarcity == 'high':
            bid = 88.0 if strong_pressure >= 2 else max(76.0, avg_prev - 18.0)
        elif scarcity == 'medium':
            bid = 34.0 if strong_pressure >= 2 else 48.0
        else:
            bid = 12.0 if day < 8 else 22.0

    # Late-game survival adjustment.
    if day >= 8 and hp <= 5:
        bid = max(bid, 90.0 if scarcity != 'low' else 60.0)

    # Avoid burning out too early.
    reserve_floor = 0.0
    if day <= 6:
        reserve_floor = 140.0
    elif day <= 8:
        reserve_floor = 70.0

    affordable = budget
    if budget > reserve_floor:
        affordable = budget - reserve_floor + min(reserve_floor * 0.25, 25.0)

    bid = min(bid, affordable)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_threats = 0
    urgent_opps = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_threats += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opps += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 21.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.75
    elif hp <= 4:
        danger += 0.45
    elif hp <= 6:
        danger += 0.2

    if no_water_days >= 2:
        danger += 0.7
    elif no_water_days == 1:
        danger += 0.3

    danger += 0.35 * scarcity
    if day >= 8:
        danger += 0.1

    if danger >= 1.1:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 1.0, avg_prev * 1.03)
    elif danger >= 0.7:
        bid = max(0.68 * DAILY_SALARY, avg_prev * 0.92, highest_prev * 0.72)
    elif scarcity >= 0.75 and rich_threats >= 1:
        bid = max(0.58 * DAILY_SALARY, avg_prev * 0.75)
    else:
        bid = 0.34 * DAILY_SALARY + 6.0 * scarcity

    if highest_prev >= 145 and danger < 0.9:
        bid = min(bid, 0.46 * DAILY_SALARY)

    if urgent_opps >= 2 and danger < 0.8:
        bid = min(bid, 0.42 * DAILY_SALARY)

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = 18.0
    elif hp > 2:
        reserve = 8.0

    max_affordable = max(0.0, budget - reserve)
    bid = min(bid, max_affordable)

    if danger >= 1.0 and budget > 0:
        bid = max(bid, min(budget, 0.88 * DAILY_SALARY))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = {}
    for aid, opp in opponents_status.items():
        if opp.get('alive'):
            alive[aid] = opp

    if not alive:
        return min(budget, 18.0)

    severe_need = hp <= 3 or no_water_days >= 2
    moderate_need = hp <= 5 or no_water_days >= 1

    total_agents = 1 + len(alive)
    expected_share = float(supply) / float(total_agents)
    scarce = expected_share < WATER_REQ
    very_scarce = supply <= 17
    abundant = supply >= 22

    highest_prev = 0.0
    cindy_prev = None
    pressure_count = 0
    desperate_opp = 0

    for aid, opp in alive.items():
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            if bid > highest_prev:
                highest_prev = bid
            if bid >= 90:
                pressure_count += 1
            if aid == 'Cindy':
                cindy_prev = bid
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            desperate_opp += 1

    if cindy_prev is None:
        cindy_prev = 0.0

    if severe_need:
        target = max(78.0, cindy_prev + 3.0, highest_prev * 0.72)
        if very_scarce:
            target = max(target, 92.0)
        return float(min(budget, target))

    if abundant and not moderate_need:
        low = 8.0
        if cindy_prev >= 120:
            low = 5.0
        elif highest_prev < 40:
            low = 16.0
        return float(min(budget, low))

    if scarce:
        if cindy_prev >= 130:
            target = 54.0 if not moderate_need else 84.0
        elif cindy_prev >= 110:
            target = 60.0 if not moderate_need else 88.0
        elif cindy_prev >= 80:
            target = cindy_prev + 2.0 if moderate_need else cindy_prev - 10.0
        else:
            target = 58.0 if not moderate_need else 82.0

        if desperate_opp >= 2:
            target += 8.0
        if very_scarce:
            target += 10.0
        return float(min(budget, target))

    target = 28.0
    if moderate_need:
        target = 52.0
    if pressure_count >= 2:
        target += 8.0
    if highest_prev >= 100 and not moderate_need:
        target = 22.0

    if day >= 8 and hp >= 6 and no_water_days == 0:
        target = min(target, 20.0)

    return float(min(budget, target))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 500:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    my_urgent = (hp <= 3) or (no_water >= 1)
    critical = (hp <= 2) or (no_water >= 2)

    if critical:
        bid = max(DAILY_SALARY * 1.15, highest_prev + 3.0, 82.0)
    elif my_urgent:
        bid = max(DAILY_SALARY * 0.95, avg_prev + 2.0, 68.0)
    else:
        bid = DAILY_SALARY * (0.38 + 0.22 * scarcity)
        if highest_prev >= 150:
            bid = min(bid, DAILY_SALARY * 0.42)
        elif highest_prev >= 110:
            bid = max(bid, DAILY_SALARY * 0.52)
        elif highest_prev > 0:
            bid = max(bid, min(highest_prev + 1.5, DAILY_SALARY * 0.78))

    if urgent_opp >= 2 and not my_urgent:
        bid *= 0.9
    if rich_opp >= 2 and not my_urgent:
        bid *= 0.92

    days_left = max(0, 10 - day)
    reserve_target = days_left * DAILY_SALARY * 0.42
    max_affordable_today = budget
    if not my_urgent:
        max_affordable_today = max(0.0, budget - reserve_target)
        max_affordable_today = max(max_affordable_today, DAILY_SALARY * 0.35)

    bid = min(bid, budget)
    bid = min(bid, max_affordable_today)

    if my_urgent and bid < DAILY_SALARY * 0.75:
        bid = min(budget, DAILY_SALARY * 0.75)
    if critical and bid < DAILY_SALARY * 1.0:
        bid = min(budget, DAILY_SALARY * 1.0)

    if bid < 0:
        bid = 0.0
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if float(opp.get('budget', 0)) >= 200:
            rich_count += 1
        if float(opp.get('hp', 10)) <= 3 or int(opp.get('no_water_days', 0)) >= 2:
            desperate_count += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

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
        urgency += 1

    if tight_supply:
        urgency += 2
    elif loose_supply:
        urgency -= 1

    urgency += min(2, desperate_count)

    if day >= 8 and hp < 6:
        urgency += 1

    if highest_prev >= 140:
        if urgency <= 1:
            bid = 18.0 if loose_supply else 24.0
        elif urgency == 2:
            bid = 58.0
        elif urgency == 3:
            bid = 92.0
        else:
            bid = 148.0
    else:
        if urgency <= 0:
            bid = 16.0 if loose_supply else 22.0
        elif urgency == 1:
            bid = max(28.0, avg_prev * 0.45)
        elif urgency == 2:
            bid = max(45.0, highest_prev + 2.0 if highest_prev > 0 else 52.0)
        elif urgency == 3:
            bid = max(72.0, highest_prev + 3.0 if highest_prev > 0 else 78.0)
        else:
            bid = max(105.0, highest_prev + 4.0 if highest_prev > 0 else 110.0)

    if rich_count >= 2 and tight_supply and urgency >= 3:
        bid = max(bid, 145.0)

    reserve = 0.0
    if hp > 4 and no_water == 0:
        reserve = 20.0
    elif hp > 2:
        reserve = 8.0

    max_affordable = max(0.0, budget - reserve)
    bid = min(bid, max_affordable)

    if urgency >= 4 and budget > 0:
        bid = max(bid, min(budget, 150.0))

    if bid < 0:
        bid = 0.0

    return float(min(budget, bid))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, 18.0))

    capacity = supply / float(WATER_REQ)
    scarcity = 0
    if capacity <= 1.15:
        scarcity = 3
    elif capacity <= 1.7:
        scarcity = 2
    elif capacity <= 2.3:
        scarcity = 1

    prev_bids = []
    strong_bids = []
    weak_bids = []
    desperate_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= 700:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 90:
                strong_bids.append(float(bid))
            else:
                weak_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0
    moderate_prev = 0.0
    if weak_bids:
        moderate_prev = max(weak_bids)
    elif prev_bids:
        moderate_prev = min(prev_bids)

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    reserve_days = 10 - day
    soft_cap = budget
    if reserve_days > 0:
        keep = max(0.0, reserve_days * 8.0)
        soft_cap = max(0.0, budget - keep)
        soft_cap = min(budget, max(22.0, soft_cap))

    bid = 0.0

    if urgency >= 3:
        bid = max(95.0, highest_prev + 4.0, avg_prev + 10.0)
    elif urgency == 2:
        if scarcity >= 2:
            bid = max(78.0, moderate_prev + 3.0, avg_prev + 4.0)
        else:
            bid = max(58.0, moderate_prev + 2.0)
    else:
        if scarcity >= 3:
            bid = max(70.0, moderate_prev + 2.5)
        elif scarcity == 2:
            bid = max(44.0, min(72.0, moderate_prev + 1.5))
        elif scarcity == 1:
            bid = 26.0 if strong_bids else max(24.0, min(40.0, avg_prev * 0.45 + 8.0))
        else:
            bid = 18.0 if strong_bids or rich_opp >= 2 else 24.0

    if desperate_opp >= 2 and urgency <= 1:
        bid *= 0.82
    if rich_opp >= 2 and scarcity >= 2 and urgency >= 2:
        bid += 8.0
    if no_water >= 1 and hp <= 4:
        bid += 10.0
    if hp >= 8 and scarcity == 0:
        bid *= 0.85

    if day >= 8:
        if hp <= 4:
            bid += 12.0
        else:
            bid *= 0.95

    bid = min(bid, budget)
    bid = min(bid, soft_cap if urgency <= 1 else budget)
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
        return float(min(budget, 28.0))

    prev_bids = []
    bob_like = []
    cindy_like = []
    urgent_opp = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 110:
                cindy_like.append(float(bid))
            elif bid > 0:
                bob_like.append(float(bid))
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1

    slots = max(1, int(supply // WATER_REQ))
    tight = slots <= 1

    bob_anchor = 72.0
    if bob_like:
        bob_anchor = max(bob_like)

    cindy_anchor = 125.0
    if cindy_like:
        cindy_anchor = max(cindy_like)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(90.0, bob_anchor + 8.0))
        if tight and urgent_opp > 0:
            bid = min(budget, bid + 8.0)
        return float(max(0.0, bid))

    if hp <= 4 or no_water_days >= 1:
        if tight:
            bid = min(budget, max(82.0, bob_anchor + 3.0))
        else:
            bid = min(budget, max(68.0, bob_anchor - 2.0))
        return float(max(0.0, bid))

    if tight:
        if cindy_like:
            bid = min(budget, max(34.0, bob_anchor + 1.5))
        else:
            bid = min(budget, max(60.0, bob_anchor + 2.0))
    else:
        bid = 26.0
        if len(alive) >= 2:
            bid = 32.0
        if urgent_opp > 0:
            bid += 4.0
        if day >= 8:
            bid += 6.0
        bid = min(budget, bid)

    if budget < 120:
        bid = min(bid, budget * 0.42)
    elif budget > 500 and hp >= 7 and not tight:
        bid = max(bid, 30.0)

    return float(max(0.0, min(budget, bid)))
"""
