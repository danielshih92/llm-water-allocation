# ============================================================
# Experiment: exp_052
# Agent: David
# Source: exp_052
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_alive = len(alive_opponents) + 1; fair_share_bid = DAILY_SALARY * 0.55; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply / num_alive < WATER_REQ: return min(my_status['budget'], DAILY_SALARY * 0.75); return min(my_status['budget'], fair_share_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    target_bid = min(DAILY_SALARY * 1.05, avg_prev * 1.05)
    return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 0

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(max_prev + 5.0, 90.0))
    
    if supply < 18:
        return min(my_status['budget'], max(max_prev + 2.0, 75.0))
    
    if max_prev > 100:
        return min(my_status['budget'], 20.0)
        
    return min(my_status['budget'], 60.0)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
            
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < 18:
        return min(my_status['budget'], max(avg_opp_bid * 1.05, DAILY_SALARY * 0.8))
    
    return min(my_status['budget'], max(avg_opp_bid * 0.9, DAILY_SALARY * 0.5))
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
        return min(my_status['budget'], 10)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_bid * 1.2, 120))
    elif supply < WATER_REQ * 2:
        bid = min(my_status['budget'], avg_bid * 1.05)
    else:
        bid = min(my_status['budget'], avg_bid * 0.8)
        
    return max(1, int(bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    cindy = opponents_status.get('Cindy')
    cindy_prev_bid = cindy['previous_trace'].get('bid', 0) if cindy and cindy.get('previous_trace') else 0
    
    if not alive_opponents:
        return 1.0
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], 150.0)
    
    if cindy and cindy['alive']:
        if cindy_prev_bid > 120:
            return min(my_status['budget'], 130.0)
        return min(my_status['budget'], cindy_prev_bid + 2.0)
        
    return min(my_status['budget'], 85.0)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_prev_bid * 1.1, 50))
        
    return min(my_status['budget'], max(avg_prev_bid * 0.9, 35))
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
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 3:
        return min(my_status['budget'], avg_opp_bid * 1.2)
    
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], avg_opp_bid * 1.05)
        
    return min(my_status['budget'], max(20.0, avg_opp_bid * 0.8))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; total_req = WATER_REQ * (1 + len(alive_opponents)); competition_factor = 1.0; if alive_opponents: bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]; if bids: competition_factor = max(bids) / DAILY_SALARY; if supply < total_req: bid = min(my_status['budget'], DAILY_SALARY * 1.5 * competition_factor); else: bid = min(my_status['budget'], DAILY_SALARY * 1.05 * competition_factor); if my_status['hp'] <= 2: bid = min(my_status['budget'], DAILY_SALARY * 1.8); return float(max(1.0, bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev_bid * 1.05, DAILY_SALARY * 0.7)); return min(my_status['budget'], max(avg_prev_bid * 0.8, DAILY_SALARY * 0.4))
"""
