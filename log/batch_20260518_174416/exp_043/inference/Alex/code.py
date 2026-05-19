# ============================================================
# Experiment: exp_043
# Agent: Alex
# Source: exp_043
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

    if not alive:
        safe = min(budget, DAILY_SALARY * 0.35)
        return max(0, safe)

    total_players = 1 + len(alive)
    expected_competitors_served = max(1, int(supply // WATER_REQ))
    scarcity = total_players - expected_competitors_served

    prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 1.2:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

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

    if scarcity >= 2:
        urgency += 2
    elif scarcity >= 1:
        urgency += 1

    if desperate_opp >= max(1, len(alive) // 2):
        urgency += 1

    if budget < DAILY_SALARY:
        urgency -= 1

    if urgency <= 0:
        bid = max(8, DAILY_SALARY * 0.22)
    elif urgency == 1:
        bid = max(14, DAILY_SALARY * 0.32)
    elif urgency == 2:
        bid = max(22, DAILY_SALARY * 0.48)
    elif urgency == 3:
        bid = max(32, DAILY_SALARY * 0.62)
    elif urgency == 4:
        bid = max(42, DAILY_SALARY * 0.78)
    else:
        bid = max(52, DAILY_SALARY * 0.93)

    if highest_prev > 0:
        if scarcity >= 1 or urgency >= 3:
            target = highest_prev + 2
            if target > bid:
                bid = target
        else:
            soft_target = avg_prev + 1
            if soft_target > bid * 0.8:
                bid = max(bid, soft_target)

    if supply >= WATER_REQ * total_players:
        bid = min(bid, DAILY_SALARY * 0.4)
    elif supply <= WATER_REQ * max(1, total_players - 2):
        bid += 6

    if rich_opp >= len(alive) and urgency <= 1:
        bid = min(bid, DAILY_SALARY * 0.28)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, DAILY_SALARY * 0.9)

    bid = min(bid, budget)
    if bid < 0:
        bid = 0
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_pressure = 0.0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > budget:
                    rich_pressure = max(rich_pressure, float(bid))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units_today = int(supply // WATER_REQ)
    contested = units_today <= 1

    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1

    if urgent:
        target = max(62.0, highest_prev + 2.5)
        if contested:
            target = max(target, 74.0)
        return float(min(budget, target))

    if units_today >= 2:
        target = 26.0
        if highest_prev < 25:
            target = 18.0
        elif highest_prev < 50:
            target = 32.0
        return float(min(budget, target))

    if contested:
        if highest_prev >= 100:
            target = 8.0 if hp >= 7 and no_water == 0 else 68.0
        elif highest_prev >= 80:
            target = 12.0 if hp >= 8 and no_water == 0 else 66.0
        elif highest_prev >= 60:
            target = 20.0 if hp >= 7 else 64.0
        else:
            target = max(36.0, avg_prev + 3.0)

        if semi_urgent:
            target = max(target, 58.0)
        if rich_pressure >= 90 and hp >= 7 and no_water == 0:
            target = min(target, 15.0)
        return float(min(budget, target))

    target = 35.0
    return float(min(budget, target))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return max(0.0, float(bid))

    prev_bids = []
    cindy_prev = None
    rich_alive = 0
    urgent_opp = 0
    for opp in alive:
        if opp.get('budget', 0) > DAILY_SALARY * 2:
            rich_alive += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid')))
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            pass

    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('alive'):
        prev = opponents_status['Cindy'].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            cindy_prev = float(prev.get('bid'))

    highest_prev = max(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    survival = 0
    if hp <= 2 or no_water >= 2:
        survival = 3
    elif hp <= 4 or no_water >= 1:
        survival = 2
    elif hp <= 6:
        survival = 1

    base = DAILY_SALARY * 0.38
    if scarcity == 1:
        base = DAILY_SALARY * 0.52
    elif scarcity == 2:
        base = DAILY_SALARY * 0.68

    if survival == 1:
        base = max(base, DAILY_SALARY * 0.58)
    elif survival == 2:
        base = max(base, DAILY_SALARY * 0.82)
    elif survival == 3:
        base = max(base, DAILY_SALARY * 1.05)

    if highest_prev > 0:
        if highest_prev >= 135:
            if survival >= 2 or scarcity == 2:
                target = highest_prev + 2.0
            else:
                target = max(base, DAILY_SALARY * 0.42)
        elif highest_prev >= 105:
            if survival >= 2:
                target = highest_prev + 1.5
            elif scarcity >= 1:
                target = max(base, highest_prev * 0.78)
            else:
                target = max(base, DAILY_SALARY * 0.45)
        else:
            target = max(base, highest_prev + 2.0)
    else:
        target = base

    if cindy_prev is not None and cindy_prev >= 140 and survival < 2 and scarcity == 0:
        target = min(target, DAILY_SALARY * 0.42)

    if rich_alive >= 2 and scarcity >= 1:
        target += 6.0
    if urgent_opp >= 2 and scarcity >= 1:
        target += 4.0

    if day >= 8 and hp > 4 and no_water == 0 and supply >= 20:
        target = min(target, DAILY_SALARY * 0.36)

    hard_cap = budget
    if survival < 2:
        hard_cap = min(hard_cap, DAILY_SALARY * 1.25)
    else:
        hard_cap = min(hard_cap, DAILY_SALARY * 1.9)

    bid = min(target, hard_cap)
    if hp <= 1 or no_water >= 2:
        bid = min(budget, max(bid, highest_prev + 3.0 if highest_prev > 0 else DAILY_SALARY * 1.1))

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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive_bids = []
    normal_bids = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 100:
                    aggressive_bids.append(bid)
                else:
                    normal_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0:
        tightness = 0.0
    if tightness > 1:
        tightness = 1.0

    urgent = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    top_prev = max(prev_bids) if prev_bids else 0.0
    top_normal = max(normal_bids) if normal_bids else 0.0

    if urgent:
        target = max(88.0, top_normal + 4.0)
        if top_prev >= 110:
            target = max(target, 96.0)
        return float(min(budget, target))

    if pressured:
        if supply <= 17:
            target = max(84.0, top_normal + 2.5)
        elif supply <= 20:
            target = max(72.0, top_normal * 0.98 if top_normal > 0 else 72.0)
        else:
            target = 58.0
        return float(min(budget, target))

    if supply <= 16:
        target = max(86.0, top_normal + 3.0)
    elif supply <= 18:
        target = max(76.0, top_normal + 1.5)
    elif supply <= 21:
        target = max(61.0, min(74.0, top_normal * 0.9 if top_normal > 0 else 61.0))
    else:
        target = 42.0

    if len(aggressive_bids) >= 1 and supply >= 20 and hp >= 6:
        target = min(target, 55.0)

    if day >= 8 and hp >= 6:
        target = min(target, 68.0)

    reserve_floor = DAILY_SALARY * 1.2
    if budget < reserve_floor:
        target = min(target, max(28.0, budget * 0.55))

    return float(min(budget, max(0.0, target)))
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
    prev_bids = []
    aggressive_count = 0
    desperate_count = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 100:
                    aggressive_count += 1

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22
    critical = hp <= 3 or no_water_days >= 1
    very_safe = hp >= 8 and no_water_days == 0

    base = 0.0

    if critical:
        base = max(108.0, highest_prev + 3.0)
        if tight_supply:
            base += 8.0
    elif tight_supply:
        base = max(82.0, avg_prev * 0.82, highest_prev * 0.72)
        if aggressive_count >= 2:
            base += 8.0
        if desperate_count >= 1:
            base += 6.0
    elif loose_supply and very_safe:
        base = max(18.0, avg_prev * 0.22)
    else:
        base = max(42.0, avg_prev * 0.45, highest_prev * 0.38)
        if aggressive_count >= 2:
            base += 5.0

    days_left = max(0, 10 - int(day))
    reserve_target = days_left * 28.0
    affordable = budget
    if budget > reserve_target:
        affordable = max(0.0, budget - reserve_target * 0.35)

    if critical:
        affordable = budget

    bid = min(base, affordable, budget)

    if critical and bid < min(budget, 95.0):
        bid = min(budget, 95.0)
    if very_safe and loose_supply:
        bid = min(bid, 35.0)

    if bid < 0:
        bid = 0.0

    return float(bid)
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    est_competitors = 1
    if supply < WATER_REQ * 2:
        est_competitors = 2
    else:
        est_competitors = int(max(1, round(supply / float(WATER_REQ))))

    prev_bids = []
    threat_scores = []
    for oid, opp in alive:
        prev = opp.get('previous_trace') or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
        score = 0.0
        if opp.get('budget', 0) >= 500:
            score += 2.0
        if opp.get('hp', 0) >= 7:
            score += 1.0
        if pbid is not None:
            if pbid >= 130:
                score += 3.0
            elif pbid >= 80:
                score += 2.0
            elif pbid > 0:
                score += 1.0
        if opp.get('no_water_days', 0) >= 2:
            score += 2.0
        threat_scores.append(score)

    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    strong_opp = 0
    for s in threat_scores:
        if s >= 4.0:
            strong_opp += 1

    urgent = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1
    tight_supply = supply < WATER_REQ * 2
    abundant = supply >= WATER_REQ * 2

    if urgent:
        bid = max(138.0, high_prev + 3.0, DAILY_SALARY * 1.9)
    elif tight_supply and strong_opp >= 2:
        bid = max(136.0, high_prev + 2.0)
    elif tight_supply and strong_opp >= 1:
        bid = max(118.0, avg_prev + 4.0)
    elif pressured and strong_opp >= 2:
        bid = max(128.0, high_prev + 1.5)
    elif abundant and hp >= 7 and no_water_days == 0:
        bid = DAILY_SALARY * 0.45
    elif strong_opp >= 2:
        bid = max(92.0, avg_prev * 0.78)
    elif strong_opp == 1:
        bid = max(72.0, avg_prev * 0.7)
    else:
        bid = DAILY_SALARY * 0.55

    if day >= 8:
        if hp <= 5:
            bid = max(bid, 125.0)
        else:
            bid = max(bid, 85.0)

    reserve = 0.0
    if hp >= 6 and day <= 6:
        reserve = DAILY_SALARY * 1.2
    elif hp >= 4:
        reserve = DAILY_SALARY * 0.6

    max_affordable = max(0.0, budget - reserve)
    if urgent:
        max_affordable = budget

    bid = min(bid, max_affordable if max_affordable > 0 else budget)
    bid = min(bid, budget)
    bid = max(0.0, bid)

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

    alive = []
    prev_bids = []
    credible_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 120:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                status = prev.get('status')
                err = prev.get('error')
                if bid is not None:
                    prev_bids.append(bid)
                    if err in (None, '', False) and status != 'error':
                        credible_bids.append(bid)

    if not alive:
        return min(budget, 18.0)

    high_pressure = max(prev_bids) if prev_bids else 0.0
    credible_high = max(credible_bids) if credible_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if urgency >= 5:
        bid = max(95.0, credible_high + 3.0, high_pressure * 0.9)
        return min(budget, bid)

    if tight_supply and high_pressure >= 120 and urgency <= 2:
        return min(budget, 12.0)

    if ample_supply:
        if credible_high > 0:
            bid = min(credible_high + 2.5, 92.0)
        else:
            bid = 48.0
        if desperate_count >= 2:
            bid += 8.0
        return min(budget, bid)

    if high_pressure >= 150:
        if urgency >= 3:
            bid = 108.0
        else:
            bid = 20.0
        return min(budget, bid)

    if high_pressure >= 110:
        if urgency >= 3:
            bid = max(88.0, credible_high + 2.0)
        else:
            bid = 34.0
        return min(budget, bid)

    if credible_high > 0:
        bid = credible_high + 2.0
    elif avg_prev > 0:
        bid = avg_prev + 3.0
    else:
        bid = 52.0

    if rich_count >= 2 and urgency <= 2:
        bid -= 6.0
    if desperate_count >= 2:
        bid += 6.0
    if hp <= 4:
        bid += 10.0
    if no_water_days >= 1:
        bid += 8.0
    if day >= 8 and hp > 5 and budget < 120:
        bid -= 6.0

    if bid < 15.0:
        bid = 15.0
    return min(budget, bid)
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
    prev_bids = []
    rich_threats = 0
    urgent_opponents = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 500:
                rich_threats += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.75
    elif hp <= 4:
        danger += 0.45
    elif hp <= 6:
        danger += 0.2

    if no_water_days >= 2:
        danger += 0.8
    elif no_water_days >= 1:
        danger += 0.4

    late_game = 1.0 if day >= 8 else 0.0

    base = 18.0 + 28.0 * supply_pressure + 22.0 * danger + 8.0 * late_game

    if highest_prev >= 150:
        if hp >= 6 and no_water_days == 0 and supply >= 21:
            base = min(base, 16.0)
        else:
            base += 10.0 * supply_pressure + 6.0 * danger
    elif highest_prev >= 100:
        base = max(base, min(highest_prev * 0.42, 62.0))
    elif highest_prev > 0:
        base = max(base, min(highest_prev + 2.0, 58.0))
    else:
        base = max(base, 24.0)

    if rich_threats >= 2 and supply <= 18:
        base += 8.0
    if urgent_opponents >= 2 and supply <= 18:
        base += 5.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(base, 72.0 + 18.0 * supply_pressure)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(base, 48.0 + 14.0 * supply_pressure)
    else:
        bid = base

    soft_cap = budget
    if day <= 3:
        soft_cap = min(soft_cap, 95.0)
    elif day <= 6:
        soft_cap = min(soft_cap, 110.0)
    else:
        soft_cap = min(soft_cap, 130.0)

    if hp >= 7 and no_water_days == 0 and supply >= 22:
        soft_cap = min(soft_cap, 35.0)

    bid = min(bid, soft_cap)
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 0 and opp.get('hp', 0) > 0:
                    dangerous_prev_bids.append(float(bid))

    if not alive:
        return min(budget, 18.0)

    max_prev = max(prev_bids) if prev_bids else 0.0
    max_danger = max(dangerous_prev_bids) if dangerous_prev_bids else max_prev
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    critical = hp <= 3 or no_water >= 1
    very_critical = hp <= 2 or no_water >= 2
    scarce = supply <= 17
    ample = supply >= 22

    if very_critical:
        bid = max(72.0, max_danger + 2.0)
    elif critical and scarce:
        bid = max(62.0, max_danger + 1.5)
    elif scarce:
        if max_danger >= 100:
            bid = 44.0
        else:
            bid = max(38.0, avg_prev * 0.55)
    elif ample:
        if hp >= 6 and no_water == 0:
            bid = 16.0
        else:
            bid = 24.0
    else:
        if max_danger >= 110:
            bid = 26.0 if hp >= 5 and no_water == 0 else 58.0
        elif max_danger >= 80:
            bid = 34.0 if hp >= 5 and no_water == 0 else max(52.0, max_danger * 0.72)
        else:
            bid = max(30.0, max_danger + 1.2)

    if day >= 8:
        if hp >= 5 and no_water == 0:
            bid *= 0.9
        else:
            bid *= 1.05

    if budget <= 0:
        return 0.0

    floor_need = 0.0
    if very_critical:
        floor_need = 65.0
    elif critical:
        floor_need = 45.0

    bid = max(bid, floor_need)
    bid = min(float(budget), float(bid))
    if bid < 0:
        bid = 0.0
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_budgets = []
    urgent_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_budgets.append(float(opp.get('budget', 0.0)))
            if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 0)) <= 3:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0.0)))
                except Exception:
                    pass

    if not alive_opponents:
        return min(budget, 8.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    richest_opp = max(opp_budgets) if opp_budgets else 0.0

    my_urgent = no_water_days >= 1 or hp <= 3
    very_urgent = no_water_days >= 2 or hp <= 2
    tight_supply = supply <= 17.0
    ample_supply = supply >= 22.0

    if very_urgent:
        bid = max(95.0, highest_prev + 2.5)
        if tight_supply:
            bid += 20.0
        return max(0.0, min(budget, bid))

    if my_urgent:
        bid = max(72.0, avg_prev * 0.9, highest_prev * 0.8)
        if tight_supply:
            bid = max(bid, highest_prev + 1.5)
        return max(0.0, min(budget, bid))

    if ample_supply and hp >= 5 and no_water_days == 0:
        return max(0.0, min(budget, 6.0))

    if highest_prev >= 150.0:
        if tight_supply:
            bid = 58.0
        else:
            bid = 18.0
    elif highest_prev >= 110.0:
        if tight_supply:
            bid = 66.0
        else:
            bid = 22.0
    else:
        bid = max(20.0, min(55.0, avg_prev * 0.6 + 8.0))

    if urgent_opp_count >= 2 and not tight_supply:
        bid *= 0.8

    if richest_opp > budget * 2 and hp >= 5 and no_water_days == 0:
        bid *= 0.85

    if day >= 8 and hp >= 5 and no_water_days == 0:
        bid *= 0.9

    return max(0.0, min(budget, bid))
"""
