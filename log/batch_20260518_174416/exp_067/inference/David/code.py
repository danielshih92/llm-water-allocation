# ============================================================
# Experiment: exp_067
# Agent: David
# Source: exp_067
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_alive = len(alive_opponents) + 1; supply = day_context['supply']; if supply / num_alive >= WATER_REQ: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], DAILY_SALARY * 0.75)
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
        return float(min(my_status['budget'], 50.0))
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid')]
    max_prev = max(yesterday_bids) if yesterday_bids else 120.0
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max_prev + 10.0))
    if day_context['supply'] < 20.0:
        return float(min(my_status['budget'], max(125.0, max_prev + 2.0)))
    return float(min(my_status['budget'], max(110.0, max_prev * 0.95)))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.5); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.1, 90)); return min(my_status['budget'], max(avg_prev * 0.95, 75))
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
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_prev = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max_prev * 1.1)
        return min(my_status['budget'], max(avg_bid * 0.9, 45.0))
    return min(my_status['budget'], 50.0)
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
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    cindy = opponents_status.get('Cindy', {})
    cindy_bid = cindy.get('previous_trace', {}).get('bid', 0) if cindy else 0
    
    # If supply is tight, bid to beat Cindy's average, otherwise conserve budget
    if supply < 18:
        bid = max(cindy_bid * 1.1, DAILY_SALARY * 0.6)
    else:
        bid = max(cindy_bid * 0.8, DAILY_SALARY * 0.3)
        
    # Desperation mode
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); alex_prev = opponents_status.get('Alex', {}).get('previous_trace', {}); alex_bid = alex_prev.get('bid', 0) if alex_prev else 0; if my_status['hp'] <= 3: return min(my_status['budget'], 95.0); if day_context['supply'] < 18: return min(my_status['budget'], max(85.0, alex_bid + 2.0)); return min(my_status['budget'], max(75.0, alex_bid + 1.0))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    max_prev = max(prev_bids)
    avg_prev = sum(prev_bids) / len(prev_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(max_prev * 1.05, DAILY_SALARY * 0.9))
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.7))
    
    return min(my_status['budget'], max(avg_prev * 0.8, DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: max_prev = max(yesterday_bids); if my_status['hp'] < 4: return min(my_status['budget'], max_prev + 5.0); if max_prev > DAILY_SALARY * 0.7: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], max(25.0, max_prev * 0.8)); return min(my_status['budget'], 35.0)
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
            
    if not alive_opponents:
        return 10
        
    max_prev = max(yesterday_bids) if yesterday_bids else 70
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max_prev + 5)
    elif supply < 18:
        bid = min(my_status['budget'], max(85, max_prev + 2))
    else:
        bid = min(my_status['budget'], max(65, max_prev * 0.95))
        
    return float(max(0, int(bid)))
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
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_prev + 5.0, 60.0))
    return min(my_status['budget'], max(avg_prev * 0.9, 45.0))
"""
