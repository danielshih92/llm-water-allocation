# ============================================================
# Experiment: exp_089
# Agent: Eric
# Source: exp_089
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine maximum yesterday bid from opponents
    max_yesterday_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > max_yesterday_bid:
                max_yesterday_bid = prev['bid']

    # Base bid calculation
    if no_water_days >= 1 or hp <= 2:
        # Desperate: bid high to ensure water
        bid = min(budget, DAILY_SALARY * 0.95)
    elif hp > 5 and day < 8:
        # Healthy early: conservative, but stay competitive
        bid = min(budget, DAILY_SALARY * 0.5)
        if max_yesterday_bid > 0:
            # Try to undercut if possible
            bid = min(budget, max(bid, max_yesterday_bid * 0.9))
    else:
        # Moderate health: bid moderately, possibly slightly above yesterday's max if needed
        bid = min(budget, DAILY_SALARY * 0.75)
        if max_yesterday_bid > 0 and max_yesterday_bid < DAILY_SALARY * 0.85:
            bid = min(budget, max_yesterday_bid + 1.5)

    # Ensure bid does not exceed budget
    bid = max(0.0, min(bid, budget))
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Base bid: salary proportion based on day and health
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # If out of budget, bid 0
    if budget <= 0:
        return 0.0
    
    # Emergency: if hp <= 1 or no_water_days >= 2, bid high to secure water
    if hp <= 1 or no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        # Determine pressure from yesterday's trace (only last day of previous metaround)
        pressure = 0
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                pressure += prev['bid']
        if num_alive > 0:
            pressure /= num_alive
        else:
            pressure = 0
        
        # Early days (day 1-3): bid higher to establish water security
        if day <= 3:
            base_bid = min(budget, DAILY_SALARY * 0.65)
        else:
            base_bid = min(budget, DAILY_SALARY * 0.5)
        
        # Adjust based on pressure: if pressure is high (above 90), increase bid
        if pressure > 90:
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
        
        # If many opponents alive, bid slightly higher
        if num_alive >= 3:
            base_bid = min(budget, base_bid * 1.15)
        
        bid = min(budget, base_bid)
    
    # Ensure bid is positive and not exceeding budget
    return max(0.0, min(bid, budget))
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Get yesterday's max bid from alive opponents
    yesterday_max_bid = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])
    
    # Base bid: moderate
    base_bid = DAILY_SALARY * 0.55  # 77
    
    # Adjust for supply shortage
    if supply < 20:
        base_bid = DAILY_SALARY * 0.75  # 105
    
    # Adjust for low hp or dehydration risk
    if hp <= 3:
        base_bid = DAILY_SALARY * 0.9  # 126
    elif no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.85  # 119
    
    # If yesterday was aggressive, respond
    if yesterday_max_bid > DAILY_SALARY * 0.8:
        if hp <= 3:
            base_bid = DAILY_SALARY * 0.95  # 133
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.65)  # 91
    
    # Ensure we have budget
    final_bid = min(base_bid, budget)
    # Also ensure non-negative
    final_bid = max(final_bid, 1.0)
    return final_bid
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
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev + 1.5))
    
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
    MAX_SUPPLY = 25
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)
    prev_bids = []
    for o in alive_opps:
        trace = o.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    # Base bid scales inversely with supply: higher when scarce
    base_bid = DAILY_SALARY * (0.5 + 0.3 * (1 - supply / MAX_SUPPLY))
    # HP adjustment: bid more if dehydrated
    if hp <= 2:
        base_bid *= 1.6
    elif hp <= 5:
        base_bid *= 1.3
    # Competitive adjustment: beat yesterday's highest bid if it's within reason
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > base_bid:
            base_bid = max_prev + 2.0
    # Never exceed budget or a safe fraction of salary
    max_affordable = min(budget, DAILY_SALARY * 0.95)
    return min(max_affordable, max
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect previous bids from traces
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine bidding aggressiveness based on HP and supply
    if hp <= 2:
        # Desperate: bid high to get water
        desired = DAILY_SALARY * 0.9
    else:
        if prev_bids:
            max_prev = max(prev_bids)
        else:
            max_prev = DAILY_SALARY * 0.5  # default estimate
        
        # Adjust for supply scarcity
        if supply < 18:
            pressure_multiplier = 1.2
        elif supply > 22:
            pressure_multiplier = 0.8
        else:
            pressure_multiplier = 1.0
        
        if max_prev > DAILY_SALARY * 0.7:
            # High competition
            if hp > 4:
                desired = DAILY_SALARY * 0.3 * pressure_multiplier
            else:
                desired = DAILY_SALARY * 0.6 * pressure_multiplier
        else:
            # Low competition: outbid slightly
            desired = max(DAILY_SALARY * 0.4, max_prev + 1) * pressure_multiplier
    
    # Ensure bid is within budget and non-negative
    bid = max(0, min(budget, desired))
    return bid
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

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            yesterday_bids.append(bid)

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']

    # Base target: bid slightly above max yesterday, but not too high
    if hp <= 2:
        # Desperate: bid high to ensure water
        target = min(budget, DAILY_SALARY * 0.8)
    else:
        # Normal: outbid by a small margin
        target = min(budget, max(DAILY_SALARY * 0.3, max_prev_bid + 5.0))

    # If supply is low, increase bid slightly
    if supply < 20:
        target = min(budget, target * 1.2)

    # Ensure we never bid more than we can afford
    return min(target, budget)
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
    DAILY_SALARY = 140
    WATER_REQ = 8
    
    # Extract day info
    day = int(day_context['day'])
    supply = float(day_context['supply'])
    winners_count = int(supply // WATER_REQ)  # number of bidders who get water
    
    # My status
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Alive opponents
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid strategy
    base_bid = 0.0
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # Strong pressure from yesterday
        if max_prev >= DAILY_SALARY * 0.85:
            if hp > 3:
                # Safe to undercut
                base_bid = min(budget, max_prev * 0.75)
            else:
                # Need water, match high
                base_bid = min(budget, max_prev + 1.0)
        else:
            # Moderate: try to win by small margin
            base_bid = min(budget, max_prev + 2.0)
    else:
        # First day or no history: cautious
        if hp <= 2:
            base_bid = min(budget, DAILY_SALARY * 0.8)
        else:
            base_bid = min(budget, DAILY_SALARY * 0.4)
    
    # Adjust based on supply scarcity
    if supply < 18:
        # Very scarce, increase bid
        base_bid = min(budget, base_bid * 1.2)
    elif supply > 22:
        # Abundant, lower bid
        base_bid = min(budget, base_bid * 0.85)
    
    # Endgame push: last 3 days
    remaining_days = 10 - day  # assuming total days 10, but can be dynamic
    # Actually we don't know total days except from meta-round? Use day_context? Not given. Assume 10.
    if day >= 8:
        if hp <= 2:
            base_bid = min(budget, DAILY_SALARY * 0.95)
        else:
            base_bid = min(budget, DAILY_SALARY * 0.
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine number of water units available
    units_available = int(supply // WATER_REQ)

    # Get previous day's bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine highest previous bid from alive opponents
    highest_prev = max(prev_bids) if prev_bids else 0

    # Base bid: try to secure a unit if needed
    if hp <= 2:
        # Critical health: bid aggressively up to budget
        bid = min(budget, SALARY * 0.95)
    elif hp <= 4:
        # Low health: bid moderately high
        bid = min(budget, max(SALARY * 0.7, highest_prev + 1.5))
    else:
        # Healthy: bid just enough if competition is high, otherwise low
        if highest_prev >= SALARY * 0.8:
            # Aggressive opponent last round, undercut to preserve money
            bid = min(budget, SALARY * 0.65)
        else:
            # Conservative opponent, outbid slightly
            bid = min(budget, max(SALARY * 0.5, highest_prev + 1.5))

    # Ensure bid is within budget and non-negative
    bid = max(0, min(bid, budget))

    # If supply is high and few opponents, can afford lower bid
    if units_available > len(alive_opponents) and hp > 5:
        bid = min(bid, SALARY * 0.4)

    return bid
"""
