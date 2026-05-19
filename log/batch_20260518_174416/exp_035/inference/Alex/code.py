# ============================================================
# Experiment: exp_035
# Agent: Alex
# Source: exp_035
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    players_alive = 1 + len(alive_opponents)
    units_available = int(supply // WATER_REQ)
    scarcity = players_alive - units_available

    prev_bids = []
    desperate_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opponents += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('error') in (None, '', False):
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    if not alive_opponents:
        return min(budget, 21)

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

    if scarcity >= 2:
        urgency += 3
    elif scarcity >= 1:
        urgency += 2
    elif scarcity <= 0:
        urgency -= 1

    urgency += min(2, desperate_opponents)
    if rich_opponents >= max(1, len(alive_opponents) // 2):
        urgency += 1

    if urgency <= 0:
        base_bid = 18
    elif urgency == 1:
        base_bid = 26
    elif urgency == 2:
        base_bid = 34
    elif urgency == 3:
        base_bid = 43
    elif urgency == 4:
        base_bid = 52
    elif urgency == 5:
        base_bid = 60
    else:
        base_bid = 66

    if highest_prev > 0:
        if urgency >= 4:
            target = max(base_bid, highest_prev + 2)
        elif urgency >= 2:
            target = max(base_bid, avg_prev + 1)
        else:
            target = min(base_bid, highest_prev)
    else:
        target = base_bid

    if hp <= 2 or no_water >= 2:
        target = max(target, 63)

    if scarcity <= 0 and hp > 4 and no_water == 0:
        target = min(target, 24)

    reserve = 0
    if hp > 3 and no_water == 0:
        reserve = DAILY_SALARY * 0.4
    affordable = max(0, budget - reserve)
    bid = min(target, budget)
    if affordable > 0:
        bid = min(bid, max(affordable, 12))

    if bid < 0:
        bid = 0
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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

    alive_opponents = []
    prev_bids = []
    dangerous_prev = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(opp.get('water_requirement', WATER_REQ)) >= WATER_REQ:
                    dangerous_prev.append(float(bid))

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 40.0))
        return float(min(budget, 18.0))

    scarcity = 1.0 - ((supply - 15.0) / 10.0)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    high_pressure = max(prev_bids) if prev_bids else 0.0
    core_pressure = max(dangerous_prev) if dangerous_prev else high_pressure

    base = 26.0 + 18.0 * scarcity

    if core_pressure >= 110.0:
        target = 34.0 + 10.0 * scarcity
    elif core_pressure >= 80.0:
        target = max(base, 52.0 + 8.0 * scarcity)
    elif core_pressure >= 50.0:
        target = max(base, core_pressure + 3.0)
    elif core_pressure > 0.0:
        target = max(base, core_pressure + 2.0)
    else:
        target = base

    if supply <= 16.0:
        target += 10.0
    elif supply >= 23.0:
        target -= 6.0

    if hp <= 2:
        target = max(target, 66.0)
    elif hp <= 4:
        target = max(target, 54.0)

    if no_water_days >= 2:
        target = max(target, 69.0)
    elif no_water_days >= 1:
        target = max(target, 58.0)

    if day >= 8 and hp < 7:
        target += 6.0

    if budget < 80.0:
        target = min(target, budget * 0.72)
    elif budget < 160.0:
        target = min(target, budget * 0.58)

    if target < 0.0:
        target = 0.0

    return float(min(budget, round(target, 2)))
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    opp_infos = []
    prev_bids = []
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is None:
            pbid = 0.0
        prev_bids.append(float(pbid))
        opp_infos.append({
            'id': agent_id,
            'bid': float(pbid),
            'hp': opp.get('hp', 10),
            'budget': opp.get('budget', 0.0),
            'nwd': opp.get('no_water_days', 0),
            'req': opp.get('water_requirement', WATER_REQ)
        })

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids, reverse=True)[int(1)] if len(prev_bids) >= 2 else highest_prev
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    cindy_bid = None
    bob_bid = None
    eric_bid = None
    for info in opp_infos:
        lid = info['id'].lower()
        if lid == 'cindy':
            cindy_bid = info['bid']
        elif lid == 'bob':
            bob_bid = info['bid']
        elif lid == 'eric':
            eric_bid = info['bid']

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

    scarce = supply <= 17
    ample = supply >= 22

    strong_count = 0
    for info in opp_infos:
        if info['budget'] >= 120 and info['hp'] > 2:
            strong_count += 1

    if urgency >= 5:
        target = max(110.0, second_prev + 3.0)
        if eric_bid is not None:
            target = max(target, eric_bid + 4.0)
        if bob_bid is not None and bob_bid < 120:
            target = max(target, bob_bid + 2.0)
        if cindy_bid is not None and cindy_bid <= budget and hp <= 2:
            target = max(target, cindy_bid + 1.0)
        return float(min(budget, target))

    if scarce:
        if urgency >= 3:
            target = max(92.0, avg_prev + 6.0)
            if eric_bid is not None:
                target = max(target, eric_bid + 3.0)
            return float(min(budget, target))
        if strong_count >= 2:
            return float(min(budget, 16.0))
        return float(min(budget, 28.0))

    if ample:
        if urgency >= 2:
            target = max(58.0, (eric_bid + 2.0) if eric_bid is not None else 58.0)
            return float(min(budget, target))
        return float(min(budget, 24.0))

    if urgency >= 3:
        target = 84.0
        if eric_bid is not None:
            target = max(target, eric_bid + 2.5)
        return float(min(budget, target))

    if highest_prev >= 125.0:
        return float(min(budget, 26.0))

    target = 52.0
    if eric_bid is not None:
        target = max(target, eric_bid + 1.5)
    elif bob_bid is not None and bob_bid < 90:
        target = max(target, bob_bid + 1.5)

    if day >= 8 and hp >= 6 and budget > 140:
        target += 6.0

    return float(min(budget, target))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
    fixed_high_count = 0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80:
                    fixed_high_count += 1

    if not alive:
        return min(budget, 18.0)

    units = supply / float(WATER_REQ)
    urgent = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    low_prev = min(prev_bids) if prev_bids else 0.0

    if urgent:
        bid = max(62.0, min(79.0, highest_prev + 2.0))
        return min(budget, bid)

    if units < 1.5:
        if pressured:
            bid = max(56.0, min(74.0, highest_prev * 0.9 + 3.0))
        else:
            bid = 24.0 if fixed_high_count >= 1 else max(32.0, low_prev + 2.0)
        return min(budget, bid)

    if units >= 1.8:
        if fixed_high_count >= 1:
            bid = 14.0 if hp >= 7 and no_water_days == 0 else 26.0
        else:
            bid = max(20.0, low_prev + 1.5) if prev_bids else 22.0
        return min(budget, bid)

    if fixed_high_count >= 2:
        bid = 16.0 if hp >= 6 else 34.0
    elif fixed_high_count == 1:
        bid = 20.0 if hp >= 7 and no_water_days == 0 else 38.0
    else:
        if highest_prev >= 75:
            bid = 22.0 if hp >= 7 else 48.0
        elif highest_prev >= 55:
            bid = max(36.0, highest_prev * 0.72)
        else:
            bid = max(28.0, highest_prev + 2.0) if prev_bids else 30.0

    if day >= 8 and hp <= 6:
        bid = max(bid, 52.0)

    return min(budget, bid)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return max(0.0, float(bid))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 300:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    abundant_supply = supply >= 22
    urgent_me = hp <= 3 or no_water >= 1
    very_urgent_me = hp <= 2 or no_water >= 2

    if very_urgent_me:
        base = max(DAILY_SALARY * 1.05, highest_prev + 2.5)
    elif urgent_me:
        base = max(DAILY_SALARY * 0.9, avg_prev + 2.0)
    else:
        if abundant_supply:
            base = DAILY_SALARY * 0.42
        elif tight_supply:
            base = DAILY_SALARY * 0.62
        else:
            base = DAILY_SALARY * 0.52

        if highest_prev >= 105:
            base = min(base, DAILY_SALARY * 0.5)
        elif highest_prev >= 90:
            base = max(base, DAILY_SALARY * 0.58)
        elif highest_prev > 0:
            base = max(base, min(highest_prev + 1.25, DAILY_SALARY * 0.82))

    if desperate_count >= 2:
        base += 6.0
    elif desperate_count == 1:
        base += 3.0

    if rich_count >= 2 and not urgent_me:
        base -= 4.0

    remaining_days = max(1, 10 - int(day) + 1)
    reserve_target = max(0.0, remaining_days * DAILY_SALARY * 0.45)
    spend_cap = budget
    if not urgent_me:
        spend_cap = max(0.0, budget - reserve_target)
        spend_cap = max(DAILY_SALARY * 0.35, spend_cap)

    if abundant_supply and not urgent_me:
        base *= 0.92
    if tight_supply:
        base *= 1.08

    bid = min(budget, min(base, spend_cap))

    floor_bid = 0.0
    if very_urgent_me:
        floor_bid = min(budget, DAILY_SALARY * 0.85)
    elif urgent_me:
        floor_bid = min(budget, DAILY_SALARY * 0.72)
    else:
        floor_bid = min(budget, DAILY_SALARY * 0.28)

    bid = max(floor_bid, bid)
    bid = max(0.0, min(float(bid), float(budget)))
    return bid
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

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    strongest_prev = 0.0
    cindy_prev = None
    active_threats = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
            active_threats += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            if bid > strongest_prev:
                strongest_prev = bid
        if prev and opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if bid is not None and bid > 100:
                cindy_prev = bid

    severe_need = (hp <= 3) or (no_water >= 2)
    urgent_need = (hp <= 5) or (no_water >= 1)
    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if active_threats == 0:
        if severe_need:
            return float(min(budget, 35.0))
        return float(min(budget, 8.0))

    if severe_need:
        target = 112.0
        if cindy_prev is not None:
            target = max(target, min(145.0, cindy_prev + 3.0))
        elif strongest_prev > 0:
            target = max(target, strongest_prev + 2.0)
        if tight_supply:
            target += 8.0
        return float(min(budget, target))

    if urgent_need:
        target = 78.0
        if cindy_prev is not None and tight_supply:
            target = max(target, min(132.0, cindy_prev + 1.5))
        elif strongest_prev >= 80:
            target = max(target, min(105.0, strongest_prev * 0.92))
        elif strongest_prev > 0:
            target = max(target, strongest_prev + 1.0)
        if loose_supply:
            target -= 10.0
        return float(min(budget, max(28.0, target)))

    target = 18.0
    if cindy_prev is not None:
        if loose_supply:
            target = 12.0
        elif tight_supply:
            target = 42.0
        else:
            target = 24.0
    elif strongest_prev >= 80:
        target = 16.0
    elif strongest_prev > 0:
        target = min(36.0, strongest_prev * 0.45)

    if day >= 8 and hp >= 7:
        target *= 0.85

    return float(min(budget, max(6.0, target)))
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
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    eric_bid = None
    cindy_bid = None

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if agent_id == 'Eric':
                    eric_bid = bid
                elif agent_id == 'Cindy':
                    cindy_bid = bid

    if not alive_opps:
        return min(budget, 20.0)

    scarcity = supply <= 17
    medium_tight = supply <= 19
    danger = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    highest_prev = max(prev_bids) if prev_bids else 0.0
    if eric_bid is None:
        eric_bid = min(84.0, highest_prev)
    if cindy_bid is None:
        cindy_bid = max(114.0, highest_prev)

    if critical:
        target = max(92.0, eric_bid + 6.0)
        if scarcity:
            target = max(target, min(cindy_bid + 1.0, 126.5))
        return min(budget, target)

    if danger:
        if scarcity:
            target = max(88.0, eric_bid + 4.0)
            return min(budget, target)
        target = max(74.0, eric_bid + 2.0)
        return min(budget, target)

    if scarcity:
        target = max(80.0, eric_bid + 1.5)
        if cindy_bid <= 95.0:
            target = max(target, cindy_bid + 1.0)
        return min(budget, target)

    if medium_tight:
        target = max(58.0, min(eric_bid - 3.0, 78.0))
        return min(budget, target)

    if hp >= 7 and budget < DAILY_SALARY * 8:
        return min(budget, 18.0)

    if day >= 8 and hp >= 6:
        return min(budget, 24.0)

    return min(budget, 28.0)
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    opp_urgencies = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            urg = 0.0
            if opp.get('no_water_days', 0) >= 2:
                urg += 2.0
            elif opp.get('no_water_days', 0) == 1:
                urg += 1.0
            if opp.get('hp', 10) <= 2:
                urg += 2.0
            elif opp.get('hp', 10) <= 4:
                urg += 1.0
            opp_urgencies.append(urg)

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_urg = max(opp_urgencies) if opp_urgencies else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_risk = 0.0
    if no_water >= 2:
        my_risk += 2.5
    elif no_water == 1:
        my_risk += 1.2
    if hp <= 2:
        my_risk += 2.5
    elif hp <= 4:
        my_risk += 1.2

    base = 16.0 + 18.0 * scarcity

    if my_risk >= 4.0:
        target = max(base + 30.0, highest_prev + 8.0, 62.0)
    elif my_risk >= 2.0:
        target = max(base + 16.0, avg_prev + 4.0, 42.0)
    else:
        if supply >= 22 and max_urg < 2.0:
            target = min(base, max(10.0, avg_prev * 0.55))
        elif supply >= 19:
            target = max(base, avg_prev * 0.72)
        else:
            target = max(base + 8.0, avg_prev * 0.88)
            if max_urg >= 2.0:
                target = max(target, highest_prev + 2.0)

    if day >= 8 and hp > 4 and no_water == 0:
        target *= 0.92

    reserve = 0.0
    if day <= 7:
        reserve = 25.0
    elif day <= 9:
        reserve = 10.0

    spend_cap = max(0.0, budget - reserve)
    if my_risk >= 2.0:
        spend_cap = budget

    bid = min(target, spend_cap if spend_cap > 0 else budget)

    if my_risk == 0.0 and highest_prev >= 120.0 and supply >= 20:
        bid = min(bid, 22.0)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    live_prev_bids = []
    urgent_opps = 0
    rich_opps = 0
    max_opp_budget = 0.0

    for oid, opp in alive:
        obudget = opp.get('budget', 0.0)
        if obudget > max_opp_budget:
            max_opp_budget = obudget
        if obudget >= DAILY_SALARY * 2:
            rich_opps += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 3:
            urgent_opps += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('alive'):
                    live_prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_live_prev = max(live_prev_bids) if live_prev_bids else highest_prev

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    scarcity = 1.0 - supply_ratio
    pressure_bid = highest_live_prev
    if pressure_bid <= 0:
        pressure_bid = DAILY_SALARY * 0.55

    if supply >= 24:
        base = DAILY_SALARY * 0.32
    elif supply >= 22:
        base = DAILY_SALARY * 0.42
    elif supply >= 19:
        base = DAILY_SALARY * 0.58
    elif supply >= 17:
        base = DAILY_SALARY * 0.74
    else:
        base = DAILY_SALARY * 0.9

    target = max(base, pressure_bid * (0.72 + 0.18 * scarcity))

    if hp >= 8 and no_water_days == 0 and supply >= 21:
        target *= 0.72
    if hp <= 5:
        target = max(target, pressure_bid + 3.0)
    if hp <= 3 or no_water_days >= 2:
        target = max(target, pressure_bid + 10.0, DAILY_SALARY * 1.08)
    elif no_water_days >= 1:
        target = max(target, pressure_bid + 5.0, DAILY_SALARY * 0.92)

    if urgent_opps >= 2 and supply <= 18:
        target += 8.0
    if rich_opps == 0 and hp >= 7 and no_water_days == 0:
        target *= 0.9

    if budget < DAILY_SALARY:
        target = min(target, budget)
    else:
        reserve_days = 10 - day
        soft_cap = budget / max(1, reserve_days)
        target = min(target, max(soft_cap * 1.35, DAILY_SALARY * 0.35))

    if max_opp_budget < budget * 0.5 and hp >= 6:
        target *= 0.92

    bid = max(0.0, min(budget, round(target, 2)))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    needy_pressure = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            opp_hp = opp.get('hp', 10)
            opp_nw = opp.get('no_water_days', 0)
            if opp_hp <= 3 or opp_nw >= 2:
                needy_pressure += 1.0

    if not alive:
        return max(0.0, min(budget, 18.0))

    high_supply = supply >= 22.0
    low_supply = supply <= 17.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
    if low_supply:
        urgency += 2
    elif not high_supply:
        urgency += 1
    if day >= 8:
        urgency += 1

    if high_supply:
        base = 22.0
    elif low_supply:
        base = 58.0
    else:
        base = 38.0

    if highest_prev > 0:
        if urgency <= 1:
            target = min(base, avg_prev * 0.45)
        elif urgency <= 3:
            target = max(base, min(highest_prev * 0.72, highest_prev - 18.0))
        else:
            target = max(base + 18.0, min(highest_prev + 4.0, DAILY_SALARY * 1.55))
    else:
        target = base + urgency * 8.0

    target += needy_pressure * 3.0

    if hp <= 2 or no_water >= 2:
        target = max(target, 92.0)
    if hp <= 1:
        target = max(target, 120.0)
    if low_supply and (hp <= 4 or no_water >= 1):
        target = max(target, 88.0)

    if budget < 60:
        target = min(target, budget)
    elif budget < 120:
        target = min(target, budget * 0.82)
    else:
        target = min(target, budget * 0.58 + 22.0)

    if high_supply and urgency == 0:
        target = min(target, 26.0)

    if target < 0:
        target = 0.0
    return max(0.0, min(float(budget), float(target)))
"""
