# ============================================================
# Experiment: exp_086
# Agent: Alex
# Source: exp_086
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        solo_bid = 1.0
        if hp <= 2 or no_water_days >= 2:
            solo_bid = 8.0
        return min(budget, solo_bid)

    total_agents_alive = 1 + len(alive_opponents)
    tight_supply = supply <= total_agents_alive * WATER_REQ
    very_tight_supply = supply < total_agents_alive * WATER_REQ

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    error_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
        if prev.get('error'):
            error_opp += 1

    highest_prev = max(prev_bids) if prev_bids else None
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else None

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    elif hp <= 6:
        urgency += 1

    if no_water_days >= 2:
        urgency += 3
    elif no_water_days == 1:
        urgency += 1

    if very_tight_supply:
        urgency += 2
    elif tight_supply:
        urgency += 1

    if desperate_opp >= max(1, len(alive_opponents) // 2):
        urgency += 1

    if day >= 8:
        urgency += 1

    if highest_prev is None:
        if urgency >= 6:
            bid = 64.0
        elif urgency >= 4:
            bid = 49.0
        elif urgency >= 2:
            bid = 34.0
        else:
            bid = 18.0 if tight_supply else 10.0
    else:
        if urgency >= 6:
            bid = max(63.0, highest_prev + 2.0)
        elif urgency >= 4:
            bid = max(48.0, highest_prev + 1.0)
        elif urgency >= 2:
            anchor = avg_prev if avg_prev is not None else highest_prev
            bid = max(30.0, anchor)
            if highest_prev <= 25:
                bid = highest_prev + 1.5
        else:
            if highest_prev >= 60:
                bid = 12.0 if hp > 3 else 58.0
            elif highest_prev >= 45:
                bid = 20.0 if not tight_supply else 32.0
            else:
                bid = max(12.0, highest_prev * 0.8)

    if error_opp > 0 and urgency <= 3:
        bid *= 0.9

    if rich_opp >= len(alive_opponents) and urgency <= 2:
        bid *= 0.85

    reserve = 0.0
    if day <= 3:
        reserve = 35.0
    elif day <= 6:
        reserve = 20.0
    else:
        reserve = 5.0

    max_affordable = budget - reserve
    if urgency >= 5:
        max_affordable = budget
    elif max_affordable < 0:
        max_affordable = 0.0

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 60.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    day = day_context['day']
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
        base = DAILY_SALARY * 0.28
        if hp <= 2 or no_water >= 2:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    pressure_scores = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
        opp_hp = opp.get('hp', 0)
        opp_nw = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0)
        req = opp.get('water_requirement', WATER_REQ)
        salary = opp.get('daily_salary', DAILY_SALARY)
        score = 0.0
        if pbid is not None:
            score += float(pbid)
        score += max(0.0, (3 - opp_hp)) * 8.0
        score += max(0.0, opp_nw) * 10.0
        score += min(25.0, opp_budget / max(1.0, salary) * 6.0)
        score += max(0.0, req - 10) * 1.5
        pressure_scores.append(score)
        if opp_hp <= 3 or opp_nw >= 2:
            desperate_count += 1
        if opp_budget >= salary * 8:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_pressure = max(pressure_scores) if pressure_scores else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.35
    if day >= 8:
        urgency += 0.15

    if urgency >= 1.4:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 4.0, avg_prev + 8.0)
    elif supply_tight:
        if highest_prev >= DAILY_SALARY * 1.5 and hp >= 5 and no_water == 0:
            bid = DAILY_SALARY * 0.26
        elif highest_prev >= DAILY_SALARY * 1.15:
            bid = max(DAILY_SALARY * 0.58, avg_prev * 0.72)
        else:
            bid = max(DAILY_SALARY * 0.62, highest_prev + 2.0, max_pressure * 0.42)
    elif supply_loose:
        if hp >= 5 and no_water == 0:
            bid = DAILY_SALARY * 0.24
        else:
            bid = DAILY_SALARY * 0.42
    else:
        bid = max(DAILY_SALARY * 0.38, avg_prev * 0.6)
        if desperate_count >= 2:
            bid = max(bid, DAILY_SALARY * 0.55)
        if rich_count >= 2 and highest_prev > DAILY_SALARY * 1.1 and hp >= 5 and no_water == 0:
            bid = min(bid, DAILY_SALARY * 0.3)

    if hp >= 6 and no_water == 0 and highest_prev > DAILY_SALARY * 1.7:
        bid = min(bid, DAILY_SALARY * 0.22)

    reserve_target = 0.0
    if day <= 3:
        reserve_target = DAILY_SALARY * 3.0
    elif day <= 6:
        reserve_target = DAILY_SALARY * 2.0
    else:
        reserve_target = DAILY_SALARY * 1.0

    spend_cap = budget
    if hp >= 4 and no_water == 0:
        spend_cap = max(0.0, budget - reserve_target)
        spend_cap = max(spend_cap, DAILY_SALARY * 0.22)

    if urgency >= 1.4:
        spend_cap = budget

    bid = min(bid, spend_cap, budget)
    bid = max(0.0, bid)

    if budget < DAILY_SALARY * 0.35 and (hp <= 3 or no_water >= 1):
        bid = budget

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

    supply = float(day_context['supply'])
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
        return float(min(budget, DAILY_SALARY * 0.35))

    cindy_bid = None
    highest_prev = 0.0
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            if pbid > highest_prev:
                highest_prev = pbid
            if oid == 'Cindy':
                cindy_bid = pbid
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 0) <= 3:
            urgent_opp += 1
        if opp.get('budget', 0) >= 200:
            rich_opp += 1

    my_urgent = (hp <= 3) or (no_water_days >= 2)
    tight_supply = supply <= 17
    loose_supply = supply >= 22

    target = DAILY_SALARY * 0.45

    if cindy_bid is not None:
        target = max(target, cindy_bid + 2.0)
    elif highest_prev > 0:
        target = max(target, highest_prev + 2.0)

    if loose_supply and not my_urgent:
        target *= 0.55
    elif tight_supply:
        target *= 1.18

    if urgent_opp >= 2:
        target *= 1.1
    if rich_opp >= 2:
        target *= 1.08

    if my_urgent:
        if cindy_bid is not None:
            target = max(target, cindy_bid + 6.0)
        else:
            target = max(target, DAILY_SALARY * 1.35)

    if hp <= 2 or no_water_days >= 3:
        target = max(target, DAILY_SALARY * 1.6)
        if cindy_bid is not None:
            target = max(target, cindy_bid + 10.0)

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.6

    affordable = max(0.0, budget - reserve)
    if my_urgent:
        affordable = budget

    bid = min(target, affordable if affordable > 0 else budget)

    if bid <= 0 and my_urgent:
        bid = budget
    elif bid <= 0:
        bid = min(budget, DAILY_SALARY * 0.2)

    if not my_urgent and loose_supply and highest_prev >= 120:
        bid = min(budget, DAILY_SALARY * 0.3)

    if bid > budget:
        bid = budget
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if no_water >= 2 or hp <= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, safe_bid))

    prev_bids = []
    aggressive_count = 0
    desperate_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= DAILY_SALARY * 1.6:
                aggressive_count += 1
            if bid >= DAILY_SALARY * 2.4:
                desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if no_water >= 2:
        urgency += 1.0
    elif no_water == 1:
        urgency += 0.45

    if hp <= 2:
        urgency += 0.9
    elif hp <= 4:
        urgency += 0.45

    if day >= 8:
        urgency += 0.2

    base = DAILY_SALARY * (0.34 + 0.28 * scarcity)

    if highest_prev > 0:
        if urgency >= 1.0:
            target = max(base, highest_prev + 3.0)
        elif scarcity >= 0.7:
            target = max(base, avg_prev * 0.92 + 2.0)
        elif aggressive_count >= 2 and urgency < 0.8:
            target = min(base, DAILY_SALARY * 0.32)
        else:
            target = max(base, min(highest_prev * 0.72, avg_prev + 4.0))
    else:
        target = base

    if desperate_count >= 1 and urgency < 1.0:
        target = min(target, DAILY_SALARY * 0.3)

    if supply >= 22 and urgency < 1.0:
        target *= 0.78
    elif supply <= 17:
        target *= 1.18

    if no_water >= 2 or hp <= 2:
        target = max(target, DAILY_SALARY * 0.95)

    reserve_floor = DAILY_SALARY * max(0, 9 - int(day)) * 0.18
    spend_cap = max(0.0, budget - reserve_floor)
    if urgency >= 1.0:
        spend_cap = budget

    bid = min(target, spend_cap, budget)
    bid = max(0.0, bid)

    if 0 < budget < DAILY_SALARY * 0.25 and urgency >= 1.0:
        bid = budget

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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    urgent_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 900:
                rich_threat += 1
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev.get('bid', 0.0)))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units < 1.6:
        scarcity = 2
    elif units < 2.1:
        scarcity = 1

    my_urgent = 0
    if hp <= 2 or no_water_days >= 1:
        my_urgent = 2
    elif hp <= 4:
        my_urgent = 1

    base = 0.0

    if my_urgent == 2:
        if highest_prev > 0:
            base = max(78.0, highest_prev + 2.0)
        else:
            base = 82.0
        if scarcity == 2:
            base += 8.0
    elif my_urgent == 1:
        if scarcity == 2:
            base = max(58.0, avg_prev + 3.0)
        elif scarcity == 1:
            base = max(46.0, avg_prev * 0.7)
        else:
            base = 34.0
    else:
        if scarcity == 2:
            base = max(28.0, avg_prev * 0.42)
        elif scarcity == 1:
            base = max(20.0, avg_prev * 0.3)
        else:
            base = 12.0

    if rich_threat >= 2 and my_urgent == 0:
        base *= 0.85
    if urgent_opp >= 2 and my_urgent >= 1:
        base += 4.0
    if day >= 8 and hp >= 5 and no_water_days == 0:
        base *= 0.9

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    cap = budget
    if budget > reserve_floor:
        cap = max(0.0, budget - reserve_floor * 0.15)

    bid = min(cap, base)
    if my_urgent == 2:
        bid = min(budget, max(bid, 75.0))

    if bid < 0:
        bid = 0.0
    return float(round(min(budget, bid), 2))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = 8.0 if hp > 3 else 18.0
        return float(min(budget, base))

    prev_bids = []
    cindy_bid = None
    rich_threat = 0.0
    desperate_count = 0

    for opp in alive:
        obudget = float(opp.get('budget', 0.0))
        ohp = opp.get('hp', 0)
        onwd = opp.get('no_water_days', 0)
        if obudget > rich_threat:
            rich_threat = obudget
        if ohp <= 2 or onwd >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                bid = float(bid)
                prev_bids.append(bid)
                if bid > 80:
                    cindy_bid = bid

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply <= 17.0
    ample = supply >= 22.0
    urgent = hp <= 2 or no_water_days >= 1
    late_game = day >= 8

    bid = 0.0

    if urgent:
        target = max(72.0, highest_prev + 2.0)
        if cindy_bid is not None:
            target = max(target, cindy_bid + 2.0)
        bid = target
    elif scarcity:
        if cindy_bid is not None and rich_threat > 300:
            bid = max(58.0, cindy_bid + 1.5)
        else:
            bid = max(42.0, avg_prev + 3.0, highest_prev * 0.75)
    elif ample:
        bid = 9.0 if hp > 3 else 18.0
    else:
        bid = max(18.0, min(36.0, avg_prev * 0.45 + 8.0))

    if desperate_count >= 2 and not urgent:
        bid += 8.0
    if late_game and hp >= 4 and not scarcity:
        bid -= 4.0

    reserve = 0.0
    if hp > 3:
        reserve = DAILY_SALARY * 2
    elif hp > 1:
        reserve = DAILY_SALARY

    max_affordable = budget - reserve
    if urgent:
        max_affordable = budget
    if max_affordable < 0:
        max_affordable = min(budget, DAILY_SALARY * 0.5)

    bid = min(bid, max_affordable, budget)
    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        safe = DAILY_SALARY * 0.18
        if hp <= 2 or no_water >= 1:
            safe = DAILY_SALARY * 0.55
        return float(min(budget, safe))

    pressure_bid = 0.0
    cindy_bid = None
    desperate_opponents = 0
    rich_opponents = 0

    for oid, opp in alive_opponents:
        if opp.get('budget', 0) >= 200:
            rich_opponents += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                if bid > pressure_bid:
                    pressure_bid = bid
                if oid == 'Cindy':
                    cindy_bid = bid

    units = supply / float(WATER_REQ)
    low_supply = units < 1.5
    very_low_supply = units < 1.15

    if hp <= 2 or no_water >= 2:
        bid = DAILY_SALARY * 0.98
        if cindy_bid is not None:
            bid = max(bid, min(budget, cindy_bid + 2.0))
        return float(min(budget, bid))

    if hp <= 4 or no_water >= 1:
        bid = DAILY_SALARY * 0.72
        if pressure_bid > 0:
            bid = max(bid, min(DAILY_SALARY * 1.05, pressure_bid + 1.5))
        return float(min(budget, bid))

    if very_low_supply:
        if cindy_bid is not None and cindy_bid >= 120:
            bid = DAILY_SALARY * 0.22
        else:
            bid = DAILY_SALARY * 0.52
            if pressure_bid > 0 and pressure_bid < 85:
                bid = max(bid, pressure_bid + 1.0)
        return float(min(budget, bid))

    if low_supply:
        bid = DAILY_SALARY * 0.38
        if desperate_opponents >= 1:
            bid = DAILY_SALARY * 0.48
        if cindy_bid is not None and cindy_bid < 90:
            bid = max(bid, cindy_bid + 1.0)
        return float(min(budget, bid))

    bid = DAILY_SALARY * 0.24
    if pressure_bid > 0 and pressure_bid < 60:
        bid = max(bid, pressure_bid + 1.0)
    if rich_opponents >= 2:
        bid = min(bid, DAILY_SALARY * 0.2)
    if day >= 8 and hp >= 5:
        bid = min(bid, DAILY_SALARY * 0.18)

    return float(min(budget, bid))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return max(0.0, min(budget, 18.0 if hp > 3 and no_water == 0 else 45.0))

    expected_slots = supply / float(WATER_REQ)
    scarcity = 1.0
    if expected_slots <= 1.25:
        scarcity = 1.35
    elif expected_slots <= 1.5:
        scarcity = 1.18
    elif expected_slots >= 1.85:
        scarcity = 0.82
    elif expected_slots >= 1.65:
        scarcity = 0.92

    opp_bids = []
    threat_bids = []
    rich_count = 0
    desperate_count = 0

    for oid, opp in alive_opps:
        obudget = float(opp.get('budget', 0.0))
        ohp = float(opp.get('hp', 0.0))
        onw = int(opp.get('no_water_days', 0))
        if obudget >= 90:
            rich_count += 1
        if ohp <= 3 or onw >= 1:
            desperate_count += 1

        prev = opp.get('previous_trace') or {}
        pbid = prev.get('bid')
        if pbid is not None:
            pbid = float(pbid)
            opp_bids.append(pbid)
            weight = 1.0
            if obudget >= 120:
                weight += 0.25
            if ohp <= 3 or onw >= 1:
                weight += 0.2
            threat_bids.append(pbid * weight)

    highest_prev = max(opp_bids) if opp_bids else 0.0
    weighted_threat = max(threat_bids) if threat_bids else highest_prev

    urgency = 0.0
    if no_water >= 2:
        urgency += 40.0
    elif no_water == 1:
        urgency += 18.0
    if hp <= 2:
        urgency += 35.0
    elif hp <= 4:
        urgency += 16.0

    base = 42.0 * scarcity + urgency

    if weighted_threat >= 120:
        target = max(base, highest_prev + 2.5)
    elif weighted_threat >= 95:
        target = max(base, highest_prev + 1.5)
    elif weighted_threat > 0:
        target = max(base, highest_prev * 0.92 + 3.0)
    else:
        target = base

    if rich_count >= 2 and expected_slots < 1.6:
        target += 8.0
    if desperate_count >= 2 and hp > 4 and no_water == 0:
        target -= 10.0

    if day >= 8:
        target += 6.0
    if day >= 9 and (hp <= 4 or no_water >= 1):
        target += 10.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left > 0:
        reserve_floor = min(budget * 0.45, days_left * 18.0)

    if hp > 5 and no_water == 0 and expected_slots >= 1.8 and highest_prev >= 100:
        target = min(target, 28.0)

    affordable = budget
    if budget > reserve_floor:
        affordable = max(0.0, budget - reserve_floor * 0.25)

    bid = min(target, affordable)

    if no_water >= 2 or hp <= 2:
        bid = min(budget, max(bid, highest_prev + 2.0, 88.0))
    elif no_water == 1 or hp <= 4:
        bid = min(budget, max(bid, 62.0))

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
    rich_aggressive = 0
    weak_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                weak_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 100 and opp.get('budget', 0) >= 300:
                    rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    scarcity_pressure = 1.0 - scarcity

    danger = 0.0
    if hp <= 1:
        danger = 1.0
    elif hp <= 3:
        danger = 0.75
    elif hp <= 5:
        danger = 0.45
    else:
        danger = 0.15
    if no_water_days >= 2:
        danger = max(danger, 0.95)
    elif no_water_days == 1:
        danger = max(danger, 0.65)

    base = 16.0 + 18.0 * scarcity_pressure + 20.0 * danger

    if highest_prev >= 120:
        if danger < 0.7:
            bid = base * 0.75
        else:
            bid = max(base, min(highest_prev * 0.92, 108.0))
    elif highest_prev >= 70:
        bid = max(base, min(highest_prev + 2.0, 88.0))
    elif highest_prev > 0:
        bid = max(base, highest_prev + 1.5)
    else:
        bid = base

    if rich_aggressive >= 2 and danger < 0.7:
        bid *= 0.82

    if weak_opponents >= 2 and hp >= 6 and no_water_days == 0:
        bid *= 0.9

    if supply >= 22 and danger < 0.7:
        bid *= 0.82
    elif supply <= 17:
        bid *= 1.18

    if day >= 8:
        if hp >= 6 and budget < 180:
            bid *= 0.9
        else:
            bid *= 1.08

    min_safe = 8.0 if hp >= 6 and no_water_days == 0 else 18.0
    if danger >= 0.9:
        min_safe = 72.0
    elif danger >= 0.7:
        min_safe = 48.0

    reserve = 0.0
    if day <= 7:
        reserve = max(0.0, (10 - day) * 6.0)
    max_affordable = max(0.0, budget - reserve)
    if max_affordable <= 0:
        max_affordable = budget

    bid = max(min_safe, bid)
    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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
    rich_pressure = 0
    desperate_pressure = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 140:
                    rich_pressure += 1
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                desperate_pressure += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    low_supply = supply <= 17.0
    very_low_supply = supply <= 16.0
    high_supply = supply >= 22.0

    emergency = hp <= 2 or no_water_days >= 2
    danger = hp <= 4 or no_water_days >= 1

    if emergency:
        bid = max(95.0, high_prev + 2.0)
        if very_low_supply:
            bid = max(bid, 120.0)
        return float(min(budget, bid))

    if danger:
        if high_prev >= 150.0:
            bid = 88.0 if not very_low_supply else 108.0
        else:
            bid = max(72.0, min(110.0, high_prev + 3.0))
        return float(min(budget, bid))

    if high_supply and rich_pressure >= 1:
        bid = 8.0
    elif low_supply:
        if high_prev >= 150.0:
            bid = 22.0
        else:
            bid = max(26.0, min(60.0, high_prev * 0.55 + 4.0))
    else:
        if high_prev >= 150.0:
            bid = 12.0
        elif high_prev >= 90.0:
            bid = 24.0
        elif high_prev > 0.0:
            bid = max(20.0, min(48.0, high_prev * 0.6 + 2.0))
        else:
            bid = 21.0

    if desperate_pressure >= 2 and not high_supply:
        bid += 8.0
    elif desperate_pressure == 1 and low_supply:
        bid += 4.0

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.9

    bid = max(0.0, min(budget, bid))
    return float(bid)
"""
