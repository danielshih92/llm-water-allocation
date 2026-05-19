# ============================================================
# Experiment: exp_055
# Agent: David
# Source: exp_055
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
    
    # If no history, bid conservatively but competitively
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.3))
    
    # Calculate a fair share bid based on supply
    fair_share = supply / (num_opponents + 1)
    
    # If HP is low, prioritize survival
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.7))
    
    # Otherwise bid to win based on a moderate portion of salary
    return float(min(my_status['budget'], DAILY_SALARY * 0.45))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: avg_bids.append(prev['bid']); highest_prev = max(avg_bids) if avg_bids else 85; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if highest_prev > 100: return min(my_status['budget'], highest_prev + 2); return min(my_status['budget'], max(DAILY_SALARY * 0.9, highest_prev + 1))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; if not alive_opps: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opps if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 70; if supply < WATER_REQ * 2: bid = min(my_status['budget'], avg_prev * 1.1); elif supply < WATER_REQ * 3: bid = min(my_status['budget'], avg_prev * 0.9); else: bid = min(my_status['budget'], DAILY_SALARY * 0.4); return float(max(1.0, bid))
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
            
    max_prev = max(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1)
    
    if supply < 18:
        return min(my_status['budget'], max(80, max_prev * 1.05))
    
    return min(my_status['budget'], max(50, max_prev * 0.8))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if my_status['hp'] > 7: return min(my_status['budget'], avg_prev * 0.8); return min(my_status['budget'], avg_prev * 1.05)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0; if my_status['hp'] < 4: return min(my_status['budget'], avg_prev * 1.2); if my_status['hp'] > 8: return min(my_status['budget'], avg_prev * 0.7); return min(my_status['budget'], avg_prev * 0.95)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        target = max(avg_bid * 1.05, 85.0)
    else:
        target = 90.0

    if my_status['hp'] < 4:
        target *= 1.2

    return float(min(my_status['budget'], target))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 1.2)); return min(my_status['budget'], max(avg_prev * 0.95, DAILY_SALARY * 0.85))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); max_prev = max(yesterday_bids) if yesterday_bids else 0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], max_prev + 5); return min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.9))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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
            
    if not yesterday_bids:
        bid = DAILY_SALARY * 0.6
    else:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_bid = max(yesterday_bids)
        if supply < 18:
            bid = min(my_status['budget'], max_bid * 1.1)
        else:
            bid = min(my_status['budget'], max(avg_bid * 0.95, DAILY_SALARY * 0.5))
            
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(bid, DAILY_SALARY * 0.95))
        
    return float(max(0, bid))
"""
