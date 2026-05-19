# ============================================================
# Experiment: exp_024
# Agent: David
# Source: exp_024
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

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)

    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = min(avg_bid * 1.05, DAILY_SALARY * 0.95)
        return min(my_status['budget'], float(target_bid))

    return min(my_status['budget'], float(DAILY_SALARY * 0.6))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    bid = avg_prev_bid + 2.0
    return min(my_status['budget'], max(bid, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply >= 20: return min(my_status['budget'], max(20.0, avg_prev * 0.8)); return min(my_status['budget'], max(45.0, avg_prev * 1.05))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], avg_prev_bid * 1.1)
    elif supply < 20:
        bid = min(my_status['budget'], avg_prev_bid * 0.95)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.8)
        
    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 50.0
    
    if supply <= 18:
        bid = min(my_status['budget'], max_prev * 1.1)
    elif my_status['hp'] < 5:
        bid = min(my_status['budget'], DAILY_SALARY * 0.8)
    else:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.9))
        
    return float(max(0, bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.2); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev * 1.1); if supply < 18: return min(my_status['budget'], max(85, max_prev * 0.95)); return min(my_status['budget'], max(40, max_prev * 0.7))
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
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    elif supply < WATER_REQ * (len(alive_opponents) + 1):
        bid = min(my_status['budget'], avg_opp_bid * 1.05)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.85)
        
    return float(max(0.0, bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(bids) / len(bids) if bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], avg_bid * 1.1); return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_bid * 0.9))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if not yesterday_bids: return float(min(my_status['budget'], DAILY_SALARY * 0.6)); avg_bid = sum(yesterday_bids) / len(yesterday_bids); target = avg_bid * 1.05; if my_status['hp'] <= 4: return float(min(my_status['budget'], max(target, DAILY_SALARY * 0.95))); return float(min(my_status['budget'], max(target, DAILY_SALARY * 0.55)))
"""
