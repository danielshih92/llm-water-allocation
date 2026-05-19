# ============================================================
# Experiment: exp_049
# Agent: David
# Source: exp_049
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: highest_prev = max(yesterday_bids); if my_status['hp'] <= 2: return min(my_status['budget'], max(highest_prev * 1.1, DAILY_SALARY * 0.8)); return min(my_status['budget'], max(highest_prev * 0.9, DAILY_SALARY * 0.4)); return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 85; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < (len(alive_opponents) + 1) * WATER_REQ: return min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_prev * 0.95)); return min(my_status['budget'], DAILY_SALARY * 0.75)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        bid = min(my_status['budget'], avg_prev + 5.0)
        return max(20.0, bid)

    return min(my_status['budget'], 55.0)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0; bid = avg_prev * 1.05; if my_status['hp'] < 4: bid = max(bid, 95.0); return min(my_status['budget'], float(bid))
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
            yesterday_bids.append(prev['bid'])
            
    avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    max_prev = max(yesterday_bids) if yesterday_bids else 40.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 0.9))
    
    if day_context['supply'] >= (len(alive_opponents) + 1) * WATER_REQ:
        return float(min(my_status['budget'], avg_bid * 0.8))
    
    return float(min(my_status['budget'], max_prev + 2.0))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] < 4: return min(my_status['budget'], int(max(avg_bid * 1.1, DAILY_SALARY * 0.7))); if day_context['supply'] < 18: return min(my_status['budget'], int(avg_bid * 1.05)); return min(my_status['budget'], int(avg_bid * 0.9))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], max_prev + 5.0); if supply >= 22: return min(my_status['budget'], 20.0); return min(my_status['budget'], max(85.0, max_prev + 2.0))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 25.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.9); supply_factor = (25 - day_context['supply']) / 10; target_bid = avg_bid * (1 + supply_factor * 0.2); return float(min(my_status['budget'], max(20.0, target_bid)))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = supply / num_players; avg_opp_bid = 0; count = 0; for opp in alive_opponents: trace = opp.get('previous_trace', {}); if trace and 'bid' in trace: avg_opp_bid += trace['bid']; count += 1; if count > 0: avg_opp_bid /= count; else: avg_opp_bid = 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if supply < WATER_REQ * 1.5: return min(my_status['budget'], DAILY_SALARY * 0.85); target = max(avg_opp_bid * 1.05, DAILY_SALARY * 0.4); return min(my_status['budget'], target)
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
        return float(min(my_status['budget'], 10.0))
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 85.0
    
    if my_status['hp'] < 4:
        return float(min(my_status['budget'], max(avg_prev + 5.0, 105.0)))
    
    target = avg_prev + 2.0
    if target > 110.0:
        return float(min(my_status['budget'], 75.0))
    return float(min(my_status['budget'], target))
"""
