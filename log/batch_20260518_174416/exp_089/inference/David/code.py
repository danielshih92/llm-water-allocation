# ============================================================
# Experiment: exp_089
# Agent: David
# Source: exp_089
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):    WATER_REQ = 7    DAILY_SALARY = 80    supply = day_context['supply']    alive_opponents = [o for o in opponents_status.values() if o['alive']]    num_players = len(alive_opponents) + 1    fair_share = supply / num_players    if my_status['hp'] < 3:        return min(my_status['budget'], DAILY_SALARY * 0.8)    return min(my_status['budget'], max(20.0, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0; if my_status['hp'] < 4: return min(my_status['budget'], min(DAILY_SALARY, avg_prev * 1.2)); return min(my_status['budget'], max(15.0, avg_prev * 0.7))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(max_prev + 5.0, DAILY_SALARY * 0.9))
    
    if supply < 18:
        return min(my_status['budget'], max(max_prev + 2.0, DAILY_SALARY * 0.7))
        
    return min(my_status['budget'], max(max_prev * 0.9, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; highest_prev = max(yesterday_bids) if yesterday_bids else 60.0; if my_status['hp'] <= 3: return min(my_status['budget'], max(highest_prev + 5.0, 90.0)); if day_context['supply'] < 18: return min(my_status['budget'], highest_prev + 2.0); return min(my_status['budget'], highest_prev * 0.95)
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
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_opp_bid * 1.1, 75.0))
    if supply < 18:
        return min(my_status['budget'], avg_opp_bid * 1.05)
    return min(my_status['budget'], avg_opp_bid * 0.9)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    cindy = opponents_status.get('Cindy', {})
    
    prev_cindy = cindy.get('previous_trace', {})
    cindy_bid = prev_cindy.get('bid', 0) if prev_cindy else 0
    
    if not alive_opponents:
        return min(my_status['budget'], 10)

    target_bid = cindy_bid + 2.0 if cindy_bid > 0 else 45.0
    
    if my_status['hp'] < 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if day_context['day'] > 7:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; target_bid = avg_prev_bid + 5.0; if my_status['hp'] <= 3: target_bid = max(target_bid, DAILY_SALARY * 0.9); elif my_status['hp'] > 7: target_bid = min(target_bid, DAILY_SALARY * 0.4); return float(min(my_status['budget'], target_bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); return min(my_status['budget'], max(avg_prev * 1.05, 55.0))
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20))
    
    max_prev = max(prev_bids) if prev_bids else 50
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max(max_prev + 5, 85)))
    
    if max_prev > 100:
        return float(min(my_status['budget'], 40))
        
    return float(min(my_status['budget'], max_prev + 2))
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
        return 1.0
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        if supply < (len(alive_opponents) + 1) * WATER_REQ:
            return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.6))
        else:
            return min(my_status['budget'], max(avg_prev * 0.8, DAILY_SALARY * 0.3))
            
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""
