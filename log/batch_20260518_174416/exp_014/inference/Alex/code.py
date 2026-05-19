# ============================================================
# Experiment: exp_014
# Agent: Alex
# Source: exp_014
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

    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    desperate_opp = 0
    rich_agg = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 2:
                desperate_opp += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= DAILY_SALARY * 0.8 and opp.get('budget', 0) >= DAILY_SALARY:
                    rich_agg += 1

    players = 1 + len(alive_opponents)
    expected_share = supply / max(1, players)
    scarcity = max(0.0, (WATER_REQ - expected_share) / WATER_REQ)

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    if no_water >= 2:
        urgency += 0.35
    elif no_water >= 1:
        urgency += 0.15

    market = 0.0
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        market += min(0.35, highest_prev / (DAILY_SALARY * 3.0))
        market += min(0.2, avg_prev / (DAILY_SALARY * 5.0))
    market += min(0.2, desperate_opp * 0.06)
    market += min(0.15, rich_agg * 0.05)

    base_ratio = 0.22 + 0.55 * scarcity + urgency + market

    if supply >= 24 and hp >= 5 and no_water == 0:
        base_ratio -= 0.12
    elif supply <= 17:
        base_ratio += 0.12

    if hp <= 2 or no_water >= 2:
        floor_bid = DAILY_SALARY * 0.72
    elif hp <= 4 or no_water >= 1:
        floor_bid = DAILY_SALARY * 0.48
    else:
        floor_bid = DAILY_SALARY * 0.18

    bid = DAILY_SALARY * base_ratio
    bid = max(floor_bid, bid)

    if prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev < DAILY_SALARY * 0.9 and (hp <= 4 or no_water >= 1 or supply <= 18):
            bid = max(bid, highest_prev + 1.5)

    max_safe = budget
    if hp > 4 and no_water == 0:
        max_safe = min(max_safe, DAILY_SALARY * 0.78)
    else:
        max_safe = min(max_safe, DAILY_SALARY * 0.98)

    bid = min(bid, max_safe)
    if budget <= 0:
        return 0.0
    if bid < 0:
        bid = 0.0
    return float(round(min(bid, budget), 2))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 45.0))

    prev_bids = []
    aggressive_count = 0
    weak_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 120:
            rich_count += 1
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            aggressive_count += 1
        if opp.get('budget', 0) < 40 or opp.get('hp', 0) <= 1:
            weak_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                b = float(prev.get('bid', 0))
                if b >= 0:
                    prev_bids.append(b)
                    if b >= 90:
                        aggressive_count += 1
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgent = hp <= 2 or no_water_days >= 1
    semi_urgent = hp <= 4

    if urgent:
        target = max(92.0, highest_prev + 2.0, 110.0 * scarcity + 20.0)
    elif supply >= 23:
        target = 18.0 + 6.0 * scarcity
    elif supply >= 21:
        target = 28.0 + 10.0 * scarcity
    elif supply >= 19:
        target = max(38.0, avg_prev * 0.48, highest_prev * 0.42)
    elif supply >= 17:
        target = max(52.0, avg_prev * 0.62, highest_prev * 0.68)
    else:
        target = max(72.0, avg_prev * 0.78, highest_prev + 1.5)

    if aggressive_count >= 2 and supply <= 18 and not urgent:
        target += 8.0
    if rich_count >= 2 and supply <= 17:
        target += 6.0
    if weak_count >= 2 and hp > 3 and supply >= 20:
        target -= 8.0
    if semi_urgent and supply <= 18:
        target += 10.0
    if day >= 8 and hp > 5:
        target -= 6.0
    if day >= 8 and urgent:
        target += 8.0

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 20.0 * (8 - day)
    max_affordable = budget - reserve_floor
    if urgent:
        max_affordable = budget
    if max_affordable < 0:
        max_affordable = min(budget, DAILY_SALARY * 0.35)

    bid = min(budget, max_affordable, target)

    if urgent and bid < min(budget, 85.0):
        bid = min(budget, 85.0)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    david_like = []
    cindy_like = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid <= 80:
                    david_like.append(bid)
                else:
                    cindy_like.append(bid)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = max(david_like) if david_like else (min(prev_bids) if prev_bids else 0.0)
    expensive_field = len(cindy_like) > 0 and highest_prev > 120

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
        urgency += 1
    if tight_supply:
        urgency += 1

    if urgency >= 5:
        bid = max(78.0, moderate_prev + 8.0)
        if expensive_field and tight_supply:
            bid = max(bid, 96.0)
    elif urgency >= 3:
        bid = max(52.0, moderate_prev + 3.0)
        if ample_supply:
            bid -= 6.0
    elif urgency >= 1:
        bid = max(34.0, moderate_prev * 0.85)
        if expensive_field:
            bid = min(bid, 48.0)
        if ample_supply:
            bid -= 4.0
    else:
        bid = 24.0 if ample_supply else 30.0
        if moderate_prev > 0:
            bid = max(bid, min(40.0, moderate_prev * 0.7))
        if expensive_field:
            bid = min(bid, 36.0)

    if day >= 8:
        bid += 6.0
    elif day == 1:
        bid -= 2.0

    safe_cap = budget
    if hp > 6 and no_water == 0:
        safe_cap = min(safe_cap, budget * 0.45)
    elif hp > 4:
        safe_cap = min(safe_cap, budget * 0.6)
    else:
        safe_cap = min(safe_cap, budget * 0.85)

    bid = max(0.0, min(bid, safe_cap))
    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(bid, 70.0))

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    supply = day_context['supply']

    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, 20.0 if hp > 3 else 45.0))

    active_bids = []
    active_count = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None and bid > 0:
            active_bids.append(float(bid))
            active_count += 1

    if not active_bids:
        active_count = len(alive_opps)
        ref_high = 0.0
        ref_low = 0.0
    else:
        ref_high = max(active_bids)
        ref_low = min(active_bids)

    my_need = 1
    opp_units = 0
    for opp in alive_opps:
        req = opp.get('water_requirement', WATER_REQ)
        opp_units += int(supply // req)
    total_units = int(supply // WATER_REQ)
    scarce = total_units <= active_count
    abundant = total_units >= active_count + 1

    emergency = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if emergency:
        target = max(132.0, ref_high + 2.0)
    elif scarce:
        if pressured:
            target = max(126.0, ref_high + 1.5)
        else:
            target = 18.0
    elif abundant:
        if pressured:
            target = max(72.0, ref_low + 1.0)
        else:
            target = 8.0
    else:
        if pressured:
            target = max(88.0, ref_low + 1.0)
        else:
            target = 22.0

    if budget < 25:
        target = min(target, budget)
    elif budget < 80 and not emergency:
        target = min(target, 35.0)

    if hp >= 8 and no_water == 0 and scarce and ref_high >= 120:
        target = min(target, 12.0)

    bid = max(0.0, min(budget, target))
    return bid
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 35.0))
        return float(min(budget, 8.0))

    prev_bids = []
    cindy_like = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 130.0:
                cindy_like = True

    live_count = len(alive_opponents)
    high_supply = supply >= 22
    low_supply = supply <= 17

    if prev_bids:
        highest_prev = max(prev_bids)
        modest_prev = max([b for b in prev_bids if b < 120.0], default=0.0)
    else:
        highest_prev = 0.0
        modest_prev = 0.0

    danger = hp <= 2 or no_water_days >= 2
    caution = hp <= 4 or no_water_days >= 1

    if danger:
        if cindy_like:
            bid = 18.0 if high_supply else 32.0
        else:
            target = modest_prev + 3.0 if modest_prev > 0 else 36.0
            if low_supply:
                target += 8.0
            bid = target
        return float(min(budget, max(0.0, bid)))

    if caution:
        if cindy_like:
            bid = 10.0 if high_supply else 22.0
        else:
            target = modest_prev + 2.0 if modest_prev > 0 else 24.0
            if low_supply:
                target += 6.0
            bid = target
        return float(min(budget, max(0.0, bid)))

    if cindy_like:
        if high_supply:
            bid = 3.0
        elif low_supply:
            bid = 9.0
        else:
            bid = 6.0
    else:
        if modest_prev > 0:
            bid = min(20.0, modest_prev + 1.5)
        else:
            bid = 7.0 if high_supply else 11.0

    if day >= 8 and hp >= 6:
        bid *= 0.8

    return float(min(budget, max(0.0, bid)))
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    rich_threats = 0
    desperate_threats = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 100:
                rich_threats += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_threats += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    units = supply / WATER_REQ
    tight_supply = units < 2.0
    very_tight_supply = units < 1.4

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(DAILY_SALARY * 0.95, highest_prev + 2.0, 90.0))
        return float(bid)

    if hp <= 4 or no_water_days >= 1:
        if rich_threats >= 2 and not very_tight_supply:
            bid = min(budget, DAILY_SALARY * 0.82)
        else:
            bid = min(budget, max(DAILY_SALARY * 0.78, min(highest_prev + 1.5, DAILY_SALARY * 1.15)))
        return float(bid)

    if rich_threats >= 2:
        if very_tight_supply:
            bid = min(budget, DAILY_SALARY * 0.72)
        else:
            bid = min(budget, DAILY_SALARY * 0.18)
        return float(bid)

    if highest_prev >= 85:
        if tight_supply and desperate_threats == 0:
            bid = min(budget, DAILY_SALARY * 0.62)
        else:
            bid = min(budget, DAILY_SALARY * 0.22)
        return float(bid)

    if highest_prev > 0:
        target = avg_prev + 2.0
        floor_bid = DAILY_SALARY * 0.42 if tight_supply else DAILY_SALARY * 0.34
        cap_bid = DAILY_SALARY * 0.78
        bid = min(budget, max(floor_bid, min(target, cap_bid)))
        if day >= 8 and hp >= 6:
            bid = min(bid, DAILY_SALARY * 0.3)
        return float(bid)

    if tight_supply:
        return float(min(budget, DAILY_SALARY * 0.5))
    return float(min(budget, DAILY_SALARY * 0.36))
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
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    prev_high = 0.0
    prev_avg = 0.0
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY * 6:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > prev_high:
                prev_high = float(bid)
    if prev_bids:
        prev_avg = sum(prev_bids) / len(prev_bids)

    guaranteed_units = int(supply // WATER_REQ)

    if hp <= 2 or no_water >= 2:
        target = max(DAILY_SALARY * 0.95, prev_high + 2.0)
        return max(0.0, min(budget, target))

    if hp <= 4 or no_water >= 1:
        if guaranteed_units >= 2:
            target = max(DAILY_SALARY * 0.62, prev_avg + 1.0)
        else:
            target = max(DAILY_SALARY * 0.88, prev_high + 1.5)
        return max(0.0, min(budget, target))

    if guaranteed_units >= 2:
        if prev_high >= DAILY_SALARY * 1.3:
            target = DAILY_SALARY * 0.28
        elif prev_high >= DAILY_SALARY * 0.95:
            target = DAILY_SALARY * 0.36
        elif prev_avg > 0:
            target = max(DAILY_SALARY * 0.34, min(DAILY_SALARY * 0.58, prev_avg * 0.72))
        else:
            target = DAILY_SALARY * 0.4
        if urgent_opp >= 2:
            target += 4.0
        return max(0.0, min(budget, target))

    target = DAILY_SALARY * 0.58
    if prev_high >= DAILY_SALARY * 1.2:
        target = DAILY_SALARY * 0.42
    elif prev_high >= DAILY_SALARY * 0.9:
        target = DAILY_SALARY * 0.52
    elif prev_avg > 0:
        target = max(DAILY_SALARY * 0.5, prev_avg + 1.25)

    if rich_opp >= 2:
        target += 3.0
    if budget < DAILY_SALARY * 3:
        target *= 0.9

    return max(0.0, min(budget, target))
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
    cindy_prev_bid = None
    cindy_alive = False

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
            if agent_id == 'Cindy':
                cindy_alive = True
                if bid is not None:
                    cindy_prev_bid = bid

    if not alive_opponents:
        return max(0.0, min(budget, 8.0))

    tight_supply = supply <= 17
    very_tight_supply = supply <= 16
    danger = hp <= 3 or no_water_days >= 2
    moderate_risk = hp <= 5 or no_water_days >= 1

    if cindy_alive:
        anchor = cindy_prev_bid if cindy_prev_bid is not None else 117.0
    elif prev_bids:
        anchor = max(prev_bids)
    else:
        anchor = 60.0

    if danger:
        bid = min(budget, max(92.0, anchor + 1.0))
    elif very_tight_supply:
        bid = min(budget, max(82.0, anchor * 0.82))
    elif tight_supply and moderate_risk:
        bid = min(budget, max(72.0, anchor * 0.68))
    elif tight_supply:
        bid = min(budget, 38.0)
    else:
        bid = min(budget, 16.0)

    if day >= 8 and hp <= 5:
        bid = min(budget, max(bid, 88.0))

    if budget < bid:
        bid = budget

    return max(0.0, float(bid))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    dangerous_prev = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev['bid'])
                prev_bids.append(b)
                req = float(opp.get('water_requirement', WATER_REQ))
                obudget = float(opp.get('budget', 0.0))
                ono = int(opp.get('no_water_days', 0))
                ohp = float(opp.get('hp', 0.0))
                pressure = 0
                if ono >= 1:
                    pressure += 1
                if ohp <= 4:
                    pressure += 1
                if obudget >= b:
                    pressure += 1
                if req <= supply:
                    pressure += 1
                dangerous_prev.append((pressure, b))

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    strongest_live = 0.0
    if dangerous_prev:
        strongest_live = max([x[1] for x in dangerous_prev if x[0] >= 2] or [highest_prev])

    scarcity = (supply - WATER_REQ) / float(MAX_SUPPLY - WATER_REQ)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0
    tight = supply <= 17
    abundant = supply >= 22

    urgency = 0
    if hp <= 3:
        urgency += 2
    elif hp <= 6:
        urgency += 1
    if no_water >= 1:
        urgency += 2
    if tight:
        urgency += 1
    if day >= 8:
        urgency += 1

    reserve_floor = DAILY_SALARY * max(0, 10 - day) * 0.18
    spendable = max(0.0, budget - reserve_floor)
    if spendable <= 0:
        spendable = budget * 0.5

    if urgency >= 4:
        target = max(62.0, strongest_live + 2.0, highest_prev + 1.0)
    elif urgency >= 2:
        target = max(42.0, strongest_live * 0.92 + 2.0, highest_prev * 0.88 + 1.5)
    else:
        if abundant:
            target = 16.0 + (1.0 - scarcity) * 6.0
        else:
            target = max(24.0, highest_prev * 0.45 + 3.0)

    if highest_prev >= 110 and urgency <= 1:
        target = min(target, 34.0)
    if highest_prev >= 150 and hp > 4 and no_water == 0:
        target = min(target, 22.0)

    if hp <= 2 or no_water >= 2:
        target = max(target, 68.0)

    target = min(target, spendable, budget)
    if target < 0:
        target = 0.0
    return float(round(target, 2))
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 800:
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

    capacity = int(supply / WATER_REQ)
    scarcity = capacity <= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    for b in prev_bids:
        if b <= 120 and b > moderate_prev:
            moderate_prev = b
    if moderate_prev == 0.0:
        moderate_prev = min(highest_prev, 95.0) if highest_prev > 0 else 55.0

    critical = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if critical:
        bid = max(110.0, moderate_prev + 18.0)
        if scarcity:
            bid = max(bid, highest_prev + 3.0)
        bid = min(bid, 0.92 * budget)
        return float(max(0.0, min(budget, bid)))

    if pressured:
        bid = max(78.0, moderate_prev + 6.0)
        if scarcity:
            bid += 10.0
        if highest_prev >= 150:
            bid = max(bid, 96.0)
        bid = min(bid, 0.72 * budget)
        return float(max(0.0, min(budget, bid)))

    if scarcity:
        if highest_prev >= 150 or rich_opp >= 2:
            bid = 22.0
        else:
            bid = max(40.0, moderate_prev - 8.0)
    else:
        bid = 34.0
        if moderate_prev > 60:
            bid = max(bid, moderate_prev - 12.0)
        if urgent_opp >= 2:
            bid += 6.0

    reserve_floor = DAILY_SALARY * 0.18
    bid = min(bid, max(reserve_floor, 0.38 * budget))
    return float(max(0.0, min(budget, bid)))
"""
