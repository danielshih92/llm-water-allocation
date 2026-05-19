# ============================================================
# Experiment: exp_078
# Agent: Eric
# Source: exp_078
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
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Compute yesterday's max bid from opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    if prev_bids:
        max_prev_bid = max(prev_bids)
    else:
        max_prev_bid = 0
    
    # Heal when low HP; otherwise conservative
    if hp <= 2:
        # Need water badly: bid enough to secure, but not exceed budget
        target = min(budget, DAILY_SALARY * 0.9)
        # Ensure index safety: no list indexing needed here
        return int(target)
    elif no_water_days >= 1:
        # Moderate need
        target = min(budget, max(DAILY_SALARY * 0.5, max_prev_bid + 1.0))
        return int(target)
    else:
        # Healthy, conserve budget
        # If opponents bid high yesterday, avoid bidding war
        if max_prev_bid >= DAILY_SALARY * 0.8:
            target = min(budget, DAILY_SALARY * 0.3)
        else:
            target = min(budget, max(DAILY_SALARY * 0.4, max_prev_bid + 0.5))
        return int(target)
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

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev_bid = max(prev_bids) if prev_bids else 0

    base_bid = DAILY_SALARY * 0.4
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.7

    if max_prev_bid > 80:
        bid = min(budget, max_prev_bid + 2)
    elif supply < 18:
        bid = min(budget, base_bid + 20)
    else:
        bid = min(budget, base_bid)

    return int(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    # Number of winners: floor division, ensure int
    num_winners = int(supply
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
    no_water_days = my_status['no_water_days']

    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    winners_possible = int(supply // WATER_REQ)

    # Collect yesterday's bids from alive opponents
    last_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None and bid > 0:
            last_bids.append(bid)

    # Determine baseline bid
    if hp <= 3 or no_water_days >= 2:
        # Critical need: bid high to secure water
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        if last_bids:
            avg_last = sum(last_bids) / len(last_bids)
            # Adjust based on competition
            if winners_possible <= 1:
                target = max(DAILY_SALARY * 0.7, avg_last + 10.0)
            else:
                target = max(DAILY_SALARY * 0.5, avg_last + 5.0)
        else:
            target = DAILY_SALARY * 0.6
        bid = min(budget, target)

    # Ensure positive bid and not exceed budget
    bid = max(0.0, bid)
    bid = min(budget, bid)

    return bid
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Extract yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid on supply scarcity and HP
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 if scarce, 1 if abundant
    
    # HP urgency: lower HP -> bid higher
    if hp <= 2:
        urgency = 1.0
    elif hp <= 5:
        urgency = 0.7
    else:
        urgency = 0.4
    
    # If we haven't had water for 2+ days, emergency
    if no_water_days >= 2:
        urgency = 1.0
    
    # Estimate opponent pressure from yesterday's bids
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        avg_yesterday = sum(yesterday_bids)/len(yesterday_bids)
        # If yesterday's max was very high, they might be aggressive; avoid high bidding unless needed
        opp_pressure = max_yesterday / DAILY_SALARY
    else:
        opp_pressure = 0.5  # conservative guess
    
    # Base bid: salary times urgency adjusted by supply and opponent pressure
    # When supply is low and opponents are aggressive, we may need to bid higher
    scarcity_factor = 1.0 - supply_ratio  # 1 if scarce, 0 if abundant
    base_bid = DAILY_SALARY * (urgency * (0.5 + 0.3 * scarcity_factor) + 0.1 * opp_pressure)
    
    # Ensure we don't exceed budget
    bid = min(budget, base_bid)
    
    # On day 1, start conservative to save budget
    if day == 1:
        bid = min(budget, DAILY_SALARY * 0.4)
    
    # If we have very low budget and low HP, go all in
    if hp <= 1 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.9)
    
    # Round to 2 decimals
    bid = round(bid, 2)
    
    return bid
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
    if not alive_opponents:
        # Solo: bid minimal to save budget
        return min(budget, DAILY_SALARY * 0.3)

    # Analyze yesterday's traces for high pressure
    high_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > high_prev_bid:
                high_prev_bid = bid

    # Base bid on supply and HP
    if supply >= 20:
        base_bid = DAILY_SALARY * 0.4
    else:
        base_bid = DAILY_SALARY * 0.6

    # Adjust for HP crisis
    if hp <= 2 or no_water_days >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Counter high previous bids
    if high_prev_bid > DAILY_SALARY * 0.9:
        # Avoid bidding war; bid slightly less
        bid = min(budget, high_prev_bid - 5.0)
    elif high_prev_bid > DAILY_SALARY * 0.6:
        # Moderate pressure: match or slightly beat
        bid = min(budget, max(base_bid, high_prev_bid + 1.0))
    else:
        # Low pressure: use base
        bid = min(budget, base_bid)

    # Ensure within budget and non-negative
    bid = max(0.0, min(budget, bid))
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

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    if prev_bids:
        max_prev = max(prev_bids)
        # If someone bid very high (likely Cindy), avoid
        if max_prev > DAILY_SALARY * 0.85:
            target = min(budget, DAILY_SALARY * 0.55)
        else:
            # Bid slightly above max previous
            target = min(budget, max_prev + 2.0)
    else:
        target = min(budget, DAILY_SALARY * 0.5)

    # Urgency based on HP and supply
    if hp <= 2:
        target = max(target, min(budget, DAILY_SALARY * 0.85))
    elif hp <= 4:
        target = max(target, min(budget, DAILY_SALARY * 0.7))

    # Adjust for supply scarcity (lower supply -> higher bid needed)
    if supply < 20:
        target = max(target, min(budget, DAILY_SALARY * 0.65))

    # Ensure we never bid more than budget
    return min(budget, max(0, target))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine desperation level
    if hp <= 2:
        desperation = 3
    elif hp <= 5:
        desperation = 2
    else:
        desperation = 1
    
    # Base bid: fraction of salary scaled by desperation and supply ratio
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                yesterday_bids.append(trace['bid'])
    # Determine target bid based on yesterday's max
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If we are desperate (low HP) or need to guarantee water, bid just above max_yesterday
        if my_status['hp'] <= 2:
            target_bid = max_yesterday + 2.0
        else:
            # Otherwise, be slightly more conservative but still competitive
            target_bid = max_yesterday + 1.0
    else:
        # First day or no previous data: base on HP
        if my_status['hp'] <= 2:
            target_bid = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 5:
            target_bid = DAILY_SALARY * 0.6
        else:
            target_bid = DAILY_SALARY * 0.4
    # Ensure target does not exceed budget and is not negative
    # Also consider supply: if supply is low, we may need to bid higher
    supply = day_context['supply']
    supply_factor = 1.0
    if supply < 20:
        supply_factor = 1.2
    elif supply > 22:
        supply_factor = 0.9
    target_bid *= supply_factor
    # Cap by remaining budget
    final_bid = min(my_status['budget'], target_bid)
    # Ensure non-negative and reasonable floor
    if my_status['hp'] <= 1:
        # Desperate: bid up to 95% of daily salary or max budget
        final_bid = max(final_bid, DAILY_SALARY * 0.95)
    else:
        final_bid = max(final_bid, 0.0)
    return min(final_bid, my_status['budget'])
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure int
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # If alone, bid just enough
        return min(budget, DAILY_SALARY * 0.3)
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    max_prev = max(prev_bids) if prev_bids else 0
    avg_prev = sum(prev_bids)/len(prev_bids) if prev_bids else 0
    
    # Urgency based on hp
    if hp <= 0:
        # Should not happen, but if already dead, bid 0
        return 0.0
    elif hp <= 2:
        # Desperate: need water at any reasonable cost
        target = min(budget, DAILY_SALARY * 0.9)
        # But if supply is very low, we might need to outbid
        if supply < WATER_REQ + 5:
            target = max(target, max_prev + 1)
        return target
    elif hp <= 4:
        # Moderate urgency
        base = DAILY_SALARY * 0.5
        # If yesterday was high, we need to match pressure
        if max_prev > DAILY_SALARY * 0.85 and supply < WATER_REQ * 2:
            return min(budget, max_prev + 0.5)
        # Otherwise try to save money
        return min(budget, base)
    else:
        # Healthy; can afford to bid low and save budget
        # Use supply to estimate winning bid: if high supply, we can be cheap
        if supply >= WATER_REQ * 2:
            return min(budget, DAILY_SALARY * 0.3)
        else:
            # Low supply, need to be somewhat competitive
            return min(budget, max(DAILY_SALARY * 0.4, max_prev * 0.95))
"""
