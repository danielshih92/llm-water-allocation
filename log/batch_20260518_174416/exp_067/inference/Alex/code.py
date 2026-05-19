# ============================================================
# Experiment: exp_067
# Agent: Alex
# Source: exp_067
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
    desperate_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])

    players_alive = 1 + len(alive_opponents)
    likely_units = max(1, int(supply // WATER_REQ))
    scarcity = players_alive - likely_units

    if hp <= 2 or no_water >= 2:
        base = DAILY_SALARY * 0.96
    elif hp <= 4 or no_water >= 1:
        base = DAILY_SALARY * 0.78
    else:
        if scarcity >= 2:
            base = DAILY_SALARY * 0.68
        elif scarcity >= 1:
            base = DAILY_SALARY * 0.58
        else:
            base = DAILY_SALARY * 0.42

    if desperate_count >= max(1, len(alive_opponents) // 2):
        base += 6

    if prev_bids:
        highest_prev = max(prev_bids)
        if hp <= 4 or no_water >= 1 or scarcity >= 1:
            target = highest_prev + 1.5
            if target > base:
                base = target
        else:
            if highest_prev >= DAILY_SALARY * 0.85:
                base = min(base, DAILY_SALARY * 0.45)

    if len(alive_opponents) == 0:
        base = DAILY_SALARY * 0.35 if hp > 3 else DAILY_SALARY * 0.75

    if supply >= 24 and hp > 4 and no_water == 0:
        base -= 4
    elif supply <= 16:
        base += 5

    bid = max(0, min(budget, base))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opponents += 1
            if opp.get('budget', 0) >= budget:
                rich_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 2.5)
        return float(min(budget, bid))

    if hp <= 4 or no_water_days >= 1:
        if tight_supply:
            bid = max(0.82 * DAILY_SALARY, highest_prev + 1.5)
        else:
            bid = max(0.68 * DAILY_SALARY, min(highest_prev * 0.9, highest_prev - 3.0 if highest_prev > 0 else 48.0))
        return float(min(budget, bid))

    base = 0.34 * DAILY_SALARY
    if tight_supply:
        base = 0.48 * DAILY_SALARY
    elif loose_supply:
        base = 0.24 * DAILY_SALARY

    if highest_prev >= 0.85 * DAILY_SALARY:
        bid = base
    elif highest_prev > 0:
        bid = max(base, min(0.62 * DAILY_SALARY, avg_prev * 0.55))
    else:
        bid = base

    if urgent_opponents >= 2 and hp >= 5:
        bid *= 0.85
    if rich_opponents >= 2 and tight_supply and hp <= 5:
        bid = max(bid, 0.58 * DAILY_SALARY)

    if day >= 8 and hp >= 6 and budget < 250:
        bid *= 0.8

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
    desperate_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_opponents += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 100 and opp.get('budget', 0) >= 100:
                    rich_aggressive += 1

    if not alive_opponents:
        return float(min(budget, 20.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if tight_supply:
        urgency += 2
    if desperate_opponents >= 2:
        urgency += 1

    if urgency >= 7:
        bid = max(95.0, max_prev + 3.0)
    elif urgency >= 5:
        bid = max(72.0, min(110.0, avg_prev * 0.7 + 8.0))
    elif urgency >= 3:
        if max_prev >= 120:
            bid = 46.0 if loose_supply else 58.0
        else:
            bid = max(42.0, min(75.0, max_prev * 0.55 + 6.0))
    else:
        if rich_aggressive >= 2 or max_prev >= 120:
            bid = 18.0 if loose_supply else 26.0
        elif max_prev >= 80:
            bid = 24.0 if loose_supply else 34.0
        else:
            bid = 32.0

    if day >= 8:
        bid += 8.0
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        bid += 12.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 120.0
    elif day <= 9:
        reserve_floor = 50.0

    max_affordable = budget
    if budget > reserve_floor:
        max_affordable = budget - reserve_floor + min(20.0, DAILY_SALARY * 0.3)

    bid = min(bid, budget, max_affordable)
    if urgency >= 5:
        bid = min(max(bid, 65.0), budget)

    if bid < 0:
        bid = 0.0
    return float(bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_aggressive = 0
    weak_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                weak_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 120 and opp.get('budget', 0) >= 120:
                    rich_aggressive += 1

    if not alive:
        return float(min(budget, 18.0))

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

    if supply_tight:
        urgency += 2
    elif not supply_loose:
        urgency += 1

    if day >= 8:
        urgency += 1

    if highest_prev >= 120:
        if urgency <= 1:
            bid = 8.0 if supply_loose else 12.0
        elif urgency <= 3:
            bid = 28.0 if supply_loose else 42.0
        else:
            bid = 78.0 if supply_loose else 96.0
    else:
        if urgency <= 1:
            bid = 18.0 if supply_loose else 24.0
        elif urgency <= 3:
            bid = max(38.0, avg_prev + 4.0)
        else:
            bid = max(65.0, highest_prev + 6.0)

    if weak_opp >= 2 and urgency <= 2:
        bid *= 0.85

    if rich_aggressive >= 2 and urgency <= 2:
        bid *= 0.8

    reserve_target = 0.0
    days_left = max(0, 10 - day)
    if hp > 4 and no_water_days == 0:
        reserve_target = min(140.0, days_left * 10.0)
    elif hp > 2:
        reserve_target = min(90.0, days_left * 6.0)

    max_affordable = max(0.0, budget - reserve_target)
    if urgency >= 4:
        max_affordable = budget
    elif max_affordable < 5.0:
        max_affordable = min(budget, 20.0)

    bid = min(bid, max_affordable)

    if urgency >= 5:
        bid = max(bid, min(budget, 90.0))
    elif urgency >= 3:
        bid = max(bid, min(budget, 45.0))

    if supply_loose and urgency <= 1:
        bid = min(bid, 20.0)

    if bid < 0:
        bid = 0.0

    return float(min(budget, round(bid, 2)))
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.25)
        return max(0.0, float(bid))

    opp_prev_bids = []
    cindy_prev = None
    desperate_count = 0
    rich_alive = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_alive += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            opp_prev_bids.append(float(pbid))
        if oid == 'Cindy' and pbid is not None:
            cindy_prev = float(pbid)

    highest_prev = max(opp_prev_bids) if opp_prev_bids else 0.0
    avg_prev = sum(opp_prev_bids) / len(opp_prev_bids) if opp_prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

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
    if day >= 8:
        urgency += 1

    if cindy_prev is None:
        cindy_prev = highest_prev

    if urgency >= 5:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif urgency >= 3:
        if scarcity >= 1:
            target = max(DAILY_SALARY * 0.72, min(cindy_prev * 0.78, DAILY_SALARY * 1.02))
        else:
            target = max(DAILY_SALARY * 0.52, avg_prev + 3.0)
    else:
        if scarcity == 2:
            target = max(DAILY_SALARY * 0.58, min(cindy_prev * 0.68, DAILY_SALARY * 0.92))
        elif scarcity == 1:
            target = max(DAILY_SALARY * 0.42, min(avg_prev + 1.5, DAILY_SALARY * 0.7))
        else:
            target = DAILY_SALARY * 0.22

    if desperate_count >= 2 and urgency < 5:
        target += 6.0
    if rich_alive <= 1 and urgency <= 1:
        target -= 4.0
    if supply >= 23 and urgency <= 2:
        target -= 5.0

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget / max(1, reserve_days)
    if urgency <= 1:
        target = min(target, soft_cap * 0.9 + DAILY_SALARY * 0.15)
    elif urgency <= 3:
        target = min(target, soft_cap * 1.2 + DAILY_SALARY * 0.2)

    min_safe = 0.0
    if urgency >= 5:
        min_safe = DAILY_SALARY * 0.8
    elif urgency >= 3:
        min_safe = DAILY_SALARY * 0.5

    bid = max(min_safe, target)
    bid = min(budget, bid)
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
            alive.append(opp)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    max_affordable_threat = 0.0

    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 1.2:
            rich_opp += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            affordable = min(float(bid), float(opp.get('budget', 0) + opp.get('daily_salary', 0)))
            if affordable > max_affordable_threat:
                max_affordable_threat = affordable

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, max_affordable_threat + 2.0)
    elif hp <= 4 or no_water_days >= 1:
        if tight_supply:
            bid = max(DAILY_SALARY * 0.82, max_affordable_threat + 1.5)
        else:
            bid = max(DAILY_SALARY * 0.72, avg_prev + 1.0)
    else:
        if tight_supply:
            bid = max(DAILY_SALARY * 0.62, avg_prev + 1.0)
        elif loose_supply:
            bid = DAILY_SALARY * 0.34
        else:
            bid = DAILY_SALARY * 0.48

    if urgent_opp >= 2:
        bid += 6.0
    elif urgent_opp == 1:
        bid += 3.0

    if rich_opp >= 2 and tight_supply:
        bid += 4.0

    if highest_prev >= 140:
        bid = min(bid, DAILY_SALARY * 0.78 if hp > 4 and no_water_days == 0 else bid)
    elif highest_prev >= 100 and hp > 5 and no_water_days == 0 and not tight_supply:
        bid = min(bid, DAILY_SALARY * 0.55)

    if day >= 8:
        bid += 5.0
    if day == 10:
        bid += 8.0

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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive_count = 0
    rich_alive = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 200:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= DAILY_SALARY * 0.85:
                    aggressive_count += 1

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.2))

    slots = supply / float(WATER_REQ)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 0.0
        avg_prev = 0.0

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
        danger += 1

    if slots <= 1.05:
        danger += 3
    elif slots <= 1.35:
        danger += 2
    elif slots <= 1.7:
        danger += 1

    if aggressive_count >= 1:
        danger += 1
    if rich_alive >= 1:
        danger += 1

    if day >= 8:
        danger += 1

    if danger <= 1:
        bid = DAILY_SALARY * 0.22
    elif danger == 2:
        bid = DAILY_SALARY * 0.34
    elif danger == 3:
        bid = DAILY_SALARY * 0.48
    elif danger == 4:
        bid = DAILY_SALARY * 0.62
    elif danger == 5:
        bid = DAILY_SALARY * 0.78
    else:
        bid = DAILY_SALARY * 0.93

    if highest_prev > 0:
        if danger >= 5:
            bid = max(bid, min(DAILY_SALARY * 0.98, highest_prev + 2.0))
        elif danger >= 3:
            bid = max(bid, min(DAILY_SALARY * 0.75, avg_prev + 1.0))
        else:
            bid = min(bid, highest_prev * 0.7)

    if slots >= 1.9 and hp >= 5:
        bid = min(bid, DAILY_SALARY * 0.25)

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.7)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

    return max(0.0, min(budget, bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_budgets = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            opp_budgets.append(opp.get('budget', 0))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.25))

    prev_bids_sorted = sorted(prev_bids, reverse=True)
    highest_prev = prev_bids_sorted[int(0)] if len(prev_bids_sorted) >= 1 else DAILY_SALARY * 0.7
    second_prev = prev_bids_sorted[int(1)] if len(prev_bids_sorted) >= 2 else highest_prev * 0.9

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

    if supply <= 16:
        urgency += 2
    elif supply <= 19:
        urgency += 1

    if day >= 8:
        urgency += 1

    rich_opponents = 0
    for b in opp_budgets:
        if b >= budget:
            rich_opponents += 1
    if rich_opponents >= 2:
        urgency += 1

    if urgency >= 6:
        target = max(highest_prev + 2.0, DAILY_SALARY * 1.4)
    elif urgency >= 4:
        target = max(second_prev + 2.0, DAILY_SALARY * 1.05)
    elif urgency >= 2:
        target = max(DAILY_SALARY * 0.72, second_prev * 0.92)
    else:
        if highest_prev >= DAILY_SALARY * 1.3:
            target = DAILY_SALARY * 0.32
        elif highest_prev >= DAILY_SALARY * 1.0:
            target = DAILY_SALARY * 0.45
        else:
            target = DAILY_SALARY * 0.58

    if budget < DAILY_SALARY * 0.8 and urgency < 4:
        target = min(target, DAILY_SALARY * 0.5)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.95)

    return float(max(0.0, min(budget, target)))
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

    alive = []
    prev_bids = []
    rich_aggressive = 0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 115 and opp.get('budget', 0) >= 400:
                    rich_aggressive += 1

    if not alive:
        return max(0.0, min(float(budget), 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    critical = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if critical:
        target = max(95.0, highest_prev + 2.0)
        if tight_supply:
            target = max(target, 128.0)
        return max(0.0, min(float(budget), target))

    if tight_supply:
        if rich_aggressive >= 2 and hp >= 6 and no_water_days == 0:
            target = 24.0
        else:
            target = max(72.0, min(118.0, avg_prev * 0.72 + 8.0))
            if pressured:
                target = max(target, highest_prev + 1.0)
        return max(0.0, min(float(budget), target))

    if medium_supply:
        if pressured:
            target = max(58.0, min(98.0, highest_prev * 0.62 + 6.0))
        else:
            target = 34.0 if rich_aggressive >= 1 else 42.0
        return max(0.0, min(float(budget), target))

    if hp >= 7 and no_water_days == 0:
        target = 16.0 if rich_aggressive >= 1 else 22.0
    elif pressured:
        target = 48.0
    else:
        target = 28.0

    if day >= 8 and hp <= 6:
        target = max(target, 60.0)

    return max(0.0, min(float(budget), target))
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
    no_water = my_status['no_water_days']

    def clamp_bid(x):
        if x < 0:
            x = 0
        if x > budget:
            x = budget
        return float(x)

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        if hp <= 3 or no_water >= 1:
            return clamp_bid(DAILY_SALARY * 0.75)
        return clamp_bid(DAILY_SALARY * 0.25)

    capacity = supply / float(WATER_REQ)
    contested = capacity < (1 + len(alive))
    abundant = capacity >= (1 + len(alive))

    prev_bids = []
    pressure = 0.0
    desperate_count = 0
    rich_aggressive = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        pbid = None
        if prev and prev.get('bid') is not None:
            pbid = prev.get('bid')
            prev_bids.append(float(pbid))
        ohp = opp.get('hp', 10)
        onw = opp.get('no_water_days', 0)
        obudget = opp.get('budget', 0)
        if ohp <= 3 or onw >= 1:
            desperate_count += 1
        if obudget >= 700 and pbid is not None and pbid >= 95:
            rich_aggressive += 1
        if pbid is not None:
            pressure += float(pbid)

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.7
    max_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.9

    emergency = hp <= 3 or no_water >= 1
    very_safe = hp >= 8 and no_water == 0

    if emergency:
        if contested:
            bid = max(DAILY_SALARY * 1.45, max_prev + 6)
        else:
            bid = max(DAILY_SALARY * 0.95, avg_prev + 3)
        return clamp_bid(bid)

    if abundant:
        bid = max(DAILY_SALARY * 0.32, min(DAILY_SALARY * 0.75, avg_prev * 0.72))
        if desperate_count >= 2:
            bid += 6
        return clamp_bid(bid)

    if contested and very_safe and rich_aggressive >= 1:
        return clamp_bid(DAILY_SALARY * 0.18)

    if contested:
        if max_prev >= 120:
            bid = DAILY_SALARY * 0.22 if hp >= 6 else DAILY_SALARY * 1.0
        elif max_prev >= 95:
            bid = max(DAILY_SALARY * 0.55, avg_prev + 2)
        else:
            bid = max(DAILY_SALARY * 0.48, max_prev + 1.5)
        if desperate_count >= 2:
            bid += 5
    else:
        bid = max(DAILY_SALARY * 0.4, avg_prev * 0.78)

    if budget < DAILY_SALARY * 2:
        bid = min(bid, budget * 0.65)
    elif budget > 900 and hp <= 5:
        bid += 8

    if day >= 8 and hp >= 7 and contested:
        bid *= 0.9

    return clamp_bid(bid)
"""
