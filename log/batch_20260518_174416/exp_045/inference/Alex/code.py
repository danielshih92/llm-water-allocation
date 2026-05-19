# ============================================================
# Experiment: exp_045
# Agent: Alex
# Source: exp_045
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    error_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            if prev.get('error'):
                error_count += 1

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 50)
        return min(budget, 24)

    base = DAILY_SALARY * 0.42

    if supply >= 22:
        base -= 5
    elif supply <= 17:
        base += 8

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.68)

    if no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.88)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if highest_prev >= DAILY_SALARY * 0.9:
            if hp > 4 and no_water_days == 0 and supply >= 20:
                base = min(base, DAILY_SALARY * 0.34)
            else:
                base = max(base, DAILY_SALARY * 0.93)
        elif highest_prev >= DAILY_SALARY * 0.7:
            base = max(base, highest_prev + 2)
        else:
            base = max(base, avg_prev + 1.5)
    else:
        base = max(base, DAILY_SALARY * 0.5)

    if desperate_count >= 2:
        base += 4
    elif desperate_count == 1:
        base += 2

    if error_count >= 1:
        base -= 2

    if day >= 8 and hp > 4 and no_water_days == 0:
        base -= 2

    reserve_floor = 0
    if day < 8:
        reserve_floor = DAILY_SALARY * 0.15

    bid = min(float(budget), max(0.0, base))
    if budget - bid < reserve_floor and budget > reserve_floor:
        bid = max(0.0, budget - reserve_floor)

    if hp <= 2 or no_water_days >= 1:
        bid = min(float(budget), max(bid, DAILY_SALARY * 0.9))

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
    no_water = my_status['no_water_days']

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opps:
        bid = min(budget, DAILY_SALARY * 0.2)
        return float(max(0.0, bid))

    prev_bids = []
    desperate_opp = False
    rich_opp = False
    for opp in alive_opps:
        if opp.get('budget', 0) >= 120:
            rich_opp = True
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp = True
        prev = opp.get('previous_trace', {})
        if prev:
            b = prev.get('bid')
            if b is not None:
                prev_bids.append(float(b))
            if prev.get('status') == 'won':
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = int(supply // WATER_REQ)
    if units < 1:
        units = 1

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 2.0)
    elif urgent:
        bid = max(0.72 * DAILY_SALARY, min(0.98 * DAILY_SALARY, highest_prev + 1.5))
    else:
        if units >= 2:
            bid = 0.34 * DAILY_SALARY
            if highest_prev > 120:
                bid = 0.28 * DAILY_SALARY
            elif avg_prev > 90:
                bid = 0.31 * DAILY_SALARY
        else:
            bid = 0.56 * DAILY_SALARY
            if highest_prev >= 140:
                bid = 0.46 * DAILY_SALARY
            elif highest_prev >= 110:
                bid = 0.52 * DAILY_SALARY

    if desperate_opp and not urgent:
        bid *= 0.92
    if rich_opp and units < 2 and urgent:
        bid = max(bid, highest_prev + 1.0)

    remaining_days = 10 - day
    reserve_target = max(0.0, remaining_days * DAILY_SALARY * 0.38)
    max_affordable = budget
    if budget > reserve_target:
        max_affordable = budget - reserve_target + DAILY_SALARY * 0.25

    bid = min(bid, max_affordable, budget)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    day = day_context['day']
    supply = day_context['supply']
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
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    aggressive_count = 0
    weak_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 110:
                aggressive_count += 1
            if bid <= 40:
                weak_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = float(supply) / float(WATER_REQ)
    contested = supply_ratio < 2.0
    very_tight = supply_ratio < 1.35

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

    if very_tight:
        urgency += 2
    elif contested:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        target = max(0.92 * DAILY_SALARY, highest_prev + 6.0)
        if aggressive_count >= 2:
            target = max(target, avg_prev + 4.0)
    elif urgency >= 4:
        target = max(0.72 * DAILY_SALARY, min(0.98 * DAILY_SALARY, highest_prev + 2.5))
    elif urgency >= 2:
        if contested:
            target = max(0.52 * DAILY_SALARY, min(0.82 * DAILY_SALARY, avg_prev * 0.7 + 8.0))
        else:
            target = 0.42 * DAILY_SALARY
    else:
        if weak_count >= 1 and not contested:
            target = 0.26 * DAILY_SALARY
        elif highest_prev >= 150:
            target = 0.22 * DAILY_SALARY
        elif highest_prev >= 100:
            target = 0.28 * DAILY_SALARY
        else:
            target = 0.34 * DAILY_SALARY

    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0:
        soft_cap = min(soft_cap, budget * 0.55)
        if urgency <= 1:
            soft_cap = min(soft_cap, budget / float(reserve_days + 1) + 8.0)

    if hp <= 2 or no_water_days >= 2:
        soft_cap = budget

    bid = min(budget, max(0.0, min(target, soft_cap)))

    if budget < 25:
        bid = min(budget, max(bid, budget * 0.85 if urgency >= 4 else budget * 0.55))

    return float(max(0.0, bid))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    opp_pressures = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            pressure = 0.0
            if opp.get('no_water_days', 0) >= 1:
                pressure += 1.0
            if opp.get('hp', 10) <= 4:
                pressure += 1.0
            if opp.get('budget', 0) > budget:
                pressure += 0.5
            opp_pressures.append(pressure)

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    urgent_opps = 0
    for opp in alive:
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
            urgent_opps += 1

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        target = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
        if tight_supply:
            target = max(target, 78.0)
        return float(min(budget, target))

    if hp <= 4 or no_water_days >= 1:
        target = max(0.72 * DAILY_SALARY, min(highest_prev + 2.0, 0.95 * DAILY_SALARY))
        if tight_supply:
            target = max(target, 60.0)
        return float(min(budget, target))

    if loose_supply and highest_prev >= 120:
        return float(min(budget, 8.0))

    if tight_supply:
        if highest_prev >= 180:
            target = 28.0
        elif highest_prev >= 120:
            target = 42.0
        elif highest_prev >= 70:
            target = highest_prev + 1.5
        else:
            target = max(36.0, avg_prev * 0.7)
        if urgent_opps >= 2:
            target += 6.0
        return float(min(budget, target))

    if highest_prev >= 180:
        target = 12.0
    elif highest_prev >= 120:
        target = 20.0
    elif highest_prev >= 80:
        target = 30.0
    else:
        target = max(24.0, min(46.0, avg_prev * 0.55 + 6.0))

    if day >= 8 and hp >= 6:
        target *= 0.85

    return float(min(budget, max(0.0, target)))
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

    alive = []
    prev_bids = []
    strong_prev_bids = []
    weak_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) <= DAILY_SALARY * 0.6 or opp.get('hp', 0) <= 2:
                weak_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if opp.get('budget', 0) > DAILY_SALARY and opp.get('hp', 0) >= 4:
                    strong_prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    slots = supply / WATER_REQ
    if slots >= 3:
        supply_pressure = 0
    elif slots >= 2:
        supply_pressure = 1
    else:
        supply_pressure = 2

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strong_high = max(strong_prev_bids) if strong_prev_bids else highest_prev

    if hp <= 2 or no_water_days >= 2:
        emergency = True
    else:
        emergency = False

    if emergency:
        bid = max(DAILY_SALARY * 0.95, strong_high + 2.5)
    elif supply_pressure == 2:
        bid = max(DAILY_SALARY * 0.82, strong_high + 1.2)
    elif supply_pressure == 1:
        bid = max(DAILY_SALARY * 0.58, strong_high * 0.72)
    else:
        bid = DAILY_SALARY * 0.34

    if weak_count >= 2 and not emergency:
        bid *= 0.88

    if hp >= 8 and no_water_days == 0 and supply_pressure == 0:
        bid = min(bid, DAILY_SALARY * 0.3)

    if day >= 8 and hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.9)

    if budget < DAILY_SALARY * 1.2 and not emergency:
        bid = min(bid, budget * 0.55)

    bid = max(0.0, min(budget, bid))
    return float(bid)
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
    no_water = my_status['no_water_days']

    alive = []
    yesterday_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive:
        return min(budget, DAILY_SALARY * 0.35)

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    slots = max(1, int(supply // WATER_REQ))
    tight_supply = slots <= 1
    abundant_supply = supply >= 24

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

    if tight_supply:
        urgency += 2
    elif abundant_supply:
        urgency -= 1

    if desperate_count >= 2:
        urgency += 1

    if budget < DAILY_SALARY * 1.2:
        urgency += 1

    if urgency <= 0:
        base = DAILY_SALARY * 0.28
    elif urgency == 1:
        base = DAILY_SALARY * 0.42
    elif urgency == 2:
        base = DAILY_SALARY * 0.58
    elif urgency == 3:
        base = DAILY_SALARY * 0.78
    else:
        base = DAILY_SALARY * 0.96

    if highest_prev >= 160:
        if urgency >= 4:
            bid = max(base, 166.0)
        elif urgency >= 2:
            bid = max(base, 92.0)
        else:
            bid = min(base, DAILY_SALARY * 0.32)
    elif highest_prev >= 110:
        if urgency >= 3:
            bid = max(base, min(highest_prev + 2.0, 128.0))
        elif urgency >= 1:
            bid = max(base, 72.0)
        else:
            bid = min(base, DAILY_SALARY * 0.35)
    else:
        target = avg_prev + 3.0 if avg_prev > 0 else DAILY_SALARY * 0.52
        bid = max(base, target)

    if abundant_supply and urgency <= 2:
        bid = min(bid, DAILY_SALARY * 0.45)

    if tight_supply and urgency >= 3:
        bid = max(bid, 95.0)

    if day >= 8 and hp >= 7 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.4)

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve = DAILY_SALARY * 0.6

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 4:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
    bid = max(0.0, bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    bob_bid = None
    cindy_bid = None

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if agent_id == 'Bob':
                    bob_bid = bid
                elif agent_id == 'Cindy':
                    cindy_bid = bid

    if not alive:
        return float(min(budget, 18.0))

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    target = 42.0

    if bob_bid is not None:
        target = max(target, bob_bid + 2.0)
    elif prev_bids:
        target = max(target, max(prev_bids) * 0.9)

    if cindy_bid is not None and cindy_bid >= 120:
        target = min(target, (bob_bid + 3.0) if bob_bid is not None else 88.0)

    if tight_supply:
        target += 6.0
    elif loose_supply:
        target -= 10.0

    if hp <= 3 or no_water_days >= 2:
        emergency = max(92.0, (max(prev_bids) + 3.0) if prev_bids else 92.0)
        return float(min(budget, emergency))

    if hp <= 5 or no_water_days >= 1:
        target += 8.0

    rich_threats = 0
    for agent_id, opp in alive:
        if opp.get('budget', 0) >= budget and opp.get('water_requirement', WATER_REQ) <= WATER_REQ:
            rich_threats += 1
    if rich_threats >= 2:
        target += 4.0

    target = max(20.0, target)
    target = min(target, budget)
    return float(target)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > 300:
                rich_opp += 1
            if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    plentiful = supply >= 22
    tight = supply <= 17

    desperate = no_water_days >= 2 or hp <= 3
    pressured = no_water_days >= 1 or hp <= 5

    if desperate:
        if highest_prev >= 140:
            bid = 148.0 if budget >= 148.0 else budget
        elif highest_prev >= 100:
            bid = highest_prev + 4.0
        else:
            bid = 92.0
        return float(min(budget, bid))

    if plentiful:
        if highest_prev >= 130:
            bid = 18.0
        elif highest_prev >= 90:
            bid = 28.0
        else:
            bid = 36.0
        if pressured:
            bid += 10.0
        return float(min(budget, bid))

    if tight:
        if highest_prev >= 145:
            bid = 24.0 if hp >= 7 and no_water_days == 0 else 118.0
        elif highest_prev >= 110:
            bid = 52.0 if hp >= 7 and no_water_days == 0 else highest_prev + 3.0
        elif highest_prev >= 70:
            bid = highest_prev + 2.5
        else:
            bid = 66.0
        if urgent_opp >= 2 and hp >= 7 and no_water_days == 0:
            bid -= 8.0
        return float(max(0.0, min(budget, bid)))

    bid = 48.0
    if highest_prev >= 130:
        bid = 22.0 if hp >= 7 and no_water_days == 0 else 120.0
    elif highest_prev >= 100:
        bid = 44.0 if hp >= 7 and no_water_days == 0 else 106.0
    elif highest_prev >= 75:
        bid = highest_prev + 2.0
    else:
        bid = max(50.0, avg_prev + 3.0)

    if rich_opp >= 2 and hp >= 7 and no_water_days == 0:
        bid -= 6.0
    if pressured:
        bid += 12.0

    return float(max(0.0, min(budget, bid)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        safe = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 2:
            safe = DAILY_SALARY * 0.75
        return float(min(budget, safe))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    strongest_id = None
    strongest_score = -1.0
    strongest_prev_bid = 0.0
    max_prev_bid = 0.0
    active_pressure = 0.0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid', 0.0)
        if prev_bid is None:
            prev_bid = 0.0
        if prev_bid > max_prev_bid:
            max_prev_bid = prev_bid

        score = opp.get('budget', 0.0) + 8.0 * opp.get('hp', 0) - 12.0 * opp.get('no_water_days', 0)
        if score > strongest_score:
            strongest_score = score
            strongest_id = agent_id
            strongest_prev_bid = prev_bid

        if opp.get('budget', 0.0) > DAILY_SALARY * 2 and opp.get('hp', 0) > 2:
            active_pressure += prev_bid

    emergency = hp <= 2 or no_water >= 2
    strained = hp <= 4 or no_water >= 1

    if emergency:
        bid = DAILY_SALARY * (0.92 + 0.06 * scarcity)
    elif strained:
        bid = DAILY_SALARY * (0.62 + 0.18 * scarcity)
    else:
        bid = DAILY_SALARY * (0.34 + 0.16 * scarcity)

    if strongest_id == 'Cindy':
        if scarcity >= 0.6 and not emergency:
            target = strongest_prev_bid + 2.0
            cap = DAILY_SALARY * 0.88
            bid = max(bid, min(target, cap))
        elif strongest_prev_bid >= DAILY_SALARY * 1.5 and hp > 4 and no_water == 0:
            bid = min(bid, DAILY_SALARY * 0.4)

    if max_prev_bid <= 1.0 and hp > 4 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.28)

    if active_pressure > 0 and scarcity >= 0.7 and not emergency:
        bid = max(bid, min(DAILY_SALARY * 0.82, max_prev_bid + 1.5))

    reserve_floor = 0.0
    if day <= 7 and not emergency:
        reserve_floor = DAILY_SALARY * 1.2
    if budget <= reserve_floor:
        bid = min(bid, max(0.0, budget - reserve_floor * 0.25))

    if emergency:
        bid = max(bid, DAILY_SALARY * 0.8)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    bob_bid = None
    cindy_bid = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if agent_id == 'Bob':
                    bob_bid = bid
                elif agent_id == 'Cindy':
                    cindy_bid = bid

    if not alive:
        return max(0.0, min(budget, 18.0))

    live_count = len(alive) + 1
    pressure = (WATER_REQ * live_count) / max(1.0, supply)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = DAILY_SALARY * 0.7
        avg_prev = DAILY_SALARY * 0.6

    if bob_bid is None:
        bob_bid = 70.0
    if cindy_bid is None:
        cindy_bid = 145.0

    urgent = hp <= 3 or no_water_days >= 2
    semi_urgent = hp <= 5 or no_water_days >= 1
    very_tight = supply <= 17
    tight = supply <= 19
    roomy = supply >= 23

    target = 0.0

    if urgent:
        if cindy_bid > budget * 1.2:
            target = min(budget, bob_bid + 3.0)
        else:
            target = min(budget, max(bob_bid + 2.0, DAILY_SALARY * 0.92))
    elif very_tight:
        if hp >= 8 and no_water_days == 0:
            target = DAILY_SALARY * 0.28
        else:
            target = max(22.0, min(DAILY_SALARY * 0.88, bob_bid + 2.0))
    elif tight:
        if semi_urgent:
            target = max(26.0, min(DAILY_SALARY * 0.82, bob_bid + 1.5))
        else:
            target = DAILY_SALARY * 0.36
    elif roomy:
        if hp >= 8 and no_water_days == 0:
            target = DAILY_SALARY * 0.12
        else:
            target = DAILY_SALARY * 0.24
    else:
        if pressure > 2.2:
            target = max(24.0, min(DAILY_SALARY * 0.75, avg_prev * 0.9))
        elif semi_urgent:
            target = max(20.0, min(DAILY_SALARY * 0.62, bob_bid + 1.0))
        else:
            target = DAILY_SALARY * 0.22

    if budget < DAILY_SALARY * 0.8:
        if urgent:
            target = min(target, budget)
        else:
            target = min(target, budget * 0.55)

    if day >= 8:
        if hp >= 7 and no_water_days == 0 and not urgent:
            target = min(target, DAILY_SALARY * 0.18)
        elif semi_urgent:
            target = max(target, DAILY_SALARY * 0.52)

    bid = max(0.0, min(budget, float(target)))
    return bid
"""
