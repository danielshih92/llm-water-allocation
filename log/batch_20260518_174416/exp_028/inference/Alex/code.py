# ============================================================
# Experiment: exp_028
# Agent: Alex
# Source: exp_028
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    players = 1 + len(alive)
    total_demand_units = players * WATER_REQ
    scarcity = supply < total_demand_units

    prev_bids = []
    desperate_opp = False
    rich_aggressive = False
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            desperate_opp = True
        if opp.get('budget', 0) > budget and prev and prev.get('bid') is not None and prev.get('bid') >= DAILY_SALARY * 0.75:
            rich_aggressive = True

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.98
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.82
    else:
        if scarcity:
            base = DAILY_SALARY * 0.62
        else:
            base = DAILY_SALARY * 0.34

    if prev_bids:
        highest_prev = max(prev_bids)
        if scarcity:
            target = highest_prev + 2.0
            if rich_aggressive and hp > 4 and no_water_days == 0:
                target = DAILY_SALARY * 0.28
            base = max(base, target)
        else:
            if highest_prev >= DAILY_SALARY * 0.85 and hp > 4 and no_water_days == 0:
                base = min(base, DAILY_SALARY * 0.25)
            else:
                base = max(base, min(highest_prev + 1.0, DAILY_SALARY * 0.68))

    if desperate_opp and scarcity and hp > 4 and no_water_days == 0:
        base = min(base, DAILY_SALARY * 0.45)

    if budget <= DAILY_SALARY * 0.6:
        base = min(base, max(0.0, budget * 0.9))

    bid = min(budget, max(0.0, base))
    return float(bid)
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    slots = supply / float(WATER_REQ)
    contested = slots < 2.0

    pressure_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        prev_bid = 0.0
        if prev and prev.get('bid') is not None:
            prev_bid = float(prev.get('bid', 0.0))
            pressure_bids.append(prev_bid)

        opp_hp = opp.get('hp', 0)
        opp_nw = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0.0)
        if opp_hp <= 3 or opp_nw >= 1:
            desperate_count += 1
        if opp_budget >= 200 and prev_bid >= 80:
            rich_aggressive += 1

    max_prev = max(pressure_bids) if pressure_bids else 0.0
    avg_prev = sum(pressure_bids) / float(len(pressure_bids)) if pressure_bids else 0.0

    emergency = (hp <= 3) or (no_water >= 1)

    if emergency:
        bid = max(78.0, max_prev + 3.0)
        if contested:
            bid += 10.0
        return float(min(budget, bid))

    if contested:
        if rich_aggressive >= 1:
            bid = 24.0
        else:
            bid = max(28.0, min(62.0, avg_prev + 2.0))
            if desperate_count >= 2:
                bid += 8.0
    else:
        if max_prev >= 100.0:
            bid = 14.0
        elif max_prev >= 70.0:
            bid = 18.0
        else:
            bid = 22.0

    if day >= 8 and hp >= 6:
        bid *= 0.9
    if budget < 120:
        bid = min(bid, 36.0)

    bid = max(0.0, min(budget, bid))
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    units = supply / float(WATER_REQ)
    contested = units < 2.0

    prev_bids = []
    strongest_prev = 0.0
    david_prev = 0.0
    eric_prev = 0.0
    cindy_prev = 0.0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid')
        if b is not None:
            b = float(b)
            prev_bids.append(b)
            if b > strongest_prev:
                strongest_prev = b
            name = str(agent_id)
            if name == 'David':
                david_prev = b
            elif name == 'Eric':
                eric_prev = b
            elif name == 'Cindy':
                cindy_prev = b

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1

    live_count = len(alive)

    if danger >= 3:
        base = max(DAILY_SALARY * 0.95, strongest_prev + 6.0)
    elif contested:
        target = max(david_prev, strongest_prev * 0.98)
        if target > 0:
            base = max(DAILY_SALARY * 0.82, target + 2.5)
        else:
            base = DAILY_SALARY * 0.8
    else:
        if live_count >= 3:
            base = DAILY_SALARY * 0.48
        else:
            base = DAILY_SALARY * 0.42
        if strongest_prev > 0 and strongest_prev < DAILY_SALARY * 0.75:
            base = max(base, strongest_prev + 1.25)

    if day >= 8 and hp >= 7 and budget > DAILY_SALARY * 4:
        base *= 0.92

    if cindy_prev >= DAILY_SALARY * 1.4 and hp > 4 and not contested:
        base *= 0.9

    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0:
        soft_cap = min(soft_cap, max(DAILY_SALARY * 0.35, budget / float(reserve_days + 1) * 1.35))

    if danger >= 3:
        bid = min(budget, max(base, DAILY_SALARY * 0.95))
    else:
        bid = min(base, soft_cap)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, strongest_prev + 8.0, DAILY_SALARY * 1.0))

    bid = max(0.0, min(float(budget), float(bid)))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return min(float(budget), 35.0)

    active_bids = []
    cindy_bid = None
    eric_bid = None
    for agent_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if opp.get('alive') and bid is not None:
            active_bids.append(float(bid))
        if agent_id == 'Cindy' and opp.get('alive') and bid is not None:
            cindy_bid = float(bid)
        if agent_id == 'Eric' and opp.get('alive') and bid is not None:
            eric_bid = float(bid)

    tight_supply = supply <= 17
    loose_supply = supply >= 22
    urgent = hp <= 4 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    base = 32.0

    if eric_bid is not None:
        base = max(base, min(eric_bid + 2.0, 86.0))
    elif active_bids:
        base = max(base, min(max(active_bids) + 1.5, 80.0))
    else:
        base = 49.0

    if cindy_bid is not None and cindy_bid >= 120.0 and not urgent:
        base = min(base, 74.0)

    if loose_supply and not urgent:
        base *= 0.78
    elif tight_supply:
        base *= 1.12

    if urgent:
        base = max(base, 78.0)
    if critical:
        base = max(base, 92.0)

    remaining_days = max(0, 10 - int(day) + 1)
    reserve_floor = max(0.0, remaining_days * 18.0)
    spend_cap = float(budget)
    if not urgent:
        spend_cap = max(0.0, float(budget) - reserve_floor)
        spend_cap = min(float(budget), max(28.0, spend_cap))

    bid = min(float(budget), min(spend_cap, base))

    if critical and budget > 0:
        bid = min(float(budget), max(bid, 95.0))

    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
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
        return float(min(budget, max(8.0, DAILY_SALARY * 0.22)))

    pressure_bids = []
    urgent_bids = []
    weak_opp_count = 0
    rich_opp_count = 0

    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is not None:
            pressure_bids.append(float(prev_bid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_bids.append(float(prev_bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            weak_opp_count += 1
        if opp.get('budget', 0) >= 700:
            rich_opp_count += 1

    highest_prev = max(pressure_bids) if pressure_bids else 0.0
    urgent_prev = max(urgent_bids) if urgent_bids else highest_prev

    scarcity = float(WATER_REQ) / max(float(supply), 1.0)
    tight_supply = supply <= 17
    very_tight = supply <= 15

    must_win = hp <= 2 or no_water >= 2
    should_win = hp <= 4 or no_water >= 1

    if must_win:
        target = max(urgent_prev + 2.0, DAILY_SALARY * 0.96)
        if very_tight:
            target = max(target, DAILY_SALARY * 1.08)
        return float(min(budget, target))

    if should_win:
        target = max(urgent_prev + 1.5, highest_prev * 0.92, DAILY_SALARY * 0.78)
        if tight_supply:
            target = max(target, DAILY_SALARY * 0.9)
        return float(min(budget, target))

    if very_tight:
        target = max(highest_prev + 1.0, DAILY_SALARY * 0.72)
    elif tight_supply:
        target = max(highest_prev * 0.82, DAILY_SALARY * 0.56)
    else:
        target = DAILY_SALARY * 0.28
        if highest_prev > 0:
            target = min(target, highest_prev * 0.45)

    if weak_opp_count >= 2 and hp >= 6:
        target *= 0.85
    if rich_opp_count >= 2 and tight_supply:
        target = max(target, DAILY_SALARY * 0.68)
    if day >= 8 and hp >= 6:
        target *= 0.9

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if days_left >= 2 and hp >= 5:
        reserve_floor = min(budget * 0.55, DAILY_SALARY * 2.2)
    spend_cap = max(0.0, budget - reserve_floor)
    if spend_cap <= 0:
        spend_cap = min(budget, DAILY_SALARY * 0.35)

    bid = min(target, spend_cap)
    bid = max(0.0, min(budget, bid))
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    likely_two_units = supply >= 24
    likely_one_unit = supply < 24

    desperate = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if desperate:
        bid = max(84.0, max_prev + 2.5)
    elif likely_two_units:
        target = max(66.0, min(79.0, avg_prev + 1.2))
        if max_prev >= 80:
            target = max(67.0, min(76.0, min_prev + 2.0 if prev_bids else 70.0))
        bid = target
    elif likely_one_unit:
        if pressured:
            bid = max(79.0, min(88.0, max_prev + 1.0))
        else:
            bid = 18.0
    else:
        bid = 35.0

    if hp >= 7 and no_water == 0 and likely_one_unit and max_prev >= 75:
        bid = min(bid, 15.0)

    if budget < bid:
        bid = budget

    if budget <= 25:
        if desperate:
            bid = budget
        else:
            bid = min(bid, max(0.0, budget * 0.5))

    if bid < 0:
        bid = 0.0
    return float(bid)
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 700:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if hp <= 1 or no_water >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif hp <= 2 or no_water >= 1:
        bid = max(DAILY_SALARY * 0.8, avg_prev + 3.0)
    else:
        if tight_supply:
            bid = max(DAILY_SALARY * 0.62, avg_prev + 2.0)
        elif ample_supply:
            bid = DAILY_SALARY * 0.28
        else:
            bid = DAILY_SALARY * 0.42

    if highest_prev >= 100:
        if hp >= 4 and no_water == 0:
            bid = min(bid, DAILY_SALARY * 0.35)
        else:
            bid = max(bid, DAILY_SALARY * 0.78)
    elif highest_prev >= 75:
        if hp >= 5 and no_water == 0 and not tight_supply:
            bid = min(bid, DAILY_SALARY * 0.38)
        else:
            bid = max(bid, DAILY_SALARY * 0.6)
    else:
        bid = max(bid, highest_prev + 1.5 if highest_prev > 0 else bid)

    if desperate_count >= 2:
        bid += 4.0
    elif desperate_count == 0 and ample_supply and hp >= 4:
        bid -= 4.0

    if rich_count >= 1 and highest_prev >= 95 and hp >= 4 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.34)

    if day >= 8:
        if hp <= 3:
            bid = max(bid, DAILY_SALARY * 0.82)
        else:
            bid = max(bid, DAILY_SALARY * 0.5)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(bid)
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    yesterday_bids = []
    opp_budgets = []
    urgent_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return max(0, min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.75
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.7
    richest_opp = max(opp_budgets) if opp_budgets else 0

    tight_supply = supply <= 17
    abundant_supply = supply >= 22
    my_urgent = hp <= 3 or no_water >= 1
    very_urgent = hp <= 2 or no_water >= 2

    if very_urgent:
        bid = max(highest_prev + 2.0, DAILY_SALARY * 1.05)
    elif my_urgent:
        bid = max(avg_prev + 2.0, DAILY_SALARY * 0.92)
    else:
        if tight_supply:
            if urgent_opp_count >= 2:
                bid = DAILY_SALARY * 0.48
            else:
                bid = avg_prev * 0.72
        elif abundant_supply:
            bid = DAILY_SALARY * 0.34
        else:
            bid = DAILY_SALARY * 0.40

    if budget < DAILY_SALARY * 2:
        if my_urgent:
            bid = min(bid, budget)
        else:
            bid = min(bid, DAILY_SALARY * 0.28)

    if richest_opp < budget * 0.6 and not my_urgent:
        bid = min(bid, DAILY_SALARY * 0.36)

    if day >= 8 and hp >= 4 and not my_urgent:
        bid = min(bid, DAILY_SALARY * 0.32)

    bid = max(0, min(budget, bid))
    return bid
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
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    emergency = False
    if hp <= 2 or no_water_days >= 2:
        emergency = True
    elif hp <= 4 and scarcity >= 1:
        emergency = True

    if emergency:
        bid = max(95.0, highest_prev + 2.5)
        if scarcity == 2:
            bid = max(bid, 128.0)
        return float(min(budget, bid))

    if scarcity == 2:
        if hp >= 7 and no_water_days == 0:
            bid = max(42.0, avg_prev * 0.42)
        else:
            bid = max(78.0, highest_prev * 0.78)
            if urgent_opp >= 2:
                bid += 6.0
        return float(min(budget, bid))

    if scarcity == 1:
        if hp >= 8 and no_water_days == 0:
            bid = max(28.0, avg_prev * 0.28)
        else:
            bid = max(58.0, highest_prev * 0.55)
        if rich_opp >= 2:
            bid += 4.0
        return float(min(budget, bid))

    if hp <= 5 or no_water_days >= 1:
        bid = max(52.0, highest_prev * 0.45)
    else:
        bid = 21.0 + min(day, 10) * 0.8
        if avg_prev > 120:
            bid = min(bid, 26.0)

    return float(min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    rich_aggressive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 90 and opp.get('budget', 0) >= 200:
                    rich_aggressive += 1

    if not alive_opps:
        return min(float(budget), 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.6
    elif hp <= 7:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.45

    late_game = day >= 8
    if late_game:
        urgency += 0.2

    if hp <= 2 or no_water_days >= 2:
        emergency_bid = max(92.0, highest_prev + 3.0)
        return min(float(budget), emergency_bid)

    if float(supply) >= 23 and hp >= 8 and no_water_days == 0:
        return min(float(budget), 8.0)

    if float(supply) >= 20 and highest_prev >= 120 and hp >= 6:
        return min(float(budget), 14.0)

    base = 16.0 + 22.0 * scarcity + 18.0 * urgency

    if highest_prev > 0:
        if highest_prev >= 120:
            if hp >= 6 and no_water_days == 0 and float(supply) >= 18:
                target = 15.0
            else:
                target = 0.72 * highest_prev + 4.0
        elif highest_prev >= 85:
            target = 0.78 * highest_prev + 5.0
        else:
            target = max(base, highest_prev + 2.5)
    else:
        target = base

    if rich_aggressive >= 2 and hp >= 6 and no_water_days == 0 and float(supply) >= 18:
        target = min(target, 18.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 120.0
    elif day <= 9:
        reserve_floor = 60.0

    affordable = float(budget) - reserve_floor
    if affordable < 0:
        affordable = float(budget) * 0.45

    bid = min(target, affordable, float(budget))

    if bid < 0:
        bid = 0.0

    if hp <= 4 or no_water_days >= 1:
        bid = max(bid, min(float(budget), 35.0 + 15.0 * scarcity))

    return float(max(0.0, bid))
"""
