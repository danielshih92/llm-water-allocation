# ============================================================
# Experiment: exp_099
# Agent: Eric
# Source: exp_099
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    if my_status['hp'] <= 2:
        bid = min(my_status['budget'], DAILY_SALARY * 0.8)
    else:
        bid = min(my_status['budget'], DAILY_SALARY * 0.4)
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's highest bid from alive opponents
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # Base bid: if no data, use salary fraction
    if max_prev_bid == 0:
        base_bid = SALARY * 0.5
    else:
        base_bid = max_prev_bid
    
    # Adjust based on HP and supply
    scarcity_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 1 if supply=15, 0 if 25
    hp_factor = 1.0 if hp <= 2 else 0.7  # desperate if low HP
    
    target_bid = base_bid * (1.0 + 0.3 * scarcity_factor + 0.2 * hp_factor)
    
    # Ensure at least minimum to be competitive
    if hp <= 2:
        target_bid = max(target_bid, SALARY * 0.9)
    else:
        target_bid = max(target_bid, SALARY * 0.5)
    
    # Do not exceed budget
    final_bid = min(budget, target_bid)
    
    # Also ensure positive bid
    final_bid = max(final_bid, 1.0)
    
    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    # Current day and supply
    day = day_context['day']
    supply = int(day_context['supply'])  # cast to int to avoid float index issues

    # My state
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        # Only me, bid minimal
        return min(budget, SALARY * 0.2)

    # Collect previous day bids (from trace)
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Compute average of previous bids if available
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
    else:
        avg_prev = SALARY * 0.8  # guess for first day
        max_prev = SALARY * 0.9

    # Determine target bid based on urgency and opponent pressure
    # If we are very thirsty or have low HP, bid aggressively
    if no_water >= 1 or hp <= 2:
        target = min(budget, max(SALARY * 0.9, max_prev + 1))
    elif hp <= 4:
        target = min(budget, max(SALARY * 0.7, avg_prev + 2))
    else:
        # Healthy: try to save money by undercutting if opponents were aggressive
        if max_prev >= SALARY * 0.85:
            # Opponents wasted a lot yesterday, they may be low budget today
            target = min(budget, SALARY * 0.4)
        else:
            # Otherwise, bid slightly above their average
            target = min(budget, max(SALARY * 0.5, avg_prev + 1))

    # Never bid more than we can afford, minimum 1 to avoid zero
    bid = max(1, target)
    bid = min(bid, budget)

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp_state in opponents_status.items():
        if opp_state['alive']:
            prev_trace = opp_state.get('previous_trace', {})
            if prev_trace and 'bid' in prev_trace:
                yesterday_bids.append(prev_trace['bid'])
    
    # Determine base target bid
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If opponent max was very high, they might be desperate; we can try to outbid slightly
        target = min(max_yesterday + 1.5, DAILY_SALARY * 0.95)
    else:
        target = DAILY_SALARY * 0.5  # default if no data
    
    # Adjust based on our health
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_status['no_water_days'] > 0:
        target = max(target, DAILY_SALARY * 0.75)
    
    # Ensure we do not exceed budget or go below 0
    bid = min(my_status['budget'], target)
    bid = max(0, bid)
    
    return int(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    
    # Determine supply tier: integer index
    # supply ranges 15-25, map to 0-10 roughly
    supply_tier = int(supply)  # use int to avoid float index
    
    # Base bid: less than daily salary, higher when supply low
    if supply_tier < 20:
        base_bid = DAILY_SALARY * 0.6
    else:
        base_bid = DAILY_SALARY * 0.3
    
    # Adjust based on HP
    if hp <= 3:
        # desperate: need water
        desired_bid = min(budget, DAILY_SALARY * 0.9)
    else:
        # comfortable: try to save
        desired_bid = min(budget, base_bid)
    
    # Consider if any opponent has huge budget (like Cindy)
    max_opp_budget = max([o['budget'] for o in alive_opponents]) if alive_opponents else 0
    if max_opp_budget > 500 and hp > 5:
        # They can outbid us easily, bid minimal
        desired_bid = min(desired_bid, DAILY_SALARY * 0.2)
    
    # Ensure non-negative
    return max(0.0, desired_bid)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from previous_trace
    last_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            last_bids.append(trace['bid'])

    # Determine base bid based on supply tightness
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    bid_base = DAILY_SALARY * (0.7 - 0.2 * supply_ratio)  # higher when supply low

    if my_status['hp'] <= 2:
        # Desperate: outbid anyone
        if last_bids:
            return min(budget, max(last_bids) + 5.0)
        else:
            return min(budget, DAILY_SALARY * 0.9)

    # Healthy: target second highest or average
    if len(last_bids) >= 2:
        sorted_bids = sorted(last_bids, reverse=True)
        target = sorted_bids[1]  # second highest
        # Slightly above if we need water, else just match
        if my_status['no_water_days'] > 0:
            bid = max(bid_base, target + 2.0)
        else:
            bid = max(bid_base, target + 0.5)
    elif len(last_bids) == 1:
        bid = max(bid_base, last_bids[0] + 1.5)
    else:
        bid = bid_base

    # Cap by budget and ensure positive
    bid = min(budget, bid)
    bid = max(0.0, bid)
    # Avoid floating index errors
    # No indexing needed in this version, but for safety use int() if any
    return float(bid)
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
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    n_alive = len(alive_opponents)
    
    # Collect last bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # If HP < 3, must win at almost any cost
    if hp <= 2:
        target = DAILY_SALARY * 0.9
    # If supply is high, bid low
    elif supply >= 20:
        target = DAILY_SALARY * 0.25
    # If we have enough HP, try to undercut if possible
    elif hp > 5 and prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = avg_prev + 2.0
    elif prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = max(avg_prev + 5.0, DAILY_SALARY * 0.5)
    else:
        target = DAILY_SALARY * 0.5
    
    # Bound by budget and not negative
    bid = min(budget, max(1.0, target))
    return bid
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
    no_water_days = my_status['no_water_days']
    
    # Determine water need: if no_water_days > 0 or hp <= 3, desperate
    desperate = (no_water_days > 0 or hp <= 3)
    # If supply lower than requirement, all need water, increase bid
    shortage = supply < WATER_REQ
    
    # Base bid: moderate % of salary
    if desperate:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif shortage:
        base_bid = min(budget, DAILY_SALARY * 0.7)
    else:
        # Normal: bid around half
        base_bid = min(budget, DAILY_SALARY * 0.5)
    
    # Look at previous trace for opponents
    max_prev_bid = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace:
                prev_bid = trace['bid']
                if prev_bid is not None and prev_bid > max_prev_bid:
                    max_prev_bid = prev_bid
    
    # If any opponent previously bid high, increase our bid to compete
    # But avoid overpaying; use a multiplier
    if max_prev_bid > DAILY_SALARY * 0.8:
        # Aggressive opponents: we need to match or beat
        if desperate or shortage:
            target = min(budget, max(base_bid, max_prev_bid + 5))
        else:
            target = min(budget, max(base_bid, max_prev_bid - 5))
    else:
        target = base_bid
    
    # Ensure minimum bid to win water if we really need it
    if desperate and target < DAILY_SALARY * 0.3:
        target = min(budget, DAILY_SALARY * 0.3)
    
    # Also consider remaining budget: if budget is low near end, conserve
    remaining_days = 10 - day  # approximate; assume 10 days total
    if remaining_days > 0 and budget / remaining_days < DAILY_SALARY * 0.5:
        # Conserve, but don't die
        if not desperate:
            target = min(target, DAILY_SALARY * 0.4)
    
    # Return as integer? Keep float but ensure no index needed
    return target
"""
