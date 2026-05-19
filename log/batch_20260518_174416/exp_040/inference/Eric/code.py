# ============================================================
# Experiment: exp_040
# Agent: Eric
# Source: exp_040
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Default bid if no information
    if hp <= 2:
        # Desperate: bid high to get water
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # Moderate risk: bid enough to likely win if needed
        bid = min(budget, DAILY_SALARY * 0.6)
    else:
        # Healthy: bid low to conserve budget
        bid = min(budget, DAILY_SALARY * 0.3)
    
    # Ensure bid is within budget and non-negative
    bid = max(0, min(budget, bid))
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
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Base bid on my HP and budget
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Determine target bid
    if not prev_bids:
        # No prior info, moderate bid
        if hp <= 2:
            target = min(budget, DAILY_SALARY * 0.9)
        else:
            target = min(budget, DAILY_SALARY * 0.6)
    else:
        max_prev = max(prev_bids)
        min_prev = min(prev_bids)
        # If my HP is low, bid high to secure water
        if hp <= 2:
            target = min(budget, DAILY_SALARY * 0.95)
        elif hp <= 5:
            # Moderate HP, bid just above the lowest previous bid (likely Bob)
            target = min(budget, max(DAILY_SALARY * 0.4, min_prev + 1.5))
        else:
            # Healthy, bid just above the second highest? Use average
            avg_prev = sum(prev_bids) / len(prev_bids)
            target = min(budget, max(DAILY_SALARY * 0.3, avg_prev))
    
    # Ensure bid is within budget and at least 0
    return max(0, int(target))
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
    
    # Day index: 0-based as per typical game
    day = int(day_context['day'])  # Ensure integer

    # If first day, no previous traces, use conservative bid
    if day == 0:
        base_bid = 0.7 * DAILY_SALARY
        # If low hp, bid higher to ensure survival
        if my_status['hp'] <= 3:
            base_bid = 0.9 * DAILY_SALARY
        return min(my_status['budget'], base_bid)

    # For subsequent days, collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone bid very high yesterday, they may bid high again
        if highest_prev >= DAILY_SALARY * 0.85:
            # they are aggressive, we need to outbid if necessary
            if my_status['hp'] > 3:
                # conserve budget
                return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev + 2))
            else:
                # desperate: bid high to survive
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            # moderate environment: outbid median slightly
            median_bid = sorted(yesterday_bids)[len(yesterday_bids) // 2]
            target = max(DAILY_SALARY * 0.4, median_bid + 2)
            return min(my_status['budget'], target)
    else:
        # No traces (shouldn't happen after day 0, but safe fallback)
        base_bid = 0.7 * DAILY_SALARY
        if my_status['hp'] <= 3:
            base_bid = 0.9 * DAILY_SALARY
        return min(my_status['bud
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    budget = my_status['budget']
    hp = my_status['hp']
    day = day_context['day']
    supply = int(day_context['supply'])
    
    # Determine base bid percentage
    if hp <= 2:
        bid_percent = 0.9
    elif hp <= 5:
        bid_percent = 0.8
    else:
        bid_percent = 0.7
    
    # Adjust based on day (later days, more conservative to save budget)
    if day >= 7:
        bid_percent = min(bid_percent, 0.6)
    
    # Calculate bid
    bid = bid_percent * DAILY_SALARY
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    
    # If supply is very low, we might need to increase bid slightly
    if supply < 18:
        bid = min(bid * 1.2, budget)
    
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid decision
    urgent = (hp <= 5) or (no_water > 0)
    if urgent:
        # Need water: bid just above yesterday's max to outbid
        target = max(DAILY_SALARY * 0.6, highest_yesterday + 5.0)
    else:
        # Not urgent: bid low to conserve
        target = min(DAILY_SALARY * 0.3, 60.0)
    
    # Adjust for supply scarcity
    possible_winners = int(supply // WATER_REQ)
    if possible_winners < len(alive_opponents) + 1:  # competition high
        target = target * 1.2
    if supply < 15:
        target = max(target, 100.0)

    # Ensure within budget and reasonable
    bid = min(budget, max(1.0, target))
    return int(bid)
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

    supply = day_context['supply']
    day = day_context['day']

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    num_alive = len(alive_opponents)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base aggressive level based on
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                yesterday_bids.append(trace['bid'])
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
    else:
        max_yesterday = 0.0
    
    # Estimate bid to beat: slightly above max yesterday, but not too high
    target_bid = max_yesterday + 2.0
    # Adjust based on supply: if supply low, need higher bid
    if supply < 18:
        target_bid *= 1.2
    elif supply > 22:
        target_bid *= 0.8
    
    # HP urgency
    if hp <= 3:
        target_bid = max(target_bid, DAILY_SALARY * 0.85)
    elif hp <= 5:
        target_bid = max(target_bid, DAILY_SALARY * 0.7)
    
    # Cap at a reasonable fraction of salary to preserve budget
    max_bid = min(budget, DAILY_SALARY * 0.7)
    # Also ensure we don't exceed budget completely
    bid = min(target_bid, max_bid)
    # Ensure minimum bid (at least something)
    bid = max(bid, 1.0)
    return bid
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

    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [opp for opp in opponents_status.values() if opp['alive']]

    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Determine target bid based on yesterday's highest pressure
    if prev_bids:
        highest_prev = max(prev_bids)
        # If we are desperate (low HP or multiple days without water)
        if my_hp <= 2 or no_water_days >= 2:
            bid = min(my_budget, highest_prev + 5.0)
        else:
            # Otherwise, try to outbid by a small margin if we have HP buffer
            bid = min(my_budget, max(DAILY_SALARY * 0.4, highest_prev + 2.0))
    else:
        # No history: default based on HP and supply
        if my_hp <= 2:
            bid = min(my_budget, DAILY_SALARY * 0.8)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.5)

    # Adjust for supply tightness: bid higher if supply is low
    if supply < MAX_SUPPLY * 0.5:
        bid = max(bid, DAILY_SALARY * 0.6)
    elif supply > MAX_SUPPLY * 0.8:
        bid = min(bid, DAILY_SALARY * 0.3)

    # Always stay within budget and ensure a non-negative bid
    bid = max(0.0, min(my_budget, bid))
    return bid
"""
