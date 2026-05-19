# ============================================================
# Experiment: exp_106
# Agent: Eric
# Source: exp_106
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    alive_count = sum(1 for o in opponents_status.values() if o['alive'])

    # Base bid as fraction of salary depending on health
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.85
    elif hp >= 6:
        base_bid = DAILY_SALARY * 0.4
    else:
        base_bid = DAILY_SALARY * (0.5 + 0.05 * (6 - hp))

    # Adjust for supply: if supply is high, competition may be lower, so reduce bid
    # supply range 15-25, average 20
    supply_factor = 1.0 - (supply - 15.0) / 40.0  # between 0.75 and 1.0
    adjusted = base_bid * supply_factor

    # If many alive opponents, increase bid slightly to ensure win
    if alive_count >= 3:
        adjusted *= 1.15

    # Cannot exceed budget
    bid = min(budget, adjusted)
    # Ensure non-negative
    bid = max(bid, 0)
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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
        return min(budget, DAILY_SALARY * 0.4)

    # Gather previous bids
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Base bid: slightly above average of previous bids, but not exceeding budget
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        base_bid = avg_prev * 1.05
    else:
        base_bid = DAILY_SALARY * 0.6

    # Adjust for HP
    if hp <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif hp == 0:
        base_bid = min(budget, DAILY_SALARY * 0.95)

    # Ensure we don't blow budget
    capped_bid = min(budget, base_bid)
    # Also ensure at least 1 to avoid wasteful zero bids
    final_bid = max(1, capped_bid)
    return final_bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # First day: no previous trace
    if not yesterday_bids:
        # Base bid: enough to cover expected competition
        # Cindy typically bids >200 but may adjust; avoid overpaying
        base = DAILY_SALARY * 0.75  # 105
        # Adjust for supply scarcity
        scarcity_factor = 1 + ((MIN_SUPPLY + MAX_SUPPLY) / 2 - supply) / supply * 0.5
        bid = base * scarcity_factor
        bid = max(bid, DAILY_SALARY * 0.5)
        bid = min(bid, DAILY_SALARY * 0.95)
        return min(my_status['budget'], bid)

    # Subsequent days: react to yesterday's max bid
    max_prev = max(yesterday_bids)
    # If someone overbid heavily last time, be conservative
    if max_prev >= DAILY_SALARY * 1.0:
        if my_status['hp'] > 4:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.85)
    # Otherwise, bid slightly above average of yesterday's high
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    target = max(avg_prev + 2, DAILY_SALARY * 0.5)
    target = min(target, DAILY_SALARY * 0.9)
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.8)
    return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bid (if available) from each opponent, use only the first (last?) trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    
    # Determine base bid from opponent behavior
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        # Bid slightly above the max yesterday, but not too high
        base = max_prev + 2.0
    else:
        # No history: default to a moderate bid
        base = DAILY_SALARY * 0.5
    
    # Adjust based on supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # When supply low, we need to bid more
    if supply_ratio < 0.3:
        scarcity_factor = 1.2
    elif supply_ratio < 0.6:
        scarcity_factor = 1.0
    else:
        scarcity_factor = 0.8
    
    # Adjust based on HP
    if hp <= 2:
        hp_factor = 1.4
    elif hp <= 5:
        hp_factor = 1.1
    else:
        hp_factor = 0.9
    
    # Final bid calculation
    bid = base * scarcity_factor * hp_factor
    
    # Cap by budget and daily salary
    max_bid = min(budget, DAILY_SALARY * 0.85)
    bid = min(bid, max_bid)
    
    # Ensure we don't bid too low if we need water
    min_needed = DAILY_SALARY * 0.2
    if hp <= 3 and bid < min_needed:
        bid = min_needed
    
    # Round down to avoid fractions
    bid = int(bid * 100) / 100.0
    return max(1.0, bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Gather previous bids from traces
    prev_bids = []
    for oid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            prev_bids.append(prev['bid'])

    # Determine a baseline bid
    if no_water_days > 0 or hp <= 3:
        # Need water urgently
        base_bid = DAILY_SALARY * 0.85
    elif supply >= 20:
        base_bid = DAILY_SALARY * 0.65
    elif supply >= 15:
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.8

    # Adjust based on opponents' previous aggressiveness
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        # If they were very aggressive, they might be low on budget now
        if max_prev > DAILY_SALARY * 0.85:
            bid = min(base_bid, DAILY_SALARY * 0.75)
        else:
            # Try to outbid the average by a small margin
            bid = max(base_bid, avg_prev + 1.5)
    else:
        bid = base_bid

    # Ensure bid is within budget and not excessive
    bid = min(bid, budget)
    bid = max(bid, 0.1)
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
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Determine necessary bid to guarantee water if needed
    if my_status['hp'] <= 2:
        target_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 4:
        target_bid = min(my_status['budget'], DAILY_SALARY * 0.6)
    else:
        target_bid = min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Adjust based on yesterday's opponent bids if available
    if alive_opponents:
        highest_prev = 0
        for opp_id, opp in alive_opponents.items():
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                highest_prev = max(highest_prev, prev['bid'])
        if highest_prev > DAILY_SALARY * 0.85:
            target_bid = min(target_bid, DAILY_SALARY * 0.5)
        else:
            target_bid = max(target_bid, highest_prev * 0.8)
    
    # Ensure bid is non-negative and within budget
    bid = max(0, min(my_status['budget'], target_bid))
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    # Get current day's supply as integer
    supply = int(day_context['supply'])
    # Number of possible water allocations
    num_winners = int(supply // WATER_REQ)
    # Count alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    total_players = 1 + len(alive_opps)  # including self
    # Determine competition pressure
    competition = num_winners < total_players
    # Base bid: safe minimum
    base_bid = DAILY_SALARY * 0.4
    # If we need water urgently (low hp, or already dehydrated)
    urgent = my_status['hp'] <= 2 or my_status['no_water_days'] >= 1
    # Extract yesterday's max bid from alive opponents
    prev_max = 0.0
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_max = max(prev_max, trace['bid'])
    # Adjust bid based on competition and urgency
    if not competition:
        # Enough water for all, low bid
        bid = max(base_bid, 1.0)
    else:
        if prev_max > 0:
            # Outbid yesterday's max by a small margin, unless we are very healthy
            if not urgent and my_status['hp'] > 5:
                bid = min(prev_max + 0.5, DAILY_SALARY * 0.7)
            else:
                # Urgent: bid higher to guarantee water
                bid = max(prev_max + 1.5, DAILY_SALARY * 0.8)
        else:
            # No trace, conservative bid
            bid = DAILY_SALARY * 0.6 if urgent else DAILY_SALARY * 0.45
    # Clamp to budget and salary
    bid = min(bid, my_status['budget'], DAILY_SALARY)
    bid = max(bid, 0.0)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    desperate = (hp <= 3) or (no_water >= 2)

    alive_opps = [o for o in opponents_status.values() if o['alive']]
    last_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            lb = prev['bid']
            if lb is not None:
                last_bids.append(lb)

    if last_bids:
        avg_last = sum(last_bids) / len(last_bids)
        max_last = max(last_bids)
        if desperate:
            target = max_last + 5
        else:
            target = avg_last + 2
    else:
        progress = day / 10.0
        if desperate:
            base = 0.9 * DAILY_SALARY
        else:
            base = (0.3 + 0.4 * progress) * DAILY_SALARY
        target = base

    target = min(target, budget)
    target = max(target, 0)
    return target
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""
