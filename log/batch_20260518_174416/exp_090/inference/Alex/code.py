# ============================================================
# Experiment: exp_090
# Agent: Alex
# Source: exp_090
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    players_alive = 1 + len(alive_opponents)

    prev_bids = []
    stressed_opponents = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            stressed_opponents += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if prev.get('error'):
            stressed_opponents += 0

    if supply >= players_alive * WATER_REQ:
        base = DAILY_SALARY * 0.18
    elif supply >= max(1, players_alive - 1) * WATER_REQ:
        base = DAILY_SALARY * 0.42
    else:
        base = DAILY_SALARY * 0.68

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if highest_prev >= DAILY_SALARY * 0.9:
            base = max(base, DAILY_SALARY * 0.52)
        else:
            base = max(base, min(DAILY_SALARY * 0.78, avg_prev + 2.0))

    if hp <= 2 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.78)

    if stressed_opponents >= max(1, len(alive_opponents) // 2):
        base += 3.0

    if day >= 8:
        base += 4.0

    reserve_days = max(1, 10 - day)
    soft_cap = budget / reserve_days
    bid = min(base, max(0.0, soft_cap * 1.35))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    bid = min(budget, max(0.0, bid))
    return bid
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= 90:
                    aggressive_bids.append(bid)

    if not alive_opponents:
        return float(min(budget, 20.0))

    alive_count = len(alive_opponents)
    contested = alive_count + 1
    scarcity = supply / float(contested * WATER_REQ)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    for b in prev_bids:
        if b < 90 and b > moderate_prev:
            moderate_prev = b

    emergency = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1
    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if emergency:
        if aggressive_bids:
            bid = 96.0
        else:
            bid = max(62.0, moderate_prev + 2.5)
    elif tight_supply:
        if aggressive_bids and hp > 6 and no_water_days == 0:
            bid = 24.0
        else:
            bid = max(38.0, min(72.0, moderate_prev + 1.5))
    elif ample_supply and hp >= 7 and no_water_days == 0:
        if aggressive_bids:
            bid = 14.0
        else:
            bid = max(18.0, moderate_prev * 0.65 if moderate_prev > 0 else 18.0)
    elif scarcity >= 0.38 and hp >= 6:
        if aggressive_bids:
            bid = 18.0
        else:
            bid = max(22.0, moderate_prev * 0.75 if moderate_prev > 0 else 22.0)
    elif pressured:
        if aggressive_bids:
            bid = 44.0
        else:
            bid = max(48.0, moderate_prev + 2.0)
    else:
        if aggressive_bids:
            bid = 20.0
        else:
            bid = max(26.0, moderate_prev + 1.0 if moderate_prev > 0 else 26.0)

    if day >= 8 and hp >= 7 and no_water_days == 0 and not emergency:
        bid = min(bid, 24.0)

    reserve_floor = 0.0
    if hp <= 4:
        reserve_floor = 0.0
    elif day <= 3:
        reserve_floor = 140.0
    else:
        reserve_floor = 70.0

    max_affordable = budget - reserve_floor
    if max_affordable < 0:
        max_affordable = budget * 0.5

    bid = min(bid, budget, max_affordable if max_affordable > 0 else budget)
    if emergency and bid < 35.0 and budget >= 35.0:
        bid = 35.0

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
    rich_threat = 0
    desperate_opp = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_threat += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

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

    if supply <= 17:
        urgency += 2
    elif supply <= 19:
        urgency += 1

    urgency += min(2, desperate_opp)

    if day >= 8 and hp <= 5:
        urgency += 1

    if highest_prev >= 130:
        pressure_mode = 'extreme'
    elif highest_prev >= 90:
        pressure_mode = 'high'
    elif highest_prev >= 50:
        pressure_mode = 'medium'
    else:
        pressure_mode = 'low'

    if urgency >= 6:
        bid = max(95.0, highest_prev + 2.5)
    elif urgency >= 4:
        if pressure_mode == 'extreme':
            bid = 88.0
        elif pressure_mode == 'high':
            bid = max(72.0, avg_prev + 3.0)
        else:
            bid = max(58.0, highest_prev + 2.0)
    elif urgency >= 2:
        if supply >= 22:
            bid = 26.0
        elif pressure_mode == 'extreme':
            bid = 22.0
        elif pressure_mode == 'high':
            bid = 38.0
        else:
            bid = max(28.0, avg_prev * 0.75)
    else:
        if supply >= 22:
            bid = 14.0
        elif supply >= 20:
            bid = 18.0
        elif pressure_mode == 'extreme':
            bid = 16.0
        else:
            bid = 22.0

    if rich_threat >= 2 and urgency >= 4:
        bid += 6.0
    if rich_threat >= 2 and urgency <= 1:
        bid -= 3.0

    reserve = 0.0
    if day <= 3:
        reserve = 25.0
    elif day <= 6:
        reserve = 18.0
    else:
        reserve = 8.0

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)

    floor_bid = 0.0
    if urgency >= 4:
        floor_bid = 40.0
    elif urgency >= 2:
        floor_bid = 20.0
    elif supply <= 17:
        floor_bid = 12.0

    bid = max(floor_bid, bid)
    bid = min(bid, budget)

    if bid < 0:
        bid = 0.0
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
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        safe_bid = DAILY_SALARY * 0.28
        if hp <= 2 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.6
        return float(min(budget, safe_bid))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= 500:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0)))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    danger = 0
    if hp <= 2:
        danger = 2
    elif hp <= 4 or no_water_days >= 1:
        danger = 1

    if danger == 2:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 2.0)
    elif danger == 1:
        if scarcity == 2:
            bid = max(DAILY_SALARY * 0.82, highest_prev + 1.5)
        elif scarcity == 1:
            bid = max(DAILY_SALARY * 0.68, avg_prev + 1.0)
        else:
            bid = DAILY_SALARY * 0.56
    else:
        if scarcity == 2:
            if highest_prev > 130:
                bid = DAILY_SALARY * 0.34
            else:
                bid = max(DAILY_SALARY * 0.52, min(highest_prev + 1.0, DAILY_SALARY * 0.78))
        elif scarcity == 1:
            if highest_prev > 140:
                bid = DAILY_SALARY * 0.26
            else:
                bid = max(DAILY_SALARY * 0.38, min(avg_prev + 0.5, DAILY_SALARY * 0.6))
        else:
            bid = DAILY_SALARY * 0.22

    if rich_opp >= 2 and scarcity >= 1 and danger == 0 and highest_prev > 120:
        bid = min(bid, DAILY_SALARY * 0.3)

    if urgent_opp >= 2 and danger >= 1:
        bid = max(bid, highest_prev + 2.5)

    if day >= 8 and hp >= 6 and budget < 220:
        bid = min(bid, DAILY_SALARY * 0.42)

    bid = max(0.0, min(float(bid), float(budget)))
    return float(bid)
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
    prev_bids = []
    pressure_bids = []
    low_budget_count = 0
    urgent_opp_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) <= DAILY_SALARY * 1.2:
                low_budget_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    weight = 1.0
                    if opp.get('water_requirement', WATER_REQ) <= supply:
                        weight += 0.1
                    if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                        weight += 0.15
                    pressure_bids.append(bid * weight)

    if budget <= 0:
        return 0.0

    slots = max(1, int(supply // WATER_REQ))
    competitors = 1 + len(alive_opponents)
    tightness = competitors - slots
    very_tight = tightness >= 2
    tight = tightness >= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    effective_pressure = max(pressure_bids) if pressure_bids else 0.0

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.22))

    survival_urgent = hp <= 3 or no_water_days >= 1
    caution = hp <= 5

    if survival_urgent:
        target = max(DAILY_SALARY * 0.92, highest_prev + 3.0, effective_pressure)
        if very_tight:
            target = max(target, DAILY_SALARY * 1.02)
        return float(min(budget, target))

    if very_tight:
        if effective_pressure >= DAILY_SALARY * 1.6:
            target = DAILY_SALARY * 0.34
        elif effective_pressure >= DAILY_SALARY * 1.0:
            target = max(DAILY_SALARY * 0.58, highest_prev + 2.0)
        else:
            target = DAILY_SALARY * 0.52
        if caution:
            target = max(target, DAILY_SALARY * 0.72)
        return float(min(budget, target))

    if tight:
        target = DAILY_SALARY * 0.44
        if highest_prev > 0:
            if highest_prev <= DAILY_SALARY * 0.75:
                target = max(target, highest_prev + 1.5)
            elif highest_prev <= DAILY_SALARY * 1.05:
                target = max(target, DAILY_SALARY * 0.62)
            else:
                target = DAILY_SALARY * 0.36
        if urgent_opp_count >= 2:
            target += 4.0
        if low_budget_count >= 2:
            target -= 3.0
        if caution:
            target = max(target, DAILY_SALARY * 0.68)
        return float(min(budget, max(0.0, target)))

    target = DAILY_SALARY * 0.24
    if highest_prev > 0 and highest_prev < DAILY_SALARY * 0.6:
        target = max(target, highest_prev * 0.75)
    if caution:
        target = max(target, DAILY_SALARY * 0.42)
    if day >= 8 and hp >= 6:
        target *= 0.85
    return float(min(budget, max(0.0, target)))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    capacity = supply / float(WATER_REQ)
    scarcity = 0
    if capacity <= 1.05:
        scarcity = 2
    elif capacity <= 2.05:
        scarcity = 1

    prev_bids = []
    threat_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = 0.0
        if prev and prev.get('bid') is not None:
            pbid = float(prev.get('bid', 0.0))
            prev_bids.append(pbid)
        opp_hp = opp.get('hp', 10)
        opp_nwd = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0.0)
        if opp_hp <= 4 or opp_nwd >= 1:
            desperate_count += 1
            threat_bids.append(max(pbid, DAILY_SALARY * 0.9))
        else:
            threat_bids.append(pbid)
        if opp_budget >= 180 and pbid >= 80:
            rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_bids) if threat_bids else 0.0

    urgency = 0
    if hp <= 3:
        urgency += 2
    elif hp <= 5:
        urgency += 1
    if no_water_days >= 1:
        urgency += 2

    if urgency >= 3:
        target = max(95.0, highest_threat + 6.0)
        if scarcity == 2:
            target = max(target, 125.0)
        elif scarcity == 1:
            target = max(target, 105.0)
    elif urgency >= 1:
        if scarcity == 2:
            target = max(62.0, highest_prev + 3.0)
        elif scarcity == 1:
            target = max(42.0, highest_prev * 0.55 + 4.0)
        else:
            target = max(24.0, highest_prev * 0.22 + 2.0)
    else:
        if scarcity == 2:
            target = max(36.0, min(72.0, highest_prev * 0.35 + 3.0))
        elif scarcity == 1:
            target = max(18.0, min(40.0, highest_prev * 0.18 + 2.0))
        else:
            target = 8.0

    if rich_aggressive >= 2 and urgency == 0:
        target = min(target, 16.0)
    if desperate_count >= 2 and urgency >= 1:
        target = max(target, highest_threat + 8.0)

    if day >= 8:
        target *= 1.12
    elif day <= 2 and urgency == 0:
        target *= 0.85

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = 20.0
    elif hp > 2:
        reserve = 8.0

    affordable = max(0.0, budget - reserve)
    bid = min(target, affordable if affordable > 0 else budget)

    if urgency >= 3 and budget > 0:
        bid = min(max(bid, min(budget, 110.0)), budget)

    if bid < 0:
        bid = 0.0
    return float(round(min(bid, budget), 2))
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
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('budget', 0) > 0:
                    dangerous_prev.append((bid, opp))

    if not alive:
        return min(budget, 20.0)

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units < 1.4:
        scarcity = 3
    elif units < 1.7:
        scarcity = 2
    elif units < 2.0:
        scarcity = 1

    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    bob_like = []
    cindy_like = []
    for bid, opp in dangerous_prev:
        req = opp.get('water_requirement', 0)
        sal = opp.get('daily_salary', 0)
        if req <= 13 and sal <= 80 and bid <= 90:
            bob_like.append(bid)
        elif bid >= 120:
            cindy_like.append(bid)

    target = 38.0
    if bob_like:
        target = max(target, max(bob_like) + 2.0)
    elif prev_bids:
        target = max(target, min(max(prev_bids) * 0.75, 78.0))

    if scarcity == 0:
        bid = 26.0 if not urgent else 52.0
    elif scarcity == 1:
        bid = max(42.0, target - 6.0)
    elif scarcity == 2:
        bid = max(58.0, target)
    else:
        bid = max(68.0, target + 2.0)

    if cindy_like and not urgent and scarcity <= 1:
        bid = min(bid, 48.0)

    if urgent:
        bid = max(bid, 74.0)
    if critical:
        bid = max(bid, 92.0)

    if day >= 8 and hp >= 6 and no_water_days == 0 and scarcity == 0:
        bid = min(bid, 22.0)

    safe_cap = budget
    if hp > 4 and no_water_days == 0:
        safe_cap = min(safe_cap, max(35.0, budget * 0.22 + DAILY_SALARY * 0.35))
    elif hp > 2:
        safe_cap = min(safe_cap, max(60.0, budget * 0.35 + DAILY_SALARY * 0.45))

    bid = min(bid, safe_cap, budget)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
        danger += 1

    supply_pressure = 0
    if supply <= 16:
        supply_pressure = 3
    elif supply <= 19:
        supply_pressure = 2
    elif supply <= 22:
        supply_pressure = 1

    competition = 0
    if highest_prev >= 140:
        competition = 3
    elif highest_prev >= 120:
        competition = 2
    elif highest_prev >= 95:
        competition = 1

    score = danger + supply_pressure + competition

    if score >= 8:
        bid = max(118.0, highest_prev + 2.0)
    elif score >= 6:
        bid = max(92.0, avg_prev * 0.82)
    elif score >= 4:
        bid = max(58.0, avg_prev * 0.58)
    else:
        bid = 28.0

    if supply >= 23 and hp >= 6 and no_water == 0:
        bid *= 0.72
    elif supply >= 20 and hp >= 5 and no_water == 0:
        bid *= 0.82

    if urgent_opp >= 2 and supply <= 18:
        bid += 10.0
    elif urgent_opp >= 1 and supply <= 17:
        bid += 6.0

    if rich_opp >= 3 and highest_prev >= 130:
        bid += 5.0

    if hp >= 8 and no_water == 0 and supply >= 21 and highest_prev >= 130:
        bid = min(bid, 46.0)

    if budget < 80:
        bid = min(bid, budget * 0.72)
    elif budget < 140:
        bid = min(bid, budget * 0.82)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(0.9 * budget, 105.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    rich_threat = False
    desperate_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('budget', 0) >= 200 and opp.get('hp', 10) >= 6:
            rich_threat = True
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.4
    if no_water_days >= 1:
        urgency += 0.35
    urgency += scarcity * 0.35
    if desperate_count >= 2:
        urgency += 0.1
    if urgency > 1.0:
        urgency = 1.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    else:
        if highest_prev >= 135:
            bid = DAILY_SALARY * (0.28 + 0.18 * urgency + 0.08 * scarcity)
        elif highest_prev >= 110:
            bid = max(DAILY_SALARY * (0.48 + 0.18 * urgency), highest_prev + 1.25)
        elif highest_prev >= 70:
            bid = max(DAILY_SALARY * (0.42 + 0.16 * urgency), avg_prev + 2.0)
        else:
            bid = DAILY_SALARY * (0.34 + 0.22 * urgency + 0.10 * scarcity)

    if rich_threat and supply <= 18 and hp <= 4:
        bid = max(bid, highest_prev + 1.5)

    reserve_target = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    max_safe = budget - reserve_target
    if hp <= 3:
        max_safe = budget
    elif max_safe < DAILY_SALARY * 0.2:
        max_safe = max(budget * 0.6, DAILY_SALARY * 0.2)

    if bid > max_safe:
        bid = max_safe

    floor_bid = 0.0
    if hp <= 4 or no_water_days >= 1:
        floor_bid = DAILY_SALARY * 0.35
    elif supply <= 17:
        floor_bid = DAILY_SALARY * 0.25

    if bid < floor_bid:
        bid = floor_bid

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

    alive_opponents = []
    yesterday_bids = []
    high_pressure = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                yesterday_bids.append(float(bid))
                if bid >= 110:
                    high_pressure += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    scarcity = 1.0 - ((float(supply) - 15.0) / 10.0)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    emergency = hp <= 3 or no_water_days >= 2
    danger = hp <= 5 or no_water_days >= 1

    if emergency:
        target = max(118.0, highest_prev + 2.0)
        if supply >= 22:
            target -= 8.0
        elif supply <= 17:
            target += 8.0
    elif danger:
        target = max(72.0, avg_prev * 0.72 + 8.0)
        if high_pressure >= 2:
            target += 10.0
        if supply >= 22:
            target -= 10.0
        elif supply <= 17:
            target += 6.0
    else:
        if high_pressure >= 2:
            target = 18.0 + 10.0 * (1.0 - scarcity)
        else:
            target = 38.0 + 18.0 * scarcity
        if day >= 8 and hp >= 7:
            target *= 0.8

    if budget < 90 and not emergency:
        target *= 0.75
    if budget < 50:
        target *= 0.7

    if hp >= 8 and no_water_days == 0 and highest_prev >= 125 and supply <= 18:
        target = min(target, 16.0)

    bid = min(float(budget), max(0.0, target))
    return float(round(bid, 2))
"""
