# ============================================================
# Experiment: exp_002
# Agent: Eric
# Source: exp_002
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # get yesterday's max bid from surviving opponents
    yesterday_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        # desperate: bid high
        bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        # moderate need
        bid = DAILY_SALARY * 0.6
    else:
        # comfortable
        bid = DAILY_SALARY * 0.4
    # adjust based on yesterday's competition
    if highest_yesterday > bid and hp <= 4:
        bid = max(bid, highest_yesterday + 1)
    # cap at budget
    return min(budget, bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    if not prev_bids:
        prev_bids = [DAILY_SALARY * 0.5]
    max_prev = max(prev_bids)
    # Determine base bid
    if my_hp <= 2 or no_water_days > 0:
        base_bid = min(my_budget, DAILY_SALARY * 0.9)
    else:
        base_bid = min(my_budget, max_prev + 1.5)
    # Adjust for supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.4:
        base_bid *= 1.2
    # Ensure we don't exceed budget and not too high
    final_bid = min(my_budget, max(base_bid, DAILY_SALARY * 0.2))
    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Determine high pressure from yesterday's bids
    highest_yesterday_bid = 0
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            highest_yesterday_bid = max(highest_yesterday_bid, trace['bid'])

    # Base bid: if any opponent bid high, match or exceed slightly
    if highest_yesterday_bid > DAILY_SALARY * 0.5:
        base_bid = highest_yesterday_bid + 1.5
    else:
        base_bid = DAILY_SALARY * 0.45

    # Adjust for urgency
    if no_water_days > 0 or hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    # Consider supply scarcity
    if supply < WATER_REQ * 2:
        base_bid += 10

    # Cap by budget
    bid = min(base_bid, budget)
    # Minimum reasonable bid
    bid = max(bid, 1.0)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    salary = 140
    water_req = 8
    
    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace and trace['bid'] is not None:
                prev_bids.append(trace['bid'])
    
    # Default cautious bid
    base_bid = salary * 0.5
    
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponents were aggressive, conserve budget
        if max_prev > salary * 0.8:
            if hp > 3:
                base_bid = salary * 0.35
            else:
                base_bid = salary * 0.8
        else:
            # Outbid the highest previous by a small margin
            base_bid = max_prev + 1.5
    else:
        # No history: bid moderately based on HP
        if hp <= 2:
            base_bid = salary * 0.9
        elif hp <= 4:
            base_bid = salary * 0.7
        else:
            base_bid = salary * 0.5
    
    # Ensure we don't exceed budget and within reasonable bounds
    bid = min(budget, max(1.0, base_bid))
    
    # On early days, be more conservative if healthy
    if day <= 2 and hp > 5:
        bid = min(bid, salary * 0.4)
    
    return int(bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Check alive opponents and get their previous max bid if available
    max_prev_bid = 0.0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # Determine aggressive threshold: if any opponent bid high yesterday, they might again
    # Use a reasonable target based on supply and my health
    if hp <= 2:
        # Desperate: bid enough to ensure water
        bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        # Low health: need water but not overpay
        bid = min(budget, max(DAILY_SALARY * 0.6, max_prev_bid * 0.8 + 2))
    else:
        # Healthy: conservative, but not too low to be beaten by aggressive bidders
        base = DAILY_SALARY * 0.35
        if max_prev_bid > DAILY_SALARY * 0.8:
            # Opponent was aggressive, so raise a bit
            base = DAILY_SALARY * 0.5
        bid = min(budget, base)
    
    # Ensure bid is non-negative and not more than budget
    bid = max(0.0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Count alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Base bid: fraction of salary depending on supply scarcity
    if supply <= 17:
        base_fraction = 0.6
    elif supply <= 20:
        base_fraction = 0.5
    else:
        base_fraction = 0.4
    
    # Adjust for low hp
    if hp <= 2:
        urgency_mult = 1.5
    elif hp <= 4:
        urgency_mult = 1.2
    else:
        urgency_mult = 1.0
    
    bid = DAILY_SALARY * base_fraction * urgency_mult
    
    # Ensure bid does not exceed budget
    bid = min(bid, budget)
    
    # If no water for many days, bid more aggressively
    if my_status['no_water_days'] >= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    
    # Round to avoid floating point issues
    bid = round(bid, 2)
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        high_threshold = DAILY_SALARY * 0.85
        if highest_prev >= high_threshold:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            base_bid = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
            return min(my
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
    
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Gather previous bids from alive opponents
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev.get('bid'), (int, float)):
            prev_bids.append(prev['bid'])
    
    if prev_bids:
        max_prev = max(prev_bids)
        # If someone bid extremely high (likely Cindy), ignore and bid conservatively
        if max_prev > DAILY_SALARY * 2:
            if my_status['hp'] <= 3:
                # Need water badly but avoid wasting; bid just enough to beat moderate opponents
                return min(my_status['budget'], DAILY_SALARY * 0.75)
            else:
                # Conserve budget, let others fight
                return min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            # Normal competition: bid slightly above highest previous bid if needed
            target = max(DAILY_SALARY * 0.5, max_prev + 1.0)
            if my_status['hp'] <= 2:
                target = max(target, DAILY_SALARY * 0.85)
            elif my_status['hp'] > 5:
                target = min(target, DAILY_SALARY * 0.6)
            return min(my_status['budget'], target)
    
    # No previous bids: use default
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] > 5:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    yesterday_bids = []
    for aid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If someone bid very high yesterday, they may repeat; avoid overbidding
        if max_yesterday >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                target = DAILY_SALARY * 0.3
            else:
                target = DAILY_SALARY * 0.95
        else:
            # Slightly above max yesterday, but not too high
            target = max(DAILY_SALARY * 0.5, max_yesterday + 1.5)
    else:
        # No trace information; conservative
        if my_status['hp'] <= 2:
            target = DAILY_SALARY * 0.9
        else:
            target = DAILY_SALARY * 0.55
    
    # Ensure we don't exceed budget
    bid = min(my_status['budget'], target)
    # Ensure bid is at least 0
    return max(0, bid)
"""
