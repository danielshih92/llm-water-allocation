# ============================================================
# Experiment: exp_040
# Agent: Alex
# Source: exp_040
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return max(0, min(budget, 52.0))
        if supply >= 22:
            return max(0, min(budget, 18.0))
        return max(0, min(budget, 28.0))

    prev_bids = []
    urgent_opp = 0
    weak_opp = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) < DAILY_SALARY * 0.75:
            weak_opp += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        err = prev.get('error')
        status = prev.get('status')
        if err or status == 'error':
            continue
        if bid is not None:
            prev_bids.append(float(bid))

    if hp <= 1:
        return max(0, min(budget, 68.0))
    if no_water >= 2:
        return max(0, min(budget, 67.0))
    if hp <= 2 and no_water >= 1:
        return max(0, min(budget, 64.0))

    base = 0.0
    if supply >= 23:
        base = 20.0
    elif supply >= 20:
        base = 28.0
    elif supply >= 17:
        base = 37.0
    else:
        base = 47.0

    if hp <= 3:
        base += 10.0
    if no_water >= 1:
        base += 8.0
    if urgent_opp > 0:
        base += 4.0 * urgent_opp
    if weak_opp == len(alive_opponents):
        base -= 5.0

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if highest_prev >= 60.0:
            if hp >= 4 and no_water == 0 and supply >= 20:
                base = min(base, 26.0)
            else:
                base = max(base, 61.0)
        elif highest_prev >= 45.0:
            base = max(base, highest_prev + 2.0)
        else:
            base = max(base, avg_prev + 1.5)
    else:
        if day <= 2 and supply >= 20:
            base -= 4.0

    if budget < 25:
        return max(0, min(budget, budget))

    bid = max(0.0, min(budget, base))
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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

    alive = {k: v for k, v in opponents_status.items() if v.get('alive')}
    if not alive:
        base = 18.0 if hp > 3 else 45.0
        return float(max(0.0, min(budget, base)))

    pressure_bids = []
    cindy_bid = None
    urgent_opp = 0
    rich_opp = 0

    for oid, opp in alive.items():
        prev = opp.get('previous_trace') or {}
        pbid = prev.get('bid')
        if pbid is not None:
            pressure_bids.append(float(pbid))
            if oid == 'Cindy':
                cindy_bid = float(pbid)
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 2:
            urgent_opp += 1
        if opp.get('budget', 0) >= 500:
            rich_opp += 1

    highest_prev = max(pressure_bids) if pressure_bids else 0.0
    anchor = cindy_bid if cindy_bid is not None else highest_prev

    scarce = supply <= 16.0
    medium_tight = supply <= 19.0
    danger = hp <= 2 or no_water >= 1
    very_danger = hp <= 1 or no_water >= 2

    if very_danger:
        bid = max(62.0, anchor + 3.0)
    elif danger:
        bid = max(52.0, anchor + 1.5)
    else:
        if scarce:
            bid = max(46.0, anchor + 1.0)
        elif medium_tight:
            bid = max(34.0, anchor - 4.0)
        else:
            bid = max(22.0, anchor - 10.0)

    if urgent_opp >= 2:
        bid += 4.0
    elif urgent_opp == 0 and hp >= 4 and supply >= 20.0:
        bid -= 4.0

    if rich_opp >= 2 and medium_tight:
        bid += 3.0

    if day >= 8 and hp >= 4 and not scarce:
        bid -= 3.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if hp > 2 and days_left > 0:
        reserve_floor = days_left * 8.0

    max_affordable = budget - reserve_floor
    if danger:
        max_affordable = budget
    max_affordable = max(0.0, max_affordable)

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
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
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return min(budget, 18.0)

    prev_bids = []
    cindy_prev = None
    bob_prev = None
    pressure = 0.0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > pressure:
                pressure = float(bid)
        if oid == 'Cindy' and bid is not None:
            cindy_prev = float(bid)
        if oid == 'Bob' and bid is not None:
            bob_prev = float(bid)

    competitors = 1
    for oid, opp in alive:
        req = opp.get('water_requirement', WATER_REQ)
        if supply < req:
            competitors += 1
        elif opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            competitors += 1

    if hp <= 2 or no_water >= 2:
        emergency = max(92.0, (bob_prev + 6.0) if bob_prev is not None else 92.0)
        if cindy_prev is not None:
            emergency = min(emergency, cindy_prev - 1.0)
        return max(0.0, min(budget, emergency))

    if supply >= 24:
        base = 24.0
    elif supply >= 21:
        base = 34.0
    elif supply >= 18:
        base = 46.0
    else:
        base = 58.0

    if competitors >= 3:
        base += 8.0
    elif competitors <= 1:
        base -= 6.0

    if bob_prev is not None:
        target_bob = bob_prev + 2.5
        if target_bob > base and target_bob <= 78.0:
            base = target_bob

    if cindy_prev is not None and cindy_prev >= 100.0 and hp >= 4 and no_water == 0:
        base = min(base, 52.0)

    if hp == 3 or no_water == 1:
        base = max(base, 68.0)

    if pressure >= 110.0 and hp >= 4 and no_water == 0:
        base = min(base, 45.0)

    if budget < 120.0:
        base = min(base, 55.0)
    if budget < 70.0:
        base = min(base, budget)

    if base < 0.0:
        base = 0.0
    return min(budget, float(base))
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
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(float(bid))
                    if bid >= 100:
                        aggressive_count += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = int(supply / WATER_REQ)
    scarce = units <= 1
    ample = units >= 2

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

    if scarce:
        urgency += 2
    if desperate_count >= 2:
        urgency += 1
    if day >= 8:
        urgency += 1

    if urgency >= 6:
        target = max(115.0, highest_prev + 3.0)
    elif urgency >= 4:
        target = max(88.0, highest_prev + 2.0 if highest_prev > 0 else 88.0)
    elif urgency >= 2:
        if ample:
            target = max(42.0, avg_prev * 0.55)
        else:
            target = max(62.0, highest_prev * 0.72 if highest_prev > 0 else 62.0)
    else:
        if ample:
            target = 24.0 if aggressive_count >= 2 else 31.0
        else:
            target = max(36.0, avg_prev * 0.4 if avg_prev > 0 else 36.0)

    if budget < target:
        if urgency >= 4:
            target = budget
        else:
            target = min(budget, max(12.0, budget * 0.55))

    if hp >= 8 and no_water_days == 0 and ample and aggressive_count >= 2:
        target = min(target, 26.0)

    return float(max(0.0, min(budget, round(target, 2))))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = {k: v for k, v in opponents_status.items() if v.get('alive')}
    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    prev_bids = []
    cindy_prev = None
    weak_opp_count = 0
    dangerous_count = 0

    for oid, opp in alive.items():
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            weak_opp_count += 1
        if opp.get('budget', 0) > 150:
            dangerous_count += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if oid == 'Cindy':
                cindy_prev = float(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    base = 16.0 + 18.0 * scarcity

    if supply >= 22:
        base -= 6.0
    elif supply <= 17:
        base += 10.0

    if hp <= 2 or no_water_days >= 2:
        emergency = max(62.0, highest_prev + 4.0)
        if cindy_prev is not None:
            emergency = max(emergency, min(110.0, cindy_prev + 2.5))
        return float(min(budget, emergency))

    if hp == 3 or no_water_days == 1:
        base += 16.0

    if highest_prev > 0:
        if highest_prev >= 120.0:
            if supply >= 21 and hp >= 4:
                base = min(base, 22.0)
            else:
                base = max(base, 52.0)
        elif highest_prev >= 80.0:
            if supply >= 20 and hp >= 4:
                base = min(base, 24.0)
            else:
                base = max(base, avg_prev * 0.55)
        else:
            base = max(base, highest_prev + 1.25)

    if cindy_prev is not None:
        if cindy_prev >= 130.0:
            if supply <= 17 or hp <= 3:
                base = max(base, 74.0)
            else:
                base = min(base, 26.0)
        elif cindy_prev >= 100.0:
            if supply <= 18:
                base = max(base, 58.0)

    if weak_opp_count >= 2 and supply >= 20 and hp >= 4:
        base -= 5.0

    if dangerous_count >= 2 and supply <= 18:
        base += 8.0

    if day >= 8:
        base += 6.0
    if day == 10:
        base += 8.0

    affordable = budget
    if budget < DAILY_SALARY:
        base = min(base, budget)
    else:
        reserve_factor = 0.55 if hp >= 4 else 0.8
        affordable = min(budget, max(28.0, budget * reserve_factor))

    bid = max(0.0, min(base, affordable))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        if opp.get('budget', 0) >= 300:
            rich_opp += 1

    prev_bids.sort()
    max_prev = prev_bids[-1] if prev_bids else 0.0
    med_prev = prev_bids[int(len(prev_bids) // 2)] if prev_bids else 0.0

    scarcity = 1.0
    if supply <= 16:
        scarcity = 1.25
    elif supply >= 23:
        scarcity = 0.8

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water >= 2:
        danger += 2
    elif no_water >= 1:
        danger += 1

    if danger >= 3:
        target = max(95.0, med_prev * 0.92, max_prev * 0.82)
        target *= scarcity
    elif danger >= 2:
        target = max(62.0, med_prev * 0.62)
        target *= scarcity
    else:
        target = 22.0 + 4.0 * no_water
        if max_prev > 120:
            target = min(target, 32.0)
        elif max_prev < 80:
            target = max(target, max_prev + 2.0)
        target *= scarcity

    if urgent_opp >= 2 and danger <= 1:
        target *= 0.85
    if rich_opp >= 2 and danger >= 2:
        target *= 1.08

    if day >= 8:
        target *= 1.08
    if hp >= 8 and no_water == 0 and supply >= 22:
        target *= 0.85

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 35.0
    max_affordable = max(0.0, budget - reserve_floor)
    if danger >= 3:
        max_affordable = budget

    bid = min(target, max_affordable if max_affordable > 0 else budget)
    bid = max(0.0, min(bid, budget))
    return float(round(bid, 2))
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

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 140:
                rich_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))
                status = prev.get('status')
                hp_after = prev.get('hp_after')
                if status == 'lost' or (hp_after is not None and hp_after <= 3):
                    desperate_count += 1

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 18)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0
    if supply_pressure > 1:
        supply_pressure = 1

    survival_urgent = hp <= 2 or no_water_days >= 2
    caution = hp <= 4 or no_water_days >= 1

    if survival_urgent:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 4)
        if supply <= 17:
            bid += 10
        return min(budget, bid)

    if caution:
        bid = max(0.72 * DAILY_SALARY, avg_prev * 0.9 + 3)
        if desperate_count >= 2:
            bid += 8
        if supply <= 17:
            bid += 6
        return min(budget, bid)

    base = 0.34 * DAILY_SALARY
    bid = base + 18 * supply_pressure

    if highest_prev >= 150:
        bid = min(bid, 0.42 * DAILY_SALARY)
    elif highest_prev >= 120:
        bid = min(bid + 2, 0.48 * DAILY_SALARY)
    else:
        bid = max(bid, avg_prev * 0.55 + 1)

    if desperate_count >= 2:
        bid += 5
    if rich_count >= 3 and supply <= 18:
        bid += 6

    if day >= 8 and hp >= 6:
        bid *= 0.9

    if budget < 90:
        bid = min(bid, 0.55 * DAILY_SALARY)

    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget
    return bid
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    strong_prev_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                b = float(bid)
                prev_bids.append(b)
                if opp.get('daily_salary', 0) >= DAILY_SALARY:
                    strong_prev_bids.append(b)

    if not alive_opponents:
        return min(budget, 18.0)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = hp <= 3 or no_water >= 2
    pressured = hp <= 5 or no_water >= 1

    top_prev = max(prev_bids) if prev_bids else 0.0
    strong_top = max(strong_prev_bids) if strong_prev_bids else top_prev

    if urgent:
        target = max(72.0, strong_top + 3.0, 78.0 + 30.0 * scarcity)
    elif pressured:
        if strong_top >= 150.0:
            target = 34.0 + 10.0 * scarcity
        else:
            target = max(42.0 + 18.0 * scarcity, strong_top + 2.0)
    else:
        if supply >= 22:
            target = 16.0
        elif supply >= 19:
            target = 22.0 + 6.0 * scarcity
        else:
            if strong_top >= 150.0:
                target = 26.0 + 12.0 * scarcity
            else:
                target = max(30.0 + 14.0 * scarcity, strong_top + 1.5)

    if day >= 8 and hp >= 6 and no_water == 0:
        target *= 0.9

    max_safe = budget
    if not urgent:
        reserve = max(0.0, (10 - day) * 8.0)
        max_safe = max(0.0, budget - reserve)
        if max_safe <= 0:
            max_safe = min(budget, 20.0 + 10.0 * scarcity)

    bid = min(target, budget, max_safe if not urgent else budget)
    if urgent and bid < min(budget, 65.0):
        bid = min(budget, 65.0)

    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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

    alive_opps = []
    prev_bids = []
    aggressive_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 60:
                    aggressive_bids.append(bid)

    if not alive_opps:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, min(budget, 42.0))
        return max(0.0, min(budget, 18.0))

    high_pressure = max(prev_bids) if prev_bids else 0.0
    avg_pressure = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0
    alive_count = len(alive_opps)

    scarcity = supply <= 17
    ample = supply >= 22
    urgent = hp <= 2 or no_water_days >= 1
    very_urgent = hp <= 1 or no_water_days >= 2

    target = 0.0

    if very_urgent:
        target = max(68.0, high_pressure + 3.0)
    elif urgent:
        if scarcity:
            target = max(63.0, high_pressure + 2.0)
        else:
            target = max(52.0, avg_pressure + 1.5)
    else:
        if scarcity:
            if aggressive_bids:
                target = max(58.0, high_pressure + 1.25)
            else:
                target = max(46.0, avg_pressure + 2.0)
        elif ample:
            target = max(22.0, min(48.0, avg_pressure * 0.72 + 4.0))
        else:
            target = max(34.0, min(56.0, avg_pressure * 0.9 + 2.0))

    if alive_count >= 3 and not urgent:
        target += 3.0
    elif alive_count == 1 and not urgent:
        target -= 4.0

    if day >= 8:
        target += 4.0
    if budget < 140:
        target = min(target, 0.55 * DAILY_SALARY)
    if budget < 80:
        target = min(target, 24.0)

    if hp >= 8 and no_water_days == 0 and ample and high_pressure >= 80:
        target = min(target, 26.0)

    bid = max(0.0, min(float(budget), float(target)))
    return bid
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    players_alive = 1 + len(alive)
    total_demand_units = WATER_REQ * players_alive
    slack = supply - total_demand_units

    prev_bids = []
    rich_threat = 0.0
    desperate_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('budget', 0) > budget:
            rich_threat = max(rich_threat, opp.get('budget', 0))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    if not alive:
        return float(min(budget, 8.0))

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

    pressure = 0
    if supply <= 16:
        pressure += 3
    elif supply <= 18:
        pressure += 2
    elif supply <= 20:
        pressure += 1
    if slack < 0:
        pressure += 2
    elif slack == 0:
        pressure += 1
    if highest_prev >= 120:
        pressure += 2
    elif highest_prev >= 80:
        pressure += 1
    if desperate_count >= 2:
        pressure += 1

    if urgency == 0 and pressure <= 1 and supply >= 22:
        bid = 1.0
    elif urgency == 0 and pressure <= 2:
        bid = 8.0 + max(0.0, avg_prev * 0.12)
    elif urgency <= 2 and pressure <= 2:
        bid = max(18.0, min(32.0, avg_prev * 0.45 + 6.0))
    elif urgency <= 3 and pressure <= 4:
        bid = max(32.0, min(58.0, highest_prev * 0.55 + 6.0))
    else:
        bid = max(55.0, min(95.0, highest_prev * 0.72 + 8.0))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 82.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, 58.0)

    if supply >= 24 and urgency == 0:
        bid = min(bid, 6.0)
    elif supply >= 22 and urgency <= 1:
        bid = min(bid, 14.0)

    if rich_threat > budget * 1.8 and urgency == 0:
        bid = min(bid, 20.0)

    max_safe = budget
    if day <= 3 and hp > 4:
        max_safe = min(max_safe, budget * 0.28 + 6.0)
    elif day <= 6 and hp > 3:
        max_safe = min(max_safe, budget * 0.4 + 8.0)

    bid = min(bid, max_safe)
    if bid < 0:
        bid = 0.0
    return float(min(budget, round(bid, 2)))
"""
