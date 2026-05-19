# ============================================================
# Experiment: exp_038
# Agent: Alex
# Source: exp_038
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

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return min(budget, 0.9 * DAILY_SALARY)
        if supply >= 22:
            return min(budget, 0.28 * DAILY_SALARY)
        return min(budget, 0.42 * DAILY_SALARY)

    prev_bids = []
    desperate_opp = False
    rich_pressure = 0.0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp = True
        if opp.get('budget', 0) > budget:
            rich_pressure = max(rich_pressure, 1.0)
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    if hp <= 1 or no_water >= 2:
        base = 0.96 * DAILY_SALARY
    elif hp <= 2 or no_water >= 1:
        base = 0.82 * DAILY_SALARY
    else:
        if supply >= 23:
            base = 0.30 * DAILY_SALARY
        elif supply >= 20:
            base = 0.42 * DAILY_SALARY
        elif supply >= 17:
            base = 0.56 * DAILY_SALARY
        else:
            base = 0.70 * DAILY_SALARY

    if prev_bids:
        if highest_prev >= 0.9 * DAILY_SALARY:
            if hp > 2 and no_water == 0:
                target = 0.34 * DAILY_SALARY if supply >= 20 else 0.48 * DAILY_SALARY
            else:
                target = min(0.97 * DAILY_SALARY, highest_prev + 1.0)
        else:
            pressure_bid = max(avg_prev + 2.0, highest_prev + 1.0)
            target = max(base, pressure_bid)
    else:
        target = base

    if desperate_opp and supply <= 18:
        target = max(target, 0.78 * DAILY_SALARY)

    if rich_pressure and supply <= 17:
        target = max(target, 0.74 * DAILY_SALARY)

    if budget < target:
        if hp <= 2 or no_water >= 1:
            return max(0.0, budget)
        return max(0.0, min(budget, base * 0.85))

    return max(0.0, min(budget, target))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_threat = 0
    urgent_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_threat += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if not alive:
        return max(0.0, min(float(budget), DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    total_players = 1 + len(alive)
    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    danger = 0
    if hp <= 3:
        danger += 3
    elif hp <= 5:
        danger += 2
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 2
    if slots < 1:
        danger += 3
    elif slots < total_players:
        danger += 2
    if highest_prev >= 110:
        danger += 2
    elif highest_prev >= 85:
        danger += 1
    if urgent_opp >= 2:
        danger += 1

    if slots >= 2:
        base = 28.0
    else:
        base = 44.0

    if rich_threat >= 2:
        base += 6.0
    elif rich_threat == 1:
        base += 3.0

    if prev_bids:
        if highest_prev <= 40:
            target = max(base, highest_prev + 2.0)
        elif highest_prev <= 80:
            target = max(base + 6.0, avg_prev + 4.0)
        else:
            target = max(base + 10.0, highest_prev * 0.78)
    else:
        target = base + 4.0

    if danger >= 7:
        target = max(target, min(126.0, highest_prev + 8.0 if highest_prev > 0 else 95.0))
    elif danger >= 5:
        target = max(target, min(108.0, highest_prev + 4.0 if highest_prev > 0 else 78.0))
    elif danger <= 1 and slots >= 2:
        target = min(target, 32.0)

    if budget < target:
        if hp <= 3 or no_water_days >= 2:
            target = budget
        else:
            target = min(budget, max(18.0, budget * 0.55))

    if target > budget:
        target = budget
    if target < 0:
        target = 0.0
    return float(target)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_live = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget:
                rich_live += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17.0
    ample_supply = supply >= 22.0
    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1

    if urgent:
        bid = DAILY_SALARY * 1.18
    elif semi_urgent:
        bid = DAILY_SALARY * 0.92
    else:
        if highest_prev >= 135.0:
            bid = DAILY_SALARY * (0.28 if ample_supply else 0.42)
        elif highest_prev >= 90.0:
            bid = DAILY_SALARY * (0.38 if ample_supply else 0.58)
        else:
            bid = max(DAILY_SALARY * 0.45, avg_prev + 2.0)

    if tight_supply:
        bid += 10.0
    elif ample_supply:
        bid -= 6.0

    if day >= 8:
        bid += 8.0
    if day >= 9 and semi_urgent:
        bid += 10.0

    if rich_live >= 2 and not semi_urgent:
        bid -= 5.0

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 1.2
    elif day == 8:
        reserve = DAILY_SALARY * 0.7
    elif day == 9:
        reserve = DAILY_SALARY * 0.3

    max_affordable = max(0.0, budget - reserve)
    if urgent:
        max_affordable = budget

    bid = max(0.0, min(bid, max_affordable if max_affordable > 0 else budget))

    if bid < 1.0 and budget >= 1.0 and semi_urgent:
        bid = min(budget, 1.0)

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

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    dangerous_prev = 0.0
    fixed_high_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0.0)
                prev_bids.append(b)
                if b > dangerous_prev:
                    dangerous_prev = b
                if b >= 130:
                    fixed_high_count += 1

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

    if not alive_opps:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    if urgency >= 3:
        if scarcity >= 1:
            bid = max(92.0, dangerous_prev + 3.0)
        else:
            bid = max(78.0, dangerous_prev * 0.9)
        return float(min(budget, bid))

    if urgency == 2:
        if dangerous_prev >= 130:
            bid = 58.0 if scarcity == 0 else 74.0
        elif dangerous_prev >= 95:
            bid = dangerous_prev + 2.0 if scarcity >= 1 else 61.0
        else:
            bid = 54.0 if scarcity == 0 else 66.0
        return float(min(budget, bid))

    if fixed_high_count >= 1 and scarcity == 0:
        bid = 22.0
    elif dangerous_prev >= 120:
        bid = 28.0 if hp >= 7 else 48.0
    elif dangerous_prev >= 90:
        bid = 36.0 if scarcity == 0 else 49.0
    else:
        bid = 41.0 if scarcity == 0 else 55.0

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.85

    bid = min(budget, bid)
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_threats = 0
    urgent_opponents = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_threats += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, max(1.0, DAILY_SALARY * 0.25)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

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
        danger += 1

    if slots >= 2:
        danger -= 1
    if rich_threats >= 2 and slots == 1:
        danger += 1

    if hp <= 2 or no_water_days >= 2:
        bid = max(138.0, highest_prev + 2.0)
    elif danger >= 4:
        bid = max(132.0, avg_prev + 3.0)
    elif slots >= 2:
        if highest_prev >= 135:
            bid = 92.0
        else:
            bid = max(78.0, min(110.0, avg_prev * 0.72 + 8.0))
    else:
        if hp >= 7 and no_water_days == 0:
            bid = 0.0
        elif highest_prev >= 135:
            bid = 18.0 if hp >= 5 else 136.0
        else:
            bid = max(65.0, min(118.0, highest_prev * 0.85 + 4.0))

    if day >= 8:
        if hp <= 5:
            bid = max(bid, 130.0)
        elif hp >= 8 and no_water_days == 0 and slots == 1:
            bid = min(bid, 20.0)

    if urgent_opponents >= 2 and slots == 1 and hp >= 7 and no_water_days == 0:
        bid = min(bid, 12.0)

    bid = max(0.0, min(float(bid), float(budget)))
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    units = int(supply / WATER_REQ)
    if units < 1:
        units = 1

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = 18.0
        if hp <= 2 or no_water_days >= 1:
            base = 45.0
        return float(max(0.0, min(budget, base)))

    est_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        b = None
        if prev:
            b = prev.get('bid')
        if b is None:
            b = opp.get('daily_salary', DAILY_SALARY) * 0.75

        if opp.get('no_water_days', 0) >= 1:
            b += 8.0
        if opp.get('hp', 10) <= 2:
            b += 12.0
        if opp.get('budget', 0) < b:
            b = opp.get('budget', 0)
        if b < 0:
            b = 0.0
        est_bids.append(float(b))

    est_bids.sort(reverse=True)
    target_index = int(units - 1)
    if target_index < 0:
        target_index = 0
    if target_index >= len(est_bids):
        target_index = int(len(est_bids) - 1)

    if len(est_bids) > 0:
        clear_est = est_bids[int(target_index)]
        top_est = est_bids[0]
    else:
        clear_est = DAILY_SALARY * 0.6
        top_est = clear_est

    if units == 1:
        bid = clear_est + 2.0
        if top_est > 120:
            bid = min(bid, 92.0)
        if hp <= 2 or no_water_days >= 1:
            bid = max(bid, min(budget, clear_est + 8.0, 110.0))
        elif hp >= 7 and no_water_days == 0:
            bid = min(bid, 72.0)
    else:
        bid = clear_est + 1.5
        if len(est_bids) >= 2:
            second_idx = int(min(len(est_bids) - 1, units))
            next_est = est_bids[int(second_idx)]
            if clear_est - next_est > 18:
                bid = max(next_est + 2.0, bid - 8.0)
        if hp >= 7 and no_water_days == 0:
            bid -= 6.0
        if hp <= 3:
            bid += 10.0
        if no_water_days >= 1:
            bid += 12.0

    if hp <= 2:
        bid = max(bid, 85.0)
    elif hp <= 4:
        bid = max(bid, 62.0)

    if budget < 50:
        bid = min(bid, budget)
    else:
        reserve = 0.0
        if hp >= 6 and no_water_days == 0:
            reserve = 20.0
        elif hp >= 4:
            reserve = 10.0
        bid = min(bid, budget - reserve)
        if bid < 0:
            bid = min(budget, 0.0)

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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    high_pressure_count = 0
    desperate_count = 0
    rich_aggressive_count = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = float(prev['bid'])
            prev_bids.append(bid)
            if bid >= 90:
                high_pressure_count += 1
            if bid >= 70 and opp.get('budget', 0) > 500:
                rich_aggressive_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.6
    elif hp <= 4:
        urgency += 0.35
    if no_water >= 1:
        urgency += 0.35
    if no_water >= 2:
        urgency += 0.25
    urgency += 0.25 * scarcity
    if urgency > 1.0:
        urgency = 1.0

    if supply >= 23 and hp >= 5 and no_water == 0:
        bid = DAILY_SALARY * 0.22
    elif supply >= 20 and high_pressure_count >= 2 and hp >= 5 and no_water == 0:
        bid = DAILY_SALARY * 0.28
    else:
        base = DAILY_SALARY * (0.30 + 0.38 * scarcity + 0.32 * urgency)
        pressure_target = 0.0
        if prev_bids:
            if highest_prev >= 100:
                pressure_target = highest_prev * 0.90
            elif highest_prev >= 85:
                pressure_target = highest_prev * 0.82
            elif highest_prev >= 60:
                pressure_target = highest_prev + 2.0
            else:
                pressure_target = max(avg_prev + 3.0, DAILY_SALARY * 0.45)
        bid = max(base, pressure_target)

    if rich_aggressive_count >= 2 and urgency < 0.5 and supply >= 19:
        bid = min(bid, DAILY_SALARY * 0.42)

    if desperate_count >= 2 and supply <= 18:
        bid = max(bid, DAILY_SALARY * 0.78)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water >= 1:
        bid = max(bid, DAILY_SALARY * 0.72)

    if day >= 8 and hp >= 5 and budget > 300 and supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.40)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    max_affordable = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water >= 1:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(bid)
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
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    slots = int(supply / WATER_REQ)
    if slots < 1:
        slots = 1

    prev_bids = []
    aggressive_count = 0
    weak_count = 0
    opp_count = 0
    for opp in alive:
        opp_count += 1
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 95:
                aggressive_count += 1
            if bid <= 75:
                weak_count += 1

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 85.0
        avg_prev = 85.0

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1
    if budget < 120:
        danger += 1

    contested = opp_count + 1 > slots

    if danger >= 4:
        bid = max(96.0, highest_prev + 3.0)
    elif danger >= 2:
        bid = max(82.0, avg_prev + 1.5)
    else:
        if slots >= 2:
            if aggressive_count >= 2:
                bid = 58.0
            elif weak_count >= 2:
                bid = 72.0
            else:
                bid = 66.0
        else:
            if contested:
                bid = max(78.0, avg_prev - 8.0)
            else:
                bid = 64.0

    if day >= 8:
        bid += 6.0
    if hp <= 2:
        bid += 10.0
    if no_water_days >= 2:
        bid += 12.0

    reserve = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    affordable = budget - reserve
    if affordable < 0:
        affordable = budget * 0.6

    if danger == 0 and highest_prev >= 110 and slots >= 2:
        bid = min(bid, 54.0)

    if budget < 90:
        bid = min(bid, budget)
    else:
        bid = min(bid, affordable, budget)

    floor_bid = 18.0
    if danger >= 2:
        floor_bid = 45.0
    if bid < floor_bid:
        bid = floor_bid
    if bid > budget:
        bid = budget
    if bid < 0:
        bid = 0

    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
    prev_bids = []
    urgent_prev_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))
                opp_hp = opp.get('hp', 10)
                opp_nwd = opp.get('no_water_days', 0)
                if opp_hp <= 4 or opp_nwd >= 1:
                    urgent_prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 8.0))

    competitor_count = len(alive)
    tight_supply = supply <= 16.0
    ample_supply = supply >= 22.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_high = max(urgent_prev_bids) if urgent_prev_bids else highest_prev

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 2
    if tight_supply:
        danger += 1

    if danger >= 5:
        bid = max(urgent_high + 3.0, DAILY_SALARY * 1.18)
    elif danger >= 3:
        bid = max(urgent_high + 1.5, DAILY_SALARY * 0.92)
    elif danger >= 2:
        bid = max(highest_prev * 0.78, DAILY_SALARY * 0.62)
    else:
        if ample_supply:
            bid = DAILY_SALARY * 0.34
        elif highest_prev >= 140:
            bid = DAILY_SALARY * 0.36
        elif highest_prev >= 100:
            bid = DAILY_SALARY * 0.48
        else:
            bid = max(DAILY_SALARY * 0.42, highest_prev * 0.58)

    if competitor_count >= 3 and danger <= 2 and highest_prev >= 120:
        bid *= 0.9
    if day >= 8 and hp >= 6 and no_water == 0 and budget < 250:
        bid *= 0.85
    if day <= 2 and hp >= 8 and no_water == 0 and ample_supply:
        bid *= 0.9

    reserve = 0.0
    if hp > 4 and no_water == 0:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.5

    cap = max(0.0, budget - reserve)
    if danger >= 3:
        cap = budget

    bid = min(bid, cap if cap > 0 else budget)
    bid = min(bid, budget)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, max(1.0, DAILY_SALARY * 0.25)))

    prev_bids = []
    danger_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            danger_count += 1
        if opp.get('budget', 0) >= 250:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = [b for b in prev_bids if b <= 140]
    ref_prev = max(moderate_prev) if moderate_prev else highest_prev

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2 or no_water >= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency >= 3:
        bid = max(0.92 * DAILY_SALARY, ref_prev + 4.0)
        if rich_count >= 2 and scarcity >= 1:
            bid = max(bid, 96.0)
    elif urgency == 2:
        bid = max(0.62 * DAILY_SALARY, min(ref_prev + 2.5, 82.0))
        if scarcity >= 1:
            bid += 6.0
    elif urgency == 1:
        bid = 0.42 * DAILY_SALARY
        if scarcity >= 2:
            bid = max(bid, 38.0)
        elif scarcity == 1:
            bid = max(bid, 33.0)
        if ref_prev > 0 and ref_prev < 80:
            bid = max(bid, ref_prev + 1.5)
    else:
        bid = 0.24 * DAILY_SALARY
        if scarcity >= 2:
            bid = 24.0
        elif scarcity == 1:
            bid = 20.0
        if danger_count >= 2:
            bid *= 0.9

    if highest_prev >= 160 and urgency <= 1:
        bid = min(bid, 30.0)
    if highest_prev >= 200 and urgency == 0:
        bid = min(bid, 22.0)

    if budget < DAILY_SALARY:
        bid = min(bid, max(8.0, budget * 0.72))
    else:
        bid = min(bid, budget * 0.85)

    if hp <= 2 and budget > 0:
        bid = max(bid, min(budget, 90.0))

    bid = max(1.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
"""
