# ============================================================
# Experiment: exp_072
# Agent: David
# Source: exp_072
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; MIN_SUPPLY = 15; alive_opponents = [o for o in opponents_status.values() if o['alive']]; n = len(alive_opponents) + 1; fair_share_bid = (MIN_SUPPLY / n) * 1.2; return min(my_status['budget'], float(fair_share_bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 60; target_bid = avg_prev + 5; if my_status['hp'] < 5: target_bid += 15; if supply < 18: target_bid += 10; return min(my_status['budget'], max(0, target_bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; max_prev = max(prev_bids) if prev_bids else 30.0; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev + 5.0); if day_context['supply'] < WATER_REQ * len(alive_opponents) + 2: return min(my_status['budget'], max_prev + 2.0); return min(my_status['budget'], max(25.0, max_prev * 0.8))
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))

    avg_opp_bid = 0
    count = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_opp_bid += prev['bid']
            count += 1
    
    baseline = (avg_opp_bid / count) + 5.0 if count > 0 else 40.0
    
    if supply < 18:
        bid = min(my_status['budget'], max(baseline, 65.0))
    elif supply < 22:
        bid = min(my_status['budget'], max(baseline, 45.0))
    else:
        bid = min(my_status['budget'], max(baseline * 0.8, 25.0))
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        
    return float(bid)
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
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < WATER_REQ * len(alive_opponents) / 2:
        return min(my_status['budget'], avg_prev_bid * 1.1)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev_bid * 0.95))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
    
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            prev_bids.append(prev['bid'])
            
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))
    
    if day_context['supply'] < 18:
        return float(min(my_status['budget'], max(avg_prev * 1.1, 50.0)))
        
    return float(min(my_status['budget'], max(avg_prev * 0.8, 35.0)))
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))
    
    if supply < 18.0:
        return float(min(my_status['budget'], avg_opp_bid * 1.1))
    
    return float(min(my_status['budget'], avg_opp_bid * 0.8))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    target_bid = avg_bid * 1.05
    if target_bid > DAILY_SALARY * 0.9:
        target_bid = DAILY_SALARY * 0.9
        
    return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.9)
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

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 1.5:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev + 2.0))

    return min(my_status['budget'], DAILY_SALARY * 0.75)
"""
