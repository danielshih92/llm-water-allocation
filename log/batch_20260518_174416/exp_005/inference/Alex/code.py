# ============================================================
# Experiment: exp_005
# Agent: Alex
# Source: exp_005
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
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    total_alive = 1 + len(alive_opponents)
    expected_need = total_alive * WATER_REQ
    scarcity_ratio = 0.0
    if expected_need > 0:
        scarcity_ratio = max(0.0, min(1.0, (expected_need - supply) / float(expected_need)))

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.96
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.82
    else:
        base = DAILY_SALARY * (0.42 + 0.35 * scarcity_ratio)

    if supply >= total_alive * WATER_REQ:
        base *= 0.82
    elif supply <= max(WATER_REQ, total_alive * WATER_REQ * 0.7):
        base *= 1.12

    if highest_prev > 0:
        target = max(highest_prev + 1.5, avg_prev + 1.0)
        if hp > 4 and no_water_days == 0 and highest_prev >= DAILY_SALARY * 0.9:
            base = min(base, DAILY_SALARY * 0.45)
        else:
            base = max(base, target)

    if urgent_opponents >= max(1, len(alive_opponents) // 2):
        base += 3.0
    if rich_opponents >= max(1, len(alive_opponents) // 2):
        base += 2.0

    if not alive_opponents:
        base = DAILY_SALARY * 0.35 if hp > 3 else DAILY_SALARY * 0.75

    reserve = 0
    days_left_est = max(1, 10 - int(day_context['day']))
    if hp > 3:
        reserve = min(budget * 0.4, days_left_est * 8)

    bid = min(budget - reserve, base)
    if hp <= 3 or no_water_days >= 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.78))

    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget
    return float(round(bid, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    urgent_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 6:
                rich_threat += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.35)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgent = hp <= 3 or no_water_days >= 1
    very_urgent = hp <= 2 or no_water_days >= 2

    if very_urgent:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
        return min(budget, bid)

    if my_urgent:
        base = DAILY_SALARY * (0.78 + 0.12 * scarcity)
        bid = max(base, highest_prev + 1.0 if highest_prev > 0 else base)
        return min(budget, bid)

    if supply >= 22:
        bid = DAILY_SALARY * 0.18
    elif supply >= 19:
        bid = DAILY_SALARY * 0.28
    elif supply >= 17:
        bid = DAILY_SALARY * 0.42
    else:
        bid = DAILY_SALARY * 0.62

    if highest_prev >= DAILY_SALARY * 1.4:
        bid *= 0.75
    elif highest_prev >= DAILY_SALARY * 1.1:
        bid *= 0.85
    elif highest_prev >= DAILY_SALARY * 0.85 and supply <= 17:
        bid = max(bid, DAILY_SALARY * 0.55)
    elif highest_prev > 0 and supply <= 16:
        bid = max(bid, min(highest_prev + 1.5, DAILY_SALARY * 0.9))

    if rich_threat >= 2 and supply >= 19:
        bid *= 0.85
    if urgent_opp >= 1 and supply <= 17:
        bid *= 1.08

    if avg_prev > 0 and avg_prev < DAILY_SALARY * 0.6 and supply <= 16:
        bid = max(bid, avg_prev + 2.0)

    reserve_floor = DAILY_SALARY * 1.2 if hp > 4 else DAILY_SALARY * 0.6
    if budget <= reserve_floor:
        bid = min(bid, DAILY_SALARY * 0.45)

    if bid < 0:
        bid = 0.0
    return min(budget, bid)
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 20.0))

    prev_bids = []
    efficient_prev = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('daily_salary', 0) <= 70 and bid <= 130:
                efficient_prev.append(float(bid))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1

    max_prev = max(prev_bids) if prev_bids else 0.0
    eff_anchor = max(efficient_prev) if efficient_prev else 95.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    if hp <= 2 or no_water_days >= 2:
        bid = max(150.0, max_prev + 6.0, eff_anchor + 8.0)
    elif hp <= 4 or no_water_days >= 1:
        if tight_supply:
            bid = max(125.0, eff_anchor + 4.0, max_prev * 0.92)
        else:
            bid = max(105.0, eff_anchor + 2.0)
    else:
        if tight_supply:
            bid = max(98.0, eff_anchor + 3.0)
        elif medium_supply:
            bid = max(78.0, min(110.0, eff_anchor - 6.0))
        else:
            bid = 42.0

    if desperate_count >= 2 and tight_supply:
        bid += 10.0
    elif desperate_count == 0 and supply >= 22:
        bid -= 8.0

    if rich_count >= 2 and hp <= 4:
        bid += 8.0

    if day >= 8:
        bid += 6.0
    if day == 10:
        bid += 10.0

    min_safe_reserve = max(0.0, (10 - day) * 18.0)
    cap = budget - min_safe_reserve
    if hp <= 3 or no_water_days >= 1:
        cap = budget
    if cap < 0:
        cap = budget * 0.5

    final_bid = min(float(budget), float(cap), float(bid))
    if final_bid < 0:
        final_bid = 0.0
    return float(final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_fixed_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0.0)
                prev_bids.append(b)
                if b >= 130:
                    rich_fixed_count += 1

    if not alive:
        return float(min(budget, 12.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    likely_units = int(supply / WATER_REQ)
    my_urgent = hp <= 2 or no_water >= 2
    caution = hp <= 4 or no_water >= 1

    if my_urgent:
        target = max(92.0, highest_prev + 2.0)
        if rich_fixed_count > 0:
            target = max(target, 136.0)
        return float(min(budget, target))

    if likely_units >= 2:
        if highest_prev >= 130:
            target = 41.0 if hp > 5 else 58.0
        elif highest_prev >= 85:
            target = 52.0 if hp > 5 else 67.0
        else:
            target = 38.0 if hp > 6 else 50.0
        if desperate_count >= 2:
            target += 8.0
        return float(min(budget, target))

    target = 0.0
    if rich_fixed_count > 0:
        if caution:
            target = 136.0
        else:
            target = 18.0
    else:
        if highest_prev >= 100:
            target = 24.0 if hp > 5 else 88.0
        elif highest_prev >= 70:
            target = highest_prev + 3.0 if caution else 33.0
        elif avg_prev > 0:
            target = max(36.0, avg_prev + 4.0)
        else:
            target = 42.0

    if desperate_count >= 2 and target < 80.0:
        target += 10.0

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(target)
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

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('budget', 0) > 300:
                if bid is not None and float(bid) >= 80:
                    rich_aggressive += 1

    if not alive_opponents:
        return max(0.0, min(float(budget), 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    emergency = False
    if hp <= 2 or no_water_days >= 2:
        emergency = True
    elif hp <= 4 and no_water_days >= 1:
        emergency = True

    if emergency:
        target = max(65.0, highest_prev + 2.5)
        if rich_aggressive >= 2:
            target = max(target, 92.0)
        if scarcity == 2:
            target += 8.0
        elif scarcity == 1:
            target += 4.0
        return max(0.0, min(float(budget), target))

    if hp >= 7 and no_water_days == 0:
        if highest_prev >= 100:
            target = 8.0 if supply >= 20 else 12.0
        elif highest_prev >= 60:
            target = 14.0 if supply >= 20 else 18.0
        else:
            target = 18.0 if supply >= 20 else 24.0
        return max(0.0, min(float(budget), target))

    target = 0.0
    if highest_prev >= 110:
        target = 20.0
    elif highest_prev >= 80:
        target = 26.0
    elif highest_prev >= 40:
        target = highest_prev + 1.5
    else:
        target = max(24.0, avg_prev + 3.0)

    if scarcity == 2:
        target += 8.0
    elif scarcity == 1:
        target += 4.0

    if hp <= 5:
        target += 8.0
    if no_water_days >= 1:
        target += 10.0
    if day >= 8 and hp <= 6:
        target += 6.0

    return max(0.0, min(float(budget), float(target)))
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    max_prev_bid = 0.0
    cindy_prev_bid = None
    desperate_opp = False
    zero_bid_opp_count = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            if bid > max_prev_bid:
                max_prev_bid = bid
            if bid == 0:
                zero_bid_opp_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp = True
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if bid is not None and bid > 100:
                cindy_prev_bid = bid

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    if hp <= 2:
        bid = 92.0
    elif no_water_days >= 2:
        bid = 88.0
    elif hp <= 4:
        bid = 62.0 if supply <= 18 else 48.0
    else:
        if supply >= 22:
            bid = 8.0
        elif supply >= 19:
            bid = 14.0
        else:
            bid = 24.0

        if cindy_prev_bid is not None:
            if cindy_prev_bid >= 170:
                bid = min(bid, 16.0)
            elif cindy_prev_bid >= 140:
                bid = max(bid, 20.0)

        if max_prev_bid <= 1.0 and zero_bid_opp_count >= 2:
            bid = min(bid, 10.0)

        if desperate_opp and supply <= 18:
            bid = max(bid, 36.0)

        if hp == 5:
            bid = max(bid, 26.0)

    if budget < bid:
        bid = budget

    min_guard = 0.0
    if hp <= 3 or no_water_days >= 1:
        min_guard = min(budget, 35.0)
        bid = max(bid, min_guard)

    return float(max(0.0, min(budget, bid)))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            if opp.get('budget', 0) >= budget:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    max_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.7
    sorted_prev = sorted(prev_bids) if prev_bids else [DAILY_SALARY * 0.7]
    second_prev = sorted_prev[-2] if len(sorted_prev) >= 2 else sorted_prev[-1]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.7

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = hp <= 2 or no_water_days >= 2
    fragile = hp <= 4 or no_water_days >= 1

    if urgent:
        bid = max(max_prev + 3.0, DAILY_SALARY * (0.95 + 0.15 * scarcity))
    elif fragile:
        bid = max(second_prev + 2.0, avg_prev * (0.9 + 0.15 * scarcity), DAILY_SALARY * (0.72 + 0.18 * scarcity))
    else:
        if max_prev >= DAILY_SALARY * 1.3:
            bid = DAILY_SALARY * (0.28 + 0.18 * scarcity)
        elif max_prev >= DAILY_SALARY * 1.0:
            bid = DAILY_SALARY * (0.4 + 0.2 * scarcity)
        else:
            bid = max(DAILY_SALARY * (0.48 + 0.18 * scarcity), second_prev + 1.0)

    if desperate_count >= 2:
        bid += 6.0 + 6.0 * scarcity
    elif desperate_count == 1:
        bid += 3.0 * scarcity

    if rich_count >= 2 and not urgent:
        bid -= 2.0

    if day <= 2 and not urgent:
        bid *= 0.92
    if day >= 8 and fragile:
        bid *= 1.08

    reserve_floor = 0.0
    if hp > 4 and day < 8:
        reserve_floor = DAILY_SALARY * 2.0
    max_affordable = max(0.0, budget - reserve_floor)

    if urgent:
        final_bid = min(budget, max(bid, DAILY_SALARY * 0.9))
    else:
        if max_affordable > 0:
            final_bid = min(max_affordable, bid)
        else:
            final_bid = min(budget, DAILY_SALARY * 0.35)

    if final_bid < 0:
        final_bid = 0.0
    if final_bid > budget:
        final_bid = budget

    return float(final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(max(0.0, min(budget, 18.0)))

    yesterday_bids = []
    urgent_pressure = 0.0
    rich_aggressive = 0
    weak_opponents = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            yesterday_bids.append(float(pbid))
            if float(pbid) >= 80:
                urgent_pressure = max(urgent_pressure, float(pbid))
        if opp.get('budget', 0) >= 300 and opp.get('hp', 0) >= 6:
            rich_aggressive += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            weak_opponents += 1

    max_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    units = supply / WATER_REQ
    contested = units < 2.0
    abundant = units >= 2.0

    danger = hp <= 2 or no_water >= 2
    caution = hp <= 4 or no_water >= 1

    if danger:
        bid = max(78.0, max_prev + 3.0)
    elif contested:
        if max_prev >= 110:
            bid = 44.0 if hp >= 5 and no_water == 0 else 92.0
        elif max_prev >= 80:
            bid = 58.0 if hp >= 6 and no_water == 0 else max_prev + 2.0
        else:
            bid = 52.0 + 4.0 * rich_aggressive
    else:
        if caution:
            bid = max(36.0, min(72.0, avg_prev * 0.7 + 6.0))
        else:
            bid = 24.0 + 3.0 * rich_aggressive
            if weak_opponents >= 1:
                bid -= 4.0

    if hp >= 7 and no_water == 0 and abundant and max_prev >= 100:
        bid = min(bid, 28.0)

    if budget < bid:
        bid = budget

    reserve_floor = 12.0 if danger else 6.0
    if budget <= reserve_floor:
        bid = budget

    if bid < 0:
        bid = 0.0

    return float(round(min(budget, bid), 2))
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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    slots = supply / WATER_REQ
    severe_scarcity = slots < 1.0
    tight_scarcity = slots < 2.0

    prev_bids = []
    desperate_opp = 0
    broke_soon_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp += 1
        if opp.get('budget', 0) < DAILY_SALARY * 1.2:
            broke_soon_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    if hp <= 2 or no_water >= 2:
        emergency = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
        if severe_scarcity:
            emergency = max(emergency, DAILY_SALARY * 1.15)
        return float(min(budget, emergency))

    if hp <= 4 or no_water >= 1:
        urgent = max(DAILY_SALARY * 0.78, avg_prev + 3.0)
        if tight_scarcity:
            urgent = max(urgent, highest_prev + 2.0)
        return float(min(budget, urgent))

    if severe_scarcity:
        bid = DAILY_SALARY * 0.82
        if highest_prev > 0:
            bid = max(bid, highest_prev + 1.0)
        if desperate_opp >= 2:
            bid += 4.0
        return float(min(budget, bid))

    if tight_scarcity:
        if highest_prev >= 100:
            bid = DAILY_SALARY * 0.42
        else:
            bid = max(DAILY_SALARY * 0.52, min(DAILY_SALARY * 0.78, highest_prev + 1.5))
        if broke_soon_opp >= 2:
            bid -= 4.0
        return float(max(0.0, min(budget, bid)))

    if highest_prev >= 110:
        bid = DAILY_SALARY * 0.28
    elif highest_prev >= 85:
        bid = DAILY_SALARY * 0.38
    elif highest_prev > 0:
        bid = max(DAILY_SALARY * 0.45, min(DAILY_SALARY * 0.68, highest_prev + 1.0))
    else:
        bid = DAILY_SALARY * 0.48

    if day >= 8 and hp >= 5:
        bid *= 0.92

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
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    pressure_bid = 0.0
    cindy_bid = None
    starving_threats = 0
    rich_threats = 0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = prev.get('bid') if prev else None
        if pbid is not None:
            if pbid > pressure_bid:
                pressure_bid = pbid
            if agent_id == 'Cindy':
                cindy_bid = pbid
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 3:
            starving_threats += 1
        if opp.get('budget', 0) >= budget * 0.9:
            rich_threats += 1

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    base = DAILY_SALARY * 0.42

    if tight_supply:
        base = DAILY_SALARY * 0.72
    elif medium_supply:
        base = DAILY_SALARY * 0.56

    if hp <= 2 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.68)

    if cindy_bid is not None:
        if cindy_bid >= 180:
            if hp > 4 and not tight_supply:
                base = min(base, DAILY_SALARY * 0.38)
            else:
                base = max(base, DAILY_SALARY * 0.88)
        elif cindy_bid >= 130:
            base = max(base, min(DAILY_SALARY * 0.82, cindy_bid * 0.62))
        else:
            base = max(base, cindy_bid + 3.0)
    elif pressure_bid > 0:
        if pressure_bid >= 100:
            if hp > 4 and not tight_supply:
                base = min(base, DAILY_SALARY * 0.4)
            else:
                base = max(base, DAILY_SALARY * 0.8)
        else:
            base = max(base, pressure_bid + 2.0)

    if starving_threats >= 2 and hp > 3 and not tight_supply:
        base *= 0.9
    if rich_threats >= 2 and medium_supply:
        base *= 1.08

    if day >= 8:
        if hp <= 4:
            base = max(base, DAILY_SALARY * 0.82)
        else:
            base = max(base, DAILY_SALARY * 0.58)

    bid = min(budget, base)
    if budget <= DAILY_SALARY * 0.6 and hp > 3 and not tight_supply:
        bid = min(bid, budget * 0.75)

    if bid < 0:
        bid = 0.0
    return float(bid)
"""
