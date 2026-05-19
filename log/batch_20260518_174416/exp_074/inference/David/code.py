# ============================================================
# Experiment: exp_074
# Agent: David
# Source: exp_074
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = DAILY_SALARY / num_players; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], fair_share * 1.2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if day_context['supply'] < 18: return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev + 5)); return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 70.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_prev * 1.2)
    elif my_status['hp'] > 8:
        bid = min(my_status['budget'], avg_prev * 0.8)
    else:
        bid = min(my_status['budget'], avg_prev * 1.05)
        
    return max(1.0, float(bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)
    
    max_prev = max(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1 + 5)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max_prev * 1.05)
    
    return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev * 0.95))
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
    num_alive = len(alive_opponents) + 1
    
    # Calculate a competitive bid based on supply scarcity
    # If supply is tight, bid higher to ensure survival
    if supply < (num_alive * WATER_REQ * 0.8):
        base_bid = DAILY_SALARY * 1.3
    else:
        base_bid = DAILY_SALARY * 0.9
        
    # Adjust for low HP
    if my_status['hp'] < 4:
        base_bid = DAILY_SALARY * 1.5
        
    # Look at yesterday's max bid to stay competitive
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid')]
    if prev_bids:
        max_prev = max(prev_bids)
        bid = max(base_bid, max_prev + 2.0)
    else:
        bid = base_bid
        
    return float(min(my_status['budget'], bid))
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
        return min(my_status['budget'], 20.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        if avg_bid > DAILY_SALARY:
            return min(my_status['budget'], DAILY_SALARY * 0.6)
        return min(my_status['budget'], avg_bid + 5.0)
        
    return min(my_status['budget'], DAILY_SALARY * 0.75)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 50.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 100.0; bid = min(my_status['budget'], max(avg_prev * 1.05, 115.0)); if my_status['hp'] < 4: bid = min(my_status['budget'], max(bid, 130.0)); return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.5)
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    elif supply < WATER_REQ * (len(alive_opponents) + 1):
        bid = min(my_status['budget'], avg_prev_bid * 1.1)
    else:
        bid = min(my_status['budget'], DAILY_SALARY * 0.7)
        
    return float(bid)
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
    yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev * 1.1)
    return min(my_status['budget'], avg_prev * 0.9)
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
        return min(my_status['budget'], 20.0)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 3:
            return min(my_status['budget'], max_prev * 1.1 + 5.0)
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev * 0.95))
    return min(my_status['budget'], DAILY_SALARY * 0.7)
"""
