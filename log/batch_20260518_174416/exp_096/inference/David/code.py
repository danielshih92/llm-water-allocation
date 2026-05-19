# ============================================================
# Experiment: exp_096
# Agent: David
# Source: exp_096
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); fair_share = day_context['supply'] / (num_opponents + 1); if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); if fair_share > WATER_REQ: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if supply < WATER_REQ * 1.5: return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.8)); if my_status['hp'] < 5: return min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.4))
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
    num_active = len(alive_opponents) + 1
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.1, 95))
    elif supply < 18:
        bid = min(my_status['budget'], max(avg_prev_bid, 85))
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.9)
        
    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):    DAILY_SALARY = 80    WATER_REQ = 7    supply = day_context['supply']    alive_opponents = [o for o in opponents_status.values() if o['alive']]    avg_prev_bid = 0    if alive_opponents:        bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]        if bids:            avg_prev_bid = sum(bids) / len(bids)    if my_status['hp'] < 4:        return min(my_status['budget'], 120.0)    if supply < 18:        return min(my_status['budget'], 110.0)    if avg_prev_bid > 100:        return min(my_status['budget'], avg_prev_bid * 0.95)    return min(my_status['budget'], 85.0)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 50)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100
    target_bid = min(my_status['budget'], max(105, avg_opp_bid + 5))
    if my_status['hp'] < 4:
        return min(my_status['budget'], 150)
    return target_bid
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

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(avg_prev * 1.2, 60.0))
    
    bid = min(my_status['budget'], avg_prev * 1.05)
    return max(10.0, bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] <= 5:
        bid = min(my_status['budget'], max(avg_bid * 1.1, 75.0))
    else:
        bid = min(my_status['budget'], max(avg_bid * 0.9, 45.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev * 1.05))
        return target

    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev * 1.2)
        
    return min(my_status['budget'], max(40.0, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
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
    
    avg_bid = (avg_opp_bid / count) if count > 0 else 100.0
    
    if supply < 18.0:
        bid = avg_bid * 1.1
    elif supply < 22.0:
        bid = avg_bid * 0.9
    else:
        bid = avg_bid * 0.7
        
    if my_status['hp'] < 4:
        bid = max(bid, 130.0)
        
    return min(my_status['budget'], float(bid))
"""
