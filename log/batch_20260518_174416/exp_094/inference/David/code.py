# ============================================================
# Experiment: exp_094
# Agent: David
# Source: exp_094
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; if not alive_opps: return min(my_status['budget'], DAILY_SALARY * 0.4); prev_bids = [o['previous_trace']['bid'] for o in alive_opps if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if prev_bids: max_prev = max(prev_bids); if my_status['hp'] < 3: return min(my_status['budget'], max_prev + 5); return min(my_status['budget'], max_prev + 1); return min(my_status['budget'], DAILY_SALARY * 0.35)
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
        return min(my_status['budget'], 40)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max(highest_prev + 5, 85))
        return min(my_status['budget'], max(highest_prev + 1, 75))

    return min(my_status['budget'], 75)
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
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev * 1.2)
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev * 1.1)
    return min(my_status['budget'], avg_prev * 0.9)
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
        return float(min(my_status['budget'], DAILY_SALARY * 0.5))
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 80.0
    bid = avg_prev * 1.05
    if my_status['hp'] < 4:
        bid = max(bid, DAILY_SALARY * 1.2)
    return float(min(my_status['budget'], bid))
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
    num_alive = len(alive_opponents) + 1
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        bid = DAILY_SALARY * 1.1
    else:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
        bid = max(avg_prev, max_prev) * 1.05

    if my_status['hp'] < 4:
        bid = max(bid, DAILY_SALARY * 1.5)
    
    if supply < WATER_REQ * num_alive:
        bid = max(bid, DAILY_SALARY * 1.2)
        
    return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive = [o for o in opponents_status.values() if o['alive']]; if not alive: return 10.0; prev_bids = [o['previous_trace']['bid'] for o in alive if o['previous_trace'] and o['previous_trace']['bid'] is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 50.0; target = avg_prev + 5.0; if my_status['hp'] < 4: target += 20.0; return float(min(my_status['budget'], max(target, 45.0)))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return 10; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_yesterday = max(yesterday_bids) if yesterday_bids else 0; if my_status['hp'] <= 3: return min(my_status['budget'], 90); if max_yesterday < 20: return 21; if max_yesterday < 80: return min(my_status['budget'], max_yesterday + 2); return min(my_status['budget'], 15)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    cindy = opponents_status.get('Cindy')
    cindy_prev_bid = 0
    if cindy and cindy.get('previous_trace'):
        cindy_prev_bid = cindy['previous_trace'].get('bid', 0)

    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(cindy_prev_bid + 5.0, 60.0))
    
    if day_context['supply'] >= 20:
        return min(my_status['budget'], max(cindy_prev_bid * 0.5, 30.0))

    return min(my_status['budget'], max(cindy_prev_bid + 2.0, 45.0))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; target_bid = 45.0; if yesterday_bids: target_bid = sum(yesterday_bids) / len(yesterday_bids) + 2.0; if my_status['hp'] <= 3: target_bid = max(target_bid, 65.0); return min(float(my_status['budget']), float(target_bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_status['hp'] < 4:
            return float(min(my_status['budget'], max(highest_prev_bid + 2.0, DAILY_SALARY * 0.9)))
        if highest_prev_bid > DAILY_SALARY * 1.2:
            return float(min(my_status['budget'], DAILY_SALARY * 0.3))
        return float(min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 1.0)))
    return float(min(my_status['budget'], DAILY_SALARY * 0.6))
"""
