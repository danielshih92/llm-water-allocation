# ============================================================
# Experiment: exp_103
# Agent: Alex
# Source: exp_103
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    error_count = 0
    rich_count = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= DAILY_SALARY * 4:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))
            if prev.get('error'):
                error_count += 1

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 21)

    opp_count = len(alive_opponents)
    scarcity = opp_count * WATER_REQ - supply

    max_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    if hp <= 2 or no_water >= 2:
        base = DAILY_SALARY * 0.96
    elif hp <= 4 or no_water >= 1:
        base = DAILY_SALARY * 0.78
    else:
        if scarcity >= WATER_REQ * 2:
            base = DAILY_SALARY * 0.72
        elif scarcity > 0:
            base = DAILY_SALARY * 0.58
        else:
            base = DAILY_SALARY * 0.42

    if prev_bids:
        target = max(base, avg_prev + 2, max_prev * 0.92)
        if max_prev >= DAILY_SALARY * 0.9 and hp > 4 and no_water == 0:
            target = min(target, DAILY_SALARY * 0.38)
    else:
        target = base

    target += min(desperate_count, 3) * 2.0
    target += min(rich_count, 2) * 1.5
    target -= min(error_count, 2) * 2.0

    if supply >= 23 and hp > 4 and no_water == 0:
        target *= 0.82
    elif supply <= 17:
        target *= 1.08

    if day >= 8:
        target *= 1.08

    reserve_floor = DAILY_SALARY * max(0, 10 - day) * 0.18
    if budget < reserve_floor and hp > 3 and no_water == 0:
        target = min(target, DAILY_SALARY * 0.35)

    bid = max(0, min(budget, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        safe_bid = min(budget, DAILY_SALARY * 0.25)
        if hp <= 2 or no_water_days >= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.6)
        return float(max(0.0, safe_bid))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 300:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
    if no_water_days >= 2:
        danger += 0.35
    elif no_water_days == 1:
        danger += 0.15
    danger += scarcity * 0.25
    if day >= 8:
        danger += 0.1

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif supply <= 17:
        bid = max(DAILY_SALARY * 0.38 + scarcity * 18.0, avg_prev * 0.55 + 2.0)
    else:
        bid = DAILY_SALARY * 0.22 + scarcity * 10.0

    if highest_prev >= 120:
        if danger < 0.45:
            bid = min(bid, DAILY_SALARY * 0.28)
        else:
            bid = max(bid, DAILY_SALARY * 0.72)
    elif highest_prev >= 60:
        if danger < 0.35:
            bid = min(bid, DAILY_SALARY * 0.32)
        else:
            bid = max(bid, highest_prev * 0.78 + 2.0)
    elif highest_prev > 0:
        bid = max(bid, min(DAILY_SALARY * 0.58, highest_prev + 1.5))

    if rich_opp >= 2 and danger < 0.4:
        bid = min(bid, DAILY_SALARY * 0.26)

    if urgent_opp >= 1 and danger >= 0.4:
        bid = max(bid, DAILY_SALARY * 0.7)

    reserve_target = 0.0
    remaining_days = max(0, 10 - day)
    if remaining_days > 0:
        reserve_target = remaining_days * DAILY_SALARY * 0.18
    max_affordable = max(0.0, budget - reserve_target)
    if max_affordable <= 0:
        max_affordable = min(budget, DAILY_SALARY * 0.35)

    bid = min(bid, budget, max_affordable)
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.85))

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    day = day_context['day']
    supply = float(day_context['supply'])
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
                if float(bid) > 0:
                    dangerous_prev.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    low_supply = supply <= 17.0
    high_supply = supply >= 22.0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if low_supply:
        urgency += 2
    if day >= 8:
        urgency += 1

    highest_prev = max(dangerous_prev) if dangerous_prev else 0.0
    moderate_prev = 0.0
    for b in dangerous_prev:
        if b <= 90.0 and b > moderate_prev:
            moderate_prev = b

    if urgency >= 7:
        target = 92.0
        if highest_prev > 0 and highest_prev < 95.0:
            target = max(target, highest_prev + 2.0)
    elif urgency >= 4:
        if moderate_prev > 0:
            target = max(52.0, moderate_prev + 1.5)
        else:
            target = 58.0 if low_supply else 46.0
    else:
        if highest_prev >= 120.0:
            target = 8.0 if high_supply else 14.0
        elif highest_prev >= 85.0:
            target = 16.0 if high_supply else 24.0
        elif moderate_prev > 0:
            target = min(60.0, moderate_prev + 1.0)
        else:
            target = 22.0 if low_supply else 15.0

    reserve = 0.0
    if hp > 4 and no_water_days == 0 and day <= 7:
        reserve = 20.0
    elif hp > 2 and day <= 8:
        reserve = 10.0

    affordable = max(0.0, budget - reserve)
    bid = min(target, affordable if affordable > 0 else budget)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 88.0))
    elif hp <= 4 or no_water_days >= 1:
        bid = min(budget, max(bid, 55.0 if not low_supply else 65.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = float(budget)

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
    day = day_context['day']
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
            if opp.get('budget', 0) >= 140:
                rich_opponents += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0.0, min(budget, 18.0))

    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 2:
        emergency = max(150.0, max_prev_bid + 8.0)
        return max(0.0, min(budget, emergency))

    if hp <= 4 or no_water_days >= 1:
        if supply <= 17:
            urgent_bid = max(120.0, max_prev_bid + 5.0)
        else:
            urgent_bid = max(92.0, avg_prev_bid + 4.0)
        return max(0.0, min(budget, urgent_bid))

    if supply >= 23:
        base = 24.0
    elif supply >= 20:
        base = 38.0
    elif supply >= 18:
        base = 52.0
    else:
        base = 72.0

    if max_prev_bid <= 20:
        bid = max(base, 22.0)
    elif max_prev_bid <= 80:
        bid = max(base, max_prev_bid + 2.5)
    elif max_prev_bid <= 120:
        bid = max(base, 58.0)
    else:
        bid = max(base, 46.0)

    if urgent_opponents >= 2 and supply <= 18:
        bid += 10.0
    if rich_opponents >= 2 and supply <= 17:
        bid += 8.0
    if day >= 8 and hp >= 7:
        bid -= 6.0

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    cap = budget
    if budget > reserve_floor:
        cap = budget - reserve_floor * 0.15

    bid = min(bid, cap)
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
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

    alive = []
    prev_bids = []
    opp_reqs = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            opp_reqs.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    total_players = 1 + len(alive)
    total_req = WATER_REQ
    for r in opp_reqs:
        total_req += r

    scarcity = supply < total_req
    severe_scarcity = supply < (WATER_REQ * 2)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        bid = max(92.0, highest_prev + 4.0)
    elif severe_scarcity:
        if urgent:
            bid = max(82.0, highest_prev + 2.5)
        else:
            bid = max(61.0, avg_prev + 1.5)
    elif scarcity:
        if highest_prev >= 95.0:
            bid = 54.0 if hp >= 6 and no_water_days == 0 else 88.0
        elif highest_prev >= 75.0:
            bid = 58.0 if hp >= 6 else 79.0
        else:
            bid = max(46.0, highest_prev + 1.2)
    else:
        if hp >= 7 and no_water_days == 0:
            bid = 24.0
        elif hp >= 5:
            bid = 35.0
        else:
            bid = 52.0

    if day_context['day'] >= 8:
        bid += 6.0
    if day_context['day'] >= 9 and urgent:
        bid += 8.0

    if budget < bid:
        bid = budget

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_opp = False
    rich_opp = False

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget * 0.9:
                rich_opp = True
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.75
    elif hp <= 4:
        danger += 0.4
    if no_water_days >= 1:
        danger += 0.45
    if day >= 8:
        danger += 0.1
    if danger > 1.0:
        danger = 1.0

    base = 24.0 + 36.0 * supply_pressure + 28.0 * danger

    if highest_prev >= 150:
        target = max(base, min(highest_prev * 0.72, 118.0))
    elif highest_prev >= 110:
        target = max(base, min(highest_prev * 0.78, 102.0))
    elif highest_prev >= 70:
        target = max(base, min(highest_prev + 3.0, 88.0))
    elif highest_prev > 0:
        target = max(base, highest_prev + 2.0)
    else:
        target = base

    if supply >= 22 and hp >= 6 and no_water_days == 0:
        target *= 0.72
    elif supply <= 17:
        target *= 1.18

    if urgent_opp and hp >= 5 and no_water_days == 0:
        target *= 0.92
    if rich_opp and (hp <= 3 or no_water_days >= 1 or supply <= 17):
        target *= 1.08

    reserve = 0.0
    if day <= 7:
        reserve = 35.0
    elif day == 8:
        reserve = 20.0
    elif day == 9:
        reserve = 10.0

    affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 1:
        affordable = budget

    bid = min(target, affordable)

    if hp <= 2:
        bid = min(budget, max(bid, 92.0))
    elif no_water_days >= 1:
        bid = min(budget, max(bid, 78.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    rich_threat = 0.0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            if opp.get('budget', 0) > rich_threat:
                rich_threat = opp.get('budget', 0)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        safe = 18.0 if hp > 3 else 42.0
        return float(min(budget, safe))

    total_req = WATER_REQ
    for r in opp_requirements:
        total_req += r

    scarcity = total_req / max(1.0, float(supply))
    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 2 or no_water >= 1
    semi_urgent = hp <= 4
    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if urgent:
        target = max(0.92 * DAILY_SALARY, highest_prev + 5.0)
        if tight_supply:
            target = max(target, 1.02 * highest_prev + 3.0)
        return float(min(budget, target))

    if scarcity > 2.2 or tight_supply:
        target = max(48.0, highest_prev + 2.5)
        if semi_urgent:
            target = max(target, 0.82 * DAILY_SALARY)
        else:
            target = max(target, avg_prev * 0.92)
        return float(min(budget, target))

    if loose_supply and hp >= 5:
        target = 16.0 + (day % 3)
        return float(min(budget, target))

    target = max(24.0, min(0.68 * DAILY_SALARY, avg_prev * 0.75 + 6.0))
    if rich_threat > budget * 1.5:
        target *= 0.9
    if semi_urgent:
        target = max(target, 38.0)

    return float(min(budget, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if not alive_opps:
        return float(min(budget, 8.0))

    opp_count = len(alive_opps)
    expected_players = opp_count + 1
    water_units = supply / float(WATER_REQ)
    scarcity = expected_players - water_units

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    emergency = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1
    abundant = supply >= 22
    tight = supply <= 17

    if emergency:
        bid = max(92.0, max_prev + 6.0, avg_prev + 12.0)
        if tight:
            bid += 18.0
        bid += 6.0 * urgent_opp
        return float(max(0.0, min(budget, bid)))

    if abundant and hp >= 5 and no_water_days == 0:
        bid = 6.0
        if max_prev < 40:
            bid = 12.0
        return float(max(0.0, min(budget, bid)))

    if tight:
        bid = max(58.0, avg_prev * 0.72 + 8.0, max_prev * 0.62 + 10.0)
        bid += 5.0 * urgent_opp
        if hp <= 4:
            bid += 12.0
        if rich_opp >= 2:
            bid += 6.0
        return float(max(0.0, min(budget, bid)))

    if scarcity > 1.5:
        bid = max(46.0, avg_prev * 0.55 + 6.0)
        if pressured:
            bid += 10.0
        return float(max(0.0, min(budget, bid)))

    if max_prev >= 150:
        bid = 18.0 if hp >= 5 and no_water_days == 0 else 54.0
    elif max_prev >= 100:
        bid = 24.0 if hp >= 5 else 48.0
    elif max_prev >= 60:
        bid = 34.0 if hp >= 5 else 52.0
    else:
        bid = 28.0 if hp >= 5 else 44.0

    if day >= 8 and hp <= 4:
        bid += 10.0

    return float(max(0.0, min(budget, bid)))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.8)
        return float(max(0.0, safe_bid))

    total_players = 1 + len(alive)
    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < total_players

    opp_signals = []
    max_prev_bid = 0.0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is None:
            prev_bid = opp.get('daily_salary', DAILY_SALARY) * 0.7
        prev_bid = float(prev_bid)

        threat = prev_bid
        if opp.get('budget', 0) < prev_bid:
            threat = float(opp.get('budget', 0))
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            threat = max(threat, min(float(opp.get('budget', 0)), prev_bid * 1.15 + 8.0))
        opp_signals.append(threat)
        if threat > max_prev_bid:
            max_prev_bid = threat

    opp_signals.sort(reverse=True)
    target_to_beat = opp_signals[int(0)] if len(opp_signals) >= 1 else 0.0

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

    if scarcity:
        urgency += 2
    elif float(supply) <= 18.0:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency <= 1:
        base = DAILY_SALARY * 0.38
        if not scarcity and float(supply) >= 22.0:
            base = DAILY_SALARY * 0.28
        bid = min(base, budget)
    elif urgency == 2:
        bid = max(DAILY_SALARY * 0.6, target_to_beat + 2.0)
    elif urgency == 3:
        bid = max(DAILY_SALARY * 0.78, target_to_beat + 4.0)
    elif urgency == 4:
        bid = max(DAILY_SALARY * 0.95, target_to_beat + 7.0)
    else:
        bid = max(DAILY_SALARY * 1.1, target_to_beat + 12.0)

    if budget < DAILY_SALARY * 1.2 and urgency <= 2:
        bid = min(bid, budget * 0.72)

    if budget > 250 and scarcity and urgency >= 3:
        bid = max(bid, target_to_beat + 10.0)

    if hp >= 8 and no_water_days == 0 and not scarcity and float(supply) >= 21.0:
        bid = min(bid, DAILY_SALARY * 0.42)

    if hp <= 1 or no_water_days >= 3:
        bid = max(bid, min(budget, target_to_beat + 15.0))

    bid = min(float(budget), float(bid))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return min(budget, 18.0)

    units = int(supply / WATER_REQ)
    if units < 1:
        units = 1

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    max_prev = 0.0
    for opp in alive:
        if opp.get('budget', 0) >= 250:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid > max_prev:
                    max_prev = bid

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    my_urgent = hp <= 3 or no_water_days >= 1
    very_urgent = hp <= 2 or no_water_days >= 2

    if units >= len(alive) + 1:
        base = 8.0
    elif units >= len(alive):
        base = 16.0
    elif units >= max(1, len(alive) - 1):
        base = 28.0
    else:
        base = 42.0

    pressure = 0.0
    if max_prev > 0:
        if max_prev >= 180:
            pressure += 18.0
        elif max_prev >= 100:
            pressure += 10.0
        elif max_prev >= 50:
            pressure += 5.0
    if avg_prev > 120:
        pressure += 6.0
    elif avg_prev > 60:
        pressure += 3.0

    pressure += urgent_opp * 4.0
    pressure += rich_opp * 2.0

    if my_urgent:
        pressure += 22.0
    if very_urgent:
        pressure += 18.0

    if day >= 8:
        pressure += 6.0

    target = base + pressure

    if prev_bids:
        if units <= max(1, len(alive) - 1):
            target = max(target, min(max_prev + 2.5, budget))
        elif my_urgent:
            target = max(target, min(max_prev + 1.0, budget))
        else:
            target = max(target, min(avg_prev * 0.45 + 3.0, budget))

    if units >= len(alive) + 1 and not my_urgent:
        target = min(target, 20.0)

    if budget < 60:
        target = min(target, max(12.0, budget * 0.72))
    elif budget < 120:
        target = min(target, budget * 0.68)
    else:
        target = min(target, budget * 0.52 + 12.0)

    if very_urgent:
        target = max(target, min(budget, max_prev + 5.0 if max_prev > 0 else 55.0))
    elif my_urgent:
        target = max(target, min(budget, max_prev + 2.0 if max_prev > 0 else 42.0))

    if hp >= 7 and no_water_days == 0 and units >= len(alive):
        target = min(target, 24.0)

    if target < 0:
        target = 0.0
    if target > budget:
        target = budget

    return float(round(target, 2))
"""
