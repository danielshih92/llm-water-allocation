# ============================================================
# Experiment: exp_001
# Agent: Alex
# Source: exp_001
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

    if budget <= 0:
        return 0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return min(budget, 50)
        return min(budget, 28)

    prev_bids = []
    stressed_opponents = 0
    desperate_opponents = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            stressed_opponents += 1
        if opp.get('hp', 10) <= 1 or opp.get('no_water_days', 0) >= 2:
            desperate_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

    scarcity = supply / float(WATER_REQ)

    if hp <= 2 or no_water >= 2:
        base = 66
    elif no_water >= 1:
        base = 56
    elif scarcity <= 1.15:
        base = 52
    elif scarcity <= 1.45:
        base = 42
    else:
        base = 30

    if stressed_opponents >= 2:
        base += 4
    if desperate_opponents >= 1 and hp > 2 and no_water == 0:
        base -= 3

    if highest_prev >= 60:
        if hp > 3 and no_water == 0 and scarcity > 1.3:
            bid = max(18, avg_prev * 0.55)
        else:
            bid = max(base, highest_prev + 1.5)
    elif highest_prev >= 40:
        bid = max(base, highest_prev + 1.0)
    elif highest_prev > 0:
        bid = max(base, avg_prev + 2.0)
    else:
        bid = base

    if supply >= 24 and hp > 2 and no_water == 0:
        bid -= 4
    elif supply <= 16:
        bid += 5

    if hp >= 5 and no_water == 0 and budget < DAILY_SALARY * 2:
        bid = min(bid, 44)

    bid = max(0, min(budget, bid))
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return max(0.0, min(budget, 56.0))
        return max(0.0, min(budget, 24.0))

    opp_bids = []
    urgent_opp_bids = []
    rich_pressure = 0.0
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        prev_bid = None
        if prev:
            prev_bid = prev.get('bid')
        if prev_bid is not None:
            opp_bids.append(float(prev_bid))
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                urgent_opp_bids.append(float(prev_bid))
        if opp.get('budget', 0) > budget:
            rich_pressure = max(rich_pressure, float(opp.get('budget', 0) - budget))

    highest_prev = max(opp_bids) if opp_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else highest_prev

    supply_tight = supply <= 17
    supply_loose = supply >= 22
    critical_self = (hp <= 2) or (no_water_days >= 2)
    stressed_self = (hp <= 4) or (no_water_days >= 1)

    if critical_self:
        target = max(84.0, urgent_prev + 2.0)
        if supply_tight:
            target = max(target, highest_prev + 4.0)
        return max(0.0, min(budget, target))

    if supply_loose and hp >= 6 and no_water_days == 0:
        if highest_prev >= 90.0:
            return max(0.0, min(budget, 18.0))
        return max(0.0, min(budget, 26.0))

    if stressed_self:
        target = max(62.0, urgent_prev + 1.5)
        if supply_tight:
            target = max(target, highest_prev + 2.5)
        return max(0.0, min(budget, target))

    if supply_tight:
        if highest_prev >= 85.0:
            target = highest_prev + 1.5
        else:
            target = max(58.0, highest_prev + 2.0)
        return max(0.0, min(budget, target))

    if day >= 8 and hp >= 5 and no_water_days == 0:
        return max(0.0, min(budget, 28.0))

    base = 44.0
    if highest_prev > 0:
        base = max(base, min(60.0, highest_prev - 8.0))
    if rich_pressure > 300:
        base += 3.0

    return max(0.0, min(budget, base))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_pressure = 0
    desperate_pressure = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 110:
                    rich_pressure += 1
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                    desperate_pressure += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if supply >= 23:
        scarcity = 0
    elif supply >= 20:
        scarcity = 1
    elif supply >= 17:
        scarcity = 2
    else:
        scarcity = 3

    emergency = hp <= 2 or no_water >= 2
    urgent = hp <= 4 or no_water >= 1

    if emergency:
        base = 0.92 * DAILY_SALARY
        if highest_prev > 0:
            base = max(base, min(highest_prev + 6.0, 0.98 * DAILY_SALARY))
        if scarcity >= 2:
            base += 4.0
        return float(min(budget, max(0.0, base)))

    if urgent:
        if scarcity >= 2:
            base = max(0.78 * DAILY_SALARY, min(highest_prev + 3.0, 0.9 * DAILY_SALARY))
        else:
            base = max(0.62 * DAILY_SALARY, min(avg_prev + 2.0, 0.82 * DAILY_SALARY))
        return float(min(budget, max(0.0, base)))

    if scarcity == 0:
        base = 18.0
    elif scarcity == 1:
        base = 26.0
    elif scarcity == 2:
        base = 34.0
    else:
        base = 42.0

    if highest_prev >= 130:
        base -= 8.0
    elif highest_prev >= 100:
        base -= 4.0
    elif highest_prev <= 60 and prev_bids:
        base += 6.0

    base += desperate_pressure * 2.5
    base -= rich_pressure * 2.0

    if day >= 8 and hp >= 6:
        base -= 4.0

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    cap = budget
    if budget > reserve_floor:
        cap = max(0.0, budget - reserve_floor * 0.15)

    bid = min(cap, base)
    bid = max(0.0, min(budget, bid))
    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    dangerous_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = float(prev['bid'])
            prev_bids.append(bid)
            if bid >= 120:
                dangerous_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply <= 17)
    abundant = (supply >= 22)
    urgent = (hp <= 2 or no_water_days >= 2)
    pressured = (hp <= 4 or no_water_days >= 1)

    if urgent:
        if highest_prev >= 140:
            bid = DAILY_SALARY * 1.95
        elif highest_prev >= 110:
            bid = highest_prev + 6.0
        else:
            bid = DAILY_SALARY * 1.15
        return float(min(budget, bid))

    if scarcity:
        if highest_prev >= 145:
            bid = DAILY_SALARY * 0.55 if hp >= 5 else DAILY_SALARY * 1.35
        elif highest_prev >= 120:
            bid = highest_prev + 3.0 if pressured else DAILY_SALARY * 0.6
        elif highest_prev >= 90:
            bid = highest_prev + 2.0
        else:
            bid = DAILY_SALARY * 0.82
    elif abundant:
        if dangerous_count >= 2 or avg_prev >= 120:
            bid = DAILY_SALARY * 0.22
        elif highest_prev >= 100:
            bid = DAILY_SALARY * 0.28
        else:
            bid = DAILY_SALARY * 0.38
    else:
        if highest_prev >= 140:
            bid = DAILY_SALARY * 0.3 if hp >= 5 else DAILY_SALARY * 1.1
        elif highest_prev >= 115:
            bid = DAILY_SALARY * 0.45 if hp >= 5 else highest_prev + 3.0
        elif highest_prev >= 85:
            bid = highest_prev + 1.5
        else:
            bid = DAILY_SALARY * 0.62

    if day >= 8 and hp >= 6 and budget < DAILY_SALARY * 3:
        bid *= 0.85
    if day >= 8 and pressured:
        bid *= 1.1

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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = 0
    weak_rivals = 0
    rich_rivals = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) < DAILY_SALARY * 2 and opp.get('hp', 0) <= 5:
                weak_rivals += 1
            if opp.get('budget', 0) > budget:
                rich_rivals += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    if bid >= 90:
                        strong_prev += 1

    if not alive:
        return max(0, min(budget, 10.0))

    slots = max(1, int(supply // WATER_REQ))
    pressure = float(len(alive) + 1) / float(slots)

    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        top_prev = 0.0
        avg_prev = 0.0

    if hp <= 2 or no_water >= 2:
        bid = max(95.0, top_prev + 3.0)
    elif hp <= 4 or no_water >= 1:
        bid = max(72.0, avg_prev + 2.0)
    else:
        if slots >= 2:
            bid = 26.0
            if strong_prev >= 2:
                bid = 34.0
            if weak_rivals >= 2:
                bid -= 4.0
        else:
            bid = 58.0
            if top_prev >= 110:
                bid = 74.0
            elif top_prev >= 90:
                bid = 66.0
            if pressure > 3.5:
                bid += 6.0

    if budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.55)
    elif budget < DAILY_SALARY * 3 and hp > 4:
        bid = min(bid, budget * 0.7)

    if rich_rivals >= 2 and hp > 4 and slots >= 2:
        bid = min(bid, 24.0)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
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

    if budget <= 0:
        return 0.0

    alive = {k: v for k, v in opponents_status.items() if v.get('alive')}
    if not alive:
        return float(min(budget, 20.0))

    cindy = opponents_status.get('Cindy')
    main_opp = None
    if cindy and cindy.get('alive'):
        main_opp = cindy
    else:
        best_budget = -1
        for opp in alive.values():
            if opp.get('budget', 0) > best_budget:
                best_budget = opp.get('budget', 0)
                main_opp = opp

    prev_bid = None
    opp_hp = 5
    opp_budget = 0
    opp_req = WATER_REQ
    if main_opp is not None:
        opp_hp = main_opp.get('hp', 5)
        opp_budget = main_opp.get('budget', 0)
        opp_req = main_opp.get('water_requirement', WATER_REQ)
        prev = main_opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            prev_bid = float(prev.get('bid'))

    units = supply / float(WATER_REQ)
    scarcity = units < 2.0
    very_tight = supply <= 18.0
    abundant = supply >= 24.0

    critical_me = hp <= 2 or no_water_days >= 1
    critical_opp = opp_hp <= 2 or (main_opp is not None and main_opp.get('no_water_days', 0) >= 1)

    if prev_bid is None:
        if critical_me:
            bid = 96.0
        elif scarcity:
            bid = 82.0
        else:
            bid = 48.0
    else:
        if critical_me:
            bid = max(prev_bid + 6.0, 102.0)
        elif critical_opp and not scarcity:
            bid = max(18.0, prev_bid * 0.45)
        elif very_tight:
            bid = prev_bid + 4.0
        elif scarcity:
            bid = prev_bid + 2.0
        elif abundant:
            bid = max(22.0, prev_bid * 0.38)
        else:
            bid = max(35.0, prev_bid * 0.58)

    if day >= 8:
        bid += 8.0
    if day >= 9 and hp <= 3:
        bid += 10.0

    if opp_budget < bid and opp_budget > 0:
        bid = max(opp_budget + 1.0, bid)

    reserve = 0.0
    if day <= 7:
        reserve = max(0.0, (10 - day) * 8.0)
    max_affordable = max(0.0, budget - reserve)
    if critical_me:
        max_affordable = budget

    bid = min(bid, budget)
    if max_affordable > 0:
        bid = min(bid, max_affordable)

    if critical_me and bid < 85.0:
        bid = min(budget, 85.0)
    if scarcity and bid < 55.0 and not critical_opp:
        bid = min(budget, 55.0)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_tight = (supply <= 17)
    supply_loose = (supply >= 22)

    if hp <= 2 or no_water_days >= 2:
        bid = max(78.0, highest_prev + 4.0)
    elif hp <= 4 or no_water_days >= 1:
        if supply_tight:
            bid = max(68.0, highest_prev * 0.78 + 3.0)
        else:
            bid = max(58.0, avg_prev * 0.62 + 2.0)
    else:
        if supply_loose:
            bid = 16.0 + 2.0 * rich_opp
        elif supply_tight:
            if highest_prev >= 110:
                bid = 28.0
            else:
                bid = max(32.0, avg_prev * 0.42)
        else:
            if urgent_opp >= 2:
                bid = max(36.0, avg_prev * 0.45)
            elif highest_prev >= 120:
                bid = 24.0
            elif highest_prev >= 90:
                bid = 30.0
            else:
                bid = max(26.0, avg_prev * 0.38 + 1.0)

    if day >= 8:
        if hp >= 6 and no_water_days == 0:
            bid *= 0.9
        else:
            bid *= 1.08

    reserve = 0.0
    if hp <= 4:
        reserve = DAILY_SALARY * 0.6
    elif hp <= 2:
        reserve = DAILY_SALARY * 0.3

    max_spend = max(0.0, budget - reserve)
    if max_spend <= 0:
        max_spend = budget

    bid = min(bid, max_spend)
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
        return min(budget, 18.0)

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    pressure = 0.0

    for oid, opp in alive:
        obudget = float(opp.get('budget', 0))
        ohp = float(opp.get('hp', 0))
        onwd = int(opp.get('no_water_days', 0))
        if obudget >= DAILY_SALARY * 6:
            rich_opp += 1
        if ohp <= 3 or onwd >= 2:
            urgent_opp += 1

        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            b = float(bid)
            prev_bids.append(b)
            pressure = max(pressure, b)

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    high_prev = max(prev_bids) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    critical = hp <= 2 or no_water_days >= 2
    strained = hp <= 4 or no_water_days >= 1

    if critical:
        bid = max(92.0, high_prev + 4.0, DAILY_SALARY * (1.18 + 0.12 * supply_ratio))
        return min(budget, bid)

    if strained:
        if high_prev >= 120:
            bid = 34.0 + 10.0 * supply_ratio
        else:
            bid = max(58.0 + 12.0 * supply_ratio, avg_prev + 2.5)
        return min(budget, bid)

    if high_prev >= 135:
        bid = 18.0 + 8.0 * supply_ratio
    elif high_prev >= 100:
        bid = 24.0 + 10.0 * supply_ratio
    else:
        bid = max(36.0 + 12.0 * supply_ratio, avg_prev + 1.5)

    if urgent_opp >= 2:
        bid -= 6.0
    if rich_opp >= 2 and high_prev < 100:
        bid += 6.0
    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid -= 4.0

    if bid < 0:
        bid = 0.0
    return min(budget, bid)
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    prev_need_bids = []
    max_opp_budget = 0.0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > max_opp_budget:
                max_opp_budget = opp.get('budget', 0)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    prev_need_bids.append(bid)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.2))

    slots = max(1, int(supply // WATER_REQ))
    total_alive = len(alive) + 1
    scarcity = total_alive - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(prev_need_bids) if prev_need_bids else highest_prev

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 1.05, urgent_prev + 3.0)
    elif hp <= 4 or no_water_days >= 1:
        if scarcity >= 2:
            bid = max(DAILY_SALARY * 0.92, highest_prev + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.72, highest_prev * 0.9)
    else:
        if scarcity >= 3:
            bid = max(DAILY_SALARY * 0.9, highest_prev + 1.5)
        elif scarcity >= 2:
            bid = max(DAILY_SALARY * 0.72, highest_prev * 0.82)
        elif scarcity >= 1:
            bid = max(DAILY_SALARY * 0.52, highest_prev * 0.68)
        else:
            bid = DAILY_SALARY * 0.35

    if highest_prev >= 120:
        if hp >= 5 and no_water_days == 0:
            bid = min(bid, DAILY_SALARY * 0.45)
        else:
            bid = max(bid, DAILY_SALARY * 0.88)

    if max_opp_budget < budget * 0.6 and scarcity >= 2:
        bid = max(bid, highest_prev + 1.0)

    if budget < DAILY_SALARY * 2:
        if hp >= 5 and no_water_days == 0:
            bid = min(bid, DAILY_SALARY * 0.4)
        else:
            bid = min(bid, budget)

    bid = max(0.0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    aggressive = 0
    weak_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if float(opp.get('hp', 0)) <= 3 or int(opp.get('no_water_days', 0)) >= 1:
                weak_opp += 1
            if float(opp.get('budget', 0)) >= 350:
                rich_opp += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    bid = float(bid)
                    prev_bids.append(bid)
                    if bid >= 100:
                        aggressive += 1

    if not alive:
        return min(budget, 18.0)

    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < (len(alive) + 1)
    very_tight = expected_units <= max(1.2, (len(alive) + 1) * 0.55)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 3
    elif hp <= 7:
        urgency += 1

    if no_water >= 2:
        urgency += 4
    elif no_water >= 1:
        urgency += 2

    if very_tight:
        urgency += 3
    elif scarcity:
        urgency += 1

    if day >= 8:
        urgency += 1

    base = 16.0
    if urgency <= 1:
        base = 14.0 if not scarcity else 22.0
    elif urgency == 2:
        base = 28.0 if not scarcity else 42.0
    elif urgency == 3:
        base = 48.0 if not scarcity else 66.0
    elif urgency == 4:
        base = 72.0 if not scarcity else 92.0
    elif urgency == 5:
        base = 96.0 if not scarcity else 118.0
    else:
        base = 122.0 if not scarcity else 146.0

    target = base

    if highest_prev > 0:
        if urgency >= 5:
            target = max(target, min(highest_prev + 3.0, 155.0))
        elif urgency >= 3:
            if scarcity:
                target = max(target, min(avg_prev + 4.0, highest_prev * 0.92 + 2.0, 128.0))
            else:
                target = max(target, min(avg_prev * 0.72, 82.0))
        else:
            if aggressive >= 2 or rich_opp >= 2:
                target = min(target, 24.0 if not scarcity else 36.0)
            else:
                target = max(target, min(avg_prev * 0.55, 44.0))

    if weak_opp >= 2 and urgency <= 3:
        target = min(target, 26.0 if not scarcity else 38.0)

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left > 0:
        reserve_floor = min(budget * 0.55, days_left * 18.0)

    cap = budget - reserve_floor
    if urgency >= 5:
        cap = budget
    elif urgency == 4:
        cap = max(cap, budget * 0.55)
    else:
        cap = max(cap, budget * 0.32)

    if hp <= 2 or no_water >= 2:
        cap = budget

    bid = min(target, cap, budget)
    if bid < 0:
        bid = 0.0

    if budget < 25:
        bid = min(budget, max(bid, budget * 0.7 if urgency >= 4 else budget * 0.35))

    return float(round(bid, 2))
"""
