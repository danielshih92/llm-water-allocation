# ============================================================
# Experiment: exp_000
# Agent: Eric
# Source: exp_000
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    salary = 140
    water_req = 8

    base_bid = salary * 0.6
    if hp <= 2:
        base_bid = salary * 0.9
    elif no_water_days >= 2:
        base_bid = salary * 0.8

    if day >= 8:
        base_bid = max(base_bid, salary * 0.75)

    bid = min(budget, base_bid)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4, 200)
    
    # Estimate how many can get water based on supply
    supply = day_context['supply']
    capacity = int(supply // WATER_REQ)  # cast to int for safety
    
    # Collect yesterday's bids if available
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev.get('bid'), (int, float)):
            yesterday_bids.append(prev['bid'])
    
    # Determine bid based on yesterday's highest pressure
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If someone bid very high yesterday, they must be low on budget today -> lower bid
        if max_prev >= 100:
            # high pressure meant they might have spent a lot, now need water but less budget
            # We can afford a moderate bid
            target = min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev * 0.8))
        elif max_prev >= 80:
            # moderate pressure
            if my_status['hp'] <= 2:
                target = min(my_status['budget'], DAILY_SALARY * 0.9)
            else:
                target = min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev + 5))
        else:
            # low previous bids, we can be more conservative
            target = min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev + 8))
    else:
        # no previous data, default based on HP
        if my_status['hp'] <= 2:
            target = min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            target = min(my_status['budget'], DAILY_SALARY * 0.55)
    
    # Adjust for survival: ensure we don't bid more than necessary
    # If multiple winners likely, we can bid lower
    if capacity >= len(alive_opponents) + 1:
        target *= 0.9
    elif capacity == 1:
        target = min(my_status['budget'], max(target, DAILY_SALARY * 0.7))
    
    # Ensure we don't exceed budget
    return min(my_status['budget'], max(0, round(target, 2)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    day = day_context['day']
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        max_prev = 0
        avg_prev = 0
    if hp <= 3:
        target = max(DAILY_SALARY * 0.9, max_prev + 2)
    elif hp <= 5:
        target = max(DAILY_SALARY * 0.7, avg_prev + 1)
    else:
        target = DAILY_SALARY * 0.5
    # ensure not over budget
    bid = min(budget, target)
    # also ensure at least 0
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate number of winners
    max_winners = int(supply // WATER_REQ)

    # Base bid: if we have no history, use conservative estimate
    if not yesterday_bids:
        if hp <= 3:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.6)

    # Highest yesterday bid among alive
    highest_prev = max(yesterday_bids)

    # If there were winners yesterday, they might bid similarly
    # If we need water badly, bid above highest yesterday
    if hp <= 2 or my_status['no_water_days'] >= 2:
        target = max(highest_prev + 2, DAILY_SALARY * 0.9)
    else:
        # We can be more conservative: bid just enough to beat low bidders
        if highest_prev >= DAILY_SALARY * 0.85:
            # High pressure from others, bid moderately if healthy
            target = DAILY_SALARY * 0.5
        else:
            target = max(highest_prev + 1, DAILY_SALARY * 0.4)

    # Ensure we don't exceed budget and don't bid irrational
    bid = min(budget, target)
    return int(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and 'bid' in prev_trace and prev_trace['bid'] is not None:
            prev_bids.append(prev_trace['bid'])

    # Determine base bid
    if my_hp <= 2 or no_water_days >= 2:
        # Desperate: need water badly, bid high
        target_bid = min(my_budget, DAILY_SALARY * 0.95)
        return max(target_bid, min(my_budget, DAILY_SALARY * 0.85))
    else:
        # Normal: bid moderate, but increase if supply is low or opponents bid high
        if prev_bids:
            max_prev = max(prev_bids)
            # If opponent bid high yesterday, expect similar today
            if max_prev > DAILY_SALARY * 0.8:
                target_bid = max(DAILY_SALARY * 0.7, max_prev + 1.5)
            else:
                target_bid = DAILY_SALARY * 0.55
        else:
            target_bid = DAILY_SALARY * 0.55

        # Adjust for supply scarcity
        if supply < 18:
            target_bid *= 1.2
        elif supply > 22:
            target_bid *= 0.9

        target_bid = min(my_budget, target_bid)
        return target_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = int(day_context['supply']) if isinstance(day_context['supply'], float) else day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    # Determine base bid
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If there was a high bidder, we need to compete
        if max_yesterday > DAILY_SALARY * 0.8:
            target_bid = max(base_bid, max_yesterday * 0.95 + 2)
        elif max_yesterday > DAILY_SALARY * 0.5:
            target_bid = max(base_bid, max_yesterday * 1.02 + 1)
        else:
            target_bid = base_bid
    else:
        target_bid = base_bid
    # Ensure we don't exceed budget and not overbid unnecessarily
    bid = min(budget, max(target_bid, 1))
    # If we have many no_water_days, increase urgency
    if no_water_days >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.85))
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    supply_int = int(supply)
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    if yesterday_bids:
        # Target slightly above the highest yesterday bid
        target = max(yesterday_bids) + 1.0
    else:
        target = DAILY_SALARY * 0.6
    
    # Adjust based on health
    if hp <= 2 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp >= 5:
        target = min(target, DAILY_SALARY * 0.7)
    else:
        target = min(target, DAILY_SALARY * 0.85)
    
    # Ensure we don't bid more than budget
    bid = min(budget, target)
    # Round to two decimals
    bid = round(bid, 2)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Base bid proportional to water need relative to supply
    base_bid = (WATER_REQ / supply) * DAILY_SALARY * 1.2
    # Adjust for hp
    if hp <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    if no_water_days > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Look at yesterday's max bid from opponents
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']

    # If opponents were aggressive, we need to compete
    if max_prev_bid > DAILY_SALARY * 1.0:
        # highly aggressive opponent
        if hp <= 2:
            target = max(DAILY_SALARY * 1.2, max_prev_bid + 1)
        else:
            target = min(DAILY_SALARY * 0.8, max_prev_bid - 10)
    elif max_prev_bid > DAILY_SALARY * 0.6:
        target = max(base_bid, max_prev_bid + 2)
    else:
        target = base_bid

    # ensure within budget and not too high
    final_bid = min(budget, max(0, target))
    return int(final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for o in alive_opponents.values():
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine baseline bid based on yesterday's max
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If they bid high yesterday, they might bid high again; we need to outbid if necessary
        if hp <= 2 or no_water_days >= 2:
            # Desperate: bid enough to get water, maybe slightly above max
            bid = max_prev + 2.0
        else:
            # Healthy: bid conservatively to save budget, but still competitive
            bid = max_prev * 0.55
    else:
        # No history: use safe default
        if hp <= 2 or no_water_days >= 2:
            bid = DAILY_SALARY * 0.9
        else:
            bid = DAILY_SALARY * 0.4
    
    # Ensure bid does not exceed budget
    bid = min(bid, budget)
    # Ensure minimum bid to avoid zero (cannot bid negative)
    bid = max(bid, 0.0)
    return bid
"""
