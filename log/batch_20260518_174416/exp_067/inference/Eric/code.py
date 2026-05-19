# ============================================================
# Experiment: exp_067
# Agent: Eric
# Source: exp_067
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    hp = my_status['hp']
    budget = my_status['budget']

    # Count alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)

    # Base bid: proportional to need
    if hp <= 2:
        # Desperate: bid high
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # Moderate need
        bid = min(budget, DAILY_SALARY * 0.70)
    else:
        # Healthy: conservative
        bid = min(budget, DAILY_SALARY * 0.45)

    # If there are many opponents, increase bid slightly
    if num_alive >= 3:
        bid = min(budget, bid * 1.2)
    elif num_alive <= 1:
        # Few competitors, we can lower bid
        bid = min(budget, bid * 0.8)

    # Ensure bid is positive and within budget
    bid = max(1, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Base bid: proportional to water need relative to supply
    base_bid = DAILY_SALARY * (WATER_REQ / supply)

    # Look at previous bids of alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace')
            if prev and 'bid' in prev:
                prev_bids.append(prev['bid'])

    # Determine target bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If we are healthy, try to undercut; if desperate, go higher
        if my_hp > 3 and no_water == 0:
            target = min(base_bid, max_prev * 0.85)
        elif my_hp <= 2 or no_water >= 2:
            target = max(DAILY_SALARY * 0.9, max_prev * 1.05)
        else:
            target = max(base_bid, max_prev * 0.95)
    else:
        # No past data: bid based on hp
        if my_hp <= 2:
            target = DAILY_SALARY * 0.85
        else:
            target = base_bid * 0.9

    # Ensure we don't exceed budget and bid reasonable
    bid = min(my_budget, max(1.0, target))
    # Ensure bid is a float (not int) as expected
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Check previous traces for hints of yesterday's bids
    max_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # Base bid strategy
    if hp <= 2:
        # Desperate: bid high to get water
        bid = min(budget, DAILY_SALARY * 1.0)
    elif hp <= 4:
        bid = min(budget, DAILY_SALARY * 0.85)
    else:
        # Healthy: adjust based on supply and opponent history
        if max_prev_bid > 120:
            # Aggressive opponents yesterday, likely high today
            bid = min(budget, max(DAILY_SALARY * 0.7, max_prev_bid - 5))
        else:
            # Moderate supply-based bid
            if supply > 20:
                bid = min(budget, DAILY_SALARY * 0.7)
            else:
                bid = min(budget, DAILY_SALARY * 0.85)
    
    # Ensure bid is within budget and not less than 0
    bid = max(0, min(budget, bid))
    # To avoid float index errors, no list indexing used
    return float(bid)
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
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Base bid proportional to daily salary, adjusted by supply
    base_fraction = 0.5 + (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) * 0.3
    bid = DAILY_SALARY * base_fraction
    # High supply -> slightly lower bid, low supply -> higher
    # Adjust based on yesterday's max bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If opponents bid very high, they may still be aggressive; be cautious
        if max_prev >= DAILY_SALARY * 0.85:
            bid = min(bid, DAILY_SALARY * 0.55)
        else:
            # Slightly below highest to save budget
            bid = min(bid, max_prev + 1.0)
    # Urgency based on HP
    if hp <= 2:
        # Must get water, bid aggressively
        bid = max(bid, DAILY_SALARY * 0.85)
    elif hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.6)
    # Ensure bid does not exceed budget
    if budget < bid:
        bid = budget
    # Floor at 0
    if bid < 0:
        bid = 0
    # Ensure bid is not too high to waste budget; if many days left, save
    days_left = 10 - day  # assume total days 10 from context
    if days_left > 3 and hp > 4:
        bid = min(bid, DAILY_SALARY * 0.5)
    # Convert to float
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Determine highest previous bid among alive opponents
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace:
            prev_bids.append(trace['bid'])
    
    if prev_bids:
        max_prev = max(prev_bids)
    else:
        max_prev = 0
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    # Urgency based on hp and no_water
    if hp <= 2 or no_water > 1:
        # Need water urgently: bid competitive
        bid = min(budget, max(DAILY_SALARY * 0.9, max_prev + 1))
    elif hp <= 4:
        bid = min(budget, max(DAILY_SALARY * 0.6, max_prev + 0.5))
    else:
        # Healthy: can afford to bid low or moderate
        if max_prev >= DAILY_SALARY * 0.8:
            bid = min(budget, DAILY_SALARY * 0.4)
        else:
            bid = min(budget, max(DAILY_SALARY * 0.3, max_prev + 1.0))
    
    # Ensure bid does not exceed budget
    return min(bid, budget)
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
    no_water_days = my_status['no_water_days']
    
    # Gather opponents' previous bids
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
    
    # Determine aggressive threshold based on HP and no_water_days
    if hp <= 2 or no_water_days >= 1:
        aggressive = True
    else:
        aggressive = False
    
    # Base bid: if aggressive, bid high; else moderate
    if aggressive:
        base_bid = DAILY_SALARY * 0.9  # 126
    else:
        base_bid = DAILY_SALARY * 0.75  # 105
    
    # Adjust based on opponents' previous max bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If someone bid very high yesterday, we need to outbid or match
        if aggressive:
            target = max(base_bid, max_prev + 2)
        else:
            # If not aggressive, try to stay slightly above average
            avg_prev = sum(prev_bids) / len(prev_bids)
            target = max(base_bid, avg_prev + 5)
        bid = min(budget, target)
    else:
        bid = min(budget, base_bid)
    
    # Ensure we don't bid more than budget and at least a small amount
    bid = max(1.0, min(budget, bid))
    return bid
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
    
    # Only consider alive opponents (on day 1 all are alive)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Analyze opponents' previous trace (yesterday's behavior)
    high_aggressor = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev['bid'] > 120:
            high_aggressor = True
            break
    
    # Decide base bid
    if hp <= 3:
        # Desperate: bid high to secure water
        base_bid = DAILY_SALARY * 0.9
    elif high_aggressor:
        # Opponents are extreme; undercut them
        base_bid = DAILY_SALARY * 0.3
    else:
        # Normal: moderate bid
        base_bid = DAILY_SALARY * 0.5
    
    # Ensure bid does not exceed budget
    bid = min(budget, base_bid)
    # Ensure non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply']) if 'supply' in day_context else 20
    day = int(day_context['day']) if 'day' in day_context else 10
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect yesterday's bids from previous_trace
    yesterday_bids = []
    for opp_id, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])
    
    # Determine highest bid from yesterday
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
    else:
        max_yesterday_bid = DAILY_SALARY * 0.5  # default guess
    
    # Decide bid based on HP and pressure
    if hp <= 2:
        # Must win: bid near salary or just enough to beat yesterday's max
        bid = min(budget, max(DAILY_SALARY * 0.9, max_yesterday_bid + 1))
    elif hp <= 4:
        # Need water but can be slightly conservative
        bid = min(budget, max(DAILY_SALARY * 0.7, max_yesterday_bid * 0.95))
    else:
        # Healthy: try to save money
        # If yesterday's max was very high, undercut significantly
        if max_yesterday_bid > DAILY_SALARY * 0.85:
            bid = min(budget, DAILY_SALARY * 0.4)
        else:
            bid = min(budget, max(DAILY_SALARY * 0.5, max_yesterday_bid + 0.5))
    
    # Ensure we don't blow budget, and minimum bid at least 1
    bid = max(bid, 1)
    bid = min(bid, budget)
    return bid
"""
