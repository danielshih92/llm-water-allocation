# ============================================================
# Experiment: exp_078
# Agent: Alex
# Source: exp_078
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

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return min(budget, 50)
        return min(budget, 28)

    total_players = 1 + len(alive_opponents)
    expected_coverage = float(supply) / float(WATER_REQ)
    scarcity = total_players - expected_coverage

    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            desperate_count += 1
        if opp.get('budget', 0) > budget and prev and prev.get('bid') is not None and prev.get('bid') >= 45:
            rich_aggressive += 1

    if hp <= 2:
        base = 62
    elif no_water >= 2:
        base = 60
    elif no_water >= 1:
        base = 50
    else:
        if scarcity >= 2.5:
            base = 48
        elif scarcity >= 1.5:
            base = 40
        elif scarcity >= 0.5:
            base = 33
        else:
            base = 24

    if prev_bids:
        highest_prev = max(prev_bids)
        if hp <= 3 or no_water >= 1:
            base = max(base, min(65, highest_prev + 3))
        else:
            if highest_prev >= 60:
                base = min(base, 30)
            elif highest_prev >= 45:
                base = max(base, 36)
            else:
                base = max(base, highest_prev + 2)

    base += min(desperate_count, 2) * 3
    base += min(rich_aggressive, 2) * 2

    if budget < DAILY_SALARY * 1.2:
        base = min(base, 42)
    if budget < DAILY_SALARY * 0.7:
        base = min(base, 32)

    if hp >= 7 and no_water == 0 and scarcity < 1 and desperate_count == 0:
        base = min(base, 26)

    bid = max(0, min(budget, base))
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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply / WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    prev_high = 0.0
    prev_low = None
    desperate_count = 0
    rich_aggressive = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
            if bid > prev_high:
                prev_high = bid
            if prev_low is None or bid < prev_low:
                prev_low = bid
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 700 and bid is not None and bid >= 90:
            rich_aggressive += 1

    alive_count = len(alive)

    if alive_count == 0:
        return float(min(budget, 18.0))

    if hp <= 2 or no_water >= 2:
        emergency = max(92.0, prev_high + 3.0)
        return float(min(budget, emergency))

    if hp <= 4 or no_water >= 1:
        urgent = max(78.0, prev_high * 0.92 if prev_high > 0 else 78.0)
        return float(min(budget, urgent))

    if slots >= 2:
        base = 24.0
        if prev_low is not None:
            base = max(base, min(48.0, prev_low + 1.5))
        if desperate_count >= 2:
            base += 6.0
        if rich_aggressive >= 2:
            base += 4.0
        return float(min(budget, base))

    if slots <= 1:
        contest = 0.0
        if prev_high > 0:
            contest = prev_high + 2.5
        else:
            contest = 86.0
        if desperate_count >= 1:
            contest += 4.0
        if rich_aggressive >= 2:
            contest += 6.0
        if day >= 8 and hp >= 7:
            contest -= 8.0
        contest = max(72.0, contest)
        return float(min(budget, contest))

    mid = 42.0
    if prev_high > 0:
        mid = max(mid, min(68.0, prev_high * 0.6))
    if day >= 8 and hp >= 8:
        mid -= 6.0
    return float(min(budget, mid))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        base = 18.0 if hp > 4 else 42.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_prev_bids = []
    rich_urgent_prev_bids = []
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(float(bid))
            opp_urgent = opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1
            if opp_urgent:
                urgent_prev_bids.append(float(bid))
                if opp.get('budget', 0) >= float(bid):
                    rich_urgent_prev_bids.append(float(bid))

    tight_supply = supply <= 17.0
    loose_supply = supply >= 22.0

    base = 32.0
    if loose_supply:
        base = 24.0
    elif tight_supply:
        base = 46.0

    if hp <= 2 or no_water >= 2:
        base = max(base, 92.0)
    elif hp <= 4 or no_water >= 1:
        base = max(base, 68.0)
    elif hp >= 8 and no_water == 0 and loose_supply:
        base = min(base, 22.0)

    if rich_urgent_prev_bids:
        target = max(rich_urgent_prev_bids) + 2.0
        if hp <= 4 or no_water >= 1:
            base = max(base, target)
        else:
            base = max(base, min(target, 58.0))
    elif urgent_prev_bids:
        target = max(urgent_prev_bids) + 1.0
        if hp <= 4 or no_water >= 1:
            base = max(base, min(target, 85.0))
    elif prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev <= 60.0:
            base = max(base, highest_prev + 2.0)
        elif highest_prev >= 120.0 and hp > 4 and no_water == 0:
            base = min(base, 36.0)

    if day >= 8:
        if hp <= 4 or no_water >= 1:
            base += 10.0
        else:
            base += 4.0

    bid = min(float(budget), float(base))
    if bid < 0:
        bid = 0.0
    return float(bid)
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((oid, opp))

    if not alive_opps:
        if hp <= 2 or no_water_days >= 2:
            return max(0.0, min(budget, 63.0))
        return max(0.0, min(budget, 18.0))

    highest_prev = 0.0
    cindy_prev = None
    cindy_alive = False
    for oid, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            if bid > highest_prev:
                highest_prev = bid
        if oid == 'Cindy':
            cindy_alive = True
            if bid is not None:
                cindy_prev = bid

    severe_need = hp <= 2 or no_water_days >= 2
    urgent_need = hp <= 4 or no_water_days >= 1

    if cindy_alive:
        anchor = cindy_prev if cindy_prev is not None else highest_prev
        if severe_need:
            bid = min(budget, max(92.0, anchor + 2.0))
            return max(0.0, bid)
        if supply >= 22:
            bid = min(budget, 58.0)
            return max(0.0, bid)
        if supply >= 19:
            bid = min(budget, 28.0 if not urgent_need else 72.0)
            return max(0.0, bid)
        bid = min(budget, 8.0 if hp > 5 else 18.0)
        return max(0.0, bid)

    if severe_need:
        return max(0.0, min(budget, 75.0))
    if highest_prev >= 60.0:
        return max(0.0, min(budget, 35.0))
    if highest_prev > 0.0:
        return max(0.0, min(budget, highest_prev + 2.0))
    return max(0.0, min(budget, 24.0))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    yesterday_bids = []
    strong_pressure = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                yesterday_bids.append(bid)
                if bid >= 110:
                    strong_pressure += 1

    if not alive_opponents:
        return min(budget, 18.0)

    high_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1
    if tight_supply:
        danger += 2
    elif medium_supply:
        danger += 1
    if strong_pressure >= 2:
        danger += 1

    if danger >= 5:
        bid = max(120.0, high_prev + 4.0, avg_prev + 10.0)
    elif danger >= 3:
        bid = max(82.0, min(118.0, high_prev * 0.78 + 6.0))
    elif danger >= 2:
        bid = max(48.0, min(85.0, avg_prev * 0.45 + 8.0))
    else:
        bid = 22.0 if supply >= 22 else 30.0
        if high_prev < 80:
            bid = max(bid, high_prev * 0.4 + 3.0)

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, max(18.0, budget * 0.55))
    elif budget < DAILY_SALARY * 2.5:
        bid = min(bid, budget * 0.75)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, max(95.0, high_prev + 2.0)))

    bid = min(budget, bid)
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
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    eric_bid = None
    cindy_bid = None
    urgent_opponents = 0

    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            urgent_opponents += 1

    if 'Eric' in opponents_status and opponents_status['Eric'].get('alive'):
        prev = (opponents_status['Eric'].get('previous_trace', {}) or {})
        if prev.get('bid') is not None:
            eric_bid = float(prev.get('bid'))

    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('alive'):
        prev = (opponents_status['Cindy'].get('previous_trace', {}) or {})
        if prev.get('bid') is not None:
            cindy_bid = float(prev.get('bid'))

    low_supply = supply <= 17
    high_supply = supply >= 22
    danger = no_water_days >= 2 or hp <= 4
    moderate = no_water_days >= 1 or hp <= 6

    target = 24.0

    if eric_bid is not None:
        target = max(target, eric_bid + 2.0)
    elif prev_bids:
        target = max(target, max(prev_bids) * 0.78 + 1.0)

    if cindy_bid is not None and cindy_bid >= 120:
        target = min(target, 72.0)

    if high_supply and not danger:
        target *= 0.72
    elif low_supply:
        target *= 1.22

    if urgent_opponents >= 2:
        target *= 1.12

    if moderate:
        target = max(target, 46.0)
    if danger:
        target = max(target, 68.0)

    days_left = max(1, 10 - day + 1)
    reserve_floor = days_left * 12.0
    affordable = max(0.0, budget - reserve_floor)

    if danger:
        cap = min(budget, max(affordable + 20.0, DAILY_SALARY * 1.05))
    else:
        cap = min(budget, max(affordable, 22.0))

    bid = min(target, cap)

    if bid < 0:
        bid = 0.0

    if not danger and high_supply and budget < 120:
        bid = min(bid, 18.0)

    return float(max(0.0, min(budget, round(bid, 2))))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive_count = 0
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 110:
                    aggressive_count += 1
                    if opp.get('budget', 0) >= 500:
                        rich_aggressive += 1

    if not alive:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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
        target = max(95.0, highest_prev + 3.0)
        if scarcity == 2:
            target = max(target, 118.0)
        return max(0.0, min(budget, target))

    if scarcity == 2:
        if urgency >= 2:
            target = max(88.0, avg_prev + 4.0, highest_prev * 0.9)
        else:
            if rich_aggressive >= 2:
                target = 22.0
            else:
                target = max(72.0, avg_prev * 0.72)
        return max(0.0, min(budget, target))

    if scarcity == 1:
        if urgency >= 2:
            target = max(76.0, avg_prev * 0.7, highest_prev * 0.62)
        else:
            if aggressive_count >= 2:
                target = 18.0
            else:
                target = max(48.0, avg_prev * 0.45)
        return max(0.0, min(budget, target))

    if urgency >= 2:
        target = max(58.0, avg_prev * 0.5)
    elif urgency == 1:
        target = 36.0 if aggressive_count >= 2 else 44.0
    else:
        target = 14.0 if aggressive_count >= 1 else 24.0

    if day >= 8 and hp >= 7 and no_water_days == 0:
        target *= 0.8

    return max(0.0, min(budget, target))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 2:
            safe_bid = DAILY_SALARY * 0.75
        return float(min(budget, safe_bid))

    est_slots = max(1, int(float(supply) / float(WATER_REQ)))
    scarcity = 0
    if est_slots <= 1:
        scarcity = 2
    elif est_slots <= 2:
        scarcity = 1

    opp_infos = []
    prev_bids = []
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = None
        if prev and prev.get('bid') is not None:
            pbid = float(prev.get('bid'))
            prev_bids.append(pbid)
        danger = 0.0
        if opp.get('no_water_days', 0) >= 2:
            danger += 25.0
        elif opp.get('no_water_days', 0) == 1:
            danger += 10.0
        if opp.get('hp', 10) <= 2:
            danger += 20.0
        elif opp.get('hp', 10) <= 4:
            danger += 8.0
        if pbid is not None:
            danger += min(pbid, 120.0) * 0.35
        else:
            danger += 18.0
        opp_infos.append((agent_id, opp, pbid, danger))

    opp_infos.sort(key=lambda x: x[3], reverse=True)
    top_prev = 0.0
    if prev_bids:
        top_prev = max(prev_bids)

    urgent_self = (hp <= 2) or (no_water >= 2)
    pressured_self = (hp <= 4) or (no_water >= 1)

    base = DAILY_SALARY * 0.38
    if scarcity == 1:
        base = DAILY_SALARY * 0.52
    if scarcity == 2:
        base = DAILY_SALARY * 0.68
    if pressured_self:
        base += 10.0
    if urgent_self:
        base += 18.0

    target_bid = base

    if opp_infos:
        _, top_opp, top_pbid, _ = opp_infos[int(0)]
        if top_pbid is not None:
            if urgent_self:
                target_bid = max(target_bid, top_pbid + 2.5)
            elif scarcity >= 1 and top_pbid <= DAILY_SALARY * 1.15:
                target_bid = max(target_bid, top_pbid + 1.2)
            elif top_pbid >= 110.0 and not pressured_self:
                target_bid = min(target_bid, DAILY_SALARY * 0.42)
        if top_opp.get('budget', 0) < target_bid and top_opp.get('budget', 0) > 0:
            target_bid = max(base, float(top_opp.get('budget', 0)) + 0.5)

    if top_prev >= 120.0 and not urgent_self:
        target_bid = min(target_bid, DAILY_SALARY * 0.4)
    elif top_prev >= 95.0 and not pressured_self:
        target_bid = min(target_bid, DAILY_SALARY * 0.48)

    if day >= 8:
        target_bid += 6.0
    if day >= 9 and pressured_self:
        target_bid += 8.0

    reserve_floor = 0.0
    days_left = max(0, 10 - int(day))
    if days_left > 0:
        reserve_floor = min(budget, days_left * DAILY_SALARY * 0.18)
    max_spend = max(0.0, budget - reserve_floor)
    if urgent_self:
        max_spend = budget

    bid = min(target_bid, max_spend if max_spend > 0 else budget)
    bid = max(0.0, bid)

    if urgent_self and bid < DAILY_SALARY * 0.72:
        bid = min(budget, DAILY_SALARY * 0.72)
    if scarcity == 2 and pressured_self and bid < DAILY_SALARY * 0.8:
        bid = min(budget, DAILY_SALARY * 0.8)

    return float(min(budget, round(bid, 2)))
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
    cindy_bid = None
    david_bid = None
    highest_prev = 0.0
    second_prev = 0.0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= highest_prev:
                second_prev = highest_prev
                highest_prev = float(bid)
            elif float(bid) > second_prev:
                second_prev = float(bid)
            if oid == 'Cindy':
                cindy_bid = float(bid)
            if oid == 'David':
                david_bid = float(bid)

    guaranteed_units = int(supply // WATER_REQ)
    contested = guaranteed_units <= 1
    abundant = guaranteed_units >= 2

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1
    if contested:
        danger += 2
    elif not abundant:
        danger += 1

    if cindy_bid is None:
        cindy_bid = 118.0
    if david_bid is None:
        david_bid = 82.0

    target = DAILY_SALARY * 0.45

    if danger >= 5:
        target = max(target, cindy_bid + 2.0)
    elif danger >= 3:
        target = max(target, david_bid + 3.0)
        if contested:
            target = max(target, highest_prev + 1.5)
    else:
        if contested:
            target = max(target, david_bid + 1.0)
        else:
            target = max(target, DAILY_SALARY * 0.42)

    if hp >= 8 and no_water_days == 0 and contested and cindy_bid >= DAILY_SALARY * 1.5:
        target = min(target, DAILY_SALARY * 0.55)

    if budget < DAILY_SALARY * 1.2:
        target = min(target, budget)
    elif budget < DAILY_SALARY * 2.0 and danger < 4:
        target = min(target, DAILY_SALARY * 0.85)

    if day >= 8:
        target *= 1.1
    if day >= 9 and danger >= 3:
        target *= 1.1

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 1.15)

    bid = max(0.0, min(float(budget), float(target)))
    return float(round(bid, 4))
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
        base = 18.0 if hp > 3 else 35.0
        return float(max(0.0, min(budget, base)))

    pressure_bids = []
    req_pressure = []
    desperate_count = 0
    rich_count = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is not None:
            pressure_bids.append(float(prev_bid))
        opp_req = opp.get('water_requirement', WATER_REQ)
        if opp_req > 0:
            req_pressure.append(float(opp_req))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 120:
            rich_count += 1

    highest_prev = max(pressure_bids) if pressure_bids else 0.0
    avg_prev = sum(pressure_bids) / len(pressure_bids) if pressure_bids else 0.0
    max_req = max(req_pressure) if req_pressure else WATER_REQ

    scarcity_ratio = supply / float(WATER_REQ + max_req)
    low_supply = supply <= 18.0
    severe_scarcity = scarcity_ratio < 1.0

    emergency = hp <= 2 or no_water >= 2
    caution = hp <= 4 or no_water >= 1

    if emergency:
        bid = max(62.0, highest_prev + 4.0, avg_prev + 8.0)
        if severe_scarcity:
            bid = max(bid, 78.0)
        return float(max(0.0, min(budget, bid)))

    if caution:
        if highest_prev >= 120.0:
            bid = 58.0 if not severe_scarcity else 74.0
        else:
            bid = max(46.0, highest_prev + 2.5)
            if low_supply:
                bid += 6.0
        return float(max(0.0, min(budget, bid)))

    if highest_prev >= 135.0:
        bid = 16.0 if hp >= 6 else 28.0
    elif highest_prev >= 100.0:
        bid = 24.0 if not low_supply else 34.0
    elif highest_prev > 0.0:
        bid = max(22.0, min(52.0, highest_prev + 1.5))
    else:
        bid = 26.0

    if severe_scarcity:
        bid += 8.0
    elif low_supply:
        bid += 4.0

    if desperate_count >= 2:
        bid += 4.0
    if rich_count >= 2 and highest_prev >= 90.0:
        bid -= 3.0

    if day >= 8 and hp >= 6:
        bid -= 4.0

    reserve_floor = 12.0 if day < 8 else 0.0
    max_spend = max(0.0, budget - reserve_floor)
    bid = min(bid, max_spend)

    return float(max(0.0, min(budget, bid)))
"""
