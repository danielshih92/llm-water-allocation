# ============================================================
# Experiment: exp_060
# Agent: Eric
# Source: exp_060
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Check if any opponents have previous trace (not first day)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    has_history = any(o.get('previous_trace') for o in alive_opponents)
    
    if has_history:
        # Analyze yesterday's bids
        prev_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
        if prev_bids:
            max_prev = max(prev_bids)
            # If someone bid very high yesterday, they might be desperate; outbid them slightly if we need water
            if max_prev >= DAILY_SALARY * 0.85:
                if my_status['hp'] <= 3:
                    return min(my_status['budget'], max_prev + 1.5)
                else:
                    return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                # Otherwise, bid just above their max to secure water
                return min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev + 2.0))
    
    # No history or fallback: bid based on HP and budget
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.85)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.45)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive = [o for o in opponents_status.values() if o.get('alive')]
    
    # gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace is not None and isinstance(trace, dict) and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # base strategy: match or slightly beat the highest yesterday bid
    if prev_bids:
        target = max(prev_bids) + 1.5
        # but cap by salary and budget
        max_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        bid = min(max_bid, target)
    else:
        # no info: conservative but safe
        bid = min(my_status['budget'], DAILY_SALARY * 0.5)
    
    # adjust for low HP
    if my_status['hp'] <= 3:
        bid = max(bid, min(my_status['budget'], DAILY_SALARY * 0.95))
    
    # ensure non-negative and within budget
    return float(max(0.0, min(my_status['budget'], bid)))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    # Get alive opponents and their previous bid
    max_prev_bid = 0
    has_prev = False
    for opp in opponents_status.values():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and 'bid' in prev_trace and prev_trace['bid'] is not None:
                bid_val = prev_trace['bid']
                if bid_val > max_prev_bid:
                    max_prev_bid = bid_val
                    has_prev = True

    # Base bid: if desperate HP <= 2, go high
    if hp <= 2:
        target = min(budget, DAILY_SALARY * 0.95)
    else:
        if has_prev:
            # Slightly above highest previous bid, but cap at budget
            target = min(budget, max_prev_bid + 2.0)
            # Adjust based on supply: if high supply, can be lower
            if supply >= 20:  # upper half
                target = min(target, DAILY_SALARY * 0.75)
        else:
            # No previous info: use a moderate bid
            target = min(budget, DAILY_SALARY * 0.6)

    # Ensure bid is not below zero
    bid = max(0.0, target)
    # If budget is very low, bid everything
    if budget < DAILY_SALARY * 0.3:
        bid = budget

    # Protect against float index errors: none here
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])  # ensure int
    day = int(day_context['day'])
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))
    # Determine baseline aggressive bid
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # Add margin based on my health
        if my_hp <= 2:
            target_bid = max_yesterday + 15.0
        elif my_hp <= 5:
            target_bid = max_yesterday + 10.0
        else:
            target_bid = max_yesterday + 5.0
    else:
        # No history, use default
        target_bid = DAILY_SALARY * 0.7
    # Ensure we don't exceed budget and at least reasonable
    max_afford = my_budget * 0.9  # save some
    bid = min(target_bid, max_afford)
    # If supply is very low, increase bid
    if supply < 18:
        bid = max(bid, DAILY_SALARY * 0.9)
    # Ensure bid is >= 0
    bid = max(0.0, bid)
    # Cap at budget to avoid error
    bid = min(bid, my_budget)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']

    alive_opps = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opps.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    # Urgency: need water soon
    urgent = (hp <= 2 or no_water_days > 0)

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        min_prev = min(yesterday_bids)
        # Cindy-like: if max_prev > DAILY_SALARY * 0.9 (126), avoid unless urgent
        if max_prev > 120:
            if urgent:
                bid = min(budget, max_prev + 5)
            else:
                # bid moderately to try to beat lower bidders
                bid = min(budget, max(DAILY_SALARY * 0.3, min_prev + 5))
        else:
            # moderate competition
            if urgent:
                bid = min(budget, max_prev + 5)
            else:
                bid = min(budget, max(DAILY_SALARY * 0.25, min_prev + 5))
    else:
        # no previous data, use safe default
        if urgent:
            bid = min(budget, DAILY_SALARY * 0.8)
        else:
            bid = min(budget, DAILY_SALARY * 0.35)

    # Ensure bid is at least 0 and integer
    bid = max(0, int(bid))
    bid = min(bid, budget)
    return bid
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Get yesterday's bids from opponents that are alive
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: if low HP, bid high; else conservative
    if hp <= 2 or no_water_days >= 1:
        base_bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        base_bid = min(budget, DAILY_SALARY * 0.7)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.4)
    
    # Adjust based on opponent history: if yesterday had high bids, increase
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # Target to slightly exceed the highest previous bid if we need to beat them
        target = max(base_bid, min(budget, max_yesterday + 1.0))
        # But if supply is low, be more aggressive
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
        if scarcity > 0.5:
            target = max(target, min(budget, DAILY_SALARY * 0.8))
        final_bid = target
    else:
        final_bid = base_bid
    
    # Ensure we don't bid more than budget
    return min(budget, round(final_bid, 2))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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

    # Extract yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # Supply scarcity factor
    scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1, 1=scarce

    # Base bid: if max_prev_bid high and we are safe, bid low
    if max_prev_bid >= DAILY_SALARY * 1.2:  # e.g., 168
        if hp > 4:
            bid = DAILY_SALARY * 0.2  # 28
        else:
            bid = DAILY_SALARY * 0.8  # 112
    elif max_prev_bid >= DAILY_SALARY * 0.8:  # 112
        if hp <= 2:
            bid = DAILY_SALARY * 0.95  # 133
        else:
            bid = max(max_prev_bid * 0.9, DAILY_SALARY * 0.5)  # ~100-70
    else:
        if hp <= 2:
            bid = DAILY_SALARY * 0.9  # 126
        elif hp <= 4:
            bid = DAILY_SALARY * 0.6  # 84
        else:
            bid = DAILY_SALARY * 0.3  # 42

    # Adjust for scarcity: increase bid if supply low
    if scarcity > 0.6:
        bid *= 1.3
    elif scarcity > 0.3:
        bid *= 1.1

    # Cap at budget
    bid = min(budget, bid)
    # Ensure minimum 1 if budget allows
    if budget > 0 and bid < 1:
        bid = 1

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    if no_water > 0:
        return min(budget, DAILY_SALARY * 0.9)
    if hp <= 3:
        return min(budget, DAILY_SALARY * 0.85)
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev >= DAILY_SALARY * 0.85:
            if hp > 5:
                return min(budget, DAILY_SALARY * 0.3)
            else:
                return min(budget, DAILY_SALARY * 0.95)
        else:
            target = max(DAILY_SALARY * 0.5, max_prev + 1.0)
            return min(budget, target)
    else:
        return min(budget, DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    prev_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive if o.get('previous_trace')]
    highest_prev = max(prev_bids) if prev_bids else 0
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        bid = min(budget, max(DAILY_SALARY * 0.9, highest_prev + 1))
    elif hp <= 4:
        bid = min(budget, max(DAILY_SALARY * 0.7, highest_prev + 0.5))
    else:
        bid = min(budget, DAILY_SALARY * 0.6)
    return round(bid, 1)
"""
