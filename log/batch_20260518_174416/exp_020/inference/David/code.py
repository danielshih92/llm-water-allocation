# ============================================================
# Experiment: exp_020
# Agent: David
# Source: exp_020
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = day_context['supply'] / num_players; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.95); if fair_share >= WATER_REQ: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], DAILY_SALARY * 0.6)
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
    yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]
    if not yesterday_bids:
        return min(my_status['budget'], 70.0)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    target_bid = avg_prev * 1.05
    if my_status['hp'] < 4:
        target_bid = max(target_bid, 85.0)
    return min(my_status['budget'], float(target_bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: highest_prev = max(yesterday_bids); if my_status['hp'] < 4: return min(my_status['budget'], highest_prev + 5.0); return min(my_status['budget'], max(85.0, highest_prev * 0.9)); return min(my_status['budget'], 85.0)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_prev + 5.0, 120.0))
    
    if day_context['supply'] < 18.0:
        return min(my_status['budget'], avg_prev + 2.0)
        
    return min(my_status['budget'], max(60.0, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; budget = my_status['budget']; hp = my_status['hp']; if not alive_opps: return min(budget, 10.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opps if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0; if hp < 3: return min(budget, DAILY_SALARY * 1.2); if supply < 18: return min(budget, max(avg_prev * 0.9, 40.0)); return min(budget, max(avg_prev * 0.6, 25.0))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_prev_bid * 1.1, 75.0))
    if supply > 22:
        return min(my_status['budget'], max(avg_prev_bid * 0.8, 40.0))
    return min(my_status['budget'], max(avg_prev_bid * 1.05, 55.0))
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

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev + 5.0)
    
    return min(my_status['budget'], max(30.0, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)
        
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if day_context['supply'] / (len(alive_opponents) + 1) >= WATER_REQ:
        return min(my_status['budget'], max_prev * 0.95 + 1.0)
    
    return min(my_status['budget'], max(max_prev + 1.0, DAILY_SALARY * 0.6))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.8)
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

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev * 1.2)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev * 1.05)
        
    return min(my_status['budget'], max(40.0, avg_prev * 0.9))
"""
