# ============================================================
# Experiment: exp_089
# Agent: Alex
# Source: exp_089
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
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        base = DAILY_SALARY * 0.22
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.45
        return min(budget, max(0, base))

    prev_bids = []
    desperate_count = 0
    error_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
            if prev.get('error'):
                error_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    total_players = len(alive_opponents) + 1
    expected_need = total_players * WATER_REQ
    supply_ratio = float(supply) / float(expected_need) if expected_need > 0 else 1.0

    if supply_ratio >= 1.0:
        base = DAILY_SALARY * 0.28
    elif supply_ratio >= 0.8:
        base = DAILY_SALARY * 0.42
    elif supply_ratio >= 0.65:
        base = DAILY_SALARY * 0.58
    else:
        base = DAILY_SALARY * 0.74

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if highest_prev >= DAILY_SALARY * 0.9:
            base = max(base, DAILY_SALARY * 0.62)
        elif avg_prev < DAILY_SALARY * 0.4:
            base = min(base, DAILY_SALARY * 0.48)
        else:
            base = max(base, min(DAILY_SALARY * 0.78, highest_prev + 1.0))

    if desperate_count >= max(1, len(alive_opponents) // 2):
        base += 5
    if error_count > 0:
        base -= 3

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.92)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.72)

    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.97)
    elif no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.82)

    if budget < DAILY_SALARY * 1.2:
        base = min(base, budget)
    elif budget > DAILY_SALARY * 5 and hp > 4 and no_water_days == 0 and supply_ratio >= 0.8:
        base = min(base, DAILY_SALARY * 0.55)

    bid = max(0, min(budget, base))
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 8:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1

    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1

    if supply_tight:
        danger += 1
    if urgent_opp >= 2:
        danger += 1

    if danger >= 5:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif danger >= 3:
        target = max(DAILY_SALARY * 0.72, avg_prev + 2.0, highest_prev * 0.82)
    else:
        if highest_prev >= DAILY_SALARY * 1.2:
            target = DAILY_SALARY * 0.28
        elif highest_prev >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * 0.42
        else:
            target = max(DAILY_SALARY * 0.34, avg_prev + 1.0)

    if supply_loose:
        target *= 0.82
    elif supply_tight:
        target *= 1.12

    if rich_opp >= 1 and highest_prev >= DAILY_SALARY * 0.8:
        target *= 1.05

    remaining_days = max(1, 10 - day + 1)
    soft_cap = budget / remaining_days + DAILY_SALARY * 0.35
    if danger <= 2:
        target = min(target, soft_cap)

    if hp >= 8 and no_water_days == 0 and highest_prev > DAILY_SALARY:
        target = min(target, DAILY_SALARY * 0.3)

    bid = max(0.0, min(budget, target))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        base = 18.0 if hp > 3 else 45.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    aggressive_count = 0
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            try:
                b = float(bid)
                prev_bids.append(b)
                if b >= 85.0:
                    aggressive_count += 1
                if b >= 110.0:
                    desperate_count += 1
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0

    competitors = 1 + len(alive_opponents)
    expected_units = supply / float(WATER_REQ)
    tight_supply = expected_units < competitors * 0.55
    medium_supply = expected_units < competitors * 0.8

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1

    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1

    if tight_supply:
        danger += 2
    elif medium_supply:
        danger += 1

    if day >= 8:
        danger += 1

    if danger >= 6:
        bid = max(95.0, highest_prev + 2.0)
    elif danger >= 4:
        bid = max(72.0, min(96.0, highest_prev * 0.92 + 3.0))
    elif danger >= 2:
        if aggressive_count >= 2:
            bid = 26.0 if hp > 4 else 68.0
        else:
            bid = max(38.0, lowest_prev + 2.0 if prev_bids else 42.0)
    else:
        if aggressive_count >= 2:
            bid = 12.0
        elif highest_prev <= 40.0 and prev_bids:
            bid = highest_prev + 2.0
        else:
            bid = 20.0

    reserve_days = 3 if day <= 7 else 1
    reserve_budget = reserve_days * DAILY_SALARY
    max_affordable = budget
    if budget > reserve_budget:
        max_affordable = budget - reserve_budget + DAILY_SALARY * 0.35

    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

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
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except:
                    pass

    if not alive_opponents:
        base = DAILY_SALARY * 0.22
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, base)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    competitors = len(alive_opponents)
    expected_units = supply / float(WATER_REQ)
    pressure = competitors - expected_units

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 2.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(DAILY_SALARY * 0.72, min(highest_prev + 1.0, DAILY_SALARY * 1.02))
    else:
        if pressure <= 0.25 and supply >= 21:
            bid = DAILY_SALARY * 0.26
        elif pressure <= 1.0:
            bid = DAILY_SALARY * (0.34 + 0.10 * scarcity)
        else:
            bid = DAILY_SALARY * (0.46 + 0.18 * scarcity)

        if highest_prev >= DAILY_SALARY * 1.6:
            bid = min(bid, DAILY_SALARY * 0.48)
        elif highest_prev >= DAILY_SALARY * 1.2:
            bid = max(bid, DAILY_SALARY * 0.52)
        elif highest_prev > 0:
            bid = max(bid, min(highest_prev + 1.5, DAILY_SALARY * 0.88))

    if urgent_opp >= 2:
        bid += 6.0
    elif urgent_opp == 1:
        bid += 3.0

    if rich_opp >= 2 and hp > 4:
        bid -= 3.0

    if day >= 8:
        bid += 4.0
    if day >= 9 and (hp <= 5 or no_water_days >= 1):
        bid += 8.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if hp > 4 and no_water_days == 0 and days_left >= 2:
        reserve_floor = DAILY_SALARY * 0.35

    affordable = max(0.0, budget - reserve_floor)
    if affordable <= 0:
        affordable = budget

    bid = min(bid, affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, safe_bid)))

    prev_bids = []
    prev_aggressive = []
    prev_winners = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            status = prev.get('status')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= DAILY_SALARY * 0.9:
                    prev_aggressive.append(float(bid))
            if status == 'won':
                prev_winners += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        emergency = max(DAILY_SALARY * 1.0, highest_prev + 6.0)
        if tight_supply:
            emergency = max(emergency, DAILY_SALARY * 1.15)
        return float(max(0.0, min(budget, emergency)))

    if hp <= 4 or no_water_days >= 1:
        urgent = max(DAILY_SALARY * 0.82, highest_prev + 3.0)
        if tight_supply:
            urgent = max(urgent, DAILY_SALARY * 0.95)
        elif ample_supply:
            urgent = max(DAILY_SALARY * 0.72, avg_prev + 1.5)
        return float(max(0.0, min(budget, urgent)))

    if tight_supply:
        bid = max(DAILY_SALARY * 0.78, highest_prev + 2.0)
        if len(prev_aggressive) >= 2:
            bid = max(DAILY_SALARY * 0.9, highest_prev + 1.0)
    elif ample_supply:
        bid = max(DAILY_SALARY * 0.42, avg_prev * 0.72)
        if prev_winners >= 2:
            bid = max(bid, DAILY_SALARY * 0.48)
    else:
        bid = max(DAILY_SALARY * 0.58, avg_prev * 0.9)
        if highest_prev > 0:
            bid = max(bid, highest_prev * 0.88)

    days_left_est = max(1, 10 - int(day) + 1)
    reserve_target = DAILY_SALARY * 0.35 * days_left_est
    if budget < reserve_target:
        bid = min(bid, DAILY_SALARY * 0.6)

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.55)

    return float(max(0.0, min(budget, bid)))
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
    dangerous_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('budget', 0) > DAILY_SALARY * 2 and opp.get('hp', 0) > 3:
                dangerous_count += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    if hp <= 2 or no_water_days >= 2:
        emergency = max(0.92 * DAILY_SALARY, highest_prev + 6.0)
        if tight_supply:
            emergency = max(emergency, 0.98 * DAILY_SALARY)
        return float(min(budget, emergency))

    if hp <= 4 or no_water_days >= 1:
        protect = max(0.72 * DAILY_SALARY, highest_prev + 3.0)
        if tight_supply:
            protect = max(protect, 0.84 * DAILY_SALARY)
        return float(min(budget, protect))

    if highest_prev >= 120:
        if tight_supply:
            bid = 0.58 * DAILY_SALARY
        else:
            bid = 0.28 * DAILY_SALARY
        return float(min(budget, bid))

    if highest_prev >= 80:
        if tight_supply:
            bid = max(0.62 * DAILY_SALARY, avg_prev * 0.72)
        else:
            bid = 0.35 * DAILY_SALARY
        return float(min(budget, bid))

    if tight_supply:
        bid = max(0.68 * DAILY_SALARY, highest_prev + 2.0)
    elif medium_supply:
        bid = max(0.52 * DAILY_SALARY, highest_prev + 1.5)
    else:
        bid = max(0.34 * DAILY_SALARY, highest_prev * 0.7)

    if dangerous_count >= 2 and supply <= 18:
        bid = max(bid, 0.7 * DAILY_SALARY)

    if day >= 8 and hp >= 6 and budget > DAILY_SALARY * 3:
        bid = max(bid, 0.6 * DAILY_SALARY)

    return float(min(budget, bid))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    rich_pressure = 0.0
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 300 and opp.get('hp', 0) >= 4:
                rich_pressure = max(rich_pressure, float(bid))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 2:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    live_count = len(alive_opponents)

    scarcity = 0.0
    if supply <= 16:
        scarcity = 1.0
    elif supply <= 18:
        scarcity = 0.7
    elif supply <= 21:
        scarcity = 0.35
    else:
        scarcity = 0.1

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.45
    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.55

    pressure_bid = highest_prev
    if rich_pressure > pressure_bid:
        pressure_bid = rich_pressure

    if urgency >= 1.4:
        target = max(DAILY_SALARY * 0.95, pressure_bid + 3.0)
    elif scarcity >= 0.9:
        target = max(DAILY_SALARY * 0.82, pressure_bid * 0.92 + 2.0)
    elif scarcity >= 0.6:
        target = max(DAILY_SALARY * 0.62, pressure_bid * 0.72 + 1.5)
    else:
        target = max(DAILY_SALARY * 0.28, pressure_bid * 0.42 + 1.0)

    if desperate_count >= max(1, live_count - 1):
        target += 4.0

    if day >= 8 and hp >= 5 and no_water == 0 and supply >= 20:
        target *= 0.82

    if budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.7)
    elif budget > DAILY_SALARY * 8 and urgency < 1.0 and scarcity < 0.6:
        target = min(target, DAILY_SALARY * 0.75)

    floor_bid = 0.0
    if urgency >= 1.0:
        floor_bid = DAILY_SALARY * 0.72
    elif scarcity >= 0.6:
        floor_bid = DAILY_SALARY * 0.4
    else:
        floor_bid = DAILY_SALARY * 0.18

    bid = max(floor_bid, target)
    bid = min(budget, bid)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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
    strong_prev = 0.0
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = None
            if prev:
                bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > strong_prev:
                    strong_prev = float(bid)
            if opp.get('budget', 0) > 500:
                if bid is not None and float(bid) >= 80:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return min(float(budget), 28.0)

    low_supply = supply <= 17
    high_supply = supply >= 22
    critical_me = hp <= 2 or no_water_days >= 1
    stable_me = hp >= 6 and no_water_days == 0

    if not prev_bids:
        if critical_me:
            return min(float(budget), 84.0)
        if high_supply:
            return min(float(budget), 42.0)
        return min(float(budget), 30.0)

    top_prev = max(prev_bids)
    avg_prev = sum(prev_bids) / float(len(prev_bids))

    if critical_me:
        target = max(0.9 * DAILY_SALARY, top_prev + 2.0)
        if high_supply:
            target += 6.0
        return min(float(budget), float(target))

    if low_supply:
        if stable_me and top_prev >= 80:
            return min(float(budget), 12.0)
        if desperate_count >= 2:
            return min(float(budget), 18.0)
        return min(float(budget), max(20.0, avg_prev * 0.45))

    if high_supply:
        if top_prev < 75:
            return min(float(budget), max(46.0, top_prev + 2.0))
        if rich_aggressive >= 2 and stable_me:
            return min(float(budget), 35.0)
        return min(float(budget), max(52.0, top_prev + 1.5))

    if top_prev >= 110:
        if stable_me:
            return min(float(budget), 22.0)
        return min(float(budget), 68.0)

    if top_prev >= 85:
        if stable_me:
            return min(float(budget), 26.0)
        return min(float(budget), 60.0)

    target = max(38.0, top_prev + 1.5)
    if day >= 8 and hp >= 5:
        target *= 0.9
    return min(float(budget), float(target))
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_threat = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > rich_threat:
                rich_threat = opp.get('budget', 0)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if not alive:
        return max(0.0, min(budget, 1.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 2 if supply <= 16 else (1 if supply <= 19 else 0)
    emergency = hp <= 3 or no_water >= 1

    cindy_like = False
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if opp.get('budget', 0) > 300 and prev.get('bid') is not None and prev.get('bid', 0) >= 100:
            cindy_like = True
            break

    if emergency:
        if scarcity == 2:
            bid = min(budget, max(95.0, max_prev + 6.0, DAILY_SALARY * 1.45))
        elif scarcity == 1:
            bid = min(budget, max(78.0, avg_prev + 5.0, DAILY_SALARY * 1.1))
        else:
            bid = min(budget, max(60.0, avg_prev + 2.0, DAILY_SALARY * 0.85))
        return max(0.0, bid)

    if scarcity == 0:
        if cindy_like and max_prev >= 120:
            bid = min(budget, 8.0)
        else:
            bid = min(budget, max(12.0, min(28.0, avg_prev * 0.3 + 6.0)))
        return max(0.0, bid)

    if scarcity == 1:
        if cindy_like:
            if max_prev >= 130:
                bid = min(budget, 18.0 if hp >= 6 else 72.0)
            else:
                bid = min(budget, 42.0 if hp >= 6 else 76.0)
        else:
            bid = min(budget, max(35.0, avg_prev + 3.0))
        return max(0.0, bid)

    if cindy_like:
        if hp >= 7 and budget < rich_threat:
            bid = min(budget, 22.0)
        else:
            bid = min(budget, max(82.0, max_prev * 0.72))
    else:
        bid = min(budget, max(55.0, avg_prev + 4.0))

    if day >= 8 and hp <= 6:
        bid = min(budget, max(bid, 88.0))

    return max(0.0, bid)
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
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    base = 34.0

    if supply <= 16:
        base += 18.0
    elif supply <= 18:
        base += 10.0
    elif supply >= 23:
        base -= 8.0

    if hp <= 2:
        base += 28.0
    elif hp <= 4:
        base += 16.0
    elif hp >= 8:
        base -= 4.0

    if no_water_days >= 2:
        base += 26.0
    elif no_water_days >= 1:
        base += 14.0

    if urgent_opp >= 2:
        base += 8.0
    elif urgent_opp == 0 and supply >= 20:
        base -= 5.0

    if highest_prev >= 130.0:
        if hp > 4 and no_water_days == 0:
            base = min(base, 28.0)
        else:
            base += 10.0
    elif highest_prev >= 80.0:
        base = max(base, min(highest_prev + 2.0, 78.0))
    elif highest_prev >= 55.0:
        base = max(base, highest_prev + 1.5)
    elif avg_prev > 0:
        base = max(base, avg_prev + 1.0)

    if day >= 8:
        base += 6.0
    if day == 10:
        base += 10.0

    if budget < 45:
        base = min(base, budget)
    elif budget < 90:
        base = min(base, 0.8 * budget)
    else:
        base = min(base, 0.55 * budget)

    base = max(0.0, min(base, budget))
    return float(round(base, 2))
"""
