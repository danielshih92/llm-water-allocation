# ============================================================
# Experiment: exp_100
# Agent: Eric
# Source: exp_100
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Count alive opponents
    alive = [o for o in opponents_status.values() if o['alive']]
    num_alive = int(len(alive))
    
    # Base bid: moderate fraction of salary
    base_bid = DAILY_SALARY * 0.45
    
    # Adjust for HP urgency
    if hp <= 2:
        bid = DAILY_SALARY * 0.85
    elif no_water_days >= 2:
        bid = DAILY_SALARY * 0.7
    else:
        bid = base_bid
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Round to avoid excessive precision
    return round(bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    if no_water >= 1 or hp <= 2:
        if prev_bids:
            max_prev = max(prev_bids)
            bid = max_prev + 2.0
        else:
            bid = DAILY_SALARY * 0.9
        return min(budget, bid)
    if prev_bids:
        sorted_bids = sorted(prev_bids, reverse=True)
        if len(sorted_bids) >= 2:
            target = sorted_bids[1]
        else:
            target = sorted_bids[0] * 0.8
        bid = min(target + 1.5, DAILY_SALARY * 0.7)
    else:
        bid = DAILY_SALARY * 0.5
    return min(budget, max(bid, DAILY_SALARY * 0.2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Collect yesterday's bids from alive opponents' previous_trace
    yesterday_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    # Define desired water amount (always need WATER_REQ)
    # Decision based on health and urgency
    if no_water_days >= 2 or hp <= 2:
        # Critical: bid high to ensure water
        max_affordable = min(budget, DAILY_SALARY * 0.95)
        # But we may not need to pay more than necessary; use yesterday's max as guide
        if yesterday_bids:
            highest_yesterday = max(yesterday_bids)
            bid = min(max_affordable, max(DAILY_SALARY * 0.8, highest_yesterday + 1.0))
        else:
            bid = max_affordable
    else:
        # Normal day: try to save money but stay competitive
        if yesterday_bids:
            avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
            # Bid slightly above average to have higher chance in top
            base_bid = avg_yesterday + 1.5
            # Cap at budget and salary
            bid = min(budget, DAILY_SALARY * 0.85, base_bid)
        else:
            # No info: moderate bid
            bid = min(budget, DAILY_SALARY * 0.65)
    
    # Ensure bid is non-negative and within budget
    bid = max(0.0, min(bid, budget))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    num_alive = len(alive_opponents)
    winners = int(supply // WATER_REQ)  # number of winners
    
    # Determine if we are desperate
    desperate = (hp <= 2) or (no_water_days >= 2)
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp_id, opp in alive_opponents.items():
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            prev_bids.append(prev_trace['bid'])
    
    # Default aggressive portion if desperate
    if desperate:
        base_bid = min(budget, DAILY_SALARY * 0.9)
        return base_bid
    
    # High supply case: bid low
    if supply >= 22:
        base_bid = min(budget, DAILY_SALARY * 0.35)
        return base_bid
    
    # Moderate supply: use opponent info if available
    if prev_bids:
        max_prev = max(prev_bids)
        # We want to be slightly above the highest previous bid if we expect competition
        target = max_prev + 2
        # Cap to budget and reasonable max
        target = min(target, budget, DAILY_SALARY * 0.8)
        return target
    else:
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Analyze yesterday's traces from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Base bid calculated from supply scarcity
    scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    base_bid = DAILY_SALARY * (0.4 + 0.4 * scarcity)
    
    # Adjust based on yesterday's highest bid among alive opponents
    if prev_bids:
        max_prev_bid = max(prev_bids)
        # If someone was aggressive yesterday, expect continuation
        if max_prev_bid >= DAILY_SALARY * 0.85:
            # They might be desperate or dominant; bid high enough to secure water
            if hp <= 2:
                target = min(budget, max(base_bid, max_prev_bid + 2.0))
            else:
                target = min(budget, max(base_bid, max_prev_bid + 0.5))
        else:
            # Moderate yesterday, typical competition
            target = min(budget, max(base_bid * 1.1, max_prev_bid + 1.0))
    else:
        # No info from yesterday, use base
        target = min(budget, base_bid)
    
    # Ensure we never bid more than budget, and consider HP criticality
    if hp <= 2:
        target = max(target, min(budget, DAILY_SALARY * 0.9))
    elif hp <= 4:
        target = max(target, min(budget, DAILY_SALARY * 0.6))
    
    # Ensure reasonable upper bound
    target = min(target, budget, DAILY_SALARY * 1.2)
    return int(target)
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
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Look at yesterday's bids from opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid strategy
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        # If they were aggressive yesterday, they might be again
        if highest_prev > DAILY_SALARY * 0.8:
            # They are aggressive; bid moderately but not too high
            base = DAILY_SALARY * 0.4
        else:
            base = DAILY_SALARY * 0.5
    else:
        base = DAILY_SALARY * 0.5
    
    # Adjust for supply scarcity
    supply_ratio = supply / WATER_REQ
    if supply_ratio < 2:
        base *= 1.3
    elif supply_ratio > 2.5:
        base *= 0.8
    
    # Adjust for personal need
    if no_water_days >= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 3:
        base = DAILY_SALARY * 0.8
    
    # Ensure within budget and reasonable
    bid = min(budget, max(DAILY_SALARY * 0.2, base))
    
    # Small random factor to avoid ties (use deterministic adjustment based on day)
    bid += (day * 0.1) % 1
    
    return int(bid) if bid <= budget else int(budget)
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

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    max_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])

    base = DAILY_SALARY * 0.5
    total_required = WATER_REQ * (1 + len(alive_opponents))

    if supply < total_required:
        bid = max(base, DAILY_SALARY * 0.7)
        if max_prev_bid > DAILY_SALARY * 0.85:
            bid = max(bid, max_prev_bid + 1.0)
    else:
        bid = base

    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif hp <= 4 and no_water_days > 0:
        bid = max(bid, DAILY_SALARY * 0.7)

    bid = min(bid, budget, DAILY_SALARY)
    bid = max(bid, 0)
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    if not yesterday_bids:
        # No info, default: modest bid
        base = DAILY_SALARY * 0.6
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], base)
    # Sort bids to get second highest
    sorted_bids = sorted(yesterday_bids, reverse=True)
    second_highest = sorted_bids[1] if len(sorted_bids) >= 2 else sorted_bids[0]
    # Bid slightly above second highest to secure water
    target = second_highest + 1.5
    # Cap based on HP and budget
    if my_status['hp'] <= 2:
        # Must get water
        bid = max(target, DAILY_SALARY * 0.85)
    else:
        bid = min(target, DAILY_SALARY * 0.7)
    # Never exceed budget
    bid = min(bid, my_status['budget'])
    # Ensure non-negative
    bid = max(0, bid)
    return bid
"""
