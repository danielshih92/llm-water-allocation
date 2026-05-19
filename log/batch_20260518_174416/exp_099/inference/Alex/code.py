# ============================================================
# Experiment: exp_099
# Agent: Alex
# Source: exp_099
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

    player_count = 1 + len(alive_opponents)
    expected_units = float(supply) / float(WATER_REQ)
    scarcity = player_count - expected_units

    prev_bids = []
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
            if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 3:
                desperate_count += 1
            if prev.get('error'):
                desperate_count += 1

    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.78
    else:
        if scarcity >= 1.5:
            base = DAILY_SALARY * 0.72
        elif scarcity >= 0.5:
            base = DAILY_SALARY * 0.58
        else:
            base = DAILY_SALARY * 0.42

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if hp > 4 and no_water_days == 0 and highest_prev >= DAILY_SALARY * 0.9:
            base = min(base, DAILY_SALARY * 0.38)
        else:
            pressure_bid = max(avg_prev + 1.0, highest_prev * 0.92)
            base = max(base, pressure_bid)

    if desperate_count >= max(1, len(alive_opponents) // 2):
        base += 4

    if float(supply) >= 22.0 and hp > 4 and no_water_days == 0:
        base -= 5

    if budget < DAILY_SALARY * 0.8:
        base = min(base, budget * 0.7)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(base, DAILY_SALARY * 0.9))
    else:
        bid = min(budget, max(0, base))

    return bid
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    yesterday_bids = []
    dangerous_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = float(prev['bid'])
            yesterday_bids.append(bid)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                dangerous_bids.append(bid)

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    highest_danger = max(dangerous_bids) if dangerous_bids else highest_prev

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    severe_need = hp <= 3 or no_water_days >= 2
    moderate_need = hp <= 5 or no_water_days >= 1

    if severe_need:
        target = max(DAILY_SALARY * 1.05, highest_danger + 3.0, highest_prev + 2.0)
    elif moderate_need:
        target = max(DAILY_SALARY * (0.78 + 0.18 * scarcity), highest_prev + 1.5)
    else:
        if supply >= 22:
            target = max(DAILY_SALARY * 0.22, min(highest_prev + 1.0, DAILY_SALARY * 0.55))
        elif supply >= 19:
            target = max(DAILY_SALARY * 0.38, min(highest_prev + 1.2, DAILY_SALARY * 0.72))
        else:
            target = max(DAILY_SALARY * 0.62, highest_prev + 1.8)

    if day >= 8 and hp >= 7 and no_water_days == 0 and supply >= 20:
        target = min(target, DAILY_SALARY * 0.42)

    if budget < DAILY_SALARY * 1.2:
        if severe_need:
            target = max(min(budget, highest_prev + 1.0), budget * 0.85)
        else:
            target = min(target, budget * 0.55)

    bid = min(budget, max(0.0, target))
    return float(round(bid, 2))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    opp_prev_bids = []
    desperate_count = 0
    rich_count = 0
    req_pressure = 0.0

    for oid, opp in alive:
        if opp.get('budget', 0) >= 180:
            rich_count += 1
        req_pressure += float(opp.get('water_requirement', WATER_REQ))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                opp_prev_bids.append(float(bid))
            status = prev.get('status')
            hp_after = prev.get('hp_after')
            if status == 'no_water' or (hp_after is not None and hp_after <= 3):
                desperate_count += 1

    highest_prev = max(opp_prev_bids) if opp_prev_bids else 0.0
    avg_prev = sum(opp_prev_bids) / len(opp_prev_bids) if opp_prev_bids else 0.0

    slots = max(1, int(supply // WATER_REQ))
    total_players = 1 + len(alive)
    scarcity = total_players - slots

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if supply <= 16:
        urgency += 3
    elif supply <= 19:
        urgency += 2
    if scarcity >= 3:
        urgency += 2
    elif scarcity >= 2:
        urgency += 1
    if desperate_count >= 2:
        urgency += 1

    conservative_bid = max(12.0, min(32.0, 0.22 * DAILY_SALARY + 0.06 * avg_prev))
    medium_bid = max(38.0, min(78.0, 0.52 * DAILY_SALARY + 0.18 * highest_prev))
    aggressive_bid = max(72.0, min(140.0, highest_prev + 6.0))
    all_in_bid = max(95.0, min(0.92 * budget, highest_prev + 15.0))

    bob_like_pressure = highest_prev >= 120.0 or avg_prev >= 90.0 or rich_count >= 2

    if urgency >= 7:
        bid = all_in_bid
    elif urgency >= 5:
        bid = aggressive_bid if bob_like_pressure else max(medium_bid, 68.0)
    elif urgency >= 3:
        if supply <= 18:
            bid = max(medium_bid, highest_prev * 0.72 + 4.0)
        else:
            bid = medium_bid
    else:
        if highest_prev >= 150.0 and hp >= 5:
            bid = conservative_bid
        elif supply >= 24 and hp >= 6:
            bid = min(conservative_bid, 24.0)
        else:
            bid = max(conservative_bid, min(44.0, avg_prev * 0.45 + 8.0))

    if day >= 8:
        if hp <= 4 or no_water_days >= 1:
            bid = max(bid, aggressive_bid)
        elif budget < 90:
            bid = min(bid, 36.0)

    if budget < 60:
        bid = min(bid, max(18.0, 0.72 * budget))

    bid = min(float(budget), float(bid))
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

    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    yesterday_bids = []
    dangerous_pressure = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                yesterday_bids.append(bid)
                weight = 1.0
                if opp.get('budget', 0) > budget:
                    weight += 0.15
                if opp.get('no_water_days', 0) >= 1:
                    weight += 0.1
                dangerous_pressure = max(dangerous_pressure, bid * weight)

    if not alive_opponents:
        return float(min(budget, 18.0))

    total_players = 1 + len(alive_opponents)
    expected_share = supply / float(total_players)
    scarcity = WATER_REQ - expected_share

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

    if scarcity >= 6:
        urgency += 3
    elif scarcity >= 3:
        urgency += 2
    elif scarcity > 0:
        urgency += 1

    if supply <= 17:
        urgency += 1
    elif supply >= 22:
        urgency -= 1

    if not yesterday_bids:
        if urgency >= 5:
            bid = DAILY_SALARY * 0.95
        elif urgency >= 3:
            bid = DAILY_SALARY * 0.72
        else:
            bid = DAILY_SALARY * 0.42
        return float(min(budget, max(0.0, bid)))

    highest_prev = max(yesterday_bids)
    avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))

    if urgency >= 6:
        target = max(DAILY_SALARY * 0.95, dangerous_pressure + 3.0)
    elif urgency >= 4:
        target = max(DAILY_SALARY * 0.75, min(dangerous_pressure + 1.5, DAILY_SALARY * 1.05))
    elif urgency >= 2:
        if highest_prev > DAILY_SALARY * 2.2:
            target = DAILY_SALARY * 0.38
        else:
            target = max(DAILY_SALARY * 0.5, avg_prev * 0.72)
    else:
        if highest_prev > DAILY_SALARY * 1.5:
            target = DAILY_SALARY * 0.22
        else:
            target = DAILY_SALARY * 0.34

    if budget < DAILY_SALARY * 0.6:
        target = min(target, budget)
    elif budget > DAILY_SALARY * 3 and urgency >= 4:
        target = min(max(target, DAILY_SALARY * 0.9), budget)

    return float(min(budget, max(0.0, target)))
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

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return min(budget, 1.0)

    prev_bids = []
    fixed_low_present = False
    high_overpayer_present = False
    desperate_count = 0

    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
            if 14.5 <= bid <= 15.5:
                fixed_low_present = True
            if bid >= 100:
                high_overpayer_present = True
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        if fixed_low_present:
            bid = 16.2
        else:
            bid = 18.0
        if desperate_count >= 2:
            bid = max(bid, 24.0)
        return min(budget, bid)

    if hp <= 4 or no_water_days >= 1:
        if tight_supply:
            bid = 16.1 if fixed_low_present else 17.5
        else:
            bid = 15.2 if fixed_low_present else 12.0
        if desperate_count >= 2 and tight_supply:
            bid = max(bid, 22.0)
        return min(budget, bid)

    if loose_supply:
        bid = 0.5
    elif tight_supply:
        bid = 15.6 if fixed_low_present else 10.0
    else:
        bid = 2.0

    if high_overpayer_present and hp >= 5 and no_water_days == 0 and not tight_supply:
        bid = min(bid, 1.0)

    if day >= 8 and hp >= 5 and no_water_days == 0:
        bid = min(bid, 1.0)

    return min(budget, bid)
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if len(alive_opponents) == 0:
        base = DAILY_SALARY * 0.22
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.45
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    desperate_count = 0
    rich_aggressive = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= 300:
            if bid is not None and float(bid) >= 90:
                rich_aggressive += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (25.0 - float(supply)) / 10.0
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = False
    if hp <= 2 or no_water >= 2:
        urgent = True
    elif hp <= 4 and no_water >= 1:
        urgent = True

    very_safe = False
    if hp >= 8 and no_water == 0:
        very_safe = True

    if urgent:
        target = max(92.0, highest_prev + 2.5)
        if desperate_count >= 2:
            target += 8.0
        if float(supply) <= 17.0:
            target += 6.0
        if day >= 8:
            target += 5.0
    else:
        if very_safe:
            target = 12.0 + 10.0 * (1.0 - scarcity)
            if highest_prev < 40.0:
                target = max(target, highest_prev + 1.0)
            else:
                target = min(target, 24.0)
        else:
            target = 28.0 + 18.0 * scarcity
            if no_water >= 1:
                target += 18.0
            if hp <= 5:
                target += 10.0
            if highest_prev > 0:
                if highest_prev <= 60.0:
                    target = max(target, highest_prev + 1.5)
                elif highest_prev <= 95.0:
                    target = max(target, 0.72 * highest_prev)
                else:
                    target = max(target, 0.58 * highest_prev)

    if rich_aggressive >= 2 and not urgent:
        target *= 0.82
    elif rich_aggressive == 1 and not urgent:
        target *= 0.9

    if avg_prev > 100.0 and not urgent and hp >= 6:
        target = min(target, 36.0)

    reserve_floor = 0.0
    if hp >= 6:
        reserve_floor = DAILY_SALARY * 2.0
    elif hp >= 4:
        reserve_floor = DAILY_SALARY * 1.2
    else:
        reserve_floor = DAILY_SALARY * 0.4

    max_spend = budget
    if not urgent:
        max_spend = max(0.0, budget - reserve_floor)
        if max_spend < 8.0:
            max_spend = min(budget, 8.0)

    if day >= 9 and hp <= 4:
        max_spend = budget
        target += 12.0

    bid = min(max_spend, target)
    if urgent:
        bid = min(budget, max(bid, 88.0 if float(supply) >= 18.0 else 96.0))

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 63.0))
        return float(min(budget, 28.0))

    prev_bids = []
    threat_bids = []
    cindy_bid = None
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            weight = 1.0
            if opp.get('budget', 0) > budget:
                weight += 0.15
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                weight += 0.2
            threat_bids.append(float(bid) * weight)
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_bids) if threat_bids else highest_prev

    alive_count = len(alive_opponents) + 1
    contested_units = supply / float(WATER_REQ)
    tight_supply = contested_units < alive_count
    very_tight = contested_units < max(1.5, alive_count - 1)

    must_win = hp <= 2 or no_water_days >= 2
    urgent = hp <= 4 or no_water_days >= 1

    if must_win:
        bid = max(63.0, highest_prev + 2.5)
        return float(min(budget, bid))

    if very_tight:
        if highest_prev >= 140:
            bid = 46.0 if hp > 5 else 72.0
        elif highest_prev >= 90:
            bid = highest_prev + 2.0 if urgent else 52.0
        elif highest_prev > 0:
            bid = highest_prev + 1.5 if urgent else max(40.0, highest_prev * 0.72)
        else:
            bid = 55.0 if urgent else 38.0
    elif tight_supply:
        if highest_prev >= 140:
            bid = 34.0 if hp > 6 else 61.0
        elif highest_prev >= 90:
            bid = 58.0 if urgent else 36.0
        elif highest_prev > 0:
            bid = max(32.0, min(60.0, highest_prev + 1.0)) if urgent else max(24.0, highest_prev * 0.6)
        else:
            bid = 44.0 if urgent else 26.0
    else:
        if highest_prev >= 140:
            bid = 18.0 if hp > 5 else 48.0
        elif highest_prev >= 90:
            bid = 24.0 if hp > 5 else 52.0
        elif highest_prev > 0:
            bid = 22.0 if hp > 6 else max(30.0, highest_prev * 0.55)
        else:
            bid = 20.0 if hp > 6 else 34.0

    if budget < 25:
        bid = min(bid, budget)
    elif budget < 60:
        bid = min(bid, budget * 0.92)

    if hp >= 8 and no_water_days == 0 and highest_prev >= 140:
        bid = min(bid, 22.0)

    if urgent and highest_threat > bid and highest_threat <= budget and highest_threat < 110:
        bid = max(bid, highest_threat + 1.0)

    bid = max(0.0, min(float(budget), float(bid)))
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
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev.get('bid', 0.0)
                prev_bids.append(b)
                if b > dangerous_prev:
                    dangerous_prev = b

    if budget <= 0:
        return 0.0

    alive_count = len(alive)
    if alive_count == 0:
        return min(budget, 18.0)

    tight_supply = supply <= 17
    ample_supply = supply >= 22
    urgent = hp <= 3 or no_water_days >= 2
    semi_urgent = hp <= 5 or no_water_days >= 1

    if urgent:
        bid = min(budget, max(62.0, dangerous_prev + 2.0, DAILY_SALARY * 0.92))
        return float(max(0.0, bid))

    if dangerous_prev >= 130:
        if tight_supply:
            bid = min(budget, 58.0)
        elif ample_supply:
            bid = min(budget, 16.0)
        else:
            bid = min(budget, 24.0)
        return float(max(0.0, bid))

    if dangerous_prev >= 90:
        if semi_urgent or tight_supply:
            bid = min(budget, dangerous_prev * 0.72 + 2.0)
        else:
            bid = min(budget, 22.0)
        return float(max(0.0, bid))

    if tight_supply:
        base = 46.0 if semi_urgent else 34.0
    elif ample_supply:
        base = 18.0 if not semi_urgent else 28.0
    else:
        base = 26.0 if not semi_urgent else 38.0

    if prev_bids:
        target = max(base, min(60.0, dangerous_prev + 1.5))
        if dangerous_prev < 35:
            target = max(base, dangerous_prev + 3.0)
    else:
        target = base

    if day >= 8 and hp >= 6 and no_water_days == 0:
        target = min(target, 24.0)

    if budget < 80:
        target = min(target, budget * 0.55)

    return float(max(0.0, min(budget, target)))
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
        base = DAILY_SALARY * 0.28
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    cindy_prev = None
    max_prev = 0.0
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        bid = None
        if isinstance(prev, dict):
            bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            prev_bids.append(bid)
            if bid > max_prev:
                max_prev = bid
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13:
            if isinstance(prev, dict) and prev.get('bid') is not None:
                if opp.get('budget', 0) > 500:
                    cindy_prev = float(prev.get('bid'))

    units = int(supply // WATER_REQ)
    scarcity = 1.0 if units <= 1 else 0.0

    if hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * (0.92 if scarcity else 0.82)
        if cindy_prev is not None:
            bid = max(bid, min(budget, cindy_prev + 3.0))
        elif max_prev > 0:
            bid = max(bid, min(budget, max_prev + 2.0))
        return float(max(0.0, min(budget, bid)))

    if hp == 3 or no_water_days == 1:
        bid = DAILY_SALARY * (0.68 if scarcity else 0.58)
        if cindy_prev is not None and cindy_prev < DAILY_SALARY * 0.95:
            bid = max(bid, cindy_prev + 1.5)
        elif max_prev > 0 and max_prev < DAILY_SALARY * 0.9:
            bid = max(bid, max_prev + 1.0)
        return float(max(0.0, min(budget, bid)))

    if scarcity:
        if cindy_prev is not None:
            if cindy_prev >= 100:
                bid = DAILY_SALARY * 0.24
            elif cindy_prev >= 70:
                bid = DAILY_SALARY * 0.34
            else:
                bid = max(DAILY_SALARY * 0.42, cindy_prev + 1.0)
        elif max_prev >= 70:
            bid = DAILY_SALARY * 0.32
        elif max_prev > 0:
            bid = max(DAILY_SALARY * 0.4, max_prev + 1.0)
        else:
            bid = DAILY_SALARY * 0.38
    else:
        bid = DAILY_SALARY * 0.22
        if urgent_opp >= 2:
            bid = DAILY_SALARY * 0.3
        if cindy_prev is not None and cindy_prev < 45:
            bid = max(bid, cindy_prev + 0.5)
        elif max_prev > 0 and max_prev < 40:
            bid = max(bid, max_prev + 0.5)

    if day >= 8 and budget > DAILY_SALARY * 6:
        bid += 4.0
    if rich_opp >= 1 and scarcity:
        bid += 2.0

    return float(max(0.0, min(budget, bid)))
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
    prev_bids = []
    threat_bids = []
    urgent_opp = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                weight = 1.0
                if opp.get('water_requirement', WATER_REQ) >= WATER_REQ:
                    weight += 0.1
                if opp.get('daily_salary', DAILY_SALARY) >= DAILY_SALARY:
                    weight += 0.05
                if opp.get('hp', 0) <= 3:
                    weight += 0.15
                threat_bids.append(float(bid) * weight)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 35.0))

    slots = max(1, int(supply // WATER_REQ))
    alive_count = len(alive)
    scarcity = alive_count - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    weighted_high = max(threat_bids) if threat_bids else highest_prev

    if scarcity >= 3:
        base = weighted_high + 6.0
    elif scarcity == 2:
        base = weighted_high + 3.0
    elif scarcity == 1:
        base = max(56.0, highest_prev - 2.0)
    else:
        base = max(28.0, highest_prev - 12.0)

    if supply >= 23:
        base -= 6.0
    elif supply <= 17:
        base += 6.0

    if urgent_opp >= 2:
        base += 4.0
    elif urgent_opp == 0 and hp >= 4:
        base -= 3.0

    if hp <= 1 or no_water_days >= 2:
        bid = max(base, weighted_high + 8.0, 92.0)
    elif hp <= 2 or no_water_days >= 1:
        bid = max(base, weighted_high + 3.0, 74.0)
    elif hp >= 5 and scarcity <= 0:
        bid = min(base, 38.0)
    else:
        bid = base

    if day >= 8:
        if hp <= 3:
            bid += 6.0
        else:
            bid -= 2.0

    reserve = DAILY_SALARY * max(0, 10 - day)
    if hp >= 4:
        cap = max(25.0, budget - reserve * 0.55)
    else:
        cap = max(35.0, budget - reserve * 0.35)

    bid = min(bid, budget, cap)
    bid = max(0.0, bid)
    return float(round(bid, 2))
"""
