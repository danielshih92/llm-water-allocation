# ============================================================
# Experiment: exp_004
# Agent: Alex
# Source: exp_004
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

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return min(budget, 50)
        return min(budget, 28)

    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 3:
            if bid is not None:
                try:
                    if float(bid) >= DAILY_SALARY * 0.75:
                        rich_aggressive += 1
                except Exception:
                    pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if supply >= 23:
        base = 18
    elif supply >= 20:
        base = 26
    elif supply >= 17:
        base = 36
    else:
        base = 48

    if hp <= 2:
        base += 18
    elif hp <= 4:
        base += 8

    if no_water >= 2:
        base += 20
    elif no_water >= 1:
        base += 10

    base += min(desperate_count * 3, 9)
    base += min(rich_aggressive * 2, 6)

    if highest_prev > 0:
        if supply <= 17:
            target = max(base, highest_prev + 2.0)
        elif supply <= 20:
            target = max(base, avg_prev + 1.5)
        else:
            target = max(base, avg_prev)
    else:
        target = base

    if hp > 4 and no_water == 0 and supply >= 22:
        target = min(target, 24)

    if budget < target:
        if hp <= 2 or no_water >= 1:
            return max(0, budget)
        return max(0, min(budget, target * 0.85))

    return max(0, min(budget, round(target, 2)))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    aggressive_bids = []
    desperate_count = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= DAILY_SALARY * 0.8:
                    aggressive_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.25))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    risk = 0.0
    if hp <= 2:
        risk += 0.5
    elif hp <= 4:
        risk += 0.3

    if no_water_days >= 2:
        risk += 0.35
    elif no_water_days >= 1:
        risk += 0.2

    risk += 0.2 * supply_pressure
    risk += min(0.2, 0.05 * desperate_count)
    if highest_prev >= DAILY_SALARY * 0.8:
        risk += 0.15
    elif highest_prev >= DAILY_SALARY * 0.5:
        risk += 0.08

    if risk >= 0.8:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif risk >= 0.55:
        target = max(DAILY_SALARY * 0.72, avg_prev + 3.0, highest_prev * 0.9)
    elif risk >= 0.3:
        target = max(DAILY_SALARY * 0.48, avg_prev + 1.5)
    else:
        target = DAILY_SALARY * (0.28 + 0.12 * supply_pressure)
        if highest_prev > 0:
            target = max(target, min(highest_prev * 0.65, DAILY_SALARY * 0.45))

    if budget < DAILY_SALARY * 0.5 and (hp > 4 and no_water_days == 0):
        target = min(target, budget * 0.55)

    target = min(target, budget)
    if target < 0:
        target = 0.0

    return float(target)
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    dangerous_pressure = 0.0
    rich_alive = 0
    desperate_alive = 0
    for opp in alive:
        obudget = opp.get('budget', 0)
        ohp = opp.get('hp', 0)
        ono = opp.get('no_water_days', 0)
        if obudget >= 140:
            rich_alive += 1
        if ohp <= 3 or ono >= 2:
            desperate_alive += 1
        prev = opp.get('previous_trace', {})
        if prev:
            pbid = prev.get('bid')
            if pbid is not None:
                prev_bids.append(float(pbid))
                if obudget > 0 and opp.get('alive'):
                    dangerous_pressure = max(dangerous_pressure, float(pbid))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / WATER_REQ
    scarce = units < 1.6
    medium = units < 1.9

    urgency = 0
    if hp <= 2 or no_water_days >= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency == 3:
        base = 92.0
        if scarce:
            base = 108.0
        elif medium:
            base = 98.0
        bid = max(base, max_prev + 3.0)
    elif urgency == 2:
        base = 58.0
        if scarce:
            base = 76.0
        elif medium:
            base = 66.0
        bid = max(base, dangerous_pressure + 2.0)
    elif urgency == 1:
        base = 34.0
        if scarce:
            base = 48.0
        elif medium:
            base = 40.0
        bid = max(base, min(dangerous_pressure + 1.0, 72.0))
    else:
        if scarce:
            bid = max(28.0, min(avg_prev + 1.0, 55.0))
        elif medium:
            bid = 24.0
        else:
            bid = 18.0

    if rich_alive >= 1 and urgency <= 1:
        bid *= 0.92
    if desperate_alive >= 2 and urgency == 0:
        bid *= 0.9

    if day >= 8:
        bid += 6.0
    elif day >= 5 and urgency >= 1:
        bid += 4.0

    reserve_floor = 0.0
    if hp > 4 and day <= 6:
        reserve_floor = 70.0
    max_affordable = max(0.0, budget - reserve_floor)
    if urgency >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable)
    if urgency >= 2 and bid < 20.0 and budget >= 20.0:
        bid = min(budget, 20.0)

    if bid < 0:
        bid = 0.0
    return float(round(min(budget, bid), 2))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    strong_prev = []
    desperate_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if bid >= 100:
                    strong_prev.append(bid)

    if not alive_opps:
        return float(min(budget, 20.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.45

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    if strong_prev:
        target_high = max(strong_prev)
    else:
        target_high = highest_prev

    if urgency >= 1.4:
        bid = max(110.0, target_high + 2.0, avg_prev + 8.0)
    elif scarcity > 0.7:
        bid = max(85.0, avg_prev + 5.0)
        if target_high >= 120:
            bid = max(bid, min(target_high + 1.0, 155.0))
    elif scarcity > 0.4:
        bid = max(52.0, avg_prev * 0.72 + 4.0)
    else:
        bid = max(28.0, avg_prev * 0.45 + 2.0)

    if desperate_count >= 2:
        bid += 10.0
    elif desperate_count == 1:
        bid += 5.0

    if day >= 8 and hp <= 5:
        bid += 12.0

    if budget < 120:
        bid = min(bid, max(25.0, budget * 0.72))
    elif budget < 220:
        bid = min(bid, budget * 0.82)

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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
            if opp.get('budget', 0) >= 140:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return max(0.0, min(float(budget), 18.0 if hp > 3 else 40.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (25.0 - supply) / 10.0
    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.55
    if no_water >= 2:
        danger += 1.0
    elif no_water >= 1:
        danger += 0.45

    market_pressure = 0.0
    if highest_prev >= 180:
        market_pressure = 1.0
    elif highest_prev >= 140:
        market_pressure = 0.75
    elif highest_prev >= 100:
        market_pressure = 0.45
    else:
        market_pressure = 0.2

    if supply <= 16:
        base = 78 + 18 * danger + 10 * market_pressure + 4 * rich_opp
    elif supply <= 18:
        base = 60 + 16 * danger + 8 * market_pressure + 3 * urgent_opp
    elif supply <= 21:
        base = 43 + 13 * danger + 6 * market_pressure
    else:
        base = 28 + 10 * danger + 4 * market_pressure

    if hp >= 7 and no_water == 0 and supply >= 20 and highest_prev >= 130:
        base *= 0.72

    if day >= 8:
        base += 8 + 6 * danger

    target = max(base, avg_prev * 0.92)

    if danger >= 1.0:
        target = max(target, highest_prev + 3.0)
    elif danger >= 0.45 and supply <= 18:
        target = max(target, highest_prev + 1.5)
    else:
        if highest_prev >= 150:
            target = min(target, highest_prev - 8.0)

    if budget < 90:
        target = min(target, budget * (0.72 if danger < 1.0 else 0.9))

    floor_bid = 8.0
    if danger >= 1.0:
        floor_bid = 35.0
    elif supply <= 17:
        floor_bid = 24.0

    bid = max(floor_bid, target)
    bid = min(float(budget), bid)
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

    alive_opponents = []
    prev_bids = []
    opp_pressure = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0.0)
                prev_bids.append(b)
                if b > opp_pressure:
                    opp_pressure = b

    if not alive_opponents:
        return max(0.0, min(budget, 18.0))

    scarcity = supply / float(WATER_REQ)
    severe_scarcity = scarcity < 1.35

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1
    if day >= 8:
        danger += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    if severe_scarcity:
        if danger >= 3:
            target = max(92.0, highest_prev + 3.0)
        elif danger >= 2:
            target = max(72.0, avg_prev + 2.0)
        else:
            if highest_prev >= 110.0:
                target = 8.0
            elif highest_prev >= 85.0:
                target = 18.0
            else:
                target = 32.0
    else:
        if danger >= 3:
            target = max(78.0, highest_prev + 2.0)
        elif danger >= 2:
            target = max(58.0, avg_prev + 1.5)
        else:
            target = 24.0 if highest_prev >= 80.0 else 38.0

    for oid, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        if not prev:
            continue
        obid = prev.get('bid', 0.0)
        ohp = opp.get('hp', 10)
        onwd = opp.get('no_water_days', 0)
        if ohp <= 3 or onwd >= 2:
            if obid > 0:
                target = max(target, obid + 1.0)

    if budget < 25:
        target = min(target, budget)
    elif budget < 60 and danger < 3:
        target = min(target, 35.0)

    min_keep = 0.0
    if day < 9:
        min_keep = 12.0
    bid = min(budget - min_keep, target)
    if danger >= 3:
        bid = min(budget, max(bid, 65.0))

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
            return max(0.0, min(budget, 55.0))
        return max(0.0, min(budget, 18.0))

    prev_bids = {}
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids[agent_id] = bid

    bob_bid = prev_bids.get('Bob', 77.0)
    eric_bid = prev_bids.get('Eric', 134.0)

    alive_count = len(alive) + 1
    expected_demand_units = alive_count * WATER_REQ
    tightness = expected_demand_units / max(1.0, supply)

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if urgent:
        target = max(82.0, bob_bid + 4.0)
        if supply <= 17:
            target = max(target, 92.0)
        return max(0.0, min(budget, target))

    if tightness < 2.8 and supply >= 22:
        target = 24.0
        if pressured:
            target = 42.0
        return max(0.0, min(budget, target))

    if supply <= 17:
        if pressured:
            target = max(84.0, bob_bid + 3.0)
        else:
            target = max(76.5, bob_bid + 1.5)
        if eric_bid > 120 and hp >= 5 and no_water_days == 0:
            target = min(target, 79.0)
        return max(0.0, min(budget, target))

    if supply <= 20:
        if pressured:
            target = max(79.0, bob_bid + 2.0)
        else:
            target = max(72.0, bob_bid + 0.5)
        return max(0.0, min(budget, target))

    target = 58.0
    if pressured:
        target = 68.0
    if bob_bid < 70:
        target = max(target, bob_bid + 1.0)
    return max(0.0, min(budget, target))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    dangerous_prev.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    alive_count = len(alive)
    secure_supply = supply >= alive_count * WATER_REQ
    very_tight = supply < max(WATER_REQ, alive_count * WATER_REQ * 0.7)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    danger_prev = max(dangerous_prev) if dangerous_prev else highest_prev

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

    if day >= 8:
        urgency += 1

    if very_tight:
        urgency += 2
    elif not secure_supply:
        urgency += 1

    if secure_supply:
        base = 16.0
        if highest_prev > 0:
            base = min(base, max(10.0, avg_prev * 0.22))
    else:
        if highest_prev >= 180:
            base = 62.0 if urgency <= 2 else 96.0
        elif highest_prev >= 140:
            base = 54.0 if urgency <= 2 else 88.0
        elif highest_prev >= 90:
            base = highest_prev * 0.58 + 3.0
        elif highest_prev > 0:
            base = highest_prev + 2.5
        else:
            base = 42.0

    if urgency >= 6:
        base = max(base, danger_prev + 6.0, 98.0)
    elif urgency >= 4:
        base = max(base, danger_prev + 3.0, 72.0)
    elif urgency >= 2:
        base = max(base, min(68.0, avg_prev + 2.0 if avg_prev > 0 else 38.0))

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0:
        keep_reserve = reserve_days * 18.0
        if urgency <= 1:
            soft_cap = max(0.0, budget - keep_reserve)
        elif urgency == 2:
            soft_cap = max(0.0, budget - keep_reserve * 0.6)
        elif urgency == 3:
            soft_cap = max(0.0, budget - keep_reserve * 0.35)

    if soft_cap <= 0:
        soft_cap = min(budget, 22.0 if urgency <= 1 else 40.0)

    bid = min(base, soft_cap, budget)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, highest_prev + 8.0, 105.0))
    elif hp <= 4 or no_water_days >= 1:
        bid = min(budget, max(bid, highest_prev + 4.0, 78.0 if not secure_supply else 46.0))

    if secure_supply and urgency <= 1:
        bid = min(bid, 24.0)

    if bid < 0:
        bid = 0.0

    return float(round(min(budget, bid), 2))
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
    rich_aggressive = 0
    weak_or_dead = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 150:
                    rich_aggressive += 1
            if opp.get('budget', 0) <= 0 or opp.get('hp', 0) <= 1:
                weak_or_dead += 1
        else:
            weak_or_dead += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    tight_supply = supply <= 17
    ample_supply = supply >= 22

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

    if tight_supply:
        urgency += 2
    elif ample_supply:
        urgency -= 1

    if len(alive) <= 2:
        urgency += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    modest_prev = [b for b in prev_bids if b < 120]
    target_prev = max(modest_prev) if modest_prev else 0.0

    if urgency >= 5:
        bid = 0.92 * DAILY_SALARY
        if target_prev > 0:
            bid = max(bid, target_prev + 2.0)
    elif urgency >= 3:
        if highest_prev >= 150:
            bid = 0.58 * DAILY_SALARY if not tight_supply else 0.72 * DAILY_SALARY
        else:
            bid = max(0.52 * DAILY_SALARY, target_prev + 1.5)
    elif urgency >= 1:
        if ample_supply:
            bid = 0.28 * DAILY_SALARY
        elif highest_prev >= 150:
            bid = 0.34 * DAILY_SALARY
        else:
            bid = max(0.38 * DAILY_SALARY, target_prev + 1.0)
    else:
        if rich_aggressive >= 2:
            bid = 0.18 * DAILY_SALARY
        elif ample_supply:
            bid = 0.22 * DAILY_SALARY
        else:
            bid = 0.30 * DAILY_SALARY

    if day >= 8 and hp <= 5:
        bid = max(bid, 0.75 * DAILY_SALARY)

    if budget < 1.2 * DAILY_SALARY:
        bid = min(bid, 0.65 * DAILY_SALARY)
        if urgency <= 1:
            bid = min(bid, 0.35 * DAILY_SALARY)

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_pressure = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid > opp_pressure:
                    opp_pressure = bid

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, min(budget, 35.0))
        return max(0.0, min(budget, 18.0))

    scarcity = (MAX_SUPPLY_PLACEHOLDER := 25)
    scarcity_score = (25.0 - float(supply)) / 10.0
    if scarcity_score < 0:
        scarcity_score = 0.0
    if scarcity_score > 1:
        scarcity_score = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.55
    if no_water_days >= 2:
        danger += 1.0
    elif no_water_days >= 1:
        danger += 0.5

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 70.0
        avg_prev = 70.0

    if hp <= 2 or no_water_days >= 2:
        target = max(0.95 * DAILY_SALARY, highest_prev + 3.0)
    elif scarcity_score >= 0.8:
        target = max(0.82 * DAILY_SALARY, avg_prev * 0.92, highest_prev + 1.5)
    elif scarcity_score >= 0.5:
        if danger > 0.4:
            target = max(0.72 * DAILY_SALARY, avg_prev * 0.82)
        else:
            target = max(0.52 * DAILY_SALARY, avg_prev * 0.62)
    else:
        if danger > 0.7:
            target = max(0.62 * DAILY_SALARY, avg_prev * 0.72)
        else:
            target = max(0.28 * DAILY_SALARY, avg_prev * 0.38)

    remaining_days = max(1, 10 - int(day) + 1)
    reserve_floor = DAILY_SALARY * 0.45 * remaining_days
    if budget < reserve_floor and danger < 1.0:
        target *= 0.82

    if budget <= DAILY_SALARY * 0.6 and danger < 1.0:
        target = min(target, budget * 0.7)

    if hp >= 7 and no_water_days == 0 and scarcity_score < 0.4 and highest_prev >= 95:
        target = min(target, 24.0)

    bid = min(budget, target)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""
