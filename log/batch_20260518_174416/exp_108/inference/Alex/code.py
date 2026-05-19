# ============================================================
# Experiment: exp_108
# Agent: Alex
# Source: exp_108
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
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 63)
        return min(budget, 28)

    total_alive = 1 + len(alive_opponents)
    expected_winners = max(1, int(supply // WATER_REQ))
    scarcity = total_alive - expected_winners

    prev_bids = []
    desperate_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opponents += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opponents += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
            status = prev.get('status')
            hp_after = prev.get('hp_after')
            if status == 'failed' or (hp_after is not None and hp_after <= 2):
                desperate_opponents += 1

    highest_prev = max(prev_bids) if prev_bids else 0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0

    if hp <= 2 or no_water_days >= 2:
        target = max(60, highest_prev + 2)
    elif hp <= 4 or no_water_days >= 1:
        target = max(45, avg_prev + 3)
    else:
        if scarcity >= 2:
            target = max(36, avg_prev + 2)
        elif scarcity == 1:
            target = max(28, avg_prev + 1)
        else:
            target = 18

    if desperate_opponents >= expected_winners:
        target += 8
    elif desperate_opponents == 0 and scarcity <= 1:
        target -= 4

    if highest_prev >= 60 and hp > 4 and no_water_days == 0:
        target = min(target, 26)

    if rich_opponents >= len(alive_opponents) and hp > 3 and no_water_days == 0:
        target = min(target, 30)

    if budget < DAILY_SALARY:
        target = min(target, budget * 0.75)

    target = max(0, min(budget, target))
    return float(target)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    opp_max_budget = 0.0
    urgent_opp = 0
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0.0) > opp_max_budget:
                opp_max_budget = opp.get('budget', 0.0)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive:
        return float(min(budget, 1.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply <= 18.0
    very_scarce = supply <= 16.0

    if hp <= 2 or no_water >= 2:
        target = max(highest_prev + 2.5, DAILY_SALARY * 1.55)
        if budget < target:
            target = budget
        return float(max(0.0, min(budget, target)))

    if hp <= 4 or no_water >= 1:
        if very_scarce:
            target = max(highest_prev + 2.0, DAILY_SALARY * 1.45)
        else:
            target = max(highest_prev + 1.5, DAILY_SALARY * 1.2)
        return float(max(0.0, min(budget, target)))

    if day <= 2:
        if scarcity:
            target = DAILY_SALARY * 0.18
        else:
            target = DAILY_SALARY * 0.08
        return float(max(0.0, min(budget, target)))

    if highest_prev >= 120.0:
        if hp >= 7 and no_water == 0:
            target = DAILY_SALARY * 0.05
        else:
            target = DAILY_SALARY * 0.35
        return float(max(0.0, min(budget, target)))

    if urgent_opp >= 2 and hp >= 6:
        target = DAILY_SALARY * 0.1
        return float(max(0.0, min(budget, target)))

    if scarcity:
        target = max(DAILY_SALARY * 0.22, avg_prev * 0.22)
    else:
        target = max(DAILY_SALARY * 0.12, avg_prev * 0.15)

    if day >= 8 and hp >= 6 and budget > opp_max_budget * 0.6:
        target = min(target, DAILY_SALARY * 0.08)

    return float(max(0.0, min(budget, target)))
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water >= 1:
            return float(min(budget, 28.0))
        return float(min(budget, 12.0))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 150:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    contested_supply = supply <= 18
    abundant_supply = supply >= 22

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
    if contested_supply:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1

    if urgency >= 5:
        bid = max(62.0, highest_prev * 0.42)
    elif urgency >= 3:
        if highest_prev >= 180:
            bid = 34.0 if hp > 3 else 58.0
        else:
            bid = max(28.0, min(55.0, avg_prev * 0.55 + 6.0))
    else:
        if highest_prev >= 150:
            bid = 8.0 if abundant_supply else 14.0
        elif highest_prev >= 90:
            bid = 16.0 if abundant_supply else 22.0
        else:
            bid = 18.0 if abundant_supply else 26.0

    if day >= 8:
        bid += 6.0
    if rich_count >= 2 and urgency <= 2:
        bid -= 4.0
    if abundant_supply and urgency <= 2:
        bid -= 4.0

    min_survival = 0.0
    if hp <= 2 or no_water >= 2:
        min_survival = 60.0
    elif hp <= 4 or no_water >= 1:
        min_survival = 32.0

    bid = max(bid, min_survival)
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if b >= 60:
                    aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 8.0 if hp > 3 else 18.0))

    units = supply / WATER_REQ
    can_only_feed_one = units < 2.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    if urgency >= 5:
        bid = 68.0
    elif urgency >= 3:
        bid = 52.0 if highest_prev < 60 else highest_prev + 2.0
    else:
        if can_only_feed_one:
            if highest_prev >= 80:
                bid = 18.0
            elif highest_prev >= 55:
                bid = 36.0
            elif highest_prev > 0:
                bid = max(22.0, highest_prev + 1.5)
            else:
                bid = 16.0
        else:
            if aggressive >= 2:
                bid = 28.0
            elif highest_prev >= 60:
                bid = 24.0
            elif avg_prev > 0:
                bid = max(14.0, min(26.0, avg_prev * 0.55 + 4.0))
            else:
                bid = 12.0

    if budget < 25:
        bid = min(bid, budget)
    elif budget < 60 and urgency < 3:
        bid = min(bid, 32.0)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(0.92 * DAILY_SALARY, budget))

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_prev = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80:
                    strong_prev.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.6))
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    alive_count = len(alive_opponents)

    scarce = supply <= 18
    ample = supply >= 22
    urgent = hp <= 4 or no_water_days >= 2
    caution = hp <= 6 or no_water_days >= 1

    if urgent:
        if highest_prev > 0:
            bid = highest_prev + 2.0
        else:
            bid = DAILY_SALARY * 0.95
    elif scarce:
        if highest_prev >= 95:
            bid = highest_prev + 1.5
        elif highest_prev >= 80:
            bid = highest_prev + 2.5
        else:
            bid = DAILY_SALARY * 0.9
    elif ample:
        if caution:
            bid = max(DAILY_SALARY * 0.55, highest_prev * 0.82 if highest_prev > 0 else 0)
        else:
            bid = max(DAILY_SALARY * 0.35, highest_prev * 0.65 if highest_prev > 0 else 0)
    else:
        if caution:
            bid = max(DAILY_SALARY * 0.7, highest_prev + 1.0 if highest_prev > 0 else 0)
        else:
            bid = max(DAILY_SALARY * 0.5, highest_prev * 0.78 if highest_prev > 0 else 0)

    if alive_count >= 3 and scarce:
        bid += 3.0
    elif alive_count == 1 and not urgent:
        bid *= 0.8

    if budget < DAILY_SALARY:
        bid = min(bid, budget * (0.92 if urgent else 0.75))

    bid = min(bid, budget)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    strong_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) > 60:
                    strong_prev.append(float(bid))

    if not alive:
        return max(0.0, min(float(budget), 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev = sorted_bids[int(1)]

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water >= 2:
        urgency += 0.8
    elif no_water == 1:
        urgency += 0.35
    if day >= 8:
        urgency += 0.15
    urgency += 0.35 * scarcity

    if hp <= 2 or no_water >= 2:
        target = max(88.0, highest_prev + 2.5)
    elif urgency >= 1.0:
        target = max(72.0, second_prev + 1.5, highest_prev * 0.9)
    elif scarcity >= 0.7:
        target = max(58.0, second_prev + 1.0)
    elif scarcity <= 0.25 and hp >= 5 and no_water == 0:
        target = 16.0
    else:
        if highest_prev >= 110:
            target = 24.0 if hp >= 5 else 68.0
        elif highest_prev >= 90:
            target = 30.0 if hp >= 5 else 74.0
        elif highest_prev >= 70:
            target = max(34.0, second_prev * 0.85)
        else:
            target = 28.0 + 18.0 * scarcity

    if budget < DAILY_SALARY:
        target *= 0.9
    if budget < 40:
        target = min(target, budget)

    floor_bid = 8.0 if hp > 4 and no_water == 0 else 18.0
    bid = max(floor_bid, target)
    bid = min(float(budget), bid)
    if bid < 0:
        bid = 0.0
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
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    yesterday_bids = []
    dangerous_bids = []
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            yesterday_bids.append(float(bid))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                dangerous_bids.append(float(bid))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    highest_danger = max(dangerous_bids) if dangerous_bids else highest_prev

    alive_count = len(alive)
    contested = supply < WATER_REQ * 2
    very_tight = supply <= 18

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

    if contested:
        urgency += 1
    if very_tight:
        urgency += 1
    if alive_count >= 3:
        urgency += 1

    if urgency >= 5:
        target = max(92.0, highest_danger + 2.5)
    elif urgency >= 3:
        target = max(68.0, min(96.0, highest_prev + 1.5))
    else:
        if contested:
            target = max(42.0, min(72.0, highest_prev * 0.72))
        else:
            target = 24.0
            if highest_prev > 110:
                target = 19.0
            elif highest_prev > 80:
                target = 22.0

    if day >= 8 and hp > 4 and no_water_days == 0:
        target *= 0.9

    reserve = 0.0
    if day < 10:
        reserve = max(0.0, (10 - day) * 8.0)
    max_affordable = max(0.0, budget - reserve)
    if urgency >= 4:
        max_affordable = budget

    bid = min(target, max_affordable)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, highest_danger + 3.0, 98.0))

    if bid < 0:
        bid = 0.0
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    highest_prev = 0.0
    eric_prev = None
    urgent_opp = 0
    rich_opp = 0

    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opp += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            if bid > highest_prev:
                highest_prev = bid
            if oid == 'Eric':
                eric_prev = bid

    tight_supply = supply <= 17
    loose_supply = supply >= 22
    critical_me = hp <= 3 or no_water >= 1
    fragile_me = hp <= 5

    base = DAILY_SALARY * 0.42

    if loose_supply:
        base = DAILY_SALARY * 0.28
    elif tight_supply:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.45

    if eric_prev is not None:
        if eric_prev >= 120:
            if critical_me:
                base = max(base, DAILY_SALARY * 0.98)
            elif fragile_me:
                base = max(base, DAILY_SALARY * 0.72)
            else:
                base = min(base, DAILY_SALARY * 0.26)
        elif eric_prev >= 90:
            if tight_supply or critical_me:
                base = max(base, eric_prev * 0.78)
            else:
                base = max(base, DAILY_SALARY * 0.40)
        elif eric_prev >= 60:
            base = max(base, eric_prev + 2.0)
        else:
            base = max(base, DAILY_SALARY * 0.5)
    else:
        if highest_prev > 0:
            base = max(base, min(highest_prev + 1.5, DAILY_SALARY * 0.8))

    if urgent_opp >= 2 and not critical_me:
        base *= 0.9

    if rich_opp >= 2 and tight_supply:
        base = max(base, DAILY_SALARY * 0.75)

    if critical_me:
        base = max(base, DAILY_SALARY * 0.95)
    elif fragile_me and tight_supply:
        base = max(base, DAILY_SALARY * 0.78)

    if day >= 8:
        if hp > 5:
            base *= 0.92
        else:
            base = max(base, DAILY_SALARY * 0.82)

    reserve = 0.0
    if hp > 6:
        reserve = DAILY_SALARY * 0.6
    elif hp > 3:
        reserve = DAILY_SALARY * 0.35
    else:
        reserve = 0.0

    max_affordable = max(0.0, budget - reserve)
    if critical_me:
        max_affordable = budget

    bid = min(base, max_affordable)

    if bid < 0:
        bid = 0.0

    if bid == 0 and critical_me and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.85)

    return float(round(min(bid, budget), 2))
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.35)

    prev_bids = []
    prev_high_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 500:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 110:
                    prev_high_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = 1.0 - max(0.0, min(1.0, supply_ratio))

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.45
    urgency += scarcity * 0.7
    if day >= 8:
        urgency += 0.15

    if hp <= 2 or no_water_days >= 2:
        target = max(118.0, highest_prev + 2.0, DAILY_SALARY * 1.7)
    elif hp <= 4 or no_water_days >= 1:
        target = max(96.0, avg_prev * 0.9, highest_prev - 4.0)
    else:
        if supply >= 22:
            target = 48.0
        elif supply >= 19:
            target = 62.0
        else:
            target = 78.0

        if highest_prev >= 130 and urgency < 0.8:
            target = min(target, 60.0)
        elif highest_prev >= 115 and scarcity > 0.5:
            target = max(target, 82.0)

    if desperate_count >= 2 and scarcity > 0.4:
        target += 8.0
    if rich_count >= 2 and highest_prev >= 115:
        target += 5.0

    if budget < 140:
        target = min(target, budget * 0.72)
    elif budget < 250:
        target = min(target, budget * 0.6)

    target = max(0.0, min(float(target), float(budget)))
    return target
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) <= float(opp.get('budget', 0)) + float(opp.get('daily_salary', 0)):
                    dangerous_prev.append(float(bid))

    if not alive:
        return max(0.0, min(float(budget), 18.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    max_danger = max(dangerous_prev) if dangerous_prev else max_prev
    low_supply = supply <= 17.0
    high_supply = supply >= 22.0

    if hp <= 2 or no_water >= 2:
        bid = max(78.0, max_danger + 2.0)
        return max(0.0, min(float(budget), bid))

    if hp <= 4 or no_water >= 1:
        if low_supply:
            bid = max(74.0, min(max_danger + 1.5, 92.0))
        else:
            bid = max(62.0, min(max_danger, 82.0))
        return max(0.0, min(float(budget), bid))

    if high_supply:
        if max_prev >= 120.0:
            bid = 24.0
        elif max_prev >= 75.0:
            bid = 38.0
        else:
            bid = 32.0
        return max(0.0, min(float(budget), bid))

    if low_supply:
        if max_danger >= 120.0:
            bid = 68.0
        elif max_danger >= 70.0:
            bid = min(max_danger + 1.0, 76.0)
        else:
            bid = 58.0
        return max(0.0, min(float(budget), bid))

    if max_danger >= 120.0:
        bid = 42.0
    elif max_danger >= 75.0:
        bid = 55.0
    elif max_danger >= 65.0:
        bid = min(max_danger + 1.0, 72.0)
    else:
        bid = 48.0

    return max(0.0, min(float(budget), bid))
"""
