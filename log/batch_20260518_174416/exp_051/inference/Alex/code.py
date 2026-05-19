# ============================================================
# Experiment: exp_051
# Agent: Alex
# Source: exp_051
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 20)

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('error') in (None, '', False):
            prev_bids.append(prev.get('bid', 0))

    n_players = len(alive) + 1
    approx_units = max(1, int(supply // WATER_REQ))
    scarcity = n_players - approx_units

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

    if hp <= 2 or no_water >= 1:
        base = DAILY_SALARY * 0.92
    elif hp <= 4:
        base = DAILY_SALARY * 0.72
    else:
        base = DAILY_SALARY * 0.48

    if scarcity >= 2:
        base += 12
    elif scarcity <= 0:
        base -= 10

    base += min(10, desperate_count * 2)
    base += min(6, rich_count)

    if highest_prev >= DAILY_SALARY * 0.9:
        if hp > 4 and no_water == 0:
            bid = DAILY_SALARY * 0.28
        else:
            bid = max(base, highest_prev + 1)
    elif highest_prev >= DAILY_SALARY * 0.65:
        bid = max(base, avg_prev + 2)
    elif highest_prev > 0:
        bid = max(base, highest_prev + 1.5)
    else:
        bid = base

    if supply >= 24 and hp > 4 and no_water == 0:
        bid *= 0.75
    elif supply <= 16:
        bid *= 1.12

    if budget < DAILY_SALARY:
        bid = min(bid, max(8, budget * 0.7))

    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)

    bid = max(0, min(budget, round(bid, 2)))
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    threatening_bids = []
    desperate_count = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= DAILY_SALARY * 0.85:
                threatening_bids.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        second_prev = sorted(prev_bids)[-2]

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    elif hp <= 6:
        urgency += 1
    if no_water_days >= 1:
        urgency += 2
    if slots <= 1:
        urgency += 2
    if desperate_count >= 2:
        urgency += 1
    if day >= 8:
        urgency += 1

    if not alive_opps:
        bid = DAILY_SALARY * 0.35
    elif urgency >= 5:
        target = max(DAILY_SALARY * 0.95, min(highest_prev + 2.0, DAILY_SALARY * 1.25))
        bid = target
    elif urgency >= 3:
        if slots >= 2:
            target = max(DAILY_SALARY * 0.62, min(second_prev + 1.5, DAILY_SALARY * 0.9))
        else:
            target = max(DAILY_SALARY * 0.82, min(highest_prev + 1.5, DAILY_SALARY * 1.05))
        bid = target
    else:
        if slots >= 2:
            if highest_prev >= 120:
                bid = DAILY_SALARY * 0.38
            elif highest_prev >= 70:
                bid = DAILY_SALARY * 0.48
            else:
                bid = DAILY_SALARY * 0.42
        else:
            if highest_prev >= 120:
                bid = DAILY_SALARY * 0.58
            else:
                bid = max(DAILY_SALARY * 0.55, min(highest_prev + 1.0, DAILY_SALARY * 0.85))

    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    if no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.82)
    if budget < bid:
        bid = budget
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

    alive_opps = []
    prev_bids = []
    dangerous_bids = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= bid:
                    dangerous_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 18.0))

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    urgency = 0.0
    if hp <= 2:
        urgency += 0.7
    elif hp <= 4:
        urgency += 0.4
    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days >= 1:
        urgency += 0.25
    if day >= 8:
        urgency += 0.15

    base = DAILY_SALARY * (0.42 + 0.28 * tightness + urgency)

    target = base
    if dangerous_bids:
        top = max(dangerous_bids)
        if supply <= 18 or hp <= 4 or no_water_days >= 1:
            target = max(target, top + 2.0)
        else:
            target = max(target, top * 0.82)
    elif prev_bids:
        target = max(target, max(prev_bids) * 0.75 + 1.0)

    rich_threats = 0
    for opp in alive_opps:
        if opp.get('budget', 0) >= budget * 0.9:
            rich_threats += 1
    if rich_threats >= 2 and supply <= 18:
        target += 6.0

    if hp >= 7 and no_water_days == 0 and supply >= 22:
        target *= 0.72

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 20.0
    max_spend = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water_days >= 2:
        max_spend = budget

    bid = min(target, max_spend if max_spend > 0 else budget)
    bid = max(0.0, bid)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

    return float(min(budget, round(bid, 2)))
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

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 700:
                prev = opp.get('previous_trace', {})
                if prev and prev.get('bid') is not None and prev.get('bid') >= 80:
                    rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid'))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1

    if danger >= 5:
        bid = max(95.0, highest_prev + 3.0)
    elif danger >= 3:
        bid = max(72.0, min(98.0, highest_prev + 2.0))
    else:
        if supply >= 22:
            bid = 18.0
        elif supply >= 19:
            bid = 26.0
        elif supply >= 17:
            bid = 38.0
        else:
            bid = 52.0

        if highest_prev > 0:
            if highest_prev <= 65:
                bid = max(bid, highest_prev + 1.5)
            elif highest_prev <= 95:
                bid = max(bid, min(highest_prev + 1.0, 68.0))
            else:
                bid = max(24.0, bid - 6.0)

        bid += scarcity * 10.0
        bid += desperate_count * 1.5
        if rich_aggressive >= 2 and hp > 4 and no_water_days == 0:
            bid -= 5.0

    if day >= 8:
        bid += 6.0
    if day >= 9 and (hp <= 5 or no_water_days >= 1):
        bid += 10.0

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.6

    max_affordable = max(0.0, budget - reserve)
    if danger >= 3:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            safe_bid = DAILY_SALARY * 0.6
        return float(min(budget, safe_bid))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    cindy_like_present = False

    for opp in alive_opps:
        if opp.get('budget', 0) >= 200:
            rich_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 130:
                    cindy_like_present = True

    highest_prev = max(prev_bids) if prev_bids else 0.0
    low_prev = []
    for b in prev_bids:
        if b < 100:
            low_prev.append(b)
    pressure_bid = max(low_prev) if low_prev else 0.0

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
        urgency += 2

    if tight_supply:
        urgency += 2
    elif ample_supply:
        urgency -= 1

    urgency += min(desperate_count, 2)

    if cindy_like_present and urgency <= 1 and ample_supply:
        return float(min(budget, 8.0))

    if cindy_like_present and urgency <= 2 and not tight_supply:
        base = max(18.0, pressure_bid + 2.0)
        return float(min(budget, base))

    if urgency >= 6:
        bid = max(92.0, pressure_bid + 8.0)
    elif urgency >= 4:
        bid = max(68.0, pressure_bid + 5.0)
    elif urgency >= 2:
        bid = max(42.0, pressure_bid + 3.0)
    else:
        bid = max(22.0, pressure_bid + 1.5)

    if highest_prev >= 130 and urgency < 5:
        bid = min(bid, 75.0)

    if rich_count >= 2 and tight_supply:
        bid += 8.0

    if day >= 8:
        bid += 6.0
    if day >= 9 and (hp <= 4 or no_water >= 1):
        bid += 10.0

    return float(min(budget, max(0.0, bid)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    desperate_pressure = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_pressure += 1
            if prev.get('status') == 'lost' and opp.get('hp', 10) <= 4:
                desperate_pressure += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 1:
        urgency += 3
    if supply_tight:
        urgency += 2
    elif supply_loose:
        urgency -= 1
    urgency += min(2, desperate_pressure)

    if urgency >= 6:
        target = max(0.95 * DAILY_SALARY, highest_prev + 3.0)
    elif urgency >= 4:
        target = max(0.78 * DAILY_SALARY, avg_prev + 2.0, highest_prev * 0.72)
    elif urgency >= 2:
        target = max(0.55 * DAILY_SALARY, avg_prev * 0.82 + 1.0)
    else:
        target = max(0.28 * DAILY_SALARY, avg_prev * 0.55)

    if rich_count >= 2 and urgency <= 2:
        target *= 0.9
    if supply_loose and urgency <= 3:
        target *= 0.88
    if day >= 8 and hp <= 4:
        target = max(target, 0.85 * DAILY_SALARY)

    reserve_floor = 0.0
    if hp > 3 and day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    max_affordable = max(0.0, budget - reserve_floor)
    if urgency >= 4:
        max_affordable = budget

    bid = min(target, max_affordable if max_affordable > 0 else budget)
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, highest_prev + 4.0, 0.92 * DAILY_SALARY))

    bid = max(0.0, min(budget, bid))
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
    strong_prev = []
    weak_prev = []

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= DAILY_SALARY * 0.9:
                    strong_prev.append(float(bid))
                else:
                    weak_prev.append(float(bid))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    total_players = 1 + len(alive)
    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < total_players

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    if scarcity:
        urgency += 2
    if float(supply) <= 17:
        urgency += 1
    elif float(supply) >= 23:
        urgency -= 1

    base = DAILY_SALARY * 0.42

    if urgency >= 6:
        target = max(DAILY_SALARY * 0.98, highest_prev + 2.5)
    elif urgency >= 4:
        if highest_prev > 0:
            target = max(DAILY_SALARY * 0.78, highest_prev + 1.25)
        else:
            target = DAILY_SALARY * 0.82
    elif urgency >= 2:
        if scarcity and highest_prev > 0:
            target = max(DAILY_SALARY * 0.62, min(highest_prev + 0.75, DAILY_SALARY * 0.9))
        else:
            target = max(base, avg_prev * 0.78 if avg_prev > 0 else DAILY_SALARY * 0.52)
    else:
        if len(strong_prev) >= 2:
            target = DAILY_SALARY * 0.28
        elif highest_prev >= DAILY_SALARY * 0.9:
            target = DAILY_SALARY * 0.33
        elif scarcity and highest_prev > 0:
            target = max(DAILY_SALARY * 0.48, second_prev + 0.5)
        else:
            target = DAILY_SALARY * 0.4

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0 and urgency < 4:
        soft_cap = min(soft_cap, budget / max(1, reserve_days // 2 + 1) + DAILY_SALARY * 0.25)

    if hp <= 2 or no_water_days >= 2:
        soft_cap = budget

    bid = min(target, soft_cap, budget)

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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    urgent_bids = []
    all_prev_bids = []
    rich_survivors = 0
    desperate_count = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        prev_bid = None
        if prev and prev.get('bid') is not None:
            prev_bid = prev.get('bid')
            all_prev_bids.append(prev_bid)
        opp_hp = opp.get('hp', 0)
        opp_nw = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0)
        if opp_budget >= 800 and opp_hp >= 6:
            rich_survivors += 1
        if opp_hp <= 3 or opp_nw >= 1:
            desperate_count += 1
            if prev_bid is not None:
                urgent_bids.append(prev_bid)

    highest_prev = max(all_prev_bids) if all_prev_bids else 0.0
    highest_urgent = max(urgent_bids) if urgent_bids else highest_prev

    scarcity = float(WATER_REQ) / max(float(supply), 1.0)

    if hp <= 2 or no_water >= 2:
        target = max(92.0, highest_urgent + 2.5)
    elif hp <= 4 or no_water >= 1:
        target = max(78.0, highest_urgent + 1.5)
    else:
        if rich_survivors >= 2 and desperate_count == 0:
            target = 18.0 + 10.0 * scarcity
        elif highest_prev >= 100:
            target = 24.0 + 12.0 * scarcity
        elif highest_prev >= 80:
            target = 38.0 + 10.0 * scarcity
        else:
            target = max(32.0, highest_prev + 1.0)

    if day >= 8 and hp >= 5 and no_water == 0:
        target *= 0.9
    if budget < 120:
        target = min(target, budget * 0.55)
    elif budget < 250:
        target = min(target, budget * 0.7)

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
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

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 135:
                    aggressive_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 20.0))
        return float(min(budget, 5.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0

    my_need = 0
    if hp <= 2:
        my_need += 3
    elif hp <= 4:
        my_need += 2
    elif hp <= 6:
        my_need += 1

    if no_water_days >= 2:
        my_need += 3
    elif no_water_days == 1:
        my_need += 1

    if day >= 8:
        my_need += 1

    if supply >= 24:
        supply_pressure = -1
    elif supply >= 21:
        supply_pressure = 0
    elif supply >= 18:
        supply_pressure = 1
    else:
        supply_pressure = 2

    my_need += supply_pressure

    if aggressive_count >= 2 and hp >= 7 and no_water_days == 0 and supply <= 20:
        return float(min(budget, 1.0))

    if my_need <= 1:
        bid = max(0.0, min_prev * 0.15)
        if supply >= 22:
            bid += 6.0
        else:
            bid += 2.0
        return float(min(budget, bid))

    if my_need == 2:
        bid = 18.0
        if max_prev > 0:
            bid = max(bid, min(max_prev * 0.22, 38.0))
        if supply >= 22:
            bid -= 4.0
        return float(max(0.0, min(budget, bid)))

    if my_need == 3:
        bid = 42.0
        if max_prev >= 140:
            bid = 36.0 if hp >= 5 else 72.0
        elif max_prev >= 100:
            bid = max(bid, max_prev * 0.55)
        if supply >= 23:
            bid -= 8.0
        return float(max(0.0, min(budget, bid)))

    if my_need == 4:
        if hp <= 3 or no_water_days >= 2:
            bid = max(95.0, max_prev + 3.0)
        else:
            bid = 68.0 if max_prev >= 140 else max(60.0, max_prev * 0.7)
        if supply >= 23:
            bid -= 10.0
        return float(max(0.0, min(budget, bid)))

    if hp <= 2 or no_water_days >= 2:
        bid = max(145.0, max_prev + 2.0)
        return float(max(0.0, min(budget, bid)))

    bid = max(85.0, max_prev * 0.78)
    if supply <= 17:
        bid += 12.0
    return float(max(0.0, min(budget, bid)))
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

    alive = {k: v for k, v in opponents_status.items() if v.get('alive')}
    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 12.0))

    prev_bids = []
    cindy_bid = None
    eric_bid = None
    urgent_opp = 0
    for name, opp in alive.items():
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if name == 'Cindy' and bid is not None:
            cindy_bid = float(bid)
        if name == 'Eric' and bid is not None:
            eric_bid = float(bid)
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1

    high_pressure = max(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 1:
        if supply >= 22:
            return float(min(budget, 72.0))
        return float(min(budget, 95.0))

    if supply <= 16:
        if cindy_bid is not None and cindy_bid >= 120:
            return float(min(budget, 6.0))
        return float(min(budget, 14.0))

    if supply >= 22:
        target = 16.5
        if eric_bid is not None:
            target = max(target, float(eric_bid) + 1.5)
        if urgent_opp >= 2:
            target += 6.0
        return float(min(budget, target))

    if supply >= 19:
        if cindy_bid is not None and cindy_bid >= 130:
            target = 15.5
            if eric_bid is not None:
                target = max(target, float(eric_bid) + 1.0)
            return float(min(budget, target))
        target = 22.0
        if eric_bid is not None:
            target = max(target, float(eric_bid) + 2.0)
        if high_pressure >= 80:
            target += 4.0
        return float(min(budget, target))

    target = 17.0
    if eric_bid is not None:
        target = max(target, float(eric_bid) + 1.0)
    if high_pressure >= 120:
        target = 12.0
    if day >= 8 and hp >= 5:
        target = min(target, 13.0)
    return float(min(budget, target))
"""
