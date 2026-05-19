# ============================================================
# Experiment: exp_103
# Agent: David
# Source: exp_103
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share_bid = (supply / num_agents) * 5; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], max(20, fair_share_bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and 'bid' in prev: yesterday_bids.append(prev['bid']); aggressive_threshold = 100.0; if yesterday_bids and max(yesterday_bids) > aggressive_threshold: if my_status['hp'] < 5: return min(my_status['budget'], 130.0); return min(my_status['budget'], 40.0); bid = 65.0; if my_status['hp'] < 4: bid = 95.0; elif my_status['hp'] > 8: bid = 55.0; return min(my_status['budget'], float(bid))
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
    
    # Calculate competitive pressure from yesterday
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 50
    
    # Survival priority
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(max_prev_bid + 5, 90))
    
    # Supply-based bidding
    if supply < 18:
        return min(my_status['budget'], max(max_prev_bid, 75))
    elif supply > 22:
        return min(my_status['budget'], max(max_prev_bid * 0.7, 40))
    else:
        return min(my_status['budget'], max(max_prev_bid * 0.9, 55))
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
        return float(min(my_status['budget'], 40.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 75.0))
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.9, 45.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    avg_bids = []
    for opp in alive_opponents:
        if 'previous_trace' in opp and opp['previous_trace'].get('bid') is not None:
            avg_bids.append(opp['previous_trace']['bid'])
    
    avg_market_bid = sum(avg_bids) / len(avg_bids) if avg_bids else 70.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_market_bid * 1.2, 95.0))
    else:
        bid = min(my_status['budget'], max(avg_market_bid * 0.9, 65.0))
        
    return float(bid)
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
        return min(my_status['budget'], 50.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], avg_prev * 1.2)
    else:
        bid = min(my_status['budget'], avg_prev * 0.95)
        
    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids)
    max_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1 + 5)
    
    if day_context['supply'] < WATER_REQ * 2:
        return min(my_status['budget'], max(avg_bid * 0.9, DAILY_SALARY * 0.5))
        
    return min(my_status['budget'], avg_bid * 0.85)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1 + 5)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max_prev + 2)
    
    return min(my_status['budget'], DAILY_SALARY * 0.6)
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] <= 3:
        bid = avg_prev_bid * 1.2
    else:
        bid = avg_prev_bid * 0.9
    return min(float(my_status['budget']), float(bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(prev_bids) if prev_bids else DAILY_SALARY; if my_status['hp'] <= 3: return min(my_status['budget'], max(max_prev * 1.1, DAILY_SALARY * 0.9)); if supply < WATER_REQ * 2: return min(my_status['budget'], max_prev * 1.05); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""
