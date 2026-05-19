# ============================================================
# Experiment: exp_052
# Agent: Alex
# Source: exp_052
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

    alive = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0

    if not alive:
        if hp <= 2 or no_water >= 1:
            return min(budget, 50)
        return min(budget, 24)

    prev_bids = []
    urgent_opp = 0
    total_req = WATER_REQ
    for opp in alive:
        total_req += opp.get('water_requirement', WATER_REQ)
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)

    scarcity = total_req / max(1.0, supply)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0

    critical = (hp <= 2) or (no_water >= 1)
    fragile = (hp <= 4)

    if critical:
        target = max(58, highest_prev + 3)
        if scarcity > 2.5:
            target = max(target, 64)
        return min(budget, target)

    if scarcity <= 1.2:
        base = 18
        if highest_prev > 0:
            base = max(base, min(32, avg_prev * 0.55))
        return min(budget, base)

    if scarcity <= 1.8:
        base = 28
        if highest_prev >= 55:
            base = 24 if hp > 4 else 48
        elif highest_prev >= 40:
            base = max(base, highest_prev * 0.78)
        elif highest_prev > 0:
            base = max(base, highest_prev + 2)
        if urgent_opp >= 2 and hp > 4:
            base -= 4
        return min(budget, max(0, base))

    base = 42
    if highest_prev >= 60:
        base = 34 if hp > 5 else 60
    elif highest_prev >= 45:
        base = highest_prev + 2
    elif highest_prev > 0:
        base = max(base, avg_prev + 6)

    if urgent_opp >= 2 and hp > 5:
        base -= 5
    if fragile:
        base += 8

    reserve_floor = DAILY_SALARY * 0.2
    if budget < reserve_floor:
        base = min(base, budget)

    return min(budget, max(0, base))
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

    alive_opponents = []
    prev_bids = []
    rich_pressure = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 75:
                    rich_pressure += 1

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0

    emergency = hp <= 2 or no_water >= 2
    danger = hp <= 4 or no_water >= 1
    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if emergency:
        bid = max(72.0, highest_prev * 0.92)
        return min(budget, bid)

    if danger and tight_supply:
        bid = max(52.0, min(78.0, highest_prev * 0.72 + 3.0))
        return min(budget, bid)

    if rich_pressure >= 2:
        if ample_supply and hp >= 6 and no_water == 0:
            return min(budget, 8.0)
        if hp >= 5 and no_water == 0:
            return min(budget, 12.0)
        return min(budget, 28.0)

    if highest_prev >= 90:
        if hp >= 6 and no_water == 0:
            return min(budget, 10.0)
        return min(budget, 30.0)

    if highest_prev >= 60:
        if hp >= 6 and ample_supply:
            return min(budget, 14.0)
        return min(budget, 26.0)

    if highest_prev > 0:
        target = max(20.0, lowest_prev + 2.0)
        if tight_supply:
            target += 6.0
        if danger:
            target += 10.0
        return min(budget, target)

    base = 18.0
    if tight_supply:
        base += 6.0
    if danger:
        base += 12.0
    return min(budget, base)
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_bids = []
    moderate_bids = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 120:
                    strong_bids.append(bid)
                elif bid >= 70:
                    moderate_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 40.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    moderate_prev = max(moderate_bids) if moderate_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22

    desperation = 0
    if hp <= 2:
        desperation = 3
    elif hp <= 4 or no_water_days >= 1:
        desperation = 2
    elif hp <= 6:
        desperation = 1

    if desperation >= 3:
        bid = max(95.0, moderate_prev + 6.0)
        if supply_tight:
            bid += 8.0
        return float(min(budget, bid))

    if desperation == 2:
        if moderate_prev > 0:
            bid = moderate_prev + 4.0
        else:
            bid = 72.0
        if supply_tight:
            bid += 6.0
        if highest_prev >= 120 and hp > 3:
            bid = min(bid, 88.0)
        return float(min(budget, bid))

    if supply_loose and hp >= 7:
        return float(min(budget, 24.0))

    if supply_tight:
        if moderate_prev > 0:
            bid = moderate_prev + 3.0
        else:
            bid = 68.0
        if highest_prev >= 120:
            bid = min(bid, 82.0)
        return float(min(budget, bid))

    if moderate_prev > 0:
        bid = moderate_prev + 1.5
        if highest_prev >= 120:
            bid = min(bid, 78.0)
        bid = max(52.0, bid)
        return float(min(budget, bid))

    base = 48.0
    if day >= 8:
        base = 58.0
    return float(min(budget, base))
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

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        safe_bid = min(budget, DAILY_SALARY * 0.35)
        if hp <= 2 or no_water >= 1:
            safe_bid = min(budget, DAILY_SALARY * 0.75)
        return float(max(0.0, safe_bid))

    prev_bids = []
    urgent_count = 0
    rich_count = 0
    high_prev = 0.0
    moderate_prev = 0.0

    for opp in alive:
        if opp.get('budget', 0) >= 700:
            rich_count += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        prev = opp.get('previous_trace', {})
        bid = None
        if isinstance(prev, dict):
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) > high_prev:
                high_prev = float(bid)
            if float(bid) >= DAILY_SALARY * 0.9:
                moderate_prev += 1

    slots = int(supply / WATER_REQ)
    if slots < 1:
        slots = 1

    pressure = len(alive) - slots

    if prev_bids:
        sorted_bids = sorted(prev_bids)
        median_prev = sorted_bids[int(len(sorted_bids) // 2)]
        low_prev = sorted_bids[0]
    else:
        median_prev = DAILY_SALARY * 0.7
        low_prev = DAILY_SALARY * 0.55
        high_prev = DAILY_SALARY * 0.9

    if hp <= 2 or no_water >= 2:
        target = max(DAILY_SALARY * 1.05, high_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        if pressure >= 3:
            target = max(DAILY_SALARY * 0.95, high_prev + 1.0)
        else:
            target = max(DAILY_SALARY * 0.82, median_prev + 1.0)
    else:
        if slots >= len(alive):
            target = DAILY_SALARY * 0.28
        elif pressure <= 1:
            target = max(DAILY_SALARY * 0.42, low_prev - 2.0)
        elif pressure == 2:
            target = max(DAILY_SALARY * 0.55, median_prev - 4.0)
        else:
            if high_prev >= 100 or rich_count >= 2:
                target = DAILY_SALARY * 0.38
            else:
                target = DAILY_SALARY * 0.52

    if day >= 8 and hp >= 6 and no_water == 0:
        target *= 0.9

    if urgent_count >= 2 and hp >= 5 and no_water == 0:
        target *= 0.88

    if supply <= 16:
        target += 6.0
    elif supply >= 24:
        target -= 5.0

    cap = budget
    if hp >= 5 and no_water == 0:
        cap = min(cap, DAILY_SALARY * 1.15)
    else:
        cap = min(cap, DAILY_SALARY * 1.6)

    bid = min(cap, max(0.0, target))
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
            alive.append(opp)

    if not alive:
        return float(min(budget, 20.0))

    likely_units = int(max(1, supply // WATER_REQ))
    scarcity = likely_units <= 1

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        if opp.get('budget', 0) >= 140:
            rich_opp += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

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

    if scarcity:
        danger += 1
    if urgent_opp >= 2:
        danger += 1

    if danger >= 6:
        base = max(95.0, highest_prev + 8.0)
    elif danger >= 4:
        base = max(72.0, highest_prev + 3.0, avg_prev + 6.0)
    elif danger >= 2:
        base = max(42.0, avg_prev * 0.7)
    else:
        base = 18.0 if scarcity else 12.0

    if highest_prev >= 150.0 and danger <= 2:
        base = min(base, 28.0)
    elif highest_prev >= 100.0 and danger <= 1:
        base = min(base, 22.0)

    if rich_opp >= 2 and danger >= 4:
        base += 8.0

    if budget < 60:
        base = min(base, budget)
    elif budget < 120:
        base = min(base, 0.75 * budget)
    else:
        base = min(base, 0.55 * budget)

    if day >= 8 and (hp <= 5 or no_water >= 1):
        base = max(base, min(budget, highest_prev + 5.0, 110.0))

    if day == 1 and hp >= 8:
        base = min(base, 26.0 if scarcity else 18.0)

    bid = max(0.0, min(float(budget), float(base)))
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    desperate_bids = []
    rich_alive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > DAILY_SALARY * 2:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev.get('bid', 0)
                prev_bids.append(bid)
                if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                    desperate_bids.append(bid)

    if not alive_opponents:
        base = DAILY_SALARY * 0.28
        if hp <= 3 or no_water_days >= 1:
            base = DAILY_SALARY * 0.75
        return float(min(budget, max(0.0, base)))

    units = supply / float(WATER_REQ)
    scarcity = 0
    if units <= 1.05:
        scarcity = 2
    elif units <= 1.45:
        scarcity = 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    desperate_prev = max(desperate_bids) if desperate_bids else highest_prev

    urgent = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if urgent:
        target = max(DAILY_SALARY * 0.92, desperate_prev + 2.0)
        if scarcity == 2:
            target = max(target, DAILY_SALARY * 1.02)
        return float(min(budget, target))

    if scarcity == 2:
        if pressured:
            target = max(DAILY_SALARY * 0.86, highest_prev + 1.5)
        else:
            if highest_prev >= DAILY_SALARY * 1.4:
                target = DAILY_SALARY * 0.34
            else:
                target = max(DAILY_SALARY * 0.58, highest_prev + 1.0)
    elif scarcity == 1:
        if pressured:
            target = max(DAILY_SALARY * 0.72, highest_prev + 1.0)
        else:
            if highest_prev >= DAILY_SALARY * 1.2:
                target = DAILY_SALARY * 0.30
            else:
                target = max(DAILY_SALARY * 0.46, highest_prev * 0.88)
    else:
        if pressured:
            target = max(DAILY_SALARY * 0.56, highest_prev * 0.82)
        else:
            target = DAILY_SALARY * 0.24
            if rich_alive >= 1 and highest_prev < DAILY_SALARY * 0.5:
                target = DAILY_SALARY * 0.29

    if budget < DAILY_SALARY * 1.2 and not pressured:
        target = min(target, DAILY_SALARY * 0.35)

    target = max(0.0, target)
    return float(min(budget, target))
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
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        base = 18.0 if hp > 3 else 42.0
        return float(max(0.0, min(budget, base)))

    slots = max(1, int(supply // WATER_REQ))
    total_players = 1 + len(alive)
    scarcity = total_players - slots

    prev_bids = []
    urgent_prev_bids = []
    rich_pressure = 0.0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            prev_bids.append(float(pbid))
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_prev_bids.append(float(pbid))
        if opp.get('budget', 0) > budget:
            rich_pressure += 1.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_high = max(urgent_prev_bids) if urgent_prev_bids else highest_prev

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

    if scarcity >= 3:
        base = 72.0
    elif scarcity == 2:
        base = 58.0
    elif scarcity == 1:
        base = 44.0
    else:
        base = 26.0

    if supply >= 24:
        base -= 8.0
    elif supply <= 16:
        base += 8.0

    if danger >= 5:
        bid = max(base + 25.0, urgent_high + 3.0, highest_prev * 0.92)
    elif danger >= 3:
        bid = max(base + 12.0, urgent_high + 2.0, highest_prev * 0.72)
    elif danger >= 1:
        bid = max(base + 4.0, highest_prev * 0.58)
    else:
        if scarcity <= 0:
            bid = max(16.0, highest_prev * 0.35)
        else:
            bid = max(base, urgent_high + 1.5, highest_prev * 0.5)

    if rich_pressure >= 2 and danger <= 1:
        bid -= 6.0

    if day >= 8 and hp <= 5:
        bid += 8.0

    reserve_floor = 10.0 if day < 8 else 0.0
    affordable = max(0.0, budget - reserve_floor)
    bid = min(bid, affordable)

    if danger >= 5 and budget > 0:
        bid = max(bid, min(budget, 62.0))

    bid = max(0.0, min(budget, bid))
    return float(round(bid, 2))
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

    alive_opponents = []
    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 300:
                rich_opp_count += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    my_urgent = hp <= 4 or no_water_days >= 1
    my_critical = hp <= 2 or no_water_days >= 2

    if my_critical:
        target = max(0.92 * DAILY_SALARY, highest_prev + 3.0, 64.0)
    elif my_urgent:
        target = max(0.72 * DAILY_SALARY, 0.45 * highest_prev + 18.0, 46.0 + 10.0 * scarcity)
    else:
        if supply >= 22:
            target = 12.0 + 6.0 * scarcity
        elif supply >= 19:
            target = 16.0 + 10.0 * scarcity
        else:
            target = 22.0 + 14.0 * scarcity

        if highest_prev > 150:
            target = min(target, 24.0 if hp > 5 else 40.0)
        elif highest_prev > 100:
            target = min(target + 3.0, 32.0 if hp > 5 else 45.0)
        else:
            target = max(target, min(highest_prev + 1.5, 38.0))

    if urgent_opp_count >= 2 and not my_urgent:
        target *= 0.88
    if rich_opp_count >= 2 and supply <= 17:
        target += 6.0
    if day >= 8 and hp >= 6 and not my_urgent:
        target *= 0.9

    if budget < DAILY_SALARY:
        target = min(target, 0.55 * budget)
    else:
        target = min(target, 0.85 * budget)

    target = max(0.0, min(target, budget))
    return float(round(target, 2))
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
    desperate_count = 0
    rich_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 140:
                rich_count += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, 28.0))
        return float(min(budget, 8.0))

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    total_players = 1 + len(alive)
    expected_winners = max(1, int(supply // WATER_REQ))
    scarcity = total_players - expected_winners

    must_win = False
    if hp <= 2:
        must_win = True
    if no_water_days >= 1 and hp <= 4:
        must_win = True
    if no_water_days >= 2:
        must_win = True

    if must_win:
        bid = max(63.0, max_prev + 2.5)
        if rich_count >= 2:
            bid = max(bid, 92.0)
        if scarcity >= 2:
            bid = max(bid, 105.0)
        return float(min(budget, bid))

    if expected_winners >= total_players - 1:
        if no_water_days == 0 and hp >= 5:
            return float(min(budget, 12.0))
        return float(min(budget, 24.0))

    if scarcity >= 3:
        if hp >= 6 and no_water_days == 0:
            return float(min(budget, 18.0))
        bid = max(48.0, avg_prev * 0.55)
        return float(min(budget, bid))

    if max_prev >= 160:
        if hp >= 5 and no_water_days == 0:
            return float(min(budget, 20.0))
        return float(min(budget, 72.0))

    if max_prev >= 110:
        if hp >= 6 and no_water_days == 0 and supply >= 20:
            return float(min(budget, 22.0))
        bid = max(58.0, min(86.0, max_prev * 0.62))
        return float(min(budget, bid))

    if desperate_count >= 2:
        bid = max(52.0, max_prev + 1.5)
        return float(min(budget, bid))

    base = 36.0
    if supply <= 16:
        base += 10.0
    if hp <= 4:
        base += 8.0
    if no_water_days >= 1:
        base += 12.0
    bid = max(base, avg_prev * 0.7)
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if budget <= 0:
        return 0.0

    slots = int(supply / WATER_REQ)
    if slots < 1:
        slots = 1

    prev_bids = []
    bob_bid = None
    cindy_bid = None
    urgent_opp = 0
    for agent_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if agent_id == 'Bob':
                bob_bid = float(bid)
            if agent_id == 'Cindy':
                cindy_bid = float(bid)
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 2:
            urgent_opp += 1

    if not alive:
        return float(min(budget, 20.0))

    pressure = max(prev_bids) if prev_bids else 0.0
    bob_ref = 62.5 if bob_bid is None else bob_bid
    cindy_ref = 147.7 if cindy_bid is None else cindy_bid

    if hp <= 2 or no_water_days >= 2:
        bid = max(78.0, bob_ref + 8.0)
        return float(min(budget, bid))

    if hp <= 4 or no_water_days >= 1:
        if slots >= 2:
            bid = max(66.0, bob_ref + 3.0)
        else:
            bid = max(74.0, bob_ref + 6.0)
        if urgent_opp > 0:
            bid += 4.0
        return float(min(budget, bid))

    if slots >= 2:
        if pressure >= 120:
            bid = 46.0
        elif pressure >= 80:
            bid = 52.0
        else:
            bid = 56.0
    else:
        if cindy_ref >= 120:
            bid = 44.0
        else:
            bid = 58.0
        if bob_ref >= 70:
            bid += 4.0

    if budget < 140:
        bid = min(bid, 48.0)
    elif budget > 400 and hp >= 7 and no_water_days == 0 and slots >= 2:
        bid = max(bid, 58.0)

    return float(min(budget, max(0.0, bid)))
"""
