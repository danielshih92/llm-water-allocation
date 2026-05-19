# ============================================================
# Experiment: exp_107
# Agent: David
# Source: exp_107
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7 DAILY_SALARY = 80 alive_opponents = [o for o in opponents_status.values() if o['alive']] if not alive_opponents: return min(my_status['budget'], 25) yesterday_bids = [] for opp in alive_opponents: prev = opp.get('previous_trace', {}) if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']) avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 30 if my_status['hp'] < 4: return min(my_status['budget'], max(avg_bid * 1.2, 45)) return min(my_status['budget'], max(avg_bid * 0.9, 25))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 60
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5)
        
    if supply < 18:
        return min(my_status['budget'], max_prev + 2)
        
    if len(alive_opponents) > 2:
        return min(my_status['budget'], max(50, max_prev * 0.95))
        
    return min(my_status['budget'], 45)
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
        return min(my_status['budget'], 40.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] < 4:
            return min(my_status['budget'], max_prev + 10.0)
        if max_prev > 120:
            return min(my_status['budget'], 50.0)
        return min(my_status['budget'], max_prev + 5.0)

    return min(my_status['budget'], 85.0)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 60.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(avg_prev_bid * 1.1, DAILY_SALARY * 0.95))
    elif my_status['hp'] >= 8:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    else:
        return min(my_status['budget'], max(avg_prev_bid * 0.9, DAILY_SALARY * 0.6))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 60.0; target_bid = avg_prev * 1.05; if day_context['supply'] < 18: target_bid += 15.0; if my_status['hp'] < 4: target_bid += 25.0; return min(my_status['budget'], float(target_bid))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    
    if num_opponents == 0:
        return min(my_status['budget'], 10.0)
    
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40.0
    
    base_bid = min(my_status['budget'], avg_prev_bid * 1.05)
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], base_bid * 1.5)
    elif my_status['hp'] > 8:
        return min(my_status['budget'], base_bid * 0.8)
    
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if not prev_bids: return min(my_status['budget'], DAILY_SALARY * 0.6); avg_opp_bid = sum(prev_bids) / len(prev_bids); if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_opp_bid * 1.1, DAILY_SALARY * 0.85)); if day_context['supply'] < 18: return min(my_status['budget'], avg_opp_bid * 1.05); return min(my_status['budget'], avg_opp_bid * 0.8)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85; if my_status['hp'] <= 3: return min(my_status['budget'], 130.0); if day_context['supply'] < 20: return min(my_status['budget'], max(90.0, avg_prev + 5.0)); return min(my_status['budget'], max(75.0, avg_prev - 5.0))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] < 4: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.7)); return min(my_status['budget'], max(avg_prev * 0.9, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids: highest_prev = max(yesterday_bids); if my_status['hp'] < 4: return min(my_status['budget'], highest_prev + 5); if highest_prev > 60: return min(my_status['budget'], 55); return min(my_status['budget'], 45); return min(my_status['budget'], 40)
"""
