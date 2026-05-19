# ============================================================
# Experiment: exp_110
# Agent: Alex
# Source: exp_110
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 63)
        return min(budget, 28)

    yesterday_bids = []
    desperate_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            desperate_opponents += 1
        if opp.get('budget', 0) >= budget:
            rich_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev.get('bid', 0))

    player_count = 1 + len(alive_opponents)
    scarcity = float(supply) / float(player_count * WATER_REQ)

    if scarcity >= 1.2:
        base_bid = 20
    elif scarcity >= 0.95:
        base_bid = 30
    elif scarcity >= 0.75:
        base_bid = 40
    else:
        base_bid = 50

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))
        pressure_bid = max(avg_prev + 2, highest_prev + 1)
        if highest_prev >= 60:
            if hp > 3 and no_water_days == 0:
                bid = min(base_bid, 24)
            else:
                bid = max(base_bid, 62)
        else:
            bid = max(base_bid, pressure_bid)
    else:
        bid = base_bid

    if desperate_opponents > 0:
        bid += 4
    if rich_opponents >= len(alive_opponents) and len(alive_opponents) > 0:
        bid -= 3

    if hp <= 2:
        bid = max(bid, 63)
    elif hp <= 4 or no_water_days >= 2:
        bid = max(bid, 54)
    elif no_water_days == 1:
        bid = max(bid, 44)

    reserve_floor = 0
    if hp > 4:
        reserve_floor = DAILY_SALARY * 2
    elif hp > 2:
        reserve_floor = DAILY_SALARY

    max_affordable = budget
    if budget > reserve_floor:
        max_affordable = budget - reserve_floor + min(DAILY_SALARY, reserve_floor)

    if max_affordable < 0:
        max_affordable = 0

    final_bid = min(float(bid), float(max_affordable), float(budget))
    if final_bid < 0:
        final_bid = 0
    return final_bid
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
        base = DAILY_SALARY * 0.22
        if no_water_days >= 2 or hp <= 3:
            base = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    max_prev = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace') or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
            if float(pbid) > max_prev:
                max_prev = float(pbid)
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
            urgent_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_opp += 1

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    pressure = 0.38 + 0.22 * scarcity + 0.08 * urgent_opp + 0.04 * rich_opp
    if max_prev >= 90:
        pressure += 0.08
    elif max_prev >= 75:
        pressure += 0.05
    elif max_prev <= 45:
        pressure -= 0.04

    self_urgency = 0
    if no_water_days >= 2:
        self_urgency += 2
    elif no_water_days == 1:
        self_urgency += 1
    if hp <= 2:
        self_urgency += 2
    elif hp <= 4:
        self_urgency += 1

    pressure += 0.14 * self_urgency

    if day >= 8 and hp > 5 and no_water_days == 0:
        pressure -= 0.05

    if supply >= 23 and self_urgency == 0:
        pressure -= 0.08
    elif supply <= 17:
        pressure += 0.08

    if pressure < 0.18:
        pressure = 0.18
    if pressure > 0.98:
        pressure = 0.98

    bid = DAILY_SALARY * pressure

    if prev_bids and self_urgency > 0:
        target = max_prev + 1.5
        if target > bid:
            bid = target

    if self_urgency == 0 and max_prev >= 85 and supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.34)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * 2.0
    elif day <= 9:
        reserve_floor = DAILY_SALARY * 1.0

    affordable = budget
    if budget > reserve_floor:
        affordable = budget - reserve_floor + min(reserve_floor * 0.25, DAILY_SALARY * 0.5)

    if self_urgency >= 3:
        affordable = budget

    bid = min(bid, affordable, budget)
    if self_urgency >= 3:
        bid = max(bid, DAILY_SALARY * 0.82)
    elif self_urgency == 2:
        bid = max(bid, DAILY_SALARY * 0.68)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_pressure = 0.0
    desperate_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) > 300:
                    rich_pressure = max(rich_pressure, float(bid))
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    slots = supply / float(WATER_REQ)
    tight_supply = slots < (len(alive) + 1)
    very_tight = slots < len(alive)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    if very_tight:
        urgency += 2
    elif tight_supply:
        urgency += 1

    if desperate_count >= 2:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency <= 1:
        base = 12.0 if not tight_supply else 20.0
    elif urgency == 2:
        base = 28.0 if not tight_supply else 40.0
    elif urgency == 3:
        base = 45.0 if not tight_supply else 58.0
    elif urgency == 4:
        base = 62.0 if not tight_supply else 76.0
    else:
        base = 88.0

    if highest_prev >= 120:
        if urgency <= 2:
            base = min(base, 24.0 if not tight_supply else 36.0)
        else:
            base = max(base, min(95.0, highest_prev * 0.72))
    elif highest_prev >= 80:
        if urgency <= 1:
            base = min(base, 18.0 if not tight_supply else 28.0)
        else:
            base = max(base, min(78.0, avg_prev * 0.7 + 6.0))
    elif highest_prev > 0:
        if urgency >= 3:
            base = max(base, min(72.0, highest_prev + 3.0))
        else:
            base = max(base, min(34.0, avg_prev * 0.55 + 4.0))

    if rich_pressure >= 130 and urgency <= 2:
        base = min(base, 22.0 if not tight_supply else 32.0)

    if budget < 40:
        base = min(base, budget)
    elif budget < 100:
        base = min(base, budget * 0.65)
    else:
        base = min(base, budget * 0.5 if urgency <= 2 else budget * 0.75)

    if hp <= 2 or no_water >= 2:
        base = max(base, min(budget, 85.0))

    if supply >= 23 and urgency <= 2:
        base *= 0.8
    elif supply <= 17 and urgency >= 2:
        base *= 1.12

    bid = max(0.0, min(float(budget), float(base)))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0)
                prev_bids.append(b)
                if b >= 90 and opp.get('budget', 0) >= 90:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    slots = int(supply // WATER_REQ)
    if slots < 1:
        slots = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev = sorted_bids[int(1)]

    urgent = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2
    late_game = day >= 8

    if slots >= 2:
        base = 24.0
        if desperate_count >= 2:
            base = 38.0
        if urgent:
            base = max(base, 52.0)
        if critical:
            base = max(base, 82.0)
        if rich_aggressive >= 2 and not urgent:
            base = min(base, 20.0)
        bid = base
    else:
        anchor = highest_prev
        if second_prev > 0:
            anchor = max(anchor, second_prev + 2.0)
        bid = max(58.0, min(anchor + 3.0, 108.0))
        if urgent:
            bid = max(bid, 88.0)
        if critical:
            bid = max(bid, 112.0)
        if late_game and hp >= 5 and no_water == 0:
            bid = min(bid, 72.0)

    if highest_prev >= 120 and not urgent and slots >= 2:
        bid = min(bid, 18.0)

    if budget < bid:
        if urgent:
            bid = budget
        else:
            bid = min(budget, max(0.0, bid * 0.75))

    reserve_floor = 0.0
    if not critical:
        reserve_floor = max(0.0, budget - DAILY_SALARY * 3)
        bid = min(bid, max(18.0 if slots >= 2 else 45.0, budget - reserve_floor))

    if urgent and budget >= 85:
        bid = max(bid, 85.0 if slots >= 2 else 98.0)

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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    desperate_opp = 0
    rich_opp = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return min(budget, 18.0)

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    scarce = units < 2.0
    abundant = units >= 1.8

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

    if scarce:
        urgency += 1
    if desperate_opp >= 2:
        urgency += 1

    if budget <= DAILY_SALARY * 0.8:
        cap = budget
    elif urgency >= 5:
        cap = min(budget, DAILY_SALARY * 1.15)
    elif urgency >= 3:
        cap = min(budget, DAILY_SALARY * 0.95)
    else:
        cap = min(budget, DAILY_SALARY * 0.7)

    if urgency >= 5:
        bid = max(58.0, min(cap, max_prev * 0.72 + 4.0))
    elif urgency >= 3:
        anchor = max(42.0, min(60.0, avg_prev * 0.45 + 6.0))
        bid = min(cap, anchor)
    else:
        if max_prev >= 120:
            bid = 19.0 if abundant else 24.0
        elif max_prev >= 80:
            bid = 24.0 if abundant else 31.0
        else:
            bid = 28.0 if abundant else 36.0
        if rich_opp >= 2 and not abundant:
            bid += 4.0
        bid = min(cap, bid)

    if day >= 8:
        bid = min(budget, bid + 6.0)
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 63.0))

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
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
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_count = 0
    rich_count = 0
    cindy_like = False

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 100:
                rich_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 100:
                    dangerous_count += 1
                if bid >= 140:
                    cindy_like = True

    if not alive:
        return float(min(budget, 8.0))

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

    if supply <= 16:
        urgency += 2
    elif supply <= 19:
        urgency += 1
    elif supply >= 23:
        urgency -= 1

    if rich_count == 0:
        urgency -= 1

    if hp >= 8 and no_water_days == 0 and supply <= 18 and cindy_like:
        return float(min(budget, 0.0))

    if urgency <= 0:
        base = 12.0 if supply >= 22 else 18.0
        if highest_prev < 40:
            base = max(base, highest_prev + 2.0)
        return float(min(budget, base))

    if urgency == 1:
        base = 28.0 if supply >= 20 else 36.0
        if highest_prev < 60:
            base = max(base, highest_prev + 3.0)
        return float(min(budget, base))

    if urgency == 2:
        if cindy_like and supply <= 18 and hp > 4 and no_water_days == 0:
            return float(min(budget, 22.0))
        base = 48.0 if supply >= 20 else 58.0
        if highest_prev < 80:
            base = max(base, highest_prev + 4.0)
        return float(min(budget, base))

    if urgency == 3:
        base = 72.0 if supply >= 20 else 86.0
        if highest_prev < 100:
            base = max(base, highest_prev + 5.0)
        return float(min(budget, base))

    if urgency == 4:
        base = 95.0 if supply >= 20 else 112.0
        if highest_prev < 120:
            base = max(base, highest_prev + 6.0)
        return float(min(budget, base))

    base = 125.0 if supply >= 20 else 151.0
    if highest_prev > 0:
        base = max(base, highest_prev + 1.0)
    return float(min(budget, base))
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
        return float(min(budget, 18.0))

    slots = supply / float(WATER_REQ)
    scarcity = slots < 2.0

    prev_bids = []
    urgent_prev_bids = []
    max_prev = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            b = float(bid)
            prev_bids.append(b)
            if b > max_prev:
                max_prev = b
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_prev_bids.append(b)

    pressure_bid = max_prev
    if urgent_prev_bids:
        ub = max(urgent_prev_bids)
        if ub > pressure_bid:
            pressure_bid = ub

    if hp <= 2 or no_water >= 2:
        bid = max(62.0, pressure_bid + 2.0)
    elif hp <= 4 or no_water >= 1:
        bid = max(48.0, pressure_bid + 1.0 if pressure_bid > 0 else 48.0)
    else:
        if scarcity:
            if pressure_bid >= 100.0:
                bid = 34.0
            elif pressure_bid >= 75.0:
                bid = 42.0
            elif pressure_bid >= 45.0:
                bid = pressure_bid + 1.5
            else:
                bid = 39.0
        else:
            if pressure_bid >= 100.0:
                bid = 22.0
            elif pressure_bid >= 70.0:
                bid = 28.0
            elif pressure_bid >= 40.0:
                bid = 31.0
            else:
                bid = 24.0

    remaining_days = max(1, 10 - int(day) + 1)
    reserve_target = DAILY_SALARY * 0.45 * remaining_days
    max_affordable = budget
    if budget > reserve_target:
        max_affordable = max(0.0, budget - reserve_target * 0.35)
    else:
        max_affordable = max(0.0, budget * 0.75)

    if hp <= 2 or no_water >= 2:
        max_affordable = budget

    final_bid = min(float(budget), float(max_affordable), float(bid))
    if final_bid < 0.0:
        final_bid = 0.0
    return float(final_bid)
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > 300:
                rich_threat += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    low_supply = supply <= 17
    high_supply = supply >= 22

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

    if low_supply:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1
    if rich_threat >= 1:
        urgency += 1

    if urgency >= 6:
        bid = max(95.0, highest_prev + 2.0)
    elif urgency >= 4:
        bid = max(62.0, min(92.0, avg_prev + 3.0))
    elif urgency >= 2:
        bid = 38.0 if high_supply else 46.0
        if highest_prev < 60:
            bid = max(bid, highest_prev + 1.5)
    else:
        bid = 20.0 if high_supply else 26.0
        if day >= 8 and hp >= 6:
            bid = 16.0

    if highest_prev >= 140 and urgency <= 3:
        bid = min(bid, 28.0)

    reserve_target = 0.0
    days_left = max(0, 10 - day)
    if hp > 4:
        reserve_target = days_left * 18.0
    max_safe = max(0.0, budget - reserve_target)

    if urgency >= 4:
        final_bid = min(budget, max(bid, min(budget, max_safe + 20.0)))
    else:
        if max_safe > 0:
            final_bid = min(budget, min(bid, max_safe))
        else:
            final_bid = min(budget, 18.0 if hp > 4 else 40.0)

    if hp <= 2 or no_water_days >= 2:
        final_bid = min(budget, max(final_bid, highest_prev + 3.0, 88.0))

    if final_bid < 0:
        final_bid = 0.0

    return float(round(final_bid, 2))
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
    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 300:
                rich_aggressive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.55
    elif no_water_days >= 1:
        urgency += 0.25

    urgency += 0.25 * scarcity
    urgency += 0.08 * desperate_count

    if day >= 8:
        urgency += 0.12

    if urgency > 1.2:
        urgency = 1.2

    if highest_prev >= 300:
        target = DAILY_SALARY * (0.42 + 0.18 * urgency)
    elif highest_prev >= 180:
        target = max(DAILY_SALARY * (0.58 + 0.28 * urgency), avg_prev * 0.72)
    elif highest_prev >= 90:
        target = max(DAILY_SALARY * (0.72 + 0.22 * urgency), highest_prev + 2.0)
    elif highest_prev > 0:
        target = max(DAILY_SALARY * (0.62 + 0.24 * urgency), highest_prev + 3.0)
    else:
        target = DAILY_SALARY * (0.55 + 0.25 * urgency)

    if rich_aggressive >= 2 and hp > 4 and no_water_days == 0 and supply >= 20:
        target *= 0.82

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.95)
    elif hp <= 4 and supply <= 18:
        target = max(target, DAILY_SALARY * 0.82)

    reserve = 0.0
    if hp > 4:
        reserve = DAILY_SALARY * 1.2
    elif hp > 2:
        reserve = DAILY_SALARY * 0.6

    max_affordable = max(0.0, budget - reserve)
    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    bid = min(target, max_affordable)
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    if budget < DAILY_SALARY * 0.5 and (hp > 4 and no_water_days == 0):
        bid = min(bid, budget * 0.55)

    return float(max(0.0, bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    prev_bids = []
    desperate_count = 0
    rich_live = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 1.2:
            rich_live += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

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

    pressure = scarcity + urgency
    if desperate_count >= 2:
        pressure += 1

    if pressure >= 6:
        target = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif pressure >= 4:
        target = max(DAILY_SALARY * 0.78, avg_prev + 1.5)
    elif pressure >= 2:
        target = max(DAILY_SALARY * 0.52, min(highest_prev * 0.72, DAILY_SALARY * 0.72))
    else:
        target = DAILY_SALARY * 0.28

    if scarcity == 0 and hp >= 7 and no_water == 0:
        target = min(target, DAILY_SALARY * 0.35)

    if rich_live == 0 and pressure <= 2:
        target = min(target, DAILY_SALARY * 0.3)

    reserve = 0.0
    if day <= 7:
        reserve = DAILY_SALARY * 0.35
    max_affordable = max(0.0, budget - reserve)
    if pressure >= 4:
        max_affordable = budget

    bid = min(target, max_affordable)
    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""
