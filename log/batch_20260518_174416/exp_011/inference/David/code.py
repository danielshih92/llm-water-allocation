# ============================================================
# Experiment: exp_011
# Agent: David
# Source: exp_011
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', True)]
    num_agents = len(alive_opponents) + 1
    fair_share = supply / num_agents
    bid = min(my_status['budget'], 28.0)
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], 45.0)
    return float(bid)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = min(my_status['budget'], avg_prev * 1.05)
        return max(target_bid, DAILY_SALARY * 0.4)

    return min(my_status['budget'], DAILY_SALARY * 0.6)
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
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max_prev + 5.0)
        return min(my_status['budget'], max_prev + 1.0)
    return min(my_status['budget'], 45.0)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not yesterday_bids:
        return min(my_status['budget'], 85.0)
        
    max_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1 + 5.0)
    
    if day_context['supply'] < 18.0:
        return min(my_status['budget'], max_prev * 1.05)
        
    return min(my_status['budget'], max(75.0, max_prev * 0.95))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60
    
    # Survival priority
    if my_status['hp'] <= 3:
        bid = avg_prev_bid * 1.2
    else:
        bid = avg_prev_bid * 0.95
        
    # Adjust for supply scarcity
    supply_factor = 1.0
    if day_context['supply'] < 18:
        supply_factor = 1.3
        
    final_bid = min(my_status['budget'], bid * supply_factor)
    return max(10.0, float(final_bid))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0
    
    supply = day_context['supply']
    num_players = len(alive_opponents) + 1
    pressure = (num_players * WATER_REQ) / supply
    
    bid = avg_prev * (1.0 + (pressure - 1.0) * 0.5)
    if my_status['hp'] < 4:
        bid = max(bid, DAILY_SALARY * 0.8)
    
    return min(my_status['budget'], max(0.0, bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return 0.0; if my_status['hp'] <= 3: return min(my_status['budget'], 150.0); if supply < WATER_REQ * 1.5: return min(my_status['budget'], 145.0); return min(my_status['budget'], 85.0)
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

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        bid = max(avg_prev_bid * 1.2, 90.0)
    else:
        bid = avg_prev_bid * 1.05

    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], 75.0))
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > 100:
            return float(min(my_status['budget'], 30.0))
        return float(min(my_status['budget'], max(40.0, max_prev * 0.6)))
        
    return float(min(my_status['budget'], 45.0))
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
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    max_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
        
    if supply < (WATER_REQ * (len(alive_opponents) + 1)):
        return min(my_status['budget'], max_prev * 1.05)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev * 0.9))
"""
