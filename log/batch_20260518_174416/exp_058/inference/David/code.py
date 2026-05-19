# ============================================================
# Experiment: exp_058
# Agent: David
# Source: exp_058
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    # Calculate fair share based on supply
    fair_share_bid = (DAILY_SALARY * 0.5) if (supply / (num_opponents + 1)) >= WATER_REQ else (DAILY_SALARY * 0.75)
    
    # Emergency survival
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    return min(my_status['budget'], fair_share_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); target_bid = avg_prev * 1.05; if day_context['supply'] < 18: target_bid += 10; return min(my_status['budget'], max(DAILY_SALARY * 0.5, target_bid))
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
            
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(DAILY_SALARY * 1.2, avg_bid + 5))
    else:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_bid * 0.9))
        
    return float(bid)
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
        return min(my_status['budget'], 10.0)
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 20.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_bid * 1.2, 50.0))
    
    return min(my_status['budget'], max(avg_bid * 0.9, 15.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50
    
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] > 8:
        bid = min(my_status['budget'], DAILY_SALARY * 0.4)
    else:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev * 1.05))
        
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return 1.0
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not yesterday_bids:
        return float(DAILY_SALARY * 0.4)
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_opp_bid * 1.1)
    
    if supply < 18.0:
        return min(my_status['budget'], avg_opp_bid * 0.8)
    
    return min(my_status['budget'], DAILY_SALARY * 0.3)
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
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if supply < 18:
        return min(my_status['budget'], max(avg_prev + 2.0, DAILY_SALARY * 0.8))
    
    return min(my_status['budget'], max(avg_prev * 0.95, DAILY_SALARY * 0.6))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20); avg_opp_budget = sum(o['budget'] for o in alive_opponents) / len(alive_opponents) if alive_opponents else 0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if day_context['supply'] < 18: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], DAILY_SALARY * 0.45)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; target_bid = avg_prev * 1.05; if my_status['hp'] < 4: target_bid *= 1.5; return float(min(my_status['budget'], max(target_bid, 25.0)))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.1, 95.0))
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.95, 60.0))
    return float(bid)
"""
