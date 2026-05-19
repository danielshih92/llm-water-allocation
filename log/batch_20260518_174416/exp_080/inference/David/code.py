# ============================================================
# Experiment: exp_080
# Agent: David
# Source: exp_080
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if yesterday_bids: highest = max(yesterday_bids); if highest > 60: return min(my_status['budget'], highest + 2.0); return min(my_status['budget'], 45.0); return min(my_status['budget'], 40.0)
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
        return min(my_status['budget'], 10.0)
    yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 85.0)
    if day_context['supply'] < 20:
        return min(my_status['budget'], max(avg_bid + 2.0, 60.0))
    return min(my_status['budget'], max(avg_bid * 0.8, 40.0))
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

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0
    max_prev = max(prev_bids) if prev_bids else 50.0

    # Survival priority
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev * 1.1 + 5.0)
    
    # Competitive bidding based on supply
    if supply < 18:
        bid = max(avg_bid * 1.05, 45.0)
    else:
        bid = min(avg_bid * 0.9, 35.0)

    return min(my_status['budget'], float(bid))
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
        return float(min(my_status['budget'], 20.0))

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 70.0

    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 1.2))

    if supply < WATER_REQ * (len(alive_opponents) + 1):
        return float(min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.85)))
    
    return float(min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.5)))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    bid = avg_prev * 1.05
    if my_status['hp'] <= 3:
        bid = max(bid, 75.0)
    if my_status['hp'] >= 8:
        bid = min(bid, 45.0)
    return min(float(my_status['budget']), float(bid))
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
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 4:
        return min(my_status['budget'], max(avg_prev_bid * 1.1, 75.0))
    return min(my_status['budget'], max(avg_prev_bid * 0.95, 45.0))
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

    avg_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            avg_bids.append(prev['bid'])

    target_bid = 85.0
    if avg_bids:
        target_bid = sum(avg_bids) / len(avg_bids) + 5.0

    if my_status['hp'] <= 3:
        return min(my_status['budget'], target_bid * 1.2)
    
    if day_context['supply'] > 20:
        return min(my_status['budget'], target_bid * 0.8)

    return min(my_status['budget'], target_bid)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        max_prev = max(yesterday_bids)
        
        if my_status['hp'] <= 3:
            bid = min(my_status['budget'], max_prev * 1.1)
        else:
            bid = min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev * 0.95))
    else:
        bid = DAILY_SALARY * 0.6

    return float(max(0, bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_opp_bid = 0; if alive_opponents: bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if bids: avg_opp_bid = sum(bids) / len(bids); target_bid = avg_opp_bid * 1.05 if my_status['hp'] < 5 else avg_opp_bid * 0.95; if supply < WATER_REQ * 1.5: target_bid = max(target_bid, DAILY_SALARY * 1.2); return min(my_status['budget'], max(DAILY_SALARY * 0.6, target_bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.5); if my_status['hp'] > 8: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_prev * 0.95))
"""
