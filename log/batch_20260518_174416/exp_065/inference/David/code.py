# ============================================================
# Experiment: exp_065
# Agent: David
# Source: exp_065
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; bid = DAILY_SALARY * 0.4; if len(alive_opponents) > 0: yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: max_prev = max(yesterday_bids); if max_prev > DAILY_SALARY * 0.5: bid = min(my_status['budget'], max_prev + 1.0); else: bid = DAILY_SALARY * 0.45; if my_status['hp'] < 3: bid = min(my_status['budget'], DAILY_SALARY * 0.8); return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80 WATER_REQ = 7 alive_opponents = [o for o in opponents_status.values() if o['alive']] if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5) yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None] if yesterday_bids: avg_bid = sum(yesterday_bids) / len(yesterday_bids) max_bid = max(yesterday_bids) else: avg_bid = 90 max_bid = 100 if my_status['hp'] <= 3: return min(my_status['budget'], max(max_bid + 5, DAILY_SALARY * 1.2)) if day_context['supply'] < 18: return min(my_status['budget'], max(avg_bid + 2, DAILY_SALARY * 1.1)) return min(my_status['budget'], max(avg_bid - 5, DAILY_SALARY * 0.9))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 10.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if hp <= 2:
        return min(budget, DAILY_SALARY * 1.2)
    
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > DAILY_SALARY * 1.5:
            return min(budget, 15.0)
        return min(budget, max_prev + 5.0)
        
    return min(budget, 45.0)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = avg_prev_bid * 1.05
    else:
        target_bid = DAILY_SALARY * 0.6
    if my_status['hp'] < 4:
        return float(min(my_status['budget'], DAILY_SALARY * 1.2))
    return float(min(my_status['budget'], target_bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if 'previous_trace' in o and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if supply < 18:
        return min(my_status['budget'], avg_prev_bid * 1.1)
    return min(my_status['budget'], avg_prev_bid * 0.9)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    supply = day_context['supply']
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
    
    max_prev = max(prev_bids)
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(max_prev * 1.1, DAILY_SALARY * 1.2))
    
    if supply < 18:
        return min(my_status['budget'], max(max_prev * 1.05, DAILY_SALARY * 0.8))
        
    return min(my_status['budget'], max(max_prev * 0.9, DAILY_SALARY * 0.5))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    cindy = opponents_status.get('Cindy', {})
    
    if not alive_opponents:
        return 10.0
    
    cindy_prev_bid = 0.0
    if cindy.get('alive') and 'previous_trace' in cindy:
        cindy_prev_bid = cindy['previous_trace'].get('bid', 0.0)
    
    fair_share = supply / (len(alive_opponents) + 1)
    base_bid = min(my_status['budget'], max(fair_share * 1.1, 25.0))
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    if cindy_prev_bid > 80:
        return min(my_status['budget'], cindy_prev_bid * 0.5)
    
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], max(50.0, avg_prev * 1.1)); if day_context['day'] > 7: return min(my_status['budget'], max(45.0, avg_prev * 1.05)); return min(my_status['budget'], max(35.0, avg_prev * 0.9))
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
        return min(my_status['budget'], 20.0)
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if not prev_bids:
        return min(my_status['budget'], 60.0)
        
    avg_prev = sum(prev_bids) / len(prev_bids)
    max_prev = max(prev_bids)
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], max_prev + 10.0)
    
    if day_context['supply'] < WATER_REQ * (len(alive_opponents) + 1):
        return min(my_status['budget'], max_prev + 5.0)
        
    return min(my_status['budget'], max(avg_prev * 0.9, 40.0))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev + 5.0))
    return min(my_status['budget'], DAILY_SALARY * 0.7)
"""
