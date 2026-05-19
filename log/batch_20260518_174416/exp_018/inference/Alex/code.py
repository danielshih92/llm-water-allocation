# ============================================================
# Experiment: exp_018
# Agent: Alex
# Source: exp_018
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            desperate_opp += 1
        if opp.get('budget', 0) >= budget * 1.2:
            rich_opp += 1

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return min(budget, max(0, base))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days >= 1:
        urgency += 0.45
    urgency += scarcity * 0.35

    budget_ratio = budget / float(max(1, DAILY_SALARY * 4))
    if budget_ratio < 0.75:
        urgency += 0.15

    pressure = 0.0
    if highest_prev >= DAILY_SALARY * 0.9:
        pressure = 0.9
    elif highest_prev >= DAILY_SALARY * 0.7:
        pressure = 0.65
    elif highest_prev >= DAILY_SALARY * 0.45:
        pressure = 0.4
    elif highest_prev > 0:
        pressure = 0.2

    pressure += min(0.2, desperate_opp * 0.05)
    pressure += min(0.15, rich_opp * 0.05)

    target = DAILY_SALARY * (0.38 + 0.42 * urgency + 0.28 * pressure)

    if prev_bids:
        if highest_prev <= DAILY_SALARY * 0.8:
            target = max(target, highest_prev + 1.25)
        elif hp <= 3 or no_water_days >= 1:
            target = max(target, highest_prev + 0.75)
        else:
            target = min(target, highest_prev * 0.82)

    if supply <= WATER_REQ:
        target += 6
    elif supply <= WATER_REQ * 1.4:
        target += 3

    if hp >= 7 and no_water_days == 0 and highest_prev >= DAILY_SALARY * 0.9:
        target *= 0.72

    reserve_floor = 0
    if hp > 3 and no_water_days == 0:
        reserve_floor = DAILY_SALARY * 0.18
    max_affordable = max(0, budget - reserve_floor)

    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget
        target = max(target, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.72)

    bid = min(max_affordable, target)
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
    supply = day_context['supply']
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
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 40.0))
        return float(min(budget, 18.0))

    prev_bids = []
    urgent_prev_bids = []
    max_req = WATER_REQ
    for opp in alive_opponents:
        req = opp.get('water_requirement', WATER_REQ)
        if req > max_req:
            max_req = req
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_high = max(urgent_prev_bids) if urgent_prev_bids else highest_prev

    tight_supply = supply <= float(WATER_REQ + max_req)
    very_tight = supply <= float(WATER_REQ)

    base = 22.0
    if highest_prev > 0:
        base = max(base, highest_prev + 2.0)

    if hp <= 2 or no_water_days >= 1:
        bid = max(base, urgent_high + 4.0, 92.0)
    elif hp <= 4:
        bid = max(base, 72.0 if tight_supply else 58.0)
    else:
        if very_tight:
            bid = max(base, 84.0)
        elif tight_supply:
            bid = max(base, 64.0)
        else:
            bid = max(28.0, min(52.0, highest_prev * 0.72 if highest_prev > 0 else 36.0))

    if budget < bid:
        if hp <= 2 or no_water_days >= 1:
            return float(budget)
        return float(max(0.0, budget))

    return float(min(budget, bid))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = 0.0
    cindy_prev = 0.0
    eric_prev = 0.0
    urgent_opp = 0
    rich_threat = 0
    weak_or_broke = 0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            if bid > highest_prev:
                highest_prev = bid
            if agent_id == 'Cindy':
                cindy_prev = bid
            if agent_id == 'Eric':
                eric_prev = bid
        if opp.get('budget', 0) <= 5 or opp.get('hp', 0) <= 1:
            weak_or_broke += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 2:
            urgent_opp += 1
        if opp.get('budget', 0) >= 500 and opp.get('hp', 0) >= 5:
            rich_threat += 1

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    need = 0.0
    if hp <= 2:
        need += 40.0
    elif hp <= 4:
        need += 24.0
    else:
        need += 8.0

    need += min(20.0, no_water_days * 10.0)
    need += supply_pressure * 18.0
    need += min(18.0, urgent_opp * 4.0)

    market = 0.0
    if cindy_prev > 0:
        market = max(market, cindy_prev * 0.78)
    if eric_prev > 0:
        market = max(market, eric_prev * 0.72)
    if highest_prev > 0:
        market = max(market, highest_prev * 0.68)

    base = 22.0 + need
    bid = max(base, market + 2.0)

    if rich_threat >= 1 and supply <= 18:
        bid += 8.0
    if weak_or_broke >= 2 and hp >= 5 and supply >= 20:
        bid -= 10.0
    if day >= 8:
        bid += 8.0

    reserve_target = max(0.0, (10 - day) * 8.0)
    cap = budget - reserve_target
    if hp <= 2 or no_water_days >= 2:
        cap = budget
    elif hp <= 4:
        cap = max(cap, budget * 0.65)
    else:
        cap = max(cap, budget * 0.45)

    if supply >= 23 and hp >= 5 and no_water_days == 0:
        bid = min(bid, 28.0)
    if supply <= 16:
        bid += 10.0

    bid = min(bid, cap)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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
            return float(min(budget, DAILY_SALARY * 0.85))
        return float(min(budget, DAILY_SALARY * 0.35))

    yesterday_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev.get('bid', 0.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    my_urgent = hp <= 2 or no_water_days >= 1

    base = DAILY_SALARY * 0.42

    if slots >= 2:
        base = DAILY_SALARY * 0.34
    else:
        base = DAILY_SALARY * 0.78

    if my_urgent:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.62)

    if urgent_opp > 0 and slots == 1:
        base = max(base, DAILY_SALARY * 0.88)
    elif urgent_opp > 0:
        base = max(base, DAILY_SALARY * 0.48)

    if rich_opp >= 2 and slots == 1:
        base = max(base, DAILY_SALARY * 0.92)

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        moderate_prev = 0.0
        for b in yesterday_bids:
            if b <= DAILY_SALARY * 1.05 and b > moderate_prev:
                moderate_prev = b

        if highest_prev >= 120:
            if my_urgent:
                base = max(base, DAILY_SALARY * 0.97)
            else:
                base = min(base, DAILY_SALARY * 0.5)
        elif highest_prev >= DAILY_SALARY * 0.85:
            if my_urgent or slots == 1:
                base = max(base, min(DAILY_SALARY * 0.96, highest_prev + 2.0))
            else:
                base = max(base, DAILY_SALARY * 0.52)
        elif moderate_prev > 0:
            target = moderate_prev + 1.5
            if slots >= 2 and not my_urgent:
                target = moderate_prev + 0.75
            base = max(base, target)

    reserve = 0.0
    if hp >= 6 and no_water_days == 0:
        reserve = DAILY_SALARY * 0.15
    elif hp >= 4:
        reserve = DAILY_SALARY * 0.08

    max_affordable = budget - reserve
    if my_urgent:
        max_affordable = budget

    if max_affordable < 0:
        max_affordable = 0.0

    bid = min(base, max_affordable)

    if my_urgent and bid < min(budget, DAILY_SALARY * 0.85):
        bid = min(budget, DAILY_SALARY * 0.85)

    if bid < 0:
        bid = 0.0

    return float(round(min(budget, bid), 2))
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
    fixed_high = 0
    low_competitors = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 100:
                    fixed_high += 1
                if float(bid) <= 20:
                    low_competitors += 1

    if not alive_opponents:
        return float(min(budget, 10))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    positive_prev = [b for b in prev_bids if b > 0]
    low_anchor = min(positive_prev) if positive_prev else 15.0

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
        urgency += 1

    if supply <= WATER_REQ:
        urgency += 2
    elif supply <= WATER_REQ + 3:
        urgency += 1

    if day >= 8:
        urgency += 1

    affordable_safe = min(budget, DAILY_SALARY * 0.95)
    affordable_mid = min(budget, DAILY_SALARY * 0.55)

    if urgency >= 5:
        bid = affordable_safe
    elif urgency >= 3:
        bid = min(budget, max(30.0, low_anchor + 3.0, min(55.0, highest_prev + 1.0 if highest_prev < 60 else 45.0)))
    else:
        if fixed_high >= 1 and hp > 4 and no_water_days == 0:
            bid = min(budget, max(12.0, low_anchor + 1.0))
        elif highest_prev <= 20:
            bid = min(budget, max(16.0, highest_prev + 1.0))
        else:
            bid = affordable_mid

    if budget < 20:
        bid = min(bid, budget)

    if hp <= 3 and bid < 40:
        bid = min(budget, 40.0)

    if supply >= 22 and urgency <= 1:
        bid = min(bid, 18.0)

    return float(max(0.0, min(budget, bid)))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_aggressive = 0
    moderate_pressure = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 100 and opp.get('budget', 0) > 150:
                    rich_aggressive += 1
                if 20 <= bid < 100:
                    moderate_pressure += 1

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    low_supply = supply <= 17
    very_low_supply = supply <= 15

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water >= 2:
        danger += 2
    elif no_water >= 1:
        danger += 1
    if low_supply:
        danger += 1
    if very_low_supply:
        danger += 1

    if danger >= 4:
        bid = 66.0
    elif danger >= 3:
        bid = 58.0
    elif danger >= 2:
        bid = 46.0
    else:
        if rich_aggressive >= 2 and hp >= 6 and no_water == 0:
            bid = 8.0 if supply >= 20 else 12.0
        elif highest_prev >= 100:
            bid = 14.0 if supply >= 19 else 20.0
        elif moderate_pressure > 0:
            bid = min(42.0, max(24.0, highest_prev + 2.0))
        else:
            bid = 18.0 if supply >= 20 else 24.0

    if hp <= 2 or no_water >= 2:
        bid = max(bid, 64.0)

    if budget <= 0:
        return 0.0
    return float(min(budget, bid))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    strong_prev = []
    moderate_prev = []
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 90:
                strong_prev.append(float(bid))
            elif float(bid) >= 40:
                moderate_prev.append(float(bid))

    max_prev = max(prev_bids) if prev_bids else 0.0
    max_moderate = max(moderate_prev) if moderate_prev else 0.0
    min_strong = min(strong_prev) if strong_prev else 9999.0

    scarcity = 1.0 - ((float(supply) - 15.0) / 10.0)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.6
    elif hp <= 6:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.45

    urgency += scarcity * 0.55

    if urgency >= 1.6:
        bid = max(DAILY_SALARY * 0.95, max_moderate + 6.0)
        if min_strong < 9999.0:
            bid = max(bid, min_strong + 1.0)
    elif urgency >= 1.0:
        anchor = max(42.0, max_moderate + 2.5)
        if scarcity > 0.7:
            anchor += 8.0
        bid = anchor
    elif urgency >= 0.5:
        if supply >= 22:
            bid = 18.0
        elif supply >= 19:
            bid = 28.0
        else:
            bid = max(34.0, max_moderate)
    else:
        if supply >= 22:
            bid = 8.0
        elif supply >= 20:
            bid = 15.0
        else:
            bid = 24.0

    if max_prev >= 120 and urgency < 1.6:
        bid = min(bid, 36.0)

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.72)
    elif budget < DAILY_SALARY * 2.0:
        bid = min(bid, budget * 0.82)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    if day >= 8 and hp >= 7 and supply >= 20:
        bid = min(bid, 20.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        base = 18.0
        if no_water >= 2 or hp <= 4:
            base = 42.0
        elif supply <= 17:
            base = 28.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    strong_pressure = 0
    weak_or_broke = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                b = float(bid)
                prev_bids.append(b)
                if b >= 70:
                    strong_pressure += 1
                if b <= 5:
                    weak_or_broke += 1
            except Exception:
                pass
        if float(opp.get('budget', 0)) < 25:
            weak_or_broke += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0
    if no_water >= 2 or hp <= 3:
        urgency = 3
    elif no_water == 1 or hp <= 6:
        urgency = 2
    elif hp <= 8:
        urgency = 1

    reserve_target = max(0.0, (10 - day) * 8.0)
    spendable = max(0.0, budget - reserve_target)

    if urgency == 3:
        target = max(62.0, highest_prev + 3.0)
        if supply <= 17:
            target = max(target, 78.0)
        return float(max(0.0, min(budget, target)))

    if urgency == 2:
        target = 34.0 + 18.0 * scarcity
        if highest_prev > 0:
            target = max(target, min(highest_prev + 1.5, 72.0))
        if strong_pressure >= 2 and supply <= 18:
            target = max(target, 58.0)
        return float(max(0.0, min(budget, target)))

    target = 16.0 + 12.0 * scarcity
    if weak_or_broke >= len(alive):
        target = min(target, 14.0)
    elif highest_prev >= 75.0:
        target = min(target, 18.0)
    elif highest_prev >= 45.0:
        target = max(target, avg_prev * 0.55)
    else:
        target = max(target, avg_prev * 0.8 if avg_prev > 0 else target)

    if supply <= 16:
        target += 6.0
    elif supply >= 23:
        target -= 3.0

    if spendable < target and urgency == 0:
        target = min(target, max(10.0, spendable * 0.7))

    target = max(0.0, min(budget, target))
    return float(target)
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

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        if opp.get('budget', 0) >= 200:
            rich_opp_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgent = (hp <= 2) or (no_water_days >= 1)
    my_risky = (hp <= 4)

    if my_urgent:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
        if budget < target:
            target = budget
        return float(max(0.0, min(budget, target)))

    if supply >= 23:
        base = DAILY_SALARY * 0.22
    elif supply >= 20:
        base = DAILY_SALARY * 0.34
    elif supply >= 17:
        base = DAILY_SALARY * 0.5
    else:
        base = DAILY_SALARY * 0.68

    if highest_prev >= 170:
        pressure_bid = highest_prev + 1.5
    elif highest_prev >= 140:
        pressure_bid = highest_prev + 2.0
    elif highest_prev >= 100:
        pressure_bid = max(avg_prev + 2.0, highest_prev * 0.92)
    elif highest_prev > 0:
        pressure_bid = max(base, highest_prev + 1.0)
    else:
        pressure_bid = base

    bid = base

    if supply <= 17:
        bid = max(bid, pressure_bid)
    elif supply <= 19 and (urgent_opp_count >= 2 or my_risky):
        bid = max(bid, min(pressure_bid, DAILY_SALARY * 0.9))
    elif my_risky:
        bid = max(bid, DAILY_SALARY * 0.62)
    else:
        if highest_prev >= 160 and hp >= 5 and no_water_days == 0:
            bid = min(bid, DAILY_SALARY * 0.3)
        elif highest_prev >= 120 and supply >= 20:
            bid = min(max(bid, DAILY_SALARY * 0.38), DAILY_SALARY * 0.48)
        elif rich_opp_count >= 2 and supply <= 18:
            bid = max(bid, DAILY_SALARY * 0.72)

    if day >= 8:
        if hp >= 5 and no_water_days == 0 and supply >= 20:
            bid = min(bid, DAILY_SALARY * 0.3)
        elif hp <= 4:
            bid = max(bid, DAILY_SALARY * 0.7)

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if days_left >= 2 and hp >= 4:
        reserve_floor = min(budget * 0.55, DAILY_SALARY * 2.2)
    max_spend = budget
    if budget > reserve_floor:
        max_spend = budget - reserve_floor + min(DAILY_SALARY * 0.35, reserve_floor)

    bid = min(bid, max_spend)
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
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    yesterday_bids = []
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opp += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    units = supply / WATER_REQ
    tight = units <= 1.25
    medium_tight = units <= 1.6

    if hp <= 2 or no_water >= 2:
        base = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif no_water >= 1:
        base = max(DAILY_SALARY * 0.78, highest_prev + 2.0 if tight else highest_prev * 0.82)
    elif tight:
        base = max(DAILY_SALARY * 0.72, highest_prev + 1.5, avg_prev + 4.0)
    elif medium_tight:
        base = max(DAILY_SALARY * 0.56, avg_prev + 1.5)
    else:
        base = DAILY_SALARY * 0.34

    if rich_opp >= 2 and tight:
        base += 6.0
    elif urgent_opp >= 2 and tight:
        base += 4.0

    if hp >= 7 and no_water == 0 and not tight and highest_prev >= DAILY_SALARY * 1.2:
        base = min(base, DAILY_SALARY * 0.28)

    if budget < DAILY_SALARY:
        if hp >= 5 and no_water == 0:
            base = min(base, budget * 0.45)
        else:
            base = min(max(base, budget * 0.75), budget)

    bid = max(0.0, min(float(budget), float(base)))
    return bid
"""
