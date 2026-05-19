# ============================================================
# Experiment: exp_025
# Agent: Alex
# Source: exp_025
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
    prev_bids = []
    urgent_opps = 0
    total_alive_players = 1

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            total_alive_players += 1
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opps += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None and prev.get('status') != 'error':
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0, min(budget, 21.0))

    total_required = total_alive_players * WATER_REQ
    scarcity_ratio = float(supply) / float(total_required) if total_required > 0 else 1.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    my_urgent = hp <= 2 or no_water_days >= 2
    semi_urgent = hp <= 4 or no_water_days >= 1

    if my_urgent:
        target = max(63.0, highest_prev + 2.0)
    elif scarcity_ratio < 0.5:
        target = max(52.0, highest_prev + 1.5, avg_prev + 3.0)
    elif scarcity_ratio < 0.75:
        target = max(42.0, highest_prev + 1.0, avg_prev + 2.0)
    else:
        target = max(24.0, avg_prev * 0.9)

    if urgent_opps >= 2 and not my_urgent:
        target -= 4.0
    elif urgent_opps == 0 and scarcity_ratio < 0.75:
        target += 3.0

    if semi_urgent and not my_urgent:
        target += 6.0

    if hp >= 7 and scarcity_ratio >= 0.9:
        target = min(target, 28.0)

    if budget < 25:
        target = min(target, budget)
    elif budget < 50:
        target = min(target, budget * 0.9)
    else:
        target = min(target, budget * 0.75)

    if target < 0:
        target = 0.0

    return max(0, min(budget, float(target)))
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

    alive_opps = []
    prev_bids = []
    max_prev_bid = 0.0
    pressure_bid = 0.0
    urgent_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            opp_urgent = 0
            if opp.get('hp', 0) <= 3:
                opp_urgent += 1
            if opp.get('no_water_days', 0) >= 1:
                opp_urgent += 1
            if opp_urgent >= 1:
                urgent_opp_count += 1

            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid > max_prev_bid:
                    max_prev_bid = bid
                weight = 1.0
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    weight = 1.1
                if bid * weight > pressure_bid:
                    pressure_bid = bid * weight

    if not alive_opps:
        return max(0.0, min(budget, 18.0))

    my_urgent = 0
    if hp <= 3:
        my_urgent += 2
    elif hp <= 5:
        my_urgent += 1
    if no_water_days >= 1:
        my_urgent += 2

    tight_supply = supply <= 17
    roomy_supply = supply >= 22

    if my_urgent >= 3:
        bid = max(0.95 * DAILY_SALARY, pressure_bid + 2.0)
    elif my_urgent >= 2:
        if tight_supply:
            bid = max(0.82 * DAILY_SALARY, pressure_bid + 1.5)
        else:
            bid = max(0.68 * DAILY_SALARY, pressure_bid * 0.72)
    else:
        if roomy_supply:
            bid = max(14.0, min(0.38 * DAILY_SALARY, pressure_bid * 0.45))
        elif tight_supply:
            if max_prev_bid >= 120:
                bid = 0.42 * DAILY_SALARY
            else:
                bid = max(0.52 * DAILY_SALARY, pressure_bid * 0.62)
        else:
            if urgent_opp_count >= 2:
                bid = max(0.58 * DAILY_SALARY, pressure_bid * 0.75)
            else:
                bid = max(0.46 * DAILY_SALARY, pressure_bid * 0.58)

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.9

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.92)

    bid = max(0.0, min(budget, bid))
    return bid
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

    alive = []
    prev_bids = []
    dangerous_prev = []
    low_prev = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 90:
                    dangerous_prev.append(float(bid))
                if bid <= 25:
                    low_prev.append(float(bid))

    alive_count = len(alive)
    if alive_count == 0:
        return max(0.0, min(float(budget), 18.0))

    total_players = alive_count + 1
    pressure = total_players * WATER_REQ - supply
    scarce = pressure > 0
    very_scarce = pressure >= WATER_REQ

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        bid = max(88.0, highest_prev + 3.0, avg_prev + 8.0)
    elif urgent:
        if scarce:
            bid = max(72.0, highest_prev + 2.0)
        else:
            bid = max(42.0, avg_prev * 0.75 + 4.0)
    else:
        if very_scarce:
            if dangerous_prev:
                bid = 16.0
            else:
                bid = max(38.0, highest_prev + 1.5)
        elif scarce:
            if highest_prev >= 120:
                bid = 20.0
            elif highest_prev >= 85:
                bid = 28.0
            else:
                bid = max(30.0, avg_prev + 2.0)
        else:
            if low_prev:
                bid = max(12.0, min(26.0, max(low_prev) + 2.0))
            else:
                bid = 18.0

    if day >= 8 and hp >= 6 and not urgent and highest_prev >= 100:
        bid = min(bid, 18.0)

    if budget < bid:
        bid = float(budget)

    if budget <= 20:
        bid = float(budget)
    elif budget <= 45:
        bid = min(bid, float(budget))

    if bid < 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
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
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    dangerous_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    danger_prev = max(dangerous_bids) if dangerous_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    base = 24.0 + 18.0 * scarcity

    if hp >= 7 and no_water_days == 0 and supply >= 21:
        bid = min(base, 28.0)
    elif hp >= 5 and no_water_days == 0:
        bid = base + 4.0
    elif hp <= 2 or no_water_days >= 2:
        bid = max(0.92 * highest_prev, 82.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(0.82 * danger_prev, 68.0)
    else:
        bid = base + 10.0

    if supply <= 17:
        bid = max(bid, 0.88 * highest_prev if highest_prev > 0 else 60.0)
    elif supply >= 23 and hp >= 6:
        bid = min(bid, 26.0)

    if day >= 8:
        if hp >= 5 and budget < 250:
            bid = min(bid, 36.0)
        elif hp <= 3:
            bid = max(bid, 0.9 * highest_prev if highest_prev > 0 else 75.0)

    if avg_prev > 105 and hp >= 6 and no_water_days == 0:
        bid = min(bid, 34.0)

    bid = max(0.0, min(float(budget), float(bid)))
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

    alive_opponents = []
    prev_bids = []
    urgent_opponents = 0
    rich_alive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY:
                rich_alive += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / WATER_REQ
    low_supply = units < 1.6
    high_supply = units >= 1.85

    if hp <= 2 or no_water >= 2:
        bid = max(62.0, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        if low_supply:
            bid = max(49.0, highest_prev + 1.5)
        else:
            bid = max(41.0, avg_prev + 1.0)
    else:
        if high_supply:
            bid = 19.0
        elif low_supply:
            bid = max(28.0, min(44.0, avg_prev + 0.5))
        else:
            bid = max(23.0, min(36.0, avg_prev))

    if highest_prev >= 85.0 and hp > 4 and no_water == 0:
        bid = min(bid, 24.0)

    if rich_alive >= 2 and low_supply and hp > 4 and no_water == 0:
        bid += 4.0

    if urgent_opponents >= 2 and hp > 4 and no_water == 0 and low_supply:
        bid = min(bid, 26.0)

    if day >= 8:
        bid += 4.0
    if day >= 9 and (hp <= 4 or no_water >= 1):
        bid += 8.0

    reserve_floor = 0.0
    if day < 9:
        reserve_floor = DAILY_SALARY * 0.35
    max_affordable = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water >= 1:
        max_affordable = budget

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
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    rich_pressure = 0
    desperate_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= 700:
                rich_pressure += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0.0)))
                except Exception:
                    pass

    if not alive_opps:
        return float(min(budget, 5.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 3
    elif supply <= 18:
        scarcity = 2
    elif supply <= 21:
        scarcity = 1

    danger = 0
    if hp <= 2:
        danger = 3
    elif hp <= 4 or no_water_days >= 1:
        danger = 2
    elif hp <= 6:
        danger = 1

    if danger >= 3:
        bid = max(0.95 * DAILY_SALARY, max_prev + 2.0)
    elif danger == 2:
        bid = max(0.78 * DAILY_SALARY, min(max_prev + 1.0, 0.92 * DAILY_SALARY))
    else:
        if scarcity >= 3:
            bid = max(0.72 * DAILY_SALARY, min(max_prev + 1.0, 0.9 * DAILY_SALARY))
        elif scarcity == 2:
            bid = max(0.52 * DAILY_SALARY, min(avg_prev * 0.7 + 4.0, 0.78 * DAILY_SALARY))
        elif scarcity == 1:
            bid = max(0.32 * DAILY_SALARY, min(avg_prev * 0.45 + 2.0, 0.58 * DAILY_SALARY))
        else:
            bid = 0.18 * DAILY_SALARY

    if rich_pressure >= 2 and danger == 0 and scarcity <= 1:
        bid *= 0.75

    if desperate_count >= 2 and (scarcity >= 2 or danger >= 1):
        bid += 6.0

    if day >= 8 and hp >= 5 and scarcity == 0:
        bid *= 0.8

    if budget < DAILY_SALARY:
        bid = min(bid, max(8.0, budget * 0.7))

    bid = max(0.0, min(float(budget), float(bid)))
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        base = DAILY_SALARY * 0.28
        if no_water >= 1 or hp <= 3:
            base = DAILY_SALARY * 0.6
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    opp_desperation = 0
    rich_count = 0
    for opp in alive_opps:
        if opp.get('budget', 0) >= 300:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            opp_desperation += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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
    if no_water >= 2:
        urgency += 0.6
    elif no_water >= 1:
        urgency += 0.3

    market_pressure = 0.0
    if highest_prev >= 130:
        market_pressure = 0.5
    elif highest_prev >= 100:
        market_pressure = 0.35
    elif highest_prev >= 70:
        market_pressure = 0.2
    elif highest_prev > 0:
        market_pressure = 0.1

    base = DAILY_SALARY * (0.22 + 0.22 * scarcity + urgency + market_pressure)

    if supply >= 22 and urgency < 0.5:
        base *= 0.72
    elif supply <= 17:
        base *= 1.18

    if opp_desperation >= 2:
        base *= 1.12
    if rich_count >= 2:
        base *= 1.08

    if highest_prev > 0:
        if urgency >= 0.5:
            target = max(base, highest_prev + 2.5)
        else:
            if highest_prev >= 120:
                target = min(base, DAILY_SALARY * 0.62)
            else:
                target = max(base, avg_prev * 0.82)
    else:
        target = base

    if day >= 8 and budget > DAILY_SALARY * 3:
        target *= 1.08

    reserve = 0.0
    if hp > 4 and no_water == 0:
        reserve = DAILY_SALARY * 0.35
    elif hp > 2:
        reserve = DAILY_SALARY * 0.15

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 0.8:
        max_affordable = budget

    bid = min(target, max_affordable)

    if urgency >= 0.8:
        bid = max(bid, DAILY_SALARY * 0.92)
    elif urgency >= 0.45:
        bid = max(bid, DAILY_SALARY * 0.68)

    bid = max(0.0, min(budget, bid))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    high_pressure_count = 0
    weak_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) <= DAILY_SALARY * 0.6 or opp.get('hp', 0) <= 2:
                weak_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 80:
                    high_pressure_count += 1

    if not alive_opponents:
        return min(budget, 18.0)

    slots = max(1, int(supply // WATER_REQ))
    alive_count = len(alive_opponents) + 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev = sorted_bids[int(1)]
    elif len(prev_bids) == 1:
        second_prev = prev_bids[int(0)]

    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2
    abundant = supply >= 24
    tight = supply <= 17

    base = 28.0

    if critical:
        base = 92.0
    elif urgent:
        base = 62.0
    elif abundant:
        base = 24.0
    elif tight:
        base = 38.0

    if slots >= 2:
        base -= 6.0
    else:
        base += 6.0

    if alive_count <= slots:
        base = min(base, 16.0)

    if high_pressure_count >= slots and not urgent:
        base = min(base, 22.0)

    if highest_prev >= 110:
        if critical:
            base = max(base, 96.0)
        elif urgent:
            base = max(base, 72.0)
        else:
            base = min(base, 20.0)
    elif highest_prev >= 80:
        if urgent:
            base = max(base, second_prev + 3.0, 60.0)
        else:
            base = min(base, 24.0)
    elif highest_prev > 0:
        if slots >= 2 or abundant:
            base = max(base, min(highest_prev + 2.0, 58.0))
        else:
            base = max(base, min(highest_prev + 4.0, 68.0))

    if weak_count >= 2 and not urgent:
        base -= 4.0

    if day >= 8 and budget > 0:
        base += 6.0

    spend_cap = budget
    if not urgent:
        spend_cap = min(spend_cap, DAILY_SALARY * 0.85)
    elif not critical:
        spend_cap = min(spend_cap, DAILY_SALARY * 1.15)

    bid = max(0.0, min(base, spend_cap))

    if budget < 25:
        bid = min(bid, budget)

    return float(max(0.0, bid))
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

    alive_opponents = []
    prev_bids = []
    extreme_count = 0
    urgent_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= 120:
                    extreme_count += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22
    critical_self = hp <= 2 or no_water_days >= 2
    pressured_self = hp <= 4 or no_water_days >= 1

    if critical_self:
        if extreme_count >= 2:
            bid = 118.0 if budget >= 118.0 else budget
        else:
            bid = max(78.0, min(110.0, max_prev + 3.0))
    elif pressured_self:
        if extreme_count >= 2:
            bid = 32.0 if supply_loose else 48.0
        else:
            base = max(42.0, avg_prev + 2.0)
            if supply_tight:
                base += 10.0
            bid = min(85.0, base)
    else:
        if extreme_count >= 2:
            bid = 12.0 if supply_loose else 22.0
        else:
            base = 24.0
            if max_prev > 0:
                base = max(24.0, min(60.0, avg_prev * 0.75 + 3.0))
            if supply_tight:
                base += 8.0
            elif supply_loose:
                base -= 6.0
            bid = base

    if urgent_opp_count >= 2 and not critical_self:
        bid *= 0.85

    if day >= 8:
        if pressured_self:
            bid += 8.0
        else:
            bid += 3.0

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    affordable = max(0.0, budget - reserve_floor)
    if critical_self:
        affordable = budget

    bid = min(budget, bid)
    if affordable > 0:
        bid = min(bid, affordable) if not critical_self else min(bid, budget)
    else:
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_pressure = 0
    weak_pressure = 0
    desperate_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    if bid >= 90:
                        strong_pressure += 1
                    elif bid <= 50:
                        weak_pressure += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 28.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Supply regime: with req 13, supply < 26 means usually only one player can be fully satisfied.
    high_supply = supply >= 23
    mid_supply = supply >= 19

    # Emergency survival mode
    if hp <= 2 or no_water >= 2:
        if high_supply:
            bid = 96.0 if highest_prev < 100 else highest_prev + 2.5
        else:
            bid = 108.0 if highest_prev < 110 else highest_prev + 2.0
        return float(min(budget, bid))

    # Late game: spend more if still healthy enough to capitalize
    if day >= 8:
        if high_supply and strong_pressure <= 1:
            bid = max(78.0, highest_prev + 1.5)
        else:
            bid = max(92.0, highest_prev + 1.0)
        return float(min(budget, bid))

    # Early/mid game conservation against chronic overbidders
    if strong_pressure >= 2 and not high_supply and hp >= 4:
        bid = 18.0
    elif high_supply:
        if weak_pressure >= 1 and avg_prev < 85:
            bid = max(72.0, highest_prev + 1.5)
        else:
            bid = 84.0 if hp >= 5 else 92.0
    elif mid_supply:
        if desperate_opp >= 2:
            bid = 32.0 if hp >= 5 else 88.0
        else:
            bid = 46.0 if hp >= 5 else 86.0
    else:
        bid = 24.0 if hp >= 5 else 82.0

    # Budget discipline
    if budget < 120:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, max(15.0, budget * 0.22) if hp >= 5 else budget)

    return float(max(0.0, min(budget, bid)))
"""
