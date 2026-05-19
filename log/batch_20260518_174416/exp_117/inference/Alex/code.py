# ============================================================
# Experiment: exp_117
# Agent: Alex
# Source: exp_117
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

    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return min(budget, 50.0)
        return min(budget, 28.0)

    player_count = 1 + len(alive_opponents)
    units_available = int(float(supply) / float(WATER_REQ))
    scarcity = units_available < player_count

    prev_bids = []
    desperate_opp = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            if prev.get('error'):
                desperate_opp = True
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp = True

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water >= 2:
        bid = max(60.0, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        bid = max(46.0, avg_prev + 2.0)
    else:
        if scarcity:
            bid = max(34.0, avg_prev + 1.0)
        else:
            bid = 24.0

    if desperate_opp and hp > 4 and no_water == 0:
        bid = min(bid, 26.0)

    if day >= 8:
        if hp <= 4 or no_water >= 1:
            bid = max(bid, 52.0)
        else:
            bid = max(bid, 30.0)

    bid = min(float(budget), float(bid))
    if bid < 0:
        bid = 0.0
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                b = float(bid)
                prev_bids.append(b)
                if b >= 90:
                    dangerous_prev.append(b)

    if not alive:
        return min(budget, 18.0)

    low_supply = supply <= 17
    mid_supply = supply <= 20
    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    if prev_bids:
        filtered = [b for b in prev_bids if b < 90]
        if filtered:
            moderate_prev = max(filtered)

    target = 0.0

    if critical:
        if dangerous_prev:
            target = min(0.92 * DAILY_SALARY, max(dangerous_prev) + 2.0)
        elif highest_prev > 0:
            target = highest_prev + 2.0
        else:
            target = 0.88 * DAILY_SALARY
    elif urgent:
        if dangerous_prev and low_supply:
            target = 0.86 * DAILY_SALARY
        elif highest_prev > 0:
            target = min(0.82 * DAILY_SALARY, highest_prev + 1.5)
        else:
            target = 0.72 * DAILY_SALARY
    else:
        if low_supply:
            if moderate_prev > 0:
                target = min(0.68 * DAILY_SALARY, moderate_prev + 1.5)
            elif dangerous_prev:
                target = 0.34 * DAILY_SALARY
            else:
                target = 0.52 * DAILY_SALARY
        elif mid_supply:
            if dangerous_prev:
                target = 0.26 * DAILY_SALARY
            elif moderate_prev > 0:
                target = min(0.58 * DAILY_SALARY, moderate_prev + 1.0)
            else:
                target = 0.42 * DAILY_SALARY
        else:
            if desperate_count >= 2:
                target = 0.38 * DAILY_SALARY
            else:
                target = 0.24 * DAILY_SALARY

    if day >= 8 and hp >= 6 and budget > 140 and low_supply:
        target = max(target, 0.62 * DAILY_SALARY)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 20.0
    max_affordable = max(0.0, budget - reserve_floor)
    if critical:
        max_affordable = budget

    bid = min(target, max_affordable)
    if bid <= 0 and budget > 0:
        bid = min(budget, 8.0 if not urgent else 20.0)

    if bid > budget:
        bid = budget
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

    supply = day_context['supply']
    day = day_context['day']
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
        if hp <= 3 or no_water >= 1:
            base = DAILY_SALARY * 0.6
        return float(min(budget, base))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 140:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tightness = 1.0 - scarcity

    base = DAILY_SALARY * (0.28 + 0.22 * tightness)

    if highest_prev > 0:
        if highest_prev >= 150:
            reactive = DAILY_SALARY * 0.22
        elif highest_prev >= 100:
            reactive = DAILY_SALARY * 0.32
        elif highest_prev >= 70:
            reactive = min(DAILY_SALARY * 0.78, highest_prev * 0.62)
        else:
            reactive = min(DAILY_SALARY * 0.72, max(base, avg_prev + 4.0))
    else:
        reactive = base

    bid = max(base, reactive)

    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.78)

    if no_water >= 2:
        bid = max(bid, DAILY_SALARY * 0.98)
    elif no_water >= 1:
        bid = max(bid, DAILY_SALARY * 0.82)

    if supply <= 17:
        bid += 8.0
    elif supply >= 23:
        bid -= 6.0

    bid += min(desperate_count * 2.0, 6.0)
    if rich_count >= 2 and hp > 4 and no_water == 0:
        bid -= 4.0

    if day >= 8 and budget > DAILY_SALARY * 2:
        bid += 5.0

    reserve = 0.0
    if hp > 4 and no_water == 0:
        reserve = DAILY_SALARY * 0.35
    elif hp > 2:
        reserve = DAILY_SALARY * 0.15

    max_affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = max(0.0, bid)

    if bid < 1.0 and budget >= 1.0 and (hp <= 4 or supply <= 17):
        bid = 1.0

    return float(min(budget, bid))
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

    alive = []
    prev_bids = []
    rich_threat = 0
    urgent_opps = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_threat += 1
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_opps += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0, min(budget, 1.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = 1.0
    if supply <= 16:
        scarcity = 1.2
    elif supply >= 23:
        scarcity = 0.9

    survival_mode = hp <= 2 or no_water >= 2
    caution_mode = hp <= 4 or no_water >= 1

    if survival_mode:
        bid = max(DAILY_SALARY * 0.95, max_prev + 2.0)
        if budget < bid:
            bid = budget
        return max(0, bid)

    if caution_mode:
        base = DAILY_SALARY * 0.72 * scarcity
        if max_prev > 0:
            bid = max(base, min(max_prev + 1.25, DAILY_SALARY * 0.92))
        else:
            bid = base
        if rich_threat >= 2:
            bid += 3.0
        return max(0, min(budget, bid))

    if max_prev >= DAILY_SALARY * 0.9:
        bid = DAILY_SALARY * 0.28
    elif max_prev >= DAILY_SALARY * 0.7:
        bid = DAILY_SALARY * 0.38
    elif max_prev > 0:
        bid = max(DAILY_SALARY * 0.42 * scarcity, avg_prev * 0.9)
    else:
        bid = DAILY_SALARY * 0.4 * scarcity

    if urgent_opps >= 2 and supply <= 18:
        bid += 4.0
    if day >= 8 and hp >= 6 and budget > DAILY_SALARY * 3:
        bid += 3.0

    bid = min(budget, bid)
    return max(0, bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        safe_bid = 18.0 if hp > 3 else 45.0
        return float(max(0.0, min(budget, safe_bid)))

    prev_bids = []
    threatening_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 90.0:
                threatening_bids.append(float(bid))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            desperate_count += 1
        if opp.get('budget', 0) >= 700:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    total_players = 1 + len(alive_opponents)
    capacity = int(supply // WATER_REQ)
    scarce = capacity < total_players
    very_scarce = capacity <= 1

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

    if very_scarce:
        target = max(118.0, highest_prev + 4.0, avg_prev + 8.0)
        if urgency >= 3:
            target = max(target, 132.0)
        if rich_count >= 2:
            target += 6.0
    elif scarce:
        if urgency >= 3:
            target = max(96.0, highest_prev + 2.0)
        elif urgency >= 1:
            target = max(72.0, avg_prev * 0.8)
        else:
            target = 38.0 if highest_prev >= 100.0 else 52.0
    else:
        if urgency >= 3:
            target = 70.0
        elif urgency >= 1:
            target = 34.0
        else:
            target = 16.0

    if desperate_count >= 2 and scarce:
        target += 8.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 35.0
    affordable = max(0.0, budget - reserve_floor)
    if urgency >= 3:
        affordable = budget

    bid = min(target, affordable if affordable > 0 else budget)

    if hp <= 1 or no_water_days >= 2:
        bid = min(budget, max(bid, 145.0))
    elif hp <= 3 and scarce:
        bid = min(budget, max(bid, 110.0))

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_opps = 0
    rich_opps = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opps += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opps += 1
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

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    base = 24.0 + 18.0 * scarcity

    if supply >= 23:
        base -= 8.0
    elif supply <= 17:
        base += 10.0

    if rich_opps >= 2:
        base += 6.0
    if urgent_opps >= 1:
        base += 5.0

    if highest_prev >= 150:
        base -= 4.0
    elif highest_prev >= 90:
        base += 6.0
    elif highest_prev > 0:
        base = max(base, min(58.0, avg_prev + 4.0))

    if hp <= 2 or no_water >= 2:
        bid = max(base, 66.0)
    elif hp <= 4 or no_water >= 1:
        bid = max(base, 52.0)
    else:
        bid = base

    if day >= 8:
        bid += 6.0
    if day == 10:
        bid += 8.0

    reserve = 0.0
    remaining_days = max(0, 10 - day)
    if hp > 4 and remaining_days > 0:
        reserve = min(remaining_days * 8.0, budget * 0.45)

    affordable = budget - reserve
    if hp <= 3 or no_water >= 1:
        affordable = budget

    bid = min(bid, affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_prev = []
    needy_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 4:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80:
                    dangerous_prev.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0
    tightness = 1.0 - scarcity

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

    if supply <= 17:
        urgency += 2
    elif supply <= 20:
        urgency += 1

    if needy_count >= 2:
        urgency += 1

    if budget < DAILY_SALARY * 1.2:
        urgency -= 1

    if urgency <= 0:
        base = 14.0 + 8.0 * tightness
        if highest_prev >= 120 and hp > 4:
            base = min(base, 22.0)
        bid = base
    elif urgency == 1:
        bid = max(24.0, avg_prev * 0.45 + 6.0, highest_prev * 0.28 + 8.0)
    elif urgency == 2:
        bid = max(38.0, avg_prev * 0.62 + 8.0, highest_prev * 0.52 + 6.0)
    elif urgency == 3:
        bid = max(55.0, highest_prev + 2.0 if highest_prev > 0 else 60.0)
    else:
        bid = max(72.0, highest_prev + 3.0 if highest_prev > 0 else 78.0)

    if dangerous_prev and hp > 4 and no_water == 0 and supply >= 20:
        bid = min(bid, 36.0)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, highest_prev + 3.0 if highest_prev > 0 else 75.0)

    reserve = 0.0
    if hp > 4 and no_water == 0:
        reserve = 18.0
    elif hp > 2:
        reserve = 8.0

    max_affordable = max(0.0, budget - reserve)
    if max_affordable <= 0:
        return float(min(budget, 6.0))

    bid = min(bid, max_affordable)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        safe = DAILY_SALARY * 0.25
        if hp <= 3 or no_water >= 1:
            safe = DAILY_SALARY * 0.55
        return float(min(budget, safe))

    prev_bids = []
    prev_neediness = []
    rich_live = 0
    for opp in alive_opps:
        if opp.get('budget', 0) >= 120:
            rich_live += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        need = 0
        if opp.get('hp', 10) <= 3:
            need += 2
        elif opp.get('hp', 10) <= 5:
            need += 1
        if opp.get('no_water_days', 0) >= 2:
            need += 2
        elif opp.get('no_water_days', 0) >= 1:
            need += 1
        prev_neediness.append(need)

    high_prev = max(prev_bids) if prev_bids else 0.0
    low_prev = min(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_need = max(prev_neediness) if prev_neediness else 0

    player_count = 1 + len(alive_opps)
    likely_units = int(supply // WATER_REQ)
    scarcity = likely_units < player_count
    severe_scarcity = likely_units <= 1

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 3
    elif hp <= 6:
        urgency += 2
    else:
        urgency += 1

    if no_water >= 2:
        urgency += 4
    elif no_water >= 1:
        urgency += 2

    if severe_scarcity:
        urgency += 2
    elif scarcity:
        urgency += 1

    if day_context['day'] >= 8:
        urgency += 1

    if high_prev >= 150:
        if urgency <= 3:
            bid = DAILY_SALARY * 0.18
        elif urgency <= 5:
            bid = DAILY_SALARY * 0.42
        elif urgency <= 7:
            bid = DAILY_SALARY * 0.88
        else:
            bid = min(budget, max(DAILY_SALARY * 1.15, high_prev * 0.9))
    else:
        if urgency <= 2:
            bid = max(10.0, low_prev + 1.0, DAILY_SALARY * 0.22)
        elif urgency <= 4:
            bid = max(DAILY_SALARY * 0.45, avg_prev + 2.0)
        elif urgency <= 6:
            bid = max(DAILY_SALARY * 0.72, high_prev + 3.0)
        else:
            bid = max(DAILY_SALARY * 0.95, high_prev + 8.0)

    if rich_live >= 2 and high_prev >= 150 and urgency <= 5:
        bid = min(bid, DAILY_SALARY * 0.4)

    if max_need >= 3 and urgency >= 6:
        bid = max(bid, DAILY_SALARY * 0.95)

    reserve = 0.0
    if hp >= 7 and no_water == 0:
        reserve = 20.0
    elif hp >= 5:
        reserve = 10.0

    cap = max(0.0, budget - reserve)
    if urgency >= 7:
        cap = budget

    bid = min(bid, cap if cap > 0 else budget)
    bid = max(0.0, min(bid, budget))
    return float(bid)
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

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply <= 17)
    abundance = (supply >= 22)
    critical_me = (hp <= 3 or no_water_days >= 1)
    weak_me = (hp <= 5)

    target = 0.0

    if critical_me:
        if highest_prev > 0:
            target = max(DAILY_SALARY * 1.25, highest_prev + 4.0)
        else:
            target = DAILY_SALARY * 1.1
        if scarcity:
            target += 10.0
    elif scarcity:
        if highest_prev >= 120:
            target = highest_prev + 2.0
        elif highest_prev > 0:
            target = max(DAILY_SALARY * 0.95, avg_prev + 8.0)
        else:
            target = DAILY_SALARY * 0.9
        if urgent_opp >= 2:
            target += 6.0
    elif abundance:
        if hp >= 7 and no_water_days == 0:
            target = DAILY_SALARY * 0.18
        else:
            target = DAILY_SALARY * 0.45
        if highest_prev >= 140:
            target = min(target, DAILY_SALARY * 0.25)
    else:
        if weak_me:
            if highest_prev >= 120:
                target = highest_prev + 1.0
            elif highest_prev > 0:
                target = max(DAILY_SALARY * 0.8, avg_prev + 5.0)
            else:
                target = DAILY_SALARY * 0.75
        else:
            if highest_prev >= 140:
                target = DAILY_SALARY * 0.28
            elif highest_prev >= 100:
                target = DAILY_SALARY * 0.52
            elif highest_prev > 0:
                target = max(DAILY_SALARY * 0.42, avg_prev * 0.72)
            else:
                target = DAILY_SALARY * 0.4

    if day >= 8:
        if hp >= 6 and no_water_days == 0 and not scarcity:
            target *= 0.85
        elif critical_me:
            target *= 1.08

    if rich_opp >= 2 and critical_me:
        target += 5.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 20.0
    elif day <= 9:
        reserve_floor = 5.0

    max_affordable = budget - reserve_floor
    if max_affordable < 0:
        max_affordable = budget

    bid = min(target, max_affordable)
    if critical_me:
        bid = min(target, budget)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_budgets = []
    urgent_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_budgets.append(float(opp.get('budget', 0)))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
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
    rich_opp = max(opp_budgets) if opp_budgets else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

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

    if day >= 8:
        danger += 1

    if supply <= 17:
        danger += 1

    if danger >= 5:
        base = 0.92 * DAILY_SALARY + 0.18 * highest_prev
        if highest_prev >= 150:
            base = max(base, 118.0)
        bid = min(budget, base)
        return float(max(0.0, bid))

    if danger >= 3:
        target = max(0.72 * DAILY_SALARY, min(highest_prev + 2.5, 0.95 * DAILY_SALARY + 18.0))
        if supply >= 22 and hp >= 6 and no_water_days == 0:
            target *= 0.82
        bid = min(budget, target)
        return float(max(0.0, bid))

    if highest_prev >= 170:
        if supply >= 21 and hp >= 6 and no_water_days == 0:
            return float(min(budget, 16.0))
        return float(min(budget, 54.0))

    if highest_prev >= 120:
        if supply >= 20:
            target = 24.0 + 8.0 * (1.0 - supply_pressure)
        else:
            target = 42.0
        if urgent_opp >= 2:
            target += 6.0
        return float(max(0.0, min(budget, target)))

    target = 26.0 + 18.0 * supply_pressure
    if avg_prev > 0:
        target = max(target, min(avg_prev + 1.5, 52.0))
    if rich_opp > budget * 1.8 and supply <= 18:
        target += 6.0
    if supply >= 23 and hp >= 7 and no_water_days == 0:
        target -= 8.0
    if day == 1:
        target -= 4.0

    target = max(12.0, target)
    return float(max(0.0, min(budget, target)))
"""
