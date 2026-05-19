# ============================================================
# Experiment: exp_109
# Agent: Alex
# Source: exp_109
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
        bid = DAILY_SALARY * 0.25
        if hp <= 2 or no_water >= 2:
            bid = DAILY_SALARY * 0.6
        return min(budget, max(0, bid))

    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) > DAILY_SALARY * 6:
            rich_aggressive += 1

    player_count = len(alive) + 1
    approx_winners = max(1, int(supply // WATER_REQ))
    scarcity = approx_winners < player_count
    very_scarce = approx_winners <= max(1, player_count // 2)

    base = DAILY_SALARY * 0.42
    if not scarcity:
        base = DAILY_SALARY * 0.28
    elif very_scarce:
        base = DAILY_SALARY * 0.58

    if hp <= 2 or no_water >= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4 or no_water >= 1:
        base = max(base, DAILY_SALARY * 0.68)

    if desperate_count >= max(1, len(alive) // 2):
        base += 8
    if rich_aggressive >= max(1, len(alive) // 2):
        base += 5

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if hp > 4 and no_water == 0 and highest_prev >= DAILY_SALARY * 0.9:
            base = min(base, DAILY_SALARY * 0.35)
        else:
            target = max(avg_prev + 1.0, highest_prev + 1.5)
            if scarcity:
                base = max(base, target)
            else:
                base = max(base, min(target, DAILY_SALARY * 0.55))

    reserve_days = 3 if hp > 3 else 1
    max_affordable = max(0, budget - reserve_days * DAILY_SALARY * 0.25)
    bid = min(base, budget)
    if max_affordable > 0:
        bid = min(bid, max_affordable)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = []
    weak_prev = []
    desperate_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 85:
                    strong_prev.append(bid)
                else:
                    weak_prev.append(bid)

    if not alive:
        return max(0.0, min(budget, 18.0))

    contested = supply < (len(alive) + 1) * WATER_REQ

    highest_prev = max(prev_bids) if prev_bids else 0.0
    low_prev = min(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    if day >= 8:
        urgency += 1

    if contested:
        urgency += 1

    if urgency <= 1:
        bid = 8.0 if contested else 15.0
        if desperate_count >= 2:
            bid = 5.0
    elif urgency == 2:
        if strong_prev:
            bid = min(52.0, avg_prev * 0.55)
        else:
            bid = max(28.0, low_prev + 2.0)
    elif urgency == 3:
        if strong_prev:
            bid = max(58.0, min(78.0, highest_prev * 0.72))
        else:
            bid = max(45.0, highest_prev + 3.0)
    elif urgency == 4:
        if strong_prev:
            bid = max(72.0, min(96.0, highest_prev + 1.5))
        else:
            bid = max(62.0, highest_prev + 4.0)
    else:
        if strong_prev:
            bid = max(88.0, min(110.0, highest_prev + 3.0))
        else:
            bid = max(78.0, highest_prev + 6.0)

    if budget < bid:
        bid = budget

    if budget <= 35:
        bid = min(budget, max(bid, budget * 0.9 if urgency >= 4 else budget * 0.5))

    if hp >= 8 and no_water == 0 and strong_prev and highest_prev >= 100 and contested:
        bid = min(budget, min(bid, 12.0))

    if bid < 0:
        bid = 0.0

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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    units = int(supply / WATER_REQ)
    if units < 1:
        units = 1

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            desperate_opp += 1
        if opp.get('budget', 0) > 300:
            rich_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if not alive:
        return float(min(budget, 18.0))

    pressure = 0
    if units <= 1:
        pressure += 3
    elif units == 2:
        pressure += 2
    else:
        pressure += 1

    if no_water_days >= 2 or hp <= 2:
        pressure += 3
    elif no_water_days >= 1 or hp <= 4:
        pressure += 2
    elif hp <= 6:
        pressure += 1

    if highest_prev >= 100:
        pressure += 2
    elif highest_prev >= 80:
        pressure += 1

    if desperate_opp >= 2:
        pressure += 1
    if rich_opp >= 2:
        pressure += 1

    if day >= 8:
        pressure += 1

    if pressure <= 2:
        bid = max(8.0, avg_prev * 0.45)
    elif pressure == 3:
        bid = max(18.0, highest_prev * 0.55)
    elif pressure == 4:
        bid = max(32.0, highest_prev * 0.72 + 2.0)
    elif pressure == 5:
        bid = max(48.0, highest_prev * 0.84 + 3.0)
    else:
        bid = max(62.0, highest_prev * 0.92 + 4.0)

    if units <= 1 and (no_water_days >= 1 or hp <= 4):
        bid = max(bid, 78.0)

    if highest_prev > 110:
        bid = min(bid, 96.0)

    reserve = 0.0
    if hp >= 7 and no_water_days == 0 and day <= 5:
        reserve = 20.0
    elif hp >= 5 and day <= 7:
        reserve = 10.0

    affordable = max(0.0, budget - reserve)
    if affordable <= 0:
        affordable = budget * 0.5

    bid = min(bid, affordable)
    bid = min(bid, budget)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 85.0))

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
    prev_bids = []
    aggressive_count = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 80:
                    aggressive_count += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    units = supply / float(WATER_REQ)

    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        top_prev = 0.0
        avg_prev = 0.0

    if hp <= 2 or no_water >= 2:
        urgent = max(62.0, top_prev + 2.0)
        return float(min(budget, urgent))

    if hp <= 4 or no_water >= 1:
        if units >= 1.7:
            bid = max(26.0, min(44.0, avg_prev * 0.45 + 6.0))
        else:
            bid = max(38.0, min(58.0, top_prev * 0.6 + 8.0))
        return float(min(budget, bid))

    if units >= 1.8:
        bid = 16.0
    elif units >= 1.5:
        bid = 22.0
    elif units >= 1.25:
        bid = 29.0
    else:
        bid = 36.0

    if top_prev > 0:
        if top_prev >= 100:
            bid -= 4.0
        elif top_prev >= 70:
            bid += 2.0
        elif top_prev <= 25:
            bid += 3.0

    if aggressive_count >= 2 and hp >= 6 and no_water == 0:
        bid -= 3.0

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.55 + 6.0)

    bid = max(8.0, bid)
    return float(min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, 18.0))

    yesterday_bids = []
    rich_pressure = 0
    desperate_pressure = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            yesterday_bids.append(float(bid))
        if opp.get('budget', 0) >= 400:
            rich_pressure += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_pressure += 1

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    units = int(supply // WATER_REQ)
    scarce = units <= 1
    enough_for_two = units >= 2

    if hp <= 2 or no_water_days >= 2:
        bid = max(62.0, highest_prev + 3.0)
    elif hp <= 4 or no_water_days >= 1:
        if scarce:
            bid = max(48.0, highest_prev + 2.0)
        else:
            bid = max(34.0, avg_prev * 0.45)
    else:
        if enough_for_two:
            bid = 16.0 + 2.0 * rich_pressure + 1.5 * desperate_pressure
            if highest_prev > 120:
                bid = min(bid, 24.0)
            elif highest_prev > 80:
                bid = max(bid, 22.0)
        else:
            if highest_prev >= 130:
                bid = 28.0 if hp >= 7 else 52.0
            elif highest_prev >= 90:
                bid = 34.0 if hp >= 7 else 50.0
            else:
                bid = max(38.0, highest_prev + 1.5)

    if day >= 8:
        bid += 4.0
    if budget < 120:
        bid = min(bid, 0.42 * budget)
    elif budget < 220:
        bid = min(bid, 0.55 * budget)

    floor_bid = 8.0 if hp >= 6 else 15.0
    bid = max(floor_bid, bid)
    bid = min(budget, bid)

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev = []
    desperate_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 100:
                    dangerous_prev.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4:
        urgency = 2
    elif no_water >= 1:
        urgency = 1

    if urgency >= 3:
        target = max(118.0, highest_prev + 2.5)
    elif urgency == 2:
        if scarcity >= 1:
            target = max(108.0, highest_prev + 1.5)
        else:
            target = max(92.0, avg_prev + 2.0)
    else:
        if scarcity == 2:
            target = max(96.0, avg_prev + 1.0)
        elif scarcity == 1:
            target = 72.0 if highest_prev > 110 else max(58.0, avg_prev * 0.72)
        else:
            target = 28.0 if hp >= 6 else 42.0

    if desperate_count >= 2 and urgency >= 1:
        target += 8.0
    elif desperate_count >= 1 and scarcity >= 1 and hp <= 4:
        target += 5.0

    if day >= 8 and hp >= 6 and scarcity == 0:
        target = min(target, 24.0)

    if budget < target:
        if urgency >= 2:
            target = budget
        elif hp >= 6 and scarcity == 0:
            target = min(budget, 15.0)
        else:
            target = min(budget, max(35.0, budget * 0.7))

    if hp >= 7 and no_water == 0 and supply >= 21:
        target = min(target, 22.0)

    return float(max(0.0, min(budget, target)))
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 3:
                rich_opp += 1
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    danger = 0.0
    if no_water_days >= 2:
        danger += 0.7
    elif no_water_days == 1:
        danger += 0.35
    if hp <= 2:
        danger += 0.7
    elif hp <= 4:
        danger += 0.35

    if danger >= 1.0:
        bid = max(highest_prev + 2.0, DAILY_SALARY * 1.05)
        return float(min(budget, bid))

    if supply >= 23:
        base = DAILY_SALARY * 0.28
    elif supply >= 20:
        base = DAILY_SALARY * 0.42
    elif supply >= 17:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.88

    reactive = 0.0
    if highest_prev > 0:
        if highest_prev >= DAILY_SALARY * 1.8:
            reactive = DAILY_SALARY * 0.08
        elif highest_prev >= DAILY_SALARY * 1.2:
            reactive = DAILY_SALARY * 0.18
        elif highest_prev >= DAILY_SALARY * 0.8:
            reactive = DAILY_SALARY * 0.28
        else:
            reactive = max(0.0, highest_prev - base) * 0.35

    opp_factor = rich_opp * 2.5 + urgent_opp * 2.0
    bid = base + reactive + (supply_pressure * 10.0) + opp_factor + (danger * 18.0)

    if avg_prev > 0 and supply <= 17:
        bid = max(bid, avg_prev * 0.78)

    if hp >= 8 and no_water_days == 0 and supply >= 21:
        bid *= 0.82

    reserve_floor = DAILY_SALARY * 1.2 if hp > 4 else DAILY_SALARY * 0.4
    max_affordable = budget - reserve_floor
    if max_affordable < DAILY_SALARY * 0.2:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    named_prev = {}
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                named_prev[agent_id] = bid

    if not alive:
        return min(budget, 28.0)

    pressure = len(alive) + 1
    scarcity = supply / float(WATER_REQ * pressure)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    eric_bid = named_prev.get('Eric', None)
    cindy_bid = named_prev.get('Cindy', None)
    bob_bid = named_prev.get('Bob', None)

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    target = 0.0

    if critical:
        if eric_bid is not None and eric_bid >= 120 and budget > eric_bid:
            target = eric_bid + 2.0
        else:
            target = max(133.5, highest_prev + 2.0, DAILY_SALARY * 1.2)
    elif urgent:
        if scarcity <= 0.38:
            if eric_bid is not None and budget > eric_bid:
                target = eric_bid + 1.5
            else:
                target = max(95.0, highest_prev + 1.5)
        else:
            target = max(72.0, min(110.0, highest_prev * 0.8 if highest_prev > 0 else 72.0))
    else:
        if scarcity <= 0.30:
            if eric_bid is not None and budget > eric_bid:
                target = eric_bid + 1.5
            else:
                target = max(100.0, highest_prev + 1.5)
        elif scarcity <= 0.42:
            if eric_bid is not None and eric_bid == 133.0 and budget > 134.5:
                target = 134.5
            else:
                base = 58.0
                if bob_bid is not None:
                    base = max(base, min(90.0, bob_bid + 1.0))
                target = base
        else:
            target = 35.0
            if cindy_bid is not None and cindy_bid > 180:
                target = 25.0

    if day >= 8 and hp >= 5 and no_water == 0 and scarcity > 0.4:
        target = min(target, 45.0)

    if budget < target:
        if critical:
            return max(0.0, budget)
        return max(0.0, min(budget, target))

    return max(0.0, min(budget, target))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.8)
        return max(0.0, float(safe_bid))

    pressure_bids = []
    desperate_bids = []
    rich_aggressive = 0
    weak_opponents = 0
    total_req = WATER_REQ

    for opp in alive:
        total_req += opp.get('water_requirement', WATER_REQ)
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_bids.append(opp)
        if opp.get('hp', 10) <= 2:
            weak_opponents += 1
        if opp.get('budget', 0) >= 200:
            rich_aggressive += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            pressure_bids.append(float(prev.get('bid', 0.0)))

    max_prev = max(pressure_bids) if pressure_bids else 0.0
    avg_prev = sum(pressure_bids) / len(pressure_bids) if pressure_bids else 0.0

    scarcity = total_req / max(1.0, supply)
    very_tight = supply <= 16
    ample = supply >= 22

    emergency = hp <= 2 or no_water_days >= 2
    fragile = hp <= 4 or no_water_days >= 1

    if emergency:
        bid = max(DAILY_SALARY * 0.95, max_prev + 2.0)
        if desperate_bids:
            bid = max(bid, avg_prev + 3.0)
        return max(0.0, float(min(budget, bid)))

    if very_tight:
        if max_prev >= 120:
            bid = DAILY_SALARY * 0.42 if hp >= 6 else DAILY_SALARY * 0.88
        elif max_prev >= 80:
            bid = max(DAILY_SALARY * 0.62, max_prev + 1.5)
        else:
            bid = DAILY_SALARY * 0.58 + weak_opponents * 2.0
    elif ample:
        if max_prev >= 110 and hp >= 6:
            bid = DAILY_SALARY * 0.28
        else:
            bid = DAILY_SALARY * 0.4
    else:
        if max_prev >= 120:
            bid = DAILY_SALARY * 0.35 if hp >= 7 else DAILY_SALARY * 0.82
        elif max_prev >= 90:
            bid = DAILY_SALARY * 0.48 if hp >= 6 else DAILY_SALARY * 0.72
        elif max_prev > 0:
            bid = max(DAILY_SALARY * 0.5, min(max_prev + 1.2, DAILY_SALARY * 0.78))
        else:
            bid = DAILY_SALARY * 0.52

    if scarcity > 2.2:
        bid += 8.0
    elif scarcity < 1.7:
        bid -= 5.0

    if desperate_bids and hp >= 5:
        target = 0.0
        for opp in desperate_bids:
            prev = opp.get('previous_trace', {})
            obid = float(prev.get('bid', 0.0)) if prev and prev.get('bid') is not None else DAILY_SALARY * 0.55
            if obid > target:
                target = obid
        bid = max(bid, target + 1.1)

    if rich_aggressive >= 2 and max_prev >= 100 and hp >= 7 and not very_tight:
        bid = min(bid, DAILY_SALARY * 0.33)

    if fragile:
        bid = max(bid, DAILY_SALARY * 0.68)

    if day >= 8:
        bid += 4.0
    if day >= 9 and hp <= 5:
        bid += 8.0

    if budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.72)
    elif budget > 400 and hp <= 5:
        bid += 6.0

    bid = max(0.0, min(float(bid), float(budget)))
    return bid
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
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    weighted_pressures = []
    dangerous_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid')
        if b is not None:
            prev_bids.append(float(b))
            pressure = float(b)
            if opp.get('budget', 0) < pressure:
                pressure = float(opp.get('budget', 0))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                pressure += 8.0
                dangerous_count += 1
            weighted_pressures.append(pressure)
        else:
            fallback = min(float(opp.get('budget', 0)), float(opp.get('daily_salary', DAILY_SALARY)) * 0.6)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                fallback += 8.0
                dangerous_count += 1
            weighted_pressures.append(fallback)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_pressure = max(weighted_pressures) if weighted_pressures else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2 or no_water_days >= 2:
        urgency = 2
    elif hp <= 4 or no_water_days >= 1:
        urgency = 1

    if urgency == 2:
        target = max(DAILY_SALARY * 0.92, strongest_pressure + 2.5)
    elif scarcity == 2:
        target = max(DAILY_SALARY * 0.72, strongest_pressure + 1.5)
    elif scarcity == 1:
        target = max(DAILY_SALARY * 0.55, min(strongest_pressure + 1.0, DAILY_SALARY * 0.9))
    else:
        target = DAILY_SALARY * 0.34
        if dangerous_count >= 2:
            target = max(target, DAILY_SALARY * 0.42)
        if highest_prev < DAILY_SALARY * 0.5:
            target = max(target, highest_prev + 0.5)

    if highest_prev >= 120 and urgency == 0 and scarcity == 0:
        target = min(target, DAILY_SALARY * 0.38)

    if day >= 8 and hp <= 4:
        target = max(target, DAILY_SALARY * 0.8)

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
"""
