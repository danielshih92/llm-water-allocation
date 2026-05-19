# ============================================================
# Experiment: exp_117
# Agent: David
# Source: exp_117
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents)
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    if num_competitors == 0:
        return min(my_status['budget'], 10.0)
    
    # Calculate fair share based on supply
    fair_bid = DAILY_SALARY * 0.4
    
    # Check yesterday's behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > fair_bid:
            return min(my_status['budget'], max_prev + 2.0)
            
    return min(my_status['budget'], fair_bid)
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
        return float(min(my_status['budget'], 20.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    # Aggressive bidding if HP is low, otherwise competitive with historical max
    target_bid = avg_prev * 1.05
    if my_status['hp'] < 4:
        target_bid = max(target_bid, 120.0)
        
    return float(min(my_status['budget'], target_bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_players = len(alive_opponents) + 1
    fair_share_price = day_context['supply'] / num_players
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if yesterday_bids:
        cindy_bid = next((o['previous_trace']['bid'] for o in opponents_status.values() if 'Cindy' in opponents_status and o['previous_trace']), 0)
        if cindy_bid > fair_share_price * 1.5:
            return min(my_status['budget'], fair_share_price * 1.1)
            
    return min(my_status['budget'], fair_share_price * 1.05)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev * 1.1, 75)); return min(my_status['budget'], max(avg_prev * 0.8, 55))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_market = sum(avg_bids) / len(avg_bids) if avg_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], max(DAILY_SALARY * 1.2, avg_market * 1.05)); if day_context['supply'] < 18: return min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_market * 0.9)); return min(my_status['budget'], DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_bid * 1.1); return min(my_status['budget'], avg_bid * 0.95)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] < 4: return min(my_status['budget'], max(DAILY_SALARY * 1.2, avg_opp_bid * 1.1)); if supply < 18: return min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_opp_bid * 1.05)); return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_opp_bid * 0.9))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]; max_prev = max(yesterday_bids) if yesterday_bids else 0; if my_status['hp'] <= 3: return min(my_status['budget'], max(max_prev + 5, DAILY_SALARY * 1.2)); if max_prev > 160: return min(my_status['budget'], DAILY_SALARY * 0.9); return min(my_status['budget'], max(max_prev * 0.95, DAILY_SALARY * 0.8))
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], avg_opp_bid * 1.1)
    elif day_context['supply'] < 18:
        bid = min(my_status['budget'], avg_opp_bid * 1.05)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.85)
        
    return max(0.0, float(bid))
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

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    max_prev = max(prev_bids) if prev_bids else 80.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
    
    if day_context['supply'] < (len(alive_opponents) + 1) * WATER_REQ:
        return min(my_status['budget'], max_prev + 2.0)
        
    return min(my_status['budget'], max(40.0, max_prev * 0.7))
"""
