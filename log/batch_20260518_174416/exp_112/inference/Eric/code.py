# ============================================================
# Experiment: exp_112
# Agent: Eric
# Source: exp_112
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Determine urgency based on hp and no_water_days
    if hp <= 2 or no_water_days >= 1:
        # Very urgent: need water at almost any cost
        max_bid = min(budget, DAILY_SALARY * 0.95)
        # Lower supply means more competition, so bid higher
        if supply < 20:
            return max_bid
        else:
            return min(max_bid, DAILY_SALARY * 0.7)
    elif hp <= 4 or no_water_days == 1:
        # Moderate urgency
        base_bid = DAILY_SALARY * 0.5
        if supply < 20:
            return min(budget, base_bid + 10)
        else:
            return min(budget, base_bid)
    else:
        # Healthy: conserve money
        base_bid = DAILY_SALARY * 0.35
        if supply < 20:
            return min(budget, base_bid + 5)
        else:
            return min(budget, base_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    past_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            past_bids.append(prev['bid'])

    # Base bid factor from HP: lower HP = higher bid
    hp_factor = max(0.0, (10 - hp) / 10.0)  # 0 when hp=10, 1 when hp=0
    base_bid = DAILY_SALARY * (0.3 + 0.7 * hp_factor)

    # Adjust for supply: lower supply -> need higher bid
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 at min, 1 at max
    base_bid *= (1.2 - 0.2 * supply_ratio)  # range 1.0 to 1.2

    # Consider opponent past bids to avoid overbidding when they are aggressive
    if past_bids:
        avg_prev = sum(past_bids) / len(past_bids)
        # If average opponent bid is high, we might lower ours if we are healthy
        if avg_prev > DAILY_SALARY * 0.
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    previous_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            previous_bids.append(trace['bid'])
    if previous_bids:
        sorted_bids = sorted(previous_bids)
        # target to outbid the second highest (if at least 2 opponents)
        if len(sorted_bids) >= 2:
            target = sorted_bids[-2] + 1.5
        else:
            target = sorted_bids[-1] + 0.5
    else:
        target = DAILY_SALARY * 0.6
    # Adjust based on own HP
    if my_status['hp'] <= 3:
        target = max(target, DAILY_SALARY * 0.8)
    # Cap by budget and max bid
    bid = min(my_status['budget'], target, DAILY_SALARY * 1.0)
    # Ensure we bid at least something if we are desperate
    if my_status['hp'] <= 2 and my_status['budget'] > 0:
        bid = max(bid, DAILY_SALARY * 0.5)
    return max(0, bid)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Look at yesterday's trace for alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid depends on supply and hp
    supply = day_context['supply']  # ensure it's float from context
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # Lower supply -> more aggressive bid
    urgency = 1.0 - supply_ratio
    
    # Adjust for personal health
    if hp <= 2:
        urgency = 1.0
    elif hp <= 5:
        urgency = max(urgency, 0.7)
    
    # Base bid as a fraction of salary
    base_bid = DAILY_SALARY * (0.3 + 0.6 * urgency)
    
    # Consider yesterday's maximum bid from opponents (if any)
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If previous max is high, we can try to undercut slightly if we are not desperate
        if max_prev > DAILY_SALARY * 0.8:
            # If they overbid, bid just above their min if we need water, else drop
            min_prev = min(yesterday_bids)
            if hp <= 3:
                target = min_prev + 1.0
            else:
                target = min_prev - 1.0  # try to save money
            target = max(target, DAILY_SALARY * 0.2)  # floor
            base_bid = max(base_bid, target)
        else:
            # If previous max was moderate, bid slightly above
            target = max_prev + 1.5
            base_bid = max(base_bid, target)
    
    # Apply budget and non-negative constraints
    bid = min(budget, base_bid)
    bid = max(0.0, bid)
    # Ensure integer-safe (all operations are float, but final value is float; that's fine)
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
    
    # Count alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    # Base bid factor: higher when supply is low
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # Opponent count factor: more opponents -> higher bid
    opp_factor = 1.0 + 0.1 * num_opponents  # up to 1.5 if 5 opponents
    
    # Determine needed aggressiveness based on HP
    if hp <= 2 or no_water_days >= 2:
        # Critical: must win water
        bid_factor = 0.9
    elif hp <= 5:
        bid_factor = 0.7
    else:
        bid_factor = 0.4
    
    # Combine factors: higher when supply low and many opponents
    adjusted_factor = bid_factor * (1.0 + (1.0 - supply_ratio) * 0.5) * opp_factor
    bid = min(budget, DAILY_SALARY * adjusted_factor)
    
    # Ensure bid is non-negative and not exceed budget
    bid = max(0.0, min(budget, bid))
    
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Gather yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid strategy
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
    else:
        highest_prev = 0

    # Compute water needed factor: more needed if hp low or no_water_days > 0
    water_urgency = max(0, (WATER_REQ - my_status['hp']) / WATER_REQ)
    if my_status['no_water_days'] > 0:
        water_urgency = 1.0

    # Supply factor: adjust for scarcity
    supply = day_context['supply']
    # supply is float, use it directly in calculation, but avoid using as index
    scarcity_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 when abundant, 1 when scarce

    # Base bid from yesterday
    if highest_prev < DAILY_SALARY * 0.5:
        # Cheap yesterday, try to outbid by small margin
        base = highest_prev + 1.5 + 5 * water_urgency
    else:
        # Expensive yesterday, be more cautious unless urgent
        base = highest_prev * (0.6 + 0.3 * water_urgency)
        # Add scarcity premium
        base += scarcity_factor * 20 * water_urgency

    # Ensure minimum bid (don't go too low if desperate)
    min_bid = DAILY_SALARY * 0.15 * (1 + 2 * water_urgency)
    bid = max(min_bid, base)

    # Budget constraint (always)
    bid = min(bid, my_status['budget'])

    # Round to avoid weird floats
    return round(bid, 2)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, max(1, DAILY_SALARY * 0.1))
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    if my_hp <= 2 or no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.4
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        if max_prev > DAILY_SALARY * 0.8:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
        if avg_prev < DAILY_SALARY * 0.6:
            base_bid = max(base_bid, avg_prev + 5)
    max_winners_possible = int(supply // WATER_REQ)
    if max_winners_possible <= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif max_winners_possible >= 3:
        base_bid = min(base_bid, DAILY_SALARY * 0.5)
    bid = min(my_budget, base_bid)
    bid = min(bid, DAILY_SALARY * 0.95)
    bid = max(bid, 1)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    supply = day_context['supply']
    supply_factor = 1.0 + (1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)) * 0.3  # higher when low supply
    hp = my_status['hp']
    budget = my_status['budget']
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if hp <= 2:
            target_bid = max(DAILY_SALARY * 0.85, max_prev + 2.0)
        elif hp >= 5:
            target_bid = min(DAILY_SALARY * 0.4, max_prev * 0.6)
        else:
            target_bid = min(DAILY_SALARY * 0.6, max_prev * 0.8)
    else:
        if hp <= 2:
            target_bid = DAILY_SALARY * 0.9
        elif hp >= 5:
            target_bid = DAILY_SALARY * 0.35
        else:
            target_bid = DAILY_SALARY * 0.5
    
    target_bid *= supply_factor
    target_bid = max(0.0, min(budget, target_bid))
    return target_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
    else:
        highest_prev = 0
    if my_status['hp'] <= 2:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        if highest_prev > 0:
            bid = min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev + 1))
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        if highest_prev > 0:
            bid = min(my_status['budget'], max(DAILY_SALARY * 0.3, highest_prev - 5))
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.4)
    bid = max(0, min(bid, my_status['budget']))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    if no_water_days > 0:
        base_bid = min(budget, DAILY_SALARY * 0.9)
        if max_prev_bid > 0:
            bid = max(base_bid, max_prev_bid + 1)
        else:
            bid = base_bid
    else:
        if hp > 3:
            base_bid = min(budget, DAILY_SALARY * 0.4)
        else:
            base_bid = min(budget, DAILY_SALARY * 0.7)
        if max_prev_bid > 0:
            bid = max(base_bid, min(budget, max_prev_bid * 0.8))
        else:
            bid = base_bid
    bid = max(0, min(budget, bid))
    return bid
"""
