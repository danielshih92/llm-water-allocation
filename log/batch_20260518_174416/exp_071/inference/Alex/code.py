# ============================================================
# Experiment: exp_071
# Agent: Alex
# Source: exp_071
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return min(budget, 50)
        if supply >= 22:
            return min(budget, 18)
        return min(budget, 28)

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 6:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('error') in (None, '', False):
            prev_bids.append(prev.get('bid', 0))

    capacity = supply / float(WATER_REQ)

    if hp <= 1:
        base = 66
    elif hp <= 2 or no_water >= 2:
        base = 61
    elif hp <= 4 or no_water >= 1:
        base = 48
    else:
        if capacity >= 1.8:
            base = 24
        elif capacity >= 1.4:
            base = 31
        else:
            base = 39

    if desperate_count >= 2:
        base += 8
    elif desperate_count == 1:
        base += 4

    if rich_count >= 2:
        base += 4

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if hp <= 2 or no_water >= 1:
            target = max(base, highest_prev + 2)
        elif capacity >= 1.8:
            target = max(base, avg_prev * 0.7)
        else:
            target = max(base, highest_prev + 1)
    else:
        target = base

    if capacity >= 1.8 and hp >= 5 and no_water == 0:
        target = min(target, 34)

    if hp <= 2:
        target = max(target, 58)

    target = max(0, min(budget, target))
    return target
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    yesterday_bids = []
    aggressive_bids = []
    needy_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    yesterday_bids.append(bid)
                    if bid >= DAILY_SALARY * 0.85:
                        aggressive_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22
    emergency = hp <= 3 or no_water_days >= 2
    caution = hp <= 5 or no_water_days >= 1

    if emergency:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif tight_supply:
        if aggressive_bids:
            target = max(DAILY_SALARY * 0.78, highest_prev + 1.25)
        else:
            target = max(DAILY_SALARY * 0.62, avg_prev + 2.0)
    elif ample_supply:
        if hp >= 7 and no_water_days == 0:
            target = DAILY_SALARY * 0.28
        else:
            target = DAILY_SALARY * 0.42
    else:
        if caution:
            target = max(DAILY_SALARY * 0.58, avg_prev + 1.0)
        else:
            target = DAILY_SALARY * 0.44

    if needy_count >= 2 and not emergency:
        target += 4.0
    if highest_prev > 100 and not emergency and hp >= 7 and no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.5)

    reserve_floor = 0.0
    if hp >= 6 and no_water_days == 0:
        reserve_floor = DAILY_SALARY * 1.2
    elif hp >= 4:
        reserve_floor = DAILY_SALARY * 0.6

    spend_cap = budget - reserve_floor
    if spend_cap < 0:
        spend_cap = budget * 0.5

    bid = min(target, budget, max(0.0, spend_cap))

    if emergency and bid < min(budget, DAILY_SALARY * 0.9):
        bid = min(budget, DAILY_SALARY * 0.9)
    elif caution and bid < min(budget, DAILY_SALARY * 0.5) and not ample_supply:
        bid = min(budget, DAILY_SALARY * 0.5)

    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_count += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return float(min(budget, 8.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    my_urgent = hp <= 3 or no_water_days >= 1
    very_urgent = hp <= 2 or no_water_days >= 2

    cindy_like = False
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None and bid >= 140 and opp.get('budget', 0) >= 140:
            cindy_like = True
            break

    if very_urgent:
        if cindy_like and slots <= 1:
            return float(min(budget, 145.0))
        return float(min(budget, max(95.0, highest_prev + 3.0, DAILY_SALARY * 1.15)))

    if my_urgent:
        if slots >= 2 and highest_prev >= 130:
            return float(min(budget, 72.0))
        if highest_prev >= 130:
            return float(min(budget, 118.0))
        return float(min(budget, max(78.0, avg_prev + 4.0)))

    if slots >= 2:
        if highest_prev >= 130:
            return float(min(budget, 18.0))
        if desperate_count >= 2:
            return float(min(budget, 52.0))
        return float(min(budget, 44.0))

    if highest_prev >= 140:
        if budget > 500 and day >= 7:
            return float(min(budget, 146.0))
        return float(min(budget, 20.0))

    if highest_prev >= 100:
        return float(min(budget, 36.0))

    target = max(55.0, avg_prev + 2.0)
    if rich_count >= 2:
        target -= 8.0
    return float(min(budget, target))
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(max(0.0, min(budget, 18.0)))

    opp_bids = []
    bob_like_bids = []
    pressure_bids = []
    desperate_count = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            opp_bids.append(float(bid))
            if float(bid) <= 95:
                bob_like_bids.append(float(bid))
            if float(bid) >= 110:
                pressure_bids.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    avg_prev = sum(opp_bids) / len(opp_bids) if opp_bids else 95.0
    low_anchor = max(bob_like_bids) if bob_like_bids else 84.0
    high_pressure = max(pressure_bids) if pressure_bids else max(opp_bids) if opp_bids else 100.0

    units = supply / float(WATER_REQ)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(96.0, low_anchor + 8.0, DAILY_SALARY * 1.28))
        return float(max(0.0, bid))

    if hp <= 4 or no_water >= 1:
        if units >= 1.8:
            bid = max(72.0, low_anchor + 1.5)
        else:
            bid = max(88.0, low_anchor + 4.0)
        if desperate_count >= 2:
            bid = max(bid, 96.0)
        return float(max(0.0, min(budget, bid)))

    if units >= 1.8:
        bid = 24.0
        if avg_prev < 90:
            bid = max(bid, low_anchor + 1.0)
        return float(max(0.0, min(budget, bid)))

    if units >= 1.45:
        bid = max(58.0, low_anchor + 2.0)
        if desperate_count >= 2:
            bid += 6.0
        return float(max(0.0, min(budget, bid)))

    bid = max(82.0, low_anchor + 3.0)
    if high_pressure >= 140 and hp >= 6 and no_water == 0:
        bid = min(bid, 86.0)
    elif desperate_count >= 2:
        bid = max(bid, 92.0)

    if day >= 8 and hp >= 6:
        bid = min(bid, 84.0)

    return float(max(0.0, min(budget, bid)))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        safe = DAILY_SALARY * 0.25
        return max(0.0, min(budget, safe))

    prev_bids = []
    aggressive = 0
    desperate = 0
    zeroish = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 100:
                aggressive += 1
            if bid <= 1:
                zeroish += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate += 1

    units = supply / WATER_REQ
    base = DAILY_SALARY * 0.42

    if units >= 1.9:
        base = DAILY_SALARY * 0.32
    elif units <= 1.25:
        base = DAILY_SALARY * 0.78
    elif units <= 1.55:
        base = DAILY_SALARY * 0.58

    if prev_bids:
        top_prev = max(prev_bids)
        low_prev = min(prev_bids)
        if top_prev >= 140:
            base = min(base, DAILY_SALARY * 0.38)
        elif top_prev >= 110:
            base = max(base, DAILY_SALARY * 0.52)
        elif top_prev <= 5:
            base = min(base, DAILY_SALARY * 0.28)
        if low_prev <= 1 and units >= 1.5:
            base = min(base, DAILY_SALARY * 0.26)

    if aggressive >= 2 and hp >= 6 and no_water == 0:
        base = min(base, DAILY_SALARY * 0.24)

    if desperate >= 2 and units < 1.7:
        base = max(base, DAILY_SALARY * 0.7)

    if hp <= 2 or no_water >= 2:
        base = max(base, DAILY_SALARY * 1.08)
    elif hp <= 4 or no_water >= 1:
        base = max(base, DAILY_SALARY * 0.88)

    if budget < DAILY_SALARY * 1.2:
        base = min(base, budget)
    elif budget > 500 and (hp <= 4 or units < 1.4):
        base = max(base, DAILY_SALARY * 0.95)

    bid = round(max(0.0, min(budget, base)), 2)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) > 500:
                rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

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

    if no_water_days >= 2:
        urgency += 3
    elif no_water_days >= 1:
        urgency += 2

    if day >= 8:
        urgency += 1

    pressure = 0
    if tight_supply:
        pressure += 2
    elif not loose_supply:
        pressure += 1

    if highest_prev >= 110:
        pressure += 3
    elif highest_prev >= 85:
        pressure += 2
    elif highest_prev >= 55:
        pressure += 1

    pressure += min(desperate_count, 2)

    if urgency >= 5:
        bid = max(78.0, highest_prev + 3.0)
    elif urgency >= 3:
        if highest_prev >= 100:
            bid = 72.0 if loose_supply else 88.0
        elif highest_prev >= 70:
            bid = highest_prev + 2.5
        else:
            bid = 58.0 if not tight_supply else 76.0
    else:
        if loose_supply:
            bid = 16.0
        elif tight_supply:
            if highest_prev >= 100:
                bid = 28.0
            elif highest_prev >= 70:
                bid = 46.0
            else:
                bid = 34.0
        else:
            if avg_prev >= 90:
                bid = 22.0
            elif avg_prev >= 60:
                bid = 36.0
            else:
                bid = 30.0

    if rich_aggressive >= 2 and urgency <= 2:
        bid *= 0.85

    reserve = 0.0
    if hp <= 4 or no_water_days >= 1:
        reserve = 0.0
    elif day <= 5:
        reserve = 140.0
    else:
        reserve = 70.0

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable)

    if urgency >= 4 and bid < 65.0 and budget >= 65.0:
        bid = 65.0

    if bid < 0:
        bid = 0.0

    return float(min(budget, bid))
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
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 22.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 1:
        danger += 2

    if danger >= 3:
        bid = max(78.0, highest_prev + 2.0)
        if scarcity == 2:
            bid = max(bid, 92.0)
        return float(min(budget, bid))

    if highest_prev >= 130:
        if hp >= 6 and no_water_days == 0:
            bid = 24.0 if scarcity == 0 else 36.0
        else:
            bid = 88.0 if scarcity < 2 else 98.0
        return float(min(budget, bid))

    if highest_prev >= 100:
        if hp >= 7 and no_water_days == 0 and scarcity == 0:
            bid = 34.0
        else:
            bid = highest_prev + 1.5
        return float(min(budget, bid))

    if highest_prev >= 70:
        bid = highest_prev + 2.0
        if scarcity == 2:
            bid += 8.0
        elif scarcity == 1:
            bid += 4.0
        return float(min(budget, bid))

    base = 38.0
    if scarcity == 1:
        base = 48.0
    elif scarcity == 2:
        base = 62.0

    if rich_opp >= 2:
        base += 6.0
    if urgent_opp >= 2:
        base += 5.0
    if avg_prev > 50:
        base = max(base, avg_prev + 1.0)

    if day >= 8 and hp >= 6 and no_water_days == 0:
        base -= 6.0

    return float(min(budget, max(0.0, base)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if len(alive_opponents) == 0:
        return float(min(budget, 18.0))

    prev_bids = []
    prev_live_bids = []
    opp_pressures = []
    desperate_count = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 0:
                prev_live_bids.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        req = opp.get('water_requirement', WATER_REQ)
        sal = opp.get('daily_salary', DAILY_SALARY)
        pressure = 0.0
        if req > 0:
            pressure = float(sal) / float(req)
        opp_pressures.append(pressure)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_live_prev = max(prev_live_bids) if prev_live_bids else highest_prev
    avg_pressure = sum(opp_pressures) / float(len(opp_pressures)) if opp_pressures else (DAILY_SALARY / float(WATER_REQ))

    supply_ratio = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    scarcity = 1.0 - supply_ratio

    base = 24.0 + 18.0 * scarcity

    if highest_live_prev >= 120:
        base = min(base, 34.0)
    elif highest_live_prev >= 70:
        base = max(base, 36.0)
    elif highest_live_prev > 0:
        base = max(base, highest_live_prev + 2.0)

    if hp <= 2:
        base = max(base, 78.0 + 10.0 * scarcity)
    elif hp <= 4:
        base = max(base, 52.0 + 8.0 * scarcity)

    if no_water >= 2:
        base = max(base, 95.0)
    elif no_water >= 1:
        base = max(base, 62.0)

    if desperate_count >= 2:
        base += 8.0
    elif desperate_count == 1:
        base += 4.0

    if day >= 8 and hp > 5 and budget < 140:
        base *= 0.82

    if budget < 70:
        base = min(base, budget)
    elif budget < 140:
        base = min(base, 0.7 * budget)
    else:
        base = min(base, 0.42 * budget)

    if hp >= 7 and scarcity < 0.25 and highest_live_prev >= 100:
        base = min(base, 22.0)

    if hp <= 3 and budget > 0:
        base = max(base, min(budget, 110.0))

    floor_bid = 8.0 if hp > 4 else 16.0
    bid = max(floor_bid, base)
    bid = min(float(budget), float(bid))

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if opp.get('budget', 0) > 0:
                    strong_prev.append(b)

    if not alive:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    live_pressure = max(strong_prev) if strong_prev else highest_prev

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    danger = 0
    if hp <= 3 or no_water_days >= 2:
        danger = 2
    elif hp <= 5 or no_water_days >= 1:
        danger = 1

    rich_alive = 0
    for opp in alive:
        if opp.get('budget', 0) >= 200:
            rich_alive += 1

    target = 0.0

    if danger >= 2:
        target = max(62.0, live_pressure + 2.5)
        if scarcity == 2:
            target = max(target, 82.0)
    elif scarcity == 2:
        target = max(46.0, live_pressure + 1.5)
        if rich_alive >= 2:
            target = max(target, 72.0)
    elif scarcity == 1:
        target = max(30.0, live_pressure * 0.72)
        if live_pressure < 40:
            target = max(target, live_pressure + 2.0)
    else:
        target = max(12.0, live_pressure * 0.22)
        if rich_alive >= 2:
            target = min(target, 28.0)

    if day >= 8 and budget > 180:
        target += 6.0
    if day >= 9 and (hp <= 6 or no_water_days >= 1):
        target += 10.0

    if budget < 40:
        target = min(target, budget)
    elif budget < 90:
        target = min(target, 0.75 * budget)

    target = max(0.0, min(budget, target))
    return float(target)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    max_prev_bid = 0.0
    aggressive_count = 0
    weak_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                weak_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(float(bid))
                    if float(bid) > max_prev_bid:
                        max_prev_bid = float(bid)
                    if float(bid) >= 85:
                        aggressive_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return min(budget, 20.0)

    scarcity = 1.0
    if supply <= 17:
        scarcity = 1.2
    elif supply >= 23:
        scarcity = 0.9

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

    if prev_bids:
        target = max_prev_bid + 2.0
    else:
        target = 48.0

    if aggressive_count >= 2:
        target += 6.0
    elif aggressive_count == 1:
        target += 2.0

    target *= scarcity

    if danger >= 5:
        bid = max(95.0, target + 8.0)
    elif danger >= 3:
        bid = max(72.0, target)
    elif danger >= 2:
        bid = max(56.0, target - 6.0)
    else:
        if max_prev_bid >= 95 and hp >= 7:
            bid = 18.0
        elif max_prev_bid >= 80 and hp >= 6:
            bid = 28.0
        else:
            bid = max(34.0, target - 16.0)

    if weak_count >= 2 and danger <= 2:
        bid -= 6.0

    reserve_days = 10 - day
    soft_cap = budget
    if reserve_days > 0:
        soft_cap = min(soft_cap, budget - max(0.0, reserve_days - 1) * 18.0)
        soft_cap = max(soft_cap, 0.0)

    if danger <= 1:
        bid = min(bid, max(40.0, budget * 0.18))
    elif danger == 2:
        bid = min(bid, max(65.0, budget * 0.32))
    elif danger == 3:
        bid = min(bid, max(85.0, budget * 0.48))
    else:
        bid = min(bid, max(110.0, budget * 0.72))

    if soft_cap > 0:
        bid = min(bid, soft_cap)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, max_prev_bid + 5.0 if max_prev_bid > 0 else 100.0))

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
"""
