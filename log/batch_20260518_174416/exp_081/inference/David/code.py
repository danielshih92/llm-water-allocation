# ============================================================
# Experiment: exp_081
# Agent: David
# Source: exp_081
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); fair_share = supply / (num_opponents + 1); if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply < WATER_REQ * (num_opponents + 1): return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], DAILY_SALARY * 0.45)
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
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 120.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], avg_prev * 1.1))
    
    if supply < 20:
        return float(min(my_status['budget'], avg_prev * 1.05))
    else:
        return float(min(my_status['budget'], avg_prev * 0.85))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if hp <= 3:
        bid = min(budget, avg_prev_bid * 1.2)
    elif supply < WATER_REQ * len(alive_opponents) * 0.8:
        bid = min(budget, avg_prev_bid * 1.1)
    else:
        bid = min(budget, avg_prev_bid * 0.95)
        
    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]

    target_bid = 45.0
    if yesterday_bids:
        target_bid = sum(yesterday_bids) / len(yesterday_bids)

    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    bid = min(my_status['budget'], target_bid * 1.05 + 5.0)
    return max(bid, 35.0)
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
        return float(min(my_status['budget'], 10.0))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 2:
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_prev * 1.05
        if my_status['hp'] > 5:
            return float(min(my_status['budget'], max(DAILY_SALARY * 0.4, target_bid * 0.8)))
        return float(min(my_status['budget'], target_bid))

    return float(min(my_status['budget'], DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); avg_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: avg_bids.append(prev['bid']); aggressive_threshold = max(avg_bids) if avg_bids else 45; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.8); if my_status['hp'] >= 8: return min(my_status['budget'], aggressive_threshold * 0.8); return min(my_status['budget'], aggressive_threshold + 2.5)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; SUPPLY = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY; if SUPPLY <= 18: bid = min(my_status['budget'], max(DAILY_SALARY * 1.1, avg_prev * 1.05)); elif SUPPLY >= 22: bid = min(my_status['budget'], DAILY_SALARY * 0.7); else: bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_prev)); if my_status['hp'] < 3: bid = min(my_status['budget'], DAILY_SALARY * 1.4); return float(bid)
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
    
    # Calculate competitive baseline based on yesterday's max bids
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    max_prev = max(yesterday_bids) if yesterday_bids else 70
    
    # If HP is low, prioritize survival
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
        
    # Standard aggressive bidding to ensure water requirement
    bid = max(75.0, max_prev * 0.95)
    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; target_bid = 0; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] <= 3: target_bid = min(my_status['budget'], max(avg_opp_bid * 1.1, 75)); else: target_bid = min(my_status['budget'], max(avg_opp_bid * 0.8, 45)); return float(target_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_prev * 1.1, 75.0))
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_prev * 1.05, 65.0))
    return min(my_status['budget'], max(avg_prev * 0.9, 45.0))
"""
