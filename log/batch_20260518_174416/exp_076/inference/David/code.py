# ============================================================
# Experiment: exp_076
# Agent: David
# Source: exp_076
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 0.9); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); if yesterday_bids and max(yesterday_bids) > DAILY_SALARY * 0.6: return min(my_status['budget'], max(DAILY_SALARY * 0.4, max(yesterday_bids) + 1)); return min(my_status['budget'], DAILY_SALARY * 0.5)
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
    
    # Calculate a competitive bid based on observed behavior
    # Aim to be higher than Eric but lower than the aggressive pair
    target_bid = 65.0
    
    # If low on HP, prioritize survival
    if my_status['hp'] <= 3:
        target_bid = 95.0
    
    # Ensure we don't exceed budget
    bid = min(my_status['budget'], target_bid)
    
    # Add slight randomization to avoid static patterns
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = []; for opp in alive_opponents: prev = opp.get('previous_trace', {}); if prev and prev.get('bid') is not None: yesterday_bids.append(prev['bid']); avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); if my_status['hp'] <= 6: return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev * 1.05)); return min(my_status['budget'], max(DAILY_SALARY * 0.45, avg_prev * 0.9))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], DAILY_SALARY * 0.5); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 70; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); return min(my_status['budget'], max(DAILY_SALARY * 0.6, avg_prev * 0.95))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; prev_bids = [o['previous_trace']['bid'] for o in alive_opps if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; max_prev = max(prev_bids) if prev_bids else 0; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.2); if supply < 18: return min(my_status['budget'], max(DAILY_SALARY * 0.8, max_prev + 5)); if supply > 22: return min(my_status['budget'], DAILY_SALARY * 0.4); return min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev + 2))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; supply = day_context['supply']; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 80.0; if my_status['hp'] <= 3: return min(my_status['budget'], float(DAILY_SALARY) * 1.2); if supply < 18: return min(my_status['budget'], float(avg_prev) * 1.1); return min(my_status['budget'], float(avg_prev) * 0.85)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 40); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_bob_bid = 71.0; target = avg_bob_bid + 2.5; if my_status['hp'] <= 3: return min(my_status['budget'], DAILY_SALARY * 1.1); return min(my_status['budget'], target)
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 3:
            return min(my_status['budget'], max_prev + 5.0)
        if day_context['supply'] < 18.0:
            return min(my_status['budget'], max_prev + 2.0)
        return min(my_status['budget'], max(20.0, max_prev * 0.8))

    return min(my_status['budget'], 40.0)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 10.0); alex_bid = 61.0; for opp_id, opp in opponents_status.items(): if opp_id == 'Alex' and opp['alive']: prev = opp.get('previous_trace', {}); if prev and prev.get('bid'): alex_bid = prev['bid']; bid = alex_bid + 2.5 if supply < 18 else alex_bid * 0.7; return min(my_status['budget'], max(20.0, bid))
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
        return float(min(my_status['budget'], 20.0))
    
    prev_bids = [o.get('previous_trace', {}).get('bid', 0) for o in alive_opponents if o.get('previous_trace')]
    max_prev = max(prev_bids) if prev_bids else 0
    
    if my_status['hp'] <= 3:
        return float(min(my_status['budget'], max(max_prev * 1.1, 60.0)))
    
    if day_context['supply'] < WATER_REQ * 1.5:
        return float(min(my_status['budget'], max(max_prev * 0.9, 45.0)))
        
    return float(min(my_status['budget'], 35.0))
"""
