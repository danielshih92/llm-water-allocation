# ============================================================
# Experiment: exp_033
# Agent: Eric
# Source: exp_033
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Check yesterday's traces to detect aggressive opponents
    high_bid_yesterday = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            high_bid_yesterday = max(high_bid_yesterday, prev['bid'])
    
    if high_bid_yesterday > 0:
        # If someone bid very high, they may be desperate; avoid heavy contest unless necessary
        if high_bid_yesterday >= DAILY_SALARY * 0.85:
            if hp > 3:
                # stay conservative
                base_bid = DAILY_SALARY * 0.3
            else:
                base_bid = DAILY_SALARY * 0.95
        else:
            # Slightly above yesterday's max to outbid if affordable
            base_bid = max(DAILY_SALARY * 0.5, high_bid_yesterday + 1.5)
    else:
        # No history: use HP-based default
        if hp <= 2:
            base_bid = DAILY_SALARY * 0.9
        else:
            base_bid = DAILY_SALARY * 0.55
    
    # Ensure we don't exceed budget and keep some for future
    final_bid = min(budget, base_bid)
    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    
    # Determine highest yesterday bid among alive
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Base bid on health and opponent pressure
    if hp <= 2:
        # Desperate: bid high to ensure water
        bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        # Moderate risk: top of what we saw yesterday
        bid = max(DAILY_SALARY * 0.6, max_yesterday + 1)
    else:
        # Healthy: slightly below yesterday's max to save
        bid = min(DAILY_SALARY * 0.7, max_yesterday - 1)
    
    # Ensure bid is within budget and not negative
    bid = max(0, min(budget, bid))
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
    if not alive_opponents:
        return int(min(budget, DAILY_SALARY * 0.4))

    # Get yesterday's max bid among alive opponents
    max_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']

    # Urgency: need water if no_water_days > 0 or hp too low
    urgent = (no_water_days > 0) or (hp <= 2)
    # Very urgent: about to die of thirst (no_water_days >= 2) or hp very low
    very_urgent = (no_water_days >= 2) or (hp <= 1)

    if very_urgent:
        # Bid very high to secure water
        target_bid = min(budget, DAILY_SALARY * 1.0)
        return int(target_bid)
    elif urgent:
        # Slightly under the max if possible, but ensure we beat if needed
        target_bid = min(budget, max_prev_bid + 5)
        return int(target_bid)
    else:
        # Not urgent: we can try to save money
        # If supply is high, we can afford to bid low and still maybe win
        # But opponents are aggressive, so bid just above their previous max if we want to win
        # Decide based on day: early days we can afford to lose some, later days must be careful
        if day <= 3:
            # Early: try to win cheaply if possible
            target_bid = min(budget, max_prev_bid + 1)
        else:
            # Late: need to secure water, bid a bit higher
            target_bid = min(budget, max_prev_bid + 3)
        # Ensure bid is not too low if we need water
        # But if we have enough hp, we can risk losing once
        # Cap at a reasonable maximum
        target_bid = max(target_bid, 0.0)
        return int(min(budget, target_bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure int
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # gather previous bids from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                prev_bids.append(float(trace['bid']))

    # no_water_days penalty: need water urgently if > 1
    urgency = 0
    if no_water_days >= 1:
        urgency = 0.2 * no_water_days
    if hp <= 2:
        urgency += 0.3

    # base bid: safe level to beat typical bids
    if prev_bids:
        max_prev = max(prev_bids)
        # target to beat highest previous bid by small margin
        target_bid = max_prev + 2.0
    else:
        target_bid = DAILY_SALARY * 0.5  # default for first day

    # adjust for supply scarcity
    scarcity_factor = 1.0
    if supply < WATER_REQ * 2:  # supply < 16
        scarcity_factor = 1.3
    elif supply < WATER_REQ * 3:
        scarcity_factor = 1.1

    bid = target_bid * scarcity_factor + urgency * DAILY_SALARY
    # cap to budget and not exceed reasonable max
    max_bid = min(budget, DAILY_SALARY * 0.9)
    bid = min(bid, max_bid)
    # ensure at least a small bid if alive
    if budget > 0:
        bid = max(bid, 5.0)
    else:
        bid = 0.0
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's highest bid among alive opponents
    highest_prev = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = prev['bid']
            if bid_val > highest_prev:
                highest_prev = bid_val
    
    # Determine our health urgency
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    
    # Baseline bid
    if hp <= 2 or no_water >= 1:
        # Desperate: bid up to 90% of salary
        target_bid = min(budget, DAILY_SALARY * 0.9)
    else:
        # Healthy: try to outbid yesterday's highest by a small margin
        if highest_prev > 0:
            target_bid = min(budget, highest_prev + 2.0)
        else:
            target_bid = DAILY_SALARY * 0.6
        # Cap at 85% of salary to avoid overbidding
        target_bid = min(target_bid, DAILY_SALARY * 0.85)
    
    # Never bid more than budget
    bid = min(budget, target_bid)
    # Ensure non-negative
    bid = max(0, bid)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    previous_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            previous_bids.append(prev_trace['bid'])
    if previous_bids:
        max_prev = max(previous_bids)
        desired_bid = max_prev + 1.5
    else:
        desired_bid = DAILY_SALARY * 0.7
    if my_status['hp'] <= 3:
        desired_bid = max(desired_bid, DAILY_SALARY * 0.85)
    desired_bid = min(desired_bid, my_status['budget'])
    if desired_bid < 0:
        desired_bid = 0
    return desired_bid
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

    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    # Base bid: 60% of salary
    base_bid = DAILY_SALARY * 0.6

    # Adjust for supply scarcity (lower supply -> higher bid)
    supply_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) * 10.0
    base_bid += supply_factor

    # Adjust for dehydration risk
    if no_water > 0:
        base_bid += 15.0 * no_water
    if hp <= 3:
        base_bid += 10.0

    # Ensure bid doesn't exceed 90% of budget or 120% of salary
    max_bid = min(budget * 0.9, DAILY_SALARY * 1.2)
    bid = min(base_bid, max_bid)

    # On early days, be slightly more aggressive to build HP buffer
    if day <= 3:
        bid = max(bid, DAILY_SALARY * 0.5)

    # Ensure bid is at least 1
    bid = max(bid, 1.0)

    return min(bid, budget)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Extract yesterday's max bid from alive opponents
    max_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']

    # Decide bid based on urgency
    if hp <= 2 or no_water_days >= 1:
        # Need water: bid high up to budget, try to beat max_prev_bid if feasible
        base_bid = min(budget, DAILY_SALARY * 0.9)
        if max_prev_bid > 0 and base_bid >= max_prev_bid - 1:
            # Can slightly outbid the highest previous opponent
            bid = min(budget, max_prev_bid + 1.0)
        else:
            bid = base_bid
        # Ensure bid is at least a minimum to avoid losing cheaply
        bid = max(bid, DAILY_SALARY * 0.5)
    else:
        # Healthy: conserve budget, bid modestly
        bid = min(budget, DAILY_SALARY * 0.4)

    # Never bid more than budget
    bid = min(bid, budget)
    # Ensure non-negative and not exceeding budget
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for oid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Determine base bid based on desperation
    if hp <= 0 or no_water_days > 1:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 2:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5

    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            # Opponents were aggressive yesterday; maybe they will be again
            # But we can try to save if we are not desperate
            if hp > 3 and no_water_days == 0:
                base_bid = max(base_bid, DAILY_SALARY * 0.3)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.85)
        else:
            # Opponents were moderate; we can try to outbid by a small margin
            base_bid = max(base_bid, highest_prev + 1.5)

    # Ensure bid does not exceed budget and is at least a small amount
    bid = min(budget, base_bid)
    bid = max(bid, 1.0)
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

    hp = my_status['hp']
    budget = my_status['budget']

    # Gather yesterday's highest bid among alive opponents
    highest_prev = 0.0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev['bid']
                if b > highest_prev:
                    highest_prev = b

    # Determine bid based on desperation
    if hp <= 2:
        # very desperate: bid up to budget but not more than daily salary * 1.2
        desired = min(budget, DAILY_SALARY * 1.2)
    elif hp <= 5:
        # moderate: outbid yesterday's highest by a small margin, or use a baseline
        base = max(DAILY_SALARY * 0.6, highest_prev + 2.0)
        desired = min(budget, base)
    else:
        # healthy: conservative bid slightly above average of yesterday's high
        base = max(DAILY_SALARY * 0.4, highest_prev + 1.0)
        desired = min(budget, base)

    # Ensure non-negative and not wasteful
    bid = max(0.0, desired)
    return min(bid, budget)
"""
