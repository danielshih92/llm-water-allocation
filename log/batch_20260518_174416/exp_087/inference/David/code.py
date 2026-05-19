# ============================================================
# Experiment: exp_087
# Agent: David
# Source: exp_087
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if my_status['hp'] <= 4: return min(my_status['budget'], DAILY_SALARY * 0.85); if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_bid + 2.0)); return min(my_status['budget'], DAILY_SALARY * 0.65)
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 120.0)
    
    if supply < 18:
        return min(my_status['budget'], max(85.0, max_prev + 2.0))
    elif supply < 22:
        return min(my_status['budget'], 75.0)
    else:
        return min(my_status['budget'], 65.0)
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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.5
    
    if my_status['hp'] < 4:
        bid = avg_prev_bid * 1.2
    elif supply < 18:
        bid = avg_prev_bid * 1.1
    else:
        bid = avg_prev_bid * 0.9
        
    return min(my_status['budget'], max(0, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0; bid = min(my_status['budget'], max(85.0, avg_prev * 0.95)); if my_status['hp'] <= 3: bid = min(my_status['budget'], DAILY_SALARY * 1.5); return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(budget, 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 50.0
    
    if supply <= 16:
        bid = min(budget, max(max_prev + 5.0, 75.0))
    elif supply >= 22:
        bid = min(budget, max(30.0, max_prev * 0.6))
    else:
        bid = min(budget, max_prev + 2.0)
        
    if hp < 4:
        bid = min(budget, max(bid, 78.0))
        
    return float(bid)
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev_bid + 10.0)
    return min(my_status['budget'], max(50.0, avg_prev_bid - 5.0))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev * 1.1)
    return min(my_status['budget'], max(avg_prev * 0.9, 50.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: highest_prev_bid = max(yesterday_bids); target = highest_prev_bid + 2.0; else: target = DAILY_SALARY * 1.1; if my_status['hp'] < 4: target = max(target, DAILY_SALARY * 1.3); return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not alive_opponents:
        return min(my_status['budget'], 50.0)

    max_prev = max(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.15)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max_prev * 1.05)
        
    return min(my_status['budget'], max(60.0, max_prev * 0.95))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive = [o for o in opponents_status.values() if o['alive']]; if not alive: return min(my_status['budget'], 20.0); prev_bids = [o['previous_trace']['bid'] for o in alive if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 1.1); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.9)
"""
