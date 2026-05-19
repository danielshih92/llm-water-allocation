# ============================================================
# Experiment: exp_086
# Agent: David
# Source: exp_086
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; bid = DAILY_SALARY * 0.4; if supply < 18: bid = DAILY_SALARY * 0.7; elif supply > 22: bid = DAILY_SALARY * 0.3; if my_status['hp'] < 3: bid = min(my_status['budget'], DAILY_SALARY * 0.95); return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; if not alive_opps: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opps if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0; base_bid = min(my_status['budget'], avg_prev_bid * 1.05); if supply < 18: return min(my_status['budget'], base_bid * 1.2); if my_status['hp'] < 5: return min(my_status['budget'], base_bid * 1.1); return min(my_status['budget'], base_bid * 0.9)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    max_prev = max(yesterday_bids) if yesterday_bids else 60.0
    
    # Survival priority
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1 + 5.0)
    
    # Balanced bidding
    target = max(avg_bid * 0.95, 45.0)
    if day_context['supply'] < 18:
        target = max(target, max_prev * 1.05)
        
    return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_prev_bid + 5.0, 75.0))
    
    if day_context['supply'] > 22:
        return min(my_status['budget'], max(avg_prev_bid * 0.8, 40.0))
        
    return min(my_status['budget'], max(avg_prev_bid, 60.0))
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
        return min(my_status['budget'], 20.0)
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 75.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_prev * 1.1, 90.0))
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev + 5.0)
        
    return min(my_status['budget'], max(avg_prev * 0.9, 65.0))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 50.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; target_bid = avg_prev * 1.05; if my_status['hp'] < 5: target_bid = max(target_bid, 110.0); return min(my_status['budget'], float(target_bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 1.2); target = avg_bid * 1.05; if day_context['supply'] < WATER_REQ * (len(alive_opponents) + 1): return min(my_status['budget'], target * 1.2); return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if yesterday_bids:
        target = max(yesterday_bids) * 0.95
    else:
        target = 75.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(target, 90.0))
    return min(my_status['budget'], max(target, 82.0))
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
            
    if not alive_opponents:
        return 1.0
        
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.6
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], avg_opp_bid * 1.05)
        
    return min(my_status['budget'], avg_opp_bid * 0.85)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_opp_bid * 1.1, DAILY_SALARY * 0.8)); return min(my_status['budget'], max(avg_opp_bid * 0.9, DAILY_SALARY * 0.55))
"""
