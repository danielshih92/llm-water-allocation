# ============================================================
# Experiment: exp_060
# Agent: Alex
# Source: exp_060
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
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return min(budget, 45)
        if supply >= 22:
            return min(budget, 18)
        return min(budget, 28)

    prev_bids = []
    desperate_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid'))

    max_prev_bid = max(prev_bids) if prev_bids else None

    if hp <= 1:
        base = 68
    elif no_water >= 2:
        base = 64
    elif hp <= 2:
        base = 58
    elif no_water >= 1:
        base = 48
    else:
        if supply >= 23:
            base = 20
        elif supply >= 20:
            base = 28
        elif supply >= 17:
            base = 36
        else:
            base = 44

    pressure = desperate_opponents * 3 + rich_opponents * 2
    if supply <= 16:
        pressure += 5
    elif supply >= 23:
        pressure -= 4

    bid = base + pressure

    if max_prev_bid is not None:
        if hp <= 2 or no_water >= 2:
            bid = max(bid, max_prev_bid + 2)
        elif max_prev_bid <= 25 and supply >= 20:
            bid = max(bid, max_prev_bid + 1)
        elif max_prev_bid >= 60 and hp >= 4 and no_water == 0:
            bid = min(bid, 26)
        else:
            bid = max(bid, min(max_prev_bid + 1.5, 55))

    if budget < bid:
        if hp <= 2 or no_water >= 2:
            return max(0, budget)
        return max(0, min(budget, bid))

    return max(0, min(budget, bid))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    high_threat_bids = []
    threat_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 70.0:
                    high_threat_bids.append(float(bid))
            if opp.get('budget', 0) > 300 and opp.get('hp', 0) > 2:
                threat_count += 1

    if not alive:
        return float(min(budget, 10.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_high = sum(high_threat_bids) / len(high_threat_bids) if high_threat_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgent = False
    if hp <= 2 or no_water_days >= 1:
        urgent = True

    very_urgent = False
    if hp <= 1 or no_water_days >= 2:
        very_urgent = True

    if very_urgent:
        target = max(96.0, highest_prev + 2.0)
    elif urgent:
        if highest_prev >= 85.0:
            target = highest_prev + 1.5
        else:
            target = 82.0 + 10.0 * scarcity
    else:
        if supply >= 22:
            target = 12.0
        elif supply >= 19:
            target = 24.0 + 8.0 * scarcity
        else:
            if highest_prev >= 85.0 and threat_count >= 2:
                target = 18.0
            else:
                target = 38.0 + 10.0 * scarcity

    if day >= 8 and hp <= 4:
        target = max(target, 78.0)

    if avg_high >= 95.0 and not urgent and supply <= 18:
        target = min(target, 22.0)

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    affordable = max(0.0, budget - reserve_floor)
    if urgent:
        affordable = budget

    bid = min(target, affordable if affordable > 0 else budget)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.55))
        return float(min(budget, DAILY_SALARY * 0.2))

    prev_bids = []
    dangerous_bids = []
    rich_threats = 0
    desperate_threats = 0

    for opp in alive_opponents:
        if opp.get('budget', 0) >= 200:
            rich_threats += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_threats += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 0:
                dangerous_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_danger = max(dangerous_bids) if dangerous_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = DAILY_SALARY * (0.42 + 0.18 * scarcity)

    if supply <= 17:
        base += 8.0
    elif supply >= 23:
        base -= 5.0

    if hp <= 2 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.72)

    if highest_danger >= 120:
        if hp > 4 and no_water_days == 0 and supply >= 20:
            base = min(base, DAILY_SALARY * 0.45)
        else:
            base = max(base, DAILY_SALARY * 0.88)
    elif highest_danger >= 95:
        base = max(base, min(highest_danger + 2.0, DAILY_SALARY * 0.93))
    elif highest_danger >= 60:
        base = max(base, min(highest_danger + 1.5, DAILY_SALARY * 0.82))
    elif highest_danger > 0:
        base = max(base, highest_danger + 1.0)

    if rich_threats >= 2 and supply <= 18:
        base += 6.0
    if desperate_threats >= 1 and supply <= 19:
        base += 4.0

    if day >= 8:
        base += 4.0
    if day == 10:
        base += 6.0

    if budget < DAILY_SALARY * 1.2:
        base = min(base, budget)
    else:
        base = min(base, budget, DAILY_SALARY * 1.05)

    if base < 0:
        base = 0.0

    return float(round(base, 2))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    desperation = 0
    if hp <= 2:
        desperation += 3
    elif hp <= 4:
        desperation += 2
    elif hp <= 6:
        desperation += 1

    if no_water_days >= 2:
        desperation += 3
    elif no_water_days >= 1:
        desperation += 1

    if tight_supply:
        desperation += 1

    if day >= 8:
        desperation += 1

    if desperation >= 5:
        bid = 96.0
        if highest_prev > 0:
            bid = max(bid, min(112.0, highest_prev + 2.0))
    elif desperation >= 3:
        if highest_prev >= 110:
            bid = 62.0
        elif highest_prev >= 85:
            bid = highest_prev + 1.5
        elif highest_prev > 0:
            bid = max(48.0, avg_prev + 3.0)
        else:
            bid = 52.0
    else:
        if loose_supply and hp >= 7 and no_water_days == 0:
            if highest_prev >= 110:
                bid = 16.0
            elif highest_prev >= 90:
                bid = 22.0
            else:
                bid = 28.0
        else:
            if highest_prev >= 120:
                bid = 20.0
            elif highest_prev >= 100:
                bid = 26.0
            elif highest_prev >= 80:
                bid = 34.0
            elif highest_prev > 0:
                bid = max(30.0, min(46.0, highest_prev + 1.0))
            else:
                bid = 32.0

    if rich_opp_count >= 2 and tight_supply and desperation >= 3:
        bid += 8.0
    elif urgent_opp_count >= 2 and desperation <= 2:
        bid -= 4.0

    reserve_floor = 0.0
    if hp >= 6 and no_water_days == 0:
        reserve_floor = 0.55 * DAILY_SALARY
    elif hp >= 4:
        reserve_floor = 0.35 * DAILY_SALARY
    else:
        reserve_floor = 0.15 * DAILY_SALARY

    max_affordable = budget
    if budget > reserve_floor:
        max_affordable = budget - reserve_floor + min(reserve_floor, 18.0)

    if desperation >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_aggressive = 0
    cheap_opp = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if not opp.get('alive', False):
            continue
        alive.append(opp)
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 120:
                rich_aggressive += 1
            if bid <= 30:
                cheap_opp += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            urgent_opp += 1

    if len(alive) == 0:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    abundant_supply = supply >= 23

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

    if tight_supply:
        danger += 2
    elif medium_supply:
        danger += 1

    if urgent_opp >= 2:
        danger += 1

    if day >= 8:
        danger += 1

    if danger <= 1:
        bid = 12.0 if abundant_supply else 16.0
        if cheap_opp > 0:
            bid = max(bid, 24.5)
    elif danger == 2:
        bid = 26.0 if abundant_supply else 32.0
        if cheap_opp > 0:
            bid = max(bid, highest_prev + 1.5 if highest_prev <= 35 else 32.0)
    elif danger == 3:
        bid = 42.0 if medium_supply else 50.0
        if highest_prev > 0 and highest_prev < 60:
            bid = max(bid, highest_prev + 2.0)
    elif danger == 4:
        bid = 58.0 if not tight_supply else 68.0
        if highest_prev > 0 and highest_prev < 75:
            bid = max(bid, highest_prev + 3.0)
    else:
        bid = 72.0 if not tight_supply else 84.0
        if highest_prev > 0 and highest_prev < 90:
            bid = max(bid, highest_prev + 4.0)

    if rich_aggressive >= 2 and danger <= 3:
        bid = min(bid, 34.0 if not tight_supply else 44.0)

    if avg_prev >= 100 and danger <= 2:
        bid = min(bid, 28.0)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 78.0 if tight_supply else 66.0)

    if budget < 60:
        bid = min(bid, budget)
    elif budget < 120:
        bid = min(bid, budget * 0.7)
    else:
        bid = min(bid, budget * 0.45)

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 45.0))
        return float(min(budget, 18.0))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgent = 0
    if hp <= 2:
        my_urgent += 2
    elif hp <= 4:
        my_urgent += 1
    if no_water_days >= 1:
        my_urgent += 2

    if my_urgent >= 3:
        target = max(95.0, highest_prev + 4.0)
        if rich_opp >= 1:
            target += 8.0
        if supply <= 17:
            target += 10.0
        return float(min(budget, min(150.0, target)))

    if my_urgent == 2:
        target = max(72.0, avg_prev * 0.72, highest_prev * 0.62)
        target += scarcity * 18.0
        if urgent_opp >= 2:
            target += 8.0
        return float(min(budget, min(120.0, target)))

    if supply >= 22 and hp >= 6 and no_water_days == 0:
        target = 16.0
        if highest_prev < 80:
            target = 22.0
        return float(min(budget, target))

    if supply <= 17:
        target = max(48.0, highest_prev * 0.42)
        if urgent_opp >= 1:
            target += 6.0
        if rich_opp >= 2:
            target += 6.0
        return float(min(budget, min(78.0, target)))

    target = max(28.0, avg_prev * 0.3)
    target += scarcity * 10.0
    if hp <= 5:
        target += 8.0
    return float(min(budget, min(65.0, target)))
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
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water >= 1:
            base = DAILY_SALARY * 0.6
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opp += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22

    if hp <= 2 or no_water >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 4.0)
    elif hp <= 4 or no_water >= 1:
        if supply_tight:
            bid = max(DAILY_SALARY * 0.88, highest_prev + 2.5)
        else:
            bid = max(DAILY_SALARY * 0.72, avg_prev + 2.0)
    else:
        if supply_loose and urgent_opp == 0:
            bid = DAILY_SALARY * 0.38
        elif supply_loose:
            bid = max(DAILY_SALARY * 0.48, avg_prev * 0.72)
        elif supply_tight:
            bid = max(DAILY_SALARY * 0.78, highest_prev + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.58, avg_prev + 1.0)

    if highest_prev >= 150:
        if hp >= 6 and no_water == 0 and not supply_tight:
            bid = min(bid, DAILY_SALARY * 0.42)
        else:
            bid = max(bid, DAILY_SALARY * 0.82)

    if urgent_opp >= 2:
        bid += 4.0
    elif urgent_opp == 1:
        bid += 2.0

    if rich_opp >= 2 and supply_tight:
        bid += 3.0

    max_safe = budget
    if hp >= 7 and no_water == 0:
        max_safe = min(max_safe, DAILY_SALARY * 1.05)
    else:
        max_safe = min(max_safe, DAILY_SALARY * 1.35)

    bid = max(0.0, min(bid, max_safe))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return max(0.0, min(budget, DAILY_SALARY * 0.75))
        return max(0.0, min(budget, DAILY_SALARY * 0.15))

    total_players = 1 + len(alive_opponents)
    total_req = WATER_REQ
    for req in opp_requirements:
        total_req += req

    abundance_ratio = float(supply) / float(total_req) if total_req > 0 else 0.0
    units_for_me = float(supply) / float(WATER_REQ)
    scarcity = supply <= WATER_REQ * 1.5

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

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

    if scarcity:
        urgency += 2
    elif abundance_ratio < 0.45:
        urgency += 1

    if budget < DAILY_SALARY * 2:
        urgency -= 1

    if urgency <= 0:
        base = DAILY_SALARY * 0.08
    elif urgency == 1:
        base = DAILY_SALARY * 0.22
    elif urgency == 2:
        base = DAILY_SALARY * 0.38
    elif urgency == 3:
        base = DAILY_SALARY * 0.6
    elif urgency == 4:
        base = DAILY_SALARY * 0.82
    else:
        base = DAILY_SALARY * 0.97

    if prev_bids:
        if urgency <= 1 and highest_prev >= 120:
            bid = min(base, DAILY_SALARY * 0.18)
        elif urgency >= 4:
            bid = max(base, min(highest_prev + 2.0, DAILY_SALARY * 1.35))
        elif urgency >= 2:
            target = avg_prev * 0.72
            bid = max(base, min(target, highest_prev - 8.0 if highest_prev > 20 else base))
        else:
            bid = base
    else:
        bid = base

    if units_for_me >= 1.8 and urgency <= 2:
        bid *= 0.6
    if units_for_me >= 1.4 and urgency <= 1:
        bid *= 0.7

    if day >= 8 and hp >= 7 and no_water_days == 0 and budget < DAILY_SALARY * 4:
        bid *= 0.75

    reserve = 0.0
    if hp <= 3 or no_water_days >= 2:
        reserve = 0.0
    elif day <= 7:
        reserve = DAILY_SALARY * 0.5
    else:
        reserve = DAILY_SALARY * 0.2

    max_affordable = max(0.0, budget - reserve)
    if max_affordable <= 0:
        return 0.0

    bid = min(bid, max_affordable)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    total_players = 1 + len(alive)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < total_players

    prev_bids = []
    threat_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
            score = float(pbid)
            if opp.get('no_water_days', 0) >= 1:
                score += 12.0
            if opp.get('hp', 10) <= 3:
                score += 10.0
            threat_bids.append(score)
            if float(pbid) >= 90.0 and opp.get('budget', 0) > 120:
                rich_aggressive += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_bids) if threat_bids else 0.0

    emergency = hp <= 2 or no_water >= 2
    urgent = hp <= 4 or no_water >= 1

    if emergency:
        bid = min(budget, max(95.0, highest_prev + 3.0, DAILY_SALARY * 1.15))
        return float(max(0.0, bid))

    if scarcity:
        if urgent:
            bid = max(78.0, highest_threat + 2.0)
            if rich_aggressive >= 2:
                bid = max(bid, 110.0)
        else:
            bid = max(42.0, min(85.0, highest_prev * 0.72 + 6.0))
            if desperate_count >= 2:
                bid += 8.0
            if supply <= 16:
                bid += 10.0
    else:
        if urgent:
            bid = max(48.0, min(88.0, highest_prev * 0.6 + 8.0))
        else:
            bid = 16.0
            if highest_prev < 40.0:
                bid = 18.0
            elif highest_prev < 80.0:
                bid = 22.0
            else:
                bid = 26.0
            if supply >= 23:
                bid -= 4.0

    if day >= 8 and hp >= 6 and no_water == 0:
        bid *= 0.9

    if budget < 40:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, 140.0)

    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    reqs = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            reqs.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if not alive:
        return max(0.0, min(budget, 5.0))

    total_req = WATER_REQ
    for r in reqs:
        total_req += r

    scarcity = 0.0
    if total_req > 0:
        scarcity = max(0.0, min(1.0, 1.0 - (float(supply) / float(total_req))))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    if hp <= 2 or no_water >= 2:
        target = max(128.0, highest_prev + 1.0)
    elif hp <= 4 or no_water >= 1:
        target = max(95.0, avg_prev * 0.9, highest_prev * 0.82)
    else:
        if supply <= 16:
            target = max(72.0, highest_prev * 0.62, avg_prev * 0.7)
        elif supply >= 22:
            target = max(22.0, highest_prev * 0.22)
        else:
            target = max(38.0, highest_prev * 0.36, avg_prev * 0.32)

    if day >= 8:
        target += 8.0
    if scarcity > 0.55:
        target += 12.0
    elif scarcity > 0.35:
        target += 6.0

    if budget < target:
        if hp <= 3 or no_water >= 1:
            target = budget
        else:
            target = min(budget, max(0.0, budget * 0.55))

    if hp >= 7 and no_water == 0 and supply >= 21:
        target = min(target, 35.0)

    bid = max(0.0, min(budget, target))
    return bid
"""
