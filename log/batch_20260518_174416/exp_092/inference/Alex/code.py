# ============================================================
# Experiment: exp_092
# Agent: Alex
# Source: exp_092
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 52.0)
        return min(budget, 28.0)

    total_alive = 1 + len(alive_opponents)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < total_alive

    highest_prev_bid = 0.0
    aggressive_count = 0
    desperate_opp = 0
    for opp in alive_opponents:
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 2:
            desperate_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            if bid > highest_prev_bid:
                highest_prev_bid = bid
            if bid >= DAILY_SALARY * 0.75:
                aggressive_count += 1

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

    if scarcity:
        urgency += 1
    if desperate_opp >= max(1, len(alive_opponents) // 2):
        urgency += 1
    if aggressive_count > 0:
        urgency += 1

    if urgency >= 6:
        target = max(63.0, highest_prev_bid + 2.0)
    elif urgency >= 4:
        target = max(52.0, highest_prev_bid + 1.0 if highest_prev_bid > 0 else 52.0)
    elif urgency >= 2:
        if highest_prev_bid >= 56.0:
            target = 34.0
        else:
            target = max(38.0, highest_prev_bid + 1.0 if highest_prev_bid > 0 else 38.0)
    else:
        if expected_units >= total_alive:
            target = 18.0
        elif highest_prev_bid >= 56.0:
            target = 22.0
        else:
            target = 28.0

    if budget < target:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, budget)
        return max(0.0, min(budget, target * 0.7))

    return max(0.0, min(budget, target))
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

    alive = []
    prev_bids = []
    aggressive_bids = []
    weak_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                weak_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= DAILY_SALARY * 0.9:
                    aggressive_bids.append(bid)

    if not alive:
        return max(0.0, min(float(budget), 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    if no_water_days >= 2:
        urgency += 0.35
    elif no_water_days == 1:
        urgency += 0.18
    urgency += 0.22 * scarcity

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * (0.9 + 0.08 * scarcity)
    elif supply <= 17:
        base = DAILY_SALARY * 0.72
    elif supply >= 22:
        base = DAILY_SALARY * 0.42
    else:
        base = DAILY_SALARY * 0.56

    if highest_prev > 0:
        if highest_prev >= 110:
            if urgency >= 0.55:
                target = DAILY_SALARY * 0.95
            else:
                target = DAILY_SALARY * 0.38
        elif highest_prev >= 85:
            if urgency >= 0.45:
                target = min(DAILY_SALARY * 0.92, highest_prev * 0.82)
            else:
                target = max(base, avg_prev * 0.62)
        else:
            target = max(base, highest_prev + 2.0)
    else:
        target = base

    if weak_opp_count >= 2 and urgency < 0.45:
        target *= 0.9

    if budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.58)
    elif budget > DAILY_SALARY * 8 and urgency >= 0.45:
        target = max(target, DAILY_SALARY * 0.88)

    if hp >= 6 and no_water_days == 0 and supply >= 21 and aggressive_bids:
        target = min(target, DAILY_SALARY * 0.34)

    target = max(0.0, min(float(budget), float(target)))
    return target
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, max(1.0, DAILY_SALARY * 0.25)))

    prev_bids = []
    danger_bids = []
    soft_bids = []
    urgent_opp = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            prev_bids.append(bid)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                danger_bids.append(bid)
            else:
                soft_bids.append(bid)
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            urgent_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    danger_prev = max(danger_bids) if danger_bids else highest_prev
    soft_prev = max(soft_bids) if soft_bids else avg_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgent = no_water_days >= 1 or hp <= 4
    critical = no_water_days >= 2 or hp <= 2

    base = DAILY_SALARY * (0.34 + 0.22 * scarcity)

    if day >= 8:
        base += 6.0

    if urgent_opp >= 2:
        base += 5.0
    elif urgent_opp == 0:
        base -= 3.0

    if highest_prev >= 120:
        if my_urgent:
            bid = max(base + 18.0, min(highest_prev * 0.72, DAILY_SALARY * 1.18))
        else:
            bid = min(base - 6.0, DAILY_SALARY * 0.42)
    elif highest_prev >= 85:
        if my_urgent:
            bid = max(base + 12.0, min(danger_prev + 2.5, DAILY_SALARY * 1.08))
        else:
            bid = max(base, soft_prev + 1.5)
    elif highest_prev > 0:
        if scarcity > 0.6 or my_urgent:
            bid = max(base + 8.0, highest_prev + 2.0)
        else:
            bid = max(base, avg_prev + 1.0)
    else:
        bid = base

    if critical:
        bid = max(bid, DAILY_SALARY * 0.98 + 8.0 * scarcity)
    elif my_urgent:
        bid = max(bid, DAILY_SALARY * (0.78 + 0.12 * scarcity))

    reserve_days = 10 - day
    reserve_target = max(0.0, reserve_days * DAILY_SALARY * 0.18)
    spend_cap = budget - reserve_target
    if critical:
        spend_cap = budget
    elif my_urgent:
        spend_cap = max(spend_cap, budget * 0.72)
    else:
        spend_cap = max(spend_cap, budget * 0.45)

    bid = min(bid, spend_cap, budget)
    bid = max(0.0, bid)

    if budget < 25:
        bid = min(bid, budget)
        if my_urgent:
            bid = budget

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    distress_count = 0
    rich_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > DAILY_SALARY * 8:
                rich_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                distress_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if not alive_opponents:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.18))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    urgent = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if urgent:
        bid = max(DAILY_SALARY * 1.02, highest_prev + 2.5)
        return float(min(budget, bid))

    if pressured:
        if highest_prev >= 105:
            bid = highest_prev + 1.5
        elif highest_prev >= 85:
            bid = highest_prev + 2.0
        else:
            bid = DAILY_SALARY * 0.92
        if tight_supply:
            bid += 6.0
        return float(min(budget, bid))

    if tight_supply:
        if distress_count >= 2:
            bid = max(DAILY_SALARY * 0.88, highest_prev + 1.0)
        elif highest_prev >= 100:
            bid = DAILY_SALARY * 0.42
        elif highest_prev >= 85:
            bid = DAILY_SALARY * 0.64
        else:
            bid = DAILY_SALARY * 0.58
    elif ample_supply:
        if highest_prev >= 105 and rich_count >= 2:
            bid = DAILY_SALARY * 0.22
        else:
            bid = DAILY_SALARY * 0.16
    else:
        if highest_prev >= 105:
            bid = DAILY_SALARY * 0.26
        elif highest_prev >= 95:
            bid = DAILY_SALARY * 0.34
        elif avg_prev >= 85:
            bid = DAILY_SALARY * 0.46
        else:
            bid = DAILY_SALARY * 0.52

    if day >= 8 and hp >= 7 and no_water == 0:
        bid *= 0.9

    if budget < DAILY_SALARY * 2 and not (tight_supply or pressured):
        bid = min(bid, DAILY_SALARY * 0.25)

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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    threat_bids = []
    rich_threat = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > DAILY_SALARY * 4:
                threat_bids.append(float(bid))
        if opp.get('budget', 0) > rich_threat:
            rich_threat = opp.get('budget', 0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    threat_prev = max(threat_bids) if threat_bids else highest_prev

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 3 or no_water >= 2:
        urgency = 2
    elif hp <= 6 or no_water >= 1:
        urgency = 1

    base = DAILY_SALARY * 0.34
    if scarcity == 1:
        base = DAILY_SALARY * 0.48
    elif scarcity == 2:
        base = DAILY_SALARY * 0.68

    if urgency == 1:
        base += DAILY_SALARY * 0.12
    elif urgency == 2:
        base += DAILY_SALARY * 0.24

    if threat_prev >= DAILY_SALARY * 0.9:
        if urgency < 2 and scarcity == 0:
            bid = DAILY_SALARY * 0.22
        else:
            bid = DAILY_SALARY * 0.93
    elif threat_prev >= DAILY_SALARY * 0.65:
        bid = max(base, threat_prev + 1.25)
    elif threat_prev >= DAILY_SALARY * 0.35:
        bid = max(base, threat_prev + 0.75)
    else:
        bid = base

    if day >= 8 and hp > 5 and no_water == 0 and scarcity == 0:
        bid = min(bid, DAILY_SALARY * 0.28)

    if rich_threat > budget * 2 and urgency == 0 and scarcity == 0:
        bid = min(bid, DAILY_SALARY * 0.2)

    if budget < DAILY_SALARY:
        if urgency == 2:
            bid = max(bid, budget * 0.9)
        else:
            bid = min(bid, budget * 0.55)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((oid, opp))

    if not alive_opps:
        safe = DAILY_SALARY * 0.22
        if hp <= 2 or no_water_days >= 2:
            safe = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, safe)))

    highest_prev = 0.0
    cindy_prev = None
    needy_count = 0
    rich_count = 0

    for oid, opp in alive_opps:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            needy_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            if bid > highest_prev:
                highest_prev = bid
            if oid == 'Cindy':
                cindy_prev = bid

    units_available = supply / float(WATER_REQ)
    scarce = units_available < 1.25
    comfortable = units_available > 1.7

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

    if day >= 8:
        urgency += 1

    base = DAILY_SALARY * 0.24

    if comfortable:
        base = DAILY_SALARY * 0.18
    if scarce:
        base = DAILY_SALARY * 0.34

    if cindy_prev is not None:
        if cindy_prev >= 120:
            base = min(base, DAILY_SALARY * 0.2)
        elif cindy_prev >= 90:
            base = max(base, DAILY_SALARY * 0.28)
        elif cindy_prev <= 50:
            base = max(base, cindy_prev + 2.0)

    if highest_prev > 0:
        if highest_prev >= 100 and urgency <= 1:
            base = min(base, DAILY_SALARY * 0.2)
        elif highest_prev <= 35:
            base = max(base, highest_prev + 1.5)

    if needy_count >= 1 and scarce:
        base = max(base, DAILY_SALARY * 0.42)

    if urgency >= 5:
        bid = DAILY_SALARY * 0.96
    elif urgency >= 3:
        bid = max(base, DAILY_SALARY * 0.62)
    elif urgency >= 2:
        bid = max(base, DAILY_SALARY * 0.46)
    else:
        bid = base

    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0:
        soft_cap = min(soft_cap, budget / float(reserve_days))
        soft_cap = max(soft_cap, DAILY_SALARY * 0.18)

    if urgency >= 3:
        soft_cap = budget

    bid = min(bid, soft_cap)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threats = 0
    desperate_threats = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 100:
                rich_threats += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_threats += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev.get('bid', 0.0)))

    if not alive_opponents:
        return float(min(budget, 10.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply <= 17)
    abundant = (supply >= 22)
    critical_self = (hp <= 3 or no_water_days >= 1)
    weak_self = (hp <= 5)

    bid = 0.0

    if critical_self:
        if scarcity:
            bid = max(98.0, highest_prev + 2.0)
        else:
            bid = max(88.0, avg_prev + 3.0)
    elif weak_self:
        if scarcity:
            bid = max(72.0, min(96.0, highest_prev * 0.8))
        else:
            bid = max(58.0, min(82.0, avg_prev * 0.65))
    else:
        if scarcity:
            if rich_threats >= 2:
                bid = 24.0
            else:
                bid = max(38.0, min(65.0, avg_prev * 0.55))
        elif abundant:
            bid = 18.0 if rich_threats >= 1 else 26.0
        else:
            bid = 30.0 if rich_threats >= 2 else 42.0

    if desperate_threats >= 2 and not critical_self:
        bid *= 0.9

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.85

    reserve = 0.0
    if hp <= 3:
        reserve = 0.0
    elif hp <= 5:
        reserve = 35.0
    else:
        reserve = 70.0

    max_affordable = max(0.0, budget - reserve)
    if critical_self:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
    bid = max(0.0, min(bid, budget))
    return float(round(bid, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    bob_like_bid = None
    high_bid = 0.0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > high_bid:
                    high_bid = float(bid)
                if agent_id == 'Bob':
                    bob_like_bid = float(bid)

    if budget <= 0:
        return 0.0

    winners_capacity = int(supply // WATER_REQ)
    alive_count = len(alive) + 1
    scarcity = alive_count - winners_capacity

    if not alive:
        return float(min(budget, 21.0))

    threat_bid = bob_like_bid if bob_like_bid is not None else (max(prev_bids) if prev_bids else 45.0)

    emergency = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if winners_capacity >= 2:
        if emergency:
            bid = max(56.0, threat_bid + 2.0)
        elif pressured:
            bid = max(44.0, min(55.0, threat_bid + 1.0))
        else:
            bid = 31.0 if high_bid >= 80.0 else 36.0
    else:
        if emergency:
            bid = max(68.0, threat_bid + 6.0)
        elif pressured:
            bid = max(58.0, threat_bid + 3.0)
        else:
            bid = max(50.0, threat_bid + 1.5)

    if day >= 8:
        bid += 4.0
    if day >= 9 and pressured:
        bid += 6.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if not emergency and days_left > 0:
        reserve_floor = min(budget * 0.35, days_left * 18.0)

    max_affordable = max(0.0, budget - reserve_floor)
    if emergency:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_caps = []
    urgent_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                opp_caps.append(float(bid))
            else:
                opp_caps.append(float(opp.get('daily_salary', DAILY_SALARY)) * 0.6)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units_available = supply / float(WATER_REQ)
    tight_supply = supply <= 18
    very_tight_supply = supply <= 15.5
    looser_supply = supply >= 22

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

    if very_tight_supply:
        danger += 2
    elif tight_supply:
        danger += 1

    if urgent_opp_count >= 2:
        danger += 1

    if day >= 8:
        danger += 1

    if danger <= 1:
        base = max(18.0, avg_prev * 0.72)
        if highest_prev >= 80:
            base = min(base, 38.0)
        elif highest_prev <= 65 and tight_supply:
            base = max(base, highest_prev + 2.0)
    elif danger <= 3:
        target = max(48.0, min(66.0, second_prev + 3.0))
        if highest_prev <= 65:
            target = max(target, highest_prev + 2.0)
        if tight_supply:
            target += 3.0
        base = target
    else:
        target = max(62.0, highest_prev + 2.0)
        if highest_prev >= 95:
            target = 97.0
        elif highest_prev >= 80:
            target = highest_prev + 1.0
        if very_tight_supply:
            target += 4.0
        base = target

    if looser_supply and danger <= 2:
        base -= 6.0

    reserve_floor = 0.0
    if day <= 6:
        reserve_floor = 35.0
    elif day <= 8:
        reserve_floor = 20.0

    max_affordable = budget - reserve_floor
    if max_affordable < 0:
        max_affordable = budget

    bid = min(base, max_affordable)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, max(75.0, highest_prev + 2.0)))

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
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    total_players = 1 + len(alive)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < total_players

    opp_signals = []
    urgent_count = 0
    rich_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is None:
            prev_bid = opp.get('daily_salary', DAILY_SALARY) * 0.55
        opp_hp = opp.get('hp', 10)
        opp_nowater = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0)
        opp_salary = opp.get('daily_salary', DAILY_SALARY)

        urgency_bonus = 0.0
        if opp_nowater >= 1:
            urgency_bonus += opp_salary * 0.18
        if opp_hp <= 3:
            urgency_bonus += opp_salary * 0.14
        if opp_budget >= opp_salary * 8:
            rich_count += 1
            urgency_bonus += opp_salary * 0.06
        if opp_nowater >= 1 or opp_hp <= 3:
            urgent_count += 1

        signal = float(prev_bid) + float(urgency_bonus)
        opp_signals.append(signal)

    highest_signal = max(opp_signals) if opp_signals else DAILY_SALARY * 0.55
    avg_signal = sum(opp_signals) / float(len(opp_signals)) if opp_signals else DAILY_SALARY * 0.55

    my_urgent = (hp <= 3) or (no_water >= 1)
    my_critical = (hp <= 2) or (no_water >= 2)

    if my_critical:
        bid = max(DAILY_SALARY * 0.95, highest_signal + 2.5)
    elif my_urgent:
        bid = max(DAILY_SALARY * 0.82, highest_signal + 1.5)
    else:
        if scarcity:
            bid = max(DAILY_SALARY * 0.58, avg_signal + 1.0)
            if urgent_count >= 2:
                bid = max(bid, highest_signal + 1.8)
        else:
            bid = DAILY_SALARY * 0.34
            if day >= 8:
                bid = DAILY_SALARY * 0.42
            if highest_signal < DAILY_SALARY * 0.45:
                bid = max(bid, highest_signal + 0.8)

    if rich_count >= 2 and not my_urgent and not scarcity:
        bid *= 0.92

    if budget < DAILY_SALARY * 1.2:
        if my_urgent:
            bid = max(bid, budget * 0.92)
        else:
            bid = min(bid, budget * 0.7)

    bid = min(float(budget), float(bid))
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""
