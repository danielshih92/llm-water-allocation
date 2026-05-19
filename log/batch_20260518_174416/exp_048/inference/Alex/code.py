# ============================================================
# Experiment: exp_048
# Agent: Alex
# Source: exp_048
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']
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
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_count += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, 18)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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
        urgency += 2

    pressure = 0
    if highest_prev >= 60:
        pressure += 3
    elif highest_prev >= 45:
        pressure += 2
    elif highest_prev >= 30:
        pressure += 1

    pressure += min(desperate_count, 2)
    if rich_count >= 2:
        pressure += 1
    if supply_tight:
        pressure += 1
    if supply_loose:
        pressure -= 1

    if urgency >= 5:
        bid = 66
    elif urgency >= 3:
        bid = 56 if pressure >= 2 else 48
    else:
        if pressure >= 4:
            bid = max(44, highest_prev + 2)
        elif pressure >= 2:
            bid = max(34, avg_prev + 2)
        else:
            bid = 24 if supply_loose else 30

    if day >= 8 and hp <= 4:
        bid = max(bid, 58)

    if budget < bid:
        if urgency >= 3:
            return max(0, budget)
        return max(0, min(budget, bid))

    return max(0, min(budget, round(bid, 2)) )
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
    prev_bids = []
    strong_prev = 0.0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > strong_prev:
                    strong_prev = float(bid)

    if not alive:
        return max(0.0, min(float(budget), 18.0))

    competitors = len(alive) + 1
    tight = supply <= WATER_REQ * 1.5
    roomy = supply >= WATER_REQ * 1.8

    desperate = hp <= 2 or no_water_days >= 2
    fragile = hp <= 4 or no_water_days >= 1

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    top_prev = max(prev_bids) if prev_bids else 52.0

    if desperate:
        bid = max(63.0, top_prev + 4.0)
        if tight:
            bid = max(bid, 72.0)
        return max(0.0, min(float(budget), bid))

    if tight:
        bid = max(56.0, top_prev + 1.5)
        if top_prev >= 85.0:
            bid = 58.0 if hp >= 6 and no_water_days == 0 else 74.0
        elif top_prev >= 70.0:
            bid = max(bid, 61.0)
    elif roomy:
        if hp >= 7 and no_water_days == 0:
            bid = 24.0
        else:
            bid = max(34.0, avg_prev * 0.65)
    else:
        bid = max(42.0, avg_prev * 0.9)
        if top_prev >= 70.0:
            bid = max(bid, 52.0)

    rich = budget >= DAILY_SALARY * (11 - day)
    if not rich:
        bid *= 0.92
    if fragile and bid < 55.0:
        bid = 55.0

    if day >= 8:
        if hp >= 6 and no_water_days == 0 and not tight:
            bid *= 0.9
        elif fragile:
            bid = max(bid, top_prev + 2.0)

    bid = max(0.0, min(float(budget), bid))
    return bid
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid >= 100:
                    aggressive_bids.append(bid)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 35.0))
        return float(min(budget, 8.0))

    competition = len(alive_opponents) + 1
    tight_supply = supply <= WATER_REQ * 1.6
    medium_supply = supply <= WATER_REQ * 2.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    low_prev = min(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 2:
        emergency = max(62.0, highest_prev + 3.0 if highest_prev > 0 else 62.0)
        return float(min(budget, emergency))

    if no_water_days >= 1 or hp <= 4:
        if tight_supply:
            urgent = max(48.0, min(72.0, highest_prev * 0.55 + 6.0 if highest_prev > 0 else 52.0))
            return float(min(budget, urgent))
        return float(min(budget, 34.0))

    if aggressive_bids:
        if tight_supply:
            bid = 26.0
        elif medium_supply:
            bid = 18.0
        else:
            bid = 10.0
    elif prev_bids:
        if highest_prev >= 60:
            bid = 24.0 if tight_supply else 15.0
        elif highest_prev >= 25:
            bid = min(32.0, highest_prev + 2.0)
            if not tight_supply:
                bid *= 0.7
        else:
            bid = max(9.0, low_prev + 2.0)
            if tight_supply:
                bid += 4.0
    else:
        bid = 16.0 if tight_supply else 10.0

    if competition >= 4 and tight_supply:
        bid += 4.0
    elif competition >= 3 and medium_supply:
        bid += 2.0

    if day >= 8 and hp >= 7 and no_water_days == 0:
        bid *= 0.9

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    dangerous_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    slots = max(1, int(supply / WATER_REQ))
    scarcity = 1.0 if slots <= 1 else 0.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(dangerous_bids) if dangerous_bids else highest_prev

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if scarcity >= 1.0:
        if urgency >= 3:
            target = max(95.0, urgent_prev + 3.0, highest_prev + 1.5)
        elif urgency == 2:
            target = max(82.0, urgent_prev + 2.0)
        elif urgency == 1:
            target = max(68.0, highest_prev * 0.72)
        else:
            target = max(52.0, highest_prev * 0.55)
    else:
        if urgency >= 3:
            target = max(72.0, urgent_prev + 1.0)
        elif urgency == 2:
            target = max(58.0, highest_prev * 0.52)
        elif urgency == 1:
            target = max(42.0, highest_prev * 0.38)
        else:
            target = 26.0

    remaining_days = max(1, 10 - int(day) + 1)
    soft_cap = budget / remaining_days + DAILY_SALARY * 0.35
    if urgency >= 2:
        soft_cap = budget / remaining_days + DAILY_SALARY * 0.75
    if hp <= 2:
        soft_cap = max(soft_cap, budget * 0.7)

    bid = min(target, budget, soft_cap)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    total_players = 1 + len(alive)
    guaranteed_units = int(supply // WATER_REQ)
    scarcity = guaranteed_units < total_players

    highest_prev = 0.0
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        prev_bid = 0.0
        if prev and prev.get('bid') is not None:
            prev_bid = float(prev.get('bid', 0.0))
        if prev_bid > highest_prev:
            highest_prev = prev_bid
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_opp += 1

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

    if scarcity:
        danger += 2
    if urgent_opp >= 1:
        danger += 1
    if highest_prev >= 120:
        danger += 2
    elif highest_prev >= 85:
        danger += 1

    if danger >= 6:
        target = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
    elif danger >= 4:
        target = max(0.74 * DAILY_SALARY, highest_prev * 0.72 + 2.0)
    elif danger >= 2:
        target = max(0.48 * DAILY_SALARY, highest_prev * 0.45 + 1.5)
    else:
        target = 0.22 * DAILY_SALARY
        if scarcity:
            target = max(target, 0.34 * DAILY_SALARY)

    if day >= 8 and hp > 5 and no_water_days == 0:
        target *= 0.9

    if rich_opp >= 2 and scarcity and (hp <= 4 or no_water_days >= 1):
        target = max(target, highest_prev + 4.0, 0.88 * DAILY_SALARY)

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = 0.25 * DAILY_SALARY
    elif hp > 2:
        reserve = 0.1 * DAILY_SALARY

    affordable = max(0.0, budget - reserve)
    bid = min(target, affordable)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 0.95 * DAILY_SALARY))

    if not alive:
        bid = min(budget, 0.35 * DAILY_SALARY)

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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    low_budget_opps = 0
    desperate_opps = 0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) <= DAILY_SALARY * 1.2:
                low_budget_opps += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opps += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    critical = hp <= 2 or no_water >= 2
    urgent = hp <= 4 or no_water >= 1
    abundant = supply >= 22
    tight = supply <= 17

    if critical:
        bid = max(DAILY_SALARY * 1.15, highest_prev + 3.0)
        if abundant:
            bid = max(DAILY_SALARY * 0.95, avg_prev + 2.0)
        return float(min(budget, bid))

    if urgent:
        if tight:
            bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.78, avg_prev + 1.5)
        return float(min(budget, bid))

    if abundant:
        if low_budget_opps >= 2:
            bid = max(DAILY_SALARY * 0.48, lowest_prev + 1.0)
        else:
            bid = max(DAILY_SALARY * 0.58, avg_prev * 0.82)
        return float(min(budget, bid))

    if tight:
        if highest_prev >= 170:
            bid = DAILY_SALARY * 0.22
        elif highest_prev >= 120:
            bid = DAILY_SALARY * 0.32
        else:
            bid = max(DAILY_SALARY * 0.42, highest_prev + 1.0)
        if desperate_opps >= 2:
            bid *= 0.9
        return float(min(budget, bid))

    bid = DAILY_SALARY * 0.5
    if highest_prev > 0:
        if highest_prev <= DAILY_SALARY * 0.8:
            bid = max(bid, highest_prev + 1.5)
        elif highest_prev >= 160:
            bid = DAILY_SALARY * 0.3
        else:
            bid = max(DAILY_SALARY * 0.45, avg_prev * 0.7)

    if day >= 8 and budget > DAILY_SALARY * 2.5 and hp >= 5:
        bid = max(bid, DAILY_SALARY * 0.62)

    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    max_opp_budget = 0.0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > max_opp_budget:
                max_opp_budget = opp.get('budget', 0)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply / float(WATER_REQ)
    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif urgent:
        bid = max(DAILY_SALARY * 0.82, highest_prev + 1.5)
    else:
        if scarcity <= 1.2:
            bid = max(DAILY_SALARY * 0.72, highest_prev + 1.0)
        elif scarcity <= 1.5:
            bid = max(DAILY_SALARY * 0.60, avg_prev + 0.5)
        else:
            bid = max(DAILY_SALARY * 0.48, avg_prev * 0.9)

    if highest_prev >= DAILY_SALARY * 1.4 and hp > 4 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.45)

    if max_opp_budget > budget * 1.8 and not urgent:
        bid *= 0.92

    if budget < DAILY_SALARY * 1.2:
        if critical:
            bid = max(bid, budget * 0.9)
        else:
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return max(0.0, min(budget, 1.0))

    prev_bids = []
    threat_bids = []
    rich_threat = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid')
        if b is not None:
            prev_bids.append(float(b))
            if opp.get('budget', 0) >= DAILY_SALARY * 0.8:
                threat_bids.append(float(b))
        rich_threat = max(rich_threat, float(opp.get('budget', 0)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat_prev = max(threat_bids) if threat_bids else highest_prev

    tight_supply = supply <= 17
    very_tight = supply <= 16
    abundant = supply >= 22

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

    if very_tight:
        urgency += 2
    elif tight_supply:
        urgency += 1
    elif abundant:
        urgency -= 1

    if budget < DAILY_SALARY:
        urgency += 1
    if budget > 250:
        urgency -= 1

    if urgency <= 0:
        base = 8.0 if abundant else 12.0
        if highest_prev >= 100:
            bid = base
        elif highest_prev >= 80:
            bid = max(base, 18.0)
        else:
            bid = max(base, min(28.0, highest_prev * 0.55 + 3.0))
    elif urgency == 1:
        if highest_threat_prev >= 100:
            bid = 38.0 if not tight_supply else 52.0
        else:
            bid = max(26.0, min(60.0, highest_threat_prev + 2.0))
    elif urgency == 2:
        if highest_threat_prev >= 105:
            bid = 72.0
        else:
            bid = max(45.0, min(78.0, highest_threat_prev + 4.0))
    elif urgency == 3:
        if highest_threat_prev >= 110:
            bid = 88.0
        else:
            bid = max(62.0, min(92.0, highest_threat_prev + 6.0))
    else:
        if highest_threat_prev >= 110:
            bid = 108.0
        else:
            bid = max(85.0, min(118.0, highest_threat_prev + 8.0))

    if day >= 8 and hp >= 6 and no_water_days == 0 and highest_prev >= 90:
        bid = min(bid, 24.0)

    if budget <= 25:
        bid = min(bid, budget)
    else:
        reserve = 10.0 if day < 8 else 0.0
        bid = min(bid, max(0.0, budget - reserve))

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 95.0))

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
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
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    critical_self = (hp <= 3) or (no_water_days >= 1)
    fragile_self = (hp <= 5)
    many_alive = len(alive_opponents) >= 3

    if critical_self:
        bid = max(92.0, highest_prev + 2.5)
        if supply <= 17:
            bid += 10.0
        if rich_opp >= 2:
            bid += 6.0
    elif fragile_self:
        bid = 58.0 + 18.0 * scarcity
        if highest_prev > 0:
            bid = max(bid, min(highest_prev + 1.5, 96.0))
        if urgent_opp >= 2:
            bid += 6.0
    else:
        if highest_prev >= 120.0:
            bid = 24.0 if supply >= 20 else 34.0
        elif highest_prev >= 90.0:
            bid = 36.0 + 10.0 * scarcity
        elif highest_prev >= 60.0:
            bid = highest_prev + 1.25
        elif highest_prev > 0.0:
            bid = max(34.0 + 8.0 * scarcity, avg_prev + 2.0)
        else:
            bid = 32.0 + 10.0 * scarcity

        if many_alive and supply <= 17:
            bid += 8.0
        if day >= 8 and hp >= 7:
            bid -= 4.0

    if budget < DAILY_SALARY and not critical_self:
        bid = min(bid, budget * 0.72)
    elif budget < 120 and fragile_self:
        bid = min(bid, budget * 0.9)

    min_survival_bid = 0.0
    if critical_self:
        min_survival_bid = 55.0
    elif fragile_self and supply <= 17:
        min_survival_bid = 42.0

    bid = max(bid, min_survival_bid)
    bid = min(bid, budget)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
        base = 18.0 if hp > 3 else 42.0
        return float(max(0.0, min(budget, base)))

    opp_bids = []
    bob_bid = None
    cindy_bid = None
    dangerous_count = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev and prev.get('bid') is not None:
            bid = float(prev.get('bid'))
            opp_bids.append(bid)
        req = opp.get('water_requirement', WATER_REQ)
        obudget = opp.get('budget', 0)
        ohp = opp.get('hp', 0)
        if oid == 'Bob' and bid is not None:
            bob_bid = bid
        if oid == 'Cindy' and bid is not None:
            cindy_bid = bid
        if req >= WATER_REQ and obudget > 0 and ohp > 0:
            dangerous_count += 1

    high_supply = supply >= 22
    low_supply = supply <= 17
    very_low_supply = supply <= 16

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
    if low_supply:
        urgency += 1
    if very_low_supply:
        urgency += 1
    if day >= 8:
        urgency += 1

    target = 0.0

    if urgency >= 5:
        if cindy_bid is not None and low_supply:
            target = max(95.0, cindy_bid + 3.0)
        elif bob_bid is not None:
            target = max(72.0, bob_bid + 2.5)
        else:
            target = 84.0
    elif urgency >= 3:
        if low_supply:
            if bob_bid is not None:
                target = max(58.0, bob_bid + 2.0)
            else:
                target = 61.0
            if cindy_bid is not None and cindy_bid < 90:
                target = max(target, cindy_bid + 2.0)
        else:
            if bob_bid is not None:
                target = max(50.0, bob_bid + 1.5)
            else:
                target = 52.0
    else:
        if high_supply:
            target = 24.0
            if bob_bid is not None:
                target = min(38.0, max(24.0, bob_bid - 10.0))
        elif low_supply:
            if cindy_bid is not None and cindy_bid > 100:
                target = 34.0
            elif bob_bid is not None:
                target = max(49.0, bob_bid + 1.2)
            else:
                target = 48.0
        else:
            if bob_bid is not None:
                target = max(46.0, bob_bid + 1.0)
            else:
                target = 47.0

    if cindy_bid is not None and cindy_bid >= 120 and urgency <= 3 and not very_low_supply:
        target = min(target, 44.0 if not low_supply else 50.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = max(0.0, (10 - day) * 18.0)
    affordable = max(0.0, budget - reserve_floor)

    if urgency >= 4:
        bid = min(budget, max(target, affordable * 0.6 if affordable > 0 else target))
    else:
        bid = min(budget, target)
        if affordable > 0:
            bid = min(bid, max(affordable, 0.0) + 8.0)

    if hp <= 1 or no_water_days >= 2:
        bid = max(bid, min(budget, 96.0))

    if high_supply and urgency == 0:
        bid = min(bid, 28.0)

    return float(max(0.0, min(budget, bid)))
"""
