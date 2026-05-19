# ============================================================
# Experiment: exp_002
# Agent: Alex
# Source: exp_002
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
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) > budget:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 21)

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.4
    if no_water_days >= 2:
        urgency += 0.7
    elif no_water_days >= 1:
        urgency += 0.35

    market = 0.0
    if prev_bids:
        market += min(1.0, max_prev / DAILY_SALARY)
        market += min(1.0, avg_prev / DAILY_SALARY) * 0.5
    market += 0.15 * desperate_count
    market += 0.08 * rich_count
    market += 0.5 * supply_pressure

    base = DAILY_SALARY * (0.28 + 0.32 * supply_pressure)

    if urgency >= 1.0:
        bid = max(base, DAILY_SALARY * 0.92)
    elif urgency >= 0.5:
        bid = max(base, DAILY_SALARY * (0.68 + 0.12 * supply_pressure))
    else:
        if max_prev >= DAILY_SALARY * 0.9 and hp > 3 and no_water_days == 0:
            bid = DAILY_SALARY * 0.22
        elif prev_bids:
            target = max(avg_prev + 1.5, max_prev * 0.78)
            bid = max(base, min(target, DAILY_SALARY * 0.88))
        else:
            bid = base

    if day >= 8:
        bid += 4
    if hp <= 3:
        bid += 5
    if no_water_days >= 1:
        bid += 6

    if budget < DAILY_SALARY * 0.6:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, DAILY_SALARY)

    if hp > 4 and no_water_days == 0 and supply >= 23:
        bid = min(bid, DAILY_SALARY * 0.35)

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
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    aggressive_count = 0
    needy_count = 0
    rich_count = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            needy_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= DAILY_SALARY * 0.9:
                aggressive_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    tight_supply = units < (len(alive) + 1)
    very_tight = units < len(alive)

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    if no_water >= 2:
        urgency += 3
    elif no_water >= 1:
        urgency += 2
    if very_tight:
        urgency += 2
    elif tight_supply:
        urgency += 1
    if day >= 8:
        urgency += 1

    if urgency >= 5:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif urgency >= 3:
        if aggressive_count > 0:
            target = max(DAILY_SALARY * 0.72, min(highest_prev + 1.5, DAILY_SALARY * 1.02))
        else:
            target = max(DAILY_SALARY * 0.58, avg_prev + 1.0)
    else:
        if aggressive_count >= 2 and hp > 4:
            target = DAILY_SALARY * 0.28
        elif tight_supply:
            target = max(DAILY_SALARY * 0.48, avg_prev * 0.75 + 1.0)
        else:
            target = DAILY_SALARY * 0.34

    if rich_count >= 2 and tight_supply and urgency <= 2:
        target *= 0.9
    if needy_count >= 2 and urgency >= 3:
        target *= 1.08

    reserve_days = max(0, 10 - day)
    soft_cap = budget
    if reserve_days > 0:
        reserve_buffer = reserve_days * DAILY_SALARY * 0.22
        soft_cap = max(0.0, budget - reserve_buffer)
        if urgency >= 4:
            soft_cap = budget

    bid = min(target, budget)
    if soft_cap > 0:
        bid = min(bid, max(soft_cap, DAILY_SALARY * 0.25 if urgency >= 3 else DAILY_SALARY * 0.15))

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))
    elif no_water >= 1 and tight_supply:
        bid = max(bid, min(budget, DAILY_SALARY * 0.7))

    if budget < DAILY_SALARY * 0.5:
        bid = min(bid, budget)
    bid = max(0.0, min(float(budget), float(bid)))
    return float(bid)
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

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 50.0))
        return float(min(budget, 18.0))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= 700:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if no_water_days >= 2 or hp <= 2:
        bid = max(72.0, highest_prev * 0.72)
        if tight_supply:
            bid = max(bid, highest_prev * 0.82, 88.0)
        return float(min(budget, bid))

    if no_water_days == 1 or hp <= 4:
        bid = max(48.0, avg_prev * 0.62)
        if tight_supply:
            bid = max(bid, highest_prev * 0.68, 62.0)
        elif loose_supply:
            bid = min(bid, 52.0)
        return float(min(budget, bid))

    bid = 24.0
    if tight_supply:
        bid = max(36.0, avg_prev * 0.45)
        if rich_count >= 2:
            bid = max(bid, 44.0)
    elif loose_supply:
        bid = 16.0
    else:
        bid = max(22.0, avg_prev * 0.28)

    if highest_prev >= 120:
        bid = min(bid, 38.0)
    elif highest_prev >= 90:
        bid = min(max(bid, 28.0), 42.0)
    elif highest_prev <= 20 and desperate_count == 0:
        bid = max(bid, 26.0)

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid = min(bid, 22.0)

    return float(min(budget, max(0.0, bid)))
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
    prev_bids = []
    aggressive_count = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 0.9 * DAILY_SALARY:
                    aggressive_count += 1

    if not alive:
        return float(min(budget, max(8.0, DAILY_SALARY * 0.22)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.65
    elif hp <= 6:
        urgency += 0.35

    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.55

    late_game = 1.0 if day >= 8 else (0.5 if day >= 6 else 0.0)

    if urgency >= 1.4:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 2.5, avg_prev + 4.0)
    elif urgency >= 0.8:
        bid = max(0.72 * DAILY_SALARY, avg_prev + 2.0, highest_prev * 0.72)
    else:
        if supply >= 22 and hp >= 7:
            bid = DAILY_SALARY * 0.18
        elif supply >= 20:
            bid = DAILY_SALARY * 0.26
        elif supply >= 18:
            bid = DAILY_SALARY * 0.38
        else:
            bid = DAILY_SALARY * 0.52

        if aggressive_count >= 2 and hp >= 6 and no_water_days == 0 and supply <= 18:
            bid *= 0.82
        elif desperate_count >= 2 and supply <= 18:
            bid = max(bid, highest_prev + 1.5)

        bid += scarcity * 8.0 + late_game * 4.0 + urgency * 10.0

    reserve_target = max(0.0, (10 - day) * DAILY_SALARY * 0.18)
    affordable = max(0.0, budget - reserve_target)

    if urgency >= 0.8:
        cap = min(budget, max(affordable, budget * 0.7))
    else:
        cap = min(budget, max(affordable, budget * 0.4))

    bid = min(bid, cap)

    if hp >= 7 and no_water_days == 0 and supply >= 21 and highest_prev >= 85:
        bid = min(bid, DAILY_SALARY * 0.22)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, highest_prev + 3.0, DAILY_SALARY * 1.02))

    bid = max(0.0, min(budget, bid))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    total_agents = 1 + len(alive)
    tight_supply = supply <= WATER_REQ * 1.25
    very_tight = supply < WATER_REQ * 1.05
    enough_for_two = supply >= WATER_REQ * 2

    danger = 0
    if hp <= 3:
        danger += 3
    elif hp <= 5:
        danger += 2
    elif hp <= 7:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1
    if very_tight:
        danger += 2
    elif tight_supply:
        danger += 1
    if day >= 8:
        danger += 1

    if highest_prev >= 170:
        pressure = 'extreme'
    elif highest_prev >= 135:
        pressure = 'high'
    elif highest_prev >= 90:
        pressure = 'medium'
    else:
        pressure = 'low'

    if danger >= 5:
        target = highest_prev + 2.5 if highest_prev > 0 else 150.0
    elif danger >= 3:
        if pressure == 'extreme':
            target = highest_prev + 1.0
        elif pressure == 'high':
            target = highest_prev + 2.0
        else:
            target = max(95.0, avg_prev + 8.0)
    else:
        if pressure == 'extreme':
            target = 18.0 if hp >= 7 and no_water_days == 0 else highest_prev + 1.0
        elif pressure == 'high':
            target = 28.0 if hp >= 8 and enough_for_two else 60.0
        elif pressure == 'medium':
            target = avg_prev + 3.0
        else:
            target = 45.0

    if budget < 120:
        target = min(target, budget * 0.72)
    elif budget < 200 and danger < 3:
        target = min(target, budget * 0.55)

    if day == 1 and hp >= 9 and no_water_days == 0:
        target = min(target, 55.0)

    bid = max(0.0, min(budget, target))
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

    alive_opponents = []
    prev_bids = []
    moderate_bids = []
    high_bids = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 90:
                    high_bids.append(float(bid))
                else:
                    moderate_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    competitors = 1 + len(alive_opponents)
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < competitors

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_anchor = max(moderate_bids) if moderate_bids else 0.0

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1

    if no_water_days >= 2 or hp <= 2:
        bid = min(budget, max(78.0, moderate_anchor + 6.0, DAILY_SALARY * 1.05))
        return float(max(0.0, bid))

    if scarcity:
        if danger >= 2:
            target = max(62.0, moderate_anchor + 4.0)
        else:
            target = max(38.0, min(58.0, moderate_anchor + 1.5 if moderate_anchor > 0 else 44.0))
    else:
        if danger >= 2:
            target = max(42.0, moderate_anchor + 2.0 if moderate_anchor > 0 else 42.0)
        else:
            target = 16.0 if highest_prev >= 90.0 else 24.0

    if day >= 8 and hp <= 5:
        target += 8.0
    if budget < 140:
        target = min(target, 46.0 if danger < 3 else 68.0)
    if budget < 70:
        target = min(target, budget)

    bid = min(budget, target)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_non_cindy = []
    cindy_bid = None

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if agent_id == 'Cindy':
                    cindy_bid = bid
                else:
                    strong_non_cindy.append(bid)

    if not alive:
        return min(budget, 20.0)

    alive_count = len(alive)
    units = supply / float(WATER_REQ)
    scarcity = units / float(alive_count + 1)

    max_prev = max(prev_bids) if prev_bids else 0.0
    ref_non_cindy = max(strong_non_cindy) if strong_non_cindy else 0.0

    if hp <= 2 or no_water_days >= 2:
        emergency = max(92.0, ref_non_cindy + 8.0)
        if cindy_bid is not None and cindy_bid < emergency and hp <= 1:
            emergency = cindy_bid + 3.0
        return min(budget, emergency)

    if hp <= 4 or no_water_days >= 1:
        urgent = max(78.0, ref_non_cindy + 4.0)
        if scarcity < 0.45:
            urgent += 8.0
        return min(budget, urgent)

    if scarcity >= 0.7:
        bid = 36.0
    elif scarcity >= 0.5:
        bid = max(48.0, ref_non_cindy - 6.0)
    else:
        bid = max(68.0, ref_non_cindy + 2.5)

    if cindy_bid is not None and cindy_bid > 95.0 and hp >= 5:
        bid = min(bid, 74.0)

    if day >= 8 and hp >= 6:
        bid = min(bid, 58.0)

    if budget < DAILY_SALARY * 2:
        bid = min(bid, max(28.0, budget * 0.55))

    return min(budget, bid)
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    rich_threat_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > DAILY_SALARY * 4 and opp.get('hp', 0) > 2:
                    rich_threat_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.35))

    high_prev = max(prev_bids) if prev_bids else 0.0
    threat_prev = max(rich_threat_bids) if rich_threat_bids else high_prev

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    low_supply = supply <= 17
    high_supply = supply >= 22

    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1
    late_game = day >= 8

    if urgent:
        bid = max(DAILY_SALARY * 0.95, threat_prev + 2.0)
    elif semi_urgent:
        if low_supply:
            bid = max(DAILY_SALARY * 0.78, threat_prev * 0.92)
        else:
            bid = max(DAILY_SALARY * 0.68, threat_prev * 0.82)
    else:
        if high_supply:
            bid = DAILY_SALARY * 0.28
        elif low_supply:
            bid = max(DAILY_SALARY * 0.42, threat_prev * 0.55)
        else:
            bid = max(DAILY_SALARY * 0.34, threat_prev * 0.42)

    if late_game and hp <= 6:
        bid = max(bid, DAILY_SALARY * 0.72)

    if high_prev >= 120 and not urgent:
        bid = min(bid, DAILY_SALARY * 0.45 if not semi_urgent else DAILY_SALARY * 0.7)

    reserve_days = 2 if hp > 4 else 1
    reserve = reserve_days * DAILY_SALARY
    affordable = max(0.0, budget - reserve)
    if urgent:
        affordable = budget
    elif semi_urgent:
        affordable = max(DAILY_SALARY * 0.5, affordable)

    bid = min(bid, affordable, budget)
    bid = max(0.0, bid)
    return float(bid)
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

    day = day_context['day']
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = {k: v for k, v in opponents_status.items() if v.get('alive')}
    if not alive:
        return float(min(budget, 18.0))

    strongest_name = None
    strongest_score = -1.0
    strongest = None
    for name, opp in alive.items():
        score = float(opp.get('budget', 0.0)) + 0.2 * float(opp.get('hp', 0.0))
        if score > strongest_score:
            strongest_score = score
            strongest_name = name
            strongest = opp

    prev_bid = 0.0
    prev_supply = None
    if strongest is not None:
        prev = strongest.get('previous_trace', {}) or {}
        bid_val = prev.get('bid')
        if bid_val is not None:
            prev_bid = float(bid_val)
        ps = prev.get('supply')
        if ps is not None:
            prev_supply = float(ps)

    contested = False
    active_bidders = 0
    max_prev_bid = 0.0
    for opp in alive.values():
        prev = opp.get('previous_trace', {}) or {}
        bid_val = prev.get('bid')
        if bid_val is not None and float(bid_val) > 0:
            active_bidders += 1
            if float(bid_val) > max_prev_bid:
                max_prev_bid = float(bid_val)
    if active_bidders >= 1:
        contested = True

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.45
    urgency += 0.45 * supply_pressure

    if strongest is not None:
        opp_budget = float(strongest.get('budget', 0.0))
        opp_hp = float(strongest.get('hp', 0.0))
        if opp_budget < 80:
            urgency -= 0.2
        if opp_hp <= 3:
            urgency -= 0.15
        if prev_bid >= 140:
            urgency += 0.35
        elif prev_bid <= 1:
            urgency -= 0.2
    else:
        opp_budget = 0.0

    if urgency < 0:
        urgency = 0.0

    if not contested or max_prev_bid <= 1:
        base_bid = 16.0 + 10.0 * supply_pressure
    else:
        anchor = min(prev_bid + 2.5, 72.0)
        base_bid = max(24.0 + 12.0 * supply_pressure, anchor)

    if urgency >= 1.6:
        bid = max(base_bid, 78.0 + 18.0 * supply_pressure)
    elif urgency >= 0.9:
        bid = max(base_bid, 48.0 + 14.0 * supply_pressure)
    else:
        bid = base_bid

    if day >= 8 and hp > 4 and no_water_days == 0:
        bid *= 0.9

    reserve = 0.0
    days_left = max(0, 10 - int(day))
    if days_left > 0:
        reserve = min(budget * 0.35, days_left * 12.0)

    cap = budget - reserve
    if hp <= 3 or no_water_days >= 2:
        cap = budget
    if cap < 0:
        cap = 0.0

    bid = min(bid, cap)
    if bid < 0:
        bid = 0.0

    if hp <= 2 or no_water_days >= 2:
        emergency = min(budget, max(90.0, prev_bid + 6.0))
        bid = max(bid, emergency)

    if strongest_name == 'Cindy' and strongest is not None and float(strongest.get('budget', 0.0)) < 40 and hp > 3:
        bid = min(bid, min(budget, 28.0 + 8.0 * supply_pressure))

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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_budgets = []
    urgent_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0
    rich_opp = max(opp_budgets) if opp_budgets else 0

    scarcity = supply <= 17
    abundant = supply >= 22
    danger = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        bid = max(78.0, highest_prev + 2.5)
    elif danger:
        if scarcity:
            bid = max(68.0, highest_prev + 1.5)
        else:
            bid = max(54.0, avg_prev * 0.72 if avg_prev > 0 else 54.0)
    else:
        if abundant:
            bid = 16.0 if rich_opp > 200 else 20.0
        elif scarcity:
            if highest_prev >= 120:
                bid = 30.0
            else:
                bid = max(44.0, highest_prev * 0.78 if highest_prev > 0 else 44.0)
        else:
            if urgent_opp >= 2:
                bid = max(36.0, avg_prev * 0.55 if avg_prev > 0 else 36.0)
            else:
                bid = max(28.0, avg_prev * 0.42 if avg_prev > 0 else 28.0)

    if budget < DAILY_SALARY and not critical:
        bid = min(bid, budget * 0.82)

    if budget < 35 and not danger:
        bid = min(bid, 22.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
"""
