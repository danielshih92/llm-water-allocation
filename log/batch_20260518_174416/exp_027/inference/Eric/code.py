# ============================================================
# Experiment: exp_027
# Agent: Eric
# Source: exp_027
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = [o for o in opponents_status.values() if o['alive']]
    supply = day_context['supply']
    # Check if we have yesterday's trace to adapt
    highest_prev = 0
    for opp in alive:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            if prev['bid'] > highest_prev:
                highest_prev = prev['bid']
    # Base target
    if my_status['hp'] <= 3:
        target = DAILY_SALARY * 0.9
    else:
        n_alive = len(alive)
        if n_alive <= 2:
            target = DAILY_SALARY * 0.35
        else:
            target = DAILY_SALARY * 0.5
    # Adjust if opponent was aggressive yesterday
    if highest_prev > 0:
        # We want to beat the highest if we need water, else stay slightly below
        if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
            target = max(target, highest_prev + 2.0)
        else:
            # Try to undercut if possible to save money
            target = min(target, highest_prev - 1.0)
            if target < 5:
                target = DAILY_SALARY * 0.3
    # Ensure within budget and positive
    target = max(1.0, min(my_status['budget'], target))
    return target
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Estimate Cindy's expected bid from her previous trace
    cindy_bid_est = None
    if 'Cindy' in alive_opponents:
        prev = alive_opponents['Cindy'].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            cindy_bid_est = prev['bid']
    
    # Determine bid based on HP and supply
    if hp <= 2:
        # Critical: must get water, bid high
        target_bid = DAILY_SALARY * 0.9  # 126
        if cindy_bid_est and cindy_bid_est > target_bid:
            target_bid = min(cindy_bid_est + 10, DAILY_SALARY * 0.95)
    elif hp <= 5:
        # Moderate health
        target_bid = DAILY_SALARY * 0.6  # 84
        if cindy_bid_est and cindy_bid_est > target_bid:
            target_bid = min(cindy_bid_est + 5, DAILY_SALARY * 0.8)
    else:
        # Healthy: conserve budget
        target_bid = DAILY_SALARY * 0.4  # 56
        if cindy_bid_est and cindy_bid_est > target_bid:
            target_bid = min(cindy_bid_est + 2, DAILY_SALARY * 0.5)
    
    # Adjust for low supply (more competition)
    avg_supply = (15 + 25) / 2.0
    if supply < avg_supply:
        target_bid *= 1.2
    elif supply > avg_supply:
        target_bid *= 0.9
    
    # Cap to budget and ensure non-negative
    bid = min(budget, max(0, target_bid))
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    water_req = 8
    salary = 140

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base pressure from yesterday
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
    else:
        max_yesterday = 0.0
        avg_yesterday = 0.0

    # Estimate how many units will be claimed
    unit_price_est = max(avg_yesterday, salary * 0.5)
    # If supply is low, competition is fiercer
    if supply < 20:
        unit_price_est *= 1.2

    # My required bid to secure one unit
    base_bid = min(budget, max(unit_price_est, salary * 0.4))

    # Adjust based on HP
    if hp <= 2:
        # Critical: must win
        bid = min(budget, max(base_bid, salary * 0.9))
    elif hp <= 4:
        bid = min(budget, max(base_bid, salary * 0.75))
    else:
        # Comfortable: try to save money
        bid = min(budget, max(base_bid, salary * 0.5))

    # But if many opponents are alive, bid more aggressively
    if num_opponents >= 3:
        bid = min(budget, bid + 5)

    # Ensure bid is at least salary * 0.3 to avoid being too cheap
    bid = max(bid, salary * 0.3)

    # Prevent overspending: never bid more than 90% of budget if HP is high
    if hp > 5 and bid > budget * 0.6:
        bid = budget * 0.6

    # Round to 2 decimals
    return round(bid, 2)
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

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}

    # Extract yesterday's bids from opponents
    yesterday_bids = []
    for o in alive_opponents.values():
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    if no_water_days >= 2:
        # Desperate: bid high to survive
        base = DAILY_SALARY * 0.9
    elif hp <= 3:
        # Low health: need water
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.5

    # Opponent pressure adjustment
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If opponents were very aggressive, reduce bid to save budget for later
        if max_prev > DAILY_SALARY * 0.85:
            base = min(base, DAILY_SALARY * 0.4)
        else:
            # Slightly above max_prev to outbid, but not exceed budget
            base = max(base, max_prev + 1.0)

    # Ensure bid is within budget and non-negative
    bid = min(budget, base)
    bid = max(0, bid)
    # Floor division for indices not needed, but ensure float safety
    # Return as float
    return float(bid)
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
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        prev_max = max(yesterday_bids)
        if my_hp <= 2:
            target = max(DAILY_SALARY * 0.9, prev_max + 1)
        elif my_hp <= 5:
            target = max(DAILY_SALARY * 0.6, prev_max + 0.5)
        elif supply <= MIN_SUPPLY + 2:
            target = max(DAILY_SALARY * 0.5, prev_max + 0.5)
        else:
            target = max(DAILY_SALARY * 0.3, prev_max + 0.2)
        return min(my_budget, target)
    else:
        if my_hp <= 2:
            return min(my_budget, DAILY_SALARY * 0.9)
        return min(my_budget, DAILY_SALARY * 0.55)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from traces
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    
    supply = day_context['supply']
    # Calculate how many can be fully satisfied
    max_winners = int(supply // WATER_REQ)  # explicit int for safety
    
    # Determine desperation
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    
    # Base bid: try to beat yesterday's highest by a small margin but stay reasonable
    if no_water > 0 or hp <= 2:
        # Desperate: bid high to guarantee water
        bid = DAILY_SALARY * 0.85
    else:
        # Normal: try to beat highest previous bid by 1.5, but not exceed 80% of salary
        bid = max(DAILY_SALARY * 0.4, max_prev_bid + 1.5)
        bid = min(bid, DAILY_SALARY * 0.75)
    
    # If supply is very low, need to be more aggressive
    if supply < 16:
        bid = max(bid, DAILY_SALARY * 0.7)
    
    # Ensure we do not bid more than budget
    bid = min(bid, budget)
    
    # Also ensure a minimum bid of 1 if budget allows
    if budget >= 1.0 and bid < 1.0:
        bid = 1.0
    
    return bid
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
    no_water_days = my_status['no_water_days']
    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    previous_bids = []
    for aid, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            previous_bids.append(trace['bid'])
    base_bid = DAILY_SALARY * 0.5
    if hp <= 2:
        if previous_bids:
            base_bid = max(previous_bids) + 5.0
        else:
            base_bid = DAILY_SALARY * 0.95
    elif hp <= 4 or no_water_days >= 2:
        if previous_bids:
            base_bid = max(previous_bids) + 2.0
        else:
            base_bid = DAILY_SALARY * 0.7
    else:
        if previous_bids:
            max_prev = max(previous_bids)
            if max_prev > DAILY_SALARY * 0.8:
                base_bid = min(DAILY_SALARY * 0.4, max_prev - 10.0)
            else:
                base_bid = max(DAILY_SALARY * 0.5, max_prev + 1.0)
        else:
            base_bid = DAILY_SALARY * 0.4
    # Ensure bid is within budget and non-negative
    bid = max(0.0, min(float(budget), base_bid))
    # Ensure we don't exceed supply? No, bid is not limited by supply directly; but we can't buy more than supply. However, we just bid.
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    if my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 0.9
    else:
        if prev_bids:
            highest_prev = max(prev_bids)
            base_bid = highest_prev + 2.0
        else:
            base_bid = DAILY_SALARY * 0.6
    bid = min(my_status['budget'], DAILY_SALARY, base_bid)
    if my_status['no_water_days'] > 0:
        bid = min(my_status['budget'], DAILY_SALARY, max(bid, DAILY_SALARY * 0.95))
    return max(0, bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    # Estimate number of winners possible
    max_winners = int(supply // WATER_REQ)
    # Determine base bid based on HP
    if hp <= 2:
        # Must win at all costs
        bid = min(budget, DAILY_SALARY * 0.98)
    elif hp <= 5:
        # Need water but can be moderate
        if max_winners >= 3:
            bid = min(budget, DAILY_SAL
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Find highest previous bid among alive opponents
    highest_prev = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > highest_prev:
                highest_prev = prev['bid']
    
    # Base bid: try to outbid highest previous by 1.5, but not exceed budget
    base_bid = min(budget, highest_prev + 1.5)
    
    # Emergency: if out of water for 2+ days, bid high
    if my_status['no_water_days'] >= 2 or hp <= 2:
        return min(budget, DAILY_SALARY * 0.95)
    
    # Late game: days 7-10, be more aggressive
    if day >= 7:
        return min(budget, max(base_bid, DAILY_SALARY * 0.8))
    
    # Early game: conserve budget, bid modestly
    if day <= 3:
        return min(budget, max(base_bid, DAILY_SALARY * 0.6))
    
    # Mid game: moderate
    return min(budget, max(base_bid, DAILY_SALARY * 0.7))
"""
