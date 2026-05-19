# ============================================================
# Experiment: exp_044
# Agent: David
# Source: exp_044
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.4; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], max(DAILY_SALARY * 0.45, avg_bid + 2.0))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 10.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] < 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if supply > 20:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    if supply < 18:
        return min(my_status['budget'], avg_opp_bid * 1.05)
    return min(my_status['budget'], avg_opp_bid * 0.9)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return 0; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev + 5, 85)); return min(my_status['budget'], max(avg_prev * 0.6, 40))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(bids) / len(bids) if bids else DAILY_SALARY; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev_bid + 5, DAILY_SALARY * 0.95)); return min(my_status['budget'], max(avg_prev_bid * 0.8, DAILY_SALARY * 0.6))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        bid = DAILY_SALARY * 0.7
    else:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        if supply < 18:
            bid = min(my_status['budget'], max(avg_prev + 5, DAILY_SALARY * 1.1))
        else:
            bid = min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.6))
            
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
        
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = supply / num_players; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], 120.0); if supply < WATER_REQ * 1.2: return min(my_status['budget'], 95.0); target_bid = max(avg_prev * 0.95, 65.0); return min(my_status['budget'], target_bid)
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
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    elif supply < 18:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.1, DAILY_SALARY * 0.8))
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.9, DAILY_SALARY * 0.5))
        
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 85.0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and 'bid' in prev: avg_bid = (avg_bid + prev['bid']) / 2; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], avg_bid + 5.0); return min(my_status['budget'], avg_bid * 0.7)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)
        
    max_prev = max(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max_prev * 1.05)
    else:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev * 0.9))
        
    return float(max(1.0, bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); target_bid = min(DAILY_SALARY * 1.1, avg_prev * 1.05); return float(min(my_status['budget'], max(25.0, target_bid)))
"""
