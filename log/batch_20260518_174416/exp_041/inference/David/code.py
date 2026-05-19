# ============================================================
# Experiment: exp_041
# Agent: David
# Source: exp_041
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_agents = len(alive_opponents) + 1
    fair_share = DAILY_SALARY / num_agents
    if my_status['hp'] < 3:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    return min(my_status['budget'], fair_share * 1.1)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_prev * 0.95
    else:
        target_bid = DAILY_SALARY * 0.6

    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.45))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0; scarcity_factor = 1.0 if day_context['supply'] < 18 else 0.8; bid = min(my_status['budget'], max(avg_prev * 0.95, 65.0) * scarcity_factor); if my_status['hp'] < 4: bid = min(my_status['budget'], bid * 1.3); return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.2); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], min(DAILY_SALARY * 1.3, avg_prev_bid * 1.05)); return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev_bid * 0.9))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        max_prev = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.8))
        if max_prev > DAILY_SALARY * 1.2:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        return min(my_status['budget'], avg_prev * 1.05)
    return min(my_status['budget'], DAILY_SALARY * 0.6)
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

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 50.0
    
    # If supply is low, bid high to secure water
    if supply < 18:
        return min(my_status['budget'], max_prev + 10.0, DAILY_SALARY * 1.1)
    
    # If HP is low, prioritize survival
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max_prev + 5.0, DAILY_SALARY * 0.9)
    
    # Standard bidding to conserve budget
    return min(my_status['budget'], max(30.0, max_prev * 0.9))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 50)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    highest_prev = max(yesterday_bids) if yesterday_bids else 80
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(highest_prev + 5, 95))
    if day_context['supply'] < 18:
        return min(my_status['budget'], highest_prev + 2)
    return min(my_status['budget'], max(70, highest_prev * 0.95))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.3))

    cindy = opponents_status.get('Cindy', {})
    cindy_bid = 0
    if cindy.get('alive') and cindy.get('previous_trace'):
        cindy_bid = cindy['previous_trace'].get('bid', 0)

    if my_status['hp'] <= 2:
        return float(min(my_status['budget'], DAILY_SALARY * 1.2))

    if supply < WATER_REQ * (len(alive_opponents) + 1):
        target = max(cindy_bid * 1.05, DAILY_SALARY * 0.7)
        return float(min(my_status['budget'], target))

    return float(min(my_status['budget'], max(DAILY_SALARY * 0.4, cindy_bid * 0.9)))
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
        return min(my_status['budget'], 45.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] < 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_opp_bid * 1.1)
    return min(my_status['budget'], max(50.0, avg_opp_bid * 0.95))
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
    
    # Calculate competitive threshold based on yesterday's aggressive bidders
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    max_prev = max(yesterday_bids) if yesterday_bids else 80
    
    # Strategy: If supply is tight relative to requirement, bid high to guarantee survival.
    # If supply is abundant, bid moderately to save budget.
    if supply < WATER_REQ * 2:
        bid = max_prev * 1.05
    else:
        bid = min(max_prev * 0.8, DAILY_SALARY * 0.7)
        
    # Final safety check
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max_prev * 1.2)
        
    return float(min(my_status['budget'], max(0, bid)))
"""
