# ============================================================
# Experiment: exp_081
# Agent: Eric
# Source: exp_081
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, max(1, DAILY_SALARY * 0.5))

    # Attempt to exploit opponent yesterday trace if available (none here)
    # Fallback: base bid on own health and expected competition

    days_left = 10 - day
    if hp <= 2:
        # Critical: need water at any cost
        target_bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        # Moderate risk
        target_bid = min(budget, DAILY_SALARY * 0.7)
    else:
        # Healthy: can afford to lose a day
        target_bid = min(budget, DAILY_SALARY * 0.4)

    # Ensure positive bid
    if target_bid < 1:
        target_bid = 1
    if target_bid > budget:
        target_bid = budget

    return target_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    alive = [o for o in opponents_status.values() if o['alive']]
    max_prev_bid = 0
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    
    if hp <= 2:
        bid = min(budget, SALARY * 0.95)
    elif hp <= 4:
        bid = min(budget, SALARY * 0.7)
    else:
        bid = min(budget, SALARY * 0.2)
    
    if hp <= 4 and max_prev_bid > 0:
        needed = max_prev_bid + 0.1
        if needed <= budget:
            bid = max(bid, needed)
    
    bid = min(bid, budget)
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    my_hp = int(my_status['hp'])
    my_budget = my_status['budget']
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}

    # Estimate opponents' bids today from their previous trace (yesterday's bid)
    estimated_bids = []
    for aid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            estimated_bids.append(prev['bid'])

    # Base bid: enough to get water, scale with supply tightness
    if supply <= 16:
        base_bid = min(my_budget, DAILY_SALARY * 0.95)
    elif supply >= 22:
        base_bid = min(my_budget, DAILY_SALARY * 0.4)
    else:
        base_bid = min(my_budget, DAILY_SALARY * 0.65)

    # Adjust based on HP
    if my_hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif my_hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # If no water for 2+ days, raise bid
    if no_water_days >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Counter strong opponents: ensure we beat the maximum estimated bid if needed
    if estimated_bids:
        highest_est = max(estimated_bids)
        # Cindy bids exactly 147 every day; if she's present, we need to beat 147
        # We'll add a margin of 1 if we can afford it and if we are desperate
        if highest_est >= DAILY_SALARY * 0.85:
            # Aggressive opponent: match or beat by a small margin
            target = highest_est + 1.0
            if my_hp > 5 and supply >= 20:
                # can afford to be conservative, just slightly above
                base_bid = max(base_bid, min(my_budget, highest_est + 0.5))
            else:
                base_bid = max(base_bid, min(my_budget, target))
        else:
            # Opponents moderate: bid slightly above highest estimate
            base_bid = max(base_bid, min(my_budget, highest_est + 1.5))

    # Final clamp to budget
    final_bid = min(my_budget, base_bid)
    # Ensure positive and integer-ish (but Python float ok, will round in game? keep as float)
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
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive'] and opp.get('previous_trace'):
            prev_trace = opp['previous_trace']
            if prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])
    
    # Base bid: use 50% of salary if healthy
    base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on health
    if hp <= 2 or no_water_days >= 1:
        # desperate: bid high
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.6
    elif hp >= 10:
        # very healthy, can save money
        base_bid = DAILY_SALARY * 0.3
    
    # Incorporate yesterday's competition
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If yesterday's max was very high, we need to match or exceed slightly to secure water
        if max_prev > DAILY_SALARY * 0.8:
            # Suggesting they are aggressive; if we are healthy, stay moderate but safe
            if hp >= 5:
                target = max_prev + 2
            else:
                target = max_prev * 1.1  # slight increase
        else:
            # Moderate competition: outbid the highest by a small margin if needed
            target = max_prev + 1.5
        
        # Blend: use the higher of base_bid and target, but cap by budget
        bid = min(budget, max(base_bid, target))
    else:
        # No opponents or no trace data, just use base_bid
        bid = min(budget, base_bid)
    
    # Don't bid more than necessary; minimum 1 to avoid default 0
    if bid < 1:
        bid = 1.0
    
    # Ensure bid is not more than budget and a reasonable upper bound
    bid = min(budget, bid)
    
    return bid
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

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    bid_fraction = 0.8 - 0.6 * supply_ratio

    if hp <= 2:
        bid_fraction = max(bid_fraction, 0.9)
    elif hp <= 4:
        bid_fraction = max(bid_fraction, 0.6)

    if no_water_days >= 2:
        bid_fraction = min(1.0, bid_fraction + 0.2)

    bid = min(budget, DAILY_SALARY * bid_fraction)
    bid = max(bid, 1.0)

    max_prev_bid = 0
    for opp in opponents_status.values():
        if opp['alive'] and opp.get('previous_trace')
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid on yesterday's average if available
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 2:
            # Desperate: bid high to guarantee water
            bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 4:
            # Moderate HP: bid above average to increase win chance
            bid = min(my_status['budget'], max(avg_prev_bid + 2, DAILY_SALARY * 0.4))
        else:
            # High HP: bid conservatively, just above average
            bid = min(my_status['budget'], max(avg_prev_bid + 1, DAILY_SALARY * 0.3))
    else:
        # No trace: use safe fallback
        if my_status['hp'] <= 2:
            bid = min(my_status['budget'], DAILY_SALARY * 0.8)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Ensure we don't exceed budget and stay positive
    bid = max(0, min(bid, my_status['budget']))
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return max(0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday's bids from traces
    prev_bids = []
    for o in alive_opponents.values():
        trace = o.get('previous_trace', None)
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    supply = day_context['supply']
    # Estimate number of water units available
    num_units = int(supply // WATER_REQ)  # ensures integer
    num_opponents = len(alive_opponents)
    competition_factor = num_opponents / max(1, num_units)

    hp = my_status['hp']
    budget = my_status['budget']

    # Base bid on previous behavior
    if prev_bids:
        max_prev = max(prev_bids)
        median_prev = sorted(prev_bids)[len(prev_bids) // 2]
    else:
        max_prev = DAILY_SALARY * 0.7
        median_prev = DAILY_SALARY * 0.5

    # Determine aggressiveness based on health and competition
    if hp <= 2:
        # Urgent need: bid high to secure water
        target = max(max_prev + 5, DAILY_SALARY * 1.1)
    elif hp <= 5:
        # Moderate need: outbid the highest previous bidder slightly
        target = max(max_prev + 2, median_prev + 10)
    else:
        # Safe: conserve budget, bid low but enough to bid if needed
        target = min(DAILY_SALARY * 0.3, median_prev - 5)

    # Adjust for competition intensity
    if competition_factor > 2.0:
        target *= 1.1  # More aggressive when scarce
    elif competition_factor < 1.0:
        target *= 0.8  # Can be less aggressive

    # Ensure bid is within budget and non-negative
    bid = min(budget, max(1, int(target)))
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    SUPPLY = day_context['supply']
    DAY = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    DAILY_SALARY = 140
    WATER_REQ = 8

    alive_opps = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opps:
        return min(budget, 10.0)

    prev_bids = []
    for opp in alive_opps.values():
        pt = opp.get('previous_trace', {})
        if pt and 'bid' in pt and pt['bid'] is not None:
            prev_bids.append(pt['bid'])

    if hp <= 2 or no_water >= 1:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.8
    else:
        urgency = 0.5

    if prev_bids:
        max_prev = max(prev_bids)
        base_bid = max(DAILY_SALARY * urgency, max_prev + 5.0)
    else:
        base_bid = DAILY_SALARY * urgency

    bid = min(budget, base_bid)
    if no_water > 0:
        bid = max(bid, 10.0)
    if hp <= 1:
        bid = min(budget, DAILY_SALARY * 1.0)
    return min(budget, bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    day = day_context['day']
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Decision logic
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            # Opponents aggressive; if I'm healthy, bid low to save budget; if weak, bid higher
            if hp > 4:
                bid = min(budget, DAILY_SALARY * 0.35)
            else:
                bid = min(budget, DAILY_SALARY * 0.9)
        else:
            # Moderate opponents; try to beat highest by small margin, but cap at 90% salary
            target = max(DAILY_SALARY * 0.45, highest_prev + 1)
            bid = min(budget, target)
    else:
        # No info, default
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.4)
    
    # Ensure bid is within 0 and budget, and not exceed budget
    bid = max(0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""
