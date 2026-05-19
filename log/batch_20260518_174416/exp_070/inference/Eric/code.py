# ============================================================
# Experiment: exp_070
# Agent: Eric
# Source: exp_070
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if day == 1:
        return min(budget, SALARY * 0.3)
    else:
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
        if yesterday_bids:
            max_prev_bid = max(yesterday_bids)
            if hp <= 2:
                return min(budget, max(SALARY * 0.8, max_prev_bid + 1))
            else:
                return min(budget, max(SALARY * 0.4, max_prev_bid + 0.5))
        else:
            return min(budget, SALARY * 0.35)
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

    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    supply = day_context['supply']

    # Get yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Determine our urgency
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # If desperately thirsty (critical hp), bid high
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * 0.9
        if prev_bids:
            target = max(target, max(prev_bids) + 10)
        return min(budget, target)

    # If supply is low, more competition
    if supply < MIN_SUPPLY + 3:
        target = DAILY_SALARY * 0.7
        if prev_bids:
            target = max(target, max(prev_bids) + 5)
        return min(budget, target)

    # Normal day: use opponent history if available
    if prev_bids:
        # We want to be slightly above the median to avoid overbidding
        median_bid = sorted(prev_bids)[int(len(prev_bids) // 2)]
        # But if our hp is decent, bid moderately
        target = median_bid + 5
        # Cap at 85% salary to preserve budget
        target = min(target, DAILY_SALARY * 0.85)
        return min(budget, target)

    # No history: use supply-based default
    # Lower supply -> higher bid
    default = DAILY_SALARY * (1 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    default = max(default, DAILY_SALARY * 0.3)
    return min(budget, default)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    WATER_REQ = 8
    DAILY_SALARY = 140
    max_bid = budget

    # number of winners possible given supply
    winners_possible = supply // WATER_REQ  # integer after int(supply)

    # yesterday bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        opp_max_last = max(yesterday_bids)
    else:
        opp_max_last = 0.0

    # decision based on HP and competition
    if hp <= 2:
        # desperate, go high
        bid = min(max_bid, DAILY_SALARY * 1.5)
    elif hp <= 4:
        # moderate need, beat expected top bid
        bid = min(max_bid, max(DAILY_SALARY * 0.8, opp_max_last + 2.0))
    else:
        # healthy, conserve
        if winners_possible >= 2:
            bid = min(max_bid, max(DAILY_SALARY * 0.4, opp_max_last + 1.0))
        else:
            bid = min(max_bid, max(DAILY_SALARY * 0.5, opp_max_last + 2.0))

    # ensure we don't bid more than budget and not negative
    bid = max(0.0, min(bid, max_bid))
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

    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])

    # Determine urgency
    urgent = (hp <= 2) or (no_water_days >= 1)

    base_bid = DAILY_SALARY * 0.6
    if prev_bids:
        max_prev = max(prev_bids)
        base_bid = max(base_bid, max_prev + 1)
    else:
        base_bid = DAILY_SALARY * 0.5

    if urgent:
        bid = min(budget, max(base_bid, DAILY_SALARY * 0.9))
    else:
        bid = min(budget, base_bid * 0.85)

    # Avoid overbidding when supply is plentiful
    if supply >= 20 and not urgent:
        bid = min(bid, DAILY_SALARY * 0.45)

    # Ensure we never bid more than budget and at least 0
    bid = max(0, min(budget, bid))
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        bid = min(my_budget, DAILY_SALARY * 0.4)
        return int(bid)
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if my_hp <= 2 or no_water_days >= 1:
            needed = max(DAILY_SALARY * 0.9, highest_prev + 1.0)
        elif my_hp <= 5:
            needed = max(DAILY_SALARY * 0.6, highest_prev + 0.5)
        else:
            needed = max(DAILY_SALARY * 0.35, highest_prev * 0.8)
        bid = min(my_budget, needed)
    else:
        if my_hp <= 2:
            bid = min(my_budget, DAILY_SALARY * 0.95)
        elif my_hp <= 5:
            bid = min(my_budget, DAILY_SALARY * 0.7)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.5)
    bid = max(bid, 0.0)
    return int(bid)
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
    current_day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return int(min(budget, DAILY_SALARY * 0.3))
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base aggression from HP
    if hp <= 2:
        aggression = 0.95
    elif hp <= 5:
        aggression = 0.7
    else:
        aggression = 0.4
    
    # Adjust based on supply scarcity
    supply_percent = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_percent < 0.3:
        aggression += 0.2
    
    # Adjust based on day (late days need higher bids)
    if current_day >= 7:
        aggression += 0.15
    
    aggression = min(aggression, 1.0)
    
    # Baseline bid from aggression
    base_bid = DAILY_SALARY * aggression
    
    # Consider yesterday's highest bid to stay competitive
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If we need to surpass because of low HP, we may exceed
        target = max(base_bid, max_yesterday + 1.5)
    else:
        target = base_bid
    
    # Ensure we don't exceed budget and don't waste too much
    target = min(budget, target)
    target = max(target, 0)
    
    # Ensure result is integer (convert to int)
    return int(target)
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
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents)
    
    # Determine base bid from own need
    if hp <= 2 or no_water_days >= 1:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base_bid = min(budget, DAILY_SALARY * 0.7)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.5)
    
    # Adjust based on opponent traces from yesterday (assume similar behavior)
    max_prev_bid = 0
    for oid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # If opponents historically bid high, we may need to increase
    if max_prev_bid > 100:
        # Aggressive opponents, so avoid being undercut if we are desperate
        if hp <= 4:
            base_bid = min(budget, max(base_bid, max_prev_bid * 0.95))
        else:
            base_bid = min(budget, base_bid)
    
    # Ensure minimum bid (if supply is low, need higher bid)
    min_water_needed = WATER_REQ
    # Estimate total demand: each opponent likely bids something
    estimated_opponent_demand = 0
    for oid, opp in alive_opponents.items():
        # Use previous trace to guess their bid today; if no trace, assume moderate
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            estimated_opponent_demand += prev['bid']
        else:
            estimated_opponent_demand += DAILY_SALARY * 0.5
    total_demand = estimated_opponent_demand + base_bid
    # If total demand exceeds supply, we need to bid more to secure water
    if supply < total_demand:
        # Increase bid proportionally
        shortage_ratio = supply / total_demand
        if shortage_ratio < 0.5 and hp <= 3:
            base_bid = min(budget, base_bid * 1.5)
        elif shortage_ratio < 0.7:
            base_bid = min(budget, base_bid * 1.2)
    
    # Final bounding
    bid = max(1, min(budget, base_bid))
    # Ensure integer bid (may be float from calculations)
    bid = int(bid)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Extract previous bids from opponents' previous_trace
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Determine target bid based on highest previous bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If Cindy (or others) bid very high, bid slightly above to take water
        target = max_prev + 1.0
        # But consider budget and HP
        if my_status['hp'] <= 3:
            # Desperate: bid up to salary * 1.15 but not exceed budget
            bid = min(my_status['budget'], max(target, DAILY_SALARY * 1.15))
        else:
            # Comfortable: bid up to salary * 0.9 but not more than target if possible
            bid = min(my_status['budget'], target, DAILY_SALARY * 0.9)
    else:
        # No previous bids: use default based on HP
        if my_status['hp'] <= 3:
            bid = min(my_status['budget'], DAILY_SALARY * 1.1)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.6)
    
    # Ensure non-negative and within budget
    bid = max(0, bid)
    bid = min(bid, my_status['budget'])
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    desperate = (hp <= 2 or no_water_days >= 1)

    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                yesterday_bids.append(prev['bid'])

    if desperate:
        bid = SALARY * 0.9
    else:
        bid = SALARY * 0.6

    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        max
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
    
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    # Determine base bid from HP and supply
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.75  # ~105
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.55  # ~77
    else:
        base_bid = DAILY_SALARY * 0.40  # ~56
    
    # Adjust for supply tightness
    if supply < 20:
        base_bid *= 1.3
    elif supply < 22:
        base_bid *= 1.1
    
    # Check opponents' previous high bids
    max_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            bid_val = prev['bid']
            if bid_val is not None and bid_val > max_prev_bid:
                max_prev_bid = bid_val
    
    # If an opponent bid very high yesterday (e.g., >100), we may need to compete more when HP low
    if max_prev_bid > DAILY_SALARY * 0.75 and hp <= 2:
        base_bid = max(base_bid, max_prev_bid * 0.9)  # try to undercut but stay competitive
    
    # Final bid: ensure within budget and not exceed daily salary
    bid = min(budget, base_bid)
    bid = min(bid, DAILY_SALARY * 1.2)  # cap at 168
    bid = max(bid, 0.0)
    
    return bid
"""
