# ============================================================
# Experiment: exp_095
# Agent: Alex
# Source: exp_095
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

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    players_alive = 1 + len(alive_opponents)

    visible_prev_bids = []
    desperate_opponents = 0
    rich_aggressive = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            visible_prev_bids.append(bid)
            if bid >= DAILY_SALARY * 0.8:
                rich_aggressive += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            desperate_opponents += 1

    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < players_alive

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.96
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.78
    else:
        if scarcity:
            base = DAILY_SALARY * 0.58
        else:
            base = DAILY_SALARY * 0.42

    if visible_prev_bids:
        max_prev = max(visible_prev_bids)
        if hp <= 4 or no_water_days >= 1:
            base = max(base, min(DAILY_SALARY * 0.97, max_prev + 2.0))
        else:
            if max_prev >= DAILY_SALARY * 0.9 and hp >= 6:
                base = min(base, DAILY_SALARY * 0.35)
            elif scarcity:
                base = max(base, min(DAILY_SALARY * 0.82, max_prev + 1.0))

    if desperate_opponents >= max(1, len(alive_opponents) // 2):
        base += 4.0
    if rich_aggressive >= 2 and hp >= 6 and no_water_days == 0:
        base -= 6.0

    if float(supply) >= 23.0 and hp >= 5 and no_water_days == 0:
        base -= 5.0
    elif float(supply) <= 16.0:
        base += 5.0

    base = max(0.0, min(float(budget), base))

    if budget < DAILY_SALARY * 0.35:
        if hp <= 3 or no_water_days >= 1:
            return float(budget)
        return max(0.0, float(budget) * 0.55)

    return float(base)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    yesterday_bids = []
    yesterday_high_need = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                yesterday_high_need.append(float(prev['bid']))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    pressure_bid = max(yesterday_high_need) if yesterday_high_need else highest_prev

    competitors_for_water = 1
    for opp in alive_opponents:
        if opp.get('budget', 0) > 0:
            competitors_for_water += 1

    expected_units = supply / float(WATER_REQ)
    scarcity = competitors_for_water - expected_units

    emergency = hp <= 2 or no_water_days >= 2
    urgent = hp <= 4 or no_water_days >= 1
    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if emergency:
        target = max(DAILY_SALARY * 1.25, pressure_bid + 2.0)
    elif urgent:
        if tight_supply or scarcity > 1.5:
            target = max(DAILY_SALARY * 0.95, pressure_bid + 1.5)
        else:
            target = max(DAILY_SALARY * 0.72, min(pressure_bid * 0.72, DAILY_SALARY * 0.95))
    else:
        if loose_supply and scarcity < 0.8:
            target = DAILY_SALARY * 0.28
        elif tight_supply or scarcity > 1.8:
            target = max(DAILY_SALARY * 0.55, min(pressure_bid * 0.62, DAILY_SALARY * 0.88))
        else:
            target = max(DAILY_SALARY * 0.4, min(pressure_bid * 0.5, DAILY_SALARY * 0.7))

    if day >= 8 and hp >= 6 and no_water_days == 0:
        target *= 0.9

    reserve_floor = 0.0
    if day < 9:
        reserve_floor = DAILY_SALARY * 0.25
    max_affordable = max(0.0, budget - reserve_floor)
    if emergency:
        max_affordable = budget

    bid = min(target, max_affordable)
    if bid < 0:
        bid = 0.0
    if urgent and bid < DAILY_SALARY * 0.35 and budget >= DAILY_SALARY * 0.35:
        bid = DAILY_SALARY * 0.35

    return float(min(budget, bid))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    david_like_bid = None
    rich_aggressive = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if oid == 'David':
                    david_like_bid = float(bid)
            if opp.get('budget', 0) > 150 and opp.get('water_requirement', WATER_REQ) <= supply:
                if bid is not None and float(bid) >= 100:
                    rich_aggressive += 1

    if not alive:
        return max(0.0, min(budget, 20.0))

    capacity = int(supply // WATER_REQ)
    if capacity < 0:
        capacity = 0

    scarcity = 0.0
    if supply <= 16:
        scarcity = 1.0
    elif supply <= 19:
        scarcity = 0.7
    elif supply <= 22:
        scarcity = 0.4
    else:
        scarcity = 0.15

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    elif hp <= 6:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days == 1:
        urgency += 0.35

    if day >= 8:
        urgency += 0.2

    target = 0.0

    if david_like_bid is None:
        if prev_bids:
            david_like_bid = min(prev_bids)
        else:
            david_like_bid = 55.0

    if capacity >= 2:
        target = 34.0 + 12.0 * urgency + 6.0 * scarcity
    else:
        target = david_like_bid + 3.5 + 10.0 * urgency + 8.0 * scarcity

    if rich_aggressive >= 2 and hp > 4 and no_water_days == 0 and capacity < 2:
        target -= 10.0

    if hp <= 2 or no_water_days >= 2:
        target = max(target, 88.0)
    elif hp <= 4 or no_water_days == 1:
        target = max(target, 64.0)

    if budget < 90:
        target = min(target, budget * 0.72)
    elif budget < 160:
        target = min(target, budget * 0.6)
    else:
        target = min(target, budget * 0.42)

    floor_bid = 12.0 if capacity >= 2 else 28.0
    bid = max(floor_bid, target)
    bid = min(budget, bid)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        if supply >= 22:
            return float(min(budget, DAILY_SALARY * 0.18))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if float(opp.get('budget', 0)) > budget:
            rich_opp += 1
        if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 10)) <= 3:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = 1.0 - ((supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY))
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    emergency = (hp <= 2) or (no_water_days >= 2)
    pressured = (hp <= 4) or (no_water_days >= 1)

    if emergency:
        base = max(DAILY_SALARY * 0.95, avg_prev + 8.0, highest_prev * 0.86)
        if supply <= 17:
            base = max(base, highest_prev + 2.0, 118.0)
        return float(max(0.0, min(budget, base)))

    if pressured:
        base = DAILY_SALARY * (0.72 + 0.28 * scarcity)
        if highest_prev > 0:
            base = max(base, avg_prev * 0.9, highest_prev * 0.78)
        if urgent_opp >= 2:
            base += 8.0
        if supply <= 17:
            base += 10.0
        return float(max(0.0, min(budget, base)))

    if supply >= 23:
        base = DAILY_SALARY * 0.22
    elif supply >= 20:
        base = DAILY_SALARY * 0.34
    elif supply >= 18:
        base = DAILY_SALARY * 0.48
    else:
        base = DAILY_SALARY * 0.62

    if highest_prev >= 150:
        if supply >= 20 and hp >= 6:
            base = min(base, DAILY_SALARY * 0.28)
        else:
            base = max(base, DAILY_SALARY * 0.7)
    elif highest_prev >= 105:
        if supply >= 21 and hp >= 7:
            base = min(base, DAILY_SALARY * 0.3)
        else:
            base = max(base, avg_prev * 0.72)
    elif highest_prev > 0:
        base = max(base, avg_prev * 0.82)

    if urgent_opp >= 2 and supply <= 18:
        base += 7.0
    if rich_opp >= 2 and supply >= 21 and hp >= 7:
        base -= 4.0
    if day >= 8 and hp >= 7 and no_water_days == 0 and supply >= 20:
        base -= 5.0

    if base < 0:
        base = 0.0
    return float(min(budget, base))
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

    alive_opponents = []
    threatening_bids = []
    rich_alive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > 0:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None and opp.get('budget', 0) > 0:
                threatening_bids.append(prev.get('bid', 0))

    if not alive_opponents or rich_alive == 0:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 35.0))
        return float(min(budget, 5.0))

    highest_prev = max(threatening_bids) if threatening_bids else 0.0
    avg_prev = sum(threatening_bids) / float(len(threatening_bids)) if threatening_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if urgent:
        base = max(62.0, highest_prev + 2.0)
    elif pressured:
        if highest_prev >= 120:
            base = 58.0
        else:
            base = max(42.0, avg_prev + 3.0)
    else:
        if supply >= 22:
            base = 12.0
        elif supply >= 19:
            base = 22.0
        else:
            if highest_prev >= 120:
                base = 28.0
            elif highest_prev >= 70:
                base = highest_prev + 1.5
            else:
                base = 34.0

    if day >= 8:
        base += 8.0
    elif day >= 6:
        base += 4.0

    if scarcity < 0.3:
        base += 10.0
    elif scarcity > 0.7:
        base -= 6.0

    if budget < 40:
        base = min(base, budget)
    elif budget < 80 and not urgent:
        base = min(base, 45.0)

    if highest_prev >= 140 and not urgent and hp >= 5:
        base = min(base, 25.0)

    bid = max(0.0, min(float(budget), float(base)))
    return float(bid)
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0
    urgent_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= budget:
                rich_pressure += 1
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return float(min(budget, 55.0))
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    critical = hp <= 2 or no_water >= 2
    fragile = hp <= 4 or no_water >= 1

    if critical:
        bid = max(62.0, highest_prev + 2.5, DAILY_SALARY * (0.82 + 0.12 * scarcity))
    elif fragile:
        bid = max(42.0, avg_prev * 0.72, 36.0 + 18.0 * scarcity)
    else:
        bid = max(16.0, 14.0 + 16.0 * scarcity)
        if highest_prev > 85:
            bid = min(bid, 24.0)
        elif highest_prev > 60:
            bid = max(bid, 26.0)

    if supply >= 22:
        bid *= 0.78
    elif supply <= 17:
        bid *= 1.18

    if rich_pressure >= 2 and not critical:
        bid *= 0.9
    if urgent_opponents >= 2 and fragile:
        bid *= 1.08

    if day >= 8:
        if critical:
            bid *= 1.12
        elif hp >= 5 and no_water == 0:
            bid *= 0.92

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve_floor = DAILY_SALARY * 0.5

    max_spend = budget - reserve_floor
    if critical:
        max_spend = budget
    elif max_spend < 0:
        max_spend = budget * 0.45

    if fragile and max_spend < 28.0:
        max_spend = min(budget, 28.0)

    bid = min(bid, max_spend, budget)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0.0
    urgent_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('budget', 0) > budget:
                rich_pressure += 1.0
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    base = 16.0 + 18.0 * scarcity
    if supply <= 17:
        base += 10.0
    elif supply >= 22:
        base -= 5.0

    if hp <= 2:
        base += 32.0
    elif hp <= 4:
        base += 18.0

    if no_water_days >= 2:
        base += 28.0
    elif no_water_days >= 1:
        base += 12.0

    base += min(10.0, rich_pressure * 3.0)
    base += min(8.0, urgent_opp * 2.0)

    if max_prev >= 140.0:
        if hp > 4 and no_water_days == 0 and supply >= 20:
            base = min(base, 24.0)
        else:
            base = max(base, 58.0)
    elif max_prev >= 90.0:
        base = max(base, min(max_prev * 0.72, 74.0))
    elif max_prev > 0.0:
        base = max(base, min(max_prev + 2.0, 62.0))
    else:
        base = max(base, 26.0)

    if day >= 8:
        base += 8.0
    if day >= 9 and hp <= 4:
        base += 10.0

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = 35.0
    elif hp > 2:
        reserve = 20.0

    affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        affordable = budget

    bid = min(base, affordable if affordable > 0 else budget)

    if bid < 0:
        bid = 0.0
    if hp <= 2 and bid < 45.0:
        bid = min(budget, 45.0)

    return float(min(budget, max(0.0, bid)))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_opp_bids.append(bid)

    if not alive_opponents:
        return max(0.0, min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 120.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 120.0
    max_urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else max_prev

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0.0:
        tightness = 0.0
    if tightness > 1.0:
        tightness = 1.0

    survival_mode = hp <= 3 or no_water_days >= 1
    danger_mode = hp <= 2 or no_water_days >= 2

    if supply >= 23:
        base = 38.0
    elif supply >= 20:
        base = 62.0
    elif supply >= 18:
        base = 92.0
    else:
        base = 122.0

    target = base

    if supply <= 18:
        target = max(target, max_prev + 2.5)
    elif supply <= 20:
        target = max(target, avg_prev + 1.5)
    else:
        target = max(target, avg_prev * 0.72)

    if survival_mode:
        target = max(target, max_urgent_prev + 3.0, 118.0)
    if danger_mode:
        target = max(target, max_prev + 6.0, 145.0)

    if hp >= 7 and no_water_days == 0 and supply >= 21:
        target *= 0.82

    if day >= 8 and budget > DAILY_SALARY * 3:
        target *= 1.06

    reserve_floor = DAILY_SALARY * max(1, 10 - int(day)) * 0.18
    max_affordable = max(0.0, budget - reserve_floor)
    if danger_mode:
        max_affordable = budget
    elif survival_mode:
        max_affordable = max(max_affordable, budget * 0.72)

    bid = min(target, max_affordable)
    bid = min(bid, budget)
    if bid < 0.0:
        bid = 0.0

    if budget < 45.0 and not survival_mode:
        bid = min(bid, max(12.0, budget * 0.55))

    return float(round(bid, 2))
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
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    pressure_bids = []
    cindy_bid = None
    eric_bid = None
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid')
            prev_bids.append(bid)
            pressure_bids.append(bid)
            if oid == 'Cindy':
                cindy_bid = bid
            if oid == 'Eric':
                eric_bid = bid

    highest_prev = max(prev_bids) if prev_bids else 0.0
    realistic_prev = 0.0
    if pressure_bids:
        filtered = [b for b in pressure_bids if b <= DAILY_SALARY * 2.2]
        realistic_prev = max(filtered) if filtered else min(highest_prev, DAILY_SALARY * 1.6)

    scarcity = supply <= 17
    abundant = supply >= 22
    critical = hp <= 3 or no_water_days >= 2
    fragile = hp <= 5 or no_water_days >= 1

    base = DAILY_SALARY * 0.42
    if abundant:
        base = DAILY_SALARY * 0.28
    elif scarcity:
        base = DAILY_SALARY * 0.72

    if realistic_prev > 0:
        if critical:
            target = max(base, realistic_prev + 3.0)
        elif fragile:
            target = max(base, realistic_prev + 1.5)
        else:
            if realistic_prev >= DAILY_SALARY * 1.4:
                target = DAILY_SALARY * 0.38 if abundant else DAILY_SALARY * 0.52
            else:
                target = max(base, realistic_prev + 1.0)
    else:
        target = base

    if cindy_bid is not None and cindy_bid >= 180 and not critical:
        target = min(target, DAILY_SALARY * 0.6 if not scarcity else DAILY_SALARY * 0.82)

    if eric_bid is not None and scarcity:
        target = max(target, min(eric_bid + 2.0, DAILY_SALARY * 1.35))

    if day >= 8:
        if hp >= 7 and no_water_days == 0 and not scarcity:
            target *= 0.9
        elif fragile:
            target *= 1.08

    if critical:
        target = max(target, DAILY_SALARY * 0.88)

    target = max(0.0, min(target, budget))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return min(budget, 1.0)

    prev_bids = []
    opp_pressures = []
    desperate_count = 0
    rich_count = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        opp_hp = opp.get('hp', 10)
        opp_nw = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0)
        opp_salary = opp.get('daily_salary', DAILY_SALARY)
        opp_req = opp.get('water_requirement', WATER_REQ)

        pressure = 0.0
        if opp_hp <= 3:
            pressure += 2.0
        elif opp_hp <= 5:
            pressure += 1.0
        if opp_nw >= 1:
            pressure += 1.5
        if opp_budget >= opp_salary * 4:
            pressure += 0.8
        if opp_req > WATER_REQ:
            pressure += 0.3
        opp_pressures.append(pressure)

        if opp_hp <= 4 or opp_nw >= 1:
            desperate_count += 1
        if opp_budget >= 280:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    pressure_max = max(opp_pressures) if opp_pressures else 0.0

    winners_est = max(1, min(2, int(supply // WATER_REQ)))
    scarcity = 2 - winners_est

    urgency = 0.0
    if hp <= 2:
        urgency += 3.0
    elif hp <= 4:
        urgency += 2.0
    elif hp <= 6:
        urgency += 1.0
    if no_water >= 2:
        urgency += 3.0
    elif no_water >= 1:
        urgency += 1.5
    urgency += scarcity * 0.8

    if budget <= DAILY_SALARY:
        urgency += 0.8
    elif budget >= DAILY_SALARY * 5:
        urgency -= 0.3

    if day >= 8:
        urgency += 0.7

    if urgency >= 5.0:
        target = max(highest_prev + 3.0, avg_prev + 8.0, DAILY_SALARY * 1.45)
    elif urgency >= 3.5:
        target = max(highest_prev + 1.5, avg_prev + 3.0, DAILY_SALARY * 1.12)
    elif urgency >= 2.0:
        target = max(avg_prev * 0.96, DAILY_SALARY * 0.92)
    else:
        target = DAILY_SALARY * 0.28

    if pressure_max >= 2.5 and urgency < 3.5:
        target *= 0.82
    if desperate_count >= 2 and urgency < 5.0:
        target *= 0.88
    if rich_count == 0 and urgency >= 2.0:
        target *= 0.96

    if winners_est >= 2 and urgency < 3.5:
        target *= 0.9
    elif winners_est == 1 and urgency >= 2.0:
        target *= 1.08

    min_keep = 0.0
    if day <= 7:
        min_keep = DAILY_SALARY * 1.2
    elif day <= 9:
        min_keep = DAILY_SALARY * 0.6

    spend_cap = budget
    if urgency < 5.0:
        spend_cap = max(0.0, budget - min_keep)
        if spend_cap <= 0:
            spend_cap = min(budget, DAILY_SALARY * 0.35)

    bid = min(target, spend_cap if spend_cap > 0 else budget)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, highest_prev + 4.0, DAILY_SALARY * 1.3))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
"""
