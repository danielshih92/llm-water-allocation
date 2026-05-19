# ============================================================
# Experiment: exp_069
# Agent: Alex
# Source: exp_069
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
    urgent_opp_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    players = 1 + len(alive_opponents)
    capacity = supply / float(WATER_REQ)
    scarcity = capacity < players

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, DAILY_SALARY * 0.75)
        return min(budget, DAILY_SALARY * 0.25)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    danger = 0
    if hp <= 2:
        danger += 2
    elif hp <= 4:
        danger += 1
    if no_water_days >= 1:
        danger += 2
    if scarcity:
        danger += 1
    if urgent_opp_count > 0:
        danger += 1

    if danger >= 4:
        target = max(DAILY_SALARY * 0.9, highest_prev + 2)
    elif danger >= 2:
        target = max(DAILY_SALARY * 0.62, avg_prev + 1.5, highest_prev * 0.92)
    else:
        if scarcity:
            target = max(DAILY_SALARY * 0.48, avg_prev + 1)
        else:
            target = DAILY_SALARY * 0.32

    if highest_prev >= DAILY_SALARY * 0.9 and hp > 3 and no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.4)

    reserve_floor = 0
    if hp <= 3 or no_water_days >= 1:
        reserve_floor = DAILY_SALARY * 0.85

    bid = max(target, reserve_floor)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0
    return bid
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 70 and opp.get('budget', 0) >= 120:
                    rich_aggressive += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    severe_need = hp <= 2 or no_water >= 2
    moderate_need = hp <= 4 or no_water >= 1
    tight_supply = supply <= 17.0
    ample_supply = supply >= 22.0

    if severe_need:
        bid = max(78.0, highest_prev + 3.0)
        if tight_supply:
            bid += 10.0
        return float(min(budget, bid))

    if moderate_need:
        bid = max(48.0, avg_prev + 4.0)
        if tight_supply:
            bid += 8.0
        elif ample_supply:
            bid -= 6.0
        return float(max(0.0, min(budget, bid)))

    if ample_supply:
        bid = 16.0
    elif tight_supply:
        bid = 34.0
    else:
        bid = 24.0

    if highest_prev >= 120.0:
        bid -= 6.0
    elif highest_prev <= 20.0 and urgent_opp == 0:
        bid += 4.0

    if rich_aggressive >= 2:
        bid -= 4.0
    if urgent_opp >= 2:
        bid += 8.0

    if day >= 8 and hp >= 6 and no_water == 0:
        bid -= 4.0

    return float(max(0.0, min(budget, bid)))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    cindy_prev = None
    david_prev = None

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if agent_id == 'Cindy':
                    cindy_prev = float(bid)
                if agent_id == 'David':
                    david_prev = float(bid)

    if not alive:
        return float(min(budget, 10.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 18
    medium_supply = supply <= 21

    bid = 0.0

    if no_water_days >= 2 or hp <= 3:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 6.0)
    elif no_water_days >= 1 or hp <= 5:
        if tight_supply:
            bid = max(0.82 * DAILY_SALARY, highest_prev + 4.0)
        else:
            bid = max(0.68 * DAILY_SALARY, avg_prev + 3.0)
    else:
        if tight_supply:
            bid = max(0.74 * DAILY_SALARY, highest_prev + 2.5)
        elif medium_supply:
            bid = max(0.56 * DAILY_SALARY, avg_prev + 1.5)
        else:
            bid = 0.34 * DAILY_SALARY

    if cindy_prev is not None and cindy_prev >= 150:
        if tight_supply or no_water_days >= 1 or hp <= 5:
            bid = max(bid, min(0.95 * DAILY_SALARY, cindy_prev + 1.5))
        else:
            bid = min(bid, 0.45 * DAILY_SALARY)

    if david_prev is not None and david_prev >= 90 and not tight_supply and hp >= 6 and no_water_days == 0:
        bid = min(bid, david_prev - 8.0)

    reserve_floor = 0.0
    if hp >= 6 and no_water_days == 0:
        reserve_floor = 0.18 * budget
    elif hp >= 4:
        reserve_floor = 0.08 * budget

    bid = min(bid, budget - reserve_floor)
    bid = max(0.0, bid)
    bid = min(bid, budget)

    if budget < 25:
        if no_water_days >= 1 or hp <= 4:
            bid = budget
        else:
            bid = min(bid, 0.5 * budget)

    return float(max(0.0, min(bid, budget)))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = {}
    for k, v in opponents_status.items():
        if v.get('alive'):
            alive[k] = v

    if not alive:
        return float(min(budget, 20.0 if hp > 3 else 45.0))

    opp_bids = []
    cindy_bid = None
    david_bid = None
    urgent_opp = 0
    for name, opp in alive.items():
        prev = opp.get('previous_trace', {})
        pbid = None
        if prev and prev.get('bid') is not None:
            pbid = float(prev.get('bid'))
            opp_bids.append(pbid)
        lname = str(name).lower()
        if lname == 'cindy' and pbid is not None:
            cindy_bid = pbid
        if lname == 'david' and pbid is not None:
            david_bid = pbid
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1

    high_prev = max(opp_bids) if opp_bids else 0.0
    slots = int(supply // WATER_REQ)

    if hp <= 1:
        return float(min(budget, 160.0))
    if no_water >= 2:
        return float(min(budget, 155.0))
    if hp <= 3 and no_water >= 1:
        return float(min(budget, 145.0))

    if slots >= 2:
        if hp >= 6 and no_water == 0:
            base = 62.0
            if david_bid is not None:
                base = max(base, min(88.0, david_bid - 8.0))
            if urgent_opp >= 2:
                base += 8.0
            return float(min(budget, base))
        base = 86.0
        if david_bid is not None:
            base = max(base, david_bid + 3.0)
        if cindy_bid is not None and cindy_bid > 140 and hp >= 5:
            base = min(base, 108.0)
        return float(min(budget, base))

    if cindy_bid is not None and cindy_bid >= 140 and hp >= 5 and no_water == 0:
        if david_bid is not None and david_bid < 110:
            return float(min(budget, david_bid + 4.0))
        return float(min(budget, 18.0))

    target = 96.0
    if david_bid is not None:
        target = david_bid + 4.0
    elif high_prev > 0:
        target = max(90.0, high_prev + 2.0)

    if hp <= 4 or no_water >= 1:
        target = max(target, 118.0)
    if day >= 8 and hp <= 5:
        target = max(target, 128.0)

    return float(min(budget, target))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        return float(min(budget, 25.0))

    prev_bids = []
    strong_prev_bids = []
    weak_count = 0
    urgent_opp_count = 0

    for opp in alive_opps:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opp_count += 1
        if opp.get('hp', 0) <= 3 or opp.get('budget', 0) < 80:
            weak_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) >= 100 and opp.get('hp', 0) > 3:
                strong_prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strong_highest_prev = max(strong_prev_bids) if strong_prev_bids else highest_prev

    tight_supply = supply <= 17
    loose_supply = supply >= 22
    my_urgent = hp <= 3 or no_water_days >= 2
    my_risky = hp <= 5 or no_water_days >= 1

    if my_urgent:
        target = max(110.0, strong_highest_prev + 2.0)
        if tight_supply:
            target = max(target, 145.0)
        elif loose_supply:
            target = max(target, 118.0)
    elif my_risky:
        if tight_supply:
            target = max(95.0, strong_highest_prev + 1.5)
        elif loose_supply:
            target = max(62.0, strong_highest_prev * 0.72)
        else:
            target = max(78.0, strong_highest_prev * 0.82)
    else:
        if tight_supply:
            target = max(88.0, strong_highest_prev * 0.78)
        elif loose_supply:
            target = max(38.0, strong_highest_prev * 0.42)
        else:
            target = max(58.0, strong_highest_prev * 0.58)

    if weak_count >= 2 and not my_urgent:
        target *= 0.9
    if urgent_opp_count >= 2 and tight_supply:
        target *= 1.08

    days_left = max(0, 10 - int(day))
    reserve = days_left * 18.0
    affordable = max(0.0, budget - reserve)

    if my_urgent:
        cap = budget
    else:
        cap = max(35.0, affordable + 20.0)
        cap = min(cap, budget)

    bid = min(target, cap)

    if budget < 60:
        bid = min(bid, budget)
    if not my_urgent and loose_supply and hp >= 7 and no_water_days == 0:
        bid = min(bid, 55.0)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = float(budget)

    return float(round(bid, 2))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_bids = []
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if bid >= 80:
                    aggressive_bids.append(bid)

    if not alive_opponents:
        return float(min(budget, 18.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    aggressive_pressure = len(aggressive_bids)

    tight_supply = supply <= 17
    loose_supply = supply >= 23

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

    if tight_supply:
        urgency += 2
    elif not loose_supply:
        urgency += 1

    if desperate_count >= 2:
        urgency += 1

    if day >= 8:
        urgency += 1

    reserve_floor = 0.0
    if day <= 3:
        reserve_floor = 140.0
    elif day <= 6:
        reserve_floor = 90.0
    else:
        reserve_floor = 40.0

    spendable = max(0.0, budget - reserve_floor)

    if urgency <= 1 and loose_supply:
        bid = 8.0
    elif urgency <= 2 and aggressive_pressure >= 2:
        bid = 16.0
    elif urgency <= 3:
        bid = max(22.0, min(38.0, avg_prev * 0.35 + 6.0))
    elif urgency <= 5:
        anchor = 0.0
        if highest_prev > 0:
            anchor = min(highest_prev + 2.0, 88.0)
        bid = max(48.0, anchor if anchor > 0 else 58.0)
    else:
        anchor = 0.0
        if highest_prev > 0:
            anchor = min(highest_prev + 3.0, 110.0)
        bid = max(72.0, anchor if anchor > 0 else 82.0)

    if tight_supply and urgency >= 4:
        bid += 8.0
    if loose_supply and urgency <= 2:
        bid -= 4.0

    if aggressive_pressure >= 2 and urgency <= 3:
        bid = min(bid, 24.0)

    if spendable > 0:
        bid = min(bid, max(spendable, 12.0))
    else:
        if urgency >= 5:
            bid = min(budget, max(20.0, bid))
        else:
            bid = min(budget, 12.0)

    bid = min(bid, budget)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threats = 0
    desperate_threats = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 8:
                rich_threats += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_threats += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    survival_urgency = 0.0
    if hp <= 2:
        survival_urgency += 0.7
    elif hp <= 4:
        survival_urgency += 0.35
    if no_water >= 2:
        survival_urgency += 0.6
    elif no_water >= 1:
        survival_urgency += 0.3

    if day >= 8:
        survival_urgency += 0.15

    market_pressure = 0.0
    if highest_prev >= 110:
        market_pressure += 0.45
    elif highest_prev >= 90:
        market_pressure += 0.3
    elif highest_prev >= 70:
        market_pressure += 0.18
    elif highest_prev >= 40:
        market_pressure += 0.08

    market_pressure += 0.06 * rich_threats
    market_pressure += 0.04 * desperate_threats

    score = 0.18 + 0.42 * supply_pressure + survival_urgency + market_pressure

    if supply >= 23 and survival_urgency < 0.5:
        base_bid = DAILY_SALARY * 0.28
    elif supply >= 20 and highest_prev >= 90 and survival_urgency < 0.5:
        base_bid = DAILY_SALARY * 0.22
    else:
        if score < 0.35:
            base_bid = DAILY_SALARY * 0.3
        elif score < 0.6:
            base_bid = DAILY_SALARY * 0.48
        elif score < 0.9:
            base_bid = DAILY_SALARY * 0.68
        elif score < 1.2:
            base_bid = DAILY_SALARY * 0.9
        else:
            base_bid = DAILY_SALARY * 1.12

    if highest_prev > 0:
        if survival_urgency >= 0.8 or (supply <= 17 and hp <= 4):
            target = highest_prev + 2.0
            if target > base_bid:
                base_bid = target
        elif highest_prev >= 100 and survival_urgency < 0.5:
            base_bid = min(base_bid, DAILY_SALARY * 0.35)
        elif highest_prev <= 55 and supply <= 18:
            target = highest_prev + 1.5
            if target > base_bid:
                base_bid = target
        elif avg_prev > 0 and avg_prev < 45 and supply <= 19:
            target = avg_prev + 3.0
            if target > base_bid:
                base_bid = target

    reserve = 0.0
    if day <= 6:
        reserve = DAILY_SALARY * 2.2
    elif day <= 8:
        reserve = DAILY_SALARY * 1.2
    else:
        reserve = DAILY_SALARY * 0.4

    if survival_urgency >= 0.8:
        reserve = 0.0

    max_affordable = max(0.0, budget - reserve)
    if max_affordable <= 0:
        max_affordable = min(budget, DAILY_SALARY * 0.4)

    bid = min(base_bid, budget, max_affordable)

    if hp <= 2 or no_water >= 2:
        emergency_bid = min(budget, max(DAILY_SALARY * 0.95, highest_prev + 2.0 if highest_prev > 0 else DAILY_SALARY * 0.95))
        if emergency_bid > bid:
            bid = emergency_bid

    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_threats = 0
    desperate_threats = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_threats += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_threats += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive:
        return float(min(budget, 5.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if supply <= 17:
        urgency += 2
    elif supply <= 19:
        urgency += 1
    if day >= 8 and hp <= 5:
        urgency += 1

    pressure = 0
    if highest_prev >= 130:
        pressure += 3
    elif highest_prev >= 100:
        pressure += 2
    elif highest_prev >= 70:
        pressure += 1
    pressure += min(rich_threats, 2)
    pressure += min(desperate_threats, 2)

    if urgency >= 7:
        bid = max(95.0, highest_prev + 3.0)
    elif urgency >= 5:
        bid = max(72.0, avg_prev + 6.0, highest_prev * 0.78)
    elif urgency >= 3:
        if highest_prev >= 120 and hp > 4 and no_water_days == 0 and supply >= 20:
            bid = 18.0
        else:
            bid = max(38.0, avg_prev * 0.55 + 6.0)
    else:
        if supply >= 22 and highest_prev >= 100:
            bid = 8.0
        elif supply >= 20:
            bid = 16.0 + 6.0 * (1.0 - supply_ratio)
        else:
            bid = 24.0 + 10.0 * (1.0 - supply_ratio)

    if pressure >= 5 and urgency <= 2:
        bid *= 0.7
    elif pressure >= 4 and urgency <= 4:
        bid *= 0.85

    reserve = 0.0
    if hp <= 3 or no_water_days >= 1:
        reserve = 0.0
    else:
        reserve = 35.0
    max_safe = max(0.0, budget - reserve)
    if max_safe <= 0:
        max_safe = budget

    if day == 1 and hp >= 8 and supply >= 20:
        bid = min(bid, 22.0)

    bid = min(bid, max_safe)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    threat_bids = []
    desperate_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                affordable = min(opp.get('budget', 0) + opp.get('daily_salary', 0), bid)
                threat_bids.append(affordable)

    if not alive_opponents:
        if hp <= 3 or no_water >= 2:
            return float(min(budget, 42.0))
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    tight_supply = slots <= 1
    medium_supply = slots == 2

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_bids) if threat_bids else 0.0

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

    if tight_supply:
        urgency += 2
    elif medium_supply:
        urgency += 1

    urgency += min(2, desperate_count)

    if urgency >= 6:
        target = max(63.0, highest_threat + 2.0)
    elif urgency >= 4:
        target = max(48.0, highest_threat + 1.5)
    elif urgency >= 2:
        if highest_prev >= 120:
            target = 24.0 if hp > 4 and no_water == 0 else 56.0
        else:
            target = max(30.0, highest_threat * 0.55 + 4.0)
    else:
        if highest_prev >= 120:
            target = 14.0
        elif highest_prev >= 80:
            target = 18.0
        else:
            target = max(16.0, highest_threat * 0.35 + 3.0)

    if day >= 8:
        target += 6.0
    elif day >= 6 and (hp <= 4 or no_water >= 1):
        target += 4.0

    reserve_floor = 0.0
    if day <= 5:
        reserve_floor = 35.0
    elif day <= 8:
        reserve_floor = 20.0

    max_spend = max(0.0, budget - reserve_floor)
    if urgency >= 5:
        max_spend = budget
    elif urgency >= 3:
        max_spend = max(max_spend, budget * 0.7)

    bid = min(target, max_spend, budget)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, highest_threat + 3.0, 69.0))

    if bid < 0:
        bid = 0.0

    return float(round(min(budget, bid), 2))
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

    alive = []
    prev_bids = []
    dangerous_prev = []
    weak_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('budget', 0) < 40:
                weak_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                try:
                    b = float(bid)
                    prev_bids.append(b)
                    if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                        dangerous_prev.append(b)
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    pressure_bid = max(dangerous_prev) if dangerous_prev else highest_prev

    tight_supply = (supply <= 17.0)
    abundant_supply = (supply >= 23.0)
    urgent = (hp <= 3 or no_water_days >= 1)
    critical = (hp <= 2 or no_water_days >= 2)

    if critical:
        base = max(62.0, pressure_bid + 2.5)
    elif urgent:
        base = max(48.0, pressure_bid + 1.5)
    else:
        if tight_supply:
            base = max(36.0, avg_prev * 0.88, highest_prev * 0.82)
        elif abundant_supply:
            base = max(16.0, avg_prev * 0.45)
        else:
            base = max(24.0, avg_prev * 0.62)

    if weak_count >= 2 and not urgent:
        base *= 0.82

    if highest_prev >= 145.0 and hp > 3 and no_water_days == 0 and not tight_supply:
        base = min(base, 28.0)

    if day >= 8:
        if urgent:
            base += 6.0
        else:
            base += 2.0

    if budget < 60:
        base = min(base, budget * 0.72)
    elif budget < 120:
        base = min(base, budget * 0.82)
    else:
        base = min(base, budget * 0.9)

    if urgent and budget > 0:
        floor_bid = min(budget, 44.0 if hp > 2 else 58.0)
        if base < floor_bid:
            base = floor_bid

    if base < 0:
        base = 0.0

    return float(min(budget, round(base, 2)))
"""
