# ============================================================
# Experiment: exp_037
# Agent: Alex
# Source: exp_037
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return max(0, min(budget, 0.85 * DAILY_SALARY))
        return max(0, min(budget, 0.35 * DAILY_SALARY))

    yesterday_bids = []
    yesterday_errors = 0
    desperate_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(bid)
            if prev.get('error'):
                yesterday_errors += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1

    players = len(alive) + 1
    contested = supply < players * WATER_REQ
    very_tight = supply < max(15, players - 1) * WATER_REQ

    base = 0.42 * DAILY_SALARY
    if contested:
        base = 0.58 * DAILY_SALARY
    if very_tight:
        base = 0.68 * DAILY_SALARY

    if hp <= 2 or no_water_days >= 2:
        base = max(base, 0.9 * DAILY_SALARY)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, 0.72 * DAILY_SALARY)

    if desperate_count >= max(1, len(alive) // 2):
        base += 6

    if yesterday_bids:
        high_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        if high_prev >= 0.9 * DAILY_SALARY:
            if hp > 4 and no_water_days == 0:
                base = min(base, 0.38 * DAILY_SALARY)
            else:
                base = max(base, high_prev + 1.0)
        else:
            target = max(avg_prev + 2.0, high_prev + 0.5)
            if contested or hp <= 4 or no_water_days >= 1:
                base = max(base, target)
            else:
                base = max(base, min(target, 0.62 * DAILY_SALARY))

    if yesterday_errors > 0 and hp > 3 and no_water_days == 0:
        base -= 3

    if budget < base:
        if hp <= 2 or no_water_days >= 2:
            return max(0, budget)
        return max(0, min(budget, max(0.25 * DAILY_SALARY, budget)))

    return max(0, min(budget, base))
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
    threatening_bids = []
    active_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid > 0:
                    active_count += 1
                    threatening_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threatening_bids) if threatening_bids else 0.0
    avg_threat = sum(threatening_bids) / len(threatening_bids) if threatening_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    survival_urgency = 0.0
    if hp <= 2:
        survival_urgency += 1.0
    elif hp <= 4:
        survival_urgency += 0.6
    elif hp <= 6:
        survival_urgency += 0.25

    if no_water_days >= 2:
        survival_urgency += 1.0
    elif no_water_days >= 1:
        survival_urgency += 0.45

    if day >= 8:
        survival_urgency += 0.2

    if active_count <= 1:
        base_bid = 24.0 + 18.0 * scarcity
    else:
        base_bid = 30.0 + 26.0 * scarcity

    if highest_threat >= 120:
        pressure_bid = 60.0 + 20.0 * scarcity
    elif highest_threat >= 70:
        pressure_bid = highest_threat + 3.0
    elif highest_threat > 0:
        pressure_bid = max(base_bid, avg_threat + 4.0)
    else:
        pressure_bid = base_bid

    bid = max(base_bid, pressure_bid)

    if survival_urgency >= 1.5:
        bid = max(bid, highest_prev + 6.0 if highest_prev > 0 else 90.0)
    elif survival_urgency >= 0.8:
        bid = max(bid, highest_threat + 4.0 if highest_threat > 0 else 65.0)
    elif survival_urgency >= 0.3:
        bid = max(bid, 52.0 + 10.0 * scarcity)

    if supply >= 23 and survival_urgency < 0.8:
        bid *= 0.82
    elif supply <= 17:
        bid *= 1.12

    reserve_target = DAILY_SALARY * max(0, 10 - day)
    soft_cap = budget
    if budget > reserve_target:
        soft_cap = min(budget, budget - (reserve_target * 0.15))

    if hp <= 2 or no_water_days >= 2:
        soft_cap = budget

    bid = min(bid, soft_cap)
    bid = min(bid, budget)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_opponents += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (25.0 - float(supply)) / 10.0
    scarcity = max(0.0, min(1.0, scarcity))

    base = 24.0 + 10.0 * scarcity

    if highest_prev >= 120:
        base -= 6.0
    elif highest_prev >= 90:
        base -= 2.0
    elif highest_prev >= 50:
        base += 4.0
    else:
        base += 8.0

    base += min(urgent_opponents, 3) * 4.0
    base += min(rich_opponents, 3) * 2.0

    if hp <= 2:
        bid = max(base, 92.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(base, 68.0 + 8.0 * scarcity)
    elif hp >= 8 and no_water_days == 0 and highest_prev >= 95:
        bid = min(base, 26.0)
    else:
        bid = base

    if day >= 8:
        bid += 8.0
    if day >= 9 and hp <= 5:
        bid += 12.0

    reserve = max(0.0, (10 - int(day)) * 8.0)
    max_affordable = max(0.0, budget - reserve)
    if hp <= 3:
        max_affordable = budget

    bid = min(bid, max_affordable)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

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
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            if opp.get('budget', 0) >= budget:
                rich_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    units = max(1, int(supply / WATER_REQ))
    scarcity = 0
    if units <= 1:
        scarcity = 2
    elif units == 2:
        scarcity = 1

    top_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    desperation = 0
    if hp <= 2:
        desperation = 3
    elif hp <= 4 or no_water_days >= 1:
        desperation = 2
    elif hp <= 6:
        desperation = 1

    if desperation >= 3:
        bid = max(62.0, top_prev + 2.5)
        if scarcity == 2:
            bid = max(bid, 78.0)
        return float(min(budget, bid))

    if scarcity == 2:
        if desperation >= 2:
            bid = max(58.0, top_prev + 1.8)
        else:
            if top_prev >= 95:
                bid = 24.0
            elif top_prev >= 70:
                bid = 36.0
            else:
                bid = max(42.0, top_prev + 1.2)
        if urgent_opp >= 2:
            bid += 6.0
        return float(min(budget, bid))

    if scarcity == 1:
        if top_prev >= 100:
            bid = 20.0 if desperation == 0 else 48.0
        elif top_prev >= 75:
            bid = 26.0 if desperation == 0 else 52.0
        else:
            bid = max(28.0, avg_prev * 0.72 + 2.0)
        if desperation >= 2:
            bid += 8.0
        elif desperation == 1:
            bid += 4.0
        return float(min(budget, bid))

    bid = 18.0
    if top_prev > 0:
        if top_prev >= 100:
            bid = 14.0
        elif top_prev >= 80:
            bid = 16.0
        else:
            bid = max(18.0, min(32.0, top_prev * 0.55 + 1.0))

    if desperation >= 2:
        bid += 10.0
    elif desperation == 1:
        bid += 5.0

    if rich_opp >= 2 and top_prev < 60:
        bid += 2.0

    if day >= 8 and hp <= 5:
        bid = max(bid, 40.0)

    return float(min(budget, bid))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 100:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return max(0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    if hp <= 2 or no_water_days >= 2:
        bid = max(62.0, highest_prev + 2.5)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(48.0, avg_prev + 2.0, highest_prev * 0.92)
    else:
        if supply >= 22:
            bid = 16.0
        elif supply >= 19:
            bid = 22.0 + 6.0 * scarcity
        else:
            bid = 28.0 + 12.0 * scarcity

        if highest_prev >= 120:
            bid = min(bid, 26.0)
        elif highest_prev >= 80 and hp >= 6:
            bid = min(bid, 30.0)
        elif highest_prev > 0 and urgent_opp >= 2 and hp <= 5:
            bid = max(bid, min(highest_prev + 1.5, 55.0))

    if rich_opp >= 2 and hp >= 6:
        bid *= 0.9

    if budget < 35:
        bid = min(bid, max(8.0, budget * 0.55))
    elif budget < 70:
        bid = min(bid, budget * 0.7)
    else:
        bid = min(bid, budget * 0.82)

    bid = max(0.0, min(budget, bid))
    return bid
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
                if bid >= 90:
                    aggressive_count += 1

    players_alive = 1 + len(alive_opponents)
    units = int(supply // WATER_REQ)
    scarcity = units < players_alive
    severe_scarcity = units <= 1

    if not alive_opponents:
        base = 18.0
        if hp <= 3 or no_water_days >= 1:
            base = 35.0
        return float(min(budget, base))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 2:
        emergency = max(95.0, highest_prev + 6.0)
        return float(min(budget, emergency))

    if severe_scarcity:
        if hp <= 4 or no_water_days >= 1:
            bid = max(88.0, highest_prev + 4.0)
        else:
            bid = 14.0
        return float(min(budget, bid))

    if scarcity:
        if aggressive_count >= 2:
            if hp >= 6 and no_water_days == 0:
                bid = 16.0
            else:
                bid = max(72.0, lowest_prev + 2.0)
        else:
            bid = max(48.0, min(78.0, highest_prev * 0.72 + 3.0))
        return float(min(budget, bid))

    bid = 22.0
    if highest_prev > 0:
        bid = min(40.0, max(20.0, lowest_prev * 0.6 + 2.0))
    if hp <= 4 or no_water_days >= 1:
        bid = max(bid, 38.0)

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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_prev = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > strong_prev:
                    strong_prev = float(bid)

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    supply_units = int(supply // WATER_REQ)
    contested = supply_units <= 1

    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1

    if strong_prev >= 130:
        pressure = 'extreme'
    elif strong_prev >= 105:
        pressure = 'high'
    elif strong_prev >= 75:
        pressure = 'medium'
    else:
        pressure = 'low'

    if contested:
        if urgent:
            target = max(96.0, strong_prev + 2.0)
        elif pressure == 'extreme':
            target = 34.0
        elif pressure == 'high':
            target = max(82.0, strong_prev + 1.5)
        elif pressure == 'medium':
            target = max(68.0, strong_prev + 1.5)
        else:
            target = 58.0
    else:
        if urgent:
            target = max(62.0, strong_prev * 0.78 if strong_prev > 0 else 62.0)
        elif semi_urgent:
            target = 42.0 if pressure in ('extreme', 'high') else 36.0
        else:
            target = 24.0 if pressure in ('extreme', 'high') else 18.0

    days_left = max(0, 10 - int(day_context['day']) + 1)
    reserve = days_left * 18.0
    if urgent:
        reserve = days_left * 10.0
    affordable = max(0.0, budget - reserve)
    if affordable <= 0:
        affordable = min(budget, 28.0 if not urgent else 55.0)

    bid = min(float(budget), float(target), float(affordable))

    if urgent and bid < 55.0:
        bid = min(float(budget), max(55.0, strong_prev + 1.0 if strong_prev > 0 else 55.0))

    if hp >= 8 and no_water == 0 and contested and pressure == 'extreme':
        bid = min(bid, 26.0)

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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 20.0))

    slots = int(supply // WATER_REQ)
    total_agents = 1 + len(alive_opps)
    scarcity = total_agents - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    critical_me = (hp <= 3) or (no_water >= 2)
    stressed_me = (hp <= 5) or (no_water >= 1)

    if slots >= total_agents:
        base = 3.0
    elif slots >= len(alive_opps):
        base = 9.0
    elif slots == 1:
        base = 18.0
    else:
        base = 12.0

    if scarcity <= 0:
        bid = base
    elif critical_me:
        target = max(58.0, lowest_prev + 2.5)
        if highest_prev > 110:
            target = max(target, 72.0)
        bid = target
    elif stressed_me:
        target = max(28.0, min(55.0, lowest_prev + 1.5))
        if slots == 1:
            target = max(target, 42.0)
        bid = target
    else:
        if slots >= len(alive_opps):
            bid = 8.0
        elif highest_prev >= 120 and rich_opp >= 2:
            bid = 14.0
        elif urgent_opp >= 2:
            bid = 16.0
        else:
            bid = max(12.0, min(26.0, avg_prev * 0.22))

    if day >= 8 and hp <= 5:
        bid = max(bid, 36.0)
    if day >= 9 and no_water >= 1:
        bid = max(bid, 52.0)

    if budget < 40:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, DAILY_SALARY * 1.05)

    if bid < 0:
        bid = 0.0
    return float(bid)
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0.0)))
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    winners_possible = int(supply // WATER_REQ)
    if winners_possible < 1:
        winners_possible = 1

    urgency = 0
    if hp <= 3:
        urgency += 3
    elif hp <= 5:
        urgency += 2
    elif hp <= 7:
        urgency += 1

    if no_water >= 2:
        urgency += 3
    elif no_water >= 1:
        urgency += 1

    if day >= 8:
        urgency += 1

    if winners_possible >= 2:
        if urgency >= 4:
            bid = max(95.0, avg_prev + 2.0)
        elif urgency >= 2:
            bid = max(82.0, avg_prev + 1.0)
        else:
            bid = max(62.0, avg_prev * 0.72)
    else:
        if urgency >= 5:
            bid = max(143.0, highest_prev + 2.5)
        elif urgency >= 3:
            bid = max(136.0, highest_prev + 1.5)
        elif urgency >= 1:
            bid = max(118.0, highest_prev * 0.96)
        else:
            bid = max(35.0, highest_prev * 0.22)

    rich_aggressive = 0
    for opp in alive:
        ob = opp.get('budget', 0.0)
        prev = opp.get('previous_trace', {})
        pbid = prev.get('bid') if prev else None
        if pbid is not None and float(pbid) >= 120.0 and ob >= 500:
            rich_aggressive += 1
    if winners_possible == 1 and rich_aggressive >= 2 and urgency <= 1:
        bid = min(bid, 28.0)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, highest_prev + 3.0, 140.0)

    if budget < bid:
        if hp <= 2 or no_water >= 2:
            return float(budget)
        bid = min(bid, budget)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(round(bid, 2))
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    units = max(1, int(supply // WATER_REQ))
    scarcity = len(alive) + 1 - units

    opp_scores = []
    prev_bids = []
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid', 0) or 0
        prev_bids.append(prev_bid)

        need = 0.0
        if opp.get('no_water_days', 0) >= 1:
            need += 18.0
        if opp.get('hp', 10) <= 4:
            need += 16.0
        elif opp.get('hp', 10) <= 7:
            need += 8.0
        if opp.get('budget', 0) > 200:
            need += 6.0
        if prev.get('status') == 'won':
            need += 4.0
        if prev_bid >= 100:
            need += 8.0
        elif prev_bid >= 70:
            need += 4.0

        score_bid = prev_bid + need
        opp_scores.append(score_bid)

    highest_prev = max(prev_bids) if prev_bids else 0
    pressure_bid = max(opp_scores) if opp_scores else 0

    desperate = hp <= 3 or no_water_days >= 1
    very_safe = hp >= 8 and no_water_days == 0

    if desperate:
        if scarcity >= 3:
            bid = max(pressure_bid + 10.0, DAILY_SALARY * 1.45)
        elif scarcity >= 2:
            bid = max(pressure_bid + 7.0, DAILY_SALARY * 1.15)
        else:
            bid = max(pressure_bid + 4.0, DAILY_SALARY * 0.95)
    else:
        if scarcity >= 3:
            bid = max(pressure_bid + 5.0, DAILY_SALARY * 0.95)
        elif scarcity >= 2:
            bid = max(pressure_bid + 2.5, DAILY_SALARY * 0.72)
        elif scarcity >= 1:
            if very_safe and highest_prev >= 110:
                bid = DAILY_SALARY * 0.34
            else:
                bid = max(DAILY_SALARY * 0.52, pressure_bid * 0.78)
        else:
            if very_safe:
                bid = DAILY_SALARY * 0.28
            else:
                bid = DAILY_SALARY * 0.4

    if day >= 8 and hp >= 6 and no_water_days == 0 and scarcity <= 1:
        bid = min(bid, DAILY_SALARY * 0.45)

    reserve_floor = 0.0
    if hp >= 5:
        reserve_floor = 40.0
    if budget <= reserve_floor:
        bid = min(bid, max(0.0, budget * 0.6))

    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""
