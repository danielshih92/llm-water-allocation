# ============================================================
# Experiment: exp_112
# Agent: Alex
# Source: exp_112
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 62.0)
        return min(budget, 24.0)

    prev_bids = []
    desperate_count = 0
    weak_count = 0
    error_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('hp', 0) <= 4:
            weak_count += 1
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('error'):
            error_count += 1
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
        status = prev.get('status')
        if status in ('failed', 'error', 'dead'):
            error_count += 1

    if hp <= 1:
        base = 68.0
    elif hp <= 2 or no_water_days >= 2:
        base = 63.0
    elif hp <= 4 or no_water_days >= 1:
        base = 49.0
    else:
        base = 34.0

    if supply >= 22:
        base -= 6.0
    elif supply <= 17:
        base += 7.0

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if hp <= 2 or no_water_days >= 2:
            target = highest_prev + 2.0
            base = max(base, target)
        else:
            if highest_prev >= 62.0:
                base = min(base, 28.0 if hp >= 5 else 45.0)
            elif avg_prev >= 45.0:
                base = max(base, avg_prev + 1.5)
            else:
                base = max(base, highest_prev + 1.0)

    if desperate_count >= 2:
        base += 6.0
    elif desperate_count == 0 and weak_count >= 1 and hp >= 5:
        base -= 4.0

    if error_count >= 1:
        base -= 3.0

    if day >= 8:
        if hp >= 5 and no_water_days == 0:
            base -= 3.0
        else:
            base += 4.0

    base = max(0.0, min(base, budget))

    if budget < 25.0:
        return min(budget, max(base, budget * 0.9))
    return base
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    weak_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                weak_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 100 and opp.get('budget', 0) >= 300:
                    rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, 20.0))

    high_pressure = max(prev_bids) if prev_bids else 0.0
    avg_pressure = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
    elif supply <= 19:
        urgency += 1

    if day >= 8:
        urgency += 1

    if rich_aggressive >= 2 and urgency <= 2:
        base_bid = 8.0 if supply >= 20 else 12.0
    else:
        if urgency >= 6:
            base_bid = 125.0
        elif urgency >= 4:
            base_bid = 82.0
        elif urgency >= 2:
            base_bid = 42.0
        else:
            base_bid = 18.0

        if high_pressure > 0:
            if urgency >= 4:
                target = min(high_pressure + 3.0, 140.0)
                base_bid = max(base_bid, target)
            elif urgency <= 1 and high_pressure >= 100:
                base_bid = min(base_bid, 15.0)
            else:
                target = min(avg_pressure * 0.55 + 6.0, 65.0)
                base_bid = max(base_bid, target)

    if weak_opponents >= 2 and urgency <= 2:
        base_bid *= 0.8

    reserve = 0.0
    if day <= 3:
        reserve = 140.0
    elif day <= 7:
        reserve = 70.0

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 5:
        max_affordable = budget

    bid = min(base_bid, max_affordable)

    if urgency >= 5:
        bid = max(bid, min(budget, 90.0))
    elif urgency >= 3:
        bid = max(bid, min(budget, 45.0))

    if budget < 25:
        bid = budget

    if bid < 0:
        bid = 0.0

    return float(min(budget, bid))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if no_water_days >= 1 or hp <= 3:
            safe_bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, safe_bid))

    total_agents = 1 + len(alive)
    total_demand_units = WATER_REQ * total_agents
    scarcity = total_demand_units / max(1.0, supply)

    prev_bids = []
    prev_high = 0.0
    prev_avg = 0.0
    aggressive_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > prev_high:
                prev_high = float(bid)
            if float(bid) >= DAILY_SALARY * 1.2:
                aggressive_count += 1
    if prev_bids:
        prev_avg = sum(prev_bids) / len(prev_bids)

    low_supply = supply <= 17
    high_supply = supply >= 22
    urgent = (no_water_days >= 1) or (hp <= 3)
    very_urgent = (no_water_days >= 2) or (hp <= 2)

    base = DAILY_SALARY * 0.52

    if scarcity >= 3.0:
        base = DAILY_SALARY * 1.05
    elif scarcity >= 2.5:
        base = DAILY_SALARY * 0.88
    elif scarcity >= 2.0:
        base = DAILY_SALARY * 0.72
    else:
        base = DAILY_SALARY * 0.48

    if low_supply:
        base += 10.0
    if high_supply:
        base -= 8.0

    if prev_bids:
        if prev_high >= 120:
            if urgent:
                base = max(base, prev_avg + 3.0)
            else:
                base = min(base, DAILY_SALARY * 0.45)
        elif prev_high >= 90:
            base = max(base, min(prev_high + 2.0, DAILY_SALARY * 1.15))
        else:
            base = max(base, prev_high + 1.5)

    if aggressive_count >= 1 and not urgent:
        base -= 6.0

    if urgent:
        base = max(base, DAILY_SALARY * 0.92)
    if very_urgent:
        base = max(base, DAILY_SALARY * 1.18)

    if day >= 8:
        base += 8.0
    if day >= 9 and hp <= 5:
        base += 10.0

    reserve_floor = 0.0
    remaining_days = max(0, 10 - int(day))
    if remaining_days > 0 and not urgent:
        reserve_floor = remaining_days * DAILY_SALARY * 0.18

    max_affordable = max(0.0, budget - reserve_floor)
    if urgent:
        max_affordable = budget

    bid = min(base, max_affordable)

    if bid < 0:
        bid = 0.0
    if urgent and bid < DAILY_SALARY * 0.75:
        bid = min(budget, DAILY_SALARY * 0.75)

    return float(round(min(budget, bid), 2))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
                if prev['bid'] >= 120 and opp.get('budget', 0) > 100:
                    rich_aggressive += 1

    if not alive:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water >= 2:
        urgency += 4
    elif no_water >= 1:
        urgency += 2
    if tight_supply:
        urgency += 2
    if desperate_count >= 2:
        urgency += 1

    if urgency >= 7:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
    elif urgency >= 5:
        bid = max(0.78 * DAILY_SALARY, min(highest_prev + 1.5, 0.95 * DAILY_SALARY))
    elif urgency >= 3:
        if highest_prev >= 150:
            bid = 46.0
        else:
            bid = max(38.0, min(highest_prev + 1.0, 58.0))
    else:
        if highest_prev >= 150:
            bid = 24.0 if loose_supply else 31.0
        elif highest_prev >= 110:
            bid = 30.0 if loose_supply else 37.0
        elif highest_prev >= 70:
            bid = 36.0 if loose_supply else 43.0
        else:
            bid = max(32.0, avg_prev * 0.75 if avg_prev > 0 else 35.0)

    if rich_aggressive >= 2 and urgency <= 3:
        bid *= 0.9

    if day >= 8:
        if hp <= 4 or no_water >= 1:
            bid = max(bid, 0.82 * DAILY_SALARY)
        else:
            bid = min(bid, 0.75 * DAILY_SALARY)

    if budget < bid:
        if hp <= 2 or no_water >= 2:
            bid = budget
        else:
            bid = min(budget, max(0.0, bid * 0.85))

    if budget <= 0:
        return 0.0

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    urgent_opp_bids = []
    rich_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            bid = None
            if isinstance(prev, dict):
                bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    urgent_opp_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 18.0 if hp > 3 else 35.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else highest_prev

    total_players = 1 + len(alive_opps)
    winners_possible = int(supply // WATER_REQ)
    if winners_possible < 0:
        winners_possible = 0

    my_urgent = hp <= 3 or no_water_days >= 1
    severe = winners_possible <= 1
    moderate = winners_possible == 2

    if my_urgent:
        target = max(72.0, urgent_prev + 2.0)
        if severe:
            target = max(target, highest_prev + 3.0, 92.0)
        elif moderate:
            target = max(target, highest_prev + 1.5, 78.0)
        return float(min(budget, target))

    if severe:
        if highest_prev >= 110:
            target = 24.0 if hp >= 6 else 88.0
        elif highest_prev >= 90:
            target = 32.0 if hp >= 7 else highest_prev + 2.0
        else:
            target = max(55.0, highest_prev + 2.0)
        if rich_count >= 2 and hp >= 6:
            target = min(target, 28.0)
        return float(min(budget, target))

    if moderate:
        if highest_prev >= 115:
            target = 30.0 if hp >= 6 else 82.0
        elif highest_prev >= 95:
            target = 44.0 if hp >= 6 else 74.0
        else:
            target = max(48.0, highest_prev * 0.72)
        if day >= 8 and hp <= 5:
            target = max(target, 76.0)
        return float(min(budget, target))

    target = 18.0
    if hp <= 4:
        target = 42.0
    elif highest_prev < 60 and day >= 7:
        target = 28.0
    return float(min(budget, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

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
                req = float(opp.get('water_requirement', WATER_REQ))
                sal = float(opp.get('daily_salary', DAILY_SALARY))
                b_ratio = float(bid) / max(1.0, sal)
                need_ratio = req / float(WATER_REQ)
                pressure_scores.append(b_ratio * need_ratio)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.7
    max_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.9
    avg_pressure = sum(pressure_scores) / len(pressure_scores) if pressure_scores else 1.0

    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    urgency = 0.0
    if hp <= 2:
        urgency += 1.2
    elif hp <= 4:
        urgency += 0.7
    elif hp <= 6:
        urgency += 0.3

    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.5

    if day >= 8:
        urgency += 0.2

    market_anchor = 0.55 * avg_prev + 0.25 * max_prev + 18.0 * avg_pressure * supply_tightness

    if urgency >= 1.8:
        bid = max(market_anchor + 18.0, DAILY_SALARY * 1.35)
    elif urgency >= 1.0:
        bid = max(market_anchor + 8.0, DAILY_SALARY * 0.95)
    elif supply <= 17:
        bid = max(market_anchor, DAILY_SALARY * 0.72)
    elif supply >= 23 and hp >= 7 and no_water == 0:
        bid = min(avg_prev * 0.72, DAILY_SALARY * 0.52)
    else:
        bid = max(market_anchor * 0.9, DAILY_SALARY * 0.58)

    if budget < DAILY_SALARY * 2 and urgency < 1.0:
        bid = min(bid, DAILY_SALARY * 0.62)

    if hp >= 8 and no_water == 0 and supply >= 22:
        bid = min(bid, DAILY_SALARY * 0.5)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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
    prev_bids = []
    urgent_opps = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opps += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 0.85 * DAILY_SALARY and opp.get('budget', 0) > 2 * DAILY_SALARY:
                    rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    critical_self = hp <= 3 or no_water_days >= 2
    very_critical_self = hp <= 2 or no_water_days >= 3

    if very_critical_self:
        bid = max(0.92 * DAILY_SALARY, highest_prev_bid + 2.5)
        return float(min(budget, bid))

    if critical_self:
        bid = max(0.78 * DAILY_SALARY, avg_prev_bid + 2.0, 42.0 + 18.0 * scarcity)
        return float(min(budget, bid))

    if supply >= 22 and hp >= 7 and no_water_days == 0:
        bid = 12.0 if rich_aggressive > 0 else 18.0
        return float(min(budget, bid))

    if supply <= 17:
        bid = max(36.0 + 18.0 * scarcity, avg_prev_bid + 1.5)
        if urgent_opps >= 2:
            bid += 6.0
        return float(min(budget, bid))

    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        bid = 16.0 + 10.0 * scarcity
        if hp <= 5:
            bid = max(bid, 34.0)
        return float(min(budget, bid))

    if highest_prev_bid >= 45.0:
        bid = max(28.0 + 10.0 * scarcity, highest_prev_bid - 6.0)
        return float(min(budget, bid))

    bid = 24.0 + 12.0 * scarcity
    if day >= 8 and hp >= 6:
        bid -= 4.0
    if budget < 2 * DAILY_SALARY:
        bid -= 3.0
    if bid < 8.0:
        bid = 8.0
    return float(min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    strong_opp_count = 0
    desperate_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 6:
                strong_opp_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / WATER_REQ
    tight_supply = units < 1.55
    medium_supply = units < 1.8
    abundant_supply = units >= 1.8

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if day >= 8:
        urgency += 1

    if urgency >= 6:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 2.0)
    elif urgency >= 4:
        bid = max(0.78 * DAILY_SALARY, min(highest_prev + 1.0, 0.95 * DAILY_SALARY))
    else:
        if abundant_supply:
            bid = 0.24 * DAILY_SALARY
            if highest_prev > 0 and highest_prev < 0.55 * DAILY_SALARY:
                bid = max(bid, highest_prev + 0.5)
        elif medium_supply:
            bid = 0.42 * DAILY_SALARY
            if highest_prev > 0:
                if highest_prev >= 0.9 * DAILY_SALARY and hp > 4 and no_water_days == 0:
                    bid = 0.26 * DAILY_SALARY
                else:
                    bid = max(bid, min(highest_prev + 1.0, 0.74 * DAILY_SALARY))
        else:
            bid = 0.58 * DAILY_SALARY
            if highest_prev > 0:
                if highest_prev >= 1.4 * DAILY_SALARY and hp > 5 and no_water_days == 0:
                    bid = 0.30 * DAILY_SALARY
                elif highest_prev >= 0.95 * DAILY_SALARY and hp > 4 and no_water_days == 0:
                    bid = 0.40 * DAILY_SALARY
                else:
                    bid = max(bid, min(highest_prev + 1.5, 0.88 * DAILY_SALARY))

    if strong_opp_count >= 2 and urgency <= 2 and highest_prev >= 1.2 * DAILY_SALARY:
        bid = min(bid, 0.34 * DAILY_SALARY)

    if desperate_opp_count >= 1 and tight_supply and urgency >= 2:
        bid = max(bid, min(0.9 * DAILY_SALARY, highest_prev + 2.0))

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = DAILY_SALARY * max(0, 10 - day) * 0.18
    max_affordable = max(0.0, budget - reserve)
    if urgency >= 4:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
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
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 700:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive:
        return float(min(budget, 8.0))

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0

    supply_ratio = float(supply) / float(WATER_REQ)
    contested = supply_ratio < 1.45
    abundant = supply_ratio >= 1.75

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

    if abundant and urgency == 0:
        bid = 10.0
    elif abundant:
        bid = 22.0 + 8.0 * urgency
    elif contested:
        bid = 34.0 + 10.0 * urgency
    else:
        bid = 22.0 + 9.0 * urgency

    if prev_bids:
        if max_prev >= 140:
            if urgency >= 4:
                bid = max(bid, min(0.92 * DAILY_SALARY, max_prev * 0.72))
            elif urgency >= 2:
                bid = max(bid, 48.0)
            else:
                bid = min(bid, 18.0)
        elif max_prev >= 100:
            if urgency >= 3:
                bid = max(bid, min(0.88 * DAILY_SALARY, avg_prev * 0.58))
            elif contested:
                bid = max(bid, 30.0)
            else:
                bid = min(bid, 16.0)
        else:
            target = avg_prev + 2.5
            if urgency >= 2:
                bid = max(bid, target)
            else:
                bid = max(bid, min(28.0, target))

    if desperate_count >= 2 and contested:
        bid += 8.0
    elif desperate_count == 0 and abundant:
        bid -= 4.0

    if rich_count >= 2 and urgency <= 1:
        bid -= 3.0

    if day >= 8:
        if hp >= 6 and budget < 160:
            bid = min(bid, 20.0)
        elif urgency >= 3:
            bid += 6.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = max(0.0, budget - DAILY_SALARY * (10 - day) * 0.55)
        bid = min(bid, max(18.0, reserve_floor + 20.0))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 62.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, 46.0)

    bid = max(0.0, bid)
    bid = min(float(budget), float(bid))
    return float(round(bid, 2))
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

    supply = day_context['supply']
    day = day_context['day']
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
        return min(budget, 20.0)

    pressure_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            pressure_bids.append(float(bid))
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            urgent_opp += 1
        if opp.get('budget', 0) >= budget:
            rich_opp += 1

    if pressure_bids:
        highest_prev = max(pressure_bids)
        avg_prev = sum(pressure_bids) / len(pressure_bids)
    else:
        highest_prev = DAILY_SALARY * 0.6
        avg_prev = DAILY_SALARY * 0.5

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.6
    if no_water_days >= 2:
        danger += 1.0
    elif no_water_days >= 1:
        danger += 0.45

    market_pressure = 0.35 * scarcity
    market_pressure += 0.25 if highest_prev >= 180 else 0.0
    market_pressure += 0.15 if avg_prev >= 140 else 0.0
    market_pressure += min(0.25, 0.08 * urgent_opp)

    if day >= 8:
        market_pressure += 0.1

    if danger >= 1.4:
        target = max(highest_prev + 3.0, DAILY_SALARY * 1.35)
    elif danger >= 0.8:
        target = max(avg_prev + 4.0, DAILY_SALARY * (0.95 + 0.35 * scarcity))
    else:
        if supply >= 22 and urgent_opp == 0:
            target = DAILY_SALARY * 0.22
        elif market_pressure >= 0.75:
            target = max(avg_prev * 0.92, DAILY_SALARY * 0.9)
        elif market_pressure >= 0.45:
            target = max(DAILY_SALARY * 0.58, avg_prev * 0.72)
        else:
            target = DAILY_SALARY * 0.38

    if rich_opp >= 2 and danger < 0.8:
        target *= 0.92

    if hp >= 8 and no_water_days == 0 and supply >= 21:
        target *= 0.88

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve = DAILY_SALARY * 0.6

    affordable = max(0.0, budget - reserve)
    if danger >= 0.8:
        affordable = budget

    bid = min(target, affordable if affordable > 0 else budget)

    if danger >= 1.4 and bid < DAILY_SALARY * 0.95:
        bid = min(budget, DAILY_SALARY * 0.95)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
"""
