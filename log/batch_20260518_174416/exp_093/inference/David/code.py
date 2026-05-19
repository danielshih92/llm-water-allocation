# ============================================================
# Experiment: exp_093
# Agent: David
# Source: exp_093
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_count = sum(1 for o in opponents_status.values() if o['alive']); my_fair_share = supply / (alive_count + 1); if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], DAILY_SALARY * 0.45)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; if not yesterday_bids: return min(my_status['budget'], DAILY_SALARY * 0.6); avg_prev = sum(yesterday_bids) / len(yesterday_bids); if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.8)); return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.45))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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

    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_prev + 5.0, 95.0))
    else:
        bid = min(my_status['budget'], max(avg_prev + 1.0, 82.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    
    yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace')]
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_bid * 1.2, 75.0))
    
    if supply < 18:
        return min(my_status['budget'], avg_bid * 1.1)
        
    return min(my_status['budget'], max(avg_bid * 0.8, 30.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive = [o for o in opponents_status.values() if o['alive']]; if not alive: return min(my_status['budget'], 50.0); prev_bids = [o['previous_trace']['bid'] for o in alive if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 80.0; target_bid = min(my_status['budget'], avg_prev * 1.05); if my_status['hp'] < 4: return min(my_status['budget'], target_bid * 1.2); return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_bid * 1.1, 75.0)); if my_status['hp'] > 7: return min(my_status['budget'], avg_bid * 0.8); return min(my_status['budget'], avg_bid * 1.05)
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
        return min(my_status['budget'], DAILY_SALARY * 0.5)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    highest_prev = max(yesterday_bids) if yesterday_bids else 0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(highest_prev * 1.1, DAILY_SALARY * 0.95))
    if highest_prev > DAILY_SALARY * 1.5:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    return min(my_status['budget'], max(highest_prev * 0.95, DAILY_SALARY * 0.75))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70.0
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    else:
        bid = min(my_status['budget'], max(avg_opp_bid + 5.0, 85.0))
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        bid = DAILY_SALARY * 0.6
    else:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        bid = avg_prev * 1.05
        
    if my_status['hp'] < 3:
        bid = min(my_status['budget'], bid * 1.5)
    
    return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 80; if supply < WATER_REQ * 2: bid = min(my_status['budget'], max(avg_prev * 1.05, DAILY_SALARY * 0.9)); elif my_status['hp'] < 4: bid = min(my_status['budget'], DAILY_SALARY * 1.1); else: bid = min(my_status['budget'], max(avg_prev * 0.8, DAILY_SALARY * 0.6)); return float(bid)
"""
