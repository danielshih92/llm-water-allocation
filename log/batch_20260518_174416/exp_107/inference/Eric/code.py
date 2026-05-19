# ============================================================
# Experiment: exp_107
# Agent: Eric
# Source: exp_107
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine base bid: conservative start
    base_bid = min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Look at previous traces if any
    if alive_opponents:
        prev_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
        if prev_bids:
            max_prev = max(prev_bids)
            # If opponents bid aggressively yesterday, conservative today
            if max_prev >= DAILY_SALARY * 0.85:
                if my_status['hp'] > 3:
                    base_bid = min(my_status['budget'], DAILY_SALARY * 0.3)
                else:
                    base_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
            else:
                base_bid = min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev + 1.5))
    
    # Adjust if low hp
    if my_status['hp'] <= 2:
        base_bid = max(base_bid, min(my_status['budget'], DAILY_SALARY * 0.85))
    
    # Ensure bid is integer (convert to int if needed)
    bid = int(base_bid)
    return min(bid, int(my_status['budget']))
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

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev, dict):
            bid = prev.get('bid')
            if bid is not None and bid > 0:
                yesterday_bids.append(bid)

    # Supply factor: lower supply -> higher competition
    supply = day_context['supply']
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Base bid: fraction of salary
    if hp <= 2:
        # Desperate: bid high to get water
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 5:
        # Moderate need
        base_bid = DAILY_SALARY * (0.5 + 0.2 * (1 - supply_ratio))
    else:
        # High HP, can afford to lose
        base_bid = DAILY_SALARY * (0.3 + 0.2 * (1 - supply_ratio))

    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
        if my_status['hp'] > 3:
            # If we have HP, try to undercut slightly
            aggressive_bid = highest_yesterday + 1.0
        else:
            # Need to ensure win: bid above highest
            aggressive_bid = highest_yesterday + 2.0
        # Blend with base bid
        if aggressive_bid > base_bid:
            if hp <= 2:
                final_bid = min(aggressive_bid, DAILY_SALARY * 0.95)
            else:
                final_bid = min(aggressive_bid, DAILY_SALARY * 0.7)
        else:
            final_bid = base_bid
    else:
        # No yesterday data: use base
        final_bid = base_bid

    # Budget constraint and min 0
    final_bid = max(0, min(final_bid, budget))
    # Ensure we don't bid more than we can afford
    final_bid = min(final_bid, budget)
    # Round to 2 decimals to avoid floating issues
    final_bid = round(final_bid, 2)
    return final_bid
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate opponent max bid today based on yesterday and their budget
    estimated_max = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            # Assume aggressive opponents maintain similar bid, conservative may drop
            if opp['budget'] > 200:
                # Cindy-like: high budget, likely to bid high
                est = prev['bid'] * 0.95  # slight reduction as game progresses
            else:
                est = prev['bid'] * 0.85  # more conservative
        else:
            # No trace, assume they bid around salary * 0.5
            est = DAILY_SALARY * 0.5
        if est > estimated_max:
            estimated_max = est

    # Determine if I need water urgently
    if hp <= 2 or no_water_days >= 2:
        needed = True
    elif hp <= 4 and supply < 20:
        needed = True
    else:
        needed = False

    if needed:
        # Need to win: bid slightly above estimated max, but not exceed budget
        bid = min(budget, estimated_max + 2.0)
        # But also ensure I don't overpay if supply high
        if supply > 20:
            bid = min(bid, DAILY_SALARY * 0.7)
        return max(bid, DAILY_SALARY * 0.3)  # floor
    else:
        # Safe: bid low to save money
        base_low = DAILY_SALARY * 0.3
        # If estimated max is very low, we might still win with low bid
        if estimated_max < DAILY_SALARY * 0.4:
            return min(budget, estimated_max + 1.0)
        else:
            return min(budget, base_low)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Collect previous bids from yesterday
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Determine target bid
    if prev_bids:
        median_bid = sorted(prev_bids)[len(prev_bids)//2]
        base_bid = median_bid + 1.5  # slightly above median
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on own HP
    if my_status['hp'] <= 2:
        # Desperate: bid higher
        target = max(base_bid, DAILY_SALARY * 0.9)
    else:
        # Comfortable: bid moderate
        target = min(base_bid, DAILY_SALARY * 0.7)
    
    # Ensure we don't exceed budget and don't bid more than we can afford
    max_bid = my_status['budget']
    bid = min(target, max_bid)
    # Also ensure non-negative
    return max(bid, 0.0)
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
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    num_alive = len(alive_opponents)

    # Calculate water units available (float then int)
    water_units = int(supply // WATER_REQ)

    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Compute average previous bid if any
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0

    # Decide bid
    # Urgency: need water if hp low or no_water_days > 0
    urgent = (hp <= 3) or (no_water_days >= 1)

    if urgent:
        # Must secure water: bid high but not reckless
        target = min(budget, DAILY_SALARY * 0.9)
    else:
        # Conservative: try to win with minimal cost
        if avg_prev_bid > 0:
            # Slightly beat average of previous day
            target = min(budget, max(DAILY_SALARY * 0.3, avg_prev_bid + 1.0))
        else:
            target = min(budget, DAILY_SALARY * 0.5)

    # Ensure we don't exceed budget
    target = min(max(0, target), budget)

    return target
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
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_highest = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            bid = prev['bid']
            if bid is not None and bid > prev_highest:
                prev_highest = bid
    
    if hp <= 2:
        desired = min(budget, DAILY_SALARY * 0.9)
        if prev_highest > desired:
            desired = min(budget, prev_highest + 1)
        return max(0, int(desired))
    elif hp <= 4:
        desired = min(budget, DAILY_SALARY * 0.6)
        if prev_highest > desired:
            desired = min(budget, prev_highest + 1)
        return max(0, int(desired))
    else:
        if supply < 18:
            desired = min(budget, DAILY_SALARY * 0.4)
        else:
            desired
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday's bids
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine baseline from yesterday's competition
    if prev_bids:
        highest_prev = max(prev_bids)
    else:
        highest_prev = 0.0

    # Adjust based on supply
    supply = day_context['supply']
    supply_factor = 1.0
    if supply < 20:
        supply_factor = 1.3
    else:
        supply_factor = 0.9

    # Adjust based on our hp
    hp = my_status['hp']
    if hp <= 2:
        # critical: bid high to ensure water
        bid_target = DAILY_SALARY * 0.95
    elif hp <= 5:
        # moderate risk: bid to beat highest_prev if needed
        if highest_prev >= DAILY_SALARY * 0.85:
            bid_target = highest_prev + 1.5
        else:
            bid_target = max(DAILY_SALARY * 0.6, highest_prev + 1.0)
    else:
        # healthy: can be conservative
        if highest_prev >= DAILY_SALARY * 0.85:
            bid_target = DAILY_SALARY * 0.35
        else:
            bid_target = max(DAILY_SALARY * 0.4, highest_prev + 0.5)

    # Apply supply factor and cap by budget
    bid = bid_target * supply_factor
    bid = min(bid, my_status['budget'])
    bid = max(bid, 1.0)  # always bid at least 1
    return bid
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
    
    # Gather yesterday's bids from alive opponents
    bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bids.append(prev['bid'])
    
    # Determine base bid
    if bids:
        max_prev = max(bids)
        # Slightly beat the highest previous bid
        base = max_prev + 1.0
    else:
        base = DAILY_SALARY * 0.5
    
    # Adjust for urgency
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    
    urgency = 0
    if no_water > 0:
        urgency = 2
    elif hp <= 3:
        urgency = 1
    
    if urgency == 2:
        # Must win water
        bid = min(budget, DAILY_SALARY * 0.95)
    elif urgency == 1:
        # High priority
        bid = min(budget, max(base, DAILY_SALARY * 0.7))
    else:
        # Conservative
        bid = min(budget, base, DAILY_SALARY * 0.75)
    
    # Ensure at least a minimal bid if desperate
    if hp <= 1:
        bid = min(budget, DAILY_SALARY * 0.98)
    
    # Cap by budget
    return max(1.0, min(budget, bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    max_prev = max(prev_bids) if prev_bids else 0.0

    # Determine urgency based on hp and no_water_days
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']

    if no_water >= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 2:
        base_bid = DAILY_SALARY * 0.8
    elif hp <= 4:
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    max_prev_bid = 0
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > max_prev_bid:
                max_prev_bid = bid
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        target = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        if max_prev_bid > 90:
            target = min(budget, 70)
        else:
            target = min(budget, max(50, max_prev_bid + 5))
    else:
        if max_prev_bid > 100:
            target = min(budget, 65)
        else:
            target = min(budget, max(40, max_prev_bid + 3))
    target = max(0, target)
    return target
"""
