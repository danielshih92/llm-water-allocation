# ============================================================
# Experiment: exp_063
# Agent: Eric
# Source: exp_063
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
    # Base bid: 60% of salary, scaled by supply vs max supply
    max_supply = 25.0
    base_ratio = 0.6 * (max_supply / supply)
    target_bid = DAILY_SALARY * base_ratio
    # Adjust based on HP: if low HP, bid more aggressively
    if hp <= 3:
        target_bid = DAILY_SALARY * 0.9
    # Ensure we don't bid more than budget
    bid = min(target_bid, budget)
    # Ensure positive bid
    bid = max(bid, 1.0)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.5)
    
    # Focus on strongest opponent (likely Cindy)
    strongest = max(alive_opponents, key=lambda o: o['budget'])
    prev_bid = None
    prev_trace = strongest.get('previous_trace', {})
    if prev_trace and 'bid' in prev_trace and prev_trace['bid'] is not None:
        prev_bid = float(prev_trace['bid'])
    
    # Base bid: slightly above opponent's previous bid, adjusted for supply
    if prev_bid is not None:
        target_bid = prev_bid + 2.0
    else:
        target_bid = DAILY_SALARY * 0.7
    
    # Adjust based on supply: if plenty, bid lower
    supply_ratio = supply / WATER_REQ
    if supply_ratio >= 2.5:
        target_bid *= 0.7
    elif supply_ratio >= 2.0:
        target_bid *= 0.85
    
    # Adjust based on HP: if low, bid more aggressively
    if hp <= 2:
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target_bid = max(target_bid, DAILY_SALARY * 0.7)
    
    # Also consider day: later days, bid more to secure water
    if day >= 7:
        target_bid *= 1.2
    elif day >= 5:
        target_bid *= 1.1
    
    # Ensure no overspend
    bid = min(budget, target_bid)
    # Ensure at least a small bid if alive
    bid = max(bid, 1.0)
    return bid
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # base bid proportional to scarcity
    scarcity_factor = 1 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 when max, 1 when min
    base_bid = DAILY_SALARY * (0.3 + 0.5 * scarcity_factor)
    
    # urgency adjustments
    if no_water_days > 0:
        urgency_mult = 1.8
    elif hp <= 2:
        urgency_mult = 1.5
    elif hp <= 5:
        urgency_mult = 1.2
    else:
        urgency_mult = 0.9
    
    # consider opponents' traces (only previous day)
    opp_prev_bids = []
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            opp_prev_bids.append(prev['bid'])
    if opp_prev_bids:
        max_prev = max(opp_prev_bids)
        # if someone bid very high yesterday, be cautious unless we're desperate
        if max_prev > DAILY_SALARY * 0.85 and urgency_mult < 1.5:
            urgency_mult *= 0.8
    
    bid = base_bid * urgency_mult
    bid = max(bid, 1)  # minimum 1
    bid = min(bid, budget)
    return bid
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
    
    max_prev_bid = 0
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev:
                bid_val = prev['bid']
                if bid_val is not None:
                    max_prev_bid = max(max_prev_bid, bid_val)
    
    if hp <= 2 or no_water >= 1:
        target = max_prev_bid + 2.5
        target = max(target, DAILY_SALARY * 0.7)
    else:
        target = max_prev_bid + 1.5
        target = min(target, DAILY_SALARY * 0.6)
    
    target = min(target, budget)
    target = max(target, 0)
    return target
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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
    
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # base bid: need water, but save money
    base = DAILY_SALARY * 0.45
    
    # adjust for supply tightness
    max_winners = int(supply) // WATER_REQ
    if max_winners <= 1:
        base = DAILY_SALARY * 0.75
    
    # hp urgency
    if hp <= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 4:
        base = DAILY_SALARY * 0.65
    
    # check yesterday's bids to outbid (if any)
    highest_prev = 0.0
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        bid = trace.get('bid')
        if bid is not None:
            highest_prev = max(highest_prev, bid)
    
    if highest_prev > 0:
        # ensure outbid by small margin
        base = max(base, highest_prev + 1.5)
    
    # cap at budget
    bid = min(budget, base)
    
    # ensure non-negative
    bid = max
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

    # Identify alive opponents
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}

    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for aid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate if high bidders are present
    high_bid_pressure = any(b >= DAILY_SALARY * 0.8 for b in yesterday_bids) if yesterday_bids else False

    # Base bid: if we need water (low HP) bid moderately
    if my_status['hp'] <= 2:
        # Critical: need water now, bid up to 85% of salary
        bid = min(my_status['budget'], DAILY_SALARY * 0.85)
    elif my_status['hp'] <= 4:
        # Moderate need: bid just enough to win if others are low
        if high_bid_pressure:
            # Others are high, let them fight, we bid minimal
            bid = min(my_status['budget'], DAILY_SALARY * 0.2)
        else:
            # No high pressure, bid slightly above cost
            bid = min(my_status['budget'], max(DAILY_SALARY * 0.4, DAILY_SALARY * 0.5))
    else:
        # High HP, conserve budget
        if high_bid_pressure:
            bid = min(my_status['budget'], DAILY_SALARY * 0.15)
        else:
            # No pressure, bid minimal to maybe win cheap water
            bid = min(my_status['budget'], DAILY_SALARY * 0.3)

    # Ensure bid is non-negative
    bid = max(0.0, bid)
    # If budget already low, bid as much as we can afford (but less than salary)
    if my_status['budget'] < DAILY_SALARY * 0.4 and my_status['hp'] > 2:
        bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    # Never bid more than budget
    bid = min(bid, my_status['budget'])
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Estimate opponent bids from yesterday's trace
    opp_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opp_bids.append(prev['bid'])

    # Determine target bid
    target_bid = DAILY_SALARY * 0.6  # baseline
    if opp_bids:
        max_prev = max(opp_bids)
        # Cindy-like high bidder
        if max_prev > DAILY_SALARY * 1.2:
            if my_status['hp'] > 4:
                target_bid = min(max_prev + 0.1, DAILY_SALARY * 0.7)
            else:
                target_bid = min(max_prev + 0.5, DAILY_SALARY * 0.95)
        else:
            target_bid = max(DAILY_SALARY * 0.5, max_prev + 0.2)
    
    # Adjust for low HP
    if my_status['hp'] <= 2:
        target_bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        target_bid = max(target_bid, DAILY_SALARY * 0.75)

    # Ensure we don't exceed budget
    bid = min(my_status['budget'], target_bid)
    return max(0, bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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
        return min(budget, DAILY_SALARY * 0.4)

    # Collect previous bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Base bid: moderate
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp > 3:
                # Conserve, bid low to recover budget
                bid = min(budget, DAILY_SALARY * 0.3)
            else:
                # Need water, bid competitively
                bid = min(budget, DAILY_SALARY * 0.95)
        else:
            # Opponents moderate, we can be slightly above or safe
            safe_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            bid = min(budget, safe_bid)
    else:
        # No trace, fallback
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.55)

    # Adjust for supply tightness
    if supply < (WATER_REQ * len(alive_opponents) + 1):
        # Water scarce, increase bid if necessary
        bid = max(bid, min(budget, DAILY_SALARY * 0.8))

    # Ensure we can't bid more than budget
    return min(budget, bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0.0
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        target = max(max_yesterday + 1.5, DAILY_SALARY * 0.75)
        return min(budget, target)
    elif hp <= 4:
        target = max(max_yesterday * 0.9, DAILY_SALARY * 0.5)
        return min(budget, target)
    else:
        target = max(max_yesterday * 0.7, DAILY_SALARY * 0.4)
        return min(budget, target)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Ensure no float index issues
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Gather previous bids from opponents who were alive yesterday
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(float(trace['bid']))
    
    # Base bid: a fraction of budget, but not more than daily salary
    base_bid = min(budget, DAILY_SALARY * 0.6)
    
    # Urgency based on my health
    if hp <= 2 or no_water_days >= 1:
        urgency_mult = 0.9
    elif hp <= 5:
        urgency_mult = 0.7
    else:
        urgency_mult = 0.4
    
    bid = base_bid * urgency_mult
    
    # Adjust based on opponents' previous behavior
    if prev_bids:
        highest_prev = max(prev_bids)
        # If highest previous bid is very high, maybe they'll bid lower today? Assume inertia.
        if highest_prev > DAILY_SALARY * 0.85:
            # They are aggressive; if I need water, match or slightly exceed
            if hp <= 3:
                bid = min(budget, highest_prev + 1.5)
            else:
                bid = min(budget, highest_prev * 0.8)
        else:
            # Moderate previous bids: outbid slightly if needed, else stay low
            if hp <= 3:
                bid = min(budget, highest_prev + 2.0)
            else:
                bid = min(budget, max(bid, highest_prev * 0.6))
    else:
        # No previous data: use baseline with safety
        pass
    
    # Ensure bid is non-negative and within budget
    bid = max(0.0, min(budget, bid))
    
    # Round to avoid floating point issues? Not necessary.
    return bid
"""
