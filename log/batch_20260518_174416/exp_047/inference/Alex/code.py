# ============================================================
# Experiment: exp_047
# Agent: Alex
# Source: exp_047
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

    alive = []
    prev_bids = []
    desperate_pressure = 0.0
    rich_competitors = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_competitors += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                weight = 1.0
                if opp.get('no_water_days', 0) >= 1:
                    weight += 0.2
                if opp.get('hp', 10) <= 3:
                    weight += 0.2
                if prev.get('status') == 'lost':
                    weight -= 0.15
                desperate_pressure = max(desperate_pressure, bid * weight)

    if budget <= 0:
        return 0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 35)
        return min(budget, 18)

    scarcity = 1.0 - ((supply - 15.0) / 10.0)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = 22 + 18 * scarcity

    if hp <= 2:
        base += 22
    elif hp <= 4:
        base += 10

    if no_water_days >= 2:
        base += 18
    elif no_water_days >= 1:
        base += 10

    base += min(rich_competitors * 2.5, 8)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = max(base, avg_prev + 2, desperate_pressure + 1.5)
        if highest_prev >= DAILY_SALARY * 0.9 and hp > 4 and no_water_days == 0 and supply >= 20:
            target = min(target, DAILY_SALARY * 0.42)
    else:
        target = base

    if day >= 8:
        target += 4
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        target += 8

    reserve_floor = DAILY_SALARY * max(0, 10 - day) * 0.18
    if budget < reserve_floor:
        target *= 0.82
    if budget < DAILY_SALARY:
        target *= 0.9

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.78)

    target = min(target, budget)
    if target < 0:
        target = 0
    return float(round(target, 2))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    HIGH_BID = 91.0

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
        return max(0.0, min(budget, 1.0))

    units = int(supply // WATER_REQ)
    if units < 0:
        units = 0

    active_threats = []
    max_prev_bid = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is None:
            prev_bid = 0.0
        if prev_bid > max_prev_bid:
            max_prev_bid = prev_bid
        if opp.get('budget', 0) > 0:
            active_threats.append((oid, opp, prev_bid))

    if not active_threats:
        return max(0.0, min(budget, 1.0))

    cindy_like = False
    for oid, opp, prev_bid in active_threats:
        req = opp.get('water_requirement', 0)
        sal = opp.get('daily_salary', 0)
        if prev_bid >= 89 and req == 13 and sal == 70:
            cindy_like = True

    urgent = hp <= 2 or no_water >= 2
    very_urgent = hp <= 1 or no_water >= 3

    if very_urgent:
        return max(0.0, min(budget, HIGH_BID if budget >= HIGH_BID else budget))

    if units >= len(active_threats) + 1:
        return max(0.0, min(budget, 0.0))

    if units >= 2 and cindy_like and len(active_threats) == 1:
        if urgent:
            return max(0.0, min(budget, 5.0))
        return max(0.0, min(budget, 0.0))

    if units <= 0:
        return 0.0

    if units == 1:
        if cindy_like:
            if urgent or day >= 8:
                return max(0.0, min(budget, HIGH_BID if budget >= HIGH_BID else budget))
            return max(0.0, min(budget, 0.0))
        target = max(35.0, min(80.0, max_prev_bid + 2.0))
        if urgent:
            target = max(target, 75.0)
        return max(0.0, min(budget, target))

    if urgent:
        return max(0.0, min(budget, 8.0))
    return max(0.0, min(budget, 0.0))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if budget <= 0:
        return 0.0

    total_players = 1 + len(alive)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < total_players
    very_tight = expected_units < max(1.5, total_players - 1)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if not alive:
        return float(min(budget, 18.0 if hp > 4 else 35.0))

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 2
    if day >= 8:
        danger += 1

    if danger >= 5:
        target = max(92.0, highest_prev + 3.0)
        if very_tight:
            target = max(target, 108.0)
        return float(min(budget, target))

    if scarcity:
        if highest_prev >= 120:
            target = 36.0 if danger <= 1 else 96.0
        elif highest_prev >= 90:
            target = 44.0 if danger <= 1 else highest_prev + 2.0
        else:
            target = max(38.0, avg_prev + 4.0, 48.0 + 6.0 * urgent_opp)
        if very_tight:
            target += 8.0
        if rich_opp >= 2 and danger <= 1:
            target -= 6.0
    else:
        if highest_prev >= 100:
            target = 24.0 if danger == 0 else 58.0
        else:
            target = 22.0 + 4.0 * urgent_opp
            if danger >= 2:
                target = max(target, avg_prev + 2.0, 46.0)

    if budget < 60:
        target = min(target, budget)
    elif budget < 120 and danger <= 1:
        target = min(target, 55.0)

    if hp >= 8 and no_water == 0 and highest_prev >= 110 and scarcity:
        target = min(target, 28.0)

    target = max(0.0, min(float(budget), float(target)))
    return float(target)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_live_bid = 0.0
    cindy_alive = False
    cindy_bid = None

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > strong_live_bid:
                    strong_live_bid = float(bid)
            if oid == 'Cindy':
                cindy_alive = True
                if bid is not None:
                    cindy_bid = float(bid)

    if not alive:
        return float(min(budget, 18.0))

    ratio = supply / float(WATER_REQ)
    very_tight = ratio < 1.35
    tight = ratio < 1.6
    comfortable = ratio >= 1.8

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
    if day >= 8:
        urgency += 1

    if cindy_alive and cindy_bid is not None and cindy_bid >= 150 and urgency <= 1 and not very_tight:
        return float(min(budget, 6.0 if comfortable else 12.0))

    target = 0.0

    if urgency >= 5:
        target = 0.96 * DAILY_SALARY
        if cindy_bid is not None and cindy_bid < 0.9 * DAILY_SALARY:
            target = max(target, cindy_bid + 3.0)
    elif urgency >= 3:
        if very_tight:
            target = max(0.88 * DAILY_SALARY, strong_live_bid + 2.5)
        elif tight:
            target = max(0.72 * DAILY_SALARY, min(strong_live_bid + 1.5, 0.9 * DAILY_SALARY))
        else:
            target = 0.52 * DAILY_SALARY
    else:
        if very_tight:
            if strong_live_bid > 0:
                if strong_live_bid <= 70:
                    target = max(48.0, strong_live_bid + 1.2)
                elif strong_live_bid <= 110:
                    target = min(76.0, strong_live_bid + 1.0)
                else:
                    target = 14.0
            else:
                target = 46.0
        elif tight:
            if cindy_bid is not None and cindy_bid >= 140:
                target = 10.0
            else:
                target = 28.0 if comfortable else 34.0
        else:
            target = 8.0 if cindy_alive else 18.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if urgency <= 1 and days_left >= 3:
        reserve_floor = 20.0
    bid = min(budget, target)
    if budget - bid < reserve_floor:
        bid = max(0.0, budget - reserve_floor)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 63.0))

    return float(max(0.0, round(bid, 2)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    threat_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    threat_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    cindy_bid = None
    cindy_budget = 0.0
    cindy_alive = False
    if 'Cindy' in opponents_status:
        c = opponents_status['Cindy']
        cindy_alive = bool(c.get('alive'))
        cindy_budget = float(c.get('budget', 0.0))
        prev = c.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            cindy_bid = float(prev.get('bid'))

    urgent = hp <= 4 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        target = max(92.0, (cindy_bid + 2.0) if cindy_bid is not None else 96.0)
        return float(min(budget, target))

    if slots >= 2:
        if urgent:
            if cindy_alive and cindy_bid is not None:
                target = max(58.0, min(88.0, cindy_bid * 0.72))
            else:
                target = max(52.0, avg_prev + 4.0)
        else:
            if max_prev >= 100:
                target = 31.0
            elif max_prev >= 70:
                target = 38.0
            else:
                target = 44.0
    else:
        if cindy_alive and cindy_budget > 0:
            if urgent:
                target = max(98.0, (cindy_bid + 3.0) if cindy_bid is not None else 102.0)
            else:
                target = max(72.0, min(96.0, (cindy_bid - 6.0) if cindy_bid is not None else 78.0))
        else:
            target = max(55.0, avg_prev + 6.0)

    if budget < DAILY_SALARY * 1.2 and not urgent:
        target = min(target, 42.0)

    return float(max(0.0, min(budget, target)))
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
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                    dangerous_prev.append(bid)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    urgency += min(0.5, 0.22 * no_water)
    if day >= 8:
        urgency += 0.1

    base = DAILY_SALARY * (0.28 + 0.42 * scarcity + urgency)

    if not alive_opponents:
        bid = min(budget, DAILY_SALARY * 0.35)
        return max(0.0, float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0
    danger_prev = max(dangerous_prev) if dangerous_prev else highest_prev

    if supply >= 22:
        target = max(DAILY_SALARY * 0.22, avg_prev * 0.72)
    elif supply >= 19:
        target = max(DAILY_SALARY * 0.38, avg_prev * 0.9)
    else:
        target = max(DAILY_SALARY * 0.55, danger_prev + 2.0)

    if highest_prev >= 100 and hp >= 5 and no_water == 0 and supply >= 19:
        target = min(target, DAILY_SALARY * 0.34)

    if hp <= 2 or no_water >= 2:
        target = max(target, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water >= 1:
        target = max(target, DAILY_SALARY * 0.72)

    bid = max(base, target)

    remaining_days = max(1, 10 - int(day) + 1)
    reserve_floor = DAILY_SALARY * 0.22 * remaining_days
    spend_cap = budget
    if hp >= 5 and no_water == 0:
        spend_cap = max(0.0, budget - reserve_floor)
        if spend_cap <= 0:
            spend_cap = min(budget, DAILY_SALARY * 0.4)

    if supply <= 17 and (hp <= 4 or no_water >= 1):
        spend_cap = budget

    bid = min(bid, spend_cap, budget)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_threats = 0
    soft_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_threats += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid <= 80:
                    soft_count += 1

    if not alive:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 23
    critical = (hp <= 3) or (no_water >= 2)
    urgent = (hp <= 5) or (no_water >= 1)

    if critical:
        if highest_prev >= 135:
            bid = 143.0
        else:
            bid = max(95.0, highest_prev + 3.0)
        return max(0.0, min(budget, bid))

    if urgent and tight_supply:
        if highest_prev >= 135:
            bid = 142.6
        else:
            bid = max(88.0, highest_prev + 2.5)
        return max(0.0, min(budget, bid))

    if highest_prev >= 135:
        if ample_supply and hp >= 7 and no_water == 0:
            bid = 8.0
        elif hp >= 6:
            bid = 15.0
        else:
            bid = 40.0
        return max(0.0, min(budget, bid))

    if soft_count > 0:
        target = max(45.0, lowest_prev + 2.0)
        if tight_supply:
            target += 8.0
        if hp <= 6:
            target += 10.0
        bid = target
    else:
        bid = 28.0
        if tight_supply:
            bid += 10.0
        if ample_supply:
            bid -= 6.0
        if rich_threats >= 2:
            bid -= 5.0
        if hp <= 6:
            bid += 8.0
        if no_water >= 1:
            bid += 10.0

    if day >= 8 and hp >= 7 and no_water == 0 and highest_prev >= 100:
        bid = min(bid, 18.0)

    return max(0.0, min(budget, bid))
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
    prev_bids = []
    prev_named = {}
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                prev_named[agent_id] = bid

    if not alive:
        base = DAILY_SALARY * 0.18
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return max(0.0, min(budget, base))

    alive_count = len(alive)
    severe_need = hp <= 2 or no_water_days >= 2
    urgent_need = hp <= 4 or no_water_days >= 1
    scarce = supply <= 16
    tight = supply <= 19

    highest_prev = max(prev_bids) if prev_bids else 0.0
    bob_prev = prev_named.get('Bob', 0.0)
    cindy_prev = prev_named.get('Cindy', 0.0)

    base = DAILY_SALARY * 0.38

    if alive_count <= 1:
        base = DAILY_SALARY * 0.22
    elif alive_count == 2:
        base = DAILY_SALARY * 0.32

    if tight:
        base += 6.0
    if scarce:
        base += 8.0

    if highest_prev >= 110:
        if severe_need:
            base = max(base, min(DAILY_SALARY * 0.92, highest_prev * 0.78))
        elif urgent_need:
            base = max(base, DAILY_SALARY * 0.62)
        else:
            base = min(base, DAILY_SALARY * 0.42)
    elif highest_prev >= 70:
        if urgent_need:
            base = max(base, min(DAILY_SALARY * 0.88, bob_prev + 4.0 if bob_prev > 0 else highest_prev + 2.0))
        else:
            base = max(base, DAILY_SALARY * 0.48)
    elif highest_prev > 0:
        base = max(base, highest_prev + 2.0)

    if cindy_prev >= 120 and not urgent_need:
        base = min(base, DAILY_SALARY * 0.4)

    if severe_need:
        base = max(base, DAILY_SALARY * 0.9)
        if scarce:
            base = max(base, DAILY_SALARY * 0.96)
    elif urgent_need:
        base = max(base, DAILY_SALARY * 0.68)
        if scarce:
            base = max(base, DAILY_SALARY * 0.78)

    if budget < DAILY_SALARY * 1.2:
        base = min(base, budget)
    elif budget > DAILY_SALARY * 8 and severe_need:
        base = max(base, DAILY_SALARY * 0.98)

    if day >= 8 and hp > 5 and not urgent_need:
        base = min(base, DAILY_SALARY * 0.36)

    bid = max(0.0, min(budget, base))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_reqs = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
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

    supply_ratio = 1.0
    if total_req > 0:
        supply_ratio = float(supply) / float(total_req)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    if supply <= 16:
        market_pressure = 'tight'
    elif supply >= 22:
        market_pressure = 'loose'
    else:
        market_pressure = 'mid'

    urgent = (hp <= 3) or (no_water_days >= 2)
    semi_urgent = (hp <= 5) or (no_water_days >= 1)

    if not alive_opponents:
        if urgent:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    if urgent:
        base = max(DAILY_SALARY * 0.95, highest_prev + 2.5, avg_prev + 3.0)
    elif market_pressure == 'tight' or supply_ratio < 0.34:
        base = max(DAILY_SALARY * 1.08, highest_prev + 1.2, avg_prev + 2.0)
    elif market_pressure == 'mid' or supply_ratio < 0.42:
        base = max(DAILY_SALARY * 0.98, highest_prev + 0.8, avg_prev + 1.0)
    else:
        if semi_urgent:
            base = max(DAILY_SALARY * 0.82, avg_prev)
        else:
            base = DAILY_SALARY * 0.58

    if day >= 8 and hp > 5 and no_water_days == 0 and market_pressure == 'loose':
        base *= 0.9

    if budget < DAILY_SALARY * 1.2 and not urgent:
        base = min(base, DAILY_SALARY * 0.85)

    bid = min(float(budget), float(base))
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    bob_bid = None
    cindy_bid = None
    max_prev = 0.0
    for agent_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        bid_val = prev.get('bid')
        if bid_val is not None:
            bid_val = float(bid_val)
            prev_bids.append(bid_val)
            if bid_val > max_prev:
                max_prev = bid_val
            if agent_id == 'Bob':
                bob_bid = bid_val
            if agent_id == 'Cindy':
                cindy_bid = bid_val

    units = int(supply // WATER_REQ)
    urgent = (hp <= 4) or (no_water_days >= 2)
    very_urgent = (hp <= 2) or (no_water_days >= 3)

    if bob_bid is None:
        bob_bid = 60.0
    if cindy_bid is None:
        cindy_bid = 147.0

    alive_count = len(alive)
    likely_cindy_alive = False
    for agent_id, opp in opponents_status.items():
        if agent_id == 'Cindy' and opp.get('alive'):
            likely_cindy_alive = True
            break

    if very_urgent:
        if likely_cindy_alive:
            bid = min(budget, max(DAILY_SALARY * 1.05, bob_bid + 8.0))
        else:
            bid = min(budget, bob_bid + 6.0)
        return float(max(0.0, bid))

    if units <= 1:
        if urgent:
            bid = min(budget, max(DAILY_SALARY * 0.92, bob_bid + 4.0))
        else:
            bid = min(budget, DAILY_SALARY * 0.08)
        return float(max(0.0, bid))

    if units >= 2:
        if likely_cindy_alive:
            if urgent:
                bid = min(budget, max(bob_bid + 3.0, DAILY_SALARY * 0.92))
            else:
                bid = min(budget, max(bob_bid + 2.0, DAILY_SALARY * 0.9))
        else:
            if urgent:
                bid = min(budget, max(bob_bid + 2.0, DAILY_SALARY * 0.78))
            else:
                bid = min(budget, max(bob_bid + 1.5, DAILY_SALARY * 0.72))
    else:
        bid = min(budget, DAILY_SALARY * 0.5)

    if day >= 8 and hp >= 7 and no_water_days == 0 and units <= 1:
        bid = min(budget, DAILY_SALARY * 0.05)

    if budget < bid:
        bid = budget

    return float(max(0.0, bid))
"""
