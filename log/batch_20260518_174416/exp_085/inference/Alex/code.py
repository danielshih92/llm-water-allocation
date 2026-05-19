# ============================================================
# Experiment: exp_085
# Agent: Alex
# Source: exp_085
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])

    opponents_count = len(alive)
    players = opponents_count + 1

    affordable_days = 0
    if DAILY_SALARY > 0:
        affordable_days = budget / float(DAILY_SALARY)

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

    if affordable_days < 2:
        urgency += 2
    elif affordable_days < 4:
        urgency += 1

    scarcity = 0
    if players > 0:
        scarcity = players * WATER_REQ - supply

    if scarcity >= WATER_REQ * 2:
        urgency += 2
    elif scarcity > 0:
        urgency += 1

    highest_prev = max(prev_bids) if prev_bids else None
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else None

    if urgency >= 6:
        bid = DAILY_SALARY * 0.95
    elif urgency >= 4:
        bid = DAILY_SALARY * 0.8
    elif urgency >= 2:
        bid = DAILY_SALARY * 0.62
    else:
        bid = DAILY_SALARY * 0.42

    if highest_prev is not None:
        if highest_prev >= DAILY_SALARY * 0.9:
            if urgency <= 1:
                bid = min(bid, DAILY_SALARY * 0.35)
            else:
                bid = max(bid, DAILY_SALARY * 0.9)
        elif highest_prev >= DAILY_SALARY * 0.65:
            bid = max(bid, min(DAILY_SALARY * 0.88, highest_prev + 1.5))
        else:
            bid = max(bid, highest_prev + 1.0)
    elif avg_prev is not None:
        bid = max(bid, avg_prev + 1.0)

    day = day_context['day']
    if day >= 8 and hp > 4 and no_water == 0:
        bid *= 0.92

    if supply >= players * WATER_REQ and urgency <= 2:
        bid = min(bid, DAILY_SALARY * 0.38)

    if budget <= 0:
        return 0

    if bid > budget:
        bid = budget
    if bid < 0:
        bid = 0
    return float(bid)
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

    alive_opponents = []
    prev_bids = []
    dangerous_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if opp.get('water_requirement', WATER_REQ) >= WATER_REQ:
                    dangerous_bids.append(bid)

    if not alive_opponents:
        return max(0.0, min(float(budget), 18.0))

    ref_bids = dangerous_bids if dangerous_bids else prev_bids
    highest_prev = max(ref_bids) if ref_bids else 0.0
    avg_prev = sum(ref_bids) / len(ref_bids) if ref_bids else 0.0

    tight_supply = supply <= 18.0
    ample_supply = supply >= 22.0
    critical = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if critical:
        bid = highest_prev + 2.5 if highest_prev > 0 else DAILY_SALARY * 1.05
    elif tight_supply:
        if highest_prev >= 95.0:
            bid = highest_prev + 1.5
        else:
            bid = max(78.0, highest_prev + 2.0)
    elif ample_supply:
        if hp >= 8 and no_water_days == 0:
            bid = 26.0
        else:
            bid = 52.0 if avg_prev >= 90.0 else 44.0
    else:
        if pressured:
            bid = max(72.0, highest_prev + 1.0 if highest_prev > 0 else 72.0)
        else:
            bid = 48.0 if avg_prev >= 90.0 else 58.0

    if day >= 8 and hp >= 7 and no_water_days == 0 and not tight_supply:
        bid = min(bid, 40.0)

    if budget < bid:
        if critical:
            bid = budget
        else:
            bid = min(float(budget), max(0.0, budget * 0.75))

    if budget <= 0:
        return 0.0

    return max(0.0, min(float(budget), float(bid)))
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return min(budget, 20.0)

    serious = []
    prev_bids = []
    for agent_id, opp in alive:
        if opp.get('budget', 0) > 0:
            serious.append((agent_id, opp))
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    bob_like = 0
    cindy_like = 0
    for agent_id, opp in serious:
        prev = opp.get('previous_trace', {})
        pbid = None
        if prev and prev.get('bid') is not None:
            pbid = float(prev['bid'])
        if pbid is not None:
            if 95 <= pbid <= 120:
                bob_like += 1
            if pbid >= 130:
                cindy_like += 1

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    urgent = hp <= 4 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    target = 0.0

    if critical:
        if tight_supply:
            target = 136.0
        else:
            target = 114.0
    elif urgent:
        if tight_supply:
            target = 113.5 if cindy_like == 0 else 136.0
        elif medium_supply:
            target = 108.0
        else:
            target = 82.0
    else:
        if tight_supply:
            if bob_like >= 1 and cindy_like >= 1:
                target = 109.0
            elif cindy_like >= 1:
                target = 72.0
            else:
                target = 96.0
        elif medium_supply:
            target = 62.0
        else:
            target = 28.0

    if day >= 8 and hp <= 6:
        target = max(target, 108.0 if not tight_supply else 113.5)

    if budget < target:
        if critical:
            return float(budget)
        fallback = min(budget, max(0.0, budget * 0.72))
        return float(fallback)

    return float(min(budget, target))
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

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    aggressive_bids = []
    weak_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= DAILY_SALARY * 1.2:
                aggressive_bids.append(float(bid))
            if bid <= DAILY_SALARY * 0.45:
                weak_count += 1
        else:
            weak_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    total_alive = len(alive_opponents)
    low_supply = supply <= 17
    high_supply = supply >= 22
    urgent = hp <= 2 or no_water_days >= 2
    caution = hp <= 4 or no_water_days >= 1

    target = 0.0

    if urgent:
        if highest_prev > 0:
            target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
        else:
            target = DAILY_SALARY * 0.9
    elif low_supply:
        if aggressive_bids:
            target = min(max(DAILY_SALARY * 0.72, avg_prev * 0.72), DAILY_SALARY * 1.02)
        elif highest_prev > 0:
            target = max(DAILY_SALARY * 0.62, highest_prev + 1.5)
        else:
            target = DAILY_SALARY * 0.58
    elif high_supply:
        if caution:
            target = max(DAILY_SALARY * 0.42, min(highest_prev * 0.55 if highest_prev > 0 else DAILY_SALARY * 0.42, DAILY_SALARY * 0.6))
        else:
            target = DAILY_SALARY * 0.22
    else:
        if highest_prev >= DAILY_SALARY * 1.4:
            target = DAILY_SALARY * 0.38 if not caution else DAILY_SALARY * 0.68
        elif highest_prev >= DAILY_SALARY * 0.8:
            target = max(DAILY_SALARY * 0.48, highest_prev * 0.78)
        elif highest_prev > 0:
            target = max(DAILY_SALARY * 0.4, highest_prev + 1.0)
        else:
            target = DAILY_SALARY * 0.34

    if weak_count >= total_alive - 1 and not urgent:
        target *= 0.82

    reserve_floor = 0.0
    days_left_est = max(0, 10 - int(day))
    if days_left_est > 0:
        reserve_floor = min(budget * 0.35, days_left_est * DAILY_SALARY * 0.18)

    max_spend = budget - reserve_floor
    if urgent:
        max_spend = budget
    elif caution:
        max_spend = max(max_spend, budget * 0.55)
    else:
        max_spend = max(max_spend, budget * 0.35)

    bid = min(target, max_spend, budget)

    if urgent:
        bid = max(bid, min(budget, DAILY_SALARY * 0.88))
    elif caution and low_supply:
        bid = max(bid, min(budget, DAILY_SALARY * 0.58))

    if bid < 0:
        bid = 0.0

    return float(round(min(bid, budget), 2))
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
    yesterday_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 200:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # With supply 15-25 and req 13, at most one player can receive water each day.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Need score: prioritize survival, especially after missed water.
    need = 0.0
    if hp <= 2:
        need += 1.0
    elif hp <= 4:
        need += 0.65
    elif hp <= 6:
        need += 0.35

    if no_water >= 2:
        need += 1.0
    elif no_water == 1:
        need += 0.45

    # Endgame urgency.
    if day >= 8:
        need += 0.2

    # Pressure from yesterday's market.
    pressure = 0.0
    if highest_prev >= 120:
        pressure += 0.45
    elif highest_prev >= 90:
        pressure += 0.3
    elif highest_prev >= 60:
        pressure += 0.15

    if avg_prev >= 90:
        pressure += 0.15
    elif avg_prev >= 60:
        pressure += 0.08

    if urgent_opp >= 2:
        pressure += 0.18
    elif urgent_opp == 1:
        pressure += 0.08

    if rich_opp >= 2:
        pressure += 0.1

    score = need + pressure + 0.55 * scarcity

    # Base conservative posture to outlast overbidders.
    if score < 0.35:
        bid = 12.0 + 10.0 * scarcity
    elif score < 0.75:
        bid = 24.0 + 18.0 * scarcity + 0.10 * highest_prev
    elif score < 1.2:
        bid = 42.0 + 20.0 * scarcity + 0.18 * highest_prev
    else:
        bid = 62.0 + 24.0 * scarcity + 0.24 * highest_prev

    # Tactical response to extreme prior overbids: don't chase unless necessary.
    if highest_prev >= 130 and hp > 3 and no_water == 0:
        bid = min(bid, 28.0 + 10.0 * scarcity)

    # If in danger, ensure competitiveness.
    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(0.92 * DAILY_SALARY + 20.0 * scarcity, budget))
    elif hp <= 4 or no_water == 1:
        bid = max(bid, 0.72 * DAILY_SALARY + 14.0 * scarcity)

    # Budget discipline.
    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days >= 3 and hp > 3:
        soft_cap = min(soft_cap, budget * 0.42)
    elif reserve_days >= 1 and hp > 2:
        soft_cap = min(soft_cap, budget * 0.58)

    bid = min(bid, soft_cap, budget)
    bid = max(0.0, bid)
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

    supply = day_context['supply']
    day = day_context['day']
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
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    dangerous_count = 0
    eric_like_pressure = 0.0
    cindy_like_pressure = 0.0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        b = None
        if prev:
            b = prev.get('bid')
        if b is not None:
            prev_bids.append(float(b))
            if b >= 120:
                dangerous_count += 1
            req = opp.get('water_requirement', WATER_REQ)
            sal = opp.get('daily_salary', DAILY_SALARY)
            if req >= 13 and sal >= 70:
                if b > eric_like_pressure:
                    eric_like_pressure = float(b)
            else:
                if b > cindy_like_pressure:
                    cindy_like_pressure = float(b)

    highest_prev = max(prev_bids) if prev_bids else 0.0

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    elif hp <= 6:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days >= 1:
        urgency += 0.35

    scarcity = 1.0 - supply_ratio

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 4.0)
    else:
        if scarcity >= 0.75:
            target = max(92.0, highest_prev * 0.78 + 8.0)
        elif scarcity >= 0.45:
            target = max(68.0, highest_prev * 0.62 + 5.0)
        else:
            target = max(36.0, highest_prev * 0.38 + 2.0)

        if dangerous_count >= 2:
            target *= 0.92
        elif eric_like_pressure >= 150 and hp > 4 and no_water_days == 0 and scarcity < 0.6:
            target *= 0.72

        if cindy_like_pressure >= 100 and scarcity >= 0.45:
            target += 6.0

        target += urgency * 18.0

        reserve = 0.0
        if day <= 3:
            reserve = 35.0
        elif day <= 6:
            reserve = 20.0
        else:
            reserve = 8.0

        max_safe = budget - reserve
        if max_safe < DAILY_SALARY * 0.25:
            max_safe = budget

        bid = min(target, max_safe)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    min_defensive = 0.0
    if hp <= 4 or no_water_days >= 1:
        min_defensive = DAILY_SALARY * 0.55
    if bid < min_defensive and budget >= min_defensive:
        bid = min_defensive

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
    strong_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 45:
                    strong_prev.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    opp_count = len(alive)
    total_players = opp_count + 1

    my_need = float(WATER_REQ)
    expected_share = float(supply) / float(total_players)
    scarcity = my_need - expected_share

    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        top_prev = 50.0
        avg_prev = 50.0

    if strong_prev:
        pressure = max(sum(strong_prev) / float(len(strong_prev)), 48.0)
    else:
        pressure = max(avg_prev, 42.0)

    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1

    if urgent:
        bid = max(pressure + 8.0, top_prev + 2.0, 62.0)
    elif scarcity >= 9:
        bid = max(pressure + 4.0, 56.0)
    elif scarcity >= 7:
        bid = max(pressure + 1.5, 49.0)
    elif scarcity >= 5:
        bid = max(avg_prev - 2.0, 41.0)
    else:
        bid = max(avg_prev - 10.0, 24.0)

    if supply <= 17:
        bid += 6.0
    elif supply <= 19:
        bid += 3.0
    elif supply >= 23:
        bid -= 5.0

    if semi_urgent:
        bid += 4.0

    if day >= 8 and hp >= 6 and no_water == 0:
        bid -= 3.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * max(0, 9 - int(day)) * 0.18
    max_affordable = max(0.0, budget - reserve_floor)
    if urgent:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    dangerous_prev.append(float(bid))

    if not alive_opps:
        return float(min(budget, max(1.0, DAILY_SALARY * 0.25)))

    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    urgent_prev = max(dangerous_prev) if dangerous_prev else high_prev

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    if hp <= 2 or no_water >= 2:
        bid = max(urgent_prev + 2.0, DAILY_SALARY * 0.95)
        return float(min(budget, bid))

    if hp <= 4 or no_water >= 1:
        target = max(avg_prev + 3.0, DAILY_SALARY * (0.72 - 0.10 * scarcity))
        target = min(target, DAILY_SALARY * 1.15)
        return float(min(budget, target))

    if high_prev >= 150:
        bid = DAILY_SALARY * (0.18 + 0.10 * scarcity)
    elif high_prev >= 110:
        bid = DAILY_SALARY * (0.28 + 0.12 * scarcity)
    elif high_prev > 0:
        bid = max(DAILY_SALARY * 0.42, avg_prev + 2.5)
    else:
        bid = DAILY_SALARY * 0.45

    if day >= 8 and hp >= 6:
        bid *= 0.9

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.55)

    bid = max(0.0, min(budget, bid))
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        base = 18.0 if hp > 3 else 42.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    strong_prev = []
    cindy_bid = None
    david_bid = None
    for oid, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 60.0:
                strong_prev.append(float(bid))
        if oid == 'Cindy' and bid is not None:
            cindy_bid = float(bid)
        if oid == 'David' and bid is not None:
            david_bid = float(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    david_ref = david_bid if david_bid is not None else 76.8
    cindy_ref = cindy_bid if cindy_bid is not None else 121.5

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

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

    if scarcity == 0 and urgency == 0:
        bid = 12.0
    elif scarcity == 0 and urgency <= 2:
        bid = 22.0
    elif scarcity == 1 and urgency == 0:
        bid = 28.0
    elif scarcity == 1 and urgency <= 2:
        bid = max(38.0, min(58.0, david_ref - 10.0))
    elif scarcity == 2 and urgency == 0:
        bid = 32.0
    elif scarcity == 2 and urgency <= 2:
        bid = max(52.0, min(74.0, david_ref + 1.5))
    else:
        bid = max(68.0, min(92.0, david_ref + 6.0))

    if hp <= 2 or no_water >= 2:
        if cindy_ref < 110.0:
            bid = max(bid, min(105.0, cindy_ref + 2.0))
        else:
            bid = max(bid, 88.0)

    if highest_prev >= 120.0 and urgency <= 1:
        bid = min(bid, 26.0)

    if day >= 8 and hp > 5 and no_water == 0:
        bid = min(bid, 24.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 35.0
    affordable = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water >= 2:
        affordable = budget

    final_bid = min(budget, bid)
    if affordable > 0:
        final_bid = min(final_bid, max(affordable, min(budget, 18.0 if urgency == 0 else final_bid)))
    else:
        final_bid = min(final_bid, budget)

    if final_bid < 0:
        final_bid = 0.0
    return float(final_bid)
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
        return float(min(budget, 20.0))

    prev_bids = []
    bob_eric_high = False
    david_bid = None
    active_threat = 0.0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            prev_bids.append(bid)
            if oid in ('Bob', 'Eric') and bid >= 95:
                bob_eric_high = True
            if oid == 'David':
                david_bid = bid
            if bid > active_threat:
                active_threat = bid

    low_supply = supply <= 17.0
    high_supply = supply >= 22.0
    urgent = hp <= 4 or no_water >= 2
    semi_urgent = hp <= 6 or no_water >= 1

    if urgent:
        if high_supply:
            bid = 92.0
        elif low_supply:
            bid = 108.0
        else:
            bid = 98.0
        if david_bid is not None:
            bid = max(bid, david_bid + 3.0)
        return float(min(budget, bid))

    if low_supply and bob_eric_high and hp >= 7 and no_water == 0:
        return float(min(budget, 8.0))

    if high_supply:
        base = 44.0
        if david_bid is not None:
            base = max(base, david_bid + 2.0)
        elif active_threat > 0:
            base = max(base, min(65.0, active_threat * 0.6))
        if semi_urgent:
            base += 10.0
        return float(min(budget, base))

    base = 52.0
    if david_bid is not None:
        base = max(base, david_bid + 3.0)
    elif active_threat > 0:
        if active_threat >= 95.0 and hp >= 7:
            base = 18.0
        else:
            base = max(base, min(72.0, active_threat + 2.0))

    if semi_urgent:
        base += 12.0
    if day >= 8 and hp <= 6:
        base += 10.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 70.0 * (8 - day) * 0.15
    bid = min(budget, base)
    if budget - bid < reserve_floor and not semi_urgent:
        bid = max(0.0, budget - reserve_floor)

    return float(max(0.0, min(budget, bid)))
"""
