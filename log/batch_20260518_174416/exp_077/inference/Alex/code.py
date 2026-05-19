# ============================================================
# Experiment: exp_077
# Agent: Alex
# Source: exp_077
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.28
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return max(0, min(budget, base))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    pressure = 0.42 + 0.22 * scarcity

    if hp <= 2:
        pressure = max(pressure, 0.93)
    elif hp <= 4:
        pressure = max(pressure, 0.72)
    elif hp >= 8 and no_water_days == 0:
        pressure = min(pressure, 0.48)

    if no_water_days >= 2:
        pressure = max(pressure, 0.96)
    elif no_water_days == 1:
        pressure = max(pressure, 0.78)

    prev_bids = []
    desperate_count = 0
    failed_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
            status = prev.get('status')
            if status in ('thirsty', 'critical', 'failed', 'error'):
                desperate_count += 1
            if prev.get('error'):
                failed_count += 1
            if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 2:
                desperate_count += 1

    if prev_bids:
        top_prev = max(prev_bids)
        if top_prev >= DAILY_SALARY * 0.9:
            if hp > 4 and no_water_days == 0:
                pressure = min(pressure, 0.38)
            else:
                pressure = max(pressure, 0.9)
        elif top_prev >= DAILY_SALARY * 0.65:
            pressure = max(pressure, min(0.88, (top_prev + 2.0) / float(DAILY_SALARY)))
        else:
            pressure = max(pressure, 0.5)

    if desperate_count >= max(1, len(alive_opponents) // 2):
        pressure = max(pressure, 0.82)
    if failed_count >= 1 and hp >= 6 and no_water_days == 0:
        pressure = min(pressure, 0.46)

    if budget < DAILY_SALARY * 1.2:
        pressure = min(pressure, 0.72 if (hp > 2 and no_water_days == 0) else pressure)
    if budget < DAILY_SALARY * 0.7:
        pressure = min(pressure, 0.55 if hp > 3 else pressure)

    bid = DAILY_SALARY * pressure

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.93)

    if bid > budget:
        bid = budget
    if bid < 0:
        bid = 0
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
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    desperate_pressure = 0
    rich_aggressive = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_pressure += 1
        if opp.get('budget', 0) >= 900:
            rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22
    urgent = hp <= 2 or no_water_days >= 2
    semi_urgent = hp <= 4 or no_water_days >= 1

    if urgent:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
        if supply_tight:
            target = max(target, DAILY_SALARY * 1.1)
        return float(min(budget, target))

    if semi_urgent:
        if highest_prev >= 100:
            target = DAILY_SALARY * 0.88 if not supply_tight else DAILY_SALARY * 1.0
        else:
            target = max(DAILY_SALARY * 0.72, highest_prev + 1.5)
        return float(min(budget, target))

    if supply_loose and hp >= 6 and no_water_days == 0:
        return float(min(budget, DAILY_SALARY * 0.22))

    if highest_prev >= 115:
        target = DAILY_SALARY * 0.28
    elif highest_prev >= 95:
        target = DAILY_SALARY * 0.4
    elif highest_prev > 0:
        target = max(DAILY_SALARY * 0.5, min(highest_prev + 1.0, DAILY_SALARY * 0.82))
    else:
        target = DAILY_SALARY * 0.45

    if supply_tight:
        target += 10.0
    elif supply_loose:
        target -= 8.0

    if desperate_pressure >= 2:
        target += 6.0
    if rich_aggressive >= 2 and avg_prev >= 80:
        target -= 4.0

    if day >= 8 and hp >= 5:
        target -= 5.0

    target = max(0.0, target)
    return float(min(budget, target))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    danger_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    danger_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    high_pressure = max(prev_bids) if prev_bids else 0.0
    median_pressure = sorted(prev_bids)[int(len(prev_bids) / 2)] if prev_bids else 0.0
    urgent_pressure = max(danger_bids) if danger_bids else high_pressure

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    base = 34.0 - 10.0 * supply_ratio

    if hp <= 2 or no_water_days >= 2:
        target = max(urgent_pressure + 3.0, 92.0 - 8.0 * supply_ratio)
    elif hp <= 4 or no_water_days >= 1:
        target = max(median_pressure + 2.0, 68.0 - 8.0 * supply_ratio)
    else:
        if supply <= 17:
            target = max(base, median_pressure + 1.0)
        elif supply >= 22:
            target = min(base, 32.0)
        else:
            target = max(base, min(55.0, median_pressure * 0.72))

    rich_threats = 0
    for opp in alive:
        if opp.get('budget', 0) > budget and opp.get('hp', 0) >= hp:
            rich_threats += 1
    if rich_threats >= 2 and supply <= 18 and hp <= 4:
        target += 8.0

    if day >= 8:
        target += 6.0 if hp <= 4 else 2.0

    max_safe = budget
    if hp >= 7 and no_water_days == 0:
        max_safe = min(max_safe, budget * 0.22 + DAILY_SALARY * 0.35)
    elif hp >= 5:
        max_safe = min(max_safe, budget * 0.30 + DAILY_SALARY * 0.45)
    else:
        max_safe = min(max_safe, budget * 0.55 + DAILY_SALARY * 0.75)

    bid = min(target, max_safe)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 96.0))
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, min(budget, 72.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    weak_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                weak_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if bid >= 140:
                    aggressive_count += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = 1.0 - max(0.0, min(1.0, supply_ratio))

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

    urgency += scarcity * 0.6

    if highest_prev >= 170:
        pressure_bid = highest_prev * 0.78
    elif highest_prev >= 130:
        pressure_bid = highest_prev * 0.72
    elif highest_prev > 0:
        pressure_bid = max(55.0, highest_prev + 4.0)
    else:
        pressure_bid = 58.0 + 18.0 * scarcity

    base_bid = pressure_bid

    if aggressive_count >= 2 and urgency < 0.8:
        base_bid *= 0.72
    elif aggressive_count >= 1 and urgency < 0.5:
        base_bid *= 0.82

    if weak_opp_count >= 1 and urgency < 0.7:
        base_bid *= 0.92

    if supply >= 22:
        base_bid *= 0.78
    elif supply <= 17:
        base_bid *= 1.12

    if day >= 8 and hp >= 6:
        base_bid *= 0.9

    if urgency >= 1.6:
        bid = max(base_bid, highest_prev + 8.0 if highest_prev > 0 else 95.0)
    elif urgency >= 1.0:
        bid = max(base_bid, avg_prev + 6.0 if avg_prev > 0 else 78.0)
    else:
        bid = base_bid

    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0 and hp > 3:
        reserve_target = reserve_days * 22.0
        soft_cap = max(0.0, budget - reserve_target)
        if soft_cap < 18.0:
            soft_cap = min(budget, 18.0 + 6.0 * urgency)

    final_bid = min(budget, bid, max(soft_cap, 0.0) if urgency < 1.2 else budget)

    if hp <= 2 or no_water_days >= 2:
        final_bid = min(budget, max(final_bid, 96.0, highest_prev + 6.0 if highest_prev > 0 else 96.0))

    if final_bid < 0:
        final_bid = 0.0

    return float(round(final_bid, 2))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp_bids = []
    rich_pressure = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_opp_bids.append(float(bid))
                if opp.get('budget', 0) > budget * 0.9:
                    rich_pressure.append(float(bid))

    if not alive_opps:
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    tight = slots <= 1
    medium = slots == 2

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else highest_prev
    rich_prev = max(rich_pressure) if rich_pressure else highest_prev

    danger = hp <= 3 or no_water_days >= 1
    severe_danger = hp <= 2 or no_water_days >= 2

    if severe_danger:
        target = max(118.0, highest_prev + 2.5)
        if tight:
            target = max(target, rich_prev + 3.0, 126.0)
        return float(min(budget, target))

    if danger:
        if tight:
            target = max(112.0, urgent_prev + 2.0)
        else:
            target = max(88.0, highest_prev * 0.9)
        return float(min(budget, target))

    if tight:
        if highest_prev >= 150:
            target = 72.0
        else:
            target = max(111.5, highest_prev + 1.5)
        return float(min(budget, target))

    if medium:
        if day <= 3:
            target = 62.0
        elif highest_prev >= 120:
            target = 66.0
        else:
            target = max(58.0, highest_prev * 0.58)
        return float(min(budget, target))

    target = 34.0
    if hp >= 8 and budget > 220:
        target = 28.0
    if highest_prev > 130:
        target = 22.0
    return float(min(budget, target))
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

    alive_opponents = []
    urgent_prev_bids = []
    all_prev_bids = []
    rich_urgent = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                all_prev_bids.append(bid)
                opp_hp = opp.get('hp', 0)
                opp_nwd = opp.get('no_water_days', 0)
                if opp_hp <= 3 or opp_nwd >= 1:
                    urgent_prev_bids.append(bid)
                    if opp.get('budget', 0) > 200:
                        rich_urgent += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return min(budget, 5.0)

    highest_prev = max(all_prev_bids) if all_prev_bids else 0.0
    highest_urgent_prev = max(urgent_prev_bids) if urgent_prev_bids else highest_prev

    severe_need = hp <= 2 or no_water_days >= 2
    moderate_need = hp <= 4 or no_water_days >= 1
    abundant_supply = supply >= 22
    tight_supply = supply <= 17

    if severe_need:
        bid = max(62.0, highest_urgent_prev + 2.5)
        if rich_urgent >= 2:
            bid += 6.0
        if tight_supply:
            bid += 6.0
        return min(budget, bid)

    if moderate_need:
        if highest_urgent_prev >= 100:
            bid = 24.0 if abundant_supply else 46.0
        else:
            bid = max(18.0, highest_urgent_prev + 1.5)
        if tight_supply:
            bid += 6.0
        return min(budget, bid)

    if abundant_supply:
        bid = 4.0
    elif supply >= 19:
        bid = 7.0
    else:
        bid = 11.0

    if highest_prev < 20 and day >= 7:
        bid += 2.0

    return min(budget, bid)
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
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                desperate_count += 1
            if opp.get('budget', 0) >= 150:
                rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 8.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    high_supply = supply >= 24
    low_supply = supply <= 18
    critical_self = (no_water_days >= 2) or (hp <= 3)
    urgent_self = (no_water_days >= 1) or (hp <= 5)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    if prev_bids:
        sorted_bids = sorted(prev_bids, reverse=True)
        idx = int(min(len(sorted_bids) - 1, max(0, slots - 1)))
        moderate_prev = sorted_bids[int(idx)]

    base = 12.0
    if high_supply:
        base = 9.0
    elif low_supply:
        base = 28.0
    else:
        base = 18.0

    if desperate_count >= 2:
        base += 10.0
    elif desperate_count == 1:
        base += 5.0

    if rich_aggressive >= 2:
        base += 6.0

    if day >= 8:
        base += 6.0

    if critical_self:
        target = max(base + 25.0, moderate_prev + 3.0, 62.0)
    elif urgent_self:
        target = max(base + 10.0, moderate_prev + 2.0, 34.0)
    else:
        if high_supply and highest_prev >= 120:
            target = 7.0
        elif highest_prev >= 160:
            target = 10.0 if hp >= 6 else 58.0
        elif highest_prev >= 110:
            target = 14.0 if hp >= 6 else max(48.0, moderate_prev + 1.5)
        elif moderate_prev > 0:
            target = max(base, moderate_prev + 1.5)
        else:
            target = base

    if slots >= 2 and not urgent_self:
        target -= 4.0
    if slots == 1 and urgent_self:
        target += 8.0

    reserve = 0.0
    if day <= 7:
        reserve = 20.0
    elif day <= 9:
        reserve = 10.0

    cap = budget - reserve
    if critical_self:
        cap = budget
    elif urgent_self:
        cap = max(cap, budget * 0.75)

    if cap < 0:
        cap = budget

    bid = min(target, cap)

    if critical_self and bid < 55.0:
        bid = min(budget, 55.0)
    if urgent_self and bid < 30.0:
        bid = min(budget, 30.0)

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_pressure = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev['bid'])
                prev_bids.append(b)
                req = float(opp.get('water_requirement', WATER_REQ))
                sal = float(opp.get('daily_salary', DAILY_SALARY))
                urgency = 1.0
                if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                    urgency = 1.2
                opp_pressure = max(opp_pressure, b / max(1.0, sal) * urgency * (req / float(WATER_REQ)))

    if budget <= 0:
        return 0.0

    slots = supply / float(WATER_REQ)
    scarcity = 0
    if slots <= 1.05:
        scarcity = 3
    elif slots <= 1.6:
        scarcity = 2
    elif slots <= 2.1:
        scarcity = 1

    my_urgency = 0
    if hp <= 2 or no_water >= 2:
        my_urgency = 3
    elif hp <= 4 or no_water >= 1:
        my_urgency = 2
    elif hp <= 6:
        my_urgency = 1

    if not alive:
        base = DAILY_SALARY * 0.22
        if my_urgency >= 2:
            base = DAILY_SALARY * 0.55
        return max(0.0, min(float(budget), float(base)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if scarcity == 0:
        bid = DAILY_SALARY * 0.18
        if my_urgency >= 2:
            bid = max(bid, DAILY_SALARY * 0.42)
        if highest_prev > 0 and my_urgency >= 1:
            bid = max(bid, min(highest_prev * 0.55, DAILY_SALARY * 0.7))
    elif scarcity == 1:
        bid = DAILY_SALARY * 0.38
        if highest_prev > 0:
            bid = max(bid, min(highest_prev + 2.0, DAILY_SALARY * 0.95))
        if my_urgency >= 2:
            bid = max(bid, DAILY_SALARY * 0.78)
    elif scarcity == 2:
        bid = DAILY_SALARY * 0.62
        if highest_prev > 0:
            bid = max(bid, min(highest_prev + 4.0, DAILY_SALARY * 1.2))
        if my_urgency >= 2:
            bid = max(bid, DAILY_SALARY * 0.95)
        if opp_pressure > 1.8:
            bid = max(bid, DAILY_SALARY * 1.05)
    else:
        bid = DAILY_SALARY * 0.9
        if highest_prev > 0:
            bid = max(bid, min(highest_prev + 6.0, DAILY_SALARY * 1.45))
        if my_urgency >= 2:
            bid = max(bid, DAILY_SALARY * 1.15)
        if opp_pressure > 2.0:
            bid = max(bid, DAILY_SALARY * 1.25)

    if day >= 8 and hp >= 7 and scarcity <= 1:
        bid *= 0.82

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.72)
    elif budget < DAILY_SALARY * 2.5:
        bid = min(bid, budget * 0.8)

    if my_urgency == 0 and avg_prev >= DAILY_SALARY * 1.8 and scarcity <= 1:
        bid = min(bid, DAILY_SALARY * 0.28)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 200:
                prev = opp.get('previous_trace', {})
                pb = prev.get('bid') if prev else None
                if pb is not None and pb >= DAILY_SALARY * 0.9:
                    rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            if prev:
                pb = prev.get('bid')
                if pb is not None:
                    prev_bids.append(float(pb))

    if not alive:
        return float(min(budget, 21.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17.0
    supply_loose = supply >= 22.0

    urgent = hp <= 3 or no_water >= 1
    very_urgent = hp <= 2 or no_water >= 2

    if very_urgent:
        bid = max(63.0, highest_prev + 2.0)
    elif urgent:
        if supply_tight:
            bid = max(52.0, highest_prev * 0.92 + 1.0)
        else:
            bid = max(44.0, avg_prev * 0.55)
    else:
        if supply_loose:
            bid = 12.0 if rich_aggressive >= 1 else 18.0
        elif supply_tight:
            if highest_prev >= 100.0:
                bid = 24.0
            else:
                bid = max(28.0, min(46.0, avg_prev * 0.45 + 4.0))
        else:
            if rich_aggressive >= 2:
                bid = 20.0
            elif highest_prev >= 100.0:
                bid = 26.0
            else:
                bid = max(24.0, min(40.0, avg_prev * 0.4 + 6.0))

    if day >= 8 and hp <= 5:
        bid = max(bid, 48.0)

    if desperate_count >= 2 and not urgent:
        bid = min(bid, 26.0)

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 2.0
    elif day == 8:
        reserve = DAILY_SALARY * 1.2
    elif day == 9:
        reserve = DAILY_SALARY * 0.6

    affordable = budget - reserve
    if affordable < 0:
        affordable = budget * 0.35

    bid = min(bid, budget, affordable if affordable > 0 else budget)
    if urgent:
        bid = min(max(bid, 35.0), budget)

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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_prev_bids = []
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
                if bid >= DAILY_SALARY * 0.9:
                    strong_prev_bids.append(bid)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    competitor_count = len(alive) + 1
    expected_share = supply / float(competitor_count)
    tight_supply = expected_share < WATER_REQ
    very_tight = supply <= 17
    ample_supply = supply >= 22

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if day >= 8:
        urgency += 1

    if urgency >= 7:
        bid = DAILY_SALARY * 1.25
    elif urgency >= 4:
        bid = DAILY_SALARY * 0.95
    else:
        if ample_supply and hp >= 6 and no_water_days == 0:
            bid = DAILY_SALARY * 0.28
        elif tight_supply:
            if highest_prev >= 120:
                bid = DAILY_SALARY * 0.72
            elif highest_prev >= 80:
                bid = max(DAILY_SALARY * 0.6, avg_prev * 0.9)
            else:
                bid = DAILY_SALARY * 0.52
        else:
            if highest_prev >= 120:
                bid = DAILY_SALARY * 0.45
            elif highest_prev >= 80:
                bid = DAILY_SALARY * 0.4
            else:
                bid = DAILY_SALARY * 0.34

    if desperate_count >= 2 and very_tight:
        bid += 12
    elif desperate_count >= 1 and tight_supply:
        bid += 6

    if day <= 2 and hp >= 8 and no_water_days == 0:
        bid *= 0.9

    reserve_target = 0.0
    days_left = max(0, 10 - day)
    if days_left >= 3 and hp > 3:
        reserve_target = DAILY_SALARY * 1.2

    affordable = max(0.0, budget - reserve_target)
    if urgency >= 4:
        affordable = budget

    bid = min(bid, affordable if affordable > 0 else budget)
    bid = max(0.0, min(bid, budget))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    return float(round(bid, 2))
"""
