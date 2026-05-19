# ============================================================
# Experiment: exp_053
# Agent: Alex
# Source: exp_053
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
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 21)

    total_players = 1 + len(alive_opponents)
    scarcity = float(supply) / float(total_players * WATER_REQ)

    prev_bids = []
    desperate_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_opponents += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.92
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.72
    else:
        if scarcity >= 1.2:
            base = DAILY_SALARY * 0.34
        elif scarcity >= 0.9:
            base = DAILY_SALARY * 0.48
        elif scarcity >= 0.7:
            base = DAILY_SALARY * 0.62
        else:
            base = DAILY_SALARY * 0.8

    if desperate_opponents > 0 and hp > 4 and no_water_days == 0:
        base -= 6
    if rich_opponents >= max(1, len(alive_opponents) // 2):
        base += 4

    if highest_prev > 0:
        if hp <= 4 or no_water_days >= 1:
            target = highest_prev + 2
            if target > base:
                base = target
        else:
            if highest_prev >= DAILY_SALARY * 0.85:
                base = min(base, DAILY_SALARY * 0.42)
            else:
                soft_target = highest_prev + 1
                if soft_target > base and scarcity < 1.0:
                    base = soft_target

    if budget < DAILY_SALARY * 0.6 and hp > 3 and no_water_days == 0:
        base = min(base, budget * 0.55)

    if base < 0:
        base = 0
    if base > budget:
        base = budget

    return float(base)
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
    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_opp_count += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22
    my_urgent = hp <= 3 or no_water_days >= 1
    very_urgent = hp <= 2 or no_water_days >= 2

    if very_urgent:
        bid = max(62.0, highest_prev + 2.0)
        if supply_tight:
            bid = max(bid, 76.0)
        return float(min(budget, bid))

    if my_urgent:
        bid = max(52.0, avg_prev + 2.0)
        if highest_prev >= 75.0:
            bid = max(bid, highest_prev + 1.0)
        if supply_tight:
            bid += 6.0
        return float(min(budget, bid))

    if supply_loose and urgent_opp_count == 0:
        return float(min(budget, 24.0))

    if supply_loose:
        bid = 28.0 if highest_prev < 60.0 else 34.0
        return float(min(budget, bid))

    if supply_tight:
        if highest_prev >= 78.0:
            bid = 41.0
        elif highest_prev >= 60.0:
            bid = highest_prev + 1.5
        else:
            bid = 49.0 + min(6.0, float(rich_opp_count))
        return float(min(budget, bid))

    bid = 36.0
    if highest_prev >= 75.0:
        bid = 33.0
    elif highest_prev >= 58.0:
        bid = highest_prev + 1.0
    elif avg_prev > 0:
        bid = max(38.0, avg_prev - 3.0)

    if day >= 8 and hp >= 6 and budget < DAILY_SALARY * 2:
        bid -= 4.0

    bid = max(0.0, bid)
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    dangerous_bids = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if bid >= 80:
                    dangerous_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return min(budget, 18.0 if hp > 3 else 42.0)

    high_supply = supply >= 21
    low_supply = supply <= 17

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    danger_count = len(dangerous_bids)

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

    if high_supply:
        urgency += 1
    if low_supply:
        urgency -= 1

    if danger_count >= 2 and not high_supply:
        urgency -= 1

    if urgency <= 0:
        bid = 8.0 if low_supply else 14.0
    elif urgency == 1:
        if highest_prev >= 120:
            bid = 24.0 if not high_supply else 38.0
        else:
            bid = max(22.0, min(40.0, avg_prev * 0.45 + 6.0))
    elif urgency == 2:
        if highest_prev >= 120:
            bid = 48.0 if high_supply else 34.0
        elif highest_prev >= 80:
            bid = min(58.0, highest_prev + 2.0)
        else:
            bid = 44.0
    else:
        if highest_prev >= 120:
            bid = 72.0 if hp > 1 else 88.0
        elif highest_prev >= 80:
            bid = min(92.0, highest_prev + 3.0)
        else:
            bid = 60.0 if high_supply else 68.0

    if budget < 25:
        bid = min(bid, budget)
    elif budget < 60:
        bid = min(bid, 0.85 * budget)
    else:
        bid = min(bid, 0.72 * budget)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, 63.0))

    if low_supply and danger_count >= 2 and hp > 4 and no_water == 0:
        bid = min(bid, 18.0)

    return max(0.0, min(budget, float(bid)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if float(opp.get('budget', 0)) >= DAILY_SALARY * 1.2:
                rich_count += 1
            if int(opp.get('no_water_days', 0)) >= 2 or float(opp.get('hp', 0)) <= 4:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass

    if not alive:
        return min(budget, 8.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgency = 0
    if no_water_days >= 2:
        urgency += 3
    elif no_water_days == 1:
        urgency += 1
    if hp <= 3:
        urgency += 3
    elif hp <= 6:
        urgency += 2
    elif hp <= 9:
        urgency += 1

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if urgency >= 5:
        base = DAILY_SALARY * 0.95
    elif urgency >= 3:
        base = DAILY_SALARY * 0.78
    elif tight_supply:
        base = DAILY_SALARY * 0.62
    elif loose_supply:
        base = DAILY_SALARY * 0.34
    else:
        base = DAILY_SALARY * 0.48

    if highest_prev > 0:
        if urgency >= 3:
            target = max(base, min(highest_prev + 2.0, DAILY_SALARY * 1.02))
        else:
            if highest_prev >= DAILY_SALARY * 1.4:
                target = min(base, DAILY_SALARY * 0.42)
            elif highest_prev >= DAILY_SALARY * 0.9:
                target = min(max(base, avg_prev * 0.9), DAILY_SALARY * 0.68)
            else:
                target = max(base, highest_prev + 1.5)
    else:
        target = base

    if desperate_count >= 2 and urgency < 3:
        target *= 0.88
    if rich_count >= 2 and (tight_supply or urgency >= 3):
        target *= 1.08
    if day >= 8 and hp > 6 and no_water_days == 0:
        target *= 0.9

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if urgency < 3 and days_left > 0:
        reserve_floor = min(budget * 0.45, days_left * 8.0)

    bid = min(target, budget)
    if budget - bid < reserve_floor and urgency < 3:
        bid = max(0.0, budget - reserve_floor)

    if urgency >= 5:
        bid = max(bid, min(budget, DAILY_SALARY * 0.92))
    elif no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.85))

    if bid < 0:
        bid = 0.0
    return float(round(min(budget, bid), 2))
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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    strong_prev = 0.0
    cindy_prev = None
    david_prev = None
    for oid, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            prev_bids.append(bid)
            if bid > strong_prev:
                strong_prev = bid
        if oid == 'Cindy' and bid is not None:
            cindy_prev = float(bid)
        if oid == 'David' and bid is not None:
            david_prev = float(bid)

    urgent = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if not alive:
        return float(min(budget, 15.0))

    if slots >= 2:
        base = 18.0
        if cindy_prev is not None and cindy_prev >= 120:
            base = 12.0
        if david_prev is not None and david_prev < 60:
            base = 22.0
        if pressured:
            base = max(base, 48.0)
        if urgent:
            base = max(base, 78.0)
        return float(min(budget, base))

    target = 42.0
    if strong_prev > 0:
        target = max(target, strong_prev + 2.0)

    if cindy_prev is not None and cindy_prev >= 140:
        target = min(target, 96.0)
    if david_prev is not None and david_prev <= 70:
        target = max(target, david_prev + 3.0)

    if pressured:
        target = max(target, 72.0)
    if urgent:
        target = max(target, 95.0)

    if day >= 8 and hp >= 5 and no_water == 0:
        target = min(target, 65.0)

    return float(min(budget, target))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = DAILY_SALARY * 0.22
        if hp <= 2 or no_water_days >= 2:
            safe_bid = DAILY_SALARY * 0.55
        return float(min(budget, safe_bid))

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units <= 1.05:
        scarcity = 3
    elif units <= 1.6:
        scarcity = 2
    elif units <= 2.2:
        scarcity = 1

    prev_bids = []
    stressed_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= 500:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            stressed_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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

    if urgency >= 5:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 4.0)
    elif scarcity >= 3:
        if urgency >= 2:
            bid = max(DAILY_SALARY * 0.88, highest_prev + 3.0)
        else:
            bid = max(DAILY_SALARY * 0.62, avg_prev * 0.72 + 2.0)
    elif scarcity == 2:
        bid = DAILY_SALARY * 0.46 + rich_opp * 3.0 + stressed_opp * 2.0
        if highest_prev > 0:
            bid = max(bid, min(highest_prev * 0.58 + 1.5, DAILY_SALARY * 0.78))
        if urgency >= 2:
            bid = max(bid, DAILY_SALARY * 0.68)
    elif scarcity == 1:
        bid = DAILY_SALARY * 0.30 + rich_opp * 2.0
        if highest_prev > DAILY_SALARY * 0.9:
            bid = min(bid, DAILY_SALARY * 0.28)
        elif highest_prev > 0:
            bid = max(bid, min(highest_prev * 0.33, DAILY_SALARY * 0.42))
        if urgency >= 2:
            bid = max(bid, DAILY_SALARY * 0.55)
    else:
        bid = DAILY_SALARY * 0.18
        if urgency >= 2:
            bid = DAILY_SALARY * 0.42
        if highest_prev > DAILY_SALARY * 1.2:
            bid = min(bid, DAILY_SALARY * 0.16)

    if day >= 8 and hp >= 6 and urgency == 0:
        bid = min(bid, DAILY_SALARY * 0.26)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    if budget < reserve_floor:
        bid = min(bid, max(0.0, budget * 0.55))

    bid = max(0.0, min(budget, bid))
    return float(bid)
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, 18.0))

    prev_bids = []
    rich_threats = 0
    desperate_opp = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('budget', 0) >= 400:
            rich_threats += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 3 or no_water >= 1
    very_urgent = hp <= 2 or no_water >= 2
    abundant = supply >= 22
    scarce = supply <= 17

    if very_urgent:
        if abundant:
            bid = 96.0
        else:
            bid = 88.0
        if highest_prev > 0:
            bid = max(bid, min(110.0, highest_prev * 0.78))
        return float(min(budget, bid))

    if urgent:
        bid = 62.0 if abundant else 74.0
        if desperate_opp >= 2:
            bid += 8.0
        return float(min(budget, bid))

    if scarce and highest_prev >= 110.0 and rich_threats >= 2:
        return float(min(budget, 9.0))

    if abundant:
        bid = 44.0
        if avg_prev < 60.0:
            bid = 52.0
        if day >= 8:
            bid += 6.0
        return float(min(budget, bid))

    bid = 28.0
    if highest_prev < 50.0:
        bid = 36.0
    elif highest_prev < 90.0:
        bid = 41.0
    else:
        bid = 24.0

    if day >= 8 and hp >= 5 and budget > 180:
        bid += 6.0

    return float(min(budget, bid))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                    dangerous_prev.append(bid)

    guaranteed_units = int(supply // WATER_REQ)
    contested = guaranteed_units <= 1

    if not alive_opponents:
        base = 18.0 if hp > 4 else 42.0
        return float(min(budget, base))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    danger_high = max(dangerous_prev) if dangerous_prev else highest_prev

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

    if contested:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        bid = max(92.0, danger_high + 8.0)
    elif urgency >= 4:
        bid = max(68.0, highest_prev + 4.0)
    elif urgency >= 2:
        bid = max(42.0, min(65.0, highest_prev * 0.72 + 3.0))
    else:
        bid = 24.0 if not contested else 31.0
        if highest_prev > 0:
            bid = max(bid, min(44.0, highest_prev * 0.45))

    rich_live = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > budget * 1.5:
            rich_live += 1
    if rich_live >= 2 and urgency <= 2:
        bid *= 0.9

    if hp >= 7 and no_water == 0 and highest_prev >= 110:
        bid = min(bid, 36.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 35.0
    max_affordable = max(0.0, budget - reserve_floor)
    if urgency >= 4:
        max_affordable = budget

    final_bid = min(budget, max_affordable if max_affordable > 0 else budget, bid)

    if urgency >= 5:
        final_bid = min(budget, max(final_bid, 84.0))
    elif urgency >= 3:
        final_bid = min(budget, max(final_bid, 55.0))

    if final_bid < 0:
        final_bid = 0.0
    return float(final_bid)
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    pressure_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                threat = float(bid)
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                    threat += 8.0
                if opp.get('budget', 0) < threat:
                    threat = float(opp.get('budget', 0))
                pressure_bids.append(threat)

    if not alive:
        return float(min(budget, 18.0))

    scarcity = max(0.0, (WATER_REQ * (len(alive) + 1)) - supply)
    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if pressure_bids:
        top_pressure = max(pressure_bids)
    elif prev_bids:
        top_pressure = max(prev_bids)
    else:
        top_pressure = 0.0

    if critical:
        bid = max(58.0, top_pressure + 3.0)
    elif urgent:
        bid = max(46.0, top_pressure + 2.0)
    else:
        if top_pressure >= 180.0:
            bid = 14.0 if hp >= 6 else 42.0
        elif top_pressure >= 100.0:
            bid = 20.0 if hp >= 7 else 38.0
        elif top_pressure >= 60.0:
            bid = top_pressure + 1.5
        elif top_pressure > 0.0:
            bid = max(24.0, top_pressure + 1.0)
        else:
            bid = 26.0

    if scarcity > WATER_REQ:
        bid += 8.0
    elif scarcity > 0:
        bid += 4.0

    if supply >= 22:
        bid -= 4.0
    elif supply <= 17:
        bid += 4.0

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid -= 3.0

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve = DAILY_SALARY * 0.5

    max_affordable = budget - reserve
    if urgent:
        max_affordable = budget
    if max_affordable < 0:
        max_affordable = budget * 0.5

    bid = min(bid, budget, max_affordable)
    if urgent:
        bid = min(max(bid, 35.0), budget)
    else:
        bid = min(max(bid, 8.0), budget)

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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0.0)
                prev_bids.append(b)
                if b >= 80:
                    dangerous_prev.append(b)

    if not alive:
        return float(min(budget, 18.0))

    competitors = len(alive) + 1
    scarcity = competitors * WATER_REQ - supply

    high_pressure = max(prev_bids) if prev_bids else 0.0
    moderate_pressure = 0.0
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        moderate_pressure = sorted_bids[int(len(sorted_bids) // 2)]

    urgent = hp <= 3 or no_water >= 2
    stressed = hp <= 5 or no_water >= 1

    if urgent:
        if scarcity >= 25:
            bid = max(105.0, high_pressure + 3.0)
        elif scarcity >= 15:
            bid = max(88.0, moderate_pressure + 2.0)
        else:
            bid = 72.0
        return float(min(budget, bid))

    if scarcity <= 0:
        if high_pressure >= 110 and hp >= 6:
            bid = 8.0
        elif high_pressure >= 85:
            bid = 14.0
        else:
            bid = 18.0
        return float(min(budget, bid))

    if scarcity <= 13:
        if stressed:
            bid = max(52.0, moderate_pressure + 1.5)
        else:
            bid = 34.0 if high_pressure >= 90 else 42.0
        return float(min(budget, bid))

    if scarcity <= 26:
        if high_pressure >= 120:
            bid = 50.0 if hp >= 7 else 82.0
        elif high_pressure >= 90:
            bid = max(60.0, moderate_pressure + 2.0)
        else:
            bid = 68.0
        return float(min(budget, bid))

    if high_pressure >= 120:
        bid = 62.0 if hp >= 8 else 95.0
    elif high_pressure >= 90:
        bid = 78.0
    else:
        bid = 84.0

    if day >= 8 and hp >= 6 and budget < 140:
        bid -= 10.0

    return float(min(budget, max(0.0, bid)))
"""
