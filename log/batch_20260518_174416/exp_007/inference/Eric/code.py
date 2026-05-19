# ============================================================
# Experiment: exp_007
# Agent: Eric
# Source: exp_007
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], int(DAILY_SALARY * 0.4))
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    base_bid = int(DAILY_SALARY * 0.5)
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev >= DAILY_SALARY * 0.9:
            base_bid = min(int(DAILY_SALARY * 0.95), max_prev + 1)
        else:
            base_bid = max(base_bid, int(max_prev + 2))
    if my_status['hp'] <= 2:
        base_bid = max(base_bid, int(DAILY_SALARY * 0.9))
    if my_status['no_water_days'] >= 1:
        base_bid = max(base_bid, int(DAILY_SALARY * 0.85))
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])

    bid = DAILY_SALARY * 0.4

    # Urgency due to water need
    if hp <= 2 or no_water_days > 0:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif supply <= 18:
        bid = min(budget, DAILY_SALARY * 0.7)
    else:
        bid = min(budget, DAILY_SALARY * 0.4)

    # Respond to yesterday's high bids from competitors
    if yesterday_max_bid > 0:
        if hp <= 3 or (supply <= 18 and hp <= 5):
            bid = max(bid, min(budget, yesterday_max_bid + 1.0))
        else:
            # If we are comfortable, bid just enough to not waste money
            if yesterday_max_bid > DAILY_SALARY * 0.7:
                bid = min(bid, DAILY_SALARY * 0.3)

    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Also ensure a minimum bid of 0 if budget is very low
    if budget < 1:
        bid = 0.0
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    
    # Get yesterday's max bid among alive opponents (excluding dead)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine target bid based on yesterday's highest
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # Increase bid slightly to outbid
        target = max_prev_bid + 2.0
    else:
        # If no data, use a safe estimate based on average
        target = DAILY_SALARY * 0.7  # 98
    
    # Adjust for urgency
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    
    # If low HP or multiple days without water, bid aggressively
    if hp <= 2 or no_water >= 1:
        bid = min(budget, max(target * 1.2, DAILY_SALARY * 0.85))
    else:
        bid = min(budget, target)
    
    # Ensure bid is at least something reasonable
    if bid < 10:
        bid = 10.0
    
    # Cap by budget to avoid negative
    return min(bid, budget)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)
    
    # Estimate opponent bids from yesterday's trace
    estimated_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            # Scale based on budget and hp
            prev_bid = prev['bid']
            budget_after = prev.get('budget_after', opp['budget'])
            hp_after = prev.get('hp_after', opp['hp'])
            # If opponent has high budget relative to yesterday, they may increase
            if budget_after > opp['daily_salary'] * 3:
                scaling = 1.2
            else:
                scaling = 1.0
            estimated_bids.append(prev_bid * scaling)
        else:
            # No trace, assume baseline
            estimated_bids.append(opp['daily_salary'] * 0.7)
    
    if not estimated_bids:
        return min(my_budget, DAILY_SALARY * 0.5)
    
    max_est_bid = max(estimated_bids)
    # adjust based on supply tightness
    tight_factor = max(1.0, (WATER_REQ * len(alive_opponents) + WATER_REQ) / max(supply, 1))
    target_bid = max_est_bid * tight_factor + 1.5
    
    # personal health consideration
    if my_hp <= 2:
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    elif my_hp <= 4:
        target_bid = max(target_bid, DAILY_SALARY * 0.7)
    else:
        # can afford to lose, try to save
        target_bid = min(target_bid, DAILY_SALARY * 0.5)
    
    # ensure we don't exceed budget and not negative
    bid = min(my_budget, target_bid)
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Find yesterday's max bid among alive opponents
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    
    # Base bid: start with a moderate fraction of salary
    base_bid = DAILY_SALARY * 0.65  # ~91
    
    # Adjust based on urgency (HP and no_water_days)
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 0.9  # ~126
    
    # Outbid yesterday's highest if it is higher than base
    if max_prev_bid > base_bid:
        target_bid = max_prev_bid + 1.0
    else:
        target_bid = base_bid
    
    # Supply modulation: if supply is low, increase bid
    supply = day_context['supply']
    if supply < 20:
        target_bid *= 1.15
    
    # Ensure we don't bid more than budget
    target_bid = min(target_bid, my_status['budget'])
    # Ensure non-negative
    target_bid = max(target_bid, 0.0)
    
    return target_bid
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Estimate opponents' likely bids from previous trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
        else:
            # Fallback: assume bid proportional to salary/requirement
            # Here we use average of known aggressive bidding
            prev_bids.append(DAILY_SALARY * 0.85)
    
    max_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.9
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.7
    
    # Adjust base bid for urgency
    if hp <= 2:
        base_bid = min(budget, max_prev + 1.0)
    elif hp <= 4:
        base_bid = min(budget, avg_prev * 1.1)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.5)
    
    # Scale with supply scarcity
    scarcity_factor = 1.0
    if supply < 18:
        scarcity_factor = 1.3
    elif supply > 22:
        scarcity_factor = 0.7
    
    final_bid = base_bid * scarcity_factor
    final_bid = min(final_bid, budget)
    final_bid = max(final_bid, 0.0)
    return final_bid
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = day_context['day']
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Gather yesterday's bids from opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    
    # Base bid calculation
    # If supply scarce, increase bid
    scarcity_factor = 1.0 + (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) * 0.5
    
    if hp <= 2:
        # Critical health: bid high to survive
        target_bid = min(budget, DAILY_SALARY * 0.9 * scarcity_factor)
    elif hp <= 4:
        # Moderate health: bid moderately
        target_bid = min(budget, DAILY_SALARY * 0.6 * scarcity_factor)
    else:
        # Healthy: economical bidding
        target_bid = min(budget, DAILY_SALARY * 0.4 * scarcity_factor)
    
    # Adjust based on previous opponent bids
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        # If opponents were very aggressive, reduce our bid to save budget
        if highest_prev >= DAILY_SALARY * 0.85:
            target_bid = min(target_bid, DAILY_SALARY * 0.35 * scarcity_factor)
        else:
            # Slightly undercut the average if we are healthy
            if hp > 4:
                target_bid = min(target_bid, max(avg_prev - 2, DAILY_SALARY * 0.2))
            else:
                target_bid = min(target_bid, max(avg_prev + 1, DAILY_SALARY * 0.3))
    
    # Ensure we don't bid more than our budget and not less than 0
    final_bid = max(0, min(budget, target_bid))
    
    # Integer conversion to avoid float issues
    return int(final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    # Extract yesterday's bids from opponents' traces
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Basic target based on supply and competition
    units_available = int(supply // WATER_REQ)  # integer number of full units
    participation = num_opponents + 1  # including ourselves
    
    # Base bid: a fraction of daily salary, adjusted by desperation
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    else:
        base_bid = DAILY_SALARY * 0.6
    
    # Adapt based on yesterday's bids
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        # If opponents bid high yesterday, they might bid lower today (or continue). Assume regression.
        if max_prev > DAILY_SALARY * 1.1:
            # Very high bid: likely unsustainable, so we bid low
            bid = max(DAILY_SALARY * 0.3, base_bid * 0.5)
        elif max_prev > DAILY_SALARY * 0.8:
            # Still high, but not extreme
            bid = base_bid * 0.7
        else:
            # They bid low, we can afford to bid slightly higher than yesterday's max
            bid = max(base_bid, max_prev + 2.0)
    else:
        # No info, use base
        bid = base_bid
    
    # Ensure we don't exceed budget
    bid = min(bid, my_budget)
    # Ensure minimum bid is not negative
    bid = max(bid, 0.0)
    
    return bid
"""
