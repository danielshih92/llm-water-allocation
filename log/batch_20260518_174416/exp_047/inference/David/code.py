# ============================================================
# Experiment: exp_047
# Agent: David
# Source: exp_047
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); base_bid = DAILY_SALARY * 0.5; if num_opponents == 0: return min(my_status['budget'], 10.0); if supply < WATER_REQ * (num_opponents + 1): return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 85; if my_status['hp'] <= 3: return min(my_status['budget'], 95); target = max(avg_prev * 1.05, 82); return float(min(my_status['budget'], target))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0; target_bid = min(my_status['budget'], max(30.0, avg_prev * 0.95)); if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); return target_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid'): avg_bids.append(prev['bid']); avg_bid = sum(avg_bids) / len(avg_bids) if avg_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.5); if day_context['supply'] < 20: return min(my_status['budget'], avg_bid * 1.05); return min(my_status['budget'], avg_bid * 0.95)
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
        return float(min(my_status['budget'], 10.0))
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 30.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.9))
    
    if day_context['supply'] < WATER_REQ * 2:
        return float(min(my_status['budget'], avg_prev * 1.1))
        
    return float(min(my_status['budget'], max(25.0, avg_prev * 0.8)))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
    yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], 115.0))
    if day_context['supply'] < WATER_REQ * 2:
        return float(min(my_status['budget'], max(75.0, max_prev + 5.0)))
    return float(min(my_status['budget'], max(65.0, max_prev * 0.9)) if max_prev > 0 else 60.0)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if day_context['supply'] < 18: target = min(my_status['budget'], max(avg_opp_bid * 1.1, 90)); elif day_context['supply'] > 22: target = min(my_status['budget'], avg_opp_bid * 0.7); else: target = min(my_status['budget'], avg_opp_bid * 0.95); return float(target)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75
    
    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if len(alive_opponents) > 2:
        return min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_prev + 2.0))
    
    return min(my_status['budget'], DAILY_SALARY * 0.95)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); target_bid = 0.0; if supply < WATER_REQ * 2: target_bid = DAILY_SALARY * 0.95; else: target_bid = DAILY_SALARY * 0.6; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid'): target_bid = max(target_bid, prev['bid'] + 1.0); if my_status['hp'] < 3: target_bid = max(target_bid, DAILY_SALARY * 0.98); return min(my_status['budget'], float(target_bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_alive = len(alive_opponents) + 1; supply = day_context['supply']; target_bid = DAILY_SALARY * 0.6; if supply / num_alive < WATER_REQ: target_bid = DAILY_SALARY * 0.85; if my_status['hp'] <= 3: target_bid = min(my_status['budget'], DAILY_SALARY * 0.95); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: max_prev = max(yesterday_bids); if max_prev > target_bid and my_status['hp'] > 2: target_bid = max_prev * 0.9; return min(my_status['budget'], float(target_bid))
"""
