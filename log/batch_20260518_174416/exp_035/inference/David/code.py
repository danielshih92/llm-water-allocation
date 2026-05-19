# ============================================================
# Experiment: exp_035
# Agent: David
# Source: exp_035
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 30; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply < 18: return min(my_status['budget'], max(avg_bid * 1.1, 45)); return min(my_status['budget'], max(avg_bid * 0.8, 32))
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(avg_bid * 1.1, 75.0))
    if my_status['hp'] > 8:
        return min(my_status['budget'], avg_bid * 0.8)
    return min(my_status['budget'], avg_bid * 1.05)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = 85.0
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        base_bid = max_prev + 2.0

    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply < 18.0:
        return min(my_status['budget'], max(base_bid, DAILY_SALARY * 0.9))
    
    return min(my_status['budget'], max(DAILY_SALARY * 0.6, base_bid * 0.8))
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
        return float(min(my_status['budget'], 20.0))
    cindy = opponents_status.get('Cindy')
    if cindy and cindy['alive']:
        prev_bid = cindy.get('previous_trace', {}).get('bid', 82.5)
        target = prev_bid + 1.0
    else:
        target = 45.0
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max(target, 85.0)))
    return float(min(my_status['budget'], target))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); cindy = opponents_status.get('Cindy'); cindy_bid = cindy['previous_trace'].get('bid', 50) if cindy and cindy['alive'] else 40; if my_status['hp'] <= 3: return min(my_status['budget'], max(cindy_bid + 5.0, 60.0)); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], cindy_bid + 2.0); return min(my_status['budget'], 35.0)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); return min(my_status['budget'], max(avg_bid * 1.05, 45.0))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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

    # Target Eric's conservative range or slightly above to beat him
    eric_bid = 84.0
    if yesterday_bids:
        eric_bid = min(yesterday_bids) if min(yesterday_bids) > 10 else 80.0

    # If HP is low, prioritize survival
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    # Otherwise bid to beat Eric but stay under aggressive bidders
    bid = min(eric_bid + 2.5, DAILY_SALARY * 1.1)
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); target_bid = max(DAILY_SALARY * 0.6, avg_prev_bid * 1.05); return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5)
    
    if supply < 18:
        return min(my_status['budget'], max(85.0, max_prev * 1.05))
    
    if supply > 22:
        return min(my_status['budget'], 40.0)
        
    return min(my_status['budget'], 75.0)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_bid * 1.1)); if day_context['supply'] < WATER_REQ * 1.5: return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_bid * 1.05)); return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_bid * 0.9))
"""
