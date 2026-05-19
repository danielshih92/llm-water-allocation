# ============================================================
# Experiment: exp_087
# Agent: Alex
# Source: exp_087
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 50)
        return min(budget, 24)

    total_alive = 1 + len(alive_opponents)
    expected_demand_units = total_alive * WATER_REQ
    tightness = expected_demand_units / max(1.0, supply)

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            status = prev.get('status')
            if status in ('no_water', 'hurt', 'critical'):
                desperate_count += 1
        if opp.get('budget', 0) > budget:
            rich_count += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 2:
        base = 63.0
    elif hp <= 4 or no_water_days >= 1:
        base = 52.0
    elif hp >= 8 and no_water_days == 0:
        base = 30.0
    else:
        base = 40.0

    if tightness > 2.8:
        base += 12.0
    elif tightness > 2.3:
        base += 8.0
    elif tightness > 1.8:
        base += 4.0

    if prev_bids:
        if highest_prev >= 62:
            if hp > 5 and no_water_days == 0:
                base = min(base, 28.0)
            else:
                base = max(base, highest_prev + 1.0)
        elif highest_prev >= 48:
            base = max(base, highest_prev + 1.0)
        else:
            base = max(base, avg_prev + 2.0)

    if desperate_count >= max(1, len(alive_opponents) // 2):
        base += 4.0
    if rich_count >= len(alive_opponents) // 2 + 1:
        base += 3.0

    if day >= 8:
        base += 5.0

    if budget < DAILY_SALARY:
        base = min(base, max(12.0, budget * 0.72))
    else:
        base = min(base, budget * 0.9)

    if hp >= 8 and no_water_days == 0 and highest_prev < 40 and tightness < 2.0:
        base = min(base, 26.0)

    bid = max(0.0, min(float(budget), base))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_requirements = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_requirements.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    total_demand_units = WATER_REQ
    for req in opp_requirements:
        total_demand_units += req

    scarcity = total_demand_units / max(1.0, supply)
    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    days_left = max(1, 10 - day + 1)
    reserve_target = days_left * DAILY_SALARY * 0.45
    spendable = max(0.0, budget - reserve_target)

    emergency = hp <= 2 or no_water_days >= 2
    stressed = hp <= 4 or no_water_days >= 1

    if supply >= 23:
        base = DAILY_SALARY * 0.28
    elif supply >= 20:
        base = DAILY_SALARY * 0.42
    elif supply >= 17:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.82

    if scarcity > 2.8:
        base += 18
    elif scarcity > 2.3:
        base += 10
    elif scarcity > 1.9:
        base += 5

    if highest_prev >= 120:
        pressure_bid = highest_prev + 2.5
    elif highest_prev >= 95:
        pressure_bid = highest_prev + 1.5
    elif highest_prev > 0:
        pressure_bid = max(base, avg_prev + 4.0)
    else:
        pressure_bid = base

    if emergency:
        bid = max(pressure_bid, DAILY_SALARY * 1.15)
    elif stressed:
        bid = max(base, min(pressure_bid, DAILY_SALARY * 1.45))
    else:
        if supply >= 22 and highest_prev >= 95:
            bid = DAILY_SALARY * 0.25
        else:
            bid = min(pressure_bid, DAILY_SALARY * 1.3)

    if spendable > 0:
        bid = min(bid, spendable + DAILY_SALARY * 0.55)

    if budget < DAILY_SALARY * 0.8:
        bid = min(bid, budget)

    if emergency and budget > 0:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

    bid = max(0.0, min(budget, bid))
    return float(bid)
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

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        if hp <= 2 or no_water >= 2:
            return float(min(budget, DAILY_SALARY * 0.85))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        if opp.get('budget', 0) > 400 and bid is not None and bid >= 90:
            rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / WATER_REQ
    can_cover_two = units >= 2.0
    scarce = supply < WATER_REQ * 1.5

    if hp <= 2 or no_water >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
        return float(min(budget, bid))

    if hp <= 4 or no_water >= 1:
        if scarce:
            bid = max(DAILY_SALARY * 0.82, highest_prev + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.68, avg_prev + 1.5)
        return float(min(budget, bid))

    if can_cover_two:
        bid = DAILY_SALARY * 0.34
        if highest_prev > 95:
            bid = DAILY_SALARY * 0.22
        elif highest_prev > 70:
            bid = DAILY_SALARY * 0.28
        elif desperate_count >= 2:
            bid = DAILY_SALARY * 0.42
        return float(min(budget, bid))

    bid = DAILY_SALARY * 0.52
    if scarce:
        bid = max(bid, avg_prev + 1.0)
    if rich_aggressive >= 1:
        bid = min(bid, DAILY_SALARY * 0.48)
    if day >= 8 and hp >= 6:
        bid = min(bid, DAILY_SALARY * 0.40)

    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    danger = 0
    if hp <= 2:
        danger = 3
    elif hp <= 4:
        danger = 2
    elif hp <= 6:
        danger = 1

    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1

    base = 22.0
    if scarcity == 1:
        base = 34.0
    elif scarcity == 2:
        base = 48.0

    if highest_prev >= 120:
        if danger >= 3:
            bid = 96.0
        elif scarcity == 2:
            bid = 58.0
        else:
            bid = 24.0
    elif highest_prev >= 90:
        if danger >= 3:
            bid = highest_prev + 2.0
        elif danger >= 2:
            bid = max(base + 10.0, avg_prev * 0.72)
        else:
            bid = max(26.0, avg_prev * 0.45)
    else:
        bid = max(base, highest_prev + 1.5 if highest_prev > 0 else base)

    if urgent_opp >= 2 and danger == 0:
        bid *= 0.82
    if rich_opp >= 2 and scarcity >= 1 and danger >= 2:
        bid *= 1.12

    if day >= 8:
        if danger >= 2:
            bid *= 1.15
        else:
            bid *= 0.92

    if hp >= 8 and no_water_days == 0 and scarcity == 0:
        bid = min(bid, 28.0)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, 78.0)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(bid, 52.0 if scarcity == 0 else 68.0)

    reserve = 0.0
    if day <= 7:
        reserve = 35.0
    elif day <= 9:
        reserve = 15.0

    spend_cap = budget - reserve
    if spend_cap < 0:
        spend_cap = budget

    bid = min(bid, spend_cap)
    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0

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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    urgent_opp = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_threat += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0:
        tightness = 0.0
    if tightness > 1:
        tightness = 1.0

    danger = 0.0
    if hp <= 2:
        danger += 0.55
    elif hp <= 4:
        danger += 0.35
    elif hp <= 6:
        danger += 0.18

    if no_water_days >= 2:
        danger += 0.35
    elif no_water_days >= 1:
        danger += 0.18

    pressure = 0.0
    if highest_prev >= 120:
        pressure += 0.28
    elif highest_prev >= 90:
        pressure += 0.18
    elif highest_prev >= 60:
        pressure += 0.08

    pressure += min(0.18, rich_threat * 0.06)
    pressure += min(0.12, urgent_opp * 0.04)

    base = 16.0 + 18.0 * tightness + 42.0 * danger + 24.0 * pressure

    if supply <= 17:
        base += 10.0
    elif supply >= 23:
        base -= 6.0

    if hp >= 7 and no_water_days == 0 and highest_prev >= 100:
        base = min(base, 34.0 + 8.0 * tightness)

    if hp <= 3 or no_water_days >= 2:
        emergency = max(0.88 * DAILY_SALARY, highest_prev + 3.0)
        base = max(base, emergency)

    if highest_prev > 0 and hp > 4 and no_water_days == 0:
        shadow = highest_prev * (0.58 + 0.12 * tightness)
        if shadow < base:
            base = max(base - 4.0, shadow)

    if avg_prev > 0 and avg_prev < 50 and supply >= 21 and hp >= 6:
        base = min(base, avg_prev + 6.0)

    reserve_floor = DAILY_SALARY * 1.2 if hp > 3 else DAILY_SALARY * 0.4
    spendable = budget - reserve_floor
    if spendable < 8.0:
        spend_cap = budget
    else:
        spend_cap = max(8.0, spendable)

    bid = min(base, spend_cap, budget)
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        bid = min(budget, 18.0)
        return float(max(0.0, bid))

    yesterday_bids = []
    dangerous_prev = 0.0
    weak_count = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            pbid = float(prev['bid'])
            yesterday_bids.append(pbid)
            score = pbid
            if opp.get('budget', 0) > DAILY_SALARY * 2:
                score += 4.0
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                score += 6.0
            if score > dangerous_prev:
                dangerous_prev = score
        if opp.get('budget', 0) < DAILY_SALARY * 0.8 or opp.get('hp', 0) <= 2:
            weak_count += 1

    total_alive = len(alive) + 1
    units = int(supply / WATER_REQ)
    scarce = units < total_alive
    very_scarce = units <= 1
    comfortable = units >= 2

    if hp <= 2 or no_water >= 2:
        base = max(92.0, dangerous_prev + 2.5 if dangerous_prev > 0 else 92.0)
    elif hp <= 4 or no_water >= 1:
        base = max(74.0, dangerous_prev + 1.8 if dangerous_prev > 0 else 74.0)
    else:
        if very_scarce:
            base = max(68.0, dangerous_prev + 1.2 if dangerous_prev > 0 else 68.0)
        elif scarce:
            base = max(52.0, dangerous_prev * 0.72 if dangerous_prev > 0 else 52.0)
        else:
            base = 24.0 if weak_count >= 1 else 31.0
            if yesterday_bids:
                avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))
                base = max(base, min(46.0, avg_prev * 0.42))

    if budget < DAILY_SALARY:
        base = min(base, budget)
    elif budget < DAILY_SALARY * 2 and hp > 4 and no_water == 0:
        base = min(base, 58.0)

    if comfortable and hp > 5 and no_water == 0 and weak_count >= 2:
        base = min(base, 22.0)

    bid = min(float(budget), float(base))
    if bid < 0:
        bid = 0.0
    return float(bid)
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    urgent_prev = []
    all_prev = []
    rich_threat = []
    weak_or_broke = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            all_prev.append(float(bid))
        opp_hp = opp.get('hp', 0)
        opp_budget = opp.get('budget', 0)
        opp_nwd = opp.get('no_water_days', 0)
        if opp_hp <= 3 or opp_nwd >= 1:
            if bid is not None:
                urgent_prev.append(float(bid))
        if opp_budget >= 250:
            if bid is not None:
                rich_threat.append(float(bid))
        if opp_budget <= 40 or opp_hp <= 2:
            weak_or_broke += 1

    slots = max(1, int(supply // WATER_REQ))
    tight = slots <= 1

    highest_prev = max(all_prev) if all_prev else 0.0
    highest_urgent = max(urgent_prev) if urgent_prev else highest_prev
    highest_rich = max(rich_threat) if rich_threat else highest_prev

    if hp <= 2 or no_water >= 2:
        target = max(63.0, highest_urgent + 2.5, highest_rich + 1.5)
    elif hp <= 4 or no_water >= 1:
        if tight:
            target = max(54.0, highest_urgent + 2.0)
        else:
            target = max(42.0, highest_prev + 1.0)
    else:
        if tight:
            if highest_prev >= 120:
                target = 46.0
            elif highest_prev >= 95:
                target = highest_prev + 1.5
            elif highest_prev >= 60:
                target = highest_prev + 2.0
            else:
                target = 58.0
        else:
            if weak_or_broke >= len(alive) // 2 + 1:
                target = 24.0
            elif highest_prev >= 110:
                target = 38.0
            elif highest_prev >= 70:
                target = 34.0
            else:
                target = 28.0

    if day >= 8 and hp > 4 and no_water == 0:
        target *= 0.9
    if budget < 120:
        target = min(target, 0.42 * budget)
    elif budget < 220:
        target = min(target, 0.55 * budget)
    else:
        target = min(target, 0.75 * budget)

    target = max(0.0, min(float(budget), float(target)))
    return float(round(target, 2))
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

    alive_opponents = []
    prev_bids = []
    strong_prev = []
    needy_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 70:
                    strong_prev.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev = sorted_bids[int(1)]

    winners_est = max(1, int(float(supply) / WATER_REQ))
    tight_supply = winners_est <= 1
    very_tight = float(supply) <= 16.0
    abundant = float(supply) >= 24.0

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

    if tight_supply:
        urgency += 1
    if very_tight:
        urgency += 1
    if needy_count >= 2:
        urgency += 1
    if day >= 8:
        urgency += 1

    reserve = 0.0
    days_left = max(0, 10 - int(day))
    if hp > 4 and days_left > 0:
        reserve = min(budget * 0.35, days_left * 12.0)

    if urgency >= 5:
        target = max(92.0, highest_prev + 2.5)
    elif urgency >= 3:
        if highest_prev >= 85.0:
            target = highest_prev + 1.5
        else:
            target = max(74.0, highest_prev + 2.0)
    elif urgency >= 1:
        if abundant and hp >= 6:
            target = max(38.0, second_prev + 1.0)
        else:
            target = max(55.0, second_prev + 2.0)
    else:
        if abundant:
            target = 24.0
        elif tight_supply:
            target = 48.0
        else:
            target = 34.0

    if len(strong_prev) >= 2 and not abundant:
        target = max(target, second_prev + 1.5)

    if hp >= 8 and no_water_days == 0 and day <= 3 and highest_prev >= 95.0:
        target = min(target, 28.0)

    max_affordable = budget - reserve
    if urgency >= 4:
        max_affordable = budget
    if max_affordable < 0:
        max_affordable = 0.0

    bid = min(target, max_affordable)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 98.0 if tight_supply else 88.0))

    if budget < 25.0:
        bid = budget

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    threat_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) > 2 and opp.get('budget', 0) > DAILY_SALARY:
                    threat_bids.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    max_threat = max(threat_bids) if threat_bids else max_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.4
    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days >= 1:
        urgency += 0.25
    urgency += 0.35 * scarcity

    affordable_cap = min(float(budget), max(20.0, float(budget) * 0.55 + DAILY_SALARY * 0.35))

    if urgency >= 1.0:
        bid = max(DAILY_SALARY * 1.05, max_threat + 3.0)
    elif urgency >= 0.6:
        bid = max(DAILY_SALARY * 0.82, max_threat + 1.5)
    else:
        if supply >= 22:
            bid = DAILY_SALARY * 0.22
        elif supply >= 19:
            bid = DAILY_SALARY * 0.38
        else:
            bid = max(DAILY_SALARY * 0.55, max_threat * 0.72)

    if max_prev >= 130 and urgency < 0.9:
        bid = min(bid, DAILY_SALARY * 0.35)

    if hp >= 8 and no_water_days == 0 and supply >= 21:
        bid = min(bid, DAILY_SALARY * 0.25)

    bid = min(bid, affordable_cap)
    bid = min(bid, float(budget))
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_threats = 0
    urgent_opp = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > budget:
                rich_threats += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    abundance = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)

    emergency = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if emergency:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 3.0)
        if supply >= 22:
            bid *= 0.92
        return max(0.0, min(budget, bid))

    if highest_prev >= 120:
        if supply <= 18 and hp >= 6 and no_water_days == 0:
            return max(0.0, min(budget, DAILY_SALARY * 0.08))
        bid = DAILY_SALARY * (0.42 + 0.18 * scarcity)
        if pressured:
            bid = max(bid, DAILY_SALARY * 0.72)
        return max(0.0, min(budget, bid))

    base = 22.0 + 12.0 * scarcity + 8.0 * urgent_opp + 6.0 * rich_threats

    if supply >= 23:
        base -= 10.0
    elif supply >= 20:
        base -= 4.0

    if highest_prev > 0:
        if highest_prev <= 85:
            base = max(base, highest_prev + 2.0)
        else:
            base = max(base, avg_prev * 0.6)

    if pressured:
        base += 18.0
    if hp >= 8 and no_water_days == 0 and supply <= 17:
        base -= 8.0

    if day >= 8:
        base += 10.0

    bid = max(1.0, base)
    return max(0.0, min(budget, bid))
"""
