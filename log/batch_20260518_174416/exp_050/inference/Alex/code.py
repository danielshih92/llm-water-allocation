# ============================================================
# Experiment: exp_050
# Agent: Alex
# Source: exp_050
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
    prev_bids = []
    desperate_opp = False
    rich_aggro = False

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_opp = True
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= DAILY_SALARY * 0.8 and opp.get('budget', 0) >= DAILY_SALARY:
                    rich_aggro = True

    if not alive:
        return max(0.0, min(float(budget), DAILY_SALARY * 0.35))

    players = len(alive) + 1
    enough_supply = supply >= WATER_REQ * players
    tight_supply = supply < WATER_REQ * max(1, players - 1)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = DAILY_SALARY * 0.5
        avg_prev = DAILY_SALARY * 0.5

    if hp <= 2 or no_water >= 2:
        target = max(DAILY_SALARY * 0.92, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        target = max(DAILY_SALARY * 0.72, avg_prev + 1.5)
    else:
        if enough_supply:
            target = DAILY_SALARY * 0.28
        elif tight_supply:
            target = max(DAILY_SALARY * 0.62, highest_prev + 1.0)
        else:
            target = max(DAILY_SALARY * 0.48, avg_prev + 0.5)

    if desperate_opp and not (hp <= 4 or no_water >= 1):
        target *= 0.92
    if rich_aggro and (hp <= 4 or no_water >= 1):
        target = max(target, highest_prev + 2.0)

    if budget < DAILY_SALARY * 0.6:
        target = min(target, budget * 0.9)

    target = max(0.0, min(float(budget), float(target)))
    return target
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

    day = day_context['day']
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive.append(opp)
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 110 and opp.get('budget', 0) >= 500:
                    rich_aggressive += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17.0
    supply_loose = supply >= 22.0
    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water >= 1:
        danger += 2

    base = 42.0
    if supply_tight:
        base += 18.0
    elif supply_loose:
        base -= 8.0

    if highest_prev >= 140:
        target = highest_prev + 2.0 if danger >= 2 else highest_prev * 0.72
    elif highest_prev >= 110:
        target = highest_prev + 1.5 if danger >= 2 or supply_tight else max(58.0, highest_prev * 0.68)
    elif highest_prev >= 80:
        target = max(base + 8.0, highest_prev + 1.0 if danger >= 2 else avg_prev + 4.0)
    elif highest_prev > 0:
        target = max(base, avg_prev + 6.0)
    else:
        target = base

    if urgent_count >= 2:
        target += 8.0
    elif urgent_count == 1:
        target += 4.0

    if rich_aggressive >= 2 and danger == 0 and supply_loose:
        target -= 10.0

    if day >= 8 and hp > 5 and budget < 220:
        target -= 8.0

    if danger >= 3:
        target = max(target, 95.0)
    elif danger >= 2:
        target = max(target, 78.0)

    if budget < 120:
        target = min(target, budget * 0.72)
    elif budget < 250:
        target = min(target, budget * 0.62)
    else:
        target = min(target, budget * 0.38 + 35.0)

    if supply_loose and danger == 0:
        target = min(target, 65.0)

    target = max(12.0, min(float(budget), float(target)))
    return float(round(target, 2))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.7
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    highest_prev = 0.0
    cindy_bid = None
    david_bid = None
    desperate_count = 0

    for oid, opp in alive:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            prev_bids.append(bid)
            if bid > highest_prev:
                highest_prev = bid
            if oid == 'Cindy':
                cindy_bid = bid
            if oid == 'David':
                david_bid = bid

    tight_supply = supply <= 17.0
    roomy_supply = supply >= 22.0

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency >= 3:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
    elif urgency == 2:
        if tight_supply:
            bid = max(0.82 * DAILY_SALARY, highest_prev + 2.0)
        else:
            bid = max(0.68 * DAILY_SALARY, highest_prev * 0.72)
    else:
        if roomy_supply and desperate_count == 0:
            bid = 0.34 * DAILY_SALARY
        elif tight_supply:
            bid = max(0.60 * DAILY_SALARY, highest_prev * 0.58)
        else:
            bid = max(0.46 * DAILY_SALARY, highest_prev * 0.50)

    if cindy_bid is not None and cindy_bid >= 130:
        if urgency == 0 and not tight_supply:
            bid = min(bid, 0.42 * DAILY_SALARY)
        elif urgency >= 2:
            bid = max(bid, min(0.88 * DAILY_SALARY, highest_prev + 1.5))

    if david_bid is not None and 95 <= david_bid <= 120 and (tight_supply or urgency >= 1):
        bid = max(bid, min(0.86 * DAILY_SALARY, david_bid + 1.25))

    if day >= 8:
        if hp <= 5:
            bid = max(bid, 0.78 * DAILY_SALARY)
        else:
            bid = max(bid, 0.52 * DAILY_SALARY)

    if budget < DAILY_SALARY:
        bid = min(bid, max(0.0, budget * 0.92))
    else:
        reserve_floor = max(0.0, budget - DAILY_SALARY * max(0, 10 - day) * 0.45)
        bid = min(bid, max(0.0, reserve_floor + DAILY_SALARY * 0.35))

    bid = max(0.0, min(budget, bid))
    return float(bid)
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

    alive_opps = []
    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace') or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 75 and opp.get('budget', 0) >= 400:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    urgency = 0
    if hp <= 3:
        urgency += 3
    elif hp <= 5:
        urgency += 2
    elif hp <= 7:
        urgency += 1

    if no_water >= 2:
        urgency += 3
    elif no_water >= 1:
        urgency += 2

    if tight_supply:
        urgency += 2
    elif supply <= 19:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        bid = max(92.0, highest_prev + 4.0, avg_prev + 8.0)
    elif urgency >= 4:
        bid = max(78.0, highest_prev + 2.0, avg_prev + 4.0)
    elif urgency >= 2:
        if ample_supply and highest_prev >= 80:
            bid = 24.0
        else:
            bid = max(48.0, avg_prev * 0.82, highest_prev * 0.72)
    else:
        if ample_supply:
            bid = 16.0 if rich_aggressive >= 1 else 20.0
        elif tight_supply:
            bid = max(58.0, highest_prev * 0.78)
        else:
            bid = max(30.0, avg_prev * 0.55)

    if desperate_count >= 2 and urgency >= 3:
        bid += 6.0
    elif desperate_count == 0 and ample_supply and urgency <= 1:
        bid -= 4.0

    reserve = 0.0
    if hp > 6 and no_water == 0:
        reserve = 35.0
    elif hp > 4:
        reserve = 20.0

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_bids = []
    needy_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                needy_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 120:
                    strong_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    slots = max(1, int(supply // WATER_REQ))
    opp_count = len(alive_opponents)
    contest_ratio = opp_count / float(slots)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 2 or no_water_days >= 2
    semi_urgent = hp <= 4 or no_water_days >= 1
    scarce = slots <= 1
    ample = slots >= 2 and supply >= 24

    if urgent:
        bid = min(budget, max(118.0, highest_prev + 4.0, DAILY_SALARY * 1.45))
        return float(max(0.0, bid))

    if scarce:
        if strong_bids:
            if semi_urgent:
                bid = min(budget, max(122.0, highest_prev + 2.0))
            else:
                bid = min(budget, 24.0)
        else:
            if contest_ratio >= 3:
                bid = min(budget, max(78.0, avg_prev + 3.0, 0.75 * DAILY_SALARY))
            else:
                bid = min(budget, max(52.0, avg_prev + 2.0))
        return float(max(0.0, bid))

    if ample:
        if highest_prev >= 120:
            bid = 16.0 if hp > 4 else 34.0
        else:
            bid = max(18.0, min(36.0, avg_prev * 0.55 if avg_prev > 0 else 22.0))
        return float(min(budget, max(0.0, bid)))

    if highest_prev >= 140:
        if semi_urgent:
            bid = min(budget, 96.0)
        else:
            bid = min(budget, 20.0)
    elif highest_prev >= 100:
        bid = min(budget, 44.0 if hp > 4 else 72.0)
    else:
        pressure = 0.0
        pressure += 8.0 if semi_urgent else 0.0
        pressure += 10.0 if needy_count >= 2 else 0.0
        pressure += 8.0 if contest_ratio >= 2.5 else 0.0
        base = max(28.0, avg_prev + 2.5 if avg_prev > 0 else 32.0)
        bid = min(budget, base + pressure)

    if day >= 8 and hp > 5 and highest_prev >= 120:
        bid = min(budget, bid * 0.85)

    return float(max(0.0, bid))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    dangerous_bids = []
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 1:
                    dangerous_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    dangerous_prev = max(dangerous_bids) if dangerous_bids else highest_prev

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

    if rich_count >= 2:
        urgency += 1

    if urgency >= 6:
        target = max(DAILY_SALARY * 1.1, dangerous_prev + 3.0)
    elif urgency >= 4:
        target = max(DAILY_SALARY * 0.9, dangerous_prev + 2.0)
    elif urgency >= 2:
        target = max(DAILY_SALARY * 0.62, dangerous_prev + 1.0)
    else:
        if dangerous_prev >= DAILY_SALARY * 1.5:
            target = DAILY_SALARY * 0.28
        elif dangerous_prev >= DAILY_SALARY * 0.95:
            target = DAILY_SALARY * 0.4
        else:
            target = max(DAILY_SALARY * 0.34, dangerous_prev * 0.78)

    if day >= 8:
        target *= 1.08
    if day >= 9 and (hp <= 4 or no_water >= 1):
        target *= 1.15

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left >= 3 and hp > 3:
        reserve_floor = DAILY_SALARY * 0.35

    cap = max(0.0, budget - reserve_floor)
    if urgency >= 4:
        cap = budget

    bid = min(target, cap if cap > 0 else budget)

    if hp <= 1 or no_water >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 1.2, dangerous_prev + 4.0))

    if budget < DAILY_SALARY * 0.5:
        bid = min(budget, max(1.0, budget * 0.9))

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
    durable_pressure = 0.0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) >= 3 and opp.get('budget', 0) >= DAILY_SALARY * 4:
                    if bid > durable_pressure:
                        durable_pressure = float(bid)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    slots = supply / float(WATER_REQ)
    scarce = slots < (len(alive) + 1)
    very_scarce = slots < max(1.5, (len(alive) + 1) * 0.7)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    pressure = max(highest_prev, durable_pressure)

    critical = hp <= 2 or no_water_days >= 2
    strained = hp <= 4 or no_water_days >= 1

    if critical:
        if pressure > 0:
            bid = min(budget, max(DAILY_SALARY * 0.95, pressure + 2.5))
        else:
            bid = min(budget, DAILY_SALARY * 0.9)
        return max(0.0, bid)

    if very_scarce:
        if pressure >= 90:
            bid = DAILY_SALARY * 0.82 if hp >= 5 else DAILY_SALARY * 0.96
        elif pressure > 0:
            bid = min(DAILY_SALARY * 0.9, max(DAILY_SALARY * 0.62, pressure + 1.5))
        else:
            bid = DAILY_SALARY * 0.68
    elif scarce:
        if pressure >= 90:
            bid = DAILY_SALARY * 0.45 if hp >= 6 else DAILY_SALARY * 0.78
        elif pressure > 0:
            bid = max(DAILY_SALARY * 0.45, min(DAILY_SALARY * 0.72, pressure * 0.72))
        else:
            bid = DAILY_SALARY * 0.5
    else:
        if strained:
            bid = DAILY_SALARY * 0.52
        else:
            bid = DAILY_SALARY * 0.34

    if day >= 8 and hp >= 5 and budget > DAILY_SALARY * 6:
        bid *= 0.9

    if budget < DAILY_SALARY * 2 and not critical:
        bid = min(bid, DAILY_SALARY * 0.55)

    return max(0.0, min(budget, bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if float(opp.get('budget', 0)) > 500:
                rich_opp += 1
            if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 10)) <= 4:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return min(budget, 18.0)

    slots = max(1, int(supply // WATER_REQ))
    low_supply = slots <= 1

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    survival_mode = hp <= 3 or no_water >= 2
    caution_mode = hp <= 5 or no_water >= 1

    if survival_mode:
        base = max(82.0, highest_prev + 6.0)
        if low_supply:
            base += 10.0
        if rich_opp >= 2:
            base += 8.0
        return min(budget, base)

    if caution_mode:
        base = max(58.0, avg_prev + 3.0)
        if low_supply:
            base += 10.0
        if urgent_opp >= 2:
            base += 6.0
        return min(budget, base)

    if low_supply:
        if highest_prev >= 120.0:
            base = 24.0
        else:
            base = max(46.0, highest_prev + 2.0)
        if rich_opp >= 2:
            base += 4.0
    else:
        if highest_prev >= 120.0:
            base = 16.0
        elif highest_prev >= 80.0:
            base = 28.0
        else:
            base = max(22.0, avg_prev * 0.6 + 6.0)

    if day >= 8 and hp >= 7 and budget < 200:
        base *= 0.9

    reserve_floor = 12.0 if hp >= 6 else 0.0
    bid = min(budget - reserve_floor if budget > reserve_floor else budget, base)
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
        return float(min(budget, 20.0))

    slots = int(max(1, supply // WATER_REQ))
    opp_infos = []
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is None:
            prev_bid = 0.0
        opp_infos.append({
            'id': oid,
            'bid': float(prev_bid),
            'hp': opp.get('hp', 10),
            'budget': opp.get('budget', 0.0),
            'need': opp.get('no_water_days', 0),
            'req': opp.get('water_requirement', WATER_REQ)
        })

    high_cindy = False
    david_bid = 0.0
    max_prev = 0.0
    urgent_opp = 0
    for info in opp_infos:
        if info['id'] == 'Cindy' and info['bid'] >= 130:
            high_cindy = True
        if info['id'] == 'David':
            david_bid = info['bid']
        if info['bid'] > max_prev:
            max_prev = info['bid']
        if info['hp'] <= 3 or info['need'] >= 2:
            urgent_opp += 1

    my_urgent = hp <= 3 or no_water >= 2
    very_urgent = hp <= 2 or no_water >= 3
    tight = slots <= 1

    target = 0.0

    if very_urgent:
        if high_cindy:
            target = 146.0
        else:
            target = max(92.0, max_prev + 3.0)
    elif my_urgent:
        if tight:
            if high_cindy:
                target = 118.0
            else:
                target = max(80.0, david_bid + 2.5, max_prev + 1.5)
        else:
            target = max(62.0, david_bid + 2.0)
    else:
        if tight:
            if high_cindy:
                target = max(36.0, min(58.0, david_bid + 1.5))
            else:
                target = max(48.0, david_bid + 2.0)
        else:
            if urgent_opp >= 2:
                target = 34.0
            else:
                target = 26.0

    if day >= 8 and hp >= 5 and not my_urgent:
        target *= 0.9
    if day >= 9 and my_urgent:
        target *= 1.15

    safe_cap = budget
    if not my_urgent:
        reserve_days = max(0, 10 - int(day))
        reserve = reserve_days * 10.0
        safe_cap = max(0.0, budget - reserve)
        if safe_cap <= 0:
            safe_cap = min(budget, 25.0)

    bid = min(target, budget, safe_cap if safe_cap > 0 else budget)
    if my_urgent:
        bid = min(target, budget)

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    aggressive_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80:
                    aggressive_prev.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    competitors = len(alive) + 1
    units = max(1, int(supply // WATER_REQ))
    scarcity = units < competitors

    highest_prev = max(prev_bids) if prev_bids else 0.0
    low_prev = min(prev_bids) if prev_bids else 0.0
    david_prev = None
    cindy_prev = None
    for oid, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is None:
            continue
        if oid == 'David' and opp.get('alive'):
            david_prev = float(bid)
        if oid == 'Cindy' and opp.get('alive'):
            cindy_prev = float(bid)

    critical = hp <= 3 or no_water >= 2
    pressured = hp <= 5 or no_water >= 1

    if critical:
        target = 98.0
        if david_prev is not None:
            target = max(target, david_prev + 3.0)
        if scarcity and cindy_prev is not None and cindy_prev < budget:
            target = max(target, min(cindy_prev + 1.0, budget))
        return float(min(budget, target))

    if scarcity:
        if cindy_prev is not None and cindy_prev >= 140:
            if pressured:
                target = 96.0
                if david_prev is not None:
                    target = max(target, david_prev + 2.0)
                return float(min(budget, target))
            return float(min(budget, 24.0))
        if david_prev is not None:
            if pressured:
                return float(min(budget, david_prev + 2.5))
            return float(min(budget, max(28.0, david_prev - 18.0)))
        return float(min(budget, 35.0 if pressured else 22.0))

    if pressured:
        if david_prev is not None and david_prev < 90:
            return float(min(budget, david_prev + 2.0))
        return float(min(budget, 52.0))

    if highest_prev >= 140:
        return float(min(budget, 16.0))
    if aggressive_prev:
        return float(min(budget, 20.0))
    if low_prev > 0:
        return float(min(budget, max(18.0, low_prev + 1.0)))
    return float(min(budget, 19.0))
"""
