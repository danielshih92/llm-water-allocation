# ============================================================
# Experiment: exp_021
# Agent: Alex
# Source: exp_021
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
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
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            if opp.get('budget', 0) >= DAILY_SALARY * 4:
                rich_opp += 1
            prev = opp.get('previous_trace') or {}
            bid = prev.get('bid')
            err = prev.get('error')
            if bid is not None and not err:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 21)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    my_urgent = 0
    if hp <= 2 or no_water_days >= 2:
        my_urgent = 1
    elif hp <= 4 or no_water_days >= 1:
        my_urgent = 0.5

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if my_urgent >= 1:
        target = max(58.0, highest_prev + 2.0)
        if supply <= 18:
            target = max(target, 64.0)
        return min(budget, round(target, 2))

    base = 24.0 + 18.0 * scarcity
    base += 4.0 * urgent_opp
    base += 2.0 * rich_opp

    if prev_bids:
        if supply <= 18:
            target = max(base, highest_prev + 1.5)
        else:
            target = max(base, avg_prev + 1.0)
    else:
        target = base

    if hp >= 8 and no_water_days == 0 and supply >= 22:
        target *= 0.78
    elif hp >= 6 and supply >= 20:
        target *= 0.9

    if day >= 8:
        target += 4.0
    if budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.55)

    target = max(8.0, min(target, DAILY_SALARY * 0.95, budget))
    return round(target, 2)
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
    supply = float(day_context['supply'])
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
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.6
        return max(0.0, min(float(budget), float(base)))

    prev_bids = []
    urgent_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    scarcity = 1.0 - supply_ratio

    if hp <= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.9, highest_prev + 1.5)
    elif no_water_days == 1 or hp <= 4:
        bid = max(DAILY_SALARY * (0.68 + 0.18 * scarcity), avg_prev + 1.0)
    else:
        bid = DAILY_SALARY * (0.32 + 0.28 * scarcity)
        if highest_prev > 0:
            target = avg_prev + 1.0
            cap = DAILY_SALARY * (0.62 + 0.12 * scarcity)
            if target > bid:
                bid = min(target, cap)

    if urgent_count >= 2:
        bid += 4.0 * scarcity
    elif urgent_count == 1:
        bid += 2.0 * scarcity

    if rich_count >= 2 and scarcity > 0.5:
        bid += 3.0

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.92

    if budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.72)
    elif budget < DAILY_SALARY * 4:
        bid = min(bid, budget * 0.55)

    min_survival_bid = 0.0
    if hp <= 3:
        min_survival_bid = DAILY_SALARY * 0.75
    elif no_water_days >= 1:
        min_survival_bid = DAILY_SALARY * 0.58

    if bid < min_survival_bid:
        bid = min_survival_bid

    if supply >= 23 and hp >= 7 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.34)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
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

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= 120:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                b = float(prev.get('bid', 0.0))
            except Exception:
                b = 0.0
            if b >= 0:
                prev_bids.append(b)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.55
    elif hp <= 4:
        danger += 0.3
    if no_water_days >= 1:
        danger += 0.25
    if no_water_days >= 2:
        danger += 0.2

    pressure = 0.0
    if highest_prev >= 130:
        pressure = 0.9
    elif highest_prev >= 100:
        pressure = 0.72
    elif highest_prev >= 70:
        pressure = 0.55
    elif highest_prev >= 35:
        pressure = 0.35
    else:
        pressure = 0.18

    pressure += 0.08 * urgent_opp
    pressure += 0.03 * rich_opp
    pressure += 0.18 * scarcity

    target_frac = 0.18 + 0.42 * pressure + danger

    if supply >= 22:
        target_frac -= 0.1
    elif supply <= 17:
        target_frac += 0.12

    if day >= 8:
        target_frac += 0.08

    if hp >= 8 and budget < 140:
        target_frac -= 0.08

    if target_frac < 0.12:
        target_frac = 0.12
    if target_frac > 0.98:
        target_frac = 0.98

    bid = DAILY_SALARY * target_frac

    if highest_prev > 0:
        if hp <= 4 or no_water_days >= 1 or supply <= 17:
            bid = max(bid, min(highest_prev + 3.0, DAILY_SALARY * 1.35))
        elif supply >= 22 and hp >= 7:
            bid = min(bid, avg_prev * 0.75 + 2.0)

    if hp <= 2:
        bid = max(bid, 78.0)
    if no_water_days >= 2:
        bid = max(bid, 90.0)

    if budget < bid:
        bid = budget

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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    prev_bids = []
    urgent_opp_bids = []
    rich_count = 0
    urgent_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if float(opp.get('budget', 0)) >= 120:
                rich_count += 1
            opp_urgent = float(opp.get('hp', 0)) <= 3 or int(opp.get('no_water_days', 0)) >= 1
            if opp_urgent:
                urgent_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                b = float(bid)
                prev_bids.append(b)
                if opp_urgent:
                    urgent_opp_bids.append(b)

    if budget <= 0:
        return 0.0

    guaranteed_units = int(supply // WATER_REQ)
    tight = guaranteed_units <= 1
    very_tight = supply <= 16
    loose = supply >= 24

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 45.0))
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else highest_prev

    if hp <= 2 or no_water_days >= 2:
        base = max(92.0, urgent_prev + 2.5)
        if very_tight:
            base = max(base, 108.0)
        return float(min(budget, base))

    if hp <= 4 or no_water_days >= 1:
        if tight:
            base = max(78.0, urgent_prev + 1.5)
            if rich_count >= 2:
                base += 6.0
            return float(min(budget, base))
        base = max(52.0, highest_prev * 0.72)
        return float(min(budget, base))

    if loose and hp >= 7:
        return float(min(budget, 12.0))

    if tight:
        if highest_prev >= 130.0:
            base = 46.0 if hp >= 7 else 72.0
        elif highest_prev >= 110.0:
            base = 58.0 if hp >= 7 else 76.0
        else:
            base = max(54.0, highest_prev + 1.0)
        if urgent_count >= 2:
            base += 4.0
        if day >= 8:
            base += 5.0
        return float(min(budget, base))

    base = 34.0
    if highest_prev > 0:
        base = max(base, min(62.0, highest_prev * 0.55))
    if day >= 8 and hp <= 6:
        base += 8.0
    return float(min(budget, base))
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

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    weak_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) < 120 or opp.get('hp', 0) <= 3:
                weak_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 120 and opp.get('budget', 0) >= 200:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.55
    elif hp <= 6:
        danger += 0.2

    if no_water_days >= 2:
        danger += 1.0
    elif no_water_days >= 1:
        danger += 0.45

    if supply <= 17:
        danger += 0.35
    elif supply <= 19:
        danger += 0.15

    if danger >= 1.4:
        bid = 146.0 if highest_prev >= 130 else 118.0
    elif danger >= 0.8:
        bid = 92.0 + 18.0 * scarcity
    else:
        if rich_aggressive >= 2:
            bid = 12.0 + 10.0 * scarcity
        elif highest_prev >= 120:
            bid = 18.0 + 12.0 * scarcity
        elif avg_prev >= 70:
            bid = 35.0 + 10.0 * scarcity
        else:
            bid = 48.0 + 12.0 * scarcity

    if weak_opponents >= 2 and danger < 0.8:
        bid *= 0.8

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.85

    if budget < 90:
        if danger >= 1.4:
            bid = min(bid, budget)
        else:
            bid = min(bid, max(8.0, budget * 0.45))

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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= 80:
                    dangerous_prev.append(bid)

    if not alive:
        return max(0, min(budget, 18.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0

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

    if slots >= 2:
        urgency -= 1
    else:
        urgency += 1

    if day >= 8:
        urgency += 1

    if budget <= DAILY_SALARY * 1.2:
        urgency += 1

    if urgency <= 0:
        base = 22.0 if slots >= 2 else 34.0
    elif urgency == 1:
        base = 36.0 if slots >= 2 else 52.0
    elif urgency == 2:
        base = 52.0 if slots >= 2 else 71.0
    elif urgency == 3:
        base = 69.0 if slots >= 2 else 88.0
    else:
        base = 92.0 if slots >= 2 else 111.0

    if highest_prev >= 110:
        if urgency >= 3:
            bid = max(base, highest_prev + 1.0)
        else:
            bid = min(base, 45.0)
    elif highest_prev >= 95:
        if urgency >= 2:
            bid = max(base, highest_prev + 1.5)
        else:
            bid = min(base, 50.0)
    elif highest_prev >= 75:
        bid = max(base, highest_prev + 1.0)
    elif highest_prev > 0:
        bid = max(base, avg_prev + 2.0)
    else:
        bid = base

    rich_opponents = 0
    for opp in alive:
        if opp.get('budget', 0) >= 800:
            rich_opponents += 1
    if rich_opponents >= 2 and urgency >= 2:
        bid += 4.0

    if slots >= 2 and urgency <= 1:
        bid -= 6.0

    if hp <= 1 or no_water_days >= 2:
        bid = max(bid, 118.0)

    if budget < bid:
        bid = budget

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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_pressure = 0.0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if bid > opp_pressure:
                    opp_pressure = bid

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, 45.0))
        return float(min(budget, 18.0))

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
        urgency += 0.3

    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.55

    urgency += 0.45 * scarcity

    avg_prev = 0.0
    if prev_bids:
        avg_prev = sum(prev_bids) / float(len(prev_bids))

    affordable_cap = min(budget, DAILY_SALARY * 1.15)

    if urgency >= 1.6:
        bid = max(58.0, min(affordable_cap, opp_pressure + 2.5))
    elif urgency >= 1.0:
        target = max(42.0, avg_prev * 0.55 + 6.0)
        if scarcity > 0.7:
            target += 8.0
        bid = min(affordable_cap, target)
    elif urgency >= 0.5:
        target = 24.0 + 16.0 * scarcity
        if opp_pressure > 120:
            target -= 6.0
        bid = min(budget, max(16.0, target))
    else:
        target = 12.0 + 10.0 * scarcity
        if opp_pressure > 110:
            target = min(target, 14.0)
        bid = min(budget, max(8.0, target))

    if day >= 8:
        bid = min(budget, bid + 6.0)
    if hp <= 2:
        bid = min(budget, max(bid, 63.0))
    if no_water >= 2:
        bid = min(budget, max(bid, 66.0))

    if budget < 25:
        bid = min(budget, max(0.0, budget))

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

    alive = []
    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 140:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    high_supply = supply >= 22
    low_supply = supply <= 17

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

    pressure = 0
    if highest_prev >= 120:
        pressure += 3
    elif highest_prev >= 85:
        pressure += 2
    elif highest_prev >= 45:
        pressure += 1
    pressure += min(desperate_opp, 2)
    if rich_opp >= 2:
        pressure += 1

    if urgency >= 5:
        bid = max(90.0, highest_prev + 2.0)
    elif urgency >= 3:
        if high_supply:
            bid = max(42.0, avg_prev + 2.0)
        else:
            bid = max(68.0, highest_prev + 1.5)
    else:
        if pressure >= 4 and not high_supply:
            bid = 8.0 if hp >= 5 else 28.0
        elif pressure >= 3:
            bid = 18.0 if high_supply else 26.0
        elif high_supply:
            bid = max(22.0, min(38.0, avg_prev + 1.0))
        elif low_supply:
            bid = max(30.0, min(52.0, highest_prev * 0.55 + 6.0))
        else:
            bid = max(25.0, min(44.0, avg_prev + 1.5))

    if day >= 8:
        if hp <= 5:
            bid = max(bid, 60.0)
        else:
            bid = max(bid, 28.0)

    reserve_floor = 0.0
    if hp >= 6 and day <= 6:
        reserve_floor = 20.0
    max_affordable = max(0.0, budget - reserve_floor)
    if urgency >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.75
        return float(min(budget, safe_bid))

    prev_bids = []
    urgent_prev_bids = []
    conservative_prev_bids = []

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_prev_bids.append(float(bid))
            else:
                conservative_prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_urgent_prev = max(urgent_prev_bids) if urgent_prev_bids else highest_prev
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    my_urgency = 0
    if hp <= 2:
        my_urgency += 3
    elif hp <= 4:
        my_urgency += 2
    elif hp <= 6:
        my_urgency += 1

    if no_water_days >= 1:
        my_urgency += 2

    if supply <= 16:
        market_pressure = 3
    elif supply <= 19:
        market_pressure = 2
    else:
        market_pressure = 1

    if day >= 8:
        my_urgency += 1

    if my_urgency >= 4:
        target = max(0.92 * DAILY_SALARY, highest_urgent_prev + 2.0, avg_prev * 0.95)
    elif my_urgency >= 2:
        if market_pressure >= 2:
            target = max(0.72 * DAILY_SALARY, highest_prev * 0.78 + 1.0, avg_prev * 0.82)
        else:
            target = max(0.58 * DAILY_SALARY, avg_prev * 0.7)
    else:
        if market_pressure >= 3:
            target = max(0.52 * DAILY_SALARY, highest_prev * 0.52)
        elif market_pressure == 2:
            target = max(0.42 * DAILY_SALARY, avg_prev * 0.45)
        else:
            target = DAILY_SALARY * 0.28

    rich_threats = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > budget and opp.get('hp', 0) <= 4:
            rich_threats += 1
    if rich_threats >= 2 and my_urgency >= 2:
        target += 6.0

    if budget < DAILY_SALARY * 1.2:
        target = min(target, budget * 0.72 + 4.0)

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgent = hp <= 3 or no_water_days >= 2
    my_semi_urgent = hp <= 5 or no_water_days >= 1

    if my_urgent:
        target = max(95.0, highest_prev + 3.0)
        if rich_opp >= 2:
            target = max(target, 112.0)
        if supply <= 17:
            target += 10.0
    elif my_semi_urgent:
        target = 62.0 + 28.0 * scarcity
        if highest_prev >= 100.0:
            target = max(target, highest_prev - 6.0)
        elif highest_prev >= 75.0:
            target = max(target, highest_prev - 10.0)
    else:
        if supply >= 22:
            target = 18.0 + 6.0 * scarcity
        elif supply >= 19:
            target = 26.0 + 10.0 * scarcity
        else:
            target = 38.0 + 18.0 * scarcity

        if avg_prev >= 120.0:
            target = min(target, 42.0)
        elif avg_prev >= 85.0 and supply >= 20:
            target = min(target, 36.0)

        if urgent_opp >= 2 and supply <= 18:
            target += 8.0

    if day >= 8:
        target += 6.0 if my_semi_urgent else 2.0

    if budget < 120:
        target = min(target, budget * 0.72)
    elif budget < 220:
        target = min(target, budget * 0.82)
    else:
        target = min(target, budget * 0.9)

    if target < 0:
        target = 0.0
    if target > budget:
        target = budget

    return float(target)
"""
