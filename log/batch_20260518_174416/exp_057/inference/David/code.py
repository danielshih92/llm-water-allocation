# ============================================================
# Experiment: exp_057
# Agent: David
# Source: exp_057
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share = supply / num_agents; bid = min(my_status['budget'], max(20, fair_share * 1.2)); if my_status['hp'] < 3: bid = min(my_status['budget'], DAILY_SALARY * 0.8); return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev_bid * 1.1, 90.0))
    elif my_status['hp'] > 7:
        bid = min(my_status['budget'], max(avg_prev_bid * 0.6, 40.0))
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.9)

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], WATER_REQ * 5); cindy_bid = 0; for name, opp in opponents_status.items(): if name == 'Cindy' and opp['alive']: prev = opp.get('previous_trace', {}); cindy_bid = prev.get('bid', 40) if prev else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if day_context['supply'] < 18: return min(my_status['budget'], cindy_bid + 5); return min(my_status['budget'], max(20, cindy_bid * 0.6))
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
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_prev * 1.5)
    else:
        bid = min(my_status['budget'], avg_prev * 1.1)
        
    return float(max(1.0, min(bid, DAILY_SALARY * 1.2)))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY:
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        return min(my_status['budget'], max_prev + 5.0)
        
    return min(my_status['budget'], DAILY_SALARY * 0.6)
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
        return min(my_status['budget'], 10.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    target_bid = avg_prev_bid * 1.05
    return min(my_status['budget'], max(target_bid, 45.0))
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        bid = avg_prev_bid * 1.05
    else:
        bid = DAILY_SALARY * 0.4

    if my_status['hp'] <= 3:
        bid = max(bid, DAILY_SALARY * 0.8)
    
    return float(min(my_status['budget'], max(bid, 5.0)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: highest_prev_bid = max(yesterday_bids); if my_status['hp'] <= 3: return min(my_status['budget'], max(85.0, highest_prev_bid + 2.0)); return min(my_status['budget'], max(81.0, highest_prev_bid * 0.9)); return min(my_status['budget'], 82.0)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], 120.0); if my_status['hp'] >= 8: return min(my_status['budget'], avg_prev_bid * 0.8); return min(my_status['budget'], avg_prev_bid * 1.05)
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
    
    # Calculate a baseline bid to secure water
    # Since supply is 15-25 and there are ~5 agents, 20/5 = 4. 
    # Bidding around 1.5x-2x salary is aggressive but necessary given opponent history.
    base_bid = DAILY_SALARY * 1.6
    
    if my_status['hp'] <= 4:
        bid = min(my_status['budget'], DAILY_SALARY * 1.9)
    elif my_status['hp'] > 8:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    else:
        bid = min(my_status['budget'], base_bid)
        
    # Adjust based on yesterday's highest observed bid
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > bid:
            bid = min(my_status['budget'], max_prev + 5.0)
            
    return float(bid)
"""
