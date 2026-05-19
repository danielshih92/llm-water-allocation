# ============================================================
# Experiment: exp_019
# Agent: Alex
# Source: exp_019
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
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 20)

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    desperation = 0
    if hp <= 2:
        desperation = 3
    elif hp <= 4:
        desperation = 2
    elif no_water >= 1:
        desperation = 1

    base = DAILY_SALARY * 0.42
    if scarcity == 1:
        base = DAILY_SALARY * 0.55
    elif scarcity == 2:
        base = DAILY_SALARY * 0.72

    if desperation == 1:
        base = max(base, DAILY_SALARY * 0.62)
    elif desperation == 2:
        base = max(base, DAILY_SALARY * 0.82)
    elif desperation == 3:
        base = max(base, DAILY_SALARY * 0.96)

    if prev_bids:
        high_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if desperation >= 2:
            target = high_prev + 2.0
        elif scarcity == 2:
            target = max(avg_prev + 1.5, high_prev * 0.92)
        else:
            target = avg_prev + 1.0
        base = max(base, target)

    if urgent_opp >= max(1, len(alive_opponents) // 2):
        base += 3
    if rich_opp >= max(1, len(alive_opponents) // 2) and scarcity >= 1:
        base += 4

    if day >= 8 and hp > 4 and no_water == 0 and scarcity == 0:
        base = min(base, DAILY_SALARY * 0.38)

    if budget < DAILY_SALARY:
        base = min(base, budget * 0.75 + 2)

    bid = max(0, min(budget, round(base, 2)))
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_budgets = []
    urgent_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0
    max_opp_budget = max(opp_budgets) if opp_budgets else 0

    winners_est = int(supply // WATER_REQ)
    if winners_est < 1:
        winners_est = 1

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water >= 1:
        danger += 2
    if winners_est == 1:
        danger += 1
    if urgent_opp >= 2:
        danger += 1

    if danger >= 4:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2)
    elif danger >= 2:
        bid = max(DAILY_SALARY * 0.72, avg_prev * 0.72, highest_prev * 0.62)
    else:
        if winners_est >= 2:
            bid = max(DAILY_SALARY * 0.42, avg_prev * 0.48)
        else:
            bid = max(DAILY_SALARY * 0.58, avg_prev * 0.58, highest_prev * 0.52)

    if highest_prev >= 105 and danger <= 1 and winners_est >= 2:
        bid = min(bid, DAILY_SALARY * 0.5)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, highest_prev + 3, DAILY_SALARY * 0.98)

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, max(0.0, budget * 0.82))
    elif budget > max_opp_budget + DAILY_SALARY:
        bid = min(max(bid, highest_prev + 1.5), budget)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
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
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0
    weak_budget_count = 0

    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 180:
                rich_aggressive += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) <= 90:
            weak_budget_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    severe_need = hp <= 2 or no_water_days >= 2
    moderate_need = hp <= 4 or no_water_days >= 1

    if severe_need:
        bid = max(0.92 * budget, highest_prev + 6.0, 185.0 + 35.0 * supply_ratio)
        return float(min(budget, bid))

    if moderate_need:
        if supply >= 22:
            bid = max(125.0, avg_prev * 0.82, highest_prev * 0.72)
        else:
            bid = max(165.0, avg_prev * 0.95, highest_prev * 0.88)
        if weak_budget_count >= 1:
            bid -= 8.0
        return float(min(budget, max(0.0, bid)))

    if supply >= 23:
        bid = 118.0
        if rich_aggressive >= 2:
            bid = 132.0
        if weak_budget_count >= 2:
            bid -= 10.0
        return float(min(budget, max(0.0, bid)))

    if supply >= 20:
        bid = 72.0
        if desperate_count >= 1:
            bid += 12.0
        if rich_aggressive >= 2:
            bid += 10.0
        return float(min(budget, max(0.0, bid)))

    bid = 18.0
    if desperate_count >= 2:
        bid = 28.0
    if highest_prev < 100 and supply >= 19:
        bid = 55.0
    return float(min(budget, max(0.0, bid)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return min(budget, 18.0)

    my_need = 1
    total_players = 1 + len(alive)
    capacity = int(supply // WATER_REQ)
    shortage = capacity < total_players

    opp_signals = []
    dangerous_bids = []
    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is None:
            prev_bid = 0.0
        hp_o = opp.get('hp', 0)
        budget_o = opp.get('budget', 0.0)
        nwd_o = opp.get('no_water_days', 0)
        req_o = opp.get('water_requirement', WATER_REQ)
        salary_o = opp.get('daily_salary', DAILY_SALARY)

        urgency = 0
        if hp_o <= 3:
            urgency += 2
        elif hp_o <= 6:
            urgency += 1
        if nwd_o >= 2:
            urgency += 2
        elif nwd_o >= 1:
            urgency += 1

        est = prev_bid
        if prev_bid <= 0:
            est = min(budget_o, salary_o * (0.55 + 0.12 * urgency))
        else:
            if urgency >= 3:
                est = min(budget_o, max(prev_bid * 1.15, salary_o * 0.95))
            elif urgency >= 1:
                est = min(budget_o, max(prev_bid * 1.05, salary_o * 0.75))
            else:
                est = min(budget_o, prev_bid)

        if req_o <= supply:
            dangerous_bids.append(est)
        opp_signals.append((agent_id, est, prev_bid, urgency, budget_o))

    highest_threat = max(dangerous_bids) if dangerous_bids else 0.0
    second_threat = 0.0
    if len(dangerous_bids) >= 2:
        sorted_bids = sorted(dangerous_bids, reverse=True)
        second_threat = sorted_bids[int(1)]

    critical = hp <= 3 or no_water >= 2
    pressured = hp <= 5 or no_water >= 1

    if capacity >= total_players:
        base = 8.0
        if pressured:
            base = 16.0
        return float(min(budget, base))

    if capacity >= 2:
        target = max(42.0, second_threat + 2.0)
        if critical:
            target = max(target, highest_threat + 3.0, 78.0)
        elif pressured:
            target = max(target, 55.0)
        else:
            if highest_threat >= 120.0:
                target = 24.0
        return float(min(budget, target))

    if critical:
        target = max(88.0, highest_threat + 4.0)
        return float(min(budget, target))

    if pressured:
        if highest_threat <= 60.0:
            target = highest_threat + 2.5
        elif highest_threat <= 110.0:
            target = 68.0
        else:
            target = 26.0
        return float(min(budget, target))

    if highest_threat >= 90.0:
        return float(min(budget, 18.0))
    return float(min(budget, max(24.0, highest_threat + 1.5)))
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
    urgent_opp = 0
    rich_opp_bid = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= budget and float(bid) > rich_opp_bid:
                    rich_opp_bid = float(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1
    competitors = len(alive) + 1
    scarcity = competitors - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    target_prev = max(highest_prev, rich_opp_bid)

    if hp <= 2 or no_water_days >= 2:
        bid = max(62.0, target_prev + 2.5)
    elif hp <= 4 or no_water_days >= 1:
        if scarcity >= 2:
            bid = max(54.0, target_prev + 1.5)
        else:
            bid = max(42.0, target_prev * 0.72)
    else:
        if scarcity >= 3:
            bid = max(50.0, target_prev + 1.0)
        elif scarcity >= 2:
            bid = max(38.0, target_prev * 0.62)
        elif scarcity >= 1:
            bid = max(26.0, target_prev * 0.45)
        else:
            bid = 16.0

    if urgent_opp >= 2 and scarcity >= 2 and hp >= 5:
        bid *= 0.9

    if day >= 8:
        if hp <= 4:
            bid = max(bid, 58.0)
        else:
            bid = min(bid, 48.0)

    reserve = 0.0
    if hp > 4:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.6

    affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        affordable = budget

    bid = min(bid, affordable if affordable > 0 else budget)
    bid = min(bid, budget)
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
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 140:
                rich_opponents += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 20)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    scarcity = len(alive_opponents) + 1
    likely_units = supply / float(WATER_REQ)

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

    if likely_units < 1.2:
        danger += 2
    elif likely_units < 1.6:
        danger += 1

    if urgent_opponents >= 2:
        danger += 1

    if scarcity <= likely_units:
        base_bid = 18
    elif supply >= 22:
        base_bid = 24
    elif supply >= 19:
        base_bid = 32
    else:
        base_bid = 42

    if highest_prev >= 145:
        if danger >= 5:
            bid = 112
        elif danger >= 3:
            bid = 58
        else:
            bid = base_bid
    elif highest_prev >= 120:
        if danger >= 5:
            bid = 95
        elif danger >= 3:
            bid = 52
        else:
            bid = max(base_bid, 28)
    elif highest_prev > 0:
        if danger >= 5:
            bid = min(90, highest_prev + 3)
        elif danger >= 3:
            bid = min(70, avg_prev + 2)
        else:
            bid = max(base_bid, avg_prev * 0.45)
    else:
        if danger >= 5:
            bid = 84
        elif danger >= 3:
            bid = 48
        else:
            bid = base_bid

    if rich_opponents >= 3 and danger <= 2:
        bid *= 0.85

    if day >= 8:
        if hp >= 6 and no_water_days == 0:
            bid *= 0.9
        elif danger >= 4:
            bid *= 1.08

    if hp <= 1 or no_water_days >= 2:
        bid = max(bid, 105)

    if budget < 80:
        bid = min(bid, budget * 0.72)
    elif budget < 140:
        bid = min(bid, budget * 0.82)
    else:
        bid = min(bid, budget * 0.9)

    if bid < 0:
        bid = 0

    return float(min(budget, round(bid, 2)))
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

    day = day_context['day']
    supply = day_context['supply']
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
        return min(float(budget), 18.0)

    prev_bids = []
    max_prev_bid = 0.0
    bob_prev_bid = None
    desperate_count = 0
    rich_alive = 0

    for agent_id, opp in alive.items():
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_alive += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > max_prev_bid:
                max_prev_bid = float(bid)
            if agent_id == 'Bob':
                bob_prev_bid = float(bid)

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    alive_count = len(alive)
    contested = alive_count + 1 > slots

    base = 20.0

    if not contested:
        base = 8.0
    else:
        if slots >= 2:
            base = 24.0
        else:
            base = 42.0

    if max_prev_bid >= 80:
        base = max(base, 50.0)
    elif max_prev_bid >= 65:
        base = max(base, 38.0)
    elif max_prev_bid > 0:
        base = max(base, min(36.0, max_prev_bid * 0.58))

    if bob_prev_bid is not None:
        if bob_prev_bid >= 80:
            base = max(base, 52.0)
        elif bob_prev_bid >= 70:
            base = max(base, 40.0)

    if supply <= 16:
        base += 16.0
    elif supply <= 18:
        base += 8.0
    elif supply >= 24:
        base -= 6.0

    if hp <= 2:
        base = max(base, 66.0)
    elif hp <= 4:
        base = max(base, 52.0)
    elif no_water >= 1:
        base = max(base, 48.0)

    if desperate_count >= 2:
        base += 8.0
    if rich_alive == 0:
        base -= 6.0

    if day >= 8 and hp >= 5:
        base -= 4.0

    reserve = 0.0
    if hp >= 5:
        reserve = 20.0
    elif hp >= 3:
        reserve = 10.0

    affordable = float(budget) - reserve
    if affordable < 0:
        affordable = float(budget)

    bid = min(base, affordable)
    if bid < 0:
        bid = 0.0
    if hp <= 2 and budget > 0:
        bid = max(bid, min(float(budget), 66.0))

    return float(min(float(budget), bid))
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

    day = day_context['day']
    supply = day_context['supply']
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
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.85))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    opp_pressure = 0.0
    needy_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 4 or opp.get('no_water_days', 0) >= 1:
            needy_count += 1
        if opp.get('budget', 0) >= 700:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > opp_pressure:
                    opp_pressure = float(bid)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.6
    elif hp <= 7:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.55

    urgency += scarcity * 0.7
    urgency += min(0.4, needy_count * 0.08)

    remaining_days = max(0, 10 - day)
    reserve_target = remaining_days * DAILY_SALARY * 0.45
    spendable = budget - reserve_target
    if spendable < 0:
        spendable = budget * 0.35

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev_bid + 3.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(DAILY_SALARY * 0.78, highest_prev_bid + 1.5)
    else:
        if supply >= 22:
            bid = max(DAILY_SALARY * 0.18, avg_prev_bid * 0.42)
        elif supply >= 19:
            bid = max(DAILY_SALARY * 0.32, avg_prev_bid * 0.58)
        else:
            bid = max(DAILY_SALARY * 0.52, highest_prev_bid * 0.82)

    if rich_count >= 2 and hp > 4 and no_water_days == 0:
        bid *= 0.92

    if scarcity > 0.75 and (hp <= 5 or no_water_days >= 1):
        bid = max(bid, highest_prev_bid + 2.0)

    if day >= 8:
        if hp > 5 and no_water_days == 0:
            bid *= 0.9
        else:
            bid *= 1.08

    cap = max(0.0, spendable)
    if hp <= 3 or no_water_days >= 1:
        cap = max(cap, budget * 0.8)
    else:
        cap = max(cap, budget * 0.55)

    bid = min(bid, cap, budget)
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    strong_pressure = 0.0
    weak_count = 0
    urgent_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid > strong_pressure:
                    strong_pressure = bid
                if bid <= DAILY_SALARY * 0.45:
                    weak_count += 1

    if not alive_opponents:
        return float(min(budget, max(1.0, DAILY_SALARY * 0.2)))

    contested = len(alive_opponents) >= 2
    scarce = supply < WATER_REQ * 1.4
    very_urgent = hp <= 2 or no_water_days >= 2
    urgent = hp <= 3 or no_water_days >= 1

    if prev_bids:
        top_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        top_prev = DAILY_SALARY * 0.6
        avg_prev = DAILY_SALARY * 0.5

    if very_urgent:
        target = max(DAILY_SALARY * 0.95, top_prev + 2.0)
    elif urgent:
        target = max(DAILY_SALARY * 0.78, top_prev + 1.0 if top_prev < DAILY_SALARY * 1.15 else DAILY_SALARY * 0.9)
    else:
        if scarce and contested:
            target = max(DAILY_SALARY * 0.52, avg_prev * 0.72)
        else:
            target = DAILY_SALARY * 0.38

    if supply >= 24:
        target *= 0.72
    elif supply >= 21:
        target *= 0.84
    elif supply <= 16:
        target *= 1.08

    if urgent_opp_count >= 2 and not urgent:
        target *= 0.9
    if weak_count == len(prev_bids) and len(prev_bids) > 0 and urgent:
        target = max(target, top_prev + 0.5)

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 1.2
    elif day <= 9:
        reserve = DAILY_SALARY * 0.5

    spend_cap = budget - reserve
    if very_urgent:
        spend_cap = budget
    elif spend_cap < DAILY_SALARY * 0.25:
        spend_cap = min(budget, DAILY_SALARY * 0.5)

    bid = min(budget, max(0.0, min(target, spend_cap)))

    if urgent and bid < DAILY_SALARY * 0.55:
        bid = min(budget, DAILY_SALARY * 0.55)
    if very_urgent and bid < DAILY_SALARY * 0.9:
        bid = min(budget, DAILY_SALARY * 0.9)

    return float(max(0.0, bid))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_budgets = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water >= 2:
            return float(min(budget, DAILY_SALARY * 0.85))
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    richest_opp = max(opp_budgets) if opp_budgets else 0.0

    severe = (hp <= 3) or (no_water >= 2)
    urgent = (hp <= 5) or (no_water >= 1)
    scarce = supply <= 18
    comfortable_budget = budget >= richest_opp * 0.8 or budget >= 700

    if severe:
        target = max(DAILY_SALARY * 1.35, highest_prev + 3.0)
        if comfortable_budget and scarce:
            target = max(target, DAILY_SALARY * 1.55)
        return float(min(budget, target))

    if urgent:
        if highest_prev >= 150:
            target = DAILY_SALARY * 0.92 if not scarce else DAILY_SALARY * 1.08
        elif highest_prev >= 100:
            target = max(DAILY_SALARY * 0.82, highest_prev + 2.0)
        else:
            target = DAILY_SALARY * 0.78 if scarce else DAILY_SALARY * 0.68
        return float(min(budget, target))

    if scarce:
        if highest_prev >= 140:
            target = DAILY_SALARY * 0.28
        elif highest_prev >= 100:
            target = DAILY_SALARY * 0.42
        else:
            target = max(DAILY_SALARY * 0.48, avg_prev * 0.7)
    else:
        if highest_prev >= 140:
            target = DAILY_SALARY * 0.22
        elif highest_prev >= 100:
            target = DAILY_SALARY * 0.34
        else:
            target = DAILY_SALARY * 0.4

    if budget < 250:
        target = min(target, DAILY_SALARY * 0.45)

    return float(min(budget, max(0.0, target)))
"""
