# ============================================================
# Experiment: exp_102
# Agent: Eric
# Source: exp_102
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Decide base bid
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    else:
        if yesterday_bids:
            avg_bid = sum(yesterday_bids) / len(yesterday_bids)
            # If opponents were high, we can be conservative; else bid slightly above average
            if avg_bid >= DAILY_SALARY * 0.8:
                base_bid = max(DAILY_SALARY * 0.3, avg_bid * 0.85)
            else:
                base_bid = avg_bid * 1.15
        else:
            base_bid = DAILY_SALARY * 0.5
    # Adjust for supply: lower supply -> more competition, bid higher
    supply_factor = max(0.8, min(1.2, supply / 20.0))
    bid = base_bid * supply_factor
    # Ensure within budget and salary range
    bid = min(budget, bid)
    bid = max(1, bid)
    return int(bid)
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

    alive_opps = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opps.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_highest = sorted_bids[1] if len(sorted_bids) >= 2 else 0
    else:
        highest_prev = 0
        second_highest = 0

    my_hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']

    base_bid = max(second_highest + 0.5, DAILY_SALARY * 0.3)
    if my_hp <= 2 or no_water >= 1:
        base_bid = max(highest_prev + 1, DAILY_SALARY * 0.7)
    elif my_hp <= 4:
        base_bid = max(highest_prev + 0.5, DAILY_SALARY * 0.5)

    bid = min(budget, base_bid)
    bid = max(bid, 1)  # ensure positive
    return int(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    num_winners = int(supply // WATER_REQ)
    # Determine highest previous bid from alive opponents (if any)
    highest_prev = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            highest_prev = max(highest_prev, prev['bid'])
    # Base bid: ensure survival if low HP
    if hp < 3:
        base_bid = DAILY_SALARY * 0.9
    else:
        base_bid = DAILY_SALARY * 0.5
    # Adjust for number of winners and opponent tendencies
    if num_winners == 0:
        # unlikely but no water today? Then save budget
        bid = min(budget, base_bid * 0.5)
    elif num_winners == 1:
        # Only top bid wins; need to beat Cindy's likely 142.5
        bid = min(budget, max(base_bid, 143.0, highest_prev + 1.0))
    elif num_winners == 2:
        # Two winners: bid enough to be in top two
        bid = min(budget, max(base_bid, DAILY_SALARY * 0.7, highest_prev * 0.9))
    else:
        # Three winners: lower bid
        bid = min(budget, max(base_bid, DAILY_SALARY * 0.5, highest_prev * 0.7))
    # Ensure at least 1 to avoid floating point errors
    bid = max(1.0, bid)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        # If high HP, bid slightly below average to let others overpay
        if hp > 3:
            target = min(max_yesterday - 1, avg_yesterday * 0.9)
            bid = max(DAILY_SALARY * 0.3, target)
        else:
            # Low HP: need water, bid above max yesterday to guarantee win?
            bid = max_yesterday + 5
        # But never exceed budget or daily salary
        bid = min(budget, bid)
        bid = max(bid, 0.0)
        return bid
    
    # No trace: use conservative default
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.9)
    else:
        return min(budget, DAILY_SALARY * 0.4)
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
    
    # Alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    
    # Gather previous bids from alive opponents
    prev_bids = []
    for op in alive_opps:
        trace = op.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid decision
    base_bid = 0.5 * DAILY_SALARY  # default 70
    if prev_bids:
        # Highest previous bid among alive
        highest_prev = max(prev_bids)
        # I want to slightly outbid if necessary
        base_bid = min(highest_prev + 2, DAILY_SALARY * 0.95)
    
    # Adjust for own health
    if hp <= 2:
        # Desperate: bid high to guarantee water
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # Moderate desperation
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    
    # Cap by budget
    bid = min(base_bid, budget)
    
    # Ensure non-negative and return as float
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
        return min(budget, 0.4 * DAILY_SALARY)

    # Collect previous bids from opponents' traces
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(float(trace['bid']))

    # Base decision on previous highest conservative or moderate bid
    if prev_bids:
        # Conservative bidders likely repeat similar values
        conservative_bids = [b for b in prev_bids if b <= 0.6 * DAILY_SALARY]
        if conservative_bids:
            target = max(conservative_bids) + 1.5
        else:
            target = max(prev_bids) * 0.85 + 1.0
    else:
        target = 0.5 * DAILY_SALARY

    # Adjust based on water need
    if no_water_days > 0 or hp <= 3:
        target = max(target, 0.9 * DAILY_SALARY)
    elif hp >= 7:
        # Can afford to risk a bit less
        target = min(target, 0.5 * DAILY_SALARY)

    # Ensure bid is within reasonable bounds
    bid = min(budget, max(0.1 * DAILY_SALARY, target))
    # Round to avoid floating point quirks
    bid = round(bid, 2)
    return bid
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
    no_water_days = my_status['no_water_days']

    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive'] and opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None:
            yesterday_bids.append(opp['previous_trace']['bid'])

    if no_water_days >= 1:
        base = DAILY_SALARY * 0.9
    elif hp <= 2:
        base = DAILY_SALARY * 0.8
    elif hp <= 5:
        base = DAILY_SALARY * 0.6
    else:
        base = DAILY_SALARY * 0.4

    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        if max_yesterday > DAILY_SALARY * 0.85:
            if base < DAILY_SALARY * 0.6:
                base = DAILY_SALARY * 0.6
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        if avg_yesterday > DAILY_SALARY * 0.7:
            base = max(base, avg_yesterday * 0.8)

    bid = min(budget, base)
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    supply = day_context['supply']
    # base bid
    if my_status['hp'] <= 2:
        base = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.5

    # adjust based on yesterday's highest
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If they were very aggressive, lower to save budget
        if highest_prev >= DAILY_SALARY * 0.85:
            base = min(base, DAILY_SALARY * 0.3)
        else:
            # try to beat their average? but we'll bid just above highest_prev + small increment
            challenger = min(DAILY_SALARY * 0.95, highest_prev + 1.5)
            base = max(base, challenger)

    # Supply: if low supply, increase bid
    if supply < (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        base *= 1.2
    else:
        base *= 0.9

    # Cap by budget and max reasonable
    bid = min(my_status['budget'], base)
    bid = min(bid, DAILY_SALARY * 0.95)
    bid = max(bid, 1)
    return int(round(bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    
    # Determine highest previous bid (if any)
    highest_prev = max(prev_bids) if prev_bids else 0
    
    # Base bid calculation
    hp = my_status['hp']
    budget = my_status['budget']
    
    if hp <= 2:
        # Desperate - need water
        base_bid = min(budget, DAILY_SALARY * 0.8)
    elif hp >= 6:
        # Healthy - can conserve
        base_bid = min(budget, DAILY_SALARY * 0.4)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.55)
    
    # Adjust based on competition from yesterday
    if highest_prev > base_bid:
        # Opponents were aggressive, we need to bid slightly higher
        bid = min(budget, highest_prev + 1.0)
    else:
        bid = base_bid
    
    # Ensure non-negative and within budget
    bid = max(0, min(bid, budget))
    # Convert to int just in case, but Python allows float; however ensure no float index issues later
    # Note: Return as float as typical
    return bid
"""
