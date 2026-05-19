# ============================================================
# Experiment: exp_083
# Agent: Alex
# Source: exp_083
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(budget, 21.0)

    prev_bids = []
    desperate_count = 0
    broke_count = 0
    error_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) < DAILY_SALARY * 0.6:
            broke_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('error'):
            error_count += 1
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
        status = prev.get('status')
        if status in ('thirsty', 'critical', 'failed'):
            desperate_count += 1

    slots_est = max(1, int(supply // WATER_REQ))
    pressure = len(alive_opponents) + 1 - slots_est

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    if hp <= 2 or no_water_days >= 2:
        target = max(63.0, highest_prev + 2.0)
    elif hp <= 4 or no_water_days >= 1:
        target = max(52.0, avg_prev + 3.0, highest_prev * 0.92)
    else:
        if pressure <= 0:
            target = 18.0 + 2.0 * max(0, desperate_count - broke_count)
        elif pressure == 1:
            target = max(28.0, avg_prev + 1.5)
        else:
            target = max(36.0, avg_prev + 3.0, highest_prev * 0.82)

    if error_count > 0:
        target -= 4.0
    if broke_count >= len(alive_opponents) / 2.0:
        target -= 5.0
    if desperate_count > len(alive_opponents) / 2.0:
        target += 4.0

    day = day_context['day']
    if day >= 8 and hp <= 5:
        target += 6.0

    target = max(0.0, min(float(budget), target))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 8.0))

    total_agents = 1 + len(alive)
    likely_winners = int(supply // WATER_REQ)
    if likely_winners < 1:
        likely_winners = 1

    prev_bids = []
    danger_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid', 0.0)
            prev_bids.append(bid)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                danger_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    highest_danger = max(danger_bids) if danger_bids else 0.0

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

    scarcity = total_agents - likely_winners

    if urgency >= 5:
        bid = max(92.0, highest_danger + 3.0, avg_prev + 8.0)
    elif urgency >= 3:
        bid = max(72.0, min(96.0, highest_danger + 2.0), avg_prev * 0.9 + 6.0)
    else:
        if scarcity <= 0:
            bid = 9.0
        elif likely_winners >= 2:
            bid = max(18.0, min(52.0, avg_prev * 0.45 + 4.0))
        else:
            if highest_prev >= 140.0:
                bid = 24.0
            elif highest_prev >= 100.0:
                bid = 34.0
            elif highest_prev >= 70.0:
                bid = 46.0
            else:
                bid = 41.0

    if day >= 8 and hp >= 5 and no_water_days == 0:
        bid *= 0.9

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.82)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 88.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
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
            if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
                desperate_count += 1
            if opp.get('budget', 0) >= 700:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    pressure = 0
    if supply <= 16:
        pressure += 2
    elif supply <= 18:
        pressure += 1

    if no_water_days >= 2:
        pressure += 3
    elif no_water_days >= 1:
        pressure += 1

    if hp <= 2:
        pressure += 3
    elif hp <= 4:
        pressure += 2
    elif hp <= 6:
        pressure += 1

    if desperate_count >= 2:
        pressure += 1

    if day >= 8:
        pressure += 1

    if pressure <= 1:
        bid = 16.0 if supply >= 20 else 22.0
        if highest_prev < 60:
            bid = max(bid, highest_prev + 2.0)
    elif pressure == 2:
        bid = 38.0
        if highest_prev > 0:
            bid = max(bid, min(72.0, highest_prev * 0.55))
    elif pressure == 3:
        bid = 68.0
        if highest_prev > 0:
            bid = max(bid, min(105.0, highest_prev * 0.72))
    elif pressure == 4:
        bid = 96.0
        if highest_prev > 0:
            bid = max(bid, min(145.0, highest_prev * 0.85))
    else:
        bid = 135.0
        if highest_prev > 0:
            bid = max(bid, min(185.0, highest_prev + 3.0))

    if supply >= 23 and pressure <= 2:
        bid *= 0.8
    elif supply <= 15:
        bid *= 1.2

    if avg_prev >= 150 and pressure <= 2:
        bid *= 0.85

    if rich_count >= 2 and pressure >= 3:
        bid *= 1.08

    if no_water_days == 0 and hp >= 8 and budget < 250:
        bid *= 0.85

    min_safe = 0.0
    if no_water_days >= 2 or hp <= 2:
        min_safe = 110.0
    elif no_water_days >= 1 or hp <= 4:
        min_safe = 70.0

    bid = max(bid, min_safe)
    bid = min(bid, budget)

    if budget < 80:
        bid = min(bid, max(22.0, budget * 0.92))

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

    guaranteed_units = int(supply / WATER_REQ)
    high_supply = supply >= 24
    medium_high_supply = supply >= 20

    prev_bids = []
    named_prev = {}
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            named_prev[oid] = float(bid)

    bob_bid = named_prev.get('Bob', 0.0)
    cindy_bid = named_prev.get('Cindy', 0.0)
    max_prev = max(prev_bids) if prev_bids else 0.0

    urgent = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if not alive:
        return float(min(budget, 20.0))

    if guaranteed_units <= 1:
        if urgent:
            bid = max(96.0, bob_bid + 3.0)
            if cindy_bid > 0:
                bid = min(bid, cindy_bid - 1.0)
            bid = max(bid, 92.0)
            return float(min(budget, bid))
        if pressured and medium_high_supply:
            bid = max(88.0, bob_bid + 2.0)
            return float(min(budget, bid))
        return float(min(budget, 8.0))

    if high_supply:
        if urgent:
            bid = max(95.0, bob_bid + 2.5)
            return float(min(budget, bid))
        if pressured:
            bid = max(91.0, bob_bid + 1.5)
            return float(min(budget, bid))
        if bob_bid > 0:
            bid = max(84.0, min(94.0, bob_bid + 1.0))
            return float(min(budget, bid))
        return float(min(budget, 82.0))

    if pressured:
        bid = max(90.0, bob_bid + 2.0)
        return float(min(budget, bid))

    if max_prev >= 120.0:
        return float(min(budget, 18.0))
    return float(min(budget, 12.0))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, max(8.0, DAILY_SALARY * 0.35)))

    yesterday_bids = []
    threat_bid = 0.0
    cindy_like = False
    urgent_opp = False

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid')
        if b is not None:
            yesterday_bids.append(float(b))
            if float(b) > threat_bid:
                threat_bid = float(b)
            if float(b) >= 135.0:
                cindy_like = True
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp = True

    alive_count = len(alive)
    contest_ratio = float(WATER_REQ * (alive_count + 1)) / float(supply if supply > 0 else MIN_SUPPLY)
    tight_supply = supply <= 17
    medium_supply = supply <= 20
    my_urgent = hp <= 3 or no_water_days >= 1
    very_urgent = hp <= 2 or no_water_days >= 2

    base = DAILY_SALARY * 0.42

    if contest_ratio > 2.5:
        base = DAILY_SALARY * 1.55
    elif contest_ratio > 2.0:
        base = DAILY_SALARY * 1.2
    elif contest_ratio > 1.6:
        base = DAILY_SALARY * 0.92
    elif contest_ratio > 1.3:
        base = DAILY_SALARY * 0.72

    if tight_supply:
        base += 18.0
    elif medium_supply:
        base += 8.0
    else:
        base -= 6.0

    if cindy_like:
        if my_urgent or tight_supply:
            base = max(base, threat_bid + 3.0)
        else:
            base = min(base, DAILY_SALARY * 0.55)
    elif threat_bid > 0:
        if my_urgent:
            base = max(base, threat_bid + 2.0)
        elif threat_bid >= 100.0 and not tight_supply:
            base = min(base, DAILY_SALARY * 0.5)
        else:
            base = max(base, min(threat_bid + 1.5, DAILY_SALARY * 1.05))

    if urgent_opp and not my_urgent and not tight_supply:
        base *= 0.9

    if my_urgent:
        base = max(base, DAILY_SALARY * 1.0)
    if very_urgent:
        base = max(base, DAILY_SALARY * 1.35)

    days_left = max(1, 10 - int(day) + 1)
    reserve_floor = DAILY_SALARY * 0.25 * max(0, days_left - 1)
    affordable = max(0.0, budget - reserve_floor)

    if very_urgent:
        bid = min(budget, max(base, affordable, DAILY_SALARY * 1.1))
    else:
        if affordable <= 0:
            bid = min(budget, max(6.0, DAILY_SALARY * 0.25))
        else:
            bid = min(base, budget, max(12.0, affordable))
            bid = min(bid, budget)

    if hp >= 8 and no_water_days == 0 and supply >= 22 and threat_bid >= 120.0:
        bid = min(budget, DAILY_SALARY * 0.35)

    if day >= 8 and hp > 4:
        bid = min(budget, max(bid, DAILY_SALARY * 0.75 if tight_supply else DAILY_SALARY * 0.5))

    if bid < 0:
        bid = 0.0
    return float(round(min(budget, bid), 2))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    pressure_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is not None:
            pressure_bids.append(float(prev_bid))
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 8:
            rich_count += 1

    max_prev = max(pressure_bids) if pressure_bids else 0.0
    avg_prev = sum(pressure_bids) / len(pressure_bids) if pressure_bids else 0.0

    scarcity = 1.0 - ((supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY))
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = (hp <= 2) or (no_water_days >= 2)
    semi_urgent = (hp <= 4) or (no_water_days >= 1)

    if urgent:
        target = max(DAILY_SALARY * 0.95, max_prev + 3.0)
        if supply <= 17:
            target = max(target, DAILY_SALARY * 1.15)
        return float(min(budget, target))

    if supply >= 23:
        if max_prev >= DAILY_SALARY * 1.5 and hp > 5 and no_water_days == 0:
            return float(min(budget, DAILY_SALARY * 0.18))
        target = max(DAILY_SALARY * 0.28, avg_prev * 0.45)
        return float(min(budget, target))

    if supply <= 17:
        if semi_urgent:
            target = max(DAILY_SALARY * 0.9, max_prev + 2.0, avg_prev + 4.0)
        else:
            if max_prev >= DAILY_SALARY * 1.6 and desperate_count == 0:
                target = DAILY_SALARY * 0.22
            else:
                target = max(DAILY_SALARY * 0.62, avg_prev * 0.8)
        if rich_count >= 2:
            target += 6.0
        return float(min(budget, target))

    base = DAILY_SALARY * (0.38 + 0.22 * scarcity)
    if max_prev > 0:
        if max_prev >= DAILY_SALARY * 1.4 and hp > 5 and no_water_days == 0:
            target = DAILY_SALARY * 0.25
        else:
            target = max(base, min(max_prev + 1.5, avg_prev + 10.0))
    else:
        target = base

    if semi_urgent:
        target = max(target, DAILY_SALARY * 0.72)
    if day >= 8 and hp <= 5:
        target = max(target, DAILY_SALARY * 0.82)

    return float(min(budget, target))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_pressure = 0
    desperate_pressure = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('budget', 0) >= 700:
                rich_pressure += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_pressure += 1

    if not alive:
        return float(min(budget, 8.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Estimate how tight the day is for 13-unit demand agents
    units_for_me = supply / float(WATER_REQ)
    very_tight = units_for_me < 1.35
    tight = units_for_me < 1.55
    loose = units_for_me > 1.75

    emergency = hp <= 2 or no_water >= 2
    urgent = hp <= 4 or no_water >= 1

    if emergency:
        bid = max(62.0, min(96.0, high_prev * 0.72 + 8.0))
        return float(min(budget, bid))

    if urgent and very_tight:
        bid = max(52.0, min(82.0, avg_prev * 0.5 + 10.0))
        return float(min(budget, bid))

    if loose:
        bid = 6.0
        if hp <= 5:
            bid = 12.0
        return float(min(budget, bid))

    if tight:
        bid = 18.0
        if rich_pressure >= 2:
            bid = 14.0
        if desperate_pressure >= 2:
            bid = 24.0
        if hp <= 6:
            bid += 8.0
        return float(min(budget, bid))

    bid = 10.0
    if hp <= 5:
        bid = 18.0
    if high_prev < 20.0 and avg_prev < 15.0:
        bid += 6.0

    return float(min(budget, bid))
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        base = 12.0 if hp > 3 else 28.0
        return float(min(budget, base))

    threats = []
    cindy_bid = None
    max_prev_bid = 0.0
    urgent_opp = False

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        prev_bid = 0.0
        if prev and prev.get('bid') is not None:
            prev_bid = float(prev.get('bid', 0.0))
        if prev_bid > max_prev_bid:
            max_prev_bid = prev_bid
        if agent_id == 'Cindy':
            cindy_bid = prev_bid
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 2:
            urgent_opp = True
        threats.append((agent_id, prev_bid, opp.get('budget', 0.0), opp.get('hp', 10), opp.get('no_water_days', 0), opp.get('water_requirement', WATER_REQ)))

    competitors = len(alive) + 1
    expected_share = float(supply) / float(competitors * WATER_REQ)

    my_urgent = (hp <= 2) or (no_water >= 2)
    my_semi_urgent = (hp <= 4) or (no_water >= 1)

    if my_urgent:
        target = 62.0
        if cindy_bid is not None:
            target = max(target, min(92.0, cindy_bid + 2.0))
        if urgent_opp:
            target += 4.0
        return float(min(budget, target))

    if expected_share >= 0.45:
        base = 14.0
        if cindy_bid is not None and cindy_bid < 25.0:
            base = 18.0
        if my_semi_urgent:
            base += 8.0
        return float(min(budget, base))

    if expected_share >= 0.30:
        target = 24.0
        if cindy_bid is not None:
            if cindy_bid >= 70.0:
                target = 26.0
            elif cindy_bid >= 45.0:
                target = cindy_bid + 1.5
            else:
                target = 32.0
        if urgent_opp:
            target += 3.0
        if my_semi_urgent:
            target += 10.0
        return float(min(budget, target))

    target = 34.0
    if cindy_bid is not None:
        if cindy_bid >= 80.0:
            target = 30.0
        elif cindy_bid >= 55.0:
            target = cindy_bid + 1.5
        else:
            target = max(36.0, cindy_bid + 2.0)
    else:
        target = max(34.0, max_prev_bid + 1.0)

    if urgent_opp:
        target += 4.0
    if my_semi_urgent:
        target += 10.0
    if day >= 8 and hp > 4 and no_water == 0:
        target -= 4.0

    return float(min(budget, target))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    threatening_bids = []
    rich_aggressive = []

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= budget * 0.6:
                    threatening_bids.append(float(bid))
                if float(bid) >= DAILY_SALARY * 0.9 and opp.get('budget', 0) > DAILY_SALARY * 4:
                    rich_aggressive.append(float(bid))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    total_players = 1 + len(alive)
    expected_share = float(supply) / float(total_players * WATER_REQ)

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

    if expected_share < 0.4:
        urgency += 3
    elif expected_share < 0.6:
        urgency += 2
    elif expected_share < 0.9:
        urgency += 1

    if threatening_bids:
        ref_bid = max(threatening_bids)
    elif prev_bids:
        ref_bid = max(prev_bids)
    else:
        ref_bid = DAILY_SALARY * 0.6

    if urgency >= 6:
        bid = max(DAILY_SALARY * 1.02, ref_bid + 2.5)
    elif urgency >= 4:
        bid = max(DAILY_SALARY * 0.88, ref_bid + 1.2)
    elif urgency >= 2:
        bid = max(DAILY_SALARY * 0.62, ref_bid * 0.9)
    else:
        bid = DAILY_SALARY * 0.42

    if rich_aggressive and urgency < 4:
        bid = min(bid, DAILY_SALARY * 0.58)

    if supply >= 23 and urgency <= 2:
        bid = min(bid, DAILY_SALARY * 0.45)
    elif supply <= 17:
        bid = max(bid, DAILY_SALARY * 0.82)

    if budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.55)
    elif budget < DAILY_SALARY * 4 and urgency < 4:
        bid = min(bid, DAILY_SALARY * 0.7)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 1.05))

    return max(0.0, min(float(budget), float(bid)))
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    slots = int(supply // WATER_REQ)
    if slots < 0:
        slots = 0

    prev_bids = []
    urgent_count = 0
    rich_aggressive = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 120 or opp.get('budget', 0) >= 180:
                rich_aggressive += 1
        elif opp.get('budget', 0) >= 180:
            rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    my_urgent = hp <= 3 or no_water_days >= 1
    desperate = hp <= 2 or no_water_days >= 2

    if slots >= 2:
        base = 18.0
        if avg_prev > 100:
            base = 24.0
        if rich_aggressive >= 2:
            base += 6.0
        if my_urgent:
            base += 18.0
        if desperate:
            base += 28.0
    elif slots == 1:
        if desperate:
            base = max(0.0, highest_prev + 8.0)
            base = max(base, DAILY_SALARY * 1.35)
        elif my_urgent:
            base = max(0.0, highest_prev + 4.0)
            base = max(base, DAILY_SALARY * 0.95)
        else:
            base = max(0.0, highest_prev + 2.0)
            base = max(base, DAILY_SALARY * 0.72)
            if rich_aggressive >= 2:
                base += 10.0
    else:
        base = DAILY_SALARY * 0.15
        if my_urgent:
            base = DAILY_SALARY * 0.35

    if urgent_count >= max(1, len(alive) // 2):
        base += 8.0

    if day >= 8 and hp > 4 and not my_urgent:
        base -= 6.0

    if budget < DAILY_SALARY:
        base = min(base, budget * 0.7)

    bid = max(0.0, min(budget, base))
    return bid
"""
