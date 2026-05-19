# ============================================================
# Experiment: exp_119
# Agent: David
# Source: exp_119
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); fair_share = supply / (num_opponents + 1); if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.85); if num_opponents == 0: return min(my_status['budget'], DAILY_SALARY * 0.2); avg_prev_bid = 0; if num_opponents > 0: bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if bids: avg_prev_bid = sum(bids) / len(bids); bid = avg_prev_bid * 1.05 if avg_prev_bid > 0 else DAILY_SALARY * 0.4; return min(my_status['budget'], max(bid, DAILY_SALARY * 0.35))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
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
        bid = avg_prev * 1.2
    elif my_status['hp'] > 8:
        bid = avg_prev * 0.8
    else:
        bid = avg_prev * 1.05

    return float(min(my_status['budget'], max(10.0, bid)))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); supply = day_context['supply']; target_bid = 55.0; if supply < 18: target_bid = 75.0; elif supply > 22: target_bid = 35.0; if my_status['hp'] < 4: target_bid = min(my_status['budget'], 85.0); return float(min(my_status['budget'], target_bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20)
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], int(DAILY_SALARY * 0.95))
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 0.9:
            return min(my_status['budget'], int(DAILY_SALARY * 0.95))
        return min(my_status['budget'], int(max_prev * 1.05))
        
    return min(my_status['budget'], int(DAILY_SALARY * 0.85))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 160.0)
        
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, 120.0))
    elif supply < 22:
        return min(my_status['budget'], max(avg_prev * 0.9, 85.0))
    else:
        return min(my_status['budget'], max(avg_prev * 0.7, 40.0))
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

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if day_context['supply'] < WATER_REQ * 1.5:
        return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.8))
        
    return min(my_status['budget'], avg_prev * 0.95)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50
    target_bid = avg_prev * 1.05

    if my_status['hp'] <= 3:
        target_bid = max(target_bid, DAILY_SALARY * 0.8)
    
    if my_status['hp'] >= 8:
        target_bid = min(target_bid, DAILY_SALARY * 0.4)

    return float(min(my_status['budget'], max(0, target_bid)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(bids) / len(bids) if bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if my_status['hp'] > 7: return min(my_status['budget'], avg_bid * 0.8); return min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_bid * 1.05))
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    max_prev = max(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max_prev * 1.1))
        
    if supply < 18:
        return float(min(my_status['budget'], max(max_prev * 0.95, DAILY_SALARY * 0.7)))
    
    return float(min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.8)))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_market_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 100.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_market_bid * 1.1, 150.0))
    elif day_context['supply'] < 18:
        bid = min(my_status['budget'], avg_market_bid * 1.05)
    else:
        bid = min(my_status['budget'], avg_market_bid * 0.9)
        
    return float(max(bid, 5.0))
"""
