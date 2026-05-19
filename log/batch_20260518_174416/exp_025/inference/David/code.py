# ============================================================
# Experiment: exp_025
# Agent: David
# Source: exp_025
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_opponents = len(alive_opponents); if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 0.95); if num_opponents == 0: return min(my_status['budget'], DAILY_SALARY * 0.2); avg_bid_needed = (supply / (num_opponents + 1)) * 0.8; return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_bid_needed))
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
        return min(my_status['budget'], 40.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > DAILY_SALARY:
            return min(my_status['budget'], DAILY_SALARY * 0.6)
        return min(my_status['budget'], max_prev + 5.0)
        
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return 1.0
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.1)
    elif supply < 18:
        bid = min(my_status['budget'], max(avg_prev * 1.05, 85.0))
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.9, 65.0))
        
    return float(max(1.0, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 105.0; urgency = 1.0 if my_status['hp'] < 4 else 0.7; supply_factor = 1.0 if day_context['supply'] < 18 else 0.8; bid = avg_prev * urgency * supply_factor; return min(my_status['budget'], max(DAILY_SALARY * 0.6, bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    supply = day_context['supply']
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace')]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0
    
    if supply < WATER_REQ * 2:
        bid = avg_prev + 5.0
    else:
        bid = avg_prev * 0.9
        
    if my_status['hp'] < 3:
        bid = max(bid, DAILY_SALARY * 0.6)
        
    return float(min(my_status['budget'], max(0.0, bid)))
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
        return int(min(my_status['budget'], DAILY_SALARY * 0.4))
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85
    if my_status['hp'] <= 3:
        return int(min(my_status['budget'], DAILY_SALARY * 1.2))
    if day_context['supply'] < WATER_REQ * 2:
        return int(min(my_status['budget'], avg_prev_bid * 1.1))
    return int(min(my_status['budget'], avg_prev_bid * 0.95))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; bid = 40.0; if supply < 18: bid = 75.0; elif supply < 21: bid = 55.0; if my_status['hp'] < 3: bid = min(my_status['budget'], 80.0); for opp in alive_opps: prev = opp.get('previous_trace', {}); if prev and prev.get('bid', 0) > bid: bid = min(my_status['budget'], prev['bid'] + 2.0); return float(min(my_status['budget'], bid))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return 10.0
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70.0
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
        
    if supply < 18:
        return min(my_status['budget'], max(avg_prev * 1.05, 82.0))
        
    return min(my_status['budget'], max(avg_prev * 0.95, 75.0))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] < 4: return min(my_status['budget'], max(60, avg_bid + 5)); if day_context['supply'] < 18: return min(my_status['budget'], max(55, avg_bid)); return min(my_status['budget'], max(45, avg_bid * 0.8))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid'): avg_bid += prev['bid']; count += 1; if count > 0: avg_bid /= count; target_bid = avg_bid + 2; else: target_bid = 85; if my_status['hp'] < 3: return min(my_status['budget'], 110.0); return min(my_status['budget'], max(80.0, target_bid))
"""
