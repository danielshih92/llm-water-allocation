# ============================================================
# Experiment: exp_051
# Agent: David
# Source: exp_051
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_agents = len(alive_opponents) + 1; fair_share = supply / num_agents; base_bid = DAILY_SALARY * 0.4; if supply < WATER_REQ * num_agents: base_bid = DAILY_SALARY * 0.65; if my_status['hp'] <= 3: base_bid = min(my_status['budget'], DAILY_SALARY * 0.9); return float(min(my_status['budget'], base_bid))
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], 145.0)

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > 100:
            return min(my_status['budget'], 75.0)
        return min(my_status['budget'], max_prev + 5.0)

    return min(my_status['budget'], 72.0)
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
        return min(my_status['budget'], 10.0)
    cindy = opponents_status.get('Cindy')
    if cindy and cindy['alive']:
        prev_bid = cindy.get('previous_trace', {}).get('bid', 80)
        if my_status['hp'] < 5:
            return min(my_status['budget'], prev_bid + 5.0)
        return min(my_status['budget'], 75.0)
    return min(my_status['budget'], 45.0)
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
        return min(my_status['budget'], 20.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 90.0
    
    if my_status['hp'] <= 3:
        target_bid = max(avg_opp_bid * 1.1, DAILY_SALARY * 1.2)
    else:
        target_bid = max(avg_opp_bid * 0.95, DAILY_SALARY * 0.7)

    return float(min(my_status['budget'], target_bid))
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
        return min(my_status['budget'], 10.0)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_status['hp'] <= 3:
            return min(my_status['budget'], float(highest_prev_bid + 5.0))
        if day_context['supply'] < (len(alive_opponents) + 1) * WATER_REQ:
            return min(my_status['budget'], float(highest_prev_bid + 1.0))
        return min(my_status['budget'], float(highest_prev_bid * 0.9))
    return min(my_status['budget'], float(DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; bid = 45.0; if alive: cindy = opponents_status.get('Cindy'); if cindy and cindy['alive']: bid = 65.0; elif len(alive) > 1: bid = 55.0; if my_status['hp'] <= 4: bid += 20.0; if supply < 18: bid += 15.0; return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    supply = day_context['supply']
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.1)
    
    if supply / (len(alive_opponents) + 1) < WATER_REQ:
        return min(my_status['budget'], avg_prev_bid * 1.05)
        
    return min(my_status['budget'], max(30.0, avg_prev_bid * 0.9))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 70.0; if my_status['hp'] < 4: return min(my_status['budget'], 115.0); if supply < 18: return min(my_status['budget'], max(85.0, avg_prev + 2.0)); return min(my_status['budget'], max(60.0, avg_prev - 10.0))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]; if not yesterday_bids: return min(my_status['budget'], DAILY_SALARY * 0.6); avg_prev = sum(yesterday_bids) / len(yesterday_bids); target = min(my_status['budget'], max(DAILY_SALARY * 0.7, avg_prev * 0.85)); if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); return target
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: max_prev = max(yesterday_bids); if max_prev > 100: return min(my_status['budget'], 40); if max_prev > 15: return min(my_status['budget'], max_prev + 5); return min(my_status['budget'], 25); if my_status['hp'] <= 3: return min(my_status['budget'], 60); return min(my_status['budget'], 30)
"""
