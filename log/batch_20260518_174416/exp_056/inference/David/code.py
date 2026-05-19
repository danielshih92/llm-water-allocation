# ============================================================
# Experiment: exp_056
# Agent: David
# Source: exp_056
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share = supply / num_agents; bid = min(my_status['budget'], max(20, fair_share * 1.2)); return float(bid)
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
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], avg_opp_bid + 5.0)
    
    return min(my_status['budget'], max(20.0, avg_opp_bid * 0.8))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); aggressive_threshold = 70.0; if yesterday_bids: max_prev = max(yesterday_bids); if max_prev > aggressive_threshold: return min(my_status['budget'], max_prev + 5.0 if my_status['hp'] < 4 else 25.0); return min(my_status['budget'], max(30.0, max_prev + 2.0)); if my_status['hp'] <= 3: return min(my_status['budget'], 60.0); return min(my_status['budget'], 35.0)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        target = avg_bid + 2.0
    else:
        target = DAILY_SALARY * 0.5

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    return min(my_status['budget'], max(target, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; target = avg_bid * 1.05; if day_context['supply'] < 18: target = max(target, 75.0); if my_status['hp'] < 4: target = min(my_status['budget'], target * 1.5); return min(my_status['budget'], float(target))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(budget, 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    max_prev = max(prev_bids) if prev_bids else 50.0
    
    if hp <= 3:
        return min(budget, max(max_prev * 1.1, 75.0))
    
    if supply < 18:
        return min(budget, max(max_prev * 1.05, 60.0))
        
    return min(budget, max(40.0, max_prev * 0.9))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0; if my_status['hp'] <= 3: return min(my_status['budget'], max(highest_prev_bid * 1.1, DAILY_SALARY * 0.8)); if day_context['supply'] < 18: return min(my_status['budget'], max(highest_prev_bid * 1.05, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev_bid * 0.9))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        base_bid = DAILY_SALARY * 0.4
    else:
        avg_prev = sum(prev_bids) / len(prev_bids)
        base_bid = min(avg_prev * 1.05, DAILY_SALARY * 0.9)
        
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], base_bid * 1.2)
    
    return min(my_status['budget'], base_bid * 0.8)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.5); if day_context['supply'] < 18: return min(my_status['budget'], avg_bid * 1.1); return min(my_status['budget'], avg_bid * 0.95)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_prev * 1.1)); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], max(DAILY_SALARY * 0.7, avg_prev * 1.05)); return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev * 0.9))
"""
