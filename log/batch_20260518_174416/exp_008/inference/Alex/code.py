# ============================================================
# Experiment: exp_008
# Agent: Alex
# Source: exp_008
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass

    if not alive_opponents:
        return max(0.0, min(float(budget), 18.0))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    base = 24.0 + 18.0 * scarcity

    if hp <= 2:
        base += 24.0
    elif hp <= 4:
        base += 10.0

    if no_water >= 2:
        base += 22.0
    elif no_water >= 1:
        base += 10.0

    base += min(urgent_opp * 2.0, 8.0)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = max(avg_prev + 1.0, highest_prev + 1.5)
        if highest_prev >= 60:
            if hp > 4 and no_water == 0:
                base = min(base, 28.0 + 8.0 * scarcity)
            else:
                base = max(base, min(66.0, highest_prev + 1.0))
        else:
            base = max(base, target)

    if budget < DAILY_SALARY:
        base = min(base, max(12.0, budget * 0.55))

    if hp <= 2 or no_water >= 2:
        base = max(base, 60.0)

    bid = min(float(budget), base)
    if bid < 0:
        bid = 0.0
    return float(bid)
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_aggro = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if bid >= 80 and opp.get('budget', 0) >= 200:
                    rich_aggro += 1

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        emergency = max(78.0, highest_prev + 3.0)
        if tight_supply:
            emergency += 8.0
        return min(budget, emergency)

    if hp <= 4 or no_water_days >= 1:
        protective = max(52.0, avg_prev * 0.8 + 4.0)
        if tight_supply:
            protective += 10.0
        return min(budget, protective)

    if loose_supply and rich_aggro >= 1:
        return min(budget, 8.0)

    if tight_supply:
        if highest_prev >= 120:
            return min(budget, 20.0)
        if highest_prev >= 90:
            return min(budget, 28.0)
        return min(budget, max(26.0, avg_prev * 0.45 + 3.0 + urgent_opp * 2.0))

    if highest_prev >= 130:
        return min(budget, 10.0)
    if highest_prev >= 100:
        return min(budget, 14.0)
    if highest_prev >= 80:
        return min(budget, 18.0)

    base = 16.0
    if avg_prev > 0:
        base = max(base, avg_prev * 0.35 + 2.0)
    base += urgent_opp * 1.5

    remaining_days = 10 - day_context['day']
    if remaining_days <= 2 and hp >= 5:
        base *= 0.8

    return min(budget, max(6.0, base))
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    aggressive_count = 0
    weak_count = 0
    rich_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                weak_count += 1
            if opp.get('budget', 0) >= 700:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 90:
                    aggressive_count += 1

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1
    high_supply = supply >= 22
    low_supply = supply <= 17

    if urgent:
        target = max(92.0, highest_prev + 3.0)
        if low_supply:
            target += 8.0
        return float(min(budget, target))

    if high_supply and hp >= 5 and no_water_days == 0:
        target = 16.0
        if aggressive_count == 0 and avg_prev < 60:
            target = 24.0
        return float(min(budget, target))

    if low_supply:
        if highest_prev >= 110:
            target = 36.0 if hp >= 6 and no_water_days == 0 else 88.0
        elif highest_prev >= 85:
            target = 54.0 if hp >= 6 else 82.0
        else:
            target = max(58.0, highest_prev + 2.5)
        if rich_count >= 1:
            target += 4.0
        return float(min(budget, target))

    target = 0.0
    if highest_prev >= 120:
        target = 28.0 if hp >= 6 and no_water_days == 0 else 86.0
    elif highest_prev >= 95:
        target = 34.0 if hp >= 6 else 74.0
    elif highest_prev >= 70:
        target = max(46.0, highest_prev * 0.72)
    elif highest_prev > 0:
        target = max(38.0, highest_prev + 1.5)
    else:
        target = 42.0

    if pressured:
        target += 10.0
    if weak_count >= 2 and hp >= 5 and no_water_days == 0:
        target -= 6.0

    remaining_days = max(0, 10 - int(day))
    reserve = remaining_days * 18.0
    if budget - target < reserve and not pressured:
        target = max(20.0, min(target, budget - reserve))

    if target < 0:
        target = 0.0
    return float(min(budget, target))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        base = 18.0 if hp > 3 else 40.0
        return float(min(budget, base))

    prev_bids = []
    threat_bid = 0.0
    cindy_bid = None
    desperate_count = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = 0.0
        if prev and prev.get('bid') is not None:
            pbid = float(prev.get('bid', 0.0))
            prev_bids.append(pbid)
            if pbid > threat_bid:
                threat_bid = pbid
        if oid == 'Cindy':
            cprev = opp.get('previous_trace', {})
            if cprev and cprev.get('bid') is not None:
                cindy_bid = float(cprev.get('bid', 0.0))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            desperate_count += 1

    expected_units = supply / float(WATER_REQ)
    tight = expected_units <= 1.6
    very_tight = expected_units <= 1.2
    loose = expected_units >= 1.9

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
    elif tight:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1

    if cindy_bid is not None and cindy_bid >= 120 and urgency <= 2 and loose:
        return float(min(budget, 12.0))

    if urgency >= 6:
        bid = max(78.0, threat_bid + 3.0)
        if cindy_bid is not None and cindy_bid > 140:
            bid = max(92.0, min(cindy_bid - 8.0, budget))
        return float(min(budget, bid))

    if urgency >= 4:
        if threat_bid >= 100:
            bid = 72.0
        elif threat_bid > 0:
            bid = max(58.0, threat_bid + 2.0)
        else:
            bid = 56.0
        return float(min(budget, bid))

    if urgency >= 2:
        if loose:
            bid = 28.0
        else:
            if threat_bid >= 110:
                bid = 34.0
            elif threat_bid > 0:
                bid = max(32.0, min(48.0, threat_bid * 0.72))
            else:
                bid = 36.0
        return float(min(budget, bid))

    if cindy_bid is not None and cindy_bid >= 120:
        bid = 10.0 if loose else 16.0
    elif threat_bid >= 80:
        bid = 18.0
    elif threat_bid > 0:
        bid = max(20.0, min(30.0, threat_bid * 0.55))
    else:
        bid = 22.0

    if day >= 8 and hp <= 5:
        bid = max(bid, 42.0)

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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_pressure = 0.0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if bid > opp_pressure:
                    opp_pressure = bid

    if budget <= 0:
        return 0.0

    if len(alive_opponents) == 0:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0:
        supply_ratio = 0.0
    if supply_ratio > 1:
        supply_ratio = 1.0

    tight_supply = supply <= 17
    very_tight_supply = supply <= 16

    if hp <= 2 or no_water >= 2:
        emergency = max(DAILY_SALARY * 1.05, opp_pressure + 4.0)
        return float(min(budget, emergency))

    if hp <= 4 or no_water >= 1:
        urgent = max(DAILY_SALARY * 0.88, opp_pressure + 2.0)
        if very_tight_supply:
            urgent = max(urgent, DAILY_SALARY * 0.98)
        return float(min(budget, urgent))

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    if tight_supply:
        base = DAILY_SALARY * 0.72
        if highest_prev > 0:
            base = max(base, min(highest_prev + 1.5, DAILY_SALARY * 0.96))
        return float(min(budget, base))

    if highest_prev >= 145:
        bid = DAILY_SALARY * 0.34
    elif highest_prev >= 135:
        bid = DAILY_SALARY * 0.42
    elif highest_prev >= 120:
        bid = DAILY_SALARY * 0.52
    else:
        bid = DAILY_SALARY * (0.48 + 0.10 * (1.0 - supply_ratio))
        if avg_prev > 0:
            bid = max(bid, min(avg_prev * 0.52, DAILY_SALARY * 0.7))

    if day >= 8 and hp >= 7:
        bid *= 0.9

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.7)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
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

    alive = []
    prev_bids = []
    bob_bid = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
                if agent_id == 'Bob':
                    bob_bid = prev['bid']

    if not alive:
        return max(0.0, min(budget, 18.0))

    alive_count = len(alive)
    tight_supply = supply <= WATER_REQ * 1.35
    medium_supply = supply <= WATER_REQ * 1.7

    if hp <= 2 or no_water_days >= 2:
        emergency = DAILY_SALARY * 0.96
        if bob_bid is not None:
            emergency = max(emergency, bob_bid + 2.0)
        return max(0.0, min(budget, emergency))

    highest_prev = max(prev_bids) if prev_bids else 0.0

    if tight_supply:
        base = 62.0
        if bob_bid is not None:
            base = max(base, min(95.0, bob_bid + 1.25))
        elif highest_prev > 0:
            base = max(base, min(90.0, highest_prev + 1.0))
        if hp <= 4:
            base += 6.0
        return max(0.0, min(budget, base))

    if medium_supply:
        base = 41.0
        if bob_bid is not None and bob_bid < 80:
            base = max(base, bob_bid + 0.75)
        if hp <= 4:
            base += 5.0
        return max(0.0, min(budget, base))

    base = 24.0
    if alive_count >= 3:
        base = 27.0
    if hp <= 4:
        base += 4.0
    if day >= 8 and budget > DAILY_SALARY:
        base += 3.0
    return max(0.0, min(budget, base))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.55))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    threat_score = 0.0
    cindy_bid = None
    bob_bid = None

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            req = opp.get('water_requirement', WATER_REQ)
            sal = opp.get('daily_salary', DAILY_SALARY)
            pressure = float(bid) / max(1.0, float(sal))
            if req <= supply:
                threat_score += pressure
            if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
                pass
        opp_prev_name_hint = opp.get('previous_trace', {})
        _ = opp_prev_name_hint

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if opp_id == 'Cindy' and bid is not None:
            cindy_bid = float(bid)
        if opp_id == 'Bob' and bid is not None:
            bob_bid = float(bid)

    contested = supply < (len(alive_opponents) + 1) * WATER_REQ
    very_tight = supply < 2 * WATER_REQ

    if hp <= 2 or no_water_days >= 2:
        emergency = max(0.92 * DAILY_SALARY, (max(prev_bids) + 2.0) if prev_bids else 64.0)
        if cindy_bid is not None:
            emergency = max(emergency, min(165.0, cindy_bid + 3.0))
        return float(min(budget, emergency))

    if hp <= 4 or no_water_days >= 1:
        if contested:
            target = 0.78 * DAILY_SALARY
            if prev_bids:
                target = max(target, max(prev_bids) + 1.5)
            if cindy_bid is not None and cindy_bid <= 90:
                target = max(target, cindy_bid + 2.0)
            return float(min(budget, target))
        return float(min(budget, 0.48 * DAILY_SALARY))

    if very_tight:
        if cindy_bid is not None and cindy_bid >= 95:
            return float(min(budget, 8.0))
        if prev_bids:
            top = max(prev_bids)
            if top < 70:
                return float(min(budget, top + 1.0))
        return float(min(budget, 18.0))

    if contested:
        if cindy_bid is not None and cindy_bid >= 110:
            return float(min(budget, 12.0))
        if bob_bid is not None and cindy_bid is None:
            return float(min(budget, max(32.0, bob_bid + 1.0)))
        if prev_bids:
            top = max(prev_bids)
            if top <= 60:
                return float(min(budget, top + 1.0))
            if top <= 80:
                return float(min(budget, 46.0))
        return float(min(budget, 28.0))

    return float(min(budget, 17.0))
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    eric_prev = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            if agent_id == 'Eric':
                eric_prev = float(prev['bid'])

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    total_alive = len(alive) + 1
    expected_fair = float(supply) / float(total_alive)
    tight = expected_fair < 1.0
    very_tight = float(supply) <= 16.0
    abundant = float(supply) >= 22.0

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water >= 2:
        danger += 2
    elif no_water >= 1:
        danger += 1

    ref_bid = 0.0
    if eric_prev is not None:
        ref_bid = eric_prev
    elif prev_bids:
        ref_bid = max(prev_bids)

    if danger >= 3:
        bid = max(DAILY_SALARY * 0.95, ref_bid + 3.0)
    elif danger >= 2:
        bid = max(DAILY_SALARY * 0.78, ref_bid + 2.0)
    elif very_tight:
        bid = max(DAILY_SALARY * 0.72, ref_bid + 1.5)
    elif tight:
        bid = max(DAILY_SALARY * 0.58, ref_bid * 0.72 + 1.0)
    elif abundant:
        bid = DAILY_SALARY * 0.26
    else:
        bid = DAILY_SALARY * 0.4

    if ref_bid >= 120.0 and danger == 0:
        bid = min(bid, DAILY_SALARY * 0.32)
    if ref_bid >= 150.0 and danger <= 1:
        bid = min(bid, DAILY_SALARY * 0.22)

    reserve = 0.0
    if day <= 3:
        reserve = DAILY_SALARY * 1.2
    elif day <= 6:
        reserve = DAILY_SALARY * 0.8
    else:
        reserve = DAILY_SALARY * 0.3

    max_affordable = max(0.0, budget - reserve)
    if danger >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return bid
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_bid = 0.0
    rich_competitors = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > budget:
                rich_competitors += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > dangerous_bid:
                    dangerous_bid = float(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.22))

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0:
        tightness = 0.0
    if tightness > 1:
        tightness = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days == 1:
        urgency += 0.3

    urgency += 0.45 * tightness

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if supply <= 17:
        base = 72 + 22 * tightness + 10 * urgency
    elif supply <= 20:
        base = 54 + 18 * tightness + 8 * urgency
    else:
        base = 28 + 14 * tightness + 6 * urgency

    if dangerous_bid > 0:
        if urgency >= 0.9:
            target = dangerous_bid + 2.5
        elif supply <= 17 and hp > 4:
            target = dangerous_bid + 1.2
        elif dangerous_bid >= 150 and hp > 5 and no_water_days == 0:
            target = max(base, avg_prev * 0.45)
        elif dangerous_bid >= 105 and supply >= 22 and hp > 4:
            target = max(base, avg_prev * 0.55)
        else:
            target = max(base, dangerous_bid + 1.0)
    else:
        target = base

    if rich_competitors >= 2 and supply <= 18:
        target += 6.0

    reserve_floor = 0.0
    if hp > 4 and no_water_days == 0:
        reserve_floor = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve_floor = DAILY_SALARY * 0.6

    max_affordable = budget - reserve_floor
    if max_affordable < 0:
        max_affordable = budget * 0.7
    if urgency >= 1.0:
        max_affordable = budget

    bid = min(target, max_affordable)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, dangerous_bid + 2.0 if dangerous_bid > 0 else DAILY_SALARY * 0.9))
    elif hp <= 4 and supply <= 18:
        bid = max(bid, min(budget, dangerous_bid + 1.5 if dangerous_bid > 0 else DAILY_SALARY * 0.78))

    if supply >= 23 and hp >= 7 and no_water_days == 0 and dangerous_bid >= 120:
        bid = min(bid, DAILY_SALARY * 0.42)

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
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_count += 1
            if opp.get('budget', 0) > 500:
                prev = opp.get('previous_trace', {}) or {}
                pb = prev.get('bid')
                if pb is not None and pb >= 70:
                    rich_aggressive += 1
            prev = opp.get('previous_trace', {}) or {}
            pb = prev.get('bid')
            if pb is not None:
                prev_bids.append(float(pb))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    total_alive = len(alive) + 1
    pressure = supply / float(total_alive * WATER_REQ)

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

    if supply <= 16:
        urgency += 2
    elif supply <= 18:
        urgency += 1

    if day >= 8:
        urgency += 1

    if pressure >= 0.45 and urgency <= 1:
        bid = 14.0
    elif pressure >= 0.35 and urgency <= 2:
        bid = 22.0
    else:
        if urgency >= 5:
            bid = max(72.0, highest_prev + 2.0)
        elif urgency >= 3:
            bid = max(48.0, min(78.0, highest_prev * 0.82 + 3.0))
        else:
            bid = max(28.0, min(58.0, avg_prev * 0.72 + 2.0))

    if rich_aggressive >= 2 and urgency <= 2:
        bid = min(bid, 24.0)

    if desperate_count >= 2 and urgency >= 3:
        bid = max(bid, highest_prev + 3.0)

    if hp <= 1 or no_water_days >= 3:
        bid = max(bid, 90.0)

    reserve = 0.0
    if day <= 7:
        reserve = 25.0
    elif day <= 9:
        reserve = 10.0

    bid = min(bid, budget)
    if budget > reserve:
        bid = min(bid, budget - reserve + min(reserve, 5.0))

    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""
