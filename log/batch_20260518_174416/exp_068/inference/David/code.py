# ============================================================
# Experiment: exp_068
# Agent: David
# Source: exp_068
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share_bid = (day_context['supply'] / num_agents) * 1.2; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], fair_share_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(bids) if bids else 0; if supply < WATER_REQ * 2: bid = max_prev + 5.0; else: bid = min(max_prev * 0.8, 40.0); return min(my_status['budget'], max(10.0, bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); max_prev = max(yesterday_bids) if yesterday_bids else 0; if my_status['hp'] <= 3: return min(my_status['budget'], max(max_prev + 5.0, 85.0)); if day_context['supply'] < 18: return min(my_status['budget'], max(max_prev + 2.0, 65.0)); return min(my_status['budget'], 55.0)
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
            
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
        
    max_prev = max(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max(max_prev + 5.0, 75.0)))
        
    if supply < (len(alive_opponents) + 1) * WATER_REQ:
        return float(min(my_status['budget'], max_prev + 2.0))
        
    return float(min(my_status['budget'], max(40.0, max_prev * 0.95)))
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
    
    max_prev = max(yesterday_bids) if yesterday_bids else 40
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], max_prev + 5)
    
    if supply >= 20:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    if supply < 15:
        return min(my_status['budget'], max_prev + 2)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev * 0.9))
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if day_context['supply'] < 18:
            return min(my_status['budget'], max_prev + 2.0)
        return min(my_status['budget'], max(30.0, max_prev * 0.6))

    return min(my_status['budget'], 45.0)
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
        return float(min(my_status['budget'], 20.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0
    
    if my_status['hp'] <= 5:
        bid = min(my_status['budget'], avg_opp_bid * 1.15)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.95)
        
    return float(max(10.0, min(bid, DAILY_SALARY * 1.2)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; target_bid = 0; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); target_bid = avg_bid * 0.95; else: target_bid = DAILY_SALARY * 0.6; if my_status['hp'] <= 3: target_bid = min(my_status['budget'], DAILY_SALARY * 1.2); return float(min(my_status['budget'], max(10.0, target_bid)))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    highest_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if supply < 18:
        return min(my_status['budget'], highest_prev + 5.0)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev * 0.9))
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
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    if supply < WATER_REQ * 1.5:
        bid = min(my_status['budget'], avg_prev_bid * 1.1)
    elif supply < WATER_REQ * 2.5:
        bid = min(my_status['budget'], avg_prev_bid * 0.9)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.6)
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    return float(max(1.0, bid))
"""
