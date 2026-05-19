# ============================================================
# Experiment: exp_065
# Agent: Alex
# Source: exp_065
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
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
            alive.append(opp)

    if budget <= 0:
        return 0

    if not alive:
        if hp <= 2 or no_water >= 1:
            return min(budget, 50)
        if supply >= 22:
            return min(budget, 18)
        return min(budget, 28)

    prev_bids = []
    distressed_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) > budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            distressed_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))
            if prev.get('status') == 'lost' and opp.get('hp', 10) <= 3:
                distressed_opp += 1

    high_supply = supply >= 22
    low_supply = supply <= 17

    if hp <= 1:
        base = 68
    elif hp <= 2 or no_water >= 2:
        base = 62
    elif hp <= 4 or no_water >= 1:
        base = 48
    else:
        base = 34 if high_supply else 42

    if low_supply:
        base += 8
    elif high_supply:
        base -= 6

    if distressed_opp > 0:
        base += 4
    if rich_opp >= max(1, len(alive) // 2):
        base += 3

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if hp <= 2 or no_water >= 1:
            target = highest_prev + 2
            bid = max(base, target)
        else:
            if highest_prev >= 60:
                bid = min(base, 32 if high_supply else 38)
            elif highest_prev >= 45:
                bid = max(base, avg_prev + 1.5)
            else:
                bid = max(base, highest_prev + 1)
    else:
        bid = base

    remaining_days = max(0, 10 - day)
    reserve = 0
    if remaining_days > 0:
        reserve = remaining_days * 8
    max_affordable = max(0, budget - reserve)

    if hp <= 2 or no_water >= 2:
        max_affordable = budget
    elif hp <= 4 and no_water >= 1:
        max_affordable = max(max_affordable, budget * 0.75)

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0, bid)

    if bid < 1 and budget >= 1 and (hp <= 4 or no_water >= 1):
        bid = 1

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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.2
        if hp <= 2 or no_water_days >= 2:
            safe_bid = DAILY_SALARY * 0.6
        return float(min(budget, safe_bid))

    prev_bids = []
    prev_neediness = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        need = 0.0
        if opp.get('hp', 0) <= 2:
            need += 1.5
        elif opp.get('hp', 0) <= 4:
            need += 0.8
        if opp.get('no_water_days', 0) >= 2:
            need += 1.5
        elif opp.get('no_water_days', 0) == 1:
            need += 0.7
        if opp.get('budget', 0) > budget:
            need += 0.4
        prev_neediness.append(need)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_need = max(prev_neediness) if prev_neediness else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 2.0
    elif hp <= 4:
        urgency += 1.0
    if no_water_days >= 2:
        urgency += 2.0
    elif no_water_days == 1:
        urgency += 0.8

    base = DAILY_SALARY * (0.28 + 0.42 * scarcity)

    if supply >= 23:
        base *= 0.8
    elif supply <= 17:
        base *= 1.2

    if urgency >= 3.0:
        target = max(base, DAILY_SALARY * 0.92)
    elif urgency >= 1.5:
        target = max(base, DAILY_SALARY * 0.72)
    else:
        target = base

    if highest_prev > 0:
        if highest_prev >= 120:
            if urgency < 1.5:
                target = min(target, DAILY_SALARY * 0.42)
            else:
                target = max(target, DAILY_SALARY * 0.88)
        elif highest_prev >= 90:
            if urgency < 1.5 and supply >= 20:
                target = min(target, DAILY_SALARY * 0.4)
            else:
                target = max(target, min(highest_prev + 2.0, DAILY_SALARY * 0.95))
        else:
            target = max(target, min(highest_prev + 1.5, DAILY_SALARY * 0.82))
    else:
        target = max(target, avg_prev * 0.9)

    if max_need >= 2.0 and supply <= 18:
        target += 8.0
    elif max_need >= 1.0 and supply <= 19:
        target += 4.0

    days_left = 11 - day
    reserve_floor = max(0.0, days_left * DAILY_SALARY * 0.18)
    affordable = max(0.0, budget - reserve_floor)

    if urgency >= 3.0:
        affordable = budget
    elif hp <= 3 and no_water_days >= 1:
        affordable = max(affordable, budget * 0.75)

    bid = min(target, affordable if affordable > 0 else budget)

    if bid < 0:
        bid = 0.0
    if urgency >= 3.0 and bid < DAILY_SALARY * 0.75:
        bid = min(budget, DAILY_SALARY * 0.75)
    if supply >= 24 and urgency == 0.0:
        bid = min(bid, DAILY_SALARY * 0.3)

    return float(min(budget, max(0.0, bid)))
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

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0
    desperate_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))
                if prev.get('bid', 0.0) >= 120:
                    rich_pressure += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return min(budget, 20.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
        urgency += 2

    if day >= 8:
        urgency += 1

    supply_score = 0
    if supply >= 23:
        supply_score = 3
    elif supply >= 20:
        supply_score = 2
    elif supply >= 17:
        supply_score = 1

    if urgency == 0:
        if supply >= 23 and rich_pressure <= 1:
            bid = 58.0
        elif supply >= 20 and highest_prev < 100:
            bid = 42.0
        else:
            bid = 0.0
    elif urgency <= 2:
        if rich_pressure >= 2 and supply < 20:
            bid = 18.0
        else:
            bid = 55.0 + 6.0 * supply_score
    elif urgency <= 4:
        bid = 78.0 + 8.0 * supply_score
        if highest_prev >= 140:
            bid = max(bid, 118.0)
    else:
        bid = 125.0 + 10.0 * supply_score
        if highest_prev > 0:
            bid = max(bid, highest_prev + 2.0)

    if desperate_count >= 2 and urgency >= 3:
        bid += 8.0

    if avg_prev >= 130 and urgency <= 2:
        bid = min(bid, 35.0)

    reserve = 0.0
    if hp >= 5 and day <= 7:
        reserve = DAILY_SALARY * 2
    elif hp >= 3 and day <= 8:
        reserve = DAILY_SALARY

    max_affordable = budget - reserve
    if max_affordable < 0:
        max_affordable = 0.0

    bid = min(bid, budget)
    if urgency <= 2:
        bid = min(bid, max_affordable)

    if hp <= 2 or no_water_days >= 2:
        bid = min(max(bid, 110.0), budget)

    if bid < 0:
        bid = 0.0

    return float(bid)
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= DAILY_SALARY * 0.8:
                    dangerous_prev.append(float(bid))

    if not alive:
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
        urgency += 40.0
    elif hp <= 4:
        urgency += 24.0
    elif hp <= 6:
        urgency += 10.0

    if no_water >= 2:
        urgency += 28.0
    elif no_water >= 1:
        urgency += 12.0

    urgency += scarcity * 12.0

    if hp >= 7 and no_water == 0 and highest_prev >= 90.0:
        return float(min(budget, 9.0))

    if hp >= 5 and no_water == 0 and highest_prev >= 105.0:
        return float(min(budget, 7.0))

    base = 32.0 + urgency

    if highest_prev > 0:
        if hp <= 3 or no_water >= 2:
            bid = max(base, highest_prev + 2.5)
        elif hp <= 5 or no_water >= 1:
            bid = max(base, avg_prev + 3.0)
        else:
            if highest_prev >= 95.0:
                bid = 12.0
            else:
                bid = max(base, highest_prev - 6.0)
    else:
        bid = base

    if day >= 8:
        bid += 8.0
    elif day >= 6:
        bid += 4.0

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.82)
    elif budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.72)
    else:
        bid = min(bid, budget * 0.58 + 18.0)

    if hp <= 2:
        bid = max(bid, min(budget, 92.0))
    elif hp <= 4 and highest_prev > 0:
        bid = max(bid, min(budget, highest_prev + 1.5))

    if bid < 0:
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_bidders = 0
    desperate_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 120:
                    strong_bidders += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2

    scarcity = 0
    if supply <= 16:
        scarcity = 3
    elif supply <= 19:
        scarcity = 2
    elif supply <= 22:
        scarcity = 1

    pressure = scarcity + urgency
    if desperate_opponents >= 2:
        pressure += 1

    if pressure >= 6:
        target = max(110.0, highest_prev + 3.0)
    elif pressure >= 4:
        target = max(72.0, min(108.0, avg_prev * 0.7 + 18.0))
    elif pressure >= 2:
        target = max(32.0, min(70.0, avg_prev * 0.35 + 10.0))
    else:
        target = 12.0 if strong_bidders >= 1 else 20.0

    if strong_bidders >= 2 and urgency == 0 and supply >= 18:
        target = min(target, 15.0)

    remaining_days = max(0, 10 - int(day) + 1)
    reserve_floor = max(0.0, remaining_days * 8.0)
    spend_cap = max(0.0, budget - reserve_floor)

    if urgency >= 4:
        spend_cap = budget
    elif urgency >= 2:
        spend_cap = max(spend_cap, budget * 0.45)

    bid = min(target, spend_cap if spend_cap > 0 else budget * 0.25)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, max(95.0, highest_prev + 2.0)))

    if budget < 25:
        bid = min(bid, budget)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    opp_count = len(alive)
    expected_needers = opp_count + 1
    scarcity = supply / float(WATER_REQ * expected_needers)

    highest_prev = 0.0
    avg_prev = 0.0
    count_prev = 0
    eric_prev = 0.0
    desperate_opp = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            highest_prev = max(highest_prev, bid)
            avg_prev += bid
            count_prev += 1
            if oid == 'Eric':
                eric_prev = bid
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1

    if count_prev > 0:
        avg_prev /= count_prev

    if scarcity >= 1.25:
        base = DAILY_SALARY * 0.32
    elif scarcity >= 1.0:
        base = DAILY_SALARY * 0.48
    elif scarcity >= 0.8:
        base = DAILY_SALARY * 0.68
    else:
        base = DAILY_SALARY * 0.9

    pressure_bid = 0.0
    if highest_prev > 0:
        pressure_bid = highest_prev + 2.0
        if eric_prev > 0 and eric_prev >= highest_prev - 1e-9:
            pressure_bid = eric_prev + 3.0
        if highest_prev >= DAILY_SALARY * 1.3:
            pressure_bid = highest_prev * 0.82

    bid = max(base, pressure_bid if pressure_bid > 0 else base)

    if desperate_opp >= 2:
        bid += 6.0
    elif desperate_opp == 0 and scarcity >= 1.0:
        bid -= 5.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.78)

    if day >= 8 and hp > 4 and scarcity >= 1.0:
        bid *= 0.9

    reserve_floor = DAILY_SALARY * max(0, 10 - day)
    if budget > reserve_floor:
        cap = max(DAILY_SALARY * 1.35, budget * 0.28)
    else:
        cap = max(DAILY_SALARY * 0.95, budget * 0.5)

    bid = min(bid, cap, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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

    alive_opponents = []
    prev_bids = []
    rich_threats = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget:
                rich_threats += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 2:
        urgency = 2
    elif hp <= 6 or no_water_days >= 1:
        urgency = 1

    if urgency >= 3:
        bid = max(62.0, min(95.0, highest_prev + 2.0))
    elif urgency == 2:
        if highest_prev >= 100:
            bid = 58.0 + 4.0 * scarcity
        else:
            bid = max(48.0 + 4.0 * scarcity, min(78.0, highest_prev + 1.5))
    elif urgency == 1:
        if highest_prev >= 100:
            bid = 26.0 + 3.0 * scarcity
        elif highest_prev >= 80:
            bid = 34.0 + 4.0 * scarcity
        else:
            bid = max(28.0 + 3.0 * scarcity, min(52.0, avg_prev * 0.6 + 4.0))
    else:
        if highest_prev >= 100:
            bid = 8.0 + 3.0 * scarcity
        elif highest_prev >= 80:
            bid = 14.0 + 3.0 * scarcity
        else:
            bid = 20.0 + 4.0 * scarcity

    if rich_threats >= 2 and urgency <= 1:
        bid -= 4.0

    if day >= 8 and hp >= 6 and urgency == 0:
        bid -= 3.0

    if budget < 80:
        bid = min(bid, max(18.0, budget * 0.55))
    elif budget < 140:
        bid = min(bid, budget * 0.7)

    bid = max(0.0, min(budget, bid))
    return bid
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    prev_bids = []
    cindy_prev = None
    eric_prev = None
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if bid is not None and bid >= 100:
                cindy_prev = float(bid)
            elif bid is not None:
                if eric_prev is None or float(bid) > eric_prev:
                    eric_prev = float(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids)
        second_prev = float(sorted_bids[int(len(sorted_bids) - 2)])

    scarcity = supply <= 18
    urgent = hp <= 4 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        target = max(92.0, highest_prev + 2.0)
    elif urgent:
        if scarcity:
            target = max(78.0, highest_prev + 1.5)
        else:
            target = max(62.0, second_prev + 1.0)
    else:
        if scarcity:
            if cindy_prev is not None and cindy_prev >= 110:
                target = 66.0
            else:
                target = max(58.0, min(82.0, highest_prev - 6.0))
        else:
            target = 41.0
            if eric_prev is not None:
                target = max(target, min(63.0, eric_prev - 8.0))

    if day >= 8:
        target += 6.0
    if hp >= 8 and no_water == 0 and not scarcity:
        target -= 6.0

    target = max(0.0, min(float(budget), target))
    return float(round(target, 2))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    weak_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                weak_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 60:
                    aggressive_count += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply <= 17
    abundant = supply >= 22

    critical = hp <= 2 or no_water >= 2
    urgent = hp <= 4 or no_water >= 1

    if critical:
        target = max(72.0, highest_prev + 2.5)
        if scarcity:
            target = max(target, 88.0)
        return float(min(budget, target))

    if urgent:
        target = max(46.0, avg_prev + 3.0)
        if highest_prev >= 100:
            target = 58.0 if hp > 3 else 92.0
        if scarcity:
            target += 8.0
        return float(min(budget, target))

    if highest_prev >= 120:
        if abundant or weak_count >= 1:
            return float(min(budget, 12.0))
        return float(min(budget, 24.0))

    if highest_prev >= 90:
        if scarcity:
            return float(min(budget, 34.0))
        return float(min(budget, 20.0))

    base = 18.0
    if scarcity:
        base = 30.0
    elif abundant:
        base = 14.0

    if aggressive_count == 0 and avg_prev > 0:
        base = max(base, avg_prev + 1.5)

    if day >= 8 and hp <= 6:
        base += 8.0

    reserve_cap = budget
    if day <= 3:
        reserve_cap = min(reserve_cap, DAILY_SALARY * 0.65)
    elif day <= 7:
        reserve_cap = min(reserve_cap, DAILY_SALARY * 0.85)

    return float(min(reserve_cap, base))
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    rich_pressure = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > budget:
                    rich_pressure = max(rich_pressure, float(bid))

    slots = supply / WATER_REQ
    tight = slots < 1.5
    medium_tight = slots < 2.0

    if not alive_opps:
        return float(min(budget, 20.0))

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
    if tight:
        danger += 1

    if danger >= 4:
        bid = max(0.95 * DAILY_SALARY, highest_prev + 3.0)
    elif danger >= 2:
        bid = max(0.78 * DAILY_SALARY, highest_prev + 1.5)
    else:
        if tight:
            bid = max(0.62 * DAILY_SALARY, avg_prev * 0.9)
        elif medium_tight:
            bid = max(0.48 * DAILY_SALARY, avg_prev * 0.72)
        else:
            bid = 0.38 * DAILY_SALARY

    if highest_prev >= 170:
        if hp > 5 and no_water_days == 0:
            bid = min(bid, 30.0)
        else:
            bid = max(bid, 66.0)
    elif highest_prev >= 120:
        bid = max(bid, min(highest_prev + 2.0, 0.92 * DAILY_SALARY))

    if rich_pressure >= 120 and hp > 5 and no_water_days == 0 and tight:
        bid = min(bid, 32.0)

    if day >= 8:
        bid += 4.0
    if hp <= 2:
        bid = max(bid, 68.0)

    reserve = 0.0
    if hp > 5 and no_water_days == 0:
        reserve = 20.0
    elif hp > 3:
        reserve = 10.0

    cap = max(0.0, budget - reserve)
    if cap <= 0:
        cap = budget

    bid = min(bid, cap)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""
