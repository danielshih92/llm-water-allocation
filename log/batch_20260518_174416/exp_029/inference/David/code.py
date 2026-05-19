# ============================================================
# Experiment: exp_029
# Agent: David
# Source: exp_029
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = DAILY_SALARY / num_players; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], fair_share * 1.2)
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
    num_agents = len(alive_opponents) + 1
    fair_share_bid = (supply / num_agents) * 1.1
    if my_status['hp'] < 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    if my_status['hp'] > 8:
        return min(my_status['budget'], fair_share_bid * 0.8)
    return min(my_status['budget'], max(fair_share_bid, DAILY_SALARY * 0.4))
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
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.1)
    elif my_status['hp'] > 7:
        bid = min(my_status['budget'], avg_prev * 0.8)
    else:
        bid = min(my_status['budget'], avg_prev * 1.05)
        
    return max(1.0, float(bid))
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

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    # Aggressive if low HP, otherwise competitive based on Cindy/Alex trends
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    else:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.05, 75.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70.0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_opp_bid + 5.0); return min(my_status['budget'], avg_opp_bid * 1.05)
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
    num_players = len(alive_opponents) + 1
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40

    if supply / num_players < WATER_REQ:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev_bid * 1.05))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); bid = 35.0; if alive_opponents: cindy = opponents_status.get('Cindy'); if cindy and cindy['alive']: bid = max(bid, 45.0); if my_status['hp'] <= 3: bid = min(my_status['budget'], bid * 1.5); if my_status['hp'] >= 8: bid = min(my_status['budget'], 30.0); return float(min(my_status['budget'], bid))
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

    bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(bids) / len(bids) if bids else 40.0
    max_bid = max(bids) if bids else 60.0

    if supply < WATER_REQ * 1.5:
        bid = min(my_status['budget'], max_bid + 5.0)
    elif supply < WATER_REQ * 2.5:
        bid = min(my_status['budget'], avg_bid + 2.0)
    else:
        bid = min(my_status['budget'], max(20.0, avg_bid - 5.0))

    if my_status['hp'] < 3:
        return min(my_status['budget'], max_bid + 10.0)
        
    return float(bid)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1)
    
    if supply < 18:
        return min(my_status['budget'], max(85, max_prev * 1.05))
    
    if supply > 22:
        return min(my_status['budget'], 60)
        
    return min(my_status['budget'], max(75, max_prev * 0.95))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    cindy_bid = next((o['previous_trace']['bid'] for o in opponents_status.values() if 'Cindy' in opponents_status and o.get('previous_trace')), 80.0)
    if my_status['hp'] < 4:
        return min(my_status['budget'], 95.0)
    if yesterday_bids and max(yesterday_bids) > 100:
        return min(my_status['budget'], 110.0)
    target = max(cindy_bid * 1.05, 75.0)
    return min(my_status['budget'], target)
"""
