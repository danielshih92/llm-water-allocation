# ============================================================
# Experiment: exp_014
# Agent: Eric
# Source: exp_014
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid on a fraction of salary, adjusted by HP
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.65
    else:
        base_bid = DAILY_SALARY * 0.45
    
    # Adjust for low budget: never bid more than budget
    if base_bid > budget:
        base_bid = budget
    
    # Slight adjustment based on supply scarcity (high supply -> lower bids)
    scarcity_ratio = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0-1
    # If scarce (supply low), increase bid slightly; if abundant, decrease
    if scarcity_ratio > 0.6:
        base_bid *= 1.15
    elif scarcity_ratio < 0.3:
        base_bid *= 0.9
    
    # Final bid is capped by budget and must be non-negative
    bid = max(0, min(budget, base_bid))
    
    # Ensure bid is an integer (though game may accept float)
    return round(bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    max_prev_bid = max(prev_bids) if prev_bids else DAILY_SALARY * 0.6
    bid = max_prev_bid + 5.0
    # Cap based on HP
    if my_status['hp'] <= 2:
        # desperate: bid up to 0.95*salary
        cap = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        cap = DAILY_SALARY * 0.8
    else:
        cap = DAILY_SALARY * 0.7
    bid = min(bid, cap)
    bid = min(bid, my_status['budget'])
    # Ensure enough for water requirement (bid must be positive)
    bid = max(bid, 1.0)
    return int(bid)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    
    # Extract previous bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine a base target based on yesterday's highest bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If I have low hp, need to ensure water; else be slightly above highest
        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
            target = max(DAILY_SALARY * 0.9, highest_prev + 2)
        elif my_status['hp'] <= 5:
            target = highest_prev + 1.5
        else:
            target = highest_prev * 0.8  # conservative if healthy
    else:
        # Fallback: bid based on hp
        if my_status['hp'] <= 2:
            target = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 5:
            target = DAILY_SALARY * 0.65
        else:
            target = DAILY_SALARY * 0.4
    
    # Ensure bid is within budget and not negative
    bid = min(my_status['budget'], max(0, target))
    return min(my_status['budget'], bid)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Estimate opponent aggressiveness from previous trace
    highest_prev_bid = 0.0
    for o in alive_opponents.values():
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
    
    # If low on HP, must win water at any reasonable cost
    if hp < 4:
        # Bid aggressively but not more than budget
        bid = min(budget, DAILY_SALARY * 0.95)
        if previous_trace_high and highest_prev_bid > DAILY_SALARY * 0.8:
            # Outbid Cindy if needed
            bid = max(bid, highest_prev_bid + 1.0)
        return min(bid, budget)
    
    # Otherwise conserve budget but still secure water if supply is tight
    # Use supply to gauge competition: low supply -> higher bids expected
    norm_supply = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # Base bid decreases as supply increases
    base_bid = DAILY_SALARY * (0.6 - 0.3 * norm_supply)  # range: 42 to 84
    
    # Adjust if previous opponent bids were high (Cindy)
    if highest_prev_bid > DAILY_SALARY * 0.8:
        # Likely aggressive round, increase bid a bit
        base_bid = max(base_bid, DAILY_SALARY * 0.6)
    
    # Ensure we have budget for future, don't overbid
    max_affordable = budget * 0.5  # spend at most half today
    bid = min(base_bid, max_affordable)
    
    # Safety: if no_water_days > 1, we must win today
    if no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.8)
    
    return min(bid, budget)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # should not happen in multi-agent, but just in case
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # estimate how many players can get water: supply // WATER_REQ
    # use int conversion to avoid float index
    water_slots = supply // WATER_REQ
    num_alive = len(alive_opponents) + 1  # including self

    # Calculate a base bid: if slots are tight, bid higher
    if water_slots < num_alive:
        # competitive situation, need to outbid Cindy's 138
        target = 139.0
    else:
        target = 80.0  # moderate bid

    # Adjust based on yesterday's max bid from opponents
    if prev_bids:
        max_prev = max(prev_bids)
        # If someone was very aggressive yesterday (>= 138), we need to match or exceed
        if max_prev >= 138:
            target = max(target, 139.0)
        else:
            # Otherwise, we can bid slightly above yesterday's max
            target = max(target, max_prev + 1.0)

    # HP safety: if hp <= 2, must get water
    if hp <= 2 or no_water_days >= 1:
        target = max(target, 139.0)

    # Budget constraint: cannot exceed budget
    target = min(target, budget)
    # Ensure bid is non-negative
    target = max(target, 0.0)

    return target
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
    yesterday_max_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])

    # Base bid: 60% of salary, scaled by supply scarcity
    base_bid = DAILY_SALARY * 0.6
    if supply < 20:
        base_bid *= 0.8  # less water available, we need to compete
    else:
        base_bid *= 0.5  # more water, can be conservative

    # Adjust based on yesterday's pressure
    if yesterday_max_bid > DAILY_SALARY * 1.0:
        # Opponents were extremely aggressive, conserve budget
        target_bid = min(base_bid * 0.7, budget)
    elif yesterday_max_bid > DAILY_SALARY * 0.6:
        target_bid = min(base_bid * 1.2, budget)
    else:
        target_bid = min(base_bid, budget)

    # Emergency: if hp is very low or no water days > 1, bid higher
    if hp <= 2 or no_water_days >= 2:
        target_bid = min(DAILY_SALARY * 0.9, budget)
    elif hp <= 5:
        target_bid = min(target_bid * 1.3, budget)

    # Ensure we don't bankrupt unnecessarily
    if budget - target_bid < DAILY_SALARY * 0.5:
        target_bid = min(target_bid, budget * 0.3)

    return max(0, min(target_bid, budget))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    WATER_REQ = 8
    DAILY_SALARY = 140

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opp = len(alive_opponents)
    max_winners = supply // WATER_REQ

    # urgency based on health and no_water_days
    urgency =
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure integer
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Determine base bid from supply and hp urgency
    if hp <= 2:
        # Desperate: need water
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base_bid = min(budget, DAILY_SALARY * 0.7)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.4)
    
    # Adjust for supply scarcity
    if supply <= 17:
        base_bid = min(budget, DAILY_SALARY * 0.85)
    elif supply >= 22:
        base_bid *= 0.7
    
    # Look at yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(bid)
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If we are healthy, try to slightly undercut or match
        if hp > 2:
            # Aim to beat yesterday's max by a small margin
            target = min(budget, max_yesterday + 1.5)
            if target < max_yesterday:
                target = max_yesterday  # can't outbid? then match at least
            # But don't exceed our base judgment too much
            bid = max(base_bid, target)
        else:
            # Low hp: must outbid, no limit
            bid = min(budget, max_yesterday + 5.0)
    else:
        bid = base_bid
    
    # Ensure we never bid more than budget
    bid = min(bid, budget)
    # Also ensure non-negative
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
    budget = my_status['budget']
    hp = my_status['hp']
    supply = int(day_context['supply'])
    day = int(day_context['day'])

    # Base bid as fraction of salary
    if supply < 18:
        base = DAILY_SALARY * 0.7
    elif supply > 22:
        base = DAILY_SALARY * 0.3
    else:
        base = DAILY_SALARY * 0.5

    # Adjust for low HP
    if hp <= 2:
        base = DAILY_SALARY * 0.9

    # Later days: increase bid to secure water
    if day >= 8:
        base = max(base, DAILY_SALARY * 0.8)
    elif day <= 3:
        base = min(base, DAILY_SALARY * 0.4)

    # Check yesterday's traces for high pressure from opponents
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace')
            if prev and prev.get('bid') is not None:
                if prev['bid'] > DAILY_SALARY * 0.8:
                    # If someone bid high yesterday, they might again
                    base = max(base, prev['bid'] * 0.9)

    # Cap by budget and ensure non-negative
    bid = min(budget, max(0, base))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    # Get yesterday's max bid from alive opponents' previous_trace
    yesterday_max = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid_val = prev['bid']
                if bid_val > yesterday_max:
                    yesterday_max = bid_val
    # Base bid: cover water requirement proportional to supply
    base_bid = max(DAILY_SALARY * 0.3, (WATER_REQ / supply) * DAILY_SALARY * 0.8)
    # Adjust for desperation
    if hp <= 2 or no_water_days >= 2:
        # Aggressive: match yesterday's max + small increment, but within budget
        target = max(base_bid, yesterday_max + 1)
        bid = min(budget, target)
    elif hp <= 4:
        # Moderate: slightly above base, but don't overpay
        target = max(base_bid, yesterday_max * 0.8)
        bid = min(budget, target)
    else:
        # Conservative: just base
        bid = min(budget, base_bid)
    # Ensure bid is non-negative and at most budget
    bid = max(0, bid)
    # Protection: if budget is high, cap at 0.9 * budget to save for future
    if bid > budget * 0.9:
        bid = budget * 0.9
    # Ensure integer-like but float allowed
    return bid
"""
