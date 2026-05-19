# ============================================================
# Experiment: exp_056
# Agent: Eric
# Source: exp_056
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Get yesterday's bids from opponents (if available)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid on my need and opponent aggression
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone bid very high, be conservative if I can survive
        if highest_prev >= DAILY_SALARY * 0.8:
            if hp > 3:
                return min(budget, DAILY_SALARY * 0.3)
            else:
                return min(budget, DAILY_SALARY * 0.9)
        else:
            # Try to outbid the highest by a small margin
            target = max(DAILY_SALARY * 0.5, highest_prev + 2)
            return min(budget, target)
    else:
        # No trace: bid based on supply and HP
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            # Moderate bid proportional to scarcity
            scarcity_factor = 1.0 - (supply - 15) / (25 - 15)
            bid = DAILY_SALARY * (0.3 + 0.4 * scarcity_factor)
            return min(budget, bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)
    # Determine opponent with highest previous bid
    highest_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > highest_prev_bid:
                highest_prev_bid = prev['bid']
    # Critical HP threshold
    if my_hp <= 2 or no_water_days >= 1:
        return min(my_budget, DAILY_SALARY * 0.9)
    # Early days: conserve but stay alive
    if day <= 3:
        return min(my_budget, max(DAILY_SALARY * 0.3, highest_prev_bid + 0.5))
    # Mid-late game: compete more
    # If opponent's previous bid was very high, they might overbid again
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        if my_hp > 3:
            return min(my_budget, DAILY_SALARY * 0.25)
        else:
            return min(my_budget, DAILY_SALARY * 0.75)
    # Normal: try to slightly beat the highest previous bid
    target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.0)
    return min(my_budget, target)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Get yesterday's bids from previous_trace
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine urgency
    urgent = my_status['hp'] <= 3 or my_status['no_water_days'] >= 2
    
    supply = day_context['supply']
    
    if urgent:
        # Desperate: bid high to guarantee water
        bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        return bid
    
    # Not urgent: try to save budget
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        # Adjust based on supply pressure
        if supply < 20:
            target = max(avg_prev + 5, DAILY_SALARY * 0.6)
        else:
            target = avg_prev + 2
        # Never exceed a safe cap to avoid waste
        cap = DAILY_SALARY * 0.7
        bid = min(target, cap)
    else:
        # No previous data: bid moderate
        bid = DAILY_SALARY * 0.45
    
    # Ensure we don't exceed budget
    bid = min(bid, my_status['budget'])
    return max(1, bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Get yesterday's max bid among alive opponents
    yesterday_bids = []
    for oid, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    # Base bid decision
    if not alive_opponents:
        # No competition, bid low to conserve budget
        return min(my_budget, DAILY_SALARY * 0.4)
    
    # Determine target bid based on yesterday's max
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If opponent was very aggressive, we need to be high
        if max_yesterday >= DAILY_SALARY * 1.0:
            if my_hp <= 2:
                # Must survive: bid very high
                return min(my_budget, DAILY_SALARY * 1.4)
            else:
                # Healthy, can match or slightly exceed
                return min(my_budget, max(DAILY_SALARY * 0.8, max_yesterday + 2.0))
        else:
            # Moderate competition: bid slightly above yesterday's max
            if my_hp <= 2:
                return min(my_budget, max(DAILY_SALARY * 0.9, max_yesterday + 3.0))
            else:
                return min(my_budget, max(DAILY_SALARY * 0.6, max_yesterday + 1.5))
    else:
        # No previous trace (first day or opponents dead? but we have alive_opponents but no trace?)
        if my_hp <= 2:
            return min(my_budget, DAILY_SALARY * 0.8)
        else:
            return min(my_budget, DAILY_SALARY * 0.5)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    base_bid = 0.0
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If I'm desperate (low HP or no water for days), outbid highest by small margin
        if my_status['no_water_days'] >= 2 or my_status['hp'] <= 2:
            base_bid = max(DAILY_SALARY * 0.9, highest_prev + 1.5)
        else:
            # If healthy, undercut or match
            base_bid = max(DAILY_SALARY * 0.5, highest_prev - 5.0)
    else:
        # No trace, use moderate bid
        base_bid = DAILY_SALARY * 0.6
    
    # Ensure we don't bid more than budget
    bid = min(my_status['budget'], base_bid)
    
    # Also ensure bid is non-negative and not ridiculously low
    bid = max(1.0, bid)
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

    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents)

    # Determine max units of water available (at most 3 given supply range)
    max_units = int(supply // WATER_REQ)  # explicit int conversion

    # Gather previous bids from alive opponents
    prev_bids = []
    for o in alive_opponents.values():
        trace = o.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Base decision on desperation
    desperate = (hp <= 2) or (no_water_days >= 1)

    # If we are the only alive player, just bid minimal to win
    if num_alive == 0:
        return min(budget, DAILY_SALARY * 0.4)

    # Estimate required bid to secure water
    # If supply is low (<= 2 units), competition is high; bid aggressively
    if max_units <= 1:
        if desperate:
            target = DAILY_SALARY * 0.9
        else:
            target = DAILY_SALARY * 0.6
    elif max_units == 2:
        if desperate:
            target = DAILY_SALARY * 0.7
        else:
            target = DAILY_SALARY * 0.45
    else:  # max_units >= 3, plenty of water
        if desperate:
            target = DAILY_SALARY * 0.5
        else:
            target = DAILY_SALARY * 0.3

    # Adjust based on previous opponent bids (if any)
    if prev_bids:
        highest_prev = max(prev_bids)
        # If someone bid very high yesterday, they may continue; avoid overbidding if not desperate
        if highest_prev > DAILY_SALARY * 0.8:
            if desperate:
                target = max(target, highest_prev * 1.1)
            else:
                target = min(target, DAILY_SALARY * 0.3)
        # If low bids, we can slightly outbid the max
        else:
            target = max(target, highest_prev + 1.5)

    # Clamp to budget and ensure positive
    bid = max(0, min(budget, target))
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = [o for o in opponents_status.values() if o['alive']]
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    # Get yesterday's max bid from alive opponents with trace
    max_prev = None
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            if max_prev is None or trace['bid'] > max_prev:
                max_prev = trace['bid']
    
    # Emergency bids if low HP or many days without water
    if my_hp <= 2 or no_water >= 2:
        return min(my_budget, DAILY_SALARY * 0.95)
    if my_hp <= 4:
        return min(my_budget, DAILY_SALARY * 0.75)
    
    # Normal case: use yesterday's info if available
    if max_prev is not None:
        # Slightly outbid, but cap at budget and not more than 85% of salary
        bid = min(my_budget, max(DAILY_SALARY * 0.5, max_prev + 1.5))
        return bid
    
    # First day or no trace: conservative bid
    return min(my_budget, DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    daily_salary = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, daily_salary * 0.4)
    
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= daily_salary * 0.85:
            if hp > 3:
                return min(budget, daily_salary * 0.55)
            return min(budget, daily_salary * 0.95)
        else:
            target = max(daily_salary * 0.5, highest_prev_bid + 1.5)
            return min(budget, target)
    else:
        if hp <= 2:
            return min(budget, daily_salary * 0.9)
        else:
            base = daily_salary * (0.5 + 0.1 * (day / 10))
            return min(budget, base)
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
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Base bid depends on HP and remaining days
    # More aggressive when HP is low
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    elif hp <= 6:
        base_bid = DAILY_SALARY * 0.5
    else:
        base_bid = DAILY_SALARY * 0.35
    
    # Increase bid if many opponents (more competition)
    adjustment = 1.0 + (num_alive - 1) * 0.1
    bid = base_bid * adjustment
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    
    # Ensure minimum bid to not be zero (sometimes needed)
    bid = max(bid, 1.0)
    
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    highest_prev = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev = max(highest_prev, prev['bid'])
    base_bid = max(DAILY_SALARY * 0.5, highest_prev + 1.0)
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    return min(my_status['budget'], base_bid)
"""
