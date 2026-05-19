# ============================================================
# Experiment: exp_019
# Agent: Eric
# Source: exp_019
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
    # base bid: half salary
    bid = DAILY_SALARY * 0.5
    # urgency based on HP
    if hp <= 2:
        bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        bid = DAILY_SALARY * 0.7
    # adjust for low supply
    if supply < 18:
        bid = max(bid, DAILY_SALARY * 0.85)
    # ensure we don't exceed budget
    bid = min(bid, budget)
    # return as float
    return float(bid)
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
    
    alive = [o for o in opponents_status.values() if o['alive']]
    
    # Estimate required bids based on previous traces
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    if prev_bids:
        max_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
    else:
        max_prev_bid = 100  # conservative estimate
        avg_prev_bid = 100
    
    # Base bid: aim to be in top 2-3 winners
    # Number of possible winners: int(supply // WATER_REQ)
    winners = int(supply // WATER_REQ)  # floor division yields float, wrap with int
    target_bid = avg_prev_bid * 1.05  # slightly above average
    
    # Adjust based on health
    if hp <= 2 or no_water_days >= 1:
        target_bid = max(target_bid, max_prev_bid * 1.1, DAILY_SALARY * 0.85)
    elif hp <= 4:
        target_bid = max(target_bid, avg_prev_bid * 1.08, DAILY_SALARY * 0.7)
    else:
        target_bid = min(target_bid, DAILY_SALARY * 0.4)
    
    # Clamp to budget
    bid = min(budget, target_bid)
    # Ensure non-negative
    bid = max(0, bid)
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
    no_water_days = my_status['no_water_days']

    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        # Solo: bid minimal to save budget
        return min(budget, DAILY_SALARY * 0.3)

    # Extract yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Determine maximum previous bid to undercut
    if prev_bids:
        max_prev = max(prev_bids)
    else:
        max_prev = 0

    # Urgency based on HP and no_water_days
    if hp <= 3 or no_water_days >= 1:
        # Need water badly: bid slightly above the highest previous bid if affordable
        target = max(DAILY_SALARY * 0.8, max_prev + 2)
        return min(budget, int(target))
    # Healthy, conserve budget: bid moderately, undercut highest previous
    target = max(DAILY_SALARY * 0.4, max_prev + 1)
    return min(budget, int(target))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Base bid fraction
    if hp <= 2 or no_water_days >= 2:
        aggressive_factor = 0.9
    elif hp <= 5:
        aggressive_factor = 0.7
    else:
        aggressive_factor = 0.5

    # Check opponent previous traces for yesterday's aggression
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        if max_yesterday > DAILY_SALARY * 1.0:
            aggressive_factor *= 0.7
        elif max_yesterday > DAILY_SALARY * 0.8:
            aggressive_factor *= 0.85

    # Adjust for low supply
    supply_ratio = supply / WATER_REQ
    if supply_ratio < 2:
        aggressive_factor *= 1.2

    bid = min(budget, DAILY_SALARY * aggressive_factor)
    # Avoid zero bid if we need water
    if hp < WATER_REQ and no_water_days > 0:
        bid = max(bid, 10)
    return int(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Estimate yesterday's highest bid among alive opponents
    highest_prev = 0
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace:
            highest_prev = max(highest_prev, trace['bid'])
    
    # Urgency based on my HP and no_water_days
    if my_hp <= 2 or no_water_days >= 2:
        # Desperate: bid high to guarantee water
        target_bid = min(my_budget, DAILY_SALARY * 1.2)
    elif my_hp <= 4 or no_water_days == 1:
        # Moderate urgency: try to outbid opponents' yesterday max
        target_bid = min(my_budget, max(DAILY_SALARY * 0.6, highest_prev + 2))
    else:
        # Comfortable: bid low to save money
        target_bid = min(my_budget, DAILY_SALARY * 0.25)
    
    # Ensure we don't exceed budget and at least a small positive bid
    target_bid = max(1, min(my_budget, target_bid))
    return target_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
    else:
        max_yesterday_bid = 0
    
    # Base bid calculation
    # If supply is plentiful, we can afford to bid less
    supply_ratio = supply / MAX_SUPPLY  # between 0.6 and 1.0
    
    # Desperation factor: need water badly?
    if hp <= 2 or no_water_days > 0:
        desperation = 1.2
    else:
        desperation = 1.0
    
    # Late game pressure (last 3 days)
    if day >= 7:
        day_factor = 1.3
    else:
        day_factor = 1.0
    
    # Estimate opponent's likely bid based on yesterday
    if max_yesterday_bid >= 140:  # Cindy's typical bid
        likely_opponent_max = 150
    elif max_yesterday_bid >= 80:
        likely_opponent_max = max_yesterday_bid * 1.1
    else:
        likely_opponent_max = max_yesterday_bid + 5
    
    # We want to win if we can afford it and need it
    # Our target bid: slightly above likely opponent max, scaled by desperation and day
    target_bid = (likely_opponent_max + 1.5) * desperation * day_factor
    # Adjust for supply: if supply is low, need to bid higher
    if supply < 18:
        target_bid *= 1.2
    elif supply > 22:
        target_bid *= 0.8
    
    # Clamp to budget and a maximum of 150 to avoid overbidding
    max_viable_bid = min(budget, 150.0)
    bid = min(max_viable_bid, target_bid)
    
    # Ensure minimum bid if we are desperate
    if desperation > 1.1:
        bid = max(bid, 40.0)  # At least bid something meaningful
    
    # In early days, conserve budget
    if day <= 3 and hp > 3 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.5)  # Max 70
    
    bid = max(bid, 1.0)  # Always bid positive
    bid = min(bid, budget)  # Final budget sanity
    return bid
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
        if prev and isinstance(prev.get('bid'), (int, float)) and prev['bid'] > 0:
            yesterday_bids.append(prev['bid'])
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        # desperate: bid high to survive
        target = min(budget, DAILY_SALARY * 0.9)
    elif highest_yesterday > DAILY_SALARY * 0.8:
        # opponents are aggressive; match or slightly beat the average of top bids
        # but be careful not to overspend
        base = max(DAILY_SALARY * 0.6, highest_yesterday * 0.7)
        target = min(budget, base)
    else:
        # conservative bid
        target = min(budget, DAILY_SALARY * 0.4)
    return max(0.0, target)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    num_players = len(alive_opponents) + 1
    max_winners = supply // WATER_REQ  # integer division gives int
    
    # Determine if we are desperate
    if my_hp <= 3 or my_no_water_days >= 2:
        # Must get water
        target_bid = DAILY_SALARY * 0.95
    elif my_hp <= 5:
        target_bid = DAILY_SALARY * 0.7
    else:
        target_bid = DAILY_SALARY * 0.5
    
    # Gather yesterday's opponent bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If we are desperate, we need to beat the max if possible
        if my_hp <= 3 or my_no_water_days >= 2:
            if my_budget >= max_prev + 1:
                target_bid = min(my_budget, max_prev + 1)
            else:
                target_bid = min(my_budget, DAILY_SALARY * 0.95)
        else:
            # Not desperate, try to stay near median
            # To avoid overbidding, use min of our target and max_prev * 0.8
            if max_prev > 0:
                target_bid = min(target_bid, max_prev * 0.8)
    
    # Ensure we don't overspend budget
    final_bid = min(my_budget, target_bid)
    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    alive = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid: fraction of salary depending on supply
    if supply >= 20:
        base_ratio = 0.5
    else:
        base_ratio = 0.65
    
    # Adjust for low HP
    if hp <= 2:
        base_ratio = 0.9
    elif hp <= 4:
        base_ratio = max(base_ratio, 0.75)
    
    bid = min(budget, DAILY_SALARY * base_ratio)
    
    # Use previous day trace if available
    if alive:
        prev_bids = []
        for opp in alive:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
        if prev_bids:
            max_prev = max(prev_bids)
            # If someone bid very high yesterday, they might still be aggressive
            if max_prev >= DAILY_SALARY * 0.85:
                if hp > 3:
                    bid = min(budget, DAILY_SALARY * 0.3)
                else:
                    bid = min(budget, DAILY_SALARY * 0.95)
            else:
                # try to stay just above or at a safe level
                target = max(DAILY_SALARY * 0.4, max_prev + 1.0)
                bid = min(budget, target)
    
    # Ensure we don't bid more than budget
    return float(bid)
"""
