# ============================================================
# Experiment: exp_072
# Agent: Alex
# Source: exp_072
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.8)
        return max(0, safe_bid)

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    total_alive = len(alive_opponents)

    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    my_urgent = hp <= 2 or no_water_days >= 2
    somewhat_urgent = hp <= 4 or no_water_days >= 1

    supply_ratio = supply / float(WATER_REQ)
    contested = supply_ratio < (total_alive + 1)
    very_tight = supply_ratio < max(1.2, (total_alive + 1) * 0.7)

    if my_urgent:
        base = DAILY_SALARY * 0.92
        if highest_prev > 0:
            base = max(base, highest_prev + 2)
        if very_tight:
            base = max(base, DAILY_SALARY * 0.98)
        return max(0, min(budget, base))

    if very_tight:
        base = DAILY_SALARY * 0.72
        if highest_prev > 0:
            base = max(base, highest_prev + 1.5)
        if urgent_opponents >= total_alive / 2.0:
            base += 3
        return max(0, min(budget, base))

    if contested:
        base = DAILY_SALARY * 0.56
        if highest_prev >= DAILY_SALARY * 0.8:
            base = DAILY_SALARY * 0.42 if hp > 4 else DAILY_SALARY * 0.86
        elif highest_prev > 0:
            base = max(base, avg_prev + 1)
        if somewhat_urgent:
            base = max(base, DAILY_SALARY * 0.68)
        return max(0, min(budget, base))

    base = DAILY_SALARY * 0.28
    if highest_prev > 0 and highest_prev < DAILY_SALARY * 0.4:
        base = max(base, highest_prev * 0.9)
    if somewhat_urgent:
        base = max(base, DAILY_SALARY * 0.45)
    if rich_opponents == total_alive and avg_prev > DAILY_SALARY * 0.6:
        base = DAILY_SALARY * 0.22

    return max(0, min(budget, base))
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

    alive = []
    prev_bids = []
    rich_aggressive = 0
    weak_opp = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                weak_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if b >= 0.75 * DAILY_SALARY and opp.get('budget', 0) > 2 * DAILY_SALARY:
                    rich_aggressive += 1

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    capacity = supply / float(WATER_REQ)
    scarcity = capacity < (len(alive) + 1)
    very_tight = capacity < len(alive)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    emergency = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if emergency:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 2.0)
    elif very_tight:
        if highest_prev >= DAILY_SALARY * 0.85:
            bid = DAILY_SALARY * (0.88 if pressured else 0.52)
        else:
            bid = max(DAILY_SALARY * (0.72 if pressured else 0.46), highest_prev + 1.25)
    elif scarcity:
        if rich_aggressive >= 2 and hp > 4:
            bid = DAILY_SALARY * 0.34
        else:
            bid = max(DAILY_SALARY * (0.58 if pressured else 0.38), min(highest_prev + 1.0, DAILY_SALARY * 0.76))
    else:
        bid = DAILY_SALARY * (0.42 if pressured else 0.22)

    if weak_opp >= 2 and hp > 4 and not emergency:
        bid *= 0.9

    if day >= 8 and hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.78)

    if budget < DAILY_SALARY:
        bid = min(bid, max(0.0, budget * (0.72 if pressured else 0.5)))
    else:
        reserve = max(0.0, (10 - day) * DAILY_SALARY * 0.18)
        bid = min(bid, max(0.0, budget - reserve))

    if budget <= 0:
        return 0.0
    return max(0.0, min(budget, bid))
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
    prev_bids = []
    threat_bids = []
    rich_threat = 0.0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > rich_threat:
                rich_threat = opp.get('budget', 0)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('budget', 0) > DAILY_SALARY * 4 or opp.get('hp', 0) >= 6:
                    threat_bids.append(bid)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_bids) if threat_bids else highest_prev

    tight_supply = supply <= 17
    very_tight = supply <= 15.5
    danger = hp <= 3 or no_water_days >= 2
    caution = hp <= 5 or no_water_days >= 1

    if danger:
        bid = max(DAILY_SALARY * 0.88, highest_threat + 2.0)
    elif very_tight:
        bid = max(DAILY_SALARY * 0.72, highest_threat + 1.5)
    elif tight_supply:
        bid = max(DAILY_SALARY * 0.6, highest_threat * 0.92 + 1.0)
    elif caution:
        bid = max(DAILY_SALARY * 0.48, highest_threat * 0.75)
    else:
        bid = max(DAILY_SALARY * 0.34, highest_threat * 0.55)

    if highest_prev >= DAILY_SALARY * 0.9 and not danger and hp >= 6:
        bid = min(bid, DAILY_SALARY * 0.42)

    if day >= 8 and hp >= 6 and budget < rich_threat:
        bid = min(bid, DAILY_SALARY * 0.45)

    if budget <= DAILY_SALARY * 0.8:
        if danger:
            bid = max(min(budget, DAILY_SALARY * 0.85), min(budget, highest_threat + 1.0))
        else:
            bid = min(bid, budget)

    bid = max(0.0, min(budget, bid))
    return bid
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 45.0))
        return float(min(budget, 12.0))

    prev_bids = []
    aggressive_bids = []
    active_threats = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 95:
                aggressive_bids.append(float(bid))
        if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
            active_threats += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0
    high_anchor = max(aggressive_bids) if aggressive_bids else highest_prev

    units = int(supply // WATER_REQ)
    tight_supply = units <= 1

    emergency = hp <= 2 or no_water_days >= 1
    fragile = hp <= 4

    if emergency:
        target = max(110.0, high_anchor + 2.0)
        if tight_supply:
            target = max(target, 128.0)
        return float(min(budget, target))

    if fragile and tight_supply:
        target = max(96.0, avg_prev * 0.92)
        return float(min(budget, target))

    if tight_supply:
        if highest_prev >= 120:
            target = 18.0
        else:
            target = 28.0
        return float(min(budget, target))

    if active_threats >= 2 and highest_prev >= 100:
        return float(min(budget, 10.0))

    return float(min(budget, 16.0))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    desperate_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    if bid >= 100:
                        aggressive_count += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    if day >= 8 and hp <= 5:
        urgency += 1

    if urgency >= 5:
        bid = max(95.0, highest_prev + 4.0)
    elif urgency >= 3:
        bid = max(62.0 + 8.0 * scarcity, avg_prev * 0.72 + 6.0)
    else:
        if supply >= 22:
            bid = 22.0
        elif supply >= 19:
            bid = 30.0
        else:
            bid = 40.0

        if highest_prev > 0:
            if highest_prev >= 140:
                bid = min(bid, 36.0 + 4.0 * scarcity)
            elif highest_prev >= 100:
                bid = max(bid, 44.0 + 5.0 * scarcity)
            elif highest_prev >= 70:
                bid = max(bid, highest_prev * 0.68)
            else:
                bid = max(bid, highest_prev + 2.0)

    if aggressive_count >= 2 and urgency <= 2:
        bid *= 0.88
    if desperate_count >= 2 and scarcity >= 1:
        bid += 8.0

    reserve = 0.0
    if hp > 4 and day <= 7:
        reserve = 25.0
    elif hp > 2:
        reserve = 10.0

    cap = budget - reserve
    if urgency >= 4:
        cap = budget
    if cap < 0:
        cap = 0.0

    bid = min(bid, cap)

    if urgency >= 4 and bid < 55.0 and budget >= 55.0:
        bid = min(budget, 55.0 + 5.0 * scarcity)

    if bid < 0:
        bid = 0.0

    return float(round(min(budget, bid), 2))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return min(budget, 18.0)

    prev_bids = []
    strong_count = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 80:
                strong_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    desperate = hp <= 3 or no_water >= 2
    pressured = hp <= 5 or no_water >= 1
    high_supply = supply >= 22

    if desperate:
        target = max(88.0, highest_prev + 2.5)
        if high_supply:
            target += 4.0
        return min(budget, target)

    if pressured:
        if highest_prev >= 100:
            target = 72.0 if not high_supply else 82.0
        elif highest_prev >= 85:
            target = highest_prev + 1.5
        else:
            target = max(66.0, avg_prev + 2.0)
        return min(budget, target)

    if high_supply:
        if highest_prev >= 100:
            target = 58.0
        elif highest_prev >= 85:
            target = 64.0
        else:
            target = max(60.0, avg_prev - 2.0)
        return min(budget, target)

    if strong_count >= 1 and highest_prev >= 100:
        target = 16.0
    elif highest_prev >= 90:
        target = 28.0
    elif highest_prev >= 75:
        target = 44.0
    else:
        target = 52.0

    if day >= 8 and hp >= 7:
        target -= 6.0

    if budget < 120:
        target = min(target, 45.0)

    return max(0.0, min(budget, target))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.2))

    prev_bids = []
    rich_aggressive = 0
    needy_opponents = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 110:
                rich_aggressive += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            needy_opponents += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if supply >= 24:
        scarcity = 0
    elif supply >= 21:
        scarcity = 1
    elif supply >= 18:
        scarcity = 2
    else:
        scarcity = 3

    if hp <= 2 or no_water_days >= 2:
        emergency_bid = max(95.0, highest_prev + 3.0)
        if scarcity >= 2:
            emergency_bid = max(emergency_bid, 125.0)
        return float(min(budget, emergency_bid))

    if hp <= 4 or no_water_days >= 1:
        if scarcity == 3:
            return float(min(budget, max(118.0, highest_prev + 2.0)))
        if scarcity == 2:
            return float(min(budget, max(92.0, avg_prev * 0.8 + 8.0)))
        return float(min(budget, 62.0))

    if rich_aggressive >= 2:
        if scarcity <= 1:
            return float(min(budget, 1.0))
        if scarcity == 2:
            return float(min(budget, 12.0))
        return float(min(budget, 38.0))

    if highest_prev >= 100:
        if scarcity <= 1:
            return float(min(budget, 2.0))
        if scarcity == 2:
            return float(min(budget, 18.0))
        return float(min(budget, 45.0))

    if needy_opponents >= 2 and scarcity >= 2:
        return float(min(budget, max(55.0, highest_prev + 2.0)))

    base_by_scarcity = [3.0, 8.0, 18.0, 34.0]
    bid = base_by_scarcity[int(scarcity)]

    if day >= 8 and hp >= 6:
        bid *= 0.7

    if budget < 80:
        bid *= 0.8

    return float(min(budget, max(0.0, bid)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 3 or no_water >= 1:
            safe_bid = DAILY_SALARY * 0.7
        return float(min(budget, safe_bid))

    capacity = supply / float(WATER_REQ)
    tight = capacity <= 1.45
    medium = capacity <= 1.8

    opp_bids = []
    urgent_bids = []
    rich_pressure = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        prev_bid = None
        if prev:
            prev_bid = prev.get('bid')
        if prev_bid is not None:
            opp_bids.append(float(prev_bid))
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                urgent_bids.append(float(prev_bid))
            if opp.get('budget', 0) > DAILY_SALARY * 3:
                rich_pressure.append(float(prev_bid))

    highest_prev = max(opp_bids) if opp_bids else 0.0
    urgent_prev = max(urgent_bids) if urgent_bids else highest_prev
    rich_prev = max(rich_pressure) if rich_pressure else highest_prev

    if hp <= 2 or no_water >= 2:
        bid = max(DAILY_SALARY * 0.95, urgent_prev + 3.0)
    elif hp <= 4 or no_water >= 1:
        if tight:
            bid = max(DAILY_SALARY * 0.82, urgent_prev + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.62, highest_prev * 0.72)
    else:
        if tight:
            bid = max(DAILY_SALARY * 0.58, rich_prev + 1.5)
        elif medium:
            bid = max(DAILY_SALARY * 0.46, highest_prev * 0.58)
        else:
            bid = DAILY_SALARY * 0.28

    days_left = 11 - day
    reserve_target = max(0.0, (days_left - 1) * DAILY_SALARY * 0.42)
    spend_cap = budget - reserve_target
    if hp <= 3 or no_water >= 1:
        spend_cap = budget - max(0.0, (days_left - 1) * DAILY_SALARY * 0.28)
    if spend_cap <= 0:
        spend_cap = min(budget, DAILY_SALARY * 0.45)
        if hp <= 3 or no_water >= 1:
            spend_cap = min(budget, DAILY_SALARY * 0.75)

    bid = min(bid, spend_cap)
    bid = min(bid, budget)

    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
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

    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    supply = day_context['supply']
    day = day_context['day']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    strong_prev = []
    weak_prev = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = prev.get('bid', 0.0)
            prev_bids.append(b)
            if b >= 120:
                strong_prev.append(b)
            if b <= 50:
                weak_prev.append(b)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0

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

    if supply <= 17:
        urgency += 2
    elif supply <= 20:
        urgency += 1
    elif supply >= 23:
        urgency -= 1

    if day >= 8:
        urgency += 1

    rich_aggressive = 0
    for opp in alive:
        if opp.get('budget', 0) >= 150 and opp.get('hp', 0) >= 6:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None and prev.get('bid', 0) >= 120:
                rich_aggressive += 1

    if urgency <= 0:
        base = DAILY_SALARY * 0.28
        if weak_prev:
            base = max(base, lowest_prev + 2.0)
        bid = base
    elif urgency == 1:
        base = DAILY_SALARY * 0.48
        if highest_prev > 0:
            if highest_prev >= 150:
                base = max(base, DAILY_SALARY * 0.42)
            else:
                base = max(base, min(highest_prev + 3.0, DAILY_SALARY * 0.78))
        bid = base
    elif urgency == 2:
        base = DAILY_SALARY * 0.72
        if highest_prev > 0 and highest_prev < 120:
            base = max(base, highest_prev + 4.0)
        elif highest_prev >= 120:
            base = max(base, DAILY_SALARY * 0.82)
        bid = base
    else:
        base = DAILY_SALARY * 0.95
        if highest_prev > 0 and highest_prev < 140:
            base = max(base, highest_prev + 6.0)
        bid = base

    if rich_aggressive >= 2 and urgency <= 1:
        bid *= 0.82
    elif rich_aggressive >= 1 and urgency == 0:
        bid *= 0.9

    reserve_days = 10 - day
    if reserve_days < 1:
        reserve_days = 1
    soft_cap = budget
    if urgency <= 1:
        soft_cap = min(soft_cap, budget / float(reserve_days) + DAILY_SALARY * 0.35)
    elif urgency == 2:
        soft_cap = min(soft_cap, budget / float(reserve_days) + DAILY_SALARY * 0.7)

    bid = min(bid, soft_cap)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    if budget < DAILY_SALARY * 0.5:
        bid = min(bid, budget)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(bid)
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
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    unit_slots = max(1, int(supply / WATER_REQ))
    tight = unit_slots <= 1

    prev_bids = []
    danger_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                danger_bids.append(float(bid))

    max_prev = max(prev_bids) if prev_bids else 0.0
    max_danger = max(danger_bids) if danger_bids else max_prev

    if not alive:
        return float(min(budget, 20.0))

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
    if tight:
        urgency += 2
    if day >= 8:
        urgency += 1

    if urgency >= 5:
        target = max(max_danger + 2.0, DAILY_SALARY * 0.95)
    elif urgency >= 3:
        if max_prev > 0:
            target = max(DAILY_SALARY * 0.62, max_prev + 1.5)
        else:
            target = DAILY_SALARY * 0.62
    else:
        if tight:
            if max_prev >= DAILY_SALARY * 1.5:
                target = DAILY_SALARY * 0.28
            elif max_prev > 0:
                target = min(DAILY_SALARY * 0.58, max_prev + 1.0)
            else:
                target = DAILY_SALARY * 0.45
        else:
            if max_prev >= DAILY_SALARY * 1.5:
                target = DAILY_SALARY * 0.18
            elif max_prev > 0:
                target = min(DAILY_SALARY * 0.42, max_prev * 0.7)
            else:
                target = DAILY_SALARY * 0.3

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0 and urgency < 5:
        soft_cap = min(budget, budget / float(reserve_days))
        if urgency <= 1:
            soft_cap = min(soft_cap, DAILY_SALARY * 0.5)
        elif urgency == 2:
            soft_cap = min(soft_cap * 1.2, DAILY_SALARY * 0.75)
        else:
            soft_cap = min(soft_cap * 1.5, DAILY_SALARY * 1.05)

    bid = min(budget, max(0.0, target, 1.0))
    if urgency < 5:
        bid = min(bid, max(1.0, soft_cap))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

    return float(max(0.0, min(budget, bid)))
"""
