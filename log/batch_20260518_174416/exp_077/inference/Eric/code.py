# ============================================================
# Experiment: exp_077
# Agent: Eric
# Source: exp_077
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    salary = 140
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Determine base bid based on health
    if hp <= 2:
        base_bid = 0.9 * salary
    else:
        base_bid = 0.5 * salary
    
    # Consider yesterday's traces if available (optional refinement)
    for opp in opponents_status.values():
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            # Not enough data yet; ignore for now
            pass
    
    # Constrain by budget and ensure non-negative
    bid = min(base_bid, budget)
    bid = max(0, bid)
    
    # Return as float (acceptable)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    num_winners = supply // WATER_REQ
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    # Determine if any opponent was aggressive yesterday
    max_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # Base bid proportion
    if max_prev_bid > DAILY_SALARY * 0.75:
        # Aggressive opponent detected – adapt
        if my_hp <= 3:
            # Need water urgently, outbid aggressively
            target_bid = min(my_budget, DAILY_SALARY * 0.95)
        else:
            # Let them waste, stay low
            target_bid = min(my_budget, DAILY_SALARY * 0.4)
    else:
        # Normal situation
        if my_hp <= 3:
            target_bid = min(my_budget, DAILY_SALARY * 0.85)
        elif my_hp <= 5:
            target_bid = min(my_budget, DAILY_SALARY * 0.6)
        else:
            target_bid = min(my_budget, DAILY_SALARY * 0.5)
    
    # Ensure we don't bid more than necessary to beat a potential last winner
    # Simple: if many opponents, bid slightly above threshold
    num_alive = len(alive_opponents)
    if num_alive >= 3 and my_hp <= 5:
        target_bid = min(my_budget, target_bid * 1.1)
    
    # Clamp to avoid negative or zero
    bid = max(1.0, round(target_bid, 2))
    return min(bid, my_budget)
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
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Collect previous bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    
    # Determine baseline from yesterday's max
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
    else:
        highest_prev = DAILY_SALARY * 0.8  # default estimate
    
    # Adjust based on supply and desperation
    # Supply can satisfy at most supply // WATER_REQ agents
    max_satisfy = supply // WATER_REQ
    max_satisfy = int(max_satisfy)  # ensure int for index safety (not used as index though)
    
    # If supply is low (1 unit), we need to outbid everyone
    if max_satisfy <= 1:
        multiplier = 1.2
    elif max_satisfy == 2:
        multiplier = 1.0
    else:
        multiplier = 0.8
    
    # Urgency factor: hp low or no_water_days
    if hp <= 2 or no_water_days >= 1:
        urgency_mult = 1.3
    elif hp <= 5:
        urgency_mult = 1.1
    else:
        urgency_mult = 0.9
    
    target = highest_prev * multiplier * urgency_mult
    
    # Ensure we don't exceed budget
    bid = min(budget, target)
    # Ensure non-negative and at least a small bid
    bid = max(bid, DAILY_SALARY * 0.3)
    # Return as float (supply is float? But we output float)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    HP_CRITICAL_THRESHOLD = 3
    base_bid = DAILY_SALARY * 0.65
    if my_status['hp'] <= HP_CRITICAL_THRESHOLD:
        base_bid = DAILY_SALARY * 0.9
    # Ensure we don't bid more than budget
    bid = min(my_status['budget'], base_bid)
    # Keep bid as float; ensure no integer division issues
    return float(bid)
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
    return 15.0
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # Ensure integer
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    # Determine aggressive threshold from yesterday
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
    else:
        max_yesterday = 0.0
    
    # Water scarcity: number of competitors
    num_alive = len(alive_opponents)
    # Need water if supply is limited (if supply < num_alive * WATER_REQ, competition)
    # Simple heuristic
    if hp <= 4:
        # Urgent need for water
        target_bid = min(budget, max(DAILY_SALARY * 0.9, max_yesterday * 0.95 + 1))
    else:
        # Healthy, try to save
        if max_yesterday >= DAILY_SALARY * 0.8:
            # Others are aggressive, bid conservative
            target_bid = min(budget, DAILY_SALARY * 0.4)
        else:
            # Moderate competition
            target_bid = min(budget, max(DAILY_SALARY * 0.5, max_yesterday * 0.8))
    
    # Ensure we don't exceed budget
    return min(budget, target_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from opponents who have previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine target bid based on highest past pressure
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If opponent bid very aggressively, we need to compete only if necessary
        if highest_prev >= DAILY_SALARY * 0.9:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.85, highest_prev + 1.0))
        else:
            # Conservative bump above highest opponent
            base = max(DAILY_SALARY * 0.4, highest_prev + 1.5)
            return min(my_status['budget'], min(base, DAILY_SALARY * 0.8))
    
    # No info: adjust based on HP
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
    
    # Determine base bid considering supply scarcity
    # At low supply, competition is higher.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 when min, 1 when max
    
    # Base bid as fraction of salary, adjusted by supply
    if supply < WATER_REQ * len(alive_opponents) + 1:
        # Very scarce: need to bid high
        base_fraction = 0.7 + (1 - supply_ratio) * 0.2
    else:
        base_fraction = 0.5 + (1 - supply_ratio) * 0.1
    
    # Use opponent's previous bid to adjust
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        # If opponents were aggressive yesterday, be cautious unless desperate
        if max_prev_bid > DAILY_SALARY * 0.85:
            if hp > 3:
                target_bid = DAILY_SALARY * 0.4
            else:
                target_bid = DAILY_SALARY * 0.9
        else:
            # Bid slightly above average to secure water but not overpay
            target_bid = max(DAILY_SALARY * base_fraction, avg_prev_bid + 1.5)
    else:
        # No history: bid based on hp
        if hp <= 2:
            target_bid = DAILY_SALARY * 0.9
        elif hp <= 4:
            target_bid = DAILY_SALARY * 0.7
        else:
            target_bid = DAILY_SALARY * base_fraction
    
    # Ensure we don't bid more than budget
    bid = min(budget, target_bid)
    # Also ensure at least 1 to have a chance
    return max(1, bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for o in alive:
        trace = o.get('previous_trace')
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    urgent = (hp <= 2) or (no_water_days >= 1)
    ratio = WATER_REQ / max(supply, 1)
    base = DAILY_SALARY * ratio * 1.2

    if not alive:
        return min(budget, DAILY_SALARY * 0.3)

    if prev_bids:
        max_prev = max(prev_bids)
        if urgent:
            target = min(budget, max(base, max_prev * 1.1, DAILY_SALARY * 0.8))
        else:
            if max_prev > DAILY_SALARY * 0.8:
                target = min(budget, base * 0.8)
            else:
                target = min(budget, max(base, max_prev + 1.5))
    else:
        target = base if not urgent else DAILY_SALARY * 0.7
        target = min(budget, target)

    if urgent and budget > 0:
        target = max(target, DAILY_SALARY * 0.5)
    return target
"""
