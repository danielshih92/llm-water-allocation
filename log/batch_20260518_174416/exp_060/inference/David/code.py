# ============================================================
# Experiment: exp_060
# Agent: David
# Source: exp_060
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_alive = len(alive_opponents) + 1; fair_share = supply / num_alive; base_bid = DAILY_SALARY * 0.4; if my_status['hp'] < 4: base_bid = DAILY_SALARY * 0.7; if supply < 18: base_bid += 10; return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev_bid + 2, DAILY_SALARY * 0.85)); return min(my_status['budget'], max(avg_prev_bid * 0.9, DAILY_SALARY * 0.5))
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
        return min(my_status['budget'], 50.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 105.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_opp_bid + 15.0)
    if day_context['supply'] < 18.0:
        return min(my_status['budget'], avg_opp_bid + 5.0)
    return min(my_status['budget'], avg_opp_bid * 0.9)
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
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
    
    avg_bid_needed = supply / (len(alive_opponents) + 1)
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 0.7:
            return float(min(my_status['budget'], DAILY_SALARY * 0.3))
        return float(min(my_status['budget'], max(avg_bid_needed * 1.1, max_prev + 2.0)))
        
    return float(min(my_status['budget'], DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] < 4:
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if supply < 18:
            return float(min(my_status['budget'], max_prev + 5.0))
        return float(min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev * 0.8)))
        
    return float(min(my_status['budget'], DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 10.0)
    
    avg_opp_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_opp_bids.append(prev['bid'])
    
    avg_bid = sum(avg_opp_bids) / len(avg_opp_bids) if avg_opp_bids else 50.0
    
    if hp <= 3:
        return min(budget, avg_bid * 1.2)
    
    if supply < 18:
        return min(budget, avg_bid * 1.05)
    
    return min(budget, avg_bid * 0.9)
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
        return 10.0

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_prev * 1.1, 75.0))
    
    if supply < 18:
        return min(my_status['budget'], avg_prev * 1.05)
    
    return min(my_status['budget'], max(45.0, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context.get('supply', 20)
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 60.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_opp_bid * 1.2)
    
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], avg_opp_bid * 1.05)
    
    return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_opp_bid * 0.9))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_alive = len(alive_opponents) + 1; fair_share = supply / num_alive; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], max(max_prev * 1.1, 75)); if fair_share >= WATER_REQ: return min(my_status['budget'], max(20.0, max_prev * 0.8)); return min(my_status['budget'], max(40.0, max_prev * 1.05))
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
    
    # Determine competitive baseline based on supply
    # If supply is tight, bid higher to ensure allocation
    if supply < 18:
        base_bid = DAILY_SALARY * 0.9
    else:
        base_bid = DAILY_SALARY * 0.6

    # Look at yesterday's behavior
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If opponents are bidding aggressively, match or slightly exceed if HP is low
        if my_status['hp'] <= 3:
            return min(my_status['budget'], max(base_bid, max_prev + 5.0))
        # Otherwise, bid conservatively to save budget
        return min(my_status['budget'], max(base_bid, max_prev * 0.95))
        
    return min(my_status['budget'], base_bid)
"""
