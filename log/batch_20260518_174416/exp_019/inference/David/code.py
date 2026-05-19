# ============================================================
# Experiment: exp_019
# Agent: David
# Source: exp_019
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
    num_opponents = len(alive_opponents)
    
    # Calculate fair share
    fair_share = supply / (num_opponents + 1)
    
    # If supply is tight, bid more aggressively
    if fair_share < WATER_REQ:
        bid = DAILY_SALARY * 0.7
    else:
        bid = DAILY_SALARY * 0.4
        
    # Adjust for HP status
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        
    return float(min(my_status['budget'], bid))
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
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
            
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 85
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    elif supply < 18:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_prev + 5))
    else:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.7, avg_prev * 0.9))
        
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0; target_bid = avg_bid * 1.05; if my_status['hp'] < 3: return min(my_status['budget'], target_bid * 1.5); return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if day_context['supply'] < WATER_REQ * 1.5: return min(my_status['budget'], max(avg_prev_bid * 1.1, DAILY_SALARY * 0.8)); if my_status['hp'] < 4: return min(my_status['budget'], max(avg_prev_bid, DAILY_SALARY * 0.7)); return min(my_status['budget'], max(avg_prev_bid * 0.8, DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75; base_bid = min(DAILY_SALARY * 1.15, max(70, avg_prev + 2)); if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.3); return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < 18:
        return min(my_status['budget'], avg_prev_bid * 1.1)
        
    return min(my_status['budget'], max(40, avg_prev_bid * 0.9))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.95); if supply < 18: return min(my_status['budget'], max(avg_prev_bid + 5.0, 60.0)); return min(my_status['budget'], max(avg_prev_bid * 0.8, 30.0))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 75.0))
    elif my_status['hp'] >= 8:
        bid = min(my_status['budget'], max(avg_prev * 0.5, 30.0))
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.9, 50.0))
        
    return float(int(bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: avg_prev = sum(yesterday_bids) / len(yesterday_bids); target_bid = avg_prev * 1.05; else: target_bid = DAILY_SALARY * 0.7; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 1.2); return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.1, 60)); return min(my_status['budget'], max(avg_prev * 0.9, 45))
"""
