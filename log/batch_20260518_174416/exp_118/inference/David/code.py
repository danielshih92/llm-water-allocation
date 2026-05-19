# ============================================================
# Experiment: exp_118
# Agent: David
# Source: exp_118
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); fair_share_bid = DAILY_SALARY / (num_opponents + 1); if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], max(fair_share_bid * 1.2, 25.0))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if supply < 18: return min(my_status['budget'], max(avg_prev + 5.0, 75.0)); if my_status['hp'] < 4: return min(my_status['budget'], 70.0); return min(my_status['budget'], max(avg_prev - 5.0, 40.0))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 50); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 88; target = avg_prev + 2.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); return min(my_status['budget'], target)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
        
    max_prev = max(yesterday_bids)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(max_prev * 1.05, DAILY_SALARY * 1.2))
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 1.1))
        
    return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.8))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20); avg_prev_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid'): avg_prev_bid += prev['bid']; count += 1; if count > 0: avg_prev_bid /= count; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply > 22: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev_bid * 0.8))
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
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 120.0)
        
    if supply < 18:
        return min(my_status['budget'], max(85.0, avg_prev_bid + 5.0))
    
    if supply >= 22:
        return min(my_status['budget'], 40.0)
        
    return min(my_status['budget'], max(60.0, avg_prev_bid * 0.9))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):    DAILY_SALARY = 80    WATER_REQ = 7    alive_opponents = [o for o in opponents_status.values() if o['alive']]    if not alive_opponents:        return min(my_status['budget'], 10)    yesterday_bids = []    for opp in alive_opponents:        prev = opp.get('previous_trace', {})        if prev and prev.get('bid') is not None:            yesterday_bids.append(prev['bid'])    if yesterday_bids:        avg_bid = sum(yesterday_bids) / len(yesterday_bids)        target = min(my_status['budget'], avg_bid * 0.8)    else:        target = DAILY_SALARY * 0.5    if my_status['hp'] < 5:        target = min(my_status['budget'], target * 1.5)    return float(max(10.0, min(my_status['budget'], target)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev * 1.2); if supply < 18: return min(my_status['budget'], max(max_prev + 5, 50)); return min(my_status['budget'], max(max_prev * 0.8, 30))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(bids) / len(bids) if bids else 75; target = min(my_status['budget'], max(avg_bid * 1.05, 85)); if my_status['hp'] < 4: return min(my_status['budget'], 110); return target
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive = [o for o in opponents_status.values() if o['alive']]; if not alive: return min(my_status['budget'], 10.0); bids = [o['previous_trace']['bid'] for o in alive if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(bids) / len(bids) if bids else 20.0; target = avg_bid * 1.1 if my_status['hp'] < 5 else avg_bid * 0.95; return min(my_status['budget'], max(15.0, target))
"""
