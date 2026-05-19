# ============================================================
# Experiment: exp_041
# Agent: Alex
# Source: exp_041
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

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        if hp <= 2 or no_water >= 1:
            return max(0, min(budget, 56.0))
        return max(0, min(budget, 24.0))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        err = prev.get('error')
        status = prev.get('status')
        if err is None and bid is not None:
            prev_bids.append(float(bid))
        elif status == 'error':
            prev_bids.append(0.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = 1.0 - ((float(supply) - 15.0) / 10.0)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    critical = hp <= 2 or no_water >= 1
    fragile = hp <= 4

    if critical:
        target = max(58.0, highest_prev + 3.0, 42.0 + 18.0 * scarcity)
    elif fragile:
        target = max(44.0, highest_prev + 2.0, 30.0 + 16.0 * scarcity)
    else:
        target = max(20.0, avg_prev + 1.5, 18.0 + 14.0 * scarcity)

    if urgent_opp >= 2:
        target -= 4.0
    elif urgent_opp == 1:
        target -= 2.0

    if rich_opp >= 2:
        target += 4.0
    elif rich_opp == 1:
        target += 2.0

    if supply >= 23:
        target -= 6.0
    elif supply <= 17:
        target += 5.0

    max_safe = budget
    if not critical:
        reserve = DAILY_SALARY * 1.2
        max_safe = max(0.0, budget - reserve)
        if max_safe < 12.0:
            max_safe = min(budget, 12.0)

    bid = min(target, max_safe, budget)
    if bid < 0.0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if len(alive) == 0:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    panic_bids = 0
    weak_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            weak_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0)
            prev_bids.append(bid)
            if bid >= 90:
                panic_bids += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (25.0 - supply) / 10.0
    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water >= 2:
        urgency += 1.0
    elif no_water == 1:
        urgency += 0.45

    endgame = day >= 8

    if urgency >= 1.5:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif urgency >= 1.0:
        bid = max(DAILY_SALARY * 0.78, avg_prev + 2.0, highest_prev * 0.72)
    else:
        if panic_bids >= 2 and hp >= 5 and no_water == 0:
            bid = DAILY_SALARY * (0.22 + 0.10 * scarcity)
        elif highest_prev >= 120:
            bid = DAILY_SALARY * (0.28 + 0.10 * scarcity)
        elif highest_prev >= 80:
            bid = min(highest_prev + 1.5, DAILY_SALARY * (0.72 + 0.10 * scarcity))
        elif highest_prev > 0:
            bid = max(DAILY_SALARY * (0.48 + 0.10 * scarcity), highest_prev + 1.5)
        else:
            bid = DAILY_SALARY * (0.50 + 0.12 * scarcity)

    if weak_opp >= 2 and urgency < 1.0 and hp >= 6:
        bid *= 0.88
    if rich_opp >= 2 and urgency > 0:
        bid *= 1.08
    if endgame and hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.9)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = max(0.0, (7 - day) * 8.0)
    max_affordable = max(0.0, budget - reserve_floor)
    if urgency >= 1.0:
        max_affordable = budget

    bid = min(bid, max_affordable)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.2)
        return float(max(0.0, safe_bid))

    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) > 300:
            if bid is not None and float(bid) >= 75:
                rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # In this scenario supply 15-25 means only one agent can be fully satisfied each day.
    # Use yesterday pressure and our urgency to choose whether to contest.
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

    if day >= 8:
        urgency += 1

    pressure = 0
    if highest_prev >= 110:
        pressure += 3
    elif highest_prev >= 85:
        pressure += 2
    elif highest_prev >= 60:
        pressure += 1

    pressure += min(2, desperate_count)
    pressure += min(1, rich_aggressive)

    # Budget-aware ceilings
    if budget < 40:
        return float(max(0.0, budget))

    # Emergency survival: secure water now.
    if urgency >= 5:
        bid = max(92.0, highest_prev + 4.0)
        bid = min(budget, bid)
        return float(max(0.0, bid))

    # High pressure but not desperate: avoid waste unless moderately urgent.
    if pressure >= 4 and urgency <= 1:
        bid = min(budget, 18.0)
        return float(max(0.0, bid))

    if pressure >= 4:
        bid = max(88.0, highest_prev + 2.5)
        bid = min(budget, bid)
        return float(max(0.0, bid))

    # Moderate pressure: selective contesting.
    if pressure >= 2:
        if urgency >= 3:
            bid = max(72.0, avg_prev + 3.0)
        elif urgency >= 2:
            bid = max(58.0, avg_prev * 0.9)
        else:
            bid = 28.0
        bid = min(budget, bid)
        return float(max(0.0, bid))

    # Low pressure: conserve against Bob/Cindy overbidding tendencies.
    if urgency >= 3:
        bid = 61.0
    elif urgency >= 2:
        bid = 42.0
    else:
        bid = 16.0 + (day % 3)

    # Slight upward adjustment if multiple opponents look weak and may suddenly contest.
    if desperate_count >= 2 and urgency >= 2:
        bid += 6.0

    bid = min(budget, bid)
    return float(max(0.0, bid))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            if opp.get('budget', 0) >= 700:
                prev = opp.get('previous_trace', {})
                if prev and prev.get('bid') is not None and prev.get('bid') >= 70:
                    rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.45

    if urgency >= 1.5:
        bid = max(78.0, highest_prev + 2.0)
    elif urgency >= 0.8:
        bid = max(52.0 + 18.0 * scarcity, min(highest_prev + 1.5, 88.0))
    else:
        if supply >= 22:
            bid = 18.0
        elif supply >= 19:
            bid = 24.0 + 8.0 * scarcity
        else:
            bid = 36.0 + 14.0 * scarcity

        if highest_prev >= 95.0:
            bid = min(bid, 34.0 + 6.0 * scarcity)
        elif highest_prev >= 70.0:
            bid = max(bid, min(highest_prev * 0.72, 58.0))
        elif highest_prev > 0:
            bid = max(bid, min(highest_prev + 1.0, 54.0))

    if rich_aggressive >= 2 and urgency < 1.5:
        bid *= 0.9
    if desperate_count >= 2:
        bid += 6.0

    safe_cap = budget
    if hp > 4 and no_water_days == 0:
        safe_cap = min(safe_cap, DAILY_SALARY * 0.85)
    else:
        safe_cap = min(safe_cap, DAILY_SALARY * 1.6)

    if budget < 120:
        bid = min(bid, max(18.0, budget * 0.55))
    elif budget < 250 and urgency < 1.5:
        bid = min(bid, budget * 0.45)

    bid = min(bid, safe_cap)
    if urgency >= 1.5:
        bid = min(max(bid, 65.0), budget)

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    rich_aggressive = 0
    urgent_opps = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_aggressive += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opps += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    danger = 0
    if hp <= 2 or no_water >= 2:
        danger = 3
    elif hp <= 4 or no_water >= 1:
        danger = 2
    elif hp <= 6:
        danger = 1

    bid = 0.0

    if danger == 3:
        bid = max(95.0, max_prev + 6.0)
    elif danger == 2:
        bid = max(62.0 + 10.0 * scarcity, min(max_prev + 3.0, 108.0))
    else:
        if scarcity == 2:
            bid = max(38.0, min(max_prev * 0.55 + 6.0, 72.0))
        elif scarcity == 1:
            bid = max(28.0, min(avg_prev * 0.35 + 8.0, 52.0))
        else:
            bid = 16.0

    if rich_aggressive >= 2 and scarcity == 0 and danger == 0:
        bid = min(bid, 14.0)

    if urgent_opps >= 2 and scarcity >= 1:
        bid += 8.0

    if day >= 8:
        bid += 6.0
    if day == 10:
        bid += 10.0

    reserve_floor = 0.0
    days_left = 10 - day
    if danger == 0 and days_left > 0:
        reserve_floor = min(budget * 0.35, days_left * 12.0)

    affordable = max(0.0, budget - reserve_floor)
    if danger >= 2:
        affordable = budget

    final_bid = min(bid, affordable)
    if danger >= 2:
        final_bid = min(max(final_bid, 45.0), budget)

    if final_bid < 0:
        final_bid = 0.0

    return float(final_bid)
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_bids = []
    low_bids = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                b = float(bid)
                prev_bids.append(b)
                if b >= 80:
                    strong_bids.append(b)
                if b <= 40:
                    low_bids.append(b)

    if not alive:
        return min(budget, 18.0)

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    pressure = 0.0
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        pressure = max(avg_prev, highest_prev * 0.75)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    urgent = hp <= 3 or no_water_days >= 2
    semi_urgent = hp <= 5 or no_water_days >= 1

    if urgent:
        if strong_bids:
            bid = min(budget, max(95.0, highest_prev + 4.0))
        else:
            bid = min(budget, max(58.0, pressure + 3.0))
        return float(max(0.0, bid))

    if tight_supply:
        if highest_prev >= 150:
            bid = 34.0 if hp >= 7 else 72.0
        elif highest_prev >= 90:
            bid = 52.0 if hp >= 7 else 78.0
        elif highest_prev >= 35:
            bid = highest_prev + 2.5
        else:
            bid = 33.0
    elif ample_supply:
        if highest_prev >= 150:
            bid = 16.0
        elif highest_prev >= 90:
            bid = 20.0
        elif highest_prev >= 35:
            bid = 24.0
        else:
            bid = 18.0
    else:
        if highest_prev >= 150:
            bid = 20.0 if hp >= 6 else 60.0
        elif highest_prev >= 90:
            bid = 26.0 if hp >= 6 else 54.0
        elif highest_prev >= 35:
            bid = max(28.0, min(48.0, highest_prev + 1.5))
        else:
            bid = 24.0

    if semi_urgent:
        bid = max(bid, 48.0 if not tight_supply else 60.0)

    if day >= 8 and hp >= 6 and budget < 140:
        bid = min(bid, 26.0)

    if ample_supply and len(strong_bids) >= 1 and hp >= 6:
        bid = min(bid, 18.0)

    if len(low_bids) >= 2 and highest_prev <= 40:
        bid = max(bid, 29.0)

    bid = min(budget, bid)
    if bid < 0:
        bid = 0.0
    return float(bid)
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    highest_prev = 0.0
    cindy_prev = None
    pressure_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            if bid > highest_prev:
                highest_prev = bid
            if bid >= 80:
                pressure_count += 1
        if prev and opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if bid is not None and bid >= 90:
                cindy_prev = float(bid)

    units = supply / WATER_REQ
    scarce = units < 1.6
    comfortable = units >= 1.9
    critical = hp <= 2 or no_water_days >= 2
    fragile = hp <= 4 or no_water_days >= 1

    if critical:
        target = max(95.0, highest_prev + 2.0)
        if scarce:
            target = max(target, 108.0)
        return float(min(budget, target))

    if scarce:
        if cindy_prev is not None:
            target = cindy_prev + 1.5
        else:
            target = max(88.0, highest_prev + 1.5)
        if fragile:
            target += 6.0
        return float(min(budget, target))

    if comfortable and hp > 5 and no_water_days == 0:
        low = 12.0
        if highest_prev <= 20:
            low = 8.0
        return float(min(budget, low))

    if highest_prev >= 110:
        target = 26.0 if hp > 5 else 72.0
    elif highest_prev >= 90:
        target = 34.0 if hp > 5 else 84.0
    elif highest_prev >= 50:
        target = highest_prev + 1.5 if fragile else 28.0
    else:
        target = 22.0 if hp > 5 else 48.0

    if day >= 8 and hp <= 5:
        target = max(target, 78.0)

    return float(min(budget, target))
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    desperate = 0
    rich = 0
    prev_bids = []
    prev_high = 0.0
    prev_competitive = 0

    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate += 1
        if opp.get('budget', 0) >= 200:
            rich += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            b = float(bid)
            prev_bids.append(b)
            if b > prev_high:
                prev_high = b
            if b >= 90:
                prev_competitive += 1

    low_supply = supply <= 17
    high_supply = supply >= 22

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water >= 1:
        urgency += 3
    if low_supply:
        urgency += 2
    if desperate >= 2:
        urgency += 2
    if prev_high >= 120:
        urgency += 2
    elif prev_high >= 90:
        urgency += 1
    if day >= 8:
        urgency += 1

    if hp >= 7 and no_water == 0 and high_supply and prev_high >= 100:
        return float(min(budget, 8.0))

    if urgency <= 1:
        base = 14.0 if high_supply else 20.0
        if prev_high > 0:
            base = min(base, max(12.0, prev_high * 0.22))
        return float(min(budget, base))

    if urgency == 2:
        base = 26.0 if high_supply else 34.0
        if prev_bids:
            base = max(base, min(48.0, prev_high * 0.38))
        return float(min(budget, base))

    if urgency == 3:
        target = 52.0
        if prev_bids:
            target = max(target, min(78.0, prev_high * 0.62 + 2.0))
        return float(min(budget, target))

    if urgency == 4:
        target = 78.0
        if prev_bids:
            target = max(target, min(108.0, prev_high * 0.82 + 3.0))
        return float(min(budget, target))

    target = 108.0
    if prev_bids:
        target = max(target, min(145.0, prev_high + 4.0))
    if hp <= 1 or no_water >= 2:
        target = max(target, 132.0)
    if rich == 0 and prev_competitive == 0:
        target = min(target, 95.0)

    return float(min(budget, target))
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
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive:
        return max(0.0, min(float(budget), 18.0))

    slots = supply / float(WATER_REQ)
    scarcity = 0
    if slots < 1.2:
        scarcity = 2
    elif slots < 1.8:
        scarcity = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if no_water >= 2 or hp <= 2:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 4.0)
    elif no_water >= 1 or hp <= 4:
        bid = max(0.72 * DAILY_SALARY, avg_prev + 3.0)
    else:
        if scarcity == 2:
            bid = max(0.78 * DAILY_SALARY, highest_prev + 2.0)
        elif scarcity == 1:
            bid = max(0.58 * DAILY_SALARY, avg_prev + 1.5)
        else:
            bid = 0.34 * DAILY_SALARY

    if highest_prev >= 120:
        if hp >= 6 and no_water == 0 and scarcity == 0:
            bid = min(bid, 0.28 * DAILY_SALARY)
        else:
            bid = max(bid, 0.68 * DAILY_SALARY)

    if urgent_opp >= 2 and scarcity >= 1:
        bid += 6.0
    if rich_opp >= 2 and scarcity == 2:
        bid += 4.0

    if day <= 2 and scarcity == 0 and no_water == 0:
        bid = min(bid, 0.30 * DAILY_SALARY)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 25.0
    max_spend = max(0.0, float(budget) - reserve_floor)
    if no_water >= 1 or hp <= 4:
        max_spend = float(budget)

    bid = min(float(budget), bid)
    bid = min(max_spend if max_spend > 0 else float(budget), bid)

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
        base = 8.0 if hp > 3 else 18.0
        return float(max(0.0, min(budget, base)))

    pressure_bids = []
    desperate_count = 0
    rich_live = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            pressure_bids.append(float(prev['bid']))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 200:
            rich_live += 1

    highest_prev = max(pressure_bids) if pressure_bids else 0.0
    avg_prev = sum(pressure_bids) / len(pressure_bids) if pressure_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = hp <= 2 or no_water_days >= 2
    semi_urgent = hp <= 4 or no_water_days >= 1

    if urgent:
        bid = max(62.0, highest_prev + 3.0, 70.0 + 20.0 * scarcity)
        return float(max(0.0, min(budget, bid)))

    if semi_urgent:
        bid = max(38.0, avg_prev + 2.0, 42.0 + 12.0 * scarcity)
        if supply <= 17:
            bid = max(bid, highest_prev + 2.5)
        return float(max(0.0, min(budget, bid)))

    if supply >= 22:
        bid = 12.0 + 4.0 * scarcity
        if highest_prev > 120:
            bid = min(bid, 16.0)
        return float(max(0.0, min(budget, bid)))

    if supply >= 19:
        bid = 18.0 + 10.0 * scarcity
        if desperate_count >= 2:
            bid += 6.0
        if highest_prev > 90:
            bid = min(bid, 28.0)
        return float(max(0.0, min(budget, bid)))

    bid = 26.0 + 18.0 * scarcity + 3.0 * desperate_count
    if rich_live >= 1 and highest_prev >= 100:
        bid = min(bid, 36.0)
    else:
        bid = max(bid, min(highest_prev + 1.5, 55.0))

    if day >= 8 and hp > 5:
        bid *= 0.9

    return float(max(0.0, min(budget, bid)))
"""
