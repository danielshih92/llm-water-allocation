# ============================================================
# Experiment: exp_095
# Agent: David
# Source: exp_095
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = DAILY_SALARY / num_players; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.9); return min(my_status['budget'], fair_share * 1.2)
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
        return min(my_status['budget'], 60.0)

    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    if avg_opp_bid > 100:
        return min(my_status['budget'], 50.0)
        
    return min(my_status['budget'], max(65.0, avg_opp_bid + 2.0))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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
            
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
        
    max_prev = max(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max_prev * 1.1 + 5.0))
    
    if supply < 18:
        return float(min(my_status['budget'], max_prev * 0.95))
    
    return float(min(my_status['budget'], max(20.0, max_prev * 0.6)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.8)); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.4))
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if supply < 18:
            return min(my_status['budget'], max(max_prev + 2.0, DAILY_SALARY * 0.7))
        elif my_status['hp'] < 4:
            return min(my_status['budget'], max_prev + 1.0)
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.3, max_prev * 0.5))
            
    return min(my_status['budget'], DAILY_SALARY * 0.4)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70.0
    
    # If supply is tight, bid aggressively. If supply is high, bid conservatively.
    if supply < 18:
        bid = min(my_status['budget'], max(avg_opp_bid * 1.05, DAILY_SALARY * 1.1))
    else:
        bid = min(my_status['budget'], max(avg_opp_bid * 0.9, DAILY_SALARY * 0.6))
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.5)
        
    return float(bid)
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    highest_prev = max(yesterday_bids) if yesterday_bids else 80.0
    
    # Aggressive if survival is at risk, otherwise strategic bidding
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(highest_prev * 1.1, 90.0))
    
    # If supply is tight, bid higher; if abundant, bid lower to save budget
    if supply < 18.0:
        return min(my_status['budget'], max(highest_prev * 1.05, 85.0))
    else:
        return min(my_status['budget'], max(highest_prev * 0.8, 60.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; target_bid = avg_prev_bid * 1.05; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if my_status['hp'] >= 8: return min(my_status['budget'], max(25.0, avg_prev_bid * 0.8)); return min(my_status['budget'], target_bid)
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if supply < 18.0:
        bid = min(my_status['budget'], avg_opp_bid * 1.1)
    elif supply > 22.0:
        bid = min(my_status['budget'], avg_opp_bid * 0.6)
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.9)
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], max(bid, 120.0))
        
    return float(max(0.0, bid))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.7))
    elif supply > 22:
        return min(my_status['budget'], max(avg_prev * 0.8, DAILY_SALARY * 0.4))
    else:
        return min(my_status['budget'], avg_prev * 0.95)
"""
