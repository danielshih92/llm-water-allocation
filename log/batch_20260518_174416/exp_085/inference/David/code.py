# ============================================================
# Experiment: exp_085
# Agent: David
# Source: exp_085
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = 1 + len(alive_opponents); fair_share = supply / num_players; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.9); if supply / WATER_REQ >= num_players: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(avg_bid + 5.0, 75.0))
    
    if supply > 20:
        return min(my_status['budget'], 40.0)
    
    return min(my_status['budget'], max(avg_bid * 0.8, 30.0))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; bid = avg_prev + 5.0; if my_status['hp'] < 4: bid += 15.0; if my_status['budget'] < 100: bid = min(bid, my_status['budget'] * 0.8); return float(min(my_status['budget'], max(30.0, bid)))
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] < 4:
        return float(min(my_status['budget'], max(avg_prev_bid * 1.1, 120.0)))
    if day_context['supply'] < 18:
        return float(min(my_status['budget'], avg_prev_bid * 1.05))
    return float(min(my_status['budget'], avg_prev_bid * 0.95))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < WATER_REQ * 1.2: return min(my_status['budget'], avg_bid * 1.1); if supply > WATER_REQ * 2.5: return min(my_status['budget'], DAILY_SALARY * 0.3); return min(my_status['budget'], avg_bid * 0.95)
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
        return float(min(my_status['budget'], 20.0))

    eric_bid = 0.0
    if 'Eric' in opponents_status and opponents_status['Eric'].get('previous_trace'):
        eric_bid = opponents_status['Eric']['previous_trace'].get('bid', 0.0)

    target_bid = 35.0
    if eric_bid > 0:
        target_bid = min(eric_bid + 2.0, 60.0)
    
    if my_status['hp'] < 3:
        target_bid = min(my_status['budget'], 75.0)
    
    if day_context['supply'] < 18.0:
        target_bid += 10.0
        
    return float(min(my_status['budget'], target_bid))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 4:
            return min(my_status['budget'], max_prev + 5.0)
        return min(my_status['budget'], max_prev * 0.95)
    return min(my_status['budget'], 65.0)
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
        return min(my_status['budget'], 10.0)
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    # If supply is high, bid conservatively. If low, match or exceed the average.
    if supply >= 20:
        bid = avg_prev_bid * 0.7
    elif supply <= 16:
        bid = avg_prev_bid * 1.1
    else:
        bid = avg_prev_bid * 0.9
        
    # Emergency survival check
    if my_status['hp'] <= 3:
        bid = max(bid, DAILY_SALARY * 1.2)
        
    return float(min(my_status['budget'], bid))
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
    if not alive_opponents:
        return 10.0

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    cindy_bid = 0
    if 'Cindy' in opponents_status and opponents_status['Cindy']['alive']:
        prev = opponents_status['Cindy'].get('previous_trace', {})
        cindy_bid = prev.get('bid', 0) if prev else 0

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(cindy_bid + 5, 60.0))
    
    if supply < 18:
        return min(my_status['budget'], max(cindy_bid + 2, 45.0))
        
    return min(my_status['budget'], max(cindy_bid * 0.8, 30.0))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if supply < WATER_REQ * 2: return min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_prev_bid * 1.1)); if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev_bid * 0.9))
"""
