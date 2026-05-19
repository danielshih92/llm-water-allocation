# ============================================================
# Experiment: exp_109
# Agent: David
# Source: exp_109
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); num_opponents = len(alive_opponents); fair_share = supply / (num_opponents + 1); if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], DAILY_SALARY * 0.45)
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 75.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev_bid * 1.15)
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev_bid * 1.05)
    return min(my_status['budget'], max(60.0, avg_prev_bid * 0.95))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 25.0); cindy_bid = 0; for name, opp in opponents_status.items(): if name == 'Cindy' and 'previous_trace' in opp: cindy_bid = opp['previous_trace'].get('bid', 50); if supply < 18: return min(my_status['budget'], max(cindy_bid * 0.9, 45.0)); if supply > 22: return min(my_status['budget'], 20.0); return min(my_status['budget'], 35.0)
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
        return 10
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40
    
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], avg_prev_bid * 1.2)
    elif my_status['hp'] > 8:
        bid = min(my_status['budget'], avg_prev_bid * 0.8)
    else:
        bid = min(my_status['budget'], avg_prev_bid * 1.05)
        
    return max(5, int(bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 100; if my_status['hp'] <= 3: return min(my_status['budget'], 140); if day_context['supply'] < WATER_REQ * 3: return min(my_status['budget'], int(max(avg_prev * 0.9, 90))); return min(my_status['budget'], int(max(avg_prev * 0.7, 75)))
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 105.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_opp_bid * 1.05, 120.0))
    else:
        bid = min(my_status['budget'], avg_opp_bid * 0.95)
        
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]; max_prev = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] < 4: return min(my_status['budget'], max_prev + 5); if my_status['hp'] > 8: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], max_prev + 2)
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
        return min(my_status['budget'], 50.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    bid = avg_prev_bid * 0.95
    if supply < 20:
        bid += 20.0
        
    return min(my_status['budget'], max(bid, 75.0))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev + 5.0); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], max_prev + 2.0); return min(my_status['budget'], max(40.0, max_prev * 0.9))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] < 4: return min(my_status['budget'], 110.0); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], max(90.0, avg_prev + 5.0)); return min(my_status['budget'], max(75.0, avg_prev - 5.0))
"""
