# ============================================================
# Experiment: exp_015
# Agent: David
# Source: exp_015
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share = supply / num_agents; base_bid = min(my_status['budget'], fair_share * 1.2); if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], max(base_bid, 15.0))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        target_bid = max_prev + 2.0
    else:
        target_bid = DAILY_SALARY * 0.8
        
    if my_status['hp'] < 3:
        target_bid = DAILY_SALARY * 0.95
        
    return float(min(my_status['budget'], target_bid))
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
        return float(min(my_status['budget'], 20.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] < 3:
        target_bid = min(my_status['budget'], avg_opp_bid * 1.1)
    else:
        target_bid = min(my_status['budget'], avg_opp_bid * 0.95)
        
    return float(max(10.0, target_bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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

    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], avg_bid * 1.2)
    else:
        bid = min(my_status['budget'], max(40.0, avg_bid * 0.9))
        
    return float(bid)
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
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_prev * 1.2)
    elif day_context['supply'] < 18:
        bid = min(my_status['budget'], avg_prev * 1.1)
    else:
        bid = min(my_status['budget'], avg_prev * 0.9)
        
    return max(10.0, float(bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max(avg_opp_bid * 1.1, DAILY_SALARY * 0.9))
    
    target_bid = min(my_status['budget'], avg_opp_bid * 0.95)
    return max(target_bid, DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if my_status['budget'] < 50: return min(my_status['budget'], 15.0); return min(my_status['budget'], max(avg_prev * 1.05, 35.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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
        return min(my_status['budget'], 20.0)
        
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < 18.0:
        return min(my_status['budget'], avg_prev_bid + 5.0)
        
    return min(my_status['budget'], avg_prev_bid * 0.8)
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.6
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    if day_context['supply'] < WATER_REQ * 2:
        return min(my_status['budget'], avg_prev * 1.05)
    return min(my_status['budget'], avg_prev * 0.95)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_opp_bid * 1.1)
    
    if day_context['supply'] < WATER_REQ * 2:
        return min(my_status['budget'], avg_opp_bid * 1.05)
        
    return min(my_status['budget'], avg_opp_bid * 0.95)
"""
