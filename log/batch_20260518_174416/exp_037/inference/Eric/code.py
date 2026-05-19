# ============================================================
# Experiment: exp_037
# Agent: Eric
# Source: exp_037
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
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.85)
    elif hp <= 4:
        bid = min(budget, DAILY_SALARY * 0.65)
    else:
        bid = min(budget, DAILY_SALARY * 0.4)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # identify alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # compute a pressure factor based on past opponent behavior
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])

    # base bid: proportion of daily salary
    base_bid = DAILY_SALARY * 0.45

    # adjust for water need
    if hp < 3:
        need_multiplier = 1.8
    elif hp < 5:
        need_multiplier = 1.2
    else:
        need_multiplier = 0.9

    # adjust for supply tightness
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0=low, 1=high
    supply_multiplier = 1.0 + (1.0 - supply_ratio) * 0.3

    # adjust for no_water_days
    if no_water_days > 0:
        water_drought_mult = 1.0 + no_water_days * 0.15
    else:
        water_drought_mult = 1.0

    # final bid calculation
    bid = base_bid * need_multiplier * supply_multiplier * water_drought_mult

    # if opponents were very aggressive last round, consider matching
    if max_prev_bid > DAILY_SALARY * 0.8:
        bid = max(bid, DAILY_SALARY * 0.7)

    # ensure we don't overbid and stay within budget
    bid = min(bid, budget)
    bid = max(bid, 1.0)  # always bid at least 1

    return int(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    
    alive = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Gather yesterday's bids from alive opponents
    y_bids = []
    for opp in alive.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            y_bids.append(float(prev['bid']))
    
    # Determine pressure from yesterday
    if len(y_bids) > 0:
        max_prev = max(y_bids)
    else:
        max_prev = 0.0
    
    # Calculate a baseline: our water requirement fraction of supply
    needed_fraction = WATER_REQ / supply if supply > 0 else 1.0
    # Base bid: daily salary * needed_fraction
    base_bid = DAILY_SALARY * needed_fraction
    
    # Adjust based on opponent pressure and our HP
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    
    if hp <= 2:
        # Desperate: bid to outbid highest yesterday + some margin
        target = max(max_prev + 5.0, base_bid * 1.5)
    elif hp <= 5:
        # Need water but can be a bit more conservative
        target = max(max_prev + 1.0, base_bid * 1.2)
    else:
        # Healthy: try to save money
        target = min(base_bid * 0.9, max_prev + 1.0)
    
    # Cannot exceed budget
    bid = min(target, budget)
    # Ensure non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Convert supply to int for index safety
    supply_int = int(supply)

    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        # No opponents, bid low to save budget
        return min(budget, DAILY_SALARY * 0.3)

    # Collect yesterday's bids from traces
    yesterday_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])

    # Determine max yesterday bid
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: ensure we can win water even if supply low
    target_units = WATER_REQ
    # Estimate required proportion: need at least water_req / supply
    bid_per_unit = DAILY_SALARY * 0.5  # default

    # If supply is very limited, increase bid
    if supply_int <= 18:
        bid_per_unit = DAILY_SALARY * 0.7

    # If yesterday opponents were aggressive, match or slightly exceed
    if max_yesterday > 100:
        bid_per_unit = max(bid_per_unit, max_yesterday * 0.8)

    # Adjust based on health
    if hp <= 2 or no_water_days >= 1:
        # Desperate: need water
        base_bid = min(budget, DAILY_SALARY * 0.85)
    elif hp <= 5:
        base_bid = min(budget, DAILY_SALARY * 0.65)
    else:
        # Healthy, can be conservative
        base_bid = min(budget, DAILY_SALARY * 0.4)

    # Combine: use max of base and calculated from yesterday
    final_bid = min(budget, max(base_bid, bid_per_unit))
    # Ensure not negative
    return max(0.0, min(budget, final_bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    if prev_bids:
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev_bid = DAILY_SALARY * 0.5
    # Determine urgency
    urgent = (no_water_days >= 2) or (hp <= 2)
    if urgent:
        target = max(DAILY_SALARY * 0.9, min(budget, avg_prev_bid * 1.15))
    else:
        # Normal bid: use supply to adjust
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
        base_bid = DAILY_SALARY * (0.5 + 0.3 * (1 - supply_ratio))  # higher when supply low
        if avg_prev_bid > base_bid:
            base_bid = avg_prev_bid * 0.95
        target = min(budget, base_bid)
    return max(1.0, target)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    else:
        max_prev = DAILY_SALARY * 0.6
        avg_prev = DAILY_SALARY * 0.6
    
    supply = day_context['supply']
    if my_status['hp'] <= 3:
        # desperate: bid above average to secure water
        target = avg_prev + 2.0
    else:
        # comfortable: undercut to save budget
        target = avg_prev * 0.8
        min_bid = DAILY_SALARY * 0.3
        if target < min_bid:
            target = min_bid
    
    # ensure bid within budget and reasonable
    bid = min(my_status['budget'], target)
    bid = max(bid, 10)
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's highest bid from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Determine base bid based on health and supply
    if my_hp <= 3:
        # Danger: need water
        base = max(DAILY_SALARY * 0.8, highest_yesterday + 1.5)
        if supply <= 18:
            base = max(base, DAILY_SALARY * 0.9)
    elif my_hp <= 6:
        # Moderate risk
        base = max(DAILY_SALARY * 0.5, highest_yesterday * 0.95)
        if supply <= 18:
            base = max(base, DAILY_SALARY * 0.7)
    else:
        # Healthy: save money
        base = min(DAILY_SALARY * 0.4, highest_yesterday * 0.8)
        if supply <= 18:
            base = max(base, DAILY_SALARY * 0.3)
    
    # Cap at budget and ensure positive
    bid = min(my_budget, base)
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    
    # my info
    hp = my_status['hp']
    budget = my_status['budget']
    
    # get alive opponents
    alive = [o for o in opponents_status.values() if o['alive']]
    
    # collect previous bids from alive opponents
    prev_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # decide bid
    if prev_bids:
        highest_prev = max(prev_bids)
        # base bid: slightly above highest previous bid
        base_bid = highest_prev + 2.0
    else:
        # no info: bid a safe moderate amount
        base_bid = DAILY_SALARY * 0.55
    
    # hp-dependent adjustment
    if hp <= 2:
        # desperate: bid high to survive
        target = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        target = min(budget, max(base_bid, DAILY_SALARY * 0.8))
    else:
        target = min(budget, max(base_bid, DAILY_SALARY * 0.6))
    
    # ensure non-negative
    return max(0, target)
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
    
    alive_opponents = {oid: opp for oid, opp in opponents_status.items() if opp.get('alive', False)}
    
    # Get previous trace bids from alive opponents
    prev_bids = []
    for opp_id, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid strategy
    if prev_bids:
        max_prev = max(prev_bids)
        # Bid just above the highest previous bid, but not more than necessary
        base_bid = max(DAILY_SALARY * 0.5, max_prev + 1.0)
    else:
        # No data: conservative bid
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on urgency
    if hp <= 2:
        # Must win water today
        bid = min(budget, DAILY_SALARY * 0.9)
    elif day <= 3 and supply < 20:
        # Early days with limited supply: be aggressive
        bid = min(budget, max(DAILY_SALARY * 0.7, base_bid))
    else:
        # Standard: use base_bid
        bid = min(budget, base_bid)
    
    # Ensure we never bid more than budget
    bid = max(0.0, bid)
    return int(bid)  # bidding amount as integer
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140

    supply = day_context['supply']
    # Ensure supply is float; convert to int if needed for division
    max_possible_winners = int(supply // WATER_REQ)  # explicit int to avoid float index

    alive_opps = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opps)

    # Determine urgency
    urgent = my_status['hp'] <= 2 or my_status['no_water_days'] > 0

    # Gather previous bids from alive opponents
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev_bid = max(prev_bids) if prev_bids else 0

    # Base bid: small fraction of salary to conserve
    base_bid = DAILY_SALARY * 0.4

    if urgent:
        if max_prev_bid > DAILY_SALARY * 0.8:
            # Opponents are aggressive; outbid slightly if we need water
            target = min(max_prev_bid + 2, my_status['budget'])
            return max(base_bid, target)
        else:
            # Opponents not too aggressive; bid just above their max
            target = min(max_prev_bid + 1, my_status['budget'])
            return max(base_bid, target)
    else:
        # Not urgent: conserve budget
        bid = min(base_bid, my_status['budget'])
        # However, if supply is low and many opponents, we might need to secure water later
        if max_possible_winners <= num_alive and supply < 20:
            bid = max(bid, DAILY_SALARY * 0.5)
        return bid
"""
