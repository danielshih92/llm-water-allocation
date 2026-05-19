# ============================================================
# Experiment: exp_075
# Agent: Alex
# Source: exp_075
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return min(budget, 50)
        return min(budget, 22)

    max_prev_bid = 0
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > budget:
            rich_opponents += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid')
        if prev_bid is not None and prev_bid > max_prev_bid:
            max_prev_bid = prev_bid

    scarcity = 1.0 - ((supply - 15.0) / 10.0)
    if scarcity < 0:
        scarcity = 0
    if scarcity > 1:
        scarcity = 1

    if hp <= 1 or no_water >= 2:
        target = max(60, max_prev_bid + 3)
    elif hp <= 2 or no_water >= 1:
        target = max(48, max_prev_bid + 2)
    else:
        target = 24 + 18 * scarcity
        if max_prev_bid > 0:
            target = max(target, max_prev_bid + 1)

    if urgent_opponents >= 2:
        target += 4
    elif urgent_opponents == 1:
        target += 2

    if rich_opponents >= len(alive_opponents) / 2.0 and hp > 2 and no_water == 0:
        target -= 3

    if supply >= 23 and hp > 3 and no_water == 0:
        target -= 4
    elif supply <= 17:
        target += 4

    reserve = 0
    if hp > 2 and no_water == 0:
        reserve = 20
    elif hp > 1:
        reserve = 10

    affordable = budget - reserve
    if affordable < 0:
        affordable = budget

    bid = min(affordable, target)
    if bid < 0:
        bid = 0
    if hp <= 2 and bid < 35 and budget >= 35:
        bid = 35

    return min(budget, bid)
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
    urgent_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0.0))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22
    emergency = hp <= 2 or no_water_days >= 2
    danger = hp <= 4 or no_water_days >= 1

    if emergency:
        bid = max(72.0, highest_prev + 4.0)
        if tight_supply:
            bid += 8.0
        return float(min(budget, bid))

    if danger:
        bid = max(46.0, avg_prev + 3.0)
        if highest_prev >= 85.0:
            bid = 52.0
        if tight_supply:
            bid += 8.0
        elif ample_supply:
            bid -= 4.0
        return float(max(0.0, min(budget, bid)))

    if highest_prev >= 95.0:
        bid = 18.0 if ample_supply else 24.0
    elif highest_prev >= 75.0:
        bid = 22.0 if ample_supply else 30.0
    elif highest_prev >= 45.0:
        bid = highest_prev * 0.72
    elif highest_prev > 0.0:
        bid = max(20.0, highest_prev + 1.5)
    else:
        bid = 24.0

    if tight_supply:
        bid += 6.0 + 2.0 * urgent_opp
    elif ample_supply:
        bid -= 4.0

    if rich_opp >= 2 and not ample_supply:
        bid += 3.0

    if day >= 8 and hp >= 7 and no_water_days == 0:
        bid -= 4.0

    bid = max(8.0, bid)
    return float(min(budget, bid))
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
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    prev_success_bids = []
    opp_pressure = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                status = prev.get('status')
                if status == 'won':
                    prev_success_bids.append(float(bid))
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                opp_pressure += 1.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    highest_success = max(prev_success_bids) if prev_success_bids else avg_prev

    supply_tight = (supply <= 17)
    supply_loose = (supply >= 22)

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
    elif supply <= 19:
        urgency += 1

    if opp_pressure >= 2:
        urgency += 1

    reserve_floor = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    spendable = max(0.0, budget - reserve_floor)
    if hp <= 2 or no_water_days >= 2:
        spendable = budget

    if urgency >= 6:
        target = max(DAILY_SALARY * 1.45, highest_prev + 3.0, highest_success + 2.0)
    elif urgency >= 4:
        target = max(DAILY_SALARY * 1.05, avg_prev + 3.0, highest_success * 0.9)
    elif urgency >= 2:
        if supply_loose:
            target = max(DAILY_SALARY * 0.42, avg_prev * 0.45)
        else:
            target = max(DAILY_SALARY * 0.62, avg_prev * 0.62)
    else:
        if supply_loose:
            target = DAILY_SALARY * 0.22
        else:
            target = DAILY_SALARY * 0.38

    if day >= 8:
        target *= 1.12
    if len(alive_opponents) <= 2:
        target *= 0.92
    if budget < DAILY_SALARY * 2:
        target *= 0.88

    bid = min(spendable, target)
    bid = min(budget, bid)
    bid = max(0.0, bid)
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

    day = day_context['day']
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > 250:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        return float(min(budget, 8.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    desperation = 0
    if hp <= 2:
        desperation += 3
    elif hp <= 4:
        desperation += 2
    elif hp <= 6:
        desperation += 1

    if no_water_days >= 2:
        desperation += 3
    elif no_water_days >= 1:
        desperation += 2

    if tight_supply:
        desperation += 1

    if day >= 8:
        desperation += 1

    if desperation >= 5:
        bid = max(62.0, high_prev + 3.0, avg_prev + 6.0)
    elif desperation >= 3:
        bid = max(42.0, avg_prev * 0.72, high_prev * 0.55)
    else:
        if loose_supply and high_prev >= 120:
            bid = 9.0
        elif loose_supply:
            bid = 16.0
        elif tight_supply:
            bid = max(24.0, avg_prev * 0.38)
        else:
            bid = max(18.0, avg_prev * 0.28)

    if rich_opp >= 1 and desperation <= 2:
        bid *= 0.9
    if urgent_opp >= 2 and desperation >= 3:
        bid *= 1.08

    if hp >= 8 and no_water_days == 0 and high_prev >= 140:
        bid = min(bid, 12.0)

    reserve = 0.0
    if day <= 7:
        reserve = 35.0
    elif day <= 9:
        reserve = 15.0

    max_affordable = max(0.0, budget - reserve)
    if desperation >= 5:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    slots = max(1, int(supply / WATER_REQ))
    tight = slots <= 1

    prev_bids = []
    aggressive_bids = []
    needy_count = 0
    rich_count = 0

    for opp in alive:
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            needy_count += 1
        if opp.get('budget', 0) >= 500:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= DAILY_SALARY * 1.8:
                aggressive_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        second_prev = sorted(prev_bids)[-2]
    elif len(prev_bids) == 1:
        second_prev = prev_bids[0]

    base = DAILY_SALARY * 0.42

    if tight:
        if aggressive_bids:
            target = max(DAILY_SALARY * 1.55, second_prev + 3.0)
        else:
            target = max(DAILY_SALARY * 0.82, highest_prev + 2.0)
    else:
        if highest_prev >= DAILY_SALARY * 1.5:
            target = DAILY_SALARY * 0.48
        else:
            target = max(base, highest_prev * 0.72)

    if rich_count >= 2 and tight:
        target += 8.0
    if needy_count >= 2 and tight:
        target += 6.0

    if hp <= 2:
        target = max(target, DAILY_SALARY * 1.15 if tight else DAILY_SALARY * 0.9)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.88)

    if no_water_days >= 2:
        target = max(target, DAILY_SALARY * 1.35)
    elif no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.95 if tight else DAILY_SALARY * 0.75)

    if budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.72 + 2.0)
    elif budget > 900 and tight:
        target += 5.0

    if day >= 8 and hp >= 6 and no_water_days == 0 and not tight:
        target = min(target, DAILY_SALARY * 0.38)

    bid = min(budget, max(0.0, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    weak_or_dead = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 120 and opp.get('budget', 0) >= 300:
                    rich_aggressive += 1
            if opp.get('budget', 0) <= 1 or opp.get('hp', 0) <= 0:
                weak_or_dead += 1
        else:
            weak_or_dead += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 10.0))

    high_supply = supply >= 22
    low_supply = supply <= 17

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev = sorted_bids[int(1)]
    elif len(prev_bids) == 1:
        second_prev = prev_bids[int(0)]

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
        urgency += 2
    elif not high_supply:
        urgency += 1

    if day >= 8:
        urgency += 1

    if rich_aggressive >= 2 and hp > 4 and no_water_days == 0 and high_supply:
        bid = 8.0
    else:
        if urgency >= 6:
            target = max(95.0, second_prev + 3.0)
            if highest_prev >= 150:
                target = max(target, 118.0)
            bid = target
        elif urgency >= 4:
            if highest_prev > 0 and highest_prev < 110:
                bid = highest_prev + 2.5
            else:
                bid = 58.0 if high_supply else 72.0
        elif urgency >= 2:
            if high_supply:
                bid = 24.0
            elif low_supply:
                bid = 44.0
            else:
                bid = 34.0
        else:
            bid = 12.0 if high_supply else 20.0

    if weak_or_dead >= 2 and urgency <= 3:
        bid *= 0.8

    reserve = 0.0
    if hp > 4 and no_water_days == 0:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.6

    max_affordable = max(0.0, budget - reserve)
    if urgency >= 5:
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
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if isinstance(prev, dict) else None
            if bid is not None:
                prev_bids.append(float(bid))

    if not alive:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, 40.0))
        return float(min(budget, 12.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    severe_need = hp <= 2 or no_water_days >= 2
    moderate_need = hp <= 4 or no_water_days >= 1
    tight_supply = supply <= 16.0
    medium_tight = supply <= 19.0
    abundant = supply >= 23.0

    if severe_need:
        target = max(72.0, high_prev + 2.0)
        if tight_supply:
            target = max(target, 95.0)
        return float(min(budget, target))

    if moderate_need:
        if high_prev >= 150.0:
            target = 58.0 if not tight_supply else 92.0
        else:
            target = max(52.0, avg_prev + 2.5)
            if tight_supply:
                target = max(target, 82.0)
        return float(min(budget, target))

    if abundant:
        if high_prev >= 140.0:
            return float(min(budget, 8.0))
        return float(min(budget, max(14.0, avg_prev * 0.35)))

    if medium_tight:
        if high_prev >= 160.0:
            target = 18.0
        elif high_prev >= 110.0:
            target = min(high_prev + 1.5, 76.0)
        else:
            target = max(34.0, avg_prev + 3.0)
        if urgent_opp >= 2:
            target += 6.0
        return float(min(budget, target))

    target = 22.0
    if high_prev >= 150.0:
        target = 12.0
    elif high_prev >= 100.0:
        target = min(high_prev + 1.0, 68.0)
    else:
        target = max(24.0, avg_prev + 2.0)

    if rich_opp >= 2 and hp >= 6:
        target *= 0.85
    if day >= 8 and hp >= 6:
        target *= 0.9

    return float(min(budget, max(0.0, target)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.35)
        return max(0.0, float(bid))

    prev_bids = []
    prev_live_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 2:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace') or {}
        bid_y = prev.get('bid')
        if bid_y is not None:
            prev_bids.append(float(bid_y))
            if prev.get('status') != 'dead':
                prev_live_bids.append(float(bid_y))

    max_prev = max(prev_bids) if prev_bids else 0.0
    max_live_prev = max(prev_live_bids) if prev_live_bids else max_prev
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 16.0
    ample_supply = supply >= 22.0

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
    if desperate_opp >= 2:
        urgency += 1

    if urgency >= 5:
        target = max(DAILY_SALARY * 1.15, max_live_prev + 8.0)
    elif urgency >= 3:
        target = max(DAILY_SALARY * 0.9, max_live_prev + 3.0)
    else:
        if ample_supply:
            if max_prev >= DAILY_SALARY * 1.8:
                target = DAILY_SALARY * 0.28
            elif max_prev >= DAILY_SALARY * 1.2:
                target = DAILY_SALARY * 0.38
            else:
                target = max(DAILY_SALARY * 0.32, avg_prev * 0.45)
        else:
            if max_prev >= DAILY_SALARY * 1.8:
                target = DAILY_SALARY * 0.42
            elif max_prev >= DAILY_SALARY * 1.2:
                target = max(DAILY_SALARY * 0.52, avg_prev * 0.55)
            else:
                target = max(DAILY_SALARY * 0.48, max_live_prev + 1.5)

    if rich_opp >= 2 and not ample_supply:
        target += 6.0
    if day >= 8 and (hp <= 5 or no_water_days >= 1):
        target += 8.0

    soft_cap = budget
    if urgency <= 2:
        soft_cap = min(soft_cap, DAILY_SALARY * 0.95)
    elif urgency == 3:
        soft_cap = min(soft_cap, DAILY_SALARY * 1.25)
    else:
        soft_cap = min(soft_cap, DAILY_SALARY * 1.8)

    bid = min(target, soft_cap)
    if hp >= 8 and no_water_days == 0 and ample_supply and max_prev >= DAILY_SALARY * 1.5:
        bid = min(bid, DAILY_SALARY * 0.25)

    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    alive_opps = []
    prev_bids = []
    prev_urgent_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                b = float(bid)
                prev_bids.append(b)
                if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 10)) <= 4:
                    prev_urgent_bids.append(b)

    if budget <= 0:
        return 0.0

    competitors = len(alive_opps) + 1
    expected_units = supply / float(WATER_REQ)
    scarcity = expected_units < competitors
    very_tight = expected_units < max(1.2, competitors - 1)

    max_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else max_prev
    urgent_anchor = max(prev_urgent_bids) if prev_urgent_bids else max_prev

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1
    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 1
    if very_tight:
        danger += 2
    elif scarcity:
        danger += 1
    if day >= 8:
        danger += 1

    if not alive_opps:
        return round(min(budget, DAILY_SALARY * 0.35), 2)

    if danger >= 6:
        target = max(urgent_anchor + 2.0, 0.92 * DAILY_SALARY)
        if max_prev > DAILY_SALARY:
            target = max(target, second_prev + 1.5)
        target = min(target, budget)
    elif danger >= 4:
        target = max(0.72 * DAILY_SALARY, min(max_prev + 1.25, DAILY_SALARY * 1.02))
        if scarcity:
            target = max(target, 0.82 * DAILY_SALARY)
        target = min(target, budget)
    elif danger >= 2:
        if scarcity:
            target = max(0.48 * DAILY_SALARY, min(second_prev * 0.55 + 6.0, DAILY_SALARY * 0.78))
        else:
            target = 0.34 * DAILY_SALARY
        target = min(target, budget)
    else:
        if max_prev >= 110:
            target = 0.18 * DAILY_SALARY
        elif scarcity:
            target = 0.28 * DAILY_SALARY
        else:
            target = 0.12 * DAILY_SALARY
        target = min(target, budget)

    reserve = 0.0
    if hp > 4 and no_water == 0 and day <= 7:
        reserve = DAILY_SALARY * 0.15
    if budget - target < reserve:
        target = max(0.0, budget - reserve)

    if hp <= 2 or no_water >= 2:
        target = max(target, min(budget, DAILY_SALARY * 0.9))

    return round(max(0.0, min(budget, target)), 2)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    opp_bids = []
    pressure_bids = []
    desperate_count = 0
    rich_count = 0
    low_req_count = 0

    for agent_id, opp in alive:
        if opp.get('budget', 0) >= 250:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('water_requirement', WATER_REQ) < WATER_REQ:
            low_req_count += 1

        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            opp_bids.append((agent_id, bid))
            if prev.get('status') == 'won':
                pressure_bids.append(bid)
            else:
                pressure_bids.append(bid * 0.92)

    highest_prev = 0.0
    second_prev = 0.0
    bob_prev = None
    cindy_prev = None
    for agent_id, bid in opp_bids:
        if bid > highest_prev:
            second_prev = highest_prev
            highest_prev = bid
        elif bid > second_prev:
            second_prev = bid
        if agent_id == 'Bob':
            bob_prev = bid
        if agent_id == 'Cindy':
            cindy_prev = bid

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    capacity = supply / float(WATER_REQ)
    if capacity >= 2.0:
        market_tightness = 0.2
    elif capacity >= 1.5:
        market_tightness = 0.45
    elif capacity >= 1.15:
        market_tightness = 0.7
    else:
        market_tightness = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2
    if no_water_days >= 1:
        urgency += 0.35
    urgency = min(1.0, urgency)

    base = DAILY_SALARY * (0.22 + 0.38 * market_tightness + 0.28 * urgency + 0.12 * scarcity)

    if pressure_bids:
        avg_pressure = sum(pressure_bids) / float(len(pressure_bids))
    else:
        avg_pressure = DAILY_SALARY * 0.45

    target = max(base, avg_pressure * (0.72 + 0.22 * urgency))

    if cindy_prev is not None and cindy_prev >= 160 and urgency < 0.7 and capacity >= 1.5:
        target = min(target, DAILY_SALARY * 0.62)

    if bob_prev is not None:
        if bob_prev <= 140 and urgency >= 0.35 and capacity < 2.0:
            target = max(target, bob_prev + 2.0)
        elif bob_prev >= 125 and urgency < 0.35 and capacity >= 1.5:
            target = min(target, bob_prev - 8.0)

    if desperate_count >= 2:
        target += 8.0
    elif desperate_count == 1:
        target += 4.0

    if rich_count >= 2 and urgency < 0.5:
        target -= 5.0

    if low_req_count >= 1 and capacity < 1.5:
        target += 5.0

    if hp <= 2 or no_water_days >= 1:
        floor_bid = DAILY_SALARY * 0.78
        target = max(target, floor_bid)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.58)

    if day >= 8:
        target += 4.0 * urgency

    max_safe = budget
    if hp > 4 and no_water_days == 0:
        max_safe = min(max_safe, DAILY_SALARY * 1.15)
    else:
        max_safe = min(max_safe, DAILY_SALARY * 1.55)

    bid = max(0.0, min(target, max_safe))

    if budget < DAILY_SALARY * 0.5:
        bid = min(bid, budget)

    return float(round(bid, 2))
"""
