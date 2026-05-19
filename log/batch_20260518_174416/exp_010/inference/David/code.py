# ============================================================
# Experiment: exp_010
# Agent: David
# Source: exp_010
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): def get_bid(day_context, my_status, opponents_status):    WATER_REQ = 7    DAILY_SALARY = 80    supply = day_context['supply']    alive_opponents = [o for o in opponents_status.values() if o['alive']]    if not alive_opponents:        return min(my_status['budget'], 25.0)    yesterday_bids = []    for opp in alive_opponents:        prev = opp.get('previous_trace', {})        if prev and prev.get('bid') is not None:            yesterday_bids.append(prev['bid'])    if yesterday_bids:        avg_bid = sum(yesterday_bids) / len(yesterday_bids)        return min(my_status['budget'], avg_bid + 2.0)    return min(my_status['budget'], 28.0)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.1, 75.0))
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.9, 45.0))
        
    return float(bid)
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
    num_survivors = len(alive_opponents) + 1
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    max_prev = max(yesterday_bids)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    
    if supply / num_survivors >= WATER_REQ:
        return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev * 0.9))
    else:
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev + 2.0))
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

    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.6
    
    if supply < WATER_REQ * 1.5:
        bid = min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.9))
    elif supply < WATER_REQ * 2.5:
        bid = min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.55))
    else:
        bid = min(my_status['budget'], DAILY_SALARY * 0.35)
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.1)
        
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.9)); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.7)); return min(my_status['budget'], max(avg_prev * 0.95, DAILY_SALARY * 0.5))
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
        return 10
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 130
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], 160)
    elif supply < 18:
        bid = min(my_status['budget'], max(145, avg_opp_bid + 5))
    else:
        bid = min(my_status['budget'], max(135, avg_opp_bid - 5))
        
    return int(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 40.0)

    avg_opp_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_opp_bids.append(prev['bid'])
            
    market_pressure = sum(avg_opp_bids) / len(avg_opp_bids) if avg_opp_bids else 110.0
    
    # If supply is tight, bid aggressively to secure water
    if supply < 18:
        bid = market_pressure * 1.05
    else:
        bid = market_pressure * 0.95
        
    # Desperation logic
    if hp <= 3:
        bid = max(bid, 130.0)
        
    return min(budget, float(bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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
            
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        return float(min(my_status['budget'], DAILY_SALARY * 1.1))
    
    if day_context['supply'] < 18.0:
        return float(min(my_status['budget'], avg_bid * 1.1))
        
    return float(min(my_status['budget'], avg_bid * 0.95))
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
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
            
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 60
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 75))
    elif supply / (len(alive_opponents) + 1) < WATER_REQ:
        bid = min(my_status['budget'], max(avg_prev + 5, 80))
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.9, 45))
        
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.9)); return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.6))
"""
