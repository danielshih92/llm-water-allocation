# ============================================================
# Experiment: exp_073
# Agent: Alex
# Source: exp_073
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
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.35)

    scarcity = WATER_REQ / max(1.0, supply)
    severe_need = hp <= 3 or no_water_days >= 1
    moderate_need = hp <= 5

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

    if severe_need:
        bid = max(DAILY_SALARY * 0.9, highest_prev + 2)
    elif scarcity > 0.75:
        if highest_prev >= DAILY_SALARY * 0.85:
            bid = DAILY_SALARY * (0.42 if hp > 6 else 0.88)
        else:
            bid = max(DAILY_SALARY * 0.62, avg_prev + 2)
    elif scarcity > 0.6:
        if desperate_count >= 1:
            bid = max(DAILY_SALARY * 0.58, highest_prev + 1)
        else:
            bid = max(DAILY_SALARY * 0.48, avg_prev)
    else:
        bid = DAILY_SALARY * 0.34
        if moderate_need:
            bid = DAILY_SALARY * 0.5

    if rich_count >= 2 and not severe_need:
        bid *= 0.92

    if hp >= 8 and no_water_days == 0 and highest_prev >= DAILY_SALARY * 0.9:
        bid = min(bid, DAILY_SALARY * 0.38)

    reserve = 0
    if hp <= 4:
        reserve = DAILY_SALARY * 0.15
    elif hp <= 6:
        reserve = DAILY_SALARY * 0.08

    final_bid = min(budget - reserve, bid)
    if severe_need:
        final_bid = min(budget, max(final_bid, DAILY_SALARY * 0.88))

    if final_bid < 0:
        final_bid = 0
    if final_bid > budget:
        final_bid = budget
    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return min(budget, 18.0)

    slots = supply / float(WATER_REQ)
    pressure = len(alive) + 1 - slots

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

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
        danger += 2

    if pressure >= 2.0:
        danger += 2
    elif pressure >= 1.0:
        danger += 1

    if rich_opp >= 2:
        danger += 1
    if urgent_opp >= 1:
        danger += 1

    if highest_prev >= 140:
        market = 'very_high'
    elif highest_prev >= 110:
        market = 'high'
    elif highest_prev >= 70:
        market = 'mid'
    else:
        market = 'low'

    if danger >= 6:
        if market == 'very_high':
            bid = highest_prev + 2.5
        elif market == 'high':
            bid = max(108.0, highest_prev + 2.0)
        elif market == 'mid':
            bid = max(82.0, highest_prev + 3.0)
        else:
            bid = 76.0
    elif danger >= 4:
        if market == 'very_high':
            bid = max(92.0, highest_prev * 0.78)
        elif market == 'high':
            bid = max(74.0, avg_prev + 4.0)
        elif market == 'mid':
            bid = max(58.0, highest_prev + 2.0)
        else:
            bid = 49.0
    elif danger >= 2:
        if slots >= 2.0:
            bid = 26.0
        elif market == 'very_high':
            bid = 34.0
        elif market == 'high':
            bid = 42.0
        elif market == 'mid':
            bid = 37.0
        else:
            bid = 28.0
    else:
        if slots >= 2.0:
            bid = 12.0
        else:
            bid = 19.0

    if budget < bid:
        if hp <= 2 or no_water >= 2:
            bid = budget
        else:
            bid = min(budget, max(0.0, budget * 0.55))

    if hp >= 8 and no_water == 0 and slots >= 1.8 and highest_prev >= 120:
        bid = min(bid, 18.0)

    if budget <= 25 and (hp > 3 and no_water == 0):
        bid = min(bid, 10.0)

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
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
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= DAILY_SALARY * 0.9:
                    aggressive_bids.append(float(bid))

    if not alive_opponents:
        safe = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            safe = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, safe)))

    slots = max(1, int(supply // WATER_REQ))
    live_count = len(alive_opponents) + 1
    scarcity = live_count - slots
    tight = scarcity >= 2
    medium_tight = scarcity == 1

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
        urgency += 2

    if tight:
        urgency += 2
    elif medium_tight:
        urgency += 1

    if day >= 8:
        urgency += 1

    if urgency >= 6:
        bid = max(DAILY_SALARY * 0.92, highest_prev + 2.5)
    elif urgency >= 4:
        bid = max(DAILY_SALARY * 0.72, highest_prev + 1.5)
    elif urgency >= 2:
        if highest_prev >= DAILY_SALARY * 1.3:
            bid = DAILY_SALARY * 0.52
        else:
            bid = max(DAILY_SALARY * 0.48, avg_prev + 1.0)
    else:
        if tight and highest_prev < DAILY_SALARY * 0.95:
            bid = max(DAILY_SALARY * 0.42, highest_prev + 0.5)
        else:
            bid = DAILY_SALARY * 0.28

    if len(aggressive_bids) >= 2 and urgency <= 2:
        bid = min(bid, DAILY_SALARY * 0.35)

    if supply >= 24 and urgency <= 2:
        bid = min(bid, DAILY_SALARY * 0.22)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = DAILY_SALARY * (10 - day) * 0.18
    if budget < reserve_floor and urgency <= 3:
        bid = min(bid, DAILY_SALARY * 0.3)

    bid = max(0.0, min(float(budget), float(bid)))
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
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(max(0.0, min(budget, base)))

    threat_bid = 0.0
    cindy_bid = None
    cindy_budget = 0.0
    cindy_hp = 10
    cindy_nowater = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace') or {}
        pbid = prev.get('bid')
        if pbid is None:
            pbid = 0.0
        if pbid > threat_bid:
            threat_bid = pbid
        if oid == 'Cindy':
            cindy_bid = pbid
            cindy_budget = opp.get('budget', 0.0)
            cindy_hp = opp.get('hp', 10)
            cindy_nowater = opp.get('no_water_days', 0)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgency = 0.0
    if hp <= 2:
        my_urgency += 0.55
    elif hp <= 4:
        my_urgency += 0.3
    if no_water_days >= 2:
        my_urgency += 0.35
    elif no_water_days >= 1:
        my_urgency += 0.18
    if day >= 8:
        my_urgency += 0.1

    if cindy_bid is None:
        target = max(DAILY_SALARY * 0.45, threat_bid + 1.0)
    else:
        cindy_urgency = 0.0
        if cindy_hp <= 2:
            cindy_urgency += 0.3
        elif cindy_hp <= 4:
            cindy_urgency += 0.15
        if cindy_nowater >= 1:
            cindy_urgency += 0.15
        if cindy_budget > budget * 1.5:
            cindy_urgency += 0.08

        if scarcity >= 0.7 or my_urgency >= 0.45:
            target = cindy_bid + 3.0 + 8.0 * scarcity + 6.0 * cindy_urgency
        elif scarcity >= 0.4:
            target = cindy_bid * 0.82 + 4.0 * scarcity
        else:
            target = max(DAILY_SALARY * 0.28, cindy_bid * 0.55)

    if hp >= 6 and no_water_days == 0 and scarcity < 0.35:
        target *= 0.82

    if budget < DAILY_SALARY * 0.8:
        target = min(target, budget)

    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.9)

    target = max(0.0, min(budget, target))
    return float(target)
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
    prev_bids = []
    dangerous_prev = 0.0
    rich_alive = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= budget * 0.8:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0.0)
                prev_bids.append(bid)
                if bid > dangerous_prev:
                    dangerous_prev = bid

    if not alive:
        return float(min(budget, 18.0))

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    urgent = hp <= 4 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if not prev_bids:
        if critical:
            return float(min(budget, 95.0))
        if tight_supply:
            return float(min(budget, 72.0))
        return float(min(budget, 42.0))

    target = dangerous_prev + 2.0

    if critical:
        bid = max(target, 108.0)
    elif urgent:
        bid = max(target, 92.0 if tight_supply else 82.0)
    else:
        if tight_supply:
            bid = max(target, 86.0)
        elif medium_supply:
            bid = max(58.0, dangerous_prev * 0.78)
        else:
            bid = max(35.0, dangerous_prev * 0.58)

    if hp >= 8 and no_water_days == 0 and not tight_supply and dangerous_prev >= 100:
        bid = min(bid, 61.0)

    if rich_alive >= 2 and (tight_supply or urgent):
        bid = max(bid, dangerous_prev + 3.0)

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid = min(bid, max(28.0, dangerous_prev * 0.62))

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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    prev_high = 0.0
    prev_mid = 0.0
    cindy_bid = None
    david_bid = None

    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if bid > prev_high:
                    prev_mid = prev_high
                    prev_high = float(bid)
                elif bid > prev_mid:
                    prev_mid = float(bid)
                if agent_id == 'Cindy':
                    cindy_bid = float(bid)
                if agent_id == 'David':
                    david_bid = float(bid)

    if not alive:
        return float(min(budget, 5.0))

    scarcity = float(WATER_REQ) / max(1.0, float(supply))
    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 2:
        danger += 2
    elif no_water_days >= 1:
        danger += 1
    if supply <= 16:
        danger += 1

    if cindy_bid is None:
        cindy_bid = 160.0
    if david_bid is None:
        david_bid = 95.0

    if danger >= 4:
        target = max(david_bid + 4.0, 138.0)
        if budget > cindy_bid + 2.0 and hp <= 2:
            target = cindy_bid + 2.0
    elif danger >= 2:
        target = max(david_bid + 3.0, prev_mid + 2.0, 96.0)
        if supply <= 16:
            target = max(target, 112.0)
    else:
        if prev_high >= 150.0:
            target = 22.0 if supply >= 20 else 35.0
        elif prev_high >= 120.0:
            target = 48.0 if supply >= 20 else 62.0
        else:
            target = max(28.0, prev_high * 0.55)

    reserve_days = 3 if hp > 4 else 2
    reserve = reserve_days * DAILY_SALARY
    affordable = budget - reserve
    if affordable < 0:
        affordable = budget * 0.6

    if danger == 0 and scarcity < 0.7:
        target *= 0.85
    elif scarcity > 0.8:
        target *= 1.08

    bid = min(float(budget), float(max(0.0, affordable)), float(target))

    if danger >= 3 and bid < min(float(budget), 90.0):
        bid = min(float(budget), max(float(bid), 90.0))

    if hp <= 2:
        bid = min(float(budget), max(float(bid), 120.0))

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
            alive.append((oid, opp))

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 45.0))
        return float(min(budget, 12.0))

    prev_bids = []
    rich_pressure = 0
    weak_count = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 120:
                rich_pressure += 1
            if bid <= 5:
                weak_count += 1
        if opp.get('budget', 0) < 40 or opp.get('hp', 10) <= 2:
            weak_count += 1

    max_prev = max(prev_bids) if prev_bids else 0.0
    min_prev = min(prev_bids) if prev_bids else 0.0

    units = int(supply / WATER_REQ)
    if units < 0:
        units = 0

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

    if units >= 2:
        if danger >= 4:
            bid = 95.0
        elif danger >= 2:
            bid = 72.0
        else:
            bid = 48.0
        if rich_pressure >= 2:
            bid = min(bid, 58.0)
    else:
        if danger >= 5:
            bid = 118.0
        elif danger >= 3:
            bid = 84.0
        elif danger >= 1:
            bid = 28.0
        else:
            bid = 8.0
        if rich_pressure >= 2 and danger <= 2:
            bid = 5.0

    if weak_count >= 2 and units >= 2:
        bid = max(bid, 52.0)
    if weak_count >= 2 and units <= 1 and danger >= 3:
        bid = max(bid, 88.0)

    if day >= 8:
        if danger >= 2:
            bid += 8.0
        else:
            bid -= 4.0

    if max_prev > 0 and max_prev < 80 and danger >= 2:
        bid = max(bid, max_prev + 3.0)
    if min_prev >= 130 and danger <= 2 and units <= 1:
        bid = min(bid, 6.0)

    if budget < bid:
        bid = budget

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
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return float(min(budget, 18.0))

    highest_prev_bid = 0.0
    cindy_prev_bid = 0.0
    pressure = 0
    rich_alive = 0

    for agent_id, opp in alive:
        if opp.get('budget', 0) >= 200:
            rich_alive += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            if bid > highest_prev_bid:
                highest_prev_bid = bid
            if bid >= 75:
                pressure += 2
            elif bid >= 45:
                pressure += 1
        if agent_id == 'Cindy' and bid is not None:
            cindy_prev_bid = bid

    urgent = hp <= 3 or no_water >= 2
    semi_urgent = hp <= 5 or no_water >= 1

    if urgent:
        target = max(88.0, cindy_prev_bid + 2.5, highest_prev_bid + 1.5)
        if budget < target:
            target = budget
        return float(max(0.0, min(budget, target)))

    if semi_urgent:
        if cindy_prev_bid >= 85:
            target = 89.0
        elif cindy_prev_bid >= 70:
            target = cindy_prev_bid + 2.0
        else:
            target = max(52.0, highest_prev_bid + 1.0)
        return float(max(0.0, min(budget, target)))

    if rich_alive <= 1 and cindy_prev_bid >= 80:
        return float(max(0.0, min(budget, 12.0)))

    if pressure == 0:
        base = 24.0 if day <= 3 else 18.0
        return float(max(0.0, min(budget, base)))

    if cindy_prev_bid >= 90:
        return float(max(0.0, min(budget, 10.0)))

    if cindy_prev_bid >= 75:
        target = 46.0 if day < 8 else 58.0
        return float(max(0.0, min(budget, target)))

    target = max(28.0, min(60.0, highest_prev_bid + 1.5))
    return float(max(0.0, min(budget, target)))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    dangerous_prev = []
    weak_opps = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                weak_opps += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80:
                    dangerous_prev.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 18.0))

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
        urgency += 0.6
    elif no_water_days >= 1:
        urgency += 0.3

    urgency += 0.35 * scarcity

    endgame = day >= 8
    base = 18.0 + 20.0 * scarcity

    if avg_prev > 0:
        base = max(base, avg_prev * (0.52 + 0.18 * scarcity))

    target = base

    if hp <= 2 or no_water_days >= 2:
        target = max(target, highest_prev + 2.5, 92.0)
    elif scarcity >= 0.75 and dangerous_prev:
        target = max(target, highest_prev + 1.5)
    elif scarcity >= 0.45 and hp <= 5:
        target = max(target, avg_prev + 4.0)
    elif supply >= 22 and hp >= 7 and no_water_days == 0:
        target = min(target, 28.0)
    elif supply >= 20 and hp >= 6 and no_water_days == 0:
        target = min(target, 36.0)

    if weak_opps >= 2 and hp >= 6 and no_water_days == 0:
        target *= 0.88

    if endgame and hp <= 5:
        target = max(target, highest_prev + 2.0, 85.0)

    reserve_floor = 0.0
    days_left = max(0, 10 - day)
    if days_left >= 2 and hp >= 5:
        reserve_floor = 25.0
    if budget < reserve_floor:
        reserve_floor = 0.0

    target = min(target, budget - reserve_floor if budget > reserve_floor else budget)

    if target < 0:
        target = 0.0

    if budget <= 35:
        if hp <= 3 or no_water_days >= 1:
            target = min(budget, max(target, 30.0))
        else:
            target = min(budget, target)

    return float(max(0.0, min(budget, round(target, 2))))
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
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    prev_bids = []
    dangerous_prev = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 80.0:
                dangerous_prev.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = 0.0
    for b in prev_bids:
        if b < 140.0 and b > moderate_prev:
            moderate_prev = b
    if moderate_prev == 0.0:
        moderate_prev = highest_prev

    alive_count = len(alive)
    expected_demand = WATER_REQ * (alive_count + 1)
    tight_supply = supply <= expected_demand
    very_tight = supply <= expected_demand - 4

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

    if day >= 8:
        urgency += 1

    if urgency <= 1:
        if highest_prev >= 150.0:
            bid = 12.0
        elif highest_prev >= 90.0:
            bid = 22.0
        else:
            bid = max(20.0, moderate_prev + 2.0)
    elif urgency == 2:
        if highest_prev >= 150.0:
            bid = 38.0
        else:
            bid = max(35.0, moderate_prev + 3.0)
    elif urgency == 3:
        if highest_prev >= 150.0:
            bid = 62.0
        else:
            bid = max(58.0, moderate_prev + 5.0)
    elif urgency == 4:
        if highest_prev >= 150.0:
            bid = 88.0
        else:
            bid = max(82.0, moderate_prev + 7.0)
    else:
        if highest_prev >= 150.0:
            bid = 118.0
        else:
            bid = max(105.0, moderate_prev + 10.0)

    if no_water_days >= 2 or hp <= 2:
        bid = max(bid, 120.0)
    elif no_water_days >= 1 and hp <= 4:
        bid = max(bid, 90.0)

    if supply >= 23 and urgency <= 2:
        bid *= 0.8
    elif supply <= 16:
        bid *= 1.12

    reserve_floor = 0.0
    if hp >= 7 and no_water_days == 0:
        reserve_floor = 10.0
    elif hp >= 5:
        reserve_floor = 5.0

    max_affordable = max(0.0, budget - reserve_floor)
    final_bid = min(bid, max_affordable)
    if final_bid < 0:
        final_bid = 0.0
    return float(final_bid)
"""
