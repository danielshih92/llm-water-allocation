# ============================================================
# Experiment: exp_058
# Agent: Alex
# Source: exp_058
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    total_alive = 1 + len(alive_opponents)
    units = int(supply // WATER_REQ)
    scarce = units < total_alive
    very_scarce = units <= max(0, total_alive - 2)

    highest_prev_bid = 0
    desperate_opp = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > highest_prev_bid:
                highest_prev_bid = prev['bid']
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp = True

    if hp <= 1:
        base = DAILY_SALARY * 0.98
    elif no_water_days >= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 3:
        base = DAILY_SALARY * 0.82
    elif very_scarce:
        base = DAILY_SALARY * 0.72
    elif scarce:
        base = DAILY_SALARY * 0.58
    else:
        base = DAILY_SALARY * 0.34

    if highest_prev_bid > 0:
        if hp <= 3 or no_water_days >= 1 or scarce:
            target = highest_prev_bid + 1.5
            if target > base:
                base = target
        elif highest_prev_bid >= DAILY_SALARY * 0.9:
            base = min(base, DAILY_SALARY * 0.3)

    if desperate_opp and (hp > 3 and no_water_days == 0) and scarce:
        base = min(base, DAILY_SALARY * 0.45)

    if not alive_opponents:
        base = DAILY_SALARY * 0.25

    if base > budget:
        return budget
    if base < 0:
        return 0
    return base
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 20.0))

    units_available = int(supply // WATER_REQ)
    if units_available < 1:
        units_available = 1

    opp_bids = []
    urgent_opp = 0
    rich_opp = 0
    max_prev_bid = 0.0
    sum_prev_bid = 0.0
    count_prev = 0

    for opp in alive:
        if opp.get('budget', 0) >= 350:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            opp_bids.append(float(bid))
            sum_prev_bid += float(bid)
            count_prev += 1
            if float(bid) > max_prev_bid:
                max_prev_bid = float(bid)

    avg_prev_bid = (sum_prev_bid / count_prev) if count_prev > 0 else 55.0

    scarcity = 0
    if units_available <= 1:
        scarcity = 2
    elif units_available == 2:
        scarcity = 1

    my_urgent = False
    if hp <= 3 or no_water >= 1:
        my_urgent = True

    if my_urgent:
        target = max(82.0, max_prev_bid + 2.5)
        if scarcity >= 2:
            target = max(target, 96.0)
        elif scarcity == 1:
            target = max(target, 86.0)
        return float(min(budget, target))

    if hp >= 8 and no_water == 0:
        if max_prev_bid >= 90.0 and scarcity >= 1:
            return float(min(budget, 24.0))
        if scarcity >= 2:
            return float(min(budget, 41.0))
        return float(min(budget, 18.0))

    target = avg_prev_bid + 1.6
    if max_prev_bid >= 100.0:
        target = min(target, 62.0)
    elif max_prev_bid >= 85.0:
        target = min(target, 58.0)

    if scarcity >= 2:
        target += 10.0
    elif scarcity == 1:
        target += 4.0

    if urgent_opp >= 2:
        target += 6.0
    elif urgent_opp == 0 and max_prev_bid >= 85.0:
        target -= 6.0

    if rich_opp >= 3 and scarcity >= 1:
        target += 4.0

    if day >= 8 and hp <= 5:
        target += 10.0

    if hp <= 5:
        target = max(target, 64.0)
    else:
        target = max(target, 36.0)

    if budget < 120:
        target = min(target, budget)
    else:
        target = min(target, 92.0)

    if target < 0:
        target = 0.0

    return float(min(budget, target))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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
    eric_prev = None
    strongest_prev = 0.0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > strongest_prev:
                    strongest_prev = float(bid)
            if agent_id == 'Eric' and bid is not None:
                eric_prev = float(bid)

    if not alive:
        return float(min(budget, 18.0))

    scarcity = 0.0
    if supply <= 16:
        scarcity = 1.0
    elif supply <= 18:
        scarcity = 0.7
    elif supply <= 21:
        scarcity = 0.4
    else:
        scarcity = 0.1

    danger = 0.0
    if hp <= 2 or no_water_days >= 2:
        danger = 1.0
    elif hp <= 4 or no_water_days >= 1:
        danger = 0.65
    elif hp <= 6:
        danger = 0.35
    else:
        danger = 0.1

    target = 22.0 + 18.0 * scarcity + 20.0 * danger

    if eric_prev is not None:
        if supply <= 18 or danger >= 0.65:
            target = max(target, eric_prev + 2.0)
        else:
            target = max(target, eric_prev * 0.72)
            if eric_prev >= 120:
                target -= 6.0
    elif strongest_prev > 0:
        target = max(target, strongest_prev * 0.8 + 1.0)

    living_count = len(alive)
    if living_count >= 3 and supply <= 17:
        target += 8.0
    elif living_count <= 1 and danger < 0.65:
        target -= 6.0

    if day >= 8:
        target += 8.0 * danger

    if budget < 80:
        target = min(target, budget * (0.72 if danger < 1.0 else 0.9))
    else:
        cap = budget * (0.55 + 0.3 * danger)
        target = min(target, cap)

    floor_bid = 8.0
    if danger >= 0.65:
        floor_bid = 20.0
    elif scarcity >= 0.7:
        floor_bid = 15.0

    bid = max(floor_bid, target)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 100:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (25.0 - float(supply)) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.55
    if no_water_days >= 1:
        danger += 0.8

    base = 24.0 + 20.0 * scarcity + 10.0 * danger

    if float(supply) <= 16.0:
        base += 18.0
    elif float(supply) >= 22.0:
        base -= 8.0

    if urgent_opp >= 2:
        base += 8.0
    if rich_opp >= 2:
        base += 6.0

    if highest_prev >= 170.0:
        if hp > 4 and no_water_days == 0 and float(supply) >= 19.0:
            bid = 16.0
        else:
            bid = max(base + 10.0, 92.0)
    elif highest_prev >= 130.0:
        if hp > 5 and no_water_days == 0 and float(supply) >= 20.0:
            bid = max(base - 6.0, 20.0)
        else:
            bid = max(base, min(highest_prev * 0.78, highest_prev - 8.0))
    elif highest_prev >= 80.0:
        bid = max(base, avg_prev + 3.0)
    elif highest_prev > 0.0:
        bid = max(base, highest_prev + 2.0)
    else:
        bid = base

    if hp <= 2 or no_water_days >= 1:
        bid = max(bid, 88.0 + 14.0 * scarcity)

    if day >= 8:
        bid += 6.0

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = 10.0
    max_affordable = max(0.0, budget - reserve)
    if max_affordable <= 0.0:
        max_affordable = budget

    bid = min(bid, max_affordable)
    if bid < 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if opp.get('budget', 0) > DAILY_SALARY * 8 and bid >= DAILY_SALARY * 0.8:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = DAILY_SALARY * (0.42 + 0.28 * scarcity)

    if highest_prev >= 120:
        base = max(base, min(highest_prev * 0.72, DAILY_SALARY * 0.95))
    elif highest_prev >= 80:
        base = max(base, min(avg_prev + 3.0, DAILY_SALARY * 0.88))
    elif highest_prev > 0:
        base = max(base, min(highest_prev + 2.0, DAILY_SALARY * 0.78))

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.97)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.82)
    elif hp >= 8 and no_water_days == 0 and supply >= 22:
        base = min(base, DAILY_SALARY * 0.38)

    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.98)
    elif no_water_days == 1:
        base = max(base, DAILY_SALARY * 0.86)

    if rich_aggressive >= 2 and hp > 4 and no_water_days == 0:
        base = min(base, DAILY_SALARY * 0.45)

    if desperate_count >= 2 and hp > 5 and supply >= 20:
        base = min(base, DAILY_SALARY * 0.4)

    if day >= 8:
        base = max(base, DAILY_SALARY * 0.62)
    if day >= 9 and hp <= 5:
        base = max(base, DAILY_SALARY * 0.9)

    bid = min(budget, base)
    if bid < 0:
        bid = 0.0
    return float(bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    weak_count = 0
    strong_count = 0
    rich_aggressive = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = None
            if prev:
                bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) <= 80:
                    weak_count += 1
                if float(bid) >= 140:
                    strong_count += 1
            if opp.get('budget', 0) >= 300 and opp.get('hp', 0) >= 6:
                if bid is not None and float(bid) >= 120:
                    rich_aggressive += 1

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 20)

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 110.0
    max_prev = max(prev_bids) if prev_bids else 110.0
    min_prev = min(prev_bids) if prev_bids else 70.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)

    emergency = False
    if hp <= 3 or no_water_days >= 2:
        emergency = True
    elif hp <= 5 and day >= 7:
        emergency = True

    if emergency:
        bid = max(0.9 * DAILY_SALARY, min(0.92 * budget, max_prev + 3))
        return min(budget, bid)

    if supply >= 22:
        bid = 58
        if weak_count >= 1:
            bid = 52
        if strong_count >= 2:
            bid = 64
        if hp >= 8 and budget < 250:
            bid = min(bid, 50)
        return min(budget, bid)

    if supply >= 19:
        bid = 68
        if avg_prev >= 140:
            bid = 62
        elif min_prev <= 70:
            bid = 72
        if rich_aggressive >= 2:
            bid = 66
        if hp >= 8 and no_water_days == 0:
            bid -= 4
        return min(budget, max(45, bid))

    bid = 78
    if avg_prev >= 145:
        bid = 72
    elif weak_count >= 2:
        bid = 84
    if day >= 8 and hp <= 6:
        bid = max(bid, 88)
    if budget < 180:
        bid = min(bid, 74)

    return min(budget, max(50, bid))
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

    alive = []
    prev_bids = []
    strong_pressure = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 75:
                    strong_pressure += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    for b in prev_bids:
        if b < 75 and b > moderate_prev:
            moderate_prev = b

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    emergency = False
    if hp <= 2 or no_water_days >= 2:
        emergency = True
    elif hp <= 4 and no_water_days >= 1:
        emergency = True

    if emergency:
        bid = 92.0 if scarcity >= 1 else 82.0
        if moderate_prev > 0:
            bid = max(bid, moderate_prev + 6.0)
        return float(min(budget, bid))

    if hp >= 8 and no_water_days == 0 and scarcity == 0:
        if strong_pressure >= 1:
            return float(min(budget, 24.0))
        if moderate_prev > 0:
            return float(min(budget, max(22.0, moderate_prev - 4.0)))
        return float(min(budget, 26.0))

    if scarcity == 2:
        if strong_pressure >= 1:
            bid = 68.0
        else:
            bid = max(52.0, moderate_prev + 2.5 if moderate_prev > 0 else 52.0)
    elif scarcity == 1:
        if strong_pressure >= 1:
            bid = 54.0
        else:
            bid = max(42.0, moderate_prev + 2.0 if moderate_prev > 0 else 42.0)
    else:
        if strong_pressure >= 1:
            bid = 34.0
        else:
            bid = max(30.0, moderate_prev + 1.5 if moderate_prev > 0 else 30.0)

    if hp <= 5:
        bid += 10.0
    elif hp <= 7:
        bid += 4.0

    if no_water_days == 1:
        bid += 8.0

    if day >= 8 and hp <= 6:
        bid += 6.0

    if budget < 120:
        bid = min(bid, budget * 0.72)
    elif budget < 200:
        bid = min(bid, budget * 0.6)

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
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

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('budget', 0) > budget:
                rich_pressure += 1

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 45.0))
        return float(min(budget, 18.0))

    prev_bids.sort(reverse=True)
    top_bid = prev_bids[int(0)] if len(prev_bids) >= 1 else 0.0
    second_bid = prev_bids[int(1)] if len(prev_bids) >= 2 else top_bid
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 1.0
    if supply <= 16:
        scarcity = 1.25
    elif supply >= 23:
        scarcity = 0.85

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
    if day >= 8 and hp <= 5:
        urgency += 1

    if urgency >= 5:
        bid = max(62.0, second_bid * 0.7, avg_prev * 0.6)
    elif urgency >= 3:
        bid = max(42.0, second_bid * 0.45, avg_prev * 0.38)
    elif urgency >= 1:
        bid = max(24.0, second_bid * 0.22, avg_prev * 0.2)
    else:
        if top_bid >= 120:
            bid = 14.0
        elif top_bid >= 90:
            bid = 18.0
        else:
            bid = max(16.0, avg_prev * 0.16)

    if rich_pressure >= 2 and urgency <= 1:
        bid *= 0.9

    bid *= scarcity

    reserve_target = max(0.0, (10 - day) * 16.0)
    if budget > reserve_target + 80:
        bid *= 1.08
    elif budget < reserve_target:
        bid *= 0.85

    if hp >= 8 and no_water_days == 0 and supply >= 22:
        bid = min(bid, 16.0)

    bid = max(1.0, min(budget, bid))
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
    rich_opp_pressure = 0.0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev.get('bid', 0.0))
                prev_bids.append(bid)
                if opp.get('budget', 0) > budget * 0.8:
                    rich_opp_pressure = max(rich_opp_pressure, bid)

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = int(supply / WATER_REQ)
    scarcity = units <= 1
    severe_scarcity = float(supply) <= 16.0

    danger = hp <= 3 or no_water_days >= 2
    caution = hp <= 5 or no_water_days >= 1

    if danger:
        base = max(92.0, highest_prev + 8.0)
        if severe_scarcity:
            base = max(base, 118.0)
        if rich_opp_pressure >= 120.0:
            base = max(base, rich_opp_pressure + 3.0)
        return float(min(budget, base))

    if scarcity:
        if highest_prev >= 140.0:
            bid = 34.0 if hp >= 7 and no_water_days == 0 else 96.0
            return float(min(budget, bid))
        if highest_prev >= 85.0:
            bid = 42.0 if hp >= 8 and no_water_days == 0 else highest_prev + 4.0
            return float(min(budget, bid))

        bid = 48.0
        if caution:
            bid = 72.0
        if urgent_opp_count >= 2:
            bid += 10.0
        if severe_scarcity:
            bid += 8.0
        return float(min(budget, bid))

    bid = 22.0
    if caution:
        bid = 38.0
    if avg_prev > 60.0:
        bid = max(bid, min(58.0, avg_prev * 0.75))
    if day >= 8 and hp <= 6:
        bid = max(bid, 55.0)

    return float(min(budget, bid))
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

    alive_opps = []
    prev_bids = []
    aggressive_count = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 90:
                    aggressive_count += 1

    if not alive_opps:
        return float(min(budget, 8.0))

    tight_supply = supply <= 18
    abundant_supply = supply >= 22

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency = 4
    elif hp <= 4:
        urgency = 3
    elif no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency >= 4:
        bid = max(95.0, highest_prev + 3.0)
    elif urgency == 3:
        if tight_supply:
            bid = max(82.0, avg_prev + 4.0)
        else:
            bid = max(72.0, avg_prev + 2.0)
    elif urgency == 2:
        if aggressive_count >= 2 and not tight_supply:
            bid = 48.0
        else:
            bid = max(58.0, avg_prev * 0.72)
    elif urgency == 1:
        if abundant_supply and aggressive_count >= 1:
            bid = 24.0
        elif tight_supply:
            bid = max(44.0, avg_prev * 0.55)
        else:
            bid = 34.0
    else:
        if abundant_supply:
            bid = 12.0
        elif tight_supply and desperate_count >= 2:
            bid = 36.0
        elif highest_prev >= 100:
            bid = 18.0
        else:
            bid = 26.0

    if day >= 8:
        bid += 8.0
    if day >= 9 and (hp <= 5 or no_water_days >= 1):
        bid += 12.0

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = 35.0
    elif hp > 2:
        reserve = 15.0

    max_affordable = max(0.0, budget - reserve)
    if max_affordable <= 0:
        return float(min(budget, 10.0))

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
"""
