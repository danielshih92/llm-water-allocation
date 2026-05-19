# ============================================================
# Experiment: exp_009
# Agent: David
# Source: exp_009
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    num_alive = sum(1 for opp in opponents_status.values() if opp['alive']) + 1
    
    # First day strategy: secure water with a moderate bid
    bid = DAILY_SALARY * 0.5
    
    # Ensure we do not exceed budget
    return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return 0; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_prev * 1.1, 75)); if day_context['supply'] < 20: return min(my_status['budget'], max(avg_prev + 5, 55)); return min(my_status['budget'], max(avg_prev * 0.8, 30))
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
        if max_prev > DAILY_SALARY:
            return min(my_status['budget'], max_prev * 0.95)
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev + 5.0))

    return min(my_status['budget'], DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if not yesterday_bids:
        bid = DAILY_SALARY * 0.5
    else:
        avg_opp = sum(yesterday_bids) / len(yesterday_bids)
        max_opp = max(yesterday_bids)
        
        if day_context['supply'] < WATER_REQ * (len(alive_opponents) + 1):
            bid = min(my_status['budget'], max_opp * 1.05 + 2)
        else:
            bid = min(my_status['budget'], avg_opp * 0.95)

    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)

    return float(max(0, min(my_status['budget'], bid)))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if day_context['supply'] < WATER_REQ * (len(alive_opponents) + 1): return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], avg_prev * 0.95)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; highest_prev_bid = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], max(highest_prev_bid + 5.0, 95.0)); if day_context['supply'] < 18: return min(my_status['budget'], max(highest_prev_bid + 2.0, 85.0)); return min(my_status['budget'], max(highest_prev_bid * 0.9, 75.0))
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
    
    if not yesterday_bids:
        return min(my_status['budget'], 60.0)

    max_prev = max(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
    
    if supply < 18:
        return min(my_status['budget'], max_prev + 2.0)
    
    return min(my_status['budget'], 55.0)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < WATER_REQ * 1.5: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev * 0.9))
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
    num_alive = len(alive_opponents) + 1
    
    # Calculate fair share based on supply
    fair_share_price = (DAILY_SALARY * 1.1) if supply < (num_alive * WATER_REQ) else (DAILY_SALARY * 0.6)
    
    # Look at yesterday's bids to gauge aggression
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            yesterday_bids.append(prev['bid'])
            
    bid = fair_share_price
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If supply is tight, match or slightly exceed top competitor
        if supply < (num_alive * WATER_REQ):
            bid = max(fair_share_price, max_prev * 1.05)
        else:
            bid = max(fair_share_price, max_prev * 0.8)
            
    # Desperation mode
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.5)
        
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; target_bid = max(45.0, avg_prev_bid * 0.95); if my_status['hp'] < 4: target_bid += 25.0; return min(my_status['budget'], target_bid)
"""
