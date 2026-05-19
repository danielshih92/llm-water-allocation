# ============================================================
# Experiment: exp_096
# Agent: Alex
# Source: exp_096
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

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    player_count = 1 + len(alive)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < player_count

    prev_bids = []
    desperate_opp = False
    rich_opp_pressure = 0.0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0)
            prev_bids.append(bid)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_opp = True
            if opp.get('budget', 0) > budget and bid > rich_opp_pressure:
                rich_opp_pressure = bid

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
    if scarcity:
        urgency += 1
    if desperate_opp:
        urgency += 1

    if prev_bids:
        top_prev = max(prev_bids)
    else:
        top_prev = 0

    if urgency >= 5:
        target = max(0.92 * DAILY_SALARY, top_prev + 2.0)
    elif urgency >= 3:
        target = max(0.72 * DAILY_SALARY, top_prev + 1.0)
    elif urgency >= 2:
        target = max(0.55 * DAILY_SALARY, min(top_prev + 0.5, 0.78 * DAILY_SALARY))
    else:
        if scarcity:
            target = max(0.42 * DAILY_SALARY, min(top_prev + 0.5, 0.62 * DAILY_SALARY))
        else:
            target = 0.28 * DAILY_SALARY

    if rich_opp_pressure >= 0.85 * DAILY_SALARY and urgency <= 2:
        target = min(target, 0.38 * DAILY_SALARY)

    days_left_est = max(1, 10 - int(day_context['day']) + 1)
    reserve_floor = max(0.0, (days_left_est - 1) * DAILY_SALARY * 0.18)
    affordable = max(0.0, budget - reserve_floor)

    bid = min(budget, affordable if affordable > 0 else budget, target)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, 0.9 * DAILY_SALARY, top_prev + 1.5 if prev_bids else 0))

    if bid < 0:
        bid = 0
    return float(round(bid, 2))
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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.25)
        return float(max(0.0, bid))

    total_players = 1 + len(alive)
    capacity = int(supply / WATER_REQ)
    scarcity = capacity < total_players

    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = prev.get('bid') if prev else None
        if pbid is not None:
            prev_bids.append(float(pbid))
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            desperate_count += 1
        if opp.get('budget', 0) > 300 and pbid is not None and pbid >= 80:
            rich_aggressive += 1

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
    if scarcity:
        urgency += 1
    if desperate_count >= max(1, len(alive) // 2):
        urgency += 1

    if urgency >= 5:
        base = max(DAILY_SALARY * 0.95, highest_prev + 4.0)
    elif urgency >= 3:
        base = max(DAILY_SALARY * 0.72, avg_prev + 2.5, highest_prev * 0.82)
    else:
        if scarcity:
            if highest_prev >= 100:
                base = DAILY_SALARY * 0.22
            elif highest_prev >= 80:
                base = DAILY_SALARY * 0.30
            else:
                base = max(DAILY_SALARY * 0.38, avg_prev * 0.72)
        else:
            base = max(DAILY_SALARY * 0.18, avg_prev * 0.45)

    if rich_aggressive >= 1 and urgency <= 2:
        base *= 0.85

    if day >= 8:
        if urgency >= 3:
            base = max(base, DAILY_SALARY * 0.85)
        else:
            base = max(base, DAILY_SALARY * 0.42)

    if budget < DAILY_SALARY * 1.2:
        if urgency >= 4:
            base = min(base, budget)
        else:
            base = min(base, budget * 0.55)
    elif budget < DAILY_SALARY * 2.5 and urgency <= 2:
        base = min(base, budget * 0.45)

    bid = min(budget, max(0.0, base))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    yesterday_bids = []
    high_threat = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                b = float(bid)
                yesterday_bids.append(b)
                if b >= 120:
                    high_threat += 1

    if not alive_opponents:
        return min(budget, 20.0)

    max_prev = max(yesterday_bids) if yesterday_bids else 0.0
    min_prev = min(yesterday_bids) if yesterday_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    urgency = 0
    if hp <= 2 or no_water_days >= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency == 3:
        target = max(145.0, max_prev + 3.0)
        if supply >= 22:
            target += 5.0
    elif urgency == 2:
        if supply >= 22:
            target = max(118.0, min(145.0, max_prev + 2.0))
        else:
            target = 72.0 if max_prev < 90 else 96.0
    elif urgency == 1:
        if high_threat >= 2 and supply < 21:
            target = 18.0
        else:
            target = max(35.0, min(90.0, min_prev + 2.0 if yesterday_bids else 45.0))
    else:
        if high_threat >= 1:
            target = 8.0 + 10.0 * supply_ratio
        else:
            target = 28.0 + 18.0 * supply_ratio

    if day >= 8 and hp > 4 and no_water_days == 0 and high_threat >= 1:
        target *= 0.75

    if budget < 120:
        target = min(target, budget * 0.92)
    elif budget < 250:
        target = min(target, budget * 0.75)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, min(budget, 110.0))

    if target < 0:
        target = 0.0
    if target > budget:
        target = budget
    return float(target)
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev['bid'])
                prev_bids.append(b)
                if b >= 100:
                    dangerous_prev.append(b)

    if not alive_opponents:
        base = 18.0 if hp > 4 else 40.0
        return float(min(budget, base))

    highest_prev = max(prev_bids) if prev_bids else 80.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 80.0

    total_players = 1 + len(alive_opponents)
    expected_share = float(supply) / float(total_players * WATER_REQ)
    scarce = expected_share < 0.5
    very_scarce = expected_share < 0.35
    abundant = expected_share > 0.8

    emergency = hp <= 3 or no_water >= 2
    fragile = hp <= 5 or no_water >= 1

    if emergency:
        bid = max(110.0, highest_prev + 3.0)
        if very_scarce:
            bid = max(bid, 135.0)
        return float(min(budget, bid))

    if abundant and hp >= 6:
        bid = 12.0 + 0.05 * DAILY_SALARY
        if no_water >= 1:
            bid += 10.0
        return float(min(budget, bid))

    if very_scarce:
        if hp >= 8 and no_water == 0:
            bid = min(55.0, avg_prev * 0.55)
        else:
            bid = max(95.0, highest_prev * 0.82)
        return float(min(budget, bid))

    if scarce:
        if fragile:
            bid = max(78.0, min(highest_prev + 1.5, 120.0))
        else:
            bid = max(45.0, min(avg_prev * 0.6, 85.0))
        return float(min(budget, bid))

    bid = 28.0
    if fragile:
        bid = 48.0
    if dangerous_prev:
        bid = min(bid, 35.0)
    if day >= 8 and hp <= 6:
        bid += 18.0

    return float(min(budget, bid))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    threatening_bids = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > 0:
                    threatening_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(threatening_bids) if threatening_bids else 0.0
    second_prev = 0.0
    if len(threatening_bids) >= 2:
        sorted_bids = sorted(threatening_bids, reverse=True)
        second_prev = sorted_bids[int(1)]

    likely_competitors = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None and float(bid) > 0:
            likely_competitors += 1

    supply_pressure = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)

    emergency = hp <= 2 or no_water_days >= 2
    danger = hp <= 4 or no_water_days >= 1

    if emergency:
        target = max(DAILY_SALARY * 1.55, highest_prev + 8.0)
        if supply >= 22:
            target = max(DAILY_SALARY * 1.25, highest_prev + 4.0)
        return float(min(budget, target))

    if danger:
        if highest_prev >= DAILY_SALARY * 1.8:
            target = DAILY_SALARY * 0.72 if hp > 3 else DAILY_SALARY * 1.1
        else:
            target = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
            if supply >= 21:
                target = max(DAILY_SALARY * 0.82, second_prev + 2.0)
        return float(min(budget, target))

    if likely_competitors <= 1:
        target = max(DAILY_SALARY * 0.42, highest_prev + 1.5)
        if highest_prev == 0:
            target = DAILY_SALARY * 0.28
        return float(min(budget, target))

    if supply_pressure >= 0.7:
        target = DAILY_SALARY * 0.58
    elif highest_prev >= DAILY_SALARY * 1.5:
        target = DAILY_SALARY * 0.22
    else:
        target = DAILY_SALARY * 0.38

    if budget < DAILY_SALARY * 3:
        target = min(target, DAILY_SALARY * 0.3)

    return float(min(budget, max(0.0, target)))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.75
        return float(min(budget, safe_bid))

    highest_prev_bid = 0.0
    avg_prev_bid = 0.0
    count_prev = 0
    rich_aggressive = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        prev_bid = None
        if prev:
            prev_bid = prev.get('bid')
        if prev_bid is not None:
            if prev_bid > highest_prev_bid:
                highest_prev_bid = prev_bid
            avg_prev_bid += prev_bid
            count_prev += 1
        if opp.get('budget', 0) >= 140 and opp.get('hp', 0) >= 6:
            rich_aggressive += 1

    if count_prev > 0:
        avg_prev_bid = avg_prev_bid / count_prev
    else:
        avg_prev_bid = DAILY_SALARY * 0.8
        highest_prev_bid = DAILY_SALARY * 0.9

    scarcity = 0
    if supply <= WATER_REQ + 2:
        scarcity = 2
    elif supply <= WATER_REQ + 6:
        scarcity = 1

    emergency = (hp <= 2) or (no_water_days >= 1)
    pressured = (hp <= 4)

    if emergency:
        bid = max(DAILY_SALARY * 1.55, highest_prev_bid + 8.0)
    elif scarcity == 2:
        bid = max(DAILY_SALARY * 1.3, highest_prev_bid + 4.0)
    elif scarcity == 1:
        bid = max(DAILY_SALARY * 1.0, avg_prev_bid + 2.5)
    else:
        if pressured:
            bid = max(DAILY_SALARY * 0.9, avg_prev_bid + 1.5)
        else:
            if highest_prev_bid >= 140:
                bid = DAILY_SALARY * 0.62
            elif highest_prev_bid >= 110:
                bid = DAILY_SALARY * 0.72
            else:
                bid = max(DAILY_SALARY * 0.58, avg_prev_bid * 0.72)

    if rich_aggressive >= 2 and not emergency and scarcity == 0 and hp >= 6:
        bid = min(bid, DAILY_SALARY * 0.6)

    if day >= 8:
        if hp <= 5:
            bid = max(bid, highest_prev_bid + 3.0)
        else:
            bid = max(bid, DAILY_SALARY * 0.8)

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    yesterday_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(bid)

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    scarcity = 1.0 - ((supply - 15.0) / 10.0)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    my_urgency = 0.0
    if hp <= 2:
        my_urgency += 1.0
    elif hp <= 4:
        my_urgency += 0.55
    if no_water >= 2:
        my_urgency += 1.0
    elif no_water >= 1:
        my_urgency += 0.5

    if highest_prev >= 100:
        if my_urgency < 1.0:
            return float(min(budget, DAILY_SALARY * 0.18))
        return float(min(budget, DAILY_SALARY * 0.92))

    base = DAILY_SALARY * (0.28 + 0.22 * scarcity)
    pressure = max(highest_prev + 1.25, avg_prev + 2.0, base)
    pressure += urgent_opp * 1.2
    if rich_opp >= 2:
        pressure += 2.0

    if my_urgency >= 1.5:
        bid = max(pressure, DAILY_SALARY * 0.9)
    elif my_urgency >= 0.5:
        bid = max(pressure, DAILY_SALARY * (0.58 + 0.12 * scarcity))
    else:
        if scarcity < 0.25 and highest_prev > DAILY_SALARY * 0.8:
            bid = DAILY_SALARY * 0.22
        else:
            bid = min(pressure, DAILY_SALARY * (0.62 + 0.08 * scarcity))

    if day >= 8 and hp > 4 and no_water == 0:
        bid *= 0.9

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_pressures = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                b = float(bid)
                prev_bids.append(b)
                req = float(opp.get('water_requirement', WATER_REQ))
                obudget = float(opp.get('budget', 0.0))
                pressure = 0.0
                if req > 0:
                    pressure += min(1.0, supply / req)
                pressure += min(2.0, b / max(1.0, obudget + b))
                opp_pressures.append((b, pressure))

    if not alive_opponents:
        return min(budget, 18.0)

    units = supply / WATER_REQ
    tight = units < 1.45
    roomy = units > 1.75

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    dangerous_opp_bid = 0.0
    if opp_pressures:
        opp_pressures.sort(key=lambda x: (x[1], x[0]), reverse=True)
        dangerous_opp_bid = opp_pressures[int(0)][0]

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water >= 2:
        urgency += 1.0
    elif no_water == 1:
        urgency += 0.45
    if tight:
        urgency += 0.55
    elif roomy:
        urgency -= 0.15

    days_left = max(0, 10 - day)
    reserve_target = max(0.0, days_left * DAILY_SALARY * 0.42)
    spendable = max(0.0, budget - reserve_target)

    if urgency >= 1.6:
        target = max(62.0, dangerous_opp_bid + 3.0, highest_prev + 1.5)
    elif urgency >= 0.9:
        target = max(44.0, avg_prev * 0.72, dangerous_opp_bid * 0.82)
    else:
        if roomy:
            target = max(10.0, avg_prev * 0.18)
        else:
            target = max(18.0, avg_prev * 0.35)

    if budget < DAILY_SALARY * 0.9:
        target *= 0.82
    if spendable < target and urgency < 1.6:
        target = max(8.0, min(target, spendable + DAILY_SALARY * 0.18))

    if hp <= 1 or no_water >= 3:
        target = max(target, min(budget, highest_prev + 6.0, 95.0))

    bid = min(budget, max(0.0, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    danger_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    danger_bids.append(float(bid))

    if not alive:
        base = 8.0 if hp > 3 else 20.0
        return max(0.0, min(float(budget), base))

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units < 1.35:
        scarcity = 2
    elif units < 1.7:
        scarcity = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    danger_prev = max(danger_bids) if danger_bids else highest_prev

    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        target = max(72.0, danger_prev + 3.0)
        if scarcity == 2:
            target = max(target, highest_prev + 5.0)
        return max(0.0, min(float(budget), target))

    if urgent:
        target = max(55.0, danger_prev + 2.0)
        if scarcity >= 1:
            target = max(target, highest_prev + 3.0)
        return max(0.0, min(float(budget), target))

    if scarcity == 2:
        if highest_prev >= 110.0:
            target = 44.0
        elif highest_prev >= 80.0:
            target = highest_prev + 2.5
        else:
            target = max(58.0, highest_prev + 3.0)
    elif scarcity == 1:
        if highest_prev >= 120.0:
            target = 32.0
        elif highest_prev >= 90.0:
            target = 48.0
        else:
            target = max(42.0, highest_prev + 1.5)
    else:
        if highest_prev >= 100.0:
            target = 18.0
        elif highest_prev >= 70.0:
            target = 28.0
        else:
            target = 36.0

    if day >= 8 and hp > 4:
        target *= 0.92

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 12.0
    bid = min(float(budget), target)
    if budget - bid < reserve_floor:
        bid = max(0.0, float(budget) - reserve_floor)

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
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= bid:
                    dangerous_prev.append(float(bid))

    if not alive:
        base = DAILY_SALARY * 0.35
        if no_water >= 2 or hp <= 3:
            base = DAILY_SALARY * 0.75
        return float(min(budget, max(0.0, base)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0
    high_danger = max(dangerous_prev) if dangerous_prev else highest_prev

    my_need_urgent = (no_water >= 2 or hp <= 3)
    need_water = (no_water >= 1 or hp <= 6)

    guaranteed_winners = int(supply // WATER_REQ)
    if guaranteed_winners < 1:
        guaranteed_winners = 1

    alive_count = len(alive)
    scarcity = alive_count - guaranteed_winners

    if guaranteed_winners == 1:
        if my_need_urgent:
            bid = max(DAILY_SALARY * 1.6, high_danger + 8.0, avg_prev + 18.0)
        elif need_water:
            bid = max(DAILY_SALARY * 1.15, high_danger + 3.0)
        else:
            bid = DAILY_SALARY * 0.28
    else:
        if my_need_urgent:
            bid = max(DAILY_SALARY * 0.95, avg_prev + 2.0)
        elif need_water:
            if scarcity >= 2:
                bid = max(DAILY_SALARY * 0.72, avg_prev * 0.78, 52.0)
            else:
                bid = max(DAILY_SALARY * 0.55, avg_prev * 0.62, 38.0)
        else:
            if scarcity >= 2:
                bid = max(24.0, min(DAILY_SALARY * 0.48, avg_prev * 0.5 if avg_prev > 0 else 30.0))
            else:
                bid = 18.0

    if budget < DAILY_SALARY and not my_need_urgent:
        bid = min(bid, budget * 0.55)

    if day >= 8 and (hp <= 5 or no_water >= 1):
        bid = max(bid, min(budget, high_danger + 4.0 if high_danger > 0 else DAILY_SALARY * 0.9))

    bid = min(budget, max(0.0, bid))
    return float(bid)
"""
