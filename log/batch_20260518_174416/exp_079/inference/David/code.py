# ============================================================
# Experiment: exp_079
# Agent: David
# Source: exp_079
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = DAILY_SALARY / num_players; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], fair_share * 1.2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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
    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_bid * 1.05
    else:
        target_bid = DAILY_SALARY * 0.5
    if my_status['hp'] < 4:
        target_bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    return float(min(my_status['budget'], target_bid))
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
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 85.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < 18:
        return min(my_status['budget'], avg_prev + 5.0)
        
    return min(my_status['budget'], avg_prev * 0.95)
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
    
    if not yesterday_bids:
        return min(my_status['budget'], 45.0)

    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    max_prev = max(yesterday_bids)

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
    
    target = max(avg_prev * 0.9, 40.0)
    return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if my_status['hp'] >= 8: return min(my_status['budget'], max(20, avg_bid * 0.8)); return min(my_status['budget'], max(35, avg_bid * 1.05))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); highest_prev = max(yesterday_bids) if yesterday_bids else 80.0; if my_status['hp'] < 4: return min(my_status['budget'], highest_prev + 5.0); if day_context['supply'] < 20: return min(my_status['budget'], highest_prev + 2.0); return min(my_status['budget'], max(40.0, highest_prev * 0.9))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive = [o for o in opponents_status.values() if o['alive']]; if not alive: return min(my_status['budget'], DAILY_SALARY * 0.2); avg_prev = [o['previous_trace']['bid'] for o in alive if o['previous_trace'] and o['previous_trace']['bid'] is not None]; avg_bid = sum(avg_prev) / len(avg_prev) if avg_prev else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if supply < WATER_REQ * 2: return min(my_status['budget'], max(avg_bid * 1.05, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_bid * 0.8, DAILY_SALARY * 0.4))
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
        return float(min(my_status['budget'], 20.0))
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0
    
    if my_status['hp'] < 5:
        bid = min(my_status['budget'], max(avg_prev + 5.0, 95.0))
    else:
        bid = min(my_status['budget'], max(avg_prev, 85.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    base_bid = DAILY_SALARY * 1.1
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = max(base_bid, avg_prev * 0.95)
    else:
        target = base_bid
        
    if my_status['hp'] < 3:
        target = min(my_status['budget'], DAILY_SALARY * 1.5)
    
    return float(min(my_status['budget'], target))
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
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_opp_bid * 1.05)
    return min(my_status['budget'], avg_opp_bid * 0.95)
"""
