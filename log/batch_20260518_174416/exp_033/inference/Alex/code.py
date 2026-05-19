# ============================================================
# Experiment: exp_033
# Agent: Alex
# Source: exp_033
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 45)
        return min(budget, 18)

    highest_prev_bid = 0
    desperate_count = 0
    rich_pressure = 0

    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_pressure += 1
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is not None and prev_bid > highest_prev_bid:
            highest_prev_bid = prev_bid

    my_urgent = (hp <= 2) or (no_water_days >= 1)
    tight_supply = supply <= 18
    ample_supply = supply >= 22

    if my_urgent:
        target = max(58, highest_prev_bid + 2)
        if tight_supply:
            target = max(target, 64)
        return min(budget, target)

    if ample_supply and desperate_count == 0:
        return min(budget, 16)

    if tight_supply:
        target = max(36, highest_prev_bid + 1.5)
        if desperate_count >= 2:
            target = max(target, 48)
        if rich_pressure >= 2:
            target = max(target, 44)
        return min(budget, target)

    target = max(24, highest_prev_bid * 0.78)
    if desperate_count >= 1:
        target = max(target, 30)
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    danger_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                danger_opp += 1
            if opp.get('budget', 0) >= budget:
                rich_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 16.0
    ample_supply = supply >= 22.0
    critical_self = hp <= 2 or no_water_days >= 2
    stressed_self = hp <= 4 or no_water_days >= 1

    if critical_self:
        bid = max(62.0, highest_prev + 3.0)
        if tight_supply:
            bid = max(bid, 78.0)
        return float(min(budget, bid))

    if stressed_self:
        if highest_prev >= 95.0:
            bid = 58.0 if hp > 3 and no_water_days == 0 else 74.0
        else:
            bid = max(46.0, min(72.0, highest_prev + 2.0))
        if tight_supply:
            bid += 8.0
        return float(min(budget, bid))

    if highest_prev >= 120.0:
        bid = 16.0 if ample_supply else 22.0
    elif highest_prev >= 90.0:
        bid = 20.0 if ample_supply else 28.0
    elif highest_prev >= 60.0:
        bid = 26.0 if ample_supply else 34.0
    else:
        bid = 24.0 if ample_supply else 31.0

    if danger_opp >= 2 and not tight_supply:
        bid -= 4.0
    if rich_opp >= 2 and tight_supply:
        bid += 6.0
    if avg_prev < 20.0 and hp >= 6:
        bid = min(bid, 24.0)

    if day >= 8 and hp >= 6 and budget < 140:
        bid = min(bid, 22.0)

    bid = max(0.0, bid)
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        if hp <= 2 or no_water >= 2:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    pressure_bids = []
    cindy_bid = None
    active_count = 0
    desperate_others = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            pressure_bids.append(float(bid))
            if oid == 'Cindy':
                cindy_bid = float(bid)
        if opp.get('budget', 0) > 0:
            active_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_others += 1

    highest_prev = max(pressure_bids) if pressure_bids else 0.0
    median_prev = 0.0
    if pressure_bids:
        s = sorted(pressure_bids)
        median_prev = s[int(len(s) // 2)]

    scarcity = (25.0 - float(supply)) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = hp <= 2 or no_water >= 2
    semi_urgent = hp <= 4 or no_water >= 1

    if cindy_bid is None:
        cindy_bid = max(highest_prev, DAILY_SALARY * 0.75)

    if urgent:
        target = max(DAILY_SALARY * 0.95, cindy_bid + 2.0)
        if desperate_others >= 2:
            target += 4.0
        return float(min(budget, target))

    if semi_urgent:
        if supply >= 22:
            target = max(DAILY_SALARY * 0.52, median_prev * 0.55)
        elif supply >= 18:
            target = max(DAILY_SALARY * 0.72, cindy_bid * 0.82)
        else:
            target = max(DAILY_SALARY * 0.88, cindy_bid + 1.0)
        return float(min(budget, target))

    if supply >= 22:
        target = DAILY_SALARY * 0.18
    elif supply >= 20:
        target = DAILY_SALARY * 0.28
    elif supply >= 18:
        target = DAILY_SALARY * 0.42
    else:
        target = DAILY_SALARY * 0.58

    if active_count <= 1:
        target *= 0.75
    if highest_prev >= DAILY_SALARY * 1.5:
        target *= 0.8
    if day >= 8 and hp >= 6 and no_water == 0:
        target *= 0.9

    floor_bid = 0.0
    if no_water >= 1:
        floor_bid = DAILY_SALARY * 0.22

    bid = max(target, floor_bid)
    if scarcity > 0.7 and hp <= 5:
        bid = max(bid, DAILY_SALARY * 0.7)

    return float(min(budget, bid))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    yesterday_bids = []
    aggressive_count = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(bid)
                if bid >= 110:
                    aggressive_count += 1

    if not alive_opponents:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    emergency = hp <= 3 or no_water_days >= 2
    caution = hp <= 5 or no_water_days >= 1

    if emergency:
        if tight_supply:
            bid = max(118.0, highest_prev + 6.0)
        else:
            bid = max(95.0, avg_prev + 4.0)
        return max(0.0, min(budget, bid))

    if tight_supply:
        if highest_prev >= 150:
            bid = 72.0 if hp >= 7 else 98.0
        elif highest_prev >= 110:
            bid = highest_prev + 3.0
        else:
            bid = 88.0 if aggressive_count >= 2 else 76.0
    elif loose_supply:
        if caution:
            bid = max(48.0, avg_prev * 0.45)
        else:
            bid = 22.0 if aggressive_count >= 1 else 16.0
    else:
        if caution:
            if highest_prev >= 120:
                bid = 78.0
            else:
                bid = max(58.0, avg_prev * 0.6)
        else:
            if highest_prev >= 140:
                bid = 38.0
            elif highest_prev >= 100:
                bid = 54.0
            else:
                bid = 44.0

    if budget < 60:
        bid = min(bid, max(12.0, budget * 0.75))
    elif budget < 120:
        bid = min(bid, budget * 0.85)

    return max(0.0, min(budget, bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_aggressive = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 110 and opp.get('budget', 0) >= 100:
                    rich_aggressive += 1

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if supply <= 16:
        scarcity = 1.0
    elif supply <= 19:
        scarcity = 0.7
    else:
        scarcity = 0.35

    emergency = 0
    if hp <= 2 or no_water >= 2:
        emergency = 2
    elif hp <= 4 or no_water >= 1:
        emergency = 1

    if emergency == 2:
        bid = max(63.0, highest_prev * 0.72 + 6.0)
        if supply <= 17:
            bid = max(bid, 78.0)
        return min(budget, bid)

    if emergency == 1:
        bid = 34.0 + scarcity * 18.0
        if highest_prev > 0:
            bid = max(bid, min(highest_prev * 0.48 + 3.0, 82.0))
        return min(budget, bid)

    if rich_aggressive >= 2 and supply >= 20:
        return min(budget, 8.0)

    if highest_prev >= 150:
        if supply >= 21:
            return min(budget, 6.0)
        bid = 18.0 + scarcity * 14.0
        return min(budget, bid)

    if highest_prev >= 110:
        if supply >= 20:
            return min(budget, 10.0)
        bid = 22.0 + scarcity * 18.0
        return min(budget, bid)

    if highest_prev >= 70:
        bid = max(26.0 + scarcity * 16.0, avg_prev * 0.55 + 2.0)
        return min(budget, bid)

    bid = 24.0 + scarcity * 14.0
    if supply >= 22:
        bid -= 6.0
    return min(budget, max(5.0, bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    yesterday_bids = []
    urgent_count = 0
    rich_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 100:
                rich_count += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    danger = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    base = 22.0
    if day <= 2:
        base = 18.0
    if medium_supply:
        base += 8.0
    if tight_supply:
        base += 10.0
    if rich_count >= 2:
        base += 6.0
    if urgent_count >= 2:
        base += 8.0

    if highest_prev >= 130:
        pressure_bid = 118.0
    elif highest_prev >= 120:
        pressure_bid = 110.0
    elif highest_prev >= 100:
        pressure_bid = highest_prev + 2.0
    elif highest_prev > 0:
        pressure_bid = max(60.0, avg_prev + 3.0)
    else:
        pressure_bid = 55.0

    if critical:
        bid = max(base + 20.0, pressure_bid)
    elif danger:
        bid = max(base + 10.0, min(pressure_bid, 105.0))
    else:
        if tight_supply:
            bid = max(base, min(pressure_bid, 95.0))
        elif medium_supply:
            bid = max(base, min(avg_prev * 0.7 if avg_prev > 0 else 52.0, 82.0))
        else:
            bid = min(base, 38.0)

    if budget < 90:
        bid = min(bid, budget * 0.72)
    if budget < 50:
        bid = min(bid, budget * 0.85)

    if hp >= 7 and no_water == 0 and not tight_supply and highest_prev >= 120:
        bid = min(bid, 30.0)

    bid = max(0.0, min(float(bid), float(budget)))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 3 or no_water_days >= 1:
            safe_bid = min(budget, DAILY_SALARY * 0.6)
        return float(max(0.0, safe_bid))

    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 300:
            rich_opp_count += 1
        if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

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

    if no_water_days >= 2:
        danger += 1.0
    elif no_water_days >= 1:
        danger += 0.5

    if day >= 8:
        danger += 0.2

    if supply >= 22 and danger < 0.8:
        bid = DAILY_SALARY * 0.18
    elif supply >= 19 and danger < 0.8:
        bid = DAILY_SALARY * 0.28
    else:
        bid = DAILY_SALARY * (0.35 + 0.25 * scarcity)

    if highest_prev >= 100:
        if danger >= 1.2:
            bid = max(bid, highest_prev + 2.0)
        elif danger >= 0.7 and supply <= 17:
            bid = max(bid, highest_prev + 1.0)
        else:
            bid = min(bid, DAILY_SALARY * 0.32)
    elif highest_prev >= 85:
        if danger >= 1.0:
            bid = max(bid, highest_prev + 1.5)
        else:
            bid = min(max(bid, avg_prev * 0.55), DAILY_SALARY * 0.48)
    elif highest_prev > 0:
        if danger >= 0.8:
            bid = max(bid, highest_prev + 1.0)
        else:
            bid = max(bid, avg_prev * 0.75)

    if urgent_opp_count >= 2 and danger < 1.0:
        bid = min(bid, DAILY_SALARY * 0.3)

    if rich_opp_count >= 2 and supply <= 17 and danger >= 1.0:
        bid = max(bid, highest_prev + 2.5)

    reserve_target = DAILY_SALARY * max(0, 10 - int(day)) * 0.22
    max_affordable = max(0.0, budget - reserve_target)
    if danger >= 1.4:
        max_affordable = budget
    elif max_affordable < DAILY_SALARY * 0.2:
        max_affordable = min(budget, DAILY_SALARY * 0.2)

    bid = min(bid, max_affordable, budget)

    if danger >= 1.6:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))
    elif danger >= 1.1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.72))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    day = day_context['day']
    supply = day_context['supply']
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
        base = DAILY_SALARY * 0.22
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_count = 0
    rich_aggressive = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_count += 1
        if opp.get('budget', 0) > budget and pbid is not None and pbid >= DAILY_SALARY * 0.9:
            rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 1.0 - ((float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY))
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

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
        danger += 1

    days_left = 10 - int(day) + 1
    reserve_target = max(0.0, days_left * DAILY_SALARY * 0.28)
    spendable = max(0.0, budget - reserve_target)

    base = DAILY_SALARY * (0.22 + 0.28 * scarcity)

    if highest_prev > 0:
        if highest_prev >= 120:
            base = min(base, DAILY_SALARY * 0.42)
        elif highest_prev >= 80:
            base = max(base, min(DAILY_SALARY * 0.62, avg_prev * 0.72))
        else:
            base = max(base, highest_prev + 2.0)

    if urgent_count >= 2:
        base += 8.0
    elif urgent_count == 1:
        base += 4.0

    if rich_aggressive >= 2 and danger == 0:
        base *= 0.82

    if danger >= 5:
        bid = max(base, highest_prev + 4.0, DAILY_SALARY * 0.95)
    elif danger >= 3:
        bid = max(base, highest_prev + 2.0, DAILY_SALARY * 0.72)
    elif danger >= 1:
        bid = max(base, DAILY_SALARY * 0.48)
    else:
        bid = base

    if float(supply) >= 23.0 and danger == 0:
        bid *= 0.72
    elif float(supply) >= 20.0 and danger <= 1:
        bid *= 0.84
    elif float(supply) <= 16.0:
        bid *= 1.12

    if int(day) >= 8:
        if hp <= 4 or no_water_days >= 1:
            bid = max(bid, DAILY_SALARY * 0.85)
        else:
            bid *= 0.95

    cap = budget
    if spendable > 0:
        cap = min(budget, spendable + DAILY_SALARY * 0.65)
    bid = min(bid, cap)
    bid = max(0.0, min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        return float(min(budget, 20.0))

    units = int(supply // WATER_REQ)
    total_alive = 1 + len(alive_opps)
    tight = units < total_alive
    very_tight = units <= 1

    threat_bid = 0.0
    cindy_bid = 0.0
    eric_bid = 0.0
    cindy_budget = None
    eric_budget = None

    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        pbid = 0.0
        if prev and prev.get('bid') is not None:
            pbid = float(prev.get('bid', 0.0))
        if pbid > threat_bid:
            threat_bid = pbid
        req = opp.get('water_requirement', WATER_REQ)
        sal = opp.get('daily_salary', DAILY_SALARY)
        if req == 13 and sal == 70:
            if pbid > 300:
                cindy_bid = pbid
                cindy_budget = opp.get('budget', 0.0)
            elif pbid >= 100:
                eric_bid = pbid
                eric_budget = opp.get('budget', 0.0)

    if hp <= 2 or no_water_days >= 2:
        emergency = max(135.0, eric_bid + 3.0, threat_bid + 2.0)
        return float(min(budget, emergency))

    if very_tight:
        if eric_bid > 0:
            target = eric_bid + 2.0
        else:
            target = max(110.0, threat_bid + 2.0)
        if cindy_budget is not None and cindy_budget < 80:
            target = max(110.0, eric_bid + 2.0)
        return float(min(budget, target))

    if tight:
        if hp >= 7 and no_water_days == 0:
            conserve = 18.0
            if cindy_bid > 250 and cindy_budget is not None and cindy_budget < 100:
                conserve = 12.0
            return float(min(budget, conserve))
        target = max(95.0, eric_bid + 1.5)
        return float(min(budget, target))

    if hp <= 4 or no_water_days == 1:
        safe_bid = max(72.0, min(95.0, threat_bid * 0.7 if threat_bid > 0 else 72.0))
        return float(min(budget, safe_bid))

    low = 8.0
    if day >= 8:
        low = 20.0
    if cindy_bid > 250 and cindy_budget is not None and cindy_budget < 50:
        low = 5.0
    return float(min(budget, low))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive.append(opp)
        if opp.get('budget', 0) >= 120:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    if not alive:
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    competitors = len(alive) + 1
    scarcity = competitors - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    must_win = False
    if hp <= 2:
        must_win = True
    if no_water_days >= 1 and hp <= 4:
        must_win = True
    if day >= 8 and hp <= 4:
        must_win = True

    if must_win:
        target = max(72.0, min(0.92 * budget, highest_prev + 6.0 if highest_prev > 0 else 78.0))
        return float(min(budget, target))

    if slots >= competitors:
        base = 8.0 + 2.0 * rich_opp
        if hp <= 4 or no_water_days >= 1:
            base += 10.0
        return float(min(budget, base))

    if scarcity >= 3:
        if hp >= 7 and no_water_days == 0:
            target = 18.0 + 4.0 * urgent_opp
        else:
            target = 58.0 + 4.0 * urgent_opp
            if highest_prev > 0:
                target = max(target, min(highest_prev + 2.0, 88.0))
        return float(min(budget, target))

    target = 32.0
    if avg_prev > 0:
        if highest_prev >= 150:
            target = 42.0 if hp >= 6 and no_water_days == 0 else 76.0
        elif highest_prev >= 100:
            target = 55.0 if hp <= 5 or no_water_days >= 1 else 38.0
        else:
            target = max(34.0, min(highest_prev + 2.0, 72.0))

    if hp <= 5:
        target += 12.0
    if no_water_days >= 1:
        target += 18.0
    if supply <= 16:
        target += 10.0
    elif supply >= 23:
        target -= 6.0

    reserve_floor = max(0.0, budget - DAILY_SALARY * max(0, 10 - day))
    if reserve_floor > 0:
        target = min(target, budget - reserve_floor * 0.35)

    target = max(6.0, target)
    return float(min(budget, target))
"""
