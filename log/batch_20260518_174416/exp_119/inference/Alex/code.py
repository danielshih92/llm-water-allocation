# ============================================================
# Experiment: exp_119
# Agent: Alex
# Source: exp_119
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

    if not alive:
        base = DAILY_SALARY * 0.22
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.55
        return max(0, min(budget, base))

    opp_count = len(alive)
    total_players = opp_count + 1
    expected_units = supply / float(WATER_REQ)
    scarcity = total_players - expected_units

    prev_bids = []
    prev_fail_bids = []
    desperate_opp = 0
    rich_opp = 0

    for opp in alive:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_opp += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
            status = prev.get('status')
            err = prev.get('error')
            if status not in ('won', 'success', 'alive_ok') or err:
                prev_fail_bids.append(bid)

    if hp <= 1:
        target = DAILY_SALARY * 0.98
    elif no_water >= 2:
        target = DAILY_SALARY * 0.95
    elif hp <= 2 or no_water >= 1:
        target = DAILY_SALARY * 0.82
    else:
        if scarcity <= 0:
            target = DAILY_SALARY * 0.28
        elif scarcity < 1:
            target = DAILY_SALARY * 0.42
        elif scarcity < 2:
            target = DAILY_SALARY * 0.56
        else:
            target = DAILY_SALARY * 0.68

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if hp > 2 and no_water == 0 and highest_prev >= DAILY_SALARY * 0.9:
            target = min(target, DAILY_SALARY * 0.34)
        else:
            target = max(target, min(DAILY_SALARY * 0.92, avg_prev + 2.0))
            if prev_fail_bids:
                target = max(target, min(DAILY_SALARY * 0.95, max(prev_fail_bids) + 3.0))

    if desperate_opp >= max(1, opp_count // 2):
        target += 4.0
    if rich_opp >= max(1, opp_count // 2):
        target += 3.0
    if supply >= 23:
        target -= 5.0
    elif supply <= 17:
        target += 5.0

    reserve_floor = 0.0
    if hp > 2 and no_water == 0:
        reserve_floor = budget * 0.55
    elif hp > 1:
        reserve_floor = budget * 0.35
    spend_cap = max(0.0, budget - reserve_floor)

    if hp <= 2 or no_water >= 1:
        spend_cap = budget

    bid = min(target, spend_cap if spend_cap > 0 else budget)
    if bid < 0:
        bid = 0
    if hp <= 1 or no_water >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    return max(0, min(budget, bid))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 55.0))

    prev_bids = []
    urgent_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        if opp.get('budget', 0) >= 300:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgent = hp <= 3 or no_water_days >= 1

    if my_urgent:
        target = max(92.0, highest_prev + 3.0)
        if supply <= 17:
            target += 10.0
        if urgent_count >= 2:
            target += 8.0
        if rich_count >= 2:
            target += 5.0
        return float(min(budget, target))

    if hp >= 8 and no_water_days == 0:
        if highest_prev >= 120.0 or (avg_prev >= 105.0 and supply <= 18):
            return float(min(budget, 12.0 + 6.0 * (1.0 - scarcity)))
        base = 26.0 + 10.0 * scarcity
        if day >= 8:
            base += 6.0
        return float(min(budget, base))

    target = 40.0 + 18.0 * scarcity
    if highest_prev > 0:
        target = max(target, min(highest_prev + 1.5, 88.0))
    if avg_prev >= 100.0:
        target -= 8.0
    if urgent_count >= 2 and supply <= 18:
        target += 8.0
    if hp <= 5:
        target += 10.0
    if no_water_days >= 1:
        target += 12.0
    if day >= 8 and hp <= 6:
        target += 8.0

    if target < 0:
        target = 0.0
    return float(min(budget, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    urgent_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 120 and opp.get('budget', 0) >= 300:
                    rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    danger = 0
    if hp <= 2:
        danger += 4
    elif hp <= 4:
        danger += 2
    if no_water_days >= 2:
        danger += 4
    elif no_water_days >= 1:
        danger += 2
    if tight_supply:
        danger += 2
    elif loose_supply:
        danger -= 1
    if urgent_opponents >= 2:
        danger += 1

    if danger >= 7:
        bid = max(78.0, highest_prev + 2.0)
    elif danger >= 5:
        bid = max(58.0, min(92.0, avg_prev * 0.55 + 8.0))
    elif danger >= 3:
        if rich_aggressive >= 1 and highest_prev >= 120:
            bid = 22.0 if loose_supply else 31.0
        else:
            bid = max(28.0, min(52.0, avg_prev * 0.45 + 6.0))
    else:
        if rich_aggressive >= 1 or highest_prev >= 110:
            bid = 12.0 if loose_supply else 18.0
        else:
            bid = 20.0 if not tight_supply else 26.0

    if day >= 8:
        bid += 6.0
    if hp <= 3:
        bid += 8.0
    if no_water_days >= 2:
        bid += 10.0

    reserve = 0.0
    if day <= 7:
        reserve = 35.0
    elif day <= 9:
        reserve = 15.0

    affordable = max(0.0, budget - reserve)
    if affordable <= 0:
        affordable = budget

    bid = min(bid, affordable)
    bid = min(bid, budget)
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
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    opp_req_sum = 0
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        opp_req_sum += opp.get('water_requirement', WATER_REQ)
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    total_demand_est = WATER_REQ + opp_req_sum
    scarcity = total_demand_est / max(1.0, float(supply))

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 8.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(DAILY_SALARY * 0.72, highest_prev + 3.0)
    else:
        if scarcity >= 2.2:
            bid = max(DAILY_SALARY * 0.68, highest_prev + 2.0)
        elif scarcity >= 1.8:
            bid = max(DAILY_SALARY * 0.58, avg_prev + 2.0)
        else:
            bid = DAILY_SALARY * 0.42

    if urgent_opp > 0:
        bid += 6.0
    if rich_opp >= 2:
        bid += 4.0

    if float(supply) >= 23.0 and hp >= 5 and no_water_days == 0:
        bid *= 0.82
    elif float(supply) <= 17.0:
        bid *= 1.12

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.92)
    else:
        reserve = max(DAILY_SALARY * 1.2, budget * 0.18)
        bid = min(bid, max(0.0, budget - reserve))

    if hp >= 7 and no_water_days == 0 and highest_prev >= 150 and float(supply) >= 20.0:
        bid = min(bid, DAILY_SALARY * 0.35)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 150:
                rich_aggressive += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY_PLACEHOLDER := 25)
    if supply <= 16:
        supply_tier = 'tight'
    elif supply >= 22:
        supply_tier = 'loose'
    else:
        supply_tier = 'mid'

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

    if supply_tier == 'tight':
        urgency += 2
    elif supply_tier == 'mid':
        urgency += 1

    if day >= 8:
        urgency += 1

    if highest_prev >= 150:
        market = 'very_high'
    elif highest_prev >= 100:
        market = 'high'
    elif highest_prev >= 55:
        market = 'medium'
    else:
        market = 'low'

    if urgency >= 6:
        bid = max(95.0, highest_prev + 3.0)
    elif urgency >= 4:
        if market == 'very_high':
            bid = 88.0 if supply_tier != 'tight' else 112.0
        elif market == 'high':
            bid = highest_prev + 2.0
        elif market == 'medium':
            bid = max(62.0, highest_prev + 1.5)
        else:
            bid = 54.0
    elif urgency >= 2:
        if supply_tier == 'loose':
            bid = 28.0 if market in ('high', 'very_high') else 36.0
        elif supply_tier == 'mid':
            if market == 'very_high':
                bid = 34.0
            elif market == 'high':
                bid = 48.0
            elif market == 'medium':
                bid = max(40.0, avg_prev * 0.9)
            else:
                bid = 42.0
        else:
            if market == 'very_high':
                bid = 60.0
            elif market == 'high':
                bid = 72.0
            elif market == 'medium':
                bid = highest_prev + 1.0
            else:
                bid = 50.0
    else:
        if supply_tier == 'loose':
            bid = 18.0
        elif supply_tier == 'mid':
            bid = 24.0 if market in ('high', 'very_high') else 30.0
        else:
            bid = 34.0 if market in ('high', 'very_high') else 38.0

    if rich_aggressive >= 2 and urgency <= 3:
        bid *= 0.9
    if desperate_count >= 2 and supply_tier == 'tight':
        bid += 8.0

    if budget < DAILY_SALARY:
        bid = min(bid, max(12.0, budget * 0.72))
    elif budget < 140:
        bid = min(bid, budget * 0.82)
    else:
        bid = min(bid, budget * 0.9)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 105.0))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    guaranteed_units = int(supply // WATER_REQ)
    scarcity = guaranteed_units <= 1

    prev_bids = []
    threat_scores = []
    rich_alive = 0
    for agent_id, opp in alive:
        obudget = opp.get('budget', 0)
        ohp = opp.get('hp', 0)
        onw = opp.get('no_water_days', 0)
        if obudget >= 80:
            rich_alive += 1

        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        else:
            bid = 0.0

        score = float(bid)
        if ohp <= 3:
            score += 18.0
        elif ohp <= 5:
            score += 8.0
        if onw >= 1:
            score += 10.0
        if obudget < 40:
            score -= 8.0
        elif obudget > 140:
            score += 6.0
        threat_scores.append(score)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_scores) if threat_scores else 0.0

    emergency = hp <= 3 or no_water >= 1
    very_safe = hp >= 8 and no_water == 0

    if emergency:
        if scarcity:
            bid = max(95.0, highest_prev + 6.0, highest_threat + 2.0)
        else:
            bid = max(78.0, highest_prev + 3.0)
    else:
        if scarcity:
            if very_safe and rich_alive >= 2 and highest_prev >= 95.0:
                bid = 44.0
            else:
                bid = max(72.0, min(108.0, highest_prev + 2.5, highest_threat + 1.5))
        else:
            if very_safe:
                bid = max(28.0, min(62.0, highest_prev * 0.72 + 3.0))
            else:
                bid = max(48.0, min(82.0, highest_prev * 0.82 + 4.0))

    if day >= 8:
        bid += 6.0
    if hp <= 2:
        bid += 12.0
    if budget < 90:
        bid = min(bid, budget * 0.72)
    elif budget < 140:
        bid = min(bid, budget * 0.82)

    bid = max(0.0, min(float(budget), float(bid)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    desperate_prev.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    slots = int(supply / WATER_REQ)
    contested = slots < (len(alive) + 1)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    desperate_high = max(desperate_prev) if desperate_prev else 0.0

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

    affordable_cap = min(float(budget), max(0.0, float(budget) * 0.42 + DAILY_SALARY * 0.35))

    if urgency >= 5:
        base = max(95.0, highest_prev + 4.0, desperate_high + 3.0)
        return float(min(budget, base))

    if urgency >= 3:
        if highest_prev >= 150.0:
            bid = 82.0
        else:
            bid = max(72.0, min(108.0, highest_prev + 2.5))
        return float(min(budget, bid))

    if not contested:
        if highest_prev > 0:
            bid = min(46.0, highest_prev * 0.72 + 1.0)
        else:
            bid = 28.0
        return float(min(budget, bid))

    if highest_prev >= 155.0:
        bid = 24.0 if hp >= 6 and no_water == 0 else 76.0
        return float(min(budget, bid))

    if highest_prev >= 110.0:
        bid = 38.0 if hp >= 7 and no_water == 0 else 74.0
        return float(min(budget, bid))

    if highest_prev >= 70.0:
        bid = max(52.0, min(78.0, highest_prev + 1.5))
        return float(min(budget, bid))

    if desperate_high > 0 and desperate_high < 90.0:
        bid = max(58.0, desperate_high + 2.0)
        return float(min(budget, min(bid, affordable_cap))))

    if day >= 8:
        bid = 62.0
    elif day >= 5:
        bid = 56.0
    else:
        bid = 49.0

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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if bid >= 100:
                    dangerous_prev.append(bid)

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = [b for b in prev_bids if b < 100]
    highest_moderate = max(moderate_prev) if moderate_prev else 0.0

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

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        bid = 128.0 if dangerous_prev else max(72.0, highest_moderate + 6.0)
    elif urgency >= 4:
        if dangerous_prev:
            bid = 96.0
        else:
            bid = max(54.0, highest_moderate + 3.0)
    elif urgency >= 2:
        if supply_loose:
            bid = 24.0
        else:
            bid = 38.0 if highest_moderate < 35 else min(58.0, highest_moderate + 2.0)
    else:
        if supply_loose:
            bid = 12.0
        else:
            bid = 20.0 if highest_moderate < 25 else 28.0

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * (10 - day) * 0.18
    max_affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_prev = 0.0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if bid > strong_prev:
                    strong_prev = bid

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return max(0.0, min(budget, DAILY_SALARY * 0.75))
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    total_players = 1 + len(alive_opponents)
    expected_share = float(supply) / float(total_players)
    scarce = expected_share < WATER_REQ
    very_scarce = float(supply) <= 16.0
    ample = float(supply) >= 22.0

    emergency = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if strong_prev <= 0:
        strong_prev = DAILY_SALARY * 0.8

    if emergency:
        bid = max(DAILY_SALARY * 1.45, strong_prev + 3.0)
    elif very_scarce:
        bid = max(DAILY_SALARY * 1.2, strong_prev + 2.0)
    elif scarce:
        bid = max(DAILY_SALARY * 0.95, strong_prev + 1.5)
    elif ample and hp >= 7 and no_water_days == 0:
        bid = DAILY_SALARY * 0.38
    elif pressured:
        bid = max(DAILY_SALARY * 0.82, strong_prev * 0.9)
    else:
        bid = max(DAILY_SALARY * 0.55, strong_prev * 0.72)

    if budget < DAILY_SALARY * 0.6:
        bid = min(bid, budget)
    else:
        reserve_floor = DAILY_SALARY * max(0, 9 - int(day_context['day'])) * 0.18
        if budget - bid < reserve_floor:
            bid = max(0.0, budget - reserve_floor)

    if emergency and budget > 0:
        bid = max(bid, min(budget, strong_prev + 1.0))

    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    strong_prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > DAILY_SALARY * 2:
                    strong_prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    scarcity = (25.0 - supply) / 10.0
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    elif hp <= 6:
        urgency += 0.2

    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.45

    if day >= 8:
        urgency += 0.15

    pressure_bid = 0.0
    if strong_prev_bids:
        pressure_bid = max(strong_prev_bids)
    elif prev_bids:
        pressure_bid = max(prev_bids)

    if pressure_bid >= 120:
        if urgency >= 1.4:
            bid = 92.0 + 10.0 * scarcity
        elif urgency >= 0.7:
            bid = 36.0 + 10.0 * scarcity
        else:
            bid = 12.0 + 6.0 * scarcity
    elif pressure_bid >= 70:
        if urgency >= 1.2:
            bid = min(88.0, pressure_bid + 2.0)
        elif urgency >= 0.5:
            bid = 48.0 + 12.0 * scarcity
        else:
            bid = 20.0 + 8.0 * scarcity
    elif pressure_bid > 0:
        target = pressure_bid + 1.25
        floor_bid = 24.0 + 18.0 * scarcity + 12.0 * urgency
        bid = max(target, floor_bid)
    else:
        bid = 22.0 + 16.0 * scarcity + 12.0 * urgency

    if supply >= 23:
        bid *= 0.72
    elif supply >= 20:
        bid *= 0.84
    elif supply <= 16:
        bid *= 1.18

    reserve = 0.0
    if hp > 4 and no_water == 0:
        reserve = DAILY_SALARY * 0.35
    elif hp > 2:
        reserve = DAILY_SALARY * 0.2

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 1.5:
        max_affordable = budget

    bid = min(bid, max_affordable)

    if urgency >= 1.2:
        bid = max(bid, min(budget, 55.0 + 12.0 * scarcity))
    elif hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, 62.0))

    bid = max(0.0, min(budget, bid))
    return float(round(bid, 2))
"""
