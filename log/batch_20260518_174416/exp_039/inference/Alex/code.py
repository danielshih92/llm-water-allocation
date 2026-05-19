# ============================================================
# Experiment: exp_039
# Agent: Alex
# Source: exp_039
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
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        if hp <= 3 or no_water_days >= 2:
            return max(0, min(budget, 28.0))
        return max(0, min(budget, 8.0))

    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    base = DAILY_SALARY * (0.42 + 0.18 * tightness)

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(base + 18.0, highest_prev + 2.0, DAILY_SALARY * 0.88)
    elif hp <= 4 or no_water_days >= 1:
        bid = max(base + 8.0, avg_prev + 2.0, DAILY_SALARY * 0.62)
    else:
        if highest_prev >= DAILY_SALARY * 0.9:
            bid = DAILY_SALARY * 0.28
        elif highest_prev >= DAILY_SALARY * 0.75:
            bid = max(DAILY_SALARY * 0.38, avg_prev - 6.0)
        elif highest_prev > 0:
            bid = max(base, highest_prev + 1.5)
        else:
            bid = base

    bid += min(6.0, urgent_opp * 1.5)
    bid += min(4.0, rich_opp * 0.8)

    if supply >= 22:
        bid -= 6.0
    elif supply <= 17:
        bid += 5.0

    reserve_floor = 0.0
    if hp > 4 and no_water_days == 0:
        reserve_floor = min(12.0, budget * 0.18)

    bid = min(bid, max(0.0, budget - reserve_floor))
    bid = max(0.0, min(budget, bid))
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

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        if hp <= 2 or no_water >= 1:
            return min(budget, 45.0)
        return min(budget, 18.0)

    prev_bids = []
    prev_by_id = {}
    eric_prev = None
    urgent_count = 0
    rich_count = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev and prev.get('bid') is not None:
            bid = prev.get('bid')
            prev_bids.append(bid)
            prev_by_id[oid] = bid
        if oid == 'Eric' and bid is not None:
            eric_prev = bid
        if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_count += 1
        if opp.get('budget', 0) >= 100:
            rich_count += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = supply <= 17
    ample = supply >= 22
    danger = hp <= 2 or no_water >= 1
    caution = hp <= 4

    bid = 0.0

    if danger:
        anchor = eric_prev if eric_prev is not None else highest_prev
        if scarcity:
            bid = max(78.0, anchor + 4.0)
        else:
            bid = max(62.0, anchor * 0.72 + 6.0)
    elif scarcity:
        if eric_prev is not None:
            bid = max(48.0, eric_prev + 2.5)
        else:
            bid = max(42.0, highest_prev + 2.0)
        if rich_count >= 2:
            bid += 6.0
        if day >= 7:
            bid += 4.0
    elif ample:
        if hp >= 6 and no_water == 0:
            bid = 16.0
        else:
            bid = max(24.0, avg_prev * 0.22)
    else:
        if eric_prev is not None:
            bid = max(28.0, min(58.0, eric_prev * 0.42))
        else:
            bid = max(26.0, min(52.0, avg_prev * 0.55 + 4.0))
        if caution:
            bid += 8.0
        if urgent_count >= 2:
            bid += 5.0

    if day >= 8:
        bid += 6.0
    if budget < 60:
        bid = min(bid, budget)
    else:
        bid = min(bid, budget, 110.0)

    if bid < 0:
        bid = 0.0
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
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    dangerous_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                    dangerous_bids.append(float(bid))

    if not alive_opponents:
        return float(min(budget, 18.0))

    expected_winners = supply / float(WATER_REQ)
    tight_supply = expected_winners < 2.0
    medium_supply = expected_winners < 3.0

    highest_prev = max(prev_bids) if prev_bids else 0.0
    urgent_prev = max(dangerous_bids) if dangerous_bids else highest_prev

    if hp <= 2 or no_water >= 2:
        bid = max(110.0, highest_prev + 2.0)
    elif hp <= 4 or no_water >= 1:
        if tight_supply:
            bid = max(108.0, highest_prev + 1.5)
        else:
            bid = max(92.0, urgent_prev + 1.0)
    else:
        if tight_supply:
            bid = max(100.0, highest_prev + 1.0)
        elif medium_supply:
            bid = 72.0 if highest_prev > 105.0 else max(66.0, highest_prev * 0.72)
        else:
            bid = 38.0 if highest_prev > 100.0 else 52.0

    if day >= 8 and hp >= 7 and no_water == 0:
        bid *= 0.9

    reserve_floor = 0.0
    if hp > 4:
        reserve_floor = DAILY_SALARY * max(0, 10 - day) * 0.18
    spendable = max(0.0, budget - reserve_floor)
    if spendable <= 0:
        spendable = min(budget, DAILY_SALARY * 0.75)

    final_bid = min(float(budget), float(spendable), float(bid))
    if final_bid < 0:
        final_bid = 0.0
    return float(final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    units_available = int(supply / WATER_REQ)
    total_players = 1 + len(alive)
    scarcity = units_available < total_players

    highest_prev = 0.0
    urgent_prev = 0.0
    pressure_sum = 0.0
    pressure_count = 0

    for agent_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = 0.0
        if prev and prev.get('bid') is not None:
            bid = float(prev.get('bid', 0.0))
            if bid > highest_prev:
                highest_prev = bid
            pressure_sum += bid
            pressure_count += 1

        opp_urgent = False
        if opp.get('no_water_days', 0) >= 1 or opp.get('hp', 10) <= 4:
            opp_urgent = True
        if prev and prev.get('status') == 'lost':
            opp_urgent = True
        if opp_urgent and bid > urgent_prev:
            urgent_prev = bid

    avg_prev = pressure_sum / pressure_count if pressure_count > 0 else 0.0

    danger = 0
    if hp <= 3:
        danger += 2
    elif hp <= 5:
        danger += 1
    if no_water_days >= 1:
        danger += 2

    if scarcity:
        if danger >= 3:
            target = max(92.0, highest_prev + 2.5, urgent_prev + 2.5)
        elif danger >= 1:
            target = max(74.0, avg_prev + 4.0, urgent_prev + 2.0)
        else:
            if highest_prev >= 120.0:
                target = 46.0
            elif highest_prev >= 90.0:
                target = 58.0
            else:
                target = max(52.0, avg_prev * 0.78)
    else:
        if danger >= 3:
            target = max(72.0, avg_prev + 1.5)
        elif danger >= 1:
            target = 44.0
        else:
            target = 24.0

    if day >= 8:
        if danger >= 1:
            target += 8.0
        else:
            target += 3.0

    if budget < target:
        if danger >= 3:
            target = budget
        elif danger >= 1:
            target = max(0.0, min(budget, budget * 0.92))
        else:
            target = max(0.0, min(budget, budget * 0.7))

    target = min(target, budget)
    if target < 0:
        target = 0.0
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
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= DAILY_SALARY * 2:
                rich_opp += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive:
        return float(min(budget, 8.0))

    slots = max(1, int(supply // WATER_REQ))
    tight_supply = slots <= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water >= 1:
        base = DAILY_SALARY * 0.95
        if highest_prev > 0:
            base = max(base, min(highest_prev + 3.0, DAILY_SALARY * 1.15))
        if tight_supply:
            base += 8.0
        return float(max(0.0, min(budget, base)))

    if tight_supply:
        if highest_prev >= 180:
            base = DAILY_SALARY * 0.42
        elif highest_prev >= 90:
            base = highest_prev + 2.5
        elif highest_prev >= 35:
            base = max(48.0, highest_prev + 2.0)
        else:
            base = 46.0 + 4.0 * urgent_opp
    else:
        if highest_prev >= 180:
            base = DAILY_SALARY * 0.22
        elif highest_prev >= 90:
            base = DAILY_SALARY * 0.32
        elif highest_prev >= 35:
            base = max(24.0, avg_prev * 0.7)
        else:
            base = 18.0

    if hp >= 8 and no_water == 0 and not tight_supply:
        base *= 0.85
    if day >= 8 and hp > 4:
        base *= 0.9
    if rich_opp >= 2 and tight_supply:
        base += 4.0

    reserve_floor = 10.0 if day < 8 else 0.0
    spend_cap = max(0.0, budget - reserve_floor)
    if spend_cap <= 0:
        spend_cap = budget

    bid = min(base, spend_cap)
    bid = max(0.0, min(budget, bid))
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

    alive = []
    prev_bids = []
    david_bid = None
    high_spender_count = 0
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)
                if agent_id == 'David':
                    david_bid = bid
                if bid >= 90:
                    high_spender_count += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    tight_supply = supply <= 17
    medium_supply = supply <= 20

    urgency = 0
    if hp <= 3:
        urgency += 3
    elif hp <= 6:
        urgency += 2
    else:
        urgency += 1
    if no_water >= 2:
        urgency += 3
    elif no_water >= 1:
        urgency += 1
    if tight_supply:
        urgency += 2
    elif medium_supply:
        urgency += 1

    target = 0.0

    if david_bid is not None:
        if urgency >= 5:
            target = david_bid + 6.0
        elif urgency >= 3:
            target = david_bid + 2.5
        else:
            target = max(18.0, david_bid - 6.0)
    elif prev_bids:
        highest_prev = max(prev_bids)
        if urgency >= 5:
            target = min(highest_prev + 2.0, 78.0)
        elif urgency >= 3:
            target = max(28.0, highest_prev * 0.55)
        else:
            target = max(16.0, highest_prev * 0.3)
    else:
        if urgency >= 5:
            target = 60.0
        elif urgency >= 3:
            target = 34.0
        else:
            target = 20.0

    if high_spender_count >= 2 and urgency <= 2 and supply >= 20:
        target = min(target, 16.0)

    if day >= 8 and hp > 6 and no_water == 0:
        target = min(target, 22.0)

    if hp <= 2 or no_water >= 2:
        target = max(target, 72.0)

    if budget < DAILY_SALARY * 2:
        target = min(target, max(12.0, budget * 0.6))

    target = max(0.0, min(float(budget), float(target)))
    return float(target)
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

    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    serious = []
    max_prev_bid = 0.0
    cindy_like_bid = None
    for opp in alive_opponents:
        if opp.get('budget', 0) > 0:
            serious.append(opp)
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is not None and pbid > max_prev_bid:
            max_prev_bid = pbid
        if opp.get('daily_salary') == 70 and opp.get('water_requirement') == 13 and pbid is not None:
            if cindy_like_bid is None or pbid > cindy_like_bid:
                cindy_like_bid = pbid

    if not serious:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 35.0))
        return float(min(budget, 5.0))

    units = supply / WATER_REQ
    if units >= 2.0:
        base = 46.0
    elif units >= 1.5:
        base = 58.0
    else:
        base = 72.0

    if cindy_like_bid is not None:
        if units < 1.5:
            base = max(base, cindy_like_bid + 3.0)
        elif units < 2.0:
            base = max(base, cindy_like_bid + 1.5)
        else:
            base = max(base, cindy_like_bid - 8.0)
    elif max_prev_bid > 0:
        base = max(base, max_prev_bid + 1.5)

    if hp <= 2 or no_water_days >= 2:
        base = max(base, 84.0)
    elif hp <= 4 or no_water_days >= 1:
        base = max(base, 68.0)

    if day >= 8 and hp > 4 and no_water_days == 0 and units >= 1.5:
        base -= 6.0

    if budget < base:
        if hp <= 2 or no_water_days >= 2:
            return float(budget)
        return float(min(budget, max(0.0, base * 0.85)))

    return float(min(budget, max(0.0, base)))
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
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    strong_prev = 0.0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = float(prev['bid'])
                prev_bids.append(bid)
                if bid > strong_prev:
                    strong_prev = bid

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, 25.0))
        return float(min(budget, 8.0))

    tight_supply = supply <= 16
    medium_supply = supply <= 19
    danger = hp <= 2 or no_water_days >= 2
    caution = hp <= 4 or no_water_days >= 1

    if danger:
        target = max(78.0, strong_prev + 2.0)
        if tight_supply:
            target = max(target, 86.0)
        return float(min(budget, target))

    if tight_supply:
        if strong_prev >= 80.0:
            target = strong_prev + 1.5
        elif strong_prev >= 65.0:
            target = strong_prev + 2.0
        else:
            target = 72.0
        if caution:
            target += 4.0
        return float(min(budget, target))

    if medium_supply:
        if caution:
            target = max(62.0, strong_prev + 1.0 if strong_prev >= 55.0 else 62.0)
        else:
            if strong_prev >= 75.0:
                target = 54.0
            elif strong_prev >= 60.0:
                target = 58.0
            else:
                target = 52.0
        return float(min(budget, target))

    if caution:
        target = 48.0 if strong_prev < 60.0 else 55.0
        return float(min(budget, target))

    if day >= 8:
        return float(min(budget, 44.0))
    return float(min(budget, 36.0))
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
    bob_bid = None
    cindy_bid = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((agent_id, opp))
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if agent_id == 'Bob':
                    bob_bid = bid
                elif agent_id == 'Cindy':
                    cindy_bid = bid

    if not alive:
        return min(budget, 20.0)

    seats = supply / float(WATER_REQ)
    tight = seats < 2.0

    target = 55.5
    if bob_bid is not None:
        target = bob_bid + 1.6
    elif prev_bids:
        target = min(max(prev_bids) + 1.0, 62.0)

    if cindy_bid is not None and cindy_bid > 100:
        target = min(target, 58.0)

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

    if tight:
        urgency += 1
    if day >= 8:
        urgency += 1

    if urgency >= 5:
        bid = max(target + 4.0, 66.0)
    elif urgency >= 3:
        bid = max(target + 1.0, 58.0)
    elif urgency >= 1:
        bid = max(target - 1.0, 52.0)
    else:
        bid = 34.0 if tight else 28.0

    if budget < 120:
        bid = min(bid, 0.55 * budget)
    elif budget < 200:
        bid = min(bid, 0.7 * budget)

    if hp <= 2 or no_water_days >= 2:
        bid = max(bid, min(budget, 68.0))

    if len(alive) == 1:
        only_id = alive[int(0)][0]
        if only_id == 'Cindy':
            bid = 25.0 if hp > 3 and no_water_days == 0 else 60.0
        else:
            bid = max(bid, 56.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return bid
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

    alive_opponents = []
    for opp_id in opponents_status:
        opp = opponents_status[opp_id]
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    if not alive_opponents:
        if hp <= 2 or no_water_days >= 2:
            return float(min(budget, DAILY_SALARY * 0.9))
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    threat_scores = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            req = opp.get('water_requirement', WATER_REQ)
            obudget = opp.get('budget', 0)
            ohp = opp.get('hp', 0)
            ono = opp.get('no_water_days', 0)
            score = float(bid)
            if req >= WATER_REQ:
                score += 4.0
            if ohp <= 3 or ono >= 1:
                score += 6.0
            if obudget > budget:
                score += 3.0
            threat_scores.append(score)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    highest_threat = max(threat_scores) if threat_scores else highest_prev

    scarcity = 0
    if supply <= 16:
        scarcity = 3
    elif supply <= 18:
        scarcity = 2
    elif supply <= 21:
        scarcity = 1

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

    if scarcity >= 3:
        base = max(72.0, highest_threat + 2.5)
    elif scarcity == 2:
        base = max(60.0, highest_prev + 1.5)
    elif scarcity == 1:
        base = max(46.0, highest_prev * 0.72)
    else:
        base = max(28.0, highest_prev * 0.48)

    if urgency >= 5:
        base = max(base, highest_threat + 4.0, 88.0)
    elif urgency >= 3:
        base = max(base, highest_prev + 2.0, 72.0)
    elif urgency >= 1:
        base = max(base, 52.0)

    if day >= 8 and hp > 5 and no_water_days == 0 and supply >= 20:
        base *= 0.82

    max_safe = budget
    if hp > 6 and no_water_days == 0:
        max_safe = min(max_safe, DAILY_SALARY * 1.1)
    elif hp > 3:
        max_safe = min(max_safe, DAILY_SALARY * 1.45)

    bid = min(base, max_safe)

    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, max(bid, highest_threat + 5.0, DAILY_SALARY * 1.2))

    if bid < 0:
        bid = 0.0

    return float(min(budget, bid))
"""
