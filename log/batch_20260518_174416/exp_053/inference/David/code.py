# ============================================================
# Experiment: exp_053
# Agent: David
# Source: exp_053
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; num_alive = len(alive_opps); fair_share = supply / (num_alive + 1); if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply < 18: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], DAILY_SALARY * 0.45)
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
        return 10.0
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], 75.0)
    if supply < 18:
        return min(my_status['budget'], min(80.0, avg_opp_bid + 5.0))
    return min(my_status['budget'], max(55.0, avg_opp_bid + 2.0))
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    # Aggression adjustment based on supply
    if supply < 18:
        bid = avg_prev * 1.1
    else:
        bid = avg_prev * 0.8

    # Survival priority
    if my_status['hp'] < 4:
        bid = max(bid, 60.0)
        
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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

    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_bid * 1.1)

    return min(my_status['budget'], max(20.0, avg_bid * 0.8))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    
    cindy = opponents_status.get('Cindy', {})
    cindy_prev = cindy.get('previous_trace', {})
    cindy_bid = cindy_prev.get('bid', 0) if cindy_prev else 0
    
    # If Cindy is bidding excessively high, we conserve budget unless HP is critical
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    # If supply is high, we bid moderately to save resources
    if supply > 20:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # If supply is tight, bid to beat Cindy's last known behavior or a baseline
    bid = max(DAILY_SALARY * 0.6, cindy_bid * 0.5)
    return min(my_status['budget'], bid)
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 80
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev_bid * 1.1)
    
    if supply < 18:
        return min(my_status['budget'], avg_prev_bid * 1.05)
    
    return min(my_status['budget'], avg_prev_bid * 0.85)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 3:
            return float(min(my_status['budget'], max_prev * 1.1))
        if max_prev > DAILY_SALARY * 1.2:
            return float(min(my_status['budget'], DAILY_SALARY * 0.5))
        return float(min(my_status['budget'], max_prev + 5.0))

    return float(min(my_status['budget'], DAILY_SALARY * 0.8))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40
    
    if my_status['hp'] <= 2:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif supply < 18:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.1, DAILY_SALARY * 0.6))
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.8, DAILY_SALARY * 0.35))
        
    return float(bid)
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
            
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 150.0))
    elif supply < 18:
        bid = min(my_status['budget'], max(avg_prev * 1.05, 120.0))
    else:
        bid = min(my_status['budget'], avg_prev * 0.9)
        
    return float(max(bid, 40.0))
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
    if supply < 18:
        return min(my_status['budget'], max(DAILY_SALARY * 0.7, max_prev + 1.0))
    return min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.8))
"""
