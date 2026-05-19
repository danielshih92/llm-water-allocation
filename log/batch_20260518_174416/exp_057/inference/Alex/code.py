# ============================================================
# Experiment: exp_057
# Agent: Alex
# Source: exp_057
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

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 18)

    total_players = 1 + len(alive)
    units_available = int(supply // WATER_REQ)
    scarcity = units_available < total_players

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        if opp.get('budget', 0) > budget:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0

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

    if scarcity:
        urgency += 2
    if desperate_opp >= max(1, len(alive) // 2):
        urgency += 1
    if rich_opp >= max(1, len(alive) // 2):
        urgency += 1

    if urgency >= 6:
        base = 66
    elif urgency >= 4:
        base = 54
    elif urgency >= 2:
        base = 38
    else:
        base = 24

    if highest_prev > 0:
        if urgency >= 4:
            target = max(base, highest_prev + 2)
        elif scarcity:
            target = max(base, avg_prev + 1)
        else:
            target = min(base, highest_prev)
    else:
        target = base

    if not scarcity and urgency <= 1:
        target = min(target, 22)

    reserve_floor = 0
    if hp > 4 and no_water_days == 0:
        reserve_floor = 20
    elif hp > 2:
        reserve_floor = 10

    affordable = budget - reserve_floor
    if affordable < 0:
        affordable = budget

    bid = min(target, affordable)

    if bid < 0:
        bid = 0
    if urgency >= 5 and budget > 0:
        bid = max(bid, min(budget, 60))
    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 67))

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

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    desperate_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if bid >= 120 and opp.get('budget', 0) >= 500:
                    rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    very_tight_supply = supply <= 16
    loose_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        base = 118.0 if very_tight_supply else 102.0
        if highest_prev > 0:
            base = max(base, min(132.0, highest_prev + 3.0))
        return float(min(budget, base))

    if hp <= 4 or no_water >= 1:
        base = 78.0
        if tight_supply:
            base = 88.0
        if highest_prev >= 110:
            base = max(base, 96.0)
        return float(min(budget, base))

    base = 34.0

    if loose_supply:
        base = 24.0
    elif tight_supply:
        base = 46.0

    if desperate_opp >= 2:
        base += 8.0
    elif desperate_opp == 1:
        base += 4.0

    if rich_aggressive >= 2:
        base -= 6.0
    elif rich_aggressive == 1:
        base -= 3.0

    if highest_prev >= 130:
        base = min(base, 32.0 if not tight_supply else 40.0)
    elif highest_prev >= 90:
        base = max(base, 38.0)
    elif highest_prev > 0:
        base = max(base, min(52.0, avg_prev * 0.55 + 4.0))

    if day >= 8 and hp >= 6:
        base -= 4.0

    base = max(18.0, base)
    return float(min(budget, base))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return min(budget, DAILY_SALARY * 0.35)

    cindy_bid = None
    highest_prev = 0.0
    urgent_opponents = 0
    weak_opponents = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = prev.get('bid') if prev else None
        if pbid is not None:
            pbid = float(pbid)
            if pbid > highest_prev:
                highest_prev = pbid
            if oid == 'Cindy':
                cindy_bid = pbid
        if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0)) <= 3:
            urgent_opponents += 1
        if float(opp.get('budget', 0)) < DAILY_SALARY * 0.8 or float(opp.get('hp', 0)) <= 2:
            weak_opponents += 1

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tightness = 1.0 - scarcity

    base = DAILY_SALARY * (0.34 + 0.18 * tightness)

    if cindy_bid is not None:
        if cindy_bid >= 120:
            base = max(base, 58.0 if hp > 3 and no_water_days == 0 else 82.0)
        elif cindy_bid >= 90:
            base = max(base, min(78.0, cindy_bid + 2.0))
        else:
            base = max(base, cindy_bid + 3.0)
    elif highest_prev > 0:
        base = max(base, min(75.0, highest_prev + 2.0))

    if no_water_days >= 2:
        base = max(base, 98.0)
    elif no_water_days == 1:
        base = max(base, 76.0 + 10.0 * tightness)

    if hp <= 2:
        base = max(base, 95.0)
    elif hp <= 4:
        base = max(base, 72.0 + 8.0 * tightness)

    if urgent_opponents >= 2 and hp > 4 and no_water_days == 0:
        base *= 0.9
    if weak_opponents >= 2 and hp > 3:
        base *= 0.94

    if day >= 8:
        base *= 1.08

    reserve_days = max(0, 10 - day)
    reserve = reserve_days * DAILY_SALARY * 0.28
    affordable = max(0.0, budget - reserve)
    if affordable <= 0:
        bid = min(budget, max(18.0, DAILY_SALARY * 0.22))
    else:
        bid = min(base, budget, max(affordable, 0.0))
        if no_water_days >= 1 or hp <= 3:
            bid = min(budget, max(bid, min(affordable + DAILY_SALARY * 0.2, 105.0)))

    bid = max(0.0, min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    winners_est = max(1, int(supply / WATER_REQ))

    prev_bids = []
    named_prev = {}
    dangerous_count = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            named_prev[oid] = float(bid)
            if float(bid) >= 120:
                dangerous_count += 1

    bob_bid = named_prev.get('Bob', 75.0)
    eric_bid = named_prev.get('Eric', 130.0)
    cindy_bid = named_prev.get('Cindy', 0.0)

    active_threats = 0
    for oid, opp in alive:
        if opp.get('budget', 0) > 0:
            active_threats += 1

    if hp <= 2 or no_water >= 2:
        emergency = max(bob_bid + 8.0, 118.0)
        if eric_bid < 125:
            emergency = max(emergency, eric_bid + 3.0)
        return float(min(budget, emergency))

    if winners_est >= 2:
        base = bob_bid + 2.5
        if active_threats <= 2:
            base = min(base, 72.0)
        if hp >= 6 and no_water == 0 and dangerous_count >= 1:
            base = min(base, 68.0)
        if hp <= 4 or no_water == 1:
            base = max(base, bob_bid + 5.0)
        return float(min(budget, max(18.0, base)))

    scarce_bid = max(bob_bid + 7.0, 86.0)
    if eric_bid <= 110:
        scarce_bid = max(scarce_bid, eric_bid + 2.0)
    if hp >= 6 and no_water == 0 and eric_bid >= 125:
        scarce_bid = min(scarce_bid, 92.0)
    if hp <= 4 or no_water == 1:
        scarce_bid = max(scarce_bid, 96.0)
    if cindy_bid > 0 and cindy_bid < 90:
        scarce_bid = max(scarce_bid, cindy_bid + 3.0)

    return float(min(budget, scarce_bid))
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 2 else 35.0))

    need_units = int(supply / WATER_REQ)
    if need_units < 0:
        need_units = 0

    prev_bids = []
    dangerous_prev = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 80.0:
                dangerous_prev.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    for b in prev_bids:
        if b < 90.0 and b > moderate_prev:
            moderate_prev = b

    critical = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if need_units >= 2:
        if critical:
            bid = max(58.0, moderate_prev + 2.0 if moderate_prev > 0 else 58.0)
        elif pressured:
            bid = max(42.0, moderate_prev + 1.5 if moderate_prev > 0 and moderate_prev < 75.0 else 42.0)
        else:
            if moderate_prev > 0:
                bid = max(24.0, min(48.0, moderate_prev - 6.0))
            else:
                bid = 26.0
    else:
        if critical:
            bid = max(88.0, highest_prev + 2.0 if highest_prev > 0 else 88.0)
        elif pressured:
            if highest_prev >= 100.0:
                bid = 72.0
            else:
                bid = max(60.0, highest_prev + 1.5 if highest_prev > 0 else 60.0)
        else:
            if highest_prev >= 100.0:
                bid = 34.0
            elif highest_prev >= 70.0:
                bid = 46.0
            else:
                bid = max(36.0, highest_prev + 1.0 if highest_prev > 0 else 36.0)

    if len(dangerous_prev) >= 2 and not critical:
        bid = min(bid, 38.0 if need_units >= 2 else 30.0)

    reserve_target = 0.0
    if day_context['day'] <= 3:
        reserve_target = 220.0
    elif day_context['day'] <= 6:
        reserve_target = 140.0
    else:
        reserve_target = 70.0

    max_affordable = budget
    if budget > reserve_target:
        max_affordable = budget - reserve_target + min(25.0, DAILY_SALARY * 0.35)

    if critical:
        max_affordable = budget

    bid = min(bid, max_affordable)
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strongest_live_prev = 0.0
    cindy_alive = False
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            if agent_id == 'Cindy':
                cindy_alive = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid > strongest_live_prev:
                    strongest_live_prev = bid

    alive_count = len(alive)
    if alive_count == 0:
        return float(min(budget, 18.0))

    units = int(supply // WATER_REQ)
    scarcity = units < (alive_count + 1)
    severe_scarcity = units <= max(0, alive_count - 1)

    urgent = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if urgent:
        if cindy_alive:
            bid = 58.0
        else:
            bid = 52.0 if scarcity else 44.0
        if strongest_live_prev > 0:
            bid = max(bid, min(64.0, strongest_live_prev + 2.0))
        return float(min(budget, bid))

    if severe_scarcity:
        if strongest_live_prev >= 100:
            bid = 12.0 if hp > 5 else 46.0
        elif strongest_live_prev >= 70:
            bid = 24.0 if hp > 5 else 49.0
        else:
            bid = 34.0 if pressured else 22.0
    elif scarcity:
        if strongest_live_prev >= 100:
            bid = 14.0 if hp > 6 else 42.0
        elif strongest_live_prev >= 60:
            bid = 28.0 if hp > 5 else 40.0
        else:
            bid = 30.0 if pressured else 20.0
    else:
        bid = 16.0 if hp > 5 else 26.0

    dangerous_rivals = 0
    for agent_id, opp in alive:
        ob = opp.get('budget', 0)
        ohp = opp.get('hp', 0)
        prev = opp.get('previous_trace', {})
        pbid = prev.get('bid') if prev else None
        if ob >= 40 and ohp <= 4:
            dangerous_rivals += 1
        elif pbid is not None and float(pbid) >= 60 and ob >= 20:
            dangerous_rivals += 1

    if dangerous_rivals >= 2 and pressured:
        bid += 8.0
    elif dangerous_rivals == 0 and hp >= 6:
        bid -= 4.0

    if cindy_alive and strongest_live_prev >= 110 and hp >= 5:
        bid = min(bid, 18.0)

    bid = max(0.0, min(float(budget), bid))
    return float(bid)
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_prev_bids = []
    rich_aggressive = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_prev_bids.append(float(bid))
                if opp.get('budget', 0) > 300 and float(bid) >= 90:
                    rich_aggressive.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    contested = slots <= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_urgent = max(urgent_prev_bids) if urgent_prev_bids else highest_prev
    rich_pressure = max(rich_aggressive) if rich_aggressive else 0.0

    danger = hp <= 2 or no_water_days >= 2
    caution = hp <= 4 or no_water_days >= 1

    if danger:
        bid = max(72.0, min(118.0, highest_urgent + 2.5))
        if contested:
            bid = max(bid, 96.0)
        return float(min(budget, bid))

    if contested:
        if rich_pressure >= 110 and hp >= 5:
            bid = 24.0
        elif highest_prev >= 95:
            bid = 34.0 if hp >= 6 else 82.0
        elif highest_prev >= 60:
            bid = highest_prev + 2.0 if caution else highest_prev * 0.72
        else:
            bid = 52.0 if caution else 41.0
    else:
        if highest_prev >= 100:
            bid = 20.0 if hp >= 6 else 58.0
        elif highest_prev >= 70:
            bid = 33.0 if hp >= 5 else 54.0
        else:
            bid = 28.0 if hp >= 5 else 46.0

    if day >= 8 and hp <= 4:
        bid = max(bid, 78.0)
    elif day >= 9 and hp <= 6:
        bid = max(bid, 62.0)

    min_safe = 0.0
    if no_water_days >= 1:
        min_safe = 36.0
    if hp <= 3:
        min_safe = max(min_safe, 60.0)

    bid = max(bid, min_safe)
    bid = min(bid, budget)
    if bid < 0:
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    pressure_bids = []
    urgent_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            pbid = prev.get('bid')
            if pbid is not None:
                pressure_bids.append(float(pbid))
                if prev.get('status') != 'ok' or prev.get('hp_after', 10) <= 3:
                    urgent_count += 1

    prev_max = max(pressure_bids) if pressure_bids else 0.0
    prev_avg = sum(pressure_bids) / len(pressure_bids) if pressure_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    if hp <= 2 or no_water_days >= 2:
        target = max(prev_max + 2.0, DAILY_SALARY * (0.92 + 0.18 * scarcity))
        return float(min(budget, target))

    if hp <= 4 or no_water_days >= 1:
        target = max(prev_avg + 3.0, DAILY_SALARY * (0.72 + 0.18 * scarcity))
        if urgent_count >= 2:
            target += 6.0
        return float(min(budget, target))

    base = DAILY_SALARY * (0.34 + 0.18 * scarcity)
    if prev_max > DAILY_SALARY * 1.2:
        base *= 0.8
    elif prev_max > DAILY_SALARY * 0.85:
        base *= 0.9
    else:
        base = max(base, prev_avg + 1.5)

    if rich_count >= 2 and supply <= 18:
        base += 5.0
    if urgent_count == 0 and supply >= 22:
        base -= 4.0
    if day >= 8 and hp >= 6:
        base *= 0.9

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    if budget < reserve_floor:
        base *= 0.8

    if base < 0:
        base = 0.0
    return float(min(budget, base))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget:
                rich_threat += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    very_tight = units < 1.6
    tight = units < 2.0
    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        target = max(DAILY_SALARY * 1.15, highest_prev + 2.0)
    elif urgent and very_tight:
        target = max(DAILY_SALARY * 0.95, highest_prev + 1.5)
    elif urgent:
        target = max(DAILY_SALARY * 0.8, avg_prev + 1.0)
    elif very_tight:
        target = max(DAILY_SALARY * 0.72, avg_prev + 0.5)
    elif tight:
        target = DAILY_SALARY * 0.52
    else:
        target = DAILY_SALARY * 0.28

    if rich_threat >= 2 and not urgent:
        target *= 0.9

    if day >= 8 and hp > 4 and no_water_days == 0:
        target *= 0.9

    reserve_floor = DAILY_SALARY * 0.25
    if budget < DAILY_SALARY:
        target = max(target, budget * 0.72)
    else:
        target = min(target, budget - reserve_floor)

    if target < 0:
        target = 0.0

    bid = min(float(budget), float(target))
    if urgent and bid < min(budget, DAILY_SALARY * 0.75):
        bid = float(min(budget, DAILY_SALARY * 0.75))

    return float(max(0.0, bid))
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

    alive_opponents = []
    yesterday_bids = []
    rich_aggressive = 0
    desperate_opp = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                yesterday_bids.append(float(bid))
                if bid >= 120:
                    rich_aggressive += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_opp += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    tight_supply = supply <= 17
    abundant_supply = supply >= 22
    critical_me = hp <= 3 or no_water_days >= 2
    pressured_me = hp <= 5 or no_water_days >= 1

    if critical_me:
        bid = max(110.0, highest_prev + 3.0)
        if tight_supply:
            bid += 12.0
        return float(min(budget, bid))

    if pressured_me:
        bid = max(78.0, avg_prev * 0.72 + 8.0)
        if tight_supply:
            bid = max(bid, highest_prev * 0.82 + 5.0)
        elif abundant_supply and rich_aggressive >= 1:
            bid *= 0.82
        return float(min(budget, bid))

    if abundant_supply and rich_aggressive >= 1:
        return float(min(budget, 22.0))

    if tight_supply:
        bid = max(52.0, avg_prev * 0.45 + 6.0)
        if desperate_opp >= 1:
            bid += 8.0
        return float(min(budget, bid))

    if highest_prev >= 130:
        bid = 26.0
    elif highest_prev >= 100:
        bid = 34.0
    else:
        bid = max(28.0, avg_prev * 0.32 + 4.0)

    if day >= 8 and hp <= 6:
        bid += 10.0

    return float(min(budget, bid))
"""
