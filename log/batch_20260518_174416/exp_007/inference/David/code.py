# ============================================================
# Experiment: exp_007
# Agent: David
# Source: exp_007
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_count = 1 + len([o for o in opponents_status.values() if o['alive']]); fair_share = supply / alive_count; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.9); if fair_share >= WATER_REQ: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(my_status['budget'], 10.0)
    
    prev_bids = []
    for opp in alive_opps:
        if 'previous_trace' in opp and opp['previous_trace'].get('bid') is not None:
            prev_bids.append(opp['previous_trace']['bid'])
            
    target_bid = 85.0
    if prev_bids:
        target_bid = sum(prev_bids) / len(prev_bids) + 5.0
        
    if my_status['hp'] < 4:
        target_bid += 20.0
    
    return min(my_status['budget'], max(0.0, target_bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 0; if supply < WATER_REQ * len(alive_opponents) + 2: return min(my_status['budget'], max_prev + 5); if my_status['hp'] < 4: return min(my_status['budget'], max_prev + 2); return min(my_status['budget'], max(20, max_prev * 0.6))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return min(my_status['budget'], 10.0)
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    target_bid = avg_prev * 1.05
    if supply < 18:
        target_bid += 10.0
        
    return min(my_status['budget'], max(target_bid, 45.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.1, 50)); return min(my_status['budget'], max(avg_prev * 0.9, 45))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid'): avg_bid += prev['bid']; count += 1; if count > 0: avg_bid /= count; target_bid = avg_bid * 0.6 if my_status['hp'] > 5 else avg_bid * 0.95; if supply < WATER_REQ * 2: target_bid = max(target_bid, DAILY_SALARY * 1.1); return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.9)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 30.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 50.0)
    
    target_bid = min(max(avg_prev * 0.9, 25.0), 40.0)
    return min(my_status['budget'], target_bid)
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
        return min(my_status['budget'], 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0
    
    base_bid = min(my_status['budget'], avg_prev + 5.0)
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    if day_context['supply'] < WATER_REQ * (len(alive_opponents) + 1):
        return min(my_status['budget'], DAILY_SALARY * 0.85)
    return min(my_status['budget'], base_bid)
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max_prev_bid * 1.1)
    elif supply < 18:
        bid = min(my_status['budget'], avg_prev_bid * 1.05)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.8)
        
    return float(max(0.0, bid))
"""
