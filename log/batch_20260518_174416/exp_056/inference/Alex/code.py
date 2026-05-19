# ============================================================
# Experiment: exp_056
# Agent: Alex
# Source: exp_056
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
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    players_alive = 1 + len(alive_opponents)
    affordable_cap = min(budget, DAILY_SALARY)

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('error') in (None, '', False):
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    supply_ratio = supply / float(WATER_REQ * players_alive)

    if hp <= 2 or no_water >= 2:
        base = DAILY_SALARY * 0.96
    elif hp <= 4 or no_water >= 1:
        base = DAILY_SALARY * 0.82
    else:
        if supply_ratio >= 1.2:
            base = DAILY_SALARY * 0.28
        elif supply_ratio >= 0.9:
            base = DAILY_SALARY * 0.48
        elif supply_ratio >= 0.7:
            base = DAILY_SALARY * 0.64
        else:
            base = DAILY_SALARY * 0.78

    pressure = 0
    if highest_prev > 0:
        if highest_prev >= DAILY_SALARY * 0.9:
            pressure += 8
        elif highest_prev >= DAILY_SALARY * 0.7:
            pressure += 5
        elif highest_prev >= DAILY_SALARY * 0.5:
            pressure += 2
    pressure += urgent_opponents * 2
    pressure += rich_opponents * 1

    target = base + pressure

    if highest_prev > 0 and (hp <= 4 or supply_ratio < 0.9):
        target = max(target, highest_prev + 1.5)
    elif avg_prev > 0 and supply_ratio < 0.7:
        target = max(target, avg_prev + 2)

    if players_alive <= 2 and hp > 4 and no_water == 0:
        target *= 0.9

    reserve_floor = 0
    if hp > 4 and no_water == 0:
        reserve_floor = DAILY_SALARY * 0.18

    bid = min(affordable_cap, max(reserve_floor, target))

    if budget < DAILY_SALARY * 0.75 and hp > 3 and no_water == 0:
        bid = min(bid, budget * 0.55)

    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget
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
    rich_aggressive = 0
    weak_opponents = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('budget', 0) >= 300 and opp.get('hp', 0) >= 5:
            rich_aggressive += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            weak_opponents += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    contested_units = int(supply / WATER_REQ)
    scarcity = contested_units <= 1
    ample = contested_units >= 2

    danger = hp <= 2 or no_water_days >= 2
    caution = hp <= 4 or no_water_days >= 1

    if danger:
        if highest_prev >= 100:
            bid = 96.0
        elif highest_prev >= 70:
            bid = highest_prev + 4.0
        else:
            bid = 78.0
    elif scarcity:
        if rich_aggressive >= 2:
            bid = 11.0 if hp >= 6 else 32.0
        elif highest_prev >= 90:
            bid = 14.0 if hp >= 6 else 40.0
        elif highest_prev >= 50:
            bid = 26.0 if hp >= 6 else highest_prev + 3.0
        else:
            bid = max(24.0, avg_prev + 2.0)
    elif ample:
        if highest_prev >= 90:
            bid = 8.0 if hp >= 5 else 22.0
        elif highest_prev >= 60:
            bid = 16.0 if hp >= 5 else 28.0
        else:
            bid = 21.0
    else:
        bid = 20.0

    if weak_opponents >= 2 and hp >= 5:
        bid *= 0.85

    if budget < 80:
        bid = min(bid, budget * 0.55 + 6.0)
    elif budget < 160:
        bid = min(bid, budget * 0.7)

    if day_context['day'] >= 8 and hp >= 5:
        bid *= 0.9
    if day_context['day'] >= 9 and hp <= 3:
        bid = max(bid, 72.0)

    bid = max(0.0, min(float(budget), float(bid)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    yesterday_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if float(opp.get('budget', 0)) >= DAILY_SALARY * 4:
                rich_opp += 1
            if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0)) <= 4:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    emergency = no_water >= 2 or hp <= 3
    pressured = no_water >= 1 or hp <= 6

    if emergency:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
        if tight_supply:
            bid = max(bid, 1.02 * highest_prev + 2.0)
        return float(min(budget, bid))

    if loose_supply and not pressured:
        bid = max(6.0, min(18.0, avg_prev * 0.28 + 4.0))
        return float(min(budget, bid))

    if tight_supply:
        if highest_prev >= 95:
            if hp >= 7 and no_water == 0:
                bid = 12.0
            else:
                bid = min(0.88 * DAILY_SALARY, highest_prev * 0.72)
        else:
            bid = max(34.0, highest_prev + 2.5)
            if urgent_opp >= 2:
                bid += 4.0
        return float(min(budget, bid))

    bid = 22.0
    if pressured:
        bid = max(bid, 42.0)
    if highest_prev > 0:
        if highest_prev >= 90:
            bid = max(bid, 24.0 if not pressured else 48.0)
        elif highest_prev >= 65:
            bid = max(bid, highest_prev * 0.7)
        else:
            bid = max(bid, highest_prev + 1.5)

    if rich_opp >= 2 and not pressured:
        bid *= 0.9
    if day >= 8 and hp >= 7 and no_water == 0:
        bid *= 0.9

    reserve_floor = DAILY_SALARY * 0.35
    if budget < reserve_floor and not pressured:
        bid = min(bid, 18.0)

    return float(min(budget, max(0.0, bid)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    threat_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
                    threat_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    high_prev = max(threat_bids) if threat_bids else (max(prev_bids) if prev_bids else 0.0)
    avg_prev = (sum(threat_bids) / len(threat_bids)) if threat_bids else ((sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.9
    elif hp <= 4:
        urgency += 0.45
    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days == 1:
        urgency += 0.35
    urgency += scarcity * 0.55
    if day >= 8:
        urgency += 0.1

    if hp <= 2 or no_water_days >= 2:
        target = max(DAILY_SALARY * 0.95, high_prev + 2.0)
    elif scarcity >= 0.7:
        target = max(DAILY_SALARY * 0.72, avg_prev + 1.5, high_prev * 0.82)
    elif scarcity >= 0.4:
        target = max(DAILY_SALARY * 0.58, avg_prev + 0.8)
    else:
        target = max(DAILY_SALARY * 0.38, avg_prev * 0.72)

    rich_threats = 0
    for opp in alive:
        if opp.get('budget', 0) >= budget and opp.get('hp', 0) > 0:
            rich_threats += 1
    if rich_threats >= 2:
        target += 4.0
    elif rich_threats == 0:
        target -= 3.0

    if high_prev >= 120 and urgency < 0.8:
        target = min(target, DAILY_SALARY * 0.52)

    if hp >= 8 and no_water_days == 0 and scarcity < 0.35:
        target = min(target, DAILY_SALARY * 0.45)

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left > 0:
        reserve_floor = min(budget * 0.45, days_left * DAILY_SALARY * 0.22)
    max_spend = max(0.0, budget - reserve_floor)

    if urgency >= 1.2:
        max_spend = budget
    elif urgency >= 0.8:
        max_spend = max(max_spend, budget * 0.7)

    bid = min(target, max_spend, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.22))

    opp_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opp_bids.append(prev.get('bid', 0))

    highest_prev = max(opp_bids) if opp_bids else 0.0
    avg_prev = sum(opp_bids) / len(opp_bids) if opp_bids else 0.0

    scarcity = 1.0
    if supply <= 16:
        scarcity = 1.25
    elif supply >= 23:
        scarcity = 0.85

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

    if day >= 8:
        danger += 1

    if danger >= 5:
        target = max(DAILY_SALARY * 1.05, highest_prev + 6.0, avg_prev + 10.0)
    elif danger >= 3:
        target = max(DAILY_SALARY * 0.72, highest_prev * 0.72 + 3.0, avg_prev + 2.0)
    else:
        if highest_prev >= 140:
            target = DAILY_SALARY * 0.24
        elif highest_prev >= 110:
            target = DAILY_SALARY * 0.30
        elif highest_prev >= 80:
            target = DAILY_SALARY * 0.42
        else:
            target = DAILY_SALARY * 0.52

    if urgent_opp >= 2:
        target += 6.0
    elif urgent_opp == 1:
        target += 3.0

    if rich_opp >= 2 and danger <= 2:
        target -= 4.0

    target *= scarcity

    if budget < DAILY_SALARY * 1.2 and danger <= 2:
        target = min(target, DAILY_SALARY * 0.38)

    if hp >= 8 and no_water == 0 and supply >= 22 and highest_prev >= 100:
        target = min(target, DAILY_SALARY * 0.22)

    bid = max(0.0, min(float(budget), float(target)))
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((oid, opp))

    if len(alive_opps) == 0:
        return float(min(budget, 20.0))

    prev_bids = []
    cindy_prev = None
    urgent_opps = 0
    rich_opps = 0

    for oid, opp in alive_opps:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opps += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 3:
            urgent_opps += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if oid == 'Cindy':
                cindy_prev = float(bid)

    slots = int(supply // WATER_REQ)
    contested = slots <= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    if cindy_prev is None:
        cindy_prev = avg_prev

    if no_water_days >= 2 or hp <= 2:
        target = max(0.92 * DAILY_SALARY, cindy_prev + 6.0, min(highest_prev + 3.0, 0.98 * DAILY_SALARY))
        return float(min(budget, max(0.0, target)))

    if contested:
        if no_water_days >= 1 or hp <= 4:
            target = max(0.82 * DAILY_SALARY, cindy_prev + 4.0)
        else:
            target = max(0.58 * DAILY_SALARY, cindy_prev * 0.55)
            if urgent_opps >= 1:
                target = min(target, 0.52 * DAILY_SALARY)
        return float(min(budget, max(0.0, target)))

    target = 0.26 * DAILY_SALARY
    if cindy_prev > 0:
        target = max(target, min(cindy_prev * 0.22, 0.38 * DAILY_SALARY))
    if rich_opps >= 2 and day >= 7:
        target = max(target, 0.34 * DAILY_SALARY)
    if no_water_days >= 1:
        target = max(target, 0.48 * DAILY_SALARY)
    if hp <= 4:
        target = max(target, 0.54 * DAILY_SALARY)

    return float(min(budget, max(0.0, target)))
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
    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 180:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if len(alive) == 0:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (25.0 - float(supply)) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.45

    urgency += scarcity * 0.55

    if hp <= 2 or no_water_days >= 2:
        bid = max(0.92 * DAILY_SALARY, avg_prev + 8.0, 72.0)
    elif hp <= 4 or no_water_days >= 1:
        if max_prev >= 150:
            bid = 58.0 + 10.0 * scarcity
        else:
            bid = max(52.0 + 12.0 * scarcity, avg_prev + 3.0)
    else:
        if supply >= 22:
            bid = 12.0 + 6.0 * scarcity
        elif supply >= 19:
            if max_prev >= 150:
                bid = 22.0 + 8.0 * scarcity
            else:
                bid = max(26.0 + 10.0 * scarcity, min(max_prev + 1.5, 48.0))
        else:
            if max_prev >= 150:
                bid = 34.0 + 12.0 * scarcity
            else:
                bid = max(38.0 + 12.0 * scarcity, min(max_prev + 2.0, 62.0))

    if desperate_opp >= 2 and urgency < 0.8:
        bid *= 0.88
    if rich_opp >= 2 and scarcity > 0.5 and urgency > 0.4:
        bid += 6.0

    reserve = 0.0
    if day <= 3:
        reserve = 110.0
    elif day <= 6:
        reserve = 70.0
    else:
        reserve = 25.0

    max_affordable = budget - reserve
    if urgency >= 1.0:
        max_affordable = budget
    elif max_affordable < 0:
        max_affordable = budget * 0.45

    if hp >= 7 and supply >= 22 and max_prev >= 160:
        bid = min(bid, 18.0)

    if bid < 0:
        bid = 0.0
    bid = min(float(bid), float(max_affordable), float(budget))

    if urgency >= 1.0 and bid < min(budget, 60.0):
        bid = min(float(budget), 60.0)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > budget:
                    rich_pressure = max(rich_pressure, float(bid))

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    low_supply = supply <= 17
    high_supply = supply >= 22
    desperate = (no_water_days >= 2) or (hp <= 3)
    urgent = (no_water_days >= 1 and hp <= 5)

    if desperate:
        target = max(DAILY_SALARY * 1.05, highest_prev + 3.0)
        if low_supply:
            target += 8.0
        return float(min(budget, target))

    if urgent:
        target = max(DAILY_SALARY * 0.8, highest_prev * 0.72 + 4.0)
        if low_supply:
            target += 6.0
        return float(min(budget, target))

    if highest_prev >= 140:
        if hp >= 7 and no_water_days == 0:
            target = DAILY_SALARY * 0.18
        else:
            target = DAILY_SALARY * 0.58
        if low_supply:
            target += 5.0
        return float(min(budget, target))

    if highest_prev >= 90:
        target = max(DAILY_SALARY * 0.42, avg_prev * 0.42)
        if low_supply:
            target += 6.0
        elif high_supply:
            target -= 4.0
        return float(min(budget, max(0.0, target)))

    target = DAILY_SALARY * 0.34
    if low_supply:
        target += 7.0
    if high_supply:
        target -= 5.0
    if rich_pressure > 100:
        target -= 3.0
    if hp >= 8 and no_water_days == 0 and day <= 3:
        target -= 3.0

    return float(min(budget, max(0.0, target)))
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
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    yesterday_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev.get('bid', 0.0))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    total_players = len(alive) + 1
    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < total_players
    very_tight = expected_units < max(1.6, total_players - 1)

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

    if danger >= 5:
        target = max(DAILY_SALARY * 1.05, highest_prev + 4.0, avg_prev + 6.0)
    elif danger >= 3:
        target = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
    else:
        if very_tight:
            target = max(DAILY_SALARY * 0.82, avg_prev + 3.0)
        elif scarcity:
            target = max(DAILY_SALARY * 0.62, avg_prev * 0.9)
        else:
            target = DAILY_SALARY * 0.34

    if highest_prev >= 120:
        if danger <= 1 and not very_tight:
            target = min(target, DAILY_SALARY * 0.28)
        elif danger <= 2:
            target = min(max(target, DAILY_SALARY * 0.72), DAILY_SALARY * 0.9)

    if desperate_count >= 2 and scarcity:
        target += 6.0
    if rich_count >= 2 and very_tight:
        target += 4.0

    remaining_days = max(0, 10 - int(day) + 1)
    reserve = max(0.0, remaining_days * DAILY_SALARY * 0.22)
    if danger <= 1 and budget < reserve + DAILY_SALARY:
        target = min(target, DAILY_SALARY * 0.3)

    bid = min(float(budget), float(target))
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
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) > 0 and opp.get('budget', 0) > 0:
                    dangerous_prev.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_danger = max(dangerous_prev) if dangerous_prev else highest_prev

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    critical = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if critical:
        bid = max(0.92 * DAILY_SALARY, highest_danger + 3.0)
    elif tight_supply:
        bid = max(0.78 * DAILY_SALARY, highest_danger + 2.0)
    elif medium_supply:
        if highest_danger >= 90:
            bid = 0.52 * DAILY_SALARY
        else:
            bid = max(0.58 * DAILY_SALARY, highest_danger + 1.5)
    else:
        if pressured:
            bid = max(0.48 * DAILY_SALARY, min(highest_danger + 1.0, 0.72 * DAILY_SALARY))
        else:
            bid = 0.34 * DAILY_SALARY

    if day >= 8:
        if critical:
            bid = max(bid, 0.95 * DAILY_SALARY)
        elif pressured:
            bid = max(bid, 0.72 * DAILY_SALARY)

    reserve = 0.0
    if day <= 7:
        reserve = max(0.0, (10 - day) * 8.0)
    max_affordable = max(0.0, budget - reserve)
    if max_affordable <= 0:
        max_affordable = budget

    bid = min(bid, max_affordable, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
"""
