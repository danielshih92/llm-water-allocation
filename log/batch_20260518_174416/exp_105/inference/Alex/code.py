# ============================================================
# Experiment: exp_105
# Agent: Alex
# Source: exp_105
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return min(budget, max(0, base))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 6:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    scarcity_pressure = 0
    if supply <= 16:
        scarcity_pressure = 10
    elif supply <= 18:
        scarcity_pressure = 6
    elif supply >= 23:
        scarcity_pressure = -4

    urgency = 0
    if hp <= 2:
        urgency += 22
    elif hp <= 4:
        urgency += 10
    if no_water_days >= 2:
        urgency += 18
    elif no_water_days == 1:
        urgency += 8

    opponent_pressure = desperate_count * 4 + rich_count * 2

    base_bid = DAILY_SALARY * 0.48 + scarcity_pressure + urgency + opponent_pressure

    if highest_prev > 0:
        target = max(base_bid, highest_prev + 1.5)
        if highest_prev >= DAILY_SALARY * 0.9 and hp > 4 and no_water_days == 0:
            target = min(target, DAILY_SALARY * 0.42)
        elif highest_prev <= DAILY_SALARY * 0.45:
            target = max(target, avg_prev + 2.0)
    else:
        target = base_bid

    remaining_days = max(1, 10 - day + 1)
    reserve_floor = DAILY_SALARY * 0.28 * remaining_days
    if hp > 4 and no_water_days == 0 and budget < reserve_floor:
        target = min(target, DAILY_SALARY * 0.32)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.88)

    if day >= 8 and hp <= 4:
        target = max(target, DAILY_SALARY * 0.8)

    bid = max(0, min(budget, target))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    req_pressure = 0.0
    rich_aggressive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            req_pressure += opp.get('water_requirement', 0)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))
            if opp.get('budget', 0) > 800 and opp.get('hp', 0) > 4:
                rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    contested = supply <= 18 or req_pressure >= supply * 1.4
    abundant = supply >= 22

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
    if day >= 8:
        urgency += 1

    if abundant and urgency == 0:
        bid = max(12.0, avg_prev * 0.45)
    elif abundant:
        bid = max(22.0, avg_prev * 0.6)
    elif contested:
        target = max(48.0, min(highest_prev + 2.5, DAILY_SALARY * 0.98))
        if highest_prev > 110:
            target = max(58.0, min(82.0, avg_prev * 0.75))
        bid = target
    else:
        bid = max(30.0, min(62.0, avg_prev + 1.5))

    if rich_aggressive >= 2 and contested:
        bid += 6.0

    if urgency >= 5:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif urgency >= 3:
        bid = max(bid, DAILY_SALARY * 0.8)
    elif urgency >= 1:
        bid = max(bid, DAILY_SALARY * 0.6)

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, max(18.0, budget * 0.7))
    elif budget > 900 and contested:
        bid = min(max(bid, 72.0), 96.0)

    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    passive_count = 0
    aggressive_count = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid <= 15:
                    passive_count += 1
                if bid >= 70:
                    aggressive_count += 1

    if not alive:
        return min(budget, 12.0)

    expected_low = 15.0
    if prev_bids:
        expected_low = max(15.0, min(prev_bids) + 1.0)

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tightness = 1.0 - scarcity

    bid = expected_low

    if aggressive_count >= 1:
        bid += 2.0
    if passive_count >= 2:
        bid -= 1.0

    bid += 6.0 * tightness

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 66.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, 28.0 + 12.0 * tightness)
    else:
        bid = max(bid, 16.0 + 6.0 * tightness)

    if day >= 8 and hp > 4:
        bid *= 0.95

    if budget < 40:
        bid = min(bid, budget)
    else:
        reserve_floor = max(0.0, budget - DAILY_SALARY * max(0, 10 - int(day)))
        bid = min(bid, max(18.0, budget - reserve_floor))

    bid = max(0.0, min(budget, bid))
    return float(round(bid, 2))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    dangerous_bids = []
    low_budget_count = 0
    rich_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) < DAILY_SALARY * 0.8:
                low_budget_count += 1
            if opp.get('budget', 0) > DAILY_SALARY * 4:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    dangerous_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.35))

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units <= 1.2:
        scarcity = 2
    elif units <= 1.6:
        scarcity = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
    danger_prev = max(dangerous_bids) if dangerous_bids else 0.0

    urgency = 0
    if hp <= 2 or no_water >= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    base = DAILY_SALARY * 0.42

    if urgency >= 3:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif urgency == 2:
        if scarcity >= 1:
            bid = max(DAILY_SALARY * 0.82, second_prev + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.72, danger_prev + 1.0)
    else:
        if scarcity >= 2:
            bid = max(DAILY_SALARY * 0.68, second_prev + 1.0)
        elif scarcity == 1:
            bid = max(base, min(DAILY_SALARY * 0.75, second_prev + 0.5))
        else:
            if highest_prev >= DAILY_SALARY * 1.2:
                bid = DAILY_SALARY * 0.28
            elif highest_prev >= DAILY_SALARY * 0.9:
                bid = DAILY_SALARY * 0.34
            else:
                bid = max(DAILY_SALARY * 0.45, second_prev + 0.75)

    if low_budget_count >= 2 and urgency == 0:
        bid *= 0.88
    if rich_count >= 2 and scarcity >= 1:
        bid *= 1.08

    if day >= 8 and hp >= 6 and no_water == 0:
        bid *= 0.92

    reserve = 0.0
    if urgency == 0:
        reserve = DAILY_SALARY * 1.2
    elif urgency == 1:
        reserve = DAILY_SALARY * 0.8
    elif urgency == 2:
        reserve = DAILY_SALARY * 0.3

    cap = budget - reserve
    if cap < 0:
        cap = budget

    bid = min(bid, cap)
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
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    pressure_bid = 0.0
    eric_bid = None
    tight_competitors = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        obid = 0.0
        if prev and prev.get('bid') is not None:
            obid = prev.get('bid', 0.0)
        if obid > pressure_bid:
            pressure_bid = obid
        if oid == 'Eric':
            eric_bid = obid
        if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
            tight_competitors += 1

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    danger = 0.0
    if hp <= 2:
        danger += 0.7
    elif hp <= 4:
        danger += 0.4
    if no_water >= 2:
        danger += 0.8
    elif no_water == 1:
        danger += 0.35

    base = DAILY_SALARY * (0.22 + 0.38 * scarcity + danger)

    if eric_bid is not None:
        if danger >= 0.7:
            target = eric_bid + 2.5
        elif scarcity >= 0.6:
            target = eric_bid + 1.0
        else:
            target = eric_bid * 0.72
        bid = max(base, target)
    else:
        if pressure_bid > 0:
            if danger >= 0.7:
                bid = max(base, pressure_bid + 1.5)
            else:
                bid = max(base, pressure_bid * 0.7)
        else:
            bid = base

    if supply >= 22 and danger < 0.7:
        bid *= 0.72
    elif supply <= 17:
        bid *= 1.18

    if day >= 8:
        bid *= 1.12
    if tight_competitors <= 1 and danger < 0.7:
        bid *= 0.75

    min_need_bid = 0.0
    if no_water >= 2 or hp <= 2:
        min_need_bid = DAILY_SALARY * 0.92
    elif no_water == 1 or hp <= 4:
        min_need_bid = DAILY_SALARY * 0.62

    bid = max(bid, min_need_bid)
    bid = min(budget, bid)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.28))

    pressure = max(prev_bids) if prev_bids else DAILY_SALARY * 0.75
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else DAILY_SALARY * 0.7

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.75
    elif hp <= 4:
        danger += 0.45
    elif hp <= 6:
        danger += 0.2

    if no_water_days >= 2:
        danger += 0.8
    elif no_water_days == 1:
        danger += 0.35

    if day >= 8:
        danger += 0.15

    base = DAILY_SALARY * (0.34 + 0.22 * scarcity + 0.28 * danger)

    if supply >= 22 and hp >= 7 and no_water_days == 0:
        bid = min(base, DAILY_SALARY * 0.38)
    elif pressure < DAILY_SALARY * 0.9:
        bid = max(base, pressure + 1.2)
    elif pressure < DAILY_SALARY * 1.3:
        if danger >= 0.6:
            bid = max(base, pressure + 2.0)
        else:
            bid = max(base, avg_prev * 0.82)
    else:
        if danger >= 0.85:
            bid = max(base, min(pressure * 0.92, DAILY_SALARY * 1.45))
        else:
            bid = max(base, DAILY_SALARY * 0.42)

    if urgent_opp >= 2:
        bid += 4.0
    elif urgent_opp == 0 and supply >= 20:
        bid -= 3.0

    if rich_opp >= 3 and danger >= 0.5:
        bid += 3.5

    if budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.58)
    elif budget < DAILY_SALARY * 4:
        bid = min(bid, budget * 0.42)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.95)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
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
        return float(min(budget, 18.0))

    bob_prev_bid = None
    cindy_alive = False
    pressure_bids = []
    weak_count = 0

    for agent_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            pressure_bids.append(float(bid))
        if agent_id == 'Bob' and bid is not None:
            bob_prev_bid = float(bid)
        if agent_id == 'Cindy':
            cindy_alive = True
        if opp.get('budget', 0) < 80 or opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            weak_count += 1

    tight_supply = supply <= 17
    loose_supply = supply >= 22
    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        target = 148.0 if cindy_alive else 110.0
    elif urgent:
        if bob_prev_bid is not None:
            target = max(92.0, min(120.0, bob_prev_bid + 4.0))
        else:
            target = 96.0
    else:
        if tight_supply:
            if bob_prev_bid is not None:
                target = max(72.0, min(112.0, bob_prev_bid + 2.0))
            else:
                target = 78.0
        elif loose_supply:
            target = 18.0 if weak_count >= 2 else 26.0
        else:
            if pressure_bids:
                prev_max = max(pressure_bids)
                if prev_max >= 140.0:
                    target = 24.0
                elif prev_max >= 100.0:
                    target = 58.0
                else:
                    target = max(32.0, prev_max + 2.0)
            else:
                target = 42.0

    reserve_floor = 0.0
    if hp >= 5 and no_water == 0:
        reserve_floor = 35.0
    elif hp >= 3:
        reserve_floor = 20.0

    affordable = max(0.0, budget - reserve_floor)
    if urgent or critical:
        affordable = budget

    bid = min(target, affordable)

    if bid < 0:
        bid = 0.0
    if urgent and bid < 35.0 and budget >= 35.0:
        bid = 35.0

    return float(min(bid, budget))
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

    alive_opps = []
    prev_bids = []
    strong_prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    strong_prev_bids.append(float(bid))

    if not alive_opps:
        return max(0.0, min(budget, 20.0))

    req_players = 1
    for opp in alive_opps:
        req = opp.get('water_requirement', WATER_REQ)
        if req and supply >= req:
            req_players += 1

    scarcity = supply / float(WATER_REQ * req_players)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    active_high = max(strong_prev_bids) if strong_prev_bids else highest_prev
    low_prev = min(prev_bids) if prev_bids else 0.0

    critical = hp <= 3 or no_water >= 2
    pressured = hp <= 5 or no_water >= 1

    if critical:
        target = max(150.0, active_high + 2.0)
        if supply >= 22:
            target -= 10.0
        return max(0.0, min(budget, target))

    if scarcity >= 1.2:
        target = 18.0
        if pressured:
            target = 45.0
        if highest_prev < 100:
            target = max(target, low_prev + 1.0 if prev_bids else target)
        return max(0.0, min(budget, target))

    if scarcity >= 0.9:
        target = 55.0
        if pressured:
            target = 95.0
        if prev_bids:
            target = max(target, min(active_high - 35.0, 110.0))
        return max(0.0, min(budget, target))

    target = 85.0
    if prev_bids:
        target = max(target, min(active_high - 8.0, 155.0))
    if pressured:
        target = max(target, min(active_high + 1.5, 165.0))
    if supply <= 16:
        target += 8.0
    if day >= 8 and hp >= 6 and no_water == 0:
        target -= 12.0

    return max(0.0, min(budget, target))
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    dangerous_prev.append(float(bid))

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    pressure_prev = max(dangerous_prev) if dangerous_prev else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    affordable_daily = budget / max(1.0, float(11 - day))

    emergency = hp <= 3 or no_water >= 1
    severe = hp <= 2 or no_water >= 2

    if severe:
        target = max(112.0, pressure_prev + 3.0)
    elif emergency:
        target = max(98.0, pressure_prev + 2.0)
    else:
        if supply >= 22:
            target = min(72.0, max(24.0, affordable_daily * 0.7))
        elif supply >= 19:
            target = max(58.0, min(92.0, pressure_prev * 0.72 + 6.0))
        else:
            target = max(96.0, pressure_prev + 1.5)

    if highest_prev >= 140 and not emergency and supply >= 20:
        target = min(target, 70.0)

    if day >= 8:
        target += 8.0
    elif day >= 6:
        target += 4.0

    target = min(target, budget)
    target = min(target, max(0.0, affordable_daily * 1.9 + 18.0))

    if severe:
        target = min(budget, max(target, min(118.0, budget)))

    if target < 0:
        target = 0.0
    return float(target)
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

    alive = []
    yesterday_bids = []
    threatening_bids = []
    rich_threat = False
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 200:
                rich_threat = True
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    threatening_bids.append(float(bid))

    if not alive:
        return max(0.0, min(budget, 18.0))

    max_prev = max(yesterday_bids) if yesterday_bids else 0.0
    max_threat = max(threatening_bids) if threatening_bids else max_prev

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    danger = 0
    if hp <= 3 or no_water_days >= 2:
        danger = 2
    elif hp <= 6 or no_water_days >= 1:
        danger = 1

    if danger == 2:
        bid = max(92.0, max_threat + 2.0)
        if rich_threat:
            bid = max(bid, 108.0)
    elif scarcity == 2:
        bid = max(82.0, min(109.0, max_threat + 1.5))
    elif scarcity == 1:
        bid = max(58.0, min(96.0, max_threat * 0.92 + 1.0))
    else:
        if max_prev >= 105:
            bid = 31.0
        elif max_prev >= 85:
            bid = 44.0
        else:
            bid = max(36.0, max_prev * 0.72)

    if budget < 80:
        bid = min(bid, max(22.0, budget * 0.72))
    elif budget < 140:
        bid = min(bid, budget * 0.82)

    if day >= 8:
        if hp <= 5:
            bid = max(bid, 78.0)
        elif budget > 200 and scarcity >= 1:
            bid = max(bid, 72.0)

    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
"""
