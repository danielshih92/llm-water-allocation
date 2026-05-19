# ============================================================
# Experiment: exp_064
# Agent: David
# Source: exp_064
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > 50:
            return min(my_status['budget'], max_prev + 5.0)
        return min(my_status['budget'], 45.0)

    return min(my_status['budget'], 42.0)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_market = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] < 4: return min(my_status['budget'], max(85.0, avg_market + 5.0)); if day_context['supply'] < 18: return min(my_status['budget'], max(70.0, avg_market + 2.0)); return min(my_status['budget'], max(45.0, avg_market * 0.8))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: avg_bid += prev['bid']; count += 1; if count > 0: avg_bid /= count; else: avg_bid = DAILY_SALARY; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < WATER_REQ * (len(alive_opponents) + 1): return min(my_status['budget'], avg_bid * 1.1); return min(my_status['budget'], avg_bid * 0.95)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if supply < 18: target_bid = avg_prev_bid * 1.1; else: target_bid = avg_prev_bid * 0.95; if my_status['hp'] < 4: target_bid = max(target_bid, DAILY_SALARY * 1.2); return min(my_status['budget'], max(0, target_bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_agents = len(alive_opponents) + 1
    fair_share = supply / num_agents
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_prev_bid * 1.05
    else:
        target_bid = DAILY_SALARY * 0.6
        
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], DAILY_SALARY * 0.85)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.4, target_bid))
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
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
        
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    # If supply is tight, bid aggressively to ensure survival
    if supply < 18:
        bid = min(my_status['budget'], avg_opp_bid * 1.1)
    # If supply is generous, bid moderately
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.95)
        
    # Desperation logic if HP is low
    if my_status['hp'] <= 2:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
        
    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80 WATER_REQ = 7 supply = day_context['supply'] alive_opponents = [o for o in opponents_status.values() if o['alive']] if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5) yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')] avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 1.2 if my_status['hp'] <= 3: bid = min(my_status['budget'], DAILY_SALARY * 1.5) elif supply < 18: bid = min(my_status['budget'], avg_prev_bid * 1.1) else: bid = min(my_status['budget'], DAILY_SALARY * 0.8) return float(max(0, bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] < 4: return min(my_status['budget'], max_prev * 1.1); if day_context['supply'] < 18: return min(my_status['budget'], max_prev * 1.05); return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev * 0.9))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if not yesterday_bids:
        return min(my_status['budget'], 60.0)
    avg_bid = sum(yesterday_bids) / len(yesterday_bids)
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max(avg_bid * 1.2, 75.0))
    return min(my_status['budget'], max(avg_bid * 0.9, 50.0))
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
        return min(my_status['budget'], 20.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_prev_bid * 1.1)
    elif day_context['supply'] < 18:
        bid = min(my_status['budget'], avg_prev_bid * 0.95)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.7)
        
    return max(0.0, float(bid))
"""
