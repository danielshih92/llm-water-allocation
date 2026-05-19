# ============================================================
# Experiment: exp_092
# Agent: Eric
# Source: exp_092
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Gather yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    hp = my_status['hp']
    budget = my_status['budget']

    # When HP critical, bid high to secure water
    if hp <= 2:
        target = min(budget, DAILY_SALARY * 0.95)
        return target

    # When HP moderate, outbid yesterday's maximum slightly
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # Ensure we beat the highest yesterday bid by a small margin
        target = max(DAILY_SALARY * 0.4, max_yesterday + 1)
        target = min(budget, target)
        # But not too high if we are comfortable
        if hp > 3 and target > DAILY_SALARY * 0.6:
            target = min(budget, DAILY_SALARY * 0.6)
        return target

    # No data: bid conservatively
    return min(budget, DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Look at yesterday's highest bid among alive opponents
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > highest_prev_bid:
                highest_prev_bid = bid

    # Base bid: if we have no water days, urgent
    if no_water_days >= 2 or hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
    elif highest_prev_bid > 0:
        # If opponent historically high, they might bid similarly; bid slightly above to win
        bid = min(budget, highest_prev_bid + 5)
    else:
        # Default moderate
        bid = min(budget, DAILY_SALARY * 0.5)

    # Cap to stay rational
    bid = max(bid, DAILY_SALARY * 0.1)
    bid = min(bid, budget)

    # If supply is low, increase bid slightly
    if supply < 18:
        bid = min(budget, bid * 1.2)

    return bid
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

    # Extract alive opponents with previous_trace
    alive = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive:
        return min(budget, DAILY_SALARY * 0.5)

    # Get yesterday's bids from traces
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Identify aggressive opponent (Cindy-like) from highest yesterday bid
    highest_prev = max(yesterday_bids) if yesterday_bids else 0

    # Base bid from supply and hp
    scarcity = supply / 25.0  # 1.0 if max supply, lower if scarce
    base_bid = DAILY_SALARY * (0.6 + 0.3 * (1 - scarcity))

    # If we are low on hp, increase bid
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Adjust to outbid aggressive opponent if needed
    if highest_prev > 0:
        # If opponent bid high yesterday, they might bid high again
        target = highest_prev + 1.0
        if target > DAILY_SALARY * 1.2:
            # If they are overbidding, we may not want to compete excessively
            target = DAILY_SALARY * 0.9
        base_bid = max(base_bid, target)

    # Also consider number of days left: last few days, be more aggressive
    if day >= 8:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Ensure we don't exceed budget
    return min(budget, base_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's bids from alive opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid on yesterday's maximum bid among alive opponents
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
    else:
        max_yesterday_bid = 0
    
    # Adjust based on own hp
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Target bid: slightly above yesterday's max, but within budget and capped
    # Use a multiplier based on hp urgency
    if hp <= 2:
        # Desperate: bid high to ensure water
        target_bid = max(DAILY_SALARY * 0.9, max_yesterday_bid + 1)
    elif hp <= 5:
        # Moderate: stay competitive
        target_bid = max(DAILY_SALARY * 0.6, max_yesterday_bid + 0.5)
    else:
        # Healthy: be conservative
        target_bid = max(DAILY_SALARY * 0.4, max_yesterday_bid + 0.2)
    
    # Ensure we don't bid more than budget or more than daily salary * 1.2 (safety)
    max_bid = min(budget, DAILY_SALARY * 1.2)
    bid = min(max_bid, target_bid)
    
    # Floor to avoid negative
    bid = max(bid, 1)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.5)
    # Estimate opponent aggressiveness from yesterday's highest bid among alive
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    base_bid = DAILY_SALARY * 0.55
    if my_hp <= 2 or no_water_days > 0:
        base_bid = DAILY_SALARY * 0.85
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.65
    # If opponents were very aggressive yesterday, slightly increase
    if max_prev_bid > DAILY_SALARY * 0.8:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    # But don't exceed budget and avoid wasting if supply is plenty
    max_bid = min(my_budget, DAILY_SALARY * 1.0)
    # Ensure we have enough for future days if supply low
    if day >= 7:
        base_bid = min(base_bid, DAILY_SALARY * 0.6)
    bid = min(max_bid, base_bid)
    # Ensure bid is at least 0
    bid = max(0.0, bid)
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
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    supply = day_context['supply']
    # Estimate number of agents that can get water (supply / WATER_REQ floor)
    # Not used directly, just for context
    max_served = int(supply // WATER_REQ)
    
    # Base bid: if we have budget, safe to bid around 55.
    base_bid = 55.0
    
    if yesterday_bids:
        # Find a bid that beats Bob's last bid (but stay below Cindy's likely high bid)
        # Assume Cindy's bid will be highest.
        # Sort yesterday bids to find second highest (likely Bob's)
        sorted_bids = sorted(yesterday_bids, reverse=True)
        if len(sorted_bids) >= 2:
            second_highest = sorted_bids[1]
        else:
            second_highest = sorted_bids[0]
        # Beat second highest by a small margin
        base_bid = max(second_highest + 1.5, 50.0)
        # But don't exceed Cindy's bid if she's super aggressive; cap at 65
        if sorted_bids[0] > 80:
            base_bid = min(base_bid, 65.0)
    
    # Consider my health urgency
    if my_status['hp'] <= 3:
        urgent_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(urgent_bid, my_status['budget'])
    else:
        proposed = min(base_bid, my_status['budget'])
        # Preserve budget for future days
        return max(proposed, 30.0)  # Ensure minimum bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    supply_int = int(supply)
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace')
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])
    
    # Base bid depending on health
    if hp <= 1:
        bid = min(budget, SALARY * 0.8)
    elif hp <= 3:
        bid = min(budget, SALARY * 0.5)
    else:
        bid = min(budget, SALARY * 0.3)
    
    # Adjust using previous opponents' bids and current supply
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        if supply_int < 20:
            target = min(budget, max(avg_prev + 5, SALARY * 0.5))
        else:
            target = min(budget, max(avg_prev - 10, SALARY * 0.2))
        if hp <= 1:
            target = max(target, SALARY * 0.7)
        bid = min(budget, target)
    
    return float(bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
    
    # Base bid on yesterday's average or max
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
    else:
        avg_prev = DAILY_SALARY * 0.5
        max_prev = DAILY_SALARY * 0.6
    
    # Desperation factor: need water if no_water >= 1 or hp low
    if my_hp <= 3 or no_water >= 2:
        # Bid high to guarantee water, but not exceed budget
        bid = min(my_budget, max(avg_prev + 10, DAILY_SALARY * 0.9))
    elif my_hp <= 5:
        # Moderate need
        bid = min(my_budget, max(avg_prev + 5, DAILY_SALARY * 0.7))
    else:
        # Healthy: undercut with slight margin over average
        bid = min(my_budget, max(avg_prev + 2, DAILY_SALARY * 0.4))
    
    # Ensure bid is at least 1 if we have budget and need water
    if my_budget > 0 and (my_hp < 8 or no_water > 0):
        bid = max(bid, 1)
    
    # Clamp to budget
    bid = min(bid, my_budget)
    
    # Floor divide to avoid float index issues (though not used here)
    return float(bid)
"""
