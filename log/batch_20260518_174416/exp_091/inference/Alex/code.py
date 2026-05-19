# ============================================================
# Experiment: exp_091
# Agent: Alex
# Source: exp_091
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

    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    supply = day_context['supply']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return min(budget, 20)
        return min(budget, 8)

    prev_bids = []
    desperate_opp = False
    rich_opp = False
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_opp = True
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp = True
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)

    expected_units = int(supply / WATER_REQ)
    player_count = 1 + len(alive_opponents)
    scarcity = expected_units < player_count

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

    if hp <= 1:
        target = DAILY_SALARY * 0.98
    elif hp <= 2 or no_water >= 2:
        target = max(DAILY_SALARY * 0.88, highest_prev + 2)
    elif no_water >= 1:
        target = max(DAILY_SALARY * 0.72, avg_prev + 2)
    else:
        if scarcity:
            if highest_prev >= DAILY_SALARY * 0.85:
                target = DAILY_SALARY * 0.52
            elif highest_prev > 0:
                target = max(DAILY_SALARY * 0.58, highest_prev + 1.5)
            else:
                target = DAILY_SALARY * 0.56
        else:
            if highest_prev >= DAILY_SALARY * 0.8:
                target = DAILY_SALARY * 0.34
            elif highest_prev > 0:
                target = max(DAILY_SALARY * 0.4, avg_prev * 0.82)
            else:
                target = DAILY_SALARY * 0.38

    if desperate_opp and hp > 2 and no_water == 0:
        target *= 0.9
    if rich_opp and scarcity and hp <= 3:
        target = max(target, highest_prev + 2)

    reserve_days = 2 if hp > 2 else 1
    max_affordable_today = max(0, budget - reserve_days * DAILY_SALARY * 0.35)
    if hp <= 2 or no_water >= 1:
        max_affordable_today = budget

    bid = min(target, max_affordable_today, budget)
    if bid < 0:
        bid = 0
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water >= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.8)
        return float(max(0.0, safe_bid))

    yesterday_bids = []
    aggressive_count = 0
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('budget', 0) >= 500:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(bid)
                if bid >= 70:
                    aggressive_count += 1

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    total_alive = len(alive) + 1
    seats = int(supply // WATER_REQ)
    scarce = seats <= 1
    comfortable = seats >= 2

    if hp <= 2 or no_water >= 2:
        bid = max(78.0, highest_prev + 3.0)
        return float(min(budget, bid))

    if scarce:
        if aggressive_count >= 2 or highest_prev >= 90:
            bid = 92.0 if hp >= 5 else 108.0
        elif highest_prev >= 70:
            bid = highest_prev + 2.5
        else:
            bid = 76.0
        if desperate_count >= 1:
            bid += 6.0
        return float(min(budget, bid))

    if comfortable:
        if aggressive_count >= 2:
            bid = 24.0
        elif avg_prev >= 70:
            bid = 31.0
        else:
            bid = 36.0

        if rich_count >= 2:
            bid -= 4.0
        if hp <= 4 or no_water >= 1:
            bid += 16.0
        if day >= 8 and hp >= 6:
            bid -= 6.0
        bid = max(12.0, bid)
        return float(min(budget, bid))

    bid = 42.0
    if highest_prev >= 80:
        bid = 48.0
    if hp <= 4 or no_water >= 1:
        bid += 18.0
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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

    alive_opponents = []
    prev_bids = []
    cindy_bid = None
    max_opp_budget = 0.0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0.0) > max_opp_budget:
                max_opp_budget = opp.get('budget', 0.0)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid_val = float(prev.get('bid', 0.0))
                prev_bids.append(bid_val)
                if agent_id == 'Cindy':
                    cindy_bid = bid_val

    if not alive_opponents:
        return float(min(budget, 18.0))

    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    competitors = len(alive_opponents) + 1
    scarcity = supply / float(WATER_REQ * competitors)

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

    if scarcity < 0.45:
        danger += 3
    elif scarcity < 0.7:
        danger += 2
    elif scarcity < 1.0:
        danger += 1

    if day >= 8:
        danger += 1

    if cindy_bid is None:
        cindy_bid = pressure

    if danger >= 6:
        target = max(63.0, cindy_bid + 2.0, pressure + 1.0)
    elif danger >= 4:
        target = max(46.0, min(72.0, cindy_bid * 0.55 + 6.0), pressure * 0.7 + 3.0)
    elif danger >= 2:
        target = max(24.0, min(52.0, cindy_bid * 0.28 + 4.0), pressure * 0.45 + 2.0)
    else:
        target = 12.0
        if scarcity < 0.9:
            target = 18.0
        if pressure > 0:
            target = max(target, min(28.0, pressure * 0.22 + 1.5))

    if cindy_bid is not None and cindy_bid > 120 and danger <= 3:
        target = min(target, 26.0)

    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0 and danger < 5:
        soft_cap = min(budget, max(18.0, budget / float(reserve_days + 1) + 8.0))

    if hp <= 2 or no_water >= 2:
        soft_cap = budget

    bid = min(budget, target, soft_cap)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opps:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 60.0))
        return float(min(budget, 20.0))

    prev_bids = []
    rich_aggressive = 0
    desperate_opps = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 120:
                rich_aggressive += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opps += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (float(supply) <= 17.0)
    comfortable_supply = (float(supply) >= 22.0)

    if hp <= 1 or no_water_days >= 2:
        bid = 160.0 if scarcity else 120.0
    elif hp <= 2 or no_water_days >= 1:
        if highest_prev >= 140:
            bid = 145.0 if scarcity else 110.0
        else:
            bid = max(85.0, highest_prev + 6.0)
    else:
        if scarcity:
            if rich_aggressive >= 1:
                bid = 72.0
            else:
                bid = max(58.0, min(95.0, avg_prev + 4.0))
        elif comfortable_supply:
            bid = 24.0 if rich_aggressive >= 1 else 32.0
        else:
            if highest_prev >= 140:
                bid = 30.0
            elif highest_prev >= 90:
                bid = 42.0
            else:
                bid = max(34.0, min(55.0, avg_prev + 3.0))

    if desperate_opps >= 2 and hp >= 4 and no_water_days == 0:
        bid = min(bid, 35.0)

    if day >= 8:
        if hp <= 3:
            bid = max(bid, 95.0)
        else:
            bid = min(max(bid, 40.0), 75.0)

    if budget < bid:
        if hp <= 2 or no_water_days >= 1:
            bid = budget
        else:
            bid = min(budget, bid)

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = 0
    desperate_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 4:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    if bid >= DAILY_SALARY * 0.9:
                        strong_prev += 1

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.35))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

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
    if no_water_days >= 2:
        urgency += 3
    elif no_water_days >= 1:
        urgency += 2

    pressure = 0
    if highest_prev >= DAILY_SALARY * 1.4:
        pressure = 3
    elif highest_prev >= DAILY_SALARY * 0.95:
        pressure = 2
    elif highest_prev >= DAILY_SALARY * 0.45:
        pressure = 1

    if urgency >= 5:
        bid = max(DAILY_SALARY * 1.15, highest_prev + 4.0)
    elif urgency >= 3:
        bid = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
    else:
        if scarcity == 2:
            bid = max(DAILY_SALARY * 0.72, avg_prev + 3.0, highest_prev * 0.92)
        elif scarcity == 1:
            bid = max(DAILY_SALARY * 0.55, avg_prev + 1.5)
        else:
            if pressure >= 2 and hp > 5 and no_water_days == 0:
                bid = DAILY_SALARY * 0.28
            else:
                bid = max(DAILY_SALARY * 0.38, avg_prev * 0.72)

    if rich_opp >= 1 and scarcity >= 1:
        bid += 4.0
    if desperate_opp >= 2 and urgency == 0 and scarcity == 0:
        bid -= 4.0
    if day >= 8 and hp > 5 and no_water_days == 0:
        bid *= 0.9

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    max_spend = budget
    if budget > reserve_floor:
        max_spend = budget - reserve_floor + DAILY_SALARY * 0.35
    if urgency >= 3:
        max_spend = budget

    bid = min(bid, max_spend)
    bid = min(bid, budget)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= budget:
                rich_threat += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, max(1.0, DAILY_SALARY * 0.35)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 2 if supply < WATER_REQ * 2 else 1
    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if day >= 8:
        urgency += 1
    urgency += scarcity

    if urgency >= 8:
        target = max(95.0, highest_prev + 3.0)
    elif urgency >= 6:
        target = max(82.0, highest_prev + 1.5)
    elif urgency >= 4:
        if highest_prev >= 110:
            target = 72.0
        else:
            target = max(60.0, avg_prev * 0.78)
    else:
        if highest_prev >= 100:
            target = 28.0
        elif highest_prev >= 85:
            target = 42.0
        else:
            target = max(36.0, avg_prev * 0.6 if avg_prev > 0 else 38.0)

    if rich_threat >= 2 and urgency < 6:
        target *= 0.92
    if budget < 120:
        target = min(target, budget * (0.72 if urgency >= 6 else 0.5))
    elif budget < 220 and urgency < 6:
        target = min(target, budget * 0.42)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, min(budget, highest_prev + 2.5 if highest_prev > 0 else 88.0))

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    rich_threats = 0
    desperate_threats = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
        if opp.get('budget', 0) >= 140:
            rich_threats += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_threats += 1

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
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
        urgency += 0.35
    elif no_water_days == 1:
        urgency += 0.15

    market_pressure = 0.0
    if highest_prev_bid >= 200:
        market_pressure = 0.55
    elif highest_prev_bid >= 140:
        market_pressure = 0.4
    elif highest_prev_bid >= 90:
        market_pressure = 0.25
    elif highest_prev_bid >= 40:
        market_pressure = 0.12

    base = DAILY_SALARY * (0.22 + 0.33 * scarcity + urgency + market_pressure)
    base += rich_threats * 6.0 + desperate_threats * 4.0

    if supply >= 23 and hp >= 6 and no_water_days == 0:
        base *= 0.72
    elif supply <= 17:
        base *= 1.18

    if highest_prev_bid > 0:
        if hp <= 3 or no_water_days >= 2:
            reactive = min(highest_prev_bid + 6.0, DAILY_SALARY * 1.25)
        elif supply <= 18:
            reactive = min(max(avg_prev_bid + 4.0, highest_prev_bid * 0.78), DAILY_SALARY * 1.05)
        else:
            reactive = min(max(avg_prev_bid * 0.72, highest_prev_bid * 0.58), DAILY_SALARY * 0.9)
        bid = max(base, reactive)
    else:
        bid = base

    if day >= 8:
        bid *= 1.12
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        bid *= 1.18

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve_floor = DAILY_SALARY * 0.5

    max_affordable = budget
    if budget > reserve_floor:
        max_affordable = budget - reserve_floor + DAILY_SALARY * 0.35
    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    if max_affordable < 0:
        max_affordable = 0.0

    bid = min(bid, max_affordable)
    bid = min(bid, budget)

    min_defensive = 0.0
    if hp <= 2 or no_water_days >= 2:
        min_defensive = min(budget, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water_days == 1:
        min_defensive = min(budget, DAILY_SALARY * 0.58)

    if bid < min_defensive:
        bid = min_defensive

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80 and opp.get('budget', 0) > budget:
                    rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    urgent = hp <= 3 or no_water_days >= 2
    semi_urgent = hp <= 5 or no_water_days >= 1

    if urgent:
        if tight_supply:
            bid = max(0.95 * DAILY_SALARY, max_prev + 3.0)
        else:
            bid = max(0.72 * DAILY_SALARY, min(max_prev + 1.5, 0.95 * DAILY_SALARY))
        return float(min(budget, bid))

    if ample_supply and hp >= 7 and no_water_days == 0:
        bid = 8.0 if rich_aggressive > 0 else 12.0
        return float(min(budget, bid))

    if tight_supply:
        if max_prev >= 110:
            bid = 24.0 if hp >= 7 else 58.0
        elif max_prev >= 80:
            bid = 32.0 if hp >= 7 else 62.0
        else:
            bid = max(28.0, avg_prev + 3.0)
        return float(min(budget, bid))

    if semi_urgent:
        if max_prev >= 100:
            bid = 48.0
        elif max_prev >= 70:
            bid = 42.0
        else:
            bid = max(30.0, avg_prev + 2.0)
        return float(min(budget, bid))

    if max_prev >= 120:
        bid = 14.0
    elif max_prev >= 90:
        bid = 18.0
    elif max_prev >= 60:
        bid = 24.0
    else:
        bid = 27.0

    if day >= 8 and hp >= 6:
        bid *= 0.9

    return float(min(budget, bid))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp_bid = []
    rich_aggressive_bid = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                    urgent_opp_bid.append(float(bid))
                if opp.get('budget', 0) >= 140:
                    rich_aggressive_bid.append(float(bid))

    if not alive_opps:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    danger = 0.0
    if hp <= 2:
        danger += 0.7
    elif hp <= 4:
        danger += 0.4
    if no_water >= 2:
        danger += 0.8
    elif no_water >= 1:
        danger += 0.35
    if day >= 8:
        danger += 0.15

    baseline = DAILY_SALARY * (0.28 + 0.32 * scarcity + danger)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    target = baseline

    if supply <= 17:
        if rich_aggressive_bid:
            target = max(target, max(rich_aggressive_bid) + 2.0)
        else:
            target = max(target, highest_prev + 1.5)
    elif danger >= 0.7:
        target = max(target, highest_prev + 1.0)
    elif danger >= 0.35:
        target = max(target, avg_prev * 0.92)
    else:
        if highest_prev >= DAILY_SALARY * 1.8:
            target = min(target, DAILY_SALARY * 0.35)
        elif highest_prev >= DAILY_SALARY * 1.2:
            target = min(target, DAILY_SALARY * 0.5)
        else:
            target = max(target, avg_prev * 0.75)

    if urgent_opp_bid and danger < 0.35 and supply >= 20:
        target = min(target, DAILY_SALARY * 0.38)

    reserve_days = max(1, 11 - day)
    soft_cap = budget / float(reserve_days)
    if danger < 0.35:
        target = min(target, soft_cap * 1.15)
    elif danger < 0.7:
        target = min(target, max(soft_cap * 1.6, target))
    else:
        target = min(max(target, soft_cap * 1.4), budget)

    if hp <= 2 or no_water >= 2:
        target = max(target, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water >= 1:
        target = max(target, DAILY_SALARY * 0.7)

    target = max(0.0, min(float(budget), float(target)))
    return float(round(target, 2))
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    opp_pressures = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                b = float(bid)
                prev_bids.append(b)
                req = float(opp.get('water_requirement', WATER_REQ))
                sal = float(opp.get('daily_salary', DAILY_SALARY))
                pressure = b / max(1.0, sal)
                scarcity = req / max(1.0, supply)
                opp_pressures.append((pressure, scarcity, b, opp))

    if not alive_opps:
        return min(budget, 18.0)

    slots = supply / float(WATER_REQ)
    alive_count = len(alive_opps) + 1
    scarcity_ratio = alive_count / max(0.5, slots)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water >= 2:
        danger += 3
    elif no_water == 1:
        danger += 1
    if scarcity_ratio >= 2.8:
        danger += 2
    elif scarcity_ratio >= 2.1:
        danger += 1
    if day >= 8:
        danger += 1

    rich_aggressive = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid')
        if b is None:
            continue
        if float(b) >= 0.9 * float(opp.get('daily_salary', DAILY_SALARY)):
            rich_aggressive += 1

    if danger >= 5:
        target = max(62.0, highest_prev + 6.0, avg_prev + 8.0)
    elif danger >= 3:
        target = max(44.0, min(78.0, highest_prev + 2.5), avg_prev + 3.0)
    else:
        if rich_aggressive >= 2 and highest_prev >= 90.0:
            target = 8.0
        elif highest_prev >= 140.0:
            target = 10.0
        elif highest_prev >= 90.0:
            target = 14.0
        elif highest_prev >= 50.0:
            target = 24.0
        else:
            target = max(22.0, avg_prev * 0.75 + 3.0)

    if supply <= 16.0:
        target += 8.0
    elif supply >= 23.0 and danger <= 2:
        target -= 4.0

    if budget < target:
        if danger >= 4:
            target = budget
        else:
            target = min(budget, max(0.0, budget * 0.55))

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if danger <= 2:
        reserve_floor = min(budget, days_left * 10.0)
    elif danger == 3:
        reserve_floor = min(budget, days_left * 6.0)

    bid = min(budget - reserve_floor, target) if budget > reserve_floor else min(budget, target)
    if danger >= 4:
        bid = max(bid, min(budget, 63.0 if hp <= 2 or no_water >= 2 else 52.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(round(bid, 2))
"""
