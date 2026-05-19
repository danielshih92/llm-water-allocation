# ============================================================
# Experiment: exp_010
# Agent: Alex
# Source: exp_010
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

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 18)

    prev_bids = []
    desperate_count = 0
    total_players = 1
    for opp in alive_opponents:
        total_players += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    scarcity_ratio = float(supply) / float(total_players * WATER_REQ)

    if hp <= 2 or no_water >= 2:
        base = 64
    elif hp <= 4 or no_water >= 1:
        base = 52
    else:
        if scarcity_ratio >= 1.2:
            base = 22
        elif scarcity_ratio >= 0.9:
            base = 31
        else:
            base = 43

    base += min(desperate_count * 2, 8)

    if prev_bids:
        highest_prev = max(prev_bids)
        if hp <= 4 or no_water >= 1:
            target = highest_prev + 2
            if target > base:
                base = target
        else:
            if highest_prev < 28 and scarcity_ratio >= 1.0:
                base = max(base, highest_prev + 1)
            elif highest_prev > 58 and hp >= 5 and no_water == 0:
                base = min(base, 26)

    if budget < base:
        if hp <= 2 or no_water >= 2:
            return max(0, budget)
        return max(0, min(budget, base))

    return max(0, min(budget, base))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_aggression = 0.0
    rich_aggressive = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                opp_aggression += float(bid)
                if float(bid) >= 85 and opp.get('budget', 0) >= 400:
                    rich_aggressive += 1

    alive_count = len(alive_opponents)
    if alive_count == 0:
        return min(budget, 18.0)

    avg_prev = opp_aggression / alive_count if alive_count > 0 else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.6
    elif hp <= 6:
        danger += 0.3

    if no_water >= 2:
        danger += 1.0
    elif no_water >= 1:
        danger += 0.45

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if tight_supply:
        danger += 0.45
    elif loose_supply:
        danger -= 0.2

    if day >= 8:
        danger += 0.15

    if danger < 0:
        danger = 0.0

    if budget <= 0:
        return 0.0

    if danger >= 1.6:
        target = max(92.0, max_prev + 2.5, avg_prev + 4.0)
    elif danger >= 1.0:
        target = max(74.0, avg_prev + 1.5)
        if tight_supply:
            target = max(target, max_prev + 1.0)
    elif danger >= 0.5:
        if loose_supply and rich_aggressive >= 1:
            target = 24.0
        else:
            target = max(38.0, min(68.0, avg_prev * 0.72))
    else:
        if loose_supply:
            target = 12.0
        elif max_prev >= 90:
            target = 20.0
        else:
            target = 28.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 70.0 * (8 - day) * 0.18
    max_affordable = max(0.0, budget - reserve_floor)
    if max_affordable <= 0:
        max_affordable = min(budget, 25.0)

    bid = min(target, budget, max_affordable)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, 96.0))
    elif hp <= 4 and tight_supply:
        bid = min(budget, max(bid, 82.0))

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_prev = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                b = float(bid)
                prev_bids.append(b)
                if b > strong_prev:
                    strong_prev = b

    if not alive:
        safe = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            safe = DAILY_SALARY * 0.6
        return float(max(0.0, min(budget, safe)))

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days >= 1:
        urgency += 0.35

    urgency += 0.35 * supply_pressure
    if day >= 8:
        urgency += 0.1

    cindy_alive = False
    cindy_prev = None
    bob_prev = None
    for oid, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if oid == 'Cindy':
            cindy_alive = True
            if bid is not None:
                cindy_prev = float(bid)
        if oid == 'Bob' and bid is not None:
            bob_prev = float(bid)

    if urgency < 0.35 and cindy_alive and cindy_prev is not None and cindy_prev >= 85:
        bid = DAILY_SALARY * (0.22 + 0.18 * (1.0 - supply_pressure))
        return float(max(0.0, min(budget, bid)))

    target = 0.0
    if bob_prev is not None:
        target = max(target, bob_prev + 2.0)
    if cindy_prev is not None:
        if urgency >= 0.7:
            target = max(target, cindy_prev + 1.5)
        else:
            target = max(target, min(cindy_prev - 10.0, DAILY_SALARY * 0.95))
    if strong_prev > 0:
        target = max(target, strong_prev * 0.92)

    base = DAILY_SALARY * (0.38 + 0.42 * urgency + 0.12 * supply_pressure)
    bid = max(base, target)

    if urgency >= 1.0:
        bid = max(bid, DAILY_SALARY * 0.96)
    elif urgency >= 0.7:
        bid = max(bid, DAILY_SALARY * 0.82)
    elif urgency < 0.25:
        bid = min(bid, DAILY_SALARY * 0.58)

    if budget < DAILY_SALARY * 0.8:
        bid = min(bid, budget * 0.92)

    if hp <= 1 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.98))

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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    opp_pressure = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                    opp_pressure = max(opp_pressure, bid)

    if not alive:
        return float(min(budget, 18.0))

    competitors = len(alive) + 1
    expected_units = supply / float(WATER_REQ)
    scarcity = competitors - expected_units

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0
    threat_bid = max(highest_prev, opp_pressure)

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2
    abundant = supply >= 22
    tight = supply <= 18

    if critical:
        base = max(0.92 * DAILY_SALARY, threat_bid + 2.0)
    elif urgent:
        base = max(0.78 * DAILY_SALARY, avg_prev + 3.0)
    else:
        if abundant:
            base = 0.28 * DAILY_SALARY
        elif tight:
            base = max(0.52 * DAILY_SALARY, avg_prev + 1.5)
        else:
            base = max(0.40 * DAILY_SALARY, avg_prev)

    if scarcity > 2.5:
        base += 10.0
    elif scarcity > 1.5:
        base += 6.0
    elif scarcity < 0.5:
        base -= 5.0

    if threat_bid >= 100 and not urgent:
        base = min(base, 0.42 * DAILY_SALARY)
    elif threat_bid >= 80 and urgent:
        base = max(base, 0.82 * DAILY_SALARY)

    remaining_days = max(1, 10 - day)
    reserve_target = remaining_days * 18.0
    if budget < reserve_target and not urgent:
        base *= 0.82

    if day >= 8 and hp >= 5 and no_water == 0:
        base *= 0.9

    bid = max(0.0, min(float(budget), base))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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
    rich_pressure = 0
    desperate_pressure = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('budget', 0) >= 500 and bid >= 90:
                    rich_pressure = max(rich_pressure, bid)
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    desperate_pressure = max(desperate_pressure, bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if supply >= 23:
        base = 16.0
    elif supply >= 20:
        base = 24.0
    elif supply >= 17:
        base = 36.0
    else:
        base = 52.0

    if max_prev > 0:
        if supply >= 22:
            target = min(base, max(14.0, min_prev + 1.0))
        elif supply >= 19:
            target = max(base, max_prev * 0.42)
        elif supply >= 17:
            target = max(base, max_prev * 0.58)
        else:
            target = max(base, max_prev * 0.72)
    else:
        target = base

    if rich_pressure > 0:
        if urgency == 0 and supply >= 19:
            target = min(target, rich_pressure * 0.38)
        elif urgency == 1:
            target = max(target, rich_pressure * 0.52)
        else:
            target = max(target, rich_pressure * 0.7)

    if desperate_pressure > 0 and urgency >= 2:
        target = max(target, desperate_pressure + 2.0)

    if urgency == 1:
        target = max(target, 48.0)
    elif urgency == 2:
        target = max(target, 72.0)
    elif urgency == 3:
        target = max(target, 96.0)

    if day >= 8 and hp >= 7 and no_water == 0:
        target *= 0.9

    reserve = 0.0
    if day <= 3:
        reserve = 120.0
    elif day <= 6:
        reserve = 70.0
    else:
        reserve = 20.0

    cap = budget
    if budget > reserve:
        cap = budget - reserve + DAILY_SALARY * 0.35
    cap = min(cap, budget)

    if urgency == 3:
        cap = budget

    bid = min(target, cap)
    bid = max(0.0, bid)

    if hp <= 1 or no_water >= 2:
        bid = min(budget, max(bid, 120.0))

    return float(round(min(budget, bid), 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 20.0))
        return float(min(budget, 1.0))

    total_players = 1 + len(alive_opponents)
    total_req = WATER_REQ
    for req in opp_requirements:
        total_req += req

    scarcity = 0
    if supply < total_req:
        scarcity = 2
    elif supply < total_req + WATER_REQ:
        scarcity = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    danger = 0
    if hp <= 2:
        danger += 2
    elif hp <= 4:
        danger += 1
    if no_water_days >= 1:
        danger += 1

    if scarcity == 2:
        if danger >= 2:
            bid = max(145.0, highest_prev + 2.0)
        elif danger == 1:
            bid = max(136.0, highest_prev + 1.5)
        else:
            bid = max(126.0, avg_prev + 2.0)
    elif scarcity == 1:
        if danger >= 2:
            bid = max(118.0, highest_prev + 1.5)
        elif danger == 1:
            bid = max(95.0, avg_prev + 1.0)
        else:
            bid = 62.0
    else:
        if danger >= 2:
            bid = 88.0
        elif danger == 1:
            bid = 36.0
        else:
            bid = 8.0

    if budget < bid:
        if danger >= 2:
            bid = budget
        elif scarcity >= 1:
            bid = min(budget, max(0.0, highest_prev + 1.0))
        else:
            bid = min(budget, 5.0)

    if budget <= DAILY_SALARY and danger == 0 and scarcity == 0:
        bid = min(bid, 3.0)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 1:
            safe_bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, safe_bid))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 23
    urgent_self = hp <= 2 or no_water_days >= 1
    semi_urgent = hp <= 4

    if urgent_self:
        target = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
        if tight_supply:
            target = max(target, highest_prev + 8.0, 118.0)
        return float(min(budget, target))

    if tight_supply:
        target = max(108.0, highest_prev + 2.5)
        if desperate_count >= 1:
            target = max(target, highest_prev + 5.0)
        if rich_count >= 2:
            target += 4.0
        if semi_urgent:
            target += 6.0
        return float(min(budget, target))

    if ample_supply:
        target = max(36.0, min(72.0, avg_prev * 0.55))
        if desperate_count >= 2:
            target = max(target, 62.0)
        if semi_urgent:
            target = max(target, 78.0)
        return float(min(budget, target))

    target = max(60.0, min(105.0, avg_prev * 0.82 + 6.0))
    if highest_prev >= 115.0:
        target = max(target, highest_prev + 1.5)
    if desperate_count >= 2:
        target += 5.0
    if semi_urgent:
        target += 8.0
    if day >= 8 and hp >= 6:
        target = min(target, 88.0)

    return float(min(budget, max(0.0, target)))
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    units = int(supply // WATER_REQ)
    if units < 1:
        units = 1

    prev_bids = []
    prev_urgent_bids = []
    opp_count = 0
    urgent_opp_count = 0

    for opp in alive_opponents:
        opp_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = float(prev['bid'])
            prev_bids.append(bid)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                prev_urgent_bids.append(bid)
                urgent_opp_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    highest_urgent = max(prev_urgent_bids) if prev_urgent_bids else highest_prev

    contested = opp_count + 1 > units
    very_tight = units <= 1
    tight = units <= 2
    danger = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if opp_count == 0:
        return float(min(budget, 18.0 if not danger else 42.0))

    if critical:
        target = max(0.92 * DAILY_SALARY, highest_urgent + 2.0)
        if very_tight:
            target = max(target, highest_prev + 4.0)
        return float(min(budget, target))

    if danger:
        if contested:
            target = max(0.78 * DAILY_SALARY, highest_prev + 1.5)
            if very_tight:
                target = max(target, 0.9 * DAILY_SALARY)
        else:
            target = max(0.58 * DAILY_SALARY, avg_prev + 1.0)
        return float(min(budget, target))

    if very_tight:
        if highest_prev >= 75:
            target = max(34.0, highest_prev - 8.0)
        else:
            target = max(52.0, highest_prev + 1.5)
        return float(min(budget, target))

    if tight:
        if highest_prev >= 80:
            target = 31.0
        else:
            target = max(43.0, avg_prev + 1.0)
        return float(min(budget, target))

    if contested:
        if highest_prev >= 80:
            target = 26.0
        else:
            target = max(32.0, avg_prev * 0.72)
        return float(min(budget, target))

    target = 22.0
    if day >= 8 and hp >= 5:
        target = 18.0
    return float(min(budget, target))
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
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, 18.0))

    winners_est = int(supply // WATER_REQ)
    if winners_est < 1:
        winners_est = 1

    prev_bids = []
    threat_bid = 0.0
    eric_bid = None
    needy_count = 0
    rich_count = 0

    for oid, opp in alive:
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            needy_count += 1
        if opp.get('budget', 0) >= 200:
            rich_count += 1
        prev = opp.get('previous_trace') or {}
        b = prev.get('bid')
        if b is not None:
            prev_bids.append(float(b))
            if float(b) > threat_bid:
                threat_bid = float(b)
            if oid == 'Eric':
                eric_bid = float(b)

    if eric_bid is not None and eric_bid > threat_bid:
        threat_bid = eric_bid

    pressure = 0
    if winners_est <= 1:
        pressure += 2
    if len(alive) >= 3:
        pressure += 1
    if needy_count >= winners_est:
        pressure += 1
    if rich_count >= 2:
        pressure += 1
    if threat_bid >= 110:
        pressure += 2
    elif threat_bid >= 80:
        pressure += 1

    urgent = False
    if hp <= 3 or no_water_days >= 1:
        urgent = True

    if urgent:
        if threat_bid >= 120:
            bid = 121.5
        elif threat_bid >= 90:
            bid = threat_bid + 3.0
        else:
            bid = 78.0 if winners_est >= 2 else 96.0
    else:
        if winners_est >= 2:
            if pressure <= 1:
                bid = 24.0
            elif pressure == 2:
                bid = 34.0
            elif pressure == 3:
                bid = 46.0
            else:
                bid = 58.0
        else:
            if pressure <= 2:
                bid = 52.0
            elif pressure == 3:
                bid = 68.0
            else:
                bid = 84.0

        if eric_bid is not None:
            if eric_bid >= 120 and hp >= 5:
                bid = min(bid, 36.0)
            elif eric_bid <= 60 and winners_est >= 2:
                bid = max(bid, eric_bid + 2.0)

    if day >= 8 and hp >= 6 and budget < 160:
        bid *= 0.85
    if day >= 8 and urgent:
        bid = max(bid, 88.0)

    reserve_floor = 0.0
    days_left = 10 - day
    if days_left > 0 and hp >= 5:
        reserve_floor = min(budget * 0.35, days_left * 12.0)
    max_today = budget - reserve_floor
    if urgent:
        max_today = budget

    if max_today < 0:
        max_today = 0.0

    bid = min(bid, max_today, budget)
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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    prev_valid = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                prev_valid.append((float(bid), opp))

    if not alive_opps:
        if hp <= 3 or no_water_days >= 2:
            return float(min(budget, 45.0))
        return float(min(budget, 12.0))

    prev_bids.sort()
    highest_prev = prev_bids[-1] if prev_bids else 0.0
    second_prev = prev_bids[-2] if len(prev_bids) >= 2 else highest_prev

    emergency = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1
    ample_supply = supply >= 21
    tight_supply = supply <= 17

    rich_aggressive = 0
    for bid_val, opp in prev_valid:
        if bid_val >= 100 and opp.get('budget', 0) >= 150:
            rich_aggressive += 1

    if emergency:
        target = max(78.0, min(118.0, second_prev + 3.0))
        if tight_supply:
            target += 8.0
        return float(min(budget, target))

    if pressured:
        if ample_supply:
            target = max(48.0, min(88.0, second_prev * 0.72 + 4.0))
        else:
            target = max(36.0, min(72.0, second_prev * 0.58 + 2.0))
        return float(min(budget, target))

    if rich_aggressive >= 2 and not ample_supply:
        return float(min(budget, 8.0))

    if highest_prev >= 120:
        if ample_supply:
            target = 34.0
        else:
            target = 10.0
    elif highest_prev >= 100:
        target = 18.0 if not ample_supply else 30.0
    else:
        target = max(20.0, min(55.0, highest_prev + 2.5))

    if day >= 8 and hp >= 7 and budget < 120:
        target *= 0.75

    return float(min(budget, max(0.0, target)))
"""
