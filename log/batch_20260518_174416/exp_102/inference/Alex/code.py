# ============================================================
# Experiment: exp_102
# Agent: Alex
# Source: exp_102
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
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
    desperate_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    competitors = 1 + len(alive)
    est_units = supply / float(WATER_REQ)
    scarcity = est_units < competitors

    if not alive:
        if hp <= 2 or no_water >= 2:
            return min(budget, 63)
        if scarcity:
            return min(budget, 35)
        return min(budget, 22)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0

    emergency = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    target = 0

    if emergency:
        target = max(60, highest_prev + 2)
    elif scarcity:
        if highest_prev >= 60:
            target = 28 if hp > 4 else 62
        elif highest_prev >= 45:
            target = highest_prev + 2
        else:
            target = 44 + min(10, desperate_count * 3)
    else:
        if highest_prev >= 60:
            target = 20 if hp > 5 else 58
        elif highest_prev >= 40:
            target = 34 if not pressured else 46
        else:
            target = 24 + min(8, desperate_count * 2)

    if day >= 8:
        target += 6 if pressured else 2

    if budget < target:
        target = budget

    if budget <= 0:
        return 0

    if target < 0:
        target = 0

    return min(budget, target)
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    opp_pressures = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = None
            if prev:
                bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            pressure = 0.0
            if opp.get('hp', 10) <= 3:
                pressure += 1.0
            if opp.get('no_water_days', 0) >= 1:
                pressure += 1.0
            if opp.get('budget', 0) > budget:
                pressure += 0.5
            opp_pressures.append(pressure)

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_pressure = max(opp_pressures) if opp_pressures else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.55
    if no_water >= 2:
        danger += 1.0
    elif no_water >= 1:
        danger += 0.45

    base = 16.0 + 18.0 * scarcity + 10.0 * danger

    if highest_prev >= 120:
        if danger < 0.8 and supply >= 20:
            bid = 8.0 + 6.0 * scarcity
        else:
            bid = 78.0 + 10.0 * danger + 6.0 * scarcity
    elif highest_prev >= 90:
        if danger < 0.5 and supply >= 21:
            bid = 12.0 + 6.0 * scarcity
        else:
            bid = max(base + 10.0, min(highest_prev - 6.0, 82.0 + 8.0 * danger))
    elif highest_prev >= 60:
        bid = max(base + 8.0, highest_prev + 2.0)
    elif highest_prev > 0:
        bid = max(base, avg_prev + 4.0)
    else:
        bid = base

    if max_pressure >= 1.5 and danger >= 0.5:
        bid += 8.0

    if supply >= 23 and danger < 0.5:
        bid *= 0.72
    elif supply >= 20 and danger < 0.5:
        bid *= 0.85
    elif supply <= 16:
        bid += 10.0

    if day >= 8:
        bid += 6.0 * danger + 3.0 * scarcity

    safe_cap = budget
    if budget > DAILY_SALARY * 8:
        safe_cap = min(budget, 110.0)
    elif budget > DAILY_SALARY * 5:
        safe_cap = min(budget, 95.0)
    else:
        safe_cap = min(budget, 82.0 + 10.0 * danger)

    if danger >= 1.5:
        bid = max(bid, 88.0)
        safe_cap = budget
    elif danger >= 1.0:
        bid = max(bid, 72.0)

    if hp >= 7 and no_water == 0 and supply >= 22 and highest_prev >= 90:
        bid = min(bid, 15.0)

    bid = max(0.0, min(float(bid), float(safe_cap)))
    return float(round(bid, 2))
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

    supply = day_context['supply']
    day = day_context['day']
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
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    max_prev_bid = 0.0
    desperate_threat = 0.0
    rich_high = 0

    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
            if float(pbid) > max_prev_bid:
                max_prev_bid = float(pbid)
        if opp.get('budget', 0) >= 120:
            rich_high += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_threat = max(desperate_threat, max(float(pbid) if pbid is not None else 0.0, DAILY_SALARY * 0.85))

    capacity = supply / float(WATER_REQ)
    tight_supply = capacity < (len(alive_opps) + 1)
    very_tight = capacity < len(alive_opps)

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
    if very_tight:
        urgency += 2
    elif tight_supply:
        urgency += 1

    if max_prev_bid <= 0:
        if urgency >= 4:
            bid = DAILY_SALARY * 0.95
        elif urgency >= 2:
            bid = DAILY_SALARY * 0.72
        else:
            bid = DAILY_SALARY * 0.45
        return float(max(0.0, min(budget, bid)))

    if urgency >= 5:
        target = max(max_prev_bid + 2.5, desperate_threat + 1.5, DAILY_SALARY * 1.95)
    elif urgency >= 3:
        target = max(max_prev_bid + 1.6, desperate_threat + 1.0, DAILY_SALARY * 1.45)
    elif urgency >= 1:
        target = max(max_prev_bid + 0.8, DAILY_SALARY * 1.0)
    else:
        if max_prev_bid >= DAILY_SALARY * 1.9 and hp >= 7 and no_water == 0 and not very_tight:
            target = DAILY_SALARY * 0.38
        elif max_prev_bid >= DAILY_SALARY * 1.6 and hp >= 6 and no_water == 0:
            target = DAILY_SALARY * 0.55
        else:
            target = max_prev_bid * 0.72

    if rich_high >= 2 and tight_supply and urgency >= 2:
        target += 2.0

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0 and urgency <= 2:
        soft_cap = min(soft_cap, budget / 2.0 + DAILY_SALARY * 0.5)
    elif reserve_days > 0 and urgency <= 4:
        soft_cap = min(soft_cap, budget * 0.72 + DAILY_SALARY * 0.5)

    hard_cap = budget
    bid = min(target, soft_cap, hard_cap)

    if hp <= 2 or no_water >= 2:
        bid = min(hard_cap, max(bid, min(hard_cap, max_prev_bid + 2.0, DAILY_SALARY * 1.7)))

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
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 120 and opp.get('budget', 0) >= 120:
                    rich_aggressive += 1

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

    if tight_supply:
        urgency += 2
    elif not loose_supply:
        urgency += 1

    if desperate_count >= 2:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        target = max(95.0, highest_prev + 6.0)
    elif urgency >= 4:
        target = max(62.0, avg_prev + 4.0, highest_prev * 0.72)
    elif urgency >= 2:
        target = max(34.0, avg_prev * 0.45 + 8.0)
    else:
        target = 16.0 if loose_supply else 22.0

    if rich_aggressive >= 2 and hp > 4 and no_water_days == 0:
        target *= 0.72
    elif rich_aggressive >= 1 and hp > 5 and loose_supply:
        target *= 0.82

    reserve_days = max(0, 10 - day)
    soft_cap = budget / max(1, reserve_days)
    if urgency <= 2:
        cap = max(22.0, soft_cap * 0.9)
    elif urgency <= 4:
        cap = max(45.0, soft_cap * 1.35)
    else:
        cap = max(70.0, soft_cap * 2.4)

    bid = min(target, cap, budget)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 105.0, highest_prev + 3.0))
    elif hp <= 4 or no_water_days >= 1:
        bid = min(budget, max(bid, 72.0))

    if budget < 25:
        bid = budget

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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if len(alive) == 0:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    cindy_prev = None
    urgent_opps = 0
    rich_opps = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if oid == 'Cindy' and bid is not None:
            cindy_prev = float(bid)
        if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0)) <= 3:
            urgent_opps += 1
        if float(opp.get('budget', 0)) >= DAILY_SALARY * 6:
            rich_opps += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.6
    elif hp <= 6:
        danger += 0.25
    danger += min(0.8, no_water_days * 0.35)

    base = DAILY_SALARY * (0.34 + 0.22 * scarcity + 0.28 * danger)

    if cindy_prev is not None:
        if danger >= 0.9 or (scarcity >= 0.6 and hp <= 5):
            target = cindy_prev + 2.0
            base = max(base, target)
        elif cindy_prev >= 120:
            base = min(base, DAILY_SALARY * 0.52)
        elif cindy_prev >= 95:
            base = max(base, DAILY_SALARY * 0.58)

    if highest_prev > 0:
        if highest_prev <= 70:
            base = max(base, highest_prev + 1.25)
        elif highest_prev >= 115 and danger < 0.9:
            base = min(base, DAILY_SALARY * 0.5)
        elif danger >= 0.9:
            base = max(base, highest_prev + 1.5)
        else:
            base = max(base, avg_prev * 0.72)

    if urgent_opps >= 2 and danger < 0.9:
        base *= 0.9
    if rich_opps >= 2 and scarcity >= 0.5:
        base *= 1.08

    if day >= 8:
        base *= 1.08
    if day >= 9 and hp <= 5:
        base *= 1.15

    reserve = 0.0
    days_left = max(0, 10 - day)
    if days_left > 0:
        reserve = min(budget * 0.55, days_left * DAILY_SALARY * 0.38)

    cap = budget - reserve
    if danger >= 0.9:
        cap = budget
    elif cap < DAILY_SALARY * 0.25:
        cap = min(budget, DAILY_SALARY * 0.45)

    bid = min(base, cap, budget)

    if danger >= 1.2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.95, highest_prev + 2.0 if highest_prev > 0 else 0.0))
    elif hp <= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.88))

    min_bid = 1.0 if budget >= 1.0 else budget
    if bid < min_bid:
        bid = min_bid

    if bid > budget:
        bid = budget
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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_opp_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, 18.0))

    alive_count = len(alive_opps) + 1
    expected_share = supply / float(alive_count)
    scarcity = expected_share < WATER_REQ

    max_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else max_prev

    if hp <= 2 or no_water >= 2:
        bid = max(0.92 * DAILY_SALARY, urgent_prev + 3.0)
    elif hp <= 4 or no_water >= 1:
        if scarcity:
            bid = max(0.78 * DAILY_SALARY, urgent_prev + 2.0)
        else:
            bid = max(0.58 * DAILY_SALARY, 0.55 * max_prev)
    else:
        if scarcity:
            if max_prev >= 130:
                bid = 0.44 * DAILY_SALARY
            elif max_prev >= 90:
                bid = min(0.74 * DAILY_SALARY, max_prev + 1.5)
            else:
                bid = 0.61 * DAILY_SALARY
        else:
            if max_prev >= 120:
                bid = 0.26 * DAILY_SALARY
            elif max_prev >= 80:
                bid = 0.38 * DAILY_SALARY
            else:
                bid = 0.48 * DAILY_SALARY

    if day >= 8 and hp >= 6 and budget < 120:
        bid *= 0.82

    if budget < 70:
        bid = min(bid, budget * 0.78)
    elif budget < 140:
        bid = min(bid, budget * 0.68)

    if hp >= 7 and no_water == 0 and not scarcity:
        bid = min(bid, 32.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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

    alive_opponents = []
    sane_prev_bids = []
    all_prev_bids = []
    urgent_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                all_prev_bids.append(bid)
                if bid <= 100:
                    sane_prev_bids.append(bid)

    if not alive_opponents:
        return max(0.0, min(budget, 8.0))

    highest_sane = max(sane_prev_bids) if sane_prev_bids else 0.0
    highest_any = max(all_prev_bids) if all_prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 3
    elif supply <= 19:
        scarcity = 2
    elif supply <= 22:
        scarcity = 1

    my_urgency = 0
    if hp <= 2 or no_water_days >= 2:
        my_urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        my_urgency = 2
    elif hp <= 6:
        my_urgency = 1

    if my_urgency >= 3:
        target = max(72.0, highest_sane + 6.0)
        if highest_any > 120:
            target = max(target, 88.0)
    elif scarcity >= 3:
        target = max(64.0, highest_sane + 3.0)
    elif scarcity == 2:
        target = max(56.0, highest_sane + 2.0)
    elif scarcity == 1:
        target = max(42.0, highest_sane + 1.0)
    else:
        target = 24.0

    if urgent_opponents >= 2 and scarcity >= 2:
        target += 4.0
    elif urgent_opponents == 0 and hp >= 7 and no_water_days == 0 and supply >= 21:
        target -= 8.0

    if day >= 8 and budget > 200 and my_urgency >= 2:
        target += 5.0

    max_safe = budget
    if hp > 4 and no_water_days == 0:
        max_safe = min(max_safe, DAILY_SALARY * 1.05)
    else:
        max_safe = min(max_safe, DAILY_SALARY * 1.4)

    bid = min(max_safe, target)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

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
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    aggressive_bids = []
    weak_count = 0
    urgent_opp = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= DAILY_SALARY * 0.85:
                aggressive_bids.append(float(bid))
            if bid <= DAILY_SALARY * 0.45:
                weak_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = supply < WATER_REQ * (len(alive) + 1)
    very_tight = supply <= WATER_REQ * max(1, len(alive))
    my_urgent = hp <= 3 or no_water >= 2
    my_caution = hp <= 5 or no_water >= 1

    if my_urgent:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.5)
    elif very_tight:
        if aggressive_bids:
            target = max(DAILY_SALARY * 0.82, highest_prev + 1.6)
        else:
            target = max(DAILY_SALARY * 0.68, avg_prev + 2.0)
    elif scarcity:
        if urgent_opp >= 2:
            target = max(DAILY_SALARY * 0.72, highest_prev + 1.2)
        else:
            target = max(DAILY_SALARY * 0.58, avg_prev + 1.0)
    else:
        if weak_count >= len(prev_bids) / 2.0:
            target = DAILY_SALARY * 0.34
        else:
            target = max(DAILY_SALARY * 0.4, avg_prev * 0.78)

    if hp >= 8 and no_water == 0 and not my_caution and not very_tight:
        target *= 0.92
    if day >= 8 and budget < DAILY_SALARY * 2.2:
        target *= 0.9
    if budget < DAILY_SALARY * 1.2 and not my_urgent:
        target = min(target, DAILY_SALARY * 0.62)

    floor_bid = 0.0
    if my_urgent:
        floor_bid = DAILY_SALARY * 0.78
    elif my_caution and scarcity:
        floor_bid = DAILY_SALARY * 0.56
    elif scarcity:
        floor_bid = DAILY_SALARY * 0.44
    else:
        floor_bid = DAILY_SALARY * 0.28

    bid = max(target, floor_bid)
    bid = min(bid, budget)
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
    day = day_context['day']
    supply = day_context['supply']
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
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    aggressive_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0.0)
            prev_bids.append(bid)
            if bid >= DAILY_SALARY * 1.5:
                aggressive_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    cindy_like_pressure = len(aggressive_bids) >= 1

    remaining_days = max(1, 10 - day + 1)
    reserve_target = DAILY_SALARY * 0.45 * remaining_days
    spendable = max(0.0, budget - reserve_target)

    if hp <= 2 or no_water_days >= 2:
        if cindy_like_pressure:
            bid = min(budget, max(DAILY_SALARY * 1.65, highest_prev * 0.92))
        else:
            bid = min(budget, max(DAILY_SALARY * 0.95, highest_prev + 3.0))
        return float(max(0.0, bid))

    if hp <= 4 or no_water_days >= 1:
        if cindy_like_pressure:
            bid = max(DAILY_SALARY * 1.2, min(budget, highest_prev * 0.82))
        else:
            bid = max(DAILY_SALARY * 0.7, highest_prev + 2.0)
        bid = min(budget, bid)
        return float(max(0.0, bid))

    if supply >= 22:
        base = DAILY_SALARY * 0.18
    elif supply >= 19:
        base = DAILY_SALARY * 0.28
    else:
        base = DAILY_SALARY * 0.4

    if cindy_like_pressure:
        base *= 0.75

    if spendable > 0:
        bid = min(budget, max(base, min(spendable * 0.35, DAILY_SALARY * 0.6)))
    else:
        bid = min(budget, base)

    if avg_prev > 0 and avg_prev < DAILY_SALARY:
        bid = max(bid, min(budget, avg_prev + 1.5))

    return float(max(0.0, bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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

    alive_opponents = []
    prev_bids = []
    strong_prev_bids = []
    needy_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('budget', 0) > DAILY_SALARY * 2:
                    strong_prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    high_supply = supply >= 22
    low_supply = supply <= 17

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strong_highest_prev = max(strong_prev_bids) if strong_prev_bids else highest_prev

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

    if low_supply:
        danger += 2
    elif supply <= 19:
        danger += 1

    if needy_count >= 2:
        danger += 1

    if day >= 8:
        danger += 1

    if danger >= 6:
        target = max(DAILY_SALARY * 1.45, strong_highest_prev + 2.5)
    elif danger >= 4:
        target = max(DAILY_SALARY * 1.1, strong_highest_prev * 0.98 + 1.5)
    elif danger >= 2:
        if high_supply:
            target = DAILY_SALARY * 0.42
        else:
            target = max(DAILY_SALARY * 0.72, highest_prev * 0.72)
    else:
        if high_supply:
            target = DAILY_SALARY * 0.22
        else:
            target = DAILY_SALARY * 0.34

    if highest_prev >= 150 and danger <= 2:
        target = min(target, DAILY_SALARY * 0.3)

    if budget < DAILY_SALARY:
        target = min(target, budget * 0.92)

    min_survival = 0.0
    if hp <= 2 or no_water_days >= 2:
        min_survival = DAILY_SALARY * 0.9
    elif hp <= 4 or no_water_days >= 1:
        min_survival = DAILY_SALARY * 0.65

    bid = max(target, min_survival)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""
