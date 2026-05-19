# ============================================================
# Experiment: exp_000
# Agent: Alex
# Source: exp_000
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
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if not alive_opponents:
        return max(0, min(budget, DAILY_SALARY * 0.35))

    high_supply = supply >= 22
    low_supply = supply <= 17

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

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
        danger += 2

    pressure = 0
    if highest_prev >= DAILY_SALARY * 0.9:
        pressure += 3
    elif highest_prev >= DAILY_SALARY * 0.7:
        pressure += 2
    elif highest_prev >= DAILY_SALARY * 0.45:
        pressure += 1

    if urgent_opp >= 2:
        pressure += 1
    if rich_opp >= 2:
        pressure += 1
    if low_supply:
        pressure += 2
    elif high_supply:
        pressure -= 1

    if danger >= 5:
        target = DAILY_SALARY * 0.96
    elif danger >= 3:
        target = DAILY_SALARY * 0.82
    elif pressure >= 5:
        target = max(DAILY_SALARY * 0.72, highest_prev + 2)
    elif pressure >= 3:
        target = max(DAILY_SALARY * 0.58, avg_prev + 1.5)
    elif high_supply:
        target = DAILY_SALARY * 0.34
    else:
        target = DAILY_SALARY * 0.48

    if budget < DAILY_SALARY * 0.6 and danger <= 2:
        target = min(target, DAILY_SALARY * 0.42)
    if budget < DAILY_SALARY * 0.35:
        target = min(target, budget)

    target = max(0, min(budget, target))
    return target
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    threatening_prev = 0.0
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > threatening_prev:
                threatening_prev = float(bid)

    # Estimate competition for limited units
    units = int(supply // WATER_REQ)
    alive_count = len(alive)
    scarcity = units <= 1 or supply <= 16
    abundant = supply >= 24

    # Identify likely serious competitor from yesterday traces
    eric_bid = None
    for agent_id, opp in alive:
        if agent_id == 'Eric':
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                eric_bid = float(prev.get('bid'))

    base = 22.0
    if eric_bid is not None:
        base = eric_bid + 2.0
    elif threatening_prev > 0:
        base = min(threatening_prev + 2.0, 78.0)

    # Main policy
    if hp <= 2 or no_water >= 2:
        bid = max(base, 92.0)
    elif hp <= 4 or no_water >= 1:
        bid = max(base, 72.0 if scarcity else 58.0)
    else:
        if scarcity:
            bid = max(base, 64.0)
        elif abundant:
            bid = 26.0 if alive_count >= 2 else 18.0
        else:
            bid = max(34.0, min(base, 68.0))

    # Avoid wasting budget late if healthy
    day = day_context['day']
    if day >= 8 and hp >= 6 and no_water == 0:
        bid = min(bid, 48.0 if not scarcity else 62.0)

    # If only one meaningful rival remains, slightly undercut expensive wars when healthy
    active_threats = 0
    for agent_id, opp in alive:
        if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
            active_threats += 1
    if active_threats <= 1 and hp >= 5 and no_water == 0:
        bid = min(bid, 38.0 if not scarcity else 58.0)

    bid = max(0.0, min(float(budget), float(bid)))
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

    alive = []
    prev_bids = []
    high_spenders = 0
    mid_spenders = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 75:
                    high_spenders += 1
                elif bid >= 40:
                    mid_spenders += 1

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 25.0))
        return float(min(budget, 8.0))

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = 1.0 - max(0.0, min(1.0, supply_ratio))

    pressure = 0.0
    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        pressure = max(top_prev * 0.55, avg_prev)
    else:
        top_prev = 0.0
        avg_prev = 0.0
        pressure = 45.0

    need = 0.0
    if hp <= 2:
        need += 40.0
    elif hp <= 4:
        need += 22.0
    elif hp <= 6:
        need += 10.0

    if no_water_days >= 2:
        need += 35.0
    elif no_water_days >= 1:
        need += 18.0

    if day >= 8:
        need += 8.0

    contest_bonus = high_spenders * 6.0 + mid_spenders * 2.5

    target = 28.0 + scarcity * 22.0 + need + contest_bonus

    if pressure >= 80:
        if hp >= 7 and no_water_days == 0 and supply <= 18:
            target = min(target, 36.0)
        else:
            target = max(target, min(pressure + 2.0, 96.0))
    elif pressure >= 50:
        target = max(target, min(pressure + 1.5, 72.0))
    else:
        target = max(target, 52.0 if scarcity > 0.5 else 38.0)

    if hp >= 8 and no_water_days == 0 and supply >= 22:
        target -= 10.0

    if budget < 120:
        target = min(target, budget * 0.55 + 8.0)
    elif budget < 220:
        target = min(target, budget * 0.65)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, 88.0 if budget >= 88.0 else budget)

    target = max(0.0, min(float(budget), float(target)))
    return float(round(target, 2))
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, max(8.0, DAILY_SALARY * 0.22)))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 700:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY_PLACEHOLDER() if False else None)
    scarcity = 1.0 - ((float(supply) - 15.0) / 10.0)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency >= 3:
        target = max(DAILY_SALARY * 1.05, highest_prev + 3.0)
    elif urgency == 2:
        target = max(DAILY_SALARY * 0.82, highest_prev + 1.6)
    elif urgency == 1:
        target = max(DAILY_SALARY * 0.58 + scarcity * 10.0, avg_prev * 0.92)
    else:
        target = DAILY_SALARY * (0.34 + 0.18 * scarcity)
        if desperate_count >= 2:
            target += 6.0
        if rich_count >= 2:
            target += 4.0

    if highest_prev >= 100 and urgency == 0:
        target = min(target, DAILY_SALARY * 0.42)
    elif highest_prev >= 100 and urgency == 1:
        target = min(max(target, DAILY_SALARY * 0.62), DAILY_SALARY * 0.78)

    if day >= 8:
        target += 5.0 * urgency
    if day >= 9 and hp <= 4:
        target += 10.0

    reserve = 0.0
    if hp >= 7 and no_water == 0:
        reserve = DAILY_SALARY * 1.2
    elif hp >= 5:
        reserve = DAILY_SALARY * 0.7

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 2:
        max_affordable = budget

    bid = min(target, max_affordable)

    if urgency >= 2 and bid < DAILY_SALARY * 0.72:
        bid = min(budget, DAILY_SALARY * 0.72)
    if urgency >= 3 and bid < highest_prev + 1.0:
        bid = min(budget, highest_prev + 1.0)

    if bid < 0.0:
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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                    urgent_prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    guaranteed_units = int(supply // WATER_REQ)
    competitors = 1 + len(alive)
    tight = guaranteed_units < competitors
    very_tight = guaranteed_units <= max(0, competitors - 2)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_highest = max(urgent_prev_bids) if urgent_prev_bids else highest_prev

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1

    if not alive:
        if danger >= 2:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    base = DAILY_SALARY * 0.42

    if very_tight:
        target = max(base + 18.0, urgent_highest + 2.1, highest_prev * 0.92)
    elif tight:
        target = max(base + 8.0, highest_prev + 1.6)
    else:
        target = max(DAILY_SALARY * 0.28, highest_prev * 0.62)

    if danger >= 4:
        target = max(target, highest_prev + 3.0, DAILY_SALARY * 0.95)
    elif danger >= 2:
        target = max(target, highest_prev + 1.8, DAILY_SALARY * 0.72)
    elif hp >= 8 and no_water_days == 0 and not very_tight:
        target = min(target, DAILY_SALARY * 0.45)

    if day >= 8 and budget > DAILY_SALARY * 6:
        target += 4.0

    if highest_prev >= 130:
        if danger <= 1:
            target = min(target, DAILY_SALARY * 0.4)
        else:
            target = max(target, DAILY_SALARY * 0.88)

    target = max(0.0, min(float(budget), float(target)))
    return float(round(target, 2))
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 40)
        return min(budget, 12)

    opp_bids = []
    needy_pressure = 0
    rich_pressure = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            opp_bids.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            needy_pressure += 1
        if opp.get('budget', 0) >= budget:
            rich_pressure += 1

    highest_prev = max(opp_bids) if opp_bids else 0.0
    avg_prev = sum(opp_bids) / len(opp_bids) if opp_bids else 0.0

    supply_ratio = float(supply) / float(WATER_REQ)
    if supply_ratio <= 1.25:
        tightness = 'very_tight'
    elif supply_ratio <= 1.55:
        tightness = 'tight'
    else:
        tightness = 'loose'

    if hp <= 2 or no_water_days >= 2:
        if highest_prev > 0:
            bid = highest_prev + 6
        else:
            bid = DAILY_SALARY * 0.95
        return max(0, min(budget, bid))

    if hp <= 4 or no_water_days >= 1:
        if tightness == 'very_tight':
            bid = max(DAILY_SALARY * 0.82, highest_prev + 3)
        elif tightness == 'tight':
            bid = max(DAILY_SALARY * 0.68, avg_prev + 2)
        else:
            bid = max(DAILY_SALARY * 0.5, avg_prev * 0.9)
        return max(0, min(budget, bid))

    if tightness == 'very_tight':
        if highest_prev >= 95:
            bid = highest_prev + 1.5
        elif highest_prev >= 70:
            bid = highest_prev + 2.5
        else:
            bid = 74 + 2 * needy_pressure + rich_pressure
    elif tightness == 'tight':
        if highest_prev >= 90:
            bid = highest_prev * 0.88
        elif highest_prev >= 60:
            bid = highest_prev + 1
        else:
            bid = 52 + 2 * needy_pressure
    else:
        if highest_prev >= 85:
            bid = 38
        elif highest_prev >= 60:
            bid = 30
        else:
            bid = 22

    if day >= 8 and hp >= 6:
        bid *= 0.9
    if budget < DAILY_SALARY * 2:
        bid = min(bid, DAILY_SALARY * 0.75)
    if budget < DAILY_SALARY:
        bid = min(bid, DAILY_SALARY * 0.55)

    return max(0, min(budget, bid))
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

    alive_opps = []
    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= 500:
                rich_opp_count += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if not alive_opps:
        return min(budget, 18.0)

    units = supply / float(WATER_REQ)
    scarcity = units < (1 + len(alive_opps)) * 0.55
    ample = units >= (1 + len(alive_opps)) * 0.9

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        moderate_prev = sorted_bids[int(len(sorted_bids) // 2)]

    danger = hp <= 2 or no_water_days >= 1
    fragile = hp <= 4

    if danger:
        if highest_prev >= 100:
            bid = 92.0 if budget >= 92.0 else budget
        else:
            bid = max(62.0, highest_prev + 4.0)
        return min(budget, bid)

    if scarcity:
        if highest_prev >= 120:
            bid = 38.0 if hp >= 5 else 78.0
        elif highest_prev >= 80:
            bid = max(55.0, highest_prev + 2.0)
        elif highest_prev >= 35:
            bid = max(42.0, highest_prev + 1.5)
        else:
            bid = 36.0 + 4.0 * urgent_opp_count
        if rich_opp_count >= 2 and hp >= 5 and highest_prev >= 100:
            bid = min(bid, 34.0)
        return min(budget, bid)

    if ample:
        if highest_prev >= 100:
            bid = 12.0 if hp >= 5 else 28.0
        elif highest_prev >= 70:
            bid = 18.0 if hp >= 5 else 34.0
        else:
            bid = 22.0 if fragile else 14.0
        return min(budget, bid)

    if highest_prev >= 110:
        bid = 20.0 if hp >= 5 else 48.0
    elif highest_prev >= 80:
        bid = 30.0 if hp >= 5 else 52.0
    elif highest_prev >= 45:
        bid = max(28.0, moderate_prev + 2.0)
    else:
        bid = 24.0 if hp >= 5 else 38.0

    if day >= 8 and hp >= 5 and budget < 220:
        bid = min(bid, 26.0)
    if day >= 8 and fragile:
        bid = max(bid, 40.0)

    return min(budget, bid)
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
    prev_high = 0.0
    prev_low_supply_pressure = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid > prev_high:
                    prev_high = bid
                ps = prev.get('supply')
                if ps is not None and float(ps) <= 18.0 and bid >= 90:
                    prev_low_supply_pressure += 1

    if not alive:
        return max(0.0, min(budget, 18.0))

    affordable_income = budget + DAILY_SALARY * max(0, 10 - day)
    tight_supply = supply <= 18.0
    very_tight = supply <= 16.0

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
    if very_tight:
        urgency += 2
    elif tight_supply:
        urgency += 1

    if prev_bids:
        sorted_bids = sorted(prev_bids, reverse=True)
        top1 = sorted_bids[int(0)]
        top2 = sorted_bids[int(1)] if len(sorted_bids) > 1 else sorted_bids[int(0)]
    else:
        top1 = 80.0
        top2 = 70.0

    if urgency >= 5:
        target = max(top1 + 2.5, 118.0 if very_tight else 102.0)
    elif urgency >= 3:
        target = max(top2 + 1.5, 88.0 if tight_supply else 74.0)
    elif tight_supply:
        target = max(top2 + 1.0, 72.0)
    else:
        target = 34.0
        if prev_high >= 120.0:
            target = 28.0
        elif prev_high >= 90.0:
            target = 32.0

    if prev_low_supply_pressure >= 2 and tight_supply:
        target = max(target, top1 + 2.0)

    if budget < 90:
        if urgency >= 4:
            target = max(target, budget * 0.92)
        else:
            target = min(target, budget * 0.55)

    if affordable_income < 220 and urgency <= 2:
        target = min(target, 40.0)

    if day >= 8:
        if urgency >= 3:
            target = max(target, top2 + 2.0)
        else:
            target = max(target, 42.0)

    bid = min(budget, target)
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
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 100:
                    dangerous_prev.append(bid)

    if not alive:
        base = 18.0 if hp > 3 else 35.0
        return max(0.0, min(budget, base))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = hp <= 2 or no_water >= 1
    very_urgent = hp <= 1 or no_water >= 2

    if very_urgent:
        bid = max(90.0, highest_prev + 3.0)
        return max(0.0, min(budget, bid))

    if urgent:
        bid = 62.0 + 28.0 * scarcity
        if highest_prev > 0:
            bid = max(bid, min(highest_prev + 2.0, 115.0))
        return max(0.0, min(budget, bid))

    if supply >= 22:
        if dangerous_prev:
            bid = 16.0
        else:
            bid = max(20.0, avg_prev * 0.45)
        return max(0.0, min(budget, bid))

    if supply <= 17:
        target = 48.0 + 22.0 * scarcity
        if highest_prev > 0:
            if highest_prev <= 85.0:
                target = max(target, highest_prev + 1.5)
            else:
                target = max(42.0, highest_prev * 0.72)
        if budget < DAILY_SALARY * 2:
            target *= 0.9
        return max(0.0, min(budget, target))

    target = 34.0 + 18.0 * scarcity
    if highest_prev > 0:
        if highest_prev < 70.0:
            target = max(target, highest_prev + 1.2)
        elif highest_prev > 120.0:
            target = min(target, 46.0)
        else:
            target = max(target, highest_prev * 0.6)

    if day >= 8 and hp >= 4:
        target *= 0.9
    if budget < 140:
        target *= 0.88

    return max(0.0, min(budget, target))
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
        return float(min(budget, 1.0))

    prev_bids = []
    stressed_bids = []
    max_opp_budget = 0.0
    danger_count = 0

    for opp in alive:
        obudget = float(opp.get('budget', 0.0))
        if obudget > max_opp_budget:
            max_opp_budget = obudget

        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            b = float(bid)
            prev_bids.append(b)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                stressed_bids.append(b)
            if b >= 80:
                danger_count += 1
        else:
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                danger_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    stressed_high = max(stressed_bids) if stressed_bids else highest_prev

    high_supply = supply >= 22
    low_supply = supply <= 17

    if hp <= 2 or no_water_days >= 2:
        base = max(92.0, stressed_high + 2.0, avg_prev + 8.0)
    elif hp <= 4 or no_water_days >= 1:
        base = max(72.0, min(96.0, stressed_high + 1.5), avg_prev + 4.0)
    else:
        if high_supply:
            base = 8.0 if danger_count >= 2 else 3.0
        elif low_supply:
            if highest_prev >= 100:
                base = 18.0
            elif highest_prev >= 80:
                base = 28.0
            else:
                base = max(36.0, avg_prev * 0.55)
        else:
            if highest_prev >= 100:
                base = 12.0
            elif highest_prev >= 80:
                base = 22.0
            else:
                base = max(26.0, avg_prev * 0.5)

    if day >= 8 and hp >= 5 and budget < max_opp_budget:
        base *= 0.85

    if day <= 2 and hp == 10 and high_supply:
        base = min(base, 10.0)

    cap = budget
    if hp >= 5:
        cap = min(cap, DAILY_SALARY * 1.05)
    elif hp >= 3:
        cap = min(cap, DAILY_SALARY * 1.35)

    bid = min(cap, base)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""
