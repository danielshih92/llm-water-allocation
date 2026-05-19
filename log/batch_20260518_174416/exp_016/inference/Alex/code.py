# ============================================================
# Experiment: exp_016
# Agent: Alex
# Source: exp_016
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
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return max(0, min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    need = 0
    if hp <= 2 or no_water_days >= 2:
        need = 3
    elif hp <= 4 or no_water_days >= 1:
        need = 2
    elif hp <= 6:
        need = 1

    base = 28.0
    if scarcity == 2:
        base = 52.0
    elif scarcity == 1:
        base = 40.0
    else:
        base = 26.0

    if need == 3:
        base = max(base, 64.0)
    elif need == 2:
        base = max(base, 54.0)
    elif need == 1:
        base = max(base, 38.0)

    if max_prev > 0:
        if scarcity == 2 or need >= 2:
            target = max(base, min(68.0, max_prev + 2.0))
        else:
            target = max(base, min(55.0, avg_prev + 1.0))
    else:
        target = base

    target += min(6.0, urgent_opp * 1.5)
    if rich_opp >= 2 and scarcity >= 1:
        target += 3.0

    if supply >= 23 and need == 0:
        target = min(target, 24.0)
    elif supply >= 21 and need <= 1:
        target = min(target, 30.0)

    if budget < 25:
        target = min(target, budget)
    elif budget < 50:
        target = min(target, budget * 0.85)
    else:
        target = min(target, budget * 0.7 + 8.0)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_threats = 0
    desperate_threats = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_threats += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_threats += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive:
        return max(0.0, min(budget, 5.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    emergency = hp <= 2 or no_water >= 1
    fragile = hp <= 4

    if emergency:
        bid = max(0.95 * DAILY_SALARY, max_prev + 2.0)
        if supply <= 17:
            bid += 8.0
        return max(0.0, min(budget, bid))

    if fragile:
        bid = 0.68 * DAILY_SALARY + 0.18 * max_prev + 10.0 * scarcity
        if rich_threats >= 2:
            bid += 6.0
        return max(0.0, min(budget, bid))

    base = 0.34 * DAILY_SALARY + 0.10 * avg_prev + 8.0 * scarcity
    if supply >= 22:
        base -= 6.0
    elif supply <= 17:
        base += 8.0

    if max_prev >= 140:
        base = min(base, 0.42 * DAILY_SALARY)
    elif max_prev >= 90:
        base = max(base, 0.38 * DAILY_SALARY)

    if desperate_threats >= 2:
        base += 5.0

    if day >= 8 and hp >= 6 and no_water == 0:
        base -= 4.0

    reserve_floor = DAILY_SALARY * max(0, 10 - day) * 0.18
    if budget < reserve_floor:
        base *= 0.8

    return max(0.0, min(budget, base))
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
    prev_bids = []
    bob_bid = None
    cindy_bid = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if agent_id == 'Bob':
                    bob_bid = bid
                elif agent_id == 'Cindy':
                    cindy_bid = bid

    if not alive:
        return max(0.0, min(budget, 5.0))

    units = supply / float(WATER_REQ)
    scarcity = units < (len(alive) + 1)
    very_tight = units < len(alive)

    ref_bid = 0.0
    if bob_bid is not None:
        ref_bid = max(ref_bid, bob_bid)
    elif prev_bids:
        ref_bid = max(prev_bids)

    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        bid = max(62.0, ref_bid + 3.0)
    elif urgent:
        if scarcity:
            bid = max(54.0, ref_bid + 2.0)
        else:
            bid = 36.0
    else:
        if very_tight:
            bid = max(58.0, ref_bid + 2.0)
        elif scarcity:
            bid = max(44.0, min(60.0, ref_bid + 1.5))
        else:
            bid = 18.0

    if cindy_bid is not None and cindy_bid > 140 and not urgent and not very_tight:
        bid = min(bid, 22.0)

    if day >= 8 and hp >= 5 and budget < 140 and not critical:
        bid = min(bid, 28.0)

    if budget < bid:
        bid = budget

    if budget <= 0:
        return 0.0
    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((oid, opp))

    if not alive_opps:
        return float(min(budget, 20.0 if hp > 3 else 45.0))

    prev_bids = []
    cindy_prev = None
    dangerous_prev = 0.0
    rich_alive = 0
    urgent_opp_count = 0

    for oid, opp in alive_opps:
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_alive += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            b = float(bid)
            prev_bids.append(b)
            if b > dangerous_prev:
                dangerous_prev = b
            if oid == 'Cindy':
                cindy_prev = b

    slots = max(1.0, supply / float(WATER_REQ))
    scarce = supply <= 16.5
    ample = supply >= 23.0

    if cindy_prev is None:
        cindy_prev = 69.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(88.0, cindy_prev + 4.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(72.0, cindy_prev + 2.0 if scarce else cindy_prev - 4.0)
    else:
        if ample and urgent_opp_count == 0:
            bid = 26.0
        elif ample:
            bid = 34.0
        elif scarce:
            bid = max(58.0, cindy_prev - 6.0)
        else:
            bid = max(44.0, min(66.0, cindy_prev - 10.0))

    if rich_alive >= 2:
        bid += 6.0
    elif rich_alive == 0 and hp > 4 and no_water_days == 0:
        bid -= 4.0

    if dangerous_prev >= 100.0 and hp > 4 and no_water_days == 0:
        bid = min(bid, 38.0)

    if day >= 8:
        bid += 8.0
    if day >= 9 and hp <= 4:
        bid += 10.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if hp > 4 and no_water_days == 0 and days_left >= 2:
        reserve_floor = DAILY_SALARY * 1.2
    max_spend = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water_days >= 1:
        max_spend = budget

    bid = min(bid, max_spend if max_spend > 0 else budget)
    bid = max(0.0, min(bid, budget))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    alive_opps = []
    prev_bids = []
    danger_bids = []
    affordable_pressures = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                    danger_bids.append(bid)
                if bid <= budget * 1.2:
                    affordable_pressures.append(bid)

    if not alive_opps:
        return float(min(budget, 18.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    base = 20.0 + 18.0 * scarcity

    if hp >= 8 and no_water_days == 0:
        base -= 4.0
    if hp <= 5:
        base += 18.0
    if hp <= 3:
        base += 28.0
    if no_water_days >= 1:
        base += 16.0
    if no_water_days >= 2:
        base += 28.0

    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        practical = max(40.0, avg_prev)
        if danger_bids:
            practical = max(practical, max(danger_bids) + 2.0)
        elif affordable_pressures:
            practical = max(practical, max(affordable_pressures) + 1.5)
        else:
            practical = max(practical, min(max_prev * 0.72, budget * 0.55))

        if max_prev >= 150 and hp >= 7 and no_water_days == 0 and supply >= 20:
            base = min(base, 24.0)
        else:
            base = max(base, practical * (0.72 + 0.18 * scarcity))

    reserve_days = max(0, 10 - day)
    soft_cap = budget / max(1, reserve_days)
    if hp >= 7 and no_water_days == 0:
        cap = max(22.0, soft_cap * 0.95)
    elif hp <= 4 or no_water_days >= 1:
        cap = max(40.0, soft_cap * 2.2)
    else:
        cap = max(30.0, soft_cap * 1.45)

    if hp <= 2 or no_water_days >= 2:
        cap = max(cap, budget)
        base = max(base, 0.82 * budget)

    bid = min(base, cap, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
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

    strongest_prev = 0.0
    pressure_bid = 0.0
    desperate_count = 0
    rich_count = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        prev_bid = 0.0
        if prev and prev.get('bid') is not None:
            prev_bid = float(prev.get('bid', 0.0))
        if prev_bid > strongest_prev:
            strongest_prev = prev_bid

        opp_hp = opp.get('hp', 0)
        opp_budget = opp.get('budget', 0.0)
        opp_nowater = opp.get('no_water_days', 0)
        opp_req = opp.get('water_requirement', WATER_REQ)
        opp_salary = opp.get('daily_salary', DAILY_SALARY)

        score = prev_bid
        if opp_hp <= 2 or opp_nowater >= 1:
            score += opp_salary * 0.35
            desperate_count += 1
        if opp_budget >= opp_salary * 1.5:
            score += opp_salary * 0.15
            rich_count += 1
        if opp_req <= supply:
            score += 2.0
        if score > pressure_bid:
            pressure_bid = score

    can_only_feed_one = supply < WATER_REQ * 2

    if hp <= 2 or no_water >= 1:
        base = max(DAILY_SALARY * 0.95, pressure_bid + 3.0)
    elif can_only_feed_one:
        base = max(DAILY_SALARY * 0.82, pressure_bid + 2.0)
    else:
        base = max(DAILY_SALARY * 0.28, min(DAILY_SALARY * 0.62, pressure_bid * 0.55 + 1.0))

    if strongest_prev > 150:
        if hp > 3 and no_water == 0 and not can_only_feed_one:
            base = min(base, DAILY_SALARY * 0.42)
        else:
            base = max(base, DAILY_SALARY * 0.88)

    if desperate_count >= 2 and can_only_feed_one:
        base = max(base, DAILY_SALARY * 0.92)

    if rich_count == 0 and hp > 3 and no_water == 0 and not can_only_feed_one:
        base = min(base, DAILY_SALARY * 0.38)

    if day >= 8:
        base += 6.0
    if day == 10:
        base += 8.0

    bid = min(float(budget), float(base))
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    danger_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                danger_count += 1
            if opp.get('budget', 0) > 700:
                rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if not alive:
        return min(budget, 18.0)

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 55.0
    max_prev = max(prev_bids) if prev_bids else 70.0

    total_players = len(alive) + 1
    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < total_players
    very_tight = expected_units <= max(1.2, total_players * 0.55)

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water >= 2:
        urgency += 4
    elif no_water >= 1:
        urgency += 2
    if day >= 8:
        urgency += 1

    pressure = 0
    if max_prev >= 120:
        pressure += 3
    elif max_prev >= 90:
        pressure += 2
    elif max_prev >= 65:
        pressure += 1
    pressure += min(2, danger_count)
    if rich_aggressive >= 2:
        pressure += 1

    if urgency >= 7:
        bid = max(95.0, avg_prev + 8.0)
        if very_tight:
            bid = max(bid, max_prev + 3.0)
    elif urgency >= 4:
        if scarcity:
            bid = max(72.0, avg_prev + 2.5)
        else:
            bid = 54.0 if pressure >= 2 else 42.0
    else:
        if very_tight:
            bid = 61.0 if pressure <= 2 else 74.0
        elif scarcity:
            bid = 44.0 if pressure >= 3 else 34.0
        else:
            bid = 18.0 if pressure >= 2 else 9.0

    if budget < DAILY_SALARY * 2 and urgency < 4:
        bid = min(bid, 28.0)
    if budget < DAILY_SALARY and urgency < 7:
        bid = min(bid, 22.0)

    if hp <= 1 or no_water >= 3:
        bid = max(bid, min(budget, max_prev + 5.0 if prev_bids else 85.0))

    if day == 1 and urgency == 0 and not very_tight:
        bid = min(bid, 20.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        base = DAILY_SALARY * 0.35
        if no_water_days >= 1 or hp <= 3:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    cindy_bid = None
    highest_prev = 0.0
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= 120:
            rich_opp += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            pbid = prev.get('bid')
            if pbid is not None:
                if pbid > highest_prev:
                    highest_prev = pbid
                if oid == 'Cindy':
                    cindy_bid = pbid

    slots = max(1, int(supply // WATER_REQ))
    tight = slots <= 1

    if cindy_bid is None:
        cindy_bid = 150.0 if day <= 3 else 120.0

    if no_water_days >= 2 or hp <= 2:
        bid = min(budget, max(0.92 * DAILY_SALARY, cindy_bid + 3.0, highest_prev + 2.0))
        return float(max(0.0, bid))

    if tight:
        if no_water_days >= 1 or hp <= 4:
            target = max(cindy_bid + 2.5, highest_prev + 1.5, 0.88 * DAILY_SALARY)
        else:
            if cindy_bid >= 180:
                target = DAILY_SALARY * 0.22
            else:
                target = max(DAILY_SALARY * 0.52, min(cindy_bid + 1.0, DAILY_SALARY * 0.86))
    else:
        if no_water_days >= 1:
            target = max(DAILY_SALARY * 0.6, highest_prev * 0.7)
        else:
            target = DAILY_SALARY * 0.28
            if rich_opp >= 2 and highest_prev > 100:
                target = DAILY_SALARY * 0.18
            elif urgent_opp >= 2:
                target = DAILY_SALARY * 0.4

    days_left = max(1, 10 - day + 1)
    reserve_floor = max(0.0, (days_left - 2) * DAILY_SALARY * 0.18)
    spend_cap = max(0.0, budget - reserve_floor)
    if hp >= 7 and no_water_days == 0 and not tight:
        spend_cap = min(spend_cap, DAILY_SALARY * 0.45)

    bid = min(target, budget)
    if spend_cap > 0:
        bid = min(bid, max(spend_cap, DAILY_SALARY * 0.12) if (no_water_days >= 1 or hp <= 4) else max(DAILY_SALARY * 0.12, spend_cap))
    else:
        bid = min(bid, DAILY_SALARY * 0.2 if (hp >= 5 and no_water_days == 0) else budget)

    min_pressure = 0.0
    if no_water_days >= 1 or hp <= 4:
        min_pressure = DAILY_SALARY * 0.45
    elif tight and cindy_bid < 170:
        min_pressure = DAILY_SALARY * 0.35

    bid = max(min_pressure, bid)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
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

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 500:
                rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply <= 17
    abundant = supply >= 22
    critical_me = hp <= 3 or no_water_days >= 1
    very_critical = hp <= 2 or no_water_days >= 2

    if very_critical:
        target = max(72.0, highest_prev + 3.0)
        if scarcity:
            target = max(target, 95.0)
        return min(budget, target)

    if critical_me:
        target = max(58.0, avg_prev + 4.0)
        if highest_prev >= 120:
            target = max(target, 82.0)
        if scarcity:
            target += 10.0
        return min(budget, target)

    if scarcity:
        if highest_prev >= 140:
            return min(budget, 28.0)
        target = max(46.0, avg_prev + 2.5)
        if desperate_count >= 2:
            target += 8.0
        return min(budget, target)

    if abundant:
        if highest_prev >= 120:
            return min(budget, 16.0)
        return min(budget, 22.0 + 2.0 * desperate_count)

    target = 32.0
    if highest_prev > 0:
        if highest_prev >= 130:
            target = 20.0
        elif highest_prev >= 90:
            target = 27.0
        else:
            target = max(32.0, avg_prev * 0.75)

    if rich_aggressive >= 2:
        target -= 4.0
    if day >= 8 and hp >= 6 and no_water_days == 0:
        target -= 3.0

    if target < 12.0:
        target = 12.0

    return min(budget, target)
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

    alive_opps = []
    prev_bids = []
    moderate_bids = []
    dangerous_bids = []
    eric_like_bid = None

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((oid, opp))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid <= 150:
                    moderate_bids.append(float(bid))
                if bid >= 80:
                    dangerous_bids.append(float(bid))
                if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
                    if eric_like_bid is None or float(bid) < eric_like_bid:
                        eric_like_bid = float(bid)

    if not alive_opps:
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    alive_count = len(alive_opps) + 1
    scarcity = alive_count > slots
    very_tight = slots <= 1

    if eric_like_bid is None:
        if moderate_bids:
            eric_like_bid = max(moderate_bids)
        elif prev_bids:
            eric_like_bid = min(max(prev_bids), 90.0)
        else:
            eric_like_bid = 45.0

    base = 24.0
    if scarcity:
        base = 48.0
    if very_tight:
        base = 58.0

    target = max(base, eric_like_bid + 2.5)

    if dangerous_bids and hp > 3 and no_water_days == 0:
        target = min(target, 52.0)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, eric_like_bid + 8.0, 72.0)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, eric_like_bid + 5.0, 60.0)

    if day >= 8:
        target += 6.0
    if day >= 9 and (hp <= 4 or scarcity):
        target += 8.0

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.6

    max_affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    bid = min(target, max_affordable if max_affordable > 0 else budget)

    if not scarcity and hp > 4 and no_water_days == 0:
        bid = min(bid, 36.0)

    if bid < 0:
        bid = 0.0
    if budget < 12 and (hp <= 2 or no_water_days >= 2):
        bid = budget

    return float(min(budget, max(0.0, bid)))
"""
