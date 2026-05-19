# ============================================================
# Experiment: exp_115
# Agent: David
# Source: exp_115
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = DAILY_SALARY / num_players; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], fair_share * 1.2)
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
        return float(min(my_status['budget'], DAILY_SALARY * 0.5))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_prev * 1.05
    else:
        target_bid = DAILY_SALARY * 0.7
        
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 1.1))
    return float(min(my_status['budget'], target_bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return 1.0
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if hp <= 3:
        return min(budget, max(85.0, avg_prev_bid * 1.1))
    
    if supply < 18:
        return min(budget, max(75.0, avg_prev_bid * 1.05))
        
    return min(budget, max(40.0, avg_prev_bid * 0.8))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev * 1.1, 50)); return min(my_status['budget'], max(avg_prev * 0.8, 30))
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_bid * 1.05
    else:
        target_bid = DAILY_SALARY * 0.6

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [opp.get('previous_trace', {}).get('bid', 0) for opp in alive_opponents if opp.get('previous_trace')]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 30; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.9); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_bid * 1.2); return min(my_status['budget'], avg_bid * 0.8)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents) + 1
    supply = day_context['supply']
    
    # Calculate baseline bid based on competition
    base_bid = DAILY_SALARY * 0.85
    
    # Aggressive bidding if supply is scarce
    if supply < (num_alive * WATER_REQ):
        base_bid = DAILY_SALARY * 0.95
        
    # Look at yesterday's max bid to stay competitive
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        base_bid = max(base_bid, min(max_prev + 2.0, DAILY_SALARY * 1.1))
        
    # Survival priority
    if my_status['hp'] <= 3:
        base_bid = min(my_status['budget'], DAILY_SALARY * 1.2)
        
    return min(my_status['budget'], float(base_bid))
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
    num_competitors = len(alive_opponents)
    
    if num_competitors == 0:
        return 1.0
    
    # Estimate fair share
    fair_share = supply / (num_competitors + 1)
    
    # If supply is high, bid conservatively
    if supply > 20:
        bid = DAILY_SALARY * 0.4
    # If supply is low, bid aggressively to ensure survival
    elif supply < 18:
        bid = DAILY_SALARY * 0.8
    else:
        bid = DAILY_SALARY * 0.6
        
    # Adjust for HP
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], bid * 1.5)
        
    return min(my_status['budget'], float(bid))
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max(avg_opp_bid * 1.1, 50.0))
        return min(my_status['budget'], max(avg_opp_bid * 0.8, 25.0))

    return min(my_status['budget'], 35.0)
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

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], avg_prev_bid * 1.1)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev_bid * 0.95)
    
    return min(my_status['budget'], avg_prev_bid * 0.75)
"""
