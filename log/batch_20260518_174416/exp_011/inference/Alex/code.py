# ============================================================
# Experiment: exp_011
# Agent: Alex
# Source: exp_011
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

    alive_opponents = []
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    players = 1 + len(alive_opponents)
    affordable = max(0, int(supply) // WATER_REQ)
    shortage = max(0, players - affordable)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return min(budget, 35)
        return min(budget, 18)

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    if hp <= 2 or no_water >= 2:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 2)
    elif hp <= 4 or no_water >= 1:
        bid = max(0.72 * DAILY_SALARY, highest_prev + 1)
    else:
        if shortage <= 0:
            bid = 0.28 * DAILY_SALARY
        elif shortage == 1:
            bid = max(0.45 * DAILY_SALARY, avg_prev + 1)
        else:
            bid = max(0.62 * DAILY_SALARY, highest_prev + 1.5)

    if urgent_opponents >= max(1, len(alive_opponents) // 2):
        bid += 4
    if rich_opponents >= max(1, len(alive_opponents) // 2):
        bid += 3
    if int(supply) <= MIN_SUPPLY + 1:
        bid += 5
    elif int(supply) >= MAX_SUPPLY - 1 and hp > 4 and no_water == 0:
        bid -= 4

    reserve = 0
    if hp > 4 and no_water == 0:
        reserve = DAILY_SALARY * 0.35
    elif hp > 2:
        reserve = DAILY_SALARY * 0.15

    max_spend = max(0, budget - reserve)
    if hp <= 2 or no_water >= 2:
        max_spend = budget

    bid = min(bid, max_spend)
    bid = max(0, bid)

    if 0 < bid < 1:
        bid = 1

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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_threats = 0
    urgent_opponents = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 100:
                rich_threats += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 20.0)
        return min(budget, 5.0)

    slots = max(1, int(supply // WATER_REQ))
    crowded = len(alive) + 1 > slots
    severe_scarcity = slots <= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    critical_me = hp <= 2 or no_water_days >= 1
    fragile_me = hp <= 4

    if critical_me:
        target = max(58.0, highest_prev + 2.5)
        if severe_scarcity:
            target = max(target, 72.0)
        return min(budget, target)

    if severe_scarcity:
        if highest_prev >= 150:
            target = 18.0 if hp >= 6 else 62.0
        elif highest_prev >= 100:
            target = 42.0 if hp >= 6 else 66.0
        else:
            target = max(36.0, highest_prev + 2.0)
        if urgent_opponents >= 2:
            target += 6.0
        return min(budget, target)

    if crowded:
        if highest_prev >= 140:
            target = 16.0 if hp >= 7 else 48.0
        elif highest_prev >= 90:
            target = max(30.0, avg_prev * 0.55)
        else:
            target = max(24.0, highest_prev + 1.5)
        if fragile_me:
            target += 8.0
        return min(budget, target)

    target = 10.0
    if highest_prev > 0:
        target = min(28.0, max(10.0, avg_prev * 0.22))
    if rich_threats >= 2 and day >= 7 and fragile_me:
        target = max(target, 24.0)
    return min(budget, target)
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 4 else 35.0))

    slots = supply / float(WATER_REQ)
    pressure = len(alive_opponents) + 1 - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water >= 2:
        bid = max(95.0, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        if pressure >= 2.5:
            bid = max(82.0, avg_prev + 3.0)
        elif pressure >= 1.5:
            bid = max(68.0, avg_prev * 0.72)
        else:
            bid = 44.0
    else:
        if supply >= 24:
            bid = 18.0
        elif supply >= 21:
            bid = 24.0
        elif supply >= 18:
            bid = 34.0
        else:
            bid = 48.0

        if pressure >= 2.5:
            bid = max(bid, min(72.0, avg_prev * 0.62 + 4.0))
        elif pressure >= 1.5:
            bid = max(bid, min(56.0, avg_prev * 0.48 + 3.0))

    if urgent_opp >= 2 and hp > 4 and no_water == 0:
        bid *= 0.88
    if rich_opp >= 2 and pressure >= 1.5:
        bid *= 1.08
    if day >= 8 and hp > 5 and budget < DAILY_SALARY * 2:
        bid *= 0.9
    if day >= 8 and (hp <= 4 or no_water >= 1):
        bid *= 1.15

    min_safe = 12.0 if hp > 5 and no_water == 0 else 22.0
    bid = max(min_safe, bid)
    bid = min(budget, bid)
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

    winners_est = max(1, int(supply / WATER_REQ))

    prev_bids = []
    urgent_opp_bids = []
    weak_opp_count = 0
    rich_opp_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_bids.append(float(bid))
        if opp.get('budget', 0) < DAILY_SALARY:
            weak_opp_count += 1
        if opp.get('budget', 0) > DAILY_SALARY * 2.2:
            rich_opp_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else highest_prev

    my_urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if winners_est >= 2:
        if critical:
            bid = min(budget, max(92.0, urgent_prev + 2.0, highest_prev * 0.72))
        elif my_urgent:
            bid = min(budget, max(66.0, urgent_prev + 1.5, highest_prev * 0.52))
        else:
            if highest_prev >= 150:
                bid = min(budget, 24.0)
            elif highest_prev >= 110:
                bid = min(budget, 32.0)
            else:
                bid = min(budget, max(22.0, highest_prev * 0.28 + 3.0))
    else:
        if critical:
            bid = min(budget, max(118.0, urgent_prev + 3.0, highest_prev * 0.82))
        elif my_urgent:
            bid = min(budget, max(88.0, urgent_prev + 2.0, highest_prev * 0.68))
        else:
            bid = min(budget, max(54.0, highest_prev * 0.42 + 4.0))

    if weak_opp_count >= 2 and not my_urgent:
        bid = min(bid, 28.0 if winners_est >= 2 else 46.0)

    if rich_opp_count >= 2 and my_urgent:
        bid = min(budget, max(bid, highest_prev * 0.75 + 2.0))

    reserve_floor = DAILY_SALARY * max(0, 9 - int(day_context['day'])) * 0.18
    if budget - bid < reserve_floor and not critical:
        bid = max(0.0, budget - reserve_floor)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    yesterday_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    tight_supply = supply <= 17
    abundant_supply = supply >= 22
    critical_me = hp <= 3 or no_water_days >= 1
    stable_me = hp >= 7 and no_water_days == 0

    base = 0.0

    if critical_me:
        if highest_prev >= 140:
            base = 145.0
        elif highest_prev >= 110:
            base = highest_prev + 6.0
        elif highest_prev > 0:
            base = max(78.0, highest_prev + 4.0)
        else:
            base = 82.0
    else:
        if tight_supply:
            if highest_prev >= 140:
                base = 58.0 if stable_me else 88.0
            elif highest_prev >= 110:
                base = 72.0
            elif highest_prev >= 80:
                base = highest_prev + 2.0
            else:
                base = 63.0
        elif abundant_supply:
            if highest_prev >= 140:
                base = 24.0
            elif highest_prev >= 110:
                base = 38.0
            else:
                base = 48.0
        else:
            if highest_prev >= 140:
                base = 32.0
            elif highest_prev >= 110:
                base = 52.0
            elif highest_prev >= 80:
                base = min(76.0, avg_prev + 3.0)
            else:
                base = 56.0

    if urgent_opp >= 2 and not critical_me:
        base -= 8.0
    if rich_opp >= 2 and not critical_me:
        base -= 5.0
    if day >= 8 and hp >= 6 and no_water_days == 0:
        base -= 6.0
    if day >= 8 and critical_me:
        base += 8.0

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left > 0 and not critical_me:
        reserve_floor = min(budget * 0.45, days_left * 18.0)

    cap = budget - reserve_floor
    if critical_me:
        cap = budget
    if cap < 0:
        cap = budget * 0.5

    bid = min(base, cap, budget)

    if bid < 0:
        bid = 0.0

    if critical_me and bid < 35.0:
        bid = min(budget, 35.0)

    return float(round(bid, 2))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) >= 500:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.6
    elif hp <= 4:
        urgency += 0.35
    if no_water >= 2:
        urgency += 0.5
    elif no_water == 1:
        urgency += 0.2

    market = 0.0
    if highest_prev >= 120:
        market = 0.75
    elif highest_prev >= 90:
        market = 0.62
    elif highest_prev >= 60:
        market = 0.5
    elif highest_prev >= 35:
        market = 0.38
    else:
        market = 0.28

    target_ratio = 0.22 + 0.28 * supply_pressure + urgency + market * 0.35
    target_ratio += desperate_count * 0.04
    target_ratio += min(rich_count, 2) * 0.03

    if supply >= 22 and hp >= 5 and no_water == 0:
        target_ratio -= 0.12
    if supply <= 17:
        target_ratio += 0.1

    if target_ratio < 0.12:
        target_ratio = 0.12
    if target_ratio > 0.95:
        target_ratio = 0.95

    base_bid = DAILY_SALARY * target_ratio

    if highest_prev > 0:
        if urgency >= 0.5:
            base_bid = max(base_bid, min(highest_prev + 2.0, DAILY_SALARY * 1.15))
        elif supply <= 17:
            base_bid = max(base_bid, min(avg_prev + 3.0, DAILY_SALARY * 0.95))
        else:
            base_bid = max(base_bid, min(avg_prev * 0.92 + 1.0, DAILY_SALARY * 0.8))

    if hp <= 2 or no_water >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.88)
    elif hp <= 4 and supply <= 18:
        base_bid = max(base_bid, DAILY_SALARY * 0.72)

    if day >= 8 and hp >= 6 and budget < 180:
        base_bid *= 0.9

    if budget < DAILY_SALARY * 0.6:
        base_bid = min(base_bid, budget)
    else:
        base_bid = min(base_bid, budget, DAILY_SALARY * 1.2)

    if base_bid < 0:
        base_bid = 0.0

    return float(base_bid)
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    stressed = 0
    broke_count = 0
    for oid, opp in alive:
        if opp.get('budget', 0) <= DAILY_SALARY * 1.2:
            broke_count += 1
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            stressed += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(float(bid))

    prev_bids.sort(reverse=True)
    highest_prev = prev_bids[int(0)] if len(prev_bids) >= 1 else 0.0
    second_prev = prev_bids[int(1)] if len(prev_bids) >= 2 else highest_prev

    scarcity = 1.0 if supply <= 16 else (0.6 if supply <= 19 else 0.25)
    danger = 0
    if hp <= 2 or no_water >= 2:
        danger = 3
    elif hp <= 4 or no_water >= 1:
        danger = 2
    elif hp <= 6:
        danger = 1

    if danger == 0:
        if highest_prev >= 165:
            bid = DAILY_SALARY * 0.08
        elif highest_prev >= 145:
            bid = DAILY_SALARY * 0.15
        elif highest_prev >= 120:
            bid = DAILY_SALARY * 0.22
        else:
            bid = DAILY_SALARY * 0.28
        if scarcity >= 1.0:
            bid *= 0.8
        if broke_count >= 2:
            bid *= 0.9
    elif danger == 1:
        target = max(DAILY_SALARY * 0.55, second_prev + 2.0)
        if highest_prev >= 150 and scarcity >= 0.6:
            target = max(target, highest_prev * 0.9)
        bid = target
    elif danger == 2:
        target = max(DAILY_SALARY * 0.95, highest_prev + 1.5)
        if broke_count >= 2:
            target = max(DAILY_SALARY * 0.8, second_prev + 3.0)
        bid = target
    else:
        target = max(DAILY_SALARY * 1.35, highest_prev + 3.0)
        if stressed >= 2 and highest_prev > 0:
            target = max(target, highest_prev + 6.0)
        bid = target

    if day >= 8:
        bid *= 1.08
    if day >= 9 and danger >= 1:
        bid *= 1.12

    reserve = 0.0
    if danger == 0:
        reserve = DAILY_SALARY * 1.2
    elif danger == 1:
        reserve = DAILY_SALARY * 0.7
    elif danger == 2:
        reserve = DAILY_SALARY * 0.25

    max_affordable = budget - reserve
    if max_affordable < 0:
        max_affordable = budget * 0.5 if danger == 0 else budget

    bid = min(bid, max_affordable, budget)
    if danger >= 2 and budget <= DAILY_SALARY * 1.1:
        bid = budget

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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    strong_pressure = 0
    cindy_bid = None
    cindy_alive = False

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 90:
                    strong_pressure += 1
            if oid == 'Cindy':
                cindy_alive = True
                if bid is not None:
                    cindy_bid = float(bid)

    if not alive_opps:
        return float(min(budget, 8.0))

    expected_slots = max(1, int(float(supply) / WATER_REQ))
    alive_count = len(alive_opps) + 1
    scarcity = alive_count - expected_slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    base = 18.0

    if scarcity >= 3:
        base = 52.0
    elif scarcity == 2:
        base = 40.0
    elif scarcity == 1:
        base = 28.0

    if cindy_alive and cindy_bid is not None:
        if cindy_bid >= 120:
            base = min(base, 24.0) if hp >= 5 and no_water == 0 else max(base, 72.0)
        elif cindy_bid >= 80:
            base = max(base, 34.0)

    if highest_prev >= 150:
        if hp >= 5 and no_water == 0:
            base = min(base, 20.0)
        else:
            base = max(base, 78.0)
    elif highest_prev >= 90:
        base = max(base, 32.0)

    if hp <= 2 or no_water >= 2:
        base = max(base, 88.0)
    elif hp <= 4 or no_water >= 1:
        base = max(base, 62.0)

    if day >= 8:
        base = max(base, 42.0)
    if day >= 9 and (hp <= 4 or no_water >= 1):
        base = max(base, 85.0)

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0:
        soft_cap = min(budget, max(25.0, budget / float(reserve_days)))

    bid = min(base, soft_cap)

    if hp >= 6 and no_water == 0 and strong_pressure >= 2:
        bid = min(bid, 22.0)

    if budget < 25:
        bid = budget

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.25))

    total_players = 1 + len(alive_opponents)
    total_req = WATER_REQ
    for r in opp_requirements:
        total_req += r

    scarcity = total_req / max(supply, 1.0)
    per_capita = supply / max(total_players, 1)
    urgent = (hp <= 2) or (no_water >= 2)
    pressured = (hp <= 4) or (no_water >= 1)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    if urgent:
        base = max(DAILY_SALARY * 0.95, highest_prev + 4.0)
    elif scarcity >= 2.8:
        base = max(DAILY_SALARY * 0.88, highest_prev + 2.5)
    elif scarcity >= 2.3:
        base = max(DAILY_SALARY * 0.72, avg_prev + 1.5)
    elif scarcity >= 1.8:
        base = max(DAILY_SALARY * 0.55, avg_prev * 0.82)
    else:
        base = DAILY_SALARY * 0.28

    if per_capita >= WATER_REQ * 1.4 and not pressured:
        base *= 0.72
    elif per_capita < WATER_REQ * 0.9:
        base *= 1.12

    rich_live = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > budget:
            rich_live += 1
    if rich_live >= 2 and not urgent:
        base *= 0.93

    if day >= 8 and hp > 5 and no_water == 0:
        base *= 0.9

    bid = min(float(budget), float(base))
    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.35))

    total_agents = 1 + len(alive_opponents)
    total_req = WATER_REQ + sum(opp_requirements)
    scarcity_ratio = float(supply) / float(total_req) if total_req > 0 else 1.0
    per_agent_supply = float(supply) / float(total_agents)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    urgent = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1
    very_tight = scarcity_ratio < 0.34 or per_agent_supply < 4.2
    tight = scarcity_ratio < 0.42 or per_agent_supply < 5.2
    comfortable_supply = scarcity_ratio > 0.52 and per_agent_supply > 6.0

    if urgent:
        target = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
    elif very_tight:
        target = max(DAILY_SALARY * 0.82, avg_prev + 2.0, highest_prev * 0.92)
    elif tight:
        if highest_prev >= DAILY_SALARY * 0.9:
            target = DAILY_SALARY * 0.52 if hp > 5 and no_water_days == 0 else DAILY_SALARY * 0.88
        else:
            target = max(DAILY_SALARY * 0.58, avg_prev * 0.72 + 4.0)
    elif comfortable_supply:
        target = DAILY_SALARY * 0.22 if hp > 5 and no_water_days == 0 else DAILY_SALARY * 0.4
    else:
        if pressured:
            target = max(DAILY_SALARY * 0.62, avg_prev * 0.62 + 3.0)
        else:
            target = DAILY_SALARY * 0.34

    rich_threshold = DAILY_SALARY * 10
    if budget < DAILY_SALARY * 2:
        target *= 0.9
    elif budget > rich_threshold and pressured:
        target *= 1.08

    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.98)
    elif hp >= 8 and no_water_days == 0 and comfortable_supply:
        target = min(target, DAILY_SALARY * 0.28)

    target = max(0.0, min(float(budget), float(target)))
    return float(round(target, 2))
"""
