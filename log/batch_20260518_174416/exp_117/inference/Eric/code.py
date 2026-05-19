# ============================================================
# Experiment: exp_117
# Agent: Eric
# Source: exp_117
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # No previous traces available, use default strategy
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.5)
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
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = prev['bid']
            if b > highest_prev_bid:
                highest_prev_bid = b
    # Determine urgency based on hp and no_water_days
    if hp <= 2 or no_water_days >= 2:
        # desperate: need water at almost any cost
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # moderate need
        bid = min(budget, max(DAILY_SALARY * 0.6, highest_prev_bid + 0.5))
    else:
        # healthy, try to conserve
        bid = min(budget, max(DAILY_SALARY * 0.3, highest_prev_bid + 0.1))
    # Ensure bid is positive and not exceeding budget
    bid = max(0.0, min(budget, bid))
    # Adjust based on supply vs demand: if supply high, can lower bid slightly
    # But keep it simple
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
    
    # Estimate number of winners
    max_winners = int(supply // WATER_REQ)
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(bid)
    
    # Determine base bid
    if hp <= 2 or no_water_days > 0:
        base_bid = DAILY_SALARY * 0.9
    else:
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            if max_prev > DAILY_SALARY * 0.8:
                base_bid = max_prev * 0.95
            else:
                base_bid = max(DAILY_SALARY * 0.5, max_prev + 1)
        else:
            base_bid = DAILY_SALARY * 0.6
    
    bid = min(budget, base_bid)
    bid = max(bid, 0)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
    
    # Determine yesterday's max opponent bid from previous_trace
    yesterday_max_bid = 0
    for opp_id, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            if trace['bid'] > yesterday_max_bid:
                yesterday_max_bid = trace['bid']
    
    # Supply scarcity factor
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    scarcity = 1.0 - supply_ratio  # higher when supply is low
    
    # Base bid on hp and no_water_days
    urgency = 0.0
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 6:
        urgency = 0.4
    
    # If opponent yesterday had a high bid (indicating aggressor like Cindy), we may need to bid higher
    aggressive_opponent_bid = yesterday_max_bid if yesterday_max_bid > 0 else 0
    # Expected baseline is DAILY_SALARY * 0.5 = 70, but we can adjust
    if aggressive_opponent_bid > DAILY_SALARY * 0.8:
        # Very aggressive opponent, we need to compete strongly
        target_bid = min(budget, max(DAILY_SALARY * 0.9, aggressive_opponent_bid + 2))
    elif aggressive_opponent_bid > DAILY_SALARY * 0.5:
        target_bid = min(budget, max(DAILY_SALARY * 0.7, aggressive_opponent_bid + 1))
    else:
        # No high opponent bid, use urgency and scarcity
        target_bid = DAILY_SALARY * (0.5 + 0.3 * urgency + 0.2 * scarcity)
    
    # Ensure we don't bid more than budget and cap at a reasonable level
    bid = min(budget, target_bid)
    # Ensure bid is non-negative and not too small if we need water
    if urgency >= 0.7:
        bid = max(bid, DAILY_SALARY * 0.4)
    else:
        bid = max(bid, 1)  # at least 1 to participate
    
    # Round to 1 decimal
    bid = round(bid, 1)
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: low if healthy, high if desperate
    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.4
    
    # Adjust based on opponent's past maximum bid
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # Need to ensure we get water if supply is low
        if supply < 20:
            # competitive scenario: outbid the highest previous bid by a small margin
            required = max(base_bid, max_prev_bid + 2.0)
        else:
            required = max(base_bid, max_prev_bid * 0.9)
    else:
        required = base_bid
    
    # Ensure we don't exceed budget and stay positive
    final_bid = min(my_budget, required)
    # Also ensure non-negative
    final_bid = max(0, final_bid)
    return int(final_bid)
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    n_alive = len(alive_opponents)
    
    # Determine number of potential winners
    n_winners = int(supply // WATER_REQ)
    
    # Get yesterday's max bid from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    
    # Base bid calculation
    if no_water_days > 0:
        # Dehydrated, need water urgently
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 2:
        # Low HP, need water
        bid = min(budget, DAILY_SALARY * 0.85)
    else:
        # Healthy, conserve budget
        if n_alive <= 1:
            bid = min(budget, DAILY_SALARY * 0.3)
        else:
            # Only bid enough to beat yesterday's max if we think it's necessary
            if max_prev_bid < DAILY_SALARY * 0.5:
                bid = min(budget, DAILY_SALARY * 0.5)
            else:
                # Aggressive opponent(s) - match or slightly exceed
                target = max(DAILY_SALARY * 0.6, max_prev_bid + 1.0)
                bid = min(budget, target)
    
    # Ensure we never bid more than budget
    bid = max(0.0, min(budget, bid))
    # If we are out of budget, bid 0 (but that will cause death)
    return bid
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
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    high_threshold = DAILY_SALARY * 0.85  # 119
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev >= high_threshold:
            if my_status['hp'] <= 2:
                return min(my_status['budget'], max(DAILY_SALARY * 0.95, max_prev + 1))
            else:
                return min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev + 1))
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev + 2))
    else:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    # find yesterday's max bid among alive opponents
    max_prev = 0
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                max_prev = max(max_prev, prev['bid'])
    # conservative baseline: avoid overbidding if healthy
    if hp >= 2 and no_water < 2:
        target = max_prev + 1
        # cap at a reasonable multiple of salary
        target = min(target, DAILY_SALARY * 1.0)
    else:
        # desperate: bid high to secure water
        target = max(DAILY_SALARY * 0.9, max_prev + 5)
    # ensure within budget and at least 0
    return int(min(max(budget, 0), max(target, 0)))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Need water urgently: bid just above yesterday's max or high floor
        required = max(DAILY_SALARY * 0.9, yesterday_max_bid + 1.0)
        return min(my_status['budget'], required)
    else:
        # Healthy: bid conservatively
        if yesterday_max_bid > 0:
            base = max(DAILY_SALARY * 0.3, yesterday_max_bid + 0.5)
        else:
            base = DAILY_SALARY * 0.4
        return min(my_status['budget'], base)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0

    # Base bid: conservative, aim for low cost
    base_bid = max(DAILY_SALARY * 0.4, 1)

    # If HP is critical, bid higher
    if hp <= 2:
        target_bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        target_bid = min(budget, max(base_bid, DAILY_SALARY * 0.8))
    else:
        # Good HP: try to save money, but ensure not too low
        target_bid = min(budget, base_bid)

    # Avoid outbidding yesterday's max if we can afford to lose
    # If we have enough HP, stay below max_yesterday_bid to save
    if hp > 3 and target_bid > max_yesterday_bid:
        target_bid = max(base_bid, max_yesterday_bid - 1)

    # Ensure bid is positive and within budget
    final_bid = max(0, min(budget, target_bid))
    return int(final_bid * 100) / 100  # round to cents
"""
