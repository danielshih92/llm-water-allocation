# ============================================================
# Experiment: exp_021
# Agent: David
# Source: exp_021
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 35.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] < 3:
            return min(my_status['budget'], max_prev + 5.0)
        return min(my_status['budget'], max_prev + 1.0)

    return min(my_status['budget'], 42.0)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.6); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_prev * 1.1)); if day_context['supply'] < 18: return min(my_status['budget'], max(DAILY_SALARY * 0.7, avg_prev * 1.05)); return min(my_status['budget'], max(DAILY_SALARY * 0.55, avg_prev * 0.95))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev * 1.2, 90.0)); return min(my_status['budget'], max(avg_prev * 0.9, 45.0))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev * 1.1, 75)); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], max(avg_prev + 5, 60)); return min(my_status['budget'], max(avg_prev * 0.9, 45))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); target_bid = avg_prev * 1.05; return min(my_status['budget'], max(DAILY_SALARY * 0.4, target_bid))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70.0
    max_prev = max(yesterday_bids) if yesterday_bids else 80.0

    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(max_prev + 5.0, 85.0))
    elif day_context['supply'] < 20:
        bid = min(my_status['budget'], max(avg_prev + 2.0, 75.0))
    else:
        bid = min(my_status['budget'], max(avg_prev - 5.0, 60.0))

    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); aggressive_threshold = 120; if yesterday_bids and max(yesterday_bids) > aggressive_threshold: bid = min(my_status['budget'], max(DAILY_SALARY * 1.1, max(yesterday_bids) + 1)); else: bid = min(my_status['budget'], DAILY_SALARY * 0.95); if my_status['hp'] < 3: bid = min(my_status['budget'], DAILY_SALARY * 1.5); return float(max(0, bid))
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
        return min(my_status['budget'], DAILY_SALARY * 0.2)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.5
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_prev * 1.15)
    elif day_context['supply'] < 18:
        bid = min(my_status['budget'], avg_prev * 1.05)
    else:
        bid = min(my_status['budget'], avg_prev * 0.9)
    return float(max(1, int(bid)))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.98)

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 0.9:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], max_prev * 1.05)

    return min(my_status['budget'], DAILY_SALARY * 0.85)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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
            
    max_prev = max(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max_prev * 1.1)
        
    if supply < 18:
        return min(my_status['budget'], max(max_prev * 0.95, 85))
    
    if supply > 22:
        return min(my_status['budget'], 65)
        
    return min(my_status['budget'], max_prev * 0.9)
"""
