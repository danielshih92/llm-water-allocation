# ============================================================
# Experiment: exp_032
# Agent: David
# Source: exp_032
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; fair_share = supply / (len(alive_opponents) + 1) if alive_opponents else supply; bid = min(my_status['budget'], max(10.0, DAILY_SALARY * 0.4)); if my_status['hp'] < 4: bid = min(my_status['budget'], DAILY_SALARY * 0.8); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: max_prev = max(yesterday_bids); if max_prev > bid: bid = min(my_status['budget'], max_prev + 2.0); return float(int(bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80; if my_status['hp'] <= 3: return min(my_status['budget'], avg_bid * 1.2); if supply < 18: return min(my_status['budget'], avg_bid * 1.05); return min(my_status['budget'], avg_bid * 0.95)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 80
    WATER_REQ = 7
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 10.0)

    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    max_prev = max(prev_bids) if prev_bids else 20.0

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    if supply < WATER_REQ * 1.5:
        return min(my_status['budget'], max_prev + 5.0)
        
    return min(my_status['budget'], max(20.0, max_prev * 0.8))
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
        return min(my_status['budget'], 15.0)

    cindy_bid = 0
    if 'Cindy' in opponents_status and opponents_status['Cindy']['alive']:
        prev = opponents_status['Cindy'].get('previous_trace', {})
        cindy_bid = prev.get('bid', 75.0)

    if my_status['hp'] < 4:
        return min(my_status['budget'], cindy_bid + 2.0)
    
    fair_share_bid = (DAILY_SALARY / (len(alive_opponents) + 1)) * 1.1
    return min(my_status['budget'], max(fair_share_bid, 25.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); aggressive_threshold = max(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if day_context['supply'] < 18: return min(my_status['budget'], aggressive_threshold + 5.0); return min(my_status['budget'], max(55.0, aggressive_threshold * 0.9))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; num_winners = int(supply // WATER_REQ); if not alive_opponents: return 0; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.95); if len(alive_opponents) >= num_winners: return min(my_status['budget'], max(avg_prev + 2.0, DAILY_SALARY * 0.6)); return min(my_status['budget'], max(avg_prev * 0.8, DAILY_SALARY * 0.4))
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
    
    prev_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        if supply < 18:
            return min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.6))
        return min(my_status['budget'], max(avg_prev * 0.8, DAILY_SALARY * 0.4))
        
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if not yesterday_bids: return min(my_status['budget'], DAILY_SALARY * 0.6); avg_bid = sum(yesterday_bids) / len(yesterday_bids); target_bid = avg_bid * 1.05; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); return min(my_status['budget'], max(DAILY_SALARY * 0.4, target_bid))
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
        return min(my_status['budget'], 40.0)
    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        target = max_prev * 0.95
    else:
        target = DAILY_SALARY * 1.1
    if my_status['hp'] < 4:
        bid = min(my_status['budget'], target * 1.2)
    else:
        bid = min(my_status['budget'], target)
    return float(max(10.0, bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0; supply = day_context['supply']; if supply >= 20: bid = highest_prev_bid * 0.8 if highest_prev_bid > 0 else DAILY_SALARY * 0.4; else: bid = highest_prev_bid * 1.05 + 2.0 if highest_prev_bid > 0 else DAILY_SALARY * 0.7; if my_status['hp'] <= 3: bid = max(bid, DAILY_SALARY * 0.9); return min(my_status['budget'], float(bid))
"""
