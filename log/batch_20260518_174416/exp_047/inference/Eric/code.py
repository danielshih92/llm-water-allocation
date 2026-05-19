# ============================================================
# Experiment: exp_047
# Agent: Eric
# Source: exp_047
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    import math
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    supply_tight = supply < 18
    if hp <= 2 or no_water_days >= 2:
        base = min(budget, DAILY_SALARY * 0.9)
        return min(base, max(DAILY_SALARY * 0.4, max_prev_bid + 2))
    else:
        if supply_tight:
            desired = max(DAILY_SALARY * 0.3, max_prev_bid * 1.15)
        else:
            desired = max(DAILY_SALARY * 0.2, max_prev_bid * 1.05 + 1)
        return min(budget, min(DAILY_SALARY * 0.75, desired))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    daily_salary = 140
    budget = my_status['budget']
    hp = my_status['hp']
    supply = day_context['supply']
    # Number of alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # If we are alone, bid minimal to conserve budget
        return min(budget, daily_salary * 0.4)
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    # Determine a baseline bid based on yesterday's maximum bid
    if prev_bids:
        max_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
        # If we are low on HP, we need to secure water even at higher cost
        if hp <= 2:
            target = min(budget, max(daily_salary * 0.9, max_prev_bid + 1))
        else:
            # Otherwise, try to bid just above the average but not too high
            target = min(budget, max(daily_salary * 0.6, avg_prev_bid + 0.5))
    else:
        # No previous data: be cautious
        if hp <= 2:
            target = min(budget, daily_salary * 0.85)
        else:
            target = min(budget, daily_salary * 0.55)
    # Ensure we don't bid more than we can afford, and not negative
    bid = max(0, target)
    # Cap at budget
    bid = min(bid, budget)
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
    
    # Opponents alive
    alive_opp = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Analyze yesterday's max bid among alive opponents
    max_yesterday_bid = 0
    for o in alive_opp.values():
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > max_yesterday_bid:
                max_yesterday_bid = bid
    
    # Base price: water cost per unit? Estimate willingness to pay.
    # If supply high, expect lower bids; else higher.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    base_bid = DAILY_SALARY * (0.5 + 0.3 * (1 - supply_ratio))  # range 0.5 to 0.8
    
    # Urgency: if no water days >0, increase bid
    urgency_mult = 1.0
    if my_status['no_water_days'] > 0:
        urgency_mult = 1.2
    
    # Danger: if HP low, need water more
    hp_urgency = 1.0
    if hp <= 2:
        hp_urgency = 1.3
    elif hp <= 4:
        hp_urgency = 1.1
    
    # Reaction to yesterday's high bid
    if max_yesterday_bid > DAILY_SALARY * 0.7:
        # Aggressive opponents yesterday -> possibly need to compete
        if hp <= 3:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
    else:
        # Normal: compute adaptive bid
        bid = min(budget, base_bid * urgency_mult * hp_urgency)
    
    # Ensure we can get at least one unit if possible
    # Number of water units: supply / WATER_REQ
    n_units = int(supply // WATER_REQ)
    if n_units == 0:
        # Very low supply, bid high if affordable
        bid = min(budget, DAILY_SALARY * 0.95)
    
    # Round to reasonable precision
    bid = round(bid, 2)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    SUPPLY = int(day_context['supply'])
    DAY = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    # Get alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from traces (if any)
    yesterday_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(float(trace['bid']))
    
    # Determine a measure of opponent aggression from yesterday
    high_agg = False
    if yesterday_bids:
        max_bid = max(yesterday_bids)
        # If someone bid >= 90% of salary, treat as aggressive
        if max_bid >= DAILY_SALARY * 0.9:
            high_agg = True
    
    # Base bid calculation
    if hp <= 2:
        # Desperate: need water
        bid = min(budget, DAILY_SALARY * 0.85)
    elif hp <= 5:
        # Moderate health, some urgency
        if high_agg:
            bid = min(budget, DAILY_SALARY * 0.7)
        else:
            bid = min(budget, DAILY_SALARY * 0.55)
    else:
        # Healthy enough, save money
        if high_agg:
            bid = min(budget, DAILY_SALARY * 0.4)
        else:
            bid = min(budget, DAILY_SALARY * 0.3)
    
    # Ensure bid is non-negative and within budget
    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget
    
    # Rounded to nearest 0.5 to avoid floating issues
    bid = round(bid * 2) / 2.0
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']

    # Count alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)

    # Determine required water units
    needed_units = (WATER_REQ + supply - 1) // supply if supply > 0 else 1
    max_possible_bid = budget

    # Base bid: try to be conservative
    base_bid = DAILY_SALARY * 0.3  # ~42

    # Adjust based on survival pressure
    if hp <= 2:
        # Desperate, bid higher to ensure water
        base_bid = DAILY_SALARY * 0.65  # ~91
    elif no_water_days > 0:
        # Already missing water, raise bid
        base_bid = DAILY_SALARY * 0.5  # ~70

    # Use opponent traces if available (day 1 may have none)
    historical_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            historical_bids.append(prev['bid'])
    if len(historical_bids) >= 2:
        # If opponents historically bid high, stay lower to conserve
        if max(historical_bids) > DAILY_SALARY * 0.8:
            base_bid = min(base_bid, DAILY_SALARY * 0.35)

    # Final bid: ensure at least minimum to win water if supply is low
    # Minimum required to secure one unit (assume one unit auction per day?)
    # Actually, supply is total units, all winners split? Not clear, but we'll assume per-unit auction.
    # To be safe, we'll bid enough to beat most if needed.
    minimum_bid = 1.0
    if supply < 12:
        minimum_bid = DAILY_SALARY * 0.25  # ~35

    bid = max(minimum_bid, base_bid)
    bid = min(bid, max_possible_bid)
    bid = max(bid, 0)  # non-negative

    return int(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # collect yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # base bid calculation
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # if supply is low or hp critical, need to outbid
        if supply < 18 or hp <= 2:
            target = max(highest_prev + 1, DAILY_SALARY * 0.9)
        else:
            # try to just above the highest but not too high
            target = max(highest_prev + 0.5, DAILY_SALARY * 0.5)
    else:
        # no previous info, base on supply
        if supply < 18 or hp <= 2:
            target = DAILY_SALARY * 0.8
        else:
            target = DAILY_SALARY * 0.55
    
    # ensure within budget and non-negative
    bid = min(budget, max(0, target))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # First day: conservative
    if day == 1:
        # If supply is low, need to secure water
        if supply < 20:
            # Bid enough to likely win, but not overpay
            bid = min(budget, DAILY_SALARY * 0.6)
        else:
            # Save money, bid low
            bid = min(budget, DAILY_SALARY * 0.3)
        return int(bid)

    # Subsequent days: use opponents' previous traces
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    # Collect yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid according to water need
    if no_water
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
    return 15.0
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive:
        return min(budget, DAILY_SALARY * 0.4)
    # Estimate opponent bids from yesterday
    bids = []
    for opp in alive.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bids.append(prev['bid'])
    # Set thresholds
    if hp <= 3:
        # urgent: outbid highest known (Cindy 147, but may be less)
        highest = max(bids) if bids else 147
        target = highest + 2
        return min(budget, max(target, DAILY_SALARY * 0.9))
    elif hp <= 5:
        # moderate: outbid Bob (around 60) but stay below Alex
        if bids:
            # assume Bob is the lowest among alive? use min bid plus safety
            low_bid = min(bids)
            target = low_bid + 1
        else:
            target = DAILY_SALARY * 0.5
        return min(budget, max(target, DAILY_SALARY * 0.5))
    else:
        # high HP: low bid
        return min(budget, DAILY_SALARY * 0.3)
"""
