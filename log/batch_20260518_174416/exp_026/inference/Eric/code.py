# ============================================================
# Experiment: exp_026
# Agent: Eric
# Source: exp_026
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # No previous trace data, use generic strategy
    if hp <= 2:
        # desperate
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # moderately thirsty
        bid = min(budget, DAILY_SALARY * 0.6)
    else:
        # healthy, conserve money
        bid = min(budget, DAILY_SALARY * 0.35)
    
    # Increase bid on later days (last 3 days)
    if day >= 7:
        bid = min(budget, bid * 1.2)
    
    # Ensure bid is at least something if we have budget
    if budget > 0 and bid < 1:
        bid = 1.0
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Determine yesterday's max bid among alive opponents
    max_prev_bid = None
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('status') != 'error':
            bid = prev['bid']
            if max_prev_bid is None or bid > max_prev_bid:
                max_prev_bid = bid
    
    # Base strategy based on current hp
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Urgency levels
    if hp <= 2:
        # Critical need water
        if max_prev_bid is not None:
            target = max_prev_bid + 5.0
        else:
            target = DAILY_SALARY * 0.95  # 133
        return min(budget, target)
    elif hp <= 5:
        # Moderate need
        if max_prev_bid is not None:
            target = max_prev_bid + 2.5
        else:
            target = DAILY_SALARY * 0.85  # 119
        return min(budget, target)
    else:
        # Healthy, conserve
        if max_prev_bid is not None:
            target = max_prev_bid - 2.5
            # Ensure positive and reasonable
            if target < DAILY_SALARY * 0.5:
                target = DAILY_SALARY * 0.55
        else:
            target = DAILY_SALARY * 0.65  # 91
        return min(budget, max(1.0, target))
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
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate market price based on supply and basic need
    fair_price = DAILY_SALARY * (WATER_REQ / supply) * 0.9

    # Base bid from yesterday's competition
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        # Want to slightly exceed yesterday's average, but not too high
        target = max(fair_price, avg_yesterday + 1.0)
    else:
        target = fair_price

    # Adjust based on urgency
    if hp <= 3 or no_water_days >= 1:
        # Desperate: need water
        bid = max(target, DAILY_SALARY * 0.85)
        if yesterday_bids:
            bid = max(bid, max_yesterday + 0.5)
    elif hp <= 5:
        # Moderate urgency
        bid = max(target, DAILY_SALARY * 0.6)
    else:
        # Healthy: can be conservative
        bid = min(target, DAILY_SALARY * 0.5)

    # Ensure we don't overextend budget
    bid = min(bid, budget, DAILY_SALARY * 0.95)
    # Ensure positive bid
    bid = max(bid, 1.0)

    return int(bid)
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine aggressiveness based on highest yesterday bid
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
    else:
        highest_yesterday = 0
    
    # Base bid: if low hp or desperate, bid high
    if hp <= 2 or no_water_days >= 1:
        desired_bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 5:
        desired_bid = min(budget, max(DAILY_SALARY * 0.7, highest_yesterday + 2))
    else:
        # High hp, try to undercut
        if highest_yesterday > 0:
            desired_bid = min(budget, max(DAILY_SALARY * 0.4, highest_yesterday - 3))
        else:
            desired_bid = min(budget, DAILY_SALARY * 0.5)
    
    # Ensure we don't bid more than budget or daily salary
    final_bid = min(budget, max(0, desired_bid))
    return int(final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    prev_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    if my_hp <= 2 or no_water_days >= 1:
        base = DAILY_SALARY * 0.8
    else:
        base = DAILY_SALARY * 0.5

    if prev_bids:
        max_prev = max(prev_bids)
        target = max(base, max_prev + 1)
    else:
        target = base

    target = min(target, my_budget)
    target = max(target, 0)

    if supply < 18:
        target = max(target, DAILY_SALARY * 0.7)

    return target
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Extract key info
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get previous bid from each opponent's trace
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine reference bid
    if prev_bids:
        max_prev = max(prev_bids)
    else:
        max_prev = DAILY_SALARY * 0.6
    
    # Base bid: slightly above max_prev, but consider supply
    bid_raw = max_prev + 1.5
    
    # Adjust based on HP
    if hp <= 2:
        # Urgent need water
        bid_raw = max(bid_raw, DAILY_SALARY * 0.9)
    elif hp <= 4:
        bid_raw = max(bid_raw, DAILY_SALARY * 0.75)
    else:
        # Can be more conservative
        bid_raw = min(bid_raw, DAILY_SALARY * 0.7)
    
    # Cap by budget and reasonable maximum (90% of salary)
    max_allowed = min(budget, DAILY_SALARY * 0.9)
    bid = min(bid_raw, max_allowed)
    
    # Ensure non-negative and within bounds
    bid = max(bid, 0)
    
    # Round to 2 decimals for sanity
    return round(bid, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    
    # Estimate needed bid: slightly above average of yesterday's high bids
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        # Alex and Cindy were around 104, so target slightly above
        target = avg_prev + 2.0
    else:
        target = DAILY_SALARY * 0.5
    
    # Adjust based on HP and day
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.7)
    
    # Late days: be more aggressive
    if day >= 8:
        target = max(target, DAILY_SALARY * 0.8)
    
    # Ensure we don't overspend budget
    bid = min(budget, target)
    # At minimum, bid 1 to avoid disqualification
    bid = max(1, bid)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)
    
    # Check yesterday's highest bid from alive opponents
    highest_yesterday_bid = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > highest_yesterday_bid:
                highest_yesterday_bid = bid
    
    # Critical HP: need water desperately
    if hp <= 2:
        # bid safely above any known max (max seen was 94.27, plus margin)
        target = max(95, highest_yesterday_bid + 5)
        return min(budget, target)
    
    # Healthy: try to save budget
    # If supply is abundant, bid low
    if supply >= 20:
        return min(budget, 30)
    
    # Medium supply: bid just enough to survive
    # If yesterday's highest bid was high, opponent may be aggressive
    if highest_yesterday_bid > 80:
        return min(budget, highest_yesterday_bid + 3)
    
    # Otherwise safe low bid
    return min(budget, 40)
"""
