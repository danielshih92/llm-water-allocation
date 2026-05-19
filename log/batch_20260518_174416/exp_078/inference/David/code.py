# ============================================================
# Experiment: exp_078
# Agent: David
# Source: exp_078
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); avg_bid = 0; count = 0; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: avg_bid += prev['bid']; count += 1; if count > 0: avg_bid /= count; target = avg_bid * 1.05; else: target = DAILY_SALARY * 0.65; if my_status['hp'] < 4: target = max(target, DAILY_SALARY * 0.8); return float(min(my_status['budget'], target))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 45; bid = avg_prev * 1.05; if my_status['hp'] <= 3: bid = max(bid, DAILY_SALARY * 0.9); return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev * 1.1, 75.0)); if my_status['hp'] >= 8: return min(my_status['budget'], avg_prev * 0.7); return min(my_status['budget'], avg_prev * 0.95)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40.0); yesterday_bids = [opp['previous_trace']['bid'] for opp in alive_opponents if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 85.0; bid = avg_prev * 1.05; if my_status['hp'] <= 3: bid = max(bid, 110.0); return float(min(my_status['budget'], bid))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], max(avg_prev * 1.1, 90)); if supply < 18: return min(my_status['budget'], max(avg_prev * 1.05, 75)); return min(my_status['budget'], max(avg_prev * 0.95, 65))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.3); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 40; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < 18: return min(my_status['budget'], max(avg_prev_bid * 1.1, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_prev_bid * 0.8, DAILY_SALARY * 0.4))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not alive_opponents:
        return min(my_status['budget'], 10.0)
        
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 1.2)
        
    if supply > 20:
        return min(my_status['budget'], avg_prev * 0.8)
    elif supply < 17:
        return min(my_status['budget'], avg_prev * 1.1)
    else:
        return min(my_status['budget'], avg_prev * 0.95)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.6
    
    # Aggressive bidding if low HP, otherwise competitive
    if my_status['hp'] <= 3:
        bid = avg_prev_bid * 1.2
    else:
        bid = avg_prev_bid * 1.05
        
    # Ensure we don't overspend relative to salary unless necessary
    bid = max(DAILY_SALARY * 0.4, min(bid, DAILY_SALARY * 1.5))
    
    return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); cindy_bid = 0; if 'Cindy' in opponents_status and opponents_status['Cindy']['alive']: prev = opponents_status['Cindy'].get('previous_trace', {}); cindy_bid = prev.get('bid', 80.0); if my_status['hp'] <= 2: return min(my_status['budget'], DAILY_SALARY * 1.2); if day_context['supply'] < WATER_REQ * 2: return min(my_status['budget'], cindy_bid + 5.0); return min(my_status['budget'], max(40.0, cindy_bid * 0.8))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(yesterday_bids) if yesterday_bids else 80.0
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max_prev + 5.0)
    if supply < 18.0:
        return min(my_status['budget'], max(85.0, max_prev + 2.0))
    return min(my_status['budget'], 75.0)
"""
