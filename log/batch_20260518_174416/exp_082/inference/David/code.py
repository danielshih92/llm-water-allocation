# ============================================================
# Experiment: exp_082
# Agent: David
# Source: exp_082
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_opp_bid + 5.0)
    
    if supply < 18:
        return min(my_status['budget'], avg_opp_bid + 2.0)
    elif supply > 22:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    else:
        return min(my_status['budget'], avg_opp_bid - 2.0)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return min(my_status['budget'], 10.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < WATER_REQ + 2: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.8)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and 'bid' in prev: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.95)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max(highest_prev_bid * 1.1, 40.0))
        return min(my_status['budget'], max(highest_prev_bid * 0.9, 25.0))

    if my_status['hp'] <= 2:
        return min(my_status['budget'], 60.0)
    return min(my_status['budget'], 35.0)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 1.2:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        return min(my_status['budget'], max_prev + 2.0)
        
    return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):    DAILY_SALARY = 80    supply = day_context['supply']    alive_opponents = [o for o in opponents_status.values() if o['alive']]    if not alive_opponents:        return min(my_status['budget'], 10.0)    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100.0    if my_status['hp'] <= 3:        return min(my_status['budget'], DAILY_SALARY * 1.5)    if supply > 22:        return min(my_status['budget'], avg_prev * 0.8)    if supply < 18:        return min(my_status['budget'], avg_prev * 1.1)    return min(my_status['budget'], avg_prev * 1.05)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY; if my_status['hp'] < 4: return min(my_status['budget'], max(DAILY_SALARY * 1.2, avg_prev * 1.05)); if supply < 18: return min(my_status['budget'], max(DAILY_SALARY * 1.1, avg_prev * 1.02)); return min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_prev * 0.9))
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    if yesterday_bids and max(yesterday_bids) > 85:
        return min(my_status['budget'], 86.0)
    return min(my_status['budget'], max(40.0, avg_bid + 2.0))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 1.2))
    bid = avg_prev * 1.05
    return float(min(my_status['budget'], max(bid, DAILY_SALARY * 0.6)))
"""
