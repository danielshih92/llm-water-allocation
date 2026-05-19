# ============================================================
# Experiment: exp_057
# Agent: Eric
# Source: exp_057
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    max_bid = my_status['budget']
    my_hp = my_status['hp']
    my_no_water = my_status['no_water_days']
    
    if my_hp <= 2 or my_no_water > 0:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.4
    
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if alive_opps:
        max_desperation = 0
        for opp in alive_opps:
            opp_hp = opp['hp']
            opp_no_water = opp['no_water_days']
            desperation = (WATER_REQ - opp_hp) * 10 + opp_no_water * 20
            if desperation > max_desperation:
                max_desperation = desperation
        if max_desperation > 20:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
        if max_desperation > 40:
            base_bid = DAILY_SALARY * 0.95
    return min(max_bid, base_bid)
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
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's highest bid among all opponents (alive or not, but trace exists)
    yesterday_bids = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Urgency: if no water yesterday, must win today
    urgent = (no_water_days >= 1) or (hp <= 2)
    
    # Base bid: we need to win water. If urgent, bid high; else bid conservatively.
    if urgent:
        target_bid = max(DAILY_SALARY * 0.9, highest_yesterday + 1.0)
    else:
        # if supply high enough, we can afford to be cheap
        max_players = 5  # including us
        # estimate total water needed by all
        if supply >= WATER_REQ * max_players:
            target_bid = DAILY_SALARY * 0.3
        else:
            target_bid = max(DAILY_SALARY * 0.5, highest_yesterday + 0.5)
    
    # Cap by budget and daily salary
    bid = min(budget, target_bid, DAILY_SALARY * 1.0)
    # Ensure non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Base bid: 55% of salary
    bid = DAILY_SALARY * 0.55
    
    # Desperation based on hp and no_water_days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.8
    if my_status['no_water
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid: if low HP, bid higher
    if my_hp <= 3:
        base_bid = DAILY_SALARY * 0.85
    elif my_hp <= 5:
        base_bid = DAILY_SALARY * 0.6
    else:
        base_bid = DAILY_SALARY * 0.4
    
    # Adjust based on opponent history
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
        if avg_prev > DAILY_SALARY * 0.7:
            # Opponents aggressive, match or slightly beat avg
            base_bid = min(base_bid, avg_prev * 1.05)
        else:
            # Opponents moderate, bid enough to beat max among moderate
            if max_prev < DAILY_SALARY * 0.6:
                base_bid = max(base_bid, max_prev + 2)
    
    # Ensure within budget and reasonable
    bid = min(my_budget, max(base_bid, DAILY_SALARY * 0.1))
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        bid = min(my_status['budget'], DAILY_SALARY * 0.4)
        return int(round(bid))
    
    # Gather yesterday's bids from traces
    last_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev:
            last_bids.append(prev['bid'])
    
    # Base bid: if we have recent bids, aim slightly above average
    if last_bids:
        avg_last = sum(last_bids) / len(last_bids)
        target = avg_last + 5.0   # small edge
    else:
        target = DAILY_SALARY * 0.55  # default moderate
    
    # Adjust based on health and water needs
    if my_status['no_water_days'] > 0:
        target = max(target, DAILY_SALARY * 0.85)
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.95)
    
    # Caps and constraints
    max_bid = min(my_status['budget'], DAILY_SALARY)
    bid = min(max_bid, max(target, 1.0))
    return int(round(bid))
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
    no_water_days = my_status['no_water_days']
    # Determine base bid
    if hp <= 2:
        base_bid = min(budget, DAILY_SALARY * 0.95)
    elif no_water_days >= 1 or hp <= 4:
        base_bid = min(budget, DAILY_SALARY * 0.75)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.55)
    # Adjust based on opponents' yesterday highest bid
    max_prev_bid = 0
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    # If they were very aggressive, stay moderate
    if max_prev_bid > DAILY_SALARY * 0.85:
        if hp > 4:
            base_bid = min(budget, DAILY_SALARY * 0.35)
        else:
            base_bid = min(budget, DAILY_SALARY * 0.7)
    # Ensure we don't go bust
    if budget < DAILY_SALARY * 0.3:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    return float(int(base_bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure int
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Collect yesterday bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Determine bid
    if hp <= 2:
        # desperate - bid high to ensure water
        bid = min(budget, DAILY_SALARY * 0.95)
    elif supply < 20:
        # low supply - need to compete
        if prev_bids:
            avg_prev = sum(prev_bids) / len(prev_bids)
            bid = min(budget, max(DAILY_SALARY * 0.8, avg_prev + 2.0))
        else:
            bid = min(budget, DAILY_SALARY * 0.85)
    else:
        # high supply - can save budget
        if prev_bids:
            avg_prev = sum(prev_bids) / len(prev_bids)
            bid = min(budget, max(DAILY_SALARY * 0.4, avg_prev + 1.0))
        else:
            bid = min(budget, DAILY_SALARY * 0.5)

    # Ensure we don't exceed budget or go negative
    bid = max(0.0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Base aggressive bid against expected high bidders
    base_bid = 130.0
    
    # Increase bid if supply is scarce
    if supply <= 18.0:
        base_bid = min(base_bid + 10.0, 145.0)
    
    # Urgent need if hp low
    if hp <= 2:
        bid = min(budget, 140.0)
    elif hp <= 4:
        bid = min(budget, base_bid + 5.0)
    else:
        bid = min(budget, base_bid)
    
    # Ensure we don't bid more than budget
    return float(min(budget, max(0.0, bid)))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        bid_target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.0)
    else:
        bid_target = DAILY_SALARY * 0.5
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    return min(my_status['budget'], bid_target)
"""
