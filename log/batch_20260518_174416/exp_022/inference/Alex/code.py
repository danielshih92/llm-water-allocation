# ============================================================
# Experiment: exp_022
# Agent: Alex
# Source: exp_022
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

    total_players = 1 + len(alive_opponents)
    units = int(supply // WATER_REQ)
    scarcity = units < total_players

    prev_bids = []
    desperate_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opponents += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if isinstance(bid, (int, float)):
            prev_bids.append(bid)

    max_prev = max(prev_bids) if prev_bids else 0

    if hp <= 2 or no_water >= 2:
        bid = DAILY_SALARY * 0.98
    elif hp <= 4 or no_water >= 1:
        if scarcity:
            bid = max(DAILY_SALARY * 0.82, max_prev + 2)
        else:
            bid = max(DAILY_SALARY * 0.58, max_prev + 1)
    else:
        if not scarcity:
            bid = DAILY_SALARY * 0.28
            if max_prev > 0 and max_prev < DAILY_SALARY * 0.45:
                bid = max(bid, max_prev + 1)
        else:
            pressure = desperate_opponents + rich_opponents
            if pressure >= max(1, len(alive_opponents) // 2):
                bid = max(DAILY_SALARY * 0.68, max_prev + 1.5)
            else:
                bid = max(DAILY_SALARY * 0.52, max_prev + 1)

    if units <= 0:
        bid = DAILY_SALARY * 0.15

    if bid > budget:
        bid = budget
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_aggressive = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 60 and opp.get('budget', 0) >= 150:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0

    affordable_caps = []
    for opp in alive:
        affordable_caps.append(float(min(opp.get('budget', 0), opp.get('daily_salary', 0))))
    opp_pressure = max(affordable_caps) if affordable_caps else 0.0
    pressure = max(highest_prev, opp_pressure)

    scarcity = 1.0 - ((supply - 15.0) / 10.0)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    if no_water >= 2 or hp <= 3:
        emergency = True
    else:
        emergency = False

    if supply >= WATER_REQ * 2:
        can_clear_market = True
    else:
        can_clear_market = False

    if emergency:
        bid = max(72.0, pressure + 3.0)
        if rich_aggressive >= 2:
            bid = max(bid, 92.0)
        return float(min(budget, bid))

    if can_clear_market:
        if pressure >= 100:
            bid = 18.0
        elif pressure >= 70:
            bid = 28.0
        else:
            bid = max(22.0, min(45.0, pressure * 0.55 + 6.0))
        if no_water == 1:
            bid += 10.0
        return float(min(budget, bid))

    if scarcity >= 0.7:
        if no_water == 1 or hp <= 5:
            bid = max(78.0, pressure + 2.0)
            return float(min(budget, bid))
        return 0.0

    if pressure >= 110:
        bid = 0.0
    elif pressure >= 80:
        bid = 12.0 if no_water == 0 else 55.0
    elif pressure >= 60:
        bid = 18.0 if no_water == 0 else 62.0
    else:
        bid = 26.0 if no_water == 0 else 58.0

    if hp >= 8 and no_water == 0 and scarcity > 0.4 and pressure >= 70:
        bid = 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    highest_prev = 0.0
    cindy_prev = None
    urgent_opp_count = 0
    rich_opp_count = 0

    for oid, opp in alive:
        if float(opp.get('budget', 0.0)) >= DAILY_SALARY * 4:
            rich_opp_count += 1
        if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0)) <= 2:
            urgent_opp_count += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            if bid > highest_prev:
                highest_prev = bid
            if oid == 'Cindy':
                cindy_prev = bid

    slots = int(supply // WATER_REQ)
    scarce = slots <= 1
    abundant = slots >= 2

    if cindy_prev is None:
        cindy_prev = highest_prev if highest_prev > 0 else DAILY_SALARY * 0.8

    danger = hp <= 2 or no_water >= 2
    caution = hp <= 4 or no_water >= 1

    if danger:
        target = max(DAILY_SALARY * 1.15, cindy_prev + 3.0)
    elif scarce:
        if cindy_prev >= 110:
            target = DAILY_SALARY * 0.42 if hp > 4 and no_water == 0 else DAILY_SALARY * 1.05
        else:
            target = max(DAILY_SALARY * 0.9, cindy_prev + 2.0)
    elif abundant:
        target = DAILY_SALARY * 0.28
        if caution and rich_opp_count >= 1:
            target = DAILY_SALARY * 0.52
        if urgent_opp_count >= 2:
            target = max(target, DAILY_SALARY * 0.6)
    else:
        target = DAILY_SALARY * 0.5

    if day >= 8:
        if hp > 4 and no_water == 0 and abundant:
            target = min(target, DAILY_SALARY * 0.22)
        elif caution:
            target = max(target, DAILY_SALARY * 0.82)

    if budget < DAILY_SALARY * 2 and not danger:
        target = min(target, DAILY_SALARY * 0.55)

    bid = max(0.0, min(budget, target))
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
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 500:
                rich_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        return float(min(budget, 18.0))

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0

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
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.7
    elif no_water_days >= 1:
        urgency += 0.3

    if day >= 8:
        urgency += 0.15

    pressure = 0.0
    if max_prev >= 120:
        pressure = 0.85
    elif max_prev >= 95:
        pressure = 0.65
    elif max_prev >= 70:
        pressure = 0.45
    elif max_prev > 0:
        pressure = 0.25

    if supply >= 23:
        base = 18.0
    elif supply >= 20:
        base = 28.0
    elif supply >= 17:
        base = 42.0
    else:
        base = 58.0

    if rich_count >= 2 and scarcity > 0.5 and urgency < 0.8:
        bid = 16.0
    else:
        bid = base + 18.0 * urgency + 16.0 * pressure + 10.0 * scarcity
        if desperate_count >= 2:
            bid += 8.0

    if urgency >= 1.1:
        bid = max(bid, max_prev + 3.0 if max_prev > 0 else 72.0)
    elif urgency >= 0.7 and 40.0 <= max_prev <= 95.0:
        bid = max(bid, max_prev + 2.0)

    if hp >= 7 and no_water_days == 0 and max_prev >= 110 and supply <= 18:
        bid = min(bid, 24.0)

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.92)
    else:
        bid = min(bid, budget)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        if hp <= 3 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    prev_bids = []
    strong_prev = []
    desperate_count = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            prev_bids.append(bid)
            if bid >= 140:
                strong_prev.append(bid)
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    critical = hp <= 2 or no_water_days >= 2
    urgent = hp <= 4 or no_water_days >= 1

    base = DAILY_SALARY * (0.22 + 0.28 * scarcity)

    if strong_prev:
        if critical:
            target = min(budget, max(145.0, highest_prev + 2.0))
            return float(target)
        if urgent and supply <= 18:
            target = min(budget, max(110.0, min(highest_prev - 8.0, 145.0)))
            return float(max(0.0, target))
        target = min(budget, base)
        return float(max(0.0, target))

    if critical:
        target = max(95.0, highest_prev + 3.0, DAILY_SALARY * (0.9 + 0.2 * scarcity))
        return float(min(budget, target))

    if urgent:
        target = max(60.0 + 20.0 * scarcity, avg_prev + 4.0)
        if desperate_count >= 2:
            target += 10.0
        return float(min(budget, target))

    if supply >= 22:
        target = max(8.0, avg_prev * 0.35)
    elif supply >= 19:
        target = max(18.0, avg_prev * 0.45)
    else:
        target = max(28.0, avg_prev * 0.6)

    if day >= 8 and hp >= 7:
        target *= 0.85

    return float(min(budget, max(0.0, target)))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = {}
    for k, v in opponents_status.items():
        if v.get('alive'):
            alive[k] = v

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 1:
            safe_bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, safe_bid))

    y_bids = []
    cindy_bid = None
    david_bid = None
    for name, opp in alive.items():
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            y_bids.append(float(bid))
            if name == 'Cindy':
                cindy_bid = float(bid)
            elif name == 'David':
                david_bid = float(bid)

    highest_prev = max(y_bids) if y_bids else 0.0
    second_prev = 0.0
    if len(y_bids) >= 2:
        second_prev = sorted(y_bids)[-2]
    elif len(y_bids) == 1:
        second_prev = y_bids[0]

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = False
    if hp <= 2 or no_water_days >= 2:
        urgent = True
    elif hp <= 4 and no_water_days >= 1:
        urgent = True

    very_safe = hp >= 8 and no_water_days == 0

    base = DAILY_SALARY * (0.52 + 0.28 * scarcity)

    if urgent:
        target = max(base, highest_prev + 6.0, DAILY_SALARY * 1.18)
    elif supply <= 17:
        target = max(base, second_prev + 3.0, DAILY_SALARY * 0.95)
    elif very_safe and cindy_bid is not None and cindy_bid >= 130:
        target = min(base, DAILY_SALARY * 0.42)
    else:
        reference = david_bid if david_bid is not None else second_prev
        target = max(base, reference + 2.5)
        if cindy_bid is not None and cindy_bid >= 140 and hp >= 6 and no_water_days == 0 and supply >= 20:
            target = min(target, DAILY_SALARY * 0.6)

    if day >= 8:
        target += 6.0
    if day >= 9 and (hp <= 5 or no_water_days >= 1):
        target += 10.0

    max_affordable = budget
    if not urgent and hp >= 6:
        reserve = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
        max_affordable = max(0.0, budget - reserve)

    bid = min(target, budget, max_affordable if max_affordable > 0 else budget)

    if urgent:
        bid = min(max(bid, DAILY_SALARY * 0.95), budget)

    if bid < 0:
        bid = 0.0

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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0.0
    urgent_opponents = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if opp.get('budget', 0.0) > 200:
                    rich_pressure = max(rich_pressure, bid)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    danger = 0
    if hp <= 2 or no_water >= 2:
        danger = 3
    elif hp <= 4 or no_water >= 1:
        danger = 2
    elif hp <= 6:
        danger = 1

    base = 0.0

    if danger >= 3:
        base = max(62.0, highest_prev_bid + 2.0)
    elif danger == 2:
        if scarcity >= 1:
            base = max(48.0, highest_prev_bid * 0.55 + 6.0)
        else:
            base = max(38.0, avg_prev_bid * 0.35 + 5.0)
    else:
        if scarcity == 2:
            base = max(34.0, rich_pressure * 0.28 + 4.0)
        elif scarcity == 1:
            base = max(24.0, avg_prev_bid * 0.18 + 3.0)
        else:
            base = 12.0 + 2.0 * urgent_opponents

    if highest_prev_bid >= 150 and danger <= 1:
        base = min(base, 22.0)
    elif highest_prev_bid >= 120 and danger <= 1:
        base = min(base, 26.0)

    if day >= 8 and hp >= 5 and no_water == 0:
        base *= 0.9

    reserve = DAILY_SALARY * max(0, 10 - int(day)) * 0.12
    affordable = max(0.0, budget - reserve)
    if danger >= 2:
        affordable = budget

    bid = min(base, affordable, budget)

    if danger >= 2 and bid < 20.0 and budget >= 20.0:
        bid = min(budget, 20.0)

    if bid < 0:
        bid = 0.0
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

    yesterday_bids = []
    urgent_opp = 0
    rich_aggressive = 0
    max_prev_bid = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            yesterday_bids.append(b)
            if b > max_prev_bid:
                max_prev_bid = b
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_aggressive += 1

    total_alive = len(alive) + 1
    approx_units = int(supply // WATER_REQ)
    scarcity = approx_units < total_alive
    severe_scarcity = approx_units <= 1

    if yesterday_bids:
        ref_bid = max_prev_bid
    else:
        ref_bid = DAILY_SALARY * 0.55

    if hp <= 2 or no_water >= 2:
        bid = max(62.0, ref_bid + 2.0)
    elif severe_scarcity:
        if hp >= 6 and budget < 350:
            bid = 16.0
        elif hp >= 5 and no_water == 0 and rich_aggressive >= 2:
            bid = 22.0
        else:
            bid = max(58.0, ref_bid + 1.5)
    elif scarcity:
        if hp >= 6 and no_water == 0:
            bid = 26.0 if ref_bid > 75.0 else 34.0
        else:
            bid = max(48.0, ref_bid * 0.82)
    else:
        if hp >= 5 and no_water == 0:
            bid = 12.0
        else:
            bid = 28.0

    if urgent_opp >= 2 and hp >= 5 and no_water == 0:
        bid = min(bid, 24.0)

    if day >= 8 and hp <= 4:
        bid = max(bid, 60.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 70.0
    max_affordable = max(0.0, budget - reserve_floor)
    if hp <= 2 or no_water >= 2 or day >= 9:
        max_affordable = budget

    final_bid = min(float(bid), float(max_affordable if max_affordable > 0 else budget))
    if final_bid < 0:
        final_bid = 0.0
    return float(min(final_bid, budget))
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

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, 35.0))
        return float(min(budget, 18.0))

    prev_bids = []
    opp_pressure = 0.0
    rich_alive = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > 0:
            rich_alive += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid > opp_pressure:
                    opp_pressure = float(bid)

    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
    else:
        avg_prev = 80.0
        max_prev = 100.0

    total_alive = 1 + len(alive_opponents)
    units = int(supply // WATER_REQ)
    scarcity = units < total_alive
    very_tight = units <= 1

    if hp <= 2 or no_water_days >= 2:
        bid = max(150.0, max_prev + 3.0)
    elif hp <= 4 or no_water_days >= 1:
        if very_tight:
            bid = max(140.0, avg_prev + 8.0)
        elif scarcity:
            bid = max(118.0, avg_prev + 2.0)
        else:
            bid = 72.0
    else:
        if very_tight:
            bid = max(132.0, avg_prev + 4.0)
        elif scarcity:
            bid = 58.0
        else:
            bid = 22.0

    if rich_alive == 1 and hp > 4 and no_water_days == 0:
        bid = min(bid, 45.0)

    if day >= 8:
        if hp <= 5:
            bid = max(bid, 110.0)
        else:
            bid = max(bid, 40.0)

    bid = min(bid, budget)
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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, 18.0))

    units = supply / WATER_REQ
    scarcity = units < 2.0

    prev_bids = []
    strong_opp = 0
    weak_opp = 0
    desperate_opp = 0
    rich_opp = 0

    for oid, opp in alive:
        if opp.get('budget', 0) >= 140:
            rich_opp += 1
        if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 90:
                strong_opp += 1
            if bid <= 20:
                weak_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency == 3:
        base = 112.0 if scarcity else 88.0
    elif urgency == 2:
        base = 82.0 if scarcity else 62.0
    elif urgency == 1:
        base = 44.0 if scarcity else 28.0
    else:
        base = 16.0 if scarcity else 8.0

    if highest_prev >= 140:
        if urgency <= 1:
            bid = 6.0 if not scarcity else 12.0
        else:
            bid = base + 8.0
    elif highest_prev >= 90:
        bid = base + (6.0 if urgency >= 2 else -4.0)
    elif highest_prev > 0:
        bid = max(base, avg_prev + 3.0)
    else:
        bid = base

    if weak_opp >= 2 and urgency >= 1:
        bid += 6.0
    if desperate_opp >= 2 and scarcity:
        bid += 10.0
    if rich_opp >= 2 and urgency == 0:
        bid -= 4.0

    if day >= 8:
        if urgency >= 2:
            bid += 10.0
        elif hp >= 7:
            bid -= 3.0

    reserve = 0.0
    if hp >= 7 and day <= 5:
        reserve = 35.0
    elif hp >= 5 and day <= 7:
        reserve = 20.0
    max_affordable = max(0.0, budget - reserve)

    if urgency >= 2:
        max_affordable = budget

    bid = max(0.0, min(bid, max_affordable))

    if urgency == 0 and scarcity and strong_opp >= 1:
        bid = min(bid, 18.0)

    return float(max(0.0, min(bid, budget)))
"""
