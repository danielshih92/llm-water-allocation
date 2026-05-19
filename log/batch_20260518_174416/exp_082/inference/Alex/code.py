# ============================================================
# Experiment: exp_082
# Agent: Alex
# Source: exp_082
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return max(0, min(budget, base))

    players = 1 + len(alive)
    units = supply / float(WATER_REQ)
    scarcity = players - units

    prev_bids = []
    distressed = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            distressed += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)

    if hp <= 1:
        target = DAILY_SALARY * 0.98
    elif hp <= 2 or no_water >= 2:
        target = DAILY_SALARY * 0.9
    elif no_water >= 1:
        target = DAILY_SALARY * 0.78
    else:
        if scarcity <= 0:
            target = DAILY_SALARY * 0.38
        elif scarcity < 1:
            target = DAILY_SALARY * 0.5
        elif scarcity < 2:
            target = DAILY_SALARY * 0.62
        else:
            target = DAILY_SALARY * 0.78

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if hp >= 4 and no_water == 0 and highest_prev >= DAILY_SALARY * 0.9:
            target = min(target, DAILY_SALARY * 0.32)
        else:
            pressure_bid = max(avg_prev + 1.0, highest_prev + 0.5)
            if scarcity > 0 or hp <= 2 or no_water >= 1:
                target = max(target, pressure_bid)
            else:
                target = max(target, min(pressure_bid, DAILY_SALARY * 0.62))

    target += distressed * 1.5
    target += rich_opp * 0.5

    if budget < DAILY_SALARY:
        if hp >= 4 and no_water == 0:
            target = min(target, budget * 0.45)
        else:
            target = min(target, max(budget * 0.75, target))

    if hp >= 5 and no_water == 0 and scarcity <= 0:
        target = min(target, DAILY_SALARY * 0.42)

    return max(0, min(budget, target))
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
    yesterday_bids = []
    rich_threat = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 3:
                rich_threat += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, min(budget, DAILY_SALARY * 0.65))
        return max(0.0, min(budget, DAILY_SALARY * 0.18))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    scarcity = 0.0
    if supply <= 16:
        scarcity = 1.0
    elif supply <= 18:
        scarcity = 0.7
    elif supply <= 21:
        scarcity = 0.4
    else:
        scarcity = 0.15

    emergency = False
    if hp <= 2 or no_water_days >= 2:
        emergency = True
    elif hp <= 4 and no_water_days >= 1:
        emergency = True

    if emergency:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 1.25)
        if budget < bid:
            bid = budget
        return max(0.0, min(budget, bid))

    if scarcity >= 0.7:
        if highest_prev >= DAILY_SALARY * 0.8:
            bid = highest_prev + 1.1
        else:
            bid = max(DAILY_SALARY * 0.72, avg_prev + 4.0)
        if hp >= 7 and no_water_days == 0 and rich_threat >= 1:
            bid *= 0.96
        return max(0.0, min(budget, bid))

    if scarcity >= 0.4:
        if hp >= 7 and no_water_days == 0 and highest_prev >= DAILY_SALARY * 0.85:
            bid = DAILY_SALARY * 0.34
        else:
            bid = max(DAILY_SALARY * 0.48, min(highest_prev + 0.8, DAILY_SALARY * 0.78))
        return max(0.0, min(budget, bid))

    if hp <= 4 or no_water_days >= 1:
        bid = max(DAILY_SALARY * 0.52, avg_prev + 1.5)
    else:
        if highest_prev >= DAILY_SALARY * 0.8:
            bid = DAILY_SALARY * 0.22
        else:
            bid = DAILY_SALARY * 0.28

    if day >= 8 and hp <= 5:
        bid = max(bid, DAILY_SALARY * 0.6)

    return max(0.0, min(budget, bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp_bid = 0.0
    rich_pressure = 0.0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = None
            if prev:
                bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                    if float(bid) > urgent_opp_bid:
                        urgent_opp_bid = float(bid)
                pressure_score = float(bid)
                if opp.get('budget', 0) > 300:
                    pressure_score += 5.0
                if pressure_score > rich_pressure:
                    rich_pressure = pressure_score

    if not alive:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    critical_me = (hp <= 3) or (no_water >= 1)
    very_critical = (hp <= 2) or (no_water >= 2)

    if very_critical:
        target = max(highest_prev + 2.0, rich_pressure + 1.0, DAILY_SALARY * 0.92)
    elif critical_me:
        if tight_supply:
            target = max(highest_prev + 1.5, rich_pressure, DAILY_SALARY * 0.82)
        else:
            target = max(avg_prev + 2.0, urgent_opp_bid + 1.0, DAILY_SALARY * 0.72)
    else:
        if tight_supply:
            if highest_prev > 120:
                target = DAILY_SALARY * 0.58
            else:
                target = max(DAILY_SALARY * 0.52, avg_prev + 1.0)
        elif medium_supply:
            if highest_prev > 150:
                target = DAILY_SALARY * 0.42
            else:
                target = max(DAILY_SALARY * 0.38, min(highest_prev + 1.0, DAILY_SALARY * 0.68))
        else:
            if day >= 8 and hp >= 6:
                target = DAILY_SALARY * 0.22
            else:
                target = DAILY_SALARY * 0.30

    if budget < target:
        if critical_me:
            target = budget
        else:
            target = min(budget, max(0.0, DAILY_SALARY * 0.2))

    if hp >= 8 and no_water == 0 and highest_prev > 170 and supply >= 20:
        target = min(target, DAILY_SALARY * 0.26)

    if day >= 9 and hp <= 4:
        target = max(target, DAILY_SALARY * 0.88)

    return max(0.0, min(budget, float(target)))
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = min(budget, 8.0)
        return float(max(0.0, safe_bid))

    prev_bids = []
    dangerous_prev = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) <= 120.0:
                    dangerous_prev.append(float(bid))

    slots = int(supply // WATER_REQ)
    alive_count = len(alive) + 1

    base = 6.0
    if slots >= alive_count:
        base = 3.0
    elif slots >= max(1, alive_count - 1):
        base = 8.0
    else:
        base = 12.0

    if dangerous_prev:
        top_danger = max(dangerous_prev)
        if top_danger < 15.0:
            base = max(base, top_danger + 1.1)
        elif top_danger < 35.0:
            base = max(base, top_danger + 0.8)
        else:
            base = max(base, 10.0)

    if no_water_days >= 2 or hp <= 3:
        emergency = 42.0
        if dangerous_prev:
            emergency = max(emergency, min(65.0, max(dangerous_prev) + 2.0))
        return float(max(0.0, min(budget, emergency)))

    if hp <= 5 or no_water_days == 1:
        urgent = max(base, 18.0)
        if dangerous_prev:
            urgent = max(urgent, min(45.0, max(dangerous_prev) + 1.5))
        return float(max(0.0, min(budget, urgent)))

    if day >= 8 and hp >= 7:
        base = min(base, 7.0)

    if budget < 25.0:
        base = min(base, max(4.0, budget * 0.5))

    return float(max(0.0, min(budget, base)))
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0
    zeroish_count = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) <= 1.0:
                zeroish_count += 1
            if float(bid) >= 85.0 and opp.get('budget', 0) >= 80:
                rich_aggressive += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    abundant_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        base = 66.0 if not tight_supply else 69.0
    elif hp <= 4 or no_water >= 1:
        base = 52.0 if abundant_supply else 58.0
    else:
        if abundant_supply:
            base = 18.0
        elif tight_supply:
            base = 34.0
        else:
            base = 26.0

    if highest_prev >= 95.0:
        if hp >= 5 and no_water == 0:
            base = min(base, 22.0 if abundant_supply else 28.0)
        else:
            base = max(base, 60.0)
    elif highest_prev >= 70.0:
        if hp >= 5 and no_water == 0:
            base = max(base, min(45.0, highest_prev * 0.55))
        else:
            base = max(base, min(64.0, highest_prev * 0.78))
    elif highest_prev > 0.0:
        target = highest_prev + 2.0
        if abundant_supply:
            target -= 3.0
        base = max(base, target)

    if rich_aggressive >= 2 and hp >= 5 and no_water == 0:
        base = min(base, 24.0 if abundant_supply else 30.0)

    if desperate_count >= 2 and (hp <= 4 or no_water >= 1):
        base = max(base, 61.0)

    if zeroish_count >= len(alive_opponents) - 1 and len(alive_opponents) > 0:
        base = min(base, 8.0 if hp >= 5 and no_water == 0 else 20.0)

    if day >= 8:
        if hp <= 4 or no_water >= 1:
            base = max(base, 60.0)
        else:
            base = max(base, 32.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 25.0
    affordable = max(0.0, budget - reserve_floor)
    if hp <= 2 or no_water >= 2:
        affordable = budget

    bid = min(base, affordable if affordable > 0 else budget)

    if hp >= 6 and no_water == 0 and avg_prev >= 90.0 and abundant_supply:
        bid = min(bid, 16.0)

    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_budgets = []
    urgent_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 18)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0
    richest_opp = max(opp_budgets) if opp_budgets else 0

    units = supply / WATER_REQ
    tight = units < (len(alive) + 1)
    very_tight = units < len(alive)
    roomy = units >= (len(alive) + 1.5)

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1

    if danger >= 3:
        bid = max(92, highest_prev + 3)
    elif very_tight:
        bid = max(78, avg_prev + 2)
        if highest_prev > 0:
            bid = max(bid, highest_prev + 1.25)
    elif tight:
        bid = max(58, avg_prev * 0.78)
        if highest_prev >= 120:
            bid = max(52, highest_prev * 0.72)
    elif roomy:
        bid = 26 if hp > 5 else 40
    else:
        bid = 44

    if urgent_opp >= 2 and tight:
        bid += 8

    if richest_opp > budget * 2 and tight:
        bid += 6

    if day >= 8:
        if hp >= 6 and no_water_days == 0:
            bid *= 0.9
        else:
            bid *= 1.1

    if budget < 120:
        bid = min(bid, budget * 0.72)
    elif budget < 200:
        bid = min(bid, budget * 0.82)

    floor_bid = 12
    if danger >= 2:
        floor_bid = 45
    elif tight:
        floor_bid = 32

    bid = max(floor_bid, bid)
    bid = min(bid, budget)

    if bid < 0:
        bid = 0
    return float(bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    serious_bids = []
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                if bid >= 40:
                    serious_bids.append(bid)

    if not alive:
        return float(min(budget, 8.0))

    high_prev = max(serious_bids) if serious_bids else 0.0
    low_prev = min(serious_bids) if serious_bids else 0.0

    units = supply / WATER_REQ
    very_tight = units < 1.4
    tight = units < 1.8

    if hp <= 2 or no_water >= 2:
        target = max(95.0, high_prev + 3.0)
    elif hp <= 4 or no_water >= 1:
        if high_prev > 0:
            target = high_prev + 2.0
        else:
            target = 72.0
    else:
        if very_tight:
            if high_prev >= 150:
                target = 108.0
            elif high_prev >= 110:
                target = high_prev + 1.5
            elif high_prev > 0:
                target = max(82.0, high_prev + 2.0)
            else:
                target = 78.0
        elif tight:
            if high_prev >= 140:
                target = 92.0
            elif high_prev > 0:
                target = max(68.0, low_prev + 2.0)
            else:
                target = 60.0
        else:
            if desperate_count >= 2:
                target = 66.0
            elif high_prev > 0:
                target = max(52.0, low_prev + 1.0)
            else:
                target = 45.0

    if budget < DAILY_SALARY * 1.2:
        target = min(target, budget * 0.72)
    elif budget < DAILY_SALARY * 2.0 and hp > 4 and no_water == 0:
        target = min(target, DAILY_SALARY * 0.95)

    if hp >= 7 and no_water == 0 and high_prev >= 170 and very_tight:
        target = min(target, 88.0)

    bid = max(0.0, min(float(budget), float(target)))
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(min(budget, base))

    highest_prev = 0.0
    eric_prev = None
    rich_alive = 0
    urgent_opp_count = 0

    for opp in alive_opps:
        if opp.get('budget', 0) > DAILY_SALARY:
            rich_alive += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None and bid > highest_prev:
            highest_prev = bid
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if bid is not None and bid > 0:
                eric_prev = bid

    pressure = highest_prev
    if eric_prev is not None:
        pressure = max(pressure, eric_prev)

    ample_supply = supply >= 24
    tight_supply = supply <= 18

    desperation = 0
    if hp <= 2:
        desperation += 2
    elif hp <= 4:
        desperation += 1
    if no_water_days >= 2:
        desperation += 2
    elif no_water_days >= 1:
        desperation += 1

    if desperation >= 3:
        bid = max(DAILY_SALARY * 0.95, pressure + 3.0)
    elif desperation == 2:
        bid = max(DAILY_SALARY * 0.8, pressure * 0.72 + 2.0)
    else:
        if ample_supply:
            bid = DAILY_SALARY * 0.28
        elif tight_supply:
            bid = max(DAILY_SALARY * 0.48, pressure * 0.55)
        else:
            bid = max(DAILY_SALARY * 0.38, pressure * 0.42)

    if rich_alive <= 1 and pressure >= 100:
        if desperation <= 1:
            bid = min(bid, DAILY_SALARY * 0.34)
        else:
            bid = max(bid, DAILY_SALARY * 0.78)

    if urgent_opp_count >= 2 and desperation == 0:
        bid = min(bid, DAILY_SALARY * 0.3)

    days_left = 11 - day
    reserve_target = max(0.0, days_left * DAILY_SALARY * 0.32)
    affordable = max(0.0, budget - reserve_target)

    if desperation >= 2:
        affordable = budget
    elif affordable < DAILY_SALARY * 0.2:
        affordable = min(budget, DAILY_SALARY * 0.25)

    final_bid = min(budget, affordable, bid)

    if desperation >= 2:
        final_bid = min(budget, max(final_bid, min(budget, DAILY_SALARY * 0.72)))

    if final_bid < 0:
        final_bid = 0.0

    return float(final_bid)
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append((oid, opp))

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, min(budget, 35.0))
        return max(0.0, min(budget, 12.0))

    highest_prev = 0.0
    cindy_prev = None
    pressure_count = 0
    for oid, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            if bid > highest_prev:
                highest_prev = bid
            if bid >= 70.0:
                pressure_count += 1
        if oid == 'Cindy' and bid is not None:
            cindy_prev = bid

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tight_supply = supply <= 17.0
    loose_supply = supply >= 22.0

    urgent = hp <= 2 or no_water_days >= 1
    semi_urgent = hp <= 4

    if cindy_prev is None:
        cindy_prev = 84.9

    target = 0.0

    if urgent:
        if tight_supply:
            target = max(88.0, cindy_prev + 1.0)
        else:
            target = max(80.0, cindy_prev - 2.0)
    elif semi_urgent:
        if tight_supply:
            target = max(82.0, cindy_prev - 1.0)
        elif loose_supply:
            target = 42.0
        else:
            target = 58.0
    else:
        if tight_supply:
            target = 76.0 if pressure_count == 0 else max(79.0, highest_prev - 3.0)
        elif loose_supply:
            target = 16.0
        else:
            target = 28.0 if pressure_count == 0 else 34.0

    if day >= 8:
        target += 6.0
    if hp >= 8 and not urgent and not tight_supply:
        target -= 4.0

    reserve_floor = 0.0
    if day < 9:
        reserve_floor = DAILY_SALARY * (10 - day) * 0.18
    spend_cap = max(0.0, budget - reserve_floor)
    if urgent:
        spend_cap = budget

    bid = min(target, spend_cap)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    urgent_opp = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    total_players = 1 + len(alive_opponents)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < total_players
    very_tight = expected_units < max(1.6, total_players - 1)

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 4.0)
    elif no_water_days >= 1 or hp <= 4:
        bid = max(DAILY_SALARY * 0.82, highest_prev + 2.0)
    else:
        if very_tight:
            bid = max(DAILY_SALARY * 0.78, highest_prev + 1.5)
        elif scarcity:
            bid = max(DAILY_SALARY * 0.62, avg_prev + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.38, avg_prev * 0.72)

    if urgent_opp >= 2 and scarcity:
        bid += 4.0
    elif urgent_opp == 0 and not scarcity:
        bid -= 4.0

    if day >= 8 and hp >= 7 and no_water_days == 0 and not very_tight:
        bid -= 3.0

    reserve = 0.0
    if day <= 3:
        reserve = DAILY_SALARY * 1.2
    elif day <= 7:
        reserve = DAILY_SALARY * 0.7
    else:
        reserve = DAILY_SALARY * 0.25

    max_affordable = budget - reserve
    if hp <= 3 or no_water_days >= 1:
        max_affordable = budget
    if max_affordable < 0:
        max_affordable = budget * 0.5

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)

    return float(round(bid, 2))
"""
