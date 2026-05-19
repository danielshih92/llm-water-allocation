# ============================================================
# Experiment: exp_091
# Agent: Eric
# Source: exp_091
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Base bid: 40% of salary
    base_bid = DAILY_SALARY * 0.4
    # Increase if low health
    if my_status['hp'] < 3:
        base_bid = DAILY_SALARY * 0.75
    # Increase if late in episode
    if day_context['day'] >= 8:
        base_bid = DAILY_SALARY * 0.85
    # Ensure we don't exceed budget
    bid = min(my_status['budget'], base_bid)
    # Ensure bid is at least 1 if we have budget
    bid = max(1, int(bid))
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    nodays = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    n_alive = len(alive_opponents)

    # Base bid fraction
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Determine yesterday's highest bid among alive opponents
    highest_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = prev['bid']
            if bid_val > highest_prev_bid:
                highest_prev_bid = bid_val
    
    # Base bid proportional to our water need relative to supply
    need_ratio = WATER_REQ / supply
    base_bid = DAILY_SALARY * need_ratio
    
    # Desperation adjustment
    if no_water_days > 0:
        # Need water urgently, outbid highest if possible
        target_bid = max(base_bid * 1.5, highest_prev_bid + 1)
    elif hp <= 2:
        target_bid = max(base_bid * 1.2, highest_prev_bid + 0.5)
    else:
        target_bid = base_bid
        # If we have budget and need to maintain water, slightly above base
        if highest_prev_bid > base_bid and budget > highest_prev_bid:
            target_bid = highest_prev_bid + 0.1
        else:
            target_bid = base_bid
    
    # Ensure not over budget
    bid = min(budget, target_bid)
    # Ensure positive
    bid = max(0, bid)
    # Round to avoid weird floats (optional)
    bid = round(bid, 2)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']

    # Get yesterday's bids from opponents
    prev_bids = []
    for opp in opponents_status.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    max_prev = max(prev_bids) if prev_bids else 0

    # Baseline bid: 70% of salary
    base_bid = DAILY_SALARY * 0.7

    # If any opponent bid very high yesterday, they may continue aggressive
    if max_prev > DAILY_SALARY * 0.85:
        base_bid = DAILY_SALARY *
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    # Extract current state
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Determine alive opponents and their last bids from previous_trace
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    last_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            last_bids.append(trace['bid'])

    # Compute base bid as a fraction of daily salary
    # Conservative start
    bid = DAILY_SALARY * 0.4

    # If no water days or low health, become aggressive
    if no_water_days > 0 or hp <= 2:
        # Need water desperately
        if last_bids:
            # Beat the highest previous bid by a small margin
            min_bid = max(last_bids) + 1.0
        else:
            min_bid = DAILY_SALARY * 0.8
        bid = max(bid, min_bid)
    else:
        # Healthy, can adapt based on supply
        # Supply ranges 15-25, so define thresholds
        if supply <= 18:
            # Tight supply, bid competitively
            if last_bids:
                # Slightly beat highest previous bid
                target = max(last_bids) + 2.0
            else:
                target = DAILY_SALARY * 0.7
            bid = max(bid, target)
        elif supply >= 22:
            # Abundant supply, bid low to save money
            bid = DAILY_SALARY * 0.3
        else:
            # Moderate supply, use intermediate bid
            if last_bids:
                # Use average of previous bids
                avg_last = sum(last_bids) / len(last_bids)
                target = avg_last * 0.9
            else:
                target = DAILY_SALARY * 0.5
            bid = min(bid, target)  # we want to be lower than average? Actually we want to be safe, but stay moderate
            # Let's set bid as target if higher than base
            bid = max(bid, target)

    # Ensure we never exceed budget and stay within reasonable bounds
    bid = min(bid, budget)
    bid = max(bid, 0)
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Estimate opponent aggressiveness from previous trace (if exists)
    aggressive_count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev['bid'] > DAILY_SALARY * 0.8:
            aggressive_count += 1

    # Base aggressive escalation threshold
    if aggressive_count >= 2:
        # Need to be more competitive
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.5

    # Adjust based on supply tightness
    supply_ratio = supply / 25.0  # 0.6 to 1.0
    if supply_ratio < 0.7:
        # Low supply: bid higher
        base_bid *= 1.3
    elif supply_ratio > 0.85:
        base_bid *= 0.85

    # Adjust based on HP and no_water_days
    if hp <= 2 or no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.65)

    # Late game escalation (last 3 days)
    if day >= 8:
        if hp < 6:
            base_bid = DAILY_SALARY * 0.95
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.85)

    # Ensure bid is within budget and at least minimum sensible
    bid = max(10, min(budget, base_bid))
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
    supply = int(day_context['supply'])  # ensure integer
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        # No competition, bid minimal
        return min(budget, DAILY_SALARY * 0.3)

    # Extract previous day bids from opponents (yesterday)
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    # Base bid strategy
    # If we have no water for multiple days, we must win at high cost
    urgency = 0
    if no_water_days > 0:
        urgency = 1.0 + 0.2 * no_water_days  # scale up
    if hp <= 2:
        urgency = 2.0

    # Compute expected opponent bid: use max of previous bids or default to 30% of salary
    if prev_bids:
        expected_opp_bid = max(prev_bids)
    else:
        expected_opp_bid = DAILY_SALARY * 0.3

    # Adjust for supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # When supply is low, opponents bid more aggressively
    if supply_ratio < 0.5:
        # scarce water -> increase expected
        expected_opp_bid *= (1.0 + (0.5 - supply_ratio))

    # Our desired bid: beat expected by a margin but cap by urgency and budget
    desired_bid = expected_opp_bid + 2.0  # small increment
    if urgency > 1.5:
        desired_bid = min(budget, max(desired_bid, DAILY_SALARY * 0.8))
    else:
        desired_bid = min(budget, max(desired_bid, DAILY_SALARY * 0.4))

    # Ensure we don't bid more than budget
    bid = min(budget, desired_bid)

    # Also never bid negative
    bid = max(0.0, bid)

    return bid
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
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    healthy = hp > 3
    
    # Get previous traces from alive opponents
    alive_opponents = [opp for opp in opponents_status.values() if opp['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Emergency if no water days > 1 or hp <= 0
    if no_water_days > 1 or hp <= 0:
        base = DAILY_SALARY * 0.95
    elif hp <= 2:
        base = DAILY_SALARY * 0.8
    elif healthy:
        base = DAILY_SALARY * 0.5
    else:
        base = DAILY_SALARY * 0.6
    
    # Adjust based on opponents' previous max bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If they were very aggressive, we might need to match or exceed
        if max_prev > DAILY_SALARY * 0.85:
            if hp <= 2:
                bid = max(base, max_prev * 0.9)
            else:
                bid = max(base, max_prev * 0.75)
        else:
            bid = max(base, max_prev * 1.1)
    else:
        bid = base
    
    # Cap at budget and ensure not below 0
    bid = max(0, min(budget, bid))
    
    # On last day or high HP, maybe bid less
    if day >= 9 and hp > 5:
        bid = min(bid, DAILY_SALARY * 0.3)
    
    return int(bid)
"""
