# ============================================================
# Experiment: exp_110
# Agent: David
# Source: exp_110
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
    
    # Basic fair share heuristic for day 1
    target_bid = DAILY_SALARY * 0.5
    
    # If supply is tight, bid more aggressively
    if supply < (num_opponents + 1) * WATER_REQ:
        target_bid = DAILY_SALARY * 0.75
        
    return float(min(my_status['budget'], target_bid))
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

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = min(my_status['budget'], avg_prev * 1.05)
        return max(target, 25.0)

    return min(my_status['budget'], 40.0)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], avg_prev + 5.0)
        if avg_prev > DAILY_SALARY * 1.2:
            return min(my_status['budget'], DAILY_SALARY * 0.6)
        return min(my_status['budget'], avg_prev * 0.95)
    return min(my_status['budget'], DAILY_SALARY * 0.7)
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
        return min(my_status['budget'], 20.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = avg_prev * 1.05
    else:
        target = DAILY_SALARY * 0.6
        
    if my_status['hp'] <= 3:
        return min(my_status['budget'], target * 1.5)
    return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 1.2))
    if my_status['hp'] > 8:
        return float(min(my_status['budget'], avg_prev * 0.8))
    return float(min(my_status['budget'], avg_prev * 1.05))
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
    
    # Cindy is the main competition, prioritize survival if HP is low
    cindy_bid = 0
    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('previous_trace'):
        cindy_bid = opponents_status['Cindy']['previous_trace'].get('bid', 80)

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(85.0, cindy_bid * 1.05))
    
    # Standard bidding strategy
    if supply / (len(alive_opponents) + 1) < WATER_REQ:
        return min(my_status['budget'], max(60.0, cindy_bid * 0.8))
    
    return min(my_status['budget'], 45.0)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): 
    DAILY_SALARY = 80 
    WATER_REQ = 7 
    supply = day_context['supply'] 
    alive_opponents = [o for o in opponents_status.values() if o['alive']] 
    
    if not alive_opponents: 
        return 1.0 
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None] 
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0 
    
    if my_status['hp'] < 3: 
        return min(my_status['budget'], DAILY_SALARY * 1.2) 
    
    if supply < 18: 
        return min(my_status['budget'], max(avg_prev * 1.1, 85.0)) 
    
    return min(my_status['budget'], max(avg_prev * 0.9, 40.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        target = min(my_status['budget'], avg_bid * 1.05)
        return max(target, DAILY_SALARY * 0.6)
        
    return min(my_status['budget'], DAILY_SALARY * 0.75)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 50.0
    
    # Scarcity adjustment: if supply is low, bid higher
    scarcity_factor = 1.0 if supply > 20 else 1.5
    
    # Base bid strategy: target a bit above average or previous max
    bid = min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.95 * scarcity_factor))
    
    # Emergency mode if HP is low
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(prev_bids) if prev_bids else 0; if my_status['hp'] <= 3: return min(my_status['budget'], max(DAILY_SALARY * 1.2, max_prev + 5)); if max_prev > DAILY_SALARY * 1.1: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], max(DAILY_SALARY * 0.8, max_prev * 0.9))
"""
