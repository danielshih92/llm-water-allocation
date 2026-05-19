# ============================================================
# Experiment: exp_105
# Agent: Eric
# Source: exp_105
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Check yesterday's bids from opponents to gauge aggression
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # Base bid on health
    if hp > 5:
        base = DAILY_SALARY * 0.5
    elif hp > 2:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.9
    
    # Adjust if yesterday's top bid was high (aggressive opponents)
    if max_prev_bid > DAILY_SALARY * 0.8:
        base = min(base, max_prev_bid + 1)
    elif max_prev_bid > 0:
        base = max(base, max_prev_bid + 1)
    
    # Ensure not to exceed budget and keep some reserve
    bid = min(budget, base)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_high_bid = 0
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_high_bid = max(prev_high_bid, trace['bid'])
    # Determine number of units needed: only 1 unit (water_requirement=8, supply max 25, so at most 3 units but we just need 1 to avoid no-water)
    # Base bid strategy
    if hp <= 2:
        # Desperate: bid high to ensure water
        target = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # Moderate risk: bid around 0.7 of salary
        target = min(budget, DAILY_SALARY * 0.7)
    else:
        # Healthy: bid low to save money
        target = min(budget, DAILY_SALARY * 0.4)
    # If previous opponent was aggressive, adjust upwards slightly
    if prev_high_bid >= DAILY_SALARY * 0.85:
        target = max(target, min(budget, DAILY_SALARY * 0.65))
    # Ensure we can bid at least something positive
    if budget <= 0:
        return 0.0
    # Return as float
    return float(min(budget, max(1.0, target)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Identify alive opponents
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive:
        return min(budget, DAILY_SALARY * 0.3)
    
    # Get yesterday's max bid from alive opponents
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    if not prev_bids:
        # No data, use conservative aggressive
        base_bid = DAILY_SALARY * 0.7
    else:
        max_prev = max(prev_bids)
        # Adjust based on how competitive
        if max_prev > DAILY_SALARY * 0.9:
            base_bid = max_prev + 2
        else:
            base_bid = max_prev + 5
    
    # Consider desperation
    if hp <= 2 or no_water_days >= 1:
        bid = min(budget, base_bid * 1.3)
    elif hp <= 5:
        bid = min(budget, base_bid * 1.1)
    else:
        bid = min(budget, base_bid * 0.9)
    
    # Ensure at least a minimum bid to compete if budget allows
    min_bid = DAILY_SALARY * 0.3
    if bid < min_bid and budget >= min_bid:
        bid = min_bid
    
    return min(bid, budget)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Gather yesterday's max bid from opponents
    max_prev_bid = 0.0
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    
    # Urgency based on HP and no_water_days
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    
    # If in danger of dying, bid high
    if no_water > 0 or hp <= 3:
        target_bid = max(DAILY_SALARY * 0.9, max_prev_bid + 2.0)
    else:
        target_bid = min(DAILY_SALARY * 0.6, max_prev_bid - 1.0)
        if target_bid < 0:
            target_bid = DAILY_SALARY * 0.4
    
    # Ensure we don't exceed budget
    return min(budget, target_bid)
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = int(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Determine number of possible winners based on supply
    possible_winners = supply // WATER_REQ
    
    # Default aggressive bid: just above Cindy's fixed 150
    aggressive_bid = 151
    
    # If supply is high, we can be less aggressive
    if possible_winners >= 3:
        aggressive_bid = 145
    
    # Urgency: if low on water or HP, must win
    if hp <= 2 or no_water_days > 0:
        # Ensure we can afford it
        bid = min(budget, aggressive_bid)
    else:
        # Otherwise, bid low to save money
        # Look at opponents' previous traces to see if they are still aggressive
        max_prev_bid = 0
        for opp_id, opp_state in opponents_status.items():
            prev = opp_state.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                if float(prev['bid']) > max_prev_bid:
                    max_prev_bid = float(prev['bid'])
        
        # If previous max bid was high, we may need to increase a bit
        if max_prev_bid > 150:
            # Still, we don't want to waste unless necessary
            bid = min(budget, 145)
        else:
            bid = min(budget, 100)
    
    # Ensure bid is at least 1 and integer
    bid = max(1, int(bid))
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > highest_prev_bid:
                highest_prev_bid = prev['bid']
    
    # Base bid
    bid = DAILY_SALARY * 0.5
    
    # Urgency adjustments
    if hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        bid = DAILY_SALARY * 0.7
    
    # If opponents were aggressive yesterday, increase bid
    if highest_prev_bid > DAILY_SALARY *
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
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    salary = 140
    water_req = 8

    alive_opps = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opps:
        return min(budget, salary * 0.4)

    prev_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in
"""
