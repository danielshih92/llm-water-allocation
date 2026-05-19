# ============================================================
# Experiment: exp_042
# Agent: Alex
# Source: exp_042
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

    if budget <= 0:
        return 0

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return max(0, min(budget, base))

    prev_bids = []
    opp_urgent = 0
    opp_errors = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
            if prev.get('error'):
                opp_errors += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            opp_urgent += 1

    high_pressure = 0
    avg_pressure = 0
    if prev_bids:
        high_pressure = max(prev_bids)
        avg_pressure = sum(prev_bids) / float(len(prev_bids))

    supply_ratio = supply / float(WATER_REQ)

    if hp <= 1 or no_water >= 2:
        bid = DAILY_SALARY * 0.98
    elif hp <= 2 or no_water >= 1:
        bid = DAILY_SALARY * 0.88
    else:
        if supply_ratio >= 1.8:
            bid = DAILY_SALARY * 0.34
        elif supply_ratio >= 1.4:
            bid = DAILY_SALARY * 0.46
        else:
            bid = DAILY_SALARY * 0.6

        if high_pressure > 0:
            if high_pressure >= DAILY_SALARY * 0.9:
                bid = max(bid, DAILY_SALARY * 0.52)
            elif high_pressure >= DAILY_SALARY * 0.7:
                bid = max(bid, min(DAILY_SALARY * 0.78, high_pressure + 2.0))
            else:
                bid = max(bid, avg_pressure + 1.5)

        if opp_urgent >= max(1, len(alive) // 2):
            bid += 4.0
        if opp_errors > 0:
            bid -= 2.0

    if budget < DAILY_SALARY * 2 and hp > 2 and no_water == 0:
        bid *= 0.82

    bid = max(0, min(budget, bid))
    return bid
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    prev_active_bids = []
    david_like_bid = None
    rich_aggressive = 0
    low_pressure_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if prev.get('status') != 'dead':
                    prev_active_bids.append(float(bid))
                if 48 <= float(bid) <= 60:
                    if david_like_bid is None or float(bid) > david_like_bid:
                        david_like_bid = float(bid)
                if float(bid) >= 75 and opp.get('budget', 0) > 300:
                    rich_aggressive += 1
                if float(bid) <= 45:
                    low_pressure_count += 1

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    active_highest_prev = max(prev_active_bids) if prev_active_bids else highest_prev
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Urgency from health and deprivation
    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1

    # Supply pressure heuristic
    if supply <= 16:
        pressure = 'tight'
    elif supply >= 22:
        pressure = 'loose'
    else:
        pressure = 'mid'

    # Base strategy
    if urgent:
        if active_highest_prev >= 85:
            bid = 90.0
        elif david_like_bid is not None:
            bid = david_like_bid + 2.5
        else:
            bid = max(62.0, active_highest_prev + 2.0)
    elif semi_urgent:
        if pressure == 'tight':
            if david_like_bid is not None:
                bid = david_like_bid + 1.5
            else:
                bid = max(56.0, min(72.0, active_highest_prev + 1.5))
        elif pressure == 'mid':
            bid = max(42.0, min(60.0, avg_prev * 0.9 if avg_prev > 0 else 49.0))
        else:
            bid = 34.0
    else:
        if pressure == 'loose':
            bid = 18.0 if rich_aggressive >= 2 else 24.0
        elif pressure == 'mid':
            if active_highest_prev <= 56:
                bid = min(58.0, active_highest_prev + 1.2)
            else:
                bid = 31.0 if rich_aggressive >= 2 else 39.0
        else:
            if david_like_bid is not None and rich_aggressive == 0:
                bid = david_like_bid + 1.2
            elif rich_aggressive >= 2:
                bid = 28.0
            else:
                bid = 47.0

    # Endgame survival adjustment
    if day >= 8:
        if hp <= 5:
            bid = max(bid, 68.0)
        elif pressure == 'loose':
            bid = max(bid, 26.0)

    # Budget discipline
    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0:
        soft_cap = min(soft_cap, max(22.0, budget / (reserve_days + 0.5) + 8.0))

    if urgent:
        soft_cap = budget

    bid = min(bid, soft_cap, budget)
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 8:
            rich_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif hp <= 4 or no_water_days >= 1:
        if supply_tight:
            bid = max(DAILY_SALARY * 0.82, highest_prev + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.68, avg_prev + 2.0)
    else:
        if supply_loose:
            bid = max(DAILY_SALARY * 0.28, avg_prev * 0.75)
        elif supply_tight:
            bid = max(DAILY_SALARY * 0.52, avg_prev + 1.0)
        else:
            bid = max(DAILY_SALARY * 0.4, avg_prev * 0.9)

    if urgent_opp >= 2:
        bid += 6.0
    elif urgent_opp == 1:
        bid += 3.0

    if rich_opp >= 1 and highest_prev >= DAILY_SALARY * 0.9:
        if hp > 4 and no_water_days == 0:
            bid *= 0.72
        else:
            bid = max(bid, DAILY_SALARY * 0.88)

    if day >= 8:
        bid += 4.0
    if day == 10:
        bid += 6.0

    reserve_floor = 0.0
    if hp > 4 and no_water_days == 0:
        reserve_floor = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve_floor = DAILY_SALARY * 0.6

    max_affordable = max(0.0, budget - reserve_floor)
    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    aggressive = 0
    desperate_opp = 0
    rich_opp = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if b >= 100:
                    aggressive += 1

    if not alive:
        return float(min(budget, 8.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / WATER_REQ
    scarce = units < 2.0
    very_scarce = units < 1.5

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1

    if day >= 8:
        danger += 1

    reserve_floor = max(0.0, (10 - day) * 8.0)
    spendable = max(0.0, budget - reserve_floor)

    if danger >= 4:
        bid = max(110.0, highest_prev + 3.0, DAILY_SALARY * 1.45)
    elif very_scarce:
        bid = max(95.0, highest_prev + 2.0, avg_prev + 8.0)
    elif scarce:
        bid = max(62.0, avg_prev + 3.0)
        if aggressive >= 2 or rich_opp >= 2:
            bid = max(bid, highest_prev + 1.5)
    else:
        bid = 18.0
        if desperate_opp >= 2:
            bid = 28.0
        if highest_prev >= 120:
            bid = min(bid, 16.0)

    if hp >= 8 and no_water_days == 0 and not scarce and highest_prev >= 100:
        bid = min(bid, 12.0)

    if spendable > 0:
        bid = min(bid, max(12.0, spendable))
    bid = min(bid, budget)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 130.0))

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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev['bid']
                prev_bids.append(b)
                if opp.get('budget', 0) >= max(10, b * 0.6):
                    dangerous_prev.append(b)

    if not alive:
        return max(0, min(budget, 18.0 if hp > 3 else 40.0))

    slots = supply / float(WATER_REQ)
    scarce = slots < 1.6
    medium = slots < 2.0

    strongest_prev = max(dangerous_prev) if dangerous_prev else (max(prev_bids) if prev_bids else 0.0)
    active_count = len(alive)

    emergency = hp <= 2 or no_water >= 2
    stressed = hp <= 4 or no_water >= 1

    if emergency:
        bid = max(58.0, strongest_prev + 4.0)
        if scarce:
            bid = max(bid, 82.0)
        return max(0, min(budget, bid))

    if scarce:
        if strongest_prev >= 110:
            bid = 42.0 if hp >= 6 and no_water == 0 else 88.0
        elif strongest_prev >= 70:
            bid = strongest_prev + 3.0
        else:
            bid = 74.0 if active_count >= 2 else 61.0
        if stressed:
            bid = max(bid, 79.0)
        return max(0, min(budget, bid))

    if medium:
        if strongest_prev >= 120:
            bid = 28.0 if hp >= 7 and no_water == 0 else 67.0
        elif strongest_prev >= 90:
            bid = 54.0
        elif strongest_prev >= 50:
            bid = strongest_prev + 2.0
        else:
            bid = 45.0
        if stressed:
            bid = max(bid, 58.0)
        return max(0, min(budget, bid))

    if strongest_prev >= 120:
        bid = 16.0
    elif strongest_prev >= 80:
        bid = 24.0
    elif strongest_prev >= 40:
        bid = 33.0
    else:
        bid = 29.0

    if stressed:
        bid = max(bid, 46.0)

    if budget < 35:
        bid = min(bid, budget)

    return max(0, min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    threat_bids = []
    rich_threat = 0.0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > DAILY_SALARY * 1.5:
                threat_bids.append(float(bid))
        if opp.get('budget', 0) > rich_threat:
            rich_threat = float(opp.get('budget', 0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    high_threat_prev = max(threat_bids) if threat_bids else high_prev

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2 or no_water_days >= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency >= 3:
        target = max(98.0, high_threat_prev + 3.0)
        if scarcity >= 1:
            target = max(target, 118.0)
        return float(min(budget, target))

    if scarcity >= 2:
        if high_threat_prev >= 130:
            target = high_threat_prev + 2.0
        else:
            target = 110.0 + 8.0 * urgency
        return float(min(budget, target))

    if scarcity == 1:
        if high_threat_prev >= 130:
            if hp >= 7 and no_water_days == 0 and budget < rich_threat:
                return float(min(budget, 32.0))
            target = 96.0 + 8.0 * urgency
            return float(min(budget, target))
        target = max(55.0, high_threat_prev + 2.0)
        return float(min(budget, target))

    if high_threat_prev >= 130:
        if hp >= 7 and no_water_days == 0:
            return float(min(budget, 24.0))
        return float(min(budget, 88.0))

    if high_prev > 0:
        target = max(38.0, high_prev * 0.72 + 2.0 * urgency)
        return float(min(budget, target))

    base = 30.0
    if day >= 8:
        base = 42.0
    if urgency >= 1:
        base += 18.0
    return float(min(budget, base))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        base = DAILY_SALARY * 0.28
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    prev_bids_survivors = []
    opp_pressure = 0.0
    rich_alive = 0
    desperate_alive = 0

    for opp in alive:
        if opp.get('budget', 0) >= 90:
            rich_alive += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_alive += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
                prev_bids_survivors.append(float(bid))
                if float(bid) > opp_pressure:
                    opp_pressure = float(bid)

    if prev_bids_survivors:
        ref_bid = max(prev_bids_survivors)
    elif prev_bids:
        ref_bid = max(prev_bids)
    else:
        ref_bid = DAILY_SALARY * 0.55

    scarcity = 1.0 - ((supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY))
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    urgent = False
    if hp <= 2 or no_water >= 2:
        urgent = True
    elif hp <= 4 and no_water >= 1:
        urgent = True

    if urgent:
        target = max(DAILY_SALARY * 0.92, ref_bid + 2.5)
        target += 8.0 * scarcity
    else:
        if supply >= 22:
            target = max(DAILY_SALARY * 0.34, ref_bid * 0.72)
        elif supply >= 19:
            target = max(DAILY_SALARY * 0.46, ref_bid * 0.84)
        else:
            target = max(DAILY_SALARY * 0.58, ref_bid + 1.2)

        if ref_bid >= 110:
            target = min(target, DAILY_SALARY * 0.62)
        elif ref_bid >= 95 and hp > 4 and no_water == 0:
            target = min(target, DAILY_SALARY * 0.68)

        target += rich_alive * 1.0 + desperate_alive * 1.5
        target += 5.0 * scarcity

    days_left = max(0, 10 - day)
    reserve_floor = 0.0
    if days_left > 0:
        reserve_floor = days_left * DAILY_SALARY * 0.22

    affordable = budget
    if not urgent and budget > reserve_floor:
        affordable = max(0.0, budget - reserve_floor * 0.15)

    bid = min(target, affordable)

    if urgent and bid < DAILY_SALARY * 0.75:
        bid = min(budget, DAILY_SALARY * 0.75)

    if hp >= 7 and no_water == 0 and supply >= 23 and ref_bid >= 100:
        bid = min(bid, DAILY_SALARY * 0.4)

    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    opp_bids = []
    cindy_bid = None
    urgent_opp_count = 0
    rich_opp_count = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opp_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            opp_bids.append(float(bid))
            if oid == 'Cindy':
                cindy_bid = float(bid)

    highest_prev = max(opp_bids) if opp_bids else 0.0
    moderate_prev = 0.0
    if opp_bids:
        sorted_bids = sorted(opp_bids)
        idx = int(len(sorted_bids) * 0.5)
        if idx >= len(sorted_bids):
            idx = int(len(sorted_bids) - 1)
        moderate_prev = float(sorted_bids[int(idx)])

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

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
        danger += 1

    if danger >= 5:
        base = DAILY_SALARY * (0.95 + 0.20 * scarcity)
    elif danger >= 3:
        base = DAILY_SALARY * (0.72 + 0.18 * scarcity)
    elif danger >= 1:
        base = DAILY_SALARY * (0.52 + 0.16 * scarcity)
    else:
        base = DAILY_SALARY * (0.30 + 0.12 * scarcity)

    if cindy_bid is not None:
        if cindy_bid >= 120:
            if danger <= 1 and supply >= 20:
                base = min(base, DAILY_SALARY * 0.28)
            elif danger >= 3:
                base = max(base, DAILY_SALARY * 0.82)
        elif cindy_bid >= 80:
            base = max(base, min(cindy_bid + 2.0, DAILY_SALARY * 0.92))
        else:
            base = max(base, cindy_bid + 1.5)
    elif highest_prev > 0:
        if highest_prev >= DAILY_SALARY * 0.9:
            if danger <= 1:
                base = min(base, DAILY_SALARY * 0.30)
            else:
                base = max(base, DAILY_SALARY * 0.85)
        else:
            target = max(moderate_prev + 1.5, DAILY_SALARY * (0.45 + 0.10 * scarcity))
            base = max(base, target)

    if urgent_opp_count >= 2 and supply <= 18:
        base = max(base, DAILY_SALARY * 0.88)
    elif urgent_opp_count == 0 and rich_opp_count <= 1 and supply >= 22 and danger == 0:
        base = min(base, DAILY_SALARY * 0.26)

    if day >= 8:
        base *= 1.08
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        base = max(base, DAILY_SALARY * 0.9)

    reserve_floor = 0.0
    days_left = 10 - day
    if days_left > 1 and danger == 0:
        reserve_floor = DAILY_SALARY * 0.15
    affordable = max(0.0, budget - reserve_floor)
    bid = min(base, affordable if affordable > 0 else budget)

    if danger >= 5:
        bid = min(max(bid, DAILY_SALARY * 0.92), budget)

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, 20.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    prev_bids = []
    low_competitor_bids = []
    urgent_opp_count = 0
    rich_urgent_count = 0
    max_prev_bid = 0.0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = None
        if prev and prev.get('bid') is not None:
            pbid = prev.get('bid')
            prev_bids.append(float(pbid))
            if pbid > max_prev_bid:
                max_prev_bid = float(pbid)
        if pbid is not None and pbid <= 80:
            low_competitor_bids.append(float(pbid))

        opp_hp = opp.get('hp', 10)
        opp_nw = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0)
        if opp_hp <= 4 or opp_nw >= 1:
            urgent_opp_count += 1
            if opp_budget >= 70:
                rich_urgent_count += 1

    # Baseline: beat David-like cheap bidder, ignore Cindy/Eric burn unless we are in danger.
    if low_competitor_bids:
        target = max(low_competitor_bids) + 2.1
    else:
        target = 33.0

    # Supply pressure adjustment.
    if slots == 1:
        target += 4.0
    else:
        target -= 6.0

    # If yesterday showed only extreme bids, avoid matching unless necessary.
    if prev_bids and min(prev_bids) >= 120:
        target = min(target, 38.0)

    # Endurance / survival logic.
    if hp <= 2 or no_water >= 2:
        target = max(target, 95.0)
    elif hp <= 4 or no_water >= 1:
        target = max(target, 58.0)

    # Opponent urgency can create temporary spikes.
    if rich_urgent_count >= 2 and slots == 1:
        target = max(target, 72.0)
    elif urgent_opp_count >= 2:
        target = max(target, 48.0)

    # Late-game: secure survival more aggressively if healthy budget remains.
    if day >= 8 and hp <= 5:
        target = max(target, 78.0)

    # Budget discipline.
    if budget < 60:
        target = min(target, budget)
    elif budget < 120:
        target = min(target, 0.75 * budget)
    else:
        target = min(target, 110.0)

    # Never overspend when healthy and competition looked irrationally high.
    if hp >= 7 and no_water == 0 and max_prev_bid >= 150:
        target = min(target, 42.0)

    if target < 0:
        target = 0.0
    if target > budget:
        target = budget

    return float(round(target, 2))
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
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    cindy = opponents_status.get('Cindy')
    cindy_prev_bid = None
    cindy_urgent = False
    if cindy and cindy.get('alive'):
        prev = cindy.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            cindy_prev_bid = float(prev['bid'])
        cindy_urgent = (cindy.get('hp', 10) <= 3) or (cindy.get('no_water_days', 0) >= 1)

    threatening_bids = []
    urgent_count = 0
    for agent_id, opp in alive:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            threatening_bids.append(float(prev['bid']))

    highest_prev = max(threatening_bids) if threatening_bids else 0.0

    scarcity = (supply <= 17)
    comfortable_supply = (supply >= 22)
    my_urgent = (hp <= 3) or (no_water_days >= 1)
    critical = (hp <= 2) or (no_water_days >= 2)

    if critical:
        base = DAILY_SALARY * 0.96
    elif my_urgent:
        base = DAILY_SALARY * 0.82
    elif scarcity:
        base = DAILY_SALARY * 0.58
    elif comfortable_supply:
        base = DAILY_SALARY * 0.34
    else:
        base = DAILY_SALARY * 0.45

    if cindy_prev_bid is not None:
        if cindy_prev_bid >= 110:
            if not my_urgent:
                base = min(base, DAILY_SALARY * 0.38)
            else:
                base = max(base, DAILY_SALARY * 0.88)
        elif cindy_prev_bid >= 85:
            if scarcity or my_urgent:
                base = max(base, DAILY_SALARY * 0.72)
            else:
                base = min(max(base, cindy_prev_bid * 0.62), DAILY_SALARY * 0.6)
        else:
            base = max(base, min(DAILY_SALARY * 0.68, cindy_prev_bid + 3.0))

    if cindy_urgent and scarcity:
        base = max(base, DAILY_SALARY * 0.78)

    if urgent_count >= 2 and not comfortable_supply:
        base = max(base, DAILY_SALARY * 0.7)

    if day >= 8 and hp >= 6 and budget > DAILY_SALARY * 4:
        base = min(base, DAILY_SALARY * 0.42)

    if day >= 8 and my_urgent:
        base = max(base, DAILY_SALARY * 0.9)

    if budget < DAILY_SALARY * 1.2 and not critical:
        base = min(base, budget * 0.72)

    bid = min(budget, max(0.0, base))
    return float(round(bid, 2))
"""
