# ============================================================
# Experiment: exp_102
# Agent: David
# Source: exp_102
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    avg_supply = 20.0
    num_agents = len(opponents_status) + 1
    fair_share = avg_supply / num_agents
    bid = min(my_status['budget'], DAILY_SALARY * 0.45)
    if my_status['hp'] < 5:
        bid = min(my_status['budget'], DAILY_SALARY * 0.7)
    return float(bid)
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
    fair_share = supply / num_agents
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_bid * 1.2, DAILY_SALARY * 0.9))
    else:
        bid = min(my_status['budget'], max(avg_bid * 1.05, DAILY_SALARY * 0.6))
        
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
            
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    max_prev = max(prev_bids)
    avg_prev = sum(prev_bids) / len(prev_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(DAILY_SALARY * 1.1, max_prev * 1.05))
    
    if supply < 18:
        return min(my_status['budget'], max(DAILY_SALARY * 0.8, max_prev * 0.95))
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev * 0.8))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1 + 5)
    
    if supply < 18:
        return min(my_status['budget'], max_prev + 10)
    
    return min(my_status['budget'], max(40, max_prev * 0.8))
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
        return min(my_status['budget'], 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    # Aggressive bidding if HP is low, otherwise competitive with market
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 90.0))
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.95, 75.0))
        
    # Adjust for supply scarcity
    if supply < 18:
        bid += 15.0
        
    return float(min(my_status['budget'], bid))
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if day_context['supply'] < 20:
        return min(my_status['budget'], avg_opp_bid * 1.05)
    return min(my_status['budget'], DAILY_SALARY * 0.75)
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

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    bid = min(my_status['budget'], avg_bid * 1.05)
    return max(10.0, bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_bid * 1.1, DAILY_SALARY * 0.85)); return min(my_status['budget'], max(avg_bid * 0.95, DAILY_SALARY * 0.55))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    supply = day_context['supply']
    num_players = len(alive_opponents) + 1
    
    # Calculate threshold for winning based on supply distribution
    fair_share = supply / num_players
    
    # If supply is tight, bid aggressively
    if fair_share < WATER_REQ:
        base_bid = DAILY_SALARY * 0.9
    else:
        base_bid = DAILY_SALARY * 0.5
        
    # Adjust based on Cindy's high historical bidding
    cindy = opponents_status.get('Cindy', {})
    if cindy.get('alive', False):
        prev_cindy = cindy.get('previous_trace', {})
        if prev_cindy and prev_cindy.get('bid', 0) > base_bid:
            base_bid = min(my_status['budget'], prev_cindy['bid'] + 2.0)
            
    # Ensure we don't exceed budget or spend unnecessarily if HP is high
    if my_status['hp'] > 8:
        base_bid *= 0.7
        
    return float(min(my_status['budget'], max(0, base_bid)))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
            
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev * 1.2)
        
    return min(my_status['budget'], max(35.0, avg_prev * 0.95))
"""
