# ============================================================
# Experiment: exp_106
# Agent: Alex
# Source: exp_106
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

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 63)
        if supply >= 22:
            return min(budget, 18)
        return min(budget, 28)

    prev_bids = []
    distress_count = 0
    rich_count = 0
    total_req = WATER_REQ

    for opp in alive_opponents:
        total_req += opp.get('water_requirement', WATER_REQ)
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            distress_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))
            status = prev.get('status')
            if status in ['lost', 'thirsty', 'error']:
                distress_count += 1

    expected_competition = float(total_req) / float(max(supply, 1))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 0
        avg_prev = 0

    if hp <= 2 or no_water_days >= 2:
        bid = max(60, highest_prev + 2)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(48, avg_prev + 3)
    else:
        if supply >= 23:
            bid = 20
        elif supply >= 20:
            bid = 28
        elif supply >= 17:
            bid = 36
        else:
            bid = 44

        if expected_competition > 2.0:
            bid += 8
        elif expected_competition > 1.5:
            bid += 4

        if highest_prev >= 60:
            bid = max(bid, highest_prev - 8 if hp > 4 else highest_prev + 1)
        elif highest_prev >= 45:
            bid = max(bid, highest_prev + 2)
        elif highest_prev > 0:
            bid = max(bid, avg_prev + 2)

    bid += min(distress_count, 3) * 2
    bid += min(rich_count, 2) * 2

    if budget < DAILY_SALARY * 2 and hp > 4 and no_water_days == 0:
        bid *= 0.8

    if supply >= 24 and hp > 4 and no_water_days == 0:
        bid *= 0.85

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
    pressure_scores = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            score = 0.0
            if bid is not None:
                score += float(bid)
            if opp.get('no_water_days', 0) >= 1:
                score += 12.0
            if opp.get('hp', 0) <= 4:
                score += 10.0
            if opp.get('budget', 0) < DAILY_SALARY:
                score -= 8.0
            if prev.get('status') in ('dead', 'eliminated', 'error'):
                score -= 20.0
            pressure_scores.append(score)

    if not alive:
        return float(min(budget, 12.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    opp_pressure = max(pressure_scores) if pressure_scores else 0.0

    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_tightness < 0:
        supply_tightness = 0.0
    if supply_tightness > 1:
        supply_tightness = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 38.0
    elif hp <= 4:
        urgency += 24.0
    elif hp <= 6:
        urgency += 12.0

    if no_water >= 2:
        urgency += 34.0
    elif no_water >= 1:
        urgency += 18.0

    urgency += supply_tightness * 18.0

    if day >= 8:
        urgency += 8.0

    base = 18.0 + urgency

    if highest_prev >= 120:
        target = min(highest_prev * 0.72, 92.0) + urgency * 0.25
    elif highest_prev >= 80:
        target = max(42.0, highest_prev * 0.78) + urgency * 0.22
    elif highest_prev >= 45:
        target = max(30.0, avg_prev * 0.92 + 4.0) + urgency * 0.18
    else:
        target = base + max(0.0, opp_pressure * 0.08)

    rich_threats = 0
    for opp in alive:
        if opp.get('budget', 0) > budget and opp.get('hp', 0) > 4:
            rich_threats += 1
    target += 3.0 * rich_threats

    if supply >= 23 and hp >= 6 and no_water == 0:
        target *= 0.72
    elif supply <= 17:
        target *= 1.18

    reserve_floor = DAILY_SALARY * 0.22
    if budget < DAILY_SALARY * 1.2:
        target = min(target, budget - min(reserve_floor, budget * 0.15))

    if hp <= 2 or no_water >= 2:
        target = max(target, min(budget, 78.0))

    if target < 0:
        target = 0.0

    bid = min(budget, target)
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
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
    prev_bids = []
    danger_bids = []
    req_sum = WATER_REQ

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            req_sum += opp.get('water_requirement', WATER_REQ)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if b >= 115:
                    danger_bids.append(b)

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, min(budget, 35.0))
        return max(0.0, min(budget, 8.0))

    scarcity = req_sum / max(float(supply), 1.0)
    high_supply = supply >= 22
    low_supply = supply <= 17

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
    elif no_water_days >= 1:
        urgency += 2
    if low_supply:
        urgency += 2
    elif not high_supply:
        urgency += 1
    if scarcity > 3.2:
        urgency += 2
    elif scarcity > 2.6:
        urgency += 1
    if highest_prev >= 120:
        urgency += 1

    if urgency <= 1:
        bid = 18.0 if high_supply else 28.0
    elif urgency == 2:
        bid = 42.0
    elif urgency == 3:
        bid = max(58.0, min(88.0, avg_prev * 0.72 + 8.0))
    elif urgency == 4:
        target = max(96.0, min(112.0, highest_prev + 2.5)) if highest_prev > 0 else 98.0
        bid = target
    elif urgency == 5:
        target = max(108.0, min(121.0, highest_prev + 3.0)) if highest_prev > 0 else 112.0
        bid = target
    else:
        target = max(118.0, min(130.0, highest_prev + 4.0)) if highest_prev > 0 else 122.0
        bid = target

    if high_supply and hp >= 7 and no_water_days == 0:
        bid *= 0.72
    if day >= 8 and budget > 0:
        bid *= 1.06
    if budget < 120:
        bid = min(bid, budget * 0.72)
    if budget < 70:
        bid = min(bid, budget * 0.9)

    if hp <= 2 or no_water_days >= 2:
        emergency = max(115.0, highest_prev + 3.0 if highest_prev > 0 else 115.0)
        bid = max(bid, emergency)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_pressure = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 100:
                    strong_pressure += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    desperate = hp <= 2 or no_water_days >= 2
    urgent = hp <= 4 or no_water_days >= 1

    if desperate:
        bid = min(budget, max(62.0, highest_prev + 2.0, DAILY_SALARY * 0.95))
        return float(max(0.0, bid))

    if tight_supply:
        if highest_prev >= 120:
            bid = 22.0 if hp > 5 and no_water_days == 0 else 68.0
        elif highest_prev >= 70:
            bid = max(54.0, highest_prev + 1.5)
        else:
            bid = 49.0 if urgent else 38.0
        return float(min(budget, max(0.0, bid)))

    if medium_supply:
        if strong_pressure >= 1 and hp > 5 and no_water_days == 0:
            bid = 16.0
        elif avg_prev >= 60:
            bid = 34.0 if not urgent else 52.0
        else:
            bid = 28.0 if not urgent else 46.0
        return float(min(budget, max(0.0, bid)))

    if highest_prev >= 120 and hp > 4 and no_water_days == 0:
        bid = 10.0
    elif urgent:
        bid = 42.0
    else:
        bid = 20.0

    return float(min(budget, max(0.0, bid)))
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, 18.0))

    opp_bids = []
    strong_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            opp_bids.append(float(bid))
            if bid >= 90:
                strong_bids.append(float(bid))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 0) <= 4:
            urgent_opp += 1
        if opp.get('budget', 0) >= 300:
            rich_opp += 1

    max_prev = max(opp_bids) if opp_bids else 0.0
    avg_prev = sum(opp_bids) / len(opp_bids) if opp_bids else 0.0

    total_players = 1 + len(alive)
    likely_winners = int(max(1, supply // WATER_REQ))
    scarcity = likely_winners < total_players
    moderate = likely_winners >= 2

    critical_me = (hp <= 4) or (no_water >= 1)
    very_critical_me = (hp <= 2) or (no_water >= 2)

    if very_critical_me:
        base = max(96.0, max_prev + 2.5)
    elif critical_me:
        base = max(82.0, avg_prev + 3.0)
    else:
        if scarcity:
            base = max(58.0, avg_prev * 0.72 + 6.0)
        elif moderate:
            base = max(16.0, avg_prev * 0.22)
        else:
            base = 12.0

    if len(strong_bids) >= 2 and not critical_me and moderate:
        base = min(base, 24.0)

    if rich_opp >= 2 and scarcity:
        base += 8.0
    if urgent_opp >= 2 and scarcity:
        base += 10.0

    if day >= 8:
        base += 8.0
    if day >= 9 and critical_me:
        base += 10.0

    if budget < DAILY_SALARY:
        base = min(base, budget * 0.82)
    elif budget < 140:
        base = min(base, budget * 0.72)

    if not critical_me and moderate and max_prev >= 110:
        base = min(base, 21.0)

    bid = max(0.0, min(float(budget), float(base)))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 90 and opp.get('budget', 0) >= 120:
                    rich_aggressive += 1

    winners_est = max(1, int(supply // WATER_REQ))
    num_alive = len(alive_opps) + 1

    if not alive_opps:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 40.0))
        return float(min(budget, 18.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
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
    elif no_water_days >= 1:
        urgency += 2

    pressure = 0
    if winners_est < min(2, num_alive):
        pressure += 2
    elif winners_est == 2 and num_alive > 2:
        pressure += 1
    if high_prev >= 120:
        pressure += 2
    elif high_prev >= 80:
        pressure += 1
    if desperate_count >= winners_est:
        pressure += 1

    if urgency >= 5:
        bid = max(95.0, high_prev + 3.0, avg_prev + 8.0)
    elif urgency >= 3:
        bid = max(62.0, min(98.0, high_prev * 0.78 + 6.0))
    else:
        if winners_est >= 2:
            bid = 24.0 + 4.0 * pressure
            if rich_aggressive >= 2:
                bid = min(bid, 30.0)
        else:
            bid = 34.0 + 8.0 * pressure
            if high_prev >= 100 and hp > 4 and no_water_days == 0:
                bid = 22.0

    remaining_days = max(1, 10 - int(day) + 1)
    soft_cap = budget / remaining_days + DAILY_SALARY * 0.45
    if urgency <= 1:
        bid = min(bid, soft_cap)

    if hp > 6 and no_water_days == 0 and rich_aggressive >= 2 and winners_est >= 2:
        bid = min(bid, 26.0)

    if hp <= 3 and budget >= 80:
        bid = max(bid, 78.0)

    bid = max(0.0, min(float(bid), float(budget)))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    dangerous_prev = 0.0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0.0)
            prev_bids.append(bid)
            if opp.get('budget', 0) > 0 and bid > dangerous_prev:
                dangerous_prev = bid

    alive_count = len(alive)
    req_pressure = (alive_count + 1) * WATER_REQ
    tight_supply = supply <= req_pressure
    very_tight = supply <= req_pressure - WATER_REQ

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

    if very_tight:
        urgency += 2
    elif tight_supply:
        urgency += 1

    if day >= 8:
        urgency += 1

    if dangerous_prev <= 0:
        if urgency >= 5:
            bid = DAILY_SALARY * 0.9
        elif urgency >= 3:
            bid = DAILY_SALARY * 0.62
        elif tight_supply:
            bid = DAILY_SALARY * 0.48
        else:
            bid = DAILY_SALARY * 0.32
    else:
        if urgency >= 5:
            bid = max(DAILY_SALARY * 0.9, dangerous_prev + 2.0)
        elif urgency >= 3:
            bid = max(DAILY_SALARY * 0.68, dangerous_prev + 1.2)
        elif tight_supply:
            bid = max(DAILY_SALARY * 0.52, dangerous_prev + 0.8)
        else:
            if dangerous_prev >= DAILY_SALARY * 1.8:
                bid = DAILY_SALARY * 0.22
            elif dangerous_prev >= DAILY_SALARY * 1.2:
                bid = DAILY_SALARY * 0.3
            else:
                bid = max(DAILY_SALARY * 0.38, dangerous_prev * 0.72)

    if hp >= 8 and no_water_days == 0 and not tight_supply:
        bid = min(bid, DAILY_SALARY * 0.28)

    if budget < DAILY_SALARY * 0.8 and urgency < 4:
        bid = min(bid, budget * 0.55)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
                prev_bids.append(float(bid))
            req = float(opp.get('water_requirement', WATER_REQ))
            sal = float(opp.get('daily_salary', DAILY_SALARY))
            pressure = req / max(1.0, supply)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                pressure += 0.35
            if bid is not None:
                pressure += min(0.5, float(bid) / 200.0)
            pressure += min(0.3, sal / 300.0)
            opp_pressures.append(pressure)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    my_risk = 0.0
    if hp <= 2:
        my_risk += 0.8
    elif hp <= 4:
        my_risk += 0.45
    if no_water_days >= 1:
        my_risk += 0.45

    opp_threat = max(opp_pressures) if opp_pressures else 0.0

    base = DAILY_SALARY * (0.28 + 0.42 * scarcity)
    base += DAILY_SALARY * 0.32 * my_risk

    if highest_prev >= 120:
        if my_risk < 0.45 and supply >= 20:
            bid = DAILY_SALARY * 0.22
        else:
            bid = max(base, min(highest_prev + 2.0, DAILY_SALARY * 1.45))
    elif highest_prev >= 85:
        if my_risk < 0.3 and supply >= 21:
            bid = DAILY_SALARY * 0.26
        else:
            bid = max(base, highest_prev + 1.5)
    elif highest_prev > 0:
        bid = max(base, avg_prev + 3.0, highest_prev + 1.0)
    else:
        bid = base

    if opp_threat > 1.25:
        bid += 8.0
    elif opp_threat > 1.0:
        bid += 4.0

    if day >= 8 and hp >= 6 and budget < DAILY_SALARY * 3:
        bid *= 0.82

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 1.05)

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve = DAILY_SALARY * 0.6

    affordable = max(0.0, budget - reserve)
    if my_risk >= 0.8:
        affordable = budget

    bid = min(bid, budget, max(0.0, affordable) if affordable > 0 else budget)
    bid = max(0.0, bid)
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

    alive = []
    prev_bids = []
    opp_budgets = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(float(opp.get('budget', 0)))
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            if opp.get('budget', 0) >= 900:
                rich_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 90.0))
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 130.0
    median_anchor = 128.0
    if prev_bids:
        s = sorted(prev_bids)
        median_anchor = s[int(len(s) // 2)]

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

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

    endgame = day >= 8

    if danger >= 5:
        target = max(146.0, highest_prev + 4.0)
    elif danger >= 3:
        target = max(138.0, median_anchor + 6.0, highest_prev - 1.0)
    else:
        if supply >= 23:
            target = 36.0
        elif supply >= 21:
            target = 62.0
        elif supply >= 19:
            target = 96.0
        elif supply >= 17:
            target = max(122.0, median_anchor + 2.0)
        else:
            target = max(136.0, highest_prev + 2.0)

    target += scarcity * 10.0
    target += urgent_opp * 1.5
    target += rich_opp * 1.0
    if endgame and (hp <= 6 or no_water_days >= 1):
        target += 6.0

    reserve = 0.0
    if day <= 3 and hp >= 7 and no_water_days == 0:
        reserve = 25.0
    elif day <= 6 and hp >= 5 and no_water_days == 0:
        reserve = 10.0

    max_affordable = max(0.0, budget - reserve)
    if danger >= 5:
        max_affordable = budget

    bid = min(target, max_affordable)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 150.0))
    elif hp <= 4 or no_water_days >= 1:
        bid = min(budget, max(bid, 138.0))

    if supply >= 23 and hp >= 7 and no_water_days == 0:
        bid = min(bid, min(budget, 45.0))

    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0

    scarcity = supply <= WATER_REQ * 2
    danger = hp <= 4 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        bid = max(DAILY_SALARY * 1.15, max_prev + 3.0)
    elif danger:
        if max_prev <= DAILY_SALARY * 0.9:
            bid = max(DAILY_SALARY * 0.95, max_prev + 2.0)
        else:
            bid = DAILY_SALARY * 0.9 if scarcity else DAILY_SALARY * 0.8
    else:
        if scarcity:
            if avg_prev >= 120:
                bid = DAILY_SALARY * 0.18
            elif max_prev >= 90:
                bid = DAILY_SALARY * 0.32
            else:
                bid = max(DAILY_SALARY * 0.45, max_prev + 1.5)
        else:
            if avg_prev >= 120:
                bid = DAILY_SALARY * 0.22
            elif max_prev >= 90:
                bid = DAILY_SALARY * 0.35
            else:
                bid = max(DAILY_SALARY * 0.5, max_prev + 1.0)

    if budget < DAILY_SALARY * 2 and not critical:
        bid = min(bid, DAILY_SALARY * 0.55)

    return float(min(budget, max(0.0, bid)))
"""
