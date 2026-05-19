# ============================================================
# Experiment: exp_054
# Agent: Alex
# Source: exp_054
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

    supply = float(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    stressed_count = 0
    error_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                stressed_count += 1
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('error'):
                error_count += 1
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            status = prev.get('status')
            if status in ('dehydrated', 'dead', 'eliminated'):
                stressed_count += 1

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.35)

    high_supply = supply >= 22
    low_supply = supply <= 17

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = DAILY_SALARY * 0.55
        avg_prev = DAILY_SALARY * 0.5

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

    if low_supply:
        urgency += 2
    elif high_supply:
        urgency -= 1

    if stressed_count >= max(1, len(alive_opponents) // 2):
        urgency += 1
    if error_count >= 1:
        urgency -= 1

    if urgency >= 6:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 2.0)
    elif urgency >= 4:
        bid = max(DAILY_SALARY * 0.78, avg_prev + 1.5)
    elif urgency >= 2:
        bid = max(DAILY_SALARY * 0.6, avg_prev)
    else:
        if high_supply:
            bid = DAILY_SALARY * 0.38
        else:
            bid = DAILY_SALARY * 0.48

    if highest_prev >= DAILY_SALARY * 0.9 and urgency <= 2:
        bid = min(bid, DAILY_SALARY * 0.5)

    if day >= 8:
        bid += 4
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        bid += 6

    bid = max(0, min(float(budget), float(bid)))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    fixed70_count = 0
    high_pressure = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = None
            if prev:
                bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if abs(bid - 70) < 1e-9:
                    fixed70_count += 1
                if bid >= 90:
                    high_pressure += 1

    if not alive:
        return max(0.0, min(budget, 18.0))

    units = supply / WATER_REQ
    very_tight = units < 1.6
    tight = units < 2.1

    highest_prev = max(prev_bids) if prev_bids else 70.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

    critical = hp <= 3 or no_water_days >= 1
    fragile = hp <= 5

    if critical:
        target = max(92.0, highest_prev + 2.5)
        if budget < target:
            return max(0.0, budget)
        return max(0.0, min(budget, target))

    if very_tight:
        if high_pressure >= 2:
            target = max(96.0, second_prev + 1.5)
        else:
            target = max(72.5, highest_prev + 1.5)
        return max(0.0, min(budget, target))

    if tight:
        if fragile:
            target = max(74.0, min(98.0, highest_prev + 1.0))
        else:
            if fixed70_count >= 1:
                target = 71.5
            else:
                target = 63.0
        return max(0.0, min(budget, target))

    if hp >= 8 and budget < DAILY_SALARY * 6:
        return max(0.0, min(budget, 22.0))

    if fixed70_count >= 1 and hp >= 6:
        return max(0.0, min(budget, 71.2))

    if day >= 8 and hp >= 6:
        return max(0.0, min(budget, 58.0))

    return max(0.0, min(budget, 48.0))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 45.0)
        return min(budget, 18.0)

    opp_bids = []
    eric_bid = None
    active_threats = 0
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            opp_bids.append(float(bid))
            if bid > 0:
                active_threats += 1
        if agent_id == 'Eric' and bid is not None:
            eric_bid = float(bid)

    if eric_bid is None:
        eric_bid = 94.0

    if supply >= 24:
        scarcity = 'low'
    elif supply >= 20:
        scarcity = 'medium'
    else:
        scarcity = 'high'

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if urgent:
        target = max(62.0, min(eric_bid + 2.0, 110.0))
    elif scarcity == 'high':
        target = max(58.0, min(eric_bid - 4.0, 92.0))
    elif scarcity == 'medium':
        if pressured:
            target = max(46.0, min(eric_bid - 12.0, 78.0))
        else:
            target = 28.0 if active_threats <= 1 else 36.0
    else:
        if pressured:
            target = 34.0
        else:
            target = 14.0

    if day >= 8:
        if urgent:
            target += 8.0
        elif hp >= 6 and budget < 120:
            target -= 6.0

    if budget <= 0:
        return 0.0

    if budget < target:
        if urgent:
            return float(budget)
        return min(float(budget), 20.0)

    return float(min(budget, max(0.0, target)))
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

    slots = max(1, int(supply / WATER_REQ))
    opp_bids = []
    desperate_count = 0
    rich_conservative = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            opp_bids.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) > 300 and opp.get('daily_salary', 0) >= 70:
            rich_conservative += 1

    highest_prev = max(opp_bids) if opp_bids else 0.0
    second_prev = 0.0
    if len(opp_bids) >= 2:
        sorted_bids = sorted(opp_bids, reverse=True)
        second_prev = sorted_bids[int(1)]

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

    tight = slots <= 1
    very_tight = supply <= 16

    base = 16.0
    if slots >= 2:
        base = 12.0
    if slots == 1:
        base = 24.0
    if very_tight:
        base += 6.0

    if highest_prev >= 500:
        pressure_bid = 46.0
    elif highest_prev >= 130:
        pressure_bid = 58.0
    elif highest_prev >= 90:
        pressure_bid = min(72.0, highest_prev + 2.0)
    elif highest_prev >= 50:
        pressure_bid = highest_prev + 1.5
    elif highest_prev > 0:
        pressure_bid = max(base, highest_prev + 1.0)
    else:
        pressure_bid = base

    bid = max(base, pressure_bid)

    if desperate_count >= slots:
        bid += 10.0
    elif desperate_count > 0:
        bid += 4.0

    if rich_conservative >= 1 and highest_prev <= 140:
        bid += 3.0

    if urgency >= 5:
        bid = max(bid, 82.0)
    elif urgency >= 3:
        bid = max(bid, 62.0)
    elif urgency >= 1:
        bid = max(bid, 42.0)

    if day >= 8:
        bid += 6.0
    if day >= 9 and hp <= 5:
        bid += 8.0

    reserve = 0.0
    if day <= 7:
        reserve = 20.0
    elif day == 8:
        reserve = 10.0

    affordable = max(0.0, budget - reserve)
    if urgency >= 5:
        affordable = budget

    bid = min(bid, affordable if affordable > 0 else budget)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    day = day_context['day']
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
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if opp.get('hp', 0) > 2 and opp.get('budget', 0) > 0:
                    strong_prev.append(bid)

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_live_prev = max(strong_prev) if strong_prev else highest_prev

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0:
        tightness = 0.0
    if tightness > 1:
        tightness = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    elif hp <= 6:
        urgency += 0.12

    if no_water_days >= 2:
        urgency += 0.35
    elif no_water_days >= 1:
        urgency += 0.18

    urgency += 0.45 * tightness

    conservative = 16.0 + 18.0 * tightness
    pressure_bid = strongest_live_prev + 1.6 if strongest_live_prev > 0 else 0.0

    if hp >= 7 and no_water_days == 0 and supply >= 22:
        target = conservative
    elif urgency >= 0.95:
        target = max(62.0, pressure_bid, 0.88 * DAILY_SALARY + 28.0 * tightness)
    elif urgency >= 0.65:
        target = max(42.0 + 16.0 * tightness, min(pressure_bid, 96.0))
    else:
        target = max(conservative, min(pressure_bid, 58.0 + 10.0 * tightness))

    if day >= 8:
        target += 6.0 * tightness
        if hp <= 4:
            target += 8.0

    max_safe = budget
    if day < 9:
        reserve_days = 10 - day
        reserve = max(0.0, reserve_days * 8.0)
        max_safe = max(0.0, budget - reserve)
        if max_safe < 12.0:
            max_safe = min(budget, 12.0 + 8.0 * urgency)

    bid = min(budget, max_safe if max_safe > 0 else budget, target)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, max(68.0, pressure_bid, 84.0 + 18.0 * tightness)))

    if bid < 0:
        bid = 0.0
    return float(round(min(budget, bid), 2))
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

    alive_opponents = []
    prev_bids = []
    opp_budgets = []
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0
    richest_opp = max(opp_budgets) if opp_budgets else 0.0

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0:
        tightness = 0.0
    if tightness > 1:
        tightness = 1.0

    base = DAILY_SALARY * (0.28 + 0.30 * tightness)

    if supply <= 16:
        base += 12
    elif supply >= 23:
        base -= 8

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.95)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * (0.62 + 0.18 * tightness))

    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 1.15)
    elif no_water_days == 1:
        base = max(base, DAILY_SALARY * 0.82)

    if desperate_count >= 2 and supply <= 18:
        base += 10

    if highest_prev > 0:
        if highest_prev >= 140:
            if hp >= 5 and no_water_days == 0 and supply >= 20:
                base = min(base, DAILY_SALARY * 0.35)
            else:
                base = max(base, min(highest_prev * 0.72, DAILY_SALARY * 1.02))
        elif highest_prev >= 90:
            base = max(base, min(highest_prev + 2.0, DAILY_SALARY * 0.98))
        else:
            base = max(base, highest_prev + 3.0)
    else:
        base = max(base, DAILY_SALARY * 0.4)

    if avg_prev >= 130 and hp >= 6 and no_water_days == 0 and supply >= 21:
        base = min(base, DAILY_SALARY * 0.33)

    if budget < DAILY_SALARY * 2:
        base = min(base, budget * 0.55)
    elif budget < richest_opp * 0.5 and hp >= 5 and no_water_days == 0:
        base = min(base, DAILY_SALARY * 0.5)

    if day >= 8:
        if hp <= 4 or no_water_days >= 1:
            base += 10
        else:
            base -= 4

    bid = max(0.0, min(float(budget), float(base)))
    return float(round(bid, 2))
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
    prev_bids = []
    prev_aggressive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                req = opp.get('water_requirement', WATER_REQ)
                if req > 0:
                    prev_aggressive.append(bid / float(req))

    if not alive_opponents:
        return max(0.0, min(budget, 18.0))

    total_players = 1 + len(alive_opponents)
    est_units = supply / float(WATER_REQ)
    scarcity = est_units < total_players
    severe_scarcity = est_units < max(1.5, total_players * 0.6)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0
    high_pressure = highest_prev >= 90
    medium_pressure = highest_prev >= 60 or avg_prev >= 50

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 3
    elif hp <= 7:
        urgency += 2
    else:
        urgency += 1

    if no_water_days >= 2:
        urgency += 3
    elif no_water_days >= 1:
        urgency += 2

    if severe_scarcity:
        urgency += 2
    elif scarcity:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency >= 7:
        target = max(92.0, highest_prev + 2.5)
        if high_pressure:
            target = max(target, 108.0)
    elif urgency >= 5:
        if severe_scarcity:
            target = max(72.0, highest_prev + 1.5)
        else:
            target = max(58.0, avg_prev + 4.0)
    elif urgency >= 3:
        if medium_pressure and scarcity:
            target = max(46.0, avg_prev + 2.0)
        else:
            target = 32.0 if not scarcity else 40.0
    else:
        if high_pressure:
            target = 18.0
        elif medium_pressure:
            target = 24.0
        else:
            target = 20.0

    if budget < DAILY_SALARY * 1.2 and urgency < 6:
        target = min(target, 45.0)
    if budget < 35:
        target = min(target, budget)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, min(budget, 95.0))

    return max(0.0, min(budget, target))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply / WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 120:
            rich_opponents += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    my_urgent = hp <= 3 or no_water_days >= 2
    my_semi_urgent = hp <= 5 or no_water_days >= 1

    if not alive_opponents:
        return float(min(budget, 18.0 if not my_urgent else 45.0))

    if my_urgent:
        bid = max(92.0, highest_prev + 4.0, avg_prev + 8.0)
        if slots >= 2:
            bid -= 8.0
        return float(max(0.0, min(budget, bid)))

    if slots >= 2:
        if highest_prev >= 120:
            bid = 24.0
        elif highest_prev >= 90:
            bid = 32.0
        else:
            bid = 38.0
        if rich_opponents >= 2:
            bid += 4.0
        if my_semi_urgent:
            bid += 10.0
        if day >= 8 and hp > 5:
            bid -= 6.0
        return float(max(0.0, min(budget, bid)))

    bid = 0.0
    if highest_prev >= 130:
        bid = 58.0 if not my_semi_urgent else 88.0
    elif highest_prev >= 100:
        bid = 66.0 if not my_semi_urgent else 94.0
    elif highest_prev > 0:
        bid = highest_prev + 2.5
    else:
        bid = 72.0

    if urgent_opponents >= 2 and not my_semi_urgent:
        bid -= 8.0
    if my_semi_urgent:
        bid += 8.0
    if day >= 8 and hp > 6 and no_water_days == 0:
        bid -= 10.0

    if budget < bid:
        bid = budget
    if bid < 0:
        bid = 0.0
    return float(bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_opp = 0
    desperate_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive.append(opp)
        if opp.get('budget', 0) >= 120:
            rich_opp += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        if opp.get('daily_salary', 0) >= DAILY_SALARY:
            strong_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(float(bid))

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_pressure = 1.0 - ((supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY))
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    if no_water_days >= 2:
        urgency += 0.35
    elif no_water_days >= 1:
        urgency += 0.2
    urgency += 0.2 * supply_pressure

    if highest_prev >= 150:
        base = DAILY_SALARY * 0.22
    elif highest_prev >= 110:
        base = DAILY_SALARY * 0.3
    elif highest_prev >= 70:
        base = min(DAILY_SALARY * 0.7, highest_prev * 0.72)
    elif highest_prev > 0:
        base = max(DAILY_SALARY * 0.42, highest_prev + 2.0)
    else:
        base = DAILY_SALARY * 0.4

    if rich_opp >= 2 and avg_prev > 100:
        base *= 0.85
    if desperate_opp >= 2:
        base *= 1.15
    if supply >= 22:
        base *= 0.82
    elif supply <= 17:
        base *= 1.18

    bid = base + DAILY_SALARY * urgency

    if hp <= 2 or no_water_days >= 2:
        floor_bid = DAILY_SALARY * 0.88
        if bid < floor_bid:
            bid = floor_bid

    if hp >= 7 and no_water_days == 0 and highest_prev >= 120 and supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.28)

    max_safe = budget
    if hp > 4 and no_water_days == 0:
        max_safe = min(max_safe, budget * 0.55)
    elif hp > 2:
        max_safe = min(max_safe, budget * 0.75)

    bid = min(bid, max_safe)
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        base = 18.0 if hp > 3 else 40.0
        return float(max(0.0, min(budget, base)))

    units = supply / WATER_REQ
    tight = units <= 1.45
    roomy = units >= 1.8

    prev_bids = []
    urgent_prev_bids = []
    weak_opp_exists = False
    rich_pressure = 0.0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            weak_opp_exists = True
        if opp.get('budget', 0) > budget:
            rich_pressure += 1.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_high = max(urgent_prev_bids) if urgent_prev_bids else highest_prev

    if hp <= 2 or no_water >= 2:
        bid = max(62.0, urgent_high + 2.0)
    elif hp <= 4 or no_water >= 1:
        if tight:
            bid = max(52.0, urgent_high + 1.2)
        else:
            bid = max(38.0, highest_prev * 0.72 + 2.0)
    else:
        if roomy:
            bid = max(18.0, min(34.0, highest_prev * 0.38 + 1.0))
        elif tight:
            bid = max(34.0, urgent_high + 0.8)
        else:
            bid = max(26.0, highest_prev * 0.55 + 1.5)

    if weak_opp_exists and hp >= 5 and tight:
        bid += 4.0

    if rich_pressure >= 2 and hp >= 5 and roomy:
        bid -= 4.0

    if day >= 8:
        if hp <= 4:
            bid += 8.0
        else:
            bid += 3.0

    cap = budget
    if hp >= 6 and no_water == 0:
        soft_cap = DAILY_SALARY * 0.95
    elif hp >= 4:
        soft_cap = DAILY_SALARY * 1.15
    else:
        soft_cap = DAILY_SALARY * 1.45
    if soft_cap < cap:
        cap = soft_cap

    if bid < 0:
        bid = 0.0
    if bid > cap:
        bid = cap

    return float(max(0.0, min(budget, bid)))
"""
