# ============================================================
# Experiment: exp_091
# Agent: David
# Source: exp_091
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; num_opps = len(alive_opps); fair_share = supply / (num_opps + 1); if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.95); return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and 'bid' in prev: avg_bid += prev['bid']; count += 1; aggressive_factor = (avg_bid / count) if count > 0 else DAILY_SALARY; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 16: return min(my_status['budget'], max(DAILY_SALARY * 0.9, aggressive_factor * 0.95)); return min(my_status['budget'], max(DAILY_SALARY * 0.75, aggressive_factor * 0.85))
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
    
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
            
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, 90.0))
        
    return min(my_status['budget'], max(avg_prev * 0.9, 65.0))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(avg_prev * 1.2, 75.0))
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, 65.0))
    return min(my_status['budget'], max(avg_prev * 0.9, 50.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); cindy = opponents_status.get('Cindy'); cindy_bid = 0; if cindy and cindy['alive']: prev = cindy.get('previous_trace', {}); cindy_bid = prev.get('bid', 0) if prev else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(cindy_bid * 1.05, 75.0)); return min(my_status['budget'], max(cindy_bid * 0.8, 45.0))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
        
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev_bid * 1.1 + 5.0)
    
    if my_status['hp'] > 8:
        return min(my_status['budget'], avg_prev_bid * 0.8)
        
    return min(my_status['budget'], max(avg_prev_bid, 55.0))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if day_context['supply'] < 18: return min(my_status['budget'], max(DAILY_SALARY * 0.7, avg_prev_bid * 1.1)); if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.85); return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev_bid * 0.9))
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
        return min(my_status['budget'], 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0
    
    # If supply is tight, bid higher to guarantee water
    if supply < WATER_REQ * 2:
        bid = avg_prev_bid * 1.2
    else:
        bid = avg_prev_bid * 0.9
        
    # Emergency protocol
    if my_status['hp'] <= 3:
        bid = max(bid, DAILY_SALARY * 0.8)
        
    return float(min(my_status['budget'], max(10.0, bid)))
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
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    avg_prev = sum(prev_bids) / len(prev_bids)
    max_prev = max(prev_bids)

    if my_status['hp'] < 4:
        return min(my_status['budget'], max_prev * 1.1 + 5.0)

    if supply / (len(alive_opponents) + 1) >= WATER_REQ:
        return min(my_status['budget'], DAILY_SALARY * 0.5)

    return min(my_status['budget'], avg_prev * 1.05)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; target_bid = avg_prev_bid * 1.05; if my_status['hp'] < 4: return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.8)); if supply < 18: return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(DAILY_SALARY * 0.3, target_bid * 0.7))
"""
