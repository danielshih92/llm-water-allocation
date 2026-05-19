# ============================================================
# Experiment: exp_046
# Agent: Eric
# Source: exp_046
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine max previous bid from opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    max_prev_bid = max(prev_bids) if prev_bids else 0
    
    # Base bid on hp
    if hp <= 2:
        # Critical need: bid high to secure water
        target_bid = DAILY_SALARY * 0.95
    elif hp >= 6:
        # Healthy, bid low and save
        target_bid = DAILY_SALARY * 0.3
    else:
        # Moderate need: try to beat previous max but not too high
        target_bid = max(DAILY_SALARY * 0.4, min(DAILY_SALARY * 0.7, max_prev_bid + 1.5))
    
    # Cap by budget
    bid = min(budget, target_bid)
    # Ensure bid is non-negative
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid calculation
    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        # If we are desperate, bid above average to guarantee water
        if my_status['hp'] <= 3 or my_status['no_water_days'] >= 2:
            target_bid = min(avg_yesterday + 3, DAILY_SALARY * 0.85)
        else:
            # Conservative: bid below average, rely on supply
            target_bid = max(DAILY_SALARY * 0.3, avg_yesterday - 5)
    else:
        # No trace info, use default
        if my_status['hp'] <= 3:
            target_bid = DAILY_SALARY * 0.8
        else:
            target_bid = DAILY_SALARY * 0.4
    
    # Adjust based on supply (high supply means more water available, lower bid needed)
    supply = day_context['supply']
    if supply > 20:
        target_bid *= 0.85
    elif supply < 17:
        target_bid *= 1.15
    
    # Ensure not exceeding budget and not less than 0
    target_bid = max(0, min(my_status['budget'], target_bid))
    return target_bid
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    # Base bid proportional to supply scarcity
    scarcity_factor = WATER_REQ / supply
    base_bid = DAILY_SALARY * scarcity_factor
    # Adjust for own urgency
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    # Consider opponents' previous highest bid
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    # React based on past aggression
    if max_prev_bid > DAILY_SALARY * 0.8 and hp > 2:
        base_bid = min(base_bid, max_prev_bid * 0.95)
    else:
        base_bid = max(base_bid, max_prev_bid * 0.9 + 1)
    # Clamp to budget and non-negative
    bid = max(0, min(budget, base_bid))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8

    alive_opponents = {k: v for k, v in opponents_status.items() if v.get('alive', False)}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect their previous bids from yesterday's trace
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Base bid
    base_bid = DAILY_SALARY * 0.5
    # If any opponent previously bid high, we might need to outbid them
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > base_bid:
            # Outbid by a small margin if we have enough budget and HP is not super high
            if my_status['hp'] > 5 and my_status['budget'] > max_prev + 0.1:
                target = max_prev + 0.1
            else:
                # If low HP or low budget, be more aggressive
                target = max_prev + 0.5
        else:
            target = base_bid
    else:
        target = base_bid

    # Adjust for personal situation
    if my_status['hp'] <= 2:
        # Desperate, bid high
        target = max(target, DAILY_SALARY * 0.85)
    elif my_status['hp'] >= 8:
        # Healthy, can be conservative
        target = min(target, DAILY_SALARY * 0.4)

    # Ensure within budget and non-negative
    bid = min(my_status['budget'], max(0, target))
    # Round to avoid floating issues
    return round(bid, 2)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Gather yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Compute a baseline bid: enough to secure water given supply
    base_bid = max(DAILY_SALARY * 0.3, (supply // WATER_REQ) * DAILY_SALARY * 0.1)

    # Emergency if low HP or consecutive days without water
    if hp <= 2 or no_water_days >= 2:
        target_bid = min(budget, DAILY_SALARY * 0.95)
    else:
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            if max_prev > DAILY_SALARY * 0.8:
                # Opponents were aggressive yesterday; we conserve
                target_bid = min(budget, max(base_bid, DAILY_SALARY * 0.3))
            else:
                # Outbid yesterday's max slightly
                target_bid = min(budget, max(base_bid, max_prev + 2.0))
        else:
            # No info: moderate conservative
            target_bid = min(budget, base_bid)

    # Ensure non-negative and reasonable
    bid = max(0.0, target_bid)
    return round(bid, 2)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opps = {k:v for k,v in opponents_status.items() if v['alive']}
    prev_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    if prev_bids:
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev_bid = DAILY_SALARY * 0.5
    if hp <= 2:
        bid = min(budget, max(DAILY_SALARY * 0.9, avg_prev_bid + 5))
    elif hp <= 4:
        bid = min(budget, max(DAILY_SALARY * 0.7, avg_prev_bid + 2))
    else:
        bid = min(budget, max(DAILY_SALARY * 0.4, avg_prev_bid - 5))
    if supply < (WATER_REQ * len(alive_opps) + 1):
        bid = min(budget, max(bid, DAILY_SALARY * 0.8))
    bid = max(1, bid)
    bid = min(budget, bid)
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Decision based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If yesterday was very high, conserve (they may persist)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            # Slightly outbid the previous max to secure water
            target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            return min(my_status['budget'], target)
    
    # Fallback if no yesterday data
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid depends on health
    if my_status['hp'] <= 2:
        base_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    else:
        base_bid = min(my_status['budget'], DAILY_SALARY * 0.6)
    
    # If any opponent previously bid very high, match or beat if we can
    if prev_bids:
        max_prev = max(prev_bids)
        # If my health is critical, beat the highest
        if my_status['hp'] <= 2:
            target = max_prev + 1.0
            base_bid = min(my_status['budget'], max(base_bid, target))
        # If healthy but previous bids were aggressive, raise slightly
        elif max_prev > DAILY_SALARY * 0.85:
            base_bid = min(my_status['budget'], max(base_bid, max_prev + 0.5))
    
    # Ensure positive and not exceed budget
    return max(0.0, min(my_status['budget'], base_bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    
    # Determine bid based on HP and yesterday's max
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0
    hp = my_status['hp']
    budget = my_status['budget']
    
    if hp <= 2:
        # Desperate: bid high to secure water
        target = min(budget, DAILY_SALARY * 0.9)
    else:
        # If high competition yesterday, try to undercut slightly
        if max_yesterday >= DAILY_SALARY * 0.85:
            target = min(budget, DAILY_SALARY * 0.45)
        else:
            # Otherwise, aim to beat the highest yesterday by a small margin
            target = min(budget, max(DAILY_SALARY * 0.5, max_yesterday + 2.0))
    
    # Ensure we never bid more than budget
    bid = max(1.0, min(target, budget))
    # Additional check: cap at daily salary * 1.0 to avoid waste
    bid = min(bid, DAILY_SALARY * 1.0)
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        base = max(DAILY_SALARY * 0.9, yesterday_max_bid + 1.0)
    else:
        base = DAILY_SALARY * 0.5
    return min(budget, base)
"""
