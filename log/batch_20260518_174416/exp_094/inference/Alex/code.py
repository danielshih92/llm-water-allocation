# ============================================================
# Experiment: exp_094
# Agent: Alex
# Source: exp_094
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    supply = day_context['supply']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    if not alive:
        base = DAILY_SALARY * 0.22
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.55
        return min(budget, max(0, base))

    total_players = 1 + len(alive)
    supply_ratio = float(supply) / float(WATER_REQ * total_players)

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 3:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

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

    if supply_ratio < 0.9:
        urgency += 2
    elif supply_ratio < 1.1:
        urgency += 1

    if desperate_opp > 0:
        urgency += 1

    if urgency >= 6:
        target = max(DAILY_SALARY * 0.92, highest_prev + 2)
    elif urgency >= 4:
        target = max(DAILY_SALARY * 0.72, avg_prev + 2, highest_prev * 0.9)
    elif urgency >= 2:
        target = max(DAILY_SALARY * 0.5, avg_prev + 1)
    else:
        if supply_ratio >= 1.25:
            target = DAILY_SALARY * 0.24
        elif supply_ratio >= 1.0:
            target = DAILY_SALARY * 0.34
        else:
            target = DAILY_SALARY * 0.46

    if rich_opp >= max(1, len(alive) // 2) and urgency < 4:
        target *= 0.92

    days_left_including_today = max(1, 10 - int(day_context['day']) + 1)
    soft_cap = budget / days_left_including_today * 1.35
    hard_cap = max(DAILY_SALARY * 0.98, soft_cap)

    bid = min(target, budget, hard_cap)
    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9, highest_prev + 2))

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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    affordable_prev_bids = []
    urgent_count = 0
    rich_threat = 0
    cindy_like_bid = 0.0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('budget', 0) >= float(bid):
                affordable_prev_bids.append(float(bid))
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 0) <= 2:
            urgent_count += 1
        if opp.get('budget', 0) >= 700:
            rich_threat += 1
        if bid is not None and float(bid) >= 110:
            cindy_like_bid = max(cindy_like_bid, float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_affordable = max(affordable_prev_bids) if affordable_prev_bids else highest_prev

    scarcity = (supply <= 17)
    abundance = (supply >= 22)
    danger = (hp <= 2 or no_water_days >= 2)
    caution = (hp <= 4 or no_water_days >= 1)

    target = DAILY_SALARY * 0.42

    if abundance and not caution:
        target = DAILY_SALARY * 0.28
    elif scarcity:
        target = DAILY_SALARY * 0.78
    else:
        target = DAILY_SALARY * 0.5

    if highest_affordable > 0:
        if scarcity or danger:
            target = max(target, highest_affordable + 2.0)
        else:
            target = max(target, min(highest_affordable + 1.0, DAILY_SALARY * 0.72))

    if cindy_like_bid >= 110 and not danger:
        target = min(target, DAILY_SALARY * 0.62)

    if rich_threat >= 1 and scarcity:
        target = max(target, DAILY_SALARY * 0.82)

    if urgent_count >= 2 and not danger:
        target = min(target, DAILY_SALARY * 0.55)

    if danger:
        target = max(target, DAILY_SALARY * 0.92)
    elif caution and scarcity:
        target = max(target, DAILY_SALARY * 0.8)

    if day >= 8:
        if hp >= 6 and no_water_days == 0:
            target = min(target, DAILY_SALARY * 0.58)
        else:
            target = max(target, DAILY_SALARY * 0.88)

    reserve_days = 2 if day < 8 else 1
    reserve = reserve_days * DAILY_SALARY * 0.55
    spendable = budget - reserve
    if spendable < 0:
        spendable = budget * 0.6

    bid = min(target, budget)
    if not danger:
        bid = min(bid, max(0.0, spendable))
        if bid <= 0:
            bid = min(budget, DAILY_SALARY * 0.22)

    if budget < DAILY_SALARY * 0.5:
        bid = min(bid, budget)
    if danger:
        bid = min(max(bid, min(budget, DAILY_SALARY * 0.92)), budget)

    if bid < 0:
        bid = 0.0
    return float(bid)
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0

    alive = []
    prev_bids = []
    dangerous_affordable = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= bid * 0.8:
                    dangerous_affordable.append(float(bid))

    if not alive:
        return min(budget, 20)

    competitors = len(alive) + 1
    expected_share = supply / float(competitors)
    scarcity = WATER_REQ / max(1.0, expected_share)

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.45
    if day >= 8:
        urgency += 0.2

    base = DAILY_SALARY * 0.42
    if scarcity > 1.35:
        base = DAILY_SALARY * 0.9
    elif scarcity > 1.1:
        base = DAILY_SALARY * 0.68
    elif scarcity < 0.8:
        base = DAILY_SALARY * 0.28

    if dangerous_affordable:
        target = max(dangerous_affordable)
    elif prev_bids:
        target = max(prev_bids)
    else:
        target = DAILY_SALARY * 0.5

    if urgency >= 1.5:
        bid = max(base, min(target + 2.0, DAILY_SALARY * 1.55))
    elif urgency >= 0.7:
        bid = max(base, min(target * 0.82 + 3.0, DAILY_SALARY * 1.15))
    else:
        if scarcity < 0.9:
            bid = min(base, DAILY_SALARY * 0.35)
        else:
            bid = max(base, min(target * 0.62 + 2.0, DAILY_SALARY * 0.9))

    if budget < DAILY_SALARY * 0.6 and urgency < 1.0:
        bid = min(bid, budget * 0.55)
    elif budget < DAILY_SALARY and urgency < 1.5:
        bid = min(bid, budget * 0.75)

    if hp <= 1 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 1.2))

    if day == 1 and supply >= 22:
        bid = min(bid, DAILY_SALARY * 0.3)

    bid = max(0.0, min(float(budget), float(bid)))
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
        return float(min(budget, max(1.0, DAILY_SALARY * 0.35)))

    opp_bids = []
    credible_bids = []
    stressed_count = 0
    desperate_count = 0
    rich_aggressive_count = 0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is not None:
            opp_bids.append(float(prev_bid))
            if opp['budget'] >= float(prev_bid) * 0.8:
                credible_bids.append(float(prev_bid))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            stressed_count += 1
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= 700 and prev_bid is not None and float(prev_bid) >= 90:
            rich_aggressive_count += 1

    highest_prev = max(opp_bids) if opp_bids else 0.0
    highest_credible = max(credible_bids) if credible_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.8
    elif hp <= 4:
        urgency += 0.45
    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days >= 1:
        urgency += 0.35
    if day >= 8:
        urgency += 0.15
    if urgency > 1.2:
        urgency = 1.2

    target = DAILY_SALARY * (0.42 + 0.28 * scarcity + 0.22 * min(1.0, urgency))

    if supply <= 17:
        target = max(target, highest_credible + 2.5)
    elif supply <= 20:
        target = max(target, highest_credible + 1.0)
    else:
        target = max(target, min(highest_credible, DAILY_SALARY * 1.05) * 0.9)

    if stressed_count >= 2 and urgency < 0.5 and supply >= 20:
        target *= 0.82

    if desperate_count >= 2 and (hp <= 4 or no_water_days >= 1):
        target = max(target, highest_credible + 3.0)

    if rich_aggressive_count >= 1 and supply <= 18:
        target = max(target, highest_credible + 4.0)

    if hp >= 7 and no_water_days == 0 and supply >= 22 and highest_prev >= 95:
        target *= 0.72

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.95)

    max_safe = budget
    if day < 10:
        reserve = max(0.0, (10 - day) * DAILY_SALARY * 0.18)
        max_safe = max(0.0, budget - reserve)
        if hp <= 3 or no_water_days >= 1:
            max_safe = budget

    if max_safe <= 0:
        max_safe = min(budget, DAILY_SALARY * 0.4)

    bid = min(target, max_safe)
    bid = max(0.0, min(bid, budget))

    if bid < 1.0 and budget >= 1.0:
        bid = 1.0

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > strong_prev:
                    strong_prev = float(bid)

    if not alive:
        return max(0.0, min(budget, 8.0))

    contested = supply < WATER_REQ * 2
    danger = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        target = max(92.0, strong_prev + 2.0)
    elif contested and danger:
        target = max(82.0, strong_prev + 1.5)
    elif contested:
        if strong_prev >= 120.0:
            target = 36.0 if hp >= 5 and no_water == 0 else 88.0
        elif strong_prev >= 90.0:
            target = 68.0 if hp >= 5 and no_water == 0 else 84.0
        else:
            target = max(58.0, strong_prev + 1.5)
    else:
        if danger:
            target = max(60.0, strong_prev * 0.8 if strong_prev > 0 else 60.0)
        else:
            target = 22.0 if strong_prev >= 90.0 else 34.0

    if budget < target:
        if critical:
            return max(0.0, budget)
        return max(0.0, min(budget, max(12.0, budget * 0.7)))

    return max(0.0, min(budget, float(target)))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_threat += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return float(min(budget, 8.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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
    elif supply <= 19:
        urgency += 1

    if desperate_count >= 2:
        urgency += 1

    if day >= 8 and hp < 8:
        urgency += 1

    if highest_prev >= 120:
        market_mode = 'very_high'
    elif highest_prev >= 85:
        market_mode = 'high'
    elif highest_prev >= 40:
        market_mode = 'medium'
    else:
        market_mode = 'low'

    if urgency >= 6:
        bid = 92.0 if market_mode in ('very_high', 'high') else 72.0
    elif urgency >= 4:
        bid = 62.0 if market_mode == 'very_high' else 48.0
    elif urgency >= 2:
        if loose_supply and market_mode in ('high', 'very_high'):
            bid = 12.0
        else:
            bid = 24.0 if market_mode in ('high', 'very_high') else 18.0
    else:
        if loose_supply:
            bid = 6.0
        elif market_mode in ('high', 'very_high'):
            bid = 10.0
        else:
            bid = 14.0

    if highest_prev > 0 and highest_prev < 35 and urgency >= 3:
        bid = max(bid, highest_prev + 2.5)

    if avg_prev > 90 and urgency <= 2:
        bid = min(bid, 14.0)

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0:
        keep_reserve = reserve_days * 8.0
        soft_cap = max(0.0, budget - keep_reserve)
        if urgency >= 5:
            soft_cap = budget

    if soft_cap <= 0:
        bid = min(bid, budget * 0.5)
    else:
        bid = min(bid, soft_cap)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 95.0))

    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    low_fixed = []
    high_spenders = []
    desperate_count = 0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid')
            prev_bids.append(float(bid))
            if bid <= 20:
                low_fixed.append(float(bid))
            if bid >= 80:
                high_spenders.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_low = min(low_fixed) if low_fixed else 15.0

    base = 16.5

    if supply >= 24:
        base = max(base, lowest_low + 1.0)
    elif supply >= 21:
        base = max(base, lowest_low + 2.0)
    elif supply >= 18:
        base = max(base, 22.0)
    else:
        base = max(base, 30.0)

    if len(high_spenders) >= 1 and supply <= 17 and hp > 5 and no_water_days == 0:
        base = min(base, 18.0)

    if desperate_count >= 2:
        base = max(base, 32.0)
    elif desperate_count == 1:
        base = max(base, 24.0)

    if hp <= 2 or no_water_days >= 2:
        base = max(base, 78.0)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, 48.0)

    if highest_prev >= 120 and supply <= 17 and hp >= 6 and no_water_days == 0:
        base = min(base, 20.0)

    if budget < 40:
        base = min(base, budget)
    elif budget < 80:
        base = min(base, max(24.0, budget * 0.7))
    else:
        base = min(base, budget * 0.55 + 8.0)

    if hp >= 7 and no_water_days == 0 and supply >= 21 and low_fixed:
        target = lowest_low + 2.5
        if target > base:
            base = target

    bid = min(float(budget), float(base))
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    capacity = float(supply) / float(WATER_REQ)

    prev_bids = []
    strong_threat = False
    cheap_lane = False
    desperate_opp = False
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = prev.get('bid') if prev else None
        if pbid is not None:
            prev_bids.append(float(pbid))
            if float(pbid) >= 100:
                strong_threat = True
            if float(pbid) <= 25:
                cheap_lane = True
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opp = True

    alive_count = len(alive)

    if hp <= 2 or no_water_days >= 2:
        if prev_bids:
            target = max(prev_bids) + 3.0
            return float(min(budget, max(78.0, target)))
        return float(min(budget, 85.0))

    if alive_count == 0:
        return float(min(budget, 8.0))

    if capacity >= alive_count:
        if cheap_lane:
            return float(min(budget, 12.0))
        return float(min(budget, 9.0))

    if capacity >= 1.5:
        if strong_threat and hp >= 5 and no_water_days == 0:
            return float(min(budget, 18.0))
        if prev_bids:
            low_prev = min(prev_bids)
            return float(min(budget, max(16.0, low_prev + 2.0)))
        return float(min(budget, 20.0))

    if strong_threat:
        if hp >= 6 and no_water_days == 0 and day < 8:
            return float(min(budget, 14.0))
        if prev_bids:
            target = max(prev_bids) + 2.0
            return float(min(budget, max(72.0, target)))
        return float(min(budget, 76.0))

    if desperate_opp:
        if prev_bids:
            target = max(prev_bids) + 2.0
            return float(min(budget, max(55.0, target)))
        return float(min(budget, 58.0))

    if prev_bids:
        sorted_bids = sorted(prev_bids)
        idx = int(min(len(sorted_bids) - 1, 1))
        anchor = sorted_bids[idx]
        return float(min(budget, max(28.0, anchor + 3.0)))

    return float(min(budget, 30.0))
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
    pressure_bids = []
    desperate_count = 0
    rich_count = 0

    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                bid = float(bid)
                prev_bids.append(bid)
                if prev.get('status') == 'success' or prev.get('hp_after', opp.get('hp', 10)) <= 3:
                    pressure_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    high_pressure = max(pressure_bids) if pressure_bids else highest_prev

    scarcity = (supply <= 17)
    abundant = (supply >= 22)
    critical_me = (hp <= 2 or no_water_days >= 2)
    urgent_me = (hp <= 4 or no_water_days >= 1)

    if critical_me:
        target = max(DAILY_SALARY * 0.95, high_pressure + 2.0)
        if scarcity:
            target = max(target, DAILY_SALARY * 1.15)
        return float(min(budget, target))

    if abundant:
        if highest_prev >= DAILY_SALARY * 1.3 and hp >= 5:
            return float(min(budget, DAILY_SALARY * 0.18))
        if highest_prev <= DAILY_SALARY * 0.55:
            return float(min(budget, max(DAILY_SALARY * 0.32, avg_prev + 1.0)))
        return float(min(budget, DAILY_SALARY * 0.28))

    if scarcity:
        if high_pressure >= DAILY_SALARY * 1.4 and hp >= 6:
            return float(min(budget, DAILY_SALARY * 0.22))
        if urgent_me:
            target = max(DAILY_SALARY * 0.88, high_pressure + 1.5)
            return float(min(budget, target))
        if desperate_count >= 2:
            return float(min(budget, DAILY_SALARY * 0.2))
        target = max(DAILY_SALARY * 0.58, min(high_pressure + 1.0, DAILY_SALARY * 0.82))
        return float(min(budget, target))

    if urgent_me:
        target = max(DAILY_SALARY * 0.72, min(high_pressure + 1.0, DAILY_SALARY * 0.95))
        return float(min(budget, target))

    if highest_prev >= DAILY_SALARY * 1.25 and hp >= 5:
        return float(min(budget, DAILY_SALARY * 0.24))

    if rich_count >= 2 and hp >= 6:
        return float(min(budget, DAILY_SALARY * 0.3))

    target = max(DAILY_SALARY * 0.42, min(avg_prev + 1.0, DAILY_SALARY * 0.68))
    if day >= 8 and hp >= 6:
        target = min(target, DAILY_SALARY * 0.38)
    return float(min(budget, target))
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

    alive = []
    prev_bids = []
    strong_opp = False
    needy_opp = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                needy_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev.get('bid', 0.0))
                prev_bids.append(b)
                if b >= 120:
                    strong_opp = True
            if opp.get('budget', 0) > budget * 1.5 and opp.get('hp', 0) >= hp:
                strong_opp = True

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    pressure = 0.0
    if slots <= 1:
        pressure += 1.0
    elif slots == 2:
        pressure += 0.55
    else:
        pressure += 0.2

    if len(alive) > slots:
        pressure += 0.35
    if strong_opp:
        pressure += 0.35
    if needy_opp > 0:
        pressure += 0.15
    if hp <= 2:
        pressure += 0.9
    elif hp <= 4:
        pressure += 0.45
    if no_water >= 1:
        pressure += 0.5
    if day >= 8:
        pressure += 0.15

    top_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if hp <= 1 or no_water >= 2:
        bid = min(budget, max(95.0, top_prev + 3.0, DAILY_SALARY * 1.15))
        return max(0.0, bid)

    if pressure >= 1.8:
        target = max(78.0, min(110.0, avg_prev * 0.75 + 18.0, top_prev + 2.5))
    elif pressure >= 1.2:
        target = max(52.0, min(82.0, avg_prev * 0.55 + 10.0, top_prev * 0.7 + 6.0))
    elif pressure >= 0.8:
        target = max(30.0, min(58.0, avg_prev * 0.4 + 6.0))
    else:
        target = 18.0 if hp > 5 else 26.0

    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0:
        keep = reserve_days * 18.0
        soft_cap = max(0.0, budget - keep)
        if hp <= 3:
            soft_cap = budget

    if soft_cap < 8.0:
        soft_cap = min(budget, max(8.0, budget * 0.6))

    bid = min(budget, min(target, soft_cap))
    if hp <= 3 and bid < 42.0:
        bid = min(budget, 42.0)
    if slots <= 1 and hp <= 4:
        bid = min(budget, max(bid, 68.0))

    return max(0.0, float(bid))
"""
