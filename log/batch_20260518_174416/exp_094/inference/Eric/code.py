# ============================================================
# Experiment: exp_094
# Agent: Eric
# Source: exp_094
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], SALARY * 0.2)
    hp = my_status['hp']
    budget = my_status['budget']
    days_left = 10 - day_context['day']
    min_bid = SALARY * 0.1
    if hp <= 2:
        bid = SALARY * 0.85
    elif hp <= 4:
        bid = SALARY * 0.55
    else:
        bid = SALARY * 0.35
    if days_left <= 2:
        bid = max(bid, SALARY * 0.8)
    bid = max(min_bid, min(budget, bid))
    return float(bid)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Gather previous bids from yesterday's trace (last day of previous metaround)
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Determine competition level
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0
        avg_prev = 0
    
    # Supply scarcity factor: lower supply -> higher need to compete
    # Number of winners estimate: supply // WATER_REQ, ensure integer index
    num_winners = int(supply) // WATER_REQ
    scarcity = 1.5 - num_winners / 3.0  # roughly 1.5 when 1 winner, 0.5 when 3 winners
    scarcity = max(0.3, min(1.5, scarcity))
    
    # Base bid: average of previous high bids adjusted by scarcity
    target = max(DAILY_SALARY * 0.4, avg_prev * scarcity)
    
    # Adjust based on HP
    if hp <= 2:
        # Desperate: bid high to ensure water
        bid = max(target, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # Moderate health: need to bid competitively
        bid = max(target, DAILY_SALARY * 0.6)
    else:
        # Healthy: try to save budget
        bid = max(target, DAILY_SALARY * 0.4)
    
    # If we have a lot of budget, we can be more aggressive to secure wins
    if budget > DAILY_SALARY * 3:
        bid = max(bid, DAILY_SALARY * 0.8)
    
    # Ensure we don't overbid beyond budget or underbid too low
    bid = min(budget, bid)
    bid = max(1, bid)
    
    # Final small random element to avoid predictability (but within bounds)
    # Use hash of day to add slight variation
    variation = (day * 7) % 10 - 5  # -5 to +4
    bid += variation
    bid = min(budget, max(1, bid))
    return int(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Gather yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Estimate highest bid from yesterday
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0
    
    # My desperation: low HP -> need water
    very_low_hp = hp <= 2
    low_hp = hp <= 4
    
    # Water needed per day: WATER_REQ, supply range 15-25 -> number of winners = supply // WATER_REQ = 1 or 2 or 3 (since 15//8=1, 19//8=2, 25//8=3)
    # Convert supply to int for division
    supply_int = int(supply)
    winners = supply_int // WATER_REQ  # integer division on int yields int
    
    # Base bid: try to win if needed
    if very_low_hp:
        # Bid aggressively to secure water
        target_bid = min(budget, max(DAILY_SALARY * 0.95, highest_yesterday + 2))
    elif low_hp and winners < 2:
        # Low supply, need water
        target_bid = min(budget, max(DAILY_SALARY * 0.8, highest_yesterday + 1))
    else:
        # Conserve budget
        if highest_yesterday > DAILY_SALARY * 0.8:
            # Opponents bidding high, stay low to save
            target_bid = min(budget, DAILY_SALARY * 0.3)
        else:
            target_bid = min(budget, DAILY_SALARY * 0.5)
    
    # Ensure not negative
    return max(0, target_bid)
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
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        # Sort and find median
        sorted_bids = sorted(yesterday_bids)
        mid_idx = int(len(sorted_bids) // 2)
        median_bid = sorted_bids[mid_idx]
        max_bid = max(yesterday_bids)
        
        # Adjust based on own hp
        hp = my_status['hp']
        budget = my_status['budget']
        no_water = my_status['no_water_days']
        
        if hp <= 2 or no_water >= 2:
            # Urgent need, bid high but not more than budget
            target = max(DAILY_SALARY * 0.9, max_bid + 1.0)
            return min(budget, target)
        elif hp <= 4:
            # Moderate need, bid around median + small buffer
            target = median_bid + 1.5
            return min(budget, target)
        else:
            # Save budget, undercut median
            target = max(DAILY_SALARY * 0.3, median_bid - 2.0)
            return min(budget, target)
    else:
        # No trace, safe bid
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    max_prev = max(prev_bids) if prev_bids else 0
    
    # Base bid strategy
    if hp <= 2:
        base = min(DAILY_SALARY * 0.9, max_prev + 2)
    elif hp <= 5:
        base = min(DAILY_SALARY * 0.65, max_prev + 1.5)
    else:
        base = min(DAILY_SALARY * 0.4, max_prev + 1)
    
    # Adjust for supply (lower supply = higher competition)
    if supply <= 16:
        base *= 1.2
    elif supply >= 22:
        base *= 0.8
    
    # Ensure bid is affordable for water requirement
    max_affordable = budget / WATER_REQ if budget > 0 else 0
    final_bid = min(base, max_affordable, DAILY_SALARY)
    
    return max(final_bid, 1)  # at least 1 to participate
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
    return 15.0
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    budget = my_status['budget']
    hp = my_status['hp']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0
    if hp <= 2:
        target = min(budget, DAILY_SALARY * 0.9)
    else:
        if max_prev_bid > DAILY_SALARY * 0.85:
            target = min(budget, max_prev_bid + 5)
        else:
            target = min(budget, DAILY_SALARY * 0.45)
    return max(0, target)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate if yesterday's highest bid was aggressive
    aggressive_yesterday = False
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        if max_prev_bid >= DAILY_SALARY * 0.85:
            aggressive_yesterday = True

    # Base bid: moderate
    base_bid = DAILY_SALARY * 0.5

    # Adjust for HP
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.75

    # Adjust for supply scarcity
    supply_ratio = supply / MAX_SUPPLY
    if supply_ratio < 0.7:
        base_bid *= 1.2
    elif supply_ratio > 0.9:
        base_bid *= 0.85

    # Respond to yesterday's aggression: if they bid high, they may be low on budget; we can undercut
    if aggressive_yesterday:
        # They spent a lot, so might be weak today; we can bid lower if we don't need water
        if hp > 4:
            base_bid = min(base_bid, DAILY_SALARY * 0.35)
    else:
        # They saved budget, may outbid us; increase bid if we need water
        if hp <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    final_bid = min(budget, base_bid)
    # Ensure we don't bid more than we have
    final_bid = min(budget, max(0, final_bid))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's max bid from opponents with valid trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Determine urgency
    urgent = (no_water_days > 0) or (hp <= 2)
    
    # Base bid calculation
    if urgent:
        # Need water badly, outbid max_prev_bid by a margin
        target = max(DAILY_SALARY * 0.8, max_prev_bid + 5)
        # Increase if supply is low
        if supply <= 18:
            target = max(target, DAILY_SALARY * 0.95)
    else:
        # Healthy: try to conserve
        target = max(DAILY_SALARY * 0.4, max_prev_bid + 2)
        # Cap to avoid overbidding
        target = min(target, DAILY_SALARY * 0.7)
        # If supply low, be slightly more aggressive
        if supply <= 18:
            target = max(target, DAILY_SALARY * 0.65)
    
    # Ensure we never bid more than budget
    bid = min(budget, target)
    # Floor at 0
    bid = max(bid, 0.0)
    return bid
"""
