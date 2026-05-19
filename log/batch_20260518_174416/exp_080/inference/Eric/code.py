# ============================================================
# Experiment: exp_080
# Agent: Eric
# Source: exp_080
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    # No previous traces, default moderate bid
    bid = DAILY_SALARY * 0.6
    # Ensure we have enough budget
    bid = min(bid, my_status['budget'])
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    num_winners = int(supply // WATER_REQ)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Check yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
        # Desperate: bid high to secure water
        bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    elif yesterday_bids:
        # Assume opponents similar today; pick a target just above the lowest yesterday bid among alive
        min_yesterday = min(yesterday_bids)
        threshold = max(DAILY_SALARY * 0.4, min_yesterday + 5.0)
        bid = min(my_status['budget'], threshold)
    else:
        # No info: moderate bid
        bid = min(my_status['budget'], DAILY_SALARY * 0.5)
    
    # Ensure positive bid
    bid = max(1.0, bid)
    return bid
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
    supply = day_context['supply']
    day = int(day_context['day'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid calculation
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_prev_bid = max(yesterday_bids)
    else:
        avg_prev_bid = 0
        max_prev_bid = 0
    
    # HP-based urgency
    if my_hp <= 2:  # desperate for water
        target_bid = min(my_budget, DAILY_SALARY * 1.1)
    elif my_hp <= 4:  # moderate urgency
        target_bid = min(my_budget, max(DAILY_SALARY * 0.8, avg_prev_bid + 2))
    else:  # healthy, can be more conservative
        target_bid = min(my_budget, max(DAILY_SALARY * 0.6, avg_prev_bid + 1))
    
    # Adjust for supply tightness
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # When supply is low, increase bid; when high, decrease
    supply_factor = 1 + (1 - supply_ratio) * 0.3  # ranges 1.0 to 1.3
    target_bid *= supply_factor
    
    # Ensure we don't overbid beyond budget
    bid = min(target_bid, my_budget - 1)  # leave small buffer
    # Ensure non-negative
    if bid < 0:
        bid = 0
    # Round to 2 decimals for realism
    return round(bid, 2)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Determine alive opponents
    alive_opps = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Compute yesterday's average bid from traces of alive opponents
    yesterday_bids = []
    for opp in alive_opps.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)
        # If they were aggressive, we may need to be more aggressive
        if avg_yesterday_bid > DAILY_SALARY * 0.8:
            # high competition, bid strong but not reckless
            base_bid = min(my_status['budget'], DAILY_SALARY * 0.7)
        else:
            # moderate competition
            base_bid = min(my_status['budget'], avg_yesterday_bid + 5)
    else:
        base_bid = min(my_status['budget'], DAILY_SALARY * 0.5)

    # Adjust based on our own HP
    if my_status['hp'] <= 2:
        # desperate: need water badly
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] > 5:
        # comfortable: can be conservative
        bid = min(my_status['budget'], base_bid * 0.8)
    else:
        bid = min(my_status['budget'], base_bid)

    # Ensure minimum bid to have chance
    bid = max(bid, 1)
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    if prev_bids:
        highest_prev = max(prev_bids)
        # if yesterday was very competitive, lower bid to save money
        if highest_prev >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                bid = min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            bid = min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev + 1.5))
    else:
        # no previous data, base on hp
        if my_status['hp'] <= 2:
            bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.55)

    # ensure bid is non-negative and within budget
    bid = max(0.0, min(bid, my_status['budget']))
    # round to 2 decimals to avoid floating issues
    bid = round(bid, 2)
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure integer

    alive = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Check previous_trace of opponents
    prev_bids = []
    for o in alive.values():
        trace = o.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Base on hp and budget
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # If we are in desperate need
    if no_water > 0:
        urgent_factor = 0.95
    else:
        urgent_factor = 0.5

    # If we have high hp, we can be cautious
    if hp > 5:
        base = DAILY_SALARY * 0.35
    else:
        base = DAILY_SALARY * 0.55

    # React to previous bids
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponents were aggressive, resist overbidding
        if max_prev > DAILY_SALARY * 0.7:
            # Bid slightly less than their highest, but within budget
            target = max(base, max_prev * 0.85)
        else:
            # Otherwise a bit more than their max
            target = max(base, max_prev + 2.0)
    else:
        # No history: assume moderate competition
        target = DAILY_SALARY * 0.45

    # Adjust for supply scarcity
    if supply < WATER_REQ * 2:
        target *= 1.2
    elif supply > WATER_REQ * 3:
        target *= 0.85

    # Ensure we don't exceed budget
    final_bid = min(budget, target)
    # Don't bid more than needed
    max_waste = DAILY_SALARY * 0.9
    final_bid = min(final_bid, max_waste)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.5)
    max_prev = max(yesterday_bids)
    if my_status['hp'] <= 2:
        return min(my_status['budget'], max_prev + 5)
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max_prev + 2)
    return min(my_status['budget'], max(DAILY_SALARY * 0.3, max_prev - 10))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Determine highest previous bid among alive opponents
    highest_prev = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None and isinstance(bid, (int, float)):
            if bid > highest_prev:
                highest_prev = bid

    hp = my_status['hp']
    budget = my_status['budget']

    # Calculate survival bid based on water requirement and supply
    supply = day_context['supply']
    # Ensure integer index for any list usage (none here, but safe)
    # Compute a baseline bid
    if hp <= 2:
        # Desperate: bid up to 90% of salary plus maybe beat high previous
        target = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
        return min(budget, target)
    elif hp <= 4:
        # Moderate risk: try to win if previous high is not extreme
        if highest_prev >= DAILY_SALARY * 1.2:
            # Too expensive, conserve
            return min(budget, DAILY_SALARY * 0.5)
        else:
            target = max(DAILY_SALARY * 0.6, highest_prev + 1.5)
            return min(budget, target)
    else:
        # Healthy: bid conservatively
        if highest_prev == 0:
            return min(budget, DAILY_SALARY * 0.4)
        if highest_prev >= DAILY_SALARY * 1.0:
            return min(budget, DAILY_SALARY * 0.3)
        return min(budget, max(DAILY_SALARY * 0.45, highest_prev + 1.0))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    highest_prev_bid = max(prev_bids) if prev_bids else 0
    
    my_hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    if my_hp <= 2 or no_water > 0:
        # Desperate: bid up to salary
        target = min(budget, DAILY_SALARY * 0.95)
    else:
        # Safe: try to beat highest previous by small margin
        target = max(DAILY_SALARY * 0.4, highest_prev_bid + 1.5)
        target = min(budget, target)
    
    # Ensure minimum 0
    return max(0, target)
"""
