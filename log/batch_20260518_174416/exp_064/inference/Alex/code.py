# ============================================================
# Experiment: exp_064
# Agent: Alex
# Source: exp_064
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
    prev_bids = []
    desperate_count = 0
    strong_prev = 0.0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid > strong_prev:
                    strong_prev = bid

    players = 1 + len(alive)
    supply_units = float(supply) / float(WATER_REQ)
    scarcity = supply_units < players
    severe_scarcity = supply_units < max(1, players - 1)

    if budget <= 0:
        return 0

    if not alive:
        if hp <= 2 or no_water >= 1:
            return min(budget, 50)
        return min(budget, 24)

    if hp <= 1 or no_water >= 2:
        target = max(63.0, strong_prev + 3.0)
        return min(budget, target)

    if hp <= 2 or no_water >= 1:
        if severe_scarcity:
            target = max(58.0, strong_prev + 2.0)
        else:
            target = max(46.0, strong_prev + 1.0)
        return min(budget, target)

    if severe_scarcity:
        if prev_bids:
            target = max(40.0, strong_prev + 1.5)
        else:
            target = 39.0
        if desperate_count >= 2:
            target += 4.0
        return min(budget, target)

    if scarcity:
        if prev_bids:
            target = max(31.0, strong_prev + 1.0)
        else:
            target = 30.0
        if desperate_count >= 2:
            target += 3.0
        return min(budget, target)

    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = max(18.0, min(28.0, avg_prev * 0.75))
    else:
        target = 21.0

    return min(budget, target)
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= 120:
            rich_opp += 1
        if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0)))
            except:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    emergency = False
    if hp <= 3 or no_water >= 2:
        emergency = True
    elif hp <= 5 and scarcity >= 1:
        emergency = True

    if emergency:
        bid = max(62.0, highest_prev + 2.0)
        if scarcity == 2:
            bid = max(bid, 88.0)
        elif scarcity == 1:
            bid = max(bid, 74.0)
        return float(min(budget, bid))

    if scarcity == 2:
        if highest_prev >= 120:
            bid = 54.0 if hp >= 7 else 82.0
        elif highest_prev >= 80:
            bid = max(58.0, highest_prev + 1.5)
        else:
            bid = 61.0 + 4.0 * urgent_opp
        if rich_opp >= 2 and hp >= 7:
            bid = min(bid, 60.0)
        return float(min(budget, bid))

    if scarcity == 1:
        if highest_prev >= 130:
            bid = 34.0 if hp >= 8 else 72.0
        elif highest_prev >= 90:
            bid = 48.0 if hp >= 7 else 68.0
        elif highest_prev > 0:
            bid = max(44.0, avg_prev * 0.72)
        else:
            bid = 42.0
        return float(min(budget, bid))

    if highest_prev >= 130 and hp >= 7:
        bid = 20.0
    elif highest_prev >= 100 and hp >= 8:
        bid = 24.0
    elif highest_prev >= 70:
        bid = 31.0
    else:
        bid = 28.0 + min(day, 4) * 1.5

    if hp <= 6:
        bid += 10.0
    if no_water >= 1:
        bid += 8.0

    return float(min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 100:
                    strong_prev.append(float(bid))

    alive_count = len(alive)
    if alive_count == 0:
        return float(min(budget, 18.0))

    guaranteed_slots = int(supply // WATER_REQ)
    scarcity = guaranteed_slots < alive_count

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    emergency = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        target = max(130.0, highest_prev + 8.0)
    elif emergency:
        target = max(105.0, highest_prev + 4.0)
    else:
        if scarcity:
            if highest_prev >= 170:
                target = 118.0 if hp >= 6 else 145.0
            elif highest_prev >= 120:
                target = highest_prev + 3.0
            elif highest_prev > 0:
                target = max(88.0, avg_prev + 6.0)
            else:
                target = 82.0
        else:
            if hp >= 7 and no_water_days == 0:
                target = 28.0
            else:
                target = 52.0

    if day >= 8:
        target += 8.0
    if budget < 140:
        target = min(target, budget * 0.72)
    elif budget < 220:
        target = min(target, budget * 0.82)
    else:
        target = min(target, budget * 0.9)

    floor_bid = 0.0
    if emergency:
        floor_bid = 60.0
    elif scarcity:
        floor_bid = 40.0
    else:
        floor_bid = 18.0

    bid = max(floor_bid, target)
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
    rich_aggressive = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= 120 and opp.get('budget', 0) >= 120:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 5.0))

    high_pressure = max(prev_bids) if prev_bids else 0.0
    avg_pressure = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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

    if supply >= 23 and urgency < 1.0:
        base = 1.0
    elif supply >= 20 and urgency < 0.8:
        base = 4.0
    elif supply >= 18:
        base = 8.0 + 8.0 * urgency
    else:
        base = 18.0 + 18.0 * urgency

    if high_pressure >= 150:
        if urgency < 0.9:
            bid = base
        else:
            bid = max(base, 0.78 * DAILY_SALARY + 8.0 * scarcity)
    elif high_pressure >= 100:
        if urgency < 0.7 and supply >= 19:
            bid = base
        else:
            bid = max(base, min(high_pressure * 0.72, 62.0 + 10.0 * urgency))
    elif high_pressure > 0:
        target = high_pressure + 2.5
        bid = max(base, min(target, 58.0 + 8.0 * urgency))
    else:
        bid = base + 6.0 * scarcity

    if rich_aggressive >= 2 and urgency < 1.0 and supply >= 19:
        bid = min(bid, 6.0)

    if desperate_count >= 2 and supply <= 18:
        bid = max(bid, 42.0 + 10.0 * urgency)

    if day >= 8:
        bid += 6.0 * urgency + 4.0 * scarcity

    reserve_floor = 0.0
    if hp > 4 and no_water_days == 0:
        reserve_floor = budget * 0.18
    max_spend = budget - reserve_floor
    if max_spend < 0:
        max_spend = budget

    bid = min(bid, max_spend)

    if urgency >= 1.5:
        bid = max(bid, min(budget, 68.0))
    elif urgency >= 1.0:
        bid = max(bid, min(budget, 52.0 + 10.0 * scarcity))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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
    high_threat = 0
    medium_threat = 0
    desperate_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 100:
                    high_threat += 1
                elif bid >= 70:
                    medium_threat += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        top_prev = 0.0
        avg_prev = 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if no_water_days >= 2 or hp <= 3:
        urgency = 3
    elif no_water_days >= 1 or hp <= 5:
        urgency = 2
    elif hp <= 7:
        urgency = 1

    if urgency == 3:
        bid = max(92.0, top_prev + 2.0)
        if scarcity == 2:
            bid = max(bid, 108.0)
        elif scarcity == 1:
            bid = max(bid, 98.0)
    elif urgency == 2:
        if top_prev >= 105:
            bid = 96.0 if scarcity >= 1 else 82.0
        elif top_prev >= 85:
            bid = min(95.0, top_prev + 1.5)
        else:
            bid = 72.0 if scarcity >= 1 else 58.0
    elif urgency == 1:
        if scarcity == 2 and desperate_count >= 1:
            bid = 66.0
        elif top_prev >= 100:
            bid = 28.0
        elif top_prev >= 80:
            bid = 44.0
        else:
            bid = 36.0
    else:
        if scarcity == 2 and desperate_count >= 2:
            bid = 30.0
        elif top_prev >= 100:
            bid = 12.0
        elif avg_prev >= 70:
            bid = 18.0
        else:
            bid = 24.0

    remaining_days = max(0, 10 - day)
    reserve = remaining_days * 22.0
    if urgency <= 1 and budget < reserve:
        bid = min(bid, 20.0)
    elif urgency == 2 and budget < reserve:
        bid = min(bid, 72.0)

    if day >= 8:
        if urgency >= 2:
            bid += 8.0
        elif hp <= 6:
            bid += 4.0

    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    winners_est = int(supply / WATER_REQ)
    if winners_est < 1:
        winners_est = 1

    prev_bids = []
    prev_max = 0.0
    prev_min = None
    urgent_opp = 0
    rich_opp = 0

    for opp in alive_opponents:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= budget:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid > prev_max:
                    prev_max = bid
                if prev_min is None or bid < prev_min:
                    prev_min = bid

    if prev_min is None:
        prev_min = DAILY_SALARY * 0.5

    need_level = 0
    if hp <= 2 or no_water_days >= 2:
        need_level = 3
    elif hp <= 4 or no_water_days >= 1:
        need_level = 2
    elif hp <= 6:
        need_level = 1

    if not alive_opponents:
        if need_level >= 2:
            return min(budget, DAILY_SALARY * 0.55)
        return min(budget, DAILY_SALARY * 0.2)

    pressure = prev_max
    if urgent_opp >= 2:
        pressure += 6
    elif urgent_opp == 1:
        pressure += 3

    if winners_est >= 2:
        if need_level == 0:
            bid = max(18.0, prev_min * 0.72)
        elif need_level == 1:
            bid = max(32.0, prev_min * 0.9)
        elif need_level == 2:
            bid = max(52.0, min(pressure * 0.82, DAILY_SALARY * 0.95))
        else:
            bid = max(68.0, min(pressure + 2.0, budget))
    else:
        if need_level == 0:
            bid = max(24.0, min(prev_min * 0.85, DAILY_SALARY * 0.55))
        elif need_level == 1:
            bid = max(45.0, min(pressure * 0.72, DAILY_SALARY * 0.85))
        elif need_level == 2:
            bid = max(65.0, min(pressure * 0.9 + 2.0, budget))
        else:
            bid = max(78.0, min(pressure + 4.0, budget))

    if day >= 8 and budget > DAILY_SALARY * 2:
        bid += 4.0
    if rich_opp >= 2 and need_level >= 2:
        bid += 3.0
    if hp >= 8 and no_water_days == 0 and winners_est >= 2:
        bid *= 0.9

    max_safe = budget
    if need_level == 0:
        max_safe = min(max_safe, budget * 0.45)
    elif need_level == 1:
        max_safe = min(max_safe, budget * 0.6)
    elif need_level == 2:
        max_safe = min(max_safe, budget * 0.8)

    bid = min(bid, max_safe)
    if need_level >= 2:
        bid = max(bid, 50.0)
    elif need_level == 1:
        bid = max(bid, 28.0)
    else:
        bid = max(bid, 12.0)

    if bid > budget:
        bid = budget
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
    opp_pressures = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                pressure = float(bid)
                if opp.get('budget', 0) < pressure:
                    pressure = float(opp.get('budget', 0))
                opp_pressures.append(pressure)

    if not alive:
        return float(min(budget, 8.0))

    expected_units = max(1, int(supply // WATER_REQ))
    alive_count = len(alive)
    scarcity = alive_count > expected_units

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
    effective_high = max(opp_pressures) if opp_pressures else highest_prev

    low_supply = supply <= 17
    high_supply = supply >= 23

    danger = 0
    if hp <= 4:
        danger += 2
    elif hp <= 7:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1
    if scarcity:
        danger += 1
    if low_supply:
        danger += 1

    base = 0.0

    if danger >= 5:
        base = max(62.0, effective_high + 6.0)
    elif danger >= 3:
        if effective_high >= 140:
            base = 58.0
        else:
            base = max(46.0, effective_high + 3.0)
    else:
        if high_supply and effective_high >= 150:
            base = 18.0
        elif effective_high >= 180:
            base = 22.0
        elif effective_high >= 120:
            base = 28.0
        elif scarcity:
            base = max(34.0, second_prev + 2.0)
        else:
            base = max(20.0, min(36.0, highest_prev * 0.55))

    rich_threats = 0
    weak_threats = 0
    for opp in alive:
        ob = float(opp.get('budget', 0))
        ohp = float(opp.get('hp', 0))
        onw = float(opp.get('no_water_days', 0))
        prev = opp.get('previous_trace', {})
        pbid = prev.get('bid') if prev else None
        if ob >= 140 and ohp >= 6:
            rich_threats += 1
        if onw >= 1 or ohp <= 4:
            weak_threats += 1
        if pbid is not None and float(pbid) <= 35 and scarcity:
            base = max(base, float(pbid) + 2.5)

    if rich_threats >= 2 and danger <= 2:
        base *= 0.9
    if weak_threats >= 2 and danger >= 3:
        base += 4.0

    if day >= 8:
        base *= 1.08
    if day == 10:
        base *= 1.12

    reserve_floor = 10.0 if hp > 5 else 0.0
    cap = max(0.0, budget - reserve_floor)
    if danger >= 5:
        cap = budget

    bid = min(base, cap)
    if bid < 0:
        bid = 0.0
    if budget < 12:
        bid = budget

    return float(round(min(budget, bid), 2))
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return max(0.0, min(budget, 18.0))

    serious = []
    for agent_id, opp in alive:
        if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
            serious.append((agent_id, opp))

    if not serious:
        return max(0.0, min(budget, 12.0))

    highest_prev = 0.0
    eric_prev = None
    rich_threat = 0.0
    for agent_id, opp in serious:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            if bid > highest_prev:
                highest_prev = bid
            if agent_id == 'Eric':
                eric_prev = bid
        if opp.get('budget', 0) > rich_threat:
            rich_threat = opp.get('budget', 0)

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    serious_count = len(serious)
    contested = slots < (serious_count + 1)
    base_ref = highest_prev
    if eric_prev is not None:
        base_ref = max(base_ref, eric_prev)

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

    if contested:
        urgency += 2
    if slots <= 1:
        urgency += 1

    if budget < DAILY_SALARY * 0.8:
        urgency -= 1

    if urgency <= 1:
        bid = 16.0 if slots >= 2 else 28.0
        if base_ref > 0:
            bid = max(bid, min(base_ref * 0.22, 32.0))
    elif urgency == 2:
        bid = 34.0
        if base_ref > 0:
            bid = max(bid, min(base_ref * 0.38, 58.0))
    elif urgency == 3:
        bid = 58.0
        if base_ref > 0:
            bid = max(bid, min(base_ref * 0.55, 88.0))
    elif urgency == 4:
        bid = 82.0
        if base_ref > 0:
            bid = max(bid, min(base_ref * 0.72 + 2.0, 118.0))
    else:
        target = 96.0
        if base_ref > 0:
            target = max(target, min(base_ref + 3.0, 145.0))
        bid = target

    if eric_prev is not None and contested and urgency >= 4:
        bid = max(bid, min(eric_prev + 4.0, 150.0))

    if slots >= serious_count + 1 and urgency <= 3:
        bid = min(bid, 24.0)

    if day >= 8 and hp > 5 and no_water == 0 and contested:
        bid = min(bid, 52.0)

    if hp <= 1 or no_water >= 2:
        bid = max(bid, 105.0)

    if budget <= 0:
        return 0.0

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
    pressure_scores = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            opp_req = opp.get('water_requirement', WATER_REQ)
            opp_budget = opp.get('budget', 0)
            opp_hp = opp.get('hp', 0)
            opp_nowater = opp.get('no_water_days', 0)
            urgency = 0.0
            if opp_hp <= 3:
                urgency += 20.0
            elif opp_hp <= 5:
                urgency += 10.0
            urgency += min(opp_nowater, 3) * 6.0
            urgency += min(opp_budget / max(1.0, opp.get('daily_salary', DAILY_SALARY)), 3.0) * 4.0
            urgency += max(0.0, opp_req - WATER_REQ) * 0.5
            if bid is not None:
                urgency += min(float(bid), 120.0) * 0.35
            pressure_scores.append(urgency)

    if not alive_opps:
        return float(min(budget, 18.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    opp_pressure = max(pressure_scores) if pressure_scores else 0.0

    my_urgency = 0.0
    if hp <= 2:
        my_urgency += 55.0
    elif hp <= 4:
        my_urgency += 32.0
    elif hp <= 6:
        my_urgency += 16.0
    my_urgency += min(no_water, 3) * 14.0
    if day >= 8:
        my_urgency += 8.0

    supply_tight = 0.0
    if supply <= 16:
        supply_tight = 22.0
    elif supply <= 18:
        supply_tight = 14.0
    elif supply <= 20:
        supply_tight = 8.0
    else:
        supply_tight = 2.0

    budget_ratio = budget / float(DAILY_SALARY)
    conserve = 0.0
    if budget_ratio < 1.2:
        conserve += 18.0
    elif budget_ratio < 2.0:
        conserve += 8.0

    if hp >= 8 and no_water == 0 and supply >= 22 and high_prev >= 110:
        bid = 8.0
    else:
        base = 24.0 + supply_tight + my_urgency - conserve
        if slots == 1:
            base += 18.0
        if high_prev > 0:
            if high_prev >= 125:
                base = min(base, 52.0) if my_urgency < 45 else max(base, 88.0)
            elif high_prev >= 95:
                base = max(base, avg_prev * 0.72)
            else:
                base = max(base, high_prev + 2.0)
        if opp_pressure >= 55 and my_urgency >= 35:
            base += 12.0
        elif opp_pressure >= 55 and my_urgency < 20:
            base -= 8.0
        bid = base

    if hp <= 2 or no_water >= 2:
        bid = max(bid, 92.0 if supply <= 20 else 78.0)
    elif hp <= 4 and supply <= 18:
        bid = max(bid, 74.0)

    max_affordable_push = budget
    if day < 9:
        reserve = max(0.0, (9 - day) * 8.0)
        max_affordable_push = max(0.0, budget - reserve)
        if max_affordable_push < 12.0:
            max_affordable_push = min(budget, 12.0)

    bid = min(bid, max_affordable_push)
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_count += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    severe_need = hp <= 3 or no_water >= 2
    urgent_need = hp <= 5 or no_water >= 1

    low_supply = supply <= 16
    high_supply = supply >= 22

    if severe_need:
        target = max(78.0, highest_prev + 4.0)
        if low_supply:
            target = max(target, 96.0)
        return float(min(budget, target))

    if urgent_need:
        if highest_prev >= 110:
            target = 72.0 if not low_supply else 88.0
        else:
            target = max(62.0, highest_prev + 2.0)
            if low_supply:
                target += 10.0
        return float(min(budget, target))

    if high_supply:
        if highest_prev >= 120:
            target = 16.0
        elif highest_prev >= 90:
            target = 24.0
        else:
            target = max(18.0, avg_prev * 0.28)
        return float(min(budget, target))

    if low_supply:
        if desperate_count >= 2 and highest_prev >= 100:
            target = 38.0
        else:
            target = max(44.0, highest_prev + 1.5)
            if rich_count >= 2:
                target += 6.0
        return float(min(budget, target))

    if highest_prev >= 130:
        target = 22.0
    elif highest_prev >= 100:
        target = 34.0
    elif highest_prev >= 70:
        target = highest_prev + 1.5
    else:
        target = max(28.0, avg_prev * 0.55 if avg_prev > 0 else 30.0)

    if day >= 8 and hp >= 7 and budget < 140:
        target *= 0.85

    return float(min(budget, target))
"""
