# ============================================================
# Experiment: exp_065
# Agent: Eric
# Source: exp_065
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

    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Look at yesterday's highest bid from opponents
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If we are very low on hp, bid aggressively
        if my_status['hp'] <= 2:
            target = min(my_status['budget'], max(DAILY_SALARY * 0.9, highest_prev + 2))
        else:
            target = min(my_status['budget'], highest_prev + 1.5)
        return target

    # No history: conservative bid
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.85)
    return min(my_status['budget'], DAILY_SALARY * 0.4)
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
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    # Supply factor: lower supply => need higher bid
    supply = day_context['supply']
    supply_factor = max(1.0, (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1) + 1.0)

    # HP urgency
    hp = my_status['hp']
    no_water = my_status['no_water_days']

    # Base bid strategy
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If we are desperate (low HP or already dehydrated)
        if hp <= 2 or no_water >= 1:
            target_bid = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
        else:
            # Conservative: outbid only if previous was high, otherwise maintain moderate
            if highest_prev >= DAILY_SALARY * 0.75:
                target_bid = max(DAILY_SALARY * 0.6, highest_prev + 1.0)
            else:
                target_bid = DAILY_SALARY * 0.5
    else:
        # No history: moderate initial bid
        target_bid = DAILY_SALARY * 0.55

    # Apply supply factor (aggressive if supply low)
    if supply < 18:
        target_bid = max(target_bid, DAILY_SALARY * 0.7)

    # Ensure we don't exceed budget
    final_bid = min(my_status['budget'], max(1.0, target_bid))

    # Round to two decimals for consistency (optional but safe)
    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}

    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    if not yesterday_bids:
        # No trace, baseline conservative
        base_bid = min(budget, DAILY_SALARY * 0.55)
    else:
        max_prev = max(yesterday_bids)
        min_prev = min(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)

        # Assume Cindy (high) and Bob (low) are extremes
        # Target to beat low bidders but not exceed medium bid
        target = min_prev + 5  # slightly above lowest
        if target > DAILY_SALARY * 0.85:
            target = max_prev * 0.9  # reduce if too high
        base_bid = min(budget, max(target, DAILY_SALARY*0.4))

    # Adjust for urgency
    if hp <= 2 or no_water_days >= 1:
        # Critical need, bid high but within budget
        bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        bid = min(budget, base_bid * 1.2)
    else:
        bid = min(budget, base_bid * 0.9)

    # Ensure we don't exceed budget
    bid = min(bid, budget)

    # Handle edge case: if budget is very low, bid 0
    if budget < 1:
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Baseline: if no yesterday data, use salary * 0.5
    if not yesterday_bids:
        base = DAILY_SALARY * 0.5
    else:
        # Use average of yesterday bids as a competitive indicator
        base = sum(yesterday_bids) / len(yesterday_bids)

    # Adjust based on urgency
    if hp <= 2 or no_water_days >= 2:
        # Urgent: need water, bid high enough to win
        target = max(DAILY_SALARY * 0.9, base * 1.3)
    elif hp <= 4:
        target = max(DAILY_SALARY * 0.7, base * 1.1)
    else:
        # Comfortable: save budget
        target = min(DAILY_SALARY * 0.5, base * 0.8)
        target = max(target, 1)  # never bid below 1

    # Ensure we don't exceed budget
    bid = min(budget, target)
    # Also ensure minimum bid of 1 if we have budget
    if budget >= 1 and bid < 1:
        bid = 1
    return int(bid)
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
    
    budget = my_status['budget']
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Estimate opponent bidding behavior from yesterday's trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid on supply level and day
    if supply >= 22:
        base_bid = DAILY_SALARY * 0.35
    elif supply >= 18:
        base_bid = DAILY_SALARY * 0.55
    else:
        base_bid = DAILY_SALARY * 0.75

    # Adjust if yesterday's bids were extreme
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 0.9:
            # Opponents aggressive, stay competitive but not excessive
            base_bid = max(base_bid, DAILY_SALARY * 0.65)
        elif max_prev < DAILY_SALARY * 0.3:
            # Opponents cautious, we can be conservative
            base_bid = min(base_bid, DAILY_SALARY * 0.4)

    # HP emergency: if very low, bid high
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    if hp == 0:
        # Desperate
        base_bid = min(budget, DAILY_SALARY * 1.0)

    # Ensure we don't spend more than budget
    bid = min(base_bid, budget)
    # Minimum bid to have a chance
    bid = max(bid, 1.0)

    return int(bid)
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
    salary = 140
    req = 8
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Desperate if HP low
    if hp <= 2:
        bid = min(budget, salary * 0.9)
    else:
        if yesterday_bids:
            avg_prev = sum(yesterday_bids) / len(yesterday_bids)
            bid = min(budget, avg_prev + 2)
        else:
            bid = min(budget, salary * 0.4)
    return max(0, min(budget, bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.5  # default moderate

    if hp <= 2 or no_water_days >= 2:
        # Need water urgently
        base_bid = DAILY_SALARY * 0.9
    elif yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.86:  # ~120
            if hp > 4:
                base_bid = DAILY_SALARY * 0.3
            else:
                base_bid = DAILY_SALARY * 0.8
        else:
            base_bid = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
    else:
        # No history, play safe
        base_bid = DAILY_SALARY * 0.55

    # Ensure bid does not exceed budget and is non-negative
    bid = min(budget, base_bid)
    return max(int(bid), 0)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    # Determine target bid based on yesterday's max
    if yesterday_bids:
        target = max(yesterday_bids) + 2.0
    else:
        target = DAILY_SALARY * 0.6  # default
    # Adjust based on my HP
    hp = my_status['hp']
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.7)
    else:
        target = min(target, DAILY_SALARY * 0.7)
    # Ensure within budget
    bid = min(target, my_status['budget'])
    # Ensure non-negative
    bid = max(0.0, bid)
    return bid
"""
