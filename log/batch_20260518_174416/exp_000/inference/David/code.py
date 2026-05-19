# ============================================================
# Experiment: exp_000
# Agent: David
# Source: exp_000
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
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
        if avg_opp_bid > 60:
            return min(my_status['budget'], 55.0)
        return min(my_status['budget'], avg_opp_bid + 5.0)

    return min(my_status['budget'], 45.0)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 82.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev_bid + 5.0)
    if day_context['supply'] < 18.0:
        return min(my_status['budget'], avg_prev_bid + 2.0)
    return min(my_status['budget'], avg_prev_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_bid * 1.1, 75.0)); return min(my_status['budget'], max(avg_bid * 0.95, 45.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100; if my_status['hp'] <= 3: return min(my_status['budget'], 180.0); if supply < 18: return min(my_status['budget'], max(110.0, avg_prev + 5.0)); if supply > 22: return min(my_status['budget'], 75.0); return min(my_status['budget'], max(90.0, avg_prev))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev + 5, 95)); if my_status['hp'] > 7: return min(my_status['budget'], max(avg_prev - 10, 40)); return min(my_status['budget'], max(avg_prev, 75))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
            
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY
    
    # Aggressive if low HP, otherwise calculated bidding
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 1.2))
    elif supply < 18:
        bid = min(my_status['budget'], avg_prev * 1.05)
    else:
        bid = min(my_status['budget'], avg_prev * 0.85)
        
    return float(max(0, bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_prev + 5.0, DAILY_SALARY * 0.9))
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev + 2.0, DAILY_SALARY * 0.7))
        
    return min(my_status['budget'], max(avg_prev * 0.8, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40); yesterday_bids = [opp.get('previous_trace', {}).get('bid', 0) for opp in alive_opponents if opp.get('previous_trace')]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; base_bid = max(avg_prev * 1.05, 65); if my_status['hp'] <= 5: base_bid = max(base_bid, 85); return min(my_status['budget'], base_bid)
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

    target_bid = 105.0
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = max(100.0, avg_prev + 2.0)

    if my_status['hp'] <= 3:
        target_bid = max(target_bid, 115.0)
    
    return float(min(my_status['budget'], target_bid))
"""
