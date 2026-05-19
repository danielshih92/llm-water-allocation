# ============================================================
# Experiment: exp_039
# Agent: Eric
# Source: exp_039
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine yesterday's high bid from opponents
    high_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > high_prev_bid:
                high_prev_bid = prev['bid']
    
    # Urgency based on health and no_water_days
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    
    if no_water > 0 or hp <= 2:
        # Desperate: bid high to secure water
        target_bid = max(DAILY_SALARY * 0.9, high_prev_bid + 5)
    elif hp <= 4:
        # Moderate need: bid competitively
        target_bid = max(DAILY_SALARY * 0.6, high_prev_bid + 2)
    else:
        # Healthy: bid low and save
        target_bid = min(DAILY_SALARY * 0.4, high_prev_bid * 0.8)
    
    # Ensure we don't exceed budget and return int
    bid = min(my_status['budget'], target_bid)
    bid = max(0, bid)  # non-negative
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine opponent pressure
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
        # If any opponent had HP <=2, they might be desperate
        desperate = any(opp['hp'] <= 2 for opp in alive_opponents)
        if desperate:
            # They will likely bid very high; match or exceed if I need water
            if hp <= 2:
                return min(budget, DAILY_SALARY * 0.95)
            else:
                # Bid just below their potential despair bid to save budget
                return min(budget, max(DAILY_SALARY * 0.5, highest_yesterday + 1))
        else:
            # Normal pressure
            if hp <= 2:
                return min(budget, DAILY_SALARY * 0.95)
            elif hp <= 5:
                # Moderate need: bid enough to win against typical high bid
                return min(budget, max(DAILY_SALARY * 0.6, highest_yesterday + 0.5))
            else:
                # High HP: conserve budget
                return min(budget, max(DAILY_SALARY * 0.3, highest_yesterday - 5))
    else:
        # No traces available (maybe first day?)
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        elif hp <= 5:
            return min(budget, DAILY_SALARY * 0.6)
        else:
            return min(budget, DAILY_SALARY * 0.4)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, SALARY * 0.4)

    # Check yesterday's trace for Cindy (or highest bidder)
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev = max(prev_bids) if prev_bids else 0

    # Emergency if no water for 2+ days or hp critical
    if no_water_days >= 2 or hp <= 2:
        return min(budget, SALARY * 0.95)

    # If supply low and we have many days left, be aggressive
    days_left = 10 - day
    supply_per_capita = supply / (len(alive_opponents) + 1)
    if supply_per_capita < WATER_REQ:
        # scarcity: need to bid high
        target = max(SALARY * 0.85, max_prev + 2)
        return min(budget, target)

    # Normal: try to outbid previous max slightly if we can afford, else conservative
    if budget > max_prev + 5:
        return min(budget, max_prev + 3)
    else:
        return min(budget, SALARY * 0.6)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    daily_salary = 140
    max_supply = 25
    min_supply = 15
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Determine base bid based on urgency
    if hp <= 2:
        # Desperate: need water
        bid = max(max_prev_bid + 2.0, daily_salary * 0.9)
    elif hp <= 5:
        # Moderate risk, match or slightly undercut
        bid = max(max_prev_bid - 1.0, daily_salary * 0.6)
    else:
        # Healthy, can conserve
        bid = min(max_prev_bid - 3.0, daily_salary * 0.5)
        if bid < daily_salary * 0.3:
            bid = daily_salary * 0.3
    
    # Ensure we don't exceed budget or salary
    bid = min(bid, budget, daily_salary * 0.95)
    bid = max(bid, 1.0)  # Always positive minimum
    
    # Check supply: if low, bid more aggressively
    supply = day_context['supply']
    if supply < (min_supply + max_supply) / 2:
        bid = max(bid, daily_salary * 0.7)
    
    return min(bid, budget)
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
    
    # Base bid: 60% of salary, adjusted by supply scarcity
    supply = day_context['supply']
    scarcity_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid = DAILY_SALARY * (0.6 + 0.3 * scarcity_factor)
    
    # Adjust based on yesterday's highest bid (if available)
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
    
    # If a competitor had a very high bid yesterday, they may be aggressive again
    if highest_prev_bid > DAILY_SALARY * 0.85:
        # Increase bid to compete, but not exceed budget
        target_bid = min(max(base_bid, highest_prev_bid * 0.8), my_status['budget'])
    else:
        target_bid = min(base_bid, my_status['budget'])
    
    # Desperation: if no water for several days or low HP
    if my_status['no_water_days'] >= 3 or my_status['hp'] <= 2:
        target_bid = min(DAILY_SALARY * 0.95, my_status['budget'])
    
    # Ensure we never bid more than we have
    return max(0.0, min(target_bid, my_status['budget']))
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
    return 15.0
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    req = 8
    salary = 140

    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        if no_water > 0 or hp <= 2:
            return min(budget, salary * 0.4)
        return min(budget, salary * 0.1)

    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids)/len(prev_bids) if prev_bids else 0

    if no_water >= 2 or hp <= 2:
        target = max(salary * 0.9, max_prev + 1)
        return min(budget, target, 130)
    elif hp <= 4:
        target = max(salary * 0.5, avg_prev * 0.85)
        return min(budget, target)
    else:
        # Healthy:
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
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Extract yesterday's bids from opponents that have a previous_trace
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
    
    # Determine a target bid based on opponents' past behavior
    if prev_bids:
        # Bob's max was around 61, Alex/Cindy around 156
        # Find the second highest bid to guess moderate competition
        sorted_bids = sorted(prev_bids, reverse=True)
        if len(sorted_bids) >= 2:
            moderate_bid = sorted_bids[1]  # second highest
        else:
            moderate_bid = sorted_bids[0]
        # If we are healthy, try to bid just above Bob's level
        if hp > 5 and budget > 0:
            base_bid = min(70, moderate_bid + 5)
        else:
            base_bid = max(80, moderate_bid + 10)
    else:
        # No trace: start conservatively
        base_bid = 60 if hp > 5 else 90
    
    # Adjust based on supply and water requirement
    if supply < WATER_REQ:
        # Very low supply, need high bid to secure water
        bid = min(budget, max(100, base_bid + 30))
    else:
        # Enough supply, can be more relaxed
        bid = min(budget, max(base_bid, 50))
    
    # Ensure at least enough to buy water if possible
    if hp <= 3:
        bid = min(budget, max(bid, 120))
    
    # Prevent bidding more than budget
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Convert supply to int to avoid float index issues
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Determine maximum possible water units available
    max_units = supply // WATER_REQ
    # Number of alive opponents
    alive = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive)

    # Look at yesterday's highest bid among alive opponents
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    highest_prev = max(prev_bids) if prev_bids else 0

    # Base bid calculation
    base = min(budget, DAILY_SALARY)

    # Emergency: if low HP or no water for 2+ days, must get water at any cost
    if hp <= 2 or no_water_days >= 2:
        # Bid enough to outbid highest prev, but capped by budget
        bid = min(budget, max(highest_prev + 1, base * 0.9))
        return int(bid)

    # If healthy, bid conservatively to save money
    # If there are many competitors, we may need to bid slightly above average
    # If highest prev is very high (e.g., past 120), assume Cindy bids high again
    if highest_prev > 120:
        # Cindy is aggressive; if we don't need water desperately, bid low and skip
        if hp > 5:
            return int(min(budget, DAILY_SALARY * 0.2))
        else:
            # Need water but not urgent
            bid = min(budget, max(highest_prev * 0.6, DAILY_SALARY * 0.4))
            return int(bid)

    # Normal situation: bid a fraction of salary ensuring we can get water if needed
    # Typical winning bid in medium scenario is around 40-60 when supply is moderate
    if supply <= 18:
        # Limited supply, need higher bid
        target = max(DAILY_SALARY * 0.6, highest_prev * 1.1)
    else:
        target = max(DAILY_SALARY * 0.4, highest_prev * 0.9)

    bid = min(budget, target)
    return int(bid)
"""
