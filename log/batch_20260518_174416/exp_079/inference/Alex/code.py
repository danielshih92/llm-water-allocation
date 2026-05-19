# ============================================================
# Experiment: exp_079
# Agent: Alex
# Source: exp_079
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

    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.28
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return max(0, min(budget, base))

    opp_count = len(alive_opponents)
    total_players = opp_count + 1

    pressure_bids = []
    desperation = 0
    failed_yesterday = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperation += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            pressure_bids.append(bid)
        status = prev.get('status')
        if status is not None and status != 'won':
            failed_yesterday += 1

    expected_share = float(supply) / float(total_players)
    scarcity = expected_share < WATER_REQ

    if pressure_bids:
        highest_prev = max(pressure_bids)
        avg_prev = sum(pressure_bids) / float(len(pressure_bids))
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
    elif hp <= 4 or no_water_days == 1:
        bid = max(DAILY_SALARY * 0.62, avg_prev + 1.5)
    else:
        if scarcity:
            bid = DAILY_SALARY * 0.56
        else:
            bid = DAILY_SALARY * 0.34
        if highest_prev >= DAILY_SALARY * 0.85:
            bid = min(bid, DAILY_SALARY * 0.32)
        elif highest_prev > 0:
            bid = max(bid, min(DAILY_SALARY * 0.68, highest_prev + 1.0))

    if desperation >= max(1, opp_count // 2):
        bid += 4.0
    if failed_yesterday >= max(1, opp_count // 2):
        bid += 2.0

    if day >= 8 and hp > 3 and no_water_days == 0:
        bid *= 0.92

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.72)

    bid = max(0.0, min(float(budget), float(bid)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > 0:
                    dangerous_prev.append(float(bid))

    if not alive:
        base = 12.0 if hp > 3 else 28.0
        return float(min(budget, base))

    high_prev = max(dangerous_prev) if dangerous_prev else 0.0
    avg_prev = sum(dangerous_prev) / len(dangerous_prev) if dangerous_prev else 0.0

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

    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.45

    if day >= 8:
        urgency += 0.2

    cindy_alive = False
    eric_alive = False
    for oid, opp in alive:
        if oid == 'Cindy':
            cindy_alive = True
        if oid == 'Eric':
            eric_alive = True

    if hp <= 2 or no_water >= 2:
        emergency = max(92.0, high_prev + 3.0)
        if cindy_alive:
            emergency = max(emergency, 106.0)
        return float(min(budget, emergency))

    if supply >= 23 and hp >= 7 and no_water == 0:
        return float(min(budget, 8.0))

    if supply <= 17:
        target = 48.0 + 26.0 * scarcity + 18.0 * urgency
        if high_prev > 0:
            target = max(target, min(high_prev + 2.0, 104.0))
        if cindy_alive and urgency >= 0.8:
            target = max(target, 106.0)
        return float(min(budget, target))

    target = 20.0 + 18.0 * scarcity + 16.0 * urgency
    if eric_alive and avg_prev > 0:
        target = max(target, min(avg_prev + 1.5, 82.0))
    if cindy_alive and urgency < 0.8:
        target = min(target, 72.0)

    if hp >= 8 and no_water == 0 and supply >= 20:
        target = min(target, 24.0)

    target = max(0.0, target)
    return float(min(budget, target))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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
    aggressive_bids = []
    needy_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= DAILY_SALARY * 0.9:
                    aggressive_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        safe = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            safe = DAILY_SALARY * 0.7
        return float(max(0.0, min(budget, safe)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17.0
    loose_supply = supply >= 22.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif hp <= 4 or no_water_days >= 1:
        if tight_supply:
            bid = max(DAILY_SALARY * 0.88, highest_prev + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.78, avg_prev + 2.0)
    else:
        if tight_supply:
            bid = max(DAILY_SALARY * 0.72, avg_prev + 3.0)
        elif loose_supply:
            bid = DAILY_SALARY * 0.42
        else:
            bid = max(DAILY_SALARY * 0.55, avg_prev + 1.0)

    if len(aggressive_bids) >= 2 and hp > 4 and no_water_days == 0:
        bid *= 0.88

    if needy_count >= 2 and (tight_supply or hp <= 4):
        bid = max(bid, highest_prev + 1.0, DAILY_SALARY * 0.82)

    if day >= 8 and hp > 5 and budget < DAILY_SALARY * 3:
        bid *= 0.9

    reserve_floor = 0.0
    if hp > 4 and no_water_days == 0:
        reserve_floor = DAILY_SALARY * 0.15

    max_affordable = max(0.0, budget - reserve_floor)
    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(bid)
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

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return float(min(budget, 20.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = 24.0 + 18.0 * scarcity

    if hp <= 2:
        base = 78.0 + 10.0 * scarcity
    elif hp <= 4:
        base += 18.0

    if no_water_days >= 2:
        base += 28.0
    elif no_water_days >= 1:
        base += 12.0

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if hp <= 3 or no_water_days >= 1:
            target = max(base, min(highest_prev + 2.0, 92.0))
        else:
            if highest_prev >= 120.0:
                target = min(base, 38.0)
            elif highest_prev >= 90.0:
                target = max(base, avg_prev * 0.55)
            else:
                target = max(base, highest_prev + 1.5)
    else:
        target = base

    if urgent_opp >= 2 and hp >= 5:
        target -= 6.0
    if rich_opp >= 2 and scarcity > 0.5:
        target += 6.0

    if day >= 8:
        target += 8.0
    if day == 10:
        target += 10.0

    reserve = 0.0
    if hp >= 5:
        reserve = DAILY_SALARY * 1.2
    elif hp >= 3:
        reserve = DAILY_SALARY * 0.6

    affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        affordable = budget

    bid = min(target, affordable)

    floor_bid = 0.0
    if hp <= 2:
        floor_bid = min(budget, 75.0)
    elif no_water_days >= 1:
        floor_bid = min(budget, 48.0)
    elif scarcity > 0.7:
        floor_bid = min(budget, 32.0)
    else:
        floor_bid = min(budget, 18.0)

    if bid < floor_bid:
        bid = floor_bid

    if bid > budget:
        bid = budget
    if bid < 0:
        bid = 0.0

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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    pressure_scores = []

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            opp_pressure = 0.0
            opp_pressure += max(0, 6 - opp.get('hp', 10)) * 4.0
            opp_pressure += opp.get('no_water_days', 0) * 10.0
            opp_pressure += max(0.0, DAILY_SALARY - opp.get('budget', 0.0)) * 0.05
            if bid is not None:
                opp_pressure += float(bid) * 0.15
            pressure_scores.append(opp_pressure)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    sorted_bids = sorted(prev_bids) if prev_bids else []
    highest_prev = sorted_bids[-1] if sorted_bids else 0.0
    second_prev = sorted_bids[-2] if len(sorted_bids) >= 2 else highest_prev
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_pressure = max(pressure_scores) if pressure_scores else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    my_urgency = 0.0
    my_urgency += max(0, 5 - hp) * 9.0
    my_urgency += no_water_days * 14.0
    if day >= 8:
        my_urgency += 6.0

    safe = hp >= 7 and no_water_days == 0
    danger = hp <= 4 or no_water_days >= 2
    critical = hp <= 2 or no_water_days >= 3

    if critical:
        bid = max(92.0, highest_prev + 3.0, second_prev + 5.0)
    elif danger:
        bid = max(72.0 + 18.0 * scarcity, second_prev + 2.5, avg_prev * 0.82)
    elif safe and supply >= 21:
        bid = max(18.0, min(46.0, avg_prev * 0.42 + 4.0))
    elif safe and supply >= 18:
        bid = max(28.0, min(58.0, second_prev * 0.62 + 3.0))
    else:
        bid = max(45.0 + 12.0 * scarcity, second_prev * 0.78 + 2.0)

    if highest_prev >= 130.0 and safe:
        bid = min(bid, 44.0)
    elif highest_prev >= 110.0 and safe and supply >= 18:
        bid = min(bid, 52.0)

    if max_pressure >= 28.0 and not safe:
        bid = max(bid, second_prev + 3.0)

    if day == 1 and supply >= 20 and hp >= 8:
        bid = min(bid, 35.0)

    reserve = 0.0
    if hp >= 6:
        reserve = DAILY_SALARY * 1.2
    elif hp >= 4:
        reserve = DAILY_SALARY * 0.6

    affordable = max(0.0, budget - reserve)
    if critical:
        cap = budget
    else:
        cap = max(20.0, affordable)
        cap = min(cap, budget)

    bid = min(bid, cap)
    bid = max(0.0, bid)
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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
    yesterday_bids = []
    strong_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                yesterday_bids.append(bid)
                if bid >= 100:
                    strong_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    tight_supply = supply <= 17.0
    ample_supply = supply >= 22.0
    critical = hp <= 3 or no_water_days >= 1
    desperate = hp <= 2 or no_water_days >= 2

    high_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_strong = sum(strong_bids) / len(strong_bids) if strong_bids else 0.0

    bid = 0.0

    if desperate:
        if strong_bids:
            bid = min(budget, max(118.0, min(161.0, avg_strong + 3.0)))
        else:
            bid = min(budget, 95.0)
    elif critical:
        if tight_supply:
            if strong_bids:
                bid = min(budget, max(105.0, min(150.0, high_prev + 2.0)))
            else:
                bid = min(budget, 78.0)
        else:
            if strong_bids:
                bid = min(budget, max(88.0, min(135.0, avg_strong - 8.0)))
            else:
                bid = min(budget, 62.0)
    else:
        if ample_supply:
            bid = min(budget, 16.0)
        elif tight_supply:
            if high_prev >= 120.0:
                bid = min(budget, 34.0)
            elif high_prev >= 70.0:
                bid = min(budget, 42.0)
            else:
                bid = min(budget, 48.0)
        else:
            if high_prev >= 120.0:
                bid = min(budget, 22.0)
            elif high_prev >= 70.0:
                bid = min(budget, 30.0)
            else:
                bid = min(budget, 38.0)

    if day >= 8 and hp <= 5:
        bid = max(bid, min(budget, 72.0 if not strong_bids else 110.0))

    if budget < 80.0:
        bid = min(bid, budget)
    else:
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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        base = 18.0 if hp > 3 else 45.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    weak_opponents = 0

    for opp in alive:
        if opp.get('budget', 0) >= 200:
            rich_opponents += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        if opp.get('hp', 10) <= 2:
            weak_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    contested = len(alive) >= 3
    low_supply = supply <= 17.0
    high_supply = supply >= 22.0
    my_urgent = hp <= 3 or no_water_days >= 1
    my_critical = hp <= 2 or no_water_days >= 2

    bid = 0.0

    if my_critical:
        bid = max(95.0, highest_prev + 3.0, avg_prev + 6.0)
    elif my_urgent:
        bid = max(78.0, highest_prev + 2.0 if highest_prev > 0 else 82.0)
    else:
        if high_supply and weak_opponents >= 1:
            bid = 24.0
        elif high_supply:
            bid = 32.0 if contested else 26.0
        elif low_supply:
            if highest_prev >= 120.0:
                bid = highest_prev + 2.0
            else:
                bid = max(62.0, avg_prev + 4.0 if avg_prev > 0 else 66.0)
        else:
            if highest_prev >= 145.0:
                bid = 52.0 if hp > 4 else 88.0
            elif highest_prev >= 120.0:
                bid = highest_prev + 1.5 if hp <= 4 else 58.0
            elif highest_prev > 0:
                bid = max(48.0, avg_prev + 3.0)
            else:
                bid = 44.0

    if rich_opponents >= 2 and low_supply and not my_urgent:
        bid = max(bid, 68.0)
    if urgent_opponents >= 2 and hp > 4 and not my_urgent:
        bid = min(bid, 40.0)

    if day >= 8 and hp > 4 and budget < 120:
        bid = min(bid, 38.0)
    if day >= 8 and my_urgent:
        bid = max(bid, 90.0)

    if budget < 50:
        bid = min(bid, max(12.0, budget))
    elif budget < 90 and not my_urgent:
        bid = min(bid, 36.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(bid)
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    base = DAILY_SALARY * 0.38

    if scarcity == 2:
        base = DAILY_SALARY * 0.72
    elif scarcity == 1:
        base = DAILY_SALARY * 0.56

    if urgency == 3:
        base = max(base, DAILY_SALARY * 0.95)
    elif urgency == 2:
        base = max(base, DAILY_SALARY * 0.78)
    elif urgency == 1:
        base = max(base, DAILY_SALARY * 0.60)

    if highest_prev >= 100:
        if urgency >= 2 or scarcity == 2:
            base = max(base, min(highest_prev + 1.0, DAILY_SALARY * 1.50))
        else:
            base = min(base, DAILY_SALARY * 0.30)
    elif highest_prev >= 85:
        if urgency >= 1 or scarcity >= 1:
            base = max(base, highest_prev + 1.5)
        else:
            base = min(base, DAILY_SALARY * 0.34)
    elif highest_prev > 0:
        target = max(avg_prev + 2.0, highest_prev + 0.8)
        if scarcity >= 1 or urgency >= 1:
            base = max(base, target)
        else:
            base = max(base, min(target, DAILY_SALARY * 0.62))

    if desperate_opp >= 2 and (scarcity >= 1 or urgency >= 1):
        base += 4.0

    if rich_opp >= 2 and urgency == 0 and scarcity == 0:
        base = min(base, DAILY_SALARY * 0.32)

    remaining_days = max(0, 10 - day)
    reserve = remaining_days * DAILY_SALARY * 0.28
    affordable = budget
    if urgency == 0:
        affordable = max(0.0, budget - reserve)
        if affordable <= 0:
            affordable = min(budget, DAILY_SALARY * 0.22)

    bid = min(base, affordable if urgency == 0 else budget)

    if hp <= 1 or no_water_days >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 1.05, highest_prev + 2.0))

    if bid < 0:
        bid = 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = []
    weak_prev = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= 100:
                    strong_prev.append(float(bid))
                else:
                    weak_prev.append(float(bid))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.2))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.7
    elif hp <= 4:
        urgency += 0.4
    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days == 1:
        urgency += 0.25
    urgency += 0.35 * scarcity
    if day >= 8:
        urgency += 0.1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strong_high = max(strong_prev) if strong_prev else highest_prev

    affordable_cap = min(budget, max(0.0, budget * 0.42 + DAILY_SALARY * 0.35))

    if urgency >= 1.0:
        target = max(DAILY_SALARY * 0.95, strong_high + 2.0)
    elif urgency >= 0.6:
        target = max(DAILY_SALARY * 0.68, strong_high * 0.78 + 3.0)
    elif scarcity >= 0.7:
        target = max(DAILY_SALARY * 0.52, strong_high * 0.55)
    else:
        target = DAILY_SALARY * 0.28
        if highest_prev > 0 and highest_prev < 80:
            target = max(target, highest_prev + 1.0)

    rich_alive = 0
    for opp in alive:
        if opp.get('budget', 0) >= 500:
            rich_alive += 1
    if rich_alive >= 2 and urgency < 0.8:
        target *= 0.9

    if budget <= DAILY_SALARY * 1.2:
        target = min(target, budget * 0.75)

    bid = min(affordable_cap, target)
    if hp > 6 and no_water_days == 0 and scarcity <= 0.2:
        bid = min(bid, DAILY_SALARY * 0.22)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
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
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    opp_budgets = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opps:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 50.0)
        return min(budget, 18.0)

    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    richest_opp = max(opp_budgets) if opp_budgets else 0.0

    severe_need = hp <= 2 or no_water_days >= 2
    urgent_need = hp <= 4 or no_water_days >= 1

    if supply < WATER_REQ:
        if severe_need:
            bid = min(budget, max(58.0, max_prev + 3.0))
        else:
            bid = min(budget, 8.0)
        return max(0.0, bid)

    enough_for_one = supply < 2 * WATER_REQ

    if severe_need:
        target = max(62.0, min(0.92 * DAILY_SALARY, max_prev + 4.0))
        if budget < target:
            target = budget
        return max(0.0, min(budget, target))

    if enough_for_one:
        if max_prev >= 160:
            if hp >= 7 and no_water_days == 0 and day <= 7:
                bid = 16.0
            elif urgent_need:
                bid = min(budget, max(66.0, min(max_prev + 2.0, 0.95 * DAILY_SALARY)))
            else:
                bid = 24.0
        elif max_prev >= 100:
            if urgent_need:
                bid = min(budget, max(58.0, max_prev + 2.0))
            else:
                bid = min(budget, max(32.0, avg_prev * 0.55))
        else:
            bid = 40.0 if urgent_need else 22.0
    else:
        if urgent_need:
            bid = min(budget, max(48.0, min_prev + 2.0 if prev_bids else 48.0))
        else:
            bid = min(budget, max(26.0, avg_prev * 0.35 if prev_bids else 26.0))

    if budget > richest_opp and urgent_need:
        bid = min(budget, bid + 4.0)

    if day >= 8:
        if hp >= 6 and no_water_days == 0:
            bid = min(budget, bid * 0.9)
        else:
            bid = min(budget, bid + 5.0)

    return max(0.0, min(budget, float(bid)))
"""
