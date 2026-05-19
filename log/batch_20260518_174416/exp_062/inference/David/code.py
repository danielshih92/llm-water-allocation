# ============================================================
# Experiment: exp_062
# Agent: David
# Source: exp_062
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and 'bid' in prev: avg_bid += prev['bid']; count += 1; if count > 0: avg_bid /= count; else: avg_bid = DAILY_SALARY * 0.4; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_bid * 1.2, DAILY_SALARY * 0.8)); if supply < 18: return min(my_status['budget'], max(avg_bid * 1.1, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_bid * 0.9, DAILY_SALARY * 0.4))
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
        return min(my_status['budget'], DAILY_SALARY * 0.5)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], highest_prev_bid + 5.0)
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 0.5))
    return min(my_status['budget'], DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 70; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if supply < 18: return min(my_status['budget'], max_prev + 5); return min(my_status['budget'], max(DAILY_SALARY * 0.8, max_prev * 0.95))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0
    
    # Aggressive bid if supply is low, otherwise moderate
    if supply < 18:
        bid = min(my_status['budget'], max(avg_prev + 5.0, 95.0))
    else:
        bid = min(my_status['budget'], max(avg_prev, 82.0))

    # Emergency survival
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.5)

    return float(bid)
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
        return min(my_status['budget'], 40)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 60
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], avg_bid * 1.2)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_bid * 1.05)
        
    return min(my_status['budget'], avg_bid * 0.95)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid'): avg_bid += prev['bid']; count += 1; if count > 0: avg_bid /= count; else: avg_bid = 75; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], avg_bid * 1.05); return min(my_status['budget'], avg_bid * 0.9)
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    max_prev = max(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max_prev * 1.15 + 5)
    elif my_status['hp'] >= 8:
        bid = min(my_status['budget'], avg_bid * 0.9)
    else:
        bid = min(my_status['budget'], avg_bid * 1.05)
        
    return float(max(10.0, bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_opp_bid * 1.05, DAILY_SALARY * 0.9)); return min(my_status['budget'], max(avg_opp_bid * 0.9, DAILY_SALARY * 0.6))
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
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_bid * 1.2, 75.0))
    if my_status['hp'] >= 8:
        return min(my_status['budget'], avg_bid * 0.8)
    return min(my_status['budget'], avg_bid + 5.0)
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

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    max_prev = max(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 3:
        return min(my_status['budget'], max(avg_bid * 1.2, 70.0))
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max_prev * 1.05)
        
    return min(my_status['budget'], avg_bid * 0.95)
"""
