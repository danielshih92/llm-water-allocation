# ============================================================
# Experiment: exp_013
# Agent: Eric
# Source: exp_013
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    # Determine baseline bid
    if my_status['hp'] <= 2 and my_status['no_water_days'] >= 1:
        # desperate: bid high to ensure water
        base = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        # moderate need
        base = min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        # comfortable: low bid to save money
        base = min(my_status['budget'], DAILY_SALARY * 0.4)
    # Adjust based on opponent yesterday maximum
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponent bid high yesterday, they may do similar today
        # Slightly outbid if we need water, else undercut
        if max_prev >= DAILY_SALARY * 0.85 and (my_status['hp'] <= 4 or my_status['no_water_days'] > 1):
            # opponent aggressive, we need water: bid just over their high
            bid = min(my_status['budget'], max_prev + 0.5)
        elif max_prev >= DAILY_SALARY * 0.7:
            # moderate pressure
            bid = min(my_status['budget'], max(base, max_prev * 0.9))
        else:
            # opponent low: we can go lower
            bid = min(my_status['budget'], max(base, DAILY_SALARY * 0.35))
    else:
        # no trace, play safe
        bid = base
    # Never bid more than budget, enforce positivity
    bid = max(0, min(my_status['budget'], bid))
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

    supply = int(day_context['supply'])
    day = int(day_context['day'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], int(DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        if max_prev_bid > DAILY_SALARY * 0.85:
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    # Get only alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
    else:
        avg_prev = 0
        max_prev = 0
    
    # Base bid: slightly above average to beat weaker opponents
    base_bid = avg_prev * 1.1
    
    # Adjust for supply: if supply is abundant, we can bid lower
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # More supply -> lower bid
    supply_factor = 1 - 0.3 * supply_ratio
    
    # Adjust for health: low HP -> higher urgency
    if my_hp <= 2:
        urgency = 1.3
    elif my_hp <= 5:
        urgency = 1.1
    else:
        urgency = 0.9
    
    # Also consider if any opponent had very high bid yesterday (Cindy)
    # If so, we lower our bid to avoid overbidding if we don't need to
    if max_prev >= DAILY_SALARY * 0.8 and my_hp > 3:
        # Conservative: bid just enough to secure water if supply allows
        target_bid = min(base_bid * 0.8, DAILY_SALARY * 0.5)
    else:
        target_bid = base_bid * urgency * supply_factor
    
    # Ensure bid is at least a minimal amount if we need water
    if my_hp <= 2 or my_status['no_water_days'] > 0:
        target_bid = max(target_bid, DAILY_SALARY * 0.4)
    
    # Constrain by budget
    bid = min(my_budget, target_bid)
    # Also ensure bid is non-negative
    bid = max(0, bid)
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

    supply = int(day_context['supply'])  # ensure int
    day = int(day_context['day'])

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Opponents alive
    alive_opp = [o for o in opponents_status.values() if o['alive']]

    # Previous traces
    prev_bids = []
    for opp in alive_opp:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    # Emergency: need water badly
    if no_water_days >= 2 or hp <= 2:
        # bid up to 90% of budget, but not more than DAILY_SALARY * 1.5
        return min(budget, DAILY_SALARY * 0.9)

    # Very high pressure from yesterday
    if prev_bids:
        max_prev = max(prev_bids)
        # If highest previous bid is very high (Cindy-like)
        if max_prev >= DAILY_SALARY * 0.8:
            # Conserve: bid moderate unless desperate
            return min(budget, DAILY_SALARY * 0.35)
        else:
            # Slightly above previous max to secure water
            return min(budget, max(DAILY_SALARY * 0.4, max_prev + 2.0))

    # Default: bid based on supply and health
    # Low supply -> need to be more aggressive
    if supply < 18:
        base = DAILY_SALARY * 0.6
    else:
        base = DAILY_SALARY * 0.4
    return min(budget, base)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    
    # Get yesterday's highest bid from alive opponents
    highest_prev_bid = 0.0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                if prev['bid'] > highest_prev_bid:
                    highest_prev_bid = prev['bid']
    
    # Base bid: slightly above highest previous, or a safe default
    if highest_prev_bid > 0:
        bid = highest_prev_bid + 1.5
    else:
        bid = 0.55 * DAILY_SALARY
    
    # Adjust for HP urgency
    if my_status['hp'] <= 2:
        bid = max(bid, 0.9 * DAILY_SALARY)
    elif my_status['hp'] <= 5:
        bid = max(bid, 0.7 * DAILY_SALARY)
    
    # Cap at budget and daily salary
    bid = min(bid, my_status['budget'], DAILY_SALARY)
    
    # Ensure minimum meaningful bid
    bid = max(bid, 1.0)
    
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev = max(prev_bids) if prev_bids else 0.0
    urgency = (hp <= 2) or (no_water_days > 0)
    if urgency:
        target_bid = max(DAILY_SALARY * 0.9, max_prev + 1.0)
        bid = min(budget, target_bid)
    else:
        if max_prev > DAILY_SALARY * 0.8:
            bid = min(budget, DAILY_SALARY * 0.6)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
    if not alive_opponents:
        bid = min(budget, DAILY_SALARY * 0.4)
    return max(bid, 0.0)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Get alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Determine urgency
    if hp <= 2 or no_water_days >= 1:
        # Need water badly; bid high but within budget and 90% salary
        target_bid = min(budget, DAILY_SALARY * 0.9)
    else:
        # Healthy: use conservative baseline, possibly adjusted by yesterday's max
        base_bid = DAILY_SALARY * 0.4
        if max_yesterday_bid > 0:
            # If yesterday was very high, bid moderately above baseline to stay competitive
            if max_yesterday_bid > DAILY_SALARY * 0.7:
                target_bid = min(budget, max(base_bid, DAILY_SALARY * 0.5))
            else:
                target_bid = min(budget, max(base_bid, max_yesterday_bid * 0.8))
        else:
            target_bid = min(budget, base_bid)
    
    # Ensure we don't bid more than budget
    bid = min(budget, target_bid)
    # Also ensure at least 0
    bid = max(0, bid)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
    else:
        max_yesterday = 0
        avg_yesterday = 0

    urgent = (hp <= 2) or (no_water >= 1)

    if urgent:
        # Need water - bid aggressively to outbid Cindy's typical high bid
        target = max(DAILY_SALARY * 0.85, max_yesterday + 5)
        bid = min(budget, target)
    else:
        # Not urgent - try to save money
        if avg_yesterday > 0:
            # If previous average was high, still bid low but not too low
            target = max(DAILY_SALARY * 0.35, avg_yesterday * 0.6)
        else:
            target = DAILY_SALARY * 0.35
        bid = min(budget, target)

    # Ensure bid is non-negative
    bid = max(0, bid)
    return bid
"""
