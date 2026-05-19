# ============================================================
# Experiment: exp_045
# Agent: David
# Source: exp_045
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share = supply / num_agents; base_bid = DAILY_SALARY * 0.5; if fair_share < WATER_REQ: base_bid = DAILY_SALARY * 0.8; if my_status['hp'] < 3: base_bid = min(my_status['budget'], DAILY_SALARY * 0.95); return float(min(my_status['budget'], base_bid))
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

    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
        bid = avg_opp_bid * 0.95
    else:
        bid = DAILY_SALARY * 0.6

    if my_status['hp'] < 4:
        bid = max(bid, DAILY_SALARY * 0.85)
    
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    supply = day_context['supply']
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, 50.0))
    
    if supply > 22:
        return min(my_status['budget'], max(avg_prev * 0.6, 25.0))
        
    return min(my_status['budget'], avg_prev * 0.85)
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
        return min(my_status['budget'], 10.0)
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not yesterday_bids:
        return min(my_status['budget'], 45.0)
        
    max_prev = max(yesterday_bids)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max_prev + 5.0)
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev + 2.0, 50.0))
        
    return min(my_status['budget'], max(avg_prev * 0.8, 30.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(budget, 10))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 50
    
    if hp <= 3:
        return float(min(budget, max_prev * 1.2))
    
    if supply < 18:
        return float(min(budget, max_prev * 1.05))
    elif supply > 22:
        return float(min(budget, max(30, max_prev * 0.7)))
    else:
        return float(min(budget, max_prev * 0.9))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100.0; target_bid = min(my_status['budget'], max(avg_prev * 1.05, 145.0)); if my_status['hp'] <= 3: return min(my_status['budget'], target_bid * 1.2); return target_bid
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
    num_alive = len(alive_opponents) + 1
    
    if not alive_opponents:
        return 10
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if supply / num_alive >= WATER_REQ:
        return min(my_status['budget'], avg_opp_bid * 0.8)
    else:
        return min(my_status['budget'], avg_opp_bid * 1.1 + 5)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0; if my_status['hp'] <= 3: return min(my_status['budget'], max(highest_prev_bid * 1.1, 85.0)); if day_context['supply'] < 18: return min(my_status['budget'], max(highest_prev_bid * 1.05, 50.0)); return min(my_status['budget'], max(highest_prev_bid * 0.9, 35.0))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_bid * 1.1, 75.0)); return min(my_status['budget'], max(avg_bid * 0.9, 45.0)); return min(my_status['budget'], 50.0)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 25.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.8)
    elif my_status['hp'] >= 8:
        bid = min(my_status['budget'], avg_bid * 0.8)
    else:
        bid = min(my_status['budget'], avg_bid * 1.05)

    return float(max(1.0, bid))
"""
