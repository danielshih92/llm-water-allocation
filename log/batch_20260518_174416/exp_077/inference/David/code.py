# ============================================================
# Experiment: exp_077
# Agent: David
# Source: exp_077
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.95); if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); if supply < 18: return min(my_status['budget'], max(avg_bid * 1.1, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_bid * 0.8, DAILY_SALARY * 0.3)); return min(my_status['budget'], DAILY_SALARY * 0.45)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_bid * 1.1, 75.0))
    return min(my_status['budget'], max(avg_bid * 0.9, 40.0))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.05)
    if day_context['supply'] < 18:
        return min(my_status['budget'], max_prev * 0.95)
    return min(my_status['budget'], max(60.0, max_prev * 0.8))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply / (len(alive_opponents) + 1) >= WATER_REQ: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.05, 75.0)); return min(my_status['budget'], max(avg_prev * 0.9, 65.0))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 150.0)
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev_bid + 5.0, 90.0))
    
    return min(my_status['budget'], max(avg_prev_bid * 0.8, 60.0))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    max_prev = max(yesterday_bids) if yesterday_bids else 80.0

    if my_status['hp'] < 4:
        return min(my_status['budget'], max_prev + 5.0)
    
    if day_context['supply'] < WATER_REQ * (len(alive_opponents) + 1):
        return min(my_status['budget'], max_prev + 2.0)

    return min(my_status['budget'], max(avg_bid * 0.9, 30.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); highest_prev_bid = max(yesterday_bids) if yesterday_bids else 100; if my_status['hp'] <= 3: return min(my_status['budget'], highest_prev_bid * 1.1 + 5); if day_context['supply'] < 20: return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid * 0.95)); return min(my_status['budget'], DAILY_SALARY * 0.6)
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
        return min(my_status['budget'], 20)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = min(avg_prev * 1.1, DAILY_SALARY * 0.8)
        return min(my_status['budget'], max(target, 45))
        
    return min(my_status['budget'], 50)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev_bid * 1.2)
    
    if supply < 18:
        return min(my_status['budget'], avg_prev_bid * 1.05)
    
    if supply > 22:
        return min(my_status['budget'], avg_prev_bid * 0.7)
        
    return min(my_status['budget'], avg_prev_bid * 0.9)
"""
