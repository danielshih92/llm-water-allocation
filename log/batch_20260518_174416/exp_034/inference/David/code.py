# ============================================================
# Experiment: exp_034
# Agent: David
# Source: exp_034
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = DAILY_SALARY / num_players; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], fair_share * 1.2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: avg_bid += prev['bid']; count += 1; avg = (avg_bid / count) if count > 0 else 65; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if my_status['hp'] > 8: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], max(65.0, avg * 0.95))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if not yesterday_bids:
        return min(my_status['budget'], 60.0)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 75.0)
    bid = min(my_status['budget'], max(65.0, avg_prev + 2.0))
    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev = max(prev_bids) if prev_bids else 40
    
    if my_status['hp'] <= 3:
        target = max_prev * 1.2
    elif day_context['supply'] < 18:
        target = max_prev + 5
    else:
        target = max_prev * 0.8

    bid = min(my_status['budget'], max(20, target))
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], max(85.0, avg_opp_bid + 5.0)); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], avg_opp_bid + 2.0); return min(my_status['budget'], avg_opp_bid * 0.8)
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

    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace:
            prev_bids.append(trace['bid'])

    max_prev = max(prev_bids) if prev_bids else 80
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(max_prev + 5.0, 95.0))
    
    target = min(max_prev + 2.0, 90.0)
    return min(my_status['budget'], max(target, 75.0))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] < 4: return min(my_status['budget'], min(80.0, max_prev + 5.0)); if day_context['supply'] < WATER_REQ * (len(alive_opponents) + 1): return min(my_status['budget'], max_prev + 2.0); return min(my_status['budget'], max(40.0, max_prev * 0.9))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    supply = day_context['supply']
    num_players = len(alive_opponents) + 1
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if supply / num_players >= 7:
        return min(my_status['budget'], avg_prev * 0.9)
    else:
        return min(my_status['budget'], avg_prev * 1.15)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 10.0)
        
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(yesterday_bids) if yesterday_bids else 50
    
    if hp <= 3:
        return min(budget, max(max_prev * 1.1, 75.0))
    if supply < 18:
        return min(budget, max(max_prev + 5.0, 60.0))
    return min(budget, max(max_prev * 0.8, 40.0))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; target_bid = avg_prev * 0.95 if supply > 20 else avg_prev * 1.15; if my_status['hp'] <= 3: return min(my_status['budget'], 120.0); return min(my_status['budget'], max(50.0, target_bid))
"""
