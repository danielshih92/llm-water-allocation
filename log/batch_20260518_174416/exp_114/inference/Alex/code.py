# ============================================================
# Experiment: exp_114
# Agent: Alex
# Source: exp_114
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

    if budget <= 0:
        return 0

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            if opp.get('budget', 0) >= DAILY_SALARY * 4:
                rich_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return min(budget, 20)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = 28 + 18 * scarcity

    if supply >= 22:
        base -= 6
    elif supply <= 17:
        base += 8

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = max(avg_prev + 1.0, highest_prev * 0.92 + 1.5)
        base = max(base, target)
        if highest_prev >= 60:
            if hp > 4 and no_water_days == 0:
                base = min(base, 30)
            else:
                base = max(base, 61)
    else:
        if day == 1:
            base = 34 if supply >= 20 else 40

    if urgent_opp >= 2:
        base += 4
    if rich_opp >= 2:
        base += 3

    if hp <= 2:
        base = max(base, 63)
    elif hp <= 4:
        base += 10

    if no_water_days >= 2:
        base = max(base, 66)
    elif no_water_days == 1:
        base += 12

    days_left = max(1, 10 - day + 1)
    reserve_floor = max(0, (days_left - 1) * 18)
    affordable = max(0, budget - reserve_floor)

    if hp <= 3 or no_water_days >= 1:
        bid = min(budget, max(base, affordable * 0.9 if affordable > 0 else base))
    else:
        bid = min(budget, min(base, max(22, affordable)))

    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
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
        return float(min(budget, 18.0))

    prev_bids = []
    desperate_opp = False
    rich_aggressive = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp = True
        if opp.get('budget', 0) >= 180:
            rich_aggressive = True

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    low_supply = supply <= 17.0
    very_low_hp = hp <= 2 or no_water_days >= 1
    caution_hp = hp <= 4

    if very_low_hp:
        target = max(78.0, highest_prev + 6.0)
        if low_supply:
            target = max(target, 110.0)
        return float(min(budget, target))

    if low_supply:
        target = max(52.0, avg_prev * 0.55, highest_prev * 0.42)
        if desperate_opp:
            target = max(target, highest_prev + 2.0)
        if rich_aggressive and highest_prev >= 120.0:
            target = min(target, 88.0)
        if caution_hp:
            target = max(target, 72.0)
        return float(min(budget, target))

    target = 26.0
    if highest_prev > 0:
        if highest_prev >= 140.0:
            target = 24.0
        elif highest_prev >= 90.0:
            target = 30.0
        else:
            target = max(28.0, highest_prev * 0.38)

    if caution_hp:
        target = max(target, 48.0)
    if desperate_opp:
        target = max(target, 34.0)

    reserve_floor = DAILY_SALARY * 2.0
    if budget < reserve_floor:
        target = min(target, budget * 0.55)

    return float(min(budget, target))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_opp = 0
    rich_opp = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 140:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev.get('bid', 0.0)))

    if not alive:
        return float(min(budget, 12.0))

    slots = supply / float(WATER_REQ)
    scarcity = 1.0
    if slots >= 1.9:
        scarcity = 0.35
    elif slots >= 1.5:
        scarcity = 0.55
    elif slots >= 1.2:
        scarcity = 0.8
    else:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    elif hp <= 6:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days >= 1:
        urgency += 0.45

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    base = DAILY_SALARY * (0.18 + 0.42 * scarcity + 0.35 * urgency)

    if rich_opp >= 2:
        base += 8.0
    elif rich_opp == 1:
        base += 4.0

    if desperate_opp >= 2:
        base += 6.0
    elif desperate_opp == 1:
        base += 3.0

    if highest_prev >= 150:
        if urgency < 0.7 and scarcity < 0.9:
            bid = DAILY_SALARY * 0.22
        else:
            bid = min(budget, highest_prev * 0.72)
    elif highest_prev >= 100:
        if urgency < 0.5 and scarcity < 0.8:
            bid = max(base, DAILY_SALARY * 0.26)
        else:
            bid = max(base, highest_prev + 2.0)
    elif highest_prev > 0:
        target = avg_prev + 3.0
        if scarcity >= 0.8 or urgency >= 0.7:
            target = highest_prev + 2.5
        bid = max(base, target)
    else:
        bid = base

    if day >= 8 and hp > 4 and budget < DAILY_SALARY * 2:
        bid *= 0.82

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.92)
    elif hp <= 4 and scarcity >= 0.8:
        bid = max(bid, DAILY_SALARY * 0.68)

    if slots >= 1.9 and urgency < 0.7:
        bid = min(bid, DAILY_SALARY * 0.34)
    elif slots >= 1.5 and urgency < 0.5:
        bid = min(bid, DAILY_SALARY * 0.48)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    pressure = 0.0
    max_prev_bid = 0.0
    urgent_opp = 0
    active_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            try:
                pbid = float(pbid)
            except:
                pbid = 0.0
            if pbid > max_prev_bid:
                max_prev_bid = pbid
            pressure += pbid
            if pbid > 0:
                active_opp += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1

    avg_pressure = pressure / max(1, len(alive))

    # Since supply < 2 * WATER_REQ in this scenario, at most one full allocation is feasible.
    # Use conservative bids unless survival risk is high.
    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(62.0, max_prev_bid + 2.0))
        return float(max(0.0, bid))

    if hp <= 4 or no_water >= 1:
        bid = min(budget, max(45.0, min(68.0, max_prev_bid + 1.0)))
        return float(max(0.0, bid))

    if max_prev_bid >= 120.0:
        bid = 16.0
    elif max_prev_bid >= 80.0:
        bid = 18.0
    elif max_prev_bid >= 40.0:
        bid = 24.0
    elif active_opp == 0:
        bid = 14.0
    else:
        bid = max(20.0, avg_pressure * 0.75 + 2.0)

    if urgent_opp >= 2:
        bid -= 4.0
    elif urgent_opp == 0 and day >= 7 and hp >= 7:
        bid += 3.0

    reserve = DAILY_SALARY * max(0, 10 - day)
    if budget > reserve + 120:
        bid += 4.0

    bid = min(budget, max(0.0, bid))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    yesterday_bids = []
    urgent_opps = 0
    rich_opps = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opps += 1
            if opp.get('budget', 0) >= 140:
                rich_opps += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if budget <= 0:
        return 0.0

    players = 1 + len(alive)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < players

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    my_urgent = hp <= 3 or no_water >= 1
    my_critical = hp <= 2 or no_water >= 2

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    if my_critical:
        target = max(DAILY_SALARY * 1.9, highest_prev + 8.0)
        return max(0.0, min(budget, target))

    if my_urgent:
        if scarcity:
            target = max(DAILY_SALARY * 1.55, highest_prev + 4.0)
        else:
            target = max(DAILY_SALARY * 1.15, avg_prev + 2.0)
        return max(0.0, min(budget, target))

    if scarcity:
        if highest_prev >= 160:
            target = DAILY_SALARY * 0.42
        elif highest_prev >= 130:
            target = DAILY_SALARY * 0.58
        else:
            target = max(DAILY_SALARY * 0.6, highest_prev + 1.5)

        if urgent_opps >= 2:
            target *= 0.9
        if rich_opps >= 2:
            target *= 1.08
    else:
        target = DAILY_SALARY * 0.26
        if highest_prev < 90:
            target = DAILY_SALARY * 0.34
        if hp >= 8 and no_water == 0:
            target *= 0.9

    if budget < DAILY_SALARY:
        target = min(target, budget * 0.72)

    return max(0.0, min(budget, target))
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

    day = day_context['day']
    supply = day_context['supply']
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
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    dangerous_count = 0
    rich_count = 0
    cindy_like_high = False

    for opp in alive:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            dangerous_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            pbid = prev.get('bid', 0.0)
            prev_bids.append(pbid)
            if pbid >= 120:
                cindy_like_high = True

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22
    critical = hp <= 2 or no_water_days >= 2
    strained = hp <= 4 or no_water_days >= 1

    if critical:
        if cindy_like_high:
            bid = min(budget, 118.0)
        else:
            bid = min(budget, max(78.0, highest_prev + 4.0, DAILY_SALARY * 1.02))
        return float(max(0.0, bid))

    if strained:
        if highest_prev >= 110:
            bid = min(budget, 92.0 if not tight_supply else 104.0)
        elif highest_prev >= 70:
            bid = min(budget, highest_prev + 3.0)
        else:
            bid = min(budget, 61.0 if ample_supply else 72.0)
        return float(max(0.0, bid))

    base = 24.0
    if tight_supply:
        base += 10.0
    if dangerous_count >= 2:
        base += 8.0
    elif dangerous_count == 1:
        base += 4.0
    if rich_count >= 1:
        base += 4.0
    if day >= 8:
        base += 6.0

    if highest_prev >= 120:
        bid = min(budget, 36.0 if hp >= 5 else 58.0)
    elif highest_prev >= 85:
        bid = min(budget, max(base + 8.0, 54.0))
    elif highest_prev >= 45:
        bid = min(budget, max(base + 6.0, highest_prev + 2.0))
    elif avg_prev > 0:
        bid = min(budget, max(base, avg_prev + 1.5))
    else:
        bid = min(budget, base)

    reserve_floor = 0.0
    if hp >= 5 and day <= 7:
        reserve_floor = budget - DAILY_SALARY * 3.2
        if bid > reserve_floor and reserve_floor > 0:
            bid = max(base, reserve_floor)
            bid = min(bid, budget)

    return float(max(0.0, bid))
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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return min(budget, 18.0)

    prev_bids = []
    aggressive = 0
    desperate_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= 120:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 100:
                aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 25.0 - float(supply)
    base = 20.0 + scarcity * 3.0

    if float(supply) >= 23.0:
        base -= 10.0
    elif float(supply) <= 17.0:
        base += 18.0

    if hp <= 2:
        base = max(base, 95.0)
    elif hp <= 4:
        base += 18.0

    if no_water >= 2:
        base = max(base, 120.0)
    elif no_water >= 1:
        base += 22.0

    if desperate_opp >= 2:
        base += 12.0

    if aggressive >= 2 and hp > 4 and no_water == 0 and float(supply) >= 20.0:
        base = min(base, 22.0)
    elif highest_prev >= 130.0 and hp > 4 and no_water == 0:
        base = min(base, 28.0)
    elif highest_prev > 0:
        target = avg_prev * 0.72 + 6.0
        if hp <= 4 or no_water >= 1 or float(supply) <= 17.0:
            target = highest_prev + 3.0
        base = max(base, target)

    if rich_opp >= 2 and day <= 3 and hp > 5 and no_water == 0:
        base = min(base, 24.0)

    if day >= 8:
        base += 10.0

    bid = max(0.0, min(float(budget), float(base)))

    if budget < 25:
        bid = min(float(budget), max(bid, float(budget) * 0.9 if (hp <= 3 or no_water >= 1) else float(budget) * 0.45))

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

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    scarcity = 1.0 - supply_ratio

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    if scarcity > 0.6:
        danger += 1
    if urgent_opp >= 2:
        danger += 1

    if danger >= 5:
        target = max(62.0, highest_prev + 6.0)
    elif danger >= 3:
        target = max(42.0 + 10.0 * scarcity, avg_prev + 3.0)
    else:
        if supply >= 22:
            target = 16.0 + 6.0 * scarcity
        elif supply >= 19:
            target = 22.0 + 10.0 * scarcity
        else:
            target = 30.0 + 12.0 * scarcity
        if highest_prev > 0:
            target = max(target, min(highest_prev + 1.5, 58.0))

    if rich_opp >= 2 and scarcity > 0.5 and danger >= 2:
        target += 6.0

    if day >= 8 and hp > 5 and no_water_days == 0:
        target *= 0.9

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 20.0
    max_affordable = max(0.0, budget - reserve_floor)
    if danger >= 4:
        max_affordable = budget

    bid = min(target, max_affordable)

    if danger >= 5:
        bid = min(max(bid, 68.0), budget)
    elif danger >= 3:
        bid = min(max(bid, 45.0), budget)

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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    threat_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    threat_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, 12.0))

    high_supply = supply >= 22
    low_supply = supply <= 17
    urgent = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    active_highest = max(threat_bids) if threat_bids else highest_prev

    rich_threats = 0
    for opp in alive_opps:
        if opp.get('budget', 0) >= budget * 0.9:
            rich_threats += 1

    if urgent:
        if active_highest >= 110:
            bid = 96.0
        elif active_highest >= 85:
            bid = active_highest + 2.5
        elif active_highest > 0:
            bid = max(63.0, active_highest + 3.0)
        else:
            bid = 68.0
    elif low_supply:
        if active_highest >= 110:
            bid = 34.0
        elif active_highest >= 85:
            bid = 56.0 if rich_threats >= 2 else 61.0
        elif active_highest >= 45:
            bid = active_highest + 1.75
        elif active_highest > 0:
            bid = max(38.0, active_highest + 2.0)
        else:
            bid = 36.0
    elif high_supply:
        if pressured and active_highest < 90:
            bid = max(28.0, active_highest + 1.0 if active_highest > 0 else 28.0)
        else:
            bid = 12.0 if hp > 5 else 20.0
    else:
        if active_highest >= 110:
            bid = 24.0 if hp > 5 else 52.0
        elif active_highest >= 85:
            bid = 44.0 if hp > 5 else 60.0
        elif active_highest >= 45:
            bid = active_highest + 1.5
        elif active_highest > 0:
            bid = max(30.0, active_highest + 2.0)
        else:
            bid = 26.0

    if day >= 8 and hp > 6 and no_water_days == 0:
        bid *= 0.85

    if budget < 40:
        bid = min(bid, max(8.0, budget * 0.7))
    elif budget < 100:
        bid = min(bid, budget * 0.85)
    else:
        bid = min(bid, budget)

    if urgent:
        bid = max(bid, min(budget, 62.0))

    if bid < 0:
        bid = 0.0

    return float(min(budget, round(bid, 2)))
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    urgent_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if float(opp.get('budget', 0)) > budget * 1.2:
                rich_threat += 1
            if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 10)) <= 4:
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
        danger += 0.6
    elif hp <= 6:
        danger += 0.25

    if no_water_days >= 2:
        danger += 1.0
    elif no_water_days == 1:
        danger += 0.55

    danger += scarcity * 0.45
    if day >= 8:
        danger += 0.15

    if hp <= 2 or no_water_days >= 2:
        bid = max(62.0, highest_prev + 2.5)
        if supply <= 17:
            bid = max(bid, 68.0)
        return float(min(budget, bid))

    if hp <= 4 or no_water_days == 1:
        if highest_prev >= 120:
            bid = 58.0 + scarcity * 10.0
        else:
            bid = max(52.0 + scarcity * 8.0, highest_prev + 2.0)
        return float(min(budget, bid))

    if highest_prev >= 130:
        bid = 16.0 + scarcity * 8.0
    elif highest_prev >= 100:
        bid = 22.0 + scarcity * 10.0
    elif highest_prev >= 70:
        bid = max(30.0 + scarcity * 8.0, avg_prev * 0.55)
    elif highest_prev > 0:
        bid = max(26.0 + scarcity * 8.0, highest_prev * 0.72)
    else:
        bid = 24.0 + scarcity * 8.0

    if rich_threat >= 2:
        bid -= 3.0
    elif urgent_opp >= 2 and supply <= 18:
        bid += 4.0

    if day >= 9 and hp >= 7 and no_water_days == 0:
        bid -= 4.0

    if bid < 8.0:
        bid = 8.0

    return float(min(budget, bid))
"""
