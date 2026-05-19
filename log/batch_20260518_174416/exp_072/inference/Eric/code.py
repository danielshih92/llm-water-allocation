# ============================================================
# Experiment: exp_072
# Agent: Eric
# Source: exp_072
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)
    hp = my_status['hp']
    budget = my_status['budget']
    if hp > 5:
        base_bid = DAILY_SALARY * 0.4
    else:
        base_bid = DAILY_SALARY * 0.7
    bid = min(budget, base_bid)
    return int(bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    base_bid = DAILY_SALARY * (WATER_REQ / supply)
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    urgent = (hp <= 2) or (no_water_days >= 1)
    if urgent:
        target_bid = max(base_bid * 1.5, max_prev_bid + 5)
    else:
        target_bid = base_bid
        if max_prev_bid > target_bid * 1.2:
            target_bid = max_prev_bid * 0.9
    bid = min(budget, max(1, int(target_bid)))
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
    no_water_days = my_status['no_water_days']
    
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Estimate competitive price based on supply scarcity
    scarcity_factor = max(0, (20 - supply) / 10)  # 0 when supply>=20, 1 when supply=10, clamp
    base_bid = min(budget, DAILY_SALARY * (0.5 + 0.4 * scarcity_factor))
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If yesterday was high, we need to raise or stay safe
        if hp <= 2 or no_water_days >= 1:
            target = max(base_bid, highest_prev + 5)
        else:
            target = max(base_bid, highest_prev * 0.95)
    else:
        # No trace, just base
        target = base_bid
    
    # Ensure not overpay if budget limited
    bid = min(budget, max(1, target))
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Determine base bid from opponent history if available
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = avg_prev + 5.0
    else:
        target = 115.0
    
    # Adjust based on urgency
    if hp <= 3:
        target = max(target, 130.0)
    if no_water_days >= 2:
        target = max(target, 135.0)
    
    # Ensure bid stays within budget and non-negative
    bid = min(budget, max(0.0, target))
    return round(bid, 2)
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
    
    my_hp = int(my_status['hp'])
    my_budget = my_status['budget']
    no_water_days = int(my_status['no_water_days'])
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents) + 1  # include myself
    
    # Determine opponent yesterday bids from trace
    opp_prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            opp_prev_bids.append(float(prev['bid']))
    
    # Base bid: try to get water at reasonable price
    # Supply per person roughly
    supply_per_person = supply / num_alive if num_alive > 0 else supply
    # My water need: 8
    # If supply_per_person >= 8, average bid can be lower; otherwise needs higher
    base_bid = DAILY_SALARY * 0.45
    if supply_per_person < WATER_REQ:
        base_bid = DAILY_SALARY * 0.6
    
    # Urgency based on my HP and no_water_days
    if my_hp <= 2 or no_water_days >= 1:
        urgent_bid = min(my_budget, DAILY_SALARY * 0.9)
        return int(urgent_bid)
    
    # Adapt to opponent yesterday bids: if they bid high, we may need to match
    if opp_prev_bids:
        max_prev = max(opp_prev_bids)
        avg_prev = sum(opp_prev_bids) / len(opp_prev_bids)
        # If they are bidding high, we might need to increase
        if max_prev > DAILY_SALARY * 0.8:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
        # If average is high, be cautious
        if avg_prev > DAILY_SALARY * 0.6:
            base_bid = min(base_bid, DAILY_SALARY * 0.65)
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.55)
    
    # Ensure bid is within budget and at least 1
    bid = min(my_budget, max(1.0, base_bid))
    return int(bid)
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
    DAILY_SALARY = 140
    WATER_REQ = 8
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid based on hp
    if hp <= 2:
        base_bid = DAILY_SALARY * 1.0
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif hp <= 6:
        base_bid = DAILY_SALARY * 0.5
    else:
        base_bid = DAILY_SALARY * 0.3

    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If base is too low, raise to beat previous
        if base_bid < highest_prev + 5:
            base_bid = highest_prev + 5

    # Adjust for supply scarcity
    if supply <= 18:
        base_bid *= 1.2

    # Ensure not exceed budget and non-negative
    bid = min(budget, max(0, base_bid))

    # Final sanity: if hp is 0 or budget is 0, bid 0
    if my_status['hp'] <= 0:
        bid = 0

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

    # Determine expected opponent bid
    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
    else:
        avg_opp_bid = 130  # default guess based on Cindy's avg

    # Base target: survive with minimal cost
    if hp <= 3:
        # Need water, bid strongly but not overpay
        target = min(budget, max(DAILY_SALARY * 0.95, avg_opp_bid + 1.0))
    elif no_water_days > 0:
        # Already missed water, bid to get it
        target = min(budget, max(DAILY_SALARY * 0.85, avg_opp_bid + 0.5))
    else:
        # Healthy, can save: bid low but competitive
        target = min(budget, max(DAILY_SALARY * 0.4, avg_opp_bid - 5.0))

    # Ensure bid is within reasonable range (0 to budget)
    bid = max(0.0, min(budget, target))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine bid based on health and water need
    bid = DAILY_SALARY * 0.5  # base bid
    
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
        bid = DAILY_SALARY * 0.9  # desperate
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.7
    
    # React to opponents' previous high bids
    high_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > 150:
                high_bids.append(prev['bid'])
    
    if high_bids:
        # If someone bid very high last time, they may do so again; bid moderately to compete only if desperate
        if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
            bid = max(bid, DAILY_SALARY * 0.85)
        else:
            # Let them waste budget
            bid = min(bid, DAILY_SALARY * 0.4)
    
    # Ensure we don't exceed budget
    bid = min(bid, my_status['budget'])
    # Ensure positive bid
    bid = max(bid, 1)
    return bid
"""
