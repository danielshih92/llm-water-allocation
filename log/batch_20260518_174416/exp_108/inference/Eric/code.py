# ============================================================
# Experiment: exp_108
# Agent: Eric
# Source: exp_108
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    k = int(supply // WATER_REQ)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents or len(alive_opponents) < k:
        if my_status['hp'] < 3:
            return min(DAILY_SALARY * 0.8, my_status['budget'])
        return min(DAILY_SALARY * 0.2, my_status['budget'])
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        max_yesterday = max(yesterday_bids)
    else:
        avg_yesterday = DAILY_SALARY * 0.5
        max_yesterday = DAILY_SALARY * 0.6
    if my_status['hp'] < 2 or my_status['no_water_days'] >= 2:
        target = max_yesterday + 1.0
        return min(max(target, DAILY_SALARY * 0.3), my_status['budget'])
    bid = max(avg_yesterday * 0.9, DAILY_SALARY * 0.2)
    if supply < 18:
        bid = max(bid, DAILY_SALARY * 0.6)
    if my_status['hp'] > 4:
        bid = min(bid, DAILY_SALARY * 0.4)
    return min(bid, my_status['budget'])
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

    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    prev_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    if prev_bids:
        highest_prev = max(prev_bids)
        if supply < 18:
            base = max(highest_prev + 2, DAILY_SALARY * 0.9)
        else:
            base = max(highest_prev + 1, DAILY_SALARY * 0.7)
    else:
        base = DAILY_SALARY * 0.7

    if hp <= 2 or no_water_days > 0:
        bid = min(budget, base * 1.2)
    else:
        bid = min(budget, base)

    bid = max(0.0, bid)
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])
    max_prev = max(yesterday_bids) if yesterday_bids else 0.0
    hp = my_status['hp']
    budget = my_status['budget']
    no_water
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    n_alive = len(alive_opponents)
    # Urgency
    if my_status['hp'] <= 2:
        return min(my_status['budget'], int(SALARY * 0.95))
    # Supply stress
    supply = day_context['supply']
    stress = (n_alive * WATER_REQ) / supply if supply > 0 else 0
    base = SALARY * 0.5
    if stress > 1.5:
        base = SALARY * 0.7
    # Gather previous bids
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    if prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev > 100:
            bid = min(my_status['budget'], int(SALARY * 0.3))
        else:
            bid = min(my_status['budget'], int(max(base, highest_prev + 2)))
    else:
        bid = min(my_status['budget'], int(base))
    return max(0, bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_BID = 0.0
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            bid = trace.get('bid')
            if bid is not None:
                prev_bids.append(bid)
    if my_status['hp'] <= 2:
        target = min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 4:
        target = min(my_status['budget'], DAILY_SALARY * 0.6)
    else:
        target = min(my_status['budget'], DAILY_SALARY * 0.3)
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > DAILY_SALARY * 0.8:
            if my_status['hp'] <= 4:
                target = min(my_status['budget'], max_prev + 1.0)
            else:
                target = min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            target = min(my_status['budget'], max(DAILY_SALARY * 0.2, max_prev + 0.5))
    bid = max(MIN_BID, min(target, my_status['budget']))
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Determine desired bid based on health and supply
    if hp <= 2 or no_water_days >= 2:
        # desperate: need water
        desired_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        desired_bid = DAILY_SALARY * 0.7
    else:
        # healthy: can be conservative
        if supply >= 20:
            desired_bid = DAILY_SALARY * 0.4
        elif supply >= 15:
            desired_bid = DAILY_SALARY * 0.5
        else:
            desired_bid = DAILY_SALARY * 0.6
    
    # Adjust to avoid overpaying: if yesterday's max is high, undercut slightly
    if max_yesterday_bid > desired_bid + 5:
        # opponents are aggressive, we can try to win with a slightly lower bid
        selected_bid = max_yesterday_bid - 2
    else:
        selected_bid = desired_bid
    
    # Ensure we don't bid more than budget
    final_bid = min(budget, selected_bid)
    # Ensure non-negative
    final_bid = max(final_bid, 0)
    
    # As per index rule, any use of supply in math must ensure int indices (none here)
    return final_bid
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
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base target bid calculation
    need_water = hp < WATER_REQ or no_water_days > 0

    if need_water:
        # Desire to win water: outbid highest previous by a small margin
        target = max(DAILY_SALARY * 0.4, highest_prev_bid + 1.5)
    else:
        # Conserve: bid much lower than highest, but not zero
        target = min(DAILY_SALARY * 0.7, max(DAILY_SALARY * 0.2, highest_prev_bid - 5.0))

    # Adjust for supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.5:
        target = target * 1.2  # scarcity premium

    # Don't exceed budget
    bid = min(budget, target)

    # If we are critically low on HP, try harder
    if hp <= 2 and need_water:
        bid = min(budget, max(DAILY_SALARY * 0.85, highest_prev_bid + 3.0))

    # Ensure bid is non-negative and no higher than daily salary * 1.5 (safety)
    bid = max(0.0, min(budget, DAILY_SALARY * 1.5, bid))

    # If day is late and we have plenty HP, be very conservative
    if day >= 8 and hp >= 6:
        bid = min(budget, DAILY_SALARY * 0.3)

    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']
    # Ensure supply is int for index use (though not used as index)
    supply = int(supply)
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid: 40% of salary
    base_bid = DAILY_SALARY * 0.4
    
    # If we have no_water_days, increase urgency
    if no_water_days > 0:
        base_bid = DAILY_SALARY * 0.6
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    
    # Adjust based on yesterday's highest bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If an opponent bid very high, we might need to raise if we want water
        if max_prev > DAILY_SALARY * 0.7:
            # Aggressive opponent: if we are healthy, bid slightly above to ensure water, else very high
            if hp > 3:
                base_bid = max(base_bid, max_prev + 1.5)
            else:
                base_bid = max(base_bid, max_prev + 0.5)
        else:
            # Weak opponents: bid just enough to secure water if needed, else stay low
            base_bid = max(base_bid, max_prev + 1.0)
    
    # Ensure we don't exceed budget
    bid = min(budget, base_bid)
    # Also never bid more than we can afford (already min)
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
    
    # Get yesterday's highest bid among alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if day_context['day'] == 1 or not yesterday_bids:
        # First day or no trace: bid based on HP
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 5:
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.5)
    
    highest_prev_bid = max(yesterday_bids)
    
    # If someone bid very high yesterday, they might repeat; conserve if possible
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            # Must secure water
            return min(my_status['budget'], DAILY_SALARY * 0.95)
    else:
        # Moderate pressure: match or slightly beat yesterday's high
        target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.0)
        return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    base_bid = max_prev_bid + 1.5
    if my_status['no_water_days'] >= 1:
        base_bid *= 1.2
    if my_status['hp'] <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    bid = min(base_bid, my_status['budget'], DAILY_SALARY * 0.95)
    return max(bid, 0)
"""
