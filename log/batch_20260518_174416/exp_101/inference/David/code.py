# ============================================================
# Experiment: exp_101
# Agent: David
# Source: exp_101
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); fair_share = DAILY_SALARY / (num_opponents + 1); if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], fair_share * 1.2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if not yesterday_bids: return 40.0; max_prev = max(yesterday_bids); if my_status['hp'] < 4: return min(my_status['budget'], max_prev + 5.0); return min(my_status['budget'], max(42.0, min(max_prev + 2.0, 65.0)))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        return float(min(my_status['budget'], avg_prev * 1.2 + 10.0))
    
    if supply > 20:
        return float(min(my_status['budget'], avg_prev * 0.8))
    
    return float(min(my_status['budget'], avg_prev * 1.05))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev * 1.2, 60.0))
    elif my_status['hp'] >= 8:
        bid = min(my_status['budget'], max(avg_prev * 0.8, 30.0))
    else:
        bid = min(my_status['budget'], avg_prev * 1.05)
        
    return float(bid)
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_prev * 1.2, 60.0))
    elif my_status['hp'] > 8:
        bid = min(my_status['budget'], avg_prev * 0.8)
    else:
        bid = min(my_status['budget'], avg_prev * 1.05)
        
    return float(bid)
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        bid = avg_prev_bid * 1.05
        if my_status['hp'] <= 3:
            bid = max(bid, DAILY_SALARY * 0.8)
    else:
        bid = DAILY_SALARY * 0.6
    return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev * 1.2); if supply < WATER_REQ * 2: return min(my_status['budget'], max_prev * 1.05); return min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.8))
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

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 70.0
    max_prev_bid = max(prev_bids) if prev_bids else 80.0

    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max_prev_bid * 1.15)
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.95, 65.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev * 1.1, 50)); return min(my_status['budget'], max(avg_prev * 0.8, 30))
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
        return min(my_status['budget'], 10.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    bid = avg_prev * 1.05
    if day_context['supply'] < WATER_REQ * 2:
        bid = max(bid, DAILY_SALARY * 0.95)
    return min(my_status['budget'], float(bid))
"""
