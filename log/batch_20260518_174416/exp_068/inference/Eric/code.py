# ============================================================
# Experiment: exp_068
# Agent: Eric
# Source: exp_068
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
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
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
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
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                yesterday_bids.append(prev['bid'])
    
    high_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # supply-based aggressiveness
    if supply <= 18:
        target_bid = max(high_bid + 1, DAILY_SALARY * 0.7)
    elif supply >= 22:
        target_bid = min(DAILY_SALARY * 0.4, high_bid - 5 if high_bid > 0 else DAILY_SALARY * 0.3)
    else:
        if hp <= 3:
            target_bid = max(high_bid + 1, DAILY_SALARY * 0.6)
        else:
            target_bid = min(DAILY_SALARY * 0.5, high_bid - 2 if high_bid > 0 else DAILY_SALARY * 0.4)
    
    bid = min(budget, max(0, target_bid))
    return round(bid, 2)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    max_winners = supply // WATER_REQ
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v.get('alive', False)}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine aggressiveness based on supply and my health
    if max_winners == 1:
        # Very competitive: need top bid
        target_bid = DAILY_SALARY * 0.85
        if hp <= 3 or my_status['no_water_days'] >= 2:
            target_bid = DAILY_SALARY * 0.95
    elif max_winners == 2:
        target_bid = DAILY_SALARY * 0.65
        if hp <= 3 or my_status['no_water_days'] >= 2:
            target_bid = DAILY_SALARY * 0.8
    else:
        # max_winners >=3
        target_bid = DAILY_SALARY * 0.5
        if hp <= 3 or my_status['no_water_days'] >= 2:
            target_bid = DAILY_SALARY * 0.7
    
    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
        median_yesterday = sorted(yesterday_bids)[len(yesterday_bids)//2]
        # If yesterday's high was very high, we might need to match or exceed
        if highest_yesterday > target_bid:
            # Need to outbid if we have budget
            target_bid = max(target_bid, highest_yesterday + 1.0)
        else:
            # If we are already above median, we can be more conservative
            if target_bid > median_yesterday * 1.2:
                target_bid = max(DAILY_SALARY * 0.4, median_yesterday * 1.1)
    
    # Budget constraint: ensure we don't bid more than we have
    target_bid = min(target_bid, budget * 0.95) if budget > 0 else 0
    # Ensure positive bid
    target_bid = max(1, target_bid)
    
    return target_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids)/len(yesterday_bids) if yesterday_bids else 0.0
    
    # Urgency: low HP or no water for 2+ days
    is_desperate = (hp <= 2) or (no_water_days >= 2)
    
    if is_desperate:
        # Bid high to survive
        target_bid = min(budget, DAILY_SALARY * 0.9)  # up to 126
    else:
        # Normal day: balance competition and conservation
        # Base bid: half salary, but can increase if opponents were aggressive yesterday
        base = DAILY_SALARY * 0.5  # 70
        if max_prev_bid > 0:
            # Aim to slightly beat yesterday's max, but cap at 75% salary
            competitive = min(max_prev_bid + 1.0, DAILY_SALARY * 0.75)  # cap 105
            target_bid = min(budget, max(base, competitive))
        else:
            target_bid = min(budget, base)
    
    # Also reduce bid if we have good HP and budget to preserve for later
    if hp > 5 and target_bid > DAILY_SALARY * 0.5:
        target_bid = DAILY_SALARY * 0.5
    
    # Ensure not negative and not above budget
    return max(0.0, min(budget, target_bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    alive_opp = {k:v for k,v in opponents_status.items() if v['alive']}
    if not alive_opp:
        return min(budget, SALARY * 0.4)
    prev_bids = []
    for opp in alive_opp.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    if prev_bids:
        highest_prev = max(prev_bids)
        target = highest_prev + 1.5
    else:
        target = SALARY * 0.6
    if hp <= 2 or no_water > 0:
        base = max(target, SALARY * 0.8)
        max_bid = min(budget, SALARY * 1.0)
    else:
        base = target
        max_bid = min(budget, SALARY * 0.85)
    bid = min(budget, base)
    bid = min(bid, max_bid)
    if supply < 18:
        bid = max(bid, SALARY * 0.7)
    return float(min(bid, budget))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.2)
    
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    else:
        max_prev = 0.0
        avg_prev = 0.0
    
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
        if max_prev > 0 and bid <= max_prev:
            bid = min(budget, max_prev + 1)
        return bid
    elif hp <= 5:
        target = max_prev + 5 if max_prev > 0 else DAILY_SALARY * 0.5
        bid = min(budget, target)
        bid = min(bid, DAILY_SALARY * 0.95)
        bid = max(bid, DAILY_SALARY * 0.1)
        return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])

    # Base bid: if we are dehydrated, bid high; else moderate
    if hp <= 3 or no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.9
    else:
        base_bid = DAILY_SALARY * 0.5

    # Adjust based on yesterday's pressure
    bid = base_bid
    if yesterday_max_bid > 0:
        # If we need water, outbid yesterday's max by a small margin
        if hp <= 3 or no_water_days >= 1:
            bid = max(bid, yesterday_max_bid + 5.0)
        else:
            # If we are healthy, bid slightly above average
            bid = max(bid, yesterday_max_bid * 0.7)

    # Supply adjustment: if supply is low, bid higher
    if supply < 18:
        bid = max(bid, DAILY_SALARY * 0.6)

    # Final bound: not more than budget, not more than salary * 1.1
    bid = min(bid, budget)
    bid = min(bid, DAILY_SALARY * 1.1)
    bid = max(bid, 1.0)
    return int(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""
