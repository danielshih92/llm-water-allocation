# ============================================================
# Experiment: exp_007
# Agent: Alex
# Source: exp_007
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
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opponents += 1
            if opp.get('budget', 0) >= budget:
                rich_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 18)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    danger = 0.0
    if hp <= 2:
        danger += 0.55
    elif hp <= 4:
        danger += 0.3
    if no_water_days >= 2:
        danger += 0.35
    elif no_water_days == 1:
        danger += 0.15
    danger = min(1.0, danger)

    base = 22 + 18 * scarcity + 20 * danger

    if highest_prev > 0:
        if danger >= 0.5:
            target = max(base, highest_prev + 2.0)
        else:
            if highest_prev >= 58:
                target = base - 6
            else:
                target = max(base, avg_prev + 1.5)
    else:
        target = base

    if urgent_opponents >= 2:
        target += 6
    elif urgent_opponents == 1:
        target += 3

    if rich_opponents >= len(alive_opponents) and len(alive_opponents) > 0:
        target += 2

    if supply >= 23 and danger < 0.5:
        target -= 6
    elif supply <= 17:
        target += 5

    if hp <= 2 or no_water_days >= 2:
        target = max(target, 58)

    max_safe = budget
    if hp > 4 and no_water_days == 0:
        max_safe = min(max_safe, DAILY_SALARY * 0.9)

    bid = max(0, min(max_safe, target))
    return float(round(bid, 2))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    prev_bids = []
    strong_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
                strong_bids.append(float(bid))

    top_prev = max(prev_bids) if prev_bids else 0.0
    top_strong = max(strong_bids) if strong_bids else top_prev
    second_strong = 0.0
    if len(strong_bids) >= 2:
        second_strong = sorted(strong_bids)[-2]
    elif len(prev_bids) >= 2:
        second_strong = sorted(prev_bids)[-2]

    units = supply / WATER_REQ
    tight = units < 2.0
    comfortable = units >= 2.0

    emergency = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if emergency:
        bid = max(92.0, top_strong + 2.0, second_strong + 4.0)
    elif tight:
        bid = max(78.0, second_strong + 2.0)
    elif comfortable and hp >= 5 and no_water == 0:
        bid = 24.0
        if top_prev < 40:
            bid = 18.0
    else:
        bid = max(38.0, min(88.0, second_strong + 1.5))
        if pressured:
            bid = max(bid, 62.0)

    if budget < bid:
        if emergency:
            return float(budget)
        bid = max(0.0, min(budget, budget * 0.85))

    return float(min(budget, bid))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_bids = []
    weak_count = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        alive_opponents.append(opp)
        if opp.get('budget', 0) <= DAILY_SALARY * 0.6 or opp.get('hp', 0) <= 2:
            weak_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) >= bid * 0.8:
                dangerous_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.25))

    strongest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_danger = max(dangerous_bids) if dangerous_bids else strongest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
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

    if supply <= 17:
        urgency += 2
    elif supply <= 20:
        urgency += 1

    if day >= 8:
        urgency += 1

    affordable_cap = min(budget, DAILY_SALARY * 1.35)

    if urgency >= 6:
        target = max(DAILY_SALARY * 0.95, strongest_danger + 2.0)
    elif urgency >= 4:
        target = max(DAILY_SALARY * 0.72, strongest_danger + 1.25)
    elif urgency >= 2:
        target = max(DAILY_SALARY * (0.48 + 0.18 * scarcity), strongest_danger * 0.72)
    else:
        target = DAILY_SALARY * (0.22 + 0.18 * scarcity)

    if weak_count >= len(alive_opponents) - 1 and urgency <= 2:
        target *= 0.72

    if strongest_prev >= DAILY_SALARY * 1.5 and urgency <= 3:
        target = min(target, DAILY_SALARY * 0.38)

    if budget < DAILY_SALARY * 0.8:
        target = min(target, budget * 0.92)

    if hp <= 2 or no_water >= 2:
        target = max(target, DAILY_SALARY * 0.9)

    bid = min(affordable_cap, target)
    if bid < 0:
        bid = 0.0
    return float(min(budget, round(bid, 2)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
    urgent_opp = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0
    bob_prev = None
    if 'Bob' in opponents_status and opponents_status['Bob'].get('alive'):
        prev = opponents_status['Bob'].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bob_prev = float(prev.get('bid'))

    scarcity = float(WATER_REQ) / max(1.0, float(supply))

    if hp <= 2 or no_water >= 2:
        target = max(92.0, (bob_prev + 2.0) if bob_prev is not None else 92.0)
        if supply <= 16:
            target = max(target, 108.0)
        return float(min(budget, target))

    if hp <= 4 or no_water >= 1:
        target = 72.0
        if bob_prev is not None:
            target = max(target, bob_prev + 1.5)
        if max_prev >= 100.0:
            target = min(target, 84.0)
        if supply <= 16:
            target = max(target, 86.0)
        return float(min(budget, target))

    if supply >= 22:
        target = 24.0 if urgent_opp == 0 else 31.0
        return float(min(budget, target))

    if supply >= 19:
        if max_prev >= 110.0:
            target = 28.0
        elif bob_prev is not None and bob_prev <= 72.0:
            target = bob_prev + 1.0
        else:
            target = max(32.0, min_prev + 1.0 if prev_bids else 32.0)
        return float(min(budget, target))

    if supply >= 17:
        if urgent_opp >= 2:
            target = 58.0
        elif bob_prev is not None:
            target = max(48.0, min(74.0, bob_prev + 1.0))
        else:
            target = 52.0
        return float(min(budget, target))

    target = 64.0
    if bob_prev is not None:
        target = max(target, min(78.0, bob_prev + 2.0))
    if max_prev >= 100.0 and hp >= 6 and no_water == 0:
        target = 46.0
    if day >= 8 and hp >= 6 and budget < 250:
        target = min(target, 52.0)
    return float(min(budget, target))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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
    urgent_count = 0
    rich_aggressive = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if not opp.get('alive', False):
            continue
        alive.append(opp)
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        if opp.get('budget', 0) >= 220:
            rich_aggressive += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    if not alive:
        return float(min(budget, 18.0))

    slots = supply / float(WATER_REQ)
    competitor_count = len(alive) + 1
    scarcity = competitor_count - slots

    sorted_prev = sorted(prev_bids, reverse=True)
    top_prev = sorted_prev[0] if len(sorted_prev) >= 1 else 90.0
    second_prev = sorted_prev[1] if len(sorted_prev) >= 2 else top_prev * 0.78

    danger = 0.0
    if hp <= 2:
        danger += 4.0
    elif hp <= 4:
        danger += 2.5
    elif hp <= 6:
        danger += 1.0

    danger += min(3.0, no_water_days * 1.8)
    if supply <= 16:
        danger += 2.2
    elif supply <= 18:
        danger += 1.2
    elif supply >= 23:
        danger -= 0.8

    danger += max(0.0, scarcity) * 0.9
    danger += urgent_count * 0.35
    danger += rich_aggressive * 0.25

    if day >= 8:
        danger += 0.8

    if danger >= 6.0:
        target = max(top_prev + 4.0, 0.92 * DAILY_SALARY)
    elif danger >= 4.0:
        target = max(second_prev + 3.0, 0.72 * DAILY_SALARY)
    elif danger >= 2.0:
        target = max(second_prev + 1.5, 0.52 * DAILY_SALARY)
    else:
        target = max(18.0, min(0.42 * DAILY_SALARY, second_prev * 0.72))

    if top_prev >= 180 and hp >= 6 and no_water_days == 0 and supply >= 20:
        target = min(target, 28.0)

    reserve_floor = 0.0
    if hp >= 5:
        reserve_floor = DAILY_SALARY * max(0, 10 - day) * 0.18
    max_affordable = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water_days >= 2:
        max_affordable = budget

    bid = min(target, max_affordable)

    if bid <= 0 and budget > 0:
        bid = min(budget, 12.0)

    if hp <= 2:
        bid = max(bid, min(budget, top_prev + 6.0, 0.98 * budget))
    elif no_water_days >= 2:
        bid = max(bid, min(budget, top_prev + 3.0))

    if bid > budget:
        bid = budget
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    opp_budgets = []
    desperate_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0.0))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if not alive:
        return float(min(budget, 1.0))

    units = int(supply / WATER_REQ)
    if units < 1:
        units = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_opp_budget = max(opp_budgets) if opp_budgets else 0.0

    urgent = hp <= 3 or no_water_days >= 1
    semi_urgent = hp <= 5
    abundant = supply >= 24
    medium_supply = supply >= 20

    if urgent:
        target = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
        if abundant:
            target *= 0.9
        target = min(target, 0.55 * budget + 0.45 * DAILY_SALARY)
        target = min(target, budget, max_opp_budget + 5.0 if max_opp_budget > 0 else budget)
        return float(max(1.0, target))

    if units >= 2:
        if highest_prev <= 90:
            target = max(38.0, avg_prev + 2.0)
        elif highest_prev <= 140:
            target = max(55.0, highest_prev * 0.72)
        else:
            target = 44.0 if hp >= 7 else 58.0
        if desperate_count >= 2:
            target += 8.0
        if abundant:
            target -= 6.0
        target = min(target, budget)
        return float(max(1.0, target))

    if highest_prev >= 150:
        target = 18.0 if hp >= 7 else 32.0
    elif highest_prev >= 110:
        target = 26.0 if hp >= 7 else 42.0
    else:
        target = max(36.0, highest_prev + 2.5)

    if semi_urgent:
        target += 18.0
    if desperate_count >= 2:
        target += 10.0
    if medium_supply:
        target -= 4.0
    if abundant:
        target -= 8.0

    reserve_floor = 0.18 * budget if hp >= 7 else 0.35 * budget
    target = min(target, budget - max(0.0, reserve_floor * 0.0))
    target = min(target, budget)
    return float(max(1.0, target))
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    cindy_prev = None
    pressure_count = 0
    needy_opponents = 0
    rich_opponents = 0

    for opp in alive:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            needy_opponents += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        prev = opp.get('previous_trace', {})
        bid = None
        if isinstance(prev, dict):
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= DAILY_SALARY * 0.75:
                pressure_count += 1
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if opp.get('budget', 0) > 200:
                cindy_prev = bid if bid is not None else cindy_prev

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    low_supply = supply <= 17
    mid_supply = supply <= 20
    emergency = hp <= 2 or no_water_days >= 2
    caution = hp <= 4 or no_water_days >= 1

    bid = DAILY_SALARY * 0.38

    if emergency:
        if low_supply:
            bid = DAILY_SALARY * 0.96
        elif mid_supply:
            bid = DAILY_SALARY * 0.88
        else:
            bid = DAILY_SALARY * 0.8
    elif caution:
        if highest_prev >= DAILY_SALARY * 0.85:
            bid = DAILY_SALARY * 0.72
        elif low_supply:
            bid = max(DAILY_SALARY * 0.62, highest_prev + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.52, avg_prev + 1.5)
    else:
        if low_supply:
            bid = max(DAILY_SALARY * 0.58, highest_prev + 1.0)
        elif mid_supply:
            bid = max(DAILY_SALARY * 0.46, avg_prev + 1.0)
        else:
            bid = DAILY_SALARY * 0.34
            if highest_prev > 0:
                bid = max(bid, min(DAILY_SALARY * 0.5, highest_prev * 0.72))

    if cindy_prev is not None:
        if cindy_prev >= 150 and not emergency:
            bid = min(bid, DAILY_SALARY * 0.55)
        elif cindy_prev <= DAILY_SALARY * 0.6 and (caution or low_supply):
            bid = max(bid, cindy_prev + 1.5)

    if pressure_count >= 2 and not emergency:
        bid *= 0.92
    if needy_opponents >= 2 and (caution or low_supply):
        bid = max(bid, DAILY_SALARY * 0.68)
    if rich_opponents == 0 and not caution:
        bid *= 0.9

    remaining_days_factor = max(0, 10 - day)
    reserve_target = remaining_days_factor * DAILY_SALARY * 0.28
    if budget < reserve_target and not emergency:
        bid = min(bid, DAILY_SALARY * 0.48)

    bid = max(0.0, bid)
    bid = min(bid, budget)
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    reqs = [WATER_REQ]
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            reqs.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    total_agents = 1 + len(alive)
    avg_req = sum(reqs) / float(len(reqs)) if reqs else WATER_REQ
    expected_winners = max(1, int(supply / avg_req))
    scarcity = expected_winners < total_agents

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if urgent:
        bid = max(63.0, highest_prev + 1.5)
        return float(min(budget, bid, DAILY_SALARY))

    if scarcity:
        if highest_prev >= 68:
            bid = 64.0 if pressured else 46.0
        elif highest_prev >= 55:
            bid = max(52.0, min(66.0, highest_prev + 1.0))
        elif highest_prev > 0:
            bid = max(38.0, min(58.0, second_prev + 2.0))
        else:
            bid = 42.0 if pressured else 30.0
    else:
        if pressured:
            bid = 34.0 if highest_prev < 60 else 52.0
        else:
            bid = 18.0 if highest_prev >= 68 else 24.0

    if budget < bid:
        bid = budget

    if hp >= 8 and no_water_days == 0 and budget < DAILY_SALARY * 3:
        bid = min(bid, budget * 0.45)

    return float(max(0.0, min(budget, bid)))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    strongest_prev = 0.0
    bob_prev = 0.0
    urgent_opponents = 0
    rich_opponents = 0

    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_opponents += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            if bid > strongest_prev:
                strongest_prev = bid
            if oid == 'Bob':
                bob_prev = bid

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    my_urgent = (hp <= 2) or (no_water_days >= 2)
    semi_urgent = (hp <= 4) or (no_water_days >= 1)

    if my_urgent:
        target = max(DAILY_SALARY * 0.92, strongest_prev + 2.0, bob_prev + 1.0)
        return float(min(budget, target))

    if scarcity == 2:
        base = DAILY_SALARY * 0.72
        if rich_opponents >= 1:
            base = max(base, strongest_prev + 1.25)
        if urgent_opponents >= 1:
            base = max(base, DAILY_SALARY * 0.8)
        if semi_urgent:
            base = max(base, DAILY_SALARY * 0.84)
        return float(min(budget, base))

    if scarcity == 1:
        base = DAILY_SALARY * 0.52
        if strongest_prev >= DAILY_SALARY * 0.75:
            base = DAILY_SALARY * 0.38
        elif strongest_prev > 0:
            base = max(base, strongest_prev * 0.9)
        if semi_urgent:
            base = max(base, DAILY_SALARY * 0.62)
        return float(min(budget, base))

    base = DAILY_SALARY * 0.24
    if semi_urgent:
        base = DAILY_SALARY * 0.42
    if strongest_prev >= DAILY_SALARY * 0.85 and hp > 4 and no_water_days == 0:
        base = DAILY_SALARY * 0.18

    if day >= 8 and hp <= 5:
        base = max(base, DAILY_SALARY * 0.5)

    return float(min(budget, base))
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
    prev_bids = []
    desperate_pressure = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_pressure += 1
            if opp.get('budget', 0) >= 500:
                rich_aggressive += 1

    if not alive:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 1.0
    if supply <= 16:
        scarcity = 1.35
    elif supply <= 18:
        scarcity = 1.15
    elif supply >= 23:
        scarcity = 0.8
    elif supply >= 21:
        scarcity = 0.9

    urgency = 0.0
    if hp <= 2:
        urgency += 55.0
    elif hp <= 4:
        urgency += 28.0
    elif hp <= 6:
        urgency += 12.0

    if no_water >= 2:
        urgency += 45.0
    elif no_water >= 1:
        urgency += 20.0

    if day >= 8 and hp <= 5:
        urgency += 12.0

    base = 34.0 * scarcity + urgency

    if highest_prev >= 140:
        target = max(base, 86.0 + urgency * 0.35)
    elif highest_prev >= 90:
        target = max(base, min(98.0, avg_prev + 6.0 + urgency * 0.25))
    elif highest_prev >= 55:
        target = max(base, highest_prev + 3.0)
    elif highest_prev > 0:
        target = max(base, highest_prev + 2.0)
    else:
        target = base

    target += desperate_pressure * 3.0
    target += rich_aggressive * 2.0

    if supply >= 23 and hp >= 7 and no_water == 0:
        target *= 0.72
    elif supply >= 21 and hp >= 6 and no_water == 0:
        target *= 0.82

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0:
        keep = min(budget * 0.45, reserve_days * 18.0)
        if hp <= 3 or no_water >= 1:
            keep *= 0.45
        soft_cap = max(0.0, budget - keep)

    if hp <= 2 or no_water >= 2:
        soft_cap = budget

    bid = min(budget, soft_cap if soft_cap > 0 else budget, target)

    if bid < 8.0 and budget >= 8.0:
        bid = 8.0

    if hp <= 2 and bid < 75.0:
        bid = min(budget, 75.0)
    if no_water >= 2 and bid < 88.0:
        bid = min(budget, 88.0)
    if supply <= 16 and (hp <= 4 or no_water >= 1) and bid < 95.0:
        bid = min(budget, 95.0)

    return float(max(0.0, bid))
"""
