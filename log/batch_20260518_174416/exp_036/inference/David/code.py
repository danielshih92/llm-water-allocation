# ============================================================
# Experiment: exp_036
# Agent: David
# Source: exp_036
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 15.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 20.0; if my_status['hp'] < 3: return min(my_status['budget'], max(avg_bid * 1.2, 30.0)); return min(my_status['budget'], max(avg_bid * 0.9, 15.0))
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max_prev + 5.0)
        return min(my_status['budget'], max(85.0, max_prev * 0.95))

    return min(my_status['budget'], 82.0)
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0

    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_prev_bid * 1.1)

    if supply < 18:
        return min(my_status['budget'], avg_prev_bid * 1.05)

    return min(my_status['budget'], max(20.0, avg_prev_bid * 0.6))
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
        return float(min(my_status['budget'], 20.0))
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 2:
        return float(min(my_status['budget'], max_prev * 1.2 + 5.0))
    
    if day_context['supply'] < 18.0:
        return float(min(my_status['budget'], max_prev * 1.05))
    else:
        return float(min(my_status['budget'], max(30.0, max_prev * 0.8)))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and 'bid' in prev: avg_bid += prev['bid']; count += 1; if count > 0: avg_bid /= count; else: avg_bid = 75; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_bid * 1.05, 85)); if supply > 22: return min(my_status['budget'], max(avg_bid * 0.8, 60)); return min(my_status['budget'], max(avg_bid, 75))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    avg_prev = sum(prev_bids) / len(prev_bids)
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if supply < 20:
        return min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.7))
    
    return min(my_status['budget'], max(avg_prev * 0.95, DAILY_SALARY * 0.5))
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if supply < 16:
        bid = avg_prev_bid * 1.1
    elif supply > 20:
        bid = avg_prev_bid * 0.6
    else:
        bid = avg_prev_bid * 0.9
        
    if my_status['hp'] < 4:
        bid = max(bid, 75.0)
        
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if day_context['supply'] < WATER_REQ * 1.5: return min(my_status['budget'], avg_prev + 5); return min(my_status['budget'], DAILY_SALARY * 0.45)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10))

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 1.2))
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 1.5:
            return float(min(my_status['budget'], DAILY_SALARY * 0.4))
        return float(min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev + 2.0)))
        
    return float(min(my_status['budget'], DAILY_SALARY * 0.75))
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
        return float(min(my_status['budget'], DAILY_SALARY * 0.3))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.5
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif day_context['supply'] < WATER_REQ * 1.5:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev_bid * 1.1))
    else:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev_bid * 0.9))
        
    return float(bid)
"""
