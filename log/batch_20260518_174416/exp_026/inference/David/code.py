# ============================================================
# Experiment: exp_026
# Agent: David
# Source: exp_026
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            bids.append(prev['bid'])

    avg_bid = sum(bids) / len(bids) if bids else 20.0
    
    if supply < 16.0:
        bid = min(my_status['budget'], max(avg_bid * 1.2, 40.0))
    elif supply > 22.0:
        bid = min(my_status['budget'], max(avg_bid * 0.8, 15.0))
    else:
        bid = min(my_status['budget'], avg_bid + 5.0)
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], bid * 1.5)
        
    return float(bid)
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
        return min(my_status['budget'], 20.0)

    avg_prev_bid = 0
    count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_prev_bid += prev['bid']
            count += 1
    
    if count > 0:
        avg_prev_bid /= count
    
    target_bid = avg_prev_bid * 1.05 if avg_prev_bid > 0 else 35.0
    
    if my_status['hp'] < 4:
        target_bid = max(target_bid, 55.0)
    
    if supply < WATER_REQ * 2:
        target_bid = max(target_bid, 45.0)

    return min(my_status['budget'], float(target_bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] < 4: return min(my_status['budget'], avg_prev * 1.15); if supply < 18: return min(my_status['budget'], avg_prev * 1.05); return min(my_status['budget'], max(25.0, avg_prev * 0.8))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 70.0

    if hp <= 3:
        return min(budget, max_prev * 1.2, DAILY_SALARY * 1.1)
    
    if supply < 18:
        return min(budget, max(max_prev * 1.05, 75.0))
    
    return min(budget, max(60.0, max_prev * 0.95))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.8); if supply > 20: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], max(avg_prev_bid * 0.95, DAILY_SALARY * 1.1))
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
        return min(my_status['budget'], 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if supply < 18.0:
        return min(my_status['budget'], avg_prev_bid * 1.1)
        
    return min(my_status['budget'], max(50.0, avg_prev_bid * 0.95))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if not yesterday_bids: return min(my_status['budget'], DAILY_SALARY * 1.2); max_prev = max(yesterday_bids); if my_status['hp'] <= 3: return min(my_status['budget'], max_prev + 5.0); if day_context['supply'] < 18: return min(my_status['budget'], max_prev + 2.0); return min(my_status['budget'], max_prev * 0.95)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0; bid = min(my_status['budget'], avg_prev + 5.0); if my_status['hp'] < 4: bid = min(my_status['budget'], bid * 1.2); return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); bid = 55.0; if my_status['hp'] <= 3: bid = 75.0; elif day_context['supply'] < 18: bid = 65.0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') and prev['bid'] > bid: bid = min(my_status['budget'], prev['bid'] + 2.0); return float(min(my_status['budget'], bid))
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
        return 10.0
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 85.0)
    
    target_bid = avg_prev_bid + 2.0
    if target_bid > 78.0:
        target_bid = 78.0
        
    return float(min(my_status['budget'], max(55.0, target_bid)))
"""
