# ============================================================
# Experiment: exp_030
# Agent: Alex
# Source: exp_030
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 1.2:
                rich_count += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
    
    players = 1 + len(alive_opponents)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < players
    severe_scarcity = expected_units < max(1.0, players - 1)
    
    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return min(budget, DAILY_SALARY * 0.75)
        return min(budget, DAILY_SALARY * 0.28)
    
    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0
    
    if hp <= 2 or no_water >= 2:
        base = DAILY_SALARY * 0.96
    elif hp <= 4 or no_water >= 1:
        base = DAILY_SALARY * 0.82
    elif severe_scarcity:
        base = DAILY_SALARY * 0.72
    elif scarcity:
        base = DAILY_SALARY * 0.58
    else:
        base = DAILY_SALARY * 0.34
    
    if highest_prev > 0:
        if highest_prev >= DAILY_SALARY * 0.9:
            if hp > 4 and no_water == 0:
                base = min(base, DAILY_SALARY * 0.32)
            else:
                base = max(base, DAILY_SALARY * 0.93)
        elif scarcity or hp <= 4 or no_water >= 1:
            base = max(base, highest_prev + 1.5)
        else:
            base = max(base, avg_prev * 0.9)
    
    if desperate_count >= max(1, len(alive_opponents) // 2):
        base += 4.0
    if rich_count >= max(1, len(alive_opponents) // 2) and scarcity:
        base += 3.0
    
    if day >= 8:
        base += 4.0
    elif day <= 2 and hp >= 7 and no_water == 0 and not scarcity:
        base -= 4.0
    
    if budget < DAILY_SALARY * 0.8:
        base = min(base, budget)
    else:
        reserve_floor = DAILY_SALARY * 0.18
        if day < 9:
            base = min(base, max(reserve_floor, budget - reserve_floor))
    
    if hp > 5 and no_water == 0 and not scarcity and highest_prev < DAILY_SALARY * 0.6:
        base = min(base, DAILY_SALARY * 0.45)
    
    bid = max(0.0, min(float(budget), float(base)))
    return bid
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
    prev_bids = []
    opp_budgets = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return max(0, min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.8
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.8
    richest_opp = max(opp_budgets) if opp_budgets else 0

    units_today = int(supply // WATER_REQ)
    scarce = units_today <= 1
    high_supply = supply >= 24

    critical = hp <= 2 or no_water_days >= 2
    semi_critical = hp <= 4 or no_water_days >= 1

    if critical:
        target = highest_prev + 2.5
        if richest_opp < target:
            target = max(target, richest_opp + 1)
        return max(0, min(budget, target))

    if high_supply and semi_critical:
        target = max(DAILY_SALARY * 0.9, avg_prev + 1.5)
        return max(0, min(budget, target))

    if scarce:
        if hp >= 6 and no_water_days == 0:
            return max(0, min(budget, DAILY_SALARY * 0.08))
        if semi_critical:
            target = max(DAILY_SALARY * 0.88, highest_prev + 1.0)
            return max(0, min(budget, target))
        return max(0, min(budget, DAILY_SALARY * 0.12))

    if hp >= 7 and budget < DAILY_SALARY * 4:
        return max(0, min(budget, DAILY_SALARY * 0.18))

    if semi_critical:
        target = max(DAILY_SALARY * 0.72, avg_prev * 0.92)
        return max(0, min(budget, target))

    if day >= 8:
        return max(0, min(budget, DAILY_SALARY * 0.45))

    return max(0, min(budget, DAILY_SALARY * 0.2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
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
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 63.0))
        return float(min(budget, 28.0))

    opp_bids = []
    cindy_bid = None
    eric_bid = None
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            opp_bids.append(float(bid))
        req = opp.get('water_requirement')
        sal = opp.get('daily_salary')
        if req == 13 and sal == 70:
            if bid is not None and bid >= 100:
                cindy_bid = float(bid)
            elif bid is not None and bid <= 60:
                eric_bid = float(bid)

    highest_prev = max(opp_bids) if opp_bids else 0.0
    moderate_prev = 50.0
    if eric_bid is not None:
        moderate_prev = eric_bid
    elif opp_bids:
        low_bids = [b for b in opp_bids if b <= 80]
        if low_bids:
            moderate_prev = max(low_bids)

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if urgent:
        if cindy_bid is not None and cindy_bid > 120 and budget < cindy_bid:
            bid = min(budget, max(58.0, moderate_prev + 3.0))
        else:
            target = max(64.0, moderate_prev + 4.0)
            if tight_supply:
                target = max(target, 72.0)
            bid = min(budget, target)
        return float(max(0.0, bid))

    if tight_supply:
        if highest_prev >= 120:
            bid = max(52.0, moderate_prev + 2.0)
        else:
            bid = max(54.0, moderate_prev + 3.0)
        if pressured:
            bid += 6.0
        return float(min(budget, bid))

    if medium_supply:
        if pressured:
            bid = max(48.0, moderate_prev + 2.0)
        else:
            bid = 41.0 if highest_prev >= 120 else 45.0
        return float(min(budget, bid))

    if pressured:
        bid = max(36.0, moderate_prev * 0.75)
    else:
        bid = 24.0 if highest_prev >= 120 else 30.0

    return float(min(budget, bid))
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
    prev_bids = []
    fixed_135_count = 0
    aggressive_count = 0
    rich_alive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 135:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if abs(bid - 135.0) < 1e-9:
                    fixed_135_count += 1
                if bid >= 110:
                    aggressive_count += 1

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return max(0, min(budget, 40.0))
        return max(0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    emergency = hp <= 2 or no_water_days >= 2
    danger = hp <= 4 or no_water_days >= 1
    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if emergency:
        target = max(110.0, highest_prev + 2.5)
        if fixed_135_count > 0 and budget >= 136:
            target = max(target, 136.0)
        return max(0, min(budget, target))

    if tight_supply:
        if danger:
            target = max(95.0, highest_prev + 2.0)
            if fixed_135_count > 0 and budget >= 136 and hp <= 3:
                target = max(target, 136.0)
            return max(0, min(budget, target))
        lowball = 8.0 + 2.0 * no_water_days
        if aggressive_count >= 2:
            lowball = 5.0
        return max(0, min(budget, lowball))

    if ample_supply:
        if highest_prev >= 130 and hp >= 5:
            return max(0, min(budget, 42.0))
        target = max(48.0, min(88.0, avg_prev + 3.0))
        if day >= 8:
            target += 8.0
        return max(0, min(budget, target))

    target = 0.0
    if highest_prev >= 130:
        if hp >= 6 and no_water_days == 0:
            target = 38.0
        else:
            target = 96.0
    elif highest_prev >= 110:
        target = highest_prev + 2.0
    elif highest_prev > 0:
        target = max(52.0, highest_prev + 1.5)
    else:
        target = 50.0

    if rich_alive >= 2 and hp >= 5 and no_water_days == 0 and target > 90:
        target = 72.0

    if day >= 9 and hp <= 5:
        target = max(target, 92.0)

    return max(0, min(budget, target))
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

    supply = day_context['supply']
    day = day_context['day']
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
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opp_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        bid = max(DAILY_SALARY * 0.95, highest_prev_bid + 2.5)
    elif my_urgent:
        bid = max(DAILY_SALARY * 0.82, highest_prev_bid + 1.5)
    else:
        if supply >= 23:
            bid = max(DAILY_SALARY * 0.32, avg_prev_bid * 0.55)
        elif supply >= 20:
            bid = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.72)
        elif supply >= 17:
            bid = max(DAILY_SALARY * 0.58, highest_prev_bid * 0.82)
        else:
            bid = max(DAILY_SALARY * 0.72, highest_prev_bid + 1.0)

    if rich_opp_count >= 2 and supply <= 18 and not my_urgent:
        bid = max(bid, highest_prev_bid + 1.0)

    if urgent_opp_count >= 2 and hp >= 5 and no_water_days == 0 and supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.42)

    if day >= 8 and hp >= 5 and no_water_days == 0:
        bid = min(bid, max(DAILY_SALARY * 0.38, avg_prev_bid * 0.7 if prev_bids else DAILY_SALARY * 0.38))

    bid = max(0.0, min(float(budget), float(bid)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_bid = 0.0
    rich_alive = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 1.2:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev['bid'])
                prev_bids.append(b)
                if b > dangerous_bid:
                    dangerous_bid = b

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    total_alive = 1 + len(alive_opponents)
    likely_units = supply / float(WATER_REQ)
    scarcity = likely_units < total_alive

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
    if day >= 8:
        urgency += 1

    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev = 0.0

    if scarcity:
        if urgency >= 5:
            target = max(90.0, dangerous_bid + 3.0, avg_prev + 8.0)
        elif urgency >= 3:
            target = max(58.0, min(95.0, avg_prev * 0.85 + 6.0))
            if dangerous_bid >= 120.0:
                target = min(target, 52.0)
        else:
            if dangerous_bid >= 100.0 or rich_alive >= 2:
                target = 16.0
            else:
                target = max(22.0, min(45.0, avg_prev * 0.55 + 4.0))
    else:
        if urgency >= 5:
            target = max(62.0, avg_prev + 2.0)
        elif urgency >= 3:
            target = max(38.0, min(62.0, avg_prev * 0.7 + 3.0))
        else:
            target = 20.0 if dangerous_bid >= 90.0 else 28.0

    if budget < DAILY_SALARY:
        target = min(target, budget * (0.72 if urgency < 4 else 0.92))
    else:
        reserve_days = max(0, 10 - day)
        soft_cap = budget / max(1, reserve_days)
        if urgency < 3:
            target = min(target, max(18.0, soft_cap * 0.9))
        elif urgency < 5:
            target = min(target, max(35.0, soft_cap * 1.2))

    target = max(0.0, min(float(budget), float(target)))
    return float(round(target, 2))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_aggressive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 100 or opp.get('budget', 0) >= 500:
                    rich_aggressive += 1

    if not alive:
        return float(min(budget, 18.0))

    units = int(float(supply) // WATER_REQ)
    scarcity = units <= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

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

    base = 0.0

    if scarcity:
        if urgency >= 5:
            base = max(118.0, highest_prev + 3.0)
        elif urgency >= 3:
            base = max(92.0, min(116.0, second_prev + 2.5))
        else:
            if highest_prev >= 120:
                base = 24.0
            elif highest_prev >= 90:
                base = 52.0
            else:
                base = max(48.0, highest_prev + 1.5)
    else:
        if urgency >= 5:
            base = max(82.0, second_prev + 2.0)
        elif urgency >= 3:
            base = max(58.0, min(88.0, highest_prev * 0.7))
        else:
            if rich_aggressive >= 2 and highest_prev >= 100:
                base = 18.0
            elif highest_prev >= 100:
                base = 28.0
            else:
                base = max(22.0, second_prev * 0.55)

    remaining_days = max(0, 10 - int(day) + 1)
    soft_cap = budget
    if remaining_days > 0:
        reserve_target = max(0.0, (remaining_days - 1) * 22.0)
        soft_cap = max(0.0, budget - reserve_target)
        if urgency >= 4:
            soft_cap = max(soft_cap, min(budget, 110.0))

    bid = min(budget, base)
    if soft_cap > 0:
        bid = min(bid, max(soft_cap, 16.0 if urgency <= 1 else 30.0))

    if urgency >= 5:
        bid = max(bid, min(budget, 95.0 if not scarcity else 120.0))
    elif urgency >= 3:
        bid = max(bid, min(budget, 60.0 if not scarcity else 90.0))

    if budget < 35:
        bid = min(bid, budget)
        if urgency <= 1:
            bid = min(bid, 20.0)

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.6
        return max(0.0, min(budget, base))

    prev_bids = []
    cindy_bid = None
    eric_bid = None
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp_id == 'Cindy':
                cindy_bid = float(bid)
            if opp_id == 'Eric':
                eric_bid = float(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17.0
    ample_supply = supply >= 22.0
    urgent = hp <= 2 or no_water >= 1
    very_urgent = hp <= 1 or no_water >= 2

    target = avg_prev + 2.0
    if eric_bid is not None:
        target = max(target, eric_bid + 2.0)
    if cindy_bid is not None and cindy_bid <= DAILY_SALARY * 1.6:
        target = max(target, cindy_bid + 1.0)

    if tight_supply:
        target += 6.0
    elif ample_supply:
        target -= 8.0

    if urgent:
        target = max(target, highest_prev + 3.0)
    if very_urgent:
        target = max(target, highest_prev + 8.0)

    if day >= 8 and hp >= 4 and not urgent:
        target -= 4.0

    reserve_days = 3 if hp >= 3 else 2
    spend_cap = budget - DAILY_SALARY * reserve_days
    if spend_cap < DAILY_SALARY * 0.25:
        spend_cap = DAILY_SALARY * 0.25
    spend_cap = min(spend_cap, budget)

    floor_bid = DAILY_SALARY * 0.22
    if urgent:
        floor_bid = DAILY_SALARY * 0.75
    elif tight_supply:
        floor_bid = DAILY_SALARY * 0.55

    bid = max(floor_bid, target)
    if highest_prev >= 100.0 and hp >= 4 and not tight_supply and not urgent:
        bid = min(bid, highest_prev - 8.0)

    if budget < DAILY_SALARY * 1.2 and not urgent:
        bid = min(bid, DAILY_SALARY * 0.45)

    bid = min(bid, spend_cap)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return float(min(budget, 20.0))

    prev_bids = []
    bob_bid = None
    cindy_bid = None
    urgent_opp = 0
    rich_opp = 0

    for agent_id, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0)
            prev_bids.append(bid)
            if agent_id == 'Bob':
                bob_bid = bid
            elif agent_id == 'Cindy':
                cindy_bid = bid

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    if bob_bid is not None:
        moderate_prev = bob_bid
    elif prev_bids:
        moderate_prev = sorted(prev_bids)[int(len(prev_bids) // 2)]

    if hp <= 2 or no_water_days >= 2:
        if cindy_bid is not None:
            target = min(DAILY_SALARY * 1.55, cindy_bid + 2.0)
        else:
            target = DAILY_SALARY * 1.1
        return float(min(budget, max(1.0, target)))

    if slots >= 2:
        if moderate_prev > 0:
            target = moderate_prev + 2.0
        else:
            target = DAILY_SALARY * 0.62
        if urgent_opp >= 2:
            target += 6.0
        if hp >= 8 and no_water_days == 0:
            target -= 3.0
        return float(min(budget, max(1.0, target)))

    if hp >= 8 and no_water_days == 0:
        if highest_prev >= DAILY_SALARY * 1.3:
            return float(min(budget, 8.0))
        return float(min(budget, 18.0))

    if hp >= 5:
        if bob_bid is not None:
            target = bob_bid + 1.5
        else:
            target = DAILY_SALARY * 0.78
        if cindy_bid is not None and cindy_bid > target + 35 and hp > 6:
            target = min(target, 45.0)
        return float(min(budget, max(1.0, target)))

    target = max(DAILY_SALARY * 0.92, moderate_prev + 3.0)
    if rich_opp >= 2:
        target += 5.0
    return float(min(budget, max(1.0, target)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, 35.0))
        return float(min(budget, 8.0))

    prev_bids = []
    cindy_bid = None
    strongest_prev = 0.0
    active_threats = 0
    for opp in alive:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            prev_bids.append(bid)
            if bid > strongest_prev:
                strongest_prev = bid
            if bid >= 20:
                active_threats += 1
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if bid is not None and opp.get('budget', 0) > 200 and opp.get('hp', 0) >= 5:
                if cindy_bid is None or bid > cindy_bid:
                    cindy_bid = bid

    scarce = supply <= 16
    medium_tight = supply <= 19
    emergency = hp <= 2 or no_water >= 2
    urgent = hp <= 4 or no_water >= 1

    base = 0.0

    if emergency:
        if cindy_bid is not None:
            base = min(budget, max(78.0, cindy_bid + 2.0))
        else:
            base = min(budget, max(65.0, strongest_prev + 2.0))
    elif urgent:
        if scarce:
            if cindy_bid is not None:
                base = min(budget, max(62.0, min(cindy_bid + 1.0, 95.0)))
            else:
                base = min(budget, max(52.0, strongest_prev + 1.5))
        elif medium_tight:
            base = min(budget, max(38.0, min(strongest_prev * 0.55 + 6.0, 72.0)))
        else:
            base = min(budget, 28.0)
    else:
        if scarce:
            if cindy_bid is not None and cindy_bid >= 100:
                base = min(budget, 24.0)
            else:
                base = min(budget, max(26.0, strongest_prev * 0.45 + 4.0))
        elif medium_tight:
            if active_threats >= 2:
                base = min(budget, 22.0)
            else:
                base = min(budget, 16.0)
        else:
            base = min(budget, 9.0)

    remaining_days = max(0, 10 - day)
    reserve_target = remaining_days * 10.0
    if budget - base < reserve_target and not urgent and not emergency:
        base = max(0.0, budget - reserve_target)

    if day >= 8 and hp >= 6 and no_water == 0 and not scarce:
        base = min(base, 12.0)

    return float(max(0.0, min(budget, round(base, 2))))
"""
