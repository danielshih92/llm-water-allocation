# ============================================================
# Experiment: exp_012
# Agent: Eric
# Source: exp_012
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    max_prev = max(prev_bids) if prev_bids else 0
    base = DAILY_SALARY * 0.4
    if hp <= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 4:
        base = DAILY_SALARY * 0.6
    if supply < 18:
        base *= 1.2
    if max_prev > 0 and max_prev + 1 > base:
        bid = min(budget, max_prev + 1)
    else:
        bid = min(budget, base)
    bid = max(0, bid)
    return bid
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid
    if hp <= 2:
        # Desperate: must win water
        base_bid = DAILY_SALARY * 0.9
    elif hp >= 5:
        # Healthy: can afford to be frugal
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            if max_yesterday >= DAILY_SALARY * 0.7:
                # Aggressive last day; still safe to bid low
                base_bid = DAILY_SALARY * 0.35
            else:
                base_bid = DAILY_SALARY * 0.4
        else:
            base_bid = DAILY_SALARY * 0.4
    else:
        # Moderate health
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            if max_yesterday >= DAILY_SALARY * 0.8:
                base_bid = DAILY_SALARY * 0.65
            else:
                base_bid = DAILY_SALARY * 0.5
        else:
            base_bid = DAILY_SALARY * 0.5
    
    # Adjust for supply scarcity
    avg_supply = (15 + 25) / 2.0
    if supply < avg_supply:
        base_bid *= 1.2  # increase bid when supply low
    elif supply > avg_supply:
        base_bid *= 0.85  # decrease bid when supply high
    
    # Ensure bid is within budget and at least 0
    bid = min(budget, base_bid)
    bid = max(0, bid)
    # Round to avoid fractional pennies if needed
    bid = round(bid, 2)
    return bid
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
    
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # Get yesterday's bids from opponent traces
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    # base target bid on yesterday's max
    if prev_bids:
        target = max(prev_bids)
    else:
        target = DAILY_SALARY * 0.6  # default if no data
    # adjust based on current hp and budget
    if my_status['hp'] <= 2:
        # desperate: bid up to 90% of salary
        bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 5:
        # moderate need: match target but cap at 70% salary
        bid = min(my_status['budget'], target, DAILY_SALARY * 0.7)
    else:
        # healthy: low bid, just above min to save budget
        bid = min(my_status['budget'], DAILY_SALARY * 0.4, target * 0.5)
    # ensure minimum bid to have a chance (at least 1)
    bid = max(1, bid)
    # ensure not exceeding budget
    bid = min(bid, my_status['budget'])
    return float(bid)
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
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    high_prev = max(prev_bids) if prev_bids else 0

    # Base bid logic
    if hp <= 2:
        # Desperate: must win
        if budget > DAILY_SALARY * 0.9:
            bid = DAILY_SALARY * 0.9
        else:
            bid = budget * 0.9
    elif hp <= 4:
        # Need water soon
        if high_prev > DAILY_SALARY * 0.7:
            bid = DAILY_SALARY * 0.7
        else:
            bid = max(DAILY_SALARY * 0.5, high_prev + 1.5)
    else:
        # Healthy, can be conservative
        if high_prev > DAILY_SALARY * 0.85:
            bid = min(DAILY_SALARY * 0.4, high_prev * 0.5)
        else:
            bid = max(DAILY_SALARY * 0.3, high_prev * 0.9)

    # Ensure bid is within budget and non-negative, with int index safety
    bid = min(budget, max(0, bid))
    # Convert to float as required
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    supply = day_context['supply']
    day = day_context['day']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    total_demand = (num_opponents + 1) * WATER_REQ
    supply_ratio = supply / total_demand if total_demand > 0 else 1.0
    
    # Base bid as fraction of salary depending on supply tightness
    if supply_ratio >= 1.0:
        base_bid = DAILY_SALARY * 0.4
    elif supply_ratio >= 0.7:
        base_bid = DAILY_SALARY * 0.6
    else:
        base_bid = DAILY_SALARY * 0.8
    
    # Adjust based on my health
    hp = my_status['hp']
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif hp <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    
    # Use previous trace of opponents to gauge aggressiveness
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If opponents bid high yesterday, expect similar today
        if max_prev > DAILY_SALARY * 0.8:
            # Need to compete
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
        else:
            base_bid = max(base_bid, max_prev + 5)
    
    # Clamp to budget
    max_bid = my_status['budget']
    final_bid = min(base_bid, max_bid)
    # Ensure at least minimum bid if we have budget
    if final_bid < 1.0 and max_bid >= 1.0:
        final_bid = 1.0
    return final_bid
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)

    # Determine how many units of water can be allocated (each unit serves WATER_REQ)
    max_units = int(supply // WATER_REQ)

    # Check yesterday's traces for lowest max bid among alive opponents
    low_prev = None
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if low_prev is None or prev['bid'] < low_prev:
                low_prev = prev['bid']

    # If desperate (low HP or no water), bid high
    desperate = hp <= 2 or no_water_days > 0

    if desperate:
        # Need water urgently: bid close to salary but ensure winning
        if max_units >= num_alive + 1:
            # Enough supply for all, bid low average
            base_bid = DAILY_SALARY * 0.4
        else:
            # Competition: bid enough to outbid lowest yesterday or a safe amount
            if low_prev is not None:
                base_bid = low_prev + 1.0
            else:
                base_bid = DAILY_SALARY * 0.75
        return min(budget, max(base_bid, DAILY_SALARY * 0.3))
    else:
        # Healthy: conserve budget
        # If low_prev is very low, we might still win with low bid
        if low_prev is not None and low_prev < DAILY_SALARY * 0.3:
            safe_bid = max(low_prev + 0.5, DAILY_SALARY * 0.15)
        else:
            safe_bid = DAILY_SALARY * 0.25
        return min(budget, safe_bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Get alive opponents and their previous bids
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    # Determine target bid: beat yesterday's max if any, else baseline
    if prev_bids:
        max_prev = max(prev_bids)
        target = max_prev + 0.5  # beat by a tiny margin
    else:
        target = DAILY_SALARY * 0.5  # default moderate

    # Adjust based on urgency
    urgency = 0.0
    if my_hp <= 3:
        urgency = 0.3
    if no_water_days > 0:
        urgency += 0.2 * no_water_days

    # Final bid: ensure we don't overpay, but bid enough
    if my_hp <= 2 or no_water_days >= 2:
        # Critical need: bid high to secure water
        bid = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 5:
        bid = max(target, DAILY_SALARY * 0.7)
    else:
        bid = max(target, DAILY_SALARY * 0.5)

    # Cap at remaining budget
    bid = min(bid, my_budget)
    # Ensure non-negative and reasonable
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure integer
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid: if no previous info, use safe default
    if not prev_bids:
        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    max_prev = max(prev_bids)
    # Strategy: if HP low, outbid the highest previous by a small margin; else bid slightly above average
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        target = max_prev + 5.0
    else:
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = avg_prev + 1.0
    
    # Ensure target is within budget and reasonable (not more than salary)
    target = min(target, my_status['budget'], DAILY_SALARY * 0.85)
    target = max(target, 0.0)
    return target
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    salary = 140
    req = 8
    scarcity = req / max(supply, 1)
    base_bid = scarcity * salary * 1.5
    if hp <= 2:
        bid = base_bid * 1.5
    elif hp <= 4:
        bid = base_bid * 1.2
    else:
        bid = base_bid
    bid = min(budget, max(bid, 5))
    if budget > salary * 5 and hp > 5:
        bid = min(bid, salary * 0.7)
    return bid
"""
