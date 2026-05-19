# ============================================================
# Experiment: exp_068
# Agent: Alex
# Source: exp_068
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])

    if budget <= 0:
        return 0

    units = supply / float(WATER_REQ)
    base = DAILY_SALARY * 0.42

    if units >= len(alive_opponents) + 1:
        base = DAILY_SALARY * 0.22
    elif units >= max(1, len(alive_opponents) * 0.6):
        base = DAILY_SALARY * 0.4
    else:
        base = DAILY_SALARY * 0.62

    if hp <= 2 or no_water >= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4 or no_water >= 1:
        base = max(base, DAILY_SALARY * 0.72)

    if desperate_count > 0:
        base += min(10, 3 * desperate_count)

    if prev_bids:
        highest_prev = max(prev_bids)
        if hp <= 4 or no_water >= 1:
            target = highest_prev + 2
            if target > base:
                base = target
        else:
            if highest_prev >= DAILY_SALARY * 0.9:
                base = min(base, DAILY_SALARY * 0.38)
            elif highest_prev >= DAILY_SALARY * 0.65:
                base = max(base, highest_prev * 0.9)
            else:
                base = max(base, highest_prev + 1)

    if day >= 8:
        base += 6
    elif day <= 2 and hp > 4 and no_water == 0:
        base -= 4

    reserve = 0
    if day < 9:
        reserve = max(0, (10 - day) * 4)
    cap = max(0, budget - reserve)
    if hp <= 2 or no_water >= 2:
        cap = budget

    bid = min(base, cap if cap > 0 else budget)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    bob_like_bids = []
    extreme_bids = []
    broke_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) <= 0:
                broke_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid <= 100:
                    bob_like_bids.append(float(bid))
                else:
                    extreme_bids.append(float(bid))

    if len(alive) == 0:
        return float(min(budget, DAILY_SALARY * 0.25))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = False
    if hp <= 2 or no_water_days >= 2:
        urgent = True

    if bob_like_bids:
        anchor = max(bob_like_bids)
    elif prev_bids:
        anchor = min(max(prev_bids), DAILY_SALARY * 0.95)
    else:
        anchor = DAILY_SALARY * 0.5

    base = DAILY_SALARY * (0.42 + 0.28 * scarcity)
    target = max(base, anchor + 2.0)

    if extreme_bids and not urgent and hp >= 4:
        target = min(target, DAILY_SALARY * (0.62 + 0.08 * scarcity))

    if broke_count >= 1:
        target *= 0.94

    if hp <= 4:
        target += 8.0
    if hp <= 2:
        target += 14.0
    if no_water_days >= 1:
        target += 6.0
    if no_water_days >= 2:
        target += 12.0

    if supply <= 17:
        target += 6.0
    elif supply >= 23:
        target -= 5.0

    if day >= 8 and hp > 4:
        target *= 0.95

    safe_cap = budget
    if not urgent:
        safe_cap = min(budget, DAILY_SALARY * 1.05)
    else:
        safe_cap = min(budget, DAILY_SALARY * 1.35)

    bid = max(0.0, min(target, safe_cap))
    return float(round(bid, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    prev_bids = []
    cindy_bid = None
    eric_bid = None
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp_id == 'Cindy':
                cindy_bid = float(bid)
            if opp_id == 'Eric':
                eric_bid = float(bid)

    if eric_bid is None:
        eric_bid = 15.0

    tight_supply = supply <= 17
    very_tight_supply = supply <= 15

    danger = False
    if hp <= 3 or no_water >= 2:
        danger = True

    severe_danger = False
    if hp <= 2 or no_water >= 3:
        severe_danger = True

    if severe_danger:
        target = 96.0
        if cindy_bid is not None:
            target = max(target, cindy_bid + 2.0)
        return float(min(budget, target))

    if danger:
        if tight_supply:
            target = 92.0
            if cindy_bid is not None:
                target = max(target, cindy_bid + 1.0)
            return float(min(budget, target))
        return float(min(budget, max(28.0, eric_bid + 3.0)))

    if very_tight_supply:
        target = 88.0
        if cindy_bid is not None and cindy_bid < 110.0:
            target = max(target, cindy_bid + 1.0)
        return float(min(budget, target))

    if tight_supply:
        return float(min(budget, max(22.0, eric_bid + 2.5)))

    if cindy_bid is not None and cindy_bid >= 90.0:
        return float(min(budget, max(16.5, eric_bid + 1.0)))

    if prev_bids:
        highest_prev = max(prev_bids)
        target = min(highest_prev + 1.0, 30.0)
        target = max(target, eric_bid + 1.0, 16.0)
        return float(min(budget, target))

    return float(min(budget, 17.0))
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

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.25
        if hp <= 2 or no_water >= 2:
            safe_bid = DAILY_SALARY * 0.6
        return float(min(budget, safe_bid))

    total_agents = 1 + len(alive_opponents)
    total_req = WATER_REQ
    for req in opp_requirements:
        total_req += req

    scarcity = supply < total_req
    severe_scarcity = supply <= max(WATER_REQ, 15)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    if severe_scarcity:
        danger += 2
    elif scarcity:
        danger += 1

    if highest_prev >= 90:
        if danger >= 5:
            bid = 96.0
        elif danger >= 3:
            bid = 78.0
        else:
            bid = 46.0
    elif highest_prev >= 75:
        if danger >= 5:
            bid = highest_prev + 4.0
        elif danger >= 3:
            bid = highest_prev + 1.5
        else:
            bid = 52.0
    elif highest_prev > 0:
        if danger >= 5:
            bid = max(72.0, highest_prev + 3.0)
        elif danger >= 3:
            bid = max(58.0, avg_prev + 2.0)
        else:
            bid = max(40.0, avg_prev * 0.75)
    else:
        if danger >= 5:
            bid = 75.0
        elif danger >= 3:
            bid = 58.0
        else:
            bid = 42.0

    if supply >= 24:
        bid -= 8.0
    elif supply >= 20:
        bid -= 4.0
    elif supply <= 16:
        bid += 6.0

    if hp >= 8 and no_water == 0 and highest_prev >= 90:
        bid = min(bid, 44.0)

    reserve_floor = DAILY_SALARY * 0.35
    if budget < bid:
        bid = budget
    elif budget - bid < reserve_floor and danger < 4:
        bid = max(0.0, budget - reserve_floor)

    if danger >= 5:
        bid = max(bid, min(budget, 82.0))

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
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = (supply <= 17)
    supply_loose = (supply >= 22)
    critical_me = (hp <= 3 or no_water_days >= 1)
    fragile_me = (hp <= 5)

    base = 0.0

    if critical_me:
        base = max(62.0, highest_prev + 2.0)
        if supply_tight:
            base = max(base, 78.0)
    elif fragile_me:
        base = max(42.0, avg_prev * 0.72)
        if supply_tight:
            base = max(base, highest_prev + 1.0)
    else:
        if supply_loose and urgent_opp == 0:
            base = 16.0
        elif supply_loose:
            base = 22.0
        elif supply_tight:
            base = max(34.0, avg_prev * 0.55)
        else:
            base = max(24.0, avg_prev * 0.45)

    if highest_prev >= 110:
        if critical_me:
            base = max(base, 84.0)
        else:
            base = min(base, 36.0)
    elif highest_prev >= 90:
        if critical_me or fragile_me:
            base = max(base, 58.0)
        else:
            base = min(base, 32.0)

    if rich_opp >= 2 and supply_tight and not critical_me:
        base = min(base, 28.0)

    remaining_days = max(0, 10 - day)
    reserve_target = remaining_days * 18.0
    spendable = max(0.0, budget - reserve_target)

    if critical_me:
        cap = min(budget, max(70.0, spendable + 35.0))
    elif fragile_me:
        cap = min(budget, max(52.0, spendable + 20.0))
    else:
        cap = min(budget, max(34.0, spendable + 8.0))

    bid = min(base, cap)

    if budget < 25:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, 95.0)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

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
        return float(min(budget, 18.0))

    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1
        if opp.get('budget', 0) >= 140:
            rich_opp_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

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

    remaining_days = max(1, 10 - int(day) + 1)
    reserve_target = max(0.0, remaining_days * 18.0)
    spendable = max(0.0, budget - reserve_target)

    base = 20.0 + 18.0 * scarcity

    if highest_prev >= 150:
        pressure_bid = highest_prev + 1.25
    elif highest_prev >= 120:
        pressure_bid = highest_prev + 1.75
    elif highest_prev >= 80:
        pressure_bid = max(65.0, avg_prev + 4.0)
    else:
        pressure_bid = max(38.0, avg_prev + 3.0)

    bid = base

    if supply >= 22 and danger == 0:
        bid = min(bid, 24.0)
    elif supply >= 20 and danger <= 1:
        bid = max(bid, 28.0)
    elif supply <= 17:
        bid = max(bid, pressure_bid)
    elif supply <= 19:
        bid = max(bid, 0.75 * pressure_bid)

    if urgent_opp_count >= 2 and supply <= 18:
        bid = max(bid, pressure_bid + 2.0)
    elif rich_opp_count >= 2 and supply <= 17:
        bid = max(bid, pressure_bid + 1.0)

    if danger >= 5:
        bid = max(bid, highest_prev + 2.5, 118.0)
    elif danger >= 3:
        bid = max(bid, highest_prev + 1.5, 88.0)
    elif danger >= 1:
        bid = max(bid, 52.0)

    if spendable < bid and danger == 0:
        bid = max(16.0, min(spendable + 10.0, 42.0))
    elif spendable < bid and danger <= 2:
        bid = min(budget, max(45.0, spendable + 18.0))

    if hp >= 8 and no_water_days == 0 and supply >= 21:
        bid = min(bid, 26.0)

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
        return min(budget, 20.0)

    yesterday_bids = []
    fixed_70_present = False
    desperate_opp = 0
    high_pressure = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = None
        if prev:
            pbid = prev.get('bid')
        if pbid is not None:
            yesterday_bids.append(float(pbid))
            if abs(float(pbid) - 70.0) < 1e-9:
                fixed_70_present = True
            if float(pbid) >= 90.0:
                high_pressure += 1
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            desperate_opp += 1

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

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

    pressure = 0
    if slots <= 1:
        pressure += 3
    elif slots == 2:
        pressure += 1
    pressure += min(desperate_opp, 2)
    if fixed_70_present:
        pressure += 1
    if high_pressure >= 2:
        pressure += 1

    target = 32.0
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev >= 100.0:
            target = 71.0 if urgency + pressure >= 4 else 28.0
        elif max_prev >= 70.0:
            target = 71.0 if urgency + pressure >= 3 else 35.0
        else:
            target = min(72.0, max_prev + 3.0)
    else:
        target = 40.0

    if slots >= 2 and urgency <= 1:
        target = min(target, 34.0)
    if slots <= 1 and (urgency >= 2 or pressure >= 4):
        target = max(target, 71.0)
    if hp <= 2 or no_water_days >= 2:
        target = max(target, 72.0)
    if hp <= 1:
        target = max(target, 90.0)

    remaining_days = max(1, 10 - int(day) + 1)
    reserve_floor = max(0.0, (remaining_days - 1) * 12.0)
    affordable = max(0.0, budget - reserve_floor)
    if urgency >= 3:
        affordable = budget

    bid = min(target, affordable if affordable > 0 else budget)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev_bids = []
    needy_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    if opp.get('budget', 0) >= bid:
                        strong_prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    total_players = len(alive) + 1
    expected_share = supply / float(total_players)
    scarcity = expected_share < WATER_REQ

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    strong_high = max(strong_prev_bids) if strong_prev_bids else highest_prev

    if hp <= 2 or no_water_days >= 2:
        bid = max(62.0, strong_high + 2.0)
    elif hp <= 4 or no_water_days >= 1:
        if scarcity:
            bid = max(54.0, avg_prev + 3.0)
        else:
            bid = max(34.0, avg_prev * 0.55)
    else:
        if scarcity:
            if supply <= 17:
                bid = max(46.0, min(strong_high + 1.5, 78.0))
            elif supply <= 20:
                bid = max(38.0, min(avg_prev * 0.72 + 2.0, 68.0))
            else:
                bid = max(30.0, min(avg_prev * 0.58 + 1.0, 58.0))
        else:
            bid = 18.0 if day < 8 else 24.0

    if needy_count >= 2 and scarcity:
        bid += 6.0
    elif needy_count >= 1 and scarcity:
        bid += 3.0

    rich_opponents = 0
    for opp in alive:
        if opp.get('budget', 0) > budget:
            rich_opponents += 1
    if rich_opponents >= 3 and hp >= 5 and no_water_days == 0:
        bid -= 4.0

    if day >= 8 and hp >= 5 and budget > 120:
        bid += 4.0

    bid = max(0.0, min(float(budget), bid))
    return float(round(bid, 2))
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    opp_pressures = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                pressure = float(bid)
                if opp.get('no_water_days', 0) >= 1:
                    pressure += 8.0
                if opp.get('hp', 10) <= 4:
                    pressure += 10.0
                if opp.get('budget', 0) < 40:
                    pressure -= 6.0
                opp_pressures.append(pressure)

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_pressure = max(opp_pressures) if opp_pressures else highest_prev

    scarcity = (float(MAX_SUPPLY) - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.45

    base = 20.0 + 18.0 * scarcity

    if urgency >= 1.4:
        bid = max(62.0, strongest_pressure + 2.5, base + 25.0)
    elif urgency >= 0.7:
        bid = max(45.0, highest_prev + 1.5, base + 12.0)
    else:
        if supply >= 22:
            bid = max(18.0, min(34.0, highest_prev * 0.55 + 4.0))
        elif supply >= 19:
            bid = max(26.0, min(46.0, highest_prev * 0.72 + 3.0))
        else:
            bid = max(34.0, min(58.0, highest_prev * 0.82 + 4.0))

    if day >= 8:
        bid += 6.0 * urgency + 4.0 * scarcity

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.92)
    else:
        reserve_target = max(0.0, (10 - day) * 18.0)
        if budget - bid < reserve_target and urgency < 1.0:
            bid = max(15.0, budget - reserve_target)

    if hp >= 7 and no_water == 0 and supply >= 23 and highest_prev >= 90:
        bid = min(bid, 22.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
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

    alive = []
    prev_bids = []
    desperate_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    desperate_prev.append(float(bid))

    if budget <= 0:
        return 0.0

    units = int(supply / WATER_REQ)
    if units < 0:
        units = 0

    if not alive:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    desperate_anchor = max(desperate_prev) if desperate_prev else highest_prev

    critical_me = hp <= 2 or no_water >= 1
    very_safe = hp >= 7 and no_water == 0

    if units >= len(alive) + 1:
        base = DAILY_SALARY * 0.18
        if critical_me:
            base = DAILY_SALARY * 0.4
        return float(min(budget, max(0.0, base)))

    if units >= len(alive):
        base = max(DAILY_SALARY * 0.22, highest_prev * 0.45)
        if critical_me:
            base = max(base, DAILY_SALARY * 0.55)
        return float(min(budget, base))

    if units == 0:
        if critical_me:
            return float(min(budget, DAILY_SALARY * 0.98))
        return float(min(budget, DAILY_SALARY * 0.08))

    if units == 1:
        if critical_me:
            target = max(DAILY_SALARY * 1.1, desperate_anchor + 6.0, highest_prev + 3.0)
            return float(min(budget, target))
        if very_safe:
            return float(min(budget, DAILY_SALARY * 0.12))
        target = max(DAILY_SALARY * 0.42, highest_prev * 0.55)
        return float(min(budget, target))

    pressure = highest_prev
    if len(alive) >= 3:
        pressure = max(pressure, desperate_anchor)

    if critical_me:
        target = max(DAILY_SALARY * 0.92, pressure + 2.5)
        return float(min(budget, target))

    if very_safe and pressure >= DAILY_SALARY * 1.4:
        return float(min(budget, DAILY_SALARY * 0.18))

    target = max(DAILY_SALARY * 0.48, pressure * 0.72)
    if pressure <= DAILY_SALARY * 0.5:
        target = max(target, pressure + 1.5)
    return float(min(budget, target))
"""
