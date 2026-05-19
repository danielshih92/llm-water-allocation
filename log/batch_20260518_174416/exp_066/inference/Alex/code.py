# ============================================================
# Experiment: exp_066
# Agent: Alex
# Source: exp_066
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

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    players = 1 + len(alive_opponents)
    total_need = players * WATER_REQ
    scarcity = total_need - supply

    if len(alive_opponents) == 0:
        return max(0, min(budget, round(DAILY_SALARY * 0.25, 2)))

    if hp <= 1:
        base = DAILY_SALARY * 0.98
    elif hp <= 2 or no_water >= 1:
        base = DAILY_SALARY * 0.9
    elif scarcity <= 0:
        base = DAILY_SALARY * 0.38
    elif scarcity <= WATER_REQ:
        base = DAILY_SALARY * 0.52
    else:
        base = DAILY_SALARY * 0.68

    if desperate_count >= max(1, len(alive_opponents) // 2):
        base += 6
    if rich_count >= max(1, len(alive_opponents) // 2):
        base += 4

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if hp <= 2 or no_water >= 1:
            base = max(base, highest_prev + 2.0)
        elif scarcity > 0:
            base = max(base, avg_prev + 1.0)
        else:
            base = min(base, highest_prev)

    if budget < DAILY_SALARY * 0.6 and hp > 2 and no_water == 0:
        base *= 0.8

    bid = max(0, min(budget, base))
    return round(bid, 2)
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    aggressive_count = 0
    weak_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 100:
                aggressive_count += 1
            if bid <= 45:
                weak_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    scarcity = 1.0 - supply_ratio

    if hp <= 2 or no_water_days >= 2:
        emergency = True
    elif hp <= 4 and no_water_days >= 1:
        emergency = True
    else:
        emergency = False

    if emergency:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
        if highest_prev >= 140:
            target = max(target, 145.0)
        return float(min(budget, target))

    if scarcity <= 0.2:
        base = DAILY_SALARY * 0.28
    elif scarcity <= 0.5:
        base = DAILY_SALARY * 0.42
    else:
        base = DAILY_SALARY * 0.62

    if highest_prev >= 140:
        target = base
        if hp <= 5 or no_water_days >= 1:
            target = max(target, DAILY_SALARY * 0.88)
    elif highest_prev >= 100:
        target = max(base, min(highest_prev * 0.72, DAILY_SALARY * 0.92))
    elif highest_prev >= 60:
        target = max(base, highest_prev + 2.5)
    elif highest_prev > 0:
        target = max(base, highest_prev + 1.5)
    else:
        target = DAILY_SALARY * 0.45

    if aggressive_count >= 2 and scarcity < 0.4 and hp >= 6 and no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.33)

    if weak_count >= 2 and scarcity > 0.5:
        target = max(target, DAILY_SALARY * 0.58)

    if day >= 8:
        target += 6.0
    if hp <= 5:
        target += 8.0
    if no_water_days == 1:
        target += 10.0

    if target < 0:
        target = 0.0

    return float(min(budget, target))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_threat = 0.0
    weak_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2 or opp.get('budget', 0) <= 0:
                weak_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev['bid'])
                prev_bids.append(b)
                if opp.get('hp', 0) >= 5 and opp.get('budget', 0) >= DAILY_SALARY * 2:
                    if b > strong_threat:
                        strong_threat = b

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    contested_units = supply / float(WATER_REQ)
    high_supply = contested_units >= 1.8
    low_supply = contested_units <= 1.3

    if hp <= 2 or no_water >= 2:
        emergency = DAILY_SALARY * 0.98
        if prev_bids:
            emergency = max(emergency, max(prev_bids) + 2.0)
        return max(0.0, min(budget, emergency))

    if hp <= 4 or no_water >= 1:
        urgent = DAILY_SALARY * 0.82
        if strong_threat > 0:
            urgent = max(urgent, min(strong_threat + 2.0, DAILY_SALARY * 1.15))
        elif prev_bids:
            urgent = max(urgent, max(prev_bids) + 1.5)
        return max(0.0, min(budget, urgent))

    base = DAILY_SALARY * 0.42
    if high_supply:
        base = DAILY_SALARY * 0.28
    if low_supply:
        base = DAILY_SALARY * 0.6

    if strong_threat >= DAILY_SALARY * 1.8:
        base = min(base, DAILY_SALARY * 0.35)
    elif strong_threat >= DAILY_SALARY * 1.1:
        base = max(base, DAILY_SALARY * 0.68)
    elif prev_bids:
        base = max(base, min(max(prev_bids) + 1.0, DAILY_SALARY * 0.75))

    if weak_count >= 2 and hp >= 6:
        base *= 0.85

    if budget < DAILY_SALARY:
        base = min(base, budget)
    elif budget > DAILY_SALARY * 6 and hp >= 7 and low_supply:
        base = max(base, DAILY_SALARY * 0.78)

    return max(0.0, min(budget, base))
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
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    urgent_prev_bids = []
    weak_prev_bids = []
    rich_count = 0
    desperate_count = 0

    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 8:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_prev_bids.append(float(pbid))
            else:
                weak_prev_bids.append(float(pbid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_urgent = max(urgent_prev_bids) if urgent_prev_bids else highest_prev
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    need = 0.0
    if hp <= 2:
        need += 1.0
    elif hp <= 4:
        need += 0.65
    elif hp <= 6:
        need += 0.35

    if no_water >= 2:
        need += 1.0
    elif no_water >= 1:
        need += 0.55

    if day >= 8:
        need += 0.2

    pressure_bid = highest_urgent + 2.0
    if pressure_bid < avg_prev + 1.0:
        pressure_bid = avg_prev + 1.0

    base = DAILY_SALARY * (0.28 + 0.42 * scarcity)

    if need >= 1.4:
        bid = max(base, pressure_bid, DAILY_SALARY * 0.95)
    elif need >= 0.8:
        bid = max(base, min(pressure_bid, DAILY_SALARY * 1.15), DAILY_SALARY * 0.72)
    elif scarcity >= 0.75:
        bid = max(base, min(highest_prev + 1.5, DAILY_SALARY * 0.95))
    elif supply >= 22:
        bid = DAILY_SALARY * 0.22
    elif supply >= 20:
        bid = DAILY_SALARY * 0.32
    else:
        bid = max(base, min(highest_prev * 0.72, DAILY_SALARY * 0.68))

    if rich_count >= 2 and scarcity >= 0.6 and need < 0.8:
        bid = min(bid, DAILY_SALARY * 0.45)

    if desperate_count >= 2 and need >= 0.8:
        bid = max(bid, highest_urgent + 3.0)

    reserve_target = DAILY_SALARY * max(0, 10 - day) * 0.38
    max_affordable = budget
    if budget > reserve_target and need < 1.4:
        max_affordable = max(0.0, budget - reserve_target * 0.35)

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = 18.0 if hp > 3 else 45.0
        return float(max(0.0, min(budget, base)))

    threat_bids = []
    urgent_threat = 0.0
    cindy_bid = None
    david_bid = None

    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is None:
            est = min(opp.get('budget', 0.0), opp.get('daily_salary', DAILY_SALARY) * 0.75)
            threat_bids.append(est)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                urgent_threat = max(urgent_threat, est)
            continue

        name_hint = ''
        if bid is not None:
            threat_bids.append(float(bid))
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            pass
        if bid is not None and bid > 120:
            cindy_bid = float(bid)
        elif bid is not None and 60 <= bid <= 120:
            david_bid = float(bid)
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            urgent_threat = max(urgent_threat, float(bid))

    highest_prev = max(threat_bids) if threat_bids else 0.0
    mid_prev = david_bid if david_bid is not None else highest_prev

    contested_units = float(supply) / float(WATER_REQ)

    if hp <= 2 or no_water_days >= 2:
        bid = max(highest_prev + 2.0, DAILY_SALARY * 1.15)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(mid_prev + 2.0, urgent_threat + 2.0, DAILY_SALARY * 0.92)
    else:
        if contested_units >= 1.8:
            if david_bid is not None:
                bid = max(22.0, min(david_bid + 2.0, DAILY_SALARY * 0.95))
            else:
                bid = max(24.0, min(highest_prev * 0.7 + 3.0, DAILY_SALARY * 0.9))
        elif contested_units >= 1.45:
            bid = max(mid_prev + 3.0, DAILY_SALARY * 0.82)
        else:
            if hp >= 6 and no_water_days == 0:
                bid = min(DAILY_SALARY * 0.38, max(12.0, mid_prev * 0.45))
            else:
                bid = max(mid_prev + 4.0, DAILY_SALARY * 0.9)

    if day >= 8:
        bid = max(bid, DAILY_SALARY * 0.88)
    if hp <= 3:
        bid = max(bid, DAILY_SALARY * 1.0)

    bid = min(float(budget), float(bid))
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
        return max(0.0, min(budget, 18.0))

    pressure_bids = []
    cindy_bid = None
    cindy_alive = False
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            pressure_bids.append(float(bid))
        if oid == 'Cindy':
            cindy_alive = True
            if bid is not None:
                cindy_bid = float(bid)

    tight_supply = supply <= 17.0
    medium_supply = supply <= 20.0
    critical = hp <= 3 or no_water >= 2
    urgent = hp <= 5 or no_water >= 1

    if cindy_alive:
        anchor = 99.0 if cindy_bid is None else cindy_bid
    elif pressure_bids:
        anchor = max(pressure_bids)
    else:
        anchor = 45.0

    if critical:
        bid = max(92.0, anchor + 3.0)
    elif tight_supply:
        bid = max(86.0, anchor - 4.0)
    elif urgent and medium_supply:
        bid = max(72.0, anchor - 12.0)
    elif urgent:
        bid = 58.0
    else:
        if cindy_alive:
            bid = 16.0 if supply >= 22.0 else 24.0
        else:
            bid = 28.0

    if day >= 8 and hp <= 6:
        bid = max(bid, 78.0)

    if budget <= 0:
        return 0.0

    reserve_floor = max(0.0, (10 - day) * 8.0)
    affordable = max(0.0, budget - reserve_floor)
    if critical:
        affordable = budget

    final_bid = min(budget, max(0.0, min(bid, max(affordable, 0.0))))

    if final_bid < 1.0 and budget >= 1.0:
        final_bid = 1.0

    return float(final_bid)
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    danger_scores = []

    for oid, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive.append(opp)
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

        o_hp = float(opp.get('hp', 10))
        o_nowater = int(opp.get('no_water_days', 0))
        o_budget = float(opp.get('budget', 0))
        o_salary = float(opp.get('daily_salary', DAILY_SALARY))
        desperation = 0.0
        if o_hp <= 3:
            desperation += 1.2
        elif o_hp <= 5:
            desperation += 0.6
        desperation += 0.45 * o_nowater
        if o_budget > o_salary * 8:
            desperation += 0.5
        elif o_budget > o_salary * 4:
            desperation += 0.25
        if bid is not None:
            if float(bid) >= o_salary * 1.2:
                desperation += 0.7
            elif float(bid) >= o_salary * 0.9:
                desperation += 0.35
        danger_scores.append(desperation)

    if not alive:
        base = DAILY_SALARY * 0.22
        if hp <= 3 or no_water >= 1:
            base = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, base)))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    opp_pressure = max(danger_scores) if danger_scores else 0.0

    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1

    target = DAILY_SALARY * 0.42 + scarcity * DAILY_SALARY * 0.28

    if highest_prev > 0:
        target = max(target, highest_prev + 2.1)
        if highest_prev >= 120:
            if urgent:
                target = max(target, highest_prev + 3.0)
            else:
                target = min(target, DAILY_SALARY * 0.48)
        elif highest_prev >= 85:
            if semi_urgent:
                target = max(target, highest_prev + 1.6)
            else:
                target = min(target, avg_prev * 0.82)

    if opp_pressure >= 1.8:
        target += 8.0
    elif opp_pressure >= 1.0:
        target += 4.0

    if urgent:
        target = max(target, DAILY_SALARY * 0.95 + scarcity * 10.0)
    elif semi_urgent:
        target = max(target, DAILY_SALARY * 0.72 + scarcity * 8.0)
    else:
        if scarcity < 0.35 and highest_prev >= 85:
            target = min(target, DAILY_SALARY * 0.38)

    remaining_days = max(1, 10 - day)
    reserve_floor = remaining_days * DAILY_SALARY * 0.18
    spend_cap = budget
    if budget > reserve_floor:
        spend_cap = max(0.0, budget - reserve_floor * 0.15)

    if day >= 8:
        spend_cap = budget
        if semi_urgent:
            target += 6.0

    bid = min(spend_cap, target)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    high_supply = supply >= 22
    low_supply = supply <= 17

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = DAILY_SALARY * 0.6
        avg_prev = DAILY_SALARY * 0.5

    pressure = avg_prev
    if low_supply:
        pressure += 18.0
    elif high_supply:
        pressure -= 10.0

    pressure += urgent_opp * 6.0
    pressure += rich_opp * 2.0

    if hp <= 2 or no_water >= 2:
        bid = max(pressure + 12.0, highest_prev + 3.0, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water >= 1:
        bid = max(pressure + 5.0, avg_prev + 2.0, DAILY_SALARY * 0.72)
    else:
        if high_supply:
            bid = max(18.0, avg_prev - 12.0)
        elif low_supply:
            bid = max(DAILY_SALARY * 0.62, highest_prev + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.48, avg_prev - 2.0)

    if day >= 8:
        bid += 4.0
    if hp >= 8 and no_water == 0 and high_supply:
        bid -= 4.0

    bid = max(0.0, min(float(budget), float(bid)))
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    slots = max(1, int(supply / WATER_REQ))
    scarcity = 0
    if slots <= 1:
        scarcity = 2
    elif slots <= 2:
        scarcity = 1

    highest_prev = 0.0
    cindy_prev = None
    desperate_count = 0
    rich_alive = 0
    for agent_id, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_alive += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                b = float(bid)
            except Exception:
                b = 0.0
            if b > highest_prev:
                highest_prev = b
            if agent_id == 'Cindy':
                cindy_prev = b

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    elif hp <= 6:
        urgency += 1
    if no_water_days >= 1:
        urgency += 2
    urgency += scarcity

    target = DAILY_SALARY * 0.42

    if cindy_prev is not None:
        if urgency >= 4:
            target = max(target, min(cindy_prev + 3.0, DAILY_SALARY * 1.6))
        elif urgency >= 2:
            target = max(target, min(cindy_prev * 0.82 + 2.0, DAILY_SALARY * 1.15))
        else:
            target = max(target, min(cindy_prev * 0.58, DAILY_SALARY * 0.72))
    elif highest_prev > 0:
        if urgency >= 4:
            target = max(target, min(highest_prev + 2.0, DAILY_SALARY * 1.35))
        elif urgency >= 2:
            target = max(target, min(highest_prev * 0.8 + 1.0, DAILY_SALARY))
        else:
            target = max(target, min(highest_prev * 0.55, DAILY_SALARY * 0.7))

    if scarcity == 2 and urgency >= 3:
        target = max(target, DAILY_SALARY * 1.18)
    elif scarcity == 1 and urgency >= 2:
        target = max(target, DAILY_SALARY * 0.82)

    if rich_alive <= 1 and desperate_count >= 1 and urgency <= 2:
        target *= 0.82

    if hp >= 7 and no_water_days == 0 and scarcity == 0:
        target = min(target, DAILY_SALARY * 0.45)

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0:
        soft_cap = min(budget, max(DAILY_SALARY * 0.35, budget / (reserve_days + 0.5) * 1.35))

    if urgency >= 5:
        soft_cap = budget
    elif urgency >= 3:
        soft_cap = min(budget, max(soft_cap, DAILY_SALARY * 0.95))

    bid = min(target, soft_cap)
    if hp <= 1 or no_water_days >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 1.25, highest_prev + 4.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
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
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 1:
            safe_bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, safe_bid))

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 500:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    likely_units = int(supply // WATER_REQ)
    contested = likely_units <= 1

    if hp <= 2 or no_water_days >= 2:
        return float(min(budget, max(DAILY_SALARY * 1.35, highest_prev + 3.0, 92.0)))

    if no_water_days >= 1:
        if contested:
            return float(min(budget, max(DAILY_SALARY * 1.15, highest_prev + 2.0, 82.0)))
        return float(min(budget, max(DAILY_SALARY * 0.95, avg_prev * 0.72, 62.0)))

    if contested:
        if highest_prev >= 130:
            bid = DAILY_SALARY * 0.22
        elif highest_prev >= 90:
            bid = DAILY_SALARY * 0.32
        else:
            bid = max(DAILY_SALARY * 0.55, highest_prev + 1.5)

        if day >= 8 and hp >= 5:
            bid *= 0.8
        if desperate_opp >= 1:
            bid *= 0.85
        return float(min(budget, max(0.0, bid)))

    bid = DAILY_SALARY * 0.18
    if highest_prev < 80:
        bid = DAILY_SALARY * 0.28
    if rich_opp >= 2 and highest_prev >= 120:
        bid = DAILY_SALARY * 0.12
    if day >= 9 and hp >= 6:
        bid = DAILY_SALARY * 0.1

    return float(min(budget, max(0.0, bid)))
"""
