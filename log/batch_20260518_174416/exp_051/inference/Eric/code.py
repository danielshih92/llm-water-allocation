# ============================================================
# Experiment: exp_051
# Agent: Eric
# Source: exp_051
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    if hp <= 2:
        bid = budget * 0.9
    else:
        bid = DAILY_SALARY * 0.5
    
    return min(budget, bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= 0.85 * DAILY_SALARY:
            if my_status['hp'] > 4:
                return min(my_status['budget'], DAILY_SALARY * 0.45)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            target = max(DAILY_SALARY * 0.5, highest_prev + 2)
            return min(my_status['budget'], target)
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water = my_status['no_water_days']
    sal = 140
    req = 8
    
    alive_opponents = {k:v for k,v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_budget, sal * 0.3)
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Estimate needed water from supply
    if supply >= req * 2:
        base_bid = sal * 0.3
    elif supply >= req:
        base_bid = sal * 0.5
    else:
        base_bid = sal * 0.7
    
    # Determine if we need water desperately
    if my_hp <= 2 or no_water >= 2:
        aggressive = True
    else:
        aggressive = False
    
    # Respond to yesterday's highest bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if aggressive:
            # Must win: bid just above max_prev within budget
            target = min(my_budget, max_prev + 2.0)
        else:
            # If we are comfortable, only bid if max_prev is high, else undercut
            if max_prev > sal * 0.8:
                target = min(my_budget, max_prev * 0.95)  # slightly below
            else:
                target = min(my_budget, max(base_bid, max_prev + 1.0))
        return target
    else:
        if aggressive:
            return min(my_budget, sal * 0.85)
        else:
            return min(my_budget, base_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's bids from alive opponents (previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    # Default if no yesterday info (first day or missing)
    if not yesterday_bids:
        # Use historical averages from metaround context (approximation)
        # But to stay generic, assume everyone bids around 70% salary
        avg_bid = DAILY_SALARY * 0.7
    else:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    day = day_context['day']
    
    # Determine bid based on HP and supply
    # If low HP, need water urgently
    if hp <= 2:
        # Desperate: try to outbid Cindy (135) by a small margin
        target = 136.0
    elif hp <= 5:
        # Moderate HP: bid around yesterday's average plus small premium
        target = int(avg_bid + 5.0)
    else:
        # High HP: save money, bid low but above minimum
        # Use a fraction of salary based on remaining days
        remaining_days = 10 - day if day < 10 else 1
        # Need to ensure we don't run out of budget later
        target = min(DAILY_SALARY * 0.5, int(budget / (remaining_days + 1) * 0.6))
    
    # Ensure bid is at least 1 and at most budget
    bid = max(1.0, min(float(budget), target))
    # Also ensure we don't exceed a reasonable cap (e.g., salary)
    bid = min(bid, DAILY_SALARY * 1.2)  # cap at 168
    
    # Convert to float for return
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
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Gather yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        # If previous max is high, we need to outbid slightly
        if max_prev >= DAILY_SALARY * 0.8:
            target = avg_prev + 2.0
        else:
            target = avg_prev + 1.0
    else:
        target = DAILY_SALARY * 0.5
    
    # Adjust based on HP, day, and supply
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif day >= 8:
        target = max(target, DAILY_SALARY * 0.7)
    else:
        target = max(target, DAILY_SALARY * 0.4)
    
    # Ensure we don't exceed budget and bid at least 0
    bid = min(budget, target)
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    alive_opponents = {k: o for k, o in opponents_status.items() if o['alive']}
    
    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Estimate opponent next bid
    if prev_bids:
        estimated_max = max(prev_bids)
    else:
        estimated_max = DAILY_SALARY * 0.5  # fallback
    
    # Our need: if low HP, bid aggressively
    hp = my_status['hp']
    budget = my_status['budget']
    
    if hp <= 2:
        target = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 5:
        target = min(budget, max(estimated_max + 1.0, DAILY_SALARY * 0.6))
    else:
        target = min(budget, max(estimated_max + 0.5, DAILY_SALARY * 0.4))
    
    # Ensure not to exceed budget
    bid = max(0.0, min(budget, target))
    # Convert to int if needed (bid can be float)
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    num_alive = len(alive_opponents)

    # Total water demand from all alive players including self
    total_demand = (num_alive + 1) * WATER_REQ

    # Base bid: proportional to salary, higher when supply is tight
    scarcity_factor = max(0, total_demand - supply) / total_demand  # 0-1
    base_bid = DAILY_SALARY * (0.5 + 0.4 * scarcity_factor)  # range 70 to 126

    # Adjust based on own health
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9  # 126
    elif hp <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)  # at least 98

    # Look at opponents' yesterday bids to avoid being outbid by small margin
    yesterday_max = 0
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_max = max(yesterday_max, trace['bid'])

    # If yesterday's max bid is known, try to beat it slightly, but not too high
    if yesterday_max > 0:
        target = yesterday_max + 1.5
        # Cap target at a reasonable level: maybe 1.1 * DAILY_SALARY to avoid overspend
        target = min(target, DAILY_SALARY * 1.1)
        base_bid = max(base_bid, target)

    # Ensure bid does not exceed budget
    bid = min(budget, base_bid)
    # Also ensure a minimum bid to avoid extreme bids when budget is low
    bid = max(bid, 1.0)

    return bid
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
    
    # Determine alive opponents with previous trace
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    yesterday_max_bid = 0.0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > yesterday_max_bid:
                yesterday_max_bid = bid
    
    hp = int(my_status['hp'])
    budget = int(my_status['budget'])
    
    # Base bid according to health
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # If we saw a high bid yesterday, attempt to slightly outdo it
    if yesterday_max_bid > 0:
        target = yesterday_max_bid + 2.0
        if target > base_bid:
            base_bid = target
    
    # Ensure we don't exceed budget
    final_bid = min(budget, base_bid)
    # Also ensure non-negative
    if final_bid < 0:
        final_bid = 0.0
    return final_bid
"""
