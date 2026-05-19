# ============================================================
# Experiment: exp_090
# Agent: Eric
# Source: exp_090
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # No competition, bid minimal to get water
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Gather previous bids from opponents (yesterday)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Predict opponent bid: average or max?
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
    else:
        avg_prev = DAILY_SALARY * 0.5
        max_prev = DAILY_SALARY * 0.5
    
    # My desperation
    hp = int(my_status['hp'])
    no_water = int(my_status['no_water_days'])
    budget = int(my_status['budget'])
    
    # High need: bid near salary
    if hp <= 2 or no_water >= 2:
        target_bid = min(budget, DAILY_SALARY * 0.95)
    else:
        # Bid slightly above opponent average, but not too high
        target_bid = min(budget, max(avg_prev + 2, DAILY_SALARY * 0.5))
    
    # Ensure we don't overspend if supply is plentiful
    # Also consider that supply may be low; adjust upward
    if supply < 20:
        target_bid = min(budget, target_bid * 1.2)
    
    return int(target_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Determine urgency
    water_needed = WATER_REQ
    days_left = 10 - day + 1  # remaining days including today
    
    # Base bid: minimum to survive if low hp, otherwise conservative
    if hp <= 2:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        base_bid = min(budget, DAILY_SALARY * 0.6)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.4)
    
    # Adjust based on supply scarcity
    if supply < water_needed * 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.5)
    
    # Adapt to opponent behavior: outbid moderate opponents but avoid huge jumps
    if max_yesterday_bid >= DAILY_SALARY * 0.9:
        # High bidder present, conserve if possible
        if hp > 3:
            return min(budget, base_bid * 0.7)
        else:
            return min(budget, base_bid * 1.2)
    elif max_yesterday_bid >= DAILY_SALARY * 0.5:
        # Moderate pressure, slightly exceed
        target = max_yesterday_bid + 1.5
        return min(budget, max(base_bid, target))
    else:
        # Low pressure, stick to base
        return min(budget, base_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.5)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    if my_status['hp'] <= 2:
        target = max(DAILY_SALARY * 0.95, highest_prev_bid + 1)
    elif my_status['hp'] <= 4:
        target = max(DAILY_SALARY * 0.75, highest_prev_bid + 0.5)
    else:
        target = highest_prev_bid + 1 if highest_prev_bid < DAILY_SALARY * 0.8 else DAILY_SALARY * 0.6
    target = min(target, my_status['budget'])
    return round(max(target, 0), 2)
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
    no_water = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine a base bid from yesterday's highest bid among alive
    highest_yesterday = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > highest_yesterday:
                highest_yesterday = bid

    # Urgency based on HP and no_water_days
    if hp <= 2 or no_water >= 1:
        urgency_mult = 1.0
    else:
        urgency_mult = 0.6

    # If yesterday was very aggressive (bid high), we might not need to outbid if our HP is OK
    if hp > 4 and highest_yesterday > DAILY_SALARY * 0.85:
        target = DAILY_SALARY * 0.4
    else:
        # Aim to beat yesterday's highest by a small margin, but not exceed budget or salary
        if highest_yesterday > 0:
            target = highest_yesterday + 2.0
        else:
            # First day or no traces
            target = DAILY_SALARY * 0.5

    # Adjust target by urgency
    bid = target * urgency_mult
    # Do not bid more than budget, and not more than salary to conserve
    bid = min(bid, budget, DAILY_SALARY * 0.95)
    # Ensure non-negative
    if bid < 0:
        bid = 0.0
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, max(1, DAILY_SALARY * 0.4))

    # Collect yesterday's bids from alive opponents' traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid considering my health and days left
    days_left = 10 - day
    urgency = (WATER_REQ - no_water_days) / WATER_REQ  # urgency scale 0-1
    if hp <= 2 or no_water_days >= 3:
        base = DAILY_SALARY * 0.9
    elif hp <= 4:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.6

    # Adjust based on supply (if supply plentiful, bid lower)
    if supply > 20:
        base *= 0.85
    elif supply < 17:
        base *= 1.15

    # React to yesterday's bids: try to outbid the highest if needed, but cap
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev > DAILY_SALARY * 0.8 and budget > highest_prev + 1:
            # Compete only if we have enough budget and low urgency
            if urgency < 0.3:
                target = highest_prev - 5  # try to undercut
            else:
                target = highest_prev + 1
        else:
            target = max(base, highest_prev * 0.9)
    else:
        target = base

    # Ensure we don't exceed budget or go below 1
    bid = max(1, min(budget, target))
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
    no_water = my_status['no_water_days']

    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Look at previous_trace of all alive opponents
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine baseline based on supply
    if supply >= 20:
        baseline = DAILY_SALARY * 0.25
    else:
        baseline = DAILY_SALARY * 0.35

    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # Cindy's bids are high; if she's alive, she might repeat
        if max_prev > DAILY_SALARY * 0.8:
            if hp > 3:
                # Conservative, let others fight
                bid = min(budget, DAILY_SALARY * 0.2)
            else:
                # Need water, bid moderately higher than second highest
                second_highest = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else max_prev * 0.5
                bid = min(budget, max(baseline, second_highest + 2))
        else:
            # Lower pressure, bid slightly above max
            bid = min(budget, max(baseline, max_prev + 1))
    else:
        # No history, use default
        if hp <= 2 or no_water >= 1:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.4)

    # Ensure bid is within reasonable bounds
    bid = max(0, bid)
    # Avoid overspending on last day? Not needed.
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
    
    # Determine yesterday's max bid among alive opponents
    prev_bids = []
    for opp_id, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    
    # Base bid: enough to secure water if needed
    # If supply is low, we must bid higher to win
    num_winners = int(supply // WATER_REQ)  # safe int
    # Our target: if competition is high, bid more
    
    # Urgency: if low on HP, must get water
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif day > 8:
        # Late game: bid high to survive
        bid = min(budget, DAILY_SALARY * 0.85)
    else:
        # Early-mid game: exploit Bob's low bidding
        # Expected opponent bids: Bob ~70, others ~130-170
        # If yesterday max was high (>= DAILY_SALARY), then today might be lower (mean reversion)
        if max_prev_bid >= DAILY_SALARY * 0.9:
            # Others spent a lot yesterday; they might conserve today
            if supply < 20:
                bid = min(budget, DAILY_SALARY * 0.6)
            else:
                bid = min(budget, DAILY_SALARY * 0.5)
        else:
            # Low previous max: likely Bob set the pace
            # Bob's max was 76.5; we bid safely above that
            if supply < 18:
                bid = min(budget, DAILY_SALARY * 0.7)
            else:
                bid = min(budget, (80.0 + 1.0))  # slightly above Bob's historical high
    
    # Ensure we don't exceed budget
    return min(budget, max(0, bid))
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
    
    # Determine yesterday's max bid from alive opponents
    prev_max_bid = 0.0
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            if trace['bid'] > prev_max_bid:
                prev_max_bid = trace['bid']
    
    # Base bid on health and supply scarcity
    # scarcity increases as supply decreases
    scarcity_factor = 1.0 + (25.0 - supply) / 10.0  # ranges 1.0 to 2.0
    
    if hp <= 2:
        # Desperate: match or slightly beat previous max if needed
        desired = max(DAILY_SALARY * 0.85, prev_max_bid * 0.9)
        desired *= scarcity_factor
        desired = min(desired, DAILY_SALARY * 1.1)  # cap
    elif hp <= 5:
        # Moderate health: bid a safe amount
        desired = max(DAILY_SALARY * 0.6, prev_max_bid * 0.7)
        desired *= scarcity_factor
        desired = min(desired, DAILY_SALARY * 0.95)
    else:
        # Healthy: conserve budget, bid low but not zero
        desired = max(DAILY_SALARY * 0.3, prev_max_bid * 0.5)
        desired *= scarcity_factor
        desired = min(desired, DAILY_SALARY * 0.7)
    
    bid = min(budget, desired)
    # Ensure bid is at least 1 if we have budget
    if bid < 1 and budget >= 1:
        bid = 1.0
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    water_req = 8
    salary = 140

    # Determine urgency
    urgent = hp <= 2 or no_water >= 1

    # Collect last bids from alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    if prev_bids:
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev_bid = salary * 0.5

    if urgent:
        # Need water: bid slightly above average previous bid, accounting for competition
        base_bid = avg_prev_bid + 5.0
        # But don't exceed budget or salary * 0.95
        max_bid = min(budget, salary * 0.95)
        bid = min(base_bid, max_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.4  # 56
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If highest previous bid is very high, likely still high; stay low to conserve
        if highest_prev > DAILY_SALARY * 0.8:
            base_bid = DAILY_SALARY * 0.3  # 42
        else:
            base_bid = min(base_bid, highest_prev + 1.0)

    # Adjust for urgency
    urgent = False
    if hp <= 2 or no_water_days >= 2:
        urgent = True
    # Later days: need to secure water, increase bid
    day_factor = (day / 10.0) * 0.5 + 0.5  # 0.5 to 1.0
    if urgent:
        target_bid = min(budget, max(base_bid * day_factor * 1.5, DAILY_SALARY * 0.7))
    else:
        target_bid = min(budget, base_bid * day_factor)

    # Ensure minimum required to be competitive given supply (rough estimate)
    # Supply between 15 and 25, water requirement 8, so at most 2 can survive per day on average
    # Bidding too low might lose; but we want to avoid wasting money
    # Cap at budget
    target_bid = max(target_bid, 15.0)
    return min(budget, target_bid)
"""
