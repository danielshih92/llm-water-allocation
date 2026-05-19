# ============================================================
# Experiment: exp_001
# Agent: David
# Source: exp_001
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = DAILY_SALARY / num_players; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], fair_share * 1.1)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], avg_opp_bid * 1.15)
    elif my_status['hp'] <= 6:
        bid = min(my_status['budget'], avg_opp_bid * 1.05)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.95)
        
    return max(0.0, float(bid))
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

    yesterday_bids = [opp.get('previous_trace', {}).get('bid', 0) for opp in alive_opponents if opp.get('previous_trace')]
    max_prev = max(yesterday_bids) if yesterday_bids else 80

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.15)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(95.0, max_prev * 1.05))
        
    return min(my_status['budget'], max(85.0, max_prev * 0.95))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return min(my_status['budget'], 10.0)
        
    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_bid * 1.05
    else:
        target_bid = DAILY_SALARY * 0.4
        
    if my_status['hp'] < 3:
        target_bid = min(my_status['budget'], DAILY_SALARY * 0.8)
        
    return min(my_status['budget'], float(target_bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_prev = sum(bids) / len(bids) if bids else 80; target = avg_prev * 1.05 if my_status['hp'] < 4 else avg_prev * 0.95; return min(my_status['budget'], max(50, target))
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
        return min(my_status['budget'], 10.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_opp_bid * 1.1)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.95)
        
    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0; bid = avg_prev * 0.95; if my_status['hp'] <= 5: bid = avg_prev * 1.05; return min(my_status['budget'], max(bid, 40.0))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    bid = min(my_status['budget'], avg_prev * 1.05)
    return max(bid, 45.0)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace:
            prev_bids.append(trace['bid'])
            
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
        
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 75.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(85.0, avg_prev * 1.05))
    elif my_status['hp'] >= 8:
        bid = min(my_status['budget'], max(60.0, avg_prev * 0.8))
    else:
        bid = min(my_status['budget'], max(75.0, avg_prev))
        
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev_bid * 1.1, 130.0)); if my_status['hp'] <= 6: return min(my_status['budget'], max(avg_prev_bid * 1.05, 110.0)); return min(my_status['budget'], max(avg_prev_bid * 0.95, 90.0))
"""
