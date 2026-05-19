# ============================================================
# Experiment: exp_026
# Agent: Alex
# Source: exp_026
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return min(budget, DAILY_SALARY * 0.9)
        return min(budget, DAILY_SALARY * 0.35)

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > budget:
            rich_opponents += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    my_urgency = 0
    if hp <= 2:
        my_urgency += 3
    elif hp <= 4:
        my_urgency += 1
    if no_water >= 1:
        my_urgency += 2

    if my_urgency >= 4:
        base = DAILY_SALARY * 0.95
    elif my_urgency >= 2:
        base = DAILY_SALARY * 0.78
    else:
        if highest_prev >= DAILY_SALARY * 0.9:
            base = DAILY_SALARY * 0.28 if hp > 4 else DAILY_SALARY * 0.88
        elif highest_prev >= DAILY_SALARY * 0.75:
            base = max(DAILY_SALARY * 0.52, highest_prev - 6)
        elif highest_prev > 0:
            base = max(DAILY_SALARY * 0.45, avg_prev + 2)
        else:
            base = DAILY_SALARY * 0.5

    base += scarcity * 6
    base += urgent_opponents * 1.5
    if rich_opponents >= len(alive_opponents) / 2.0:
        base += 3

    if budget < DAILY_SALARY * 0.8:
        base = min(base, budget * 0.7 + 5)

    if hp > 5 and no_water == 0 and highest_prev >= DAILY_SALARY * 0.9:
        base = min(base, DAILY_SALARY * 0.3)

    bid = max(0, min(budget, base))
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.28
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    distressed_opponents = 0
    desperate_opponents = 0
    rich_aggressive = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        opp_hp = float(opp.get('hp', 0))
        opp_budget = float(opp.get('budget', 0))
        opp_nwd = int(opp.get('no_water_days', 0))
        if opp_hp <= 3 or opp_nwd >= 1:
            distressed_opponents += 1
        if opp_hp <= 2 or opp_nwd >= 2:
            desperate_opponents += 1
        if opp_budget >= DAILY_SALARY * 6:
            rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - 15.0) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0
    low_supply = 1.0 - scarcity

    base = DAILY_SALARY * (0.34 + 0.18 * low_supply)

    if highest_prev >= 100:
        base = min(base, DAILY_SALARY * 0.38)
    elif highest_prev >= 80:
        base = min(base, DAILY_SALARY * 0.45)
    elif highest_prev > 0:
        base = max(base, min(DAILY_SALARY * 0.62, avg_prev * 0.78 + 2.0))

    if distressed_opponents >= 2:
        base *= 0.92
    if desperate_opponents >= 1 and hp >= 4:
        base *= 0.9
    if rich_aggressive >= 2 and hp >= 4:
        base *= 0.95

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.96)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * (0.72 + 0.12 * low_supply))
    elif hp >= 8 and budget < DAILY_SALARY * 4:
        base = min(base, DAILY_SALARY * 0.42)

    if day >= 8:
        if hp <= 5:
            base = max(base, DAILY_SALARY * 0.82)
        else:
            base = max(base, DAILY_SALARY * 0.46)

    if budget < DAILY_SALARY * 2:
        base = min(base, budget * 0.72 + 4.0)

    bid = max(0.0, min(budget, base))
    return float(round(bid, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_pressure = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 120:
                    opp_pressure += 2
                elif bid >= 80:
                    opp_pressure += 1

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 16
    medium_supply = supply <= 19

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

    if tight_supply:
        danger += 2
    elif medium_supply:
        danger += 1

    if highest_prev >= 130:
        danger -= 1

    if danger >= 6:
        bid = max(110.0, highest_prev + 2.5)
    elif danger >= 4:
        bid = max(78.0, avg_prev * 0.72 + 8.0)
    elif danger >= 2:
        if highest_prev >= 120:
            bid = 34.0
        else:
            bid = max(42.0, avg_prev * 0.55 + 4.0)
    else:
        if supply >= 22:
            bid = 16.0
        elif highest_prev >= 120:
            bid = 22.0
        else:
            bid = 28.0

    if budget < 40:
        bid = min(bid, budget)
    elif budget < 90:
        bid = min(bid, budget * 0.72)
    else:
        bid = min(bid, budget * 0.9)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 95.0))

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    cindy_bid = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
                if agent_id == 'Cindy':
                    cindy_bid = prev['bid']

    if not alive:
        return max(0.0, min(budget, 18.0))

    alive_count = len(alive)
    scarcity = supply / float(WATER_REQ * (alive_count + 1))
    severe_need = hp <= 3 or no_water >= 2
    moderate_need = hp <= 5 or no_water >= 1

    pressure = max(prev_bids) if prev_bids else 0.0
    if cindy_bid is None:
        cindy_bid = pressure

    if severe_need:
        if supply <= 16:
            target = max(90.0, cindy_bid + 2.0)
        elif supply <= 19:
            target = max(78.0, cindy_bid * 0.82)
        else:
            target = 62.0
    elif moderate_need:
        if supply <= 16:
            target = max(74.0, cindy_bid * 0.72)
        elif supply <= 19:
            target = max(56.0, min(72.0, pressure + 2.0))
        else:
            target = 42.0
    else:
        if scarcity < 0.7:
            target = 52.0 if supply <= 17 else 36.0
        elif scarcity < 0.9:
            target = 28.0
        else:
            target = 16.0

    days_left = max(1, 10 - day + 1)
    reserve_floor = 22.0 * days_left
    if budget < reserve_floor:
        target = min(target, max(10.0, budget / float(days_left)))

    if day >= 8 and hp > 5 and no_water == 0:
        target *= 0.9

    bid = max(0.0, min(budget, target))
    return bid
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    affordable_caps = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            affordable_caps.append(min(opp.get('budget', 0), opp.get('daily_salary', DAILY_SALARY) * 2.2))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    high_supply = supply >= 20
    low_supply = supply <= 17

    top_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.8
    top_affordable = max(affordable_caps) if affordable_caps else top_prev

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

    if low_supply:
        danger += 1
    if urgent_opp >= 2:
        danger += 1

    if danger >= 5:
        target = max(DAILY_SALARY * 1.45, min(top_affordable + 2.0, budget))
    elif danger >= 3:
        target = max(DAILY_SALARY * 1.05, min(top_prev + 1.5, top_affordable + 1.0, budget))
    else:
        if high_supply and hp >= 7 and no_water == 0:
            target = DAILY_SALARY * 0.38
        elif top_prev > DAILY_SALARY * 1.8:
            target = DAILY_SALARY * 0.42
        else:
            target = max(DAILY_SALARY * 0.52, min(top_prev * 0.72, DAILY_SALARY * 0.9))

    reserve_floor = DAILY_SALARY * 2.2 if hp > 3 else DAILY_SALARY * 1.0
    if budget > reserve_floor:
        target = min(target, budget - reserve_floor + DAILY_SALARY * 0.25)

    if hp <= 2 or no_water >= 2:
        target = max(target, DAILY_SALARY * 1.1)

    target = max(0.0, min(float(target), float(budget)))
    return float(round(target, 2))
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return max(0.0, min(budget, 18.0))

    units = int(supply // WATER_REQ)
    if units < 1:
        units = 1

    strong_bob = None
    eric = None
    prev_bids = []
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if agent_id == 'Bob':
            strong_bob = opp
        if agent_id == 'Eric':
            eric = opp

    bob_prev = 0.0
    if strong_bob is not None:
        prev = strong_bob.get('previous_trace', {})
        if prev.get('bid') is not None:
            bob_prev = float(prev.get('bid'))
        else:
            bob_prev = 78.0

    eric_prev = 0.0
    if eric is not None:
        prev = eric.get('previous_trace', {})
        if prev.get('bid') is not None:
            eric_prev = float(prev.get('bid'))

    alive_count = len(alive)
    scarcity = alive_count - units

    if hp <= 2 or no_water >= 2:
        emergency = max(92.0, bob_prev + 6.0)
        if eric_prev > 120 and hp > 1:
            emergency = max(emergency, 110.0)
        return max(0.0, min(budget, emergency))

    if units >= alive_count:
        return max(0.0, min(budget, 8.0))

    if eric_prev >= 130 and scarcity >= 2 and hp >= 5 and no_water == 0:
        return max(0.0, min(budget, 12.0))

    if scarcity >= 2:
        target = max(0.0, bob_prev + 2.5)
        target = max(target, 79.0)
        target = min(target, 96.0)
        if hp >= 7 and budget > 500:
            target += 2.0
        return max(0.0, min(budget, target))

    target = max(0.0, bob_prev + 1.5)
    target = max(target, 72.0)
    target = min(target, 88.0)

    if hp <= 4 or no_water == 1:
        target = max(target, 84.0)

    if day >= 8 and hp >= 6:
        target -= 4.0

    return max(0.0, min(budget, target))
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    winners_est = int(supply // WATER_REQ)
    if winners_est < 1:
        winners_est = 1

    prev_bids = []
    opp_risk = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            opp_risk += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 3 or no_water_days >= 1
    very_urgent = hp <= 2 or no_water_days >= 2

    if not alive_opponents:
        if urgent:
            return float(min(budget, 42.0))
        return float(min(budget, 18.0))

    if very_urgent:
        target = max(78.0, highest_prev + 2.5)
        return float(min(budget, target))

    if urgent:
        if winners_est >= 2:
            target = max(58.0, avg_prev * 0.72)
        else:
            target = max(82.0, highest_prev + 3.0)
        return float(min(budget, target))

    if winners_est >= 2:
        if highest_prev >= 130:
            target = 34.0
        elif avg_prev >= 120:
            target = 39.0
        else:
            target = 44.0
        if opp_risk >= 2:
            target += 4.0
        if rich_opp >= 2:
            target -= 2.0
        if day >= 8 and budget > 220:
            target += 3.0
        return float(max(0.0, min(budget, target)))

    target = 63.0
    if highest_prev >= 130:
        target = 71.0
    elif avg_prev >= 120:
        target = 67.0
    if opp_risk >= 2:
        target += 6.0
    if day >= 8 and hp >= 6 and budget > 180:
        target += 4.0
    return float(max(0.0, min(budget, target)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_opp += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    base = 18.0 + 18.0 * supply_pressure

    if supply <= 16:
        base += 10.0
    elif supply >= 23:
        base -= 5.0

    if no_water >= 2:
        base = max(base, 66.0)
    elif no_water >= 1:
        base = max(base, 46.0)

    if hp <= 3:
        base = max(base, 64.0)
    elif hp <= 5:
        base = max(base, 48.0)

    if highest_prev >= 100:
        if hp >= 6 and no_water == 0 and supply >= 19:
            base = min(base, 24.0)
        else:
            base = max(base, 52.0)
    elif highest_prev >= 85:
        if hp >= 7 and no_water == 0:
            base = min(base, 26.0)
        else:
            base = max(base, highest_prev * 0.62)
    elif highest_prev > 0:
        target = avg_prev + 2.5
        if supply <= 17 or no_water >= 1 or hp <= 5:
            base = max(base, target)
        else:
            base = min(max(base, target * 0.9), 42.0)

    if rich_opp >= 2 and supply <= 17 and hp >= 6 and no_water == 0:
        base = min(base, 28.0)

    days_left = max(0, 10 - day)
    reserve_target = days_left * 22.0
    affordable_cap = max(0.0, budget - reserve_target)
    if no_water >= 1 or hp <= 4:
        affordable_cap = budget

    bid = min(base, budget)
    if affordable_cap > 0:
        bid = min(bid, max(affordable_cap, 16.0))

    if (hp <= 3 or no_water >= 2) and budget > 0:
        bid = max(bid, min(budget, 68.0))

    if bid < 0:
        bid = 0.0
    return float(round(min(bid, budget), 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    desperate_opp = False
    rich_aggro_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp = True
        if opp.get('budget', 0) > 900:
            rich_aggro_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    if hp <= 2 or no_water >= 2:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        target = max(DAILY_SALARY * 0.78, highest_prev + 1.5)
    else:
        base = DAILY_SALARY * (0.38 + 0.18 * scarcity)
        if highest_prev >= 110:
            target = DAILY_SALARY * 0.32
        elif highest_prev >= 85:
            target = DAILY_SALARY * 0.42
        elif highest_prev > 0:
            target = max(base, min(highest_prev + 1.0, DAILY_SALARY * 0.72))
        else:
            target = base

    if desperate_opp and hp > 4 and no_water == 0:
        target *= 0.9
    if rich_aggro_count >= 2 and hp > 4 and no_water == 0:
        target *= 0.88

    if supply >= 23 and hp > 4:
        target *= 0.9
    elif supply <= 17:
        target *= 1.08

    if avg_prev >= 95 and hp > 4 and no_water == 0:
        target *= 0.9

    reserve = 0.0
    if hp > 4 and no_water == 0:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.5

    cap = max(0.0, budget - reserve)
    if hp <= 2 or no_water >= 2:
        cap = budget

    bid = min(target, cap if cap > 0 else budget)
    bid = max(0.0, min(bid, budget))

    if hp > 5 and no_water == 0 and highest_prev >= 120:
        bid = min(bid, DAILY_SALARY * 0.28)

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_budgets = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 35.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    rich_opp = max(opp_budgets) if opp_budgets else 0.0

    units = supply / WATER_REQ
    very_tight = units < 1.35
    tight = units < 1.6
    ample = units > 1.8

    danger = hp <= 2 or no_water_days >= 2
    caution = hp <= 4 or no_water_days >= 1

    if danger:
        bid = max(62.0, highest_prev + 3.0)
        if very_tight:
            bid = max(bid, 78.0)
        return float(min(budget, bid))

    if very_tight:
        if highest_prev >= 80:
            bid = 81.5 if hp > 4 else 88.0
        elif highest_prev >= 60:
            bid = highest_prev + 2.2
        else:
            bid = 63.0
        return float(min(budget, bid))

    if tight:
        if caution:
            bid = max(58.0, highest_prev + 1.5)
        else:
            if avg_prev >= 65:
                bid = 46.0
            else:
                bid = max(41.0, highest_prev * 0.78)
        return float(min(budget, bid))

    if ample:
        if caution:
            bid = max(34.0, highest_prev * 0.55)
        else:
            bid = 22.0
            if rich_opp > budget * 1.5 and highest_prev < 50:
                bid = 18.0
        return float(min(budget, bid))

    bid = 30.0 if hp > 4 else 48.0
    if highest_prev > 0:
        bid = max(bid, min(highest_prev + 1.0, 60.0))
    return float(min(budget, bid))
"""
