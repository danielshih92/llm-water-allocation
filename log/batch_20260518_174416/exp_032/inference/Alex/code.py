# ============================================================
# Experiment: exp_032
# Agent: Alex
# Source: exp_032
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
    prev_bids = []
    desperate_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])

    players = 1 + len(alive_opponents)
    affordable_cap = max(0.0, min(float(budget), float(DAILY_SALARY)))
    if affordable_cap <= 0:
        return 0.0

    units = float(supply) / float(WATER_REQ)
    scarcity = units < players
    severe_scarcity = units < max(1, players - 1)

    max_prev = max(prev_bids) if prev_bids else 0.0
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
        urgency += 2

    if not alive_opponents:
        if urgency >= 3:
            return min(affordable_cap, 28.0)
        return min(affordable_cap, 12.0)

    if urgency >= 5:
        bid = max(62.0, max_prev + 3.0)
    elif urgency >= 3:
        bid = max(48.0, max_prev + 2.0 if scarcity else avg_prev + 1.0)
    else:
        if severe_scarcity:
            bid = max(42.0, max_prev + 1.5)
        elif scarcity:
            bid = max(30.0, avg_prev + 1.0, 18.0 + 4.0 * desperate_count)
        else:
            bid = max(12.0, min(24.0, avg_prev * 0.75 if avg_prev > 0 else 16.0))

    if max_prev >= 60.0 and urgency <= 1:
        bid = min(bid, 24.0)
    if max_prev >= 65.0 and urgency == 0:
        bid = 15.0

    if budget < 20:
        bid = min(bid, budget)
    elif budget < 40:
        bid = min(bid, 0.8 * budget)

    bid = max(0.0, min(float(bid), affordable_cap))
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
    opp_reqs = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_reqs.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.55))
        return float(min(budget, DAILY_SALARY * 0.2))

    total_players = 1 + len(alive)
    total_req = WATER_REQ
    for r in opp_reqs:
        total_req += r

    scarcity_ratio = float(supply) / float(total_req) if total_req > 0 else 1.0
    expected_units = float(supply) / float(WATER_REQ) if WATER_REQ > 0 else 1.0
    pressure = total_players / expected_units if expected_units > 0 else total_players

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 2 or no_water_days >= 1
    fragile = hp <= 4
    very_tight = scarcity_ratio < 0.32 or pressure > 2.6
    tight = scarcity_ratio < 0.42 or pressure > 2.0
    ample = scarcity_ratio > 0.55 and pressure < 1.5

    if urgent:
        if highest_prev > 0:
            bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
        else:
            bid = DAILY_SALARY * 0.95
    elif very_tight:
        if fragile:
            bid = max(DAILY_SALARY * 0.88, highest_prev + 2.0 if highest_prev > 0 else DAILY_SALARY * 0.88)
        else:
            if highest_prev >= 120:
                bid = DAILY_SALARY * 0.28
            else:
                bid = max(DAILY_SALARY * 0.62, avg_prev + 1.5 if avg_prev > 0 else DAILY_SALARY * 0.62)
    elif tight:
        if highest_prev >= 130 and hp >= 5:
            bid = DAILY_SALARY * 0.3
        elif highest_prev > 0:
            bid = max(DAILY_SALARY * 0.52, min(highest_prev + 1.0, DAILY_SALARY * 1.55))
        else:
            bid = DAILY_SALARY * 0.55
    elif ample:
        if hp >= 5 and no_water_days == 0:
            bid = DAILY_SALARY * 0.18
        else:
            bid = DAILY_SALARY * 0.4
    else:
        if highest_prev > 0:
            bid = max(DAILY_SALARY * 0.42, min(avg_prev * 0.92, highest_prev + 0.5))
        else:
            bid = DAILY_SALARY * 0.48

    if day >= 8:
        if hp >= 5 and not urgent:
            bid *= 0.9
        else:
            bid *= 1.05

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = max(0.0, budget - DAILY_SALARY * (10 - int(day)))
        if bid > reserve_floor + DAILY_SALARY * 0.9:
            bid = reserve_floor + DAILY_SALARY * 0.9

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.75
        return max(0.0, min(budget, safe_bid))

    est_demand_units = 1
    for oid, opp in alive:
        req = opp.get('water_requirement', WATER_REQ)
        if req <= supply:
            est_demand_units += 1
    tightness = est_demand_units / max(1.0, supply / float(WATER_REQ))

    bob_prev = None
    cindy_prev = None
    highest_prev = 0.0
    urgent_opp = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = 0.0
        if prev and prev.get('bid') is not None:
            bid = float(prev.get('bid', 0.0))
            if bid > highest_prev:
                highest_prev = bid
        if oid == 'Bob':
            bob_prev = bid
        if oid == 'Cindy':
            cindy_prev = bid
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1

    if bob_prev is None:
        bob_prev = 75.5
    if cindy_prev is None:
        cindy_prev = 142.5

    pressure_bid = bob_prev + 1.6
    if urgent_opp >= 1:
        pressure_bid += 2.0
    if tightness > 1.8:
        pressure_bid += 3.0

    if hp <= 2 or no_water_days >= 1:
        bid = max(pressure_bid, DAILY_SALARY * 0.92)
    elif hp <= 4:
        bid = max(pressure_bid, DAILY_SALARY * 0.78)
    else:
        if supply >= 22 and tightness < 1.3:
            bid = DAILY_SALARY * 0.34
        elif supply >= 19 and highest_prev >= 100:
            bid = max(DAILY_SALARY * 0.48, bob_prev + 0.8)
        elif supply <= 17:
            bid = max(pressure_bid, DAILY_SALARY * 0.82)
        else:
            bid = max(DAILY_SALARY * 0.56, bob_prev + 0.9)

    if cindy_prev > 120 and hp > 4 and no_water_days == 0 and supply >= 19:
        bid = min(bid, bob_prev + 0.9)

    reserve = 0.0
    if hp > 4:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.6
    max_spend = max(0.0, budget - reserve)

    if hp <= 2 or no_water_days >= 1:
        max_spend = budget

    bid = min(bid, max_spend if max_spend > 0 else budget)
    bid = max(0.0, min(budget, bid))
    return bid
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
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 55.0))
        return float(min(budget, 1.0))

    opp_count = len(alive)
    total_players = opp_count + 1
    capacity = int(supply // WATER_REQ)

    prev_bids = []
    cindy_alive = False
    for oid, opp in alive:
        if oid == 'Cindy':
            cindy_alive = True
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1
    scarce = capacity < total_players
    very_scarce = capacity <= max(0, total_players - 2)

    if urgent:
        if cindy_alive:
            return float(min(budget, 76.0))
        return float(min(budget, max(58.0, highest_prev + 3.0)))

    if scarce:
        if cindy_alive:
            if very_scarce:
                return float(min(budget, 74.0))
            return float(min(budget, 6.0 if hp > 4 else 18.0))
        base = max(12.0, highest_prev + 2.0)
        if pressured:
            base = max(base, 32.0)
        return float(min(budget, base))

    if cindy_alive:
        if pressured:
            return float(min(budget, 8.0))
        return float(min(budget, 1.0))

    if highest_prev >= 60.0:
        return float(min(budget, 3.0 if hp > 4 else 20.0))
    if highest_prev >= 25.0:
        return float(min(budget, 10.0 if hp > 4 else 24.0))
    return float(min(budget, 5.0 if day < 8 else 9.0))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        if opp.get('budget', 0) >= budget:
            rich_opponents += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    base = 38.0
    if supply <= 16:
        base = 66.0
    elif supply <= 18:
        base = 58.0
    elif supply >= 23:
        base = 28.0
    elif supply >= 21:
        base = 34.0

    if highest_prev >= 88:
        base += 8.0
    elif highest_prev >= 78:
        base += 5.0
    elif avg_prev <= 55 and avg_prev > 0:
        base -= 4.0

    base += urgent_opponents * 2.0
    if rich_opponents >= 2:
        base += 3.0

    if hp <= 2:
        base = max(base, 82.0)
    elif hp <= 4:
        base = max(base, 68.0)
    elif no_water_days >= 2:
        base = max(base, 86.0)
    elif no_water_days >= 1:
        base = max(base, 72.0)

    if day >= 8 and hp > 4 and no_water_days == 0 and supply >= 20:
        base -= 6.0

    affordable_cap = budget
    if day < 10:
        reserve = max(0.0, (10 - day) * 8.0)
        affordable_cap = max(0.0, budget - reserve)
        if affordable_cap < 20.0:
            affordable_cap = min(budget, max(20.0, budget * 0.6))

    bid = min(base, budget, affordable_cap)
    if hp <= 2 or no_water_days >= 2:
        bid = min(max(bid, 88.0), budget)

    if not alive_opponents:
        bid = min(budget, 25.0)

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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append((oid, opp))

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    eric_prev = None
    highest_prev = 0.0
    urgent_opp_count = 0

    for oid, opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid_val = float(bid)
            prev_bids.append(bid_val)
            if bid_val > highest_prev:
                highest_prev = bid_val
            if oid == 'Eric':
                eric_prev = bid_val

    if eric_prev is None:
        eric_prev = highest_prev

    scarcity = (float(supply) <= 18.0)
    abundance = (float(supply) >= 22.0)
    my_urgent = (hp <= 2 or no_water_days >= 1)
    very_urgent = (hp <= 1 or no_water_days >= 2)

    target = DAILY_SALARY * 0.45

    if very_urgent:
        target = max(target, DAILY_SALARY * 0.96)
    elif my_urgent:
        if scarcity:
            target = max(target, DAILY_SALARY * 0.9)
        else:
            target = max(target, DAILY_SALARY * 0.78)
    else:
        if scarcity:
            if eric_prev > 0:
                target = max(target, min(DAILY_SALARY * 0.95, eric_prev + 2.0))
            else:
                target = max(target, DAILY_SALARY * 0.72)
        elif abundance:
            if urgent_opp_count == 0 and hp >= 4:
                target = max(target, DAILY_SALARY * 0.28)
            else:
                target = max(target, DAILY_SALARY * 0.4)
        else:
            if eric_prev >= DAILY_SALARY * 0.85:
                target = max(target, DAILY_SALARY * 0.52 if hp >= 4 else DAILY_SALARY * 0.82)
            elif eric_prev > 0:
                target = max(target, min(DAILY_SALARY * 0.82, eric_prev + 1.5))
            else:
                target = max(target, DAILY_SALARY * 0.55)

    days_left = max(0, 10 - int(day) + 1)
    reserve_floor = 0.0
    if days_left > 1 and hp >= 3 and no_water_days == 0:
        reserve_floor = DAILY_SALARY * 0.25 * (days_left - 1)

    affordable = budget
    if budget > reserve_floor:
        affordable = budget - reserve_floor
    if my_urgent:
        affordable = budget

    bid = min(target, affordable)
    if scarcity and not my_urgent and eric_prev > 0:
        bid = min(max(bid, eric_prev + 1.0), budget)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
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

    alive_opps = []
    prev_bids = []
    urgent_prev_bids = []
    rich_threat_bids = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_prev_bids.append(float(bid))
                if opp.get('budget', 0) >= budget * 0.8:
                    rich_threat_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_high = max(urgent_prev_bids) if urgent_prev_bids else highest_prev
    rich_high = max(rich_threat_bids) if rich_threat_bids else highest_prev

    scarcity = (supply <= 16)
    comfortable = (supply >= 22)
    critical_self = (hp <= 3 or no_water >= 1)
    very_safe = (hp >= 8 and no_water == 0)

    target = 0.0

    if critical_self:
        if scarcity:
            target = max(68.0, highest_prev + 2.0, urgent_high + 1.0)
        else:
            target = max(58.0, highest_prev + 1.5)
    elif scarcity:
        if very_safe and highest_prev >= 75.0:
            target = 18.0
        else:
            target = max(52.0, rich_high + 1.5)
    elif comfortable:
        if highest_prev >= 85.0 and very_safe:
            target = 16.0
        else:
            target = max(28.0, min(48.0, highest_prev * 0.72))
    else:
        if highest_prev >= 80.0 and very_safe:
            target = 20.0
        else:
            target = max(36.0, min(60.0, highest_prev + 1.0))

    if day >= 8:
        if hp <= 5:
            target = max(target, 62.0)
        elif budget < DAILY_SALARY * 2:
            target = min(target, 45.0)

    if budget < target:
        if critical_self:
            return float(max(0.0, budget))
        return float(max(0.0, min(budget, target)))

    return float(max(0.0, min(budget, target)))
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
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0.0, min(budget, 8.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    slots = int(supply // WATER_REQ)
    contested = len(alive) + 1 > slots

    if hp <= 2 or no_water_days >= 2:
        emergency = max(95.0, highest_prev + 6.0)
        if budget < emergency:
            return max(0.0, budget)
        return min(budget, emergency)

    if hp <= 4 or no_water_days >= 1:
        strong = max(72.0, min(118.0, highest_prev + 3.0))
        return max(0.0, min(budget, strong))

    if highest_prev >= 140:
        bid = 18.0
    elif highest_prev >= 105:
        bid = 26.0
    elif highest_prev >= 80:
        bid = min(88.0, highest_prev + 2.0)
    elif highest_prev > 0:
        bid = max(32.0, avg_prev + 2.0)
    else:
        bid = 24.0

    if contested:
        bid += 4.0
    if urgent_opp >= 2:
        bid += 6.0
    elif urgent_opp == 1:
        bid += 3.0
    if rich_opp >= 2:
        bid -= 3.0

    if day >= 8 and hp >= 6:
        bid -= 4.0

    reserve = DAILY_SALARY * max(0, 10 - int(day))
    soft_cap = budget if budget <= reserve else max(0.0, budget - reserve * 0.15)
    bid = min(bid, soft_cap)

    if bid < 0:
        bid = 0.0
    return max(0.0, min(budget, float(bid)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(float(opp.get('water_requirement', WATER_REQ)))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.8))
        return float(min(budget, DAILY_SALARY * 0.2))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    my_units = supply / WATER_REQ
    total_alive = 1 + len(alive_opponents)
    scarcity = my_units < 1.15
    moderate = my_units < 1.45

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1
    late_game = day >= 8

    if urgent:
        target = max(DAILY_SALARY * 1.15, highest_prev + 3.0, avg_prev + 6.0)
    elif scarcity:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif pressured and moderate:
        target = max(DAILY_SALARY * 0.82, avg_prev + 1.5)
    elif pressured:
        target = max(DAILY_SALARY * 0.68, highest_prev * 0.72)
    else:
        if highest_prev >= DAILY_SALARY * 1.5:
            target = DAILY_SALARY * 0.22
        elif highest_prev >= DAILY_SALARY * 1.1:
            target = DAILY_SALARY * 0.32
        else:
            target = max(DAILY_SALARY * 0.4, avg_prev * 0.55)

    if late_game and hp > 4 and no_water_days == 0 and not scarcity:
        target *= 0.9

    reserve = 0.0
    if hp > 2:
        reserve = DAILY_SALARY * 0.25
    if urgent:
        reserve = 0.0

    cap = max(0.0, budget - reserve)
    bid = min(target, cap)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = 0.0
    needy_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                needy_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if bid > strong_prev:
                    strong_prev = bid

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    high_pressure = strong_prev >= 120.0
    medium_pressure = strong_prev >= 90.0

    if hp <= 2 or no_water_days >= 2:
        target = max(110.0, strong_prev + 3.0)
        return float(min(budget, target))

    if slots >= 2:
        if hp >= 7 and no_water_days == 0:
            base = 22.0
            if medium_pressure:
                base = 34.0
            if day >= 8:
                base += 8.0
            return float(min(budget, base))
        else:
            base = 48.0
            if high_pressure:
                base = max(base, strong_prev * 0.55)
            return float(min(budget, base))

    base = 62.0
    if no_water_days >= 1:
        base = 88.0
    if hp <= 4:
        base = max(base, 96.0)
    if needy_opponents >= 2:
        base += 10.0
    if medium_pressure:
        base = max(base, min(strong_prev + 2.0, 118.0))
    if high_pressure and hp >= 6 and no_water_days == 0:
        base = min(base, 72.0)
    if day >= 9 and hp <= 5:
        base = max(base, 105.0)

    return float(min(budget, base))
"""
