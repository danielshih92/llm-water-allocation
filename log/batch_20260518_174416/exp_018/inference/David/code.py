# ============================================================
# Experiment: exp_018
# Agent: David
# Source: exp_018
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; SUPPLY = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; fair_share = DAILY_SALARY / (len(alive_opponents) + 1); if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], fair_share * 1.2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85; if my_status['hp'] <= 3: return min(my_status['budget'], 130.0); if supply < 18: return min(my_status['budget'], max(90.0, avg_bid + 5)); return min(my_status['budget'], max(85.0, avg_bid * 0.95))
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
        return min(my_status['budget'], 20.0)

    bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bids.append(prev['bid'])
            
    avg_prev_bid = sum(bids) / len(bids) if bids else 80.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_prev_bid * 1.1)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.9)
        
    return max(10.0, float(bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_bid * 1.1, 70)); if day_context['supply'] < 18: return min(my_status['budget'], avg_bid * 1.05); return min(my_status['budget'], max(35, avg_bid * 0.95))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 15.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev = max(yesterday_bids) if yesterday_bids else 15.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max_prev + 5.0)
    
    if supply < 18:
        return min(my_status['budget'], max(20.0, max_prev + 2.0))
        
    return min(my_status['budget'], 16.0)
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
        return min(my_status['budget'], float(DAILY_SALARY * 0.2))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 3:
        return min(my_status['budget'], float(DAILY_SALARY * 0.95))
    
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = avg_prev * 1.05
    else:
        target = DAILY_SALARY * 0.6

    return min(my_status['budget'], float(target))
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
    
    cindy = opponents_status.get('Cindy', {})
    cindy_prev = cindy.get('previous_trace', {}) if cindy else {}
    cindy_bid = cindy_prev.get('bid', 0) if cindy_prev else 0
    
    if supply < WATER_REQ * 2:
        bid = min(my_status['budget'], max(cindy_bid + 2, DAILY_SALARY * 0.9))
    elif supply < WATER_REQ * 3:
        bid = min(my_status['budget'], max(cindy_bid * 0.8, DAILY_SALARY * 0.5))
    else:
        bid = min(my_status['budget'], DAILY_SALARY * 0.3)
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        
    return float(bid)
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
        return min(my_status['budget'], 10.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev_bid * 1.2)
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev_bid * 1.1)
    return min(my_status['budget'], max(35.0, avg_prev_bid * 0.95))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.5); target = avg_prev * 1.05; return float(min(my_status['budget'], max(target, DAILY_SALARY * 0.8)))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))

    yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0

    if supply < 18:
        bid = min(my_status['budget'], max(avg_bid * 0.9, 75.0))
    elif supply > 22:
        bid = min(my_status['budget'], max(avg_bid * 0.5, 30.0))
    else:
        bid = min(my_status['budget'], avg_bid * 0.7)

    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
        
    return float(bid)
"""
