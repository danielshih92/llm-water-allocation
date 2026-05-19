# ============================================================
# Experiment: exp_103
# Agent: Eric
# Source: exp_103
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # Check yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    # No history: fallback based on health
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    # Extract day and supply (supply is a float, convert to int for any indexing)
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Safe function to ensure bid does not exceed budget
    def clamp(bid):
        return max(0.0, min(bid, budget))
    
    # Get yesterday's max bid from alive opponents
    yesterday_max = 0.0
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                yesterday_max = max(yesterday_max, prev['bid'])
    
    # Base target bid: if someone bid high yesterday, we may need to match or slightly beat
    # But also consider no_water_days and hp
    if no_water_days >= 1:
        # Urgent: need water to avoid HP loss
        if yesterday_max > 0:
            base = max(yesterday_max * 1.1, DAILY_SALARY * 0.8)
        else:
            base = DAILY_SALARY * 0.8
        # If hp low, be even more aggressive
        if hp <= 3:
            base = max(base, DAILY_SALARY * 0.9)
    else:
        # Not urgent, bid conservatively
        # If high competition, match yesterday's max + small increment, else bid low
        if yesterday_max > DAILY_SALARY * 0.7:
            base = max(DAILY_SALARY * 0.4, yesterday_max * 0.9)
        else:
            base = DAILY_SALARY * 0.5
    
    # Ensure bid stays within budget and above 0
    bid = clamp(base)
    # Final sanity: if budget is very low and we need water, bid max possible
    if no_water_days >= 2 and hp <= 2:
        bid = budget
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    # Base bid proportional to tightness
    tightness = max(0, (WATER_REQ - supply) / WATER_REQ)  # negative -> no shortage
    base_bid = DAILY_SALARY * (0.4 + 0.3 * tightness)
    
    # Check opponent traces from previous day (if any)
    highest_prev = 0.0
    for opp in opponents_status.values():
        if opp.get('previous_trace'):
            prev = opp['previous_trace']
            if prev.get('bid') is not None:
                highest_prev = max(highest_prev, float(prev['bid']))
    
    # Adjust based on yesterday's top bid
    if highest_prev > 0:
        # If they bid very high last day, assume they will again; we may need to compete
        if highest_prev >= DAILY_SALARY * 0.9:
            if my_hp > 5:
                # Healthy: safe to bid low, let them waste money
                bid = base_bid * 0.7
            else:
                # Need water: bid just above their average if we can afford
                bid = max(base_bid, min(highest_prev * 0.6 + 2, my_budget))
        else:
            bid = max(base_bid, min(highest_prev * 0.8 + 1, my_budget))
    else:
        bid = base_bid
    
    # Never exceed budget
    result = min(bid, my_budget)
    # Ensure integer bid (no sense in fractional)
    result = round(result, 2)
    return result
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    if hp <= 2 or no_water_days >= 2:
        urgency = 0.9
    elif hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.5
    
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace')
            if trace and 'bid' in trace and trace['bid'] is not None:
                yesterday_bids.append(trace['bid'])
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        if max_yesterday > DAILY_SALARY * 0.8:
            if hp > 3:
                target = max_yesterday - 5
            else:
                target = max_yesterday + 5
        else:
            target = max_yesterday + 2
    else:
        target = DAILY_SALARY * urgency
    
    bid = min(budget, max(1, target))
    return bid
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
        return min(budget, 20)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if hp <= 2:
        target = DAILY_SALARY * 0.9
        if yesterday_bids:
            target = max(target, max(yesterday_bids) + 1)
        return min(budget, max(target, 1))
    else:
        target = DAILY_SALARY * 0.3
        if yesterday_bids:
            avg = sum(yesterday_bids) / len(yesterday_bids)
            target = min(target, avg * 0.7)
        return min(budget, max(target, 1))
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
    
    # Estimate how many units can be allocated based on supply
    max_units = int(supply // WATER_REQ)
    
    # Base bid as fraction of daily salary, scaled by hp urgency
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.55
    
    # Adjust for supply scarcity
    if supply < 20:
        base_bid *= 1.2
    
    # Consider opponents' yesterday bids
    max_opponent_bid_yesterday = 0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace and trace['bid'] is not None:
                max_opponent_bid_yesterday = max(max_opponent_bid_yesterday, trace['bid'])
            # Also check opponent hp after yesterday to see if they are desperate
            if trace and 'hp_after' in trace:
                if trace['hp_after'] <= 2:
                    base_bid *= 1.15
    
    # If opponents bid very high yesterday, we need to compete
    if max_opponent_bid_yesterday > DAILY_SALARY * 0.8:
        base_bid = max(base_bid, max_opponent_bid_yesterday * 0.95)
    
    # Ensure we don't exceed budget, and minimum bid is 1
    final_bid = min(budget, max(1, base_bid))
    
    return final_bid
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
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Get yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid
    if hp <= 2 or no_water_days > 0:
        # Desperate: try to secure water
        if yesterday_bids:
            target = max(yesterday_bids) + 1.5
        else:
            target = DAILY_SALARY * 0.85
        base_bid = min(budget, max(target, DAILY_SALARY * 0.3))
    else:
        # Comfortable: try to save money
        if yesterday_bids:
            highest_prev = max(yesterday_bids)
            if highest_prev >= DAILY_SALARY * 0.85:
                # Opponents are aggressive, we still need water but can be slightly lower
                base_bid = min(budget, max(DAILY_SALARY * 0.6, highest_prev - 5))
            else:
                # Opponents are low, outbid slightly
                base_bid = min(budget, max(DAILY_SALARY * 0.5, highest_prev + 1.5))
        else:
            base_bid = min(budget, DAILY_SALARY * 0.55)
    
    # Ensure we don't bid more than budget
    return min(budget, max(1.0, base_bid))
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
    no_water_days = my_status['no_water_days']
    
    # Compute available water per player based on supply and number of alive players
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents) + 1
    water_per_person = supply / num_alive
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Estimate opponent bidding targets
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        # If we are desperate, match highest
        if no_water_days >= 1 or hp <= 2:
            target_bid = min(budget, max(DAILY_SALARY * 0.95, max_prev + 1))
        else:
            # Otherwise try to bid just above average to secure water if needed
            target_bid = min(budget, max(DAILY_SALARY * 0.5, avg_prev + 0.5))
    else:
        # No history: use baseline strategy
        if hp <= 2 or no_water_days >= 1:
            target_bid = min(budget, DAILY_SALARY * 0.85)
        else:
            target_bid = min(budget, DAILY_SALARY * 0.6)
    
    # Ensure bid respects budget and is at least 0
    bid = max(0, min(budget, target_bid))
    
    # If supply is abundant and we are healthy, we can be conservative
    if water_per_person >= WATER_REQ and hp > 3 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.4)
    
    # Ensure bid does not exceed budget
    bid = min(budget, bid)
    return int(bid)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents (if available)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine aggressiveness based on HP and budget
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Base bid: moderate if need water, conservative if healthy
    if hp <= 2 or no_water_days >= 2:
        # Desperate: need water, willing to pay higher
        if yesterday_bids:
            mean_yesterday = sum(yesterday_bids) / len(yesterday_bids)
            target_bid = min(budget, max(DAILY_SALARY * 0.8, mean_yesterday * 0.9))
        else:
            target_bid = min(budget, DAILY_SALARY * 0.85)
    elif hp >= 6:
        # Healthy: save money
        target_bid = min(budget, DAILY_SALARY * 0.4)
    else:
        # Moderate health: be cautious
        if yesterday_bids:
            mean_yesterday = sum(yesterday_bids) / len(yesterday_bids)
            target_bid = min(budget, max(DAILY_SALARY * 0.5, mean_yesterday * 0.7))
        else:
            target_bid = min(budget, DAILY_SALARY * 0.6)
    
    # Ensure bid is non-negative and not exceeding budget
    target_bid = max(0, min(budget, target_bid))
    return target_bid
"""
