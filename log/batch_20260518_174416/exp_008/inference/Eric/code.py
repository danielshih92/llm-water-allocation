# ============================================================
# Experiment: exp_008
# Agent: Eric
# Source: exp_008
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # Look at yesterday's highest bid from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # If we have previous data, react
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # Aggressive reaction if opponent was desperate
        if highest_prev >= DAILY_SALARY * 0.7:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.35)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            # Bid slightly above their highest to secure water
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev + 2))
    # Default based on HP
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine baseline bid
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    else:
        avg_prev = DAILY_SALARY * 0.5
    
    # Adjust based on personal state
    if hp <= 2 or no_water_days >= 1:
        # Need water urgently
        target = max(avg_prev + 2, DAILY_SALARY * 0.8)
    elif hp <= 5:
        target = max(avg_prev, DAILY_SALARY * 0.5)
    else:
        target = min(avg_prev * 0.7, DAILY_SALARY * 0.5)
    
    # Consider supply abundance
    if supply >= 20:
        target = target * 0.8
    
    # Ensure we don't overspend
    max_afford = budget * 0.9  # leave 10% buffer
    bid = min(target, max_afford)
    bid = max(bid, 0)  # non-negative
    
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace')
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    target_bid = max_prev_bid + 1.0
    if no_water_days >= 2 or hp <= 2:
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    elif hp <= 5:
        target_bid = max(target_bid, DAILY_SALARY * 0.6)
    else:
        if target_bid < DAILY_SALARY * 0.3:
            target_bid = DAILY_SALARY * 0.3
    bid = min(budget, target_bid)
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
    alive = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive:
        t = opp.get('previous_trace', {})
        if t and t.get('bid') is not None:
            prev_bids.append(t['bid'])
    max_prev = max(prev_bids) if prev_bids else 0.0
    supply = day_context['supply']

    hp_threshold = 3
    if my_status['no_water_days'] > 0:
        # desperate
        bid = min(my_status['budget'], max(max_prev + 2.0, DAILY_SALARY * 0.95))
    elif my_status['hp'] <= hp_threshold:
        bid = min(my_status['budget'], max(max_prev + 1.0, DAILY_SALARY * 0.85))
    else:
        base = max_prev + 0.5
        if supply < WATER_REQ * 1.5:
            base = max_prev + 1.5
        bid = min(my_status['budget'], base, DAILY_SALARY * 0.7)
    # ensure at least small bid
    bid = max(bid, 0.0)
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)
    
    # Determine opponent aggressiveness from yesterday's bid
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid on HP and supply scarcity
    scarcity_factor = max(0, (WATER_REQ - supply) / WATER_REQ)  # negative if supply > req
    hp_factor = max(0, (WATER_REQ - hp) / WATER_REQ)  # high when hp low
    base_urgency = max(scarcity_factor, hp_factor)
    
    # Adjust based on highest opponent previous bid
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        if max_prev_bid > DAILY_SALARY * 0.85:
            # Opponent is aggressive, reduce bid to save budget
            aggression_penalty = 0.3
        elif max_prev_bid > DAILY_SALARY * 0.6:
            aggression_penalty = 0.5
        else:
            aggression_penalty = 0.7
    else:
        aggression_penalty = 0.6
    
    # Desired bid as fraction of salary based on urgency
    if base_urgency > 0.6:
        desired_fraction = 0.9
    elif base_urgency > 0.3:
        desired_fraction = 0.7
    else:
        desired_fraction = 0.5
    
    # Combine with aggression penalty
    bid = DAILY_SALARY * desired_fraction * aggression_penalty
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Ensure minimum bid if we need water badly and have budget
    if no_water_days >= 2 or hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.6)
    
    return min(bid, budget)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Get yesterday's bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine base bid strategy
    base_bid = DAILY_SALARY * 0.3  # conservative
    if hp <= 5:
        base_b
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from previous_trace
    yesterday_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(float(prev['bid']))

    # Base bid: 40% of salary
    base_bid = DAILY_SALARY * 0.4

    # Desperation check
    desperate = (hp <= 2) or (no_water_days >= 2)
    if desperate:
        # Need water badly: bid up to 90% of budget, but cap at salary
        target = min(budget, DAILY_SALARY * 0.9)
        return target

    # If we have enough hp, we can be more conservative
    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If someone bid high yesterday, they might again; outbid slightly
        if max_prev > DAILY_SALARY * 0.7:
            target = max(base_bid, max_prev + 2.0)
        else:
            target = base_bid
    else:
        target = base_bid

    # Consider supply: if low supply, more competition -> bid higher
    if supply < 18:
        target = target * 1.3
    elif supply > 22:
        target = target * 0.9

    # Ensure within budget and reasonable
    target = min(budget, target)
    target = max(0, target)
    return target
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])  # ensure int
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {oid: opp for oid, opp in opponents_status.items() if opp['alive']}

    # Collect yesterday's bids from opponents' previous_trace if available
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Determine a base bid
    # More urgent if hp is low or no_water_days is high
    urgency = 0.0
    if hp <= 2:
        urgency = 0.9
    elif hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.5

    # Adjust based on supply: less supply means more competition, increase bid
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # Lower supply_ratio means scarce, so increase multiplier
    supply_factor = 1.0 + (1.0 - supply_ratio) * 0.3

    # Base bid is a fraction of daily salary adjusted by urgency and supply
    bid = DAILY_SALARY * urgency * supply_factor

    # If we have previous opponents bids, we can adapt slightly
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponents were high, we may need to match or exceed if urgent
        if max_prev > bid and urgency > 0.6:
            bid = max(bid, max_prev + 1.0)
        # If opponents were low, we can save budget if we are not urgent
        elif max_prev < bid and urgency <= 0.5:
            bid = min(bid, max_prev + 2.0)

    # Cap by budget
    bid = max(0, min(budget, bid))
    # Ensure integer (may be float due to calculations, but bid function accepts float? The problem says return value should be numeric, likely float is fine, but to be safe keep as float)
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.5)
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev = max(prev_bids) if prev_bids else 0
    hp = my_status['hp']
    budget = my_status['budget']
    # Aggressive if low HP
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        bid = min(budget, DAILY_SALARY * 0.8)
    else:
        # Healthy: try to undercut the max previous bid by a small margin to save budget
        # But ensure we bid enough to possibly win at least once
        base = max(DAILY_SALARY * 0.5, max_prev - 10)
        bid = min(budget, base)
    # Ensure bid non-negative and affordable
    bid = max(0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    # Collect yesterday's bids from alive opponents' traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    # Our health assessment
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    # Determine bid
    if hp <= 3 or no_water_days >= 1:
        # Need water urgently
        if yesterday_bids:
            target = max(yesterday_bids) + 2.0
        else:
            target = DAILY_SALARY * 0.85
        return min(budget, max(target, DAILY_SALARY * 0.5))
    else:
        # Healthy, try to save
        if yesterday_bids:
            highest_prev = max(yesterday_bids)
            if highest_prev > DAILY_SALARY * 0.7:
                # Opponents aggressive, we can try low if we are healthy
                return min(budget, max(DAILY_SALARY * 0.3, highest_prev * 0.6))
            else:
                return min(budget, max(DAILY_SALARY * 0.4, highest_prev + 1.5))
        else:
            return min(budget, DAILY_SALARY * 0.5)
"""
