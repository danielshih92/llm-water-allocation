# ============================================================
# Experiment: exp_043
# Agent: Eric
# Source: exp_043
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Calculate opponent desperation
    opp_desperation = 0.0
    for opp in alive_opponents:
        opp_hp = opp['hp']
        opp_no_water = opp['no_water_days']
        # Scale: lower hp and higher no_water_days increase desperation
        desperation = (max(0, WATER_REQ - opp_hp) / WATER_REQ) * 0.5 + (opp_no_water / (10.0 + opp_no_water)) * 0.5
        opp_desperation = max(opp_desperation, desperation)
    
    # Our urgency
    my_urgency = (max(0, WATER_REQ - my_hp) / WATER_REQ) * 0.5 + (my_no_water / (10.0 + my_no_water)) * 0.5
    
    # Base bid: 40% of daily salary
    base_bid = DAILY_SALARY * 0.4
    
    # Adjust: if our urgency high, increase; if opponent desperation high, decrease (avoid price war)
    bid = base_bid
    if my_urgency > 0.6:
        bid = base_bid * (1.0 + my_urgency)
    elif opp_desperation > 0.7:
        # Opponents very desperate, they will bid high; conserve budget
        bid = base_bid * 0.7
    else:
        # Moderate both
        bid = base_bid * (1.0 + my_urgency * 0.3 - opp_desperation * 0.3)
    
    # Safety: ensure bid within budget and not negative
    bid = max(1.0, min(float(my_budget), bid))
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If we are low on hp, bid aggressively
        if my_status['hp'] <= 3:
            target = max(highest_prev + 2, DAILY_SALARY * 0.95)
        elif my_status['hp'] <= 5:
            target = max(highest_prev + 1, DAILY_SALARY * 0.85)
        else:
            target = max(highest_prev * 0.95, DAILY_SALARY * 0.65)
    else:
        # No previous bids, use safe baseline
        if my_status['hp'] <= 3:
            target = DAILY_SALARY * 0.9
        else:
            target = DAILY_SALARY * 0.5
    
    # Ensure we don't bid more than budget
    bid = min(my_status['budget'], target)
    # Ensure minimum bid if desperate
    if my_status['no_water_days'] >= 2 or my_status['hp'] <= 2:
        bid = max(bid, DAILY_SALARY * 0.85)
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Gather yesterday's bids from alive opponents (if available)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Compute target bid based on yesterday's pressure
    if yesterday_bids:
        # sort bids to find median
        sorted_bids = sorted(yesterday_bids)
        n = len(sorted_bids)
        median_bid = sorted_bids[int(n // 2)] if n % 2 == 1 else (sorted_bids[int(n//2)-1] + sorted_bids[int(n//2)]) / 2.0
        target = median_bid + 5.0  # slightly above median
    else:
        # no trace, conservative default
        target = DAILY_SALARY * 0.5
    
    # Adjust for own health
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif my_status['hp'] <= 4:
        target = max(target, DAILY_SALARY * 0.65)
    
    # Cannot exceed budget
    target = min(target, my_status['budget'])
    
    # Ensure we don't bid more than necessary if supply is high
    supply = day_context['supply']
    # If supply is very high, we can afford to bid less
    if supply > 20:
        target = min(target, DAILY_SALARY * 0.5)
    
    return max(1.0, target)  # at least 1
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # collect yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # base bid: if hp critical, bid high
    if hp <= 2 or no_water_days >= 2:
        return min(budget, DAILY_SALARY * 0.95)
    
    # determine yesterday's max bid from alive opponents
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    
    # adjust based on supply - higher supply means we can bid lower and still win
    if supply >= 20:
        target = max(DAILY_SALARY * 0.5, max_prev * 0.85)
    else:
        target = max(DAILY_SALARY * 0.6, max_prev * 0.95 + 1)
    
    # ensure we don't overspend
    bid = min(budget, target)
    return int(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_BID = 10
    DAY = int(day_context['day']) if isinstance(day_context['day'], float) else day_context['day']
    SUPPLY = day_context['supply']
    if isinstance(SUPPLY, float):
        SUPPLY = int(SUPPLY)
    hp = my_status['hp']
    budget = my_status['budget']
    base_bid = DAILY_SALARY * 0.4
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(budget, base_bid)
    # collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    if prev_bids:
        max_prev = max(prev_bids)
        target = max(base_bid, min(DAILY_SALARY * 1.0, max_prev + 2.0))
    else:
        target = base_bid
    # adjust based on hp
    if hp <= 2:
        target = DAILY_SALARY * 0.9
    # if no water days > 2, increase
    if my_status['no_water_days'] >= 2:
        target = max(target, DAILY_SALARY * 0.85)
    # final cap
    target = min(budget, target)
    if target > DAILY_SALARY:
        target = DAILY_SALARY
    return max(MIN_BID, target)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.5)
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
        if hp <= 2:
            target = max_prev + 5
        elif hp <= 4:
            target = avg_prev + 3
        else:
            target = avg_prev - 2 if avg_prev > 50 else DAILY_SALARY * 0.55
        if supply < 18:
            target += 10
        bid = min(budget, target)
        bid = min(bid, DAILY_SALARY * 0.9)
        bid = max(bid, 1)
        return bid
    else:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        elif hp <= 5:
            return min(budget, DAILY_SALARY * 0.65)
        else:
            return min(budget, DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    if prev_bids:
        max_prev = max(prev_bids)
    else:
        max_prev = 0.0
    if my_status['hp'] <= 3:
        # urgent need water
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, max_prev + 2.0))
    else:
        # normal - try to outbid lower cluster
        base = DAILY_SALARY * 0.85  # ~119
        if max_prev > base:
            bid = min(my_status['budget'], max_prev + 1.0)
        else:
            bid = min(my_status['budget'], base)
    # ensure bid is at least 0 and not exceed budget
    bid = max(0.0, min(bid, my_status['budget']))
    return bid
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
    supply = day_context.get('supply', 20)
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opps.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        yesterday_max = max(yesterday_bids)
        yesterday_avg = sum(yesterday_bids) / len(yesterday_bids)
    else:
        yesterday_max = 0
        yesterday_avg = 0

    desperation = no_water_days > 0 or hp <= 3
    if desperation:
        target_bid = max(yesterday_max + 5, DAILY_SALARY * 0.8)
    else:
        target_bid = max(yesterday_max - 10, DAILY_SALARY * 0.3)

    # Adjust for high supply -- less competition
    if supply > 22:
        target_bid *= 0.85

    bid = min(budget, target_bid)
    bid = max(0, bid)
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
    
    # Determine number of winners based on supply
    num_winners = int(supply // WATER_REQ)
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # No competition, bid minimum to get water
        return min(budget, max(DAILY_SALARY * 0.2, 1.0))
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Estimate competitive bid: slightly above the median of past bids or a safety level
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        # Target to win: if num_winners is small, we need to be among top bidders
        # Use a bid that is slightly above the (num_winners-1)th highest? But we don't know order.
        # Simple heuristic: bid slightly less than the max to avoid war of attrition
        target = max(DAILY_SALARY * 0.5, max_prev * 0.95)
    else:
        # No info, assume moderate bidding
        target = DAILY_SALARY * 0.6
    
    # Adjust based on health
    if hp <= 2 or no_water_days > 0:
        # Desperate: bid higher to ensure water
        if prev_bids:
            target = max(target, DAILY_SALARY * 0.85)
        else:
            target = max(target, DAILY_SALARY * 0.8)
    else:
        # Comfortable: try to save budget
        if prev_bids:
            target = min(target, DAILY_SALARY * 0.7)
        else:
            target = min(target, DAILY_SALARY * 0.55)
    
    # Ensure bid is within budget and at least 1
    bid = min(budget, max(1.0, target))
    # Round to 2 decimals
    return round(bid, 2)
"""
