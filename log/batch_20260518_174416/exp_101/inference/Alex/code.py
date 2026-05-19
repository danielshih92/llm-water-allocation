# ============================================================
# Experiment: exp_101
# Agent: Alex
# Source: exp_101
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
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return min(budget, max(0, base))

    highest_prev_bid = None
    desperate_count = 0
    weak_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) < DAILY_SALARY * 2:
            weak_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            if highest_prev_bid is None or bid > highest_prev_bid:
                highest_prev_bid = bid

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0
    if supply_pressure > 1:
        supply_pressure = 1

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    if no_water >= 2:
        urgency += 0.35
    elif no_water >= 1:
        urgency += 0.18
    urgency += 0.22 * supply_pressure
    urgency += 0.05 * desperate_count
    urgency -= 0.04 * weak_count

    if day >= 8:
        urgency += 0.08

    if highest_prev_bid is not None:
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if hp > 4 and no_water == 0:
                target = DAILY_SALARY * 0.28
            else:
                target = min(DAILY_SALARY * 0.98, highest_prev_bid + 1.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.65:
            target = max(DAILY_SALARY * 0.52, highest_prev_bid + 1.25)
        else:
            target = max(DAILY_SALARY * 0.42, highest_prev_bid + 1.0)
    else:
        target = DAILY_SALARY * (0.38 + urgency)

    if supply >= 22 and hp > 4 and no_water == 0:
        target *= 0.82
    elif supply <= 17:
        target *= 1.12

    reserve_floor = 0
    if day <= 7:
        reserve_floor = DAILY_SALARY * (10 - day) * 0.18
    affordable = budget - reserve_floor
    if affordable < 0:
        affordable = budget * 0.5

    bid = min(target, budget, max(0, affordable))

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))
    elif hp <= 4 or no_water >= 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.68))

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
            rich_pressure += min(float(opp.get('budget', 0.0)), 200.0)

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 2:
            return float(min(budget, 45.0))
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.5
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days == 1:
        urgency += 0.45
    urgency += scarcity * 0.8

    conservative = 16.0 + scarcity * 10.0
    pressure_bid = max(avg_prev + 2.0, highest_prev + 1.5)

    if highest_prev >= 100.0:
        if urgency < 1.0:
            bid = conservative
        else:
            bid = min(pressure_bid, 78.0)
    elif highest_prev >= 50.0:
        if urgency < 0.7:
            bid = conservative + 4.0
        else:
            bid = min(pressure_bid, 72.0)
    else:
        if urgency < 0.5:
            bid = max(22.0, avg_prev + 3.0)
        else:
            bid = max(36.0, pressure_bid)

    if rich_pressure > 250.0 and urgency >= 0.8:
        bid += 4.0

    if supply >= 23 and urgency < 1.0:
        bid *= 0.8
    elif supply <= 17:
        bid += 6.0

    if budget < 60.0:
        bid = min(bid, max(12.0, budget * 0.75))
    elif budget < 140.0:
        bid = min(bid, budget * 0.6)
    else:
        bid = min(bid, budget * 0.45)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, highest_prev + 3.0 if highest_prev > 0 else 55.0))

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
        safe_bid = DAILY_SALARY * 0.25
        if hp <= 2 or no_water_days >= 2:
            safe_bid = DAILY_SALARY * 0.7
        return float(min(budget, safe_bid))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 8:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.7
    elif hp <= 4:
        urgency += 0.4
    if no_water_days >= 2:
        urgency += 0.7
    elif no_water_days == 1:
        urgency += 0.25
    if day >= 8:
        urgency += 0.1
    if urgency > 1.2:
        urgency = 1.2

    base = DAILY_SALARY * (0.28 + 0.42 * scarcity + 0.35 * min(1.0, urgency))

    pressure_bid = 0.0
    if highest_prev >= 120:
        pressure_bid = DAILY_SALARY * (0.52 + 0.18 * scarcity)
    elif highest_prev >= 75:
        pressure_bid = min(highest_prev * 0.92 + 1.0, DAILY_SALARY * 1.02)
    elif highest_prev > 0:
        pressure_bid = max(DAILY_SALARY * 0.42, avg_prev + 2.0)
    else:
        pressure_bid = DAILY_SALARY * 0.35

    bid = max(base, pressure_bid)

    if supply >= 22 and urgency < 0.5:
        bid *= 0.78
    elif supply <= 17:
        bid *= 1.18

    if desperate_count >= 2:
        bid *= 1.08
    if rich_count >= 2 and supply <= 18:
        bid *= 1.07

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.92)
    elif hp <= 4 or no_water_days == 1:
        bid = max(bid, DAILY_SALARY * 0.68)

    if day == 1 and supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.48)

    max_affordable = budget
    if day < 10:
        reserve = max(0.0, (10 - day) * DAILY_SALARY * 0.08)
        max_affordable = max(0.0, budget - reserve)
        if hp <= 3 or no_water_days >= 2:
            max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_pressures = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                pressure = bid / max(1.0, float(opp.get('daily_salary', DAILY_SALARY)))
                opp_pressures.append((bid, pressure, opp))

    if not alive:
        return max(0.0, min(budget, 18.0))

    competitors = len(alive) + 1
    guaranteed_winners = int(float(supply) // WATER_REQ)
    contest_ratio = float(supply) / float(WATER_REQ * competitors)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    desperate_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        if opp.get('budget', 0) >= 250:
            rich_opp += 1

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

    if guaranteed_winners <= 1:
        urgency += 2
    elif guaranteed_winners <= 2:
        urgency += 1

    if desperate_opp >= 2:
        urgency += 1
    if rich_opp >= 2:
        urgency += 1

    if highest_prev >= 140:
        market = 'very_high'
    elif highest_prev >= 115:
        market = 'high'
    elif highest_prev >= 85:
        market = 'medium'
    else:
        market = 'low'

    if urgency >= 6:
        target = max(145.0, highest_prev + 2.5)
    elif urgency >= 4:
        if market == 'very_high':
            target = highest_prev + 1.5
        elif market == 'high':
            target = max(124.0, highest_prev + 1.0)
        else:
            target = max(98.0, avg_prev + 8.0)
    elif urgency >= 2:
        if guaranteed_winners >= 2 and contest_ratio > 0.32:
            target = max(72.0, avg_prev * 0.88)
        else:
            if market == 'very_high':
                target = 108.0
            elif market == 'high':
                target = 92.0
            elif market == 'medium':
                target = avg_prev + 2.0
            else:
                target = 62.0
    else:
        if guaranteed_winners >= 2 and contest_ratio >= 0.35:
            target = 48.0
        elif market in ('very_high', 'high'):
            target = 36.0
        else:
            target = 55.0

    reserve_floor = 0.0
    if hp <= 3 or no_water_days >= 1:
        reserve_floor = 0.0
    else:
        reserve_floor = DAILY_SALARY * 1.2

    if budget <= DAILY_SALARY * 0.8:
        target = min(target, budget)
    else:
        target = min(target, max(0.0, budget - reserve_floor))

    if hp <= 2 or no_water_days >= 2:
        target = max(target, min(budget, highest_prev + 3.0 if highest_prev > 0 else 110.0))

    if budget > 350 and urgency >= 4:
        target += 4.0

    target = max(0.0, min(float(budget), float(target)))
    return target
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    strong_pressure = 0
    weak_pressure = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 120:
                    strong_pressure += 1
                elif float(bid) >= 50:
                    weak_pressure += 1

    if not alive_opps:
        return float(min(budget, 18.0 if hp > 4 else 35.0))

    competitor_count = len(alive_opps) + 1
    scarcity = competitor_count * WATER_REQ - supply

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

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

    if scarcity > 20:
        urgency += 3
    elif scarcity > 10:
        urgency += 2
    elif scarcity > 0:
        urgency += 1

    if supply <= 16:
        urgency += 2
    elif supply <= 19:
        urgency += 1
    elif supply >= 23:
        urgency -= 1

    if strong_pressure >= 2:
        urgency += 1
    elif strong_pressure == 0 and weak_pressure <= 1:
        urgency -= 1

    days_left = max(0, 10 - day)
    reserve_target = max(0.0, days_left * 18.0)
    spendable = max(0.0, budget - reserve_target)

    if urgency <= 0:
        base_bid = 16.0 if supply >= 22 else 22.0
    elif urgency == 1:
        base_bid = max(28.0, avg_prev * 0.45)
    elif urgency == 2:
        base_bid = max(42.0, avg_prev * 0.62, highest_prev * 0.38)
    elif urgency == 3:
        base_bid = max(60.0, avg_prev * 0.78, highest_prev * 0.52)
    elif urgency == 4:
        base_bid = max(82.0, avg_prev * 0.92, highest_prev * 0.68)
    else:
        base_bid = max(110.0, avg_prev * 1.02, highest_prev * 0.82)

    if hp <= 2 or no_water >= 2:
        base_bid = max(base_bid, highest_prev + 3.0 if highest_prev > 0 else 95.0)

    if supply >= 23 and hp > 4 and no_water == 0:
        base_bid *= 0.72
    elif supply >= 20 and urgency <= 2:
        base_bid *= 0.85

    if strong_pressure >= 2 and urgency <= 2 and hp > 4:
        base_bid *= 0.8

    if spendable > 0:
        cap = min(budget, spendable + 35.0)
    else:
        cap = min(budget, 55.0 if urgency <= 2 else budget)

    bid = min(base_bid, cap)

    if hp <= 2 and budget > 0:
        bid = max(bid, min(budget, 90.0))
    if no_water >= 2 and budget > 0:
        bid = max(bid, min(budget, 105.0))

    bid = max(0.0, min(float(budget), float(bid)))
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    aggressive = 0
    weak_opp_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 120:
                aggressive += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2 or opp.get('budget', 0) < 40:
            weak_opp_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    alive_count = len(alive_opponents)

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
        danger += 1

    if alive_count == 0:
        if danger >= 3:
            return float(min(budget, 20.0))
        return float(min(budget, 5.0))

    if slots >= 2:
        if danger >= 5:
            bid = 95.0
        elif danger >= 3:
            bid = 58.0
        else:
            if aggressive >= 2:
                bid = 9.0
            elif highest_prev >= 150:
                bid = 12.0
            else:
                bid = 18.0
    else:
        if danger >= 5:
            bid = max(110.0, highest_prev + 3.0)
        elif danger >= 3:
            bid = max(82.0, min(118.0, avg_prev + 6.0))
        else:
            if aggressive >= 2:
                bid = 22.0
            elif highest_prev >= 150:
                bid = 28.0
            else:
                bid = max(35.0, min(75.0, highest_prev + 2.0))

    if weak_opp_count >= 2 and danger <= 2:
        bid *= 0.8

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.75)
    else:
        bid = min(bid, budget * 0.6)

    if danger >= 5:
        bid = max(bid, min(budget, 90.0))
    elif danger >= 3:
        bid = max(bid, min(budget, 55.0))

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    needy_pressure = 0.0
    rich_pressure = 0.0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            opp_hp = opp.get('hp', 10)
            opp_no_water = opp.get('no_water_days', 0)
            opp_budget = opp.get('budget', 0)
            if opp_hp <= 3 or opp_no_water >= 1:
                needy_pressure = max(needy_pressure, min(float(opp_budget), DAILY_SALARY * 1.2))
            if opp_budget >= DAILY_SALARY * 3:
                rich_pressure = max(rich_pressure, DAILY_SALARY * 0.95)

    if not alive:
        return max(0.0, min(float(budget), DAILY_SALARY * 0.35))

    slots = max(1, int(supply // WATER_REQ))
    competitors = len(alive) + 1
    scarcity = competitors - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    pressure = max(highest_prev, needy_pressure, rich_pressure)

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
    if day >= 8:
        urgency += 1

    if budget <= 0:
        return 0.0

    if slots >= competitors:
        if urgency >= 3:
            bid = DAILY_SALARY * 0.28
        else:
            bid = DAILY_SALARY * 0.12
        return max(0.0, min(float(budget), bid))

    if urgency >= 5:
        bid = max(DAILY_SALARY * 0.95, pressure + 2.0)
    elif urgency >= 3:
        if pressure >= DAILY_SALARY * 1.3:
            bid = DAILY_SALARY * 0.72
        else:
            bid = max(DAILY_SALARY * 0.62, min(pressure + 1.5, DAILY_SALARY * 1.02))
    else:
        if pressure >= DAILY_SALARY * 1.15:
            bid = DAILY_SALARY * 0.22
        elif pressure >= DAILY_SALARY * 0.8:
            bid = DAILY_SALARY * 0.38
        else:
            bid = max(DAILY_SALARY * 0.34, avg_prev + 1.0)

    if scarcity >= 3:
        bid += DAILY_SALARY * 0.12
    elif scarcity >= 2:
        bid += DAILY_SALARY * 0.07
    elif scarcity <= 0:
        bid -= DAILY_SALARY * 0.08

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.92)
    elif budget < DAILY_SALARY * 2 and urgency < 3:
        bid = min(bid, DAILY_SALARY * 0.58)

    if hp >= 8 and no_water == 0 and pressure >= DAILY_SALARY * 1.2 and slots == 1:
        bid = min(bid, DAILY_SALARY * 0.2)

    return max(0.0, min(float(budget), float(bid)))
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

    alive = []
    prev_bids = []
    pressure_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if opp.get('hp', 0) > 0 and opp.get('budget', 0) > 0:
                    pressure_bids.append(bid)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    active_pressure = max(pressure_bids) if pressure_bids else highest_prev

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tight_supply = supply <= 18
    very_tight_supply = supply <= 16

    urgent = hp <= 3 or no_water_days >= 2
    semi_urgent = hp <= 5 or no_water_days >= 1

    target = DAILY_SALARY * 0.45

    if urgent:
        target = max(target, DAILY_SALARY * 0.92)
    elif semi_urgent:
        target = max(target, DAILY_SALARY * 0.72)

    if very_tight_supply:
        target = max(target, active_pressure + 3.0, DAILY_SALARY * 0.82)
    elif tight_supply:
        target = max(target, active_pressure + 1.5, DAILY_SALARY * 0.62)
    else:
        if active_pressure > DAILY_SALARY * 1.2:
            target = max(target, DAILY_SALARY * 0.38)
        else:
            target = max(target, min(DAILY_SALARY * 0.6, active_pressure + 1.0))

    if budget < DAILY_SALARY * 2 and not urgent:
        target = min(target, DAILY_SALARY * 0.5)

    if hp >= 8 and no_water_days == 0 and scarcity > 0.6 and not tight_supply:
        target = min(target, DAILY_SALARY * 0.4)

    if day >= 8 and hp > 4:
        target = min(target, DAILY_SALARY * 0.58)

    bid = min(budget, target)
    if budget > 0 and urgent:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    return max(0.0, float(bid))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    pressure_bids = []
    urgent_opps = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                weighted = float(bid)
                if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                    weighted += 8.0
                    urgent_opps += 1
                if opp.get('budget', 0) < float(bid):
                    weighted = max(weighted * 0.75, 0.0)
                pressure_bids.append(weighted)

    if not alive:
        return float(min(budget, 18.0))

    competitors = len(alive) + 1
    expected_units = float(supply) / float(WATER_REQ)
    tightness = competitors - expected_units

    strongest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_pressure = max(pressure_bids) if pressure_bids else 0.0

    if hp <= 2 or no_water >= 2:
        emergency = max(62.0, strongest_prev + 3.0, strongest_pressure)
        return float(min(budget, emergency))

    if hp <= 4 or no_water >= 1:
        if tightness > 2.0:
            bid = max(52.0, strongest_prev + 2.0, strongest_pressure)
        else:
            bid = max(42.0, min(58.0, strongest_prev + 1.0))
        return float(min(budget, bid))

    if supply >= 23:
        base = 16.0
    elif supply >= 20:
        base = 24.0
    elif supply >= 18:
        base = 34.0
    else:
        base = 44.0

    if tightness > 2.5:
        base += 12.0
    elif tightness > 1.5:
        base += 7.0
    elif tightness < 0.5:
        base -= 6.0

    if strongest_prev >= 110.0:
        base = min(base, 28.0)
    elif strongest_prev >= 80.0:
        base = min(max(base, 26.0), 40.0)
    elif strongest_prev > 0.0:
        target = strongest_prev + 1.5
        if target <= 55.0:
            base = max(base, target)

    if urgent_opps >= 2 and supply <= 17:
        base += 8.0

    if budget < 120.0:
        base = min(base, 0.42 * budget)
    elif budget < 220.0:
        base = min(base, 0.33 * budget)

    base = max(8.0, min(base, 63.0))
    return float(min(budget, base))
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

    alive_opponents = []
    prev_bids = []
    opp_budgets = []
    urgent_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    richest_opp = max(opp_budgets) if opp_budgets else 0.0

    very_tight = supply <= 16
    tight = supply <= 18
    comfortable = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        bid = max(92.0, highest_prev + 3.0)
    elif hp <= 4 or no_water_days >= 1:
        if very_tight:
            bid = max(86.0, highest_prev + 2.0)
        else:
            bid = max(74.0, avg_prev + 2.0)
    else:
        if very_tight:
            bid = max(80.0, highest_prev + 1.5)
        elif tight:
            if highest_prev >= 95.0:
                bid = 61.0
            else:
                bid = max(66.0, avg_prev + 1.0)
        elif comfortable:
            if highest_prev >= 90.0:
                bid = 34.0
            else:
                bid = 46.0
        else:
            bid = 54.0

    if urgent_opp >= 2 and hp >= 5 and no_water_days == 0:
        bid *= 0.9

    if richest_opp < budget * 0.7 and hp >= 4:
        bid *= 1.05

    max_safe = budget
    if hp >= 5 and no_water_days == 0:
        reserve = DAILY_SALARY * 2.2
        max_safe = max(0.0, budget - reserve)
        if max_safe <= 0:
            max_safe = min(budget, 42.0)
    elif hp >= 3:
        reserve = DAILY_SALARY * 1.2
        max_safe = max(0.0, budget - reserve)
        if max_safe <= 0:
            max_safe = budget

    bid = min(bid, max_safe)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
"""
