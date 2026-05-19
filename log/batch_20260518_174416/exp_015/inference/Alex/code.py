# ============================================================
# Experiment: exp_015
# Agent: Alex
# Source: exp_015
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 1.2:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if not alive:
        return max(0, min(budget, round(DAILY_SALARY * 0.35, 2)))

    players = len(alive) + 1
    scarcity = players * WATER_REQ - supply
    base = DAILY_SALARY * 0.45

    if scarcity > 20:
        base = DAILY_SALARY * 0.9
    elif scarcity > 10:
        base = DAILY_SALARY * 0.75
    elif scarcity > 0:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.42

    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if max_prev >= DAILY_SALARY * 0.9:
            if hp <= 3 or no_water >= 1:
                base = max(base, DAILY_SALARY * 0.94)
            else:
                base = min(base, DAILY_SALARY * 0.38)
        else:
            pressure_bid = max_prev + 1.25
            if avg_prev < DAILY_SALARY * 0.45:
                pressure_bid = max(pressure_bid, DAILY_SALARY * 0.5)
            base = max(base, pressure_bid)

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.97)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.82)

    if no_water >= 2:
        base = max(base, DAILY_SALARY * 0.99)
    elif no_water >= 1:
        base = max(base, DAILY_SALARY * 0.88)

    if urgent_opp >= max(1, len(alive) // 2):
        base += 3.0
    if rich_opp >= max(1, len(alive) // 2):
        base += 2.0

    days_left = max(1, 10 - day_context['day'] + 1)
    reserve_target = days_left * DAILY_SALARY * 0.42
    if budget < reserve_target:
        base *= 0.88
    if budget < DAILY_SALARY * 1.2 and not (hp <= 3 or no_water >= 1):
        base *= 0.8

    if supply >= MAX_SUPPLY - 1 and hp > 4 and no_water == 0:
        base = min(base, DAILY_SALARY * 0.48)
    if supply <= MIN_SUPPLY + 1:
        base = max(base, DAILY_SALARY * 0.72)

    bid = max(0.0, min(budget, base))
    return round(bid, 2)
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, min(budget, 35.0))
        return max(0.0, min(budget, 18.0))

    total_agents = 1 + len(alive_opponents)
    total_req = WATER_REQ + sum(opp_requirements)
    scarcity = supply < total_req
    very_tight = supply <= WATER_REQ

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
        danger += 2
    if very_tight:
        danger += 2
    elif scarcity:
        danger += 1
    if day >= 8:
        danger += 1

    if budget <= 0:
        return 0.0

    if danger >= 5:
        target = max(0.95 * DAILY_SALARY, highest_prev + 2.5)
    elif danger >= 3:
        target = max(0.82 * DAILY_SALARY, highest_prev + 1.2)
    elif scarcity:
        target = max(0.68 * DAILY_SALARY, avg_prev + 0.8)
    else:
        target = 0.42 * DAILY_SALARY

    if budget < DAILY_SALARY * 1.2 and danger <= 2:
        target = min(target, 0.45 * DAILY_SALARY)
    elif budget < DAILY_SALARY * 2 and danger <= 1:
        target = min(target, 0.55 * DAILY_SALARY)

    if hp >= 8 and no_water_days == 0 and not scarcity:
        target = min(target, 0.38 * DAILY_SALARY)

    if highest_prev >= 75 and danger <= 2:
        target = min(target, 0.35 * DAILY_SALARY)

    bid = max(0.0, min(budget, target))
    return bid
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
    no_water = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    total_players = 1 + len(alive)
    secure_units = int(supply // WATER_REQ)
    scarcity = secure_units < total_players

    prev_bids = []
    strong_prev = 0.0
    weak_pullback = False
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > strong_prev:
                    strong_prev = float(bid)
                if float(bid) < 60.0:
                    weak_pullback = True

    opp_budgets = [float(o.get('budget', 0.0)) for o in alive]
    max_opp_budget = max(opp_budgets) if opp_budgets else 0.0

    emergency = hp <= 4 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        bid = min(budget, max(110.0, strong_prev + 3.0, DAILY_SALARY * 1.6))
        return float(max(0.0, bid))

    if scarcity:
        if emergency:
            bid = max(95.0, strong_prev + 2.0)
        else:
            bid = max(82.0, strong_prev + 1.5)
            if strong_prev >= 150.0 and hp >= 7 and no_water == 0:
                bid = 28.0
    else:
        if emergency:
            bid = max(72.0, strong_prev * 0.72)
        else:
            bid = 22.0
            if weak_pullback:
                bid = 36.0
            if strong_prev >= 140.0:
                bid = 18.0

    if day >= 8:
        bid += 10.0
    elif day <= 2 and not emergency and not scarcity:
        bid -= 4.0

    if max_opp_budget < 80.0 and not emergency:
        bid = min(bid, 55.0)

    bid = min(float(budget), float(bid))
    if bid < 0.0:
        bid = 0.0
    return float(bid)
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 0.85 * opp.get('daily_salary', DAILY_SALARY) and opp.get('budget', 0) > 100:
                    rich_aggressive += 1

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    slots = max(1, int(supply // WATER_REQ))
    low_supply = slots <= 1
    high_supply = slots >= 2

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    emergency = hp <= 2 or no_water_days >= 1
    severe_emergency = hp <= 1 or no_water_days >= 2

    if severe_emergency:
        bid = min(budget, max(DAILY_SALARY * 1.15, highest_prev + 6.0, 82.0))
        return float(max(0.0, bid))

    if emergency:
        if low_supply:
            bid = min(budget, max(DAILY_SALARY * 0.95, highest_prev + 3.0, 68.0))
        else:
            bid = min(budget, max(DAILY_SALARY * 0.72, avg_prev + 1.5, 52.0))
        return float(max(0.0, bid))

    if low_supply:
        if rich_aggressive >= 2 and hp >= 4:
            bid = min(budget, DAILY_SALARY * 0.22)
        elif highest_prev >= 120:
            bid = min(budget, DAILY_SALARY * 0.28)
        elif highest_prev >= 80:
            bid = min(budget, max(DAILY_SALARY * 0.40, highest_prev - 18.0))
        else:
            bid = min(budget, max(DAILY_SALARY * 0.58, highest_prev + 2.0, 41.0))
    else:
        if highest_prev >= 120:
            bid = min(budget, DAILY_SALARY * 0.18)
        elif avg_prev >= 80:
            bid = min(budget, DAILY_SALARY * 0.30)
        else:
            bid = min(budget, max(DAILY_SALARY * 0.34, avg_prev * 0.55 + 6.0, 24.0))

    if desperate_count >= 2 and low_supply:
        bid = max(0.0, bid + 8.0)

    if day >= 8 and hp >= 4 and budget < DAILY_SALARY * 3:
        bid = min(bid, DAILY_SALARY * 0.30)

    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    affordable_prev = []
    danger_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= bid:
                    affordable_prev.append(float(bid))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                danger_count += 1

    if not alive:
        return float(min(budget, 18.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_affordable = max(affordable_prev) if affordable_prev else highest_prev

    urgent = hp <= 4 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        bid = max(0.92 * DAILY_SALARY, strongest_affordable + 3.0)
    elif urgent:
        bid = max(0.78 * DAILY_SALARY, strongest_affordable + 2.0 * scarcity + 1.0)
    else:
        if supply >= 22:
            bid = 18.0 + 6.0 * scarcity
        elif supply >= 19:
            bid = 24.0 + 14.0 * scarcity
        else:
            bid = 34.0 + 24.0 * scarcity

        if strongest_affordable > 0:
            if strongest_affordable >= 110:
                bid = min(bid, 32.0 + 10.0 * scarcity)
            elif strongest_affordable >= 85:
                bid = max(bid, min(strongest_affordable + 1.5, 62.0 + 10.0 * scarcity))
            else:
                bid = max(bid, strongest_affordable + 1.5)

    if danger_count >= 2 and not urgent:
        bid *= 0.9

    if day >= 8 and hp >= 6 and no_water == 0:
        bid *= 0.92

    reserve = 0.0
    if hp > 4:
        reserve = 25.0
    if budget < 80:
        reserve = 0.0

    bid = min(bid, budget - reserve) if budget > reserve else min(bid, budget)
    bid = max(0.0, bid)

    if urgent and bid < 20.0:
        bid = min(budget, 20.0)

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
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 120:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17.0
    loose_supply = supply >= 22.0

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
    if tight_supply:
        urgency += 2
    elif supply <= 19.0:
        urgency += 1

    if urgency >= 5:
        target = max(62.0, min(98.0, highest_prev + 3.0))
    elif urgency >= 3:
        target = max(42.0, min(78.0, avg_prev * 0.72 + 6.0))
    else:
        if highest_prev >= 130.0:
            target = 16.0 if loose_supply else 22.0
        elif highest_prev >= 90.0:
            target = 24.0 if loose_supply else 31.0
        else:
            target = max(20.0, min(52.0, highest_prev + 2.0)) if highest_prev > 0 else (26.0 if tight_supply else 18.0)

    if desperate_count >= 2 and tight_supply:
        target += 10.0
    elif desperate_count >= 1 and tight_supply:
        target += 5.0

    if rich_count >= 2 and hp > 4 and no_water_days == 0:
        target -= 4.0

    if day >= 8:
        target += 6.0
    if day == 10:
        target += 8.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if hp > 4 and no_water_days == 0:
        reserve_floor = min(budget * 0.55, days_left * 18.0)
    elif hp > 2:
        reserve_floor = min(budget * 0.35, days_left * 10.0)

    spend_cap = max(0.0, budget - reserve_floor)
    if urgency >= 4:
        spend_cap = budget
    elif spend_cap < 12.0:
        spend_cap = min(budget, max(spend_cap, 12.0))

    bid = min(budget, min(spend_cap, target))

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 85.0 if tight_supply else 72.0))
    elif hp <= 4 or no_water_days >= 1:
        bid = min(budget, max(bid, 58.0 if tight_supply else 46.0))

    if loose_supply and hp >= 7 and no_water_days == 0 and highest_prev >= 120.0:
        bid = min(bid, 18.0)

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
        return float(min(budget, DAILY_SALARY * 0.35))

    winners_est = int(supply // WATER_REQ)
    if winners_est < 1:
        winners_est = 1

    prev_bids = []
    affordable_prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= 200:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) >= bid:
                affordable_prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_affordable = max(affordable_prev_bids) if affordable_prev_bids else highest_prev

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 2:
        urgency = 2
    elif hp <= 6 or no_water_days >= 1:
        urgency = 1

    if winners_est >= 2:
        base = max(DAILY_SALARY * 0.55, highest_affordable + 2.0)
        if desperate_count >= 2:
            base += 10.0
        if urgency >= 2:
            base += 12.0
        elif urgency == 1:
            base += 5.0
        if day >= 8:
            base += 6.0
        return float(min(budget, base))

    if urgency >= 3:
        base = max(DAILY_SALARY * 1.05, highest_affordable + 8.0)
        return float(min(budget, base))

    if urgency == 2:
        base = max(DAILY_SALARY * 0.9, highest_affordable + 4.0)
        if rich_count >= 2:
            base += 6.0
        return float(min(budget, base))

    if urgency == 1:
        if highest_prev >= 140:
            base = DAILY_SALARY * 0.42
        else:
            base = max(DAILY_SALARY * 0.62, highest_affordable + 1.5)
        return float(min(budget, base))

    if highest_prev >= 150:
        base = DAILY_SALARY * 0.18
    elif highest_prev >= 110:
        base = DAILY_SALARY * 0.28
    else:
        base = DAILY_SALARY * 0.48

    if day >= 9 and hp >= 7:
        base *= 0.8

    return float(min(budget, base))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 180:
                rich_opp += 1
            if opp.get('hp', 0) <= 4 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units <= 1.25:
        scarcity = 3
    elif units <= 1.55:
        scarcity = 2
    elif units <= 1.85:
        scarcity = 1

    danger = 0
    if hp <= 3:
        danger += 3
    elif hp <= 6:
        danger += 2
    elif hp <= 8:
        danger += 1

    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 2

    if budget <= 60:
        budget_mode = 'low'
    elif budget <= 140:
        budget_mode = 'mid'
    else:
        budget_mode = 'high'

    if danger >= 5:
        target = max(0.92 * DAILY_SALARY, highest_prev + 2.0)
    elif scarcity >= 3:
        target = max(0.82 * DAILY_SALARY, avg_prev * 0.72 + 6.0)
    elif scarcity == 2:
        target = max(0.62 * DAILY_SALARY, avg_prev * 0.52 + 4.0)
    elif scarcity == 1:
        target = max(0.42 * DAILY_SALARY, avg_prev * 0.32 + 2.0)
    else:
        target = 0.26 * DAILY_SALARY

    if urgent_opp >= 2 and scarcity >= 2:
        target += 6.0
    elif rich_opp >= 2 and scarcity >= 3:
        target += 4.0

    if highest_prev >= 200:
        if danger <= 2 and scarcity <= 1:
            target = min(target, 24.0)
        elif danger <= 3 and scarcity <= 2:
            target = min(target, 38.0)

    if budget_mode == 'low':
        target = min(target, 0.55 * DAILY_SALARY)
    elif budget_mode == 'mid' and danger <= 2:
        target = min(target, 0.72 * DAILY_SALARY)

    if day >= 8:
        if hp >= 7 and no_water_days == 0:
            target *= 0.9
        else:
            target *= 1.08

    if hp <= 2:
        target = max(target, 0.96 * DAILY_SALARY)

    bid = min(budget, max(0.0, target))
    return bid
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = DAILY_SALARY * 0.22
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.55
        return max(0.0, min(budget, base))

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units < 1.15:
        scarcity = 2
    elif units < 1.8:
        scarcity = 1

    prev_bids = []
    pressure_bids = []
    stressed_count = 0
    rich_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            adj = float(bid)
            if opp.get('budget', 0) < 120:
                adj *= 0.75
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
                adj *= 1.12
            pressure_bids.append(adj)
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2 or opp.get('budget', 0) < 100:
            stressed_count += 1
        if opp.get('budget', 0) > 300:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_pressure = max(pressure_bids) if pressure_bids else 0.0

    if scarcity == 2:
        target = max(DAILY_SALARY * 0.92, highest_pressure + 2.0)
    elif scarcity == 1:
        target = max(DAILY_SALARY * 0.52, highest_pressure * 0.72 + 1.0)
    else:
        target = DAILY_SALARY * 0.26
        if highest_prev > 0:
            target = max(target, min(DAILY_SALARY * 0.48, highest_pressure * 0.5))

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.72)

    if stressed_count >= len(alive):
        target *= 0.9
    elif rich_count >= 2 and scarcity >= 1:
        target *= 1.08

    if day >= 8 and hp >= 6 and scarcity == 0:
        target *= 0.88

    if budget < DAILY_SALARY:
        target = min(target, budget * 0.92)
    elif budget < DAILY_SALARY * 2:
        target = min(target, DAILY_SALARY * 0.78)

    if target < 0:
        target = 0.0
    return max(0.0, min(budget, target))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, DAILY_SALARY * 0.35)

    high_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0
    if scarcity > 1:
        scarcity = 1

    survival_mode = hp <= 2 or no_water_days >= 1
    caution_mode = hp <= 4

    if survival_mode:
        if high_prev >= 110:
            bid = min(budget, 92)
        else:
            bid = min(budget, max(72, high_prev + 3))
        return max(0, bid)

    if supply >= 22 and hp >= 7:
        base = 18 + 6 * scarcity
    elif supply >= 19 and hp >= 6:
        base = 24 + 10 * scarcity
    else:
        base = 34 + 18 * scarcity

    if caution_mode:
        base += 10
    if urgent_opp >= 2:
        base += 6
    if rich_opp >= 2:
        base -= 4

    if high_prev > 0:
        if high_prev >= 110:
            if hp >= 8 and no_water_days == 0:
                bid = min(base, 32)
            else:
                bid = max(base + 8, 78)
        elif high_prev >= 80:
            bid = max(base, min(high_prev + 2.5, 86))
        elif high_prev >= 45:
            bid = max(base, high_prev + 1.5)
        else:
            bid = max(base, avg_prev + 2)
    else:
        bid = base

    if day >= 8 and hp >= 6:
        bid -= 4
    if day >= 9 and budget < 140:
        bid -= 6

    reserve_floor = 20 if hp >= 6 else 0
    max_affordable = max(0, budget - reserve_floor)
    bid = min(bid, max_affordable)

    if bid < 0:
        bid = 0
    return bid
"""
