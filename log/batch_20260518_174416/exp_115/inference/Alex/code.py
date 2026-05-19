# ============================================================
# Experiment: exp_115
# Agent: Alex
# Source: exp_115
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, DAILY_SALARY * 0.9)
        return min(budget, DAILY_SALARY * 0.35)

    total_players = 1 + len(alive_opponents)
    expected_units = supply / float(WATER_REQ)
    scarcity = total_players - expected_units

    prev_bids = []
    desperate_opp = False
    rich_pressure = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp = True
        if opp.get('budget', 0) > budget * 1.2:
            rich_pressure = True

    highest_prev = max(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 2:
        target = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
    elif hp <= 4 or no_water_days >= 1:
        target = max(DAILY_SALARY * 0.72, highest_prev + 1.5)
    else:
        if scarcity <= 0:
            target = DAILY_SALARY * 0.32
        elif scarcity < 1.5:
            target = DAILY_SALARY * 0.48
        else:
            target = DAILY_SALARY * 0.62

        if highest_prev > 0:
            if highest_prev >= DAILY_SALARY * 0.85:
                target = DAILY_SALARY * 0.28 if hp > 4 else DAILY_SALARY * 0.88
            else:
                target = max(target, highest_prev + 1.25)

    if desperate_opp:
        target += 3.0
    if rich_pressure and scarcity > 0.5:
        target += 2.0

    if budget < DAILY_SALARY * 0.5:
        target = min(target, budget * 0.85)

    target = max(0.0, min(float(budget), float(target)))
    return target
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    strong_prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if opp.get('hp', 0) > 2 and opp.get('budget', 0) > 0:
                    strong_prev_bids.append(bid)

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strong_highest_prev = max(strong_prev_bids) if strong_prev_bids else highest_prev

    tight_supply = supply <= 18
    very_tight_supply = supply <= 16

    emergency = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if emergency:
        target = max(78.0, strong_highest_prev + 2.0)
        if very_tight_supply:
            target = max(target, strong_highest_prev + 6.0)
        return float(min(budget, target))

    if pressured:
        if strong_highest_prev >= 85.0:
            target = 72.0 if not tight_supply else 84.0
        else:
            target = max(58.0, strong_highest_prev + 1.5)
        return float(min(budget, target))

    if very_tight_supply:
        target = 22.0
    elif tight_supply:
        target = 18.0
    else:
        target = 14.0

    if highest_prev < 40.0:
        target = max(target, highest_prev + 1.0)

    if budget < 120:
        target = min(target, 16.0)

    return float(min(budget, target))
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
    rich_aggressive = 0
    weak_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                weak_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80 and opp.get('budget', 0) >= 120:
                    rich_aggressive += 1

    if not alive:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
    elif no_water_days >= 1:
        urgency += 0.45

    base = 18.0 + 22.0 * scarcity + 10.0 * urgency

    if supply >= 23:
        base -= 8.0
    elif supply <= 17:
        base += 10.0

    if highest_prev >= 140:
        if urgency < 0.9:
            bid = base * 0.75
        else:
            bid = max(base + 10.0, 0.78 * highest_prev)
    elif highest_prev >= 90:
        if rich_aggressive >= 2 and urgency < 0.8:
            bid = max(base, avg_prev * 0.72)
        else:
            bid = max(base, min(highest_prev + 2.0, avg_prev + 12.0))
    elif highest_prev > 0:
        bid = max(base, highest_prev + 1.5)
    else:
        bid = base

    if weak_opp >= 2 and urgency < 0.7:
        bid -= 4.0

    if day >= 8:
        bid += 6.0 * urgency + 3.0 * scarcity

    if budget < 60:
        bid = min(bid, max(12.0, budget * 0.72))
    elif budget < 120:
        bid = min(bid, budget * 0.82)
    else:
        bid = min(bid, budget * 0.9)

    floor_bid = 8.0
    if urgency >= 1.0:
        floor_bid = 28.0
    elif urgency >= 0.45:
        floor_bid = 20.0

    bid = max(floor_bid, bid)
    bid = min(bid, budget)

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

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= DAILY_SALARY * 1.5:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    slots = max(1, int(supply // WATER_REQ))
    scarcity = len(alive) + 1 - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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

    if scarcity >= 3:
        urgency += 2
    elif scarcity >= 2:
        urgency += 1

    if supply <= 16:
        urgency += 2
    elif supply <= 19:
        urgency += 1

    if desperate_count >= 2:
        urgency += 1

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    if urgency >= 6:
        target = max(DAILY_SALARY * 0.95, min(highest_prev + 2.0, DAILY_SALARY * 1.15))
    elif urgency >= 4:
        target = max(DAILY_SALARY * 0.72, min(avg_prev + 3.0, DAILY_SALARY * 0.98))
    elif urgency >= 2:
        target = max(DAILY_SALARY * 0.48, min(avg_prev * 0.82 + 2.0, DAILY_SALARY * 0.78))
    else:
        target = DAILY_SALARY * 0.32

    if highest_prev > 200:
        target = min(target, DAILY_SALARY * 0.76)
    elif highest_prev > 120 and urgency < 5:
        target = min(target, DAILY_SALARY * 0.68)

    if rich_count == 0 and scarcity <= 1 and urgency <= 2:
        target = min(target, DAILY_SALARY * 0.4)

    remaining_days = max(0, 10 - int(day) + 1)
    reserve_floor = max(0.0, remaining_days * DAILY_SALARY * 0.18)
    spend_cap = budget if urgency >= 5 else max(0.0, budget - reserve_floor)

    if spend_cap <= 0:
        return float(min(budget, DAILY_SALARY * 0.2))

    bid = min(target, spend_cap, budget)
    if hp <= 2 or no_water_days >= 2:
        bid = min(max(bid, DAILY_SALARY * 0.9), budget)

    return float(max(0.0, bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    opp_bids = []
    strong_bids = []
    desperate_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                opp_bids.append(bid)
                if bid <= 110:
                    strong_bids.append(bid)

    if not alive:
        return max(0.0, min(budget, 18.0))

    slots = supply / float(WATER_REQ)
    tight = slots < 2.0
    medium = slots < 2.5

    prev_high = max(opp_bids) if opp_bids else 0.0
    prev_mid_high = max(strong_bids) if strong_bids else 0.0

    my_prev_bid = None
    my_prev_won = None
    sample_prev = None
    for opp in alive:
        p = opp.get('previous_trace', {})
        if p:
            sample_prev = p
            break
    if sample_prev and sample_prev.get('day') is not None and sample_prev.get('day') >= 1:
        my_prev_bid = budget - DAILY_SALARY
        if my_prev_bid < 0:
            my_prev_bid = 0.0
        if no_water == 0:
            my_prev_won = True
        elif no_water >= 1:
            my_prev_won = False

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        target = max(95.0, prev_mid_high + 3.0)
        if prev_high >= 140:
            target = max(target, 98.0)
        return max(0.0, min(budget, target))

    if tight:
        if urgent:
            target = max(90.0, prev_mid_high + 2.5)
        else:
            if desperate_count >= 2:
                target = max(72.0, prev_mid_high + 1.5)
            else:
                target = max(68.0, prev_mid_high + 1.0)
        if prev_high >= 150 and hp > 3:
            target = min(target, 84.0)
        return max(0.0, min(budget, target))

    if medium:
        if my_prev_won is False:
            target = max(60.0, prev_mid_high + 1.0)
        elif urgent:
            target = max(58.0, prev_mid_high)
        else:
            target = 46.0 if prev_high >= 140 else 52.0
        return max(0.0, min(budget, target))

    if urgent:
        target = 55.0
    else:
        target = 32.0 if prev_high >= 140 else 38.0
    return max(0.0, min(budget, target))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_pressure = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid > opp_pressure:
                    opp_pressure = bid

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.7))
        return float(min(budget, DAILY_SALARY * 0.25))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.55
    elif hp <= 4:
        danger += 0.3
    if no_water_days >= 2:
        danger += 0.35
    elif no_water_days >= 1:
        danger += 0.18

    avg_prev = 0.0
    if prev_bids:
        avg_prev = sum(prev_bids) / float(len(prev_bids))

    live_count = len(alive_opponents)
    competitive_load = 0.08 * live_count

    base = DAILY_SALARY * (0.22 + 0.42 * scarcity + danger + competitive_load)

    if opp_pressure > 0:
        if scarcity >= 0.7 or danger >= 0.45:
            target = max(base, opp_pressure + 2.5)
        elif scarcity <= 0.25 and danger < 0.2:
            target = min(base, max(12.0, avg_prev * 0.45))
        else:
            target = max(base, avg_prev * 0.78)
    else:
        target = base

    if supply >= 23 and hp > 4 and no_water_days == 0:
        target *= 0.72
    elif supply <= 17:
        target *= 1.18

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.72)

    if day >= 8 and budget > DAILY_SALARY * 2:
        target *= 1.08

    max_safe = budget
    if day < 4:
        max_safe = min(max_safe, DAILY_SALARY * 1.15)
    else:
        max_safe = min(max_safe, budget)

    bid = min(max_safe, target)
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    units = supply / float(WATER_REQ)
    severe_tight = units <= 1.25
    tight = units <= 1.6
    roomy = units >= 1.9

    prev_bids = []
    rich_pressure = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > budget * 0.9:
                if bid > rich_pressure:
                    rich_pressure = float(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    ref_bid = max(highest_prev, rich_pressure)

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
        urgency += 1

    if severe_tight:
        urgency += 2
    elif tight:
        urgency += 1
    elif roomy:
        urgency -= 1

    if day >= 8:
        urgency += 1

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if urgency >= 3:
            base = DAILY_SALARY * 0.75
        return float(min(budget, base))

    if urgency <= 0:
        bid = DAILY_SALARY * 0.28 if roomy else DAILY_SALARY * 0.38
    elif urgency == 1:
        bid = max(DAILY_SALARY * 0.52, ref_bid * 0.78)
    elif urgency == 2:
        bid = max(DAILY_SALARY * 0.72, ref_bid + 2.0)
    elif urgency == 3:
        bid = max(DAILY_SALARY * 0.9, ref_bid + 4.0)
    else:
        bid = max(DAILY_SALARY * 1.05, ref_bid + 8.0)

    if roomy and urgency <= 1:
        bid = min(bid, DAILY_SALARY * 0.55)

    if severe_tight and hp <= 4:
        bid = max(bid, ref_bid + 10.0, DAILY_SALARY * 1.0)

    safety_cap = budget
    if hp > 5 and no_water_days == 0 and day < 7:
        safety_cap = min(safety_cap, budget * 0.42 + DAILY_SALARY * 0.25)
    elif hp > 3:
        safety_cap = min(safety_cap, budget * 0.6 + DAILY_SALARY * 0.35)

    bid = min(bid, budget, safety_cap)
    if urgency >= 3:
        bid = min(max(bid, DAILY_SALARY * 0.82), budget)

    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    prev_bids = []
    david_like_bid = None
    cindy_like_bid = None
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            req = opp.get('water_requirement', 0)
            sal = opp.get('daily_salary', 0)
            if req == 13 and sal == 70:
                if 70 <= bid <= 100:
                    if david_like_bid is None or bid > david_like_bid:
                        david_like_bid = float(bid)
                if bid >= 150:
                    if cindy_like_bid is None or bid > cindy_like_bid:
                        cindy_like_bid = float(bid)

    high_pressure = max(prev_bids) if prev_bids else 0.0
    slots = int(supply // WATER_REQ)
    tight = slots <= 1

    critical = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if critical:
        if tight:
            target = 92.0
            if david_like_bid is not None:
                target = max(target, david_like_bid + 2.0)
            if cindy_like_bid is not None and budget > cindy_like_bid + 5.0:
                target = cindy_like_bid + 1.0
            return float(min(budget, target))
        return float(min(budget, 78.0))

    if tight:
        if budget < 120:
            return float(min(budget, 18.0))
        target = 89.5
        if david_like_bid is not None:
            target = max(target, david_like_bid + 1.5)
        if pressured:
            target += 4.0
        if high_pressure >= 150 and not pressured:
            target = min(target, 90.0)
        return float(min(budget, target))

    if pressured:
        base = 58.0
        if david_like_bid is not None:
            base = max(base, min(80.0, david_like_bid - 6.0))
        return float(min(budget, base))

    if day <= 2:
        return float(min(budget, 28.0))

    return float(min(budget, 22.0))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_pressure = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                req = opp.get('water_requirement', WATER_REQ)
                if req <= supply:
                    dangerous_pressure = max(dangerous_pressure, bid)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    urgency = 0.0
    if hp <= 2:
        urgency += 1.2
    elif hp <= 4:
        urgency += 0.7
    elif hp <= 6:
        urgency += 0.35

    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.45

    urgency += 0.55 * scarcity

    if prev_bids:
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        max_prev = max(prev_bids)
    else:
        avg_prev = 0.0
        max_prev = 0.0

    if supply >= 23:
        base = 10.0
    elif supply >= 20:
        base = 18.0
    elif supply >= 17:
        base = 28.0
    else:
        base = 40.0

    if urgency >= 1.6:
        bid = max(base + 20.0, avg_prev * 0.72 + 6.0)
    elif urgency >= 0.9:
        bid = max(base + 8.0, avg_prev * 0.5 + 4.0)
    else:
        if max_prev >= 120:
            bid = base * 0.55
        elif max_prev >= 90:
            bid = base * 0.75
        else:
            bid = max(base, avg_prev * 0.38 + 3.0)

    if dangerous_pressure >= 140 and urgency < 1.6:
        bid *= 0.75
    elif dangerous_pressure <= 40 and urgency >= 0.9:
        bid = max(bid, dangerous_pressure + 3.0, 26.0)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 52.0)
    elif hp <= 4:
        bid = max(bid, 34.0)

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.82)
    else:
        reserve_target = DAILY_SALARY * 2.2
        if budget < reserve_target and urgency < 1.0:
            bid = min(bid, DAILY_SALARY * 0.55)

    bid = max(0.0, min(float(budget), float(bid)))
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            safe_bid = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, safe_bid)))

    opp_pressures = []
    expensive_winners = 0
    desperate_opponents = 0

    for opp in alive:
        prev = opp.get('previous_trace') or {}
        prev_bid = prev.get('bid')
        prev_status = prev.get('status')
        opp_hp = opp.get('hp', 10)
        opp_nwd = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0.0)
        opp_salary = opp.get('daily_salary', DAILY_SALARY)

        pressure = 0.0
        if prev_bid is not None:
            pressure = float(prev_bid)
            if prev_status == 'won':
                pressure *= 0.9
                if float(prev_bid) >= opp_salary * 0.9:
                    expensive_winners += 1
            elif prev_status in ('lost', 'died'):
                pressure *= 1.08
        else:
            pressure = opp_salary * 0.55

        if opp_hp <= 3 or opp_nwd >= 2:
            pressure *= 1.15
            desperate_opponents += 1

        pressure = min(pressure, opp_budget)
        opp_pressures.append(pressure)

    highest_pressure = max(opp_pressures) if opp_pressures else DAILY_SALARY * 0.55
    avg_pressure = sum(opp_pressures) / len(opp_pressures) if opp_pressures else DAILY_SALARY * 0.55

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 0.45
    elif hp <= 4:
        urgency += 0.22
    if no_water_days >= 2:
        urgency += 0.35
    elif no_water_days == 1:
        urgency += 0.12

    if supply >= 23:
        base = DAILY_SALARY * 0.28
    elif supply >= 20:
        base = DAILY_SALARY * 0.42
    elif supply >= 17:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.82

    target = max(base, avg_pressure * (0.82 + 0.18 * scarcity))

    if scarcity >= 0.7 or urgency >= 0.35:
        target = max(target, highest_pressure + 2.5)
    elif scarcity >= 0.4:
        target = max(target, highest_pressure * 0.96 + 1.0)

    if expensive_winners >= 2 and urgency < 0.35 and supply >= 20:
        target *= 0.9

    if desperate_opponents >= 2 and (hp <= 4 or no_water_days >= 1):
        target = max(target, highest_pressure + 4.0)

    if day >= 8:
        target *= 1.08
    if day >= 9 and (hp <= 5 or no_water_days >= 1):
        target *= 1.12

    reserve_floor = 0.0
    if hp > 4 and no_water_days == 0 and day <= 6:
        reserve_floor = budget * 0.72
        target = min(target, budget - reserve_floor + DAILY_SALARY * 0.25)

    min_survival_bid = 0.0
    if hp <= 2 or no_water_days >= 2:
        min_survival_bid = DAILY_SALARY * 0.9
    elif hp <= 4 or no_water_days == 1:
        min_survival_bid = DAILY_SALARY * 0.65

    bid = max(min_survival_bid, target)
    bid = min(budget, bid)
    bid = max(0.0, bid)
    return float(round(bid, 2))
"""
