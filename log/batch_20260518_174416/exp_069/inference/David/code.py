# ============================================================
# Experiment: exp_069
# Agent: David
# Source: exp_069
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.5; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.85); if supply < 18: return min(my_status['budget'], avg_bid * 1.2); return min(my_status['budget'], avg_bid * 1.05)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return 10
        
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 70
    
    # Aggressive bidding if supply is low, conservative if high
    bid = avg_prev * (1.1 if supply < 18 else 0.8)
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], bid * 1.5)
        
    return int(min(my_status['budget'], max(5, bid)))
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
        return min(my_status['budget'], 5.0)

    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 80.0
    
    if my_status['hp'] <= 4:
        bid = min(my_status['budget'], avg_prev * 1.2)
    else:
        bid = min(my_status['budget'], avg_prev * 0.95)
        
    return max(0.0, float(bid))
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
        return min(my_status['budget'], 20.0)

    cindy = opponents_status.get('Cindy', {})
    alex = opponents_status.get('Alex', {})
    
    bid = 85.0
    if cindy.get('alive'):
        bid = max(bid, 143.0)
    elif alex.get('alive'):
        bid = max(bid, 116.0)

    if my_status['hp'] < 4:
        bid += 20.0
    
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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
            
    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
        bid = avg_opp_bid + 5.0
    else:
        bid = DAILY_SALARY * 0.6
        
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        
    return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))
    
    bid = min(my_status['budget'], max(avg_prev * 1.05, 55.0))
    return float(bid)
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
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    base_bid = 85.0
    if yesterday_bids:
        base_bid = max(yesterday_bids) + 1.0
    
    if supply >= 22:
        bid = min(my_status['budget'], DAILY_SALARY * 0.6)
    elif supply <= 17:
        bid = min(my_status['budget'], max(base_bid, DAILY_SALARY * 1.2))
    else:
        bid = min(my_status['budget'], max(base_bid, DAILY_SALARY * 0.9))
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.5)
        
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 70.0
    max_prev = max(prev_bids) if prev_bids else 80.0

    # Aggressive bidding if HP is low, otherwise strategic matching
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max_prev + 5.0)
    elif supply < 20:
        bid = min(my_status['budget'], max(85.0, avg_prev + 2.0))
    else:
        bid = min(my_status['budget'], avg_prev * 0.95)
        
    return float(max(10.0, bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); cindy = opponents_status.get('Cindy', {}); cindy_prev_bid = cindy.get('previous_trace', {}).get('bid', 0) if cindy.get('alive') else 0; if day_context['supply'] <= WATER_REQ * 1.5: return min(my_status['budget'], max(cindy_prev_bid + 2.0, DAILY_SALARY * 0.6)); if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], max(cindy_prev_bid * 0.8, DAILY_SALARY * 0.35))
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
    num_players = len(alive_opponents) + 1
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70
    
    if supply < (num_players * WATER_REQ) * 0.8:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_prev * 1.1))
    elif my_status['hp'] < 4:
        bid = min(my_status['budget'], DAILY_SALARY * 0.75)
    else:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev * 0.95))
        
    return float(bid)
"""
