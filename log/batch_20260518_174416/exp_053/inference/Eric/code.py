# ============================================================
# Experiment: exp_053
# Agent: Eric
# Source: exp_053
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.9)
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        target_bid = max(DAILY_SALARY * 0.45, max_prev + 1)
        return min(my_budget, target_bid)
    
    return min(my_budget, DAILY_SALARY * 0.55)
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

    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: need water if no_water_days > 0 or hp <= 5
    need_water = no_water_days > 0 or hp <= 5

    # Determine supply pressure (lower supply -> higher bid needed)
    supply_factor = max(0, (25 - supply) / 10)  # 0 when supply=25, 1 when supply=15
    base_bid = DAILY_SALARY * 0.4 + supply_factor * DAILY_SALARY * 0.3

    if need_water:
        # Ensure we win: consider yesterday's max bid
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            bid = min(budget, max(base_bid + 5, max_yesterday + 2))
        else:
            bid = min(budget, base_bid + 10)
        # Cap at salary to preserve budget
        bid = min(bid, DAILY_SALARY * 0.9)
    else:
        # Not desperate, bid low to conserve
        if yesterday_bids:
            min_yesterday = min(yesterday_bids)
            bid = min(budget, max(DAILY_SALARY * 0.2, min_yesterday - 5))
        else:
            bid = min(budget, DAILY_SALARY * 0.25)

    # Ensure bid is non-negative and within budget
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
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If low on HP, outbid yesterday's max by a margin
        if hp <= 2:
            target = min(budget, highest_prev + 2.0)
            return max(target, DAILY_SALARY * 0.7)
        elif hp <= 5:
            target = min(budget, highest_prev + 1.0)
            return max(target, DAILY_SALARY * 0.5)
        else:
            # Conserve when healthy, bid low
            return min(budget, DAILY_SALARY * 0.3)
    else:
        # No history, use default based on HP
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        elif hp <= 5:
            return min(budget, DAILY_SALARY * 0.6)
        else:
            return min(budget, DAILY_SALARY * 0.3)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ =
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
    num_alive = len(alive_opponents)

    # Estimate opponent bids from previous_trace
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Determine aggressiveness from previous bids
    if prev_bids:
        max_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
    else:
        max_prev_bid = 0
        avg_prev_bid = 0

    # Calculate total demand
    total_demand = WATER_REQ * (num_alive + 1)  # including self
    # Water shortage indicator
    shortage = supply < total_demand

    # Base bid: try to win water if needed
    if my_hp <= 2 or no_water_days >= 1:
        # Critical: need water
        if prev_bids:
            bid = max_prev_bid + 1.5
        else:
            bid = DAILY_SALARY * 0.9
        bid = min(bid, my_budget, DAILY_SALARY * 0.95)
        return max(bid, 1)

    if shortage:
        # Need to compete
        if prev_bids:
            bid = max_prev_bid + 0.5
        else:
            bid = DAILY_SALARY * 0.6
        bid = min(bid, my_budget, DAILY_SALARY * 0.85)
        return max(bid, 1)

    # Water is abundant, bid low to save budget
    if prev_bids:
        bid = min(prev_bids) * 0.8
    else:
        bid = DAILY_SALARY * 0.2
    bid = max(bid, 1)
    bid = min(bid, my_budget)
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # collect maximum previous bid from alive opponents
    max_prev_bid = 0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bid = prev['bid']
                if prev_bid > max_prev_bid:
                    max_prev_bid = prev_bid
    
    # base decision on health and desperation
    if my_status['no_water_days'] > 0:
        # desperate: bid high to get water
        bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] > 5:
        # healthy, try to save money
        bid = min(my_status['budget'], 30)
    else:
        # moderate health, compete
        bid = min(my_status['budget'], max(40, max_prev_bid + 1))
    
    # ensure bid is non-negative
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    if my_hp <= 2 or no_water > 0:
        target_bid = min(my_budget, 140 * 0.9)
    else:
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            if max_prev > 140 * 0.8:
                target_bid = min(my_budget, 140 * 0.3)
            else:
                target_bid = min(my_budget, max_prev + 1.0)
        else:
            target_bid = min(my_budget, 140 * 0.5)
    
    # Ensure valid bid
    if target_bid < 0:
        target_bid = 0
    if target_bid > my_budget:
        target_bid = my_budget
    return target_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine baseline bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.8:
            # Opponents are aggressive, be conservative if HP is okay
            if my_status['hp'] > 4:
                bid = min(my_status['budget'], DAILY_SALARY * 0.35)
            else:
                bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            # Moderate, try to undercut by a small margin
            bid = min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev + 1.5))
    else:
        # No history, use default based on HP
        if my_status['hp'] <= 2:
            bid = min(my_status['budget'], DAILY_SALARY * 0.85)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.5)
    
    # Ensure we can afford water if needed
    # Estimate how many units we can secure: price per unit = min(bid, supply) / supply? No.
    # We'll use a simple quadratic to avoid overbidding when supply is low
    supply_ratio = supply / 25.0
    if supply_ratio < 0.7 and my_status['hp'] > 3:
        bid = min(bid, DAILY_SALARY * 0.4)  # conserve budget if plenty HP
    
    return max(1.0, min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = int(day_context['supply'])  # ensure integer
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = my_status['budget']
    no_water_days = int(my_status['no_water_days'])
    
    # Collect previous bids from opponents that are alive and have a trace
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):  # only consider alive opponents
            trace = opp.get('previous_trace')
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])
    
    # Determine highest previous bid among opponents
    if prev_bids:
        highest_prev = max(prev_bids)
    else:
        highest_prev = DAILY_SALARY * 0.4  # default if no info
    
    # Base bid: need to outcompete but not overpay
    # If supply is low, competition is higher
    if supply < WATER_REQ * 2:  # supply less than twice requirement
        target_bid = max(DAILY_SALARY * 0.6, highest_prev + 1)
    else:
        target_bid = max(DAILY_SALARY * 0.4, highest_prev * 0.8)
    
    # Adjust based on personal urgency
    if hp <= 2 or no_water_days >= 1:
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    
    # Cap by budget and ensure non-negative
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']

    # Collect previous bids from opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])

    # Estimate highest likely opponent bid based on past averages
    if prev_bids:
        # Use max of previous bids plus buffer, but cap
        estimated_highest = max(prev_bids) + 5
    else:
        # Default conservative guess based on salary and water requirement
        estimated_highest = DAILY_SALARY * 0.6  # ~84

    # Base bid: enough to beat estimated highest, but not exceed budget
    desired_bid = max(DAILY_SALARY * 0.3, estimated_highest + 2)

    # Adjust based on HP: if low HP, bid more aggressively
    if hp <= 2:
        desired_bid = max(desired_bid, DAILY_SALARY * 0.8)
    elif hp <= 4:
        desired_bid = max(desired_bid, DAILY_SALARY * 0.7)

    # Also consider supply: if supply is high, fewer competitors might bid high
    winners_count = supply // WATER_REQ
    if winners_count >= 2:
        # More water available, can lower bid slightly
        desired_bid = min(desired_bid, DAILY_SALARY * 0.65)

    # Ensure we don't bid more than budget and not negative
    bid = min(budget, max(0, desired_bid))
    return bid
"""
