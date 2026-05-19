# ============================================================
# Experiment: exp_049
# Agent: Alex
# Source: exp_049
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return min(budget, 18)

    competition = len(alive) + 1
    scarcity = float(supply) / float(competition * WATER_REQ)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

    if hp <= 2 or no_water_days >= 2:
        target = max(63, highest_prev + 3)
    elif hp <= 4 or no_water_days >= 1:
        if scarcity < 0.5:
            target = max(56, highest_prev + 2)
        else:
            target = max(44, avg_prev + 2)
    else:
        if scarcity >= 1.0:
            target = 18
        elif scarcity >= 0.75:
            target = max(24, avg_prev + 1)
        elif scarcity >= 0.5:
            target = max(34, highest_prev + 1.5)
        else:
            target = max(48, highest_prev + 2.5)

    if urgent_opp >= max(1, len(alive) // 2):
        target += 4
    if rich_opp >= max(1, len(alive) // 2):
        target += 3

    if budget < 20:
        target = min(target, budget)
    elif budget < 50:
        target = min(target, 0.8 * budget)
    else:
        target = min(target, 0.6 * budget + 12)

    target = max(0, min(budget, target))
    return float(target)
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

    alive = []
    prev_bids = []
    strong_prev = []
    affordable_prev = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 0.85 * opp.get('daily_salary', DAILY_SALARY):
                    strong_prev.append(bid)
                if opp.get('budget', 0) >= bid:
                    affordable_prev.append(bid)

    if not alive:
        if hp <= 2 or no_water >= 1:
            return min(budget, 40.0)
        return min(budget, 18.0)

    slots = supply / WATER_REQ
    many_slots = slots >= 1.8
    tight = slots <= 1.2

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_affordable = max(affordable_prev) if affordable_prev else highest_prev
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 1

    if danger >= 5:
        bid = max(0.95 * DAILY_SALARY, highest_affordable + 2.0)
        return min(budget, bid)

    if tight and hp >= 6 and no_water == 0 and highest_prev >= 75:
        return min(budget, 8.0)

    if many_slots:
        if danger >= 2:
            bid = max(42.0, min(0.82 * DAILY_SALARY, highest_affordable + 1.5))
        else:
            bid = max(28.0, min(48.0, avg_prev * 0.55 if avg_prev > 0 else 35.0))
        return min(budget, bid)

    if highest_prev >= 120 and hp >= 5 and no_water == 0:
        return min(budget, 10.0)

    if danger >= 3:
        bid = max(0.88 * DAILY_SALARY, highest_affordable + 1.0)
    elif highest_prev >= 90:
        bid = 22.0 if hp >= 6 else 60.0
    elif highest_prev >= 65:
        bid = max(46.0, min(62.0, highest_affordable + 1.5))
    elif highest_prev > 0:
        bid = max(38.0, highest_affordable + 1.0)
    else:
        bid = 44.0 if hp <= 4 else 34.0

    if day >= 8 and hp <= 4:
        bid = max(bid, 62.0)

    return min(budget, bid)
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 63.0))
        return float(min(budget, 28.0))

    prev_bids = []
    strong_opp_count = 0
    urgent_opp_count = 0
    for opp in alive_opps:
        if opp.get('budget', 0) > 40:
            strong_opp_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0

    if supply <= 16:
        scarcity = 'high'
    elif supply >= 22:
        scarcity = 'low'
    else:
        scarcity = 'mid'

    if hp <= 2 or no_water_days >= 2:
        base = max(64.0, highest_prev + 3.0)
    elif hp <= 4 or no_water_days >= 1:
        base = max(56.0, highest_prev + 1.5)
    else:
        if scarcity == 'high':
            base = max(52.5, highest_prev + 1.2)
        elif scarcity == 'mid':
            base = max(46.0, highest_prev * 0.98 + 0.8)
        else:
            base = max(34.0, highest_prev * 0.82)

    if highest_prev >= 68.0 and hp >= 5 and no_water_days == 0:
        base = min(base, 39.0)

    if strong_opp_count >= 2 and scarcity != 'low':
        base += 2.0
    if urgent_opp_count == 0 and hp >= 6 and scarcity == 'low':
        base -= 4.0

    if day >= 8:
        base += 3.0
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        base += 4.0

    if budget < 25:
        bid = min(budget, max(0.0, base * 0.75))
    else:
        bid = min(budget, base)

    if hp <= 1:
        bid = min(budget, max(bid, 68.0))

    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_pressure = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_pressure += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    severe = hp <= 2 or no_water_days >= 2
    urgent = hp <= 4 or no_water_days >= 1
    abundant = supply >= 22
    tight = supply <= 17

    if severe:
        bid = max(78.0, highest_prev + 3.0)
        return float(min(budget, bid))

    if abundant:
        if highest_prev >= 100:
            bid = 46.0 if not urgent else 72.0
        else:
            bid = max(42.0, min(76.0, avg_prev * 0.7 + 8.0))
        return float(min(budget, bid))

    if tight:
        if urgent:
            bid = max(82.0, highest_prev + 2.0)
        else:
            if rich_pressure >= 2 and highest_prev >= 90:
                bid = 18.0
            else:
                bid = max(40.0, min(68.0, avg_prev * 0.75 + 6.0))
        return float(min(budget, bid))

    if highest_prev >= 110:
        bid = 22.0 if hp >= 6 else 74.0
    elif highest_prev >= 90:
        bid = 28.0 if hp >= 7 else 69.0
    elif highest_prev >= 60:
        bid = max(44.0, min(72.0, highest_prev * 0.78))
    else:
        bid = 41.0 if hp >= 7 else 58.0

    if day >= 8 and hp >= 6:
        bid *= 0.9
    if budget < 140 and not urgent:
        bid *= 0.85

    return float(min(budget, max(0.0, bid)))
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 1.0))

    prev_bids = []
    strong_opponents = 0
    desperate_opponents = 0
    richest_budget = 0.0

    for opp in alive_opponents:
        if opp.get('budget', 0) > richest_budget:
            richest_budget = opp.get('budget', 0)
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opponents += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            strong_opponents += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if no_water >= 2:
        urgency = 3

    if urgency == 3:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif urgency == 2:
        if highest_prev >= DAILY_SALARY * 1.5:
            bid = DAILY_SALARY * 0.88
        else:
            bid = max(DAILY_SALARY * 0.72, highest_prev + 2.0)
    elif urgency == 1:
        if highest_prev >= DAILY_SALARY * 1.8:
            bid = DAILY_SALARY * (0.28 + 0.10 * scarcity)
        else:
            bid = max(DAILY_SALARY * (0.42 + 0.10 * scarcity), avg_prev * 0.55)
    else:
        if highest_prev >= DAILY_SALARY * 1.5:
            bid = DAILY_SALARY * (0.10 + 0.10 * scarcity)
        elif highest_prev > 0:
            bid = max(DAILY_SALARY * (0.22 + 0.08 * scarcity), highest_prev * 0.45)
        else:
            bid = DAILY_SALARY * (0.18 + 0.08 * scarcity)

    if len(alive_opponents) == 1:
        only_opp = alive_opponents[int(0)]
        opp_prev = only_opp.get('previous_trace', {})
        opp_prev_bid = opp_prev.get('bid') if opp_prev else None
        if urgency <= 1 and opp_prev_bid is not None and opp_prev_bid > DAILY_SALARY * 1.5:
            bid = min(bid, DAILY_SALARY * (0.12 + 0.10 * scarcity))
        if urgency >= 2 and opp_prev_bid is not None and only_opp.get('budget', 0) < budget:
            bid = max(bid, min(budget, opp_prev_bid * 0.75))

    if desperate_opponents >= 2 and urgency >= 1:
        bid = max(bid, DAILY_SALARY * 0.78)

    reserve_days = 3 if hp > 4 else 2
    reserve = reserve_days * DAILY_SALARY
    if budget < reserve:
        bid = min(bid, max(0.0, budget - DAILY_SALARY * 0.5))

    if day >= 8:
        if urgency >= 2:
            bid = max(bid, DAILY_SALARY * 0.9)
        else:
            bid = max(bid, DAILY_SALARY * 0.35)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
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

    alive_opps = []
    prev_bids = []
    rich_aggressive = 0
    weak_opps = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                weak_opps += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 145 and opp.get('budget', 0) >= 120:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    high_supply = supply >= 22
    low_supply = supply <= 17

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1

    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 1

    base = 0.0

    if danger >= 5:
        base = 0.96 * DAILY_SALARY
    elif danger >= 3:
        base = 0.82 * DAILY_SALARY
    elif low_supply and highest_prev < 120:
        base = 0.74 * DAILY_SALARY
    elif high_supply:
        base = 0.33 * DAILY_SALARY
    else:
        base = 0.48 * DAILY_SALARY

    if highest_prev >= 150:
        if danger <= 1 and high_supply:
            base = min(base, 0.26 * DAILY_SALARY)
        elif danger <= 2:
            base = min(base, 0.40 * DAILY_SALARY)
    elif highest_prev <= 95 and low_supply:
        base = max(base, 0.68 * DAILY_SALARY)
    elif avg_prev <= 110 and not high_supply:
        base = max(base, 0.58 * DAILY_SALARY)

    if rich_aggressive >= 2 and danger <= 2:
        base *= 0.82

    if weak_opps >= 2 and danger <= 1:
        base *= 0.9

    base += 8.0 * supply_pressure

    if day >= 8:
        if hp >= 6 and budget < 140:
            base *= 0.9
        elif danger >= 3:
            base *= 1.08

    reserve_floor = 0.0
    if hp > 4 and day <= 7:
        reserve_floor = 35.0

    bid = min(float(budget), base)
    if budget - bid < reserve_floor and danger <= 2:
        bid = max(0.0, budget - reserve_floor)

    if danger >= 5:
        bid = max(bid, min(float(budget), 64.0))
    elif danger >= 3:
        bid = max(bid, min(float(budget), 54.0))

    if bid > budget:
        bid = float(budget)
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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    total_players_alive = 1 + len(alive)
    expected_share = supply / float(total_players_alive) if total_players_alive > 0 else supply
    enough_if_even = expected_share >= WATER_REQ

    highest_prev = 0.0
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None and bid > highest_prev:
            highest_prev = float(bid)

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 2
    if supply <= 16:
        danger += 2
    elif supply <= 18:
        danger += 1
    if not enough_if_even:
        danger += 1
    if urgent_opp >= 2:
        danger += 1
    if rich_opp >= 1:
        danger += 1

    if len(alive) == 0:
        base = DAILY_SALARY * 0.22
    elif danger >= 6:
        base = DAILY_SALARY * 0.98
    elif danger >= 4:
        base = DAILY_SALARY * 0.82
    elif danger >= 2:
        base = DAILY_SALARY * 0.58
    else:
        base = DAILY_SALARY * 0.34 if enough_if_even else DAILY_SALARY * 0.48

    if highest_prev >= DAILY_SALARY * 1.2:
        if danger <= 2:
            base = min(base, DAILY_SALARY * 0.35)
        else:
            base = max(base, DAILY_SALARY * 0.88)
    elif highest_prev >= DAILY_SALARY * 0.85:
        if danger <= 1:
            base = min(base, DAILY_SALARY * 0.32)
        else:
            base = max(base, highest_prev * 0.92)
    elif highest_prev > 0:
        target = highest_prev + 1.5
        if danger >= 3:
            base = max(base, target)
        else:
            base = max(base, min(target, DAILY_SALARY * 0.62))

    remaining_days = max(0, 10 - day)
    reserve_floor = remaining_days * DAILY_SALARY * 0.18
    affordable = max(0.0, budget - reserve_floor)
    if danger >= 4:
        affordable = budget

    bid = min(base, affordable if affordable > 0 else budget)

    if hp <= 1 or no_water >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.95))

    if day >= 8 and hp >= 5 and no_water == 0 and enough_if_even:
        bid = min(bid, DAILY_SALARY * 0.28)

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
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 55.0)
        return min(budget, 28.0)

    expected_slots = max(1, int(supply // WATER_REQ))

    prev_bids = []
    urgent_prev_bids = []
    bob_like_bid = None
    rich_aggressive = 0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append((agent_id, float(bid)))
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_prev_bids.append(float(bid))
            if agent_id == 'Bob':
                bob_like_bid = float(bid)
        if opp.get('budget', 0) >= 300 and opp.get('daily_salary', 0) >= 70:
            if bid is not None and float(bid) >= 90:
                rich_aggressive += 1

    highest_prev = 0.0
    if prev_bids:
        highest_prev = max(b for _, b in prev_bids)

    base = 32.0
    if bob_like_bid is not None:
        base = bob_like_bid + 2.0
    elif prev_bids:
        sorted_bids = sorted([b for _, b in prev_bids])
        base = sorted_bids[int(len(sorted_bids) // 2)] + 2.0

    if expected_slots <= 1:
        base += 18.0
    elif expected_slots >= 2:
        base -= 4.0

    if hp <= 2:
        base = max(base, 95.0)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, 72.0)

    if urgent_prev_bids:
        base = max(base, max(urgent_prev_bids) + 3.0)

    if rich_aggressive >= expected_slots and hp > 4 and no_water_days == 0:
        base = min(base, 36.0)

    if highest_prev >= 120 and hp > 4 and no_water_days == 0:
        base = min(base, 34.0)

    if day >= 8:
        if hp <= 4 or no_water_days >= 1:
            base += 10.0
        else:
            base += 4.0

    if budget < 120:
        base = min(base, budget * 0.55)
    elif budget < 220:
        base = min(base, budget * 0.7)

    if hp >= 8 and no_water_days == 0 and expected_slots >= 2 and highest_prev >= 100:
        base = min(base, 30.0)

    if base < 0:
        base = 0.0
    if base > budget:
        base = budget
    return float(base)
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    prev_bids = []
    bob_prev_bid = None
    pressure_count = 0
    rich_alive = 0

    for opp in alive_opponents:
        if opp.get('budget', 0) > 0:
            rich_alive += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 50.0:
                pressure_count += 1
        if prev.get('bid') is not None and opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if bob_prev_bid is None or float(prev.get('bid')) > bob_prev_bid:
                bob_prev_bid = float(prev.get('bid'))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    anchor = bob_prev_bid if bob_prev_bid is not None else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency == 3:
        bid = max(63.0, anchor + 2.5)
    elif urgency == 2:
        bid = max(52.0 + 10.0 * scarcity, anchor - 1.0)
    else:
        if supply >= 22:
            bid = 24.0 if anchor >= 60.0 else 31.0
        elif supply >= 19:
            bid = 34.0 if anchor >= 60.0 else 41.0
        else:
            bid = 43.0 if anchor >= 60.0 else 49.0

    if pressure_count >= 2:
        bid += 4.0
    if rich_alive <= 1:
        bid -= 5.0

    if no_water_days >= 2:
        bid = max(bid, 66.0)
    elif no_water_days >= 1 and hp <= 5:
        bid = max(bid, 58.0)

    reserve_floor = 35.0 if hp > 4 else 10.0
    max_affordable = max(0.0, budget - reserve_floor)
    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    prev_bids = []
    pressured_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 8:
            rich_opponents += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            pressured_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0)
            status = prev.get('status')
            err = prev.get('error')
            if err is None and status != 'error':
                prev_bids.append(float(bid))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 85.0
        avg_prev = 80.0

    units = int(supply / WATER_REQ)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 50.0))
        return float(min(budget, 20.0))

    emergency = hp <= 2 or no_water_days >= 1
    danger = hp <= 4

    if units <= 1:
        if emergency:
            bid = max(highest_prev + 4.0, 108.0)
        elif danger:
            bid = max(highest_prev + 2.0, 98.0)
        else:
            bid = max(avg_prev + 3.0, highest_prev + 1.0, 92.0)
        if pressured_opponents >= 1:
            bid += 3.0
        if rich_opponents >= 2:
            bid += 2.0
    else:
        if emergency:
            bid = max(avg_prev, 82.0)
        elif danger:
            bid = max(avg_prev - 4.0, 72.0)
        else:
            bid = max(avg_prev - 10.0, 58.0)
        if units >= 2:
            bid -= 4.0

    if day >= 8 and hp > 4 and no_water_days == 0:
        bid -= 3.0

    if budget < 120:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, 115.0)

    if emergency and budget > 0:
        bid = max(min(budget, 112.0), bid)

    if bid < 0:
        bid = 0.0

    return float(round(min(budget, bid), 2))
"""
