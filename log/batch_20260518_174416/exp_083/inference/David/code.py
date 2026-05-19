# ============================================================
# Experiment: exp_083
# Agent: David
# Source: exp_083
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); return min(my_status['budget'], max(DAILY_SALARY * 0.35, avg_bid + 2.0)); if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], DAILY_SALARY * 0.4)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
        
    max_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
        
    if supply < 18:
        return min(my_status['budget'], max(90.0, max_prev * 0.95))
    else:
        return min(my_status['budget'], max(75.0, max_prev * 0.7))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.9)); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.7)); return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    elif day_context['supply'] < 18:
        bid = min(my_status['budget'], max(avg_bid * 1.1, 75))
    else:
        bid = min(my_status['budget'], max(avg_bid * 0.9, 50))
        
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], min(80, avg_prev * 1.2)); if day_context['supply'] < 18: return min(my_status['budget'], 55); return min(my_status['budget'], max(35, avg_prev * 0.95))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if my_status['hp'] >= 8: return min(my_status['budget'], max(30.0, avg_prev * 0.8)); return min(my_status['budget'], max(45.0, avg_prev * 1.05))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0; if supply < 18: bid = min(my_status['budget'], max(avg_prev * 1.05, 75.0)); elif supply < 22: bid = min(my_status['budget'], max(avg_prev * 0.8, 50.0)); else: bid = min(my_status['budget'], max(avg_prev * 0.5, 30.0)); if my_status['hp'] < 4: bid = min(my_status['budget'], DAILY_SALARY * 0.95); return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 25.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 35.0; max_prev = max(yesterday_bids) if yesterday_bids else 40.0; target_bid = max(avg_prev + 2.0, max_prev * 0.95); if my_status['hp'] < 4: target_bid = max(target_bid, 55.0); return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], 95.0); if supply < 18: return min(my_status['budget'], max(max_prev + 5.0, 70.0)); if supply > 22: return min(my_status['budget'], 45.0); return min(my_status['budget'], max(max_prev + 2.0, 60.0))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; budget = my_status['budget']; if not alive_opponents: return min(budget, DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if supply <= 16: bid = min(budget, avg_opp_bid * 1.1); elif supply >= 22: bid = min(budget, DAILY_SALARY * 0.4); else: bid = min(budget, avg_opp_bid * 0.9); return float(max(0, bid))
"""
