# ============================================================
# Experiment: exp_113
# Agent: Eric
# Source: exp_113
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, max(WATER_REQ, DAILY_SALARY * 0.4))

    # Extract previous bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.6
    if hp <= 2 or no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp >= 5:
        base_bid = DAILY_SALARY * 0.4

    # Adjust based on opponent yesterday behavior
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            if hp <= 2:
                base_bid = min(base_bid, DAILY_SALARY * 0.95)
            else:
                base_bid = min(base_bid, DAILY_SALARY * 0.3)
        else:
            # Outbid slightly if affordable
            competitive_bid = max(base_bid, highest_prev + 1.0)
            base_bid = min(competitive_bid, DAILY_SALARY * 0.85)

    # Ensure at least minimum to survive if needed
    if hp <= 1 and no_water_days >= 3:
        base_bid = DAILY_SALARY * 0.95

    bid = min(budget, base_bid)
    bid = max(bid, 0)
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
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    # Estimate competition pressure: lower supply per agent means higher bid needed
    supply_per_agent = supply / (num_alive + 1) if num_alive > 0 else supply
    if supply_per_agent < WATER_REQ:
        bid_factor = 0.85
    else:
        bid_factor = 0.6
    # Adjust for low HP
    if hp <= 2:
        bid_factor = min(0.95, bid_factor + 0.2)
    # Also consider budget
    max_bid = min(budget, DAILY_SALARY * bid_factor)
    # Ensure positive bid
    bid = max(0.1, max_bid)
    # Prevent float indexing: not needed here, but to be safe
    bid = float(bid)
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Estimate opponent bids from previous_trace
    opp_prev_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opp_prev_bids.append(prev['bid'])

    # Base bid: moderate if supply low, else low
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.3:
        base_bid = DAILY_SALARY * 0.6
    elif supply_ratio < 0.7:
        base_bid = DAILY_SALARY * 0.4
    else:
        base_bid = DAILY_SALARY * 0.25

    # Adjust for HP
    if my_hp <= 3 or my_no_water > 0:
        need_urgent = True
    else:
        need_urgent = False

    if need_urgent:
        # Must win water, bid above likely highest opponent bid
        if opp_prev_bids:
            max_prev = max(opp_prev_bids)
            target = max_prev + 2.0
            target = min(target, my_budget + DAILY_SALARY)  # we get salary today? assume budget already includes today? But careful, budget is before salary? Typically salary is added at start. But we assume budget includes salary for this day? Safer: use my_budget as is.
            if target < DAILY_SALARY * 0.8:
                target = DAILY_SALARY * 0.8
        else:
            target = DAILY_SALARY * 0.7
    else:
        # If not urgent, try to save by bidding slightly below expected max but above low bidders
        if opp_prev_bids:
            sorted_bids = sorted(opp_prev_bids)
            # Take second highest? Or median?
            if len(sorted_bids) >= 2:
                target = sorted_bids[-2] + 0.5
            else:
                target = sorted_bids[0] + 0.5
        else:
            target = base_bid

    # Ensure bid is within budget and reasonable
    max_possible_bid = my_budget + DAILY_SALARY  # we can use today's salary
    bid = min(target, max_possible_bid)
    bid = max(bid, 0.0)
    # Cast to float (but ensure it's a number)
    return float(bid)
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # if first day, use conservative estimate
    if day == 1 or not alive_opponents:
        if supply < 20:
            return min(budget, DAILY_SALARY * 0.85)
        else:
            return min(budget, DAILY_SALARY * 0.5)
    
    # collect yesterday's bids from opponents that have trace
    high_bid_yesterday = 0
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev:
            bid = prev['bid']
            if bid is not None and bid > high_bid_yesterday:
                high_bid_yesterday = bid
    
    # adjust based on yesterday's highest bid
    if high_bid_yesterday > 0:
        target_bid = high_bid_yesterday + 1.5  # slightly beat last high
        # don't overpay if we are healthy
        if hp > 5:
            target_bid = min(target_bid, DAILY_SALARY * 0.8)
        # supply constraint: if low supply, bid more aggressively
        if supply <= 18:
            target_bid = max(target_bid, DAILY_SALARY * 0.85)
        else:
            target_bid = min(target_bid, DAILY_SALARY * 0.7)
        return min(budget, target_bid)
    else:
        # no trace info, use supply-based
        if supply <= 18:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Determine pressure from yesterday's opponent bids
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid on yesterday's highest bid from alive opponents
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If low on HP or dehydrated, bid aggressively to ensure water
        if my_hp <= 2 or no_water_days >= 1:
            target_bid = min(my_budget, max(DAILY_SALARY * 0.85, max_prev_bid + 2.0))
        else:
            # Outbid yesterday's highest by a small margin, but not too much
            target_bid = min(my_budget, max(DAILY_SALARY * 0.4, max_prev_bid + 1.5))
    else:
        # No yesterday data from alive opponents, use a moderate bid
        if my_hp <= 2 or no_water_days >= 1:
            target_bid = min(my_budget, DAILY_SALARY * 0.9)
        else:
            target_bid = min(my_budget, DAILY_SALARY * 0.6)
    
    # Ensure bid is at least 0 and integer
    bid = int(max(0, min(my_budget, target_bid)))
    return bid
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])

    # Gather yesterday's bids from alive opponents
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Determine pressure: highest yesterday bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
    else:
        max_prev = 0.0

    # Base bid: moderate portion of salary adjusted by supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # When supply low, bid higher
    base_multiplier = 0.4 + 0.3 * (1 - supply_ratio)  # 0.4 to 0.7
    base_bid = DAILY_SALARY * base_multiplier

    # Adjust based on opponent pressure
    if max_prev > DAILY_SALARY * 0.8:
        # Aggressive opponents: if hp low, fight; otherwise undercut slightly
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            # bid slightly above moderate, not worth fighting top
            bid = min(budget, max(base_bid, max_prev * 0.7))
    else:
        # Moderate opponents: bid enough to secure water
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.85)
        else:
            bid = min(budget, max(base_bid, max_prev + 0.5))

    # Ensure we don't waste budget unnecessarily when supply high
    # Also keep some reserve for future
    max_afford = budget
    if hp > 5:
        bid = min(bid, DAILY_SALARY * 0.55)
    bid = min(max_afford, bid)
    # Ensure non-negative
    bid = max(0, bid)
    return int(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    # Collect yesterday's bids from alive opponents
    yester_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yester_bids.append(trace['bid'])
    max_prev_bid = max(yester_bids) if yester_bids else 0.0
    # Supply factor: higher when supply is low
    supply_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid = DAILY_SALARY * 0.4 + supply_factor * 20
    # Aggressive if low HP
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    # Respond to yesterday's highest opponent bid
    if max_prev_bid > base_bid:
        bid = max_prev_bid + 1.0
    else:
        bid = base_bid
    # Early days: conserve budget
    days_left = 10 - day
    if days_left >= 7:
        bid = min(b
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = int(day_context['supply'])
    day = day_context['day']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Estimate likely max bid among opponents based on yesterday's trace
    prev_max_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_max_bid = max(prev_max_bid, prev['bid'])
    
    # Base bid: need to cover water requirement; if supply low, bid higher
    water_needed = max(WATER_REQ - supply, 0)
    if water_needed > 0:
        base_bid = DAILY_SALARY * 0.4
    else:
        base_bid = DAILY_SALARY * 0.3
    
    # Adjust for own health
    if my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.6
    
    # Consider opponent aggression: if they bid high yesterday, try to undercut slightly
    if prev_max_bid > DAILY_SALARY * 0.7:
        # Avoid bidding war, but ensure survival if critical
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            return min(my_status['budget'], max(base_bid, DAILY_SALARY * 0.45))
    else:
        # If opponents were moderate, bid slightly above average to secure water
        if water_needed > 0 or my_status['hp'] < 5:
            return min(my_status['budget'], base_bid + 5)
        else:
            return min(my_status['budget'], base_bid - 5)
    
    # Fallback conservative bid
    return min(my_status['budget'], DAILY_SALARY * 0.5)
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

    day = int(day_context['day'])
    supply = int(day_context['supply'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o.get('alive', False)}

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Get yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(float(prev['bid']))

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.6  # conservative baseline

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If last day high pressure, reduce bid to save budget unless low hp
        if highest_prev >= DAILY_SALARY * 0.85:
            if my_hp <= 3 or no_water_days > 0:
                base_bid = min(DAILY_SALARY * 0.95, highest_prev * 1.2)
            else:
                base_bid = DAILY_SALARY * 0.3
        else:
            # Modest aggression: slightly beat highest if we need water
            if my_hp <= 2 or no_water_days > 0:
                base_bid = min(DAILY_SALARY * 0.95, highest_prev + 5.0)
            else:
                base_bid = min(DAILY_SALARY * 0.65, highest_prev + 1.0)
    else:
        if my_hp <= 2 or no_water_days > 0:
            base_bid = DAILY_SALARY * 0.9
        else:
            base_bid = DAILY_SALARY * 0.5

    # Ensure bid does not exceed budget and is non-negative
    bid = max(0.0, min(my_budget, base_bid))

    return bid
"""
