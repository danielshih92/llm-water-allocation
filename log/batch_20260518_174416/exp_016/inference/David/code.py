# ============================================================
# Experiment: exp_016
# Agent: David
# Source: exp_016
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    # Calculate fair share bid
    fair_bid = DAILY_SALARY * 0.55
    
    # If supply is high relative to agents, bid lower
    if supply / (num_opponents + 1) >= WATER_REQ:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # If supply is tight, bid more aggressively
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.85)
        
    # Check yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        return min(my_status['budget'], max(fair_bid, max_prev + 2.0))
        
    return min(my_status['budget'], fair_bid)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return min(my_status['budget'], 5.0)
        
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    if supply > 20:
        bid = min(my_status['budget'], avg_prev_bid * 0.8)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 1.1)
        
    return max(1.0, bid)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if yesterday_bids:
        cindy_bid = next((o['previous_trace']['bid'] for o in opponents_status.values() if 'Cindy' in opponents_status and o == opponents_status['Cindy']), 50)
        return min(my_status['budget'], max(DAILY_SALARY * 0.55, cindy_bid * 0.9))

    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 5.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 3:
            return min(my_status['budget'], max_prev + 5.0)
        return min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.8))
    
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents) + 1
    
    if num_alive <= 1:
        return 1.0
    
    avg_supply_per_player = supply / num_alive
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if avg_supply_per_player >= WATER_REQ:
        base_bid = DAILY_SALARY * 0.3
    else:
        base_bid = DAILY_SALARY * 0.7
        
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        bid = max(base_bid, highest_prev * 0.5)
    else:
        bid = base_bid
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], bid * 1.5)
        
    return min(my_status['budget'], float(bid))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(max_prev * 1.1, DAILY_SALARY * 0.9))
    
    if supply < 18:
        return min(my_status['budget'], max(max_prev * 1.05, DAILY_SALARY * 0.7))
    
    return min(my_status['budget'], max(max_prev * 0.8, DAILY_SALARY * 0.4))
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
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.5)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev = DAILY_SALARY

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply > 20:
        bid = DAILY_SALARY * 0.6
    elif supply < 17:
        bid = max(DAILY_SALARY * 0.9, avg_prev * 1.05)
    else:
        bid = max(DAILY_SALARY * 0.75, avg_prev * 0.95)
        
    return min(my_status['budget'], bid)
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
        return min(my_status['budget'], 10.0)

    cindy = opponents_status.get('Cindy', {})
    cindy_bid = 0.0
    if cindy.get('alive') and cindy.get('previous_trace'):
        cindy_bid = cindy['previous_trace'].get('bid', 0.0)

    if my_status['hp'] <= 3:
        target_bid = DAILY_SALARY * 0.9
    elif supply < 18:
        target_bid = max(cindy_bid + 2.0, DAILY_SALARY * 0.6)
    else:
        target_bid = max(cindy_bid * 0.5, DAILY_SALARY * 0.4)

    return float(min(my_status['budget'], target_bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], max(DAILY_SALARY * 0.7, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = min(my_status['budget'], avg_prev * 1.05)
        return max(target_bid, DAILY_SALARY * 0.4)
        
    return min(my_status['budget'], DAILY_SALARY * 0.6)
"""
