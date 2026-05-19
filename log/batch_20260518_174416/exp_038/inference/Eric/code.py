# ============================================================
# Experiment: exp_038
# Agent: Eric
# Source: exp_038
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    # Determine urgency
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        # Moderately aggressive based on supply scarcity
        if supply <= 18:
            bid = min(budget, DAILY_SALARY * 0.7)
        elif supply <= 22:
            bid = min(budget, DAILY_SALARY * 0.5)
        else:
            bid = min(budget, DAILY_SALARY * 0.35)
    return int(bid)
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

    # Gather previous bid from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                prev_bids.append(prev_trace['bid'])

    # Determine pressure level
    max_prev_bid = max(prev_bids) if prev_bids else 0

    # Base bid: fraction of salary based on scarcity
    scarcity_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    base_bid = scarcity_factor * DAILY_SALARY * 0.8

    # Must-win condition: low HP or dehydrated
    must_win = (hp <= 2) or (no_water_days > 0)
    if must_win:
        target_bid = max(base_bid, max_prev_bid + 2, DAILY_SALARY * 0.7)
    else:
        # If we are comfortable, try to outbid only if necessary
        if max_prev_bid > base_bid:
            target_bid = max_prev_bid + 1.5
        else:
            target_bid = base_bid

    # Clamp by remaining budget and salary
    max_bid = min(budget, DAILY_SALARY)
    # Ensure we don't bid more than we can afford to lose for future
    # Also never bid below 0
    final_bid = max(0, min(target_bid, max_bid))

    # Rare case: if budget is very low, bid aggressively to survive
    if budget < DAILY_SALARY * 0.5 and must_win:
        final_bid = min(budget, DAILY_SALARY * 0.9)

    return final_bid
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate baseline: if we're desperate, bid high
    desperate = hp <= 2 or no_water_days >= 1
    if desperate:
        base = DAILY_SALARY * 0.9
    else:
        base = DAILY_SALARY * 0.5

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If previous highest is very high, we might undercut to save budget if not desperate
        if highest_prev >= DAILY_SALARY * 0.85:
            if desperate:
                target = max(base, highest_prev * 0.95)  # slightly below top
            else:
                target = base  # conservative
        else:
            # if we can afford a small increment, try to beat highest
            target = max(base, highest_prev + 1.0)
    else:
        target = base

    # Ensure we don't exceed budget
    return min(budget, target)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Determine urgency based on HP
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Base decision on yesterday's pressure
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if hp > 3:
            # Not urgent, bid low to save budget
            bid = min(budget, DAILY_SALARY * 0.3)
        else:
            # Urgent, bid high to secure water
            bid = min(budget, DAILY_SALARY * 0.95)
    else:
        # Moderate pressure
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.55)
    
    # Ensure bid is at least 0 and not more than budget
    bid = max(0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine base bid based on health
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9  # 126
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7  # 98
    else:
        base_bid = DAILY_SALARY * 0.5  # 70
    
    # Adjust based on yesterday's highest bid
    yesterday_max = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = float(prev['bid'])
            if bid_val > yesterday_max:
                yesterday_max = bid_val
    
    if yesterday_max > 0:
        # If we are desperate, try to outbid the max slightly
        if hp <= 2:
            bid = max(base_bid, yesterday_max + 2.0)
        elif hp <= 4:
            # moderate desire: outbid if we can afford
            bid = max(base_bid, yesterday_max + 1.0)
        else:
            # healthy: stay near base, but don't vastly overpay
            bid = max(base_bid, yesterday_max * 0.8)
    else:
        bid = base_bid
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Ensure positive bid
    bid = max(bid, 0.01)
    
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid
    if my_status['hp'] <= 2:
        # Critical health: bid high to secure water
        target_bid = DAILY_SALARY * 0.9
    else:
        if yesterday_bids:
            avg_prev = sum(yesterday_bids) / len(yesterday_bids)
            # Add a small margin to beat average
            target_bid = avg_prev + 2
            # Cap at 80% of salary to save budget
            target_bid = min(target_bid, DAILY_SALARY * 0.8)
        else:
            target_bid = DAILY_SALARY * 0.6
    
    # Ensure bid does not exceed budget
    bid = min(my_status['budget'], target_bid)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Extract current day and supply
    supply = day_context['supply']
    day = day_context['day']
    
    # My status
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Determine alive opponents
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # If no alive opponents, bid minimum to save budget
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Gather yesterday's bids from alive opponents (if available)
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Compute a reference bid based on yesterday's max or average
    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        max_yesterday = max(yesterday_bids)
        # If opponents bid high yesterday, expect similar today
        ref_bid = max(avg_yesterday, max_yesterday * 0.85)
    else:
        # No data, use historical averages from meta-round: Bob ~105, Cindy ~108, David ~69
        ref_bid = 85.0
    
    # Adjust for supply: if supply is low, competition is higher; if high, easier
    supply_factor = 1.0
    if supply < 18:
        supply_factor = 1.2
    elif supply > 22:
        supply_factor = 0.8
    
    # Base bid: try to outbid reference by a small margin, but not exceed budget
    base_bid = ref_bid * supply_factor + 2.0
    
    # Urgency based on HP and no_water_days
    if no_water_days >= 2 or hp <= 3:
        # Desperate: need water badly
        target_bid = min(budget, max(base_bid, DAILY_SALARY * 0.95))
    elif hp <= 5:
        # Moderate need
        target_bid = min(budget, base_bid)
    else:
        # Healthy, conserve budget
        target_bid = min(budget, base_bid * 0.7)
    
    # Ensure minimum bid to avoid losing all budget
    min_bid = max(0.5, DAILY_SALARY * 0.1)
    final_bid = max(min_bid, target_bid)
    
    # Return as float, ensure no index errors (none here)
    return float(final_bid)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Compute a reference bid based on past behaviour
    if yesterday_bids:
        # Use median to be robust
        sorted_bids = sorted(yesterday_bids)
        n = len(sorted_bids)
        if n % 2 == 1:
            median_prev = sorted_bids[int((n-1)/2)]
        else:
            median_prev = (sorted_bids[int(n/2)-1] + sorted_bids[int(n/2)]) / 2.0
        # Add a small premium if we need water very badly
        if hp <= 2:
            target = max(DAILY_SALARY * 0.9, median_prev + 2)
        elif hp <= 4:
            target = max(DAILY_SALARY * 0.7, median_prev + 1)
        else:
            target = max(DAILY_SALARY * 0.5, median_prev - 1)
    else:
        # No history - play safe
        if hp <= 2:
            target = DAILY_SALARY * 0.95
        elif hp <= 4:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.6
    
    # Ensure we don't exceed budget
    bid = min(budget, target)
    # Always ensure we can get water if supply is high enough
    # But if supply is very low, we may need to bid higher
    # Use supply to adjust: lower supply means higher competition
    supply_factor = 1.0 + (MAX_SUPPLY - supply) / MAX_SUPPLY  # 1.0 to 1.4
    bid = bid * supply_factor
    bid = min(budget, bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    max_winners = int(supply // WATER_REQ)  # floor division
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Get yesterday's bids from opponents with previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine baseline bid based on health and urgency
    if hp <= 0:
        # desperate
        bid = budget * 0.3
    elif no_water_days >= 2 or hp <= 2:
        # need water soon
        bid = DAILY_SALARY * 0.85
    elif hp <= 5:
        # moderate health
        bid = DAILY_SALARY * 0.6
    else:
        # comfortable
        bid = DAILY_SALARY * 0.45
    
    # Adjust based on yesterday's competition
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        min_prev = min(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        # If opponents bid very high yesterday, we may need to increase
        if max_prev > DAILY_SALARY * 0.8:
            # high pressure; if we are healthy, stay moderate; if desperate, match high
            if no_water_days >= 2 or hp <= 3:
                bid = max(bid, avg_prev * 0.95)
            else:
                bid = min(bid, DAILY_SALARY * 0.5)
        else:
            # moderate pressure, we can lower slightly
            if no_water_days < 2 and hp > 5:
                bid = min(bid, avg_prev * 0.8)
    
    # Adjust based on supply (number of winners)
    if max_winners <= 1:
        # scarce water; need to bid higher
        bid = max(bid, DAILY_SALARY * 0.6)
    elif max_winners >= 3:
        # plentiful, can lower
        bid = min(bid, DAILY_SALARY * 0.5)
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Ensure non-negative
    bid = max(bid, 0)
    
    # Small randomness to avoid predictability
    import random
    noise = random.uniform(0.95, 1.05)
    bid *= noise
    bid = round(bid, 2)
    
    # Final cap at budget
    bid = min(bid, budget)
    return max(bid, 0.01)
"""
