# ============================================================
# Experiment: exp_111
# Agent: Alex
# Source: exp_111
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    total_players = 1 + len(alive)
    units = int(supply // WATER_REQ)
    scarcity = total_players - units

    prev_bids = []
    desperate_opp = False
    rich_pressure = False
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 2:
            desperate_opp = True
        if opp.get('budget', 0) > budget * 1.2:
            rich_pressure = True

    if hp <= 2 or no_water >= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4 or no_water == 1:
        base = DAILY_SALARY * 0.72
    else:
        if scarcity <= 0:
            base = DAILY_SALARY * 0.22
        elif scarcity == 1:
            base = DAILY_SALARY * 0.42
        elif scarcity == 2:
            base = DAILY_SALARY * 0.58
        else:
            base = DAILY_SALARY * 0.72

    if prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev >= DAILY_SALARY * 0.9:
            if hp > 4 and no_water == 0:
                base = min(base, DAILY_SALARY * 0.28)
            else:
                base = max(base, DAILY_SALARY * 0.88)
        elif highest_prev >= DAILY_SALARY * 0.6:
            base = max(base, min(DAILY_SALARY * 0.78, highest_prev + 2))
        else:
            base = max(base, highest_prev + 1)

    if desperate_opp and hp > 4 and no_water == 0:
        base = min(base, DAILY_SALARY * 0.35)
    if rich_pressure and scarcity > 0 and (hp <= 4 or no_water >= 1):
        base = max(base, DAILY_SALARY * 0.8)

    days_left = max(1, 10 - day_context['day'] + 1)
    soft_cap = budget / days_left + DAILY_SALARY * 0.15
    if hp > 4 and no_water == 0:
        bid = min(base, soft_cap)
    else:
        bid = base

    bid = max(0, min(budget, bid))
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 56.0))
        return float(min(budget, 18.0))

    prev_bids = []
    aggressive_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 90:
                aggressive_bids.append(float(bid))
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 500:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    elif hp <= 6:
        urgency += 1

    if no_water_days >= 1:
        urgency += 2

    if tight_supply:
        urgency += 2
    elif medium_supply:
        urgency += 1

    if desperate_count >= 1:
        urgency += 1
    if rich_count >= 2 and highest_prev >= 90:
        urgency += 1

    if urgency >= 6:
        target = max(98.0, highest_prev + 1.5)
    elif urgency >= 4:
        target = max(78.0, min(96.0, highest_prev + 1.0))
    elif urgency >= 2:
        if highest_prev >= 95:
            target = 52.0
        else:
            target = max(46.0, avg_prev * 0.7)
    else:
        if highest_prev >= 90:
            target = 22.0
        else:
            target = 35.0

    if day >= 8:
        target += 6.0
    if hp <= 2:
        target += 4.0
    if no_water_days >= 1:
        target += 6.0

    max_safe = budget
    if day < 9:
        reserve_days = 10 - day
        reserve_amount = reserve_days * 8.0
        max_safe = max(0.0, budget - reserve_amount)
        if urgency >= 4:
            max_safe = budget

    bid = min(target, budget)
    if max_safe > 0:
        bid = min(bid, max_safe) if urgency < 4 else min(target, budget)

    if hp <= 2 or no_water_days >= 1:
        bid = max(bid, min(budget, 60.0))

    if bid < 0:
        bid = 0.0
    return float(round(min(bid, budget), 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    threat_bids = []
    urgent_opp = False

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                mult = 1.0
                if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                    mult = 1.08
                    urgent_opp = True
                if opp.get('budget', 0) < DAILY_SALARY * 1.2:
                    mult *= 0.92
                threat_bids.append(float(bid) * mult)

    if not alive:
        return float(min(budget, 18.0))

    alive_count = len(alive)
    plentiful = supply >= 22
    tight = supply <= 17
    very_tight = supply <= 16

    if threat_bids:
        est_top = max(threat_bids)
        est_avg = sum(prev_bids) / max(1, len(prev_bids))
    else:
        est_top = DAILY_SALARY * 0.65
        est_avg = DAILY_SALARY * 0.55

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
    if very_tight:
        danger += 2
    elif tight:
        danger += 1
    if day >= 8:
        danger += 1

    if plentiful and danger <= 1:
        base = 16.0 + 1.5 * alive_count
    elif plentiful:
        base = 24.0 + 2.0 * danger
    elif tight:
        base = max(32.0 + 4.0 * danger, est_avg * 0.72)
    else:
        base = max(26.0 + 3.0 * danger, est_avg * 0.62)

    if danger >= 5:
        target = max(base, est_top + 2.5)
    elif danger >= 3:
        target = max(base, est_top * 0.9 + 1.5)
    else:
        target = base

    if not urgent_opp and plentiful and hp > 4:
        target = min(target, est_top * 0.72 if threat_bids else target)

    if day == 1 and hp >= 8 and supply >= 20:
        target = min(target, 24.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 1.2
    if hp <= 3 or no_water >= 1:
        reserve_floor = DAILY_SALARY * 0.4

    cap = budget - reserve_floor
    if cap < 0:
        cap = budget * 0.6
    if hp <= 2 or no_water >= 2:
        cap = budget

    bid = min(budget, max(0.0, min(target, cap)))

    if bid < 1.0 and budget >= 1.0:
        bid = 1.0

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
        base = DAILY_SALARY * 0.28
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    opp_pressure = 0.0
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0.0)
            prev_bids.append(bid)
            if bid > opp_pressure:
                opp_pressure = bid

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22

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

    if supply_tight:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1

    if urgency >= 5:
        target = max(opp_pressure + 2.5, DAILY_SALARY * 0.96)
    elif urgency >= 3:
        target = max(avg_prev + 1.5, DAILY_SALARY * 0.78)
    elif urgency >= 2:
        if supply_loose:
            target = DAILY_SALARY * 0.42
        else:
            target = max(DAILY_SALARY * 0.55, avg_prev * 0.72)
    else:
        if supply_loose:
            target = DAILY_SALARY * 0.26
        else:
            target = DAILY_SALARY * 0.38

    if opp_pressure >= DAILY_SALARY * 1.35 and urgency <= 2:
        target = min(target, DAILY_SALARY * 0.34)

    if rich_count >= 3 and urgency <= 1:
        target = min(target, DAILY_SALARY * 0.3)

    if day >= 8:
        target *= 1.08

    reserve_floor = 0.0
    days_left = 10 - day
    if days_left > 0 and urgency <= 2:
        reserve_floor = min(budget, days_left * DAILY_SALARY * 0.12)

    bid = min(budget - reserve_floor, target)
    if urgency >= 4:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    credible_bids = []
    urgent_count = 0
    rich_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_count += 1
            if opp.get('budget', 0) >= 300:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if b <= opp.get('budget', 0) + opp.get('daily_salary', 0):
                    credible_bids.append(b)

    if not alive:
        return min(budget, 18.0)

    max_prev = max(prev_bids) if prev_bids else 0.0
    max_credible = max(credible_bids) if credible_bids else max_prev
    avg_credible = sum(credible_bids) / len(credible_bids) if credible_bids else 60.0

    scarcity = 1.0 - ((float(supply) - 15.0) / 10.0)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    need = 0
    if hp <= 2:
        need = 3
    elif hp <= 4 or no_water_days >= 1:
        need = 2
    elif hp <= 6:
        need = 1

    if need == 3:
        target = max(92.0, max_credible + 3.0, avg_credible + 8.0)
    elif need == 2:
        target = max(78.0, avg_credible + 3.0, max_credible * 0.92)
    else:
        if supply >= 22:
            target = max(28.0, avg_credible * 0.58)
        elif supply >= 19:
            target = max(42.0, avg_credible * 0.72)
        else:
            target = max(55.0, avg_credible * 0.84)

    target += scarcity * 10.0
    target += urgent_count * 1.5
    if rich_count >= 2 and supply < 19:
        target += 4.0
    if day >= 8 and hp >= 7:
        target -= 6.0

    reserve = 0.0
    if hp <= 2:
        reserve = 0.0
    elif hp <= 4:
        reserve = 20.0
    else:
        reserve = 35.0

    affordable = max(0.0, budget - reserve)
    if need >= 2 and affordable < 25.0:
        affordable = budget

    bid = min(target, affordable)
    if bid < 0:
        bid = 0.0
    if budget <= 0:
        return 0.0
    if need >= 2 and bid < 15.0:
        bid = min(budget, 15.0)
    return float(min(budget, round(bid, 2)))
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
    yesterday_bids = []
    rich_pressure = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > 500:
                rich_pressure += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(yesterday_bids) if yesterday_bids else 0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        bid = 112.0 if tight_supply else 96.0
        return min(budget, bid)

    if hp <= 4 or no_water_days >= 1:
        if highest_prev >= 100:
            bid = 92.0 if tight_supply else 82.0
        else:
            bid = max(68.0, highest_prev + 3.0)
        return min(budget, bid)

    if tight_supply:
        if rich_pressure >= 2:
            bid = 34.0
        elif desperate_count >= 2:
            bid = max(40.0, avg_prev * 0.75)
        else:
            bid = max(28.0, min(52.0, highest_prev * 0.45 + 8.0))
    elif loose_supply:
        bid = 12.0 if hp >= 7 else 20.0
    else:
        if highest_prev >= 100:
            bid = 18.0
        elif highest_prev >= 70:
            bid = 24.0
        else:
            bid = max(16.0, min(36.0, avg_prev * 0.7))

    if day >= 8 and hp >= 6:
        bid *= 0.85

    if budget < 120:
        bid = min(bid, 0.45 * budget)
    elif budget < 250:
        bid = min(bid, 0.6 * budget)

    if bid < 0:
        bid = 0
    return min(budget, float(bid))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    yesterday_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 140:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 42.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.45
    if day >= 8:
        urgency += 0.2

    pressure = 0.0
    if highest_prev >= 180:
        pressure = 1.0
    elif highest_prev >= 130:
        pressure = 0.75
    elif highest_prev >= 80:
        pressure = 0.45
    elif highest_prev > 0:
        pressure = 0.2

    base = 20.0 + 18.0 * scarcity + 8.0 * min(len(alive_opponents), 3)

    if urgency >= 1.4:
        bid = max(base + 35.0, highest_prev * 0.72 + 6.0, 78.0 + 18.0 * scarcity)
    elif urgency >= 0.7:
        bid = max(base + 12.0, avg_prev * 0.55 + 4.0, 48.0 + 14.0 * scarcity)
    else:
        if pressure >= 0.75 and hp > 4 and no_water_days == 0:
            bid = 16.0 + 10.0 * scarcity
        elif pressure >= 0.45:
            bid = max(28.0 + 10.0 * scarcity, min(highest_prev + 2.0, 72.0))
        else:
            bid = base

    if desperate_count >= 2:
        bid += 10.0
    elif desperate_count == 0 and rich_count >= 2 and urgency < 0.7:
        bid -= 6.0

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.6

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 1.4:
        max_affordable = budget
    elif max_affordable <= 0:
        max_affordable = min(budget, 25.0 if hp > 3 else 55.0)

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 85.0 + 20.0 * scarcity))

    return float(round(bid, 2))
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

    alive = {}
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive[agent_id] = opp

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, bid))

    prev_bids = []
    david_bid = None
    cindy_bid = None
    urgent_opp = 0
    rich_opp = 0

    for agent_id, opp in alive.items():
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = prev.get('bid', 0)
            prev_bids.append(b)
            if agent_id == 'David':
                david_bid = b
            if agent_id == 'Cindy':
                cindy_bid = b

    highest_prev = max(prev_bids) if prev_bids else 0.0
    effective_prev = david_bid if david_bid is not None else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    life_urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        base = DAILY_SALARY * (1.15 + 0.25 * scarcity)
    elif life_urgent:
        base = DAILY_SALARY * (0.92 + 0.18 * scarcity)
    else:
        base = DAILY_SALARY * (0.42 + 0.18 * scarcity)

    if effective_prev >= 120:
        if life_urgent:
            target = max(base, DAILY_SALARY * 0.95)
        else:
            target = min(base, DAILY_SALARY * 0.38)
    elif effective_prev >= 85:
        if life_urgent:
            target = max(base, effective_prev + 3.0)
        else:
            target = max(base, effective_prev * 0.72)
    elif effective_prev >= 45:
        target = max(base, effective_prev + (2.0 if life_urgent else 1.0))
    elif effective_prev > 0:
        target = max(base, effective_prev + 1.5)
    else:
        target = base

    if cindy_bid is not None and cindy_bid >= 140 and not life_urgent:
        target = min(target, DAILY_SALARY * 0.4)

    if urgent_opp >= 2 and life_urgent:
        target += 6.0
    elif urgent_opp == 0 and not life_urgent:
        target -= 3.0

    if rich_opp >= 2 and life_urgent:
        target += 4.0

    if day >= 8 and budget > DAILY_SALARY * (11 - day):
        target += 5.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if not life_urgent and days_left > 0:
        reserve_floor = min(budget * 0.5, days_left * DAILY_SALARY * 0.22)

    max_affordable = max(0.0, budget - reserve_floor)
    if life_urgent:
        max_affordable = budget

    bid = min(target, max_affordable)
    if critical:
        bid = min(max(bid, DAILY_SALARY * 0.95), budget)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
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

    alive = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0:
                    dangerous_prev.append(float(bid))

    if not alive:
        return max(0.0, min(float(budget), DAILY_SALARY * 0.35))

    units = int(supply // WATER_REQ)
    tight = units <= 1

    bob_like = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None and 45 <= float(bid) <= 80:
            bob_like.append(float(bid))

    if bob_like:
        target_competitor = max(bob_like)
    elif dangerous_prev:
        target_competitor = max(dangerous_prev)
    elif prev_bids:
        target_competitor = max(prev_bids)
    else:
        target_competitor = DAILY_SALARY * 0.55

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

    if tight:
        urgency += 2

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        bid = max(DAILY_SALARY * 0.95, target_competitor + 8.0)
    elif urgency >= 4:
        bid = max(DAILY_SALARY * 0.82, target_competitor + 3.0)
    elif urgency >= 2:
        if tight:
            bid = max(DAILY_SALARY * 0.72, target_competitor + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.58, target_competitor * 0.92)
    else:
        if tight:
            bid = max(DAILY_SALARY * 0.62, min(target_competitor + 1.0, DAILY_SALARY * 0.9))
        else:
            bid = DAILY_SALARY * 0.42

    if budget < DAILY_SALARY * 0.6:
        bid = min(bid, budget * 0.9)

    if hp > 6 and no_water_days == 0 and not tight:
        bid = min(bid, DAILY_SALARY * 0.48)

    return max(0.0, min(float(budget), float(bid)))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water_days >= 1:
            bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, bid))

    prev_bids = []
    prev_high = 0.0
    eric_like_high = 0.0
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if float(opp.get('budget', 0.0)) >= 120:
            rich_count += 1
        if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0)) <= 3:
            desperate_count += 1
        prev = opp.get('previous_trace') or {}
        bidv = prev.get('bid')
        if bidv is not None:
            bidv = float(bidv)
            prev_bids.append(bidv)
            if bidv > prev_high:
                prev_high = bidv
            if bidv > eric_like_high and bidv >= 100:
                eric_like_high = bidv

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

    if prev_bids:
        ref_bid = prev_high
    else:
        ref_bid = DAILY_SALARY * 0.55

    if urgency >= 3:
        target = max(DAILY_SALARY * 1.1, ref_bid + 6.0)
        if scarcity >= 1:
            target = max(target, DAILY_SALARY * 1.35)
    elif urgency == 2:
        target = max(DAILY_SALARY * 0.82, min(ref_bid + 2.5, DAILY_SALARY * 1.05))
        if scarcity == 2:
            target = max(target, DAILY_SALARY * 0.98)
    elif urgency == 1:
        if prev_high >= 120 and scarcity == 0:
            target = DAILY_SALARY * 0.34
        else:
            target = max(DAILY_SALARY * 0.48, min(ref_bid * 0.72, DAILY_SALARY * 0.8))
            if scarcity >= 1:
                target = max(target, DAILY_SALARY * 0.62)
    else:
        if prev_high >= 120:
            target = DAILY_SALARY * 0.22
        elif prev_high >= 80:
            target = DAILY_SALARY * 0.32
        else:
            target = DAILY_SALARY * 0.44
        if scarcity == 2 and desperate_count >= 1:
            target = max(target, DAILY_SALARY * 0.58)
        elif scarcity == 1 and desperate_count >= 2:
            target = max(target, DAILY_SALARY * 0.52)

    if day >= 8:
        target = max(target, DAILY_SALARY * 0.6)
        if urgency >= 2:
            target = max(target, DAILY_SALARY * 0.95)

    if budget < DAILY_SALARY * 0.8:
        target = min(target, budget)
    elif budget < DAILY_SALARY * 1.5 and urgency == 0:
        target = min(target, DAILY_SALARY * 0.45)

    if rich_count == 1 and prev_high >= 120 and urgency == 0 and scarcity == 0:
        target = min(target, DAILY_SALARY * 0.2)

    bid = max(0.0, min(budget, target))
    return float(bid)
"""
