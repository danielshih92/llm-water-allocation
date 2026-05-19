# ============================================================
# Experiment: exp_070
# Agent: David
# Source: exp_070
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 30.0; bid = avg_prev * 1.05; if my_status['hp'] < 3: bid = max(bid, 45.0); return float(min(my_status['budget'], bid))
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
    num_agents = len(alive_opponents) + 1
    
    # Estimate fair share bid
    fair_share_bid = (supply / num_agents) * 5
    
    # Look at yesterday's pressure
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If supply is low, bid aggressively to ensure survival
        if supply < 18:
            return min(my_status['budget'], max(max_prev * 1.05, 75))
        # If supply is high, try to save budget
        return min(my_status['budget'], max(fair_share_bid, 40))
        
    return min(my_status['budget'], 60)
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

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        bid = avg_prev * 1.05
    else:
        bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 3:
        bid = max(bid, DAILY_SALARY * 0.9)
    
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.5)
    
    if day_context['day'] > 7:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    target_bid = min(avg_opp_bid * 0.95, DAILY_SALARY * 1.1)
    return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.6))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max(avg_bid * 1.2, DAILY_SALARY * 0.85))
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_bid * 1.05)
        
    return min(my_status['budget'], avg_bid * 0.9)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < (len(alive_opponents) + 1) * WATER_REQ: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.95)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
        return min(my_status['budget'], max(40.0, max_prev * 0.95))

    return min(my_status['budget'], 45.0)
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
        return 10
        
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 50
    
    # If supply is tight, bid aggressively to beat Cindy/Eric
    if supply <= 18:
        bid = min(my_status['budget'], max_prev + 5)
    # If supply is high, bid conservatively to save budget
    else:
        bid = min(my_status['budget'], max(30, max_prev * 0.6))
        
    # Emergency survival mode
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    return int(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev + 5.0); if day_context['supply'] < 18: return min(my_status['budget'], max_prev + 2.0); return min(my_status['budget'], max(40.0, max_prev * 0.9))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; target_bid = max(avg_bids) + 2.0 if avg_bids else DAILY_SALARY * 0.6; if my_status['hp'] < 4: target_bid = max(target_bid, DAILY_SALARY * 0.95); return min(my_status['budget'], target_bid)
"""
