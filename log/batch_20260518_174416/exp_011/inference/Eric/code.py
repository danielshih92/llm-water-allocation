# ============================================================
# Experiment: exp_011
# Agent: Eric
# Source: exp_011
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    bid = 0
    if my_status['hp'] <= 2:
        bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    else:
        bid = min(my_status['budget'], DAILY_SALARY * 0.45)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # get yesterday's max bid from previous traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
    else:
        max_yesterday = 0
    
    # base bid as a fraction of salary
    if my_hp <= 3 or no_water_days > 0:
        # desperate: bid high
        bid = min(my_budget, max(DAILY_SALARY * 0.9, max_yesterday + 2.0))
    else:
        # comfortable: bid moderately
        bid = min(my_budget, max(DAILY_SALARY * 0.5, max_yesterday + 0.5))
    
    # adjust for supply scarcity
    supply_ratio = supply / ( (15+25)/2.0 )  # normalize around average supply 20
    if supply < 18:
        bid = min(bid, my_budget * 0.8)  # conserve budget if scarce
    elif supply > 22:
        # more water available, can lower bid
        if my_hp > 5:
            bid = min(bid, DAILY_SALARY * 0.5)
    
    # ensure we don't exceed budget
    bid = min(bid, my_budget)
    # round to avoid fractional cents?
    return round(bid, 2)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Determine if we need water critically
    need_water = (hp <= 3) or (no_water_days >= 1)
    
    if need_water:
        # Bid high enough to secure water
        base_bid = min(budget, DAILY_SALARY * 0.95)
        # If opponents bid high yesterday, we might need to match or exceed
        if highest_prev_bid > 0 and highest_prev_bid > base_bid * 0.9:
            bid = min(budget, highest_prev_bid + 2.0)
        else:
            bid = base_bid
    else:
        # Only bid a low amount; if we win, fine; if not, still okay
        base_bid = min(budget, DAILY_SALARY * 0.35)
        # If opponents are low, maybe we can win cheaply
        if highest_prev_bid < DAILY_SALARY * 0.4:
            bid = max(base_bid, highest_prev_bid + 1.0)
        else:
            bid = base_bid
    
    # Ensure we don't exceed budget and at least 0
    bid = max(0.0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a competitive bid based on yesterday's max
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
    else:
        max_yesterday = DAILY_SALARY * 0.6  # conservative estimate

    # Base bid: slightly above yesterday's max to win, but capped
    base_bid = min(budget, max_yesterday + 1.0)

    # Adjust based on health
    if hp <= 2:
        # Desperate: bid up to full salary if possible
        bid = min(budget, DAILY_SALARY * 1.0)
    elif hp <= 4:
        # Moderate risk: bid slightly above competition
        bid = max(base_bid, DAILY_SALARY * 0.7)
    else:
        # Healthy: conserve budget, bid lower if possible
        bid = min(base_bid, DAILY_SALARY * 0.6)

    # Supply scarcity: if supply low relative to players, increase bid
    num_alive = len(alive_opponents)
    total_needed = (num_alive + 1) * WATER_REQ  # including self
    if supply < total_needed:
        bid = max(bid, DAILY_SALARY * 0.8)

    # Late game: preserve budget if survival assured, else go all out
    remaining_days = 10 - day
    if remaining_days <= 3 and hp > 3:
        bid = min(bid, DAILY_SALARY * 0.5)

    # Ensure bid is non-negative and within budget
    bid = max(0.0, min(budget, bid))

    # Prevent float index issues (none needed here but for safety)
    # No list indices used

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Determine pressure level
    pressure = 0.5  # default moderate
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone bid very high yesterday, they might again
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            pressure = 0.8
    # Adjust for low supply
    if supply < WATER_REQ * 2:
        pressure += 0.1
    # Adjust for own desperation
    if hp <= 2 or no_water_days >= 2:
        pressure = 1.0  # must win
    # Calculate base bid
    base_bid = DAILY_SALARY * pressure
    # If yesterday's highest was high, consider outbidding
    if yesterday_bids and pressure < 1.0:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid > base_bid:
            # outbid by small margin but not exceed budget or 95% of salary
            target = min(highest_prev_bid + 1.5, DAILY_SALARY * 0.95)
            if target > base_bid:
                base_bid = target
    # Cap at budget
    final_bid = min(budget, base_bid)
    # Ensure minimum bid 0
    return max(0.0, final_bid)
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
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from opponents' previous traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid on yesterday's highest bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
    else:
        highest_prev = 0

    # Adjust based on my health
    if my_status['hp'] <= 2:
        # Desperate: bid high to secure water
        bid = max(DAILY_SALARY * 0.9, highest_prev + 2)
    elif my_status['hp'] <= 5:
        # Moderate health: competitive
        bid = max(DAILY_SALARY * 0.6, highest_prev + 1)
    else:
        # Healthy: conserve budget, bid just enough
        bid = max(DAILY_SALARY * 0.4, highest_prev + 0.5)

    # Ensure bid does not exceed budget and is non-negative
    bid = max(0, min(my_status['budget'], bid))
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    
    # Determine a safe target: enough to be competitive
    # Look at opponents' previous bids (if available)
    prev_bids = []
    for opp in opponents_status.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid', 0) > 0:
            prev_bids.append(trace['bid'])
    
    if prev_bids:
        # Estimate typical aggressive bid
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = avg_prev
    else:
        target = DAILY_SALARY * 0.6
    
    # Adjust based on my HP
    if hp <= 2:
        # Desperate, bid high
        my_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # Moderate need
        my_bid = min(budget, max(DAILY_SALARY * 0.7, target + 1))
    else:
        # Comfortable, can be thrifty
        my_bid = min(budget, max(DAILY_SALARY * 0.5, target - 2))
    
    # Supply effect: more supply, can bid less
    # Normalize: low supply -> bid higher
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # adjust by +/- 10%
    my_bid *= (0.9 + 0.2 * (1 - supply_factor))  # lower supply -> higher bid
    my_bid = min(budget, max(0, my_bid))
    
    return int(my_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(budget, SALARY * 0.3)

    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])

    if no_water > 0:
        base = SALARY * 0.8
    elif hp < 3:
        base = SALARY * 0.6
    else:
        base = SALARY * 0.4

    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > 100:
            if no_water > 0 or hp <= 2:
                target = max_prev + 1.0
            else:
                target = max(SALARY*0.5, max_prev + 0.5)
        else:
            if no_water > 0:
                target = max(base, max_prev + 1.5)
            else:
                target = max(base, max_prev + 0.5)
    else:
        target = base

    if supply < 18:
        target *= 1.3
    elif supply > 22:
        target *= 0.9

    return min(float(budget), target)
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
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Gather previous bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace and trace['bid'] is not None:
                prev_bids.append(float(trace['bid']))

    # Base bid: moderate default
    base_bid = DAILY_SALARY * 0.5  # 70

    # If we have previous opponent bids, adjust upward to beat if needed
    if prev_bids:
        max_prev = max(prev_bids)
        # Consider opponent average from meta-round context (hardcoded approximation)
        # We assume they will continue similar pattern
        base_bid = max(base_bid, min(max_prev + 2.0, DAILY_SALARY * 0.95))

    # Emergency: low HP or no water days
    if hp <= 2 or no_water_days >= 1:
        # Bid high to ensure water
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # If supply is abundant, we can lower bid
    if supply >= 20:
        base_bid = min(base_bid, DAILY_SALARY * 0.6)

    # Cannot exceed budget
    final_bid = min(budget, base_bid)
    return float(final_bid)
"""
