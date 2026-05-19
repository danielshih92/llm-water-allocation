# ============================================================
# Experiment: exp_052
# Agent: Eric
# Source: exp_052
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # convert to int
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Calculate need: how many units required to survive
    needed = WATER_REQ
    if no_water_days > 0:
        needed += no_water_days * 2  # slightly higher need if dehydrated
    
    # If HP very low, bid aggressively
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        bid = min(budget, DAILY_SALARY * 0.7)
    else:
        # Healthy: try to conserve budget
        bid = min(budget, DAILY_SALARY * 0.5)
    
    # If many opponents alive, assume competition; increase bid slightly
    if len(alive_opponents) >= 3:
        bid = min(budget, bid * 1.2)
    
    return bid
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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    # Consider previous traces if available (first day likely empty)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Base bid on HP and supply
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.95)
    if supply < 18:
        return min(budget, DAILY_SALARY * 0.9)
    if supply > 22:
        return min(budget, DAILY_SALARY * 0.5)
    # If we have yesterday's bids, adjust
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev >= DAILY_SALARY * 0.8:
            return min(budget, max_prev + 2)
        else:
            return min(budget, DAILY_SALARY * 0.6)
    # Default moderate
    return min(budget, DAILY_SALARY * 0.65)
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
        # No competition, bid low to save money
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    
    # Collect yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        base = max(DAILY_SALARY * 0.5, max_prev + 1.0)
    else:
        base = DAILY_SALARY * 0.5
    
    # Adjust based on health and no_water_days
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    
    if hp <= 2 or no_water >= 2:
        # Desperate: bid high to ensure water
        bid = min(my_status['budget'], max(base, DAILY_SALARY * 0.85))
    elif hp <= 4:
        bid = min(my_status['budget'], base * 1.1)
    else:
        bid = min(my_status['budget'], base)
    
    # Ensure we don't bid more than budget
    bid = max(0, min(bid, my_status['budget']))
    # Round to 2 decimals to match game expectations
    return round(bid, 2)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opp = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opp:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # base proportional bid
    base = (WATER_REQ / supply) * DAILY_SALARY
    
    if not prev_bids:
        if hp <= 2:
            return min(budget, base * 2.0)
        elif hp <= 5:
            return min(budget, base * 1.2)
        else:
            return min(budget, base * 0.8)
    
    max_prev = max(prev_bids)
    avg_prev = sum(prev_bids) / len(prev_bids)
    
    if hp <= 2:
        target = max_prev + 1.0
    elif hp <= 5:
        target = max(max_prev, avg_prev) + 0.5
    else:
        target = max(avg_prev, base) - 1.0
    
    target = max(target, 0.0)
    return min(budget, target)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Extract supply and day
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Collect yesterday's bids from alive opponents
    last_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                last_bids.append(prev['bid'])
    
    # Determine max last bid (if any)
    max_last_bid = max(last_bids) if last_bids else 0.0
    
    # Base bid as fraction of salary
    bid = DAILY_SALARY * 0.45
    
    # Adjust based on health
    if hp <= 2:
        # Need water urgently: outbid yesterday's max by small margin, but not exceed budget
        bid = min(budget, max(DAILY_SALARY * 0.7, max_last_bid + 1.5))
    elif hp <= 5:
        # Moderate need: slightly above average to compete
        if last_bids:
            avg_last = sum(last_bids) / len(last_bids)
            bid = min(budget, max(DAILY_SALARY * 0.5, avg_last + 2.0))
        else:
            bid = min(budget, DAILY_SALARY * 0.55)
    else:
        # High hp: be conservative, save money
        bid = min(budget, DAILY_SALARY * 0.3)
        # If supply is low, may need to bid slightly higher to ensure water later
        if supply < 18 and day < 8:
            bid = min(budget, DAILY_SALARY * 0.4)
    
    # Ensure bid is at least 1 if budget allows, but never exceed budget
    bid = min(budget, max(1.0, bid))
    return bid
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
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Collect previous bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine urgency based on no_water_days and HP
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    
    # Base bid decision
    if no_water >= 1 or hp <= 2:
        # Must get water, bid high
        if prev_bids:
            target = max(prev_bids) + 2.0
        else:
            target = DAILY_SALARY * 0.9
        return min(budget, target)
    else:
        # Conserve budget
        if prev_bids:
            avg_prev = sum(prev_bids) / len(prev_bids)
            target = min(avg_prev * 0.8, DAILY_SALARY * 0.6)
        else:
            target = DAILY_SALARY * 0.5
        return min(budget, max(target, 0.1))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 1.0)
        return min(budget, DAILY_SALARY * 0.2)
    
    # Look at yesterday's highest bid among alive opponents
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > highest_prev_bid:
                highest_prev_bid = prev['bid']
    
    # Estimate competitors' max budget and aggression
    # Basic threshold: if yesterday's max bid was very low, they might be conserving
    # If high, they are aggressive
    
    if hp <= 2:
        # Critical: must win water
        target = max(DAILY_SALARY * 1.5, highest_prev_bid * 1.1)
        return min(budget, target)
    
    if no_water_days >= 1:
        # Moderate desperation
        target = max(DAILY_SALARY * 1.2, highest_prev_bid * 0.9)
        return min(budget, target)
    
    # Healthy: conserve budget
    if highest_prev_bid > DAILY_SALARY * 0.8:
        # Opponents are aggressive, avoid price war if possible
        return min(budget, DAILY_SALARY * 0.4)
    else:
        # Opponents moderate, bid just enough to beat their history if needed
        base = max(DAILY_SALARY * 0.3, highest_prev_bid * 1.05)
        return min(budget, base)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    n_opponents = len(alive_opponents)

    # Extract yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])

    # Base bid: proportional to supply shortage (min supply = 15, max = 25)
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # When supply high, competition lower -> lower bid
    base_bid = DAILY_SALARY * (0.4 + 0.3 * (1 - supply_ratio))

    # Adjust based on yesterday's highest bid (aggressiveness)
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone was very aggressive, avoid overbidding if not desperate
        if highest_prev > DAILY_SALARY * 0.85:
            # If we are healthy, lower bid to avoid price war
            if hp > 3:
                bid = min(budget, base_bid * 0.7)
            else:
                bid = min(budget, max(base_bid, highest_prev * 0.9))
        else:
            # Otherwise, slightly beat the highest previous bid if reasonable
            target = max(base_bid, highest_prev + 2.0)
            bid = min(budget, target)
    else:
        # No history, use conservative
        bid = min(budget, base_bid)

    # Urgency: if no water for 1+ days or hp low, increase bid
    if hp <= 2 or no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.75)
        bid = min(budget, bid)

    # Ensure bid is valid
    bid = max(0.0, bid)
    return min(budget, bid)
"""
