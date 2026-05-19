# ============================================================
# Experiment: exp_076
# Agent: Eric
# Source: exp_076
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
    hp = my_status['hp']
    budget = my_status['budget']
    # No previous traces, use default heuristic
    if hp <= 3:
        # desperate: bid high to guarantee water
        bid = DAILY_SALARY * 0.85
    elif hp <= 6:
        bid = DAILY_SALARY * 0.6
    else:
        bid = DAILY_SALARY * 0.45
    return min(budget, bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    max_water_units = supply // WATER_REQ
    prev_bids = []
    for oid, opp in opponents_status.items():
        if opp.get('alive') and opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None:
            prev_bids.append(opp['previous_trace']['bid'])
    if prev_bids:
        sorted_bids = sorted(prev_bids, reverse=True)
        num_units = min(max_water_units, len(sorted_bids))
        if num_units > 0:
            target = sum(sorted_bids[:int(num_units)]) / num_units
        else:
            target = DAILY_SALARY * 0.5
        if my_status['hp'] < 3:
            target = target * 1.2 + 1
        elif my_status['hp'] > 6:
            target = target * 0.8
        else:
            target = target * 1.0
        bid = min(my_status['budget'], target)
        bid = max(1, bid)
    else:
        if my_status['hp'] < 3:
            bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.5)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            previous_bids.append(prev['bid'])

    max_prev_bid = max(previous_bids) if previous_bids else 0.0

    # Emergency: need water badly
    if hp <= 2 or no_water_days >= 1:
        # Bid up to 90% of budget, but at least a reasonable amount
        bid = min(budget, max(DAILY_SALARY * 0.5, max_prev_bid + 2.0))
        bid = min(bid, budget * 0.9)
        return bid

    # Normal situation: try to conserve budget
    # If supply is high, competition might be lower, so bid lower
    if supply >= (MIN_SUPPLY + MAX_SUPPLY) / 2:
        target = max_prev_bid * 0.9
    else:
        target = max_prev_bid + 1.0

    # Ensure we don't overpay; cap at 40% of budget as a safety
    bid = min(budget, target)
    # Floor bid to ensure we have a chance if water is cheap
    bid = max(bid, DAILY_SALARY * 0.3)
    # Make sure we don't go above budget
    bid = min(bid, budget)
    return int(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    # Estimate maximum affordable bid: salary + remaining budget / remaining days (rough)
    days_left = 10 - int(day_context['day'])
    if days_left <= 0:
        return min(my_budget, DAILY_SALARY * 0.5)
    max_affordable = my_budget + DAILY_SALARY * days_left
    
    # Identify key opponents: Alex and Cindy
    alex = opponents_status.get('Alex', {})
    cindy = opponents_status.get('Cindy', {})
    alex_alive = alex.get('alive', False)
    cindy_alive = cindy.get('alive', False)
    
    # Get previous bids if available
    alex_prev = None
    cindy_prev = None
    if alex_alive:
        prev_trace = alex.get('previous_trace', {})
        if prev_trace:
            alex_prev = prev_trace.get('bid')
    if cindy_alive:
        prev_trace = cindy.get('previous_trace', {})
        if prev_trace:
            cindy_prev = prev_trace.get('bid')
    
    # Base bid: moderate
    base_bid = min(my_budget, DAILY_SALARY * 0.8)  # 112
    
    # Adjust based on Cindy's previous bid: if she bid very high, we back off
    if cindy_prev is not None and cindy_prev > DAILY_SALARY * 1.05:  # > 147
        # Let her overpay, save budget
        base_bid = min(my_budget, DAILY_SALARY * 0.3)  # 42
    elif alex_prev is not None and alex_prev > DAILY_SALARY * 0.75:  # > 105
        # Slightly outbid Alex
        base_bid = min(my_budget, alex_prev + 5.0)
    
    # Emergency: if we are severely dehydrated, bid more
    if my_hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)  # 126
    
    # Ensure we don't exceed budget
    base_bid = min(base_bid, my_budget)
    # Floor at 0
    if base_bid < 0:
        base_bid = 0.0
    return base_bid
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine target bid based on yesterday's maximum
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # Base bid is slightly above yesterday's max, but scaled by supply vs requirement
        if supply < WATER_REQ:
            # critical: need water desperately
            bid = min(budget, max_yesterday_bid + 1.5)
        else:
            # enough supply: bid moderately above if we need water, else conserve
            if hp < 3:
                bid = min(budget, max_yesterday_bid + 1.5)
            elif hp <= 5:
                bid = min(budget, max_yesterday_bid * 0.9)
            else:
                bid = min(budget, max_yesterday_bid * 0.5)
    else:
        # No historical data: use need-based
        if hp < 3 or no_water_days > 0:
            bid = min(budget, DAILY_SALARY * 0.85)
        else:
            bid = min(budget, DAILY_SALARY * 0.6)
    
    # Ensure bid is affordable and non-negative
    bid = max(0, min(bid, budget))
    # If we have no budget, can't bid
    if budget <= 0:
        return 0
    return int(bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine urgency based on HP
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Base bid: low, medium, high based on need
    if hp <= 2 or no_water > 0:
        base_bid = 0.9 * DAILY_SALARY  # 126
    elif hp <= 5:
        base_bid = 0.6 * DAILY_SALARY  # 84
    else:
        base_bid = 0.4 * DAILY_SALARY  # 56

    # Adjust based on competitors' previous high bid
    if max_prev_bid >= 0.85 * DAILY_SALARY:  # 119
        # Competitors bidding high
        if hp <= 2:
            # Desperate: try to outbid by small margin
            bid = min(budget, max_prev_bid + 1.0)
        else:
            # Health okay: stay low to save budget
            bid = min(budget, base_bid * 0.5)
    else:
        # Moderate competition: bid slightly above average if needed
        if max_prev_bid > 0 and base_bid < max_prev_bid + 0.5:
            bid = min(budget, max_prev_bid + 0.5)
        else:
            bid = min(budget, base_bid)

    # Ensure bid is non-negative and within budget
    bid = max(0.0, min(bid, budget))
    return bid
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
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {oid: info for oid, info in opponents_status.items() if info['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for oid, info in alive_opponents.items():
        prev = info.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid on supply pressure
    supply_ratio = (supply - 15) / 10.0  # 0 to 1
    base_bid = DAILY_SALARY * (0.4 + 0.3 * (1 - supply_ratio))  # 0.4-0.7 of salary
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If opponents were very aggressive yesterday, they likely still are
        if highest_prev > 100:
            if hp <= 2:
                # Desperate: bid just above highest_prev
                target = min(budget, highest_prev + 2)
                return max(target, DAILY_SALARY * 0.5)
            elif hp <= 5:
                # Moderate risk: match highest_prev
                target = min(budget, highest_prev)
                return max(target, base_bid)
            else:
                # Healthy: save money, bid conservatively
                return min(budget, base_bid * 0.8)
        else:
            # Moderate competition: slightly undercut if healthy, otherwise outbid
            if hp <= 3:
                target = highest_prev + 1.5
            else:
                target = max(base_bid, highest_prev * 0.9)
            return min(budget, target)
    else:
        # No yesterday info: rely on supply heuristic
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        return min(budget, base_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        target = min(budget, DAILY_SALARY * 1.0)  # urgent
    elif hp <= 5:
        target = min(budget, DAILY_SALARY * 0.75)
    else:
        target = min(budget, DAILY_SALARY * 0.55)
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        bid = min(budget, max(target, max_prev + 1.0))
    else:
        bid = target
    # ensure numeric (float) is okay, no list indexing needed
    return bid
"""
