# ============================================================
# Experiment: exp_076
# Agent: Alex
# Source: exp_076
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0

    alive_opponents = []
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive_opponents.append(opp)
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opponents += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    if not alive_opponents:
        if hp <= 3 or no_water >= 1:
            return min(budget, 28)
        return min(budget, 12)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = DAILY_SALARY * (0.34 + 0.26 * scarcity)

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water >= 1:
        base = max(base, DAILY_SALARY * 0.72)
    elif hp >= 8 and no_water == 0 and supply >= 22:
        base = min(base, DAILY_SALARY * 0.28)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = max(avg_prev + 1.0, highest_prev + 1.5 * scarcity)
        if hp <= 4 or no_water >= 1:
            base = max(base, target)
        else:
            base = max(base, min(target, DAILY_SALARY * 0.78))

    if urgent_opponents > 0 and supply <= 18:
        base += 4
    if rich_opponents >= 2 and supply <= 17:
        base += 3

    remaining_days = max(1, 10 - int(day_context['day']) + 1)
    reserve_floor = DAILY_SALARY * 0.18 * remaining_days
    cap = budget
    if budget > reserve_floor:
        cap = budget - max(0, reserve_floor * 0.15)

    if hp <= 2:
        cap = budget

    bid = min(base, cap)
    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget
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

    alive_opponents = []
    prev_bids = []
    fixed_eric_like = []
    high_spenders = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if abs(float(bid) - 63.0) <= 0.01:
                    fixed_eric_like.append(opp)
                if float(bid) >= 100.0:
                    high_spenders.append(opp)

    if not alive_opponents:
        return max(0.0, min(budget, 20.0))

    severe_need = hp <= 3 or no_water_days >= 2
    urgent_need = hp <= 5 or no_water_days >= 1
    scarce = supply <= 17
    abundant = supply >= 22

    target = 0.0

    if severe_need:
        if prev_bids:
            target = max(prev_bids) + 2.0
        else:
            target = 66.0
    elif urgent_need:
        if scarce:
            if prev_bids:
                target = max(64.5, min(max(prev_bids) + 1.0, 82.0))
            else:
                target = 65.0
        else:
            target = 64.5 if fixed_eric_like else 49.0
    else:
        if abundant:
            target = 18.0
        elif scarce:
            target = 64.5 if fixed_eric_like else 42.0
        else:
            target = 28.0 if high_spenders else 52.0

    if day >= 8:
        target += 4.0
    if day >= 9 and urgent_need:
        target += 6.0

    max_safe = budget
    if hp > 6 and no_water_days == 0:
        max_safe = min(max_safe, DAILY_SALARY * 0.95)
    else:
        max_safe = min(max_safe, DAILY_SALARY * 1.35)

    bid = min(max_safe, target)
    if budget <= 0:
        return 0.0
    if bid < 0:
        bid = 0.0
    return float(round(min(budget, bid), 2))
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

    alive_opponents = []
    prev_bids = []
    opp_need_count = 0
    rich_aggressive = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                opp_need_count += 1
            if opp.get('budget', 0) >= 300:
                rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    slots = max(1, int(supply / WATER_REQ))
    competitors = 1 + len(alive_opponents)
    scarcity = competitors - slots

    urgent = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1
    tight_supply = supply <= 18
    very_tight = supply <= 15
    late_game = day >= 8

    base = 22.0

    if urgent:
        bid = max(95.0, highest_prev + 2.0, avg_prev + 6.0)
        if very_tight:
            bid += 12.0
        elif tight_supply:
            bid += 6.0
    elif pressured:
        bid = max(58.0, avg_prev * 0.72, highest_prev * 0.62)
        if tight_supply:
            bid += 8.0
        if opp_need_count >= 2:
            bid += 6.0
    else:
        if highest_prev >= 140:
            bid = 19.0
        elif highest_prev >= 90:
            bid = 27.0
        else:
            bid = max(base, avg_prev * 0.38)
        if scarcity >= 3:
            bid += 10.0
        elif scarcity >= 2:
            bid += 5.0
        if rich_aggressive >= 2 and not late_game:
            bid -= 4.0

    if late_game and hp <= 5:
        bid = max(bid, highest_prev * 0.7, 62.0)
    if late_game and urgent:
        bid = max(bid, 110.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 70.0 * (10 - day) * 0.18
    max_affordable = max(0.0, budget - reserve_floor)
    if urgent:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) > 300:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    my_urgent = hp <= 3 or no_water >= 1
    severe = hp <= 2 or no_water >= 2

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    if severe:
        bid = max(58.0, highest_prev + 2.0)
        return float(min(budget, bid))

    if slots >= len(alive) + 1:
        bid = 6.0 if hp > 4 else 18.0
        return float(min(budget, bid))

    if slots >= len(alive):
        bid = 12.0 if hp > 4 else 24.0
        return float(min(budget, bid))

    if my_urgent:
        if highest_prev >= 120:
            bid = 66.0
        elif highest_prev >= 70:
            bid = min(68.0, highest_prev + 3.0)
        else:
            bid = max(52.0, avg_prev + 6.0)
        return float(min(budget, bid))

    if highest_prev >= 150:
        bid = 8.0
    elif highest_prev >= 100:
        bid = 14.0 if hp >= 5 else 28.0
    elif highest_prev >= 60:
        bid = 22.0 if slots >= 2 else 31.0
    else:
        bid = 26.0 if slots >= 2 else 36.0

    if urgent_opp >= 2 and hp >= 5:
        bid *= 0.8
    if rich_opp >= 2 and slots <= 1 and hp <= 4:
        bid = max(bid, 44.0)

    if budget < 80:
        bid = min(bid, budget * 0.55)

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
            alive_opponents.append((oid, opp))

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.35
        if no_water_days >= 2 or hp <= 3:
            safe_bid = DAILY_SALARY * 0.75
        return float(min(budget, safe_bid))

    prev_bids = []
    prev_high = 0.0
    prev_eric = None
    desperate_count = 0
    rich_count = 0

    for oid, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > prev_high:
                prev_high = float(bid)
            if oid == 'Eric':
                prev_eric = float(bid)
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_count += 1

    target_pressure = prev_high
    if prev_eric is not None:
        target_pressure = max(target_pressure, prev_eric)

    units = supply / float(WATER_REQ)
    tight_supply = units <= 1.35
    medium_supply = units <= 1.7

    urgency = 0
    if no_water_days >= 2:
        urgency += 3
    elif no_water_days == 1:
        urgency += 1
    if hp <= 3:
        urgency += 3
    elif hp <= 6:
        urgency += 1
    if tight_supply:
        urgency += 2
    elif medium_supply:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1
    if day >= 8:
        urgency += 1

    if target_pressure <= 0:
        if urgency >= 5:
            bid = DAILY_SALARY * 0.9
        elif urgency >= 3:
            bid = DAILY_SALARY * 0.65
        else:
            bid = DAILY_SALARY * 0.4
        return float(min(budget, bid))

    if urgency >= 6:
        bid = max(DAILY_SALARY * 0.95, target_pressure + 3.0)
    elif urgency >= 4:
        bid = max(DAILY_SALARY * 0.78, target_pressure + 1.5)
    elif urgency >= 2:
        if target_pressure >= DAILY_SALARY * 1.5:
            bid = DAILY_SALARY * 0.52
        else:
            bid = max(DAILY_SALARY * 0.55, target_pressure * 0.78)
    else:
        if not tight_supply and rich_count <= 1 and target_pressure >= DAILY_SALARY * 1.2:
            bid = DAILY_SALARY * 0.32
        else:
            bid = max(DAILY_SALARY * 0.42, target_pressure * 0.62)

    if budget < DAILY_SALARY * 0.6 and urgency < 4:
        bid = min(bid, budget * 0.7)

    if no_water_days >= 2 or hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.95)

    return float(min(budget, max(0.0, bid)))
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
            if opp.get('budget', 0) >= budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if not alive:
        return float(min(budget, 12.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.55
    elif hp <= 4:
        danger += 0.3
    if no_water >= 2:
        danger += 0.35
    elif no_water >= 1:
        danger += 0.18

    base = DAILY_SALARY * (0.34 + 0.28 * supply_pressure + danger)

    if highest_prev >= 150:
        reactive = min(95.0, avg_prev * 0.62 + 6.0)
    elif highest_prev >= 100:
        reactive = min(88.0, highest_prev * 0.78 + 3.0)
    elif highest_prev > 0:
        reactive = min(82.0, highest_prev + 2.5)
    else:
        reactive = DAILY_SALARY * 0.45

    bid = max(base, reactive)

    if supply >= 23 and hp >= 6 and no_water == 0:
        bid *= 0.72
    elif supply >= 20 and hp >= 5 and no_water == 0:
        bid *= 0.84

    if supply <= 17:
        bid += 8.0 + 2.0 * urgent_opp
    if hp <= 2 or no_water >= 2:
        bid = max(bid, DAILY_SALARY * 0.96)
    elif hp <= 4 or no_water >= 1:
        bid = max(bid, DAILY_SALARY * 0.78)

    if rich_opp >= 2 and supply <= 18:
        bid += 5.0

    if day >= 8 and budget > DAILY_SALARY * (11 - day):
        bid += 6.0

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 0.35
    max_affordable = max(0.0, budget - reserve)
    if hp <= 3 or no_water >= 1 or day >= 9:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    reqs = [WATER_REQ]
    bob_prev_bid = None
    max_prev_bid = 0.0
    urgent_opp = 0
    rich_opp = 0

    for oid, opp in alive:
        reqs.append(float(opp.get('water_requirement', WATER_REQ)))
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_opp += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            pbid = float(pbid)
            if pbid > max_prev_bid:
                max_prev_bid = pbid
            if oid == 'Bob':
                bob_prev_bid = pbid

    total_req = sum(reqs)
    scarcity = total_req / max(supply, 1.0)
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)

    risk = 0.0
    if hp <= 2:
        risk += 0.9
    elif hp <= 4:
        risk += 0.45
    if no_water >= 2:
        risk += 1.0
    elif no_water >= 1:
        risk += 0.45
    if scarcity > 2.2:
        risk += 0.55
    elif scarcity > 1.8:
        risk += 0.3
    if urgent_opp >= 1:
        risk += 0.15
    if rich_opp >= 1:
        risk += 0.1

    base_frac = 0.28 + (1.0 - supply_ratio) * 0.22
    if day >= 8:
        base_frac += 0.08
    if risk >= 1.4:
        base_frac = max(base_frac, 0.92)
    elif risk >= 0.9:
        base_frac = max(base_frac, 0.72)
    elif risk >= 0.45:
        base_frac = max(base_frac, 0.54)

    target = DAILY_SALARY * base_frac

    if bob_prev_bid is not None:
        if risk >= 0.9 or supply <= 17:
            target = max(target, bob_prev_bid + 2.5)
        elif bob_prev_bid >= DAILY_SALARY * 0.95 and hp > 4 and no_water == 0 and supply >= 20:
            target = min(target, DAILY_SALARY * 0.32)
        elif bob_prev_bid <= DAILY_SALARY * 0.55 and (supply <= 18 or risk >= 0.45):
            target = max(target, bob_prev_bid + 1.5)
    elif max_prev_bid > 0 and (risk >= 0.45 or supply <= 18):
        target = max(target, max_prev_bid + 1.5)

    if budget < DAILY_SALARY * 0.6 and hp > 4 and no_water == 0 and supply >= 20:
        target = min(target, budget * 0.55)

    if hp <= 2 or no_water >= 2:
        target = max(target, DAILY_SALARY * 0.95)

    bid = min(float(budget), float(target))
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
    rich_pressure = 0
    needy_pressure = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        alive_opps.append(opp)
        if opp.get('budget', 0) >= 120:
            rich_pressure += 1
        if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
            needy_pressure += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))

    if not alive_opps:
        return float(min(budget, 8.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    tight = units < 2.0
    medium_tight = units < 2.6

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if tight:
        urgency += 2
    elif medium_tight:
        urgency += 1
    urgency += min(needy_pressure, 2)

    if urgency >= 7:
        target = max(63.0, max_prev + 3.0)
    elif urgency >= 5:
        target = max(52.0, avg_prev + 4.0, max_prev * 0.78)
    elif urgency >= 3:
        if max_prev >= 110:
            target = 24.0
        else:
            target = max(30.0, avg_prev * 0.55 + 4.0)
    else:
        if tight and rich_pressure >= 2 and max_prev >= 80:
            target = 12.0
        elif max_prev >= 110:
            target = 10.0
        elif max_prev >= 80:
            target = 16.0
        else:
            target = 22.0 if medium_tight else 14.0

    if day >= 8:
        target += 6.0
    if budget < 45:
        target = min(target, budget)
    elif budget < 90:
        target = min(target, 0.72 * budget)
    else:
        target = min(target, 0.55 * budget)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, min(budget, 66.0))

    if target < 0:
        target = 0.0
    return float(min(budget, round(target, 2)))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    david_prev = None
    strongest_prev = 0.0
    urgent_opp_count = 0

    for oid, opp in alive:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                b = float(bid)
                prev_bids.append(b)
                if b > strongest_prev:
                    strongest_prev = b
                if oid == 'David':
                    david_prev = b
            except Exception:
                pass

    if david_prev is None:
        david_prev = strongest_prev if strongest_prev > 0 else DAILY_SALARY * 0.75

    tight_supply = supply <= 18
    abundant_supply = supply >= 22
    danger = hp <= 3 or no_water_days >= 1
    severe_danger = hp <= 2 or no_water_days >= 2

    if severe_danger:
        target = max(DAILY_SALARY * 0.95, david_prev + 2.5)
    elif danger:
        if tight_supply:
            target = max(DAILY_SALARY * 0.88, david_prev + 1.5)
        else:
            target = max(DAILY_SALARY * 0.78, david_prev + 1.0)
    else:
        if abundant_supply and urgent_opp_count == 0:
            target = DAILY_SALARY * 0.34
        elif abundant_supply:
            target = DAILY_SALARY * 0.42
        elif tight_supply:
            target = max(DAILY_SALARY * 0.68, david_prev * 0.82)
        else:
            target = max(DAILY_SALARY * 0.52, david_prev * 0.72)

    if day >= 8 and hp > 4 and no_water_days == 0:
        target *= 0.92

    if budget < target:
        if severe_danger or (danger and tight_supply):
            return float(budget)
        return float(min(budget, max(0.0, DAILY_SALARY * 0.4)))

    return float(min(budget, max(0.0, target)))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    pressured_opponents = 0
    rich_opponents = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > 200:
                rich_opponents += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                pressured_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        bid = max(72.0, highest_prev * 0.72)
        if tight_supply:
            bid = max(bid, 92.0)
        return float(min(budget, bid))

    if hp <= 4 or no_water >= 1:
        bid = max(48.0, avg_prev * 0.45)
        if tight_supply:
            bid = max(bid, 62.0)
        elif loose_supply:
            bid = min(bid, 55.0)
        return float(min(budget, bid))

    if highest_prev >= 120:
        bid = 24.0
    elif highest_prev >= 70:
        bid = 31.0
    else:
        bid = 36.0

    if tight_supply:
        bid += 10.0
    elif loose_supply:
        bid -= 6.0

    if rich_opponents >= 2:
        bid += 4.0
    if pressured_opponents >= 2:
        bid -= 3.0

    reserve_target = DAILY_SALARY * 3
    if budget < reserve_target:
        bid = min(bid, 28.0)

    bid = max(12.0, bid)
    return float(min(budget, bid))
"""
