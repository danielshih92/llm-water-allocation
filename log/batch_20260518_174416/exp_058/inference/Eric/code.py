# ============================================================
# Experiment: exp_058
# Agent: Eric
# Source: exp_058
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = [o for o in opponents_status.values() if o['alive']]

    # Get yesterday's highest bid from alive opponents
    yesterday_high = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_high = max(yesterday_high, prev['bid'])

    # Determine desperation
    desperate = (hp <= 2) or (no_water_days >= 2)

    # Base bid calculation
    if desperate:
        bid = min(budget, DAILY_SALARY * 0.95)
    else:
        # Conservative against yesterday's highest
        if yesterday_high > 0:
            # Outbid by a small margin, but don't overpay
            target = max(DAILY_SALARY * 0.45, yesterday_high + 3)
        else:
            target = DAILY_SALARY * 0.45
        bid = min(budget, target)

    # Ensure bid is not too low if we really need water (e.g., low HP)
    if hp <= 3 and no_water_days >= 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.75))

    # Floor to 0, no negative
    bid = max(0, bid)
    # Ensure return is float or int? Game expects numeric.
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Use yesterday's meta-round averages as prior knowledge
    avg_bids = {'Alex': 45.22, 'Bob': 57.57, 'Cindy': 64.97, 'David': 53.6}
    # Combine with previous_trace if available
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            avg_bids[opp_id] = prev['bid']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # Compute max expected bid from opponents
    expected_bids = [avg_bids.get(opp_id, DAILY_SALARY * 0.6) for opp_id in opponents_status if opponents_status[opp_id]['alive']]
    max_expected = max(expected_bids) if expected_bids else 0
    # My target bid: slightly above max expected, but moderate
    target = max(max_expected + 2, DAILY_SALARY * 0.5)
    # Adjust if my HP is low
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    # Ensure we don't overspend budget
    bid = min(my_status['budget'], target)
    # Ensure positive
    return max(0, bid)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive'] and opp.get('previous_trace'):
            bid = opp['previous_trace'].get('bid')
            if bid is not None:
                yesterday_bids.append(bid)
    # Determine base bid from previous max aggressive opponent
    if yesterday_bids:
        max_prev = max(yesterday_bids)
    else:
        max_prev = 0.0
    # Adjust for supply: if supply high, we can bid lower
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    if hp <= 3:
        # Need water urgently, guarantee acquiring it
        target = max(DAILY_SALARY * 0.8, max_prev + 5.0)
    elif hp <= 6:
        # Moderate need, aim slightly above average of previous
        target = (max_prev + DAILY_SALARY * 0.6) * 0.8
    else:
        # Can skip, bid very low to save
        target = DAILY_SALARY * 0.2 * (1.0 - supply_factor)
    # Ensure we do not exceed budget and stay reasonable
    bid = min(budget, max(0.0, target))
    # Special case: first day, no previous traces
    if day == 1:
        # Be conservative, bid a low percentage of salary
        bid = min(budget, DAILY_SALARY * 0.4)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from previous_trace if available
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace:
            prev_bids.append(trace['bid'])
    
    # Base bid: 70% of daily salary
    base_bid = DAILY_SALARY * 0.7
    
    # Adjust based on my hunger and HP
    if my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.9
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    
    # If there are previous bids from top opponent, outbid slightly
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > base_bid:
            base_bid = max_prev + 1.5
    
    # Ensure we don't exceed budget
    max_possible = my_status['budget']
    bid = min(base_bid, max_possible)
    
    # Guarantee minimal bid to avoid penalty if budget low
    if bid < 0.1:
        bid = 0.1
    return bid
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
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Unpack
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Alive opponents only
    alive_opps = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Determine yesterday's highest bid among alive opponents
    highest_prev = 0
    for opp in alive_opps.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            bid_val = trace['bid']
            if bid_val > highest_prev:
                highest_prev = bid_val
    
    # Safety threshold based on HP and no_water_days
    if hp <= 2 or no_water_days >= 2:
        # Need water urgently
        safe_bid = min(budget, DAILY_SALARY * 0.9)
        # If yesterday's highest is high, match it
        if highest_prev >= DAILY_SALARY * 0.7:
            return min(budget, max(safe_bid, highest_prev + 2.0))
        return safe_bid
    
    # Healthy: moderate bidding
    base_bid = DAILY_SALARY * 0.55  # ~77
    # If supply is low, increase bid slightly
    if supply < 18:
        base_bid = DAILY_SALARY * 0.7  # ~98
    # If yesterday's highest was very high (aggressive), we need to match to win
    if highest_prev > DAILY_SALARY * 0.8:
        # Compete but not overpay
        needed = max(base_bid, highest_prev + 1.0)
        return min(budget, min(needed, DAILY_SALARY * 0.85))
    
    return min(budget, base_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine target bid
    if no_water > 0 or hp <= 2:
        # Desperate: bid high to secure water
        if prev_bids:
            highest_prev = max(prev_bids)
            return min(budget, max(DAILY_SALARY * 0.9, highest_prev + 2.0))
        return min(budget, DAILY_SALARY * 0.9)
    else:
        # Normal: try to undercut or match
        if prev_bids:
            highest_prev = max(prev_bids)
            # Small increment to win if needed
            return min(budget, max(DAILY_SALARY * 0.3, highest_prev + 1.5))
        return min(budget, DAILY_SALARY * 0.5)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
    else:
        highest_prev = 0
    
    # Danger threshold: if highest previous bid is very high or HP critical
    high_prev = highest_prev >= DAILY_SALARY * 0.8
    low_hp = my_hp <= 3
    
    if low_hp:
        # Need water desperately
        bid = min(my_budget, highest_prev + 5.0)
        bid = max(bid, DAILY_SALARY * 0.7)
    elif high_prev:
        # Competition was fierce, match or slightly exceed
        if my_hp > 5:
            bid = min(my_budget, DAILY_SALARY * 0.45)
        else:
            bid = min(my_budget, highest_prev + 2.0)
    else:
        # Calm situation, bid conservatively but ensure water if supply low
        base_bid = DAILY_SALARY * 0.35
        if supply <= 18:
            base_bid = DAILY_SALARY * 0.5
        bid = min(my_budget, base_bid)
    
    # Ensure bid is within budget and non-negative
    bid = max(0.0, min(my_budget, bid))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    alive_opps = {k:v for k,v in opponents_status.items() if v['alive']}
    yesterday_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Emergency if low hp or skipped water
    if hp <= 2 or no_water >= 1:
        target = min(budget, DAILY_SALARY * 0.95)
    else:
        # Base on yesterday's max and supply tightness
        supply_ratio = supply / 25.0
        if supply_ratio > 0.7:
            target = max(DAILY_SALARY * 0.3, min(budget, max_yesterday + 2.0))
        else:
            target = max(DAILY_SALARY * 0.5, min(budget, max_yesterday + 5.0))
    
    bid = int(min(budget, target))
    return max(0, bid)
"""
