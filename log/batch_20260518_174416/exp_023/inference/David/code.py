# ============================================================
# Experiment: exp_023
# Agent: David
# Source: exp_023
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.4; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], max(DAILY_SALARY * 0.35, avg_bid * 1.05))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 30.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_prev = sum(yesterday_bids) / len(yesterday_bids); target = max(avg_prev * 1.1, 35.0); else: target = 40.0; if my_status['hp'] < 3: target = max(target, 60.0); return min(my_status['budget'], float(target))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
    max_prev_bid = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(DAILY_SALARY * 0.9, max_prev_bid + 5))
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], max_prev_bid + 2)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev_bid * 0.9))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max(avg_bid * 1.2, 75.0))
    return min(my_status['budget'], max(avg_bid * 1.05, 55.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(bids) / len(bids) if bids else 140; if my_status['hp'] <= 3: return min(my_status['budget'], max(DAILY_SALARY * 1.5, avg_bid * 1.1)); if supply >= 22: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_bid * 0.9))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if day_context['supply'] < WATER_REQ * 1.5:
        return min(my_status['budget'], max(avg_prev + 5.0, 85.0))
    return min(my_status['budget'], max(avg_prev, 75.0))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 60.0; target = min(avg_prev * 0.85, 75.0) if my_status['hp'] > 5 else min(my_status['budget'], 120.0); return float(min(my_status['budget'], max(target, 40.0)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); cindy = opponents_status.get('Cindy'); cindy_bid = cindy['previous_trace'].get('bid', 0.0) if cindy and cindy.get('previous_trace') else 0.0; if my_status['hp'] <= 3: return min(my_status['budget'], 120.0); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], max(cindy_bid + 5.0, 90.0)); return min(my_status['budget'], max(cindy_bid * 0.9, 60.0))
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

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    # Aggression adjustment based on HP
    if my_status['hp'] < 4:
        bid = avg_prev_bid * 1.2
    elif my_status['hp'] > 8:
        bid = avg_prev_bid * 0.8
    else:
        bid = avg_prev_bid

    # Ensure we don't overspend early
    if day_context['day'] < 3:
        bid = min(bid, DAILY_SALARY * 0.6)

    return float(min(my_status['budget'], max(10.0, bid)))
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
        return min(my_status['budget'], 10.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(avg_bid * 1.2, DAILY_SALARY * 0.8))
    return min(my_status['budget'], max(avg_bid * 0.95, DAILY_SALARY * 0.5))
"""
