# ============================================================
# Experiment: exp_046
# Agent: Alex
# Source: exp_046
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

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 0.9:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0, min(budget, round(DAILY_SALARY * 0.35, 2)))

    players = 1 + len(alive)
    scarcity = supply / float(players * WATER_REQ)

    if hp <= 2 or no_water >= 2:
        base = DAILY_SALARY * 0.97
    elif hp <= 4 or no_water >= 1:
        base = DAILY_SALARY * 0.82
    elif scarcity < 0.9:
        base = DAILY_SALARY * 0.74
    elif scarcity < 1.1:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.46

    if prev_bids:
        top_prev = max(prev_bids)
        if top_prev >= DAILY_SALARY * 0.9:
            if hp > 4 and no_water == 0 and scarcity >= 1.0:
                base = min(base, DAILY_SALARY * 0.38)
            else:
                base = max(base, min(DAILY_SALARY * 0.96, top_prev + 1.25))
        elif top_prev >= DAILY_SALARY * 0.65:
            base = max(base, min(DAILY_SALARY * 0.88, top_prev + 1.0))
        else:
            base = max(base, top_prev + 0.75)

    if urgent_opp >= max(1, len(alive) // 2) and scarcity < 1.0:
        base += 4.0
    if rich_opp >= max(1, len(alive) // 2) and scarcity < 1.0:
        base += 3.0

    if budget < DAILY_SALARY * 0.5:
        base = min(base, budget)
    else:
        reserve_floor = 0
        days_left_est = max(0, 10 - int(day_context['day']))
        if days_left_est > 0:
            reserve_floor = min(budget * 0.4, days_left_est * DAILY_SALARY * 0.18)
        base = min(base, max(0, budget - reserve_floor))

    bid = max(0, min(budget, base))
    return round(bid, 2)
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
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    strong_prev = 0.0
    weak_count = 0
    desperate_count = 0
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > strong_prev:
                strong_prev = float(bid)
            if float(bid) <= 5:
                weak_count += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1

    alive_count = len(alive)
    supply_ratio = float(supply) / float(WATER_REQ)

    if hp <= 2 or no_water_days >= 2:
        emergency = max(63.0, strong_prev + 2.0)
        return float(min(budget, emergency))

    if supply_ratio >= alive_count + 0.4:
        base = 8.0
    elif supply_ratio >= alive_count:
        base = 16.0
    elif supply_ratio >= max(1, alive_count - 1):
        base = 28.0
    else:
        base = 44.0

    if strong_prev >= 75:
        target = 24.0 if hp >= 4 else 58.0
    elif strong_prev >= 60:
        target = strong_prev + 1.6 if (hp <= 3 or supply_ratio < alive_count) else 26.0
    elif strong_prev >= 40:
        target = max(base, strong_prev + 1.2)
    elif strong_prev > 0:
        target = max(base, strong_prev + 0.8)
    else:
        target = base

    if weak_count >= max(1, alive_count - 1) and hp >= 4:
        target = min(target, 14.0)

    if desperate_count >= 2 and supply_ratio < alive_count:
        target = max(target, 48.0)

    if day >= 8:
        if hp >= 5:
            target = min(target, 22.0)
        else:
            target = max(target, 46.0)

    target = max(0.0, min(float(budget), float(target)))
    return float(target)
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('budget', 0) > 0:
                    dangerous_prev.append((bid, opp.get('budget', 0), opp.get('hp', 0), opp.get('no_water_days', 0)))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    highest_prev = max(prev_bids) if prev_bids else 0.0
    active_highest = 0.0
    for item in dangerous_prev:
        bid, obudget, ohp, onw = item
        pressure = bid
        if onw >= 1 or ohp <= 3:
            pressure += 4.0
        if obudget < 40:
            pressure -= 3.0
        if pressure > active_highest:
            active_highest = pressure

    survival_mode = hp <= 2 or no_water >= 2
    urgent_mode = hp <= 4 or no_water >= 1

    if survival_mode:
        bid = max(78.0, active_highest + 3.0, highest_prev + 2.0)
        return float(min(budget, bid))

    if tight_supply:
        if urgent_mode:
            bid = max(72.0, active_highest + 2.0, 76.0)
        else:
            bid = max(60.0, min(82.0, active_highest + 1.5))
        return float(min(budget, bid))

    if medium_supply:
        if urgent_mode:
            bid = max(58.0, min(78.0, active_highest + 1.0))
        else:
            if active_highest >= 90:
                bid = 34.0
            elif active_highest >= 75:
                bid = 49.0
            else:
                bid = max(42.0, active_highest * 0.72)
        return float(min(budget, bid))

    if urgent_mode:
        bid = max(50.0, min(72.0, active_highest + 0.5))
    else:
        if highest_prev >= 95:
            bid = 22.0
        elif highest_prev >= 80:
            bid = 31.0
        else:
            bid = 26.0 + min(10.0, day * 0.6)

    if budget < 50:
        bid = min(bid, max(12.0, budget * 0.75))

    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
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
        base = DAILY_SALARY * 0.25
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.6
        return float(max(0.0, min(budget, base)))

    highest_prev = 0.0
    cindy_alive = False
    cindy_prev = None
    urgent_opp = 0
    rich_opp = 0

    for oid, opp in alive:
        if oid == 'Cindy':
            cindy_alive = True
        if opp.get('budget', 0) >= 200:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None and bid > highest_prev:
                highest_prev = bid
            if oid == 'Cindy':
                cindy_prev = bid

    secure = False
    if hp <= 2 or no_water_days >= 2:
        secure = True
    elif hp <= 4 and no_water_days >= 1:
        secure = True

    contested = False
    if supply <= 16:
        contested = True
    if len(alive) >= 3 and supply <= 18:
        contested = True
    if urgent_opp >= 2:
        contested = True
    if rich_opp >= 2 and supply <= 19:
        contested = True

    if secure:
        if cindy_alive and (cindy_prev is None or cindy_prev >= 140):
            bid = 148.0
        else:
            bid = max(95.0, highest_prev + 6.0)
        return float(max(0.0, min(budget, bid)))

    if hp >= 8 and no_water_days == 0:
        if cindy_alive and (cindy_prev is None or cindy_prev >= 140):
            if contested:
                bid = 18.0
            else:
                bid = 8.0
        else:
            if highest_prev >= 100:
                bid = 12.0
            elif contested:
                bid = min(45.0, highest_prev + 2.0)
            else:
                bid = 10.0
        return float(max(0.0, min(budget, bid)))

    if hp >= 5 and no_water_days == 0:
        if cindy_alive and (cindy_prev is None or cindy_prev >= 140):
            bid = 22.0 if contested else 12.0
        else:
            if highest_prev >= 120:
                bid = 18.0
            elif highest_prev >= 70:
                bid = 28.0
            else:
                bid = 24.0 if contested else 16.0
        return float(max(0.0, min(budget, bid)))

    if no_water_days >= 1 or hp <= 4:
        if cindy_alive and (cindy_prev is None or cindy_prev >= 140):
            if hp <= 3 or no_water_days >= 1:
                bid = 148.0
            else:
                bid = 90.0
        else:
            bid = max(70.0, highest_prev + 4.0)
        return float(max(0.0, min(budget, bid)))

    bid = 20.0
    return float(max(0.0, min(budget, bid)))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    danger_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                danger_opp += 1
            if opp.get('budget', 0) >= 700:
                rich_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    slots = max(1, int(supply // WATER_REQ))
    total_players = 1 + len(alive_opponents)
    scarcity = total_players - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 3
    elif hp <= 6:
        urgency += 2
    else:
        urgency += 1

    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2

    if slots <= 1:
        urgency += 3
    elif slots == 2:
        urgency += 2
    else:
        urgency += 1

    if scarcity >= 3:
        urgency += 2
    elif scarcity >= 1:
        urgency += 1

    if danger_opp >= 2:
        urgency += 1

    if budget < DAILY_SALARY * 2:
        urgency += 1

    if urgency <= 3:
        base = DAILY_SALARY * 0.28
    elif urgency <= 5:
        base = DAILY_SALARY * 0.48
    elif urgency <= 7:
        base = DAILY_SALARY * 0.72
    elif urgency <= 9:
        base = DAILY_SALARY * 0.96
    else:
        base = DAILY_SALARY * 1.22

    if highest_prev > 0:
        if urgency <= 4 and highest_prev >= DAILY_SALARY * 1.4:
            bid = DAILY_SALARY * 0.32
        elif urgency >= 8:
            bid = max(base, min(highest_prev + 2.0, DAILY_SALARY * 1.55))
        else:
            target = avg_prev * 0.92 + 3.0
            bid = max(base, min(target, highest_prev + 1.0))
    else:
        bid = base

    if rich_opp >= 2 and slots <= 1 and urgency <= 6:
        bid = min(bid, DAILY_SALARY * 0.55)

    remaining_days = max(0, 10 - int(day))
    reserve = 0.0
    if remaining_days > 0:
        reserve = remaining_days * DAILY_SALARY * 0.22
    affordable = max(0.0, budget - reserve)

    if urgency >= 8:
        final_bid = min(budget, max(bid, DAILY_SALARY * 0.9))
    else:
        final_bid = min(bid, max(DAILY_SALARY * 0.18, affordable))
        final_bid = min(final_bid, budget)

    if hp <= 2 or no_water_days >= 2:
        final_bid = min(budget, max(final_bid, highest_prev + 2.5 if highest_prev > 0 else DAILY_SALARY * 0.95))

    if final_bid < 0:
        final_bid = 0.0

    return float(round(final_bid, 2))
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

    alive = []
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 500:
                rich_opponents += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    my_urgent = hp <= 3 or no_water_days >= 1
    very_urgent = hp <= 2 or no_water_days >= 2

    if very_urgent:
        bid = max(92.0, highest_prev + 3.0)
    elif my_urgent:
        bid = max(72.0, avg_prev + 2.0)
    else:
        if slots >= 2:
            bid = 26.0
            if highest_prev < 60:
                bid = max(24.0, highest_prev + 1.0)
            elif highest_prev < 95:
                bid = 34.0
            else:
                bid = 28.0
        else:
            bid = 58.0
            if highest_prev > 0:
                bid = max(58.0, min(78.0, highest_prev * 0.72))

    if urgent_opponents >= 2 and not my_urgent:
        bid *= 0.9
    if rich_opponents >= 2 and slots == 1 and my_urgent:
        bid *= 1.1

    if day >= 8:
        if hp >= 6 and not my_urgent:
            bid *= 0.9
        else:
            bid *= 1.05

    min_safe = 0.0
    if very_urgent:
        min_safe = 85.0
    elif my_urgent:
        min_safe = 65.0

    bid = max(min_safe, bid)
    bid = min(budget, bid)
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply / float(WATER_REQ)

    if hp <= 2 or no_water >= 2:
        base = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif hp <= 4 or no_water >= 1:
        if scarcity <= 1.25:
            base = max(DAILY_SALARY * 0.82, highest_prev + 2.0)
        else:
            base = max(DAILY_SALARY * 0.62, avg_prev * 0.72)
    else:
        if scarcity >= 1.8:
            base = max(DAILY_SALARY * 0.22, avg_prev * 0.35)
        elif scarcity >= 1.45:
            base = max(DAILY_SALARY * 0.34, avg_prev * 0.5)
        else:
            base = max(DAILY_SALARY * 0.52, highest_prev + 1.5)

    if urgent_opp >= 2 and hp >= 5 and no_water == 0:
        base *= 0.88
    if rich_opp >= 2 and scarcity <= 1.25:
        base *= 1.08
    if day >= 8 and hp >= 5 and no_water == 0:
        base *= 0.9

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left >= 3 and hp >= 4:
        reserve_floor = DAILY_SALARY * 0.35

    bid = min(budget - reserve_floor, base)
    if bid < 0:
        bid = min(budget, DAILY_SALARY * 0.2)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

    if bid > budget:
        bid = budget
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 200:
                rich_opponents += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if not alive:
        return float(min(budget, 8.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    contested = units < 2.0
    very_tight = units < 1.5

    desperation = 0
    if hp <= 2:
        desperation += 3
    elif hp <= 4:
        desperation += 2
    elif hp <= 6:
        desperation += 1

    if no_water >= 2:
        desperation += 3
    elif no_water >= 1:
        desperation += 2

    if very_tight:
        desperation += 2
    elif contested:
        desperation += 1

    if urgent_opponents >= 2:
        desperation += 1

    if desperation >= 6:
        target = max(0.95 * DAILY_SALARY, highest_prev + 6.0)
    elif desperation >= 4:
        target = max(0.78 * DAILY_SALARY, avg_prev + 4.0, highest_prev * 0.72)
    elif desperation >= 2:
        if contested:
            target = max(0.52 * DAILY_SALARY, avg_prev + 2.0)
        else:
            target = max(0.34 * DAILY_SALARY, avg_prev * 0.7)
    else:
        if contested:
            target = max(0.28 * DAILY_SALARY, min(highest_prev * 0.55, 0.48 * DAILY_SALARY))
        else:
            target = max(0.12 * DAILY_SALARY, min(avg_prev * 0.4, 0.26 * DAILY_SALARY))

    if highest_prev >= 130 and desperation <= 2:
        target = min(target, 0.32 * DAILY_SALARY)

    if rich_opponents >= 2 and contested and desperation >= 3:
        target += 6.0

    if budget < DAILY_SALARY:
        target = min(target, max(8.0, budget * 0.55))
    elif budget < 2 * DAILY_SALARY:
        target = min(target, budget * 0.7)

    target = min(target, budget)
    if hp <= 2 or no_water >= 2:
        target = max(target, min(budget, 0.9 * DAILY_SALARY))

    if target < 0:
        target = 0.0

    return float(round(target, 2))
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

    alive = []
    prev_bids = []
    stressed_count = 0
    rich_aggressive = 0
    cheap_yesterday = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                stressed_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid <= 35:
                    cheap_yesterday += 1
                if bid >= 80 and opp.get('budget', 0) >= 120:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if len(alive) == 0:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply <= 17
    abundance = supply >= 22
    urgent = (hp <= 3) or (no_water_days >= 2)
    semi_urgent = (hp <= 5) or (no_water_days >= 1)

    if urgent:
        base = 96.0 if scarcity else 82.0
        if highest_prev > 0:
            base = max(base, highest_prev + 4.0)
        if rich_aggressive >= 2:
            base += 10.0
        return float(min(budget, base))

    if abundance and hp >= 6 and no_water_days == 0:
        base = 16.0
        if cheap_yesterday >= 2:
            base = 12.0
        return float(min(budget, base))

    if scarcity:
        base = 58.0
        if highest_prev >= 85:
            base = 44.0 if hp >= 7 else 88.0
        elif highest_prev >= 60:
            base = max(base, highest_prev + 2.0)
        else:
            base = max(base, avg_prev + 6.0)
        if stressed_count >= 2:
            base += 8.0
        if rich_aggressive >= 2:
            base += 6.0
        return float(min(budget, base))

    if semi_urgent:
        base = 63.0
        if highest_prev >= 90:
            base = 52.0 if hp >= 6 else 92.0
        elif highest_prev >= 55:
            base = max(base, highest_prev + 1.5)
        if stressed_count >= 2:
            base += 5.0
        return float(min(budget, base))

    base = 34.0
    if highest_prev >= 95:
        base = 24.0
    elif highest_prev >= 75:
        base = 29.0
    elif highest_prev >= 45:
        base = highest_prev + 1.0
    elif avg_prev > 0:
        base = max(base, avg_prev * 0.75)

    if abundance:
        base -= 6.0
    if day >= 8 and hp >= 6:
        base -= 4.0

    if base < 8.0:
        base = 8.0

    return float(min(budget, base))
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

    alive_opponents = []
    prev_bids = []
    dangerous_pressure = 0.0
    rich_alive = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_alive += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid > dangerous_pressure:
                    dangerous_pressure = bid

    if budget <= 0:
        return 0.0

    slots = max(1, int(supply // WATER_REQ))
    competitors = 1 + len(alive_opponents)
    scarcity = competitors - slots

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, 35.0))
        return float(min(budget, 8.0))

    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        top_prev = 0.0
        avg_prev = 0.0

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

    if scarcity >= 2:
        urgency += 2
    elif scarcity >= 1:
        urgency += 1

    if top_prev >= 100:
        urgency += 2
    elif top_prev >= 70:
        urgency += 1

    if rich_alive >= 2:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency <= 1:
        bid = 12.0 if slots >= 2 else 18.0
    elif urgency == 2:
        bid = max(22.0, avg_prev * 0.45)
    elif urgency == 3:
        bid = max(32.0, min(48.0, top_prev * 0.55 + 4.0))
    elif urgency == 4:
        bid = max(45.0, min(68.0, top_prev * 0.72 + 3.0))
    elif urgency == 5:
        bid = max(60.0, min(88.0, top_prev * 0.82 + 4.0))
    else:
        bid = max(75.0, min(110.0, top_prev * 0.9 + 6.0))

    if hp <= 2 or no_water >= 2:
        bid = max(bid, 78.0)

    if supply >= 24 and hp >= 6 and no_water == 0:
        bid *= 0.75
    elif supply >= 21 and hp >= 5 and no_water == 0:
        bid *= 0.88

    if dangerous_pressure >= 140 and hp >= 5 and no_water == 0:
        bid *= 0.8

    reserve = 0.0
    if day <= 7:
        reserve = 35.0
    elif day <= 9:
        reserve = 15.0

    affordable = max(0.0, budget - reserve)
    if hp <= 3 or no_water >= 1:
        affordable = budget

    final_bid = min(budget, bid)
    if affordable > 0:
        final_bid = min(final_bid, affordable)
    if final_bid < 0:
        final_bid = 0.0

    if (hp <= 2 or no_water >= 1) and budget > 0:
        final_bid = max(final_bid, min(budget, 35.0))

    return float(round(final_bid, 2))
"""
