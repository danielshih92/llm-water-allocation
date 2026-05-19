# ============================================================
# Experiment: exp_048
# Agent: David
# Source: exp_048
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); fair_share = DAILY_SALARY / (num_opponents + 1); if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], fair_share * 1.2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply < 18: return min(my_status['budget'], max(avg_prev_bid + 2.0, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_prev_bid * 0.8, DAILY_SALARY * 0.3))
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
    num_agents = len(alive_opponents) + 1
    fair_share = supply / num_agents
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_prev * 1.1)
    
    if fair_share >= WATER_REQ:
        return min(my_status['budget'], avg_prev * 0.8)
    
    return min(my_status['budget'], avg_prev * 1.05)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < WATER_REQ * 1.5: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.9)
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    base_bid = avg_opp_bid * 1.05
    if supply < 18:
        bid = min(my_status['budget'], max(base_bid, 110.0))
    elif supply > 22:
        bid = min(my_status['budget'], max(base_bid * 0.7, 60.0))
    else:
        bid = min(my_status['budget'], base_bid)
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], max(bid, 120.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 120; if supply < 18: return min(my_status['budget'], max(avg_opp_bid * 1.05, 130)); if my_status['hp'] < 4: return min(my_status['budget'], 150); return min(my_status['budget'], max(80, avg_opp_bid * 0.8))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 75
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < 18:
        return min(my_status['budget'], max_prev + 2.0)
    elif supply > 22:
        return min(my_status['budget'], DAILY_SALARY * 0.85)
    else:
        return min(my_status['budget'], max(DAILY_SALARY * 0.9, max_prev + 0.5))
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
        return 1.0
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 90.0))
    else:
        bid = min(my_status['budget'], avg_prev * 1.02)
        
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], avg_prev * 1.1); if supply > 22: return min(my_status['budget'], avg_prev * 0.8); return min(my_status['budget'], avg_prev)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    max_prev = max(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, 70.0))
    
    return min(my_status['budget'], max(avg_prev * 0.9, 45.0))
"""
