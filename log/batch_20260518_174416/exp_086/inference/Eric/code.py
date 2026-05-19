# ============================================================
# Experiment: exp_086
# Agent: Eric
# Source: exp_086
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
    supply = int(day_context['supply'])
    current_day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # gather previous bids from yesterday for alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    if prev_bids:
        max_prev_bid = max(prev_bids)
    else:
        max_prev_bid = 0
    
    # base bid as fraction of salary
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # adjust based on yesterday's highest bid
    if max_prev_bid > 0:
        if max_prev_bid >= DAILY_SALARY * 0.85:
            # opponents were aggressive; try to outbid slightly
            target_bid = max(base_bid, max_prev_bid + 2)
        else:
            # moderate competition, stay near base
            target_bid = max(base_bid, max_prev_bid + 1)
    else:
        target_bid = base_bid
    
    # also consider supply tightness
    if supply < (MIN_SUPPLY + MAX_SUPPLY) / 2:
        target_bid *= 1.2
    
    # ensure we don't bid more than budget and at least 1
    bid = min(budget, target_bid)
    bid = max(bid, 1)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Extract last bids from previous_trace
    last_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            last_bids.append(trace['bid'])
    
    # Base bid: moderate to save money
    base_bid = DAILY_SALARY * 0.55
    
    # Adjust based on health
    if hp <= 2:
        # Desperate for water
        target_bid = DAILY_SALARY * 0.9
    elif hp <= 5:
        target_bid = DAILY_SALARY * 0.7
    else:
        target_bid = base_bid
    
    # Respond to opponents' previous high bids
    if last_bids:
        max_prev = max(last_bids)
        if max_prev >= DAILY_SALARY * 0.85:
            # If they bid high, avoid if healthy, else outbid slightly
            if hp > 3:
                target_bid = min(target_bid, DAILY_SALARY * 0.4)
            else:
                target_bid = max(target_bid, DAILY_SALARY * 0.8)
        else:
            # Outbid them by small margin if affordable
            target_bid = max(target_bid, max_prev + 1.0)
    
    # Never bid more than budget
    return min(budget, target_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Extract alive opponents and their yesterday bids
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Determine bid based on HP, budget, and yesterday pressure
    budget = my_status['budget']
    hp = my_status['hp']
    # If HP is critically low, must secure water
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
        return int(bid)  # ensure integer
    # If we have high yesterday pressure, adjust
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If someone was very aggressive, we may need to outbid slightly
        if max_yesterday >= DAILY_SALARY * 0.85:
            # They are desperate; if we are healthy, we can bid less
            if hp > 4:
                bid = min(budget, DAILY_SALARY * 0.4)
            else:
                bid = min(budget, max_yesterday + 2.0)
        else:
            # Normal competition: outbid by a small margin if within budget
            bid = min(budget, max_yesterday + 1.5)
        return int(bid)
    # No yesterday info: baseline conservative bid
    if hp <= 4:
        bid = min(budget, DAILY_SALARY * 0.7)
    else:
        bid = min(budget, DAILY_SALARY * 0.5)
    return int(bid)
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
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Get yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Adjust based on my health
    if my_status['hp'] <= 2:
        target_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    else:
        # Outbid the highest previous bid by a small margin
        target_bid = max(DAILY_SALARY * 0.5, max_prev_bid + 1)
        target_bid = min(target_bid, my_status['budget'], DAILY_SALARY)
    
    # Also consider supply: if supply low, be more aggressive
    supply = day_context['supply']
    if supply < (WATER_REQ * (len(alive_opponents) + 1) / 2): # rough shortage indicator
        target_bid = max(target_bid, DAILY_SALARY * 0.8)
    
    return min(my_status['budget'], target_bid)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            previous_bids.append(prev['bid'])
    supply = day_context['supply']
    supply_int = int(supply)
    base_bid = DAILY_SALARY * 0.5
    if previous_bids:
        avg_prev = sum(previous_bids) / len(previous_bids)
        bid = max(base_bid, avg_prev + 1.0)
    else:
        bid = base_bid
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        bid = max(bid, DAILY_SALARY * 0.8)
    bid = min(bid, my_status['budget'])
    bid = min(bid, DAILY_SALARY * 0.95)
    return max(0, bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev = max(prev_bids) if prev_bids else 0
    base_bid = max(DAILY_SALARY * 0.5, max_prev + 1.5)
    num_winners = int(supply // WATER_REQ)
    if my_hp <= 2:
        desired_bid = min(my_b
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    # Urgency: if no water or hp critical
    if no_water > 0 or hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
        return bid
    
    # If supply is high, bid low
    if supply >= 20:
        return min(budget, DAILY_SALARY * 0.3)
    
    # Moderate or low supply
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        target = max_prev + 1
        target = min(target, DAILY_SALARY * 0.6)
        target = min(target, budget)
        return max(DAILY_SALARY * 0.2, target)
    else:
        return min(budget, DAILY_SALARY * 0.4)
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
    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        bid = trace.get('bid')
        if bid is not None:
            prev_bids.append(bid)
    max_prev = max(prev_bids) if prev_bids else 0

    # Urgent need for water
    if hp <= 2 or no_water >= 1:
        target = max(max_prev + 1.0, DAILY_SALARY * 0.6)
        return min(budget, target)
    else:
        # Conserve budget based on yesterday's aggression
        if max_prev >= DAILY_SALARY * 0.9:
            return min(budget, DAILY_SALARY * 0.4)
        elif max_prev >= DAILY_SALARY * 0.7:
            return min(budget, max_prev + 1.0)
        else:
            return min(budget, DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    # Base bid: 60% of daily salary
    base_bid = DAILY_SALARY * 0.6
    # Adjust based on personal health and water needs
    if my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['no_water_days'] >= 1:
        base_bid = DAILY_SALARY * 0.8
    # Respond to high previous bids
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 0.7:
            target = max_prev + 1.5
            if target > DAILY_SALARY * 0.95:
                target = DAILY_SALARY * 0.95
            base_bid = max(base_bid, target)
    # Ensure bid does not exceed budget
    bid = min(base_bid, my_status['budget'])
    if bid < 1:
        bid = 0
    return bid
"""
