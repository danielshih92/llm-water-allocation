# ============================================================
# Experiment: exp_059
# Agent: David
# Source: exp_059
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    # First day: default to a balanced bid
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))
    
    # Look at yesterday's trace if available
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If opponents are aggressive, match or slightly beat them if budget allows
        if max_prev > DAILY_SALARY * 0.6:
            return float(min(my_status['budget'], max_prev + 2.0))
        return float(min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev + 1.0)))
    
    # Default behavior for start of game
    return float(min(my_status['budget'], DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); highest_prev_bid = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); if highest_prev_bid > DAILY_SALARY * 1.1: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid * 0.95))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):    DAILY_SALARY = 80    WATER_REQ = 7    alive_opponents = [o for o in opponents_status.values() if o['alive']]    if not alive_opponents:        return min(my_status['budget'], 20.0)    yesterday_bids = []    for opp in alive_opponents:        prev = opp.get('previous_trace', {})        if prev and prev.get('bid') is not None:            yesterday_bids.append(prev['bid'])    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0    if my_status['hp'] <= 3:        return min(my_status['budget'], DAILY_SALARY * 0.95)    bid = avg_opp_bid + 5.0    if day_context['supply'] < 18:        bid += 10.0    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_opp_bid * 1.2, 70.0))
    
    if supply < 18:
        return min(my_status['budget'], max(avg_opp_bid * 0.9, 45.0))
        
    return min(my_status['budget'], max(avg_opp_bid * 0.7, 30.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(bids) / len(bids) if bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); target_bid = avg_prev_bid * 0.95 if supply > 20 else avg_prev_bid * 1.05; return min(my_status['budget'], max(DAILY_SALARY * 0.6, target_bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.9)); return min(my_status['budget'], max(avg_prev * 0.95, DAILY_SALARY * 0.7))
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
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max(avg_prev * 1.1, 95.0))
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.05, 85.0))
    return min(my_status['budget'], max(avg_prev * 0.9, 70.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; fair_share = supply / (len(alive_opponents) + 1); if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and 'bid' in prev: bids.append(prev['bid']); if not bids: return min(my_status['budget'], DAILY_SALARY * 0.6); avg_opp_bid = sum(bids) / len(bids); return min(my_status['budget'], max(DAILY_SALARY * 0.55, avg_opp_bid * 1.05))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 20.0)
        
    avg_prev_bid = 0
    bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace:
            bids.append(trace['bid'])
    
    if bids:
        avg_prev_bid = sum(bids) / len(bids)
    
    # Aggressive bidding if HP is low
    if hp <= 3:
        return min(budget, max(avg_prev_bid * 1.1, DAILY_SALARY * 0.9))
    
    # Conservative bidding if supply is high
    if supply > 20:
        return min(budget, max(avg_prev_bid * 0.8, DAILY_SALARY * 0.4))
    
    # Balanced approach
    return min(budget, max(avg_prev_bid * 0.95, DAILY_SALARY * 0.6))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.6; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.95); if day_context['supply'] < 18: return min(my_status['budget'], max(DAILY_SALARY * 0.7, avg_prev * 1.1)); return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev * 0.95))
"""
