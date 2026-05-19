# ============================================================
# Experiment: exp_074
# Agent: Alex
# Source: exp_074
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    player_count = 1 + len(alive)
    approx_winners = max(1, int(supply // WATER_REQ))
    scarcity = player_count - approx_winners

    prev_bids = []
    desperate_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp += 1

    my_desperate = (hp <= 2) or (no_water >= 2)

    if not alive:
        return min(budget, 20)

    base = 24
    if scarcity >= 2:
        base = 40
    elif scarcity == 1:
        base = 32

    if my_desperate:
        base = max(base, 58)
    elif hp <= 4 or no_water >= 1:
        base = max(base, 46)

    if desperate_opp >= 2 and not my_desperate:
        base = min(base, 28)
    elif desperate_opp >= 1 and not my_desperate and scarcity <= 1:
        base = min(base, 30)

    if prev_bids:
        highest_prev = max(prev_bids)
        if my_desperate:
            bid = max(base, highest_prev + 2)
        elif scarcity >= 2:
            bid = max(base, highest_prev + 1)
        else:
            if highest_prev >= 60:
                bid = min(base, 26)
            else:
                bid = max(base, highest_prev + 1)
                bid = min(bid, 49)
    else:
        bid = base

    if budget < bid:
        bid = budget

    if hp >= 7 and scarcity <= 0 and not my_desperate:
        bid = min(bid, 22)

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
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 140:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    need = 0.0
    if hp <= 2:
        need = 1.0
    elif hp <= 4:
        need = 0.75
    elif no_water_days >= 1:
        need = 0.7
    elif hp <= 6:
        need = 0.45
    else:
        need = 0.2

    pressure = 0.0
    if highest_prev >= 160:
        pressure = 1.0
    elif highest_prev >= 120:
        pressure = 0.8
    elif highest_prev >= 80:
        pressure = 0.55
    elif highest_prev > 0:
        pressure = 0.3

    if hp >= 7 and no_water_days == 0 and scarcity < 0.45 and pressure >= 0.8:
        return float(max(0.0, min(budget, DAILY_SALARY * 0.18)))

    if hp <= 2 or no_water_days >= 2:
        emergency = max(DAILY_SALARY * 1.15, highest_prev + 6.0, avg_prev + 10.0)
        if rich_count >= 2:
            emergency = max(emergency, DAILY_SALARY * 1.45)
        return float(max(0.0, min(budget, emergency)))

    base = DAILY_SALARY * (0.28 + 0.55 * need + 0.35 * scarcity)

    if pressure >= 0.8:
        if need >= 0.7 or scarcity >= 0.6:
            base = max(base, min(highest_prev + 3.0, DAILY_SALARY * 1.5))
        else:
            base = min(base, DAILY_SALARY * 0.32)
    elif pressure >= 0.55:
        base = max(base, min(highest_prev + 2.0, DAILY_SALARY * 1.15))
    elif highest_prev > 0:
        base = max(base, highest_prev + 1.0)

    if desperate_count >= 2 and (hp <= 5 or scarcity >= 0.5):
        base = max(base, DAILY_SALARY * 0.95)

    if day >= 8 and hp <= 5:
        base = max(base, DAILY_SALARY * 0.95)

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left > 0 and hp >= 6:
        reserve_floor = min(budget * 0.45, days_left * DAILY_SALARY * 0.18)

    affordable = max(0.0, budget - reserve_floor)
    if need >= 0.7:
        affordable = budget

    bid = min(base, affordable)
    if bid <= 0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.12)

    return float(max(0.0, min(budget, bid)))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 42.0))

    prev_bids = []
    pressure_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = prev.get('bid', 0)
            prev_bids.append(b)
            if prev.get('status') == 'won' or opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                pressure_bids.append(b)

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0
    pressure_prev = max(pressure_bids) if pressure_bids else max_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 2

    if danger >= 5:
        base = max(pressure_prev + 2.0, avg_prev + 8.0, 0.92 * DAILY_SALARY)
    elif danger >= 3:
        base = max(avg_prev * 0.72, pressure_prev * 0.62, 0.68 * DAILY_SALARY)
    elif scarcity >= 0.7:
        base = max(avg_prev * 0.52, 0.48 * DAILY_SALARY)
    elif scarcity <= 0.25 and hp >= 5 and no_water == 0:
        base = min(avg_prev * 0.28 if avg_prev > 0 else 16.0, 0.30 * DAILY_SALARY)
    else:
        base = max(avg_prev * 0.40, 0.38 * DAILY_SALARY)

    if max_prev >= 180 and danger <= 2:
        base = min(base, 0.34 * DAILY_SALARY)
    if urgent_opp >= 2 and danger >= 3:
        base = max(base, pressure_prev + 1.5)
    if rich_opp >= 2 and danger <= 1:
        base *= 0.92
    if day >= 8 and hp >= 5 and no_water == 0:
        base *= 0.9

    reserve = 0.0
    if hp <= 4 or no_water >= 1:
        reserve = 0.0
    else:
        reserve = DAILY_SALARY * 1.2

    bid = min(base, budget - reserve)
    if bid < 0:
        bid = 0.0

    min_live_bid = 0.0
    if hp <= 2 or no_water >= 2:
        min_live_bid = 0.9 * DAILY_SALARY
    elif hp <= 4 or no_water >= 1:
        min_live_bid = 0.62 * DAILY_SALARY
    elif scarcity >= 0.7:
        min_live_bid = 0.42 * DAILY_SALARY
    else:
        min_live_bid = 12.0

    if budget <= min_live_bid:
        return float(max(0.0, budget))

    bid = max(bid, min_live_bid)
    bid = min(bid, budget)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        base = 18.0 if hp > 3 else 40.0
        return max(0.0, min(budget, base))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        if float(opp.get('budget', 0)) >= budget:
            rich_opp += 1
        if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0)) <= 3:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = DAILY_SALARY * 0.7
        avg_prev = DAILY_SALARY * 0.55

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.55
    if hp <= 2:
        urgency += 0.8
    elif hp <= 4:
        urgency += 0.35

    pressure = 0.45 * scarcity
    pressure += 0.2 if urgent_opp >= 2 else (0.1 if urgent_opp == 1 else 0.0)
    pressure += 0.15 if highest_prev >= 120 else (0.08 if highest_prev >= 80 else 0.0)
    pressure += 0.08 if rich_opp >= 2 else 0.0

    safe_conserve = DAILY_SALARY * (0.28 + 0.18 * scarcity)
    contest = max(avg_prev + 2.0, highest_prev * 0.78)
    emergency = max(highest_prev + 3.0, DAILY_SALARY * 1.05)

    if urgency >= 1.2:
        bid = emergency
    elif urgency >= 0.55:
        bid = max(contest, DAILY_SALARY * (0.72 + 0.18 * scarcity))
    else:
        if pressure >= 0.62:
            bid = max(contest, DAILY_SALARY * (0.58 + 0.16 * scarcity))
        else:
            bid = safe_conserve

    days_left = max(0, 10 - day)
    reserve_floor = 0.0
    if days_left > 0:
        reserve_floor = min(budget * 0.45, days_left * DAILY_SALARY * 0.22)

    max_affordable_today = max(0.0, budget - reserve_floor)
    if urgency >= 1.2:
        max_affordable_today = budget
    elif urgency >= 0.55:
        max_affordable_today = max(max_affordable_today, budget * 0.55)

    bid = min(bid, max_affordable_today)

    if budget < DAILY_SALARY * 0.8 and urgency < 0.55:
        bid = min(bid, budget * 0.45)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_pressure = 0
    desperate_opp = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 120:
                    rich_pressure += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1

    if budget <= 0:
        return 0.0

    player_count = 1 + len(alive)
    enough_for_all = supply >= WATER_REQ * player_count
    very_tight = supply < WATER_REQ * max(1, player_count - 1)

    highest_prev = max(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water >= 2:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        bid = max(0.78 * DAILY_SALARY, min(highest_prev + 1.0, 0.98 * DAILY_SALARY))
    elif very_tight:
        bid = max(0.82 * DAILY_SALARY, min(highest_prev + 1.5, DAILY_SALARY * 1.02))
    elif enough_for_all:
        bid = 0.22 * DAILY_SALARY
    else:
        if rich_pressure >= 2:
            bid = 0.34 * DAILY_SALARY
        elif desperate_opp >= 2:
            bid = 0.62 * DAILY_SALARY
        else:
            bid = max(0.45 * DAILY_SALARY, min(highest_prev * 0.55, 0.68 * DAILY_SALARY))

    day_num = day_context['day']
    if day_num >= 8 and hp >= 6 and budget < DAILY_SALARY * 2:
        bid *= 0.85

    if budget < bid:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0 if hp > 3 else 45.0))

    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 120:
            rich_opp_count += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 140.0
        avg_prev = 135.0

    units_available = int(supply // WATER_REQ)
    tight_supply = units_available <= 1
    abundant_supply = units_available >= 2

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1

    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 2

    if tight_supply:
        danger += 2
    elif abundant_supply:
        danger -= 1

    danger += min(2, urgent_opp_count)

    if budget < 70:
        cap = budget
    elif budget < 140:
        cap = min(budget, highest_prev + 3.0)
    else:
        cap = min(budget, highest_prev + 8.0)

    if danger <= 0:
        bid = 18.0 if abundant_supply else 28.0
    elif danger == 1:
        bid = max(32.0, avg_prev * 0.28)
    elif danger == 2:
        bid = max(48.0, avg_prev * 0.42)
    elif danger == 3:
        bid = max(72.0, avg_prev * 0.58)
    elif danger == 4:
        bid = max(96.0, highest_prev * 0.72)
    else:
        bid = max(118.0, highest_prev + 2.0)

    if tight_supply and rich_opp_count >= 2:
        bid = max(bid, highest_prev * 0.88)
    if abundant_supply and hp > 4 and no_water == 0:
        bid = min(bid, avg_prev * 0.45)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, highest_prev + 1.5)

    bid = min(bid, cap)
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    aggressive_bids = []
    desperate_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    if bid >= 90:
                        aggressive_bids.append(bid)

    if not alive_opponents:
        return min(budget, 18.0)

    low_supply = supply <= 17
    very_low_supply = supply <= 16
    high_supply = supply >= 22

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        moderate_prev = sorted_bids[int(len(sorted_bids) // 2)]

    req_pressure = len(alive_opponents) + 1
    if supply < WATER_REQ:
        scarcity = 1.0
    else:
        scarcity = req_pressure / max(1.0, supply / float(WATER_REQ))

    if hp <= 2 or no_water_days >= 2:
        emergency_bid = max(92.0, highest_prev + 4.0)
        if very_low_supply:
            emergency_bid += 10.0
        return min(budget, emergency_bid)

    if hp <= 4 or no_water_days >= 1:
        bid = max(58.0, moderate_prev + 3.0)
        if low_supply:
            bid = max(bid, highest_prev + 2.0)
        if len(aggressive_bids) >= 2 and hp > 3:
            bid = max(52.0, bid * 0.9)
        return min(budget, bid)

    if high_supply and len(aggressive_bids) >= 2:
        return min(budget, 16.0)

    if very_low_supply:
        bid = max(46.0, moderate_prev + 2.0)
        if desperate_count >= 2:
            bid += 6.0
        return min(budget, bid)

    if low_supply:
        bid = max(34.0, moderate_prev + 1.5)
        if highest_prev >= 110:
            bid = 28.0
        return min(budget, bid)

    if scarcity > 2.5:
        return min(budget, 30.0)

    if day >= 8 and hp >= 6:
        return min(budget, 22.0)

    return min(budget, 18.0)
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    slots = int(supply / WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    max_prev = 0.0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(bid)
            if bid > max_prev:
                max_prev = bid

    need_urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        target = min(budget, max(62.0, max_prev + 2.0))
        return float(target)

    if slots >= 2:
        base = 18.0
        if max_prev > 0:
            base = min(42.0, max(18.0, max_prev * 0.42))
        if urgent_opp >= 1:
            base += 4.0
        if need_urgent:
            base += 18.0
        return float(min(budget, base))

    base = 34.0
    if max_prev > 0:
        base = max(base, min(68.0, max_prev + 1.5))
    if rich_opp >= 1:
        base += 4.0
    if urgent_opp >= 2:
        base += 6.0
    if need_urgent:
        base += 14.0

    if hp >= 7 and no_water == 0 and max_prev >= 90:
        base = 16.0

    return float(min(budget, base))
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, safe_bid)))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 700:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = hp <= 2 or no_water_days >= 1
    very_urgent = hp <= 1 or no_water_days >= 2

    base = DAILY_SALARY * (0.34 + 0.28 * scarcity)

    if supply >= 23:
        base *= 0.82
    elif supply <= 17:
        base *= 1.22

    if highest_prev >= 150:
        pressure_bid = highest_prev + 2.0
    elif highest_prev >= 110:
        pressure_bid = highest_prev + 1.5
    elif highest_prev > 0:
        pressure_bid = max(base, avg_prev + 4.0)
    else:
        pressure_bid = base

    if desperate_count >= 2:
        pressure_bid += 8.0
    elif desperate_count == 1:
        pressure_bid += 4.0

    if rich_count >= 2 and supply <= 18:
        pressure_bid += 10.0

    if urgent:
        bid = max(pressure_bid, DAILY_SALARY * 0.92)
    elif very_urgent:
        bid = max(pressure_bid, DAILY_SALARY * 1.1)
    else:
        if highest_prev >= 150 and hp >= 4 and supply >= 20:
            bid = DAILY_SALARY * 0.42
        else:
            bid = pressure_bid

    remaining_days = max(0, 10 - day)
    reserve_target = remaining_days * DAILY_SALARY * 0.45
    if not urgent and budget < reserve_target:
        bid = min(bid, DAILY_SALARY * 0.75)

    if very_urgent:
        bid = max(bid, DAILY_SALARY * 1.2)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    dangerous_prev.append(bid)

    if not alive:
        return max(0.0, min(budget, 18.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    danger_prev = max(dangerous_prev) if dangerous_prev else 0.0

    live_count = len(alive) + 1
    tightness = float(WATER_REQ * live_count) / max(float(supply), 1.0)

    emergency = hp <= 3 or no_water >= 2
    stressed = hp <= 5 or no_water >= 1
    very_tight = supply <= 17
    tight = supply <= 19

    if emergency:
        target = max(78.0, high_prev + 6.0, danger_prev + 8.0)
    elif very_tight:
        target = max(42.0, min(88.0, high_prev + 3.0))
        if stressed:
            target = max(target, 62.0, danger_prev + 5.0)
    elif tight:
        target = max(28.0, min(70.0, high_prev * 0.72 + 4.0))
        if stressed:
            target = max(target, 46.0)
    else:
        target = 14.0
        if stressed:
            target = 26.0
        if high_prev <= 35.0 and tightness > 2.0:
            target = max(target, high_prev + 1.5)

    if budget < 120:
        target *= 0.82
    if budget < 70:
        target *= 0.72

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
"""
