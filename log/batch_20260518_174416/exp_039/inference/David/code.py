# ============================================================
# Experiment: exp_039
# Agent: David
# Source: exp_039
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 25.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); if my_status['hp'] < 3: return min(my_status['budget'], max(avg_bid * 1.1, 40.0)); return min(my_status['budget'], max(avg_bid * 0.9, 20.0)); return min(my_status['budget'], 25.0)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] < 4: return min(my_status['budget'], max_prev + 5); if supply / (len(alive_opponents) + 1) >= WATER_REQ: return min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.8)); return min(my_status['budget'], max_prev + 2)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 95.0)
    
    if supply < 18:
        return min(my_status['budget'], max(75.0, avg_prev_bid + 5.0))
    
    return min(my_status['budget'], max(45.0, avg_prev_bid * 0.9))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 120.0)
        
    if supply < 18:
        return min(my_status['budget'], 110.0)
        
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > 100:
            return min(my_status['budget'], max_prev + 2.0)
        return min(my_status['budget'], 85.0)
        
    return min(my_status['budget'], 80.0)
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
        return min(my_status['budget'], 40.0)
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = min(avg_prev * 1.05, DAILY_SALARY * 0.75)
        return min(my_status['budget'], max(target, 45.0))
    
    return min(my_status['budget'], 55.0)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.1, 50.0)); return min(my_status['budget'], max(avg_prev * 0.8, 30.0))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(max_prev + 5.0, 60.0))
    
    if max_prev > 50:
        return min(my_status['budget'], 55.0)
        
    return min(my_status['budget'], max(35.0, max_prev + 2.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; if yesterday_bids: highest_prev_bid = max(yesterday_bids); if my_status['hp'] < 4: return min(my_status['budget'], max(highest_prev_bid + 2.0, DAILY_SALARY * 0.8)); if day_context['supply'] < 18: return min(my_status['budget'], highest_prev_bid + 1.0); return min(my_status['budget'], max(DAILY_SALARY * 0.5, min(yesterday_bids) + 1.0)); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; if not alive_opps: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opps if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; target = avg_prev * 1.05; if my_status['hp'] < 4: target = max(target, DAILY_SALARY * 0.9); if supply < 18: target *= 1.2; return min(my_status['budget'], float(target))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    max_prev = max(yesterday_bids)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
        
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, 75.0))
        
    return min(my_status['budget'], max(avg_prev, 60.0))
"""
