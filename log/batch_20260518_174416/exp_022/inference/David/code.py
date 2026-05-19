# ============================================================
# Experiment: exp_022
# Agent: David
# Source: exp_022
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); bid = avg_bid * 1.1; else: bid = DAILY_SALARY * 0.5; if my_status['hp'] < 3: bid = min(my_status['budget'], bid * 1.5); return float(min(my_status['budget'], max(bid, 5.0)))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; target_bid = 0.0; if yesterday_bids: target_bid = sum(yesterday_bids) / len(yesterday_bids) + 2.0; else: target_bid = DAILY_SALARY * 0.4; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.35))
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
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    cindy_bid = 116.4
    alex_bid = 84.0
    
    # Strategy: Aggressive bidding if low HP, else competitive bidding
    if my_status['hp'] <= 3:
        target_bid = 120.0
    else:
        target_bid = max(alex_bid + 2.0, 85.0)
        
    # Check if supply is scarce
    if supply < 18:
        target_bid += 15.0
        
    return float(min(int(my_status['budget']), int(target_bid)))
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
        return min(my_status['budget'], 25.0)

    cindy = opponents_status.get('Cindy', {})
    prev_cindy = cindy.get('previous_trace', {})
    cindy_bid = prev_cindy.get('bid', 0) if prev_cindy else 0
    
    # Target a bid that beats others but stays within salary
    # Cindy is aggressive, so we match or slightly exceed her if necessary
    target_bid = 35.0
    if cindy_bid > 0 and cindy_bid < 70:
        target_bid = cindy_bid + 2.5
    elif cindy_bid >= 70:
        target_bid = 75.0
        
    # Desperation mode
    if my_status['hp'] <= 3:
        target_bid = min(my_status['budget'], 80.0)
        
    return float(min(my_status['budget'], target_bid))
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
        return min(my_status['budget'], 20.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.6
    
    if my_status['hp'] < 5:
        return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.85))
    
    if supply < 18:
        return min(my_status['budget'], max(avg_prev, DAILY_SALARY * 0.75))
        
    return min(my_status['budget'], avg_prev * 0.95)
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
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    target_bid = DAILY_SALARY * 0.6
    if prev_bids:
        max_prev = max(prev_bids)
        target_bid = max_prev + 2.0

    if my_status['hp'] < 4:
        target_bid = max(target_bid, DAILY_SALARY * 0.95)
    
    if supply < WATER_REQ * (len(alive_opponents) + 1) * 0.5:
        target_bid = max(target_bid, DAILY_SALARY * 1.1)

    return min(float(my_status['budget']), float(target_bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] < 3:
        return float(min(my_status['budget'], 120.0))
    if day_context['supply'] < 18.0:
        return float(min(my_status['budget'], avg_bid + 5.0))
    return float(min(my_status['budget'], max(75.0, avg_bid * 0.95)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]; highest_prev = max(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], 95.0); if day_context['supply'] / (len(alive_opponents) + 1) < WATER_REQ: return min(my_status['budget'], highest_prev + 5.0); return min(my_status['budget'], max(60.0, highest_prev * 0.95))
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
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 3:
            return min(my_status['budget'], max_prev + 5.0)
        if supply < 18:
            return min(my_status['budget'], max_prev + 2.0)
        return min(my_status['budget'], max_prev * 0.6)

    return min(my_status['budget'], 45.0)
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
        return float(min(my_status['budget'], 20.0))
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    max_prev = max(yesterday_bids) if yesterday_bids else 60.0
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max_prev * 1.1 + 5.0)
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.9, 45.0))
    return float(bid)
"""
