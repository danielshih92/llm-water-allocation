# ============================================================
# Experiment: exp_063
# Agent: David
# Source: exp_063
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); if my_status['hp'] < 4: return min(my_status['budget'], avg_bid + 5.0); return min(my_status['budget'], max(40.0, avg_bid * 0.9)); return min(my_status['budget'], 45.0)
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
    num_players = len(alive_opponents) + 1
    fair_share = supply / num_players
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
        
    if fair_share >= WATER_REQ:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    if yesterday_bids:
        target = max(yesterday_bids) + 2.0
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, target))
        
    return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 60))
    elif num_opponents == 0:
        bid = 10
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.9, 45))
        
    if day_context['supply'] > 20 and num_opponents < 2:
        bid = bid * 0.7
        
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if my_status['hp'] > 7: return min(my_status['budget'], avg_prev * 0.8); return min(my_status['budget'], avg_prev * 1.1)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; if supply >= 22: return min(my_status['budget'], max(30.0, avg_prev * 0.4)); if supply <= 17: return min(my_status['budget'], max(85.0, avg_prev * 1.05)); return min(my_status['budget'], max(60.0, avg_prev * 0.8))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_opp_bid + 5.0, 60.0))
    
    target_bid = min(avg_opp_bid + 2.0, 55.0)
    return min(my_status['budget'], target_bid)
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
    
    # Scarcity factor
    supply = day_context['supply']
    num_competitors = len(alive_opponents) + 1
    fair_share = supply / num_competitors
    
    bid = avg_prev
    if fair_share < WATER_REQ:
        bid = max(bid, DAILY_SALARY * 0.8)
    elif fair_share > WATER_REQ * 1.5:
        bid = min(bid, DAILY_SALARY * 0.4)
    
    # HP Protection
    if my_status['hp'] <= 3:
        bid = max(bid, DAILY_SALARY * 0.95)
        
    return min(my_status['budget'], max(0.0, bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; if my_status['hp'] <= 3: return min(my_status['budget'], avg_prev * 1.05); return min(my_status['budget'], avg_prev * 0.95)
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
        return min(my_status['budget'], 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        bid = avg_prev * 1.05
    else:
        bid = DAILY_SALARY * 0.8

    if my_status['hp'] < 4:
        bid = max(bid, DAILY_SALARY * 1.1)
        
    return float(min(my_status['budget'], bid))
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

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)

    if supply < 18:
        return min(my_status['budget'], max(avg_prev_bid * 1.1, 75.0))
    
    return min(my_status['budget'], max(avg_prev_bid * 0.9, 45.0))
"""
