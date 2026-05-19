# ============================================================
# Experiment: exp_038
# Agent: David
# Source: exp_038
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 25.0))

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if prev_bids:
        max_prev = max(prev_bids)
        if my_status['hp'] < 4:
            return float(min(my_status['budget'], max_prev + 5.0))
        return float(min(my_status['budget'], max(30.0, max_prev * 0.9)))

    return float(min(my_status['budget'], 35.0))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; active_count = len(alive_opponents) + 1; fair_share = supply / active_count; bid = DAILY_SALARY * 0.45; if my_status['hp'] <= 3: bid = min(my_status['budget'], DAILY_SALARY * 0.85); elif fair_share < WATER_REQ: bid = min(my_status['budget'], DAILY_SALARY * 0.65); else: bid = min(my_status['budget'], DAILY_SALARY * 0.4); for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid'): bid = max(bid, prev['bid'] * 0.95); return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(avg_prev * 1.1, 75.0))
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev, 60.0))
    
    return min(my_status['budget'], max(avg_prev * 0.8, 30.0))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            prev_bids.append(prev['bid'])
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < 20:
        return min(my_status['budget'], avg_prev * 1.05)
    else:
        return min(my_status['budget'], max(20.0, avg_prev * 0.7))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    max_prev = max(yesterday_bids)
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max_prev * 1.05)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max_prev * 0.95)
        
    return min(my_status['budget'], avg_prev * 0.9)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_prev * 1.05, 60.0))
    
    return min(my_status['budget'], max(avg_prev * 0.9, 45.0))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
            
    max_prev = max(prev_bids) if prev_bids else 50
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
    
    if supply < 18:
        return min(my_status['budget'], max(max_prev + 2.0, 65.0))
    
    return min(my_status['budget'], 55.0)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 130.0)
    
    if supply < 20:
        return min(my_status['budget'], max(90.0, avg_prev + 5.0))
    
    return min(my_status['budget'], max(75.0, avg_prev * 0.95))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    elif supply < 18:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.05, DAILY_SALARY * 0.8))
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.9, DAILY_SALARY * 0.6))
        
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    avg_opp_bid = 0
    count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_opp_bid += prev['bid']
            count += 1
    
    avg_bid = (avg_opp_bid / count) if count > 0 else 60.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(avg_bid * 1.1, DAILY_SALARY * 0.9))
    
    if supply < 18:
        return min(my_status['budget'], max(avg_bid * 1.05, DAILY_SALARY * 0.7))
        
    return min(my_status['budget'], max(avg_bid * 0.9, DAILY_SALARY * 0.5))
"""
