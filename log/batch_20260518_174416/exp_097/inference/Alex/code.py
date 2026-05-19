# ============================================================
# Experiment: exp_097
# Agent: Alex
# Source: exp_097
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

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 20)

    prev_bids = []
    desperate_opponents = 0
    rich_opponents = 0
    total_req = WATER_REQ

    for opp in alive_opponents:
        total_req += opp.get('water_requirement', WATER_REQ)
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_opponents += 1
        if opp.get('budget', 0) >= budget:
            rich_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    scarcity = float(supply) / float(total_req) if total_req > 0 else 1.0

    if hp <= 2 or no_water_days >= 2:
        base = 64
    elif hp <= 4 or no_water_days >= 1:
        base = 52
    elif scarcity >= 0.9:
        base = 24
    elif scarcity >= 0.7:
        base = 34
    else:
        base = 45

    if desperate_opponents >= 2:
        base += 6
    elif desperate_opponents == 1:
        base += 3

    if rich_opponents >= max(1, len(alive_opponents) // 2):
        base += 4

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if highest_prev >= 60:
            if hp > 4 and no_water_days == 0 and scarcity >= 0.8:
                base = min(base, 28)
            else:
                base = max(base, highest_prev + 2)
        else:
            target = max(avg_prev + 2, highest_prev + 1)
            base = max(base, target)

    if scarcity >= 1.1 and hp > 4 and no_water_days == 0:
        base = min(base, 22)

    if budget < 40:
        base = min(base, budget)
    elif budget < 80:
        base = min(base, max(28, budget * 0.75))
    else:
        base = min(base, budget * 0.9)

    if hp <= 2 or no_water_days >= 2:
        base = max(base, min(budget, 60))

    bid = int(round(base))
    if bid < 0:
        bid = 0
    if bid > budget:
        bid = int(budget)
    return bid
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
    strong_threat = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 85:
                    strong_threat += 1

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 3
    elif hp <= 6:
        urgency += 2
    else:
        urgency += 1

    if no_water_days >= 2:
        urgency += 3
    elif no_water_days >= 1:
        urgency += 1

    if supply <= 16:
        urgency += 3
    elif supply <= 19:
        urgency += 2
    else:
        urgency += 1

    if day >= 8:
        urgency += 1

    if budget <= 70:
        urgency += 1

    if urgency >= 8:
        bid = max(92.0, highest_prev + 2.0)
    elif urgency >= 6:
        bid = max(72.0, avg_prev * 0.9)
    elif urgency >= 4:
        if highest_prev >= 110:
            bid = 38.0
        else:
            bid = max(48.0, min(78.0, highest_prev * 0.7 + 4.0))
    else:
        if strong_threat >= 2:
            bid = 16.0
        elif highest_prev >= 90:
            bid = 22.0
        else:
            bid = 28.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 95.0)

    if supply >= 23 and hp >= 7 and no_water_days == 0:
        bid = min(bid, 24.0)

    if day == 1 and hp >= 7:
        bid = min(bid, 30.0)

    return min(budget, max(0.0, bid))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive_count = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 90:
                    aggressive_count += 1
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        bid = max(78.0, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        if tight_supply:
            bid = max(58.0, avg_prev + 4.0)
        else:
            bid = max(46.0, avg_prev + 2.0)
    else:
        if loose_supply:
            bid = 16.0
        elif tight_supply:
            bid = max(34.0, min(62.0, avg_prev + 1.5))
        else:
            bid = max(24.0, min(48.0, avg_prev * 0.7 + 3.0))

    if aggressive_count >= 1 and hp > 4 and no_water == 0:
        bid = min(bid, 28.0 if not tight_supply else 38.0)

    if desperate_count >= 2 and (hp <= 4 or tight_supply):
        bid = max(bid, 55.0)

    if highest_prev >= 120 and hp > 4 and no_water == 0:
        bid = min(bid, 26.0 if loose_supply else 34.0)

    bid = min(bid, budget)
    if budget <= 0:
        return 0.0
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 2:
            bid = DAILY_SALARY * 0.8
        return max(0.0, min(budget, bid))

    prev_bids = []
    named_prev = {}
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid')
        if b is not None:
            prev_bids.append(float(b))
            named_prev[agent_id] = float(b)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev = sorted_bids[int(1)]
    elif len(prev_bids) == 1:
        second_prev = prev_bids[int(0)]

    eric_bid = named_prev.get('Eric', 0.0)
    cindy_bid = named_prev.get('Cindy', 0.0)

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        target = max(DAILY_SALARY * 0.95, eric_bid + 2.0)
        if tight_supply:
            target = max(target, second_prev + 2.0)
        return max(0.0, min(budget, target))

    if hp <= 4 or no_water >= 1:
        if tight_supply:
            target = max(DAILY_SALARY * 0.82, eric_bid + 1.5)
        else:
            target = max(DAILY_SALARY * 0.68, min(highest_prev * 0.8, eric_bid + 1.0 if eric_bid > 0 else DAILY_SALARY * 0.68))
        return max(0.0, min(budget, target))

    if ample_supply:
        if cindy_bid >= 100:
            target = DAILY_SALARY * 0.28
        else:
            target = DAILY_SALARY * 0.4
        return max(0.0, min(budget, target))

    if tight_supply:
        if eric_bid > 0:
            target = min(DAILY_SALARY * 0.78, eric_bid + 1.25)
        else:
            target = DAILY_SALARY * 0.62
        return max(0.0, min(budget, target))

    if highest_prev >= 90:
        target = DAILY_SALARY * 0.38
    elif eric_bid >= 75:
        target = DAILY_SALARY * 0.58
    else:
        target = DAILY_SALARY * 0.5

    return max(0.0, min(budget, target))
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 200:
                prev = opp.get('previous_trace', {}) or {}
                pb = prev.get('bid')
                if pb is not None and pb >= 90:
                    rich_aggressive += 1
            prev = opp.get('previous_trace', {}) or {}
            pb = prev.get('bid')
            if pb is not None:
                prev_bids.append(pb)

    total_alive = len(alive) + 1
    units = int(supply / WATER_REQ)
    scarce = units < total_alive
    very_scarce = units <= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    for b in prev_bids:
        if b <= 100 and b > moderate_prev:
            moderate_prev = b

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

    if very_scarce:
        urgency += 2
    elif scarce:
        urgency += 1

    urgency += min(2, desperate_count)

    if not alive:
        bid = 18.0 if hp > 4 else 40.0
        return float(min(budget, bid))

    if urgency >= 6:
        if moderate_prev > 0:
            bid = max(95.0, moderate_prev + 4.0)
        else:
            bid = 98.0
        if highest_prev >= 150:
            bid = min(bid, 110.0)
    elif urgency >= 4:
        if moderate_prev > 0:
            bid = max(62.0, moderate_prev + 2.5)
        else:
            bid = 68.0 if scarce else 52.0
        if highest_prev >= 150 and hp > 2:
            bid = min(bid, 75.0)
    elif urgency >= 2:
        if scarce:
            bid = 44.0
        else:
            bid = 28.0
        if moderate_prev > 0 and moderate_prev < 80:
            bid = max(bid, moderate_prev + 1.5)
    else:
        bid = 16.0 if not scarce else 24.0
        if rich_aggressive >= 2 and hp > 4:
            bid = 12.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 90.0)
    elif hp <= 3 or no_water_days >= 1:
        bid = max(bid, 60.0)

    if budget < bid:
        bid = budget

    if budget < 25:
        bid = budget

    if bid < 0:
        bid = 0.0

    return float(bid)
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    weak_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('budget', 0) < DAILY_SALARY * 0.8:
                weak_opp_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 140:
                    aggressive_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    low_supply = supply <= 17
    high_supply = supply >= 22

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1

    if danger >= 3:
        target = max(0.92 * DAILY_SALARY, min(max_prev + 8.0, 0.95 * budget))
        if low_supply:
            target = max(target, min(budget, max_prev + 15.0))
        return float(max(1.0, min(budget, target)))

    if danger == 2:
        target = max(0.72 * DAILY_SALARY, avg_prev * 0.55 + 8.0)
        if low_supply:
            target = max(target, min(budget, max_prev * 0.72 + 6.0))
        else:
            target = min(target, 0.82 * DAILY_SALARY)
        return float(max(1.0, min(budget, target)))

    if high_supply and aggressive_count >= 2:
        target = 18.0
    elif max_prev >= 180:
        target = 22.0 if hp >= 6 else 48.0
    elif max_prev >= 130:
        target = 26.0 if hp >= 6 else 44.0
    elif max_prev > 0:
        target = min(52.0, max(24.0, avg_prev * 0.35 + 6.0))
    else:
        target = 28.0

    if weak_opp_count >= 2 and hp >= 6 and no_water_days == 0:
        target = min(target, 24.0)

    if day >= 8:
        if hp <= 5 or no_water_days >= 1:
            target = max(target, 55.0)
        else:
            target = min(target, 30.0)

    return float(max(1.0, min(budget, target)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = DAILY_SALARY * 0.38
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.72
        return float(max(0.0, min(budget, base)))

    highest_prev = 0.0
    cindy_prev = None
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        if float(opp.get('budget', 0.0)) >= DAILY_SALARY * 4:
            rich_opp += 1
        if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0.0)) <= 2:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid_val = float(bid)
            if bid_val > highest_prev:
                highest_prev = bid_val
        if opp_id == 'Cindy':
            if bid is not None:
                cindy_prev = float(bid)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 1:
        danger += 0.75
    elif hp <= 3:
        danger += 0.45
    if no_water >= 2:
        danger += 0.8
    elif no_water >= 1:
        danger += 0.35

    base = DAILY_SALARY * (0.34 + 0.22 * scarcity + 0.28 * min(1.0, danger))

    if highest_prev > 0:
        if highest_prev >= 140:
            react = DAILY_SALARY * (0.42 + 0.18 * scarcity)
            if danger >= 0.45:
                react = DAILY_SALARY * (0.82 + 0.08 * scarcity)
        elif highest_prev >= 90:
            react = min(highest_prev + 2.0, DAILY_SALARY * 0.96)
            if hp > 4 and no_water == 0 and supply >= 20:
                react = DAILY_SALARY * 0.46
        else:
            react = max(base, highest_prev + 1.5)
    else:
        react = base

    if cindy_prev is not None and cindy_prev >= 150 and hp > 3 and no_water == 0:
        react = min(react, DAILY_SALARY * (0.40 + 0.10 * scarcity))

    if urgent_opp >= 2 and hp > 3 and no_water == 0:
        react *= 0.92
    if rich_opp >= 2 and (hp <= 3 or no_water >= 1):
        react = max(react, DAILY_SALARY * 0.88)

    if supply <= 16:
        react += 6.0
    elif supply >= 23 and hp > 3 and no_water == 0:
        react -= 4.0

    if day >= 8:
        if hp <= 3 or no_water >= 1:
            react = max(react, DAILY_SALARY * 0.9)
        else:
            react = max(react, DAILY_SALARY * 0.5)

    if budget < DAILY_SALARY * 1.2:
        react = min(react, budget * 0.72 + 4.0)
    elif budget > DAILY_SALARY * 6:
        react = min(react + 3.0, budget)

    bid = max(0.0, min(budget, react))
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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 8.0))

    yesterday_bids = []
    req_pressure = []
    desperate_count = 0
    rich_count = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            yesterday_bids.append(float(bid))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            desperate_count += 1
        if opp.get('budget', 0) >= 120:
            rich_count += 1
        req_pressure.append(float(opp.get('water_requirement', WATER_REQ)))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0
    max_opp_req = max(req_pressure) if req_pressure else WATER_REQ

    my_critical = (hp <= 3) or (no_water >= 1)
    very_critical = (hp <= 2) or (no_water >= 2)

    can_only_one_win = supply < (WATER_REQ + max_opp_req)
    medium_tight = supply < (2 * WATER_REQ + 2)

    bid = 0.0

    if very_critical:
        if can_only_one_win:
            bid = max(DAILY_SALARY * 0.98, highest_prev + 3.0)
        else:
            bid = max(DAILY_SALARY * 0.82, avg_prev + 2.0)
    elif my_critical:
        if can_only_one_win:
            bid = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.68, avg_prev + 1.5)
    else:
        if can_only_one_win:
            if highest_prev >= 100:
                bid = DAILY_SALARY * 0.22
            else:
                bid = max(DAILY_SALARY * 0.4, highest_prev + 1.0)
        elif medium_tight:
            if highest_prev >= 120:
                bid = DAILY_SALARY * 0.28
            else:
                bid = max(DAILY_SALARY * 0.48, min(DAILY_SALARY * 0.78, avg_prev + 1.0))
        else:
            bid = DAILY_SALARY * 0.18

    if desperate_count >= 2 and not my_critical:
        bid *= 0.9
    if rich_count >= 2 and can_only_one_win and not my_critical:
        bid *= 0.8

    if day >= 8 and hp >= 7 and not my_critical:
        bid *= 0.9

    min_safe = 0.0
    if very_critical:
        min_safe = 18.0
    elif my_critical:
        min_safe = 10.0

    bid = max(bid, min_safe)
    bid = min(bid, budget)

    if very_critical and budget > 0:
        bid = min(budget, max(bid, budget * 0.92))
    elif my_critical and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.6)

    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if len(alive_opponents) == 0:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, safe_bid))

    prev_bids = []
    prev_max = 0.0
    prev_min = None
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 120:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev.get('bid'))
            prev_bids.append(b)
            if b > prev_max:
                prev_max = b
            if prev_min is None or b < prev_min:
                prev_min = b

    if prev_min is None:
        prev_min = 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0
    low_supply = 1.0 - scarcity

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days == 1:
        urgency += 0.35

    pressure = 0.0
    if prev_max >= 120:
        pressure += 0.45
    elif prev_max >= 95:
        pressure += 0.3
    elif prev_max >= 70:
        pressure += 0.15

    pressure += 0.08 * desperate_count
    pressure += 0.04 * rich_count
    pressure += 0.35 * low_supply

    survival_mode = (hp <= 3) or (no_water_days >= 2)
    caution_mode = (hp >= 7 and no_water_days == 0 and supply >= 21)

    if survival_mode:
        bid = max(DAILY_SALARY * 0.95, prev_max + 2.0)
    elif caution_mode and prev_max >= 100:
        bid = DAILY_SALARY * 0.22
    else:
        base = DAILY_SALARY * (0.28 + 0.32 * low_supply + 0.35 * urgency + 0.18 * pressure)
        if prev_bids:
            if low_supply > 0.6 or urgency > 0.45:
                target = prev_max + 1.5
                bid = max(base, target)
            else:
                target = prev_min + 1.0
                bid = max(base, min(target, prev_max * 0.72 if prev_max > 0 else target))
        else:
            bid = base

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.9
    if day >= 8 and (hp <= 4 or no_water_days >= 1):
        bid *= 1.12

    max_affordable = budget
    soft_cap = DAILY_SALARY * 1.55
    if hp >= 7 and no_water_days == 0 and supply >= 22:
        soft_cap = DAILY_SALARY * 0.7
    if survival_mode:
        soft_cap = max(soft_cap, DAILY_SALARY * 1.45)

    bid = min(bid, soft_cap, max_affordable)

    if budget < DAILY_SALARY * 0.6:
        bid = min(bid, budget)
    elif budget > 250 and (low_supply > 0.5 or urgency > 0.4):
        bid = min(max_affordable, bid + 6.0)

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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    total_players = 1 + len(alive)
    units = int(supply / WATER_REQ)
    severe_scarcity = units <= 1
    moderate_scarcity = units == 2 and total_players > 2

    prev_bids = []
    desperate_opp = False
    rich_opp = False
    for opp in alive:
        if opp.get('budget', 0) > budget * 1.5:
            rich_opp = True
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp = True
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
            if prev.get('status') == 'lost' or prev.get('hp_after', 10) <= 3:
                desperate_opp = True

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    urgency = 0
    if hp <= 3:
        urgency += 2
    elif hp <= 5:
        urgency += 1
    if no_water_days >= 1:
        urgency += 2

    if not alive:
        base = DAILY_SALARY * 0.22
    elif severe_scarcity:
        if urgency >= 3:
            base = max(DAILY_SALARY * 0.95, highest_prev + 3)
        elif desperate_opp or rich_opp:
            base = max(DAILY_SALARY * 0.82, avg_prev + 2)
        else:
            base = max(DAILY_SALARY * 0.72, highest_prev * 0.92)
    elif moderate_scarcity:
        if urgency >= 3:
            base = max(DAILY_SALARY * 0.78, avg_prev + 1.5)
        elif highest_prev >= DAILY_SALARY * 0.9:
            base = DAILY_SALARY * 0.38
        else:
            base = max(DAILY_SALARY * 0.42, avg_prev * 0.55)
    else:
        if urgency >= 3:
            base = DAILY_SALARY * 0.62
        else:
            base = DAILY_SALARY * 0.24

    if budget < DAILY_SALARY * 1.2:
        base = min(base, budget * 0.72)
    elif budget > DAILY_SALARY * 6 and urgency >= 2:
        base = max(base, DAILY_SALARY * 0.88)

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.96)

    bid = min(budget, max(0, base))
    return float(round(bid, 2))
"""
