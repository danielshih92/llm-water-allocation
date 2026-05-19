# ============================================================
# Experiment: exp_107
# Agent: Alex
# Source: exp_107
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
    prev_bids = []
    desperate_count = 0
    error_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
            if prev.get('error'):
                error_count += 1

    alive_n = len(alive)
    total_players = alive_n + 1
    units = int(supply // WATER_REQ)
    scarcity = units < total_players
    severe_scarcity = units <= max(0, total_players - 2)

    if budget <= 0:
        return 0

    if hp <= 2 or no_water >= 2:
        emergency = DAILY_SALARY * 0.95
        if prev_bids:
            emergency = max(emergency, max(prev_bids) + 1.0)
        return min(budget, emergency)

    if hp <= 4 or no_water >= 1:
        pressure_bid = DAILY_SALARY * 0.72
        if prev_bids:
            pressure_bid = max(pressure_bid, min(DAILY_SALARY * 0.9, max(prev_bids) + 1.0))
        if not scarcity:
            pressure_bid *= 0.9
        return min(budget, pressure_bid)

    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        top_prev = 0
        avg_prev = 0

    if not scarcity:
        bid = DAILY_SALARY * 0.34
        if top_prev > 0:
            bid = min(DAILY_SALARY * 0.55, max(bid, avg_prev * 0.85))
        if error_count > 0:
            bid *= 0.92
    elif severe_scarcity:
        bid = DAILY_SALARY * 0.68
        if top_prev > 0:
            bid = max(bid, min(DAILY_SALARY * 0.88, top_prev + 1.0))
        if desperate_count >= max(1, alive_n // 2):
            bid += 4.0
    else:
        bid = DAILY_SALARY * 0.52
        if top_prev > 0:
            bid = max(bid, min(DAILY_SALARY * 0.78, top_prev + 0.5))
        if desperate_count > 0:
            bid += 2.0

    if budget < DAILY_SALARY * 1.5:
        bid *= 0.9
    if budget < DAILY_SALARY:
        bid *= 0.82

    if bid < 0:
        bid = 0
    return min(budget, bid)
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_requirements = []
    desperate_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    players_alive = 1 + len(alive)
    total_req = WATER_REQ + sum(opp_requirements) if opp_requirements else WATER_REQ * players_alive
    scarcity = total_req / max(supply, 1.0)

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

    tight_supply = supply <= 18
    very_tight = supply <= 16

    if budget <= 0:
        return 0.0

    if not alive:
        base = DAILY_SALARY * 0.22
        if urgency >= 3:
            base = DAILY_SALARY * 0.55
        return max(0.0, min(budget, base))

    if urgency >= 5:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif urgency >= 3:
        bid = max(DAILY_SALARY * 0.78, avg_prev + 2.0)
    else:
        if very_tight:
            bid = max(DAILY_SALARY * 0.72, avg_prev + 1.5)
        elif tight_supply:
            bid = max(DAILY_SALARY * 0.58, avg_prev * 0.92)
        else:
            if highest_prev >= 120:
                bid = DAILY_SALARY * 0.28
            elif highest_prev >= 95:
                bid = DAILY_SALARY * 0.38
            else:
                bid = max(DAILY_SALARY * 0.34, avg_prev * 0.72)

    if scarcity > 2.6:
        bid += 10.0
    elif scarcity > 2.2:
        bid += 6.0
    elif scarcity < 1.8 and urgency == 0:
        bid -= 5.0

    if desperate_opp >= 2:
        bid += 4.0
    if rich_opp >= 2 and urgency == 0:
        bid -= 3.0

    if day >= 8:
        if hp <= 5:
            bid += 8.0
        else:
            bid += 2.0

    if budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.62)
    elif budget < DAILY_SALARY * 4 and urgency == 0:
        bid = min(bid, DAILY_SALARY * 0.62)

    bid = max(0.0, min(budget, bid))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    prev_bids = []
    urgent_opp_bids = []
    rich_threat = 0.0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_bids.append(float(bid))
        if opp.get('budget', 0) > rich_threat:
            rich_threat = float(opp.get('budget', 0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else 0.0

    my_urgent = hp <= 3 or no_water >= 1
    very_urgent = hp <= 2 or no_water >= 2

    if len(alive_opps) == 0:
        return float(min(budget, 20.0))

    if very_urgent:
        target = max(92.0, highest_prev + 3.0)
        if rich_threat > budget * 1.2:
            target += 8.0
        return float(min(budget, target))

    if my_urgent:
        target = max(78.0, urgent_prev + 2.0, highest_prev * 0.72)
        return float(min(budget, target))

    if slots >= 2:
        base = 46.0
        if highest_prev > 80:
            base = 58.0
        elif highest_prev > 55:
            base = 52.0
        return float(min(budget, base))

    # slots == 1 most of the time: conserve unless market softens
    if highest_prev >= 120:
        bid = 18.0
    elif highest_prev >= 90:
        bid = 26.0
    elif highest_prev >= 65:
        bid = 41.0
    else:
        bid = max(44.0, highest_prev + 1.5)

    if budget < 90:
        bid = min(bid, budget * 0.55)
    elif budget > 220 and highest_prev < 80:
        bid += 4.0

    return float(min(budget, max(0.0, bid)))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    opp_requirements = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive:
        return float(min(budget, 18.0))

    total_req = WATER_REQ
    for req in opp_requirements:
        total_req += req

    scarcity = total_req / max(supply, 1.0)
    strong_pressure = max(prev_bids) if prev_bids else 0.0
    avg_pressure = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2
    tight_supply = supply <= 18
    loose_supply = supply >= 22

    if critical:
        bid = max(0.92 * DAILY_SALARY, strong_pressure + 3.0)
        return float(min(budget, bid))

    if urgent:
        if strong_pressure > 0:
            bid = max(0.78 * DAILY_SALARY, strong_pressure + 2.0)
        else:
            bid = 0.78 * DAILY_SALARY
        return float(min(budget, bid))

    if tight_supply or scarcity > 2.2:
        if strong_pressure >= 150:
            bid = min(strong_pressure + 1.5, 0.88 * DAILY_SALARY)
        elif strong_pressure >= 90:
            bid = max(0.62 * DAILY_SALARY, strong_pressure + 2.0)
        else:
            bid = 0.58 * DAILY_SALARY
    elif loose_supply and avg_pressure >= 140:
        bid = 0.22 * DAILY_SALARY
    elif loose_supply:
        bid = 0.30 * DAILY_SALARY
    else:
        if strong_pressure >= 170:
            bid = 0.26 * DAILY_SALARY
        elif strong_pressure >= 120:
            bid = 0.40 * DAILY_SALARY
        elif strong_pressure > 0:
            bid = max(0.42 * DAILY_SALARY, strong_pressure * 0.55)
        else:
            bid = 0.45 * DAILY_SALARY

    if budget < 2 * DAILY_SALARY:
        bid = min(bid, 0.55 * DAILY_SALARY)
    if budget < DAILY_SALARY:
        bid = min(bid, 0.75 * budget)

    bid = max(0.0, min(budget, bid))
    return float(bid)
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

    alive = []
    prev_bids = []
    strong_prev = 0
    desperate_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if b >= DAILY_SALARY * 0.85:
                    strong_prev += 1

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, DAILY_SALARY * 0.35)

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.45

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

    if slots >= 2:
        base = DAILY_SALARY * 0.34
        if strong_prev >= 2:
            base = max(base, avg_prev * 0.72)
        elif highest_prev > 0:
            base = max(base, min(highest_prev * 0.68, DAILY_SALARY * 0.62))
    else:
        base = DAILY_SALARY * 0.62
        if highest_prev > 0:
            base = max(base, highest_prev + 2.0)

    if desperate_opp >= 2:
        base += 6
    elif desperate_opp == 1:
        base += 3

    if urgency >= 5:
        bid = max(base, DAILY_SALARY * 0.96)
    elif urgency >= 3:
        bid = max(base, DAILY_SALARY * 0.78)
    elif urgency >= 1:
        bid = max(base, DAILY_SALARY * 0.56)
    else:
        bid = base

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.9

    if budget < DAILY_SALARY * 0.8:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, DAILY_SALARY * 1.25)

    if bid < 0:
        bid = 0
    return bid
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 1.5:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_desperate = hp <= 2 or no_water_days >= 2
    somewhat_urgent = hp <= 4 or no_water_days >= 1

    if my_desperate:
        target = max(DAILY_SALARY * 0.92, highest_prev + 3.0)
        if supply <= 17:
            target = max(target, DAILY_SALARY * 1.02)
        return float(min(budget, target))

    if somewhat_urgent:
        target = DAILY_SALARY * (0.62 + 0.25 * scarcity)
        if highest_prev > 0:
            target = max(target, highest_prev + 1.5)
        return float(min(budget, target))

    if supply >= 22 and desperate_count == 0:
        target = DAILY_SALARY * 0.22
    elif supply >= 20:
        target = DAILY_SALARY * 0.32
    elif supply >= 18:
        target = DAILY_SALARY * 0.42
    else:
        target = DAILY_SALARY * 0.55

    if highest_prev >= DAILY_SALARY * 1.6:
        target = min(target, DAILY_SALARY * 0.28)
    elif highest_prev >= DAILY_SALARY * 1.1:
        target = max(target, DAILY_SALARY * 0.48)
    elif highest_prev > 0:
        target = max(target, min(highest_prev + 1.0, DAILY_SALARY * 0.75))
    else:
        target = max(target, DAILY_SALARY * 0.35)

    if rich_count >= 2 and supply <= 18:
        target += 6.0

    if day >= 8 and budget > DAILY_SALARY * 2:
        target += 4.0

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        base = 18.0 if no_water_days > 0 or hp <= 3 else 8.0
        return float(min(budget, base))

    prev_bids = []
    prev_need_bids = []
    aggressive_count = 0
    rich_count = 0
    desperate_count = 0

    for opp in alive_opponents:
        if opp.get('budget', 0) >= 400:
            rich_count += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 90:
                    aggressive_count += 1
                opp_req = opp.get('water_requirement', WATER_REQ)
                if opp_req > 0:
                    prev_need_bids.append(float(bid) / float(opp_req))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_need_pressure = max(prev_need_bids) if prev_need_bids else 0.0

    supply_ratio = float(supply) / float(MAX_SUPPLY)
    tight_supply = supply <= 18
    very_tight_supply = supply <= 16

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if very_tight_supply:
        urgency += 2
    elif tight_supply:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1

    if urgency >= 7:
        bid = max(95.0, highest_prev + 3.0)
    elif urgency >= 5:
        bid = max(72.0, avg_prev * 0.9, highest_prev + 1.5 if highest_prev > 0 else 72.0)
    elif urgency >= 3:
        if aggressive_count >= 2 and hp > 4 and no_water_days == 0 and supply >= 20:
            bid = 28.0
        else:
            bid = max(48.0, avg_prev * 0.7, max_need_pressure * WATER_REQ * 0.92)
    else:
        if aggressive_count >= 1 or rich_count >= 2:
            bid = 20.0 if supply_ratio >= 0.8 else 26.0
        else:
            bid = max(18.0, avg_prev * 0.45)

    if day >= 8:
        bid += 8.0
    elif day >= 6 and (hp <= 4 or no_water_days >= 1):
        bid += 5.0

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if days_left >= 3 and hp > 3 and no_water_days == 0:
        reserve_floor = min(budget * 0.45, days_left * 18.0)

    affordable = max(0.0, budget - reserve_floor)
    if urgency >= 5:
        affordable = budget

    bid = min(bid, affordable if affordable > 0 else budget)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_prev = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 70:
                    strong_prev.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    units = int(supply / WATER_REQ)
    if units < 1:
        units = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        second_prev = sorted(prev_bids)[-2]

    danger = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if units == 1:
        if critical:
            bid = max(92.0, highest_prev + 2.0)
        elif danger:
            bid = max(78.0, second_prev + 2.0, highest_prev * 0.72)
        else:
            if highest_prev >= 120:
                bid = 58.0
            elif highest_prev >= 90:
                bid = 66.0
            else:
                bid = max(52.0, second_prev + 1.5)
    else:
        if critical:
            bid = max(72.0, second_prev + 1.5)
        elif danger:
            bid = max(54.0, min(78.0, second_prev + 1.5))
        else:
            if highest_prev >= 120:
                bid = 34.0
            elif highest_prev >= 90:
                bid = 42.0
            else:
                bid = 28.0

    live_count = len(alive)
    if live_count >= 3 and units == 1 and not danger:
        bid -= 4.0

    reserve_floor = 0.0
    if day_context['day'] <= 7:
        reserve_floor = 70.0
    if budget < reserve_floor + bid:
        bid = max(0.0, budget - reserve_floor)

    if critical and bid < 65.0:
        bid = min(budget, 65.0)

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
    prev_bids = []
    dangerous_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) > 2 and opp.get('budget', 0) > 0:
                    dangerous_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    if no_water_days >= 2:
        urgency += 0.45
    elif no_water_days >= 1:
        urgency += 0.2
    if day >= 8:
        urgency += 0.1

    base = 16.0 + 18.0 * scarcity + 22.0 * urgency

    ref_bids = dangerous_bids if dangerous_bids else prev_bids
    highest_prev = max(ref_bids) if ref_bids else 0.0
    avg_prev = sum(ref_bids) / len(ref_bids) if ref_bids else 0.0

    if highest_prev >= 130:
        if hp > 4 and no_water_days == 0:
            bid = 8.0 + 10.0 * scarcity
        else:
            bid = min(0.92 * DAILY_SALARY, 46.0 + 18.0 * urgency + 8.0 * scarcity)
    elif highest_prev >= 80:
        if urgency >= 0.45:
            bid = max(base, min(highest_prev + 2.0, 0.95 * DAILY_SALARY))
        else:
            bid = max(18.0 + 10.0 * scarcity, avg_prev * 0.45)
    elif highest_prev > 0:
        bid = max(base, highest_prev + 2.0)
    else:
        bid = base

    if supply >= 22 and hp > 4 and no_water_days == 0:
        bid *= 0.72
    elif supply <= 17:
        bid *= 1.18

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 60.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, 42.0)

    max_safe = budget
    if day < 10:
        reserve_days = max(0, 10 - int(day))
        reserve = min(budget * 0.35, reserve_days * 8.0)
        max_safe = max(0.0, budget - reserve)
        if hp <= 3 or no_water_days >= 1:
            max_safe = budget

    bid = min(bid, max_safe if max_safe > 0 else budget)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    winners_est = int(supply / WATER_REQ)
    if winners_est < 1:
        winners_est = 1

    prev_bids = []
    threatening_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) >= bid * 0.8:
                threatening_bids.append(float(bid))

    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0
    max_threat = max(threatening_bids) if threatening_bids else max_prev

    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1

    if not alive:
        if urgent:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    if winners_est >= 2:
        if urgent:
            bid = max(DAILY_SALARY * 0.72, min_prev + 2.0)
        elif semi_urgent:
            bid = max(DAILY_SALARY * 0.58, min_prev + 1.0)
        else:
            bid = max(DAILY_SALARY * 0.42, min_prev * 0.75 if min_prev > 0 else DAILY_SALARY * 0.42)
    else:
        if urgent:
            bid = max(DAILY_SALARY * 1.18, max_threat + 3.0)
        elif semi_urgent:
            if max_threat >= 110:
                bid = DAILY_SALARY * 0.18
            else:
                bid = max(DAILY_SALARY * 0.88, max_threat + 1.5)
        else:
            if max_threat >= 75:
                bid = DAILY_SALARY * 0.08
            else:
                bid = DAILY_SALARY * 0.45

    if day >= 8:
        bid = max(bid, DAILY_SALARY * 0.7 if semi_urgent else bid)
    if day >= 9 and urgent:
        bid = max(bid, DAILY_SALARY * 1.0)

    if budget < bid:
        bid = budget

    if bid < 0:
        bid = 0.0

    return float(bid)
"""
