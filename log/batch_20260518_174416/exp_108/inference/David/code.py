# ============================================================
# Experiment: exp_108
# Agent: David
# Source: exp_108
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_agents = len(alive_opponents) + 1
    fair_share_price = (supply / num_agents) * 10
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)
        
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            prev_bids.append(prev['bid'])
            
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        return min(my_status['budget'], max(DAILY_SALARY * 0.4, avg_prev * 1.05))
        
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 50.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 80.0
    
    if my_status['hp'] <= 4:
        bid = min(my_status['budget'], max(avg_prev * 1.1, 95.0))
    else:
        bid = min(my_status['budget'], max(avg_prev * 0.95, 75.0))
        
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 100; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.5); bid = avg_prev * 1.05; return min(my_status['budget'], max(bid, DAILY_SALARY * 0.8))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20); cindy_bid = 0; for name, opp in opponents_status.items(): if name == 'Cindy' and opp.get('previous_trace'): cindy_bid = opp['previous_trace'].get('bid', 0); if my_status['hp'] <= 3: return min(my_status['budget'], max(cindy_bid + 5, 40)); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], 35); return min(my_status['budget'], 25)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids); target = min(my_status['budget'], max(40.0, avg_bid + 2.0)); if my_status['hp'] < 4: return min(my_status['budget'], 95.0); return target; return 45.0
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
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    if day_context['supply'] < 18:
        return min(my_status['budget'], max(avg_prev + 5.0, DAILY_SALARY * 0.7))
    return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.45))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70.0; target_bid = avg_prev * 1.05; if my_status['hp'] <= 3: return min(my_status['budget'], max(target_bid, 95.0)); if my_status['hp'] > 7: return min(my_status['budget'], max(50.0, target_bid * 0.8)); return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], DAILY_SALARY * 1.5))
    
    if supply < 18:
        return float(min(my_status['budget'], avg_opp_bid * 1.1))
    elif supply > 22:
        return float(min(my_status['budget'], avg_opp_bid * 0.7))
    else:
        return float(min(my_status['budget'], avg_opp_bid * 0.9))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY; if my_status['hp'] <= 3: return min(my_status['budget'], max(DAILY_SALARY * 1.2, avg_prev * 1.05)); if my_status['hp'] >= 8: return min(my_status['budget'], DAILY_SALARY * 0.6); return min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; bid = 85.0; if len(alive_opponents) > 0: yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_prev = sum(yesterday_bids) / len(yesterday_bids); bid = avg_prev * 0.95; if supply < 18: bid += 15; if my_status['hp'] < 4: bid += 20; return float(min(my_status['budget'], max(0, bid)))
"""
