# ============================================================
# Experiment: exp_063
# Agent: Alex
# Source: exp_063
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
    desperate_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if not alive_opponents:
        return max(0, min(budget, 18.0))

    scarcity = supply / float(WATER_REQ * (len(alive_opponents) + 1))
    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(60.0, highest_prev + 3.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(46.0, avg_prev + 2.0, highest_prev * 0.92)
    else:
        if scarcity < 0.7:
            bid = max(40.0, highest_prev + 1.5)
        elif scarcity < 1.0:
            bid = max(30.0, avg_prev + 1.0, highest_prev * 0.8)
        else:
            bid = max(16.0, avg_prev * 0.7)

    if desperate_count >= 2:
        bid += 4.0
    elif desperate_count == 1:
        bid += 2.0

    if supply >= 24 and hp >= 5 and no_water_days == 0:
        bid *= 0.8
    elif supply <= 16:
        bid += 4.0

    max_safe = budget
    if hp > 4 and no_water_days == 0:
        max_safe = min(max_safe, 52.0)
    elif hp > 2:
        max_safe = min(max_safe, 64.0)

    bid = min(bid, max_safe)
    bid = max(0.0, bid)
    return bid
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    aggressive_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('hp', 0) > 0 and opp.get('budget', 0) > 0:
                    aggressive_bids.append(bid)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.25)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_aggressive = max(aggressive_bids) if aggressive_bids else highest_prev

    tight_supply = supply <= 17
    ample_supply = supply >= 22
    critical = hp <= 3 or no_water_days >= 1
    very_critical = hp <= 2 or no_water_days >= 2

    if very_critical:
        target = max(DAILY_SALARY * 1.55, highest_aggressive + 6.0)
    elif critical:
        target = max(DAILY_SALARY * 1.25, highest_aggressive + 3.0)
    elif tight_supply:
        target = max(DAILY_SALARY * 1.1, highest_aggressive + 2.0)
    elif ample_supply:
        target = max(DAILY_SALARY * 0.45, highest_aggressive * 0.72)
    else:
        target = max(DAILY_SALARY * 0.7, highest_aggressive * 0.88)

    if budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.72)

    if day >= 8 and hp > 5 and not tight_supply:
        target = min(target, DAILY_SALARY * 0.6)

    if hp >= 8 and no_water_days == 0 and ample_supply and highest_aggressive >= 120:
        target = min(target, DAILY_SALARY * 0.5)

    bid = min(budget, max(0.0, target))
    return bid
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

    day = day_context['day']
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
        safe_bid = min(budget, DAILY_SALARY * 0.28)
        if hp <= 3 or no_water_days >= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.65)
        return max(0.0, float(round(safe_bid, 2)))

    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= 500:
            rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    scarcity = 1.0 - supply_ratio
    urgency = 0.0
    if hp <= 2:
        urgency += 0.85
    elif hp <= 4:
        urgency += 0.5
    elif hp <= 6:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days == 1:
        urgency += 0.35

    urgency += scarcity * 0.45
    urgency += min(0.25, desperate_count * 0.06)

    if highest_prev >= 150:
        pressure_bid = highest_prev * 0.72
    elif highest_prev >= 100:
        pressure_bid = highest_prev * 0.78
    elif highest_prev >= 60:
        pressure_bid = highest_prev * 0.88 + 2.0
    elif highest_prev > 0:
        pressure_bid = highest_prev + 3.0
    else:
        pressure_bid = DAILY_SALARY * 0.42

    value_bid = DAILY_SALARY * (0.26 + 0.5 * urgency)

    if scarcity < 0.25 and hp >= 6 and no_water_days == 0:
        bid = min(value_bid, avg_prev * 0.55 + 2.0 if avg_prev > 0 else DAILY_SALARY * 0.25)
    elif urgency >= 1.1:
        bid = max(value_bid, pressure_bid)
    elif urgency >= 0.7:
        bid = max(value_bid, pressure_bid * 0.92)
    else:
        bid = max(value_bid, pressure_bid * 0.72)

    if rich_aggressive >= 2 and hp >= 6 and no_water_days == 0 and scarcity < 0.5:
        bid *= 0.82

    remaining_days = max(0, 10 - int(day) + 1)
    reserve_target = remaining_days * DAILY_SALARY * 0.32
    max_affordable = budget
    if budget > reserve_target:
        max_affordable = budget - reserve_target * 0.18

    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    if max_affordable < 0:
        max_affordable = budget * 0.5

    bid = min(bid, max_affordable)

    floor_bid = 0.0
    if hp <= 2 or no_water_days >= 2:
        floor_bid = DAILY_SALARY * 0.82
    elif hp <= 4 or no_water_days == 1:
        floor_bid = DAILY_SALARY * 0.58
    elif scarcity > 0.7:
        floor_bid = DAILY_SALARY * 0.4
    else:
        floor_bid = DAILY_SALARY * 0.18

    bid = max(bid, floor_bid)
    bid = min(bid, budget)

    if bid < 0:
        bid = 0.0

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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.28
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.6
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    affordable_threats = []
    desperate_count = 0
    rich_count = 0

    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 1.5:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                bid = float(bid)
                prev_bids.append(bid)
                aff = min(float(opp.get('budget', 0)), bid + 8.0)
                affordable_threats.append(aff)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_affordable = max(affordable_threats) if affordable_threats else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_pressure = max(0.0, min(1.0, supply_pressure))

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days >= 1:
        urgency += 0.45

    urgency += 0.35 * supply_pressure
    urgency += 0.08 * desperate_count

    if day >= 8:
        urgency += 0.15

    if rich_count == 0:
        urgency -= 0.1

    urgency = max(0.0, min(1.4, urgency))

    if urgency >= 1.0:
        target = max(DAILY_SALARY * 1.08, highest_affordable + 2.5)
    elif urgency >= 0.65:
        target = max(DAILY_SALARY * 0.82, highest_prev + 2.0, highest_affordable * 0.92)
    elif urgency >= 0.35:
        target = max(DAILY_SALARY * 0.56, highest_prev * 0.72)
    else:
        target = DAILY_SALARY * (0.26 + 0.14 * supply_pressure)

    if highest_prev >= 150 and hp > 4 and no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.32)

    if budget < DAILY_SALARY * 0.9:
        target = min(target, budget)
    elif budget < DAILY_SALARY * 1.5 and urgency < 0.65:
        target = min(target, DAILY_SALARY * 0.58)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, min(budget, DAILY_SALARY * 0.95))

    bid = max(0.0, min(float(budget), float(target)))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('budget', 0) > 500 and opp.get('hp', 0) >= 7:
                rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.6
    elif hp <= 6:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days == 1:
        urgency += 0.35

    if day >= 8:
        urgency += 0.2

    pressure = 0.45 * scarcity + 0.55 * urgency

    if hp <= 2 or no_water_days >= 2:
        bid = max(58.0, min(92.0, highest_prev * 0.72 + 8.0))
    elif supply >= 23 and hp >= 7:
        bid = 8.0 + 6.0 * scarcity
    elif supply <= 17:
        bid = 28.0 + 18.0 * pressure + min(highest_prev, 90.0) * 0.12
    else:
        bid = 16.0 + 20.0 * pressure + avg_prev * 0.08

    if rich_aggressive >= 2 and hp >= 6 and supply >= 20:
        bid *= 0.72

    if highest_prev >= 140 and hp >= 5 and no_water_days == 0:
        bid *= 0.7

    soft_cap = DAILY_SALARY * 0.95
    if hp >= 5 and no_water_days == 0:
        bid = min(bid, soft_cap)

    if day == 1 and hp == 10:
        bid = min(bid, 24.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
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

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= 85 and opp.get('budget', 0) >= 300:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 2 or no_water >= 1
    semi_urgent = hp <= 4

    units = int(supply // WATER_REQ)

    if urgent:
        bid = max(92.0, max_prev + 2.5)
        if desperate_count >= 2:
            bid += 4.0
        return float(min(budget, bid))

    if units >= 1:
        if max_prev >= 100:
            bid = 24.0 if hp >= 6 else 58.0
        elif max_prev >= 90:
            bid = 28.0 if hp >= 6 else 62.0
        elif max_prev >= 75:
            bid = max(46.0, avg_prev * 0.72)
        else:
            bid = max(34.0, max_prev + 1.5)
    else:
        bid = 20.0

    if semi_urgent:
        bid += 12.0
    if desperate_count >= 2:
        bid += 6.0
    if rich_aggressive >= 2 and hp >= 6:
        bid -= 8.0

    if day >= 8 and hp >= 6:
        bid -= 6.0
    if day >= 8 and semi_urgent:
        bid += 6.0

    bid = max(0.0, bid)
    return float(min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    rich_aggressive = False
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
            if opp.get('budget', 0) > budget and opp.get('hp', 0) >= hp:
                rich_aggressive = True

    alive_count = len(alive_opps)
    if alive_count == 0:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        emergency = max(78.0, highest_prev + 8.0)
        if tight_supply:
            emergency += 18.0
        return float(min(budget, emergency))

    if hp <= 4 or no_water >= 1:
        urgent = max(52.0, avg_prev + 6.0)
        if tight_supply:
            urgent = max(urgent, highest_prev + 4.0)
        return float(min(budget, urgent))

    if ample_supply:
        bid = 24.0
        if highest_prev < 25:
            bid = 19.0
        elif highest_prev < 45:
            bid = 27.0
        else:
            bid = min(36.0, highest_prev * 0.7)
        return float(min(budget, bid))

    if tight_supply:
        bid = max(38.0, avg_prev + 3.0)
        if highest_prev > 90:
            bid = 34.0
        if rich_aggressive:
            bid += 4.0
        return float(min(budget, bid))

    bid = max(30.0, avg_prev + 2.0)
    if highest_prev >= 120:
        bid = 32.0
    elif highest_prev >= 70:
        bid = 36.0
    elif highest_prev <= 30:
        bid = 28.0

    if day >= 8 and hp >= 6:
        bid = min(bid, 30.0)

    return float(min(budget, bid))
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
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if budget <= 0:
        return 0.0

    if len(alive_opps) == 0:
        return float(min(budget, 20.0))

    prev_bids = []
    dangerous_bids = []
    weak_count = 0
    rich_danger = 0

    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 110:
                dangerous_bids.append(float(bid))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            weak_count += 1
        if opp.get('budget', 0) >= 120 and opp.get('hp', 0) > 3:
            rich_danger += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    elif hp <= 7:
        urgency += 0.2

    if no_water >= 2:
        urgency += 1.0
    elif no_water == 1:
        urgency += 0.45

    if day >= 8:
        urgency += 0.15

    if weak_count >= 2:
        urgency -= 0.1

    base = 18.0 + 32.0 * scarcity + 26.0 * urgency

    if scarcity > 0.7 or urgency > 0.9:
        target = max(base, highest_prev + 2.0)
    elif scarcity > 0.4:
        target = max(base, avg_prev * 0.82 + 4.0)
    else:
        target = base

    if rich_danger >= 2 and hp > 4 and no_water == 0 and scarcity < 0.5:
        target *= 0.72

    if hp <= 2 or no_water >= 2:
        target = max(target, 95.0)
    elif hp <= 4 or no_water == 1:
        target = max(target, 62.0)

    max_safe = budget
    if hp > 5 and no_water == 0:
        reserve = DAILY_SALARY * 2.2
        max_safe = max(0.0, budget - reserve)
        if max_safe < 20.0:
            max_safe = min(budget, 20.0)
    elif hp > 3:
        reserve = DAILY_SALARY * 1.2
        max_safe = max(0.0, budget - reserve)
        if max_safe < 35.0:
            max_safe = min(budget, 35.0)

    bid = min(target, max_safe if max_safe > 0 else budget)

    if scarcity < 0.25 and hp >= 8 and no_water == 0:
        bid = min(bid, 28.0)

    if highest_prev >= 145 and hp > 4 and no_water == 0 and scarcity < 0.8:
        bid = min(bid, 55.0)

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp_count += 1
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 3:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 20.0))

    slots = supply / WATER_REQ
    tight_supply = slots < 2.0
    very_tight_supply = slots < 1.5

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    if danger >= 6:
        target = max(95.0, highest_prev + 3.0)
    elif danger >= 4:
        target = max(72.0, avg_prev + 2.0, highest_prev * 0.92)
    elif danger >= 2:
        target = max(48.0, avg_prev * 0.72)
    else:
        target = 24.0 if not tight_supply else 38.0

    if highest_prev >= 110:
        if danger <= 2:
            target = min(target, 34.0)
        else:
            target = max(target, 88.0)
    elif highest_prev >= 95:
        if danger <= 1:
            target = min(target, 30.0)
        else:
            target = max(target, 76.0)
    elif highest_prev >= 75:
        if danger >= 4:
            target = max(target, highest_prev + 1.5)
        else:
            target = max(target, 44.0)

    if rich_opp_count == 0 and danger <= 3:
        target *= 0.9

    if day >= 8 and hp > 5 and no_water_days == 0 and budget < 220:
        target *= 0.85

    if budget < 60:
        target = min(target, budget)
    elif budget < 120:
        target = min(target, budget * 0.85)
    else:
        target = min(target, budget * 0.7)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, min(budget, 98.0))

    if target < 0:
        target = 0.0
    if target > budget:
        target = budget

    return float(round(target, 2))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units <= 1.05:
        scarcity = 2
    elif units <= 1.55:
        scarcity = 1

    opp_bids = []
    desperate_affordable = []
    rich_pressure = []
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            opp_bids.append(float(pbid))
        risk = 0
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 2:
            risk = 1
        afford = min(float(opp.get('budget', 0.0)), float(opp.get('daily_salary', DAILY_SALARY)) * 1.6)
        if risk:
            desperate_affordable.append(afford)
        if opp.get('budget', 0.0) >= 140:
            rich_pressure.append(afford)

    highest_prev = max(opp_bids) if opp_bids else 0.0
    highest_desperate = max(desperate_affordable) if desperate_affordable else 0.0
    highest_rich = max(rich_pressure) if rich_pressure else 0.0

    urgency = 0
    if no_water_days >= 2 or hp <= 2:
        urgency = 2
    elif no_water_days >= 1 or hp <= 4:
        urgency = 1

    base = 0.0
    if urgency == 2:
        base = 96.0
        if scarcity == 2:
            base = 118.0
    elif urgency == 1:
        base = 58.0
        if scarcity == 2:
            base = 84.0
        elif scarcity == 1:
            base = 68.0
    else:
        if scarcity == 2:
            base = 44.0
        elif scarcity == 1:
            base = 28.0
        else:
            base = 12.0

    target = base
    if highest_prev > 0:
        if urgency >= 1 or scarcity >= 1:
            target = max(target, min(highest_prev + 2.0, 112.0))
        else:
            target = max(target, min(highest_prev * 0.45, 36.0))

    if highest_desperate > 0 and (urgency >= 1 or scarcity == 2):
        target = max(target, min(highest_desperate + 1.0, 120.0))

    if highest_rich > 0 and urgency == 0 and scarcity == 0:
        target = min(target, 18.0)

    if day >= 8:
        if urgency >= 1:
            target += 10.0
        else:
            target += 4.0

    reserve_floor = 0.0
    if hp > 4 and no_water_days == 0:
        reserve_floor = DAILY_SALARY * 0.35
    elif hp > 2:
        reserve_floor = DAILY_SALARY * 0.2

    max_spend = budget - reserve_floor
    if urgency == 2:
        max_spend = budget
    elif urgency == 1:
        max_spend = max(max_spend, budget * 0.7)

    if max_spend < 0:
        max_spend = 0.0

    bid = min(target, max_spend)

    if urgency == 0 and scarcity == 0 and highest_prev >= 120:
        bid = min(bid, 10.0)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
"""
