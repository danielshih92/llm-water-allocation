# ============================================================
# Experiment: exp_012
# Agent: David
# Source: exp_012
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; total_agents = len(alive_opponents) + 1; fair_share = day_context['supply'] / total_agents; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.8); if fair_share >= WATER_REQ: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); target_bid = avg_prev_bid * 1.05; if supply < WATER_REQ * 2: return min(my_status['budget'], target_bid * 1.2); return min(my_status['budget'], target_bid * 0.8)
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    avg_prev = sum(prev_bids) / len(prev_bids)
    max_prev = max(prev_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.7))
    
    return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.4))
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
        return min(my_status['budget'], 10.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], DAILY_SALARY * 1.1)
    elif my_status['hp'] > 8:
        bid = min(my_status['budget'], avg_prev * 0.8)
    else:
        bid = min(my_status['budget'], avg_prev * 1.05)
        
    return max(1.0, float(bid))
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    bid = min(my_status['budget'], avg_prev_bid * 1.05)
    return max(bid, DAILY_SALARY * 0.4)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 4:
        bid = min(my_status['budget'], avg_prev_bid * 1.2)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.95)
    return float(max(1.0, bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev + 5.0, 75.0)); if my_status['hp'] >= 8: return min(my_status['budget'], 40.0); return min(my_status['budget'], max(avg_prev * 0.8, 55.0))
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
        return min(my_status['budget'], 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    target_bid = 81.0
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = max(avg_prev + 2.0, 78.0)

    if my_status['hp'] < 4:
        target_bid += 15.0
    
    return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev + 5); if my_status['hp'] > 7: return min(my_status['budget'], 40); return min(my_status['budget'], max(60, max_prev * 0.9))
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

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if day_context['supply'] < WATER_REQ * 1.5:
        bid = min(my_status['budget'], avg_prev_bid * 1.15)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.8)
    
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], avg_prev_bid * 1.3)
        
    return float(max(1.0, bid))
"""
