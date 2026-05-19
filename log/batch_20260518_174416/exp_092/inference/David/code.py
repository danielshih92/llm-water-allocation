# ============================================================
# Experiment: exp_092
# Agent: David
# Source: exp_092
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; bid = 0; if not alive_opps: bid = DAILY_SALARY * 0.2; else: prev_bids = [o['previous_trace']['bid'] for o in alive_opps if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 30; if supply < 18: bid = min(my_status['budget'], max(avg_prev * 1.1, 40)); else: bid = min(my_status['budget'], max(avg_prev * 0.8, 25)); if my_status['hp'] < 4: bid = min(my_status['budget'], bid * 1.5); return float(min(int(my_status['budget']), int(bid)))
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 1.2)

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = avg_prev * 0.95
    else:
        target = DAILY_SALARY * 0.7

    bid = max(target, DAILY_SALARY * 0.5)
    return min(my_status['budget'], float(bid))
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
        return min(my_status['budget'], 10.0)

    cindy_bid = 0
    if 'Cindy' in opponents_status and opponents_status['Cindy']['alive']:
        prev = opponents_status['Cindy'].get('previous_trace', {})
        cindy_bid = prev.get('bid', 80.0)

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if cindy_bid > 0:
        target = cindy_bid * 0.95
        return min(my_status['budget'], max(35.0, target))
    
    return min(my_status['budget'], 45.0)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], avg_prev_bid * 1.2)
    elif supply < 18:
        bid = min(my_status['budget'], avg_prev_bid * 1.05)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.8)
        
    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 66.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    if day_context['supply'] < 20:
        return min(my_status['budget'], avg_opp_bid + 5.0)
    return min(my_status['budget'], avg_opp_bid + 1.0)
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
        return min(my_status['budget'], 10.0)
    
    cindy = opponents_status.get('Cindy', {})
    if cindy.get('alive'):
        target_bid = 95.0
    else:
        target_bid = 25.0
        
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); aggressive_threshold = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], aggressive_threshold + 5.0); if my_status['hp'] > 7: return min(my_status['budget'], 40.0); return min(my_status['budget'], aggressive_threshold + 2.0)
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
        return 10.0
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    max_prev = max(yesterday_bids) if yesterday_bids else 30.0
    
    # Cindy is the main threat; if she bids 90, we prioritize survival if HP is low
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 95.0)
    
    # Calculate bid based on supply availability
    fair_bid = 25.0 + (max_prev * 0.1)
    if supply < 18:
        return min(my_status['budget'], max_prev + 5.0)
    
    return min(my_status['budget'], fair_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        bid = avg_prev + 2.0
    else:
        bid = DAILY_SALARY * 0.4

    if my_status['hp'] < 4:
        bid = max(bid, DAILY_SALARY * 0.6)
    
    return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): import math; WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); cindy_bid = 85.0; for name, opp in opponents_status.items(): if name == 'Cindy' and opp.get('previous_trace'): cindy_bid = opp['previous_trace'].get('bid', 85.0); target_bid = cindy_bid + 1.0 if supply < 18 else cindy_bid * 0.7; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); return min(my_status['budget'], max(20.0, target_bid))
"""
