# ============================================================
# Experiment: exp_100
# Agent: David
# Source: exp_100
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share = day_context['supply'] / num_agents; if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.9); bid = DAILY_SALARY * 0.55; return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.05, 60)); return min(my_status['budget'], max(avg_prev * 0.9, 45))
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
    fair_share = day_context['supply'] / num_players
    
    # Analyze yesterday's competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    # Base strategy: bid higher if HP is low, otherwise aim for efficient allocation
    if my_status['hp'] < 4:
        bid = DAILY_SALARY * 0.8
    elif fair_share >= WATER_REQ:
        bid = DAILY_SALARY * 0.4
    else:
        bid = DAILY_SALARY * 0.6
        
    # Adjust for aggressive opponents
    if yesterday_bids and max(yesterday_bids) > bid:
        bid = min(my_status['budget'], max(bid, max(yesterday_bids) * 0.95))
        
    return float(min(my_status['budget'], bid))
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_bid = max(yesterday_bids)
        
        if my_status['hp'] <= 4:
            bid = min(my_status['budget'], max_bid * 1.05 + 5.0)
        else:
            bid = min(my_status['budget'], max(avg_bid, 60.0))
    else:
        bid = 70.0

    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); cindy_bid = 0; for name, opp in opponents_status.items(): if name == 'Cindy' and opp['alive']: prev = opp.get('previous_trace', {}); cindy_bid = prev.get('bid', 0) if prev else 115; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], cindy_bid + 2.0); return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    
    if not alive_opponents:
        return 10

    target_bid = 16
    if my_status['hp'] < 4:
        target_bid = 25
    
    # Check Cindy's high bids and Eric's low bids
    for name, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid', 0) > target_bid and name != 'Cindy':
            target_bid = prev['bid'] + 1
            
    if supply < 16:
        target_bid += 10
        
    return int(min(my_status['budget'], target_bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return 0.0; cindy_prev = opponents_status.get('Cindy', {}).get('previous_trace', {}); cindy_bid = cindy_prev.get('bid', 40.0) if cindy_prev else 40.0; target_bid = cindy_bid + 2.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); return min(my_status['budget'], max(35.0, target_bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev_bid * 1.05, 75.0))
    
    return min(my_status['budget'], max(avg_prev_bid * 0.95, 50.0))
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    max_prev = max(yesterday_bids)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev + 2.0, DAILY_SALARY * 0.7))
    
    return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.4))
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
        return min(my_status['budget'], 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_prev * 1.1, 75.0))
    
    target_bid = max(avg_prev * 0.9, 45.0)
    return min(my_status['budget'], target_bid)
"""
