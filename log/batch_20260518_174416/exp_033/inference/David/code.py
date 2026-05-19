# ============================================================
# Experiment: exp_033
# Agent: David
# Source: exp_033
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; avg_supply = 20; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); fair_share = avg_supply / (num_opponents + 1); bid = min(my_status['budget'], max(10, fair_share * 2.5)); if my_status['hp'] < 3: bid = min(my_status['budget'], DAILY_SALARY * 0.8); return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_bid * 0.95))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; if not alive_opps: return min(my_status['budget'], DAILY_SALARY * 0.4); cindy = opponents_status.get('Cindy'); cindy_prev_bid = cindy['previous_trace'].get('bid', 100) if cindy and cindy.get('previous_trace') else 100; if supply < 18: return min(my_status['budget'], cindy_prev_bid + 5 if my_status['hp'] < 5 else cindy_prev_bid); if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.9); return min(my_status['budget'], max(DAILY_SALARY * 0.5, cindy_prev_bid * 0.8))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]
    
    if not alive_opponents:
        return 0
    
    max_prev = max(prev_bids) if prev_bids else DAILY_SALARY * 0.8
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max_prev * 1.1)
    elif supply < WATER_REQ * len(alive_opponents):
        bid = min(my_status['budget'], max_prev + 5)
    else:
        bid = min(my_status['budget'], DAILY_SALARY * 0.85)
        
    return float(max(0, bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev * 1.05, 90.0)); return min(my_status['budget'], max(avg_prev * 0.9, 75.0))
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
    if not alive_opponents:
        return 1.0
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_opp_bid + 5.0)
    
    if supply < 18:
        return min(my_status['budget'], avg_opp_bid + 2.0)
        
    return min(my_status['budget'], 40.0)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev_bid * 0.95, DAILY_SALARY * 0.7)); return min(my_status['budget'], max(avg_prev_bid * 0.8, DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev_bid + 5, DAILY_SALARY * 0.8)); if my_status['hp'] >= 8: return min(my_status['budget'], DAILY_SALARY * 0.3); return min(my_status['budget'], max(avg_prev_bid * 0.9, DAILY_SALARY * 0.55))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    max_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < WATER_REQ * len(alive_opponents):
        return min(my_status['budget'], max_prev * 1.05 + 2)
    
    return min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.9))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev = max(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
    
    # If supply is tight, bid more aggressively
    if supply < 18:
        return min(my_status['budget'], max_prev + 2.0)
    
    # Otherwise, aim for a balanced bid to conserve budget
    return min(my_status['budget'], max(35.0, max_prev * 0.8))
"""
