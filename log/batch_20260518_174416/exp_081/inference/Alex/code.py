# ============================================================
# Experiment: exp_081
# Agent: Alex
# Source: exp_081
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = 18.0 if hp > 3 else 40.0
        return max(0.0, min(float(budget), base))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            if prev.get('status') == 'won':
                prev_bids.append(float(prev['bid']) + 0.5)

    if hp <= 1:
        target = DAILY_SALARY * 0.98
        if prev_bids:
            target = max(target, min(float(budget), max(prev_bids) + 2.0))
        return max(0.0, min(float(budget), target))

    if hp <= 2 or no_water_days >= 1:
        target = DAILY_SALARY * 0.82
        if prev_bids:
            target = max(target, max(prev_bids) + 1.5)
        if supply >= 22:
            target -= 6.0
        return max(0.0, min(float(budget), target))

    pressure = 0.0
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        pressure = max(highest_prev * 0.75, avg_prev)
    else:
        pressure = DAILY_SALARY * 0.45

    if supply >= 22:
        base = 24.0
    elif supply >= 18:
        base = 31.0
    else:
        base = 39.0

    if desperate_count > 0:
        base += 8.0
    if rich_count >= len(alive_opponents) / 2.0:
        base += 4.0
    if day >= 8:
        base += 6.0

    if prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev >= DAILY_SALARY * 0.9 and hp > 3 and no_water_days == 0:
            bid = base * 0.8
        else:
            bid = max(base, min(highest_prev + 1.0, pressure + 3.0))
    else:
        bid = base

    if budget < DAILY_SALARY * 0.6 and hp > 2:
        bid = min(bid, DAILY_SALARY * 0.45)

    return max(0.0, min(float(budget), float(bid)))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    affordable_pressures = []
    urgent_opponents = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    affordable_pressures.append(min(float(bid), float(opp.get('budget', 0))))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    slots = max(1, int(supply // WATER_REQ))
    competitors = len(alive_opponents) + 1
    tightness = competitors - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_affordable = max(affordable_pressures) if affordable_pressures else 0.0

    if slots >= competitors:
        base = 8.0
    elif tightness >= 3:
        base = 92.0
    elif tightness == 2:
        base = 72.0
    else:
        base = 48.0

    if highest_affordable > 0:
        if tightness >= 2:
            target = max(base, highest_affordable + 2.0)
        else:
            target = max(base, highest_affordable * 0.72)
    else:
        target = base

    if hp <= 2 or no_water_days >= 2:
        target = max(target, 118.0)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, 88.0)

    if urgent_opponents >= 2 and slots <= 1:
        target += 10.0

    if day >= 8:
        target += 8.0

    reserve_days = max(0, 10 - day)
    soft_cap = budget if reserve_days <= 0 else max(25.0, budget - reserve_days * 18.0)

    if hp >= 7 and no_water_days == 0 and slots >= 2 and highest_prev >= 120.0:
        target = min(target, 28.0)

    bid = min(budget, min(target, soft_cap))

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, min(130.0, budget)))

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

    supply = day_context['supply']
    day = day_context['day']
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
        safe = DAILY_SALARY * 0.28
        if hp <= 2 or no_water >= 1:
            safe = DAILY_SALARY * 0.55
        return float(min(budget, safe))

    prev_bids = []
    aggressive_count = 0
    all_in_count = 0
    fixed_high_count = 0
    weak_opp_count = 0

    for opp in alive_opponents:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            weak_opp_count += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= DAILY_SALARY * 0.75:
                aggressive_count += 1
            if bid >= DAILY_SALARY * 1.4:
                all_in_count += 1
            if bid >= 140:
                fixed_high_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    if prev_bids:
        filtered = [b for b in prev_bids if b < 120]
        moderate_prev = max(filtered) if filtered else min(highest_prev, DAILY_SALARY)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    base = DAILY_SALARY * (0.34 + 0.18 * scarcity)

    if supply >= 23:
        base -= 8
    elif supply <= 17:
        base += 8

    if hp <= 2:
        bid = DAILY_SALARY * 0.96
    elif no_water >= 2:
        bid = DAILY_SALARY * 0.98
    elif hp <= 4 or no_water >= 1:
        bid = max(DAILY_SALARY * 0.72, moderate_prev + 2.0)
    else:
        if all_in_count >= 1:
            bid = max(base, DAILY_SALARY * 0.42)
        elif aggressive_count >= 2:
            bid = max(base + 4, moderate_prev + 1.5)
        elif aggressive_count == 1:
            bid = max(base, moderate_prev + 1.0)
        else:
            bid = max(base, moderate_prev * 0.92)

    if fixed_high_count >= 1 and hp > 4 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.58)

    if weak_opp_count >= 2 and hp > 4 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.5)

    if day >= 8:
        bid += 4
    if day >= 9 and (hp <= 4 or no_water >= 1):
        bid += 8

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if hp > 4 and no_water == 0 and days_left > 1:
        reserve_floor = DAILY_SALARY * 0.35 * min(days_left - 1, 3)

    affordable = max(0.0, budget - reserve_floor)
    if affordable <= 0:
        affordable = min(budget, DAILY_SALARY * 0.4)

    bid = min(bid, affordable)
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    threat_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_opponents += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) > 0:
                threat_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_bids) if threat_bids else highest_prev

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_threat + 2.5)
    elif hp <= 4 or no_water_days >= 1:
        if tight_supply:
            bid = max(DAILY_SALARY * 0.88, highest_threat + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.72, avg_prev + 2.0)
    else:
        if tight_supply:
            bid = max(DAILY_SALARY * 0.82, highest_threat + 1.5)
        elif medium_supply:
            bid = max(DAILY_SALARY * 0.62, avg_prev + 1.0)
        else:
            bid = DAILY_SALARY * 0.42

    if rich_opponents >= 2:
        bid += 4.0
    elif rich_opponents == 1:
        bid += 2.0

    if urgent_opponents >= 2 and tight_supply:
        bid += 5.0
    elif urgent_opponents >= 1 and medium_supply:
        bid += 2.5

    if day >= 8 and hp > 4:
        bid *= 0.94

    cap = budget
    if hp > 4 and no_water_days == 0:
        cap = min(cap, DAILY_SALARY * 1.15)
    else:
        cap = min(cap, DAILY_SALARY * 1.4)

    if budget < DAILY_SALARY * 0.6 and hp > 3 and no_water_days == 0:
        bid = min(bid, budget * 0.75)

    bid = max(0.0, min(bid, cap))
    return float(round(bid, 2))
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

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0.0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > budget:
                    rich_pressure = max(rich_pressure, float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tightness = 1.0 - scarcity

    emergency = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if emergency:
        target = max(0.92 * DAILY_SALARY, highest_prev + 2.0, rich_pressure + 1.0)
        return float(min(budget, target))

    if pressured and supply <= 18:
        target = max(0.82 * DAILY_SALARY, highest_prev + 1.5)
        return float(min(budget, target))

    if supply <= 16:
        target = max(0.78 * DAILY_SALARY, highest_prev + 1.2)
        return float(min(budget, target))

    if supply >= 23 and hp >= 7:
        target = min(0.28 * DAILY_SALARY, max(8.0, avg_prev * 0.18))
        return float(min(budget, target))

    if highest_prev >= 150:
        if hp >= 6 and no_water_days == 0:
            target = 0.32 * DAILY_SALARY + 10.0 * tightness
        else:
            target = max(0.74 * DAILY_SALARY, min(highest_prev * 0.55, highest_prev + 1.0))
        return float(min(budget, target))

    if highest_prev >= 100:
        if hp >= 7 and supply >= 20:
            target = 0.38 * DAILY_SALARY
        else:
            target = max(0.62 * DAILY_SALARY, highest_prev + 1.0)
        return float(min(budget, target))

    base = 24.0 + 18.0 * tightness
    if pressured:
        base += 14.0
    if day >= 8:
        base += 8.0

    target = max(base, highest_prev + 1.0 if highest_prev > 0 else base)
    target = min(target, budget)
    return float(max(0.0, target))
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) > budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply <= WATER_REQ * 1.25
    comfortable_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 2.5)
    elif no_water_days >= 1 or hp <= 4:
        bid = max(DAILY_SALARY * 0.78, highest_prev + 1.6)
    else:
        if scarcity:
            bid = max(DAILY_SALARY * 0.62, highest_prev + 1.2)
        elif comfortable_supply:
            bid = max(DAILY_SALARY * 0.38, avg_prev * 0.92)
        else:
            bid = max(DAILY_SALARY * 0.5, avg_prev + 0.8)

    if urgent_opp >= 2:
        bid += 3.0
    elif urgent_opp == 1:
        bid += 1.5

    if rich_opp >= 2 and hp > 4 and no_water_days == 0:
        bid -= 2.0

    if day >= 8:
        bid += 2.0
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        bid += 4.0

    reserve_floor = 0.0
    if day < 8:
        reserve_floor = DAILY_SALARY * (10 - day) * 0.18
    max_affordable = max(0.0, budget - reserve_floor)
    if hp <= 3 or no_water_days >= 1:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
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
    prev_bids = []
    opp_reqs = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_reqs.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if budget <= 0:
        return 0.0

    total_players = 1 + len(alive_opponents)
    total_req = WATER_REQ
    for r in opp_reqs:
        total_req += r

    scarcity_ratio = 1.0
    if total_req > 0:
        scarcity_ratio = float(supply) / float(total_req)

    severe_need = (hp <= 3) or (no_water_days >= 1)
    moderate_need = (hp <= 5)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    units_available = float(supply) / float(WATER_REQ)
    contested = units_available < float(total_players)
    very_tight = scarcity_ratio < 0.34
    loose = scarcity_ratio > 0.5

    if not alive_opponents:
        if severe_need:
            bid = 42.0
        elif moderate_need:
            bid = 28.0
        else:
            bid = 18.0
        return max(0.0, min(float(budget), bid))

    if severe_need:
        if prev_bids:
            bid = max(84.0, highest_prev + 2.25)
        else:
            bid = 82.0
        if very_tight:
            bid += 8.0
    elif very_tight or contested:
        anchor = max(avg_prev, highest_prev - 1.0)
        bid = max(68.0, anchor + 1.75)
        if hp <= 4:
            bid += 4.0
    elif loose:
        if highest_prev >= 85.0 and hp > 4:
            bid = 24.0
        else:
            bid = 46.0 if moderate_need else 34.0
    else:
        if prev_bids:
            bid = max(52.0, min(76.0, avg_prev - 3.0))
        else:
            bid = 50.0

    if day >= 8:
        bid += 4.0 if severe_need else 1.5

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if days_left > 1 and not severe_need:
        reserve_floor = min(float(budget) * 0.35, 70.0)

    max_spend = float(budget) - reserve_floor
    if severe_need:
        max_spend = float(budget)
    if max_spend < 0.0:
        max_spend = 0.0

    bid = min(bid, max_spend)
    bid = min(bid, float(budget))
    if bid < 0.0:
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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    prev_aggressive = []
    desperate_count = 0
    rich_count = 0
    total_req = WATER_REQ

    for opp in alive_opponents:
        total_req += opp.get('water_requirement', WATER_REQ)
        if opp.get('budget', 0) >= 300:
            rich_count += 1
        if opp.get('hp', 5) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = float(prev.get('bid', 0.0))
            prev_bids.append(bid)
            if bid >= DAILY_SALARY * 0.85:
                prev_aggressive.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity_ratio = supply / float(total_req) if total_req > 0 else 1.0
    very_scarce = supply < WATER_REQ * 1.6
    scarce = scarcity_ratio < 0.42 or supply < WATER_REQ * 2.0
    comfortable = scarcity_ratio > 0.6 and supply >= WATER_REQ * 2.0

    critical_me = hp <= 2 or no_water >= 1
    fragile_me = hp <= 3

    bid = 0.0

    if critical_me:
        if highest_prev > 0:
            bid = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
        else:
            bid = DAILY_SALARY * 0.9
        if very_scarce:
            bid = max(bid, DAILY_SALARY * 1.05)
    elif scarce:
        if highest_prev >= DAILY_SALARY * 0.95:
            bid = DAILY_SALARY * (0.52 if hp >= 4 else 0.88)
        elif highest_prev > 0:
            bid = max(DAILY_SALARY * 0.58, highest_prev + 1.5)
        else:
            bid = DAILY_SALARY * 0.62
        if desperate_count >= 2:
            bid += 4.0
    elif comfortable:
        if avg_prev >= DAILY_SALARY * 0.85:
            bid = DAILY_SALARY * 0.22
        elif avg_prev > 0:
            bid = min(DAILY_SALARY * 0.45, avg_prev * 0.72)
        else:
            bid = DAILY_SALARY * 0.3
    else:
        if highest_prev >= DAILY_SALARY * 0.9:
            bid = DAILY_SALARY * 0.38
        elif highest_prev > 0:
            bid = max(DAILY_SALARY * 0.48, highest_prev * 0.82)
        else:
            bid = DAILY_SALARY * 0.5

    if rich_count >= 2 and scarce:
        bid += 3.0
    if fragile_me and bid < DAILY_SALARY * 0.7:
        bid = DAILY_SALARY * 0.7

    remaining_days = max(0, 10 - day)
    reserve_target = remaining_days * DAILY_SALARY * 0.45
    max_safe = budget if budget <= reserve_target else max(DAILY_SALARY * 0.25, budget - reserve_target * 0.35)

    if critical_me:
        final_bid = min(budget, max(bid, DAILY_SALARY * 0.82))
    else:
        final_bid = min(budget, min(bid, max_safe))

    if final_bid < 0:
        final_bid = 0.0
    return float(round(final_bid, 2))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

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
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    strong_prev_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strong_high = max(strong_prev_bids) if strong_prev_bids else highest_prev

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

    if supply >= 24:
        urgency += 1
    elif supply <= 17:
        urgency -= 1

    if strong_high >= 160:
        market = 'very_high'
    elif strong_high >= 145:
        market = 'high'
    elif strong_high >= 100:
        market = 'medium'
    else:
        market = 'low'

    if urgency <= 0:
        bid = 8.0 if market in ('very_high', 'high') else 18.0
    elif urgency == 1:
        if market == 'very_high':
            bid = 18.0
        elif market == 'high':
            bid = 32.0
        else:
            bid = max(28.0, strong_high * 0.45)
    elif urgency == 2:
        if market == 'very_high':
            bid = max(42.0, strong_high * 0.38)
        elif market == 'high':
            bid = max(58.0, strong_high * 0.48)
        else:
            bid = max(46.0, strong_high + 3.0)
    elif urgency == 3:
        if market == 'very_high':
            bid = max(78.0, strong_high * 0.62)
        elif market == 'high':
            bid = max(92.0, strong_high * 0.7)
        else:
            bid = max(70.0, strong_high + 6.0)
    else:
        if market == 'very_high':
            bid = max(118.0, strong_high + 2.0)
        elif market == 'high':
            bid = max(108.0, strong_high + 4.0)
        else:
            bid = max(88.0, strong_high + 8.0)

    if supply >= 24 and urgency >= 2:
        bid += 8.0
    if supply <= 16 and urgency <= 2:
        bid *= 0.75

    max_safe = budget
    if hp > 5 and no_water_days == 0:
        max_safe = min(max_safe, budget * 0.55)
    elif hp > 3:
        max_safe = min(max_safe, budget * 0.75)

    bid = min(bid, max_safe)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_threat_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= budget * 0.8 or opp.get('hp', 0) >= hp:
                    rich_threat_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    threat_prev = max(rich_threat_bids) if rich_threat_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if no_water >= 2:
        urgency += 1.0
    elif no_water == 1:
        urgency += 0.45
    if hp <= 3:
        urgency += 0.8
    elif hp <= 6:
        urgency += 0.35
    urgency += scarcity * 0.7

    if no_water >= 2 or hp <= 2:
        bid = max(62.0, threat_prev + 2.0)
        return float(min(budget, bid))

    if supply >= 22 and hp >= 7 and no_water == 0:
        low_bid = 12.0 if threat_prev > 90 else 18.0
        return float(min(budget, low_bid))

    if threat_prev >= 145:
        if urgency < 0.9:
            return float(min(budget, 16.0 + 8.0 * scarcity))
        return float(min(budget, max(88.0, threat_prev + 1.5)))

    if threat_prev >= 110:
        if urgency < 0.6:
            return float(min(budget, 22.0 + 10.0 * scarcity))
        return float(min(budget, max(72.0, threat_prev + 1.5)))

    base = 24.0 + 26.0 * scarcity + 18.0 * urgency
    if threat_prev > 0:
        target = threat_prev + 1.5
        if urgency >= 0.55:
            base = max(base, target)
        else:
            base = max(base, min(target, 55.0))

    remaining_days = max(0, 10 - day)
    reserve = remaining_days * 12.0
    affordable = max(0.0, budget - reserve)
    if affordable <= 0:
        affordable = min(budget, 28.0 + 10.0 * urgency)

    bid = min(base, budget, max(affordable, 0.0) if affordable > 0 else budget)
    if urgency >= 0.8:
        bid = max(bid, min(budget, 58.0 + 18.0 * scarcity))

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""
