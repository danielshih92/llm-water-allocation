# ============================================================
# Experiment: exp_002
# Agent: David
# Source: exp_002
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    num_opponents = len([o for o in opponents_status.values() if o['alive']])
    
    # First day: estimate fair share of supply
    fair_share = supply / (num_opponents + 1)
    
    if fair_share >= WATER_REQ:
        # Likely to get water easily, bid moderate
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    else:
        # Competition will be high, bid aggressively to survive
        return min(my_status['budget'], DAILY_SALARY * 0.75)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 20.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    target_bid = avg_prev * 1.05
    return min(my_status['budget'], max(15.0, target_bid))
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_opp_bid * 1.2)
    elif supply < 18:
        bid = min(my_status['budget'], avg_opp_bid * 1.05)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.8)
        
    return float(max(1.0, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    avg_prev = sum(prev_bids) / len(prev_bids)
    max_prev = max(prev_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(DAILY_SALARY * 0.8, max_prev * 1.05))
        
    if day_context['supply'] < 18:
        return min(my_status['budget'], max_prev * 1.02)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev * 0.95))
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
    
    # Calculate a competitive bid based on supply
    # If supply is low, we need to be more aggressive
    base_bid = DAILY_SALARY * 0.7
    if supply < 18:
        base_bid = DAILY_SALARY * 1.1
    elif supply > 22:
        base_bid = DAILY_SALARY * 0.5
        
    # Check for high pressure from previous day
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If others are bidding very high, match or slightly exceed
        if max_prev > DAILY_SALARY:
            base_bid = max(base_bid, max_prev * 1.05)
            
    # Ensure we don't exceed budget or go negative
    final_bid = min(my_status['budget'], base_bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return float(min(my_status['budget'], DAILY_SALARY * 0.6))
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    max_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max_prev * 1.1 + 5))
    
    if supply < 18:
        return float(min(my_status['budget'], max(avg_prev * 1.05, 45)))
    else:
        return float(min(my_status['budget'], max(avg_prev * 0.8, 35)))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    avg_prev_bid = sum(prev_bids) / len(prev_bids)
    max_prev_bid = max(prev_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev_bid * 1.1 + 5)
    
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], avg_prev_bid * 0.8)
    
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev_bid * 1.05))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: avg_prev = sum(yesterday_bids) / len(yesterday_bids); if my_status['hp'] <= 4: return min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_prev * 1.1)); return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev * 0.9)); if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.95); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    bid = avg_opp_bid * 1.05
    return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(bids) / len(bids) if bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev + 5, DAILY_SALARY * 0.9)); return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.6))
"""
