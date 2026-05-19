# ============================================================
# Experiment: exp_084
# Agent: Alex
# Source: exp_084
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 63)
        return min(budget, 28)

    opp_count = len(alive_opponents)
    total_players = opp_count + 1
    pressure = float(total_players * WATER_REQ) / max(1.0, float(supply))

    prev_bids = []
    prev_aggressive = 0
    prev_desperate = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)
                if bid >= 56:
                    prev_aggressive += 1
            if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 2:
                prev_desperate += 1

    highest_prev = max(prev_bids) if prev_bids else 0

    emergency = hp <= 2 or no_water_days >= 2
    strained = hp <= 4 or no_water_days >= 1

    if emergency:
        target = max(60, highest_prev + 2)
        if pressure > 2.2:
            target = max(target, 66)
        return min(budget, target)

    if strained:
        target = 46
        if highest_prev > 0:
            target = max(target, highest_prev + 1.5)
        if pressure > 1.8:
            target += 6
        if prev_desperate >= 2:
            target += 4
        return min(budget, target)

    if pressure <= 1.1:
        target = 18
    elif pressure <= 1.4:
        target = 24
    elif pressure <= 1.8:
        target = 31
    else:
        target = 38

    if highest_prev >= 60:
        target = min(target, 26)
    elif highest_prev >= 45:
        target = max(target, highest_prev + 1)
    elif highest_prev > 0:
        target = max(target, highest_prev * 0.78)

    if prev_aggressive >= max(1, opp_count // 2):
        target -= 4

    if budget < DAILY_SALARY * 2:
        target = min(target, 24)

    if supply >= 22:
        target -= 3
    elif supply <= 17:
        target += 4

    if target < 0:
        target = 0
    return min(budget, target)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        base = DAILY_SALARY * 0.35
        if hp <= 3 or no_water >= 1:
            base = DAILY_SALARY * 0.6
        return float(max(0.0, min(budget, base)))

    prev_bids = []
    rich_aggressive = 0
    weak_opponents = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) >= 500:
            rich_aggressive += 1
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            weak_opponents += 1
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid', 0.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17
    supply_loose = supply >= 22
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
    if supply_tight:
        danger += 1

    if danger >= 5:
        target = max(DAILY_SALARY * 1.2, highest_prev + 2.0)
    elif danger >= 3:
        target = max(DAILY_SALARY * 0.92, avg_prev * 0.78 + 4.0)
    elif supply_tight and rich_aggressive >= 2:
        target = DAILY_SALARY * 0.48
    elif supply_loose and weak_opponents >= 1:
        target = DAILY_SALARY * 0.32
    else:
        target = DAILY_SALARY * 0.4

    if highest_prev >= 120:
        if danger <= 2:
            target = min(target, DAILY_SALARY * 0.42)
        else:
            target = max(target, DAILY_SALARY * 0.95)

    if day >= 8:
        if hp >= 6 and no_water == 0:
            target = min(target, DAILY_SALARY * 0.38)
        else:
            target = max(target, DAILY_SALARY * 0.8)

    if budget < DAILY_SALARY * 2:
        target = min(target, budget * 0.7 + 5.0)

    bid = max(0.0, min(budget, target))
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = {}
    for k, v in opponents_status.items():
        if v.get('alive'):
            alive[k] = v

    if not alive:
        return float(min(budget, 10.0))

    bob_prev_bid = None
    bob_budget = None
    eric_alive = False
    eric_prev_bid = None
    max_prev_bid = 0.0
    urgent_opp = 0

    for name, opp in alive.items():
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None:
            if pbid > max_prev_bid:
                max_prev_bid = pbid
        if name == 'Bob':
            bob_prev_bid = pbid
            bob_budget = opp.get('budget', 0)
        if name == 'Eric':
            eric_alive = True
            eric_prev_bid = pbid
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1

    scarcity = supply <= 18
    abundant = supply >= 22

    need_now = False
    if hp <= 2 or no_water_days >= 1:
        need_now = True

    if need_now:
        bid = 62.0
        if bob_prev_bid is not None and bob_prev_bid >= 80:
            bid = max(bid, min(95.0, bob_prev_bid + 3.0))
        return float(min(budget, bid))

    if scarcity:
        if bob_prev_bid is not None and bob_prev_bid >= 100:
            bid = 18.0
        elif bob_prev_bid is not None and bob_prev_bid >= 75:
            bid = 24.0
        else:
            bid = 16.2 if eric_alive else 14.0
        if urgent_opp >= 2:
            bid += 2.0
    elif abundant:
        if bob_prev_bid is not None and bob_prev_bid >= 90:
            bid = 12.0
        else:
            bid = 8.0
    else:
        if bob_prev_bid is not None and bob_prev_bid >= 90:
            bid = 16.5
        elif bob_prev_bid is not None and bob_prev_bid >= 70:
            bid = 18.5
        else:
            bid = 12.5 if eric_alive else 10.0

    if bob_budget is not None and bob_budget < 80:
        bid = min(bid, 17.0)
    if hp >= 8 and budget < 120:
        bid = min(bid, 12.0)
    if hp <= 4:
        bid = max(bid, 20.0)

    bid = max(0.0, min(float(budget), float(bid)))
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water >= 2:
            return float(min(budget, 63.0))
        return float(min(budget, 24.0))

    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if bid >= 85:
                rich_aggressive += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
            desperate_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (supply <= 17)
    comfortable = (hp >= 7 and no_water == 0)
    danger = (hp <= 3 or no_water >= 2)
    caution = (hp <= 5 or no_water >= 1)

    if danger:
        base_bid = 92.0 if scarcity else 78.0
    elif caution:
        base_bid = 62.0 if scarcity else 48.0
    else:
        if rich_aggressive >= 2 and not scarcity:
            base_bid = 18.0
        elif scarcity:
            base_bid = 44.0
        else:
            base_bid = 26.0

    if highest_prev > 0:
        if highest_prev >= 100:
            if comfortable and not scarcity:
                target = 16.0
            elif danger:
                target = 88.0
            else:
                target = max(base_bid, 42.0)
        elif highest_prev >= 80:
            if comfortable and not scarcity:
                target = 20.0
            else:
                target = max(base_bid, min(74.0, highest_prev * 0.78))
        else:
            target = max(base_bid, min(76.0, highest_prev + 3.0))
    else:
        target = base_bid

    if desperate_count >= 2 and scarcity:
        target = max(target, 72.0)
    elif desperate_count >= 1 and caution:
        target = max(target, 58.0)

    reserve_days = max(0, 10 - int(day))
    soft_cap = budget
    if reserve_days > 0:
        keep_reserve = reserve_days * 14.0
        soft_cap = max(0.0, budget - keep_reserve)
        if danger:
            soft_cap = budget
        elif caution:
            soft_cap = max(soft_cap, budget * 0.55)
        else:
            soft_cap = max(soft_cap, budget * 0.28)

    final_bid = min(target, soft_cap, budget)

    if final_bid < 1.0:
        if danger:
            final_bid = min(budget, max(1.0, budget))
        else:
            final_bid = min(budget, 1.0)

    return float(max(0.0, final_bid))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, 63.0)
        return min(budget, 18.0)

    prev_bids = []
    bob_bid = None
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if prev else None
        if bid is not None:
            prev_bids.append(float(bid))
            if opp_id == 'Bob':
                bob_bid = float(bid)

    anchor = 0.0
    if bob_bid is not None:
        anchor = bob_bid
    elif prev_bids:
        anchor = max(prev_bids)

    tight_supply = supply <= 17
    medium_supply = supply <= 20
    critical = hp <= 2 or no_water_days >= 2
    pressured = hp <= 4 or no_water_days >= 1

    if critical:
        if anchor > 0:
            bid = max(63.0, min(90.0, anchor + 2.0))
        else:
            bid = 65.0
        return min(budget, bid)

    if tight_supply:
        if anchor >= 65.0:
            bid = 24.0 if hp >= 6 and no_water_days == 0 else min(88.0, anchor + 1.5)
        elif anchor > 0:
            bid = max(52.0, anchor + 1.5)
        else:
            bid = 55.0
        return min(budget, bid)

    if medium_supply:
        if pressured:
            if anchor > 0:
                bid = max(48.0, min(78.0, anchor + 1.0))
            else:
                bid = 50.0
        else:
            if anchor >= 68.0:
                bid = 16.0
            else:
                bid = 28.0
        return min(budget, bid)

    if pressured:
        if anchor > 0 and anchor < 55.0:
            bid = anchor + 1.0
        else:
            bid = 34.0
        return min(budget, bid)

    return min(budget, 12.0)
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

    alive = []
    yesterday_bids = []
    rich_threat = 0
    urgent_opp = 0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_threat += 1
            if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 3:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    crowd = len(alive) + 1
    scarcity = crowd - slots

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    need_score = 0
    if hp <= 2:
        need_score += 4
    elif hp <= 4:
        need_score += 3
    elif hp <= 6:
        need_score += 2
    else:
        need_score += 1

    if no_water >= 2:
        need_score += 4
    elif no_water >= 1:
        need_score += 2

    if supply <= 16:
        need_score += 2
    elif supply <= 19:
        need_score += 1

    if scarcity >= 3:
        need_score += 3
    elif scarcity >= 2:
        need_score += 2
    elif scarcity >= 1:
        need_score += 1

    if rich_threat >= 1:
        need_score += 1
    if urgent_opp >= 2:
        need_score += 1

    if need_score <= 2:
        base = 16.0
    elif need_score <= 4:
        base = 28.0
    elif need_score <= 6:
        base = 46.0
    elif need_score <= 8:
        base = 68.0
    else:
        base = 92.0

    if highest_prev >= 120:
        if hp >= 7 and no_water == 0:
            bid = 12.0
        else:
            bid = max(base, 74.0)
    elif highest_prev >= 90:
        if hp >= 8 and no_water == 0 and supply >= 20:
            bid = 15.0
        else:
            bid = max(base, min(highest_prev + 2.0, 78.0))
    else:
        target = max(avg_prev + 3.0, base)
        bid = target

    if day >= 8:
        bid += 8.0
    elif day >= 6 and (hp <= 5 or no_water >= 1):
        bid += 5.0

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.9 + 2.0)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(0.95 * DAILY_SALARY, budget))

    bid = min(bid, budget)
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
    dangerous_prev = []
    cindy_like_high = []

    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) <= 110:
                    dangerous_prev.append(float(bid))
                else:
                    cindy_like_high.append(float(bid))

    if not alive:
        return float(min(budget, 18.0))

    alive_count = len(alive)
    units = supply / float(WATER_REQ)
    scarcity = alive_count - units

    need_urgent = hp <= 3 or no_water_days >= 1
    need_critical = hp <= 2 or no_water_days >= 2

    baseline = 32.0
    if scarcity >= 2.5:
        baseline = 58.0
    elif scarcity >= 1.5:
        baseline = 48.0
    elif scarcity >= 0.5:
        baseline = 40.0
    else:
        baseline = 28.0

    if dangerous_prev:
        target = max(dangerous_prev) + 2.0
    elif prev_bids:
        target = min(max(prev_bids) * 0.45, 65.0)
    else:
        target = baseline

    bid = max(baseline, target)

    if supply <= 16:
        bid += 8.0
    elif supply >= 23:
        bid -= 6.0

    if need_urgent:
        bid = max(bid, 62.0)
    if need_critical:
        bid = max(bid, 82.0)

    if hp >= 8 and no_water_days == 0 and supply >= 22 and dangerous_prev:
        bid = min(bid, max(dangerous_prev) - 3.0)

    reserve = DAILY_SALARY * max(0, 10 - int(day)) * 0.18
    cap = max(0.0, budget - reserve)
    if need_critical:
        cap = budget
    elif need_urgent:
        cap = max(cap, budget * 0.72)

    bid = min(bid, cap)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    rich_aggressive = 0
    desperate_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 90 and opp.get('budget', 0) >= 200:
                    rich_aggressive += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    abundant_supply = supply >= 22

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
    elif abundant_supply:
        urgency -= 1
    if day >= 8:
        urgency += 1

    if urgency >= 7:
        target = max(92.0, highest_prev + 3.0)
    elif urgency >= 5:
        target = max(72.0, avg_prev + 4.0, highest_prev * 0.78)
    elif urgency >= 3:
        target = max(44.0, avg_prev * 0.72)
    else:
        target = 22.0 if abundant_supply else 30.0

    if rich_aggressive >= 1 and urgency <= 3:
        target = min(target, 26.0 if abundant_supply else 32.0)

    if desperate_count >= 2 and urgency >= 3:
        target += 8.0

    if highest_prev >= 110:
        if urgency <= 3:
            target = min(target, 24.0)
        else:
            target = max(target, 84.0)
    elif highest_prev >= 80 and urgency <= 2:
        target = min(target, 28.0)

    if hp >= 8 and no_water_days == 0 and abundant_supply and day <= 4:
        target = min(target, 20.0)

    max_safe = budget
    if hp > 4 and no_water_days == 0:
        max_safe = min(max_safe, budget * 0.55)
    elif hp > 2:
        max_safe = min(max_safe, budget * 0.75)

    bid = min(target, max_safe)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, 95.0))
    elif hp <= 4 or no_water_days >= 1:
        bid = min(budget, max(bid, 68.0))

    if bid < 0:
        bid = 0.0

    return float(round(min(budget, bid), 2))
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if not alive:
        return min(budget, 18.0)

    scarcity = (WATER_REQ * (len(alive) + 1)) / max(supply, 1.0)

    highest_prev = 0.0
    cindy_prev = None
    urgent_opp = 0
    rich_opp = 0
    for agent_id, opp in alive:
        if float(opp.get('budget', 0.0)) >= 250:
            rich_opp += 1
        if int(opp.get('no_water_days', 0)) >= 1 or float(opp.get('hp', 10)) <= 4:
            urgent_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        if bid is not None:
            bid = float(bid)
            if bid > highest_prev:
                highest_prev = bid
            if agent_id == 'Cindy':
                cindy_prev = bid

    emergency = hp <= 3 or no_water >= 1
    severe = hp <= 2 or no_water >= 2

    if severe:
        bid = min(budget, max(78.0, highest_prev + 2.0, DAILY_SALARY * 1.02))
        return max(0.0, bid)

    if scarcity >= 2.6:
        base = 62.0
    elif scarcity >= 2.2:
        base = 48.0
    elif scarcity >= 1.8:
        base = 34.0
    else:
        base = 20.0

    if cindy_prev is not None:
        if cindy_prev >= 145:
            target = 28.0 if hp > 4 and no_water == 0 else 74.0
        elif cindy_prev >= 120:
            target = min(cindy_prev + 1.5, 92.0)
        elif cindy_prev >= 80:
            target = cindy_prev + 2.0
        else:
            target = max(base, cindy_prev + 1.5)
    elif highest_prev > 0:
        if highest_prev >= 100:
            target = 30.0 if hp > 4 and no_water == 0 else 72.0
        else:
            target = max(base, highest_prev + 1.5)
    else:
        target = base

    if urgent_opp >= 2:
        target += 6.0
    elif urgent_opp == 0 and scarcity < 2.0:
        target -= 4.0

    if rich_opp >= 2 and scarcity >= 2.2:
        target += 5.0

    if emergency:
        target = max(target, 76.0)

    remaining_days = max(0, 10 - day)
    reserve_floor = remaining_days * 18.0
    affordable = budget
    if budget > reserve_floor:
        affordable = max(0.0, budget - reserve_floor * 0.35)

    bid = min(target, affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return bid
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
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp = False
    rich_opp = False

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if float(opp.get('budget', 0)) > budget:
                rich_opp = True
            if int(opp.get('no_water_days', 0)) >= 2 or float(opp.get('hp', 0)) <= 3:
                urgent_opp = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except Exception:
                    pass

    if not alive_opps:
        return min(budget, 18.0)

    max_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    my_urgent = no_water >= 2 or hp <= 3
    caution = no_water >= 1 or hp <= 6

    base = DAILY_SALARY * (0.32 + 0.28 * scarcity)

    if supply >= 23:
        base -= 8.0
    elif supply <= 17:
        base += 10.0

    if my_urgent:
        target = max(base + 28.0, max_prev + 4.0, DAILY_SALARY * 0.92)
    elif caution:
        target = max(base + 10.0, min(max_prev + 2.0, DAILY_SALARY * 0.95))
    else:
        if max_prev >= 130:
            target = base - 6.0
        elif max_prev >= 90:
            target = max(base, avg_prev * 0.72)
        else:
            target = max(base, max_prev + 1.5)

    if urgent_opp and not my_urgent:
        target -= 4.0
    if rich_opp and not my_urgent and max_prev > 110:
        target -= 5.0

    days_left = max(0, 10 - day)
    reserve = days_left * 14.0
    if budget < reserve:
        target *= 0.82
    if budget < 90:
        target = min(target, DAILY_SALARY * 0.72)

    if my_urgent and budget > 0:
        target = max(target, min(budget, DAILY_SALARY * 1.05))

    if target < 0:
        target = 0.0
    if target > budget:
        target = budget

    return float(round(target, 2))
"""
