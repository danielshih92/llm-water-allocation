# ============================================================
# Experiment: exp_003
# Agent: Eric
# Source: exp_003
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Check my urgency
    urgent = (my_status['hp'] <= 2) or (my_status['no_water_days'] > 0)
    
    # Gather yesterday's max bid from alive opponents
    max_prev_bid = 0.0
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                max_prev_bid = max(max_prev_bid, prev['bid'])
    
    if urgent:
        bid = DAILY_SALARY * 0.95
    else:
        # Conservative base, but slightly above yesterday's max
        base = DAILY_SALARY * 0.45
        bid = max(base, max_prev_bid + 1.0)
    
    # Ensure we don't exceed budget and keep a small reserve
    max_bid = my_status['budget'] * 0.95
    bid = min(bid, max_bid)
    # Ensure bid is non-negative
    bid = max(0.0, bid)
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
    # Determine alive opponents
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from opponent traces
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    # Estimate bid based on yesterday's max and opponent hp
    max_last_bid = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Own hp threshold
    if my_status['hp'] <= 2:
        # Must get water at almost any cost
        target_bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, max_last_bid + 5.0))
    else:
        # Can be more conservative
        target_bid = min(my_status['budget'], max(DAILY_SALARY * 0.6, max_last_bid + 2.0))
    
    # Ensure we don't waste budget when supply is low: if supply is too low for all, might need higher bid
    supply = day_context['supply']
    # But we just keep simple
    return target_bid
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
    
    # Determine how many opponents are alive
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's highest bid from opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Base bid: if we have enough HP, try to conserve budget
    if hp <= 3:
        # Desperate: bid enough to likely win
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on yesterday's pressure
    if prev_bids:
        highest_prev = max(prev_bids)
        # If yesterday was high, we may need to increase
        if highest_prev > DAILY_SALARY * 0.85:
            if hp <= 3:
                base_bid = max(base_bid, DAILY_SALARY * 0.95)
            else:
                base_bid = max(base_bid, highest_prev * 1.05)
        else:
            # Conservative: slightly above average if needed
            base_bid = max(base_bid, highest_prev + 2)
    
    # Adjust for supply: if supply is low, competition increases
    if supply < 18:
        base_bid *= 1.2
    
    # Ensure we don't bid more than budget and not negative
    bid = min(budget, base_bid)
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
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine max previous bid among alive opponents
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bid = prev['bid']
            if prev_bid > max_prev_bid:
                max_prev_bid = prev_bid
    
    # Health-based urgency
    if hp <= 2:
        urgent = True
    else:
        urgent = False
    
    # Base bid: if we need water urgently, bid higher
    if urgent:
        base_bid = DAILY_SALARY * 0.8
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # If there is a known high bidder from yesterday, outbid them slightly if feasible
    if max_prev_bid > 0:
        target_bid = max_prev_bid + 2.0
    else:
        target_bid = base_bid
    
    # Do not exceed budget or bid more than necessary
    final_bid = min(budget, target_bid, DAILY_SALARY)
    
    # Ensure we at least bid something if we have budget and need water
    if final_bid < 1 and budget >= 1 and no_water_days >= 1:
        final_bid = 1
    
    # Use int() on any index if needed (not here but keep rule)
    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine desperation
    desperate = hp <= 2 or no_water_days >= 2
    
    # Look at yesterday's bids
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Compute base bid
    if desperate:
        base = min(budget, DAILY_SALARY * 0.95)
    else:
        # Estimate required bid based on supply
        scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        base = min(budget, DAILY_SALARY * (0.4 + 0.4 * scarcity))
    
    # Compete with yesterday's highest bid if any
    if prev_bids:
        max_prev = max(prev_bids)
        # If an opponent previously bid high, we might need to outbid
        # But they may do same again; we add a small premium
        if max_prev > base:
            # Outbid by a small margin, but not too high
            base = min(budget, max_prev + 2.0)
    
    # Ensure we don't spend more than we can afford
    final_bid = min(budget, max(base, 5.0))
    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Determine base bid
    if hp <= 2:
        # Desperate: bid high to survive
        base_bid = DAILY_SALARY * 0.9
    else:
        # Healthy: try to undercut opponents' yesterday max
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            # Slightly above to beat if they repeat, but cap at 0.7*salary to save
            base_bid = min(max_yesterday + 1.0, DAILY_SALARY * 0.7)
        else:
            base_bid = DAILY_SALARY * 0.5
    # Clamp to budget and min 0
    final_bid = max(0.0, min(budget, base_bid))
    return final_bid
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
    no_water_days = my_status['no_water_days']

    WATER_REQ = 8
    DAILY_SALARY = 140

    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                yesterday_bids.append(prev['bid'])

    if not yesterday_bids:
        if no_water_days >= 2:
            return min(budget, DAILY_SALARY * 0.8)
        elif hp <= 3:
            return min(budget, DAILY_SALARY * 0.6)
        else:
            return min(budget, DAILY_SALARY * 0.45)

    max_prev = max(yesterday_bids)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)

    if supply <= 17:
        if hp <= 3:
            return min(budget, max(DAILY_SALARY * 0.75, max_prev + 2))
        else:
            return min(budget, max(DAILY_SALARY * 0.6, avg_prev))
    elif supply >= 23:
        return min(budget, DAILY_SALARY * 0.35)
    else:
        if hp <= 2:
            return min(budget, max(DAILY_SALARY * 0.7, max_prev + 1))
        elif hp <= 5:
            return min(budget, max(DAILY_SALARY * 0.5, avg_prev))
        else:
            return min(budget, max(DAILY_SALARY * 0.4, avg_prev - 5))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: 60% of salary
    base_bid = 0.6 * DAILY_SALARY
    
    if my_status['hp'] <= 2:
        # Desperate: bid almost full salary or up to budget
        bid = min(my_status['budget'], 0.95 * DAILY_SALARY)
    else:
        if len(yesterday_bids) > 0:
            avg_prev = sum(yesterday_bids) / len(yesterday_bids)
            if avg_prev > 90:
                # Opponents were aggressive: undercut a bit
                bid = min(my_status['budget'], max(base_bid, avg_prev * 0.85))
            else:
                bid = min(my_status['budget'], max(base_bid, avg_prev + 5))
        else:
            bid = min(my_status['budget'], base_bid)
    
    # Ensure we don't bid more than budget and not negative
    bid = max(0, min(bid, my_status['budget']))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Collect last known bids from opponents who have previous_trace
    last_bids = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            last_bids.append(prev['bid'])
    
    # If there are recent bids, base our bid on them
    if last_bids:
        avg_bid = sum(last_bids) / len(last_bids)
        target = avg_bid + 2  # slight premium to outbid average
    else:
        # Default aggressive: 60% of salary
        target = DAILY_SALARY * 0.6
    
    # Adjust for health: if low HP, bid more
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
        target = max(target, DAILY_SALARY * 0.9)
    
    # Do not exceed budget and ensure non-negative
    bid = min(my_status['budget'], target)
    bid = max(0, bid)
    return bid
"""
