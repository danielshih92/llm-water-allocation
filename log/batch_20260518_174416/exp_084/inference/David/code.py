# ============================================================
# Experiment: exp_084
# Agent: David
# Source: exp_084
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    avg_supply = 20
    num_agents = len(opponents_status) + 1
    fair_share_bid = (avg_supply / num_agents) * 10
    
    if my_status['hp'] < 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.8))
    
    return float(min(my_status['budget'], max(fair_share_bid, DAILY_SALARY * 0.4)))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0; if my_status['hp'] < 5: return min(my_status['budget'], max(avg_prev * 1.1, 90.0)); return min(my_status['budget'], max(avg_prev * 0.8, 40.0))
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
        return 10.0

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    if yesterday_bids:
        min_opp_bid = min(yesterday_bids)
        if min_opp_bid > 0:
            return min(my_status['budget'], min_opp_bid + 2.0)

    return min(my_status['budget'], 25.0)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 30; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply < 18: return min(my_status['budget'], max(avg_prev * 1.1, 40.0)); return min(my_status['budget'], max(avg_prev * 0.8, 25.0))
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
        return float(min(my_status['budget'], 20.0))

    avg_opp_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_opp_bids.append(prev['bid'])
            
    target_bid = 72.0
    if avg_opp_bids:
        target_bid = sum(avg_opp_bids) / len(avg_opp_bids) + 5.0

    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], 90.0))
        
    final_bid = min(my_status['budget'], target_bid)
    return float(max(final_bid, 65.0))
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 15.0))
    
    eric = opponents_status.get('Eric')
    prev_eric = eric.get('previous_trace') if eric else None
    eric_bid = prev_eric.get('bid', 0) if prev_eric else 0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.9))
    
    if supply < WATER_REQ * 1.5:
        return float(min(my_status['budget'], eric_bid + 2.0))
    
    return float(min(my_status['budget'], max(30.0, eric_bid * 0.8)))
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
    
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40
    
    if not alive_opponents:
        return min(my_status['budget'], 10)
        
    base_bid = min(DAILY_SALARY, max(avg_prev * 0.9, 35))
    
    if supply < 18:
        base_bid += 15
    
    if my_status['hp'] < 4:
        base_bid += 20
        
    return float(min(my_status['budget'], base_bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); return min(my_status['budget'], max(avg_prev * 0.95, 45.0))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 70
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 105.0)
    
    if supply < 18:
        return min(my_status['budget'], max(max_prev * 1.05, 85.0))
    elif supply > 22:
        return min(my_status['budget'], 55.0)
    else:
        return min(my_status['budget'], 75.0)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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
        target = max(yesterday_bids) + 2.5
    else:
        target = DAILY_SALARY * 0.6
        
    if my_status['hp'] < 4:
        target = max(target, DAILY_SALARY * 0.9)
        
    return float(min(my_status['budget'], target))
"""
