# ============================================================
# Experiment: exp_024
# Agent: Eric
# Source: exp_024
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Use previous_trace from any opponent to gauge competition
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = prev['bid']
            if bid_val > highest_prev_bid:
                highest_prev_bid = bid_val
    
    # Day 1 or no traces: base bid on HP
    if highest_prev_bid == 0:
        if my_status['hp'] <= 2:
            # Very low HP: need water
            bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 4:
            bid = min(my_status['budget'], DAILY_SALARY * 0.6)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.35)
        return max(0, int(bid))
    
    # Subsequent days: react to highest previous bid
    # If we are healthy and they bid high, reduce bid to save budget
    if my_status['hp'] > 3 and highest_prev_bid >= DAILY_SALARY * 0.8:
        bid = min(my_status['budget'], DAILY_SALARY * 0.3)
    elif my_status['hp'] <= 2:
        # Desperate: overbid slightly to secure water
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, highest_prev_bid + 1.5))
    else:
        # Normal: try to underbid but still win if possible
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 0.5))
    
    return max(0, int(bid))
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opps)
    
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        if prev_bids and max(prev_bids) > 100:
            base_bid = DAILY_SALARY * 0.25
        else:
            base_bid = DAILY_SALARY * 0.5
    
    supply = day_context['supply']
    supply_factor = 1 + ((MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)) * 0.3
    bid = base_bid * supply_factor
    bid = min(bid, my_status['budget'])
    bid = max(bid, 0)
    return round(bid, 2)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid
    if hp <= 2:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base_bid = min(budget, DAILY_SALARY * 0.7)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.5)
    
    # Adjust based on yesterday's highest pressure
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            if hp > 3:
                base_bid = min(budget, highest_prev * 0.95)  # slightly undercut if safe
            else:
                base_bid = min(budget, highest_prev + 5)  # match or exceed
        else:
            base_bid = min(budget, max(base_bid, highest_prev + 1.5))
    
    # Supply-based adjustment
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    if supply_ratio < 0.3:
        base_bid = min(budget, base_bid * 1.2)
    
    # Ensure we don't bid more than budget
    final_bid = min(budget, base_bid)
    return int(final_bid)
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
    day = day_context['day']  # not directly used but available
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    max_prev_bid = None
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if max_prev_bid is None or prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    
    # Base bid strategy
    if my_hp <= 2:
        # Urgent need for water
        if max_prev_bid is not None:
            target = max(DAILY_SALARY * 0.7, max_prev_bid + 2)
        else:
            target = DAILY_SALARY * 0.8
    elif my_hp <= 5:
        # Moderate need
        if max_prev_bid is not None:
            target = max(DAILY_SALARY * 0.5, max_prev_bid - 1)
        else:
            target = DAILY_SALARY * 0.6
    else:
        # High HP, can be conservative
        if max_prev_bid is not None:
            target = max(DAILY_SALARY * 0.35, max_prev_bid * 0.85)
        else:
            target = DAILY_SALARY * 0.4
    
    # Adjust based on supply scarcity
    if supply < 20:
        target *= 1.15
    
    # Ensure we don't overbid beyond budget
    target = min(my_budget, target)
    # Also ensure we don't bid higher than necessary if budget is large, keep some reserve
    target = min(target, my_budget - 5)  # always keep 5 buffer
    return max(0.0, target)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday's highest opponent bid
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])

    # Determine urgency based on health and days left
    # Low health => need water urgently
    # Also consider if supply is low => more competition
    urgency_factor = 0.0
    if hp <= 2:
        urgency_factor = 0.9
    elif hp <= 4:
        urgency_factor = 0.7
    else:
        urgency_factor = 0.55

    # Adjust for supply tightness (lower supply => more competitive)
    if supply < 20:
        urgency_factor += 0.1
    # Final bid: based on salary, but not exceeding budget
    base_bid = DAILY_SALARY * urgency_factor
    # If we have seen yesterday's high bids, decide whether to outbid
    if max_prev_bid > 0:
        # If opponent's highest bid is extremely high, we may not outbid unless desperate
        if max_prev_bid > 160 and hp > 4:
            # Let them overpay; we take a lower risk
            final_bid = max(30, min(budget, DAILY_SALARY * 0.45))
        else:
            # If we need water, outbid slightly above their max to ensure win
            if urgency_factor >= 0.7:
                final_bid = max(base_bid, max_prev_bid + 1.0)
            else:
                # If we are comfortable, bid lower to preserve budget
                final_bid = max(30, min(base_bid, max_prev_bid - 5.0))
    else:
        # No yesterday data, use base
        final_bid = base_bid

    # Clamp to budget and reasonable bounds
    final_bid = min(budget, final_bid)
    # Ensure non-negative
    final_bid = max(0, final_bid)
    # No fractional bids
    return round(final_bid, 2)
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
    no_water = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and not trace.get('status') == 'error' and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine pressure from last round
    if prev_bids:
        max_prev = max(prev_bids)
    else:
        max_prev = 0.0
    
    # Base bid as fraction of salary, considering supply scarcity
    if supply < 18:
        base = DAILY_SALARY * 0.9
    elif supply < 21:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.55
    
    # Adjust for desperation
    if hp <= 3 or no_water >= 1:
        aggressive_mult = 1.2
    else:
        aggressive_mult = 1.0
    
    # Final bid: at least maximum of base and slightly above max_prev
    bid = max(base * aggressive_mult, max_prev + 1.5)
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Also ensure non-negative
    if bid < 0:
        bid = 0.0
    return bid
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

    supply = int(day_context['supply'])
    max_winners = supply // WATER_REQ

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    num_alive = len(alive_opponents)

    # Get yesterday's bids from opponents who have trace
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Determine a baseline from yesterday's behavior
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
        # Aggressive opponents: adjust bid accordingly
        if max_prev >= DAILY_SALARY * 0.85:
            # They might be desperate; we need to compete if necessary
            if my_status['hp'] <= 3 or my_status['no_water_days'] >= 2:
                target = avg_prev + 5.0
            else:
                target = min(DAILY_SALARY * 0.4, avg_prev * 0.7)
        else:
            target = max(DAILY_SALARY * 0.35, avg_prev + 2.0)
    else:
        # No previous data, use conservative estimate
        if my_status['hp'] <= 2:
            target = DAILY_SALARY * 0.8
        else:
            target = DAILY_SALARY * 0.45

    # Adjust based on personal needs
    if my_status['no_water_days'] >= 2:
        target = max(target, DAILY_SALARY * 0.7)
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.9)

    # Ensure we don't exceed budget or go below 0
    bid = min(my_status['budget'], target)
    bid = max(0, bid)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # First day: no trace, bid moderate
    if day == 1 or not any(opp.get('previous_trace', {}).get('bid') is not None for opp in alive_opponents):
        base_bid = min(budget, DAILY_SALARY * 0.6)
        if hp <= 3:
            base_bid = min(budget, DAILY_SALARY * 0.85)
        return max(1, base_bid)
    
    # Collect yesterday's bids
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    if not prev_bids:
        # fallback
        base = min(budget, DAILY_SALARY * 0.6)
        if hp <= 3:
            base = min(budget, DAILY_SALARY * 0.85)
        return max(1, base)
    
    max_prev = max(prev_bids)
    avg_prev = sum(prev_bids) / len(prev_bids)
    
    # Determine bid
    if hp <= 2:
        # desperate: bid high but not over budget
        target = max(DAILY_SALARY * 0.9, max_prev + 1.5)
        return min(budget, target)
    elif hp <= 4:
        target = min(max_prev * 1.2, DAILY_SALARY * 0.85)
        return min(budget, target)
    else:
        # healthy: try to match or slightly beat yesterday's max
        # but don't overspend
        if max_prev >= DAILY_SALARY * 0.8:
            # high competition, stay moderate to preserve budget
            target = min(budget, DAILY_SALARY * 0.65)
        else:
            target = min(budget, max_prev + 1.0)
        return max(1, target)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid')
            if bid is not None:
                yesterday_bids.append(bid)
    
    # Base bid based on survival pressure
    if hp <= 2:
        # Desperate: bid high to secure water
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        if yesterday_bids:
            avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
            if avg_yesterday > DAILY_SALARY * 0.6:
                # Expect competition; bid moderate
                bid = min(budget, DAILY_SALARY * 0.55)
            else:
                # Low competition; bid low
                bid = min(budget, DAILY_SALARY * 0.35)
        else:
            # No trace; conservative
            bid = min(budget, DAILY_SALARY * 0.4)
    
    # Adjust for low supply
    if supply < MIN_SUPPLY + 3:
        bid = min(budget, bid + 15)
    
    # Ensure bid is at least some positive number to avoid tie issues
    bid = max(bid, 1.0)
    
    # Convert to float and cap at budget
    return float(min(bid, budget))
"""
