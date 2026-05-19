# ============================================================
# Experiment: exp_066
# Agent: David
# Source: exp_066
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
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    base_bid = DAILY_SALARY * 0.4
    if num_opponents > 0:
        if supply < (WATER_REQ * (num_opponents + 1)):
            return min(my_status['budget'], DAILY_SALARY * 0.7)
            
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [opp.get('previous_trace', {}).get('bid', 0) for opp in alive_opponents if opp.get('previous_trace')]; avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 20: return min(my_status['budget'], max(DAILY_SALARY * 0.7, avg_opp_bid + 5)); return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_opp_bid * 0.9))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    # Aggressive if low HP, otherwise balanced
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.2, 100.0))
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.95, 75.0))
        
    return float(bid)
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
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    # Strategy: If HP is low, bid aggressively. Otherwise, bid slightly above market average.
    if my_status['hp'] <= 3:
        target_bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    else:
        target_bid = min(my_status['budget'], max(avg_opp_bid * 0.95, DAILY_SALARY * 0.65))
        
    return float(target_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev + 5); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], max_prev + 2); return min(my_status['budget'], max(40, max_prev * 0.95))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    # Aggressive bidding if supply is low, conservative if high
    if supply < 18:
        bid = min(my_status['budget'], max(avg_opp_bid * 1.05, 90.0))
    elif supply > 22:
        bid = min(my_status['budget'], 40.0)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.95)
        
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.5)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.7
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if my_status['hp'] >= 8:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    return min(my_status['budget'], avg_bid * 1.05)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY; target_bid = min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_prev * 0.85)); if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.5); return target_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], avg_bid * 1.1); return min(my_status['budget'], max(40, avg_bid * 0.95))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return min(my_status['budget'], 10.0)
        
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_opp_bid * 1.1, 75.0))
    elif supply < 18:
        bid = min(my_status['budget'], avg_opp_bid + 5.0)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.8)
        
    return float(max(0, bid))
"""
