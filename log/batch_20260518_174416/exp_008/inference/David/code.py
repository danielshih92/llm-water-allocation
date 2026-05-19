# ============================================================
# Experiment: exp_008
# Agent: David
# Source: exp_008
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
    fair_share = supply / num_agents
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
        
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.5)
        
    max_prev = max(yesterday_bids)
    if fair_share < WATER_REQ:
        return min(my_status['budget'], max_prev + 5.0)
        
    return min(my_status['budget'], max(DAILY_SALARY * 0.3, max_prev * 0.9))
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
    
    cindy_prev = opponents_status.get('Cindy', {}).get('previous_trace', {})
    cindy_bid = cindy_prev.get('bid', 0) if cindy_prev else 40
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], cindy_bid + 5)
    
    if supply >= 20:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    elif supply >= 15:
        return min(my_status['budget'], cindy_bid + 2)
    
    return min(my_status['budget'], DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; if my_status['hp'] <= 3: return min(my_status['budget'], 120.0); if supply < 18: return min(my_status['budget'], avg_prev + 5.0); return min(my_status['budget'], avg_prev * 0.95)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(bids) / len(bids) if bids else 60; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_bid * 1.05, 75)); return min(my_status['budget'], max(avg_bid * 0.8, 50))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.8)); return min(my_status['budget'], max(avg_prev * 0.6, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0; if my_status['hp'] <= 3: return min(my_status['budget'], avg_prev_bid * 1.15); if my_status['budget'] < 100: return min(my_status['budget'], avg_prev_bid * 0.9); return min(my_status['budget'], avg_prev_bid * 1.05)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if day_context['supply'] < WATER_REQ * 1.5: return min(my_status['budget'], max(avg_bid * 1.1, DAILY_SALARY * 0.6)); if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 0.7); return min(my_status['budget'], max(avg_bid * 0.8, DAILY_SALARY * 0.35))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60; target_bid = avg_prev * 1.05; if day_context['supply'] < 18: target_bid += 15; if my_status['hp'] <= 3: target_bid = min(my_status['budget'], target_bid * 1.5); return min(my_status['budget'], max(0, target_bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], 20.0)
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 40.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
    
    if day_context['supply'] < 18:
        return min(my_status['budget'], avg_prev_bid * 1.1)
        
    return min(my_status['budget'], max(avg_prev_bid * 0.9, 35.0))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return float(min(my_status['budget'], 10.0))

    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            prev_bids.append(prev['bid'])

    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        bid = avg_prev * 1.05
    else:
        bid = DAILY_SALARY * 0.6

    if my_status['hp'] < 4:
        bid = max(bid, DAILY_SALARY * 0.9)

    return float(min(my_status['budget'], bid))
"""
