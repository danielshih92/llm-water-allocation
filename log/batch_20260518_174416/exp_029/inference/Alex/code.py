# ============================================================
# Experiment: exp_029
# Agent: Alex
# Source: exp_029
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
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return max(0, min(budget, 50.0))
        return max(0, min(budget, 24.0))

    prev_bids = []
    desperate_count = 0
    error_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            if prev.get('error'):
                error_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1

    base = 32.0

    if supply <= WATER_REQ:
        base = 58.0
    elif supply <= WATER_REQ * 1.5:
        base = 46.0
    else:
        base = 32.0

    if hp <= 2 or no_water_days >= 2:
        base = max(base, 61.0)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, 49.0)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if highest_prev >= 62:
            if hp > 4 and no_water_days == 0 and supply > WATER_REQ:
                base = min(base, 34.0)
            else:
                base = max(base, 64.0)
        elif highest_prev >= 48:
            base = max(base, min(60.0, highest_prev + 2.0))
        else:
            base = max(base, avg_prev + 2.5)

    if desperate_count >= 2:
        base += 4.0
    elif desperate_count == 1:
        base += 2.0

    if error_count >= 1:
        base -= 2.0

    if budget < base:
        if hp <= 2 or no_water_days >= 2:
            return max(0, float(budget))
        return max(0, min(float(budget), max(12.0, budget * 0.7)))

    return max(0, min(float(budget), float(base)))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    max_prev_bid = 0.0
    min_prev_bid = None
    eric_like_bid = None
    cindy_like_bid = None

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > max_prev_bid:
                    max_prev_bid = float(bid)
                if min_prev_bid is None or float(bid) < min_prev_bid:
                    min_prev_bid = float(bid)
                if 65.0 <= float(bid) <= 75.0:
                    eric_like_bid = float(bid)
                if float(bid) >= 110.0:
                    cindy_like_bid = float(bid)

    if not alive_opps:
        return min(float(budget), 1.0)

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

    if supply <= 16:
        urgency += 1

    if cindy_like_bid is not None and hp > 4 and no_water_days == 0:
        if supply >= 20:
            base = 8.0
        else:
            base = 18.0
        return min(float(budget), base)

    target = 0.0

    if urgency >= 5:
        if cindy_like_bid is not None:
            target = min(float(budget), max(96.0, cindy_like_bid + 1.0))
        else:
            ref = eric_like_bid if eric_like_bid is not None else max_prev_bid
            target = min(float(budget), max(85.0, ref + 3.0))
    elif urgency >= 3:
        ref = eric_like_bid if eric_like_bid is not None else 70.0
        target = max(72.0, ref + 2.0)
    elif urgency >= 1:
        if supply >= 22:
            target = 28.0
        elif supply >= 19:
            target = 42.0
        else:
            ref = eric_like_bid if eric_like_bid is not None else 70.0
            target = max(55.0, ref + 1.0)
    else:
        if supply >= 22:
            target = 5.0
        elif supply >= 19:
            target = 15.0
        else:
            target = 26.0

    reserve_days = max(0, 10 - int(day))
    soft_cap = float(budget)
    if reserve_days > 0 and urgency < 5:
        keep_reserve = reserve_days * 18.0
        soft_cap = max(0.0, float(budget) - keep_reserve)
        if soft_cap <= 0.0:
            soft_cap = min(float(budget), 22.0 if urgency == 0 else 40.0)

    bid = min(float(budget), target, soft_cap if urgency < 5 else float(budget))

    if hp <= 2 or no_water_days >= 2:
        bid = min(float(budget), max(bid, 98.0 if cindy_like_bid is not None else 78.0))

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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    aggressive_count = 0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= DAILY_SALARY * 0.95:
                    aggressive_count += 1

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.5

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tight_supply = supply <= 17
    ample_supply = supply >= 22

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

    if tight_supply:
        urgency += 2
    elif not ample_supply:
        urgency += 1

    if day >= 8:
        urgency += 1

    if budget < DAILY_SALARY * 2:
        urgency += 1

    if highest_prev >= 100:
        if urgency <= 2:
            return float(min(budget, DAILY_SALARY * 0.22))
        target = max(DAILY_SALARY * 0.92, highest_prev + 2.5)
        return float(min(budget, target))

    if urgency >= 6:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif urgency >= 4:
        target = max(DAILY_SALARY * 0.78, avg_prev + 3.0, highest_prev * 0.9)
    elif urgency >= 2:
        if aggressive_count >= 2 and hp > 4:
            target = DAILY_SALARY * 0.4
        else:
            target = max(DAILY_SALARY * 0.58, avg_prev + 1.5)
    else:
        if ample_supply:
            target = DAILY_SALARY * 0.32
        elif aggressive_count >= 1:
            target = DAILY_SALARY * 0.28
        else:
            target = DAILY_SALARY * 0.45

    if budget > DAILY_SALARY * 8 and hp <= 4:
        target += 8.0
    if budget < DAILY_SALARY and urgency < 5:
        target = min(target, budget * 0.75)

    target = max(0.0, min(budget, target))
    return float(target)
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if float(opp.get('budget', 0)) > 500:
                rich_opp += 1
            if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 10)) <= 4:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    survival_urgency = 0.0
    if hp <= 2:
        survival_urgency += 0.9
    elif hp <= 4:
        survival_urgency += 0.45
    if no_water >= 2:
        survival_urgency += 0.8
    elif no_water >= 1:
        survival_urgency += 0.35
    if survival_urgency > 1.2:
        survival_urgency = 1.2

    pressure = 0.0
    pressure += scarcity * 22.0
    pressure += min(highest_prev, 120.0) * 0.28
    pressure += min(avg_prev, 100.0) * 0.10
    pressure += urgent_opp * 3.5
    pressure += rich_opp * 2.0

    base = 18.0 + pressure

    if survival_urgency >= 0.9:
        bid = max(base, highest_prev + 6.0, DAILY_SALARY * 0.95)
    elif survival_urgency >= 0.4:
        bid = max(base, highest_prev + 2.5, DAILY_SALARY * 0.72)
    else:
        if scarcity < 0.25 and highest_prev >= DAILY_SALARY * 1.5:
            bid = DAILY_SALARY * 0.28
        elif scarcity < 0.45 and highest_prev >= DAILY_SALARY * 1.2:
            bid = DAILY_SALARY * 0.4
        else:
            bid = max(base, min(highest_prev + 1.5, DAILY_SALARY * 0.92))

    if budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.62)
    elif budget < DAILY_SALARY * 4:
        bid = min(bid, budget * 0.48)
    else:
        bid = min(bid, budget * 0.34)

    if day >= 8 and (hp <= 4 or no_water >= 1):
        bid = max(bid, min(budget, highest_prev + 4.0, DAILY_SALARY * 1.05))

    if hp >= 7 and no_water == 0 and scarcity < 0.2:
        bid = min(bid, DAILY_SALARY * 0.38)

    if bid < 0:
        bid = 0.0
    if bid > budget:
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
                prev_bids.append(prev['bid'])

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    total_agents = 1 + len(alive_opponents)
    total_req = WATER_REQ + sum(opp_requirements)
    slack = supply - total_req
    per_agent_supply = supply / float(total_agents)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1
    tight_supply = slack <= 0 or per_agent_supply < WATER_REQ
    loose_supply = slack >= WATER_REQ

    if urgent:
        target = max(78.0, highest_prev + 2.0)
    elif tight_supply:
        target = max(74.0, highest_prev + 1.25)
    elif pressured:
        target = max(72.0, avg_prev + 1.0)
    elif loose_supply:
        target = max(38.0, avg_prev * 0.72)
    else:
        target = max(52.0, avg_prev * 0.82)

    if highest_prev >= 80 and not urgent and hp >= 5:
        target = min(target, 58.0)

    if supply >= 23 and hp >= 5 and no_water_days == 0:
        target = min(target, 50.0)

    if budget < DAILY_SALARY * 1.2:
        if urgent:
            target = max(target, budget * 0.9)
        else:
            target = min(target, budget * 0.55)

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    units_available = int(supply // WATER_REQ)
    if units_available < 0:
        units_available = 0

    highest_prev_bid = 0.0
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 120:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None and bid > highest_prev_bid:
                highest_prev_bid = bid

    my_urgent = hp <= 3 or no_water_days >= 1
    very_urgent = hp <= 2 or no_water_days >= 2

    if not alive_opponents:
        return float(min(budget, 18.0 if not my_urgent else 55.0))

    if units_available >= 2:
        base = 16.0
        if highest_prev_bid > 0:
            base = min(42.0, max(base, highest_prev_bid * 0.28))
        if my_urgent:
            base = max(base, 38.0)
        if very_urgent:
            base = max(base, 58.0)
        if day >= 8 and budget > 200:
            base += 4.0
        return float(min(budget, base))

    base = 52.0
    if highest_prev_bid >= 120:
        base = 66.0
    elif highest_prev_bid >= 90:
        base = 61.0
    elif highest_prev_bid >= 60:
        base = 57.0

    if urgent_opp >= 2:
        base += 4.0
    elif urgent_opp == 0 and rich_opp >= 2:
        base -= 3.0

    if my_urgent:
        base = max(base, 68.0)
    if very_urgent:
        base = max(base, 90.0)

    if day >= 9:
        base += 6.0

    if budget < base:
        if my_urgent:
            return float(budget)
        return float(min(budget, 35.0))

    return float(min(budget, base))
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

    alive = []
    prev_bids = []
    threat_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    threat_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    expected_winners = max(1, int(supply // WATER_REQ))
    live_count = len(alive) + 1
    scarcity = live_count - expected_winners

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_bids) if threat_bids else highest_prev

    urgent = hp <= 3 or no_water >= 1
    severe = hp <= 2 or no_water >= 2

    base = 0.0

    if severe:
        base = max(62.0, highest_threat + 2.5)
    elif urgent:
        if scarcity >= 3:
            base = max(54.0, highest_threat + 1.5)
        else:
            base = max(46.0, highest_threat * 0.72 + 2.0)
    else:
        if scarcity >= 4:
            base = max(44.0, highest_threat * 0.55 + 1.0)
        elif scarcity >= 2:
            base = max(32.0, highest_threat * 0.38 + 1.0)
        else:
            base = 18.0

    if day >= 8:
        base += 6.0
    elif day >= 5 and urgent:
        base += 4.0

    reserve_days = max(0, 10 - day)
    reserve_floor = reserve_days * 16.0
    affordable = max(0.0, budget - reserve_floor)

    if severe and affordable < 35.0:
        affordable = budget
    elif urgent and affordable < 25.0:
        affordable = max(affordable, budget * 0.75)

    bid = min(base, budget, max(0.0, affordable))

    if bid <= 0.0:
        if severe:
            bid = min(budget, 55.0)
        elif urgent:
            bid = min(budget, 35.0)
        else:
            bid = min(budget, 12.0)

    if highest_threat >= 120.0 and not urgent:
        bid = min(bid, 24.0)

    return float(max(0.0, bid))
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
    prev_bids = []
    strong_prev = []
    desperate_count = 0
    low_budget_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) <= DAILY_SALARY * 0.8:
                low_budget_opp += 1
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= DAILY_SALARY * 0.8:
                    strong_prev.append(float(bid))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.2))

    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < 1.6
    very_scarce = expected_units < 1.2

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev = sorted_bids[int(1)]

    emergency = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    base = DAILY_SALARY * 0.42

    if emergency:
        if highest_prev > 0:
            bid = max(DAILY_SALARY * 0.92, highest_prev + 2.0)
        else:
            bid = DAILY_SALARY * 0.9
    elif very_scarce:
        if strong_prev:
            bid = max(DAILY_SALARY * 0.78, second_prev + 1.5, highest_prev * 0.82)
        else:
            bid = DAILY_SALARY * 0.62
    elif scarcity:
        if highest_prev >= DAILY_SALARY * 0.9:
            bid = DAILY_SALARY * 0.38 if hp > 4 else DAILY_SALARY * 0.86
        elif highest_prev > 0:
            bid = max(DAILY_SALARY * 0.52, second_prev + 1.0)
        else:
            bid = DAILY_SALARY * 0.5
    else:
        if desperate_count >= 2 and hp > 4:
            bid = DAILY_SALARY * 0.28
        elif highest_prev >= DAILY_SALARY * 0.85 and hp > 5:
            bid = DAILY_SALARY * 0.3
        else:
            bid = base

    if low_budget_opp >= 2 and not emergency:
        bid *= 0.9

    if day >= 8 and hp > 5 and budget < DAILY_SALARY * 2:
        bid *= 0.85

    min_safe = 0.0
    if emergency:
        min_safe = DAILY_SALARY * 0.75
    elif pressured and scarcity:
        min_safe = DAILY_SALARY * 0.48

    bid = max(bid, min_safe)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp_count = 0
    rich_opp_pressure = 0.0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > budget * 0.8:
                    rich_opp_pressure = max(rich_opp_pressure, float(bid))

    if not alive_opps:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    slots = max(1, int(supply // WATER_REQ))
    competitors = 1 + len(alive_opps)
    scarcity = competitors - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    need_score = 0
    if hp <= 2:
        need_score += 4
    elif hp <= 4:
        need_score += 2
    if no_water >= 2:
        need_score += 4
    elif no_water >= 1:
        need_score += 2

    pressure = 0
    if scarcity >= 3:
        pressure += 3
    elif scarcity >= 1:
        pressure += 2
    if supply <= 16:
        pressure += 2
    elif supply <= 19:
        pressure += 1
    pressure += min(2, urgent_opp_count)

    if need_score >= 6:
        base = max(62.0, highest_prev + 2.5, avg_prev + 6.0)
    elif need_score >= 3:
        base = max(42.0, avg_prev * 0.72 + 4.0, highest_prev * 0.52 + 3.0)
    else:
        if pressure >= 4:
            base = max(28.0, avg_prev * 0.45, rich_opp_pressure * 0.38)
        elif pressure >= 2:
            base = max(18.0, avg_prev * 0.28)
        else:
            base = 10.0 + max(0.0, (18.0 - supply) * 1.2)

    if highest_prev >= 120 and need_score <= 2:
        base = min(base, 24.0)
    if highest_prev >= 145 and need_score <= 4:
        base = min(base, 32.0)

    reserve = 0.0
    if hp <= 3 or no_water >= 1:
        reserve = 0.0
    else:
        reserve = DAILY_SALARY * 0.35

    max_affordable = max(0.0, budget - reserve)
    bid = min(base, max_affordable)

    if need_score >= 6:
        bid = min(max_affordable, max(bid, DAILY_SALARY * 0.9))
    elif need_score >= 3 and pressure >= 3:
        bid = min(max_affordable, max(bid, DAILY_SALARY * 0.68))

    if bid < 0:
        bid = 0.0
    return float(min(budget, round(bid, 2)))
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
    prev_bids = []
    rich_pressure = 0.0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('budget', 0) > 300:
                rich_pressure += 1.0

    if budget <= 0:
        return 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if tight_supply:
        urgency += 2
    elif ample_supply:
        urgency -= 1
    if day >= 8:
        urgency += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
    elif urgency >= 7:
        base = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif urgency >= 5:
        base = max(DAILY_SALARY * 0.78, avg_prev + 2.0)
    elif urgency >= 3:
        if highest_prev >= 120:
            base = DAILY_SALARY * 0.52
        else:
            base = max(DAILY_SALARY * 0.48, avg_prev + 1.0)
    else:
        if highest_prev >= 120:
            base = DAILY_SALARY * 0.22
        elif highest_prev >= 90:
            base = DAILY_SALARY * 0.30
        else:
            base = DAILY_SALARY * 0.42

    if rich_pressure >= 2 and urgency <= 3:
        base *= 0.9
    if ample_supply and urgency <= 3:
        base *= 0.9
    if tight_supply and urgency >= 3:
        base *= 1.08

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = DAILY_SALARY * 2.0
    elif hp > 2:
        reserve = DAILY_SALARY * 1.0

    cap = budget - reserve
    if urgency >= 5:
        cap = budget
    if cap < 0:
        cap = min(budget, DAILY_SALARY * 0.4)

    bid = min(base, cap, budget)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.95, highest_prev + 2.5))

    if bid < 0:
        bid = 0.0
    return float(bid)
"""
