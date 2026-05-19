# ============================================================
# Experiment: exp_030
# Agent: Eric
# Source: exp_030
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
    no_water_days = my_status['no_water_days']
    
    # Base bid on urgency
    if hp <= 2:
        # Desperate: bid high to guarantee water
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # Moderate need: bid average
        bid = min(budget, DAILY_SALARY * 0.6)
    else:
        # Healthy: conserve budget, bid low
        bid = min(budget, DAILY_SALARY * 0.35)
    
    # Ensure we don't bid more than budget
    bid = min(bid, budget)
    
    # Round to 2 decimals and return
    return round(bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    
    # Base bid depends on HP: lower HP -> higher bid
    if hp <= 2:
        base_bid = 110
    elif hp <= 5:
        base_bid = 80
    else:
        base_bid = 50
    
    # Adjust for supply: if supply is high, we might not need to bid as high
    supply_factor = max(1.0, supply / 20.0)  # supply between 15 and 25 -> factor 1.0 to 1.25
    adjusted_bid = int(base_bid * (1.0 / supply_factor))
    
    # Ensure bid is within budget and reasonable
    bid = min(budget, max(10, adjusted_bid))
    
    # If budget is very low, bid everything
    if budget < 30:
        bid = budget
    
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    if yesterday_bids:
        max_prev = max(yesterday_bids)
    else:
        max_prev = 0.0
    if supply < 18:
        multiplier = 1.1
    elif supply > 22:
        multiplier = 0.7
    else:
        multiplier = 0.9
    if hp <= 3:
        target = max(DAILY_SALARY * 1.0, max_prev * 1.05)
    else:
        target = max(DAILY_SALARY * 0.6, max_prev * 0.95)
    bid = target * multiplier
    bid = min(bid, budget)
    bid = max(bid, 0.0)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # supply as integer
    units = int(supply // WATER_REQ)  # number of water units available
    
    # Current status
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    # Alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0
    
    # Determine urgency
    urgent = (hp <= 2) or (no_water > 0)
    
    if urgent:
        base = max(DAILY_SALARY * 0.85, max_prev_bid + 2.0)
    else:
        base = max(DAILY_SALARY * 0.4, max_prev_bid + 1.0)
    
    # Supply scarcity adjustment
    if supply < 16:
        base *= 1.1
    
    # Ensure we don't bid more than budget
    final_bid = min(budget, base)
    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    num_winners = supply // WATER_REQ
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opp = [o for o in opponents_status.values() if o['alive']]
    max_prev_bid = 0.0
    for opp in alive_opp:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            max_prev_bid = max(max_prev_bid, trace['bid'])

    # Base bid: try to secure a win with minimal waste
    if num_winners == 1:
        # Need to be top, be aggressive based on threat
        if hp <= 2 or no_water > 0:
            bid = min(budget, DAILY_SALARY * 0.95)
        else:
            bid = min(budget, max(DAILY_SALARY * 0.7, max_prev_bid + 1.0))
    elif num_winners == 2:
        # Need top 2
        if hp <= 2 or no_water > 0:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, max(DAILY_SALARY * 0.5, max_prev_bid + 0.5))
    else:  # 3 winners
        if hp <= 2 or no_water > 0:
            bid = min(budget, DAILY_SALARY * 0.8)
        else:
            bid = min(budget, max(DAILY_SALARY * 0.35, max_prev_bid + 0.2))

    # Ensure minimum bid if absolutely necessary
    if hp <= 1 and no_water >= 1:
        bid = min(budget, DAILY_SALARY * 0.95)

    # Always respect budget
    return max(1.0, min(bid, budget))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Determine current day; day_context['day'] is the current day number (1-indexed)
    day = int(day_context['day']) if 'day' in day_context else 1
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']

    # Default bid for day 1 (no previous traces)
    if day == 1:
        # Conservative: bid 40% of salary to start
        bid = min(budget, DAILY_SALARY * 0.4)
        # If hp is very low, bid higher
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        return bid

    # For subsequent days, analyze opponents' previous traces
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    # Collect yesterday's bids from opponents that have a trace
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Determine a target bid based on pressure
    if prev_bids:
        highest_prev = max(prev_bids)
        # If any opponent previously bid aggressively, we may need to outbid
        # Consider that aggressive bidders tend to bid high again
        # Our target is slightly above the highest past bid, but within reason
        target = highest_prev + 1.0
        # Cap target by a fraction of salary to avoid extreme waste
        max_bid_ratio = 0.85 if hp > 2 else 0.95
        target = min(target, DAILY_SALARY * max_bid_ratio)
        # Ensure we have enough budget
        target = min(target, budget)
        # If we are desperate, still need to bid high
        if hp <= 2:
            target = max(target, DAILY_SALARY * 0.9)
            target = min(target, budget)
        return target
    else:
        # No previous traces available (unlikely after day 1)
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.4)
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
    my_hp = int(my_status['hp'])
    my_budget = my_status['budget']
    no_water = int(my_status['no_water_days'])
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    supply_per_player = supply / (len(alive_opponents) + 1) if alive_opponents else supply
    base_need = my_hp <= 3 or no_water >= 1
    if my_hp <= 2:
        # desperate: need water badly
        bid = min(my_budget, DAILY_SALARY * 1.1)
    elif my_hp <= 4:
        # moderate risk
        if max_prev_bid > DAILY_SALARY * 0.85 and supply_per_player >= WATER_REQ:
            bid = min(my_budget, DAILY_SALARY * 0.6)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.9)
    else:
        # healthy: can afford to lose a day
        if max_prev_bid > DAILY_SALARY * 0.85:
            bid = min(my_budget, DAILY_SALARY * 0.4)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.65)
    # Ensure minimum bid to not waste budget if bid is very low
    if bid < 10 and my_budget > 10:
        bid = 10
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    salary = 140
    water_req = 8

    # Collect previous bids from opponents alive in previous episode
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Compute target bid based on historical aggressiveness
    if prev_bids:
        # Average of max bids from each opponent? Use max to be safe
        # But we want to outbid the second highest? Use average of top two?
        sorted_bids = sorted(prev_bids, reverse=True)
        # Take the second highest if available, else highest
        target = sorted_bids[1] if len(sorted_bids) > 1 else sorted_bids[0]
        # Add a small increment to secure win, but cap at 70% of salary
        target = min(target + 2, salary * 0.7)
    else:
        target = salary * 0.5

    # Adjust for my health
    if hp <= 3:
        # desperate: bid aggressively to ensure water
        bid = min(budget, salary * 0.9)
    elif hp <= 5:
        # moderate health: slightly above target
        bid = min(budget, max(target, salary * 0.4))
    else:
        # healthy: conservative, just ensure survival
        bid = min(budget, max(target, salary * 0.3))

    # Ensure bid is within budget and positive
    bid = max(0, min(budget, int(bid)))
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    num_alive = len(alive_opponents)
    
    # Check if any opponent has previous_trace (non-empty)
    has_traces = any(v.get('previous_trace') and v['previous_trace'].get('bid') is not None for v in alive_opponents.values())
    
    if not has_traces:
        # Day 1 or no info: bid moderate
        bid = DAILY_SALARY * 0.7
        if my_hp <= 3:
            bid = DAILY_SALARY * 0.95
        return min(my_budget, bid)
    
    # Exploit yesterday's highest bid
    highest_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
    
    # Slightly outbid the
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    hp = my_status['hp']
    budget = my_status['budget']
    day = day_context['day']
    supply = int(day_context['supply'])
    if hp <= 2:
        # desperate: bid high to survive
        bid = min(budget, DAILY_SALARY * 0.95)
    elif day >= 8:
        # late days, need to preserve budget, but still compete
        target = min(budget, max(DAILY_SALARY * 0.5, max_prev_bid * 0.8))
        bid = target
    else:
        # mid game: bid slightly above yesterday's max to dominate
        target = min(budget, max(DAILY_SALARY * 0.6, max_prev_bid * 1.1 + 1.0))
        bid = target
    # ensure bid is at least some small positive to avoid default loss
    bid = max(bid, 1.0)
    return min(budget, bid)
"""
