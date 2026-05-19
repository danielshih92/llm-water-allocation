# ============================================================
# Experiment: exp_006
# Agent: David
# Source: exp_006
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    # Estimate fair share if supply is shared equally
    fair_share = supply / (num_opponents + 1)
    
    # If supply is high, bid moderately. If low, bid aggressively to survive.
    if supply >= (num_opponents + 1) * WATER_REQ:
        bid = DAILY_SALARY * 0.4
    else:
        bid = DAILY_SALARY * 0.7
        
    return min(my_status['budget'], float(bid))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 75.0))
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.95, 45.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if supply < WATER_REQ * len(alive_opponents) + 2: return min(my_status['budget'], max(avg_prev + 2, 45)); return min(my_status['budget'], max(35, avg_prev * 0.6))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 50); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: avg_prev = sum(yesterday_bids) / len(yesterday_bids); if my_status['hp'] < 4: return min(my_status['budget'], max(avg_prev + 5, 105)); return min(my_status['budget'], max(90, avg_prev - 10)); return min(my_status['budget'], 95)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); cindy = opponents_status.get('Cindy'); if cindy and cindy['alive']: cindy_prev = cindy.get('previous_trace', {}); cindy_bid = cindy_prev.get('bid', 80.0) if cindy_prev else 80.0; if my_status['hp'] < 5: return min(my_status['budget'], cindy_bid + 5.0); return min(my_status['budget'], cindy_bid * 0.6); if my_status['hp'] < 3: return min(my_status['budget'], 90.0); return min(my_status['budget'], 55.0)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev * 1.1, 75)); return min(my_status['budget'], max(avg_prev * 0.95, 65))
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
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
            
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    avg_prev_bid = sum(prev_bids) / len(prev_bids)
    max_prev_bid = max(prev_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev_bid + 5.0)
    
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], max_prev_bid * 1.1)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev_bid * 0.9))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], max(85.0, avg_prev * 1.1)); target_bid = min(my_status['budget'], avg_prev * 0.95); return max(40.0, target_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    avg_opp_bid = 0
    count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_opp_bid += prev['bid']
            count += 1
    
    avg_bid = (avg_opp_bid / count) if count > 0 else 40.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_bid * 1.2)
    
    if supply < 18:
        return min(my_status['budget'], avg_bid * 1.05)
        
    return min(my_status['budget'], max(20.0, avg_bid * 0.8))
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
        return float(min(my_status['budget'], 10.0))
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.9))
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev < supply * 2:
            return float(min(my_status['budget'], max_prev + 2.0))
            
    return float(min(my_status['budget'], supply * 1.5))
"""
