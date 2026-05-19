# ============================================================
# Experiment: exp_059
# Agent: Alex
# Source: exp_059
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
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 45)
        if supply >= 22:
            return min(budget, 12)
        return min(budget, 22)

    prev_bids = []
    desperate_count = 0
    rich_count = 0
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
        if opp.get('budget', 0) >= budget:
            rich_count += 1

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    if hp <= 1:
        base = 0.98 * DAILY_SALARY
    elif hp <= 2 or no_water_days >= 2:
        base = 0.9 * DAILY_SALARY
    elif no_water_days >= 1:
        base = 0.78 * DAILY_SALARY
    else:
        base = 0.42 * DAILY_SALARY + 0.22 * DAILY_SALARY * scarcity

    if supply >= 23:
        base -= 10
    elif supply <= 17:
        base += 8

    if highest_prev > 0:
        target = highest_prev + 1.5
        if hp >= 4 and no_water_days == 0 and highest_prev >= 0.88 * DAILY_SALARY and supply >= 20:
            bid = min(base, 0.38 * DAILY_SALARY)
        else:
            bid = max(base, target)
            if highest_prev < 0.45 * DAILY_SALARY and supply >= 21:
                bid = max(base, avg_prev + 1.0)
    else:
        if day <= 2:
            bid = base + 3
        else:
            bid = base

    if desperate_count >= 2:
        bid += 4
    if rich_count >= max(1, len(alive_opponents) // 2):
        bid += 2

    if budget < DAILY_SALARY:
        bid = min(bid, max(12, budget * 0.72))

    if hp >= 4 and no_water_days == 0 and supply >= 22 and highest_prev >= 0.9 * DAILY_SALARY:
        bid = min(bid, 20)

    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget

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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 100 and opp.get('budget', 0) >= 150:
                    rich_aggressive += 1

    if not alive_opponents:
        return max(0.0, min(float(budget), 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = int(supply / WATER_REQ)
    if units < 1:
        units = 1
    competitors = len(alive_opponents) + 1
    scarcity = competitors - units

    critical_self = hp <= 3 or no_water_days >= 2
    pressured_self = hp <= 5 or no_water_days >= 1

    if critical_self:
        target = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
        if scarcity >= 3:
            target = max(target, 1.18 * DAILY_SALARY)
        return max(0.0, min(float(budget), float(target)))

    if supply >= 24 and hp >= 7 and no_water_days == 0:
        target = 12.0
        if urgent_count >= 2:
            target = 20.0
        return max(0.0, min(float(budget), float(target)))

    if supply <= 16:
        target = highest_prev + 2.5 if highest_prev > 0 else 88.0
        if rich_aggressive >= 2:
            target += 8.0
        if pressured_self:
            target += 10.0
        return max(0.0, min(float(budget), float(target)))

    if scarcity >= 3:
        target = max(82.0, highest_prev + 2.0)
        if pressured_self:
            target += 8.0
        return max(0.0, min(float(budget), float(target)))

    if scarcity == 2:
        if highest_prev >= 110:
            target = 46.0 if not pressured_self else 92.0
        else:
            target = max(58.0, avg_prev + 1.5)
        return max(0.0, min(float(budget), float(target)))

    if scarcity == 1:
        if pressured_self:
            target = max(60.0, highest_prev * 0.72)
        else:
            target = 34.0 if highest_prev >= 100 else 42.0
        return max(0.0, min(float(budget), float(target)))

    target = 18.0
    if day >= 8 and hp >= 6:
        target = 10.0
    if pressured_self:
        target = 36.0
    return max(0.0, min(float(budget), float(target)))
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
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return min(budget, 20.0)

    strongest_name = None
    strongest_score = -1.0
    strongest_prev_bid = 0.0
    strongest_budget = 0.0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is None:
            prev_bid = 0.0
        opp_budget = opp.get('budget', 0.0)
        score = prev_bid + 0.15 * opp_budget
        if score > strongest_score:
            strongest_score = score
            strongest_name = agent_id
            strongest_prev_bid = prev_bid
            strongest_budget = opp_budget

    competitors = len(alive) + 1
    units = supply / float(WATER_REQ)
    tight_supply = units < competitors
    very_tight = units < max(1.5, competitors - 1)

    emergency = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    bid = 0.0

    if strongest_name == 'Bob':
        if emergency:
            bid = max(63.0, strongest_prev_bid + 2.0)
        elif very_tight:
            bid = max(60.0, strongest_prev_bid + 1.2)
        elif tight_supply:
            bid = max(54.0, strongest_prev_bid + 0.8)
        else:
            bid = 41.0 if not pressured else 52.0
    else:
        if emergency:
            bid = 58.0
        elif tight_supply:
            bid = 44.0
        else:
            bid = 26.0

    if strongest_budget < 35:
        bid = min(bid, strongest_prev_bid + 0.5 if strongest_prev_bid > 0 else 28.0)

    if budget < bid:
        if emergency:
            bid = budget
        else:
            bid = min(budget, max(0.0, budget * 0.72))

    if not emergency and budget < DAILY_SALARY * 2:
        bid = min(bid, max(18.0, budget * 0.45))

    if hp >= 8 and not tight_supply:
        bid = min(bid, 36.0)

    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget
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
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    prev_bids = []
    rich_threat = 0
    urgent_opp = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('budget', 0) >= 120:
            rich_threat += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22
    my_urgent = hp <= 2 or no_water_days >= 1
    my_medium = hp <= 4

    if my_urgent:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 4.0)
        if tight_supply:
            bid += 10.0
        return float(min(budget, bid))

    if tight_supply:
        base = max(DAILY_SALARY * 0.62, avg_prev * 0.72)
        if highest_prev > 0:
            base = max(base, highest_prev * 0.78)
        base += rich_threat * 3.0 + urgent_opp * 2.0
        if my_medium:
            base += 8.0
        return float(min(budget, base))

    if loose_supply:
        base = DAILY_SALARY * 0.22
        if highest_prev < 40:
            base = max(base, highest_prev * 0.55)
        if day >= 8 and hp >= 5:
            base *= 0.8
        return float(min(budget, base))

    base = DAILY_SALARY * 0.4
    if highest_prev >= 150:
        base = DAILY_SALARY * 0.3
    elif highest_prev >= 100:
        base = DAILY_SALARY * 0.36
    elif highest_prev > 0:
        base = max(base, min(highest_prev * 0.6, DAILY_SALARY * 0.55))

    if my_medium:
        base += 6.0
    if rich_threat >= 2:
        base += 4.0
    if day >= 9 and hp >= 6:
        base *= 0.9

    return float(min(budget, base))
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

    day = day_context['day']
    supply = day_context['supply']
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
            base = DAILY_SALARY * 0.8
        return float(min(budget, base))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 2.5 * DAILY_SALARY:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = 1.0 - max(0.0, min(1.0, supply_ratio))

    survival_pressure = 0.0
    if hp <= 2:
        survival_pressure += 0.55
    elif hp <= 4:
        survival_pressure += 0.28
    if no_water_days >= 2:
        survival_pressure += 0.4
    elif no_water_days == 1:
        survival_pressure += 0.15

    market_pressure = 0.0
    if highest_prev >= 110:
        market_pressure = 0.55
    elif highest_prev >= 85:
        market_pressure = 0.4
    elif highest_prev >= 60:
        market_pressure = 0.25
    elif highest_prev >= 35:
        market_pressure = 0.12

    opp_pressure = min(0.2, urgent_opp * 0.06 + rich_opp * 0.03)

    base = DAILY_SALARY * (0.28 + 0.42 * scarcity + survival_pressure + market_pressure + opp_pressure)

    if prev_bids:
        if scarcity >= 0.55 or hp <= 3 or no_water_days >= 1:
            target = max(base, highest_prev + 2.0)
        else:
            target = max(base, avg_prev * 0.82 + 1.0)
    else:
        target = base

    if supply >= 23 and hp >= 5 and no_water_days == 0:
        target *= 0.72
    elif supply <= 17:
        target *= 1.18

    if day >= 8:
        target *= 1.08
    if day == 10:
        target *= 1.12

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if hp >= 4 and no_water_days == 0:
        reserve_floor = min(budget * 0.5, days_left * DAILY_SALARY * 0.22)

    bid = min(budget, target)
    if budget > reserve_floor:
        bid = min(bid, budget)
    bid = max(0.0, bid)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, highest_prev + 4.0 if highest_prev > 0 else DAILY_SALARY * 0.92))

    return float(round(min(budget, bid), 2))
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 90:
                    strong_prev.append(bid)

    if not alive:
        return max(0.0, min(budget, 18.0))

    competitors = len(alive) + 1
    tight_supply = supply <= 17
    ample_supply = supply >= 22

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

    urgent = hp <= 3 or no_water >= 2
    pressured = hp <= 5 or no_water >= 1

    if urgent:
        if tight_supply:
            bid = max(88.0, highest_prev + 3.0)
        else:
            bid = max(72.0, second_prev + 2.0)
        return max(0.0, min(budget, bid))

    if ample_supply and hp >= 7 and no_water == 0:
        bid = 22.0 if highest_prev >= 100 else 18.0
        return max(0.0, min(budget, bid))

    if tight_supply:
        if highest_prev >= 120:
            bid = 54.0 if hp >= 7 else 82.0
        elif highest_prev >= 100:
            bid = 66.0 if hp >= 7 else 86.0
        else:
            bid = max(60.0, highest_prev + 2.0)
    else:
        if highest_prev >= 120:
            bid = 36.0 if hp >= 7 else 74.0
        elif highest_prev >= 100:
            bid = 44.0 if hp >= 7 else 68.0
        elif highest_prev >= 80:
            bid = max(46.0, second_prev + 1.5)
        else:
            bid = 42.0

    if competitors <= 2:
        bid *= 0.9
    if day >= 8 and hp >= 6:
        bid *= 0.92
    if pressured and bid < 58.0:
        bid = 58.0

    return max(0.0, min(budget, bid))
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
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 4:
                    dangerous_prev.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    max_danger = max(dangerous_prev) if dangerous_prev else max_prev

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    critical_me = hp <= 3 or no_water_days >= 2
    pressured_me = hp <= 5 or no_water_days >= 1

    if critical_me:
        target = max(90.0, max_danger + 3.0)
    elif tight_supply:
        target = max(72.0, max_danger + 2.0)
    elif pressured_me:
        target = max(54.0, min(max_prev * 0.7 + 8.0, max_prev + 1.5))
    elif medium_supply:
        if max_prev >= 120.0:
            target = 34.0
        else:
            target = max(38.0, min(60.0, max_prev * 0.55 + 6.0))
    else:
        if max_prev >= 120.0:
            target = 22.0
        elif max_prev >= 80.0:
            target = 28.0
        else:
            target = max(24.0, max_prev * 0.45 + 4.0)

    if day >= 8:
        target += 8.0
    elif day >= 6 and pressured_me:
        target += 5.0

    reserve = 0.0
    if hp > 5 and no_water_days == 0:
        reserve = 20.0
    elif hp > 3:
        reserve = 10.0

    affordable = max(0.0, budget - reserve)
    bid = min(target, affordable if affordable > 0 else budget)

    if pressured_me and bid < 35.0 and budget >= 35.0:
        bid = 35.0
    if critical_me and bid < 60.0 and budget >= 60.0:
        bid = 60.0

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if float(opp.get('budget', 0)) > budget:
                rich_opp += 1
            if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0)) <= 4:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    competitors = len(alive) + 1
    scarcity = competitors - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    my_urgent = 0
    if hp <= 3 or no_water_days >= 1:
        my_urgent = 2
    elif hp <= 5:
        my_urgent = 1

    if my_urgent >= 2:
        target = max(62.0, highest_prev + 2.0, avg_prev + 8.0)
    elif scarcity >= 3:
        target = max(52.0, avg_prev + 4.0, highest_prev * 0.72)
    elif scarcity >= 2:
        target = max(41.0, avg_prev + 2.0, highest_prev * 0.58)
    elif scarcity >= 1:
        target = max(29.0, avg_prev * 0.9, highest_prev * 0.42)
    else:
        target = 18.0 + 2.0 * urgent_opp

    if rich_opp >= 2:
        target -= 4.0
    if day >= 8 and hp >= 6 and no_water_days == 0:
        target -= 3.0
    if supply >= 24:
        target -= 4.0
    elif supply <= 16:
        target += 6.0

    reserve_days = max(1, 11 - day)
    soft_cap = budget / reserve_days + DAILY_SALARY * 0.35
    if my_urgent == 0:
        target = min(target, soft_cap)
    else:
        target = min(target, max(soft_cap, 66.0))

    target = max(8.0, target)
    bid = min(budget, target)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_bids = []
    weak_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_hp = opp.get('hp', 0)
            opp_budget = opp.get('budget', 0)
            opp_nowater = opp.get('no_water_days', 0)
            if opp_hp <= 2 or opp_budget < 40 or opp_nowater >= 2:
                weak_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp_budget >= 60 and opp_hp > 2:
                    dangerous_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    danger_prev = max(dangerous_bids) if dangerous_bids else high_prev

    scarcity = (supply <= 17)
    medium_tight = (supply <= 19)
    urgent = (hp <= 2 or no_water >= 2)
    pressured = (hp <= 4 or no_water >= 1)
    endgame = (day >= 8)

    if urgent:
        target = max(92.0, danger_prev + 3.0)
        if scarcity:
            target = max(target, 118.0)
        if endgame:
            target += 6.0
        return float(min(budget, target))

    if scarcity:
        if danger_prev >= 120:
            target = danger_prev + 2.5
        elif danger_prev >= 95:
            target = danger_prev + 3.5
        else:
            target = 104.0
        if pressured:
            target += 6.0
        if endgame:
            target += 4.0
        return float(min(budget, target))

    if medium_tight:
        if weak_count >= 2 and hp > 4:
            target = 54.0
        else:
            if danger_prev >= 115:
                target = 86.0
            elif danger_prev >= 90:
                target = danger_prev - 8.0
            else:
                target = 72.0
            if pressured:
                target += 8.0
        return float(min(budget, target))

    target = 34.0
    if high_prev >= 120:
        target = 42.0
    elif high_prev >= 95:
        target = 38.0
    if pressured:
        target += 10.0
    if endgame and hp <= 5:
        target += 8.0

    affordable_floor = 12.0
    if budget < target and budget > affordable_floor:
        target = max(affordable_floor, budget * 0.72)

    return float(min(budget, target))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    threat_bids = []
    desperate_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) > 2 and opp.get('budget', 0) > DAILY_SALARY * 0.8:
                    threat_bids.append(float(bid))

    if not alive:
        return float(min(budget, 1.0))

    competitors = 1 + len(alive)
    ample_supply = supply >= competitors * WATER_REQ
    very_tight = supply <= WATER_REQ * 1.35
    tight = supply <= WATER_REQ * 1.7

    highest_prev = max(prev_bids) if prev_bids else 0.0
    core_threat = max(threat_bids) if threat_bids else highest_prev

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
    if day >= 8:
        urgency += 1

    if ample_supply and urgency == 0:
        base = 6.0
    elif ample_supply:
        base = 14.0 + 6.0 * urgency
    elif very_tight:
        base = max(48.0, core_threat + 6.0)
    elif tight:
        base = max(34.0, core_threat + 3.0)
    else:
        base = max(20.0, core_threat * 0.72)

    if desperate_count >= 2 and not ample_supply:
        base += 8.0
    elif desperate_count == 0 and ample_supply:
        base -= 3.0

    if urgency >= 5:
        base = max(base, 66.0)
    elif urgency >= 3:
        base = max(base, 52.0)
    elif urgency >= 2:
        base = max(base, 38.0)

    reserve_days = max(0, 10 - day)
    soft_cap = budget if reserve_days <= 1 else max(0.0, budget - reserve_days * 6.0)
    bid = min(base, budget)
    if soft_cap > 0:
        bid = min(bid, max(base * 0.9, soft_cap))

    if hp <= 1 or no_water >= 2:
        bid = min(budget, max(bid, core_threat + 10.0, 69.0))

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""
