# ============================================================
# Experiment: exp_073
# Agent: David
# Source: exp_073
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_agents = len(alive_opponents) + 1
    fair_share_price = (day_context['supply'] / num_agents) * 5
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    bid = min(my_status['budget'], max(fair_share_price * 1.2, DAILY_SALARY * 0.4))
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_prev * 1.05)); return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; target_bid = avg_opp_bid + 2.0; if my_status['hp'] < 4: target_bid = max(target_bid, 95.0); if supply < 18: target_bid += 5.0; return float(min(my_status['budget'], max(0.0, target_bid)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; bid = min(my_status['budget'], avg_prev * 1.05); if my_status['hp'] < 4: bid = min(my_status['budget'], max(bid, 95.0)); return float(max(10.0, bid))
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
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 45.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    if day_context['supply'] < WATER_REQ + 5:
        return min(my_status['budget'], avg_opp_bid * 1.1)
    return min(my_status['budget'], max(30.0, avg_opp_bid * 0.8))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: highest_prev = max(yesterday_bids); if my_status['hp'] <= 3: return min(my_status['budget'], highest_prev + 5); return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev + 1)); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if not yesterday_bids: return min(my_status['budget'], DAILY_SALARY * 0.6); max_prev = max(yesterday_bids); if my_status['hp'] <= 3: return min(my_status['budget'], max_prev + 5); if max_prev > DAILY_SALARY * 1.5: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev * 0.95))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return 10
        
    max_prev = max(yesterday_bids) if yesterday_bids else 40
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5)
        
    supply = day_context['supply']
    if supply < 18:
        return min(my_status['budget'], max(max_prev + 2, 60))
    elif supply > 22:
        return min(my_status['budget'], max(max_prev - 5, 30))
    else:
        return min(my_status['budget'], max_prev + 1)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.1)
    elif my_status['hp'] > 8:
        bid = min(my_status['budget'], avg_prev_bid * 0.8)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 1.05)
        
    return float(max(1.0, bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; supply = day_context['supply']; target_bid = avg_bid * 1.05 if supply < 20 else avg_bid * 0.9; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); return min(my_status['budget'], max(target_bid, 40))
"""
