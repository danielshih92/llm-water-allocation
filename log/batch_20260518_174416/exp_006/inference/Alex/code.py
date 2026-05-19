# ============================================================
# Experiment: exp_006
# Agent: Alex
# Source: exp_006
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
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    units = int(supply // WATER_REQ)
    if units < 0:
        units = 0

    prev_bids = []
    desperate_count = 0
    rich_pressure = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
                desperate_count += 1
            if opp.get('budget', 0) >= DAILY_SALARY * 4:
                rich_pressure += 1

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2

    scarcity = 0
    if units <= 1:
        scarcity = 3
    elif units == 2:
        scarcity = 2
    else:
        scarcity = 1

    pressure = scarcity + urgency
    if desperate_count > 0:
        pressure += 1
    if rich_pressure >= 2:
        pressure += 1

    if not alive_opponents:
        if pressure >= 5:
            bid = DAILY_SALARY * 0.7
        elif pressure >= 3:
            bid = DAILY_SALARY * 0.45
        else:
            bid = DAILY_SALARY * 0.2
        return min(budget, max(0, bid))

    if pressure >= 7:
        target = max(DAILY_SALARY * 0.92, highest_prev + 2)
    elif pressure >= 5:
        target = max(DAILY_SALARY * 0.72, avg_prev + 2, highest_prev + 1)
    elif pressure >= 3:
        if units >= 2:
            target = max(DAILY_SALARY * 0.42, avg_prev)
        else:
            target = max(DAILY_SALARY * 0.58, highest_prev + 1)
    else:
        if units >= 2:
            target = DAILY_SALARY * 0.28
        else:
            target = max(DAILY_SALARY * 0.4, avg_prev * 0.9)

    if day >= 8 and hp <= 4:
        target = max(target, DAILY_SALARY * 0.8)

    if budget < target:
        if hp <= 2 or no_water_days >= 2:
            return budget
        target = min(target, budget)

    if target < 0:
        target = 0
    if target > budget:
        target = budget
    return target
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        base = DAILY_SALARY * 0.25
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.6
        return max(0.0, min(budget, base))

    pressure_bids = []
    eric_bid = None
    desperate_opp = 0
    rich_opp = 0
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            pressure_bids.append(prev['bid'])
            if agent_id == 'Eric':
                eric_bid = prev['bid']
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        if opp.get('budget', 0) >= 200:
            rich_opp += 1

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    base = DAILY_SALARY * 0.42

    if loose_supply:
        base = DAILY_SALARY * 0.28
    elif tight_supply:
        base = DAILY_SALARY * 0.72

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.78)

    if pressure_bids:
        highest_prev = max(pressure_bids)
        avg_prev = sum(pressure_bids) / float(len(pressure_bids))
        if highest_prev >= 100:
            if hp > 4 and not tight_supply:
                base = min(base, DAILY_SALARY * 0.35)
            else:
                base = max(base, DAILY_SALARY * 0.82)
        elif avg_prev >= 60:
            base = max(base, DAILY_SALARY * 0.62)
        else:
            base = max(base, min(DAILY_SALARY * 0.58, highest_prev + 2.0))

    if eric_bid is not None:
        if eric_bid >= 110:
            if hp > 4 and not tight_supply:
                base = min(base, DAILY_SALARY * 0.32)
            else:
                base = max(base, DAILY_SALARY * 0.8)
        elif eric_bid >= 85:
            if tight_supply or hp <= 4:
                base = max(base, DAILY_SALARY * 0.76)
            else:
                base = min(max(base, eric_bid * 0.72), DAILY_SALARY * 0.68)
        else:
            base = max(base, eric_bid + 3.0)

    if desperate_opp >= 2 and hp >= 5 and not tight_supply:
        base = min(base, DAILY_SALARY * 0.33)

    if rich_opp >= 2 and tight_supply:
        base = max(base, DAILY_SALARY * 0.84)

    if day >= 8:
        if hp >= 5:
            base = min(max(base, DAILY_SALARY * 0.5), DAILY_SALARY * 0.72)
        else:
            base = max(base, DAILY_SALARY * 0.82)

    if budget < DAILY_SALARY * 1.2:
        base = min(base, budget * 0.7)
    elif budget > 500 and hp <= 4:
        base = max(base, DAILY_SALARY * 0.9)

    bid = max(0.0, min(budget, base))
    return bid
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

    alive_opps = []
    prev_bids = []
    strong_prev_bids = []
    needy_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 4:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    strong_prev_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    active_high = max(strong_prev_bids) if strong_prev_bids else highest_prev
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0
    if hp <= 2 or no_water_days >= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    days_left = max(1, 10 - day + 1)
    reserve_target = max(0.0, days_left * DAILY_SALARY * 0.42)
    spendable = max(0.0, budget - reserve_target)

    if urgency == 3:
        bid = max(92.0, active_high + 2.5)
        if supply <= 17:
            bid = max(bid, 101.0)
        return float(min(budget, bid))

    if urgency == 2:
        base = 72.0 + 12.0 * scarcity
        pressure = active_high + 1.6
        bid = max(base, pressure)
        if needy_count >= 2:
            bid += 4.0
        return float(min(budget, bid))

    if active_high >= 95.0 and hp >= 7 and no_water_days == 0:
        low_bid = 8.0 + 8.0 * (1.0 - scarcity)
        return float(min(budget, low_bid))

    if active_high >= 85.0 and hp >= 6 and no_water_days == 0:
        low_bid = 14.0 + 6.0 * (1.0 - scarcity)
        return float(min(budget, low_bid))

    contest_bid = max(48.0 + 10.0 * scarcity, avg_prev + 1.25)
    if supply <= 17:
        contest_bid += 6.0
    if spendable > 0:
        contest_bid = min(contest_bid, spendable + 22.0)

    floor_bid = 16.0 if hp >= 8 else 24.0
    bid = max(floor_bid, contest_bid)
    return float(min(budget, bid))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
        base = 18.0 if hp > 4 else 42.0
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    low_hp_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 500:
            rich_count += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('hp', 0) <= 5:
            low_hp_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
    elif hp <= 6:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days >= 1:
        urgency += 0.35

    urgency += 0.45 * supply_pressure
    urgency += 0.08 * desperate_count

    if highest_prev >= 140:
        market_mode = 'burnout'
    elif highest_prev >= 115:
        market_mode = 'hot'
    elif highest_prev > 0:
        market_mode = 'normal'
    else:
        market_mode = 'unknown'

    if market_mode == 'burnout':
        if urgency >= 1.0:
            bid = min(0.92 * DAILY_SALARY, highest_prev + 1.0)
        else:
            bid = 0.34 * DAILY_SALARY
    elif market_mode == 'hot':
        if urgency >= 1.0:
            bid = min(0.88 * DAILY_SALARY, avg_prev * 0.72)
        elif supply >= 21 and hp >= 6:
            bid = 0.30 * DAILY_SALARY
        else:
            bid = max(0.44 * DAILY_SALARY, avg_prev * 0.52)
    elif market_mode == 'normal':
        if urgency >= 1.0:
            bid = max(0.70 * DAILY_SALARY, highest_prev + 2.0)
        else:
            bid = max(0.46 * DAILY_SALARY, avg_prev * 0.78 + 1.0)
    else:
        if urgency >= 1.0:
            bid = 0.78 * DAILY_SALARY
        elif supply >= 21:
            bid = 0.32 * DAILY_SALARY
        else:
            bid = 0.50 * DAILY_SALARY

    if rich_count >= 2 and supply <= 17:
        bid += 6.0
    if low_hp_count >= 2 and hp >= 6 and supply >= 20:
        bid -= 5.0

    if day >= 8:
        bid += 5.0 * urgency
    if day <= 2 and hp >= 7 and supply >= 20:
        bid -= 4.0

    reserve_target = 0.0
    days_left = max(0, 10 - day)
    if days_left > 0:
        reserve_target = min(budget, days_left * 18.0)
    spend_cap = max(0.0, budget - reserve_target * 0.25)
    if urgency >= 1.0:
        spend_cap = budget

    bid = max(0.0, bid)
    bid = min(bid, spend_cap)
    bid = min(bid, budget)

    if hp <= 2:
        bid = max(bid, min(budget, 60.0))
    elif hp <= 4 and supply <= 18:
        bid = max(bid, min(budget, 48.0))

    return float(round(max(0.0, min(budget, bid)), 2))
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    strongest_prev_bid = 0.0
    cindy_prev_bid = None
    needy_opp_count = 0
    rich_opp_count = 0

    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            needy_opp_count += 1
        if opp.get('budget', 0) >= 200:
            rich_opp_count += 1
        prev = opp.get('previous_trace', {})
        prev_bid = 0.0
        if prev and prev.get('bid') is not None:
            prev_bid = prev['bid']
        if prev_bid > strongest_prev_bid:
            strongest_prev_bid = prev_bid

    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('alive'):
        prev = opponents_status['Cindy'].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            cindy_prev_bid = prev['bid']

    scarcity = supply <= 18
    danger = hp <= 2 or no_water_days >= 1
    moderate_risk = hp <= 4 or no_water_days >= 1

    if danger:
        base = DAILY_SALARY * 0.92
        if scarcity:
            base = max(base, strongest_prev_bid + 3.0)
        elif strongest_prev_bid > 0:
            base = max(base, strongest_prev_bid + 1.5)
        return float(min(budget, base))

    if scarcity:
        base = DAILY_SALARY * 0.58
        if strongest_prev_bid >= 100:
            base = DAILY_SALARY * 0.42
        elif strongest_prev_bid >= 70:
            base = strongest_prev_bid + 2.0
        elif strongest_prev_bid > 0:
            base = max(base, strongest_prev_bid + 1.0)

        if moderate_risk:
            base = max(base, DAILY_SALARY * 0.78)
        if rich_opp_count >= 1 and needy_opp_count >= 1:
            base += 2.0
        return float(min(budget, base))

    if supply >= 22:
        if hp >= 6 and no_water_days == 0:
            return float(min(budget, DAILY_SALARY * 0.18))
        return float(min(budget, DAILY_SALARY * 0.32))

    base = DAILY_SALARY * 0.34
    if strongest_prev_bid >= 100:
        base = DAILY_SALARY * 0.22
    elif strongest_prev_bid >= 70:
        base = DAILY_SALARY * 0.30
    elif strongest_prev_bid > 0:
        base = max(base, min(DAILY_SALARY * 0.48, strongest_prev_bid * 0.7))

    if moderate_risk:
        base = max(base, DAILY_SALARY * 0.52)
    if day >= 8 and hp <= 5:
        base = max(base, DAILY_SALARY * 0.6)

    return float(min(budget, base))
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    danger_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    danger_bids.append(float(bid))

    if not alive:
        return float(min(budget, 8.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    my_urgency = 0.0
    if hp <= 2:
        my_urgency += 0.75
    elif hp <= 4:
        my_urgency += 0.45
    elif hp <= 6:
        my_urgency += 0.2
    if no_water >= 2:
        my_urgency += 0.5
    elif no_water >= 1:
        my_urgency += 0.25
    my_urgency = min(1.0, my_urgency)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_danger = max(danger_bids) if danger_bids else highest_prev

    affordable_pressure = 0.0
    if highest_prev > 0:
        affordable_pressure = min(highest_prev + 1.5, DAILY_SALARY * 1.02)

    base = DAILY_SALARY * (0.34 + 0.28 * scarcity + 0.3 * my_urgency)

    if supply >= 22:
        base *= 0.82
    elif supply <= 17:
        base *= 1.12

    if my_urgency >= 0.7:
        target = max(base, min(highest_danger + 2.0, DAILY_SALARY * 1.1))
    elif scarcity >= 0.6:
        target = max(base, affordable_pressure)
    else:
        target = base

    rich_overbidder = False
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None and float(bid) >= 90.0 and opp.get('budget', 0) > budget:
            rich_overbidder = True
            break

    if rich_overbidder and my_urgency < 0.7 and supply >= 19:
        target = min(target, DAILY_SALARY * 0.62)

    if day >= 8:
        target *= 1.08
    if budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.55)
    elif budget > DAILY_SALARY * 8 and my_urgency >= 0.45:
        target *= 1.06

    floor_bid = 6.0 if hp > 4 and no_water == 0 else 14.0
    bid = max(floor_bid, target)
    bid = min(bid, budget)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.92))

    return float(round(max(0.0, bid), 2))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    yesterday_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) > budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                b = float(prev.get('bid', 0.0))
                if b >= 0:
                    yesterday_bids.append(b)
            except Exception:
                pass

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 2

    phase = 0
    if day >= 8:
        phase = 2
    elif day >= 5:
        phase = 1

    base = 28.0
    if scarcity == 1:
        base = 42.0
    elif scarcity == 2:
        base = 58.0

    if highest_prev >= 300:
        target = base
    elif highest_prev >= 120:
        target = max(base, min(highest_prev * 0.72, 92.0))
    elif highest_prev >= 70:
        target = max(base, min(highest_prev + 3.0, 96.0))
    elif highest_prev > 0:
        target = max(base, highest_prev + 2.0)
    else:
        target = base

    target += urgent_opp * 3.0
    target += rich_opp * 1.5
    target += danger * 8.0
    target += phase * 4.0

    if hp >= 8 and no_water_days == 0 and highest_prev >= 110:
        target = min(target, 40.0)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, 95.0)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, 72.0)

    reserve_days = 10 - day
    if reserve_days < 1:
        reserve_days = 1
    soft_cap = budget / reserve_days + DAILY_SALARY * 0.35
    hard_cap = budget

    if day >= 9:
        soft_cap = budget
    elif hp <= 2:
        soft_cap = min(budget, max(soft_cap, DAILY_SALARY * 1.6))

    bid = min(target, soft_cap, hard_cap)
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    needy_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= DAILY_SALARY * 0.9:
                    aggressive_count += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.55
    if no_water_days >= 2:
        danger += 1.0
    elif no_water_days >= 1:
        danger += 0.45

    base = 22.0 + 18.0 * scarcity + 10.0 * min(needy_count, 3)

    if highest_prev >= 110:
        base += 8.0 if danger > 0.5 else -4.0
    elif highest_prev >= 90:
        base += 5.0 if danger > 0.5 else -2.0
    elif highest_prev > 0:
        base = max(base, min(highest_prev + 2.0, 78.0))

    if aggressive_count >= 2 and danger < 0.5 and supply >= 20:
        base -= 10.0

    if supply <= 17:
        base += 18.0
    elif supply >= 23:
        base -= 8.0

    if day >= 8:
        base += 6.0 * danger

    if danger >= 1.5:
        bid = max(base, min(highest_prev + 4.0, 95.0))
    elif danger >= 0.75:
        bid = max(base, min(avg_prev + 3.0, 82.0))
    else:
        bid = base

    soft_cap = DAILY_SALARY * 1.05
    if hp >= 5 and no_water_days == 0:
        soft_cap = DAILY_SALARY * 0.9
    if danger >= 1.5:
        soft_cap = DAILY_SALARY * 1.4

    bid = max(0.0, min(bid, soft_cap, budget))

    if budget < DAILY_SALARY * 0.75 and danger < 1.0:
        bid = min(bid, budget * 0.55)

    return float(max(0.0, min(bid, budget)))
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
    opp_reqs = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_reqs.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    total_players = 1 + len(alive_opponents)
    total_req = WATER_REQ + sum(opp_reqs)
    scarcity = supply / float(total_req) if total_req > 0 else 1.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    urgent = hp <= 3 or no_water_days >= 2
    fragile = hp <= 5 or no_water_days >= 1

    if urgent:
        target = max(DAILY_SALARY * 0.95, lowest_prev + 3.0)
        if scarcity < 0.32:
            target = max(target, DAILY_SALARY * 1.15)
        return float(min(budget, target))

    if scarcity >= 0.42 and hp >= 7 and no_water_days == 0:
        target = DAILY_SALARY * 0.18
        if lowest_prev > 0:
            target = min(target, max(1.0, lowest_prev * 0.35))
        return float(min(budget, target))

    if fragile:
        target = max(DAILY_SALARY * 0.62, lowest_prev + 2.0)
        if highest_prev >= 140:
            target = min(target, DAILY_SALARY * 0.78)
        return float(min(budget, target))

    target = DAILY_SALARY * 0.35
    if prev_bids:
        if avg_prev >= 120:
            target = DAILY_SALARY * 0.28
        elif avg_prev >= 80:
            target = max(target, lowest_prev + 1.5)
        else:
            target = max(target, avg_prev + 2.0)

    if scarcity < 0.36:
        target = max(target, DAILY_SALARY * 0.55)
    if scarcity < 0.30:
        target = max(target, DAILY_SALARY * 0.72)

    if day >= 8 and hp >= 6 and budget < DAILY_SALARY * 3:
        target *= 0.85

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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    strong_opp_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 4:
                strong_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opps:
        if hp <= 2 or no_water >= 1:
            return min(budget, 28.0)
        return min(budget, 12.0)

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units <= 1.05:
        scarcity = 2
    elif units <= 1.6:
        scarcity = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    danger = 0
    if hp <= 2:
        danger += 2
    elif hp <= 4:
        danger += 1
    if no_water >= 2:
        danger += 2
    elif no_water >= 1:
        danger += 1

    if danger >= 4:
        bid = max(62.0, highest_prev + 4.0)
    elif danger >= 2:
        bid = max(44.0, avg_prev + 3.0, highest_prev * 0.72)
    else:
        if scarcity == 2:
            bid = max(34.0, avg_prev + 2.0)
        elif scarcity == 1:
            bid = max(24.0, avg_prev * 0.7)
        else:
            bid = 16.0

    if highest_prev >= 120.0 and danger == 0:
        bid = min(bid, 22.0)
    elif highest_prev >= 90.0 and danger <= 1:
        bid = min(bid, 28.0)

    if strong_opp_count >= 2 and scarcity >= 1 and danger >= 2:
        bid = max(bid, highest_prev + 1.5)

    if day >= 8 and hp >= 5 and no_water == 0 and scarcity == 0:
        bid = min(bid, 14.0)

    min_guard = 0.0
    if hp <= 2 or no_water >= 2:
        min_guard = 55.0
    elif hp <= 4 or no_water >= 1:
        min_guard = 36.0
    bid = max(bid, min_guard)

    if budget <= 0:
        return 0.0
    return max(0.0, min(float(budget), float(bid)))
"""
