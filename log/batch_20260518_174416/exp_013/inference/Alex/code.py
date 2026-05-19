# ============================================================
# Experiment: exp_013
# Agent: Alex
# Source: exp_013
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return min(budget, 20)
        return min(budget, 8)

    prev_bids = []
    urgent_opponents = 0
    rich_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= budget:
            rich_opponents += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    player_count = 1 + len(alive_opponents)
    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < player_count

    base = DAILY_SALARY * 0.42
    if supply >= 23:
        base = DAILY_SALARY * 0.28
    elif supply <= 17:
        base = DAILY_SALARY * 0.62

    if scarcity:
        base += 8

    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.72)
    elif hp >= 8 and no_water_days == 0 and supply >= 22:
        base = min(base, DAILY_SALARY * 0.22)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        target = max(avg_prev + 1.0, highest_prev + 1.5)
        if highest_prev >= DAILY_SALARY * 0.9:
            if hp > 4 and no_water_days == 0:
                base = min(base, DAILY_SALARY * 0.3)
            else:
                base = max(base, DAILY_SALARY * 0.92)
        else:
            base = max(base, target)

    if urgent_opponents >= max(1, len(alive_opponents) // 2):
        base += 4
    if rich_opponents == len(alive_opponents) and len(alive_opponents) > 0:
        base += 3

    reserve = 0
    if day_context['day'] <= 3:
        reserve = 20
    elif day_context['day'] <= 7:
        reserve = 10

    affordable = max(0, budget - reserve)
    bid = min(base, budget)
    if affordable > 0:
        bid = min(bid, max(affordable, min(budget, 12)))

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.95))

    if bid < 0:
        bid = 0
    return float(round(bid, 2))
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= budget:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0.0
    if supply <= 16:
        scarcity = 1.0
    elif supply <= 18:
        scarcity = 0.6
    elif supply <= 21:
        scarcity = 0.25

    urgency = 0.0
    if hp <= 2:
        urgency += 1.2
    elif hp <= 4:
        urgency += 0.7
    if no_water >= 2:
        urgency += 1.0
    elif no_water >= 1:
        urgency += 0.45

    pressure = 0.0
    if highest_prev >= 130:
        pressure += 0.9
    elif highest_prev >= 90:
        pressure += 0.55
    elif highest_prev >= 40:
        pressure += 0.2

    pressure += min(0.5, desperate_count * 0.15)
    pressure += min(0.3, rich_count * 0.08)

    conserve = 0.0
    if budget < DAILY_SALARY * 2:
        conserve += 0.45
    elif budget < DAILY_SALARY * 4:
        conserve += 0.2
    if day >= 8:
        conserve -= 0.1

    score = urgency + scarcity + pressure - conserve

    if hp <= 2 or no_water >= 2:
        bid = max(62.0, avg_prev * 0.55 + 8.0)
    elif score >= 2.0:
        bid = max(52.0, avg_prev * 0.42 + 6.0)
    elif score >= 1.2:
        bid = max(34.0, avg_prev * 0.28 + 4.0)
    else:
        bid = 16.0 + supply * 0.2

    if highest_prev >= 130 and urgency < 0.7 and supply >= 20:
        bid = min(bid, 22.0)
    if highest_prev <= 1 and scarcity < 0.7:
        bid = max(bid, 24.0)

    max_safe = budget
    if hp > 4 and no_water == 0:
        max_safe = min(max_safe, budget * 0.38 + 8.0)
    elif hp > 2:
        max_safe = min(max_safe, budget * 0.55 + 10.0)

    bid = min(bid, max_safe)
    bid = min(bid, budget)
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        bid = DAILY_SALARY * 0.22
        if hp <= 2 or no_water_days >= 2:
            bid = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, bid)))

    highest_prev_bid = 0.0
    cindy_prev_bid = None
    cindy_alive = False
    pressure_count = 0

    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        prev_bid = 0.0
        if isinstance(prev, dict) and prev.get('bid') is not None:
            prev_bid = prev.get('bid', 0.0)
        if prev_bid > highest_prev_bid:
            highest_prev_bid = prev_bid
        if prev_bid >= DAILY_SALARY * 0.75:
            pressure_count += 1
        if opp_id == 'Cindy':
            cindy_alive = True
            cindy_prev_bid = prev_bid

    scarcity = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0
    low_supply = 1.0 - scarcity

    urgent = hp <= 2 or no_water_days >= 2
    fragile = hp <= 4 or no_water_days >= 1

    if cindy_alive and cindy_prev_bid is not None:
        anchor = cindy_prev_bid
    else:
        anchor = highest_prev_bid

    if urgent:
        if supply <= 17:
            bid = max(DAILY_SALARY * 0.96, anchor + 2.0)
        else:
            bid = max(DAILY_SALARY * 0.82, anchor * 0.92)
    elif fragile:
        if anchor >= DAILY_SALARY * 1.2:
            bid = DAILY_SALARY * (0.42 + 0.18 * low_supply)
        elif anchor >= DAILY_SALARY * 0.85:
            bid = DAILY_SALARY * (0.48 + 0.18 * low_supply)
        else:
            bid = max(DAILY_SALARY * (0.44 + 0.16 * low_supply), anchor + 1.25)
    else:
        if supply >= 22:
            bid = DAILY_SALARY * 0.18
        elif supply >= 19:
            if anchor >= DAILY_SALARY * 1.0:
                bid = DAILY_SALARY * 0.24
            else:
                bid = DAILY_SALARY * 0.32
        else:
            if anchor >= DAILY_SALARY * 1.2:
                bid = DAILY_SALARY * 0.28
            elif pressure_count >= 2:
                bid = DAILY_SALARY * 0.38
            else:
                bid = max(DAILY_SALARY * 0.36, anchor + 1.0)

    if budget < DAILY_SALARY * 0.8 and not urgent:
        bid = min(bid, budget * 0.55)
    elif budget < DAILY_SALARY * 1.5 and fragile:
        bid = min(bid, budget * 0.72)

    if urgent:
        bid = max(bid, min(budget, DAILY_SALARY * 0.75))

    bid = max(0.0, min(budget, bid))
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_aggressive = 0
    desperate_opp = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 75 and opp.get('budget', 0) >= 300:
                    rich_aggressive += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 18)

    max_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0

    if supply >= 24:
        base = 8
    elif supply >= 22:
        base = 14
    elif supply >= 20:
        base = 22
    elif supply >= 18:
        base = 34
    else:
        base = 48

    if max_prev > 0:
        if supply >= 22:
            base = min(base, max_prev * 0.35)
        elif supply >= 20:
            base = max(base, avg_prev * 0.45)
        elif supply >= 18:
            base = max(base, avg_prev * 0.6)
        else:
            base = max(base, max_prev * 0.72)

    if rich_aggressive >= 2 and supply <= 19 and hp >= 5 and no_water == 0:
        base *= 0.7

    if desperate_opp >= 2 and supply <= 18:
        base *= 1.15

    if hp <= 2:
        base = max(base, max_prev + 2 if max_prev > 0 else 78)
    elif hp <= 4:
        base = max(base, 58)

    if no_water >= 2:
        base = max(base, max_prev + 3 if max_prev > 0 else 82)
    elif no_water >= 1:
        base = max(base, 62)

    if day >= 8 and hp > 5 and budget < 220:
        base *= 0.9

    if budget < 120:
        base = min(base, budget * 0.72)
    elif budget < 200:
        base = min(base, budget * 0.82)

    if supply >= 23 and hp >= 6 and no_water == 0:
        base = min(base, 16)

    bid = min(budget, max(0, round(base, 2)))
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    sane_bids = []
    desperate_count = 0
    rich_aggressive = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) > 500:
                prev = opp.get('previous_trace', {}) or {}
                pb = prev.get('bid')
                if pb is not None and pb >= 100:
                    rich_aggressive += 1
            prev = opp.get('previous_trace', {}) or {}
            pb = prev.get('bid')
            if pb is not None:
                prev_bids.append(pb)
                if pb <= 95:
                    sane_bids.append(pb)

    if budget <= 0:
        return 0.0

    slots = int(supply / WATER_REQ)
    if slots < 1:
        slots = 1

    if not alive:
        return float(min(budget, 18.0))

    high_prev = max(prev_bids) if prev_bids else 0.0
    sane_high = max(sane_bids) if sane_bids else 0.0

    urgent = hp <= 2 or no_water >= 1
    very_urgent = hp <= 1 or no_water >= 2

    if very_urgent:
        bid = 112.0 if rich_aggressive == 0 else 128.0
        return float(min(budget, bid))

    if urgent:
        base = max(78.0, sane_high + 4.0)
        if rich_aggressive > 0:
            base = max(base, 96.0)
        if slots >= 2:
            base -= 6.0
        return float(min(budget, base))

    if slots >= 2:
        if rich_aggressive > 0:
            bid = 24.0 if hp >= 4 else 38.0
        else:
            bid = max(26.0, min(52.0, sane_high + 2.0 if sane_high > 0 else 32.0))
        if desperate_count >= 2:
            bid += 6.0
        return float(min(budget, bid))

    bid = max(34.0, sane_high + 3.0 if sane_high > 0 else 40.0)
    if rich_aggressive > 0:
        bid = 22.0 if hp >= 5 else 44.0
    if desperate_count >= 2:
        bid += 8.0
    if day >= 8 and hp >= 4:
        bid -= 6.0
    return float(min(budget, max(0.0, bid)))
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

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    threat_bids = []
    soft_count = 0
    hard_count = 0

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = None
            if prev:
                bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('budget', 0) >= DAILY_SALARY * 0.8 and opp.get('hp', 0) >= 6:
                    threat_bids.append(float(bid))
                if float(bid) <= 40:
                    soft_count += 1
                if float(bid) >= 90:
                    hard_count += 1

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.25))

    max_prev = max(prev_bids) if prev_bids else 0.0
    threat_prev = max(threat_bids) if threat_bids else max_prev

    supply_tight = supply <= 17
    supply_loose = supply >= 22

    urgency = 0
    if hp <= 3:
        urgency += 3
    elif hp <= 5:
        urgency += 2
    elif hp <= 7:
        urgency += 1

    if no_water_days >= 2:
        urgency += 3
    elif no_water_days >= 1:
        urgency += 1

    if supply_tight:
        urgency += 2
    elif supply_loose:
        urgency -= 1

    if hard_count >= 2:
        urgency += 1
    if soft_count >= 2:
        urgency -= 1

    days_left = 11 - day
    reserve_target = max(0.0, days_left * DAILY_SALARY * 0.38)
    spendable = max(0.0, budget - reserve_target)

    if urgency >= 6:
        base = max(95.0, threat_prev + 4.0, DAILY_SALARY * 1.15)
    elif urgency >= 4:
        base = max(72.0, threat_prev + 2.5, DAILY_SALARY * 0.92)
    elif urgency >= 2:
        base = max(48.0, min(threat_prev + 1.0, 88.0), DAILY_SALARY * 0.62)
    else:
        if supply_loose and hp >= 7:
            base = DAILY_SALARY * 0.28
        else:
            base = max(26.0, min(threat_prev * 0.72, 58.0), DAILY_SALARY * 0.4)

    if budget < DAILY_SALARY * 1.2:
        base = min(base, budget * 0.72)
    elif spendable > 0:
        base = min(base, spendable + DAILY_SALARY * 0.35)

    if hp <= 2 or no_water_days >= 2:
        base = max(base, min(budget, threat_prev + 5.0 if threat_prev > 0 else 90.0))

    bid = max(0.0, min(budget, base))
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

    if budget <= 0:
        return 0.0

    alive_opps = []
    yesterday_bids = []
    urgent_opp_bids = []
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            prev_bid = 0.0
            if prev and prev.get('bid') is not None:
                prev_bid = float(prev.get('bid', 0.0))
                yesterday_bids.append(prev_bid)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_bids.append(prev_bid)
            if opp.get('budget', 0) >= 200 and prev_bid >= 100:
                rich_aggressive += 1

    slots = max(1, int(supply // WATER_REQ))
    pressure = len(alive_opps) - slots

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    urgent_prev = max(urgent_opp_bids) if urgent_opp_bids else highest_prev

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

    if slots == 1:
        danger += 2
    if pressure >= 2:
        danger += 1
    if rich_aggressive >= 2:
        danger += 1

    safe_floor = DAILY_SALARY * 0.22
    conserve_bid = DAILY_SALARY * 0.32
    contest_bid = DAILY_SALARY * 0.78
    emergency_bid = DAILY_SALARY * 1.08

    if not alive_opps:
        bid = safe_floor
    elif danger <= 1:
        if highest_prev >= 120:
            bid = safe_floor
        else:
            bid = max(conserve_bid, min(55.0, highest_prev + 2.0))
    elif danger <= 3:
        if urgent_prev >= 120:
            bid = contest_bid
        else:
            bid = max(contest_bid, urgent_prev + 3.0)
    else:
        if hp <= 2 or no_water_days >= 2:
            bid = max(emergency_bid, urgent_prev + 6.0)
        else:
            bid = max(contest_bid + 10.0, urgent_prev + 4.0)

    if day >= 8:
        bid += 8.0
    if day >= 9:
        bid += 10.0

    if budget < DAILY_SALARY:
        bid = min(bid, budget)
    else:
        reserve_days = max(0, 10 - int(day))
        reserve_target = reserve_days * DAILY_SALARY * 0.18
        spend_cap = max(0.0, budget - reserve_target)
        bid = min(bid, max(DAILY_SALARY * 0.2, spend_cap))

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_threat = 0
    desperate_threat = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_threat += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_threat += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    scarcity = 1.0
    if slots <= 1:
        scarcity = 1.35
    elif slots == 2:
        scarcity = 1.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    emergency = hp <= 3 or no_water >= 1
    critical = hp <= 2 or no_water >= 2

    if critical:
        base = max(62.0, highest_prev + 2.0)
    elif emergency:
        base = max(48.0, avg_prev + 3.0)
    else:
        base = 24.0
        if highest_prev >= 110:
            base = 16.0
        elif highest_prev >= 85:
            base = 22.0
        elif highest_prev >= 55:
            base = highest_prev + 1.5
        elif highest_prev >= 20:
            base = max(28.0, highest_prev + 1.0)

    base *= scarcity
    base += rich_threat * 2.0 + desperate_threat * 1.5

    if budget < DAILY_SALARY:
        base = min(base, budget * 0.72)
    elif budget < DAILY_SALARY * 2 and not emergency:
        base = min(base, budget * 0.45)

    if not emergency and highest_prev >= 120:
        base = min(base, 20.0)

    bid = max(0.0, min(budget, base))
    return float(round(bid, 2))
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
    opp_need_count = 0
    rich_opp = 0

    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                opp_need_count += 1
            if opp.get('budget', 0) >= 120:
                rich_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0
    if supply <= 16:
        scarcity = 2
    elif supply <= 19:
        scarcity = 1

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4:
        urgency = 2
    elif hp <= 6 or no_water_days >= 1:
        urgency = 1

    if urgency >= 3:
        bid = max(0.92 * DAILY_SALARY, highest_prev + 3.0)
        if scarcity >= 1:
            bid += 8.0
        return min(budget, bid)

    if urgency == 2:
        if highest_prev >= 150:
            bid = 52.0 + 6.0 * scarcity
        elif highest_prev >= 95:
            bid = highest_prev + 2.5 + 4.0 * scarcity
        else:
            bid = 58.0 + 6.0 * scarcity + 3.0 * opp_need_count
        return min(budget, bid)

    if urgency == 1:
        if highest_prev >= 160:
            bid = 34.0 + 4.0 * scarcity
        elif highest_prev >= 110:
            bid = 46.0 + 5.0 * scarcity
        else:
            bid = max(40.0, avg_prev * 0.62) + 4.0 * scarcity
        if rich_opp >= 2 and scarcity >= 1:
            bid += 4.0
        return min(budget, bid)

    if highest_prev >= 170:
        bid = 20.0 + 3.0 * scarcity
    elif highest_prev >= 130:
        bid = 28.0 + 4.0 * scarcity
    elif highest_prev >= 90:
        bid = min(highest_prev + 1.5, 52.0 + 5.0 * scarcity)
    else:
        bid = 32.0 + 4.0 * scarcity

    if day >= 8 and hp >= 7:
        bid *= 0.9

    if budget < 45:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, 0.78 * DAILY_SALARY + 10.0 * scarcity)

    if bid < 0:
        bid = 0
    return bid
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    live_prev_bids = []
    rich_threat = False
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120 and opp.get('hp', 0) > 0:
                rich_threat = True
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                try:
                    live_prev_bids.append(float(bid))
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(live_prev_bids) if live_prev_bids else 0.0
    avg_prev = sum(live_prev_bids) / len(live_prev_bids) if live_prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water >= 2:
        urgency += 1.0
    elif no_water == 1:
        urgency += 0.45
    urgency += 0.55 * scarcity
    if day >= 8:
        urgency += 0.2

    if hp <= 2 or no_water >= 2:
        bid = max(58.0, highest_prev + 2.0)
        if rich_threat and scarcity > 0.6:
            bid = max(bid, 92.0)
        return float(min(budget, bid))

    if scarcity < 0.25 and hp >= 5 and no_water == 0:
        return float(min(budget, 16.0))

    if highest_prev >= 120:
        if urgency < 0.9:
            bid = 22.0 + 10.0 * scarcity
        else:
            bid = 72.0 + 18.0 * scarcity
    elif highest_prev >= 70:
        if urgency < 0.7:
            bid = max(28.0, avg_prev * 0.55)
        else:
            bid = min(highest_prev + 3.0, 88.0)
    else:
        bid = 34.0 + 18.0 * scarcity + 8.0 * urgency

    if rich_threat and scarcity > 0.7 and urgency >= 0.8:
        bid = max(bid, 85.0)

    reserve_floor = 20.0 if day < 8 else 0.0
    bid = min(bid, max(0.0, budget - reserve_floor))
    bid = max(0.0, bid)
    return float(min(budget, bid))
"""
