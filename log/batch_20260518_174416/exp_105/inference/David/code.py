# ============================================================
# Experiment: exp_105
# Agent: David
# Source: exp_105
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    # If no history, bid moderately to secure water.
    # Expected supply is ~20. If 2 agents, each needs 7 (14 total).
    # Bid around 25-30 units to be safe but efficient.
    base_bid = 28.0
    
    if my_status['hp'] < 3:
        return float(min(my_status['budget'], 50.0))
    
    return float(min(my_status['budget'], base_bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; active_count = len(alive_opponents) + 1; fair_share = supply / active_count; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_yesterday = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], 150.0); if supply / WATER_REQ >= 1.2: return min(my_status['budget'], 75.0); if max_yesterday > 120: return min(my_status['budget'], 95.0); return min(my_status['budget'], max(82.0, max_yesterday * 0.9))
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
        return float(min(my_status['budget'], 10.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 20.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max_prev + 5.0))
    
    if supply < 18.0:
        return float(min(my_status['budget'], max(20.0, max_prev + 2.0)))
        
    return float(min(my_status['budget'], 16.0))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; if not alive_opps: return 0.0; cindy = opponents_status.get('Cindy'); cindy_bid = cindy.get('previous_trace', {}).get('bid', 0) if cindy and cindy['alive'] else 0; if supply < WATER_REQ * 1.5: bid = min(my_status['budget'], max(cindy_bid * 1.05, DAILY_SALARY * 0.6)); else: bid = min(my_status['budget'], max(cindy_bid * 0.8, DAILY_SALARY * 0.4)); return float(bid)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    target_bid = 40.0
    if yesterday_bids:
        target_bid = sum(yesterday_bids) / len(yesterday_bids)

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    return min(my_status['budget'], max(target_bid * 0.95, 35.0))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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
        return min(my_status['budget'], 10.0)
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev * 1.1)
        
    return min(my_status['budget'], max(30.0, avg_prev * 0.95))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.2); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); supply = day_context['supply']; if supply / (len(alive_opponents) + 1) < WATER_REQ: return min(my_status['budget'], avg_bid * 1.1); return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_bid * 0.8))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > DAILY_SALARY:
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        return min(my_status['budget'], max_prev + 5.0)
        
    return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.2, 75.0))
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.9, 45.0))
        
    return float(bid)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    max_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
        
    num_winners = int(supply // WATER_REQ)
    if len(alive_opponents) < num_winners:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    return min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.55))
"""
