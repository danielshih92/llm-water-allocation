# ============================================================
# Experiment: exp_055
# Agent: Alex
# Source: exp_055
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

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 50)
        if supply >= 22:
            return min(budget, 18)
        return min(budget, 28)

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opponents += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0

    if hp <= 1 or no_water_days >= 2:
        base = max(60, highest_prev + 3)
    elif hp <= 2 or no_water_days >= 1:
        base = max(46, highest_prev + 2)
    else:
        if supply >= 23:
            base = 18
        elif supply >= 20:
            base = 24
        elif supply >= 17:
            base = 31
        else:
            base = 38
        if highest_prev > 0:
            base = max(base, highest_prev + 1.5)

    if urgent_opponents >= 2:
        base += 4
    elif urgent_opponents == 1:
        base += 2

    if rich_opponents >= 2:
        base += 3

    if budget < DAILY_SALARY:
        base = min(base, budget * 0.85)

    if hp >= 4 and no_water_days == 0 and supply >= 22 and highest_prev >= 55:
        base = min(base, 20)

    bid = min(budget, max(0, base))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_aggressive = 0
    desperate_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(float(bid))
                    if float(bid) >= 80 and opp.get('budget', 0) >= 500:
                        rich_aggressive += 1

    if not alive:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

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

    if tight_supply:
        urgency += 2
    elif supply <= 20:
        urgency += 1

    urgency += min(2, desperate_opp)

    if urgency >= 6:
        bid = max(92.0, highest_prev + 2.0)
    elif urgency >= 4:
        bid = max(68.0, avg_prev + 2.0, highest_prev * 0.78)
    elif urgency >= 2:
        if rich_aggressive >= 2 and hp >= 5 and no_water_days == 0 and not tight_supply:
            bid = 24.0
        else:
            bid = max(38.0, avg_prev * 0.55)
    else:
        if rich_aggressive >= 1 or highest_prev >= 90:
            bid = 18.0 if loose_supply else 22.0
        else:
            bid = 28.0 if not loose_supply else 20.0

    if day >= 8:
        bid += 8.0
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        bid += 12.0

    reserve = 0.0
    if hp >= 5 and no_water_days == 0:
        reserve = 35.0
    elif hp >= 3:
        reserve = 15.0

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    needy_count = 1
    dangerous = 0
    rich_live = 0
    max_prev_bid = 0.0
    urgent_opp = 0

    for opp in alive:
        req = opp.get('water_requirement', WATER_REQ)
        if req > 0:
            needy_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 8:
            rich_live += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev:
            pbid = prev.get('bid')
            if pbid is not None:
                max_prev_bid = max(max_prev_bid, float(pbid))
        if opp.get('budget', 0) > budget and opp.get('hp', 10) > 3:
            dangerous += 1

    expected_share = supply / float(max(1, needy_count))
    severe_shortage = supply < WATER_REQ * 1.35
    moderate_shortage = supply < WATER_REQ * 1.7
    abundant = supply >= WATER_REQ * 2.0

    survival_mode = hp <= 3 or no_water >= 1
    critical_mode = hp <= 2 or no_water >= 2

    if critical_mode:
        bid = max(DAILY_SALARY * 0.95, max_prev_bid + 2.0)
    elif survival_mode:
        if severe_shortage:
            bid = max(DAILY_SALARY * 0.82, max_prev_bid + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.68, min(max_prev_bid + 1.0, DAILY_SALARY * 0.9))
    else:
        if abundant and hp >= 6:
            bid = DAILY_SALARY * 0.18
        elif moderate_shortage:
            bid = DAILY_SALARY * 0.42
        else:
            bid = DAILY_SALARY * 0.28

        if max_prev_bid >= DAILY_SALARY * 1.2:
            bid = min(bid, DAILY_SALARY * 0.35)
        elif max_prev_bid >= DAILY_SALARY * 0.9:
            bid = max(bid, DAILY_SALARY * 0.38)
        elif max_prev_bid > 0:
            bid = max(bid, min(max_prev_bid + 1.0, DAILY_SALARY * 0.62))

    if rich_live >= 1 and not survival_mode:
        bid *= 0.92
    if dangerous >= 2 and severe_shortage:
        bid *= 1.08
    if urgent_opp >= 2 and not survival_mode:
        bid *= 0.9
    if expected_share < WATER_REQ * 0.55:
        bid *= 1.12

    if day >= 8 and hp >= 6 and not severe_shortage:
        bid *= 0.85

    reserve_floor = 0.0
    if hp > 3:
        reserve_floor = DAILY_SALARY * max(0, 10 - day) * 0.18
    max_affordable = max(0.0, budget - reserve_floor)
    if critical_mode:
        max_affordable = budget

    bid = min(bid, max_affordable)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
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

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    survival_pressure = 0.0
    if hp <= 2:
        survival_pressure += 0.55
    elif hp <= 4:
        survival_pressure += 0.3
    if no_water_days >= 2:
        survival_pressure += 0.35
    elif no_water_days >= 1:
        survival_pressure += 0.18

    market_pressure = 0.0
    if highest_prev >= DAILY_SALARY * 2.0:
        market_pressure = 0.55
    elif highest_prev >= DAILY_SALARY * 1.2:
        market_pressure = 0.4
    elif highest_prev >= DAILY_SALARY * 0.8:
        market_pressure = 0.25
    elif highest_prev > 0:
        market_pressure = 0.12

    opp_pressure = 0.04 * urgent_opp + 0.03 * rich_opp

    score = 0.18 + 0.32 * scarcity + survival_pressure + market_pressure + opp_pressure

    if day >= 8:
        score += 0.08
    if day >= 9 and hp <= 5:
        score += 0.12

    if highest_prev >= 120 and hp >= 6 and no_water_days == 0 and supply >= 20:
        score -= 0.18

    if avg_prev < 20 and hp >= 6 and no_water_days == 0:
        score -= 0.08

    if score < 0.08:
        score = 0.08
    if score > 1.45:
        score = 1.45

    bid = DAILY_SALARY * score

    if highest_prev > 0:
        if hp <= 4 or no_water_days >= 1 or supply <= 17:
            target = highest_prev + 2.0
            if bid < target:
                bid = target
        elif highest_prev >= 120 and supply >= 21:
            bid = min(bid, highest_prev * 0.72)
        else:
            soft_target = highest_prev + 1.0
            if soft_target < DAILY_SALARY * 1.15:
                bid = max(bid, soft_target)

    reserve = 0.0
    if hp <= 3:
        reserve = DAILY_SALARY * 0.2
    elif no_water_days >= 1:
        reserve = DAILY_SALARY * 0.1

    max_affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    if bid > max_affordable:
        bid = max_affordable

    if bid < 0:
        bid = 0.0

    return float(min(budget, bid))
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

    alive = []
    prev_bids = []
    dangerous_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= bid * 0.6:
                    dangerous_bids.append(float(bid))

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.25)
        if hp <= 2 or no_water_days >= 2:
            safe_bid = min(budget, DAILY_SALARY * 0.6)
        return max(0.0, float(safe_bid))

    high_pressure = max(prev_bids) if prev_bids else DAILY_SALARY * 0.6
    effective_pressure = max(dangerous_bids) if dangerous_bids else high_pressure

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.5
    elif hp <= 4:
        urgency += 0.3
    if no_water_days >= 2:
        urgency += 0.4
    elif no_water_days >= 1:
        urgency += 0.2
    if day >= 8:
        urgency += 0.1
    urgency += scarcity * 0.25
    if urgency > 1.0:
        urgency = 1.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.9, effective_pressure + 2.0)
    elif scarcity >= 0.7:
        bid = max(DAILY_SALARY * 0.62, effective_pressure + 1.5)
    elif scarcity >= 0.4:
        bid = max(DAILY_SALARY * 0.48, effective_pressure * 0.72)
    else:
        bid = max(DAILY_SALARY * 0.28, effective_pressure * 0.5)

    if effective_pressure >= 120 and hp >= 5 and no_water_days == 0 and supply >= 20:
        bid = DAILY_SALARY * 0.22

    reserve_days = 3 if hp >= 4 else 2
    reserve = reserve_days * DAILY_SALARY
    affordable = budget - reserve
    if affordable < DAILY_SALARY * 0.2:
        affordable = budget * (0.55 + 0.35 * urgency)

    bid = min(bid, affordable)
    bid = min(bid, budget)

    floor_bid = 0.0
    if hp <= 3 or no_water_days >= 1:
        floor_bid = DAILY_SALARY * 0.35
    if scarcity >= 0.7:
        floor_bid = max(floor_bid, DAILY_SALARY * 0.42)
    if hp <= 2 or no_water_days >= 2:
        floor_bid = max(floor_bid, DAILY_SALARY * 0.75)

    bid = max(bid, floor_bid)
    bid = min(bid, budget)

    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80:
                    aggressive_count += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if supply_tight:
        urgency += 2
    elif supply_loose:
        urgency -= 1
    if desperate_count >= 2:
        urgency += 1

    if urgency >= 7:
        target = max(95.0, highest_prev + 6.0)
    elif urgency >= 5:
        target = max(72.0, highest_prev + 2.5 if highest_prev < 120 else 78.0)
    elif urgency >= 3:
        if highest_prev >= 160:
            target = 26.0 if hp > 4 else 74.0
        elif highest_prev >= 90:
            target = highest_prev + 1.5
        else:
            target = max(48.0, avg_prev + 3.0)
    else:
        if highest_prev >= 150:
            target = 12.0
        elif highest_prev >= 100:
            target = 22.0
        elif highest_prev >= 70:
            target = 38.0
        else:
            target = 30.0 if supply_loose else 42.0

    if day >= 8:
        target += 8.0
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        target += 12.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve_floor = DAILY_SALARY * 0.5

    max_affordable = budget - reserve_floor
    if max_affordable < 0:
        max_affordable = budget * 0.6

    bid = min(target, budget, max_affordable if max_affordable > 0 else budget)

    if urgency >= 5:
        bid = min(max(bid, 70.0), budget)
    elif hp > 6 and no_water_days == 0 and aggressive_count >= 2 and highest_prev >= 150:
        bid = min(budget, 10.0)

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
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    aggressive_count = 0
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid_y = prev.get('bid')
        if bid_y is not None:
            prev_bids.append(float(bid_y))
            if bid_y >= DAILY_SALARY * 1.1:
                aggressive_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (25.0 - float(supply)) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water >= 2:
        urgency += 0.8
    elif no_water >= 1:
        urgency += 0.45

    urgency += scarcity * 0.35
    urgency += desperate_count * 0.08

    if hp >= 7 and no_water == 0 and aggressive_count >= 1:
        base_bid = DAILY_SALARY * (0.18 + 0.10 * scarcity)
    else:
        base_bid = DAILY_SALARY * (0.28 + urgency)

    if highest_prev >= 100 and hp > 4 and no_water == 0:
        base_bid = min(base_bid, DAILY_SALARY * 0.32)
    elif highest_prev > 0 and highest_prev < 60 and urgency > 0.35:
        base_bid = max(base_bid, highest_prev + 2.0)
    elif avg_prev > 0 and avg_prev < 50 and urgency > 0.2:
        base_bid = max(base_bid, avg_prev + 1.5)

    if day >= 8 and hp <= 4:
        base_bid += 8.0

    reserve = DAILY_SALARY * 1.2 if day < 8 else DAILY_SALARY * 0.5
    max_affordable = max(0.0, budget - reserve)
    if hp <= 3 or no_water >= 1:
        max_affordable = budget

    bid = min(base_bid, max_affordable if max_affordable > 0 else budget)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.92))
    elif hp <= 4 and no_water >= 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.72))

    if bid < 0:
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    opp_signals = []
    urgent_count = 0
    rich_urgent_bids = []
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is None:
            prev_bid = 0.0
        opp_hp = opp.get('hp', 10)
        opp_budget = opp.get('budget', 0)
        opp_nowater = opp.get('no_water_days', 0)
        opp_req = opp.get('water_requirement', WATER_REQ)
        opp_salary = opp.get('daily_salary', DAILY_SALARY)

        urgency = 0.0
        if opp_hp <= 3:
            urgency += 2.5
        elif opp_hp <= 5:
            urgency += 1.2
        if opp_nowater >= 1:
            urgency += 1.5
        if opp_budget > opp_salary * 4:
            urgency += 0.5
        if prev_bid >= 120:
            urgency += 1.0
        elif prev_bid >= 90:
            urgency += 0.5

        signal = prev_bid + urgency * 8.0
        opp_signals.append(signal)
        if urgency >= 2.0:
            urgent_count += 1
            rich_urgent_bids.append(prev_bid)

    highest_signal = max(opp_signals) if opp_signals else 0.0
    highest_prev = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid')
        if b is not None and b > highest_prev:
            highest_prev = b

    tight_supply = supply <= 17.0
    medium_supply = supply <= 20.0

    my_urgency = 0
    if hp <= 2:
        my_urgency += 3
    elif hp <= 4:
        my_urgency += 2
    elif hp <= 6:
        my_urgency += 1
    if no_water_days >= 1:
        my_urgency += 2

    if my_urgency >= 4:
        base = max(110.0, highest_prev + 6.0)
        if tight_supply:
            base = max(base, highest_signal + 6.0)
        return float(min(budget, base))

    if my_urgency >= 2:
        if tight_supply:
            base = max(78.0, highest_prev + 3.0)
        else:
            base = max(62.0, min(highest_prev + 1.5, 95.0))
        return float(min(budget, base))

    if tight_supply:
        if urgent_count >= 2:
            base = min(highest_signal + 2.0, 92.0)
        else:
            base = min(max(48.0, highest_prev * 0.62), 78.0)
    elif medium_supply:
        if highest_prev >= 120:
            base = 34.0
        elif highest_prev >= 90:
            base = 42.0
        else:
            base = 50.0
    else:
        if day <= 2:
            base = 28.0
        else:
            base = 22.0

    if budget < DAILY_SALARY * 2:
        base = min(base, 36.0)
    elif budget > DAILY_SALARY * 8 and hp <= 5 and medium_supply:
        base = max(base, 58.0)

    return float(min(budget, max(0.0, base)))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    reqs = [WATER_REQ]
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            reqs.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    b = float(prev.get('bid', 0))
                    if b >= 0:
                        prev_bids.append(b)
                except Exception:
                    pass

    total_req = sum(reqs)
    scarcity = total_req / max(supply, 1.0)
    tight_supply = supply <= 17.0
    abundant_supply = supply >= 22.0

    if not alive:
        if hp <= 3 or no_water_days >= 2:
            return max(0.0, min(budget, DAILY_SALARY * 0.75))
        return max(0.0, min(budget, DAILY_SALARY * 0.2))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    emergency = hp <= 3 or no_water_days >= 2
    caution = hp <= 5 or no_water_days >= 1

    if emergency:
        bid = max(DAILY_SALARY * 1.05, highest_prev + 3.0)
    elif tight_supply or scarcity > 2.6:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif caution:
        bid = max(DAILY_SALARY * 0.72, avg_prev + 1.5)
    elif abundant_supply and highest_prev >= DAILY_SALARY * 1.6:
        bid = DAILY_SALARY * 0.28
    elif abundant_supply:
        bid = DAILY_SALARY * 0.42
    else:
        bid = max(DAILY_SALARY * 0.52, min(highest_prev + 1.0, DAILY_SALARY * 0.88))

    if day >= 8 and hp >= 6 and no_water_days == 0 and budget < DAILY_SALARY * 2.2:
        bid = min(bid, DAILY_SALARY * 0.45)

    if budget <= DAILY_SALARY * 0.6:
        if emergency:
            bid = budget
        else:
            bid = min(bid, budget * 0.75)

    bid = max(0.0, min(budget, bid))
    return bid
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        base = 18.0 if hp > 3 else 42.0
        return max(0.0, min(budget, base))

    total_req = WATER_REQ
    for _, opp in alive:
        total_req += opp.get('water_requirement', WATER_REQ)

    scarcity = supply / float(total_req) if total_req > 0 else 1.0

    prev_bids = []
    dangerous_prev = 0.0
    cindy_prev = None
    desperate_count = 0
    rich_count = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
            if float(pbid) > dangerous_prev:
                dangerous_prev = float(pbid)
        if oid == 'Cindy' and pbid is not None:
            cindy_prev = float(pbid)
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            desperate_count += 1
        if opp.get('budget', 0) >= 500:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
        urgency += 2

    if scarcity < 0.34:
        urgency += 2
    elif scarcity < 0.5:
        urgency += 1

    if desperate_count >= 2:
        urgency += 1

    if cindy_prev is not None and cindy_prev >= 110 and hp > 4 and no_water == 0 and scarcity < 0.45:
        return max(0.0, min(budget, 8.0))

    if urgency <= 1:
        bid = 14.0
        if scarcity > 0.42:
            bid = 10.0
        if highest_prev <= 20:
            bid = max(bid, highest_prev + 1.0)
    elif urgency == 2:
        bid = max(26.0, avg_prev + 3.0)
        if highest_prev > 80:
            bid = 38.0
    elif urgency == 3:
        bid = max(42.0, highest_prev + 2.0)
        if cindy_prev is not None and cindy_prev >= 120 and hp > 3:
            bid = 46.0
    elif urgency == 4:
        bid = max(58.0, highest_prev + 3.0)
        if rich_count >= 1:
            bid += 4.0
    else:
        bid = max(74.0, highest_prev + 5.0)
        if cindy_prev is not None and cindy_prev >= 120:
            bid = max(bid, 88.0)

    if day >= 8 and hp > 4 and budget < 140:
        bid *= 0.8

    if budget < DAILY_SALARY:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, 0.95 * DAILY_SALARY + max(0, no_water - 1) * 8.0)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, 63.0))

    return max(0.0, float(bid))
"""
