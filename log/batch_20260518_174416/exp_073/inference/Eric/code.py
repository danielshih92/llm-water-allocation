# ============================================================
# Experiment: exp_073
# Agent: Eric
# Source: exp_073
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    previous_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            previous_bids.append(trace['bid'])
    if no_water_days >= 2 or hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    if supply < 20:
        base_bid = min(base_bid * 1.2, DAILY_SALARY * 0.95)
    if previous_bids:
        max_prev = max(previous_bids)
        if max_prev > base_bid:
            base_bid = max_prev + 1.5
    bid = min(budget, base_bid)
    bid = max(bid, 1)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    water_req = 8
    daily_salary = 140
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday = max(yesterday_bids) if yesterday_bids else 0
    avg_yesterday = sum(yesterday_bids)/len(yesterday_bids) if yesterday_bids else 0

    # Base bid depending on HP
    if hp <= 2:
        # desperate: bid high to secure water
        bid = daily_salary * 0.95
    elif hp <= 4:
        # moderate need: bid around average if supply tight, else conservatively
        if supply < 20:
            bid = max(daily_salary * 0.7, avg_yesterday + 10)
        else:
            bid = daily_salary * 0.7
    else:
        # healthy: conserve budget
        if day >= 8 and budget < daily_salary * 2:
            bid = daily_salary * 0.3
        else:
            # outbid only if max yesterday was very high and supply low
            if max_yesterday > daily_salary * 0.9 and supply < 18:
                bid = min(daily_salary * 0.95, max_yesterday + 5)
            else:
                bid = daily_salary * 0.55

    # Ensure bid does not exceed budget
    bid = min(bid, budget)
    # Also ensure non-negative
    bid = max(bid, 0)
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    budget = my_status['budget']
    hp = my_status['hp']
    no_water =
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    day = day_context['day']
    supply = day_context['supply']
    if hp <= 2 or day > 7:
        if prev_bids:
            target = max(prev_bids) + 0.5
        else:
            target = DAILY_SALARY * 0.9
        bid = max(DAILY_SALARY * 0.5, target)
    elif hp <= 5:
        if prev_bids:
            target = max(prev_bids) + 0.2
        else:
            target = DAILY_SALARY * 0.7
        bid = min(target, DAILY_SALARY * 0.8)
    else:
        if prev_bids and max(prev_bids) > DAILY_SALARY * 0.7:
            bid = DAILY_S
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    import math
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    yesterday_bids = []
    for oid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
    else:
        avg_yesterday = DAILY_SALARY * 0.5  # default
    
    need_water = (no_water_days > 0) or (hp <= 2)
    moderate_need = (hp <= 4) and not need_water
    
    if need_water:
        target_bid = max(avg_yesterday + 5, DAILY_SALARY * 0.7)
    elif moderate_need:
        target_bid = max(avg_yesterday - 2, DAILY_SALARY * 0.4)
    else:
        target_bid = avg_yesterday * 0.5
        target_bid = min(target_bid, DAILY_SALARY * 0.6)
    
    # Ensure within budget and non-negative
    bid = min(budget, target_bid)
    bid = max(0, bid)
    # If budget is very low, bid all
    if budget < DAILY_SALARY * 0.3 and need_water:
        bid = budget
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']

    # Desperate if low HP or already suffering water shortage
    desperate = (hp <= 3) or (no_water_days > 0)

    # Scarcity factor: lower supply means water more valuable
    scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1

    if desperate:
        # Must secure water: outbid highest opponent by a small margin
        target = max(DAILY_SALARY * 0.9, highest_prev_bid + 2.0 + scarcity * 10)
        bid = min(budget, target)
    else:
        # Conservative: stay slightly below highest opponent if possible, but not too low
        target = max(DAILY_SALARY * 0.4, highest_prev_bid - 5.0 - scarcity * 5)
        bid = min(budget, target)

    # Ensure bid does not exceed salary (rational limit)
    bid = min(bid, DAILY_SALARY)
    # Ensure non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    MIN_SUPPLY = 15
    MAX_SU
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Collect yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest bid from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # My urgency indicators
    hp = my_status['hp']
    no_water = my_status['no_water_days']

    # Decide base bid
    if hp <= 3 or no_water >= 1:
        # Desperate: need water badly
        base = highest_prev_bid + 5.0
    elif hp <= 5:
        # Moderate caution
        base = highest_prev_bid + 2.0
    else:
        # Healthy: save budget
        base = highest_prev_bid - 5.0 if highest_prev_bid > 20 else highest_prev_bid + 1.0

    # Ensure bid stays within budget and reasonable bounds
    bid = max(base, DAILY_SALARY * 0.1)
    bid = min(bid, my_status['budget'], DAILY_SALARY * 0.9)

    # If budget is very low, just bid all but a tiny reserve
    if my_status['budget'] < DAILY_SALARY * 0.2:
        bid = my_status['budget'] * 0.9

    return bid
"""
