# ============================================================
# Experiment: exp_013
# Agent: David
# Source: exp_013
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_players = len(alive_opponents) + 1; fair_share = DAILY_SALARY / num_players; if my_status['hp'] < 3: return min(my_status['budget'], DAILY_SALARY * 0.8); return min(my_status['budget'], fair_share * 1.2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], 75.0); if my_status['hp'] >= 8: return min(my_status['budget'], max(35.0, avg_prev * 0.6)); return min(my_status['budget'], max(50.0, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    cindy = opponents_status.get('Cindy', {})
    cindy_bid = cindy.get('previous_trace', {}).get('bid', 0) if cindy.get('previous_trace') else 0
    
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if supply < 18:
        return min(my_status['budget'], max(cindy_bid * 1.05, 45.0))
    
    return min(my_status['budget'], max(cindy_bid * 0.5, 25.0))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 10.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if hp <= 3:
        return min(budget, DAILY_SALARY * 0.95)
    
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        if avg_prev > DAILY_SALARY * 0.6:
            return min(budget, avg_prev * 0.8)
        return min(budget, max(25.0, avg_prev + 2.0))
        
    return min(budget, 22.0)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 20.0))
        
    bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bids.append(prev['bid'])
            
    avg_opp_bid = sum(bids) / len(bids) if bids else 80.0
    
    # Aggressive if low health, otherwise maintain competitive edge
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(avg_opp_bid * 1.1, 90.0))
    else:
        bid = min(my_status['budget'], avg_opp_bid * 1.05)
        
    return float(max(10.0, bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.95); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], max(avg_prev_bid * 1.1, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_prev_bid * 0.9, DAILY_SALARY * 0.4))
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
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if day_context['supply'] < 18:
        bid = min(my_status['budget'], avg_prev * 1.15)
    else:
        bid = min(my_status['budget'], avg_prev * 0.9)
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    return float(max(1.0, bid))
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
        return min(my_status['budget'], 20.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_prev_bid * 1.2)
    if supply < 18:
        return min(my_status['budget'], avg_prev_bid * 1.1)
    return min(my_status['budget'], avg_prev_bid * 0.9)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, 20.0)

    avg_opp_bid = 0
    bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if bids:
        avg_opp_bid = sum(bids) / len(bids)

    if hp <= 3:
        return min(budget, DAILY_SALARY * 0.95)
    
    if supply < 18:
        return min(budget, max(avg_opp_bid * 1.05, DAILY_SALARY * 0.7))
    
    return min(budget, max(40.0, avg_opp_bid * 0.8))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_bid * 1.1, 75)); return min(my_status['budget'], max(avg_bid * 0.9, 50))
"""
