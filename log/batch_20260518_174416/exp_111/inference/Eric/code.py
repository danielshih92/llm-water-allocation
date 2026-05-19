# ============================================================
# Experiment: exp_111
# Agent: Eric
# Source: exp_111
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid: moderate
    bid = DAILY_SALARY * 0.45
    
    # Use previous traces if available
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        # If we are desperate, outbid max_prev slightly
        if hp <= 3 or no_water >= 1:
            bid = max(bid, max_prev + 1.5)
        else:
            # If comfortable, bid just above average to win cheaply
            bid = max(bid, avg_prev + 1.0)
    else:
        # No history: escalate if low HP
        if hp <= 2:
            bid = DAILY_SALARY * 0.85
        elif hp <= 4:
            bid = DAILY_SALARY * 0.65
    
    # Keep within budget and cap at salary
    bid = min(bid, budget)
    bid = max(bid, 0.5)  # minimum bid
    return bid
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
    no_water = my_status['no_water_days']
    
    alive = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive) + 1
    
    # Check if any opponent had high bid yesterday
    high_bid_yesterday = False
    for opp in opponents_status.values():
        trace = opp.get('previous_trace', {})
        if trace and isinstance(trace.get('bid'), (int, float)):
            if trace['bid'] > 80:
                high_bid_yesterday = True
                break
    
    fair_share = supply / num_alive
    
    # Desperation threshold
    if hp <= 3 or no_water >= 2:
        # Need water badly: bid up to 90% salary or budget
        max_bid = min(budget, 0.9 * DAILY_SALARY)
        # But if there was a high bidder, ensure we beat them if possible
        if high_bid_yesterday:
            # Estimate they'll bid similar; we need to beat but not overspend
            # Try to bid just above last known high bid (if budget permits)
            last_high = max([opp.get('previous_trace', {}).get('bid', 0) for opp in opponents_status.values() if opp.get('previous_trace')])
            bid = min(max_bid, max(fair_share, last_high + 1.0))
        else:
            bid = min(max_bid, max(fair_share, DAILY_SALARY * 0.5))
    else:
        # Not desperate: bid conservatively, but enough to possibly win against low bidders
        base_bid = max(1, min(fair_share, DAILY_SALARY * 0.4))
        if high_bid_yesterday:
            # Avoid competing; bid low
            bid = min(budget, base_bid)
        else:
            bid = min(budget, max(base_bid, supply * 0.3))
    
    # Ensure bid is non-negative and within budget
    bid = max(0, min(budget, int(bid)))
    return float(bid)
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Look at yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.7
    if yesterday_bids:
        avg_high = sum(sorted(yesterday_bids, reverse=True)[:max(1, len(yesterday_bids)//2)]) / max(1, len(yesterday_bids)//2)
        base_bid = avg_high + 1.0  # slightly above average high

    # Supply adjustment: if supply is high, we can bid lower
    supply_factor = supply / 25.0  # 0.6 to 1.0
    if supply_factor > 0.85:
        base_bid *= 0.9

    # Urgency based on HP
    if hp <= 3:
        urgency = 1.3
    elif hp <= 5:
        urgency = 1.1
    else:
        urgency = 0.95

    bid = min(budget, base_bid * urgency)
    bid = max(bid, 1.0)  # minimum positive bid
    return round(bid, 2)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    salary = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: if we have recent bids, adapt
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If opponents were aggressive, try a moderate undercut
        if max_yesterday >= salary * 0.85:
            # They are spending high; if we are safe, save money
            if hp > 3:
                base = min(budget, salary * 0.4)
            else:
                base = min(budget, salary * 0.85)
        else:
            # Opponents moderate, outbid slightly
            base = min(budget, max(salary * 0.55, max_yesterday + 1.5))
    else:
        # No trace, use HP heuristic
        if hp <= 2:
            base = min(budget, salary * 0.9)
        else:
            base = min(budget, salary * 0.55)
    
    # Ensure we don't bid more than budget
    bid = max(0.0, min(budget, base))
    # If we are severely dehydrated, increase bid
    if no_water_days >= 2:
        bid = min(budget, max(bid, salary * 0.8))
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))
    
    # Gather yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine supply tightness
    supply = day_context['supply']
    # Ensure integer for potential list indexing (not used here but safe)
    supply_int = int(supply)
    
    # Base bid calculation
    if my_status['hp'] <= 2:
        # Desperate: bid up to 95% of salary or budget
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        # Moderate health: bid up to 70% of salary
        bid = min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        # Healthy: bid conservatively
        bid = min(my_status['budget'], DAILY_SALARY * 0.45)
    
    # React to yesterday's high bids if present
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If opponents were aggressive, increase bid moderately
        if max_yesterday > DAILY_SALARY * 0.85:
            # High pressure: bid just enough to stay competitive if healthy, else go higher
            if my_status['hp'] > 3:
                bid = min(bid, DAILY_SALARY * 0.3)
            else:
                bid = min(my_status['budget'], max(bid, max_yesterday + 1.0))
        else:
            # Normal pressure: bid slightly above yesterday's max
            bid = min(my_status['budget'], max(bid, max_yesterday + 0.5))
    
    # Ensure bid is non-negative and not exceeding budget
    bid = max(0.0, min(bid, my_status['budget']))
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    max_prev_bid = 0.0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev['bid']
                if b > max_prev_bid:
                    max_prev_bid = b
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    # ensure supply is int if needed
    if isinstance(supply, float):
        supply_int = int(supply)
    else:
        supply_int = supply
    # estimate number of alive opponents
    alive_count = sum(1 for o in opponents_status.values() if o['alive'])
    # base bid: enough to get water if supply is scarce
    if hp <= 3:
        # desperate: bid high to survive
        bid = min(budget, DAILY_SALARY * 1.2)
    elif max_prev_bid > DAILY_SALARY * 0.85:
        # opponents aggressive yesterday, match or slightly undercut
        bid = min(budget, max_prev_bid + 1.0)
    else:
        # conservative: bid just above average of previous max and min
        bid = min(budget, DAILY_SALARY * 0.65)
    # ensure we don't bid more than budget
    bid = min(bid, budget)
    # ensure bid is at least 0
    bid = max(bid, 0.0)
    return bid
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
    return 15.0
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine a target bid based on yesterday's maximum
    if prev_bids:
        max_prev = max(prev_bids)
    else:
        max_prev = 0.0

    # Base bid: need to secure water if hp is low
    if hp <= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 4:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.5

    # Adjust based on competition: if max_prev is high, we need to beat it
    target = max(base, max_prev + 1.0)

    # Consider supply: if supply is very low, we might need to bid higher
    if supply < 18:
        target *= 1.2
    elif supply > 22:
        target *= 0.8

    # Ensure we don't exceed budget or go negative
    bid = min(budget, max(0.0, target))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid calculation
    if no_water_days >= 1 or hp <= 2:
        # Desperate: bid high
        target_bid = min(budget, DAILY_SALARY * 0.85)
    else:
        # Conservative: try to beat yesterday's highest bid slightly
        if yesterday_bids:
            highest_prev = max(yesterday_bids)
            # To avoid overbidding, use a small margin
            target_bid = min(budget, max(DAILY_SALARY * 0.4, highest_prev + 2.0))
        else:
            # No history, use a default moderate bid
            target_bid = min(budget, DAILY_SALARY * 0.55)

    # Ensure bid is within budget and non-negative
    bid = max(0.0, min(budget, target_bid))
    return bid
"""
