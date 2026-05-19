# ============================================================
# Experiment: exp_044
# Agent: Eric
# Source: exp_044
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    budget = my_status['budget']
    hp = my_status['hp']
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        bid = min(budget, DAILY_SALARY * 0.4)
    # Ensure bid is numeric
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive'] and opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None:
            yesterday_bids.append(opp['previous_trace']['bid'])
    
    # Determine base bid factor based on my hp
    if hp <= 2:
        base_factor = 0.95  # desperate
    elif hp <= 5:
        base_factor = 0.85
    else:
        base_factor = 0.70  # healthy
    
    base_bid = SALARY * base_factor
    
    # Supply pressure: lower supply -> higher competition, increase bid
    supply_ratio = supply / 20.0  # mid-range ~20
    # If supply low (15), supply_ratio=0.75, multiply by ~1.1; if high (25), ratio=1.25, multiply by ~0.9
    supply_multiplier = 1.0 + (0.15 * (1 - supply_ratio))
    bid = base_bid * supply_multiplier
    
    # Adjust based on opponent yesterday's max bid to outbid if needed
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If they were very high, they may drop; bid slightly below that max but ensure we win if we need water
        if hp <= 2:
            # Need water: bid just above max_yesterday, but cap at budget
            bid = max(bid, max_yesterday + 1.0)
        elif hp <= 5:
            # Moderate: try to stay competitive but not overpay
            if max_yesterday > SALARY * 0.9:
                # They were aggressive, they may repeat; bid slightly above
                bid = max(bid, max_yesterday + 1.0)
            else:
                bid = max(bid, max_yesterday - 2.0)  # try to undercut
        else:
            # Healthy: save budget, bid below their max
            bid = min(bid, max_yesterday - 3.0)
    
    # Ensure bid is within budget and non-negative
    bid = max(0.0, min(bid, budget))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # base bid: water need fraction times salary, scaled by supply scarcity
    scarcity = WATER_REQ / supply
    base_bid = scarcity * DAILY_SALARY * 0.9  # 90% of proportional salary

    # adjust based on health
    if hp <= 2:
        desire_factor = 1.5
    elif hp <= 4:
        desire_factor = 1.2
    else:
        desire_factor = 1.0

    bid = base_bid * desire_factor

    # ensure minimum bid if we are desperate
    if no_water_days >= 1 or hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.7)

    # clamp to budget and reasonable max (avoid overbidding against high bidders)
    bid = min(budget, bid, DAILY_SALARY * 1.1)

    # ensure non-negative
    bid = max(0, bid)

    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    base_bid = DAILY_SALARY * 0.5
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If someone bid high yesterday, counter just above them
        if max_yesterday > DAILY_SALARY * 0.8:
            base_bid = max_yesterday + 2
        else:
            base_bid = max_yesterday + 1
    
    # Adjust based on HP
    hp = my_status['hp']
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif hp <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    
    # Budget and supply constraints
    budget = my_status['budget']
    supply = day_context['supply']
    max_water_units = int(supply // WATER_REQ)  # max units we might get per day
    # Ensure we don't overbid beyond our budget
    bid = min(base_bid, budget)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    if no_water_days > 0 or hp <= 2:
        bid = min(budget, max(DAILY_SALARY * 0.9, max_prev_bid + 1))
    else:
        if max_prev_bid > DAILY_SALARY * 0.85:
            if hp > 4:
                bid = min(budget, DAILY_SALARY * 0.3)
            else:
                bid = min(budget, max(DAILY_SALARY * 0.6, max_prev_bid - 5))
        else:
            bid = min(budget, max(DAILY_SALARY * 0.4, max_prev_bid + 2))
    max_possible = int(supply // WATER_REQ) * DAILY_SALARY * 0.8
    bid = min(bid, max_possible, budget)
    return max(0, bid)
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents) + 1
    
    # Base bid: proportional to supply scarcity and number of players
    base_share = supply / (num_alive * WATER_REQ)
    if base_share >= 1.0:
        # Plenty of water, low bid
        bid = DAILY_SALARY * 0.4
    else:
        # Scarcity, bid higher
        bid = DAILY_SALARY * (0.5 + (1 - base_share) * 0.3)
    
    # Adjust for low health
    if hp <= 3:
        bid = max(bid, DAILY_SALARY * 0.8)
    if hp <= 1:
        bid = max(bid, DAILY_SALARY * 0.95)
    
    # Ensure within budget
    bid = min(bid, budget)
    bid = max(bid, 0)
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    if prev_bids:
        max_prev = max(prev_bids)
        # if supply is low, bid higher margin
        if supply < 20:
            target = max(max_prev + 1, DAILY_SALARY * 0.85)
        else:
            target = max_prev + 0.5
        # increase if hp low
        if hp <= 2:
            target = max(target, DAILY_SALARY * 0.9)
        return min(budget, target)
    else:
        # no history, cautious
        base = DAILY_SALARY * 0.65
        if hp <= 2:
            base = DAILY_SALARY * 0.9
        return min(budget, base)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
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
        # Aggressive opponents (Alex, Cindy) often bid near 150, so we need to outbid them if necessary
        if my_status['hp'] <= 2:
            # Desperate: bid almost all budget to survive
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        elif my_status['hp'] <= 4:
            # Moderate need: bid slightly above highest previous
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev + 1.5))
        else:
            # Healthy: bid conservatively, maybe below highest to save money
            return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev - 5))
    else:
        # First day or no trace: base on HP
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 4:
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    if prev_bids:
        target = max(prev_bids) + 3.0
    else:
        supply = day_context['supply']
        target = DAILY_SALARY * (WATER_REQ / supply) * 1.2
    # adjust for hp
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    if hp <= 2 or no_water > 0:
        target *= 1.3
    elif hp > 5:
        target *= 0.85
    # supply scaling
    target *= 1.0 + (1.0 - (day_context['supply'] / 25.0)) * 0.2
    # clamp
    target = max(10.0, min(my_status['budget'], target))
    # ensure integer index safety
    return int(target) if target <= my_status['budget'] else my_status['budget']
"""
