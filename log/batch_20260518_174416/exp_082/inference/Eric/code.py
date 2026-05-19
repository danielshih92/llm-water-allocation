# ============================================================
# Experiment: exp_082
# Agent: Eric
# Source: exp_082
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
        return min(my_status['budget'], DAILY_SALARY * 0.15)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    highest_prev = max(prev_bids) if prev_bids else 0
    if my_status['hp'] <= 2:
        target = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        target = DAILY_SALARY * 0.7
    else:
        target = DAILY_SALARY * 0.4
    if highest_prev > target:
        target = highest_prev + 1.0
    if target > my_status['budget']:
        target = my_status['budget']
    return target
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    avg_prev_bid = 0.0
    count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_prev_bid += prev['bid']
            count += 1
    if count > 0:
        avg_prev_bid /= count
    base_bid = 0.75 * DAILY_SALARY
    if hp <= 3:
        base_bid = 0.92 * DAILY_SALARY
    if no_water_days > 0:
        base_bid = 0.98 * DAILY_SALARY
    if supply <= 18:
        base_bid = max(base_bid, 0.95 * DAILY_SALARY)
    if avg_prev_bid > 0:
        target = max(avg_prev_bid * 1.05, base_bid)
        base_bid = target
    else:
        base_bid = max(base_bid, 0.85 * DAILY_SALARY)
    bid = min(budget, base_bid)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's max bid among alive opponents
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, trace['bid'])
    
    # Determine urgency based on health and no_water_days
    if hp <= 0 or no_water_days >= 2:
        urgency = 3
    elif hp <= 2 or no_water_days >= 1:
        urgency = 2
    elif hp <= 4:
        urgency = 1
    else:
        urgency = 0
    
    # Estimate how many units we need (1 or 2 depending on urgency)
    # Water needed to survive: 1 unit per day, but we need 8 liters per unit
    # We can compute max affordable bid from budget
    # Base bid: if urgency high, bid above yesterday's max; else low
    if urgency >= 2:
        # Desperate: bid enough to win, but not exceed budget
        target_bid = yesterday_max_bid + 2.0
    elif urgency == 1:
        # Moderate: bid slightly above yesterday's max or a safe amount
        target_bid = max(yesterday_max_bid + 1.0, DAILY_SALARY * 0.4)
    else:
        # Comfortable: save money, bid low
        target_bid = DAILY_SALARY * 0.2
    
    # Also consider supply: if low supply (<20), competition increases
    if supply < 20:
        target_bid *= 1.2
    
    # Ensure we don't bid more than budget
    bid = min(budget, target_bid)
    # Ensure minimum positive bid
    bid = max(bid, 0.5)
    return bid
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev = max(yesterday_bids) if yesterday_bids else 0
    
    # Base bid: want to secure water when supply is low
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if hp <= 2:
        # desperate: bid high to avoid death
        base = DAILY_SALARY * 0.9
    else:
        base = DAILY_SALARY * (0.5 + 0.2 * (1 - supply_ratio))
    
    # Adjust based on yesterday's opponents
    if yesterday_bids:
        if highest_prev >= DAILY_SALARY * 0.85:
            # opponents very aggressive: undercut or save
            if hp > 4:
                bid = DAILY_SALARY * 0.4
            else:
                bid = max(base, highest_prev * 0.6)
        else:
            # bid slightly above previous highest if needed
            bid = max(base, highest_prev + 1.0)
    else:
        bid = base
    
    # Ensure we don't exceed budget and stay in reasonable range
    bid = min(bid, budget)
    bid = min(bid, DAILY_SALARY * 1.1)  # cap to avoid overspend
    
    # Return integer bid (as float is okay)
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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
    num_alive = len(alive_opponents) + 1  # including self

    # Estimate how many can get water (max winners = floor(supply / WATER_REQ))
    max_winners = int(supply) // WATER_REQ
    # If we are desperate, we need to be in top max_winners bids

    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine baseline bid
    if prev_bids:
        # Take the highest yesterday's bid among alive opponents (likely Cindy's)
        highest_prev = max(prev_bids)
    else:
        highest_prev = 0.0

    # If no_water_days > 2, we must get water today
    if no_water_days >= 2:
        # Bid aggressively to ensure we are among winners
        target_bid = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
    elif hp <= 2:
        # Low HP, need water
        target_bid = max(DAILY_SALARY * 0.7, highest_prev + 1.0)
    else:
        # Healthy and hydrated, we can save money
        target_bid = min(DAILY_SALARY * 0.5, highest_prev * 0.9)

    # Ensure bid is within budget and not negative
    bid = min(budget, max(0, target_bid))

    # If we have very high budget and late in game, we can be more conservative
    if day > 5 and hp > 5:
        bid = min(bid, DAILY_SALARY * 0.4)

    return bid
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

    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    day = day_context['day']

    supply_int = int(supply)

    # Base bid as fraction of salary depending on HP
    if hp <= 2:
        base_mult = 0.85
    elif hp <= 5:
        base_mult = 0.65
    elif hp <= 7:
        base_mult = 0.4
    else:
        base_mult = 0.25

    base_bid = min(budget, DAILY_SALARY * base_mult)

    # Adjust based on previous bids of alive opponents
    previous_max = 0
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_max = max(previous_max, prev['bid'])

    if previous_max > 0:
        # If opponents bid high, we need to match or exceed slightly
        if hp <= 3:
            target = min(budget, max(base_bid, previous_max + 1))
        else:
            target = min(budget, base_bid)
    else:
        target = base_bid

    # Ensure we don't bid more than budget
    bid = min(budget, target)
    # Also ensure bid is non-negative
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    # Get yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine urgency: need water if HP low or no_water_days > 0
    urgent = (my_status['hp'] <= 2) or (my_status['no_water_days'] > 0)
    
    # Base bid
    base_bid = DAILY_SALARY * 0.7  # 98
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        if urgent:
            # Need to win: slightly above yesterday's max, but cap by budget
            bid = min(my_status['budget'], max_yesterday + 2.0)
        else:
            # Try to save: bid just below yesterday's max if we can afford to lose, else base
            if my_status['hp'] > 6:
                bid = min(my_status['budget'], max(0.0, max_yesterday - 5.0))
            else:
                bid = min(my_status['budget'], base_bid)
    else:
        # No yesterday info, use baseline
        bid = base_bid if not urgent else min(my_status['budget'], DAILY_SALARY * 0.9)
    
    # Ensure we never bid more than budget
    bid = max(0.0, min(my_status['budget'], bid))
    # Also consider supply: if very low supply, bid higher to guarantee water
    supply = day_context['supply']
    if supply < 20 and urgent:
        bid = max(bid, min(my_status['budget'], DAILY_SALARY * 0.95))
    # Keep budget for future days: never spend more than 80% of budget if not urgent and early days?
    day = int(day_context['day'])
    if day <= 3 and not urgent:
        bid = min(bid, DAILY_SALARY * 0.6)
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = {k:
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    need_water = (my_status['hp'] < 3) or (my_status['no_water_days']
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
    
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(budget, max(5, DAILY_SALARY * 0.3))
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Determine pressure from yesterday
    if prev_bids:
        high = max(prev_bids)
        # If someone bid very high yesterday, they may do so again
        if high >= DAILY_SALARY * 0.85:  # 119
            if hp > 3:
                # Conservative, try to outbid lower ones
                target = max(DAILY_SALARY * 0.5, high - 5)
            else:
                # Need water, match high bid minimum
                target = high + 1
        else:
            # Moderate pressure: outbid the highest yesterday by small margin
            target = high + 2
    else:
        # No history, base on HP
        if hp <= 2:
            target = DAILY_SALARY * 0.9
        else:
            target = DAILY_SALARY * 0.55
    
    # Clamp to budget and reasonable bounds
    bid = min(budget, max(0, target))
    # Ensure we don't waste too much if supply is high
    # But we need water, so bid at least 1
    bid = max(bid, 1)
    return int(bid)
"""
