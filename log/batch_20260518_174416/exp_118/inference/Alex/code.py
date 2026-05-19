# ============================================================
# Experiment: exp_118
# Agent: Alex
# Source: exp_118
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
    day = int(day_context['day'])
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
            return min(budget, 45)
        return min(budget, 20)

    prev_bids = []
    pressured_opponents = 0
    rich_opponents = 0
    desperate_opponents = 0

    for opp in alive_opponents:
        if opp.get('budget', 0) > budget:
            rich_opponents += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opponents += 1

        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
            if bid >= DAILY_SALARY * 0.75:
                pressured_opponents += 1

    high_supply = supply >= 21
    low_supply = supply <= 17

    if hp <= 2 or no_water_days >= 2:
        base_bid = 66
    elif hp <= 4 or no_water_days >= 1:
        base_bid = 52
    elif low_supply:
        base_bid = 46
    elif high_supply:
        base_bid = 28
    else:
        base_bid = 36

    if day >= 8:
        base_bid += 6
    if desperate_opponents >= 2:
        base_bid += 5
    if rich_opponents >= max(1, len(alive_opponents) // 2):
        base_bid += 4

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))

        if highest_prev >= 60:
            if hp > 4 and no_water_days == 0 and high_supply:
                base_bid = min(base_bid, 24)
            else:
                base_bid = max(base_bid, min(67, highest_prev + 2))
        elif highest_prev >= 45:
            base_bid = max(base_bid, min(58, avg_prev + 2))
        else:
            base_bid = max(base_bid, avg_prev + 1)

        if pressured_opponents == 0 and high_supply:
            base_bid = min(base_bid, 30)

    reserve = 0
    if hp > 4 and no_water_days == 0:
        reserve = 35
    elif hp > 2:
        reserve = 20

    affordable = max(0, budget - reserve)
    bid = min(base_bid, affordable if affordable > 0 else budget)

    if hp <= 2 or no_water_days >= 2:
        bid = min(max(bid, 60), budget)
    elif no_water_days >= 1 and bid < 45:
        bid = min(45, budget)

    if bid < 0:
        bid = 0

    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 20.0))

    serious_prev = []
    max_prev = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            if bid > max_prev:
                max_prev = bid
            if bid > 0:
                serious_prev.append(float(bid))

    guaranteed_units = int(supply // WATER_REQ)
    contested = len(alive) + 1

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

    if guaranteed_units <= 1:
        urgency += 2
    elif guaranteed_units >= 2:
        urgency -= 1

    if contested >= 4:
        urgency += 1

    rich_threats = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= budget and opp.get('hp', 10) > 3:
            rich_threats += 1
    if rich_threats >= 2:
        urgency += 1

    if serious_prev:
        avg_prev = sum(serious_prev) / float(len(serious_prev))
    else:
        avg_prev = 0.0

    target = 0.0

    if urgency >= 5:
        target = max(90.0, max_prev + 1.5)
    elif urgency >= 3:
        if max_prev >= 85.0:
            target = max_prev + 1.0
        elif max_prev >= 60.0:
            target = max(72.0, max_prev + 2.0)
        else:
            target = 74.0
    elif urgency >= 1:
        if guaranteed_units >= 2:
            target = max(38.0, avg_prev * 0.75)
        else:
            target = max(52.0, min(78.0, max_prev * 0.9 + 3.0))
    else:
        if guaranteed_units >= 2:
            target = 26.0
        else:
            target = 42.0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev.get('status') == 'won' and prev.get('bid') >= 85.0 and hp > 4 and no_water_days == 0:
                target = min(target, 35.0)

    if budget < target:
        if urgency >= 4:
            target = budget
        elif hp <= 3 or no_water_days >= 1:
            target = max(min(budget, 0.9 * budget), min(budget, 45.0))
        else:
            target = min(budget, 25.0)

    cap = budget
    if urgency <= 1 and hp >= 7:
        cap = min(cap, DAILY_SALARY * 0.9)
    elif urgency >= 5:
        cap = min(cap, 100.0)
    else:
        cap = min(cap, 95.0)

    bid = min(target, cap)
    if bid < 0:
        bid = 0.0
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_prev_bids = []
    weak_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) < DAILY_SALARY * 0.8 or opp.get('hp', 0) <= 2:
                weak_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if opp.get('budget', 0) >= bid:
                    strong_prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    strong_high = max(strong_prev_bids) if strong_prev_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        bid = max(92.0, strong_high + 1.2)
    elif urgent:
        bid = max(78.0, avg_prev + 2.0, strong_high + 0.8 * scarcity)
    else:
        if supply >= 22:
            bid = 18.0 + 6.0 * scarcity
        elif supply >= 19:
            bid = max(28.0, avg_prev * 0.55)
        else:
            bid = max(42.0, avg_prev * 0.72, strong_high * 0.82)

    if weak_opponents >= len(alive_opponents) / 2.0 and not urgent:
        bid *= 0.9

    if day >= 8:
        bid += 4.0 * scarcity
    if day == 1 and not urgent:
        bid *= 0.92

    floor_bid = 8.0
    if urgent:
        floor_bid = 35.0
    if critical:
        floor_bid = 70.0

    bid = max(floor_bid, bid)
    bid = min(budget, bid)

    if bid < 0:
        bid = 0.0
    return float(round(bid, 3))
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

    alive_opps = []
    prev_bids = []
    urgent_opp_bids = []
    rich_opp_bids = []

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        alive_opps.append(opp)
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp_bids.append(float(bid))
            if opp.get('budget', 0) > budget:
                rich_opp_bids.append(float(bid))

    if not alive_opps:
        return float(min(budget, 18.0))

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0
    max_urgent = max(urgent_opp_bids) if urgent_opp_bids else 0.0
    max_rich = max(rich_opp_bids) if rich_opp_bids else 0.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(78.0, max_prev + 2.0)
    elif hp <= 4 or no_water_days == 1:
        if supply >= 22:
            bid = max(52.0, avg_prev * 0.72)
        elif supply >= 18:
            bid = max(60.0, avg_prev * 0.82)
        else:
            bid = max(70.0, max_prev * 0.9)
    else:
        if supply >= 23:
            bid = 34.0
        elif supply >= 20:
            bid = 42.0
        elif supply >= 17:
            bid = 51.0
        else:
            bid = 61.0

        if max_prev > 0:
            if max_prev >= 120:
                bid = min(bid, 58.0)
            elif max_prev >= 90:
                bid = max(bid, 50.0)
            else:
                bid = max(bid, min(max_prev + 1.5, 68.0))

    if max_urgent > 0 and hp > 4 and no_water_days == 0:
        bid = min(bid, max_urgent - 6.0)

    if max_rich >= 120 and hp > 5 and supply >= 18:
        bid = min(bid, 55.0)

    if day >= 8:
        bid += 6.0
    if day >= 9:
        bid += 6.0

    bid = max(0.0, min(float(budget), float(bid)))
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    alive = []
    prev_bids = []
    rich_aggressive = 0
    moderate_max = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid > moderate_max and bid <= 230:
                    moderate_max = float(bid)
                if bid >= 160 and opp.get('budget', 0) > 250:
                    rich_aggressive += 1

    if not alive:
        return float(min(budget, 18.0))

    units = int(supply / WATER_REQ)
    scarcity = units <= 1
    late_game = day >= 8

    urgent = False
    if hp <= 3:
        urgent = True
    if no_water >= 2:
        urgent = True
    if hp <= 5 and no_water >= 1:
        urgent = True
    if late_game and hp <= 6:
        urgent = True

    if urgent:
        target = max(92.0, moderate_max + 3.0)
        if rich_aggressive >= 2:
            target = max(target, 132.0)
        if hp <= 2 or no_water >= 3:
            target = max(target, 168.0)
        return float(min(budget, target))

    if scarcity:
        if hp >= 8 and no_water == 0:
            target = 8.0 if rich_aggressive >= 1 else 16.0
        elif hp >= 6:
            target = 28.0 if rich_aggressive >= 1 else 42.0
        else:
            target = max(70.0, moderate_max * 0.72)
    else:
        if hp >= 8 and no_water == 0:
            target = 22.0
        elif hp >= 6:
            target = 38.0
        else:
            target = 62.0

    if prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev < 120 and not scarcity:
            target = max(target, highest_prev + 2.0)
        elif highest_prev < 120 and hp <= 6:
            target = max(target, highest_prev + 4.0)

    reserve_floor = max(0.0, (10 - day) * 8.0)
    spend_cap = max(0.0, budget - reserve_floor)
    if urgent:
        spend_cap = budget

    bid = min(target, spend_cap if spend_cap > 0 else target, budget)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_need_pressure = 0
    rich_aggressive = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                opp_need_pressure += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if bid >= 140 and opp.get('budget', 0) >= 200:
                    rich_aggressive += 1

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgent = False
    if hp <= 2:
        urgent = True
    if no_water >= 1 and hp <= 4:
        urgent = True
    if no_water >= 2:
        urgent = True

    if urgent:
        target = max(150.0, highest_prev + 6.0)
        if supply <= 16:
            target = max(target, 178.0)
        return min(budget, target)

    if hp >= 7 and no_water == 0:
        if highest_prev >= 150 or rich_aggressive >= 2:
            return min(budget, 12.0 if supply >= 20 else 20.0)
        if scarcity == 0:
            return min(budget, max(28.0, avg_prev * 0.42))
        return min(budget, max(40.0, avg_prev * 0.5))

    if scarcity == 2:
        target = max(95.0, highest_prev * 0.72)
    elif scarcity == 1:
        target = max(78.0, avg_prev * 0.68)
    else:
        target = max(60.0, avg_prev * 0.58)

    if opp_need_pressure >= 2:
        target -= 10.0
    if highest_prev >= 180:
        target -= 12.0
    if hp <= 4:
        target += 18.0
    if no_water >= 1:
        target += 15.0
    if day >= 8 and hp <= 5:
        target += 12.0

    target = max(15.0, target)
    return min(budget, target)
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                bid = float(bid)
                prev_bids.append(bid)
                if opp.get('budget', 0) > 0:
                    dangerous_prev.append(bid)

    if not alive:
        base = DAILY_SALARY * 0.18
        if no_water_days >= 2 or hp <= 2:
            base = DAILY_SALARY * 0.55
        return max(0.0, min(budget, round(base, 2)))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_danger = max(dangerous_prev) if dangerous_prev else highest_prev

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    urgent = (no_water_days >= 2) or (hp <= 2)
    pressured = (no_water_days >= 1) or (hp <= 4)

    target = 0.0

    if urgent:
        if highest_danger >= 140:
            target = highest_danger * 0.72
        elif highest_danger >= 80:
            target = highest_danger + 3.0
        else:
            target = DAILY_SALARY * 0.95
    elif tight_supply:
        if highest_danger >= 150:
            target = DAILY_SALARY * 0.52
        elif highest_danger >= 90:
            target = min(DAILY_SALARY * 0.9, highest_danger + 2.0)
        elif highest_danger > 0:
            target = max(DAILY_SALARY * 0.58, highest_danger + 1.5)
        else:
            target = DAILY_SALARY * 0.6
    elif medium_supply:
        if pressured:
            if highest_danger >= 120:
                target = DAILY_SALARY * 0.5
            elif highest_danger > 0:
                target = max(DAILY_SALARY * 0.45, highest_danger + 1.0)
            else:
                target = DAILY_SALARY * 0.48
        else:
            if highest_danger >= 120:
                target = DAILY_SALARY * 0.22
            elif highest_danger >= 70:
                target = DAILY_SALARY * 0.34
            else:
                target = DAILY_SALARY * 0.4
    else:
        if pressured:
            if highest_danger >= 100:
                target = DAILY_SALARY * 0.42
            elif highest_danger > 0:
                target = max(DAILY_SALARY * 0.36, highest_danger * 0.9)
            else:
                target = DAILY_SALARY * 0.38
        else:
            target = DAILY_SALARY * 0.2

    rich_threats = 0
    for opp in alive:
        if float(opp.get('budget', 0)) >= 140:
            rich_threats += 1
    if rich_threats >= 2 and not urgent and not tight_supply:
        target *= 0.92

    if day >= 8 and hp > 4 and no_water_days == 0:
        target *= 0.9

    target = max(0.0, min(budget, target))
    return round(target, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_threats = 0
    desperate_threats = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 100:
                rich_threats += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_threats += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 20.0))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / float(WATER_REQ)
    scarce = units < 2.0
    ample = units >= 2.0

    critical = hp <= 2 or no_water_days >= 2
    urgent = hp <= 4 or no_water_days >= 1

    if critical:
        bid = 118.0 if scarce else 96.0
        if rich_threats >= 1:
            bid += 8.0
        return float(min(budget, bid))

    if urgent:
        bid = 78.0 if ample else 92.0
        if highest_prev_bid >= 120:
            bid = max(bid, 88.0)
        elif highest_prev_bid >= 90:
            bid = max(bid, highest_prev_bid + 2.0)
        return float(min(budget, bid))

    if ample:
        bid = 18.0 + 3.0 * desperate_threats
        if avg_prev_bid < 60:
            bid = max(bid, 16.0)
        return float(min(budget, bid))

    bid = 42.0
    if highest_prev_bid >= 130:
        bid = 34.0
    elif highest_prev_bid >= 90:
        bid = min(68.0, highest_prev_bid - 8.0)
    elif highest_prev_bid > 0:
        bid = max(45.0, highest_prev_bid + 1.0)

    if day >= 8 and budget > 120:
        bid += 8.0
    if rich_threats >= 2:
        bid += 5.0

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
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return min(budget, DAILY_SALARY * 0.35)

    pressure_bids = []
    bob_bid = None
    cindy_bid = None
    urgent_opp_count = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            pressure_bids.append(float(pbid))
        if oid == 'Bob' and pbid is not None:
            bob_bid = float(pbid)
        if oid == 'Cindy' and pbid is not None:
            cindy_bid = float(pbid)
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp_count += 1

    total_alive = len(alive)
    scarcity = supply <= 17
    abundant = supply >= 22

    if bob_bid is None:
        bob_bid = 75.0

    target = DAILY_SALARY * 0.45

    if scarcity:
        target = bob_bid + 2.0
    elif abundant:
        target = max(DAILY_SALARY * 0.32, bob_bid - 6.0)
    else:
        target = bob_bid + 0.5

    if cindy_bid is not None and cindy_bid >= 100:
        if hp >= 5 and no_water_days == 0:
            target = min(target, DAILY_SALARY * 0.42)
        elif hp <= 2 or no_water_days >= 1:
            target = max(target, DAILY_SALARY * 0.92)

    if urgent_opp_count >= 1 and scarcity:
        target += 3.0

    if total_alive >= 3 and scarcity:
        target += 2.0

    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.95)
    elif hp <= 4 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.82)
    elif hp >= 8 and no_water_days == 0 and not scarcity:
        target = min(target, DAILY_SALARY * 0.5)

    if day >= 8:
        if hp >= 6 and no_water_days == 0:
            target = min(target, bob_bid + 1.0)
        else:
            target = max(target, DAILY_SALARY * 0.88)

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left >= 3 and hp >= 5:
        reserve_floor = DAILY_SALARY * 1.2
    elif days_left >= 1 and hp <= 3:
        reserve_floor = DAILY_SALARY * 0.2

    affordable = max(0.0, budget - reserve_floor)
    if affordable <= 0:
        affordable = budget

    bid = min(target, affordable, budget)
    if bid < 0:
        bid = 0.0

    if hp <= 2 and budget > 0:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

    return float(round(bid, 2))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive_bids = []
    for agent_id in opponents_status:
        opp = opponents_status[agent_id]
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 90:
                    aggressive_bids.append(float(bid))

    if not alive:
        return min(budget, 12.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    alive_count = len(alive) + 1

    scarcity = supply / float(WATER_REQ * alive_count)

    emergency = hp <= 3 or no_water_days >= 2
    pressured = hp <= 5 or no_water_days >= 1

    if emergency:
        bid = max(62.0, highest_prev * 0.72 + 6.0)
        if supply <= 16:
            bid += 10.0
        return min(budget, bid)

    if scarcity >= 0.42 and len(aggressive_bids) >= 2 and hp >= 7 and no_water_days == 0:
        return min(budget, 0.0)

    if supply >= 23 and hp >= 6 and no_water_days == 0:
        return min(budget, 8.0)

    if supply <= 17:
        bid = max(38.0, min(78.0, avg_prev * 0.42 + 10.0))
        if pressured:
            bid += 12.0
        return min(budget, bid)

    if pressured:
        bid = max(30.0, min(68.0, highest_prev * 0.32 + 8.0))
        return min(budget, bid)

    bid = 16.0
    if highest_prev >= 120:
        bid = 10.0
    elif highest_prev >= 80:
        bid = 12.0
    elif highest_prev > 0:
        bid = min(26.0, highest_prev * 0.25 + 4.0)

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.85

    return min(budget, max(0.0, bid))
"""
