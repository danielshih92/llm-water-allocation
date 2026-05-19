# ============================================================
# Experiment: exp_090
# Agent: David
# Source: exp_090
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    num_opponents = len([o for o in opponents_status.values() if o['alive']])
    
    # Conservative opening strategy: bid 50% of salary if healthy, higher if low HP.
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.8)
    
    # Base bid calculation
    base_bid = DAILY_SALARY * 0.5
    
    # Adjust for supply scarcity
    if supply < 18:
        base_bid *= 1.2
        
    return min(my_status['budget'], base_bid)
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
        return float(min(my_status['budget'], 5.0))
        
    yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] < 3:
        return float(min(my_status['budget'], DAILY_SALARY * 1.1))
        
    if supply > 20:
        bid = min(my_status['budget'], avg_opp_bid * 0.8)
    elif supply > 15:
        bid = min(my_status['budget'], avg_opp_bid * 1.05)
    else:
        bid = min(my_status['budget'], DAILY_SALARY * 0.7)
        
    return float(max(1.0, bid))
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
        return float(min(my_status['budget'], 20.0))
    yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    if my_status['hp'] <= 2:
        return float(min(my_status['budget'], max_prev * 1.1 + 5.0))
    if day_context['supply'] < 18:
        return float(min(my_status['budget'], max(max_prev * 1.05, 45.0)))
    return float(min(my_status['budget'], max(max_prev * 0.8, 30.0)))
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
        max_prev = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max_prev + 5.0)
        if max_prev > DAILY_SALARY * 1.2:
            return min(my_status['budget'], DAILY_SALARY * 0.5)
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev + 1.0))

    return min(my_status['budget'], DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], max(85, avg_prev * 1.1)); if supply < 18: return min(my_status['budget'], max(75, avg_prev * 1.05)); return min(my_status['budget'], max(60, avg_prev * 0.9))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    max_prev = max(prev_bids)
    if supply < 18:
        return min(my_status['budget'], max_prev + 5.0)
    
    if max_prev > DAILY_SALARY * 1.1:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev * 0.95))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.1, DAILY_SALARY * 0.8))
    elif supply < 18:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.05, DAILY_SALARY * 0.5))
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.9, DAILY_SALARY * 0.4))
        
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], min(DAILY_SALARY * 1.2, avg_prev * 1.2)); if supply < 18: return min(my_status['budget'], avg_prev * 1.05); return min(my_status['budget'], avg_prev * 0.85)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    cindy_bid = 0
    for name, opp in opponents_status.items():
        if name == 'Cindy' and opp['alive']:
            prev = opp.get('previous_trace', {})
            cindy_bid = prev.get('bid', 140.0)

    if my_status['hp'] <= 3:
        return min(my_status['budget'], 150.0)

    if cindy_bid > 0 and cindy_bid < my_status['budget']:
        return min(my_status['budget'], cindy_bid + 1.0)
    
    if supply < 18:
        return min(my_status['budget'], 120.0)
        
    return min(my_status['budget'], 85.0)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 15)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 30
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    target = max(avg_prev * 1.1, 35)
    return min(my_status['budget'], target)
"""
