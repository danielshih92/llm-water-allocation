# ============================================================
# Experiment: exp_003
# Agent: Alex
# Source: exp_003
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

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    if not alive:
        base = 0.35 * DAILY_SALARY
        if hp <= 2 or no_water >= 1:
            base = 0.75 * DAILY_SALARY
        return max(0, min(budget, base))

    prev_bids = []
    stressed_opp_bid = None
    max_prev = 0
    min_prev = None
    error_count = 0
    high_need_count = 0

    for opp in alive:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            high_need_count += 1
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('error'):
            error_count += 1
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
            if bid > max_prev:
                max_prev = bid
            if min_prev is None or bid < min_prev:
                min_prev = bid
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                if stressed_opp_bid is None or bid > stressed_opp_bid:
                    stressed_opp_bid = bid

    scarcity = 1.0 - ((supply - 15.0) / 10.0)
    if scarcity < 0:
        scarcity = 0
    if scarcity > 1:
        scarcity = 1

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    if no_water >= 1:
        urgency += 0.25
    if no_water >= 2:
        urgency += 0.2

    pressure = 0.25 + 0.35 * scarcity + urgency
    if high_need_count >= 2:
        pressure += 0.08
    if error_count > 0:
        pressure -= 0.05

    if pressure < 0.15:
        pressure = 0.15
    if pressure > 1.15:
        pressure = 1.15

    bid = DAILY_SALARY * pressure

    if prev_bids:
        if hp <= 2 or no_water >= 1:
            target = max_prev + 1.5
            if stressed_opp_bid is not None:
                target = max(target, stressed_opp_bid + 1.5)
            bid = max(bid, target)
        else:
            if max_prev >= 0.9 * DAILY_SALARY and scarcity > 0.5:
                bid = min(bid, 0.32 * DAILY_SALARY)
            elif min_prev is not None and scarcity < 0.35:
                bid = max(bid, min_prev + 0.75)
            else:
                bid = max(bid, max_prev * 0.78)
    else:
        if hp <= 2 or no_water >= 1:
            bid = max(bid, 0.82 * DAILY_SALARY)
        elif scarcity < 0.25:
            bid = min(bid, 0.42 * DAILY_SALARY)

    remaining_days = 10 - day
    reserve = 0
    if remaining_days > 0:
        reserve = remaining_days * 0.18 * DAILY_SALARY
    affordable = budget - reserve
    if affordable < 0:
        affordable = budget * 0.5

    if hp <= 2 or no_water >= 1:
        affordable = budget

    bid = min(bid, affordable, budget)
    if bid < 0:
        bid = 0

    if budget < 0.35 * DAILY_SALARY and not (hp <= 2 or no_water >= 1):
        bid = min(bid, budget)

    return max(0, bid)
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    sane_prev_bids = []
    urgent_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) <= DAILY_SALARY * 1.2:
                    sane_prev_bids.append(float(bid))

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    high_supply = supply >= 22
    low_supply = supply <= 17

    emergency = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_sane = max(sane_prev_bids) if sane_prev_bids else 0.0

    if emergency:
        target = DAILY_SALARY * 0.95
        if highest_sane > 0:
            target = max(target, highest_sane + 2.0)
        return float(min(budget, target))

    if high_supply and hp >= 6 and no_water_days == 0:
        if highest_sane >= DAILY_SALARY * 0.85:
            return float(min(budget, DAILY_SALARY * 0.18))
        return float(min(budget, DAILY_SALARY * 0.28))

    if low_supply:
        if pressured:
            target = max(DAILY_SALARY * 0.72, highest_sane + 1.5 if highest_sane > 0 else DAILY_SALARY * 0.72)
        else:
            if highest_prev > DAILY_SALARY * 1.5:
                target = DAILY_SALARY * 0.35
            else:
                target = max(DAILY_SALARY * 0.52, highest_sane + 1.0 if highest_sane > 0 else DAILY_SALARY * 0.52)
        if urgent_opponents >= 2:
            target += 4.0
        return float(min(budget, target))

    target = DAILY_SALARY * 0.42
    if pressured:
        target = DAILY_SALARY * 0.62
    if highest_sane > 0:
        if highest_sane >= DAILY_SALARY * 0.85 and not pressured:
            target = min(target, DAILY_SALARY * 0.34)
        else:
            target = max(target, highest_sane + 1.0)
    if urgent_opponents >= 2 and pressured:
        target += 3.0

    if day >= 8 and hp >= 5 and no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.38)

    return float(min(budget, max(0.0, target)))
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
        safe_bid = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            safe_bid = DAILY_SALARY * 0.75
        return float(min(budget, safe_bid))

    prev_bids = []
    high_threat = 0
    cindy_alive = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 85:
                high_threat += 1
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13 and opp.get('budget', 0) > 500:
            prev2 = opp.get('previous_trace', {})
            if prev2.get('bid') is not None and prev2.get('bid') >= 80:
                cindy_alive = True

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 2
    elif hp <= 6:
        urgency += 1

    if no_water_days >= 2:
        urgency += 3
    elif no_water_days == 1:
        urgency += 1

    abundance = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if abundance >= 0.8:
        urgency += 1

    if urgency >= 5:
        bid = max(88.0, highest_prev + 1.0)
    elif urgency >= 3:
        if supply >= 22:
            bid = max(72.0, avg_prev + 1.5)
        else:
            bid = max(78.0, highest_prev * 0.98)
    else:
        if cindy_alive and supply <= 18:
            bid = 8.0
        elif supply >= 23:
            bid = 61.0
        elif supply >= 20:
            bid = 36.0
        else:
            bid = 12.0

    if day >= 8 and hp > 5 and no_water_days == 0 and budget < 120:
        bid = min(bid, 25.0)

    if budget < 40:
        if urgency >= 4:
            bid = budget
        else:
            bid = min(bid, max(0.0, budget * 0.45))

    bid = max(0.0, min(float(budget), float(bid)))
    return float(bid)
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        safe_bid = DAILY_SALARY * 0.25
        if hp <= 2 or no_water_days >= 1:
            safe_bid = DAILY_SALARY * 0.6
        return float(min(budget, safe_bid))

    prev_bids = []
    urgent_opponents = 0
    rich_live = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 200:
            rich_live += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))
    tightness = 1.0 - scarcity

    danger = 0
    if hp <= 2:
        danger += 2
    elif hp <= 4:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1

    base = DAILY_SALARY * (0.34 + 0.22 * tightness)

    if highest_prev > 0:
        target = max(base, avg_prev * 0.72, highest_prev * 0.62)
    else:
        target = base

    if urgent_opponents >= 2:
        target += 8
    elif urgent_opponents == 1:
        target += 4

    if rich_live >= 2 and tightness > 0.5:
        target += 6

    if danger >= 3:
        target = max(target, highest_prev + 2.0, DAILY_SALARY * 0.95)
    elif danger == 2:
        target = max(target, highest_prev * 0.82, DAILY_SALARY * 0.78)
    elif danger == 1:
        target = max(target, highest_prev * 0.7, DAILY_SALARY * 0.62)

    if supply >= 23:
        target *= 0.82
    elif supply <= 17:
        target *= 1.12

    if day >= 8 and hp > 5 and no_water_days == 0:
        target *= 0.92

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 1.2
    max_affordable = max(0.0, budget - reserve)
    if danger >= 2:
        max_affordable = budget

    bid = min(target, max_affordable if max_affordable > 0 else budget)
    bid = max(0.0, min(budget, bid))
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    alive = {}
    for aid, opp in opponents_status.items():
        if opp.get('alive'):
            alive[aid] = opp

    if not alive:
        return float(min(budget, 18.0))

    threat_bid = 0.0
    threat_count = 0
    rich_threats = 0
    for aid, opp in alive.items():
        prev = opp.get('previous_trace', {})
        obudget = opp.get('budget', 0)
        ohp = opp.get('hp', 0)
        ono = opp.get('no_water_days', 0)
        req = opp.get('water_requirement', WATER_REQ)

        est = 0.0
        if prev and prev.get('bid') is not None:
            est = float(prev.get('bid', 0.0))
            if prev.get('status') not in ('ok', 'alive', 'won', 'lost', None):
                est = min(est, DAILY_SALARY * 0.4)
        else:
            est = DAILY_SALARY * 0.45

        if obudget <= 0:
            est = 0.0
        else:
            if ono >= 2 or ohp <= 2:
                est = max(est, DAILY_SALARY * 0.9)
            elif ono >= 1 or ohp <= 4:
                est = max(est, DAILY_SALARY * 0.7)

            if obudget < est:
                est = float(obudget)

        if est > 0:
            threat_count += 1
        if obudget >= DAILY_SALARY * 2:
            rich_threats += 1
        if est > threat_bid:
            threat_bid = est

    units = supply / float(WATER_REQ)
    tight = units < (1.0 + 0.15 * max(0, threat_count - 1))
    ample = units >= (1.5 + 0.2 * max(0, threat_count - 1))

    urgency = 0
    if hp <= 2 or no_water >= 2:
        urgency = 3
    elif hp <= 4 or no_water >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency == 3:
        bid = max(DAILY_SALARY * 0.95, threat_bid + 3.0)
    elif urgency == 2:
        bid = max(DAILY_SALARY * 0.78, threat_bid + 2.0)
    else:
        if threat_count <= 1:
            if ample:
                bid = max(12.0, min(DAILY_SALARY * 0.38, threat_bid * 0.72))
            elif tight:
                bid = max(DAILY_SALARY * 0.52, threat_bid + 1.0)
            else:
                bid = max(DAILY_SALARY * 0.42, threat_bid * 0.82)
        else:
            if ample:
                bid = max(18.0, min(DAILY_SALARY * 0.48, threat_bid * 0.78))
            elif tight:
                bid = max(DAILY_SALARY * 0.7, threat_bid + 2.5)
            else:
                bid = max(DAILY_SALARY * 0.58, threat_bid + 1.0)

    if rich_threats == 0 and urgency == 0:
        bid = min(bid, DAILY_SALARY * 0.4)

    if day >= 8 and hp > 4 and no_water == 0:
        bid = min(bid, DAILY_SALARY * 0.5)

    reserve = 0.0
    if urgency == 0:
        reserve = DAILY_SALARY * 1.2
    elif urgency == 1:
        reserve = DAILY_SALARY * 0.8
    elif urgency == 2:
        reserve = DAILY_SALARY * 0.3

    max_affordable = budget - reserve
    if max_affordable <= 0:
        max_affordable = budget * 0.6

    bid = min(bid, budget, max_affordable)

    if urgency >= 2 and bid < min(budget, DAILY_SALARY * 0.72):
        bid = min(budget, DAILY_SALARY * 0.72)

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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_pressure = 0
    urgent_opponents = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 120:
                    rich_pressure += 1
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                urgent_opponents += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply - WATER_REQ) / float(MAX_SUPPLY - WATER_REQ)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0
    if hp <= 2:
        danger += 2
    elif hp <= 4:
        danger += 1
    if no_water_days >= 2:
        danger += 3
    elif no_water_days >= 1:
        danger += 1
    if supply <= 17:
        danger += 1

    if danger >= 4:
        bid = 92.0
        if highest_prev > 0 and highest_prev < 110:
            bid = max(bid, highest_prev + 3.0)
        return float(min(budget, bid))

    if danger >= 2:
        bid = 48.0
        if highest_prev <= 95 and highest_prev > 0:
            bid = max(bid, highest_prev + 2.0)
        if rich_pressure >= 2:
            bid -= 6.0
        if supply <= 17:
            bid += 8.0
        return float(min(budget, max(20.0, bid)))

    base = 24.0 + (1.0 - scarcity) * 10.0
    if avg_prev > 0 and avg_prev < 80:
        base = max(base, avg_prev + 1.5)
    if highest_prev >= 120:
        base = min(base, 34.0)
    if rich_pressure >= 2:
        base -= 4.0
    if urgent_opponents >= 2:
        base += 5.0
    if day >= 8 and hp >= 6:
        base -= 3.0

    reserve_target = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    affordable = budget - reserve_target
    if affordable < 8.0:
        affordable = min(budget, 8.0)

    bid = min(base, affordable)
    bid = max(6.0, bid)
    return float(min(budget, bid))
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

    day = day_context['day']
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    danger_bids = []
    rich_count = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev['bid'])
                prev_bids.append(b)
                if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                    danger_bids.append(b)

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    danger_prev = max(danger_bids) if danger_bids else highest_prev

    severe_need = hp <= 2 or no_water >= 2
    urgent_need = hp <= 4 or no_water >= 1
    tight_supply = supply <= 17.0
    loose_supply = supply >= 22.0

    remaining_days = max(0, 10 - int(day) + 1)
    reserve_target = max(0.0, remaining_days * 18.0)
    spendable = max(0.0, budget - reserve_target)

    if severe_need:
        bid = max(68.0, danger_prev + 4.0, highest_prev + 2.0)
    elif urgent_need and tight_supply:
        bid = max(58.0, danger_prev + 2.5, avg_prev + 3.0)
    elif tight_supply:
        bid = max(32.0, min(62.0, highest_prev + 1.5))
    elif loose_supply:
        bid = 12.0 if hp >= 7 and no_water == 0 else 22.0
    else:
        bid = max(20.0, min(48.0, avg_prev * 0.55 + 6.0))

    if rich_count >= 2 and not urgent_need:
        bid -= 4.0
    if desperate_count >= 2 and not severe_need:
        bid += 5.0
    if budget < DAILY_SALARY:
        bid = min(bid, max(12.0, budget * 0.72))
    elif spendable > 0 and not urgent_need:
        bid = min(bid, 20.0 + spendable * 0.25)

    bid = max(0.0, min(budget, bid))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    low_hp_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= 120:
            rich_count += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('hp', 0) <= 3:
            low_hp_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))
            if prev.get('status') != 'alive' or prev.get('hp_after', 10) <= 2:
                desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

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

    if scarcity == 2:
        urgency += 2
    elif scarcity == 1:
        urgency += 1

    if highest_prev >= 120:
        pressure_bid = 96.0
    elif highest_prev >= 90:
        pressure_bid = highest_prev + 2.0
    elif highest_prev >= 50:
        pressure_bid = max(52.0, avg_prev + 3.0)
    else:
        pressure_bid = 38.0

    if rich_count >= 2 and scarcity >= 1:
        pressure_bid += 8.0
    if desperate_count >= 2 and hp > 4:
        pressure_bid -= 10.0
    if low_hp_opp >= 2 and hp > 5:
        pressure_bid -= 6.0

    if urgency >= 7:
        bid = max(pressure_bid, 98.0)
    elif urgency >= 5:
        bid = max(pressure_bid, 78.0)
    elif urgency >= 3:
        bid = max(pressure_bid, 52.0)
    else:
        if supply >= 23 and hp >= 7:
            bid = 18.0
        elif supply >= 20 and hp >= 6:
            bid = 26.0
        else:
            bid = max(30.0, pressure_bid - 8.0)

    if budget < 60:
        bid = min(bid, max(18.0, budget * 0.72))
    elif budget < 120:
        bid = min(bid, budget * 0.82)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, 105.0))

    if bid > budget:
        bid = budget
    if bid < 0:
        bid = 0.0
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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    units = int(supply // WATER_REQ)
    if units < 0:
        units = 0

    serious_bids = []
    all_prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            all_prev_bids.append(float(pbid))
            if float(pbid) >= 80:
                serious_bids.append(float(pbid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 300:
            if pbid is not None and float(pbid) >= 95:
                rich_aggressive += 1

    highest_prev = max(all_prev_bids) if all_prev_bids else 0.0
    high_anchor = max(102.0, highest_prev + 1.2)
    medium_anchor = max(72.0, min(96.0, highest_prev * 0.82 if highest_prev > 0 else 78.0))
    low_anchor = 24.0

    urgent = hp <= 3 or no_water >= 1
    very_urgent = hp <= 2 or no_water >= 2

    if not alive:
        bid = min(budget, 18.0 if not urgent else 45.0)
        return float(max(0.0, bid))

    if units >= 2:
        if very_urgent:
            bid = min(budget, medium_anchor)
        elif urgent:
            bid = min(budget, 58.0)
        else:
            bid = min(budget, low_anchor + 2.0 * desperate_count)
    elif units == 1:
        if very_urgent:
            bid = min(budget, high_anchor)
        elif urgent:
            bid = min(budget, max(88.0, medium_anchor + 8.0))
        else:
            if rich_aggressive >= 2:
                bid = min(budget, 34.0)
            else:
                bid = min(budget, medium_anchor)
    else:
        bid = 0.0

    if day >= 8 and hp >= 5 and no_water == 0 and units == 1 and rich_aggressive >= 1:
        bid = min(bid, 28.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 35.0
    if budget - bid < reserve_floor and not urgent:
        bid = max(0.0, budget - reserve_floor)

    if very_urgent:
        bid = max(bid, min(budget, 84.0 if units >= 2 else high_anchor))

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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    cindy_prev_bid = None
    pressure_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80:
                    pressure_count += 1
                if agent_id == 'Cindy':
                    cindy_prev_bid = float(bid)

    if not alive_opponents:
        return float(min(budget, 18.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        if cindy_prev_bid is not None and supply <= 17:
            bid = min(budget, cindy_prev_bid + 3.0)
        else:
            bid = min(budget, 92.0 + 18.0 * scarcity)
        return float(max(0.0, bid))

    if urgent:
        if cindy_prev_bid is not None and supply <= 18:
            bid = min(budget, max(72.0, cindy_prev_bid * 0.9))
        else:
            bid = min(budget, 58.0 + 14.0 * scarcity)
        return float(max(0.0, bid))

    if supply >= 22:
        return float(min(budget, 12.0))

    if supply >= 20:
        base = 16.0 if pressure_count >= 1 else 20.0
        return float(min(budget, base))

    if supply >= 18:
        if cindy_prev_bid is not None and cindy_prev_bid < 60:
            bid = cindy_prev_bid + 2.0
        else:
            bid = 28.0 + 6.0 * scarcity
        return float(min(budget, bid))

    if cindy_prev_bid is not None:
        bid = min(budget, max(38.0, cindy_prev_bid * 0.72))
    elif prev_bids:
        bid = min(budget, max(36.0, max(prev_bids) * 0.75))
    else:
        bid = min(budget, 40.0)

    if day >= 8 and hp >= 5:
        bid *= 0.9

    return float(max(0.0, min(budget, bid)))
"""
