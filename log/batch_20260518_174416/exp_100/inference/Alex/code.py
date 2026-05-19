# ============================================================
# Experiment: exp_100
# Agent: Alex
# Source: exp_100
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
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            safe_bid = DAILY_SALARY * 0.8
        return min(budget, max(0, safe_bid))

    prev_bids = []
    desperate_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > DAILY_SALARY * 4:
            rich_opponents += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))
            if prev.get('status') == 'lost' and opp.get('hp', 10) <= 3:
                desperate_opponents += 1

    total_players = 1 + len(alive_opponents)
    supply_pressure = float(supply) / float(total_players * WATER_REQ)

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.92
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.72
    else:
        if supply_pressure >= 0.45:
            base = DAILY_SALARY * 0.46
        elif supply_pressure >= 0.35:
            base = DAILY_SALARY * 0.56
        else:
            base = DAILY_SALARY * 0.66

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        target = max(avg_prev + 1.0, highest_prev * 0.9)
        if hp <= 4 or no_water_days >= 1:
            base = max(base, target)
        else:
            base = max(base, min(target, DAILY_SALARY * 0.72))

    if desperate_opponents >= max(1, len(alive_opponents) // 2):
        base += 4
    if rich_opponents >= max(1, len(alive_opponents) // 2):
        base += 3

    if budget < DAILY_SALARY * 2:
        base = min(base, budget * 0.6 + 2)
    elif budget > DAILY_SALARY * 6 and (hp <= 4 or no_water_days >= 1):
        base += 3

    base = max(0, min(base, budget))
    return base
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
    prev_bids = []
    dangerous_prev = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if bid > dangerous_prev:
                    dangerous_prev = bid

    slots = int(supply / WATER_REQ)
    if slots < 0:
        slots = 0

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return min(budget, 18.0)

    opp_count = len(alive_opponents)

    urgent = False
    if hp <= 3 or no_water_days >= 2:
        urgent = True
    elif hp <= 5 and no_water_days >= 1:
        urgent = True

    if slots >= opp_count + 1:
        base = 8.0
    elif slots >= 2:
        base = 24.0
    else:
        base = 46.0

    if prev_bids:
        high_prev = max(prev_bids)
        low_prev = min(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        high_prev = 0.0
        low_prev = 0.0
        avg_prev = 0.0

    target = base

    if slots >= 2:
        if high_prev >= 95:
            target = max(target, 28.0)
        elif high_prev >= 75:
            target = max(target, 34.0)
        else:
            target = max(target, 26.0)
    else:
        if high_prev >= 95:
            target = max(target, 72.0)
        elif high_prev >= 75:
            target = max(target, 63.0)
        else:
            target = max(target, 55.0)

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        obudget = opp.get('budget', 0.0)
        ohp = opp.get('hp', 0)
        ono = opp.get('no_water_days', 0)
        oreq = opp.get('water_requirement', WATER_REQ)
        if prev and prev.get('bid') is not None:
            pbid = prev.get('bid', 0.0)
            if pbid >= 90 and obudget > budget and slots <= 1:
                target += 3.0
            if ohp <= 3 or ono >= 2:
                target += 2.0
            if oreq > WATER_REQ and slots >= 2:
                target -= 1.0

    if urgent:
        if slots >= 2:
            target = max(target, min(68.0, high_prev + 2.0 if high_prev > 0 else 52.0))
        else:
            target = max(target, min(95.0, high_prev + 3.0 if high_prev > 0 else 78.0))
    else:
        if hp >= 8 and no_water_days == 0 and high_prev >= 90 and slots >= 2:
            target = min(target, 22.0)

    if budget < DAILY_SALARY:
        target = min(target, budget * 0.9)

    if hp <= 2:
        target = max(target, min(budget, 96.0))
    elif hp <= 4 and no_water_days >= 1:
        target = max(target, min(budget, 82.0))

    if target < 0:
        target = 0.0

    return float(min(budget, round(target, 2)))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    high_budget_threat = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 140:
                high_budget_threat += 1
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    slots = max(1, int(supply // WATER_REQ))
    scarcity = slots <= 1

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

    if scarcity:
        urgency += 2
    if high_budget_threat >= 2:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency <= 1:
        bid = 12.0 if not scarcity else 28.0
    elif urgency == 2:
        bid = 26.0 if not scarcity else 52.0
    elif urgency == 3:
        bid = 45.0 if not scarcity else 82.0
    elif urgency == 4:
        bid = 68.0 if not scarcity else 118.0
    else:
        bid = 95.0 if not scarcity else 155.0

    if highest_prev > 0:
        if urgency >= 4:
            target = highest_prev + 3.0
            if target > bid:
                bid = target
        elif urgency >= 2 and scarcity:
            target = highest_prev * 0.72
            if target > bid:
                bid = target
        elif highest_prev >= 150 and hp >= 7 and no_water_days == 0:
            bid = min(bid, 18.0)
        elif avg_prev < 40 and urgency >= 2:
            target = highest_prev + 1.5
            if target > bid:
                bid = target

    income_buffer = DAILY_SALARY * max(0, 10 - day)
    if hp >= 7 and no_water_days == 0 and budget < 90 and not scarcity:
        bid = min(bid, 20.0)
    elif budget < 50:
        bid = min(bid, max(12.0, budget * 0.7))
    elif budget > income_buffer and urgency >= 4:
        bid = max(bid, min(budget, highest_prev + 5.0 if highest_prev > 0 else 120.0))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, highest_prev + 4.0 if highest_prev > 0 else 110.0)

    if scarcity and hp >= 8 and no_water_days == 0 and highest_prev >= 170:
        bid = min(bid, 22.0)

    if bid < 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    day = day_context['day']
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_threats = 0
    desperate_threats = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > budget * 0.9:
                rich_threats += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_threats += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0))

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0:
        tightness = 0.0
    if tightness > 1:
        tightness = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water >= 2:
        urgency += 0.7
    elif no_water >= 1:
        urgency += 0.35

    urgency += 0.35 * tightness
    urgency += 0.08 * min(desperate_threats, 3)

    days_left = max(0, 10 - int(day) + 1)
    reserve_target = max(0.0, days_left * DAILY_SALARY * 0.42)
    spendable = max(0.0, budget - reserve_target)

    base = DAILY_SALARY * (0.34 + 0.42 * urgency)

    if prev_bids:
        high_prev = max(prev_bids)
        low_prev = min(prev_bids)
        if high_prev >= 160:
            react = 32.0 if urgency >= 0.8 else 22.0
        elif high_prev >= 110:
            react = 72.0 if urgency >= 0.75 else 48.0
        elif high_prev >= 70:
            react = min(high_prev + 3.0, 88.0)
        else:
            react = max(38.0, low_prev + 4.0)
        bid = max(base, react)
    else:
        bid = base

    if rich_threats >= 2 and urgency < 0.75:
        bid *= 0.88

    if hp <= 2 or no_water >= 2:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water >= 1:
        bid = max(bid, DAILY_SALARY * 0.72)

    if supply >= 23 and urgency < 0.5:
        bid *= 0.82
    elif supply <= 17:
        bid *= 1.12

    cap = budget
    if spendable > 0:
        soft_cap = reserve_target * 0.15 + spendable * (0.55 + 0.35 * min(1.0, urgency))
        cap = min(cap, max(28.0, soft_cap))

    if hp <= 2 or no_water >= 2:
        cap = budget

    bid = min(bid, cap)
    bid = max(0.0, min(budget, bid))
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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    live_pressure = []
    desperate_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            prev_bids.append(b)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                live_pressure.append(b)
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_live = max(live_pressure) if live_pressure else highest_prev

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units < 1.2:
        scarcity = 2
    elif units < 1.6:
        scarcity = 1

    danger = 0
    if hp <= 2 or no_water >= 1:
        danger = 2
    elif hp <= 4:
        danger = 1

    if danger == 2:
        target = max(DAILY_SALARY * 1.15, highest_live + 2.0)
    elif scarcity == 2:
        target = max(DAILY_SALARY * 0.95, highest_live + 1.5)
    elif scarcity == 1 and danger >= 1:
        target = max(DAILY_SALARY * 0.8, highest_live + 1.0)
    elif highest_prev >= 100:
        target = DAILY_SALARY * 0.42
    elif highest_prev >= 85:
        target = DAILY_SALARY * 0.5
    else:
        target = max(DAILY_SALARY * 0.45, highest_live + 1.0)

    if desperate_opp >= 2 and danger == 0:
        target = min(target, DAILY_SALARY * 0.38)

    if day >= 8 and hp >= 5 and no_water == 0:
        target = min(target, DAILY_SALARY * 0.4)

    if budget < DAILY_SALARY * 0.8:
        target = min(target, budget)
    else:
        target = min(target, budget, DAILY_SALARY * 1.35)

    if hp <= 1:
        target = min(budget, max(target, DAILY_SALARY * 1.2))

    return float(max(0.0, target))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return float(min(budget, 12.0))

    prev_bids = []
    cindy_bid = None
    eric_bid = None
    weak_opponents = 0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if agent_id == 'Cindy' and bid is not None:
            cindy_bid = float(bid)
        if agent_id == 'Eric' and bid is not None:
            eric_bid = float(bid)
        if opp.get('hp', 10) <= 3 or opp.get('budget', 0) < 40:
            weak_opponents += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    low_supply = supply <= 17.0
    high_supply = supply >= 22.0
    urgent = (hp <= 4) or (no_water >= 1)
    endgame = day >= 8

    bid = 0.0

    if urgent:
        if low_supply:
            bid = 96.0
        else:
            bid = 78.0
    elif endgame:
        if hp >= 7 and high_supply:
            bid = 18.0
        elif low_supply:
            bid = 72.0
        else:
            bid = 38.0
    else:
        if high_supply:
            bid = 16.0
        elif low_supply:
            bid = 54.0
        else:
            bid = 28.0

    if cindy_bid is not None:
        if cindy_bid >= 120.0 and not urgent and hp >= 6 and not low_supply:
            bid = min(bid, 22.0)
        elif cindy_bid <= 90.0 and (low_supply or weak_opponents > 0):
            bid = max(bid, 62.0)

    if eric_bid is not None and eric_bid <= 16.0 and high_supply and hp >= 6:
        bid = min(bid, 17.0)

    if weak_opponents >= 2 and not urgent:
        bid = min(bid, 20.0)

    if highest_prev < 20.0 and low_supply:
        bid = max(bid, 36.0)

    reserve = 0.0
    if day <= 7:
        reserve = max(0.0, (10 - day) * 8.0)
    max_affordable = max(0.0, budget - reserve)
    if urgent or endgame:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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
        if hp <= 2 or no_water >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 500:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    severe_need = (hp <= 2) or (no_water >= 2)
    moderate_need = (hp <= 4) or (no_water >= 1)

    if severe_need:
        target = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif moderate_need:
        target = max(DAILY_SALARY * 0.7, avg_prev + 2.0)
    else:
        if supply >= 22:
            target = DAILY_SALARY * 0.28
        elif supply >= 19:
            target = DAILY_SALARY * 0.42
        else:
            target = DAILY_SALARY * 0.58

        if highest_prev > 0:
            if highest_prev >= 100:
                target = min(target, DAILY_SALARY * 0.4)
            elif highest_prev >= 70:
                target = max(target, DAILY_SALARY * 0.52)
            else:
                target = max(target, highest_prev + 1.5)

    if rich_opp >= 1 and not severe_need:
        target *= 0.95
    if urgent_opp >= 2 and supply <= 18:
        target += 8.0

    if day >= 8 and budget > DAILY_SALARY * 6 and moderate_need:
        target += 6.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left >= 2 and not severe_need:
        reserve_floor = DAILY_SALARY * 0.35

    affordable = max(0.0, budget - reserve_floor)
    bid = min(target, budget)
    if affordable > 0:
        bid = min(bid, max(affordable, min(budget, DAILY_SALARY * 0.2)))

    if severe_need:
        bid = min(max(bid, DAILY_SALARY * 0.9), budget)
    elif moderate_need:
        bid = min(max(bid, DAILY_SALARY * 0.55), budget)
    else:
        bid = min(max(bid, 0.0), budget)

    return float(max(0.0, bid))
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    strongest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    danger = 0
    if hp <= 2:
        danger += 4
    elif hp <= 4:
        danger += 2
    if no_water >= 2:
        danger += 4
    elif no_water >= 1:
        danger += 2
    if slots <= 1:
        danger += 2
    if day >= 8:
        danger += 1

    if danger >= 7:
        base = max(92.0, strongest_prev + 3.0)
    elif danger >= 4:
        base = max(68.0, avg_prev + 2.0, strongest_prev * 0.72)
    else:
        if slots >= 2:
            base = 24.0
        else:
            base = 42.0

    if strongest_prev >= 120 and danger <= 4:
        base = min(base, 54.0)
    elif strongest_prev >= 120 and danger >= 5:
        base = max(base, 88.0)

    if rich_opp >= 1 and slots <= 1 and danger <= 3:
        base = min(base, 38.0)

    if urgent_opp >= 2 and danger >= 4:
        base += 6.0

    if budget < 90:
        base = min(base, budget * 0.72)
    elif budget < 160:
        base = min(base, budget * 0.82)
    else:
        base = min(base, budget * 0.9)

    floor_bid = 8.0 if hp > 4 and no_water == 0 and slots >= 2 else 16.0
    bid = max(floor_bid, base)
    bid = min(float(budget), float(bid))

    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        base = 18.0 if hp > 3 else 40.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    cindy_prev = None
    urgent_opp = 0
    rich_opp = 0
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if agent_id == 'Cindy' and bid is not None:
            cindy_prev = float(bid)
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= 200:
            rich_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    non_cindy_prev = []
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None and agent_id != 'Cindy':
            non_cindy_prev.append(float(bid))
    highest_non_cindy = max(non_cindy_prev) if non_cindy_prev else 0.0

    critical = hp <= 2 or no_water_days >= 1
    very_safe = hp >= 8 and no_water_days == 0
    low_supply = supply <= 17.0
    high_supply = supply >= 23.0

    bid = 0.0

    if critical:
        if cindy_prev is not None and cindy_prev >= 120.0 and budget > 150.0:
            bid = min(budget, 138.0)
        else:
            bid = min(budget, max(72.0, highest_non_cindy + 4.0, highest_prev * 0.9))
    else:
        if cindy_prev is not None and cindy_prev >= 120.0:
            if low_supply:
                bid = min(budget, max(58.0, highest_non_cindy + 3.0))
            elif high_supply and very_safe:
                bid = min(budget, 16.0)
            else:
                bid = min(budget, max(28.0, highest_non_cindy + 1.5))
        else:
            if low_supply:
                bid = min(budget, max(62.0, highest_prev + 2.0))
            elif high_supply:
                bid = min(budget, max(24.0, highest_non_cindy * 0.75 + 2.0))
            else:
                bid = min(budget, max(36.0, highest_non_cindy + 2.0))

    if urgent_opp >= 2 and not critical:
        bid = max(bid, min(budget, 52.0 if not low_supply else 66.0))

    if rich_opp == 0 and very_safe and high_supply:
        bid = min(bid, budget, 18.0)

    if day >= 8:
        if hp <= 4:
            bid = max(bid, min(budget, 78.0))
        elif budget < 80:
            bid = min(bid, budget, 30.0)

    if budget < 40:
        bid = min(bid, budget)
    else:
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
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    rich_pressure = 0
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('budget', 0) >= 250 and opp.get('hp', 10) >= 6:
            rich_pressure += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tightness = 1.0 - scarcity

    base = DAILY_SALARY * (0.34 + 0.22 * tightness)

    if highest_prev > 0:
        if highest_prev >= 120:
            base = max(base, DAILY_SALARY * 0.42)
        elif highest_prev >= 95:
            base = max(base, min(highest_prev * 0.72, DAILY_SALARY * 0.88))
        elif highest_prev >= 60:
            base = max(base, highest_prev + 2.0)
        else:
            base = max(base, avg_prev + 3.0)

    if rich_pressure >= 2 and hp >= 4 and no_water_days == 0:
        base *= 0.82

    if desperate_count >= 2:
        base += 6.0

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.96)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * (0.72 + 0.18 * tightness))

    if day >= 8 and hp >= 6 and budget < 140:
        base *= 0.9

    if day == 1 and supply >= 22:
        base *= 0.9

    bid = max(0.0, min(float(budget), float(base)))
    return float(round(bid, 2))
"""
