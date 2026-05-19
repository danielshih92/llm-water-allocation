# ============================================================
# Experiment: exp_036
# Agent: Alex
# Source: exp_036
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.75
        return max(0, min(budget, base))

    prev_bids = []
    desperate_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY * 4:
            rich_count += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0))

    highest_prev = max(prev_bids) if prev_bids else 0

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

    if urgency >= 5:
        bid = DAILY_SALARY * 0.96
    elif urgency >= 3:
        bid = DAILY_SALARY * 0.82
    elif scarcity == 2:
        bid = DAILY_SALARY * 0.62
    elif scarcity == 1:
        bid = DAILY_SALARY * 0.50
    else:
        bid = DAILY_SALARY * 0.34

    if highest_prev > 0:
        if scarcity >= 1 or urgency >= 2:
            target = highest_prev + 1.5
            if target > bid:
                bid = target
        elif highest_prev >= DAILY_SALARY * 0.85:
            bid = min(bid, DAILY_SALARY * 0.38)

    if desperate_count >= 2 and scarcity >= 1:
        bid = max(bid, DAILY_SALARY * 0.72)
    if rich_count >= 2 and scarcity == 2:
        bid = max(bid, DAILY_SALARY * 0.78)

    if day >= 8 and (hp <= 4 or no_water >= 1):
        bid = max(bid, DAILY_SALARY * 0.88)

    bid = max(0, min(budget, bid))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_pressure = 0.0
    rich_alive = 0

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > 300:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                req = float(opp.get('water_requirement', WATER_REQ))
                if req >= WATER_REQ:
                    dangerous_pressure = max(dangerous_pressure, float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 35.0))

    low_supply = supply <= 17
    high_supply = supply >= 22
    critical_hp = hp <= 2 or no_water_days >= 2
    shaky_hp = hp <= 4 or no_water_days >= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    base = 0.0

    if critical_hp:
        if low_supply:
            base = max(63.0, dangerous_pressure + 2.0, highest_prev + 1.0)
        else:
            base = max(54.0, avg_prev + 2.0)
    elif shaky_hp:
        if low_supply:
            base = max(42.0, avg_prev + 1.5)
        elif high_supply:
            base = 22.0
        else:
            base = max(30.0, min(48.0, avg_prev))
    else:
        if low_supply:
            if highest_prev >= 90.0:
                base = 16.0
            else:
                base = max(24.0, min(46.0, avg_prev + 1.0))
        elif high_supply:
            base = 12.0 if rich_alive >= 1 else 16.0
        else:
            if highest_prev >= 95.0:
                base = 14.0
            else:
                base = max(18.0, min(36.0, avg_prev * 0.6 + 4.0))

    if day >= 8:
        if hp <= 4:
            base += 10.0
        else:
            base += 4.0

    if budget < 120:
        base = min(base, 0.55 * budget)
    elif budget < 250:
        base = min(base, 0.7 * budget)

    if critical_hp and budget > 0:
        base = max(base, min(budget, 58.0))

    bid = max(0.0, min(float(budget), float(base)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 500:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(float(prev['bid']))

    if not alive_opponents:
        return max(0.0, min(budget, 15.0))

    slots = max(1, int(supply // WATER_REQ))
    pressure = len(alive_opponents) + 1 - slots
    tight_supply = supply <= 18

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(95.0, highest_prev + 2.0)
    elif hp <= 4 or no_water_days >= 1:
        if tight_supply:
            bid = max(82.0, avg_prev * 0.9)
        else:
            bid = max(68.0, avg_prev * 0.72)
    else:
        if pressure >= 3 or tight_supply:
            if highest_prev >= 120:
                bid = 24.0
            elif highest_prev >= 90:
                bid = 36.0
            else:
                bid = max(42.0, highest_prev * 0.5)
        else:
            if highest_prev >= 120:
                bid = 18.0
            elif highest_prev >= 90:
                bid = 28.0
            else:
                bid = max(26.0, avg_prev * 0.4 if avg_prev > 0 else 26.0)

    if rich_opp >= 2 and hp > 4 and no_water_days == 0:
        bid *= 0.9
    if urgent_opp >= 2 and (hp <= 4 or no_water_days >= 1):
        bid *= 1.12

    if day >= 8:
        if hp <= 5 or no_water_days >= 1:
            bid *= 1.18
        else:
            bid *= 0.95

    min_survival = 8.0 if hp > 4 and no_water_days == 0 else 20.0
    bid = max(min_survival, bid)
    bid = min(budget, bid)
    if budget < 25:
        bid = budget
    return max(0.0, float(bid))
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
    no_water = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_bids = []
    weak_bids = []

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 80:
                    strong_bids.append(float(bid))
                if bid <= 20:
                    weak_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0 if hp > 3 else 35.0))

    competitor_count = len(alive_opponents) + 1
    expected_units = float(supply) / float(WATER_REQ)
    scarcity = expected_units < competitor_count

    highest_prev = max(prev_bids) if prev_bids else 0.0
    stable_pressure = 0.0
    for b in prev_bids:
        if 40 <= b <= 140:
            if b > stable_pressure:
                stable_pressure = b
    if stable_pressure == 0.0:
        stable_pressure = highest_prev

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

    if urgency >= 5:
        bid = max(95.0, stable_pressure + 8.0)
    elif urgency >= 3:
        bid = max(72.0, stable_pressure + 4.0)
    else:
        if scarcity:
            bid = max(48.0, stable_pressure + 2.0)
        else:
            bid = 28.0

    if len(strong_bids) >= 1 and hp > 5 and no_water == 0:
        bid = min(bid, 42.0)

    if len(weak_bids) >= 2 and not scarcity and urgency <= 1:
        bid = min(bid, 24.0)

    if budget < DAILY_SALARY:
        bid = min(bid, max(18.0, budget * 0.75))

    bid = min(bid, budget)
    if bid < 0:
        bid = 0.0
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

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) > 700:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        safe_bid = min(budget, 18.0)
        if hp <= 3 or no_water_days >= 1:
            safe_bid = min(budget, 32.0)
        return max(0.0, float(safe_bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_pressure < 0:
        supply_pressure = 0.0
    if supply_pressure > 1:
        supply_pressure = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.55
    if no_water_days >= 2:
        urgency += 1.0
    elif no_water_days >= 1:
        urgency += 0.45

    market_pressure = min(1.0, highest_prev / 100.0)

    base = 18.0 + 20.0 * supply_pressure + 10.0 * market_pressure + 8.0 * min(1.0, desperate_count / 3.0)

    if urgency >= 1.5:
        bid = max(base + 18.0, highest_prev * 0.96 + 2.0, 62.0)
    elif urgency >= 0.7:
        bid = max(base + 8.0, avg_prev * 0.72 + 2.0, 38.0)
    else:
        bid = max(base, avg_prev * 0.45 + 1.0)

    if supply >= 23 and urgency < 0.7:
        bid *= 0.72
    elif supply >= 20 and urgency < 0.7:
        bid *= 0.84
    elif supply <= 17:
        bid *= 1.18

    if rich_count >= 2 and supply <= 18:
        bid += 6.0

    if day >= 8:
        bid *= 1.08
    if day >= 9 and (hp <= 4 or no_water_days >= 1):
        bid *= 1.12

    reserve = 0.0
    days_left = max(0, 10 - day)
    if hp > 4 and no_water_days == 0:
        reserve = min(budget * 0.45, days_left * 10.0)
    elif hp > 2:
        reserve = min(budget * 0.25, days_left * 6.0)

    cap = max(0.0, budget - reserve)
    if urgency >= 1.5:
        cap = budget
    elif urgency >= 0.7:
        cap = max(cap, budget * 0.7)

    bid = min(bid, cap)
    bid = min(bid, budget)
    bid = max(0.0, bid)

    if budget < 25 and urgency < 1.5:
        bid = min(bid, max(8.0, budget * 0.7))

    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive') and opp.get('budget', 0) > 0:
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 1:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    units = int(supply / WATER_REQ)
    if units < 1:
        units = 1

    prev_bids = []
    urgent_count = 0
    rich_count = 0
    for opp in alive_opponents:
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_count += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = len(alive_opponents) + 1 - units

    if hp <= 2 or no_water_days >= 2:
        target = max(DAILY_SALARY * 0.92, highest_prev + 2.5)
    elif no_water_days >= 1:
        target = max(DAILY_SALARY * 0.82, highest_prev + 1.5)
    else:
        if scarcity >= 2:
            target = max(DAILY_SALARY * 0.88, highest_prev + 1.2)
        elif scarcity == 1:
            target = max(DAILY_SALARY * 0.72, avg_prev + 1.0)
        else:
            target = DAILY_SALARY * 0.42

    if urgent_count >= units:
        target = max(target, highest_prev + 1.8, DAILY_SALARY * 0.9)
    elif rich_count == 0 and scarcity <= 1 and hp >= 4 and no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.38)

    if highest_prev >= DAILY_SALARY * 1.15 and hp >= 4 and no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.35)

    if budget < target:
        if hp <= 2 or no_water_days >= 1:
            return float(budget)
        return float(min(budget, DAILY_SALARY * 0.3))

    return float(min(budget, max(0.0, target)))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
    serious_prev_bids = []
    desperate_signals = 0
    rich_opponents = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 8:
                rich_opponents += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_signals += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                status = prev.get('status')
                if bid is not None and status != 'error' and bid > 0:
                    serious_prev_bids.append(bid)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.75))
        return float(min(budget, DAILY_SALARY * 0.2))

    highest_prev = max(serious_prev_bids) if serious_prev_bids else 0.0
    avg_prev = (sum(serious_prev_bids) / len(serious_prev_bids)) if serious_prev_bids else 0.0

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    abundant_supply = supply >= 23

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2
    if tight_supply:
        urgency += 2
    elif medium_supply:
        urgency += 1
    if desperate_signals >= 2:
        urgency += 1

    base = DAILY_SALARY * 0.42

    if urgency >= 7:
        target = max(DAILY_SALARY * 1.02, highest_prev + 3.0, avg_prev + 6.0)
    elif urgency >= 5:
        target = max(DAILY_SALARY * 0.9, highest_prev + 2.0, avg_prev + 4.0)
    elif urgency >= 3:
        target = max(base + 10.0, highest_prev * 0.92 + 1.5)
    else:
        if abundant_supply:
            target = DAILY_SALARY * 0.28
        elif medium_supply:
            target = DAILY_SALARY * 0.4
        else:
            target = DAILY_SALARY * 0.52

    if highest_prev >= DAILY_SALARY * 1.6 and urgency <= 3:
        target = min(target, DAILY_SALARY * 0.38)

    if rich_opponents >= 2 and tight_supply:
        target += 6.0

    days_left = max(1, 10 - day + 1)
    sustainable = budget / days_left

    if urgency <= 2:
        cap = max(DAILY_SALARY * 0.35, sustainable * 0.9)
    elif urgency <= 4:
        cap = max(DAILY_SALARY * 0.6, sustainable * 1.15)
    else:
        cap = max(DAILY_SALARY * 0.95, sustainable * 1.8)

    if hp <= 2 or no_water_days >= 2:
        cap = max(cap, DAILY_SALARY * 1.1)

    bid = min(target, cap, budget)

    if bid < 0:
        bid = 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    rich_high = 0
    weak_or_desperate = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 135:
                    rich_high += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                weak_or_desperate += 1

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

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

    if day >= 8:
        urgency += 1

    if urgency >= 5:
        bid = 146.0 if rich_high >= 1 else max(95.0, highest_prev + 2.0)
        return float(min(budget, bid))

    if supply >= 22:
        if rich_high >= 2 and urgency <= 1:
            bid = 16.0
        else:
            bid = max(28.0, min(72.0, avg_prev * 0.35 + 8.0))
        return float(min(budget, bid))

    if supply >= 19:
        if rich_high >= 2:
            if urgency >= 3:
                bid = 146.0
            elif urgency == 2:
                bid = 88.0
            else:
                bid = 22.0
        else:
            bid = max(35.0, min(90.0, highest_prev * 0.55 + 6.0))
        return float(min(budget, bid))

    if rich_high >= 2:
        if urgency >= 4:
            bid = 147.0
        elif urgency >= 2:
            bid = 96.0
        else:
            bid = 12.0
    else:
        if highest_prev >= 100:
            bid = 18.0 if urgency <= 1 else 102.0
        else:
            bid = max(40.0, min(110.0, highest_prev + 3.0))

    if budget < 120 and urgency <= 2:
        bid = min(bid, 55.0)

    return float(min(budget, max(0.0, bid)))
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    aggressive_count = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 100:
                    aggressive_count += 1

    if not alive_opponents:
        return max(0.0, min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    bob_like = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None and bid < 100:
            if bid > bob_like:
                bob_like = bid

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4 or no_water_days >= 1:
        urgency = 2
    elif hp <= 6:
        urgency = 1

    if urgency == 3:
        target = max(110.0, bob_like + 8.0)
        if aggressive_count > 0:
            target = max(target, highest_prev + 2.0)
    elif urgency == 2:
        if tight_supply:
            target = max(82.0, bob_like + 4.0)
        else:
            target = max(68.0, bob_like + 2.0)
        if aggressive_count > 0 and highest_prev < 130:
            target = max(target, highest_prev + 1.0)
    elif urgency == 1:
        if tight_supply:
            target = max(72.0, bob_like + 1.5)
        elif loose_supply:
            target = 34.0
        else:
            target = 48.0
    else:
        if tight_supply:
            target = 52.0
        elif loose_supply:
            target = 18.0
        else:
            target = 30.0

    if aggressive_count > 0 and urgency <= 1 and highest_prev >= 130:
        target = min(target, 40.0)

    remaining_days = 11 - day_context['day']
    if remaining_days < 1:
        remaining_days = 1
    soft_cap = budget / float(remaining_days)

    if urgency >= 2:
        bid = min(budget, max(target, soft_cap * 0.9))
    else:
        bid = min(budget, min(target, max(15.0, soft_cap * 0.75)))

    if budget < 25:
        bid = budget

    if bid < 0:
        bid = 0.0
    return float(bid)
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0

    alive = []
    prev_bids = []
    opp_pressures = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            bid = None
            if prev:
                bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                req = max(1, float(opp.get('water_requirement', WATER_REQ)))
                opp_pressures.append(float(bid) / req)

    if not alive:
        base = 18.0 if hp > 3 else 42.0
        return max(0, min(budget, base))

    total_players = 1 + len(alive)
    expected_share = supply / float(total_players)
    scarcity = expected_share < WATER_REQ

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_pressure = max(opp_pressures) if opp_pressures else 0.0

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
    if day >= 8:
        urgency += 1

    if supply >= 22:
        supply_band = 0
    elif supply >= 18:
        supply_band = 1
    else:
        supply_band = 2

    if scarcity:
        if urgency >= 5:
            bid = max(86.0, highest_prev + 2.5)
        elif urgency >= 3:
            bid = max(72.0, avg_prev + 3.0)
        else:
            bid = min(46.0, max(24.0, avg_prev * 0.55))
    else:
        if urgency >= 5:
            bid = max(74.0, avg_prev + 1.5)
        elif urgency >= 3:
            bid = max(52.0, avg_prev * 0.72)
        else:
            bid = max(18.0, avg_prev * 0.38)

    if highest_prev >= 120:
        if urgency <= 2 and supply_band <= 1:
            bid = min(bid, 34.0)
        elif urgency >= 5:
            bid = max(bid, 92.0)
    elif highest_prev >= 95:
        if urgency <= 2 and not scarcity:
            bid = min(bid, 30.0)
        else:
            bid = max(bid, 58.0)

    if max_pressure >= 8.0 and urgency <= 2 and supply >= 20:
        bid = min(bid, 28.0)

    reserve_floor = 0.0
    if day <= 7:
        reserve_floor = 35.0
    if urgency >= 5:
        reserve_floor = 0.0

    affordable = max(0.0, budget - reserve_floor)
    if affordable <= 0:
        affordable = budget * 0.5

    bid = min(bid, affordable)
    bid = min(bid, budget)

    if urgency >= 5:
        bid = min(budget, max(bid, 88.0 if scarcity else 70.0))
    elif urgency >= 3:
        bid = min(budget, max(bid, 48.0))

    if bid < 0:
        bid = 0.0

    return float(round(bid, 2))
"""
