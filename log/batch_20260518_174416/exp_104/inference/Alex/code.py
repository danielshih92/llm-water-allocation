# ============================================================
# Experiment: exp_104
# Agent: Alex
# Source: exp_104
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, DAILY_SALARY * 0.85)
        return min(budget, DAILY_SALARY * 0.2)

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 3:
            rich_opponents += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev_bid = max(prev_bids) if prev_bids else 0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    total_players = 1 + len(alive_opponents)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < total_players
    very_scarce = expected_units < max(1.0, total_players - 1)

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.78
    else:
        if very_scarce:
            base = DAILY_SALARY * 0.68
        elif scarcity:
            base = DAILY_SALARY * 0.56
        else:
            base = DAILY_SALARY * 0.38

    if highest_prev_bid > 0:
        if hp <= 4 or no_water_days >= 1:
            target = max(base, highest_prev_bid + 2)
        else:
            if highest_prev_bid >= DAILY_SALARY * 0.9:
                target = DAILY_SALARY * 0.32
            else:
                target = max(base, avg_prev_bid + 1.5)
    else:
        target = base

    if urgent_opponents >= len(alive_opponents) // 2 + 1:
        target += 4
    if rich_opponents >= len(alive_opponents) // 2 + 1 and scarcity:
        target += 3

    if day >= 8:
        target += 4
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        target += 6

    if budget < DAILY_SALARY * 1.2:
        target = min(target, max(8, budget * 0.55))
    elif budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.7)

    if hp >= 7 and no_water_days == 0 and not scarcity and highest_prev_bid >= DAILY_SALARY * 0.9:
        target = min(target, DAILY_SALARY * 0.25)

    if target < 0:
        target = 0
    return min(budget, target)
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
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 1:
            safe_bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, safe_bid))

    prev_bids = []
    opp_pressures = []
    needy_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            needy_count += 1
        if opp.get('budget', 0) >= 120:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        bid = None
        if isinstance(prev, dict):
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            pressure = float(bid)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                pressure += 8.0
            if opp.get('budget', 0) < 25:
                pressure -= 6.0
            opp_pressures.append(pressure)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_pressure = max(opp_pressures) if opp_pressures else highest_prev

    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_factor < 0:
        supply_factor = 0.0
    if supply_factor > 1:
        supply_factor = 1.0

    my_urgent = 0
    if hp <= 2:
        my_urgent += 3
    elif hp <= 4:
        my_urgent += 2
    elif hp <= 6:
        my_urgent += 1
    if no_water_days >= 2:
        my_urgent += 3
    elif no_water_days >= 1:
        my_urgent += 2

    crowd = len(alive)
    base = DAILY_SALARY * (0.34 + 0.18 * (1.0 - supply_factor))
    base += 3.0 * crowd
    base += 4.0 * needy_count

    if my_urgent >= 4:
        bid = max(base, highest_pressure + 8.0, DAILY_SALARY * 0.95)
    elif my_urgent >= 2:
        bid = max(base, highest_pressure + 3.0, DAILY_SALARY * 0.72)
    else:
        if highest_prev >= DAILY_SALARY * 1.6 and supply <= 18:
            bid = DAILY_SALARY * 0.22
        elif highest_prev >= DAILY_SALARY * 1.2 and hp > 4 and no_water_days == 0:
            bid = DAILY_SALARY * 0.3
        else:
            bid = max(base, highest_pressure + 1.5)

    if supply >= 22:
        bid -= 6.0
    elif supply <= 17:
        bid += 7.0

    if rich_count >= 2 and my_urgent == 0 and highest_prev > 110:
        bid = min(bid, DAILY_SALARY * 0.38)

    if day >= 8:
        if hp <= 4 or no_water_days >= 1:
            bid = max(bid, DAILY_SALARY * 0.9)
        else:
            bid = max(bid, DAILY_SALARY * 0.55)

    if budget < DAILY_SALARY * 0.8:
        bid = min(bid, budget * 0.82)
    else:
        bid = min(bid, budget)

    if bid < 0:
        bid = 0.0
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 42.0))

    prev_bids = []
    urgent_score = 0.0
    rich_pressure = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
        opp_hp = opp.get('hp', 10)
        opp_nw = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0.0)
        if opp_nw >= 1 or opp_hp <= 4:
            urgent_score += 1.0
        if opp_budget >= 500:
            rich_pressure += 1.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # In this scenario supply 15-25 means at most one player gets full water (req=13).
    # So win probability depends on outbidding the strongest current rival without overspending.
    if hp <= 2 or no_water >= 2:
        bid = max(78.0, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        bid = max(62.0, avg_prev + 4.0)
    else:
        if highest_prev >= 110:
            bid = 36.0
        elif highest_prev >= 90:
            bid = 44.0
        elif highest_prev >= 70:
            bid = 52.0
        else:
            bid = 48.0

    # Slightly raise under stronger scarcity/pressure signals.
    if supply <= 16:
        bid += 8.0
    elif supply <= 19:
        bid += 4.0

    bid += urgent_score * 3.0
    bid += rich_pressure * 2.0

    # Early days preserve budget; late days convert budget into survival.
    if day <= 2 and hp >= 6:
        bid -= 6.0
    if day >= 8:
        bid += 6.0

    # Budget discipline.
    cap = budget
    if hp >= 6 and no_water == 0:
        cap = min(cap, DAILY_SALARY * 0.95)
    elif hp >= 4:
        cap = min(cap, DAILY_SALARY * 1.15)

    if budget < 40:
        bid = max(bid, budget * 0.85)

    bid = max(1.0, min(bid, cap))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    desperate_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 95 and opp.get('budget', 0) >= 200:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev = sorted_bids[int(1)]
    elif len(prev_bids) == 1:
        second_prev = prev_bids[int(0)]

    guaranteed_units = int(supply / WATER_REQ)
    contested = guaranteed_units <= 1

    emergency = hp <= 3 or no_water_days >= 1
    danger = hp <= 5

    if emergency:
        target = max(96.0, second_prev + 2.0, highest_prev - 1.0)
        if highest_prev >= 120:
            target = max(102.0, highest_prev - 3.0)
        return float(min(budget, target))

    if contested:
        if danger:
            target = max(88.0, second_prev + 1.5)
            if rich_aggressive >= 2:
                target = max(target, 98.0)
            return float(min(budget, target))
        else:
            if rich_aggressive >= 2:
                return float(min(budget, 24.0))
            if highest_prev >= 90:
                return float(min(budget, 28.0))
            return float(min(budget, 36.0))

    if guaranteed_units >= 2:
        if danger or desperate_opp >= 2:
            target = max(52.0, second_prev * 0.7)
            return float(min(budget, target))
        return float(min(budget, 31.0))

    return float(min(budget, 35.0))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    opp_bids = []
    urgent_opp_bids = []
    rich_opp_bids = []
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            opp_bids.append(float(pbid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_bids.append(float(pbid))
            if opp.get('budget', 0) >= budget:
                rich_opp_bids.append(float(pbid))

    base_pressure = 55.0
    if opp_bids:
        sorted_bids = sorted(opp_bids)
        base_pressure = sorted_bids[int(len(sorted_bids) * 0.75)]
        if rich_opp_bids:
            base_pressure = max(base_pressure, max(rich_opp_bids))
        if urgent_opp_bids:
            base_pressure = max(base_pressure, max(urgent_opp_bids) - 2.0)

    scarcity = 0.0
    if supply <= 16:
        scarcity = 18.0
    elif supply <= 18:
        scarcity = 10.0
    elif supply >= 23:
        scarcity = -10.0
    elif supply >= 21:
        scarcity = -5.0

    need = 0.0
    if hp <= 2:
        need += 28.0
    elif hp <= 4:
        need += 16.0
    elif hp <= 6:
        need += 8.0

    if no_water_days >= 2:
        need += 30.0
    elif no_water_days >= 1:
        need += 14.0

    endgame = 0.0
    if day >= 8:
        endgame += 8.0
    if day >= 9:
        endgame += 6.0

    target = base_pressure + scarcity + need + endgame

    if opp_bids:
        highest_prev = max(opp_bids)
        if highest_prev >= 120 and hp > 4 and no_water_days == 0 and supply >= 20:
            target = min(target, 52.0)
        elif highest_prev >= 100 and hp > 6 and supply >= 22:
            target = min(target, 58.0)

    if hp >= 8 and no_water_days == 0 and supply >= 22:
        target = min(target, 50.0)

    floor_bid = 18.0
    if hp <= 3 or no_water_days >= 1:
        floor_bid = 62.0
    elif supply <= 17:
        floor_bid = 58.0
    elif supply >= 23 and hp >= 7:
        floor_bid = 28.0

    bid = max(floor_bid, target + 1.6)

    reserve = 0.0
    if day <= 7:
        reserve = 70.0
    max_affordable = max(0.0, budget - reserve)
    if hp <= 3 or no_water_days >= 1 or day >= 9:
        max_affordable = budget

    if max_affordable <= 0:
        if hp <= 2 or no_water_days >= 1:
            return float(max(0.0, min(budget, DAILY_SALARY * 0.9)))
        return 0.0

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    dangerous_prev = []
    weak_count = 0
    rich_count = 0

    for opp in alive:
        if opp.get('budget', 0) >= 120:
            rich_count += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            weak_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0)
            prev_bids.append(bid)
            if opp.get('budget', 0) >= bid * 0.6:
                dangerous_prev.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    effective_high = max(dangerous_prev) if dangerous_prev else highest_prev

    scarcity = (25.0 - supply) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days == 1:
        urgency += 0.25
    urgency += scarcity * 0.35

    if supply >= 23:
        base = DAILY_SALARY * 0.22
    elif supply >= 20:
        base = DAILY_SALARY * 0.34
    elif supply >= 17:
        base = DAILY_SALARY * 0.52
    else:
        base = DAILY_SALARY * 0.72

    if day >= 8:
        base += 6

    if effective_high >= 180:
        if urgency < 0.55:
            target = base * 0.75
        else:
            target = min(effective_high * 0.72, DAILY_SALARY * 1.28)
    elif effective_high >= 110:
        if urgency < 0.45:
            target = max(base, effective_high * 0.55)
        else:
            target = min(effective_high + 3.0, DAILY_SALARY * 1.22)
    elif effective_high > 0:
        target = max(base, effective_high + 2.0)
    else:
        target = base

    if weak_count >= 2 and urgency < 0.6:
        target *= 0.88
    if rich_count >= 2 and supply <= 18:
        target *= 1.08

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water_days == 1:
        target = max(target, DAILY_SALARY * 0.62)

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 0.35
    max_today = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        max_today = budget

    bid = min(target, max_today)
    if bid < 0:
        bid = 0.0
    if budget < DAILY_SALARY * 0.18 and (hp <= 3 or no_water_days >= 1):
        bid = budget

    return float(min(budget, max(0.0, bid)))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
    prev_bids = []
    max_prev = 0.0
    eric_like = 0.0
    cindy_like = 0.0
    urgent_opp = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive.append(opp)
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = 0.0
        if prev and prev.get('bid') is not None:
            bid = float(prev.get('bid', 0.0))
            prev_bids.append(bid)
            if bid > max_prev:
                max_prev = bid
        oid = str(opp_id).lower()
        if oid == 'eric':
            eric_like = bid
        if oid == 'cindy':
            cindy_like = bid

    if not alive:
        return float(min(budget, 18.0))

    slots = supply / float(WATER_REQ)

    if hp <= 2 or no_water >= 2:
        target = max(62.0, eric_like + 3.0)
        if cindy_like > 0:
            target = min(target, cindy_like * 0.72)
        return float(max(0.0, min(budget, target)))

    if hp <= 4 or no_water >= 1:
        if slots >= 1.7:
            target = max(36.0, eric_like + 2.0)
        else:
            target = max(52.0, eric_like + 4.0, max_prev * 0.92)
        if cindy_like >= 120.0:
            target = min(target, cindy_like * 0.68)
        return float(max(0.0, min(budget, target)))

    if slots >= 1.8:
        base = 14.0
    elif slots >= 1.5:
        base = 21.0
    else:
        base = 29.0

    if max_prev >= 110.0:
        base -= 4.0
    elif max_prev <= 20.0 and urgent_opp == 0:
        base += 6.0

    if eric_like > 0:
        if eric_like <= 35.0:
            base = max(base, eric_like + 1.5)
        elif eric_like <= 70.0:
            base = max(base, eric_like * 0.78)
        else:
            base = min(base, eric_like * 0.62)

    if cindy_like >= 120.0:
        base = min(base, 34.0)

    if len(alive) >= 3 and slots < 1.4:
        base += 6.0

    safe_cap = budget
    if hp >= 7 and no_water == 0:
        safe_cap = min(safe_cap, DAILY_SALARY * 0.55)

    bid = max(0.0, min(safe_cap, base))
    return float(bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, safe_bid))

    prev_bids = []
    prev_bids_strong = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('budget', 0) >= 500:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= DAILY_SALARY * 0.9:
                prev_bids_strong.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.6

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    low_supply = supply <= 17.0
    high_supply = supply >= 22.0

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
    elif supply <= 19.0:
        urgency += 1

    if desperate_count >= 2:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency <= 1:
        base = DAILY_SALARY * (0.28 if high_supply else 0.38)
        if highest_prev >= DAILY_SALARY * 1.2:
            base = min(base, DAILY_SALARY * 0.3)
        bid = base
    elif urgency <= 3:
        target = max(DAILY_SALARY * 0.58, avg_prev + 2.0)
        if high_supply:
            target -= 6.0
        if highest_prev >= DAILY_SALARY * 1.35 and hp > 4 and no_water_days == 0:
            target = DAILY_SALARY * 0.42
        bid = target
    else:
        if prev_bids_strong:
            target = max(highest_prev + 1.1, DAILY_SALARY * 0.92)
        else:
            target = max(avg_prev + 6.0, DAILY_SALARY * 0.9)
        if low_supply:
            target += 6.0
        if hp <= 2 or no_water_days >= 2:
            target += 8.0
        bid = target

    if rich_count >= 2 and urgency <= 2:
        bid *= 0.92

    remaining_days = max(1, 10 - day + 1)
    soft_cap = budget / float(remaining_days)
    if urgency <= 1:
        bid = min(bid, max(DAILY_SALARY * 0.3, soft_cap * 0.9))
    elif urgency <= 3:
        bid = min(bid, max(DAILY_SALARY * 0.55, soft_cap * 1.35))
    else:
        bid = min(bid, max(DAILY_SALARY * 0.95, soft_cap * 2.4))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.95)

    bid = max(0.0, min(float(budget), float(bid)))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_pressure = 0.0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_pressure = max(urgent_pressure, bid)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        bid = max(highest_prev + 3.0, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(avg_prev + 4.0, highest_prev * 0.92, DAILY_SALARY * 0.72)
    else:
        if tight_supply:
            bid = max(avg_prev + 2.0, highest_prev * 0.86, DAILY_SALARY * 0.62)
        elif loose_supply:
            bid = max(DAILY_SALARY * 0.34, avg_prev * 0.55)
        else:
            bid = max(DAILY_SALARY * 0.48, avg_prev * 0.72)

    if urgent_pressure > 0:
        bid = max(bid, urgent_pressure + 1.5)

    if rich_count >= 3 and hp >= 5 and no_water_days == 0:
        bid *= 0.9

    if day >= 8 and hp >= 6:
        bid *= 0.92

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
    no_water = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    strong_prev = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev['bid'])
                prev_bids.append(b)
                if b > strong_prev:
                    strong_prev = b

    if budget <= 0:
        return 0.0

    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < (1 + len(alive_opps)) * 0.5
    very_scarce = expected_units < 1.2

    if not alive_opps:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, 42.0))
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        target = max(78.0, min(112.0, max_prev + 2.0))
    elif urgent:
        if very_scarce:
            target = max(72.0, min(105.0, max_prev + 1.0))
        else:
            target = max(58.0, min(88.0, avg_prev + 4.0))
    else:
        if supply >= 22:
            target = 24.0
        elif supply >= 19:
            target = 32.0
        elif scarcity:
            target = max(38.0, min(68.0, avg_prev + 1.5))
        else:
            target = 28.0

    if day >= 8 and hp >= 6 and budget < 140:
        target *= 0.85

    if hp >= 8 and no_water == 0 and supply >= 21:
        target = min(target, 26.0)

    return float(min(budget, max(0.0, target)))
"""
