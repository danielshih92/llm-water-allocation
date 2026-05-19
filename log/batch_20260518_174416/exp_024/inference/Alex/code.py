# ============================================================
# Experiment: exp_024
# Agent: Alex
# Source: exp_024
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
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 35)
        return min(budget, 18)

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0
    if scarcity > 1:
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

    if supply <= WATER_REQ:
        urgency += 2
    elif supply <= WATER_REQ + 4:
        urgency += 1

    pressure = 0
    if highest_prev >= 60:
        pressure = 3
    elif highest_prev >= 45:
        pressure = 2
    elif highest_prev >= 25:
        pressure = 1

    base = 20
    if supply >= 22:
        base = 16
    elif supply <= 17:
        base = 26

    bid = base
    bid += urgency * 8
    bid += pressure * 6
    bid += scarcity * 8
    bid += desperate_count * 2
    bid += min(rich_count, 2) * 2

    if highest_prev > 0:
        target = highest_prev + 1.5
        if urgency >= 4:
            bid = max(bid, target)
        elif pressure >= 2:
            bid = max(bid, highest_prev * 0.92)
        else:
            bid = max(bid, avg_prev + 2)

    max_safe = DAILY_SALARY * 0.95
    if urgency <= 1 and pressure == 0 and supply >= 22:
        max_safe = DAILY_SALARY * 0.45
    elif urgency >= 5:
        max_safe = DAILY_SALARY * 1.15
    elif urgency >= 3:
        max_safe = DAILY_SALARY * 1.0

    if budget < DAILY_SALARY:
        max_safe = min(max_safe, budget * 0.85 + 5)

    bid = min(bid, max_safe)
    bid = min(bid, budget)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 62))
    elif hp <= 3 and pressure >= 2:
        bid = max(bid, min(budget, highest_prev + 2 if highest_prev > 0 else 52))

    if bid < 0:
        bid = 0

    return float(bid)
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 20.0))

    likely_bids = []
    sane_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        opp_hp = opp.get('hp', 0)
        opp_budget = opp.get('budget', 0)
        opp_nowater = opp.get('no_water_days', 0)
        if opp_budget >= 120:
            rich_opp_count += 1
        if opp_hp <= 3 or opp_nowater >= 1:
            urgent_opp_count += 1

        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            likely_bids.append(float(bid))
            if float(bid) <= 140:
                sane_bids.append(float(bid))
        else:
            est = opp.get('daily_salary', DAILY_SALARY) * 0.75
            likely_bids.append(float(est))
            sane_bids.append(float(est))

    max_prev = max(likely_bids) if likely_bids else 0.0
    max_sane = max(sane_bids) if sane_bids else max_prev
    avg_sane = sum(sane_bids) / len(sane_bids) if sane_bids else 0.0

    winners_est = max(1, int(supply // WATER_REQ))
    contested = winners_est <= 1

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
    if contested:
        danger += 1
    if urgent_opp_count >= 2:
        danger += 1

    if danger >= 5:
        target = max(max_sane + 2.0, 92.0)
    elif danger >= 3:
        target = max(max_sane + 1.5, avg_sane + 4.0, 84.0)
    elif danger >= 2:
        target = max(avg_sane, 62.0)
    else:
        target = 18.0 if contested else 28.0

    if max_prev > 300:
        target = min(target, max_sane + 2.0)

    if hp >= 7 and no_water_days == 0 and contested:
        target = min(target, 25.0)

    remaining_days = max(0, 10 - int(day) + 1)
    reserve = remaining_days * 18.0
    spend_cap = budget
    if budget > reserve:
        spend_cap = max(0.0, budget - reserve * 0.35)

    if hp <= 2 or no_water_days >= 2:
        spend_cap = budget

    bid = min(target, spend_cap, budget)

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
        return float(min(budget, 18.0))

    serious_bids = []
    cindy_bid = None
    danger_count = 0
    weak_count = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = None
        if prev:
            pbid = prev.get('bid')
        if pbid is not None:
            serious_bids.append(float(pbid))
            if oid == 'Cindy':
                cindy_bid = float(pbid)
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            danger_count += 1
        if opp.get('budget', 0) < 25:
            weak_count += 1

    units = supply / float(WATER_REQ)

    if hp <= 1 or no_water >= 2:
        emergency = 68.0
        if cindy_bid is not None:
            emergency = max(emergency, min(95.0, cindy_bid + 4.0))
        return float(min(budget, emergency))

    if hp <= 2 or no_water >= 1:
        urgent = 54.0
        if cindy_bid is not None:
            urgent = max(urgent, min(90.0, cindy_bid + 2.0))
        elif serious_bids:
            urgent = max(urgent, min(85.0, max(serious_bids) + 2.0))
        return float(min(budget, urgent))

    if units >= 2.0:
        base = 16.0
        if cindy_bid is not None:
            if cindy_bid >= 90:
                base = 12.0
            elif cindy_bid >= 70:
                base = 18.0
            else:
                base = 22.0
        elif serious_bids:
            mx = max(serious_bids)
            if mx >= 80:
                base = 14.0
            elif mx >= 40:
                base = 20.0
            else:
                base = 24.0
        if weak_count >= 2:
            base -= 2.0
        if day >= 8:
            base += 4.0
        return float(min(budget, max(8.0, base)))

    base = 34.0
    if cindy_bid is not None:
        if cindy_bid >= 95:
            base = 28.0
        elif cindy_bid >= 80:
            base = 36.0
        elif cindy_bid >= 60:
            base = 42.0
        else:
            base = 38.0
    elif serious_bids:
        mx = max(serious_bids)
        base = max(32.0, min(48.0, mx + 1.5))

    if danger_count >= 2:
        base += 6.0
    if day >= 8:
        base += 8.0
    if budget < 60:
        base -= 4.0

    return float(min(budget, max(18.0, base)))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    pressured_bids = []
    rich_count = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY:
                rich_count += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace') or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 4 or opp.get('no_water_days', 0) >= 1:
                    pressured_bids.append(float(bid))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    capacity = supply / float(WATER_REQ)
    tight = capacity < (1 + 0.35 * len(alive))
    roomy = capacity > (1 + 0.6 * len(alive))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    pressure_prev = max(pressured_bids) if pressured_bids else highest_prev

    base = DAILY_SALARY * 0.42

    if roomy:
        base = DAILY_SALARY * 0.28
    elif tight:
        base = DAILY_SALARY * 0.68

    if rich_count >= 2:
        base += 8.0
    elif rich_count == 0:
        base -= 6.0

    if desperate_count >= 2:
        base += 10.0

    if highest_prev > 0:
        if highest_prev >= DAILY_SALARY * 1.5:
            target = DAILY_SALARY * 0.52 if hp > 4 and no_water_days == 0 else DAILY_SALARY * 0.92
        elif highest_prev >= DAILY_SALARY * 0.95:
            target = max(base, pressure_prev + 2.5)
        else:
            target = max(base, highest_prev + 1.5)
    else:
        target = base

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 1.02)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.82)

    if day >= 8:
        target += 6.0
    if day == 10:
        target += 10.0

    reserve_floor = 0.0
    if hp > 4 and no_water_days == 0 and day < 8:
        reserve_floor = DAILY_SALARY * (10 - day) * 0.08

    spendable = max(0.0, budget - reserve_floor)
    if spendable <= 0:
        spendable = budget * 0.5

    bid = min(target, spendable, budget)
    if bid < 0:
        bid = 0.0
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply / WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    opp_pressures = []
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        pressure = 0.0
        if bid is not None:
            pressure += float(bid)
        pressure += max(0, 4 - opp.get('hp', 0)) * 8.0
        pressure += opp.get('no_water_days', 0) * 10.0
        if opp.get('budget', 0) > budget:
            pressure += 4.0
        opp_pressures.append(pressure)
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_pressure = max(opp_pressures) if opp_pressures else 0.0

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

    contested = False
    if slots <= 1:
        contested = True
    if desperate_count >= max(1, slots):
        contested = True
    if highest_prev >= 110:
        contested = True

    if not alive_opponents:
        bid = 18.0 if urgency == 0 else 42.0
    elif urgency >= 5:
        bid = max(0.95 * DAILY_SALARY, highest_prev + 2.5, avg_prev + 4.0)
    elif urgency >= 3:
        if contested:
            bid = max(0.82 * DAILY_SALARY, highest_prev + 1.5)
        else:
            bid = max(0.62 * DAILY_SALARY, avg_prev * 0.7 + 6.0)
    elif urgency >= 1:
        if slots >= 2 and highest_prev >= 95:
            bid = max(22.0, avg_prev * 0.28)
        elif contested:
            bid = max(0.58 * DAILY_SALARY, highest_prev * 0.55)
        else:
            bid = max(20.0, avg_prev * 0.22)
    else:
        if slots >= 2:
            bid = 16.0 if highest_prev >= 90 else 24.0
        else:
            bid = max(26.0, highest_prev * 0.35)

    if budget < bid:
        bid = budget

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 63.0))

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if len(alive) == 0:
        base = DAILY_SALARY * 0.25
        if hp <= 2 or no_water >= 2:
            base = DAILY_SALARY * 0.6
        return float(min(budget, base))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    broke_count = 0
    pressure_score = 0.0

    for oid, opp in alive:
        obudget = opp.get('budget', 0)
        ohp = opp.get('hp', 0)
        onw = opp.get('no_water_days', 0)
        if obudget < DAILY_SALARY * 0.8:
            broke_count += 1
        if obudget > DAILY_SALARY * 2.0:
            rich_count += 1
        if ohp <= 3 or onw >= 2:
            desperate_count += 1

        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(pbid)
            if pbid >= 150:
                pressure_score += 2.2
            elif pbid >= 110:
                pressure_score += 1.5
            elif pbid >= 70:
                pressure_score += 0.9
            else:
                pressure_score += 0.3
        if prev.get('status') == 'error':
            pressure_score -= 0.5

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 70.0
    max_prev = max(prev_bids) if prev_bids else 70.0

    supply_tight = (supply <= 17)
    supply_loose = (supply >= 22)

    urgency = 0.0
    if hp <= 2:
        urgency += 3.0
    elif hp <= 4:
        urgency += 1.8
    if no_water >= 2:
        urgency += 3.0
    elif no_water >= 1:
        urgency += 1.2
    if day >= 8:
        urgency += 0.6
    if supply_tight:
        urgency += 1.2
    elif supply_loose:
        urgency -= 0.5

    market_heat = pressure_score / max(1, len(alive))
    if desperate_count >= 2:
        market_heat += 0.8
    if broke_count >= 2:
        market_heat -= 0.7
    if rich_count >= 2:
        market_heat += 0.4

    if urgency < 1.0 and supply_loose:
        bid = DAILY_SALARY * 0.28
    elif urgency < 2.0 and market_heat > 1.4:
        bid = DAILY_SALARY * 0.35
    elif urgency >= 4.0:
        bid = max(DAILY_SALARY * 1.35, min(max_prev + 6.0, DAILY_SALARY * 2.2))
    elif urgency >= 2.5:
        bid = max(DAILY_SALARY * 0.95, min(avg_prev + 4.0, DAILY_SALARY * 1.7))
    else:
        if market_heat > 1.8:
            bid = DAILY_SALARY * 0.45
        elif market_heat > 1.1:
            bid = DAILY_SALARY * 0.62
        else:
            bid = DAILY_SALARY * 0.78

    if supply_tight and urgency >= 2.0:
        bid += 12.0
    if supply_loose and urgency < 2.0:
        bid -= 8.0

    if budget < DAILY_SALARY * 1.2 and urgency < 3.0:
        bid = min(bid, budget * 0.55)
    elif budget < DAILY_SALARY * 0.8:
        bid = min(bid, budget * 0.8)

    if hp >= 7 and no_water == 0 and market_heat > 1.6 and day <= 6:
        bid = min(bid, DAILY_SALARY * 0.4)

    min_probe = 6.0 if urgency < 2.0 else 18.0
    bid = max(min_probe, bid)
    bid = min(bid, budget)
    return float(max(0.0, bid))
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
        if hp <= 2 or no_water >= 1:
            return max(0.0, min(budget, DAILY_SALARY * 0.75))
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    opp_signals = []
    urgent_count = 0
    rich_urgent_bids = []
    all_prev_bids = []

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is not None:
            try:
                prev_bid = float(prev_bid)
                all_prev_bids.append(prev_bid)
            except Exception:
                prev_bid = None

        urgency = 0.0
        if opp.get('hp', 10) <= 3:
            urgency += 1.2
        elif opp.get('hp', 10) <= 5:
            urgency += 0.7
        if opp.get('no_water_days', 0) >= 2:
            urgency += 1.2
        elif opp.get('no_water_days', 0) >= 1:
            urgency += 0.6
        if opp.get('budget', 0) >= 200:
            urgency += 0.4
        elif opp.get('budget', 0) <= 60:
            urgency -= 0.3
        if prev_bid is not None:
            if prev_bid >= 140:
                urgency += 0.8
            elif prev_bid >= 90:
                urgency += 0.4
            elif prev_bid <= 40:
                urgency -= 0.2

        if urgency >= 1.2:
            urgent_count += 1
            if prev_bid is not None:
                rich_urgent_bids.append(prev_bid)

        opp_signals.append((urgency, prev_bid, oid, opp))

    opp_signals.sort(key=lambda x: x[0], reverse=True)

    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_tightness < 0:
        supply_tightness = 0.0
    if supply_tightness > 1:
        supply_tightness = 1.0

    my_urgency = 0.0
    if hp <= 2:
        my_urgency += 1.8
    elif hp <= 4:
        my_urgency += 1.0
    elif hp <= 6:
        my_urgency += 0.4
    if no_water >= 2:
        my_urgency += 1.6
    elif no_water >= 1:
        my_urgency += 0.8
    my_urgency += 0.7 * supply_tightness
    if day >= 8:
        my_urgency += 0.2

    strongest_prev = 0.0
    if rich_urgent_bids:
        strongest_prev = max(rich_urgent_bids)
    elif all_prev_bids:
        strongest_prev = max(all_prev_bids)

    if my_urgency >= 2.6:
        base = max(DAILY_SALARY * 0.95, strongest_prev + 3.0)
    elif my_urgency >= 1.6:
        base = max(DAILY_SALARY * 0.72, strongest_prev + 2.0 if strongest_prev > 0 else DAILY_SALARY * 0.72)
    elif supply >= 22:
        base = DAILY_SALARY * 0.26
    elif supply >= 19:
        base = DAILY_SALARY * 0.42
    else:
        if strongest_prev >= 150:
            base = DAILY_SALARY * 0.55
        elif strongest_prev >= 100:
            base = strongest_prev + 1.5
        elif strongest_prev > 0:
            base = max(DAILY_SALARY * 0.48, strongest_prev + 1.0)
        else:
            base = DAILY_SALARY * 0.5

    if urgent_count >= 2 and supply <= 18:
        base += 6.0
    elif urgent_count == 0 and supply >= 20:
        base -= 6.0

    if budget < DAILY_SALARY:
        if my_urgency >= 2.0:
            base = min(base, budget)
        else:
            base = min(base, budget * 0.7)

    if hp >= 8 and no_water == 0 and supply >= 21:
        base = min(base, DAILY_SALARY * 0.35)

    bid = max(0.0, min(float(budget), float(base)))
    return bid
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 110:
                    strong_prev.append(float(bid))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_strong_prev = sum(strong_prev) / len(strong_prev) if strong_prev else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.6
    elif hp <= 6:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.45

    if day >= 8:
        urgency += 0.15

    if supply >= 23 and hp >= 7 and no_water_days == 0:
        bid = DAILY_SALARY * 0.28
    elif supply >= 20 and hp >= 6 and no_water_days == 0:
        bid = DAILY_SALARY * 0.42
    else:
        pressure_anchor = max(95.0, avg_strong_prev)
        bid = pressure_anchor * (0.78 + 0.28 * scarcity) + 18.0 * urgency

    if scarcity >= 0.7:
        bid += 10.0
    if hp <= 3 or no_water_days >= 2:
        bid = max(bid, highest_prev + 3.0)
    elif hp <= 5 or no_water_days == 1:
        bid = max(bid, highest_prev * 0.92)

    if budget < 140:
        bid *= 0.82
    if budget < 90:
        bid *= 0.72

    if hp >= 8 and no_water_days == 0 and supply >= 22:
        bid = min(bid, DAILY_SALARY * 0.55)

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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp_bids = []
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                    urgent_opp_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else highest_prev

    tight_supply = supply <= 17
    ample_supply = supply >= 22
    critical_me = (no_water_days >= 2) or (hp <= 3)
    pressured_me = (no_water_days >= 1) or (hp <= 5)

    if critical_me:
        bid = max(urgent_prev + 2.5, DAILY_SALARY * 0.95)
        if budget < bid:
            bid = budget
        return float(max(0.0, min(budget, bid)))

    if tight_supply:
        if highest_prev >= 120:
            bid = 36.0 if hp >= 7 and no_water_days == 0 else 78.0
        else:
            bid = max(52.0, urgent_prev + 1.8)
            if pressured_me:
                bid = max(bid, 74.0)
        return float(max(0.0, min(budget, bid)))

    if ample_supply:
        if pressured_me:
            bid = max(34.0, min(62.0, highest_prev * 0.72 + 2.0))
        else:
            bid = 16.0 if highest_prev > 90 else 22.0
        return float(max(0.0, min(budget, bid)))

    if pressured_me:
        bid = max(48.0, min(88.0, urgent_prev + 1.2))
    else:
        if highest_prev > 140:
            bid = 24.0
        elif highest_prev > 80:
            bid = 31.0
        else:
            bid = max(26.0, highest_prev * 0.6 + 3.0)

    if rich_count >= 2 and not pressured_me:
        bid *= 0.9

    return float(max(0.0, min(budget, bid)))
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
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 200:
                rich_opp += 1
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    b = float(prev.get('bid', 0))
                    if b >= 0:
                        prev_bids.append(b)
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        base = 66.0 if tight_supply else 58.0
        if highest_prev > 0:
            base = max(base, min(69.0, highest_prev + 2.0))
        return float(min(budget, base))

    if hp <= 4 or no_water >= 1:
        base = 48.0 if ample_supply else 56.0
        if highest_prev >= 80:
            base = 42.0 if hp > 3 else 63.0
        elif highest_prev >= 45:
            base = max(base, min(64.0, highest_prev + 1.5))
        return float(min(budget, base))

    if ample_supply:
        if highest_prev >= 100:
            bid = 16.0
        elif highest_prev >= 60:
            bid = 24.0
        else:
            bid = 20.0
        if rich_opp >= 1:
            bid -= 2.0
        return float(max(0.0, min(budget, bid)))

    if tight_supply:
        bid = 40.0
        if highest_prev >= 100:
            bid = 28.0
        elif highest_prev >= 70:
            bid = 34.0
        elif highest_prev >= 35:
            bid = max(bid, highest_prev + 1.0)
        if urgent_opp >= 2:
            bid += 4.0
        return float(min(budget, bid))

    bid = 30.0
    if highest_prev >= 100:
        bid = 22.0
    elif highest_prev >= 75:
        bid = 27.0
    elif highest_prev >= 40:
        bid = max(30.0, avg_prev + 1.0)

    if day >= 8 and hp >= 5:
        bid -= 3.0

    return float(max(0.0, min(budget, bid)))
"""
