# ============================================================
# Experiment: exp_030
# Agent: David
# Source: exp_030
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    
    # First day: bid conservatively to preserve budget
    # 50% of salary is a balanced starting point
    bid = DAILY_SALARY * 0.5
    
    # Ensure we do not exceed current budget
    return min(float(my_status['budget']), float(bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], min(90.0, avg_prev * 1.2)); return min(my_status['budget'], min(75.0, avg_prev * 1.05))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(bids) / len(bids) if bids else 45; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_prev * 1.1); return min(my_status['budget'], max(40, avg_prev * 0.8))
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
        return min(my_status['budget'], 10.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if supply < 18:
        return min(my_status['budget'], avg_bid * 1.1)
    return min(my_status['budget'], max(40.0, avg_bid * 0.9))
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

    if my_status['hp'] < 5:
        target_bid = max(target_bid, DAILY_SALARY * 0.85)

    return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    cindy = opponents_status.get('Cindy', {})
    cindy_bid = cindy.get('previous_trace', {}).get('bid', 80.0) if cindy.get('alive') else 0

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(cindy_bid * 1.05, 120.0))
    
    if day_context['supply'] < WATER_REQ * (len(alive_opponents) + 1):
        return min(my_status['budget'], cindy_bid * 0.95)
        
    return min(my_status['budget'], 65.0)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = supply / num_players; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if fair_share < WATER_REQ: return min(my_status['budget'], DAILY_SALARY * 0.85); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50; return min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev * 1.05))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return 0; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); target_bid = min(my_status['budget'], avg_prev * 1.05); return max(target_bid, DAILY_SALARY * 0.6)
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        if day_context['supply'] < 18:
            return min(my_status['budget'], max(avg_prev_bid * 1.1, DAILY_SALARY * 0.6))
        return min(my_status['budget'], avg_prev_bid * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
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
    cindy = opponents_status.get('Cindy', {})
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))

    target_bid = 35.0
    if cindy.get('alive'):
        prev = cindy.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            target_bid = prev['bid'] + 2.0
            
    if my_status['hp'] < 3:
        return float(min(my_status['budget'], DAILY_SALARY * 1.2))
    
    bid = min(my_status['budget'], target_bid)
    return float(max(15.0, bid))
"""
