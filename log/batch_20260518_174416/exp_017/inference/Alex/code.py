# ============================================================
# Experiment: exp_017
# Agent: Alex
# Source: exp_017
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
        return 0

    players_alive = 1 + len(alive_opponents)

    desperate_opponents = 0
    strong_prev_bid = 0
    avg_prev_bid = 0
    prev_count = 0
    failed_prev = 0

    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                if bid > strong_prev_bid:
                    strong_prev_bid = bid
                avg_prev_bid += bid
                prev_count += 1
            status = prev.get('status')
            if status is not None and status != 'ok':
                failed_prev += 1
            if prev.get('error'):
                failed_prev += 1

    if prev_count > 0:
        avg_prev_bid = avg_prev_bid / prev_count

    enough_for_all = supply >= players_alive * WATER_REQ
    enough_for_two = supply >= 2 * WATER_REQ

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

    if not enough_for_all:
        urgency += 2
    if supply <= MIN_SUPPLY + 1:
        urgency += 1
    if desperate_opponents >= max(1, len(alive_opponents) // 2):
        urgency += 1

    if len(alive_opponents) == 0:
        base_bid = DAILY_SALARY * 0.22
    elif urgency >= 6:
        base_bid = DAILY_SALARY * 0.96
    elif urgency >= 4:
        base_bid = DAILY_SALARY * 0.82
    elif urgency >= 2:
        base_bid = DAILY_SALARY * 0.62
    else:
        if enough_for_all:
            base_bid = DAILY_SALARY * 0.28
        elif enough_for_two:
            base_bid = DAILY_SALARY * 0.45
        else:
            base_bid = DAILY_SALARY * 0.58

    if prev_count > 0:
        if strong_prev_bid >= DAILY_SALARY * 0.9:
            if urgency >= 4:
                base_bid = max(base_bid, min(DAILY_SALARY * 0.97, strong_prev_bid + 1.0))
            else:
                base_bid = min(base_bid, DAILY_SALARY * 0.35)
        elif strong_prev_bid >= DAILY_SALARY * 0.65:
            if urgency >= 2:
                base_bid = max(base_bid, min(DAILY_SALARY * 0.9, strong_prev_bid + 1.5))
        elif strong_prev_bid > 0 and urgency >= 3:
            base_bid = max(base_bid, strong_prev_bid + 1.0)

    if failed_prev > 0:
        base_bid *= 0.95

    remaining_days = max(0, 10 - day)
    reserve = 0
    if remaining_days >= 4:
        reserve = DAILY_SALARY * 1.2
    elif remaining_days >= 2:
        reserve = DAILY_SALARY * 0.6

    max_affordable = max(0, budget - reserve)
    if urgency >= 5:
        max_affordable = budget

    bid = min(base_bid, budget)
    if max_affordable > 0:
        bid = min(bid, max_affordable) if urgency < 5 else min(base_bid, budget)
    else:
        bid = min(budget, DAILY_SALARY * 0.35) if urgency < 5 else min(budget, DAILY_SALARY * 0.9)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    if enough_for_all and urgency <= 1:
        bid = min(bid, DAILY_SALARY * 0.32)

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
            return float(min(budget, 35.0))
        return float(min(budget, 12.0))

    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 85:
                rich_aggressive += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = float(supply) <= 18.0
    abundant = float(supply) >= 22.0

    if hp <= 2 or no_water_days >= 2:
        if highest_prev >= 90:
            bid = 92.0
        elif highest_prev >= 75:
            bid = highest_prev + 2.0
        else:
            bid = 68.0 if scarcity else 58.0
        return float(min(budget, bid))

    if hp <= 4 or no_water_days >= 1:
        if scarcity:
            if highest_prev >= 88:
                bid = 72.0
            elif highest_prev >= 60:
                bid = highest_prev + 1.5
            else:
                bid = 52.0
        else:
            if highest_prev >= 88:
                bid = 48.0
            elif highest_prev >= 60:
                bid = highest_prev * 0.82
            else:
                bid = 38.0
        return float(min(budget, bid))

    if rich_aggressive >= 2:
        if abundant:
            bid = 9.0
        elif scarcity:
            bid = 18.0
        else:
            bid = 13.0
    else:
        if highest_prev >= 80:
            bid = 16.0 if hp >= 6 else 34.0
        elif highest_prev >= 40:
            bid = max(22.0, avg_prev * 0.7)
        else:
            bid = 26.0 if scarcity else 20.0

    if desperate_count >= 2:
        bid += 6.0
    elif desperate_count == 1:
        bid += 3.0

    if day >= 8 and hp >= 6:
        bid *= 0.85

    bid = max(0.0, min(budget, bid))
    return float(bid)
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    prev_bids = []
    strong_prev = 0.0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid') if prev else None
        if b is not None:
            prev_bids.append(float(b))
            if float(b) > strong_prev:
                strong_prev = float(b)

    competitor_pressure = 0
    for opp in alive:
        if opp.get('budget', 0) >= 90:
            competitor_pressure += 1

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    emergency = (hp <= 4) or (no_water >= 2)
    caution = (hp <= 6) or (no_water >= 1)

    if emergency:
        target = max(110.0, strong_prev + 3.0)
    elif tight_supply:
        target = max(78.0, min(108.0, strong_prev + 2.0))
    elif medium_supply:
        if caution:
            target = max(72.0, min(100.0, strong_prev * 0.82 + 4.0))
        else:
            target = 46.0 + 4.0 * competitor_pressure
    else:
        if caution:
            target = 62.0
        else:
            target = 28.0 + 3.0 * competitor_pressure

    if day >= 8 and hp >= 7 and no_water == 0:
        target *= 0.85

    if budget < target:
        if emergency:
            return float(budget)
        reserve = 0.0
        days_left = max(1, 10 - int(day) + 1)
        affordable = budget / days_left
        target = max(0.0, min(target, affordable * 1.4 + reserve))

    target = min(target, budget)
    if target < 0:
        target = 0.0
    return float(round(target, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_pressure = 0.0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if opp.get('budget', 0) > budget * 0.8:
                    rich_pressure = max(rich_pressure, bid)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = (supply <= 17)
    supply_loose = (supply >= 22)

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

    if supply_tight:
        urgency += 1
    elif supply_loose:
        urgency -= 1

    if budget < DAILY_SALARY * 2:
        urgency += 1

    if urgency <= 0:
        base = max(8.0, avg_prev * 0.45)
    elif urgency == 1:
        base = max(18.0, avg_prev * 0.65)
    elif urgency == 2:
        base = max(32.0, highest_prev * 0.72)
    elif urgency == 3:
        base = max(48.0, highest_prev + 2.0)
    else:
        base = max(62.0, highest_prev + 6.0)

    if rich_pressure > 0 and urgency >= 3:
        base = max(base, rich_pressure + 3.0)

    if supply_loose and urgency <= 1:
        base *= 0.82
    if supply_tight and urgency >= 2:
        base *= 1.08

    max_safe = budget
    if hp > 4 and no_water == 0:
        max_safe = min(max_safe, budget * 0.42)
    elif hp > 2:
        max_safe = min(max_safe, budget * 0.58)

    if urgency >= 4:
        max_safe = budget
    elif urgency == 3:
        max_safe = min(budget, max(max_safe, budget * 0.72))

    bid = min(base, max_safe)
    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, highest_prev + 8.0 if highest_prev > 0 else DAILY_SALARY * 0.9))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(round(bid, 2))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        base = DAILY_SALARY * 0.28
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.55
        return float(min(budget, base))

    prev_bids = []
    threat_bids = []
    eric_bid = None
    active_count = 0

    for oid, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        active_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 0) > 0 and opp.get('budget', 0) > 0:
                threat_bids.append(float(bid))
        if oid == 'Eric' and bid is not None:
            eric_bid = float(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    threat_prev = max(threat_bids) if threat_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.55
    elif hp <= 4:
        danger += 0.35
    elif hp <= 6:
        danger += 0.18
    if no_water_days >= 2:
        danger += 0.35
    elif no_water_days >= 1:
        danger += 0.18
    danger += 0.22 * scarcity
    if day >= 8:
        danger += 0.08

    target = DAILY_SALARY * (0.34 + 0.18 * scarcity)

    if eric_bid is not None:
        if danger >= 0.75:
            target = max(target, eric_bid + 2.0)
        elif danger >= 0.45:
            target = max(target, eric_bid * 0.78)
        else:
            target = max(target, eric_bid * 0.42)
    elif threat_prev > 0:
        if danger >= 0.75:
            target = max(target, threat_prev + 1.5)
        elif danger >= 0.45:
            target = max(target, threat_prev * 0.72)
        else:
            target = max(target, threat_prev * 0.4)

    if active_count >= 3 and supply <= 17:
        target += 8.0
    elif active_count <= 1:
        target *= 0.72

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    max_today = budget
    if budget > reserve_floor:
        max_today = budget - reserve_floor * 0.15

    if hp <= 2 or no_water_days >= 2:
        max_today = budget

    bid = min(max_today, target)
    bid = max(0.0, bid)

    if bid < 1.0 and budget >= 1.0:
        bid = 1.0

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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_prev_bids = []
    rich_prev_bids = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_prev_bids.append(float(bid))
                if opp.get('budget', 0) >= budget * 0.8:
                    rich_prev_bids.append(float(bid))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    slots_est = int(max(1, supply // WATER_REQ))
    pressure = len(alive) - slots_est

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_urgent = max(urgent_prev_bids) if urgent_prev_bids else highest_prev
    highest_rich = max(rich_prev_bids) if rich_prev_bids else highest_prev

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_urgent + 2.0, highest_rich + 1.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(DAILY_SALARY * (0.72 + 0.18 * scarcity), highest_urgent + 1.5)
    else:
        if pressure <= 0 and supply >= 22:
            bid = DAILY_SALARY * 0.18
        elif pressure <= 1 and supply >= 19:
            bid = max(DAILY_SALARY * 0.32, min(highest_prev * 0.72, DAILY_SALARY * 0.55))
        else:
            anchor = highest_prev + 1.25 if highest_prev > 0 else DAILY_SALARY * 0.58
            bid = max(DAILY_SALARY * (0.45 + 0.22 * scarcity), anchor)

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.9

    if budget < DAILY_SALARY * 0.6:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, max(DAILY_SALARY * 1.15, highest_prev + 3.0))

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 2:
            safe_bid = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, safe_bid)))

    prev_bids = []
    danger_bids = []
    strong_spenders = 0
    desperate_count = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        pbid = None
        if prev and prev.get('bid') is not None:
            pbid = prev.get('bid')
            prev_bids.append(pbid)
            if pbid >= DAILY_SALARY * 0.85:
                danger_bids.append(pbid)
        opp_hp = opp.get('hp', 0)
        opp_nw = opp.get('no_water_days', 0)
        opp_budget = opp.get('budget', 0)
        if opp_budget >= DAILY_SALARY * 2 and opp_hp >= 6:
            strong_spenders += 1
        if opp_hp <= 2 or opp_nw >= 2:
            desperate_count += 1

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = DAILY_SALARY * 0.45
        avg_prev = DAILY_SALARY * 0.4

    if hp <= 2 or no_water >= 2:
        target = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif hp <= 4 or no_water >= 1:
        if tight_supply:
            target = max(DAILY_SALARY * 0.78, avg_prev + 2.0)
        else:
            target = max(DAILY_SALARY * 0.68, avg_prev + 1.0)
    else:
        if loose_supply and highest_prev >= DAILY_SALARY * 1.5:
            target = DAILY_SALARY * 0.28
        elif tight_supply:
            target = max(DAILY_SALARY * 0.58, min(highest_prev + 1.5, DAILY_SALARY * 0.88))
        else:
            target = max(DAILY_SALARY * 0.42, min(avg_prev + 0.5, DAILY_SALARY * 0.72))

    if strong_spenders >= 1 and hp >= 5 and no_water == 0:
        target *= 0.92
    if desperate_count >= 2 and (hp <= 4 or tight_supply):
        target *= 1.08

    if day >= 8 and hp >= 5 and no_water == 0:
        target *= 0.9

    reserve_floor = DAILY_SALARY * 0.2
    max_affordable = budget
    if budget > reserve_floor:
        max_affordable = budget

    bid = min(target, max_affordable)
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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    dangerous_prev = 0.0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev.get('bid', 0.0))
                prev_bids.append(bid)
                if bid > dangerous_prev:
                    dangerous_prev = bid

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, min(budget, 35.0))
        return max(0.0, min(budget, 18.0))

    total_players = 1 + len(alive_opponents)
    expected_fair_share = supply / float(total_players)
    scarcity = expected_fair_share < WATER_REQ

    high_opp_pressure = dangerous_prev >= 110.0
    medium_opp_pressure = dangerous_prev >= 95.0

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

    if day >= 8:
        urgency += 1

    if scarcity:
        urgency += 1

    if urgency >= 5:
        target = max(120.0, dangerous_prev + 4.0)
    elif urgency >= 3:
        if high_opp_pressure:
            target = dangerous_prev + 2.5
        elif medium_opp_pressure:
            target = dangerous_prev + 1.5
        else:
            target = 96.0
    elif urgency >= 1:
        if scarcity:
            target = max(88.0, dangerous_prev - 6.0)
        else:
            target = 62.0
    else:
        if scarcity:
            target = max(72.0, dangerous_prev - 12.0)
        else:
            target = 28.0

    if budget < target:
        if urgency >= 4:
            target = budget
        elif urgency >= 2:
            target = min(budget, max(45.0, budget * 0.75))
        else:
            target = min(budget, max(15.0, budget * 0.45))

    if budget <= 0:
        return 0.0

    return max(0.0, min(budget, float(target)))
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_budgets = []
    urgent_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if not alive_opponents:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0
    max_opp_budget = max(opp_budgets) if opp_budgets else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        bid = max(88.0, highest_prev + 4.0)
        if tight_supply:
            bid += 10.0
        return max(0.0, min(budget, bid))

    if hp <= 4 or no_water_days >= 1:
        bid = max(62.0, avg_prev + 3.0)
        if tight_supply:
            bid += 8.0
        elif ample_supply:
            bid -= 6.0
        if urgent_opponents >= 1:
            bid += 5.0
        return max(0.0, min(budget, bid))

    bid = 36.0
    if tight_supply:
        bid = max(48.0, avg_prev * 0.62)
    elif ample_supply:
        bid = max(24.0, avg_prev * 0.38)
    else:
        bid = max(34.0, avg_prev * 0.5)

    if highest_prev >= 100.0:
        bid = min(bid, 52.0)
    if urgent_opponents >= 2:
        bid += 6.0
    if budget < DAILY_SALARY * 2:
        bid = min(bid, 40.0)
    if max_opp_budget < budget * 0.5:
        bid += 4.0

    return max(0.0, min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0.0)))
                except Exception:
                    pass

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 40.0))
        return float(min(budget, 12.0))

    high_pressure = max(prev_bids) if prev_bids else 0.0
    avg_pressure = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2 or no_water_days >= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency >= 3:
        bid = max(78.0, high_pressure + 2.0)
    elif scarcity == 2:
        if high_pressure >= 120:
            bid = 76.0 if urgency <= 1 else 96.0
        elif high_pressure >= 90:
            bid = high_pressure + 2.0
        else:
            bid = 74.0 + 8.0 * urgency
    elif scarcity == 1:
        if high_pressure >= 120:
            bid = 52.0 if urgency == 0 else 82.0
        elif high_pressure >= 85:
            bid = max(58.0, min(high_pressure + 1.5, 88.0 + 4.0 * urgency))
        else:
            bid = 42.0 + 8.0 * urgency
    else:
        if high_pressure >= 115:
            bid = 18.0 if urgency == 0 else 62.0
        elif avg_pressure >= 90:
            bid = 24.0 if urgency == 0 else 54.0
        else:
            bid = 16.0 + 6.0 * urgency

    if day >= 8:
        bid += 6.0 * urgency

    reserve_floor = 0.0
    days_left = 10 - day
    if days_left > 0 and urgency == 0:
        reserve_floor = min(budget * 0.35, days_left * 12.0)

    max_affordable = budget - reserve_floor
    if max_affordable < 0:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
"""
