# ============================================================
# Experiment: exp_080
# Agent: Alex
# Source: exp_080
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water >= 1:
            bid = min(budget, DAILY_SALARY * 0.75)
        return max(0, bid)

    prev_bids = []
    pressured_opponents = 0
    desperate_opponents = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            pressured_opponents += 1
        if opp.get('hp', 10) <= 1 or opp.get('no_water_days', 0) >= 2:
            desperate_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('error') in (None, '', False):
            prev_bids.append(prev.get('bid'))

    tight_supply = supply <= 17
    abundant_supply = supply >= 22

    if hp <= 1 or no_water >= 2:
        base = DAILY_SALARY * 0.96
    elif hp <= 2 or no_water >= 1:
        base = DAILY_SALARY * 0.82
    elif tight_supply:
        base = DAILY_SALARY * 0.62
    elif abundant_supply:
        base = DAILY_SALARY * 0.42
    else:
        base = DAILY_SALARY * 0.52

    if pressured_opponents >= 2:
        base += 5
    elif desperate_opponents == 0 and abundant_supply:
        base -= 4

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if highest_prev >= DAILY_SALARY * 0.9:
            if hp >= 4 and no_water == 0:
                bid = DAILY_SALARY * 0.28
            else:
                bid = DAILY_SALARY * 0.93
        elif highest_prev >= DAILY_SALARY * 0.7:
            if tight_supply or hp <= 3 or no_water >= 1:
                bid = min(DAILY_SALARY * 0.9, highest_prev + 2)
            else:
                bid = max(base, avg_prev + 1)
        else:
            bid = max(base, highest_prev + 1.5)
    else:
        bid = base

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.72)
    else:
        bid = min(bid, budget * 0.9)

    if hp >= 5 and no_water == 0 and abundant_supply and desperate_opponents == 0:
        bid = min(bid, DAILY_SALARY * 0.45)

    bid = max(0, min(budget, bid))
    return bid
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

    alive = []
    prev_bids = []
    max_prev = 0.0
    min_prev = None
    cindy_like = False
    aggressive_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid > max_prev:
                    max_prev = bid
                if min_prev is None or bid < min_prev:
                    min_prev = bid
                if bid >= 110:
                    cindy_like = True
                if bid >= 78:
                    aggressive_count += 1

    if not alive:
        return min(budget, 18.0)

    likely_units = int(supply / WATER_REQ)
    if likely_units < 1:
        likely_units = 1

    urgent = hp <= 3 or no_water >= 2
    pressured = hp <= 5 or no_water >= 1

    if min_prev is None:
        if urgent:
            return min(budget, 84.0)
        if likely_units >= 2:
            return min(budget, 52.0)
        return min(budget, 38.0)

    if cindy_like and not urgent:
        if likely_units >= 2:
            base = 79.5
        else:
            base = 22.0 if hp >= 6 and no_water == 0 else 81.0
        if aggressive_count <= 1:
            base = max(base, 55.0)
        return min(budget, base)

    target = max_prev + 1.5

    if likely_units >= 2:
        target -= 6.0
    if len(alive) <= 2:
        target -= 5.0
    if pressured:
        target += 4.0
    if urgent:
        target += 8.0
    if hp >= 8 and no_water == 0 and max_prev >= 84:
        target -= 12.0

    if max_prev >= 110 and urgent:
        target = 112.0
    elif max_prev >= 90 and not urgent:
        target = min(target, 60.0)

    floor_bid = 18.0
    if pressured:
        floor_bid = 48.0
    if urgent:
        floor_bid = 78.0

    bid = max(floor_bid, target)

    if bid > 120.0:
        bid = 120.0
    if budget < bid:
        if urgent:
            return max(0.0, budget)
        return max(0.0, min(budget, floor_bid))
    return max(0.0, bid)
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opps:
        if hp <= 3 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    urgent_opps = 0
    rich_opps = 0
    for opp in alive_opps:
        if opp.get('budget', 0) >= budget:
            rich_opps += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opps += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    survival_urgency = 0.0
    if hp <= 2:
        survival_urgency += 0.6
    elif hp <= 4:
        survival_urgency += 0.35
    if no_water_days >= 2:
        survival_urgency += 0.5
    elif no_water_days == 1:
        survival_urgency += 0.2
    if day >= 8:
        survival_urgency += 0.1

    pressure = avg_prev * 0.55 + highest_prev * 0.35 + urgent_opps * 4.0 + rich_opps * 2.0

    base = DAILY_SALARY * (0.22 + 0.38 * scarcity) + pressure * 0.28

    if highest_prev >= 130:
        if survival_urgency < 0.45:
            bid = DAILY_SALARY * (0.18 + 0.18 * scarcity)
        else:
            bid = max(base, highest_prev * 0.72)
    elif highest_prev >= 85:
        if survival_urgency < 0.3 and scarcity < 0.45:
            bid = DAILY_SALARY * 0.24
        else:
            bid = max(base, avg_prev + 3.0)
    else:
        bid = max(base, avg_prev + 2.0 if avg_prev > 0 else DAILY_SALARY * 0.34)

    if survival_urgency >= 0.8:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif survival_urgency >= 0.5:
        bid = max(bid, DAILY_SALARY * 0.78)
    elif survival_urgency >= 0.25:
        bid = max(bid, DAILY_SALARY * 0.58)

    if supply >= 23 and survival_urgency < 0.4:
        bid *= 0.82
    elif supply <= 17:
        bid *= 1.12

    if day == 1 and survival_urgency < 0.4:
        bid = min(bid, DAILY_SALARY * 0.5)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    if budget < reserve_floor and survival_urgency < 0.5:
        bid = min(bid, max(0.0, budget - reserve_floor * 0.35))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive_bids = []
    weak_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                weak_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= DAILY_SALARY * 0.85:
                    aggressive_bids.append(float(bid))

    if not alive:
        return max(0.0, min(float(budget), DAILY_SALARY * 0.2))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    pressure = len(aggressive_bids)
    urgent = hp <= 2 or no_water >= 1
    very_urgent = hp <= 1 or no_water >= 2

    if very_urgent:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif urgent:
        if pressure >= 2:
            target = max(DAILY_SALARY * 0.88, highest_prev + 1.0)
        else:
            target = max(DAILY_SALARY * 0.72, avg_prev + 1.5)
    else:
        if supply >= 22:
            target = DAILY_SALARY * 0.22
        elif supply >= 19:
            target = DAILY_SALARY * 0.34
        else:
            target = DAILY_SALARY * 0.48

        if pressure >= 2:
            target = min(target, DAILY_SALARY * 0.30)
        elif highest_prev > 0 and highest_prev < DAILY_SALARY * 0.65 and supply < 19:
            target = max(target, highest_prev + 1.0)

    if weak_opponents >= 1 and not urgent:
        target *= 0.92

    if day >= 8 and hp >= 4 and not urgent:
        target *= 0.9

    reserve_floor = DAILY_SALARY * 1.2 if hp > 2 else DAILY_SALARY * 0.4
    max_affordable = max(0.0, float(budget) - reserve_floor)
    if urgent:
        max_affordable = float(budget)

    bid = min(float(budget), target)
    if not urgent:
        bid = min(bid, max_affordable)

    if bid < 0:
        bid = 0.0

    if urgent and bid < DAILY_SALARY * 0.55 and budget >= DAILY_SALARY * 0.55:
        bid = DAILY_SALARY * 0.55

    return float(max(0.0, min(float(budget), bid)))
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        safe = DAILY_SALARY * 0.35
        if hp <= 3 or no_water >= 1:
            safe = DAILY_SALARY * 0.6
        return float(min(budget, safe))

    prev_bids = []
    prev_high = 0.0
    prev_low = None
    rich_threat = 0.0
    desperate_count = 0

    for opp in alive_opponents:
        obudget = opp.get('budget', 0)
        ohp = opp.get('hp', 0)
        onw = opp.get('no_water_days', 0)
        if obudget > rich_threat:
            rich_threat = obudget
        if ohp <= 3 or onw >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev.get('bid', 0.0))
            prev_bids.append(b)
            if b > prev_high:
                prev_high = b
            if prev_low is None or b < prev_low:
                prev_low = b

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    if no_water >= 2:
        urgency += 0.8
    elif no_water >= 1:
        urgency += 0.35
    urgency += scarcity * 0.55
    if desperate_count >= 2:
        urgency += 0.1

    base = DAILY_SALARY * (0.34 + 0.28 * scarcity)

    if prev_bids:
        if urgency >= 1.0:
            target = max(base + 8.0, prev_high + 2.5)
        elif urgency >= 0.55:
            target = max(base, prev_high * 0.78 + 3.0)
        else:
            target = max(base, prev_high * 0.52)
            if supply >= 22:
                target = min(target, DAILY_SALARY * 0.42)
    else:
        target = base
        if urgency >= 1.0:
            target = DAILY_SALARY * 0.88

    if rich_threat > budget * 1.8 and urgency < 0.8:
        target *= 0.92

    if day >= 8:
        target *= 1.08
    if day >= 9 and (hp <= 4 or no_water >= 1):
        target *= 1.12

    min_guard = 0.0
    if hp <= 2 or no_water >= 2:
        min_guard = DAILY_SALARY * 0.9
    elif hp <= 4 or no_water >= 1:
        min_guard = DAILY_SALARY * 0.68
    elif supply <= 17:
        min_guard = DAILY_SALARY * 0.52

    bid = max(target, min_guard)
    if prev_high >= 150 and urgency < 0.8:
        bid = min(bid, DAILY_SALARY * 0.58)

    if bid > budget:
        bid = budget
    if bid < 0:
        bid = 0.0
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_prev = 0
    desperate_opp = 0
    rich_opp = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 1.5:
                rich_opp += 1
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if b >= DAILY_SALARY * 0.9:
                    strong_prev += 1

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    slots = max(1, int(supply / WATER_REQ))
    competitors = len(alive) + 1
    scarcity = competitors - slots

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    base = DAILY_SALARY * 0.42

    if slots >= competitors:
        base = DAILY_SALARY * 0.18
    elif slots == competitors - 1:
        base = DAILY_SALARY * 0.48
    else:
        base = DAILY_SALARY * 0.62

    if supply <= 16:
        base += 10
    elif supply >= 23:
        base -= 8

    if max_prev >= 120:
        base += 6
    elif max_prev >= 90:
        base += 10
    elif max_prev <= 40 and prev_bids:
        base -= 5

    if avg_prev >= 80:
        base += 4

    if strong_prev >= 2:
        base += 6
    if desperate_opp >= 2:
        base += 5
    if rich_opp == 0:
        base -= 4

    if hp <= 2 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.68)
    elif hp >= 8 and supply >= 22:
        base -= 6

    if day >= 8 and hp > 4:
        base -= 4

    reserve = 0.0
    if hp > 4:
        reserve = DAILY_SALARY * 0.35
    affordable = max(0.0, budget - reserve)
    bid = min(base, budget)
    if affordable > 0:
        bid = min(bid, max(affordable, min(base, budget)))

    if hp <= 2 or no_water_days >= 1:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

    if bid < 0:
        bid = 0.0
    return float(round(min(bid, budget), 2))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(float(opp.get('water_requirement', WATER_REQ)))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if not alive_opponents:
        return max(0.0, min(float(budget), DAILY_SALARY * 0.35))

    total_players = 1 + len(alive_opponents)
    total_req = WATER_REQ
    for req in opp_requirements:
        total_req += req

    scarcity = total_req / max(supply, 1.0)
    high_supply = supply >= 22.0
    low_supply = supply <= 17.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1
    if low_supply:
        danger += 1
    if scarcity > 2.4:
        danger += 1

    if danger >= 4:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif danger >= 2:
        bid = max(DAILY_SALARY * 0.72, avg_prev + 2.0, highest_prev * 0.88)
    else:
        if high_supply and highest_prev >= 95.0:
            bid = DAILY_SALARY * 0.28
        elif high_supply:
            bid = DAILY_SALARY * 0.4
        elif low_supply:
            bid = max(DAILY_SALARY * 0.62, highest_prev * 0.72)
        else:
            bid = max(DAILY_SALARY * 0.5, avg_prev * 0.7)

    rich_opp_count = 0
    pressured_opp_count = 0
    for opp in alive_opponents:
        if float(opp.get('budget', 0.0)) > budget + 150:
            rich_opp_count += 1
        if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
            pressured_opp_count += 1

    if rich_opp_count >= 2 and danger <= 1:
        bid *= 0.85
    if pressured_opp_count >= 2 and danger <= 2 and not low_supply:
        bid *= 0.9

    if day >= 8:
        bid *= 1.08
    if budget < DAILY_SALARY * 2:
        bid = min(bid, DAILY_SALARY * 0.78)
    if budget < DAILY_SALARY:
        bid = min(bid, budget)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.98)

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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    ample_supply = units >= 1.8
    tight_supply = units <= 1.25

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

    market_heat = 0
    if highest_prev >= 150:
        market_heat += 3
    elif highest_prev >= 100:
        market_heat += 2
    elif highest_prev >= 60:
        market_heat += 1
    if avg_prev >= 120:
        market_heat += 1
    if desperate_count >= 2:
        market_heat += 1
    if tight_supply:
        market_heat += 1
    if ample_supply:
        market_heat -= 1

    if urgency >= 5:
        bid = max(DAILY_SALARY * 1.15, highest_prev + 6.0)
    elif urgency >= 3:
        if market_heat >= 3:
            bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
        else:
            bid = max(DAILY_SALARY * 0.72, avg_prev + 4.0)
    else:
        if market_heat >= 4:
            bid = DAILY_SALARY * 0.18
        elif market_heat >= 2:
            bid = DAILY_SALARY * 0.38
        else:
            if ample_supply:
                bid = max(DAILY_SALARY * 0.52, avg_prev + 2.0)
            else:
                bid = max(DAILY_SALARY * 0.42, avg_prev * 0.75)

    if rich_count >= 2 and urgency <= 2 and tight_supply:
        bid *= 0.75

    if day >= 8:
        bid *= 1.08
    if day >= 9 and urgency >= 2:
        bid *= 1.12

    reserve = 0.0
    days_left = max(0, 10 - day)
    if hp > 4 and no_water_days == 0:
        reserve = min(budget * 0.35, days_left * 18.0)
    max_affordable = max(0.0, budget - reserve)

    if urgency >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    req_sum = WATER_REQ
    dangerous_prev = 0.0
    eric_like_bid = None

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            req_sum += float(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                bid = float(bid)
                prev_bids.append(bid)
                if bid > dangerous_prev:
                    dangerous_prev = bid
                if oid == 'Eric':
                    eric_like_bid = bid

    scarcity = req_sum / max(supply, 1.0)
    tight = supply <= 17.0 or scarcity >= 2.2
    very_tight = supply <= 15.5 or scarcity >= 2.8

    if not alive:
        return max(0.0, min(budget, 18.0))

    if hp <= 2 or no_water >= 2:
        target = 96.0
        if prev_bids:
            target = max(target, dangerous_prev + 2.0)
        if very_tight:
            target += 10.0
        return max(0.0, min(budget, target))

    if hp <= 4 or no_water >= 1:
        anchor = 78.0
        if eric_like_bid is not None:
            anchor = max(anchor, eric_like_bid + 3.0)
        elif prev_bids:
            anchor = max(anchor, min(dangerous_prev + 2.0, 95.0))
        if tight:
            anchor += 6.0
        return max(0.0, min(budget, anchor))

    if day <= 2 and hp >= 8 and no_water == 0:
        base = 24.0 if not tight else 34.0
        return max(0.0, min(budget, base))

    if eric_like_bid is not None:
        base = eric_like_bid + 1.5
    elif prev_bids:
        sorted_bids = sorted(prev_bids)
        idx = int(len(sorted_bids) - 1)
        base = sorted_bids[int(idx)] * 0.72
    else:
        base = 42.0

    if dangerous_prev > 180.0:
        base = min(base, 58.0)
    elif dangerous_prev > 120.0:
        base = min(max(base, 52.0), 68.0)
    else:
        base = max(base, 46.0)

    if tight:
        base += 6.0
    if very_tight:
        base += 6.0
    if hp >= 8 and no_water == 0 and not tight:
        base -= 6.0

    spend_cap = budget
    if hp >= 7 and no_water == 0:
        spend_cap = min(spend_cap, DAILY_SALARY * 0.95)
    elif hp >= 5:
        spend_cap = min(spend_cap, DAILY_SALARY * 1.15)
    else:
        spend_cap = min(spend_cap, DAILY_SALARY * 1.45)

    bid = max(0.0, min(spend_cap, base))
    return bid
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
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if float(opp.get('budget', 0)) >= DAILY_SALARY * 4:
                rich_opp += 1
            if int(opp.get('hp', 0)) <= 2 or int(opp.get('no_water_days', 0)) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, 18.0))

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_pressure = max(0.0, min(1.0, supply_pressure))

    risk = 0.0
    if hp <= 1:
        risk += 1.0
    elif hp <= 2:
        risk += 0.7
    elif hp <= 4:
        risk += 0.35

    if no_water >= 2:
        risk += 0.9
    elif no_water >= 1:
        risk += 0.45

    risk += supply_pressure * 0.45
    risk += min(0.35, urgent_opp * 0.08)

    if hp <= 2 or no_water >= 2:
        target = max(62.0, max_prev + 3.0, avg_prev + 6.0)
    elif supply >= 22 and hp >= 4 and no_water == 0:
        target = 16.0 + rich_opp * 2.0
    elif supply >= 20 and max_prev > 95 and hp >= 4:
        target = 22.0
    else:
        base = 20.0 + supply_pressure * 18.0 + min(12.0, avg_prev * 0.12)
        if max_prev >= 110:
            base -= 6.0
        elif max_prev >= 80:
            base += 4.0
        base += rich_opp * 1.5
        target = base + risk * 22.0

    if day >= 8:
        target += 6.0 * risk
    if day == 10:
        target += 8.0

    min_safe = 0.0
    days_left = max(0, 10 - day)
    if days_left >= 2 and hp >= 3 and no_water == 0:
        min_safe = 0.0

    bid = min(budget - min_safe, target)
    bid = max(0.0, bid)

    if hp >= 5 and no_water == 0 and supply >= 23 and max_prev >= 100:
        bid = min(bid, 18.0)

    if hp <= 1:
        bid = min(budget, max(bid, 68.0))

    return float(round(max(0.0, min(budget, bid)), 2))
"""
