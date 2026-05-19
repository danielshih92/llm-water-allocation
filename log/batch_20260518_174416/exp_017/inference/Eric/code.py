# ============================================================
# Experiment: exp_017
# Agent: Eric
# Source: exp_017
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            base = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
            return min(my_status['budget'], base)
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    SALARY = 140
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opp = {k:v for k,v in opponents_status.items() if v['alive']}
    
    # Get yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opp.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    # Estimate opponent's likely bid today based on yesterday
    # Cindy: high, David: moderate. Use average of previous bids as proxy.
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        median_prev = sorted(prev_bids)[len(prev_bids)//2]
        # Assume they will bid similarly; we want to slightly undercut if possible
        target = avg_prev * 0.95
    else:
        target = SALARY * 0.6  # default first day

    # Adjust based on supply and needs
    if supply < 15:
        target = max(target, SALARY * 0.8)
    
    # Desperation: if no water days or low hp
    if no_water >= 2 or hp <= 3:
        target = min(budget, SALARY * 0.95, max(target, 10))
    else:
        # Conservative when healthy
        if hp > 6:
            target = min(target, SALARY * 0.5)
        else:
            target = min(target, SALARY * 0.75)

    bid = max(1.0, min(budget, target))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    WATER_REQ = 8
    SALARY = 140
    max_winners = supply // WATER_REQ
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    base = SALARY * 0.5
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if hp <= 2 or no_water >= 1:
            target = min(budget, max(max_prev + 1, SALARY * 0.9))
        else:
            target = min(budget, max(base, max_prev * 0.9))
    else:
        if hp <= 2 or no_water >= 1:
            target = min(budget, SALARY * 0.9)
        else:
            target = min(budget, base)
    return max(target, 0)
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
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    # Estimate required water units (exact integer)
    water_units = int(supply // WATER_REQ)
    # Need water if no_water_days >= 2 or hp <= 3
    desperate = (no_water_days >= 2) or (hp <= 3)
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Base bid
    if not yesterday_bids:
        # No history, conservative
        if desperate:
            base = min(budget, DAILY_SALARY * 0.8)
        else:
            base = min(budget, DAILY_SALARY * 0.3)
    else:
        max_prev = max(yesterday_bids)
        if desperate:
            # Need water, but don't overpay much more than necessary
            # If others are high, match slightly above
            if max_prev > DAILY_SALARY * 0.5:
                base = min(budget, max_prev + 1.0)
            else:
                base = min(budget, DAILY_SALARY * 0.8)
        else:
            # Not desperate: undercut if possible, or just safe
            if max_prev > DAILY_SALARY * 0.7:
                # Avoid bidding war
                base = min(budget, DAILY_SALARY * 0.3)
            else:
                # Try to win cheaply
                base = min(budget, max(DAILY_SALARY * 0.2, max_prev - 2.0))
    # Ensure non-negative
    bid = max(0.0, base)
    # Extra: if supply is abundant (>=20) and we are not desperate, bid very low to save money
    if supply >= 20 and not desperate:
        bid = min(bid, 5.0)
    # If David is alive and likely bids 0, we can try 1.0 to win if water units >= alive count
    alive_count = len(alive_opponents) + 1  # including self
    if 'David' in alive_opponents and water_units >= alive_count and not desperate:
        bid = min(bid, 1.0)
    # Cap at budget
    return min(budget, bid)
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for o in alive_opponents.values():
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: if low HP, go high
    if hp <= 2 or no_water_days >= 1:
        target_bid = min(budget, DAILY_SALARY * 0.9)  # up to 126
    else:
        # Determine a competitive bid based on yesterday's max
        if yesterday_bids:
            max_prev_bid = max(yesterday_bids)
            # If we have HP buffer, try to outbid modestly
            if hp > 5:
                target_bid = min(budget, max(DAILY_SALARY * 0.4, max_prev_bid + 2.0))
            else:
                target_bid = min(budget, max(DAILY_SALARY * 0.6, max_prev_bid + 3.0))
        else:
            # No history, bid a conservative fraction
            target_bid = min(budget, DAILY_SALARY * 0.5)

    # Ensure we never exceed budget
    bid = max(0, min(target_bid, budget))
    # Prevent float index errors elsewhere (not needed here)
    return bid
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
    water_req = 8
    salary = 140
    alive = {k:v for k,v in opponents_status.items() if v['alive']}
    if not alive:
        return min(budget, salary * 0.4)
    # Estimate opponent bids from yesterday
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    # Determine maximum previous bid among alive opponents
    max_prev = max(prev_bids) if prev_bids else 0
    # Determine safe bid: need to win water if supply is limited
    # Reserve enough for remaining days if possible
    remaining_days = 10 - day
    daily_need = water_req * 1.0  # we need at least water_req units
    # Base bid: fraction of salary
    base_bid = salary * 0.45
    # Adjust based on HP
    if hp <= 2:
        # Desperate: bid to ensure water, possibly exceed opponent
        target = max(base_bid, max_prev + 1) if prev_bids else base_bid * 1.5
        return min(budget, target)
    elif hp <= 4:
        # Moderate risk
        target = base_bid * 1.3
        return min(budget, target)
    else:
        # Healthy: save budget, only bid enough if competition low
        if prev_bids and max_prev > salary * 0.7:
            # Opponents aggressive, stay competitive
            target = max(base_bid, max_prev * 0.85)
            return min(budget, target)
        else:
            return min(budget, base_bid * 0.8)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = int(day_context['supply'])  # ensure integer for floor division
    day = day_context['day']
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    # Number of alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine base bid from supply and requirement
    max_units = supply // WATER_REQ  # at least 1
    # If many units, less competition; if few, more conservative
    
    # Look at yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Adaptive bid strategy based on yesterday's highest bid
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
        # If someone bid very high yesterday, they might be desperate now
        if highest_yesterday > DAILY_SALARY * 0.8:
            # They might go even higher; we can conserve unless low hp
            if my_hp <= 2:
                bid = min(my_budget, DAILY_SALARY * 0.7)
            else:
                bid = min(my_budget, DAILY_SALARY * 0.4)
        else:
            # Moderate competition: slightly above average of yesterday bids
            avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
            bid = min(my_budget, max(avg_yesterday + 2, DAILY_SALARY * 0.35))
    else:
        # No history - conservative bid
        if my_hp <= 3:
            bid = min(my_budget, DAILY_SALARY * 0.75)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.5)
    
    # Ensure bid is at least 0, and not more than budget
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    # Get yesterday's highest bid from alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0

    # Base bid: slightly above yesterday's highest, with floor 60% of salary
    base_bid = max(DAILY_SALARY * 0.6, highest_yesterday + 2)

    # HP urgency
    hp = my_status['hp']
    if hp <= 3:
        base_bid *= 1.3
    if my_status['no_water_days'] > 0:
        base_bid *= 1.2

    # Cap by budget and a safety limit (90% of salary max)
    max_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    bid = int(min(base_bid, max_bid))

    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    HP = my_status['hp']
    budget = my_status['budget']
    
    alive_opp = [o for o in opponents_status.values() if o['alive']]
    
    max_yesterday_bid = None
    for opp in alive_opp:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            bid = trace['bid']
            if max_yesterday_bid is None or bid > max_yesterday_bid:
                max_yesterday_bid = bid
    
    # If no previous data, use default
    if max_yesterday_bid is None:
        if HP <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.7)
    
    # If we are desperate (low HP)
    if HP <= 2:
        target = max(DAILY_SALARY * 0.9, max_yesterday_bid + 1.0)
        return min(budget, target)
    
    # Normal: try to outbid yesterday's highest by a small margin
    base = max(DAILY_SALARY * 0.6, max_yesterday_bid + 0.5)
    # If supply is low, increase slightly
    if supply <= 17:
        base = max(base, DAILY_SALARY * 0.75)
    return min(budget, base)
"""
