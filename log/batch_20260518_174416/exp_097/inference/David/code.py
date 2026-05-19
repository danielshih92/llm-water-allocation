# ============================================================
# Experiment: exp_097
# Agent: David
# Source: exp_097
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    
    # Baseline strategy for day 1 or no history
    bid = DAILY_SALARY * 0.6
    
    # Adjust for low HP
    if hp <= 3:
        bid = DAILY_SALARY * 0.85
        
    # Ensure bid does not exceed budget
    return float(min(budget, bid))
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
        return 0
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if not yesterday_bids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
        
    avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    if my_status['hp'] < 4:
        return min(my_status['budget'], avg_opp_bid * 1.1)
    
    if day_context['supply'] < WATER_REQ * 2:
        return min(my_status['budget'], avg_opp_bid * 1.05)
        
    return min(my_status['budget'], avg_opp_bid * 0.95)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status): DAILY_SALARY = 80; WATER_REQ = 7; supply = day_context['supply']; alive_opps = [o for o in opponents_status.values() if o['alive']]; if not alive_opps: return min(my_status['budget'], DAILY_SALARY * 0.4); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opps if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50; if supply < 18: bid = min(my_status['budget'], max(avg_prev * 1.1, DAILY_SALARY * 0.9)); elif supply > 22: bid = min(my_status['budget'], DAILY_SALARY * 0.4); else: bid = min(my_status['budget'], avg_prev * 0.95); return float(max(0, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; alive_opponents = [o for o in opponents_status.values() if o['alive']]; if not alive_opponents: return min(my_status['budget'], 20.0); yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 50.0; if my_status['hp'] < 4: return min(my_status['budget'], max(avg_prev_bid + 5.0, 75.0)); return min(my_status['budget'], max(avg_prev_bid * 0.9, 45.0))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Calculate estimated fair bid based on supply
    supply = day_context['supply']
    num_agents = len(alive_opponents) + 1
    fair_share = supply / num_agents
    bid_target = DAILY_SALARY * (WATER_REQ / max(1, fair_share))

    # Aggressive adjustment if HP is low
    if my_status['hp'] <= 3:
        bid_target *= 1.5
    
    # Analyze recent competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        bid_target = max(bid_target, max_prev * 0.95)

    # Final safety constraints
    final_bid = min(my_status['budget'], max(0, bid_target))
    return float(final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 7
    DAILY_SALARY = 80
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], 20.0)

    yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target_bid = min(my_status['budget'], avg_prev * 0.6)
    else:
        target_bid = DAILY_SALARY * 0.4

    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    return max(10.0, min(my_status['budget'], target_bid))
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
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    
    if my_status['hp'] <= 3:
        return min(my_status['budget'], max(85.0, max_prev + 5.0))
    
    if supply < 18.0:
        return min(my_status['budget'], max(75.0, max_prev + 2.0))
        
    return min(my_status['budget'], max(60.0, max_prev * 0.95))
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
        return min(my_status['budget'], 10.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    target_bid = 25.0
    if yesterday_bids:
        target_bid = sum(yesterday_bids) / len(yesterday_bids)

    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], target_bid * 1.2)
    else:
        bid = min(my_status['budget'], target_bid * 0.9)

    return max(1.0, float(bid))
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        
        if day_context['supply'] < WATER_REQ * 1.5:
            return min(my_status['budget'], DAILY_SALARY * 1.1)
        
        if my_status['hp'] < 4:
            return min(my_status['budget'], max_prev + 5.0)
            
        return min(my_status['budget'], max(avg_prev + 2.0, DAILY_SALARY * 0.6))

    return min(my_status['budget'], DAILY_SALARY * 0.7)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status): WATER_REQ = 7; DAILY_SALARY = 80; supply = day_context['supply']; alive_opponents = [o for o in opponents_status.values() if o['alive']]; bid = DAILY_SALARY * 0.6; if my_status['hp'] <= 3: bid = min(my_status['budget'], DAILY_SALARY * 1.2); elif supply < 18: bid = min(my_status['budget'], DAILY_SALARY * 0.9); if alive_opponents: yesterday_bids = [o['previous_trace']['bid'] for o in alive_opponents if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]; if yesterday_bids: avg_opp = sum(yesterday_bids) / len(yesterday_bids); if avg_opp > bid: bid = min(my_status['budget'], avg_opp * 0.95); return float(min(my_status['budget'], bid))
"""
