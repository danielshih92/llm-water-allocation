# ============================================================
# Experiment: exp_034
# Agent: Alex
# Source: exp_034
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

    alive = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return max(0, min(budget, 18.0))

    prev_bids = []
    stressed_opponents = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            stressed_opponents += 1

    player_count = 1 + len(alive)
    approx_units = supply / float(WATER_REQ)
    scarcity = approx_units < player_count

    if hp <= 2 or no_water >= 2:
        base = DAILY_SALARY * 0.96
    elif hp <= 4 or no_water >= 1:
        base = DAILY_SALARY * 0.82
    elif scarcity:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.38

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if hp <= 4 or no_water >= 1:
            target = max(base, highest_prev + 2.0)
        else:
            target = max(base, avg_prev + 1.0)
            if highest_prev >= DAILY_SALARY * 0.9 and hp > 4 and no_water == 0:
                target = min(target, DAILY_SALARY * 0.45)
    else:
        target = base

    if stressed_opponents >= max(1, len(alive) // 2):
        target += 3.0

    if supply >= 22:
        target -= 4.0
    elif supply <= 17:
        target += 4.0

    target = max(0.0, min(float(budget), float(target)))
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

    alive_opponents = []
    prev_bids = []
    rich_threat = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            rich_threat = max(rich_threat, opp.get('budget', 0.0))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opponents:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgency = 0
    if hp <= 3:
        urgency += 3
    elif hp <= 5:
        urgency += 2
    elif hp <= 7:
        urgency += 1
    if no_water_days >= 2:
        urgency += 3
    elif no_water_days >= 1:
        urgency += 2

    scarcity = 0
    if supply <= 16:
        scarcity = 3
    elif supply <= 19:
        scarcity = 2
    elif supply <= 22:
        scarcity = 1

    pressure = 0
    if highest_prev >= 110:
        pressure = 3
    elif highest_prev >= 80:
        pressure = 2
    elif highest_prev >= 45:
        pressure = 1

    base = 20.0
    if scarcity == 3:
        base = 62.0
    elif scarcity == 2:
        base = 48.0
    elif scarcity == 1:
        base = 34.0
    else:
        base = 22.0

    bid = base + urgency * 10.0

    if pressure >= 2 and urgency <= 1 and scarcity <= 1:
        bid = min(bid, 26.0)
    elif pressure >= 2:
        bid = max(bid, min(highest_prev + 2.0, 96.0))
    elif pressure == 1:
        bid = max(bid, min(highest_prev + 1.5, 72.0))
    else:
        bid = max(bid, avg_prev + 2.0)

    if budget < 90:
        bid = min(bid, budget * 0.72)
    elif budget < 160:
        bid = min(bid, budget * 0.82)

    if rich_threat > budget * 2 and urgency <= 1 and scarcity <= 1:
        bid = min(bid, 24.0)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(98.0, budget))

    if day >= 8:
        bid += 6.0
    if day >= 9 and (hp <= 5 or no_water_days >= 1):
        bid += 8.0

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(min(budget, base))

    opp_bids = []
    urgent_opp_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            opp_bids.append(float(bid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp_bids.append(float(bid))

    if opp_bids:
        highest_prev = max(opp_bids)
        avg_prev = sum(opp_bids) / float(len(opp_bids))
    else:
        highest_prev = DAILY_SALARY * 0.7
        avg_prev = DAILY_SALARY * 0.6

    if urgent_opp_bids:
        pressure_bid = max(highest_prev, max(urgent_opp_bids) + 1.0)
    else:
        pressure_bid = highest_prev + 1.5

    if supply <= 16:
        scarcity = 'high'
    elif supply <= 19:
        scarcity = 'medium'
    else:
        scarcity = 'low'

    if hp <= 2 or no_water_days >= 2:
        if scarcity == 'high':
            bid = max(pressure_bid, DAILY_SALARY * 0.96)
        elif scarcity == 'medium':
            bid = max(pressure_bid, DAILY_SALARY * 0.88)
        else:
            bid = max(avg_prev + 2.0, DAILY_SALARY * 0.78)
    elif hp <= 4 or no_water_days >= 1:
        if scarcity == 'high':
            bid = max(pressure_bid, DAILY_SALARY * 0.86)
        elif scarcity == 'medium':
            bid = max(avg_prev + 1.5, DAILY_SALARY * 0.72)
        else:
            bid = max(avg_prev, DAILY_SALARY * 0.58)
    else:
        if scarcity == 'high':
            bid = max(avg_prev, DAILY_SALARY * 0.62)
        elif scarcity == 'medium':
            bid = max(avg_prev - 3.0, DAILY_SALARY * 0.48)
        else:
            bid = DAILY_SALARY * 0.28

    if day >= 8 and hp >= 5 and no_water_days == 0:
        bid *= 0.9

    reserve_floor = 0.0
    if day <= 5:
        reserve_floor = DAILY_SALARY * 2.2
    elif day <= 8:
        reserve_floor = DAILY_SALARY * 1.2
    max_affordable = budget
    if budget > reserve_floor:
        max_affordable = budget - reserve_floor + min(reserve_floor * 0.15, DAILY_SALARY * 0.5)

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0

    if hp >= 6 and no_water_days == 0 and scarcity == 'low':
        bid = min(bid, DAILY_SALARY * 0.35)

    return float(max(0.0, bid))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 55.0))

    prev_bids = []
    urgent_affordable = []
    rich_pressure = []

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
        opp_hp = opp.get('hp', 10)
        opp_no = opp.get('no_water_days', 0)
        opp_budget = float(opp.get('budget', 0))
        opp_salary = float(opp.get('daily_salary', 0))
        req = float(opp.get('water_requirement', WATER_REQ))

        est = 0.0
        if pbid is not None:
            est = float(pbid)
        else:
            if opp_no >= 2 or opp_hp <= 3:
                est = opp_salary * 0.9
            elif opp_budget > 400:
                est = opp_salary * 0.75
            else:
                est = opp_salary * 0.45

        if opp_no >= 2 or opp_hp <= 3:
            urgent_affordable.append(min(opp_budget, est))
        if opp_budget > 250:
            rich_pressure.append(min(opp_budget, max(est, opp_salary * 0.65)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_urgent = max(urgent_affordable) if urgent_affordable else 0.0
    rich_max = max(rich_pressure) if rich_pressure else 0.0

    danger = 0
    if no_water >= 2 or hp <= 2:
        danger = 3
    elif no_water >= 1 or hp <= 4:
        danger = 2
    elif hp <= 6:
        danger = 1

    if danger == 3:
        bid = max(63.0, strongest_urgent + 2.0, highest_prev * 0.92)
    elif danger == 2:
        bid = max(42.0, strongest_urgent + 1.5, min(highest_prev * 0.72, 68.0))
    else:
        if slots >= 1:
            if highest_prev > 120:
                bid = 12.0
            elif highest_prev > 85:
                bid = 18.0
            else:
                bid = 24.0
        else:
            bid = 28.0

    if day >= 8 and hp >= 5 and budget < 140:
        bid = min(bid, 20.0)

    if rich_max > 110 and danger == 0:
        bid = min(bid, 16.0)

    if strongest_urgent > 0 and danger >= 2:
        bid = max(bid, min(strongest_urgent + 2.0, budget))

    if budget < 50:
        bid = min(bid, max(8.0, budget * 0.72))

    if no_water == 0 and hp >= 7 and slots >= 1 and highest_prev >= 100:
        bid = min(bid, 14.0)

    bid = max(0.0, min(float(bid), float(budget)))
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if no_water_days >= 2 or hp <= 3:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    urgent_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 300:
            rich_count += 1
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            urgent_count += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 18
    loose_supply = supply >= 22

    if no_water_days >= 2:
        base = max(DAILY_SALARY * 1.25, highest_prev + 2.0, 95.0)
        if urgent_count >= 2:
            base += 8.0
        if tight_supply:
            base += 10.0
        return float(min(budget, base))

    if hp <= 3:
        base = max(DAILY_SALARY * 1.05, highest_prev * 0.92, 78.0)
        if tight_supply:
            base += 8.0
        return float(min(budget, base))

    if no_water_days == 1:
        if tight_supply:
            base = max(82.0, highest_prev * 0.82, avg_prev * 0.88)
            if urgent_count >= 1:
                base += 6.0
            return float(min(budget, base))
        if loose_supply:
            base = max(58.0, highest_prev * 0.58)
            return float(min(budget, base))
        base = max(68.0, highest_prev * 0.68)
        return float(min(budget, base))

    if highest_prev >= 125:
        if loose_supply:
            return float(min(budget, 24.0))
        return float(min(budget, 32.0))

    if highest_prev >= 100:
        if tight_supply:
            return float(min(budget, 48.0))
        return float(min(budget, 28.0))

    if avg_prev >= 80:
        return float(min(budget, 30.0 if loose_supply else 40.0))

    base = DAILY_SALARY * 0.42
    if rich_count >= 2:
        base -= 4.0
    if day >= 8:
        base += 6.0
    if tight_supply:
        base += 5.0
    return float(min(budget, max(18.0, base)))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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
    bob_bid = None
    cindy_bid = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if agent_id == 'Bob':
                    bob_bid = bid
                elif agent_id == 'Cindy':
                    cindy_bid = bid

    if budget <= 0:
        return 0.0

    units = supply / float(WATER_REQ)
    scarce = units < (len(alive) + 1)
    very_scarce = units < max(1.5, (len(alive) + 1) * 0.7)

    danger = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if not alive:
        if critical:
            return float(min(budget, 40.0))
        return float(min(budget, 15.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    target = 0.0

    if critical:
        if bob_bid is not None:
            target = max(88.0, bob_bid + 3.0)
        else:
            target = 90.0
        if cindy_bid is not None and cindy_bid < target and cindy_bid <= 110:
            target = cindy_bid + 2.0
    elif danger:
        if very_scarce:
            if bob_bid is not None:
                target = max(80.0, bob_bid + 2.0)
            else:
                target = 82.0
        elif scarce:
            if bob_bid is not None:
                target = max(72.0, bob_bid + 1.5)
            else:
                target = 74.0
        else:
            target = 46.0
    else:
        if very_scarce:
            if bob_bid is not None:
                target = max(76.0, bob_bid + 1.0)
            else:
                target = 78.0
        elif scarce:
            if bob_bid is not None:
                target = max(60.0, min(76.0, bob_bid - 2.0))
            else:
                target = 62.0
        else:
            target = 28.0

    if cindy_bid is not None and cindy_bid >= 120 and not danger:
        target = min(target, 65.0 if scarce else 30.0)

    if day >= 8:
        target += 4.0
    if hp >= 8 and not scarce:
        target -= 4.0

    target = max(0.0, min(float(budget), target))
    return float(target)
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    winners_est = int(supply / WATER_REQ)
    if winners_est < 1:
        winners_est = 1

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 200:
            rich_opp += 1
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    if hp <= 2 or no_water >= 2:
        bid = max(63.0, highest_prev + 1.5)
    elif hp <= 4 or no_water >= 1:
        if highest_prev >= 85:
            bid = 62.0
        else:
            bid = max(48.0, avg_prev + 3.0)
    else:
        if winners_est >= 2:
            bid = 26.0
            if highest_prev < 35:
                bid = 22.0
            elif highest_prev < 55:
                bid = 30.0
            elif highest_prev < 80:
                bid = 34.0
            else:
                bid = 28.0
        else:
            if highest_prev >= 85:
                bid = 58.0
            elif highest_prev >= 70:
                bid = 52.0
            else:
                bid = max(40.0, highest_prev + 2.0)

    if urgent_opp >= 2 and winners_est <= 1:
        bid += 6.0
    elif urgent_opp == 0 and winners_est >= 2 and hp >= 7:
        bid -= 4.0

    if rich_opp >= 2 and highest_prev >= 85 and hp > 4 and no_water == 0:
        bid -= 6.0

    if day >= 8:
        bid += 5.0
    if day >= 9 and hp <= 5:
        bid += 8.0

    max_safe = budget
    if hp > 5 and no_water == 0:
        reserve = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
        if max_safe > reserve:
            max_safe = max_safe
    bid = min(bid, max_safe)

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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.7
        return float(min(budget, max(0.0, base)))

    prev_bids = []
    rich_aggressive = 0
    desperate_opponents = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 120:
                rich_aggressive += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opponents += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    if hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * 1.25
    elif hp <= 4 or no_water_days >= 1:
        bid = DAILY_SALARY * (0.9 + 0.35 * supply_pressure)
    else:
        bid = DAILY_SALARY * (0.22 + 0.18 * supply_pressure)
        if day >= 8:
            bid += DAILY_SALARY * 0.08

    if highest_prev >= 150 and hp > 4 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * (0.18 + 0.12 * supply_pressure))
    elif highest_prev >= 90 and hp <= 4:
        bid = max(bid, min(highest_prev * 0.72, DAILY_SALARY * 1.05))
    elif highest_prev > 0 and highest_prev < 80 and (hp <= 4 or no_water_days >= 1):
        bid = max(bid, highest_prev + 2.0)

    if rich_aggressive >= 2 and hp > 4 and no_water_days == 0:
        bid *= 0.8

    if desperate_opponents >= 2 and (hp <= 4 or no_water_days >= 1):
        bid *= 1.12

    if day >= 9 and hp > 5 and no_water_days == 0:
        bid *= 0.9

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.92)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))
                if prev.get('status') != 'won':
                    desperate_count += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if tight_supply:
        urgency += 2
    elif medium_supply:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1

    if urgency >= 7:
        bid = max(62.0, highest_prev + 2.0, avg_prev + 8.0)
    elif urgency >= 5:
        bid = max(48.0, avg_prev + 4.0)
    elif urgency >= 3:
        bid = max(32.0, avg_prev * 0.7)
    else:
        if highest_prev >= 120:
            bid = 14.0
        elif highest_prev >= 90:
            bid = 18.0
        elif highest_prev >= 60:
            bid = 24.0
        else:
            bid = 28.0 if medium_supply else 22.0

    if rich_count >= 2 and hp >= 6 and no_water_days == 0:
        bid = min(bid, 20.0)

    days_left = max(0, 10 - day)
    reserve_target = days_left * 18.0
    if budget > reserve_target + 80:
        bid += 6.0
    elif budget < reserve_target:
        bid = min(bid, 24.0 if urgency < 5 else bid)

    if day >= 8 and hp <= 4:
        bid = max(bid, 58.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

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
    desperate_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    if bid >= DAILY_SALARY * 0.85:
                        aggressive_bids.append(bid)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if tight_supply:
        urgency += 2
    elif medium_supply:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1

    if urgency >= 7:
        bid = max(DAILY_SALARY * 1.15, highest_prev + 3.0)
    elif urgency >= 5:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0 if highest_prev > 0 else DAILY_SALARY * 0.95)
    elif urgency >= 3:
        if highest_prev >= 140:
            bid = DAILY_SALARY * 0.58
        else:
            bid = max(DAILY_SALARY * 0.68, min(highest_prev + 1.5, DAILY_SALARY * 0.9))
    else:
        if highest_prev >= 140 or avg_prev >= 120:
            bid = DAILY_SALARY * 0.32
        elif highest_prev >= DAILY_SALARY * 0.9:
            bid = DAILY_SALARY * 0.42
        else:
            bid = max(DAILY_SALARY * 0.38, min(highest_prev + 1.0, DAILY_SALARY * 0.62)) if highest_prev > 0 else DAILY_SALARY * 0.4

    if day >= 8 and hp > 4 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.5)

    if budget < DAILY_SALARY * 0.8:
        bid = min(bid, budget)
    else:
        reserve_floor = 0.0
        if day <= 7:
            reserve_floor = DAILY_SALARY * 0.35
        bid = min(bid, max(0.0, budget - reserve_floor))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    bid = max(0.0, min(budget, bid))
    return float(bid)
"""
