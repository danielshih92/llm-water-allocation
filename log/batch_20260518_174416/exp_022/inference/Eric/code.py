# ============================================================
# Experiment: exp_022
# Agent: Eric
# Source: exp_022
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # No opponent info, use own status
    # Base bid: safe fraction of salary
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.6
    else:
        base_bid = DAILY_SALARY * 0.45
    
    # Adjust for supply: if low supply, bid higher
    if supply < 18:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    
    # Ensure we don't exceed budget
    bid = min(budget, base_bid)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Count alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Collect yesterday's bids and current budgets
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid: low if sufficient supply, higher if scarce
    if supply >= 20:
        base_bid = DAILY_SALARY * 0.3
    elif supply >= 18:
        base_bid = DAILY_SALARY * 0.45
    else:
        base_bid = DAILY_SALARY * 0.6
    
    # Adjust based on HP
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.5)
    
    # If we have no_water_days >= 2, bid aggressively
    if my_status['no_water_days'] >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    
    # Counter yesterday's high bidders
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev >= DAILY_SALARY * 0.8:
            # Aggressive opponent yesterday; check their budget
            for opp in alive_opponents:
                trace = opp.get('previous_trace', {})
                if trace and trace.get('bid') == max_prev:
                    if opp['budget'] < DAILY_SALARY * 2:  # low budget
                        # They might be broke, so reduce bid slightly
                        base_bid = min(base_bid, max_prev * 0.6)
                    else:
                        # They still have money, match or exceed
                        base_bid = max(base_bid, max_prev * 0.9)
                    break
        # If yesterday was moderate, just outbid slightly
        else:
            outbid = max_prev + 2.0
            base_bid = max(base_bid, outbid)
    
    # Ensure within budget and salary
    max_bid = min(budget, DAILY_SALARY)
    final_bid = min(max_bid, base_bid)
    final_bid = max(0, final_bid)
    return float(final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    if prev_bids:
        max_prev = max(prev_bids)
        if my_status['hp'] <= 2:
            bid = min(my_status['budget'], DAILY_SALARY * 0.95)
        elif my_status['hp'] <= 4:
            bid = min(my_status['budget'], max(DAILY_SALARY * 0.7, max_prev + 2.0))
        else:
            bid = min(my_status['budget'], max(DAILY_SALARY * 0.5, max_prev + 1.0))
    else:
        if my_status['hp'] <= 2:
            bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.6)
    
    # Ensure integer-safe indexing not needed here; return float
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If competition was fierce, bid accordingly
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If healthy, conserve budget; if low hp, go all in
            if hp > 3:
                target = DAILY_SALARY * 0.45
            else:
                target = DAILY_SALARY * 0.9
        else:
            # Bid slightly above last max, but not too high
            target = max(DAILY_SALARY * 0.4, highest_prev_bid + 2.0)
    else:
        # No yesterday data: base on hp
        if hp <= 2:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * 0.5

    # Ensure we don't exceed budget or go below zero
    bid = min(budget, max(0.0, target))
    # For early days, aggressive bidding to secure water
    if day <= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.6))
    # If supply low and we need water, increase bid
    if supply < WATER_REQ + 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.7))

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's max bid from opponents
    yesterday_max_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])
    
    # Base bid: slightly above yesterday's max, but not too high
    if yesterday_max_bid > 0:
        base_bid = yesterday_max_bid + 1.5
    else:
        base_bid = DAILY_SALARY * 0.6
    
    # Adjust for supply: if high supply, reduce bid; if low, increase
    supply_factor = 1.0
    if supply >= 22:
        supply_factor = 0.85
    elif supply <= 17:
        supply_factor = 1.15
    else:
        supply_factor = 1.0
    
    # Adjust for HP: if low HP, bid more aggressively
    hp_factor = 1.0
    if my_hp <= 3:
        hp_factor = 1.25
    elif my_hp <= 6:
        hp_factor = 1.1
    else:
        hp_factor = 1.0
    
    target_bid = base_bid * supply_factor * hp_factor
    
    # Ensure not exceed budget and daily salary
    max_affordable = min(my_budget, DAILY_SALARY * 0.9)
    target_bid = min(target_bid, max_affordable)
    
    # Ensure minimum bid to stay alive if water needed
    if my_hp <= 2 and my_status['no_water_days'] > 0:
        target_bid = max(target_bid, DAILY_SALARY * 0.7)
    
    # Return as float (game expects float)
    return float(target_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Base bid: reasonable fraction of salary
    base_bid = DAILY_SALARY * 1.1  # slightly above water_requirement value
    
    # Adjust based on HP urgency
    if hp <= 2:
        urgent_bid = DAILY_SALARY * 1.3
    elif hp <= 4:
        urgent_bid = DAILY_SALARY * 1.15
    else:
        urgent_bid = DAILY_SALARY * 0.95
    
    # Check yesterday traces for competitive intelligence
    if alive_opponents:
        prev_bids = []
        for opp_id, opp in alive_opponents.items():
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace and trace['bid'] is not None:
                prev_bids.append(trace['bid'])
        if prev_bids:
            max_prev = max(prev_bids)
            # If opponents bid very high yesterday, they may be desperate; bid lower to save money
            if max_prev > DAILY_SALARY * 1.2:
                target = max_prev * 0.9
            elif max_prev > DAILY_SALARY:
                target = max_prev * 0.95
            else:
                target = max_prev + 1.0
            # Blend with urgent bid
            bid = min(urgent_bid, target)
        else:
            bid = urgent_bid
    else:
        bid = DAILY_SALARY * 1.0
    
    # Ensure bid doesn't exceed budget
    bid = min(bid, budget)
    
    # Ensure bid is non-negative
    bid = max(bid, 0)
    
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    daily_salary = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    
    # Get yesterday's max bid from alive opponents
    alive_opp = [o for o in opponents_status.values() if o['alive']]
    max_yesterday_bid = 0.0
    for opp in alive_opp:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            bid_val = float(trace['bid'])
            if bid_val > max_yesterday_bid:
                max_yesterday_bid = bid_val
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Urgency based on health and no water days
    urgent = (hp <= 2) or (no_water_days >= 2)
    
    # Estimate competition: if supply is tight, need higher bid
    max_winners = supply // water_req
    if max_winners <= 1:
        competition_factor = 1.5
    elif max_winners == 2:
        competition_factor = 1.2
    else:
        competition_factor = 1.0
    
    # Base bid from yesterday's max
    if max_yesterday_bid > 0:
        # Undercut slightly to save money
        base_bid = max_yesterday_bid * 0.95 + 0.5
    else:
        base_bid = daily_salary * 0.5
    
    # If urgent, bid higher
    if urgent:
        base_bid = max(base_bid, daily_salary * 0.9)
    else:
        # Conservative if not urgent
        base_bid = min(base_bid, daily_salary * 0.7)
    
    # Adjust for competition
    bid = base_bid * competition_factor
    
    # Clamp to budget and reasonable bounds
    max_affordable = budget * 0.98
    bid = min(bid, max_affordable)
    bid = max(bid, 0.1)
    
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    prev_bids = [o['previous_trace']['bid'] for o in alive if o.get('previous_trace') and o['previous_trace'].get('bid') is not None]
    if prev_bids:
        highest_prev = max(prev_bids)
        if my_status['hp'] <= 2:
            return min(my_status['budget'], highest_prev + 5)
        elif my_status['hp'] <= 5:
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev + 2))
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev - 5))
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""
