# ============================================================
# Experiment: exp_062
# Agent: Alex
# Source: exp_062
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = False
    rich_opp_pressure = 0.0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
            if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 2:
                urgent_opp = True
            rich_opp_pressure = max(rich_opp_pressure, float(opp.get('daily_salary', 0)) * 0.75)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    scarcity = 1.0 - ((supply - 15.0) / 10.0)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    base = DAILY_SALARY * (0.42 + 0.28 * scarcity)

    if hp <= 2 or no_water_days >= 2:
        emergency = DAILY_SALARY * (0.9 + 0.06 * scarcity)
        if prev_bids:
            emergency = max(emergency, max(prev_bids) + 2.0)
        return float(min(budget, emergency))

    if hp <= 4 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * (0.68 + 0.12 * scarcity))

    if prev_bids:
        top_prev = max(prev_bids)
        if supply <= 17.0:
            target = top_prev + 2.5
        elif supply <= 20.0:
            target = top_prev + 1.0
        else:
            target = top_prev * 0.92
        base = max(base, target)

    if urgent_opp and supply <= 18.0:
        base += 3.0

    if rich_opp_pressure > 0:
        base = max(base, min(rich_opp_pressure, DAILY_SALARY * 0.88))

    if supply >= 23.0 and hp >= 5 and no_water_days == 0:
        base = min(base, DAILY_SALARY * 0.48)

    reserve_floor = 0.0
    if hp >= 5 and no_water_days == 0:
        reserve_floor = budget * 0.55
    elif hp >= 3:
        reserve_floor = budget * 0.35
    else:
        reserve_floor = budget * 0.15

    bid = min(base, budget)
    if budget - bid < reserve_floor and hp > 2 and no_water_days < 2:
        bid = max(0.0, budget - reserve_floor)
        if prev_bids and supply <= 18.0:
            bid = max(bid, min(budget, max(prev_bids) + 0.5))

    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 70
    WATER_REQ = 13

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    cindy_like = False
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 110:
                cindy_like = True

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 8.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    low_comp = 0
    for b in prev_bids:
        if b <= 45:
            low_comp += 1

    emergency = hp <= 3 or no_water >= 2
    danger = hp <= 5 or no_water >= 1
    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if emergency:
        if cindy_like:
            bid = min(budget, 118.0)
        else:
            bid = min(budget, max(62.0, highest_prev + 4.0, DAILY_SALARY * 0.95))
        return float(max(0.0, bid))

    if danger and tight_supply:
        if cindy_like:
            bid = min(budget, 114.0)
        else:
            bid = min(budget, max(52.0, highest_prev + 2.0, DAILY_SALARY * 0.8))
        return float(max(0.0, bid))

    if cindy_like:
        if ample_supply and hp >= 7 and no_water == 0:
            return float(min(budget, 3.0))
        if tight_supply:
            return float(min(budget, 18.0))
        return float(min(budget, 8.0))

    if highest_prev >= 80:
        if hp >= 7 and no_water == 0:
            return float(min(budget, 10.0))
        return float(min(budget, 60.0))

    if highest_prev > 0:
        if low_comp >= 2 and ample_supply:
            bid = max(12.0, highest_prev + 1.5)
        elif tight_supply:
            bid = max(28.0, highest_prev + 2.0)
        else:
            bid = max(18.0, highest_prev + 1.0)
        return float(min(budget, bid))

    if day <= 2:
        return float(min(budget, 14.0 if ample_supply else 20.0))
    if tight_supply:
        return float(min(budget, 24.0))
    return float(min(budget, 12.0))
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opps = 0
    rich_opps = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY:
                rich_opps += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opps += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev['bid']))
                except Exception:
                    pass

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    tight_supply = supply <= 17.0
    loose_supply = supply >= 22.0

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

    if tight_supply:
        danger += 1

    if day >= 8:
        danger += 1

    if highest_prev >= 100:
        market = 'crazy'
    elif highest_prev >= 70:
        market = 'hot'
    elif highest_prev >= 35:
        market = 'warm'
    else:
        market = 'cool'

    if danger >= 5:
        bid = max(95.0, highest_prev + 3.0)
    elif danger >= 3:
        if market == 'crazy':
            bid = 88.0
        elif market == 'hot':
            bid = max(72.0, avg_prev * 0.92)
        elif market == 'warm':
            bid = max(46.0, highest_prev + 2.0)
        else:
            bid = 42.0
    else:
        if loose_supply and urgent_opps == 0:
            bid = 16.0
        elif market == 'crazy':
            bid = 12.0 if hp > 4 else 76.0
        elif market == 'hot':
            bid = 22.0 if hp > 5 else 58.0
        elif market == 'warm':
            bid = max(24.0, min(40.0, avg_prev * 0.75))
        else:
            bid = 28.0 if tight_supply else 20.0

    if rich_opps >= 2 and hp <= 4:
        bid = max(bid, highest_prev + 2.5 if highest_prev > 0 else 65.0)

    if budget < bid:
        bid = budget

    min_live_bid = 0.0
    if hp <= 2 or no_water_days >= 2:
        min_live_bid = min(budget, 35.0)
    elif hp <= 4 or no_water_days >= 1:
        min_live_bid = min(budget, 22.0)

    if bid < min_live_bid:
        bid = min_live_bid

    if bid < 0:
        bid = 0.0

    return float(round(min(bid, budget), 2))
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    opp_pressure = 0.0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev['bid']
                prev_bids.append(b)
                if b > opp_pressure:
                    opp_pressure = b

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.55))
        return float(min(budget, DAILY_SALARY * 0.2))

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    urgency = 0.0
    if hp <= 2:
        urgency += 0.75
    elif hp <= 4:
        urgency += 0.45
    elif hp <= 6:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.9
    elif no_water_days >= 1:
        urgency += 0.45

    if day >= 8:
        urgency += 0.15

    pressure_bid = DAILY_SALARY * (0.52 + 0.35 * scarcity)
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        pressure_bid = max(pressure_bid, avg_prev * 0.92)
        if scarcity > 0.55 or urgency > 0.5:
            pressure_bid = max(pressure_bid, max_prev + 2.0)

    if supply >= 22 and urgency < 0.5:
        bid = DAILY_SALARY * 0.22
    elif supply >= 20 and urgency < 0.35:
        bid = DAILY_SALARY * 0.3
    else:
        bid = pressure_bid

    if urgency >= 1.2:
        bid = max(bid, DAILY_SALARY * 0.98)
    elif urgency >= 0.8:
        bid = max(bid, DAILY_SALARY * 0.82)
    elif urgency >= 0.45:
        bid = max(bid, DAILY_SALARY * 0.62)

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.92)
    elif budget > DAILY_SALARY * 8 and urgency < 0.4 and supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.4)

    bid = max(0.0, min(float(budget), float(bid)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    opp_reqs = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            opp_reqs.append(opp.get('water_requirement', WATER_REQ))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    total_req = WATER_REQ
    for r in opp_reqs:
        total_req += r

    scarcity_ratio = total_req / max(supply, 1.0)
    very_tight = supply <= WATER_REQ * 1.25
    tight = scarcity_ratio >= 2.2 or supply <= WATER_REQ * 1.6

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    critical = hp <= 2 or no_water_days >= 2
    urgent = hp <= 4 or no_water_days >= 1
    late_game = day >= 8

    if critical:
        target = max(DAILY_SALARY * 1.9, highest_prev + 4.0)
        if very_tight:
            target = max(target, DAILY_SALARY * 2.15)
        return float(min(budget, target))

    if urgent:
        if highest_prev >= 145:
            target = highest_prev + 2.5
        elif highest_prev >= 115:
            target = highest_prev + 3.0
        else:
            target = DAILY_SALARY * 1.45
        if very_tight:
            target += 6.0
        return float(min(budget, target))

    if tight:
        if highest_prev >= 140:
            target = highest_prev + 1.5
        elif highest_prev >= 110:
            target = highest_prev + 2.0
        else:
            target = max(DAILY_SALARY * 1.2, avg_prev + 8.0)
        if late_game:
            target += 3.0
        return float(min(budget, target))

    if highest_prev >= 145 and hp >= 5:
        return float(min(budget, DAILY_SALARY * 0.28))
    if highest_prev >= 120 and hp >= 6:
        return float(min(budget, DAILY_SALARY * 0.42))

    base = DAILY_SALARY * 0.58
    if late_game:
        base = DAILY_SALARY * 0.68
    if hp >= 8 and budget < DAILY_SALARY * 4:
        base = DAILY_SALARY * 0.45

    return float(min(budget, base))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    opp_hp_low = 0
    opp_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            opp_count += 1
            if opp.get('hp', 10) <= 2:
                opp_hp_low += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if opp_count == 0:
        return min(budget, 28.0)

    high_supply = supply >= 22
    medium_supply = supply >= 19
    danger = hp <= 2 or no_water_days >= 2
    caution = hp >= 5 and no_water_days == 0 and not high_supply

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if danger:
        if high_supply:
            bid = max(92.0, highest_prev + 2.0)
        else:
            bid = max(118.0, highest_prev + 4.0)
        return min(budget, bid)

    if caution and highest_prev >= 110.0:
        return min(budget, 18.0)

    if high_supply:
        if highest_prev <= 85.0:
            bid = max(62.0, highest_prev + 2.0)
        elif highest_prev <= 120.0:
            bid = max(74.0, avg_prev + 1.5)
        else:
            bid = 58.0
        if opp_hp_low >= 2:
            bid += 4.0
        return min(budget, bid)

    if medium_supply:
        if highest_prev >= 130.0:
            bid = 30.0 if hp >= 4 else 96.0
        elif highest_prev >= 100.0:
            bid = 42.0 if hp >= 5 else 88.0
        else:
            bid = max(68.0, highest_prev + 2.0)
        return min(budget, bid)

    if highest_prev >= 120.0:
        bid = 20.0 if hp >= 5 else 102.0
    elif highest_prev >= 90.0:
        bid = 36.0 if hp >= 4 else 94.0
    else:
        bid = max(72.0, highest_prev + 3.0)

    if day >= 8 and hp <= 4:
        bid = max(bid, 98.0)

    return min(budget, bid)
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        base = DAILY_SALARY * 0.25
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    bob_like = []
    cindy_like = []
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 120:
                cindy_like.append(float(bid))
            else:
                bob_like.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    bob_anchor = max(bob_like) if bob_like else (max(prev_bids) if prev_bids else 55.0)

    alive_count = len(alive)
    tight_supply = supply <= WATER_REQ * alive_count
    very_tight = supply <= WATER_REQ * max(1, alive_count - 1)

    urgency = 0
    if hp <= 3:
        urgency += 2
    elif hp <= 5:
        urgency += 1
    if no_water_days >= 2:
        urgency += 3
    elif no_water_days >= 1:
        urgency += 1
    if very_tight:
        urgency += 2
    elif tight_supply:
        urgency += 1
    if day >= 8:
        urgency += 1

    if urgency >= 5:
        bid = max(DAILY_SALARY * 0.95, bob_anchor + 8.0)
    elif urgency >= 3:
        bid = max(DAILY_SALARY * 0.72, bob_anchor + 2.5)
    elif urgency >= 1:
        if highest_prev >= 120:
            bid = DAILY_SALARY * 0.42
        else:
            bid = max(DAILY_SALARY * 0.5, bob_anchor)
    else:
        if highest_prev >= 120:
            bid = DAILY_SALARY * 0.22
        else:
            bid = DAILY_SALARY * 0.35

    if budget < DAILY_SALARY * 2 and urgency <= 2:
        bid = min(bid, DAILY_SALARY * 0.4)
    if budget < DAILY_SALARY and urgency >= 3:
        bid = max(min(budget, DAILY_SALARY * 0.9), budget * 0.85)

    return float(max(0.0, min(budget, bid)))
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

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        bid = min(budget, DAILY_SALARY * 0.28)
        return float(max(0.0, bid))

    opp_prev_bids = []
    desperate_count = 0
    rich_count = 0
    urgent_pressure = 0

    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= budget:
            rich_count += 1

        prev = opp.get('previous_trace', {})
        if prev:
            pbid = prev.get('bid')
            if pbid is not None:
                opp_prev_bids.append(float(pbid))
            if prev.get('status') == 'won':
                urgent_pressure += 1

    highest_prev = max(opp_prev_bids) if opp_prev_bids else 0.0
    avg_prev = sum(opp_prev_bids) / len(opp_prev_bids) if opp_prev_bids else 0.0

    base = DAILY_SALARY * 0.42

    if supply >= 23:
        base = DAILY_SALARY * 0.22
    elif supply >= 20:
        base = DAILY_SALARY * 0.32
    elif supply <= 16:
        base = DAILY_SALARY * 0.72
    elif supply <= 18:
        base = DAILY_SALARY * 0.56

    if hp <= 2 or no_water_days >= 2:
        bid = max(base, DAILY_SALARY * 0.96)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(base, DAILY_SALARY * 0.78)
    else:
        bid = base

    if highest_prev > 0:
        if highest_prev >= 120:
            if hp >= 6 and supply >= 19:
                bid = min(bid, DAILY_SALARY * 0.26)
            else:
                bid = max(bid, DAILY_SALARY * 0.74)
        elif highest_prev >= 90:
            if hp >= 7 and supply >= 20:
                bid = min(bid, DAILY_SALARY * 0.30)
            else:
                bid = max(bid, min(highest_prev * 0.72, DAILY_SALARY * 0.82))
        else:
            target = max(avg_prev + 2.0, DAILY_SALARY * 0.45)
            bid = max(bid, target)

    if desperate_count >= 2 and supply <= 18:
        bid = max(bid, DAILY_SALARY * 0.86)
    elif desperate_count == 0 and supply >= 20 and hp >= 6:
        bid = min(bid, DAILY_SALARY * 0.27)

    if rich_count >= 2 and hp >= 6 and supply >= 19:
        bid = min(bid, DAILY_SALARY * 0.34)

    if day >= 8:
        if hp >= 5:
            bid = min(bid, DAILY_SALARY * 0.38)
        else:
            bid = max(bid, DAILY_SALARY * 0.72)

    max_safe = budget
    if hp >= 6:
        reserve = max(0.0, (10 - day) * DAILY_SALARY * 0.18)
        max_safe = max(0.0, budget - reserve)
        if max_safe <= 0:
            max_safe = min(budget, DAILY_SALARY * 0.25)

    bid = min(bid, max_safe)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(bid)
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
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_threat = 0
    desperate_threat = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_threat += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_threat += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return max(0.0, min(budget, 12.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    base = 18.0

    if supply <= 16:
        base = 42.0
    elif supply <= 18:
        base = 30.0
    else:
        base = 20.0

    if highest_prev >= 150:
        base = min(base, 18.0)
    elif highest_prev >= 90:
        base = max(base, 26.0)
    elif highest_prev > 0:
        base = max(base, min(40.0, avg_prev * 0.55))

    if rich_threat >= 2 and supply <= 17:
        base += 8.0
    if desperate_threat >= 1 and supply <= 18:
        base += 6.0

    if hp <= 2:
        base = max(base, 95.0)
    elif hp <= 4:
        base = max(base, 62.0)

    if no_water >= 2:
        base = max(base, 110.0)
    elif no_water >= 1:
        base = max(base, 75.0)

    if day >= 8:
        base += 8.0

    if budget < 40:
        base = min(base, budget)
    elif budget < 90:
        base = min(base, max(28.0, budget * 0.72))

    bid = max(0.0, min(budget, base))
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
            alive.append((agent_id, opp))

    if not alive:
        return float(min(budget, 18.0))

    yesterday_bids = []
    urgent_opp = 0
    rich_opp = 0
    max_prev_bid = 0.0
    for agent_id, opp in alive:
        if opp.get('budget', 0) >= 140:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = float(prev['bid'])
            yesterday_bids.append(bid)
            if bid > max_prev_bid:
                max_prev_bid = bid
            if prev.get('status') == 'won' and bid >= 80:
                urgent_opp += 1

    guaranteed_units = int(supply // WATER_REQ)
    contested = guaranteed_units <= 1

    base = 0.0

    if hp <= 2 or no_water_days >= 2:
        base = 92.0
    elif hp <= 4 or no_water_days >= 1:
        base = 68.0
    else:
        if contested:
            base = 44.0
        else:
            base = 18.0

    if max_prev_bid >= 130:
        if hp >= 5 and no_water_days == 0:
            base -= 6.0
        else:
            base += 18.0
    elif max_prev_bid >= 90:
        if contested:
            base += 10.0
        else:
            base += 4.0
    elif max_prev_bid <= 40 and not contested:
        base += 3.0

    if urgent_opp >= 2 and hp >= 5 and no_water_days == 0:
        base -= 5.0
    elif urgent_opp == 0 and contested:
        base += 6.0

    if rich_opp >= 2 and contested and hp <= 4:
        base += 8.0

    if day >= 8:
        base += 8.0
    elif day >= 6 and hp <= 4:
        base += 6.0

    if budget < 70:
        base = min(base, budget * 0.92)
    elif budget < 140 and hp >= 5 and no_water_days == 0 and not contested:
        base = min(base, 26.0)

    if not contested and hp >= 6 and no_water_days == 0:
        base = min(base, 24.0)

    if contested and hp <= 3:
        base = max(base, 84.0)

    bid = max(0.0, min(float(budget), float(base)))
    return float(round(bid, 2))
"""
