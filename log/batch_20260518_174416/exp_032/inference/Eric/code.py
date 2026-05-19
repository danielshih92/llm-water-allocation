# ============================================================
# Experiment: exp_032
# Agent: Eric
# Source: exp_032
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Determine base fraction based on supply
    if supply < 19:
        base = 0.65
    elif supply < 22:
        base = 0.5
    else:
        base = 0.4

    # Increase if desperate
    if hp <= 2 or no_water_days > 0:
        base = max(base, 0.85)

    bid = base * DAILY_SALARY
    bid = min(bid, budget)  # cannot exceed budget
    bid = max(bid, 0)
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
    return 15.0
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Base bid: slightly above max previous opponent bid
    base_bid = max_prev_bid + 1
    
    # Adjust based on HP
    if hp <= 2:
        # Desperate: bid high up to 90% of salary, but at least base
        target = max(base_bid, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # Moderate: bid around 65% of salary or base
        target = max(base_bid, DAILY_SALARY * 0.65)
    else:
        # Healthy: can save, bid lower
        target = max(base_bid, DAILY_SALARY * 0.4)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140

    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If we are desperate or opponent pressure high, adjust
        if hp <= 2:
            # desperate, need water at any cost
            bid = min(budget, DAILY_SALARY * 0.95)
        elif hp <= 4:
            # somewhat low, be slightly aggressive
            bid = min(budget, max(DAILY_SALARY * 0.6, highest_prev + 2.0))
        else:
            # healthy, can be conservative, beat highest if possible but not overpay
            bid = min(budget, max(DAILY_SALARY * 0.4, highest_prev + 1.5))
    else:
        # no yesterday info, use base heuristic
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        elif hp <= 4:
            bid = min(budget, DAILY_SALARY * 0.6)
        else:
            bid = min(budget, DAILY_SALARY * 0.45)

    # Ensure bid does not exceed budget
    if bid > budget:
        bid = budget
    # Ensure bid is at least 0
    if bid < 0:
        bid = 0
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = float(day_context['supply'])  # convert to float explicitly
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    # get yesterday's max bid among alive opponents
    yesterday_max_bid = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = float(prev['bid'])
            if bid_val > yesterday_max_bid:
                yesterday_max_bid = bid_val

    # base bid: beat yesterday's max by a small margin, else moderate
    if yesterday_max_bid > 0:
        base_bid = yesterday_max_bid + 5.0
    else:
        base_bid = DAILY_SALARY * 0.55

    # adjust based on HP
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.65)
    elif hp >= 8:
        base_bid = min(base_bid, DAILY_SALARY * 0.45)

    # adjust based on supply
    if supply < 18:
        base_bid *= 1.2
    elif supply > 22:
        base_bid *= 0.8

    # ensure within bounds
    min_bid = DAILY_SALARY * 0.2
    max_bid = min(budget, DAILY_SALARY * 0.95)
    bid = max(min_bid, min(max_bid, base_bid))

    # round to two decimals for cleanliness
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
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 0.0)
    
    # Extract previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    max_prev = max(prev_bids) if prev_bids else None
    
    # Base bid proportional to water need vs supply
    base = (WATER_REQ / supply) * DAILY_SALARY
    
    # Adjust based on hp and previous max
    if hp <= 2:
        # Urgent need: bid high
        target = max(base, DAILY_SALARY * 0.9)
        if max_prev is not None:
            target = max(target, max_prev + 5)
    elif hp <= 5:
        # Moderate need
        target = max(base, DAILY_SALARY * 0.6)
        if max_prev is not None:
            target = max(target, max_prev + 2)
    else:
        # Healthy: can be conservative
        target = max(base, DAILY_SALARY * 0.3)
        if max_prev is not None:
            target = min(target, max_prev - 2)  # undercut
        target = max(target, 0)
    
    # Ensure not exceeding budget and not negative
    bid = min(budget, target)
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max_bid = 0.0
    yesterday_min_bid = float('inf')
    yesterday_bid_list = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev.get('bid'), (int, float)):
            bid = prev['bid']
            yesterday_bid_list.append(bid)
            if bid > yesterday_max_bid:
                yesterday_max_bid = bid
            if bid < yesterday_min_bid:
                yesterday_min_bid = bid
    if not yesterday_bid_list:
        # No information: bid moderately based on urgency
        if my_hp <= 2:
            return min(my_budget, DAILY_SALARY * 0.7)
        else:
            return min(my_budget, DAILY_SALARY * 0.4)
    # Exploit: if someone bid very high yesterday, they likely lost HP
    # If the highest bid was > 120, they might be weak; bid low to save
    # If the highest bid was moderate, bid slightly above it to secure water
    # If my HP is low, be aggressive
    if my_hp <= 2:
        target = min(my_budget, max(DAILY_SALARY * 0.8, yesterday_max_bid + 5))
        return target
    elif my_hp <= 4:
        # Medium health: bid around the second highest yesterday
        sorted_bids = sorted(yesterday_bid_list, reverse=True)
        if len(sorted_bids) >= 2:
            second_highest = sorted_bids[1]
        else:
            second_highest = sorted_bids[0]
        target = min(my_budget, max(DAILY_SALARY * 0.5, second_highest + 2))
        return target
    else:
        # High HP: exploit high yday bidders by saving budget
        if yesterday_max_bid > DAILY_SALARY * 0.85:
            return min(my_budget, DAILY_SALARY * 0.3)
        else:
            # Competitive: bid just above the minimum yesterday to win cheaply
            return min(my_budget, max(DAILY_SALARY * 0.2, yesterday_min_bid + 1))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Determine target bid: slightly above yesterday's max to win
    target = min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev_bid + 1.0))
    
    # Adjust based on HP urgency
    if my_status['hp'] <= 3:
        # Desperate: bid high to secure water
        target = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5:
        # Moderate urgency, still need water
        target = min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev_bid + 1.5))
    else:
        # Can afford to lowball, just need to outbid yesterday's max slightly
        target = min(my_status['budget'], max(DAILY_SALARY * 0.3, max_prev_bid + 1.0))
    
    # Ensure bid is positive and not over budget
    return max(0.0, min(my_status['budget'], target))
"""
