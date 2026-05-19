# ============================================================
# Experiment: exp_098
# Agent: David
# Source: exp_098
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share_bid = (supply / num_agents) * 5; bid = min(my_status['budget'], max(20, fair_share_bid)); return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    target_bid = avg_prev * 1.05
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.85)
    
    return min(my_status['budget'], max(DAILY_SALARY * 0.3, target_bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    bob = opponents_status.get('Bob', {})
    bob_prev_bid = 0
    if bob and 'previous_trace' in bob and bob['previous_trace']:
        bob_prev_bid = bob['previous_trace'].get('bid', 0)

    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(bob_prev_bid + 2.0, DAILY_SALARY * 0.7))
    
    if bob.get('alive', False):
        return min(my_status['budget'], max(bob_prev_bid * 0.9, DAILY_SALARY * 0.4))
        
    return min(my_status['budget'], DAILY_SALARY * 0.35)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], avg_prev_bid * 1.1)
    elif my_status['hp'] >= 8:
        bid = min(my_status['budget'], avg_prev_bid * 0.7)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 0.9)
        
    return max(0.0, float(bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); cindy = opponents_status.get('Cindy'); cindy_bid = cindy['previous_trace'].get('bid', 0) if cindy and cindy.get('previous_trace') else 0; if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], cindy_bid + 5.0 if cindy_bid > 0 else DAILY_SALARY * 0.8); if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], max(DAILY_SALARY * 0.4, cindy_bid * 0.6))
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
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        cindy_prev = opponents_status.get('Cindy', {}).get('previous_trace', {}).get('bid', 0)
        if cindy_prev > 0:
            target = cindy_prev + 1.1
        else:
            target = max(yesterday_bids) + 1.1
    else:
        target = 45.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(target, 75.0))
    return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive = [o for o in opponents_status.values() if o['alive']]; if not alive: return 0.0; bids = [o['previous_trace']['bid'] for o in alive if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(bids) / len(bids) if bids else 40.0; target = min(my_status['budget'], max(avg_bid * 1.1, 45.0)); if my_status['hp'] < 4: return min(my_status['budget'], avg_bid * 1.5); return target
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
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if supply < 18:
            return min(my_status['budget'], max_prev + 5.0)
        return min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.8))

    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_prev * 1.2); return min(my_status['budget'], avg_prev * 0.9)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(float(trace['bid']))
            
    if not prev_bids:
        bid = DAILY_SALARY * 0.6
    else:
        avg_prev = sum(prev_bids) / len(prev_bids)
        if supply < 20:
            bid = avg_prev * 1.05
        else:
            bid = avg_prev * 0.8
            
    if my_status['hp'] < 4:
        bid = max(bid, DAILY_SALARY * 0.9)
        
    return min(float(my_status['budget']), float(bid))
"""
