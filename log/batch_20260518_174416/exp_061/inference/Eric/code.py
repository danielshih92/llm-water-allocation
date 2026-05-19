# ============================================================
# Experiment: exp_061
# Agent: Eric
# Source: exp_061
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    # Count alive opponents
    alive = [o for o in opponents_status.values() if o['alive']]
    num_opp = len(alive)
    # Base bid: survive but conserve
    base = DAILY_SALARY * 0.4
    if my_status['hp'] <= 2:
        base = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 4:
        base = DAILY_SALARY * 0.6
    # Increase if many opponents
    if num_opp > 2:
        base *= 1.2
    # Ensure we can afford
    bid = min(base, my_status['budget'])
    # Lower bound: at least min bid to get water if needed
    if my_status['hp'] < 3 and my_status['budget'] > 0:
        bid = max(bid, 30)
    return int(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Estimate maximum previous bid among alive opponents
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    
    # Base bid: if we need water desperately
    if my_status['hp'] <= 2:
        # Need water urgently, bid slightly above previous max if possible
        bid = max(DAILY_SALARY * 0.9, max_prev_bid + 1)
    else:
        # Conserve budget, bid moderately
        bid = DAILY_SALARY * 0.3
        # If supply is low, increase bid to ensure win
        if supply < 20:
            bid = max(bid, DAILY_SALARY * 0.5)
        # If previous bids were high, we may need to match
        if max_prev_bid > DAILY_SALARY * 0.6:
            bid = max(bid, max_prev_bid + 0.5)
    
    # Cannot exceed budget
    bid = min(bid, my_status['budget'])
    # Cannot bid negative
    bid = max(0, bid)
    return bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Extract previous bid from each opponent's trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])

    high_prev = max(prev_bids) if prev_bids else 0.0

    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # If we are at risk of dying (hp <= 2 or no water for 3+ days), bid very high
    if hp <= 2 or no_water >= 3:
        target = min(budget, DAILY_SALARY * 0.95)
        return max(target, high_prev + 2.0) if budget >= high_prev + 2.0 else budget

    # Otherwise, normal strategy: try to win with a slight premium over previous high
    # But if previous high is too aggressive (above 90% salary), maybe conserve if we are healthy
    if high_prev >= DAILY_SALARY * 0.85:
        if hp > 3:
            # Conservative: bid a moderate amount to save budget
            return min(budget, DAILY_SALARY * 0.45)
        else:
            # Need water, match aggressively
            return min(budget, max(DAILY_SALARY * 0.8, high_prev + 1.0))

    # Standard bid: a bit above previous high, but cap at 70% salary
    base = DAILY_SALARY * 0.55
    bid = max(base, high_prev + 2.0)
    bid = min(bid, DAILY_SALARY * 0.8)
    return min(budget, bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            target = max(DAILY_SALARY * 0.85, max_prev + 2)
        else:
            target = DAILY_SALARY * 0.85
        return min(my_status['budget'], target)

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        target = max(DAILY_SALARY * 0.5, max_prev + 1)
        target = min(target, DAILY_SALARY * 0.9)
    else:
        target = DAILY_SALARY * 0.5
    return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    # Get current day and supply
    day = int(day_context['day'])
    supply = int(day_context['supply'])

    # My state
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Only consider alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Collect previous bids (yesterday) from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Calculate max previous bid among alive opponents
    if prev_bids:
        max_prev_bid = max(prev_bids)
    else:
        max_prev_bid = 0.0

    # Determine bidding aggressiveness based on opponent behavior
    # Alex and Cindy were aggressive (avg > 150), Bob moderate
    # If opponent max previous bid is high, we should underbid to save money
    # But if my hp is low, we must secure water

    # Base bid: conservative
    bid = 0.0

    # If there are no opponents, just bid 40% of salary (safe)
    if not alive_opponents:
        bid = min(budget, DAILY_SALARY * 0.4)
    else:
        # If opponent last bid was very aggressive (above 200), be cautious
        if max_prev_bid > DAILY_SALARY * 1.5:  # >210
            if hp > 4:
                bid = min(budget, DAILY_SALARY * 0.35)  # 49
            else:
                bid = min(budget, DAILY_SALARY * 0.9)  # 126
        elif max_prev_bid > DAILY_SALARY * 0.8:  # >112
            if hp <= 2:
                bid = min(budget, DAILY_SALARY * 1.0)  # 140
            elif hp <= 4:
                bid = min(budget, DAILY_SALARY * 0.7)  # 98
            else:
                bid = min(budget, DAILY_SALARY * 0.5)  # 70
        else:
            # Opponents moderate
            if hp <= 2:
                bid = min(budget, DAILY_SALARY * 0.85)  # 119
            elif hp <= 5:
                bid = min(budget, DAILY_SALARY * 0.6)  # 84
            else:
                bid = min(budget, DAILY_SALARY * 0.4)  # 56

        # Adjust for supply: if supply is low, increase bid slightly
        if supply < 18 and hp <= 3:
            bid = min(budget, bid + 20)

    # Ensure we don't bid more than budget
    final_bid = max(0.0, min(budget, bid))
    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # Collect yesterday's bids from opponents's previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Determine base bid
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        if my_status['hp'] <= 2:
            # Urgent need: outbid by a small margin
            target = min(my_status['budget'], max(DAILY_SALARY * 0.85, max_prev_bid * 1.2))
        else:
            # Slightly above yesterday's max, but not too high
            target = min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev_bid + 2.0))
        # Supply adjustment: if supply low, bid higher
        supply = day_context['supply']
        if supply < WATER_REQ * 2:  # less than 16 units
            target = min(my_status['budget'], max(target, DAILY_SALARY * 0.8))
        return target
    else:
        # No historical bids, moderate
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine highest previous bid among alive opponents
    max_prev_bid = -1
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            bid_amt = prev_trace['bid']
            if bid_amt > max_prev_bid:
                max_prev_bid = bid_amt
    
    # Base bid as fraction of salary, adjusted for supply
    base_bid = DAILY_SALARY * 0.4
    if supply > 20:
        base_bid = DAILY_SALARY * 0.3
    
    # If HP is very low, we must secure water
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    
    # Decide final bid considering opponents
    if max_prev_bid > 0:
        # Beat previous highest by a small margin
        target_bid = max(base_bid, max_prev_bid + 2.0)
    else:
        target_bid = base_bid
    
    # Cap by budget and ensure integer
    final_bid = min(my_budget, target_bid)
    final_bid = int(round(final_bid, 0))
    return max(final_bid, 0)
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
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)
    # Collect yesterday's bids from opponents' previous traces
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Base bid calculation
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If my HP is very low, bid aggressively to secure water
        if hp <= 2 or no_water_days >= 1:
            target = min(budget, max(DAILY_SALARY * 0.9, max_prev_bid + 2.0))
        else:
            target = max_prev_bid + 1.0
        return min(budget, target)
    # No prior info: safe bid
    safe_bid = min(budget, DAILY_SALARY * 0.5)
    if hp <= 2:
        safe_bid = min(budget, DAILY_SALARY * 0.85)
    return safe_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get previous bids of alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid: 40% of salary
    base_bid = DAILY_SALARY * 0.4
    
    # Determine target based on previous bids
    if prev_bids:
        max_prev = max(prev_bids)
        # If someone bid very high, we may still need to match
        target = max(base_bid, max_prev * 1.0)  # just match or undercut?
    else:
        target = base_bid
    
    # Adjust for desperation
    if hp <= 2 or no_water > 0:
        # Need water urgently; bid up to 95% of budget
        desired = min(budget, DAILY_SALARY * 0.95)
        # Ensure we beat the highest opponent's previous aggressive bid
        if prev_bids and max(prev_bids) > DAILY_SALARY * 0.8:
            target = max(target, max(prev_bids) + 1)
        bid = max(target, desired)
    else:
        # Healthy: conserve budget, maybe undercut
        if prev_bids and max(prev_bids) > DAILY_SALARY * 0.7:
            # Opponents are aggressive; bid slightly less to save
            bid = min(budget, max(target * 0.8, DAILY_SALARY * 0.4))
        else:
            bid = min(budget, target)
    
    # Ensure bid is positive and not exceeding budget
    bid = max(0.0, min(budget, bid))
    return bid
"""
