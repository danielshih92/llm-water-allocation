# ============================================================
# Experiment: exp_037
# Agent: David
# Source: exp_037
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: highest_prev_bid = max(yesterday_bids); if highest_prev_bid > DAILY_SALARY * 0.6: return min(my_status['budget'], highest_prev_bid + 2); return min(my_status['budget'], DAILY_SALARY * 0.5); if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], DAILY_SALARY * 0.45)
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
        return min(my_status['budget'], 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(90.0, avg_prev + 5.0))
    else:
        bid = min(my_status['budget'], max(70.0, avg_prev * 0.95))
        
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        bid = DAILY_SALARY * 0.6
    else:
        avg_prev = sum(prev_bids) / len(prev_bids)
        bid = min(DAILY_SALARY * 1.2, avg_prev * 1.05)
        
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], DAILY_SALARY * 1.5)
        
    return float(min(my_status['budget'], max(bid, DAILY_SALARY * 0.4)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 3:
            return min(my_status['budget'], max_prev + 5.0)
        return min(my_status['budget'], max_prev + 1.0)
        
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.6; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev * 1.05))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; total_agents = len(alive_opponents) + 1; supply = day_context['supply']; target_bid = 85.0; if my_status['hp'] <= 3: target_bid = 110.0; if alive_opponents: yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_prev = sum(yesterday_bids) / len(yesterday_bids); target_bid = max(target_bid, avg_prev + 5.0); return min(my_status['budget'], float(target_bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 95.0))
    elif my_status['hp'] >= 8:
        bid = min(my_status['budget'], avg_prev * 0.8)
    else:
        bid = min(my_status['budget'], avg_prev * 0.95)
        
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_bid = max(yesterday_bids)
    else:
        avg_bid = 80.0
        max_bid = 100.0

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_bid + 5.0)
    
    if day_context['supply'] < 20:
        return min(my_status['budget'], max(avg_bid, 85.0))
    
    return min(my_status['budget'], avg_bid * 0.95)
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
        return 10.0
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(85.0, avg_opp_bid + 5.0))
    
    if day_context['supply'] < WATER_REQ * 2:
        return min(my_status['budget'], avg_opp_bid + 2.0)
        
    return min(my_status['budget'], max(20.0, avg_opp_bid * 0.7))
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
    num_alive = len(alive_opponents) + 1
    
    # Calculate target bid based on supply pressure
    if supply / num_alive < WATER_REQ:
        # High pressure: bid aggressively
        bid = DAILY_SALARY * 1.2
    else:
        # Low pressure: bid moderately
        bid = DAILY_SALARY * 0.6

    # Adjust based on yesterday's max bid if available
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid')]
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        bid = max(bid, min(max_prev * 1.05, DAILY_SALARY * 1.5))

    # Final safety checks
    if my_status['hp'] <= 2:
        bid = max(bid, DAILY_SALARY * 1.5)
    
    return float(min(my_status['budget'], bid))
"""
