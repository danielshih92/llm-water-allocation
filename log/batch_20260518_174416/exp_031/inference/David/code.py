# ============================================================
# Experiment: exp_031
# Agent: David
# Source: exp_031
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    avg_fair_share = DAILY_SALARY / 3.0
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    # Check yesterday's behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > avg_fair_share:
            return min(my_status['budget'], max_prev + 2.0)
        return min(my_status['budget'], avg_fair_share + 1.0)

    # Default start
    return min(my_status['budget'], 30.0)
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 120.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_opp_bid + 10.0)
    if day_context['supply'] < WATER_REQ * 2:
        return min(my_status['budget'], avg_opp_bid + 5.0)
    return min(my_status['budget'], max(DAILY_SALARY * 1.1, avg_opp_bid * 0.8))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 70.0; if my_status['hp'] < 4: return min(my_status['budget'], 120.0); if supply < 18: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.9)
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
        return 0
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if yesterday_bids:
        target = max(yesterday_bids) + 2.0
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, target))
        
    return min(my_status['budget'], DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; target_bid = 105.0; if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); target_bid = max(101.0, avg_bid * 0.95); if my_status['hp'] <= 3: return min(my_status['budget'], 160.0); return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); highest_prev_bid = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] < 4: return min(my_status['budget'], max(highest_prev_bid * 1.05, 95)); if day_context['supply'] < 18: return min(my_status['budget'], max(highest_prev_bid * 1.02, 85)); return min(my_status['budget'], max(highest_prev_bid * 0.95, 75))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return 10.0
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    target_bid = 85.0
    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_opp_bid + 2.0
        
    if my_status['hp'] < 4:
        target_bid = max(target_bid, 110.0)
        
    if supply > 20 and my_status['hp'] > 5:
        target_bid = 60.0
        
    return float(min(my_status['budget'], target_bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50
    
    if my_status['hp'] <= 4:
        bid = max(avg_prev_bid * 1.1, DAILY_SALARY * 0.8)
    else:
        bid = max(avg_prev_bid * 0.9, DAILY_SALARY * 0.4)
        
    return min(my_status['budget'], float(bid))
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
        return float(min(my_status['budget'], 20))
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max(avg_prev * 1.2, 90)))
    return float(min(my_status['budget'], max(avg_prev * 0.95, 75)))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    target_bid = avg_prev * 1.05
    if target_bid > DAILY_SALARY * 1.1:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.4))
"""
