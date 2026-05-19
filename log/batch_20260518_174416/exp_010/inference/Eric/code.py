# ============================================================
# Experiment: exp_010
# Agent: Eric
# Source: exp_010
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    import math
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = int(day_context['supply'])  # Convert to int
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Look at yesterday's opponent bids if available
    max_opponent_bid_yesterday = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = float(prev['bid'])
            if bid > max_opponent_bid_yesterday:
                max_opponent_bid_yesterday = bid
    
    # Base bid: moderate fraction of salary
    base_frac = 0.3
    
    # Adjust based on HP
    if hp <= 2:
        base_frac = 0.9
    elif hp <= 4:
        base_frac = 0.6
    elif hp == 5:
        base_frac = 0.5
    
    # Adjust for day (final days more aggressive)
    total_days = 10
    days_left = total_days - day
    if days_left <= 2:
        base_frac = min(base_frac + 0.2, 1.0)
    
    # Adjust for supply scarcity
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    if supply_norm < 0.3:
        base_frac = min(base_frac + 0.15, 1.0)
    
    # If opponent bid high yesterday, match or undercut slightly
    if max_opponent_bid_yesterday > 0:
        if hp <= 3:
            # Must win: bid just above yesterday's max
            bid = max(DAILY_SALARY * base_frac, min(max_opponent_bid_yesterday + 0.5, budget))
        else:
            # Conservative: stay near base, but if base is too low, raise slightly
            bid = max(DAILY_SALARY * base_frac, min(max_opponent_bid_yesterday * 0.8, budget))
    else:
        bid = DAILY_SALARY * base_frac
    
    # Ensure bid is within budget and reasonable range
    bid = max(0, min(budget, bid))
    # Round to 2 decimals
    bid = round(bid, 2)
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = day_context['day']
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine target bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # Slightly above max to outbid, but avoid overpaying if supply is high
        # Adjust based on supply: lower supply -> higher competition
        if supply < (MIN_SUPPLY + MAX_SUPPLY) / 2:
            target = max_prev + 2.0
        else:
            target = max_prev + 1.0
    else:
        # No info, bid conservatively based on hp and supply scarcity
        target = DAILY_SALARY * 0.6  # default: 84
    
    # Adjust for desperation
    if hp <= 2 or no_water_days >= 2:
        # Need water urgently
        bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        # Moderate urgency
        bid = min(budget, max(target, DAILY_SALARY * 0.7))
    else:
        # Healthy: try to save money
        # If yesterday bids were very high, we might still need to compete
        if yesterday_bids and max_prev >= DAILY_SALARY * 0.8:
            bid = min(budget, max(target, DAILY_SALARY * 0.5))
        else:
            bid = min(budget, max(target * 0.9, DAILY_SALARY * 0.4))
    
    # Ensure we don't bid more than budget
    bid = max(0, min(budget, bid))
    # Convert to float and return
    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    
    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    
    # Determine base bid from yesterday's pressure
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If yesterday's max was very high, we need to be competitive
        if max_prev >= 100:
            target = max_prev + 2.0
        else:
            target = max_prev + 5.0
    else:
        target = DAILY_SALARY * 0.5  # default
    
    # Adjust based on my own health and supply
    hp = my_status['hp']
    budget = my_status['budget']
    
    if hp <= 2:
        # Urgent need for water
        target = max(target, DAILY_SALARY * 0.9)
    elif supply < 18:
        # Low supply, high competition
        target = max(target, DAILY_SALARY * 0.65)
    elif supply > 22:
        # High supply, can lower bid
        target = min(target, DAILY_SALARY * 0.4)
    else:
        # Medium supply
        target = max(target, DAILY_SALARY * 0.5)
    
    # Ceiling by budget and salary
    bid = min(budget, target, DAILY_SALARY)
    # Ensure non-negative
    bid = max(0, bid)
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
    
    # Gather yesterday's bids from alive opponents who have trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
    else:
        max_prev = 0

    # Decide bid based on HP and opponent pressure
    if hp <= 2:
        # desperate: bid up to 90% of salary or just above max_prev
        target = max(DAILY_SALARY * 0.9, max_prev + 5)
        return min(budget, target)
    else:
        # comfortable: bid moderately, but if opponent pressure is high, respond
        if max_prev >= DAILY_SALARY * 0.7:
            # need to outbid slightly to not always lose
            target = max_prev + 2
        else:
            target = DAILY_SALARY * 0.5
        target = min(target, budget)
        # Ensure at least 1 to avoid 0 bid when supply is low? Not needed but safe
        return max(1, target)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0
    
    # Determine urgency based on HP and no_water_days
    if hp <= 2:
        urgency = 2.0
    elif hp <= 4:
        urgency = 1.7
    elif no_water_days >= 2:
        urgency = 1.5
    elif no_water_days >= 1:
        urgency = 1.3
    else:
        urgency = 1.0
    
    # Base fraction of salary
    if urgency >= 1.7:
        base_bid = DAILY_SALARY * 0.95
    elif urgency >= 1.3:
        base_bid = DAILY_SALARY * 0.8
    else:
        base_bid = DAILY_SALARY * 0.55
    
    # Supply scarcity: number of possible winners
    supply_capacity = int(supply // WATER_REQ)
    if supply_capacity <= 1:
        scarcity = 1.3
    elif supply_capacity == 2:
        scarcity = 1.1
    else:
        scarcity = 1.0
    
    target_bid = base_bid * scarcity
    
    # React to previous high bids
    if max_prev_bid > DAILY_SALARY * 0.8:
        target_bid = max(target_bid, max_prev_bid * 0.9)
    
    # Ensure not exceed budget and reasonable cap
    max_allowed = min(budget, DAILY_SALARY * 2)
    final_bid = min(target_bid, max_allowed)
    
    # Override for critical situations
    if hp <= 2 or no_water_days >= 2:
        if max_prev_bid > 0:
            final_bid = min(budget, max_prev_bid * 1.1)
        else:
            final_bid = min(budget, DAILY_SALARY * 0.95)
    
    return max
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Collect last bids from alive opponents
    last_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace and trace['bid'] is not None:
                last_bids.append(trace['bid'])

    # Estimate required water units (integer division)
    required_units = int(hp // WATER_REQ) + 1  # need at least 1 unit per day
    if no_water_days > 0:
        required_units += no_water_days
    required_units = min(required_units, int(supply // WATER_REQ))  # cannot exceed supply

    # Baseline: minimum bid to get one unit
    min_bid = max(1, DAILY_SALARY * 0.1)

    # Determine if we need to win today (hp low or no water)
    urgent = hp <= 2 or no_water_days >= 1

    if urgent:
        # Need water: outbid the average last bid of others, or at least 80% salary
        if last_bids:
            avg_bid = sum(last_bids) / len(last_bids)
            target = max(avg_bid + 1, DAILY_SALARY * 0.75)
        else:
            target = DAILY_SALARY * 0.8
        return min(budget, target)
    else:
        # Not urgent: bid low, or stay just below average to conserve
        if last_bids:
            avg_bid = sum(last_bids) / len(last_bids)
            target = min(avg_bid * 0.7, DAILY_SALARY * 0.5)
        else:
            target = DAILY_SALARY * 0.4
        return min(budget, max(min_bid, target))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine previous bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None and trace.get('status') != 'error':
            prev_bids.append(trace['bid'])
    
    # If first day or no previous data, use default
    if day == 1 or not prev_bids:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        return min(budget, DAILY_SALARY * 0.5)
    
    max_prev_bid = max(prev_bids)
    
    # Decide bid based on pressure from last round
    if max_prev_bid >= 100:
        # aggressive opponents; we need to compete
        target_bid = DAILY_SALARY * 0.7  # 98
        if hp <= 3:
            target_bid = max(target_bid, DAILY_SALARY * 0.9)
    else:
        # lower competition
        target_bid = DAILY_SALARY * 0.35  # 49
        if hp <= 3:
            target_bid = max(target_bid, DAILY_SALARY * 0.7)
    
    # Ensure we don't bid more than budget
    return min(budget, target_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents) + 1
    
    # own urgency: low hp or already without water
    if hp <= 2 or no_water_days >= 1:
        own_urgency = 'high'
    elif hp <= 5:
        own_urgency = 'medium'
    else:
        own_urgency = 'low'
    
    # analyze opponents
    desperate_opponents = 0
    prev_bids = []
    for o in alive_opponents.values():
        if o['hp'] <= 2:
            desperate_opponents += 1
        prev = o.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.7
    
    # estimate competition intensity
    supply_per_player = supply / num_alive
    scarcity = supply_per_player < WATER_REQ
    
    # decide target bid
    if own_urgency == 'high':
        # must win water at almost any cost
        if desperate_opponents > 0:
            # outbid maximum possible desperation bid (approx salary)
            target = min(budget, DAILY_SALARY * 0.95)
        else:
            # still need water, but can be moderate
            target = min(budget, max(DAILY_SALARY * 0.8, avg_prev_bid + 2))
    elif own_urgency == 'medium':
        # can afford to let some water go if price high
        if scarcity or desperate_opponents >= 2:
            target = min(budget, max(DAILY_SALARY * 0.6, avg_prev_bid + 1))
        else:
            target = min(budget, DAILY_SALARY * 0.5)
    else:  # low urgency
        # not desperate, save money
        if desperate_opponents >= 1:
            # let them fight, bid low
            target = min(budget, DAILY_SALARY * 0.4)
        else:
            target = min(budget, DAILY_SALARY * 0.3)
    
    # ensure positive bid and budget constraint
    bid = max(0.1, target)
    return min(budget, bid)
"""
