# ============================================================
# Experiment: exp_023
# Agent: Alex
# Source: exp_023
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
    urgent_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev:
                b = prev.get('bid')
                if isinstance(b, (int, float)):
                    prev_bids.append(float(b))

    if not alive:
        return min(budget, 21.0)

    players = len(alive) + 1
    scarcity = float(supply) / float(players * WATER_REQ)

    my_urgent = hp <= 2 or no_water >= 2
    if hp <= 1:
        base = DAILY_SALARY * 0.98
    elif my_urgent:
        base = DAILY_SALARY * 0.9
    elif no_water == 1:
        base = DAILY_SALARY * 0.72
    else:
        base = DAILY_SALARY * 0.55

    if scarcity < 0.45:
        base += 18
    elif scarcity < 0.65:
        base += 10
    elif scarcity > 1.0:
        base -= 8

    if urgent_opp >= max(1, len(alive) // 2):
        base += 6

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if highest_prev >= DAILY_SALARY * 0.9:
            if my_urgent:
                base = max(base, DAILY_SALARY * 0.93)
            else:
                base = min(base, DAILY_SALARY * 0.42)
        else:
            target = highest_prev + 1.25
            if avg_prev < DAILY_SALARY * 0.45:
                target += 1.0
            base = max(base, target)

    if budget < DAILY_SALARY * 1.2 and not my_urgent:
        base = min(base, DAILY_SALARY * 0.5)
    if budget < DAILY_SALARY * 0.7:
        base = min(base, budget)

    if base < 0:
        base = 0.0
    return float(min(budget, round(base, 2)))
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    threat_scores = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        opp_budget = opp.get('budget', 0)
        opp_hp = opp.get('hp', 0)
        opp_nwd = opp.get('no_water_days', 0)
        score = 0.0
        score += min(float(opp_budget) / 100.0, 2.0)
        score += float(max(0, opp_hp - 2)) * 0.15
        score += float(max(0, 2 - opp_nwd)) * 0.2
        if bid is not None:
            score += min(float(bid) / 80.0, 2.0)
        threat_scores.append(score)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_threat = max(threat_scores) if threat_scores else 0.0

    supply_pressure = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    urgent = hp <= 2 or no_water_days >= 1
    fragile = hp <= 4

    if urgent:
        target = max(DAILY_SALARY * 0.95, highest_prev_bid + 3.0)
        if supply <= 17:
            target = max(target, DAILY_SALARY * 1.1)
        return float(min(budget, target))

    base = DAILY_SALARY * (0.28 + 0.32 * supply_pressure)

    if highest_prev_bid >= 120:
        if hp >= 6 and no_water_days == 0 and supply >= 20:
            return float(min(budget, DAILY_SALARY * 0.18))
        base = max(base, DAILY_SALARY * 0.72)
    elif highest_prev_bid >= 70:
        base = max(base, min(highest_prev_bid + 2.0, DAILY_SALARY * 0.92))
    elif highest_prev_bid > 0:
        base = max(base, avg_prev_bid + 1.5)
    else:
        base = max(base, DAILY_SALARY * 0.35)

    if max_threat > 2.8:
        base += 6.0
    elif max_threat < 1.2:
        base -= 4.0

    if supply >= 23 and hp >= 6:
        base *= 0.72
    elif supply <= 17:
        base *= 1.18

    if fragile:
        base *= 1.15

    if day >= 8 and hp >= 5:
        base *= 0.9

    reserve_floor = DAILY_SALARY * 0.15
    bid = max(reserve_floor, base)
    bid = min(budget, bid)
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
        base = 18.0 if hp > 3 else 40.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    dangerous_prev = 0.0
    desperate_count = 0
    rich_aggressive = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            weight = float(bid)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                weight += 8.0
                desperate_count += 1
            if opp.get('budget', 0) > 400 and float(bid) >= 80:
                weight += 6.0
                rich_aggressive += 1
            if weight > dangerous_prev:
                dangerous_prev = weight
        else:
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                desperate_count += 1

    max_prev = max(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    critical_self = hp <= 3 or no_water_days >= 1
    very_critical_self = hp <= 2 or no_water_days >= 2

    if very_critical_self:
        target = max(95.0, dangerous_prev + 6.0, max_prev + 4.0)
        if tight_supply:
            target += 18.0
        elif medium_supply:
            target += 8.0
    elif critical_self:
        target = max(72.0, dangerous_prev + 3.0, max_prev + 2.0)
        if tight_supply:
            target += 14.0
        elif medium_supply:
            target += 6.0
    else:
        if tight_supply:
            target = max(58.0, dangerous_prev + 2.0, max_prev + 1.5)
        elif medium_supply:
            target = max(42.0, 0.72 * dangerous_prev + 4.0, 0.65 * max_prev + 3.0)
        else:
            target = max(24.0, 0.38 * dangerous_prev + 2.0, 0.3 * max_prev + 2.0)

    if desperate_count >= 2:
        target += 8.0
    elif desperate_count == 1:
        target += 4.0

    if rich_aggressive >= 2:
        target += 6.0
    elif rich_aggressive == 1:
        target += 3.0

    if day >= 8 and hp > 4 and no_water_days == 0:
        target *= 0.92

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 35.0
    elif day <= 9:
        reserve_floor = 15.0

    spend_cap = budget
    if budget > reserve_floor:
        spend_cap = budget - reserve_floor
    if critical_self:
        spend_cap = budget

    bid = min(target, spend_cap)

    if bid < 0:
        bid = 0.0

    if bid == 0 and critical_self:
        bid = min(budget, 25.0)

    return float(max(0.0, min(budget, bid)))
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
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    dangerous_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                dangerous_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_opp = max(dangerous_bids) if dangerous_bids else highest_prev

    likely_winners = int(supply // WATER_REQ)
    if likely_winners < 1:
        likely_winners = 1

    my_urgent = (hp <= 3) or (no_water >= 1)
    my_critical = (hp <= 2) or (no_water >= 2)
    high_supply = supply >= 24
    mid_supply = supply >= 20

    if my_critical:
        target = max(DAILY_SALARY * 1.25, urgent_opp + 8.0)
    elif my_urgent:
        target = max(DAILY_SALARY * 0.98, urgent_opp + 4.0)
    else:
        if likely_winners >= 2 or high_supply:
            target = max(DAILY_SALARY * 0.62, highest_prev + 2.0)
        elif mid_supply:
            if highest_prev >= DAILY_SALARY * 1.15:
                target = DAILY_SALARY * 0.28
            else:
                target = max(DAILY_SALARY * 0.52, highest_prev + 1.5)
        else:
            if highest_prev >= DAILY_SALARY * 1.0:
                target = DAILY_SALARY * 0.18
            else:
                target = max(DAILY_SALARY * 0.42, highest_prev + 1.0)

    if day >= 8 and hp > 4 and not my_urgent:
        target *= 0.9

    if budget < DAILY_SALARY * 0.8 and not my_urgent:
        target = min(target, DAILY_SALARY * 0.45)

    bid = min(float(budget), float(target))
    if bid < 0:
        bid = 0.0
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    urgent_prev_bids = []
    rich_aggressive = 0
    weak_opponents = 0

    for opp in alive_opponents:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            weak_opponents += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 8:
            rich_aggressive += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                prev_supply = prev.get('supply')
                if prev_supply is not None and float(prev_supply) <= 18.0:
                    urgent_prev_bids.append(float(bid))
                elif opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_high = max(urgent_prev_bids) if urgent_prev_bids else highest_prev

    tight_supply = supply <= 17.0
    medium_tight = supply <= 19.0
    danger = hp <= 3 or no_water_days >= 1
    severe_danger = hp <= 2 or no_water_days >= 2

    if severe_danger:
        target = max(DAILY_SALARY * 1.15, urgent_high + 3.0)
    elif danger:
        if tight_supply:
            target = max(DAILY_SALARY * 0.95, urgent_high + 2.0)
        else:
            target = max(DAILY_SALARY * 0.82, highest_prev * 0.92)
    else:
        if tight_supply:
            target = max(DAILY_SALARY * 0.62, min(DAILY_SALARY * 0.95, urgent_high * 0.72))
        elif medium_tight:
            target = max(DAILY_SALARY * 0.42, min(DAILY_SALARY * 0.72, highest_prev * 0.52))
        else:
            target = DAILY_SALARY * 0.24

    if rich_aggressive >= 2 and not danger:
        target *= 0.88
    if weak_opponents >= 2 and not severe_danger:
        target *= 0.93
    if day >= 8 and hp >= 5 and no_water_days == 0 and not tight_supply:
        target *= 0.85

    reserve_floor = DAILY_SALARY * max(0, 10 - day)
    max_affordable = budget
    if not severe_danger:
        max_affordable = max(0.0, budget - reserve_floor * 0.15)
        max_affordable = min(budget, max_affordable + DAILY_SALARY * 0.35)

    bid = min(target, max_affordable)

    if danger and bid < DAILY_SALARY * 0.55:
        bid = min(budget, DAILY_SALARY * 0.55)
    if severe_danger and bid < DAILY_SALARY * 0.9:
        bid = min(budget, DAILY_SALARY * 0.9)

    if not danger and not tight_supply and highest_prev >= DAILY_SALARY * 1.8:
        bid = min(bid, DAILY_SALARY * 0.22)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = 18.0 if hp > 3 else 42.0
        return float(min(budget, base))

    prev_bids = []
    strong_prev = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 120:
                strong_prev.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

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

    if scarcity == 2:
        urgency += 2
    elif scarcity == 1:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        target = max(110.0, highest_prev + 3.0)
    elif urgency >= 4:
        if highest_prev >= 120:
            target = highest_prev + 2.0
        else:
            target = max(72.0, avg_prev * 0.7 + 8.0)
    elif urgency >= 2:
        if highest_prev >= 130:
            target = 58.0
        else:
            target = max(34.0, min(68.0, avg_prev * 0.45 + 6.0))
    else:
        if strong_prev:
            target = 22.0
        else:
            target = max(18.0, min(40.0, avg_prev * 0.35 + 4.0))

    reserve_days = 10 - day
    if reserve_days < 0:
        reserve_days = 0
    soft_cap = budget
    if reserve_days > 0:
        soft_cap = min(budget, budget / (reserve_days + 1) * 1.6)

    if urgency >= 5:
        final_bid = min(budget, max(target, soft_cap))
    else:
        final_bid = min(budget, min(target, soft_cap))

    if hp <= 2 or no_water >= 2:
        final_bid = min(budget, max(final_bid, highest_prev + 2.5, 95.0))

    if final_bid < 0:
        final_bid = 0.0
    return float(final_bid)
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    reqs = [WATER_REQ]
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            reqs.append(float(opp.get('water_requirement', WATER_REQ)))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    total_req = sum(reqs)
    pressure = total_req / max(supply, 1.0)

    if not alive:
        base = DAILY_SALARY * 0.28
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.6
        return max(0.0, min(budget, round(base, 2)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    median_prev = sorted(prev_bids)[int(len(prev_bids) / 2)] if prev_bids else 0.0

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if pressure <= 2.2:
        base = DAILY_SALARY * 0.42
    elif pressure <= 2.8:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.9

    if highest_prev >= 160:
        if urgent:
            target = max(base, 148.0)
        else:
            target = min(base, DAILY_SALARY * 0.5)
    elif highest_prev >= 120:
        if pressure <= 2.4 and not urgent:
            target = max(base, median_prev + 2.0)
        else:
            target = max(base, highest_prev + 1.5)
    elif highest_prev > 0:
        target = max(base, highest_prev + 2.0)
    else:
        target = base

    rich_threats = 0
    weak_threats = 0
    for oid, opp in alive:
        ob = float(opp.get('budget', 0.0))
        ohp = float(opp.get('hp', 0.0))
        onw = int(opp.get('no_water_days', 0))
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if ob >= 300 and ohp >= 4:
            rich_threats += 1
        if onw >= 1 or ohp <= 2:
            weak_threats += 1
        if pbid is not None and float(pbid) >= 150:
            rich_threats += 1

    if rich_threats >= 2 and not urgent and pressure > 2.5:
        target *= 0.82
    if weak_threats >= 2 and pressure <= 2.4:
        target *= 0.9

    if urgent:
        target = max(target, DAILY_SALARY * 0.95)
    if critical:
        target = max(target, 135.0)

    if day >= 8 and hp >= 6 and budget < 180:
        target *= 0.9
    if day >= 8 and urgent:
        target *= 1.08

    target = min(target, budget)
    target = max(0.0, target)
    return round(target, 2)
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if len(alive) == 0:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.8
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    cindy_prev = None
    pressure = 0.0
    desperate_count = 0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > pressure:
                pressure = float(bid)
        if agent_id == 'Cindy' and bid is not None:
            cindy_prev = float(bid)
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1

    scarcity = 1.0
    if supply <= 16:
        scarcity = 1.25
    elif supply <= 19:
        scarcity = 1.1
    elif supply >= 24:
        scarcity = 0.85
    elif supply >= 22:
        scarcity = 0.92

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.45
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.35

    if cindy_prev is None:
        target = DAILY_SALARY * 0.55 * scarcity
        if urgency > 0.8:
            target = DAILY_SALARY * 0.95
        elif desperate_count >= 2:
            target = DAILY_SALARY * 0.7 * scarcity
    else:
        if urgency >= 1.0:
            target = min(budget, cindy_prev + 8.0)
        elif urgency > 0.0:
            target = max(DAILY_SALARY * 0.6, cindy_prev * 0.72 * scarcity)
        else:
            if cindy_prev >= 160:
                target = DAILY_SALARY * 0.28 * scarcity
            elif cindy_prev >= 120:
                target = DAILY_SALARY * 0.38 * scarcity
            elif cindy_prev >= 80:
                target = DAILY_SALARY * 0.52 * scarcity
            else:
                target = max(DAILY_SALARY * 0.45, cindy_prev + 2.0)

    if day >= 8 and hp > 4 and no_water_days == 0:
        target *= 0.9

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if days_left > 0 and hp > 2:
        reserve_floor = min(budget * 0.5, days_left * DAILY_SALARY * 0.18)

    bid = min(budget, target)
    if budget - bid < reserve_floor and urgency < 1.0:
        bid = max(0.0, budget - reserve_floor)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.92))
    elif hp <= 4 or no_water_days == 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.62 * scarcity))

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_threat_bid = 0.0
    weak_pressure_bid = 0.0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 300 and opp.get('hp', 0) > 4:
                    if float(bid) > strong_threat_bid:
                        strong_threat_bid = float(bid)
                else:
                    if float(bid) > weak_pressure_bid:
                        weak_pressure_bid = float(bid)

    if not alive:
        return float(min(budget, 18.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    emergency = hp <= 2 or no_water >= 2
    danger = hp <= 4 or no_water >= 1

    if emergency:
        base = 0.92 * DAILY_SALARY + 18.0 * scarcity
    elif danger:
        base = 0.68 * DAILY_SALARY + 14.0 * scarcity
    else:
        base = 0.42 * DAILY_SALARY + 10.0 * scarcity

    if len(alive) >= 3:
        base += 4.0
    elif len(alive) == 1:
        base -= 5.0

    target = base

    if strong_threat_bid > 0:
        if emergency:
            target = max(target, min(strong_threat_bid + 2.0, 0.95 * DAILY_SALARY + 20.0 * scarcity))
        elif danger and strong_threat_bid <= 95:
            target = max(target, strong_threat_bid + 1.5)
        elif strong_threat_bid < 60:
            target = max(target, strong_threat_bid + 1.0)
    elif weak_pressure_bid > 0:
        if weak_pressure_bid <= 70:
            target = max(target, weak_pressure_bid + 1.5)
        elif emergency:
            target = max(target, weak_pressure_bid + 1.0)

    if budget < DAILY_SALARY * 1.2:
        target = min(target, budget * 0.72)
    elif budget < DAILY_SALARY * 2.0:
        target = min(target, budget * 0.60)

    if day >= 8 and hp > 4 and no_water == 0:
        target *= 0.92

    if target < 0:
        target = 0.0

    bid = min(budget, round(target, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 500:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    if hp <= 2 or no_water >= 2:
        emergency = max(62.0, highest_prev + 3.0)
        return float(min(budget, emergency))

    if hp <= 4 or no_water >= 1:
        strong = max(42.0, min(68.0, highest_prev * 0.72 + 6.0))
        return float(min(budget, strong))

    if slots >= 2:
        base = 16.0
        if highest_prev > 110:
            base = 12.0
        elif highest_prev > 70:
            base = 14.0
        elif avg_prev < 35:
            base = 18.0
        if urgent_opp >= 2:
            base += 4.0
        return float(min(budget, base))

    contest = 24.0
    if highest_prev > 110:
        contest = 20.0
    elif highest_prev > 70:
        contest = 26.0
    else:
        contest = max(24.0, avg_prev + 2.0)

    if rich_opp >= 2:
        contest -= 3.0
    if urgent_opp >= 2:
        contest += 6.0

    contest = max(15.0, min(55.0, contest))
    return float(min(budget, contest))
"""
