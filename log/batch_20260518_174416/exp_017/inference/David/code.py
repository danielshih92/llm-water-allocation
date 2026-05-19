# ============================================================
# Experiment: exp_017
# Agent: David
# Source: exp_017
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share = day_context['supply'] / num_agents; bid = min(my_status['budget'], max(20.0, fair_share * 1.5)); return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = min(max_prev + 2.0, avg_prev * 1.1)
    else:
        target_bid = DAILY_SALARY * 0.4

    if my_status['hp'] < 4:
        return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.8))
    
    if supply < (len(alive_opponents) + 1) * WATER_REQ:
        return min(my_status['budget'], max(target_bid, DAILY_SALARY * 0.6))
        
    return min(my_status['budget'], max(target_bid * 0.8, 15.0))
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
        return min(my_status['budget'], 10)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.8)
        
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > 60:
            return min(my_status['budget'], max_prev + 5)
        return min(my_status['budget'], 45)
        
    return min(my_status['budget'], 35)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; if not alive_opps: return min(my_status['budget'], DAILY_SALARY * 0.3); cindy = opponents_status.get('Cindy', {}); cindy_prev = cindy.get('previous_trace', {}).get('bid', 158.4); if supply < WATER_REQ * 1.5: return min(my_status['budget'], DAILY_SALARY * 1.2); if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if cindy.get('alive', False): return min(my_status['budget'], min(cindy_prev * 0.95, DAILY_SALARY * 0.9)); return min(my_status['budget'], DAILY_SALARY * 0.6)
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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_prev_bid + 2.0
    else:
        target_bid = DAILY_SALARY * 0.5

    if my_status['hp'] < 5:
        target_bid += 15.0
    
    if day_context['supply'] < 18:
        target_bid += 5.0

    return min(my_status['budget'], max(0, target_bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max(avg_prev * 1.1, 45.0))
        return min(my_status['budget'], max(avg_prev * 0.8, 30.0))
    return min(my_status['budget'], 35.0)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.6; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); target = avg_bid * 1.05; return min(my_status['budget'], max(DAILY_SALARY * 0.5, target))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0; base_bid = avg_prev * 1.05; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], base_bid * 1.1); return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return 0
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max(avg_opp_bid + 5, 95))
    
    target_bid = avg_opp_bid + 2
    return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if supply < 18:
        bid = min(budget, avg_opp_bid * 1.1)
    elif hp < 4:
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        bid = min(budget, max(30.0, avg_opp_bid * 0.8))

    return float(max(0, bid))
"""
