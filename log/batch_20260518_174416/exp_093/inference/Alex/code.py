# ============================================================
# Experiment: exp_093
# Agent: Alex
# Source: exp_093
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
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    players_alive = 1 + len(alive_opponents)
    supply_units = float(supply) / float(WATER_REQ)
    scarcity = supply_units < players_alive

    highest_prev_bid = 0
    aggressive_count = 0
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            if bid > highest_prev_bid:
                highest_prev_bid = bid
            if bid >= DAILY_SALARY * 0.8:
                aggressive_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * 0.96
    elif hp <= 4 or no_water_days >= 1:
        target = DAILY_SALARY * 0.82
    else:
        if scarcity:
            target = DAILY_SALARY * 0.58
            if highest_prev_bid > 0:
                target = max(target, highest_prev_bid + 1.25)
            if aggressive_count >= max(1, len(alive_opponents) // 2):
                target = max(target, DAILY_SALARY * 0.72)
            if desperate_count >= 2:
                target = max(target, DAILY_SALARY * 0.76)
        else:
            target = DAILY_SALARY * 0.28
            if highest_prev_bid >= DAILY_SALARY * 0.75:
                target = DAILY_SALARY * 0.18

    if budget < target:
        return budget
    return max(0, target)
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_threat = 0.0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > rich_threat:
                rich_threat = opp.get('budget', 0)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_tightness < 0:
        supply_tightness = 0.0
    if supply_tightness > 1:
        supply_tightness = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.65
    elif hp <= 4:
        urgency += 0.35

    if no_water >= 2:
        urgency += 0.7
    elif no_water >= 1:
        urgency += 0.3

    urgency += 0.25 * supply_tightness
    if desperate_count >= 2:
        urgency += 0.1

    if urgency >= 1.0:
        target = max(DAILY_SALARY * 1.15, highest_prev + 4.0, avg_prev + 6.0)
    elif urgency >= 0.6:
        target = max(DAILY_SALARY * 0.82, highest_prev + 2.0, avg_prev + 3.0)
    elif urgency >= 0.3:
        target = max(DAILY_SALARY * 0.52, avg_prev * 0.72, highest_prev * 0.58)
    else:
        if highest_prev >= 140:
            target = DAILY_SALARY * 0.28
        elif highest_prev >= 90:
            target = DAILY_SALARY * 0.4
        else:
            target = max(DAILY_SALARY * 0.34, avg_prev * 0.55)

    if rich_threat < budget * 0.5 and urgency < 0.6:
        target *= 0.92

    if budget < DAILY_SALARY * 1.2:
        target = min(target, budget * 0.72)
    elif budget < DAILY_SALARY * 2.5 and urgency < 0.6:
        target = min(target, DAILY_SALARY * 0.7)

    if hp >= 8 and no_water == 0 and supply >= 21:
        target = min(target, DAILY_SALARY * 0.38)

    bid = min(budget, max(0.0, target))
    return float(round(bid, 2))
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    cindy_bid = None
    max_opp_budget = 0.0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0.0) > max_opp_budget:
                max_opp_budget = opp.get('budget', 0.0)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))
                if agent_id == 'Cindy':
                    cindy_bid = prev.get('bid', 0.0)

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    effective_threat = cindy_bid if cindy_bid is not None else highest_prev

    tight_supply = supply <= 18
    medium_supply = supply <= 21
    critical = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    bid = 0.0

    if critical:
        if effective_threat >= 90:
            bid = min(budget, effective_threat + 2.0)
        elif effective_threat > 0:
            bid = min(budget, max(60.0, effective_threat + 2.0))
        else:
            bid = min(budget, 65.0)
    elif tight_supply:
        if effective_threat >= 90:
            bid = min(budget, effective_threat + 1.0)
        elif effective_threat >= 50:
            bid = min(budget, effective_threat + 2.0)
        else:
            bid = min(budget, 58.0)
    elif medium_supply:
        if pressured:
            if effective_threat >= 90:
                bid = min(budget, effective_threat + 1.0)
            elif effective_threat > 0:
                bid = min(budget, max(48.0, effective_threat + 1.5))
            else:
                bid = min(budget, 45.0)
        else:
            bid = min(budget, 18.0)
    else:
        if pressured and effective_threat > 0 and effective_threat < 80:
            bid = min(budget, max(35.0, effective_threat + 1.0))
        else:
            bid = min(budget, 8.0)

    if budget <= 0:
        return 0.0

    if hp >= 7 and no_water_days == 0 and not tight_supply and effective_threat >= 90:
        bid = min(budget, 5.0)

    return float(max(0.0, min(budget, bid)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    alive = []
    prev_bids = []
    rich_aggressive = 0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 95 and float(opp.get('budget', 0)) >= 500:
                    rich_aggressive += 1

    if not alive:
        return max(0.0, min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (25.0 - supply) / 10.0
    scarcity = max(0.0, min(1.0, scarcity))

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.6
    elif hp <= 6:
        danger += 0.25
    if no_water >= 2:
        danger += 1.0
    elif no_water >= 1:
        danger += 0.45
    if day >= 8:
        danger += 0.2

    if danger >= 1.4:
        target = max(96.0, max_prev + 4.0, avg_prev + 6.0)
    elif danger >= 0.8:
        target = max(78.0 + 10.0 * scarcity, avg_prev + 2.0)
    else:
        if supply >= 22:
            target = 16.0 + 6.0 * scarcity
        elif supply >= 19:
            target = 24.0 + 10.0 * scarcity
        else:
            target = 38.0 + 16.0 * scarcity

        if max_prev >= 110.0 and hp > 4 and no_water == 0:
            target = min(target, 22.0)
        elif max_prev >= 95.0 and hp > 5 and no_water == 0 and supply >= 19:
            target = min(target, 28.0)
        else:
            target = max(target, min(max_prev * 0.72, 72.0))

    if rich_aggressive >= 2 and danger < 0.8 and supply >= 19:
        target = min(target, 26.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 70.0 * (10 - day) * 0.22
    affordable = max(0.0, budget - reserve_floor)
    if danger >= 1.4:
        affordable = budget

    bid = min(target, affordable if affordable > 0 else budget)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, max_prev + 3.0, 98.0))
    elif hp <= 4 or no_water >= 1:
        bid = min(budget, max(bid, 82.0, avg_prev + 1.5))

    if budget < 25.0:
        bid = budget

    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    prev_bids = []
    strong_prev = 0.0
    cindy_prev = None
    david_prev = None
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        bid = None
        if prev and prev.get('bid') is not None:
            bid = float(prev.get('bid'))
            prev_bids.append(bid)
            if bid > strong_prev:
                strong_prev = bid
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp_id == 'Cindy' and bid is not None:
            cindy_prev = bid
        if opp_id == 'David' and bid is not None:
            david_prev = bid

    realistic_pressure = 0.0
    if david_prev is not None:
        realistic_pressure = max(realistic_pressure, david_prev)
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None and opp_id != 'Cindy':
            realistic_pressure = max(realistic_pressure, float(bid))

    urgent = hp <= 2 or no_water_days >= 1
    very_urgent = hp <= 1 or no_water_days >= 2
    tight_supply = slots <= 1

    if very_urgent:
        target = max(DAILY_SALARY * 0.95, realistic_pressure + 3.0)
        if cindy_prev is not None:
            target = max(target, min(cindy_prev + 1.0, budget))
        return float(min(budget, target))

    if urgent:
        if tight_supply:
            target = max(DAILY_SALARY * 0.88, realistic_pressure + 2.5)
            if cindy_prev is not None and cindy_prev <= budget * 0.9:
                target = max(target, cindy_prev + 1.0)
            return float(min(budget, target))
        target = max(DAILY_SALARY * 0.72, realistic_pressure * 0.78 + 2.0)
        return float(min(budget, target))

    if tight_supply:
        if cindy_prev is not None and cindy_prev > DAILY_SALARY * 1.8:
            target = max(DAILY_SALARY * 0.52, realistic_pressure + 1.5)
        else:
            target = max(DAILY_SALARY * 0.7, realistic_pressure + 2.0)
        if desperate_count >= 2:
            target += 6.0
        return float(min(budget, target))

    if slots >= 2:
        low_pressure = DAILY_SALARY * 0.42
        if realistic_pressure > 0:
            low_pressure = max(low_pressure, min(realistic_pressure * 0.72, DAILY_SALARY * 0.78))
        if desperate_count >= 2:
            low_pressure += 4.0
        if cindy_prev is not None and cindy_prev > 140:
            low_pressure = min(low_pressure, DAILY_SALARY * 0.6)
        return float(min(budget, low_pressure))

    return float(min(budget, DAILY_SALARY * 0.55))
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
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 140:
                rich_opp += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 5.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    my_urgent = hp <= 4 or no_water_days >= 2
    my_critical = hp <= 2 or no_water_days >= 3

    if my_critical:
        target = max(highest_prev + 8.0, 185.0)
        return float(min(budget, target))

    if my_urgent:
        target = max(highest_prev + 4.0, avg_prev + 6.0, 150.0)
        return float(min(budget, target))

    if day <= 3:
        if highest_prev >= 145:
            return float(min(budget, 8.0))
        return float(min(budget, 18.0))

    if urgent_opp > 0:
        return float(min(budget, 6.0))

    if rich_opp >= 2 and highest_prev >= 120:
        return float(min(budget, 10.0))

    if day >= 8:
        target = max(120.0, highest_prev * 0.9)
        return float(min(budget, target))

    return float(min(budget, 12.0))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    zeroish_count = 0
    desperate_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 150:
                    aggressive_count += 1
                if bid <= 1:
                    zeroish_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return float(min(budget, 40.0))
        return float(min(budget, 10.0))

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        base = 165.0 if tight_supply else 145.0
        if aggressive_count >= 2:
            base += 15.0
        return float(min(budget, base))

    if hp <= 4 or no_water >= 1:
        base = 95.0 if tight_supply else 72.0
        if aggressive_count >= 2:
            base = max(base, 110.0)
        elif prev_bids:
            observed = max(prev_bids)
            if observed < 120:
                base = max(base, observed + 3.0)
        return float(min(budget, base))

    if aggressive_count >= 2:
        if ample_supply and hp >= 7:
            return float(min(budget, 6.0))
        return float(min(budget, 14.0 if tight_supply else 9.0))

    if prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev <= 1:
            bid = 12.0 if tight_supply else 8.0
        elif highest_prev < 60:
            bid = highest_prev + 2.0
        elif highest_prev < 110:
            bid = 48.0 if ample_supply else 62.0
        else:
            bid = 18.0 if ample_supply else 28.0
    else:
        bid = 12.0 if tight_supply else 8.0

    if desperate_opp >= 2 and tight_supply:
        bid += 8.0

    if day >= 8 and hp >= 6 and no_water == 0:
        bid *= 0.8

    return float(min(budget, max(0.0, bid)))
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 8:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if budget <= 0:
        return 0.0
    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    top_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    severe_need = hp <= 2 or no_water >= 2
    moderate_need = hp <= 4 or no_water >= 1
    scarce = supply <= 17
    medium_tight = supply <= 20
    abundant = supply >= 23

    if severe_need:
        bid = max(DAILY_SALARY * 0.92, top_prev + 2.0)
        if scarce:
            bid = max(bid, DAILY_SALARY * 1.02)
        return float(min(budget, bid))

    if scarce:
        if top_prev >= DAILY_SALARY * 1.2:
            bid = DAILY_SALARY * 0.58 if hp > 5 and no_water == 0 else DAILY_SALARY * 0.9
        else:
            bid = max(DAILY_SALARY * 0.78, top_prev + 1.25)
        if urgent_opp >= 2:
            bid += 2.0
        return float(min(budget, bid))

    if medium_tight:
        if moderate_need:
            bid = max(DAILY_SALARY * 0.72, top_prev + 0.75)
        else:
            if top_prev >= DAILY_SALARY * 1.0:
                bid = DAILY_SALARY * 0.42
            else:
                bid = max(DAILY_SALARY * 0.5, avg_prev * 0.9)
        return float(min(budget, bid))

    if abundant:
        bid = DAILY_SALARY * 0.28
        if moderate_need:
            bid = DAILY_SALARY * 0.48
        if top_prev < DAILY_SALARY * 0.5 and rich_opp == 0:
            bid = max(bid, top_prev + 0.5)
        return float(min(budget, bid))

    bid = DAILY_SALARY * 0.4
    if moderate_need:
        bid = DAILY_SALARY * 0.6
    if top_prev >= DAILY_SALARY * 0.85:
        bid = DAILY_SALARY * 0.38 if hp > 5 and no_water == 0 else DAILY_SALARY * 0.82
    elif top_prev > 0:
        bid = max(bid, min(DAILY_SALARY * 0.68, top_prev + 0.5))

    if day >= 8 and hp <= 5:
        bid = max(bid, DAILY_SALARY * 0.72)

    return float(min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, safe_bid)))

    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0
    for opp in alive_opps:
        if opp.get('budget', 0) >= 100:
            rich_opp_count += 1
        if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            b = prev.get('bid')
            if b is not None:
                prev_bids.append(float(b))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    my_urgency = 0
    if hp <= 2:
        my_urgency += 3
    elif hp <= 4:
        my_urgency += 2
    elif hp <= 6:
        my_urgency += 1

    if no_water_days >= 2:
        my_urgency += 3
    elif no_water_days >= 1:
        my_urgency += 2

    if day >= 8:
        my_urgency += 1

    pressure = 0.0
    pressure += scarcity * 18.0
    pressure += urgent_opp_count * 4.0
    pressure += rich_opp_count * 2.0

    if highest_prev >= 120:
        market_anchor = max(112.0, highest_prev - 3.0)
    elif highest_prev >= 100:
        market_anchor = max(105.0, highest_prev + 1.5)
    elif highest_prev > 0:
        market_anchor = max(78.0, avg_prev + 8.0)
    else:
        market_anchor = 82.0

    if my_urgency >= 5:
        bid = market_anchor + 6.0 + pressure * 0.35
    elif my_urgency >= 3:
        bid = market_anchor + pressure * 0.2
    elif my_urgency >= 1:
        bid = 78.0 + pressure
    else:
        bid = 42.0 + pressure * 0.6

    if supply >= 23 and my_urgency <= 1:
        bid -= 10.0
    elif supply <= 17:
        bid += 8.0

    reserve = 0.0
    if hp >= 7 and no_water_days == 0 and day <= 6:
        reserve = 20.0
    elif hp >= 5 and no_water_days == 0:
        reserve = 10.0

    max_affordable = max(0.0, budget - reserve)
    if my_urgency >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable)

    if my_urgency >= 5 and budget >= 108.0:
        bid = max(bid, 108.0)
    elif my_urgency >= 3 and budget >= 102.0 and highest_prev >= 100.0:
        bid = max(bid, 102.0)

    bid = max(0.0, min(budget, bid))
    return float(round(bid, 2))
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

    alive_opponents = []
    prev_bids = []
    max_opp_budget = 0.0
    pressure = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0.0) > max_opp_budget:
                max_opp_budget = opp.get('budget', 0.0)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 90:
                    pressure += 2
                elif bid >= 50:
                    pressure += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return min(budget, 18.0)

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

    target = 0.0

    if prev_bids:
        highest_prev = max(prev_bids)
        moderate_prev = 0.0
        for b in prev_bids:
            if b <= 95 and b > moderate_prev:
                moderate_prev = b

        if urgency >= 4:
            if highest_prev >= 110:
                target = 92.0
            elif highest_prev >= 90:
                target = highest_prev + 2.0
            else:
                target = max(58.0, highest_prev + 2.5)
        elif scarcity >= 2:
            if moderate_prev > 0:
                target = max(42.0, moderate_prev + 1.5)
            else:
                target = 46.0
        elif scarcity >= 1:
            if highest_prev >= 95:
                target = 28.0
            else:
                target = max(24.0, highest_prev * 0.72)
        else:
            if highest_prev >= 100:
                target = 8.0
            elif highest_prev >= 80:
                target = 14.0
            else:
                target = max(12.0, highest_prev * 0.45)
    else:
        if urgency >= 4:
            target = 65.0
        elif scarcity >= 2:
            target = 40.0
        elif scarcity >= 1:
            target = 26.0
        else:
            target = 14.0

    if pressure >= 3 and urgency <= 2 and scarcity == 0:
        target *= 0.65
    elif pressure >= 3 and urgency >= 4:
        target = max(target, 78.0)

    reserve_floor = DAILY_SALARY * 2.2
    if budget < reserve_floor and urgency <= 2:
        target *= 0.8
    if budget < DAILY_SALARY and urgency <= 1:
        target *= 0.7

    if hp <= 2 or no_water >= 2:
        target = max(target, 88.0)

    if supply >= 23 and urgency <= 2:
        target *= 0.75

    if max_opp_budget > budget * 2 and urgency <= 2:
        target *= 0.85

    if target < 0:
        target = 0.0

    return float(min(budget, round(target, 2)))
"""
