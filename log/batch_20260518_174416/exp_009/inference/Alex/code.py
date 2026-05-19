# ============================================================
# Experiment: exp_009
# Agent: Alex
# Source: exp_009
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
    rich_pressure = 0.0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) > DAILY_SALARY * 4:
                rich_pressure += 2.0
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                if prev.get('error'):
                    rich_pressure -= 0.5

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    scarcity = (25.0 - supply) / 10.0
    scarcity = max(0.0, min(1.0, scarcity))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    urgency = 0.0
    if hp <= 2:
        urgency += 4.0
    elif hp <= 4:
        urgency += 2.0
    if no_water >= 1:
        urgency += 3.0

    pressure = highest_prev * 0.55 + avg_prev * 0.2 + desperate_count * 2.0 + rich_pressure + scarcity * 10.0

    if hp <= 2 or no_water >= 2:
        bid = max(DAILY_SALARY * 0.92, pressure + 6.0)
    elif hp <= 4 or no_water >= 1:
        bid = max(DAILY_SALARY * 0.72, pressure + 3.0)
    else:
        if supply >= 22:
            bid = max(DAILY_SALARY * 0.34, pressure * 0.75)
        elif supply >= 18:
            bid = max(DAILY_SALARY * 0.48, pressure * 0.9)
        else:
            bid = max(DAILY_SALARY * 0.62, pressure + 1.5)

    if prev_bids and highest_prev >= DAILY_SALARY * 0.9 and hp > 4 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.42)

    if budget < DAILY_SALARY * 1.2:
        if hp > 3 and no_water == 0:
            bid = min(bid, budget * 0.55)
        else:
            bid = min(max(bid, budget * 0.75), budget)

    bid = max(0.0, min(budget, bid))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, 18.0))

    urgent_prev = []
    rich_prev = []
    all_prev = []
    weak_count = 0
    desperate_count = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            all_prev.append(float(bid))
        opp_hp = opp.get('hp', 10)
        opp_nw = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0)
        if opp_hp <= 3 or opp_nw >= 1:
            desperate_count += 1
            if bid is not None:
                urgent_prev.append(float(bid))
        if opp_budget >= 140:
            weak_count += 0
        else:
            weak_count += 1
        if opp_budget >= 120 and bid is not None:
            rich_prev.append(float(bid))

    base = 22.0

    if supply <= 16:
        base = 52.0
    elif supply <= 18:
        base = 38.0
    elif supply >= 23:
        base = 18.0

    if hp <= 2 or no_water >= 2:
        base = max(base, 66.0)
    elif hp <= 4 or no_water >= 1:
        base = max(base, 48.0)

    if urgent_prev:
        top_urgent = max(urgent_prev)
        if hp <= 4 or no_water >= 1 or supply <= 18:
            base = max(base, min(72.0, top_urgent + 2.0))
        else:
            base = max(base, min(44.0, top_urgent * 0.72))

    if rich_prev:
        top_rich = max(rich_prev)
        if hp >= 6 and no_water == 0 and supply >= 19:
            base = min(base, 34.0)
        elif hp <= 3:
            base = max(base, min(78.0, top_rich * 0.55))

    if all_prev and desperate_count == 0 and supply >= 20:
        avg_prev = sum(all_prev) / float(len(all_prev))
        base = min(base, max(16.0, avg_prev * 0.35))

    if day >= 8:
        base += 6.0
    if day >= 9 and (hp <= 5 or no_water >= 1):
        base += 8.0

    if budget < 35:
        base = max(0.0, min(base, budget))
    else:
        reserve_floor = 10.0 if day >= 8 else 18.0
        base = min(base, max(0.0, budget - reserve_floor))

    if hp >= 8 and no_water == 0 and supply >= 22 and desperate_count == 0:
        base = min(base, 20.0)

    return float(max(0.0, min(budget, round(base, 2))))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_bids = []
    urgent_opponents = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(float(bid))
                    if bid >= 90:
                        aggressive_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    if prev_bids:
        high_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        high_prev = 0.0
        avg_prev = 0.0

    emergency = hp <= 2 or no_water_days >= 2
    stressed = hp <= 4 or no_water_days >= 1

    if emergency:
        target = max(88.0, min(126.0, high_prev + 4.0))
        if supply <= 17:
            target = max(target, 108.0)
        return float(min(budget, target))

    if stressed:
        target = 58.0 + 28.0 * scarcity + 6.0 * urgent_opponents
        if high_prev > 0:
            target = max(target, min(118.0, high_prev + 2.5))
        return float(min(budget, target))

    target = 28.0 + 20.0 * scarcity

    if supply <= 17:
        target += 14.0
    elif supply >= 22:
        target -= 6.0

    if aggressive_bids:
        target = max(target, min(92.0, avg_prev * 0.72 + 3.0))
    elif high_prev > 0:
        target = max(target, min(70.0, avg_prev * 0.6 + 2.0))

    if urgent_opponents >= 2:
        target += 8.0
    elif urgent_opponents == 0:
        target -= 4.0

    if day >= 8 and hp >= 7:
        target -= 5.0

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    affordable = budget
    if budget > reserve_floor:
        affordable = budget - reserve_floor * 0.15

    bid = min(affordable, target)
    bid = max(0.0, min(budget, bid))
    return float(bid)
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

    day = day_context['day']
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_aggro = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            if opp.get('budget', 0) >= 500:
                rich_aggro += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.5
    if no_water >= 2:
        danger += 1.0
    elif no_water >= 1:
        danger += 0.45

    endgame = day >= 8

    base = 16.0 + 10.0 * scarcity

    if highest_prev >= 120:
        base = min(base, 22.0 + 8.0 * scarcity)
    elif highest_prev >= 90:
        base = min(base, 26.0 + 10.0 * scarcity)
    elif highest_prev > 0:
        base = max(base, min(55.0, avg_prev * 0.55))

    if urgent_opp >= 2:
        base += 8.0
    elif urgent_opp == 1:
        base += 4.0

    if rich_aggro >= 2 and danger < 0.5:
        base -= 4.0

    if danger >= 1.5:
        bid = max(base, min(budget, highest_prev + 6.0 if highest_prev > 0 else 78.0))
    elif danger >= 0.5:
        target = highest_prev + 2.5 if 25.0 <= highest_prev <= 80.0 else 48.0 + 12.0 * scarcity
        bid = max(base, target)
    else:
        bid = base

    if endgame and hp <= 4:
        bid = max(bid, 60.0 + 10.0 * scarcity)

    max_safe = budget
    if day < 10:
        reserve_days = 10 - day
        reserve = max(0.0, reserve_days * DAILY_SALARY * 0.18)
        max_safe = max(0.0, budget - reserve)
        if danger >= 1.0:
            max_safe = budget

    if max_safe <= 0:
        max_safe = min(budget, 12.0)

    bid = min(bid, max_safe)
    bid = min(bid, budget)
    bid = max(0.0, bid)

    if budget < 25:
        bid = min(bid, budget)
    elif danger < 0.5 and highest_prev >= 100:
        bid = min(bid, 24.0 + 6.0 * scarcity)

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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 140:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_factor = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_factor < 0:
        supply_factor = 0.0
    if supply_factor > 1:
        supply_factor = 1.0

    tight_supply = supply <= 17
    abundant_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        base = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif hp <= 4 or no_water_days >= 1:
        base = max(DAILY_SALARY * 0.72, avg_prev + 2.0)
    else:
        if abundant_supply:
            base = DAILY_SALARY * 0.28
        elif tight_supply:
            base = DAILY_SALARY * 0.58
        else:
            base = DAILY_SALARY * 0.42

        if highest_prev > 0:
            if highest_prev >= 140:
                base = min(base, DAILY_SALARY * 0.4)
            elif highest_prev >= 95:
                base = max(base, DAILY_SALARY * 0.5)
            elif highest_prev >= 60:
                base = max(base, highest_prev + 1.5)
            else:
                base = max(base, avg_prev + 1.0)

    if desperate_count >= 2:
        base += 8.0
    elif desperate_count == 1:
        base += 4.0

    if rich_count >= 2 and tight_supply:
        base += 10.0
    elif rich_count >= 1 and tight_supply:
        base += 5.0

    if abundant_supply:
        base -= 6.0

    if day >= 8 and hp > 4 and no_water_days == 0:
        base -= 4.0

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    max_affordable = budget
    if hp > 3 and no_water_days == 0:
        max_affordable = max(0.0, budget - reserve_floor)
        if max_affordable <= 0:
            max_affordable = min(budget, DAILY_SALARY * 0.35)

    bid = min(base, max_affordable)
    if hp <= 2 or no_water_days >= 2:
        bid = min(max(base, DAILY_SALARY * 0.95), budget)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    threat_bids = []
    rich_threat = False

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= DAILY_SALARY * 2 or opp.get('hp', 0) > 4:
                    threat_bids.append(float(bid))
            if opp.get('budget', 0) > 250 and opp.get('hp', 0) > 2:
                rich_threat = True

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.18))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat_prev = max(threat_bids) if threat_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    danger = 0.0
    if hp <= 2:
        danger += 0.75
    elif hp <= 4:
        danger += 0.4
    if no_water_days >= 2:
        danger += 0.7
    elif no_water_days == 1:
        danger += 0.3

    if supply >= 23:
        base = DAILY_SALARY * 0.26
    elif supply >= 20:
        base = DAILY_SALARY * 0.38
    elif supply >= 17:
        base = DAILY_SALARY * 0.52
    else:
        base = DAILY_SALARY * 0.68

    if highest_threat_prev > 0:
        if danger >= 0.9:
            target = max(base + DAILY_SALARY * 0.18, highest_threat_prev + 3.0)
        elif scarcity > 0.6:
            target = max(base, highest_threat_prev + 1.5)
        else:
            target = max(base, highest_threat_prev * 0.72)
    else:
        target = base

    if rich_threat and supply <= 18:
        target += 6.0

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4 and supply <= 17:
        target = max(target, DAILY_SALARY * 0.75)

    if day >= 8 and hp > 5 and no_water_days == 0 and supply >= 20:
        target *= 0.9

    cap = budget
    if budget < DAILY_SALARY * 0.5 and danger < 0.9:
        target = min(target, budget)
    else:
        target = min(target, cap)

    if target < 0:
        target = 0.0

    return float(round(min(budget, target), 2))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if len(alive_opponents) == 0:
        base = DAILY_SALARY * 0.28
        if no_water_days >= 1 or hp <= 3:
            base = DAILY_SALARY * 0.55
        return float(min(budget, max(0.0, base)))

    total_players = 1 + len(alive_opponents)
    tight_supply = supply <= total_players * WATER_REQ
    very_tight = supply <= max(WATER_REQ, (total_players - 1) * WATER_REQ)

    highest_prev_bid = 0.0
    avg_prev_bid = 0.0
    count_prev = 0
    rich_aggressive = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        prev_bid = 0.0
        if prev and prev.get('bid') is not None:
            prev_bid = float(prev.get('bid', 0.0))
            if prev_bid > highest_prev_bid:
                highest_prev_bid = prev_bid
            avg_prev_bid += prev_bid
            count_prev += 1
        if opp.get('budget', 0.0) >= 140 and prev_bid >= 120:
            rich_aggressive += 1

    if count_prev > 0:
        avg_prev_bid = avg_prev_bid / count_prev

    urgency = 0
    if hp <= 2 or no_water_days >= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency == 3:
        target = max(0.92 * DAILY_SALARY, highest_prev_bid + 4.0)
        if very_tight:
            target = max(target, 0.98 * DAILY_SALARY)
    elif urgency == 2:
        if highest_prev_bid >= 150:
            target = 0.58 * DAILY_SALARY if not tight_supply else 0.88 * DAILY_SALARY
        else:
            target = max(0.62 * DAILY_SALARY, highest_prev_bid + 2.0)
            if tight_supply:
                target = max(target, 0.82 * DAILY_SALARY)
    else:
        if very_tight:
            if highest_prev_bid >= 150 and rich_aggressive >= 2:
                target = 0.22 * DAILY_SALARY
            else:
                target = max(0.52 * DAILY_SALARY, min(0.86 * DAILY_SALARY, highest_prev_bid + 1.5))
        elif tight_supply:
            if highest_prev_bid >= 150:
                target = 0.30 * DAILY_SALARY
            else:
                target = max(0.42 * DAILY_SALARY, min(0.72 * DAILY_SALARY, avg_prev_bid + 1.0))
        else:
            target = 0.24 * DAILY_SALARY
            if day >= 8:
                target = 0.34 * DAILY_SALARY

    if budget < DAILY_SALARY * 0.75:
        target = min(target, budget * 0.72)
    elif budget < DAILY_SALARY * 1.5:
        target = min(target, budget * 0.82)

    target = max(0.0, min(budget, target))
    return float(target)
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

    day = day_context['day']
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
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        if opp.get('budget', 0) >= 700:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    scarcity = 1.0 - supply_ratio

    if hp <= 2 or no_water_days >= 2:
        target = max(DAILY_SALARY * 1.05, highest_prev + 4.0)
    elif hp <= 4 or no_water_days >= 1:
        target = max(DAILY_SALARY * 0.82, highest_prev + 2.0)
    else:
        if highest_prev >= 150:
            target = DAILY_SALARY * (0.38 + 0.12 * scarcity)
        elif highest_prev >= 100:
            target = max(DAILY_SALARY * (0.52 + 0.18 * scarcity), avg_prev * 0.78)
        elif highest_prev >= 70:
            target = max(DAILY_SALARY * (0.58 + 0.16 * scarcity), highest_prev + 1.5)
        else:
            target = DAILY_SALARY * (0.50 + 0.18 * scarcity)

    if urgent_count >= 2:
        target += 6.0
    elif urgent_count == 1:
        target += 3.0

    if rich_count >= 1 and highest_prev >= 140:
        target -= 4.0

    if day >= 8 and hp >= 5:
        target *= 0.92
    if day >= 9 and hp >= 7:
        target *= 0.88

    if budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.72)
    elif budget < DAILY_SALARY * 4:
        target = min(target, budget * 0.55)

    floor_bid = 0.0
    if hp <= 4 or no_water_days >= 1:
        floor_bid = DAILY_SALARY * 0.45
    else:
        floor_bid = DAILY_SALARY * 0.22

    bid = max(floor_bid, target)
    bid = min(budget, bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    strong_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('budget', 0) > 0:
                    strong_prev.append(bid)

    if not alive_opps:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_strong = sum(strong_prev) / len(strong_prev) if strong_prev else highest_prev

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    critical_hp = hp <= 3 or no_water_days >= 2
    pressured_hp = hp <= 5 or no_water_days >= 1

    bid = 0.0

    if critical_hp:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 2.0)
    elif tight_supply:
        bid = max(0.78 * DAILY_SALARY, min(highest_prev + 1.5, 0.95 * DAILY_SALARY))
    elif medium_supply:
        if avg_strong >= 120:
            bid = 22.0
        else:
            bid = max(28.0, min(avg_strong * 0.45, 0.62 * DAILY_SALARY))
    else:
        if pressured_hp:
            bid = max(26.0, min(highest_prev * 0.35, 0.55 * DAILY_SALARY))
        else:
            bid = 12.0

    if budget < bid:
        if critical_hp:
            return max(0.0, budget)
        bid = min(budget, max(0.0, bid))

    reserve = 0.0
    if hp > 6:
        reserve = 35.0
    elif hp > 4:
        reserve = 20.0

    if not critical_hp and budget - bid < reserve:
        bid = max(0.0, budget - reserve)

    if pressured_hp and bid < 18.0 and budget >= 18.0:
        bid = 18.0

    if tight_supply and bid < 40.0 and not critical_hp and budget >= 40.0:
        bid = 40.0

    return min(budget, max(0.0, bid))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, 20.0))
        return float(min(budget, 5.0))

    my_units = 1
    total_units = my_units
    for req in opp_requirements:
        units = int(supply // req)
        if units < 1:
            units = 1
        total_units += units

    market_units = int(supply // WATER_REQ)
    if market_units < 1:
        market_units = 1

    highest_prev = max(prev_bids) if prev_bids else 95.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 95.0

    urgent = hp <= 4 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2
    scarce_day = market_units <= 1

    if critical:
        bid = max(110.0, highest_prev + 4.0)
    elif urgent and scarce_day:
        bid = max(102.0, highest_prev + 2.0)
    elif urgent:
        bid = max(90.0, avg_prev + 1.5)
    elif scarce_day:
        bid = max(97.0, highest_prev + 1.0)
    else:
        bid = 62.0
        if avg_prev < 85.0:
            bid = 68.0
        if day >= 8 and hp >= 7:
            bid = min(bid, 58.0)

    if budget < bid:
        if critical:
            return float(budget)
        bid = max(0.0, budget * 0.82)

    safe_cap = budget
    if hp >= 7 and no_water_days == 0 and not scarce_day:
        safe_cap = min(safe_cap, max(45.0, budget * 0.22))
    elif hp >= 5 and not urgent:
        safe_cap = min(safe_cap, max(70.0, budget * 0.35))

    final_bid = min(bid, safe_cap, budget)
    if critical:
        final_bid = min(max(final_bid, min(budget, highest_prev + 2.0)), budget)

    if final_bid < 0:
        final_bid = 0.0
    return float(final_bid)
"""
