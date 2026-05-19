# ============================================================
# Experiment: exp_045
# Agent: Eric
# Source: exp_045
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])  # ensure integer for calculations
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    WATER_REQ = 8
    DAILY_SALARY = 140
    # If critical low HP, bid high to survive
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif no_water_days >= 1:
        bid = min(budget, DAILY_SALARY * 0.8)
    else:
        # Normal: bid moderate, increase if supply is low
        # Supply low means more competition for limited water
        if supply < 18:
            bid = min(budget, DAILY_SALARY * 0.65)
        elif supply < 22:
            bid = min(budget, DAILY_SALARY * 0.55)
        else:
            bid = min(budget, DAILY_SALARY * 0.4)
    # Ensure bid is non-negative and within budget
    return max(0, min(budget, bid))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine if previous day there were high bids
    high_bid_threshold = DAILY_SALARY * 0.8
    yesterday_high_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid >= high_bid_threshold:
                yesterday_high_bids.append(bid)

    # If any opponent bid very high yesterday, assume aggressive today
    aggressive_opponents = len(yesterday_high_bids) > 0

    # Determine urgency
    need_water = (my_status['hp'] <= 2) or (my_status['no_water_days'] > 0)

    if need_water:
        # Must win water: bid high to beat aggressive opponents
        if aggressive_opponents:
            target_bid = DAILY_SALARY * 1.2
        else:
            target_bid = DAILY_SALARY * 0.9
    else:
        # Conserve budget: bid low
        target_bid = DAILY_SALARY * 0.1

    # Adjust based on supply scarcity (fewer units -> higher competition)
    supply = day_context['supply']
    # Number of alive players (including self)
    num_alive = len(alive_opponents) + 1
    total_demand = num_alive * WATER_REQ
    if supply < total_demand:
        # Scarcity: increase bid
        scarcity_factor = total_demand / max(supply, 1)
        target_bid *= min(scarcity_factor, 2.0)

    # Ensure bid does not exceed budget
    bid = min(target_bid, my_status['budget'])
    # Also ensure at least 0
    bid = max(bid, 0)

    # Round to avoid floating point issues
    bid = round(bid, 2)
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_status['hp'] <= 2:
            # desperate: bid high
            return min(my_status['budget'], highest_prev_bid + 15)
        elif my_status['hp'] <= 4:
            return min(my_status['budget'], highest_prev_bid + 10)
        else:
            # healthy: just outbid slightly
            return min(my_status['budget'], highest_prev_bid + 5)
    else:
        # no history: bid based on hp
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    # Base bid as fraction of daily salary, scaled by supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 (scarce) to 1 (abundant)
    # Lower supply -> higher bid
    base_fraction = 0.3 + 0.3 * (1 - supply_ratio)  # 0.3 to 0.6

    # Adjust based on day: increase pressure as days go on (episode 10 days)
    day_factor = 1.0 + 0.05 * (day - 1)  # day 1:1.0, day 10:1.45
    base_bid = DAILY_SALARY * base_fraction * day_factor

    # If HP is low, bid more aggressively to survive
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Ensure we have enough budget for future days (keep at least 2*DAILY_SALARY for last days?)
    # Simple: cap bid to not exceed remaining budget minus a reserve
    reserve = DAILY_SALARY * (10 - day) * 0.15  # heuristic reserve
    max_bid = max(0, budget - reserve)
    final_bid = min(base_bid, max_bid)

    # Ensure at least minimum raise if alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if alive_opponents:
        # Consider a small edge over possible low bids
        final_bid = max(final_bid, DAILY_SALARY * 0.25)

    return int(final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    # Extract current values
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v.get('alive', False)}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.2)
    
    # Collect yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])
    
    # Determine threat level
    high_threat = False
    if hp <= 2:
        high_threat = True
    
    # Decide bid base
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # if we need water badly, outbid the highest by a margin
        if high_threat:
            target_bid = max_yesterday + 5.0
        else:
            # else, target slightly above the second highest or just below highest
            sorted_bids = sorted(yesterday_bids, reverse=True)
            if len(sorted_bids) >= 2:
                second = sorted_bids[1]
                target_bid = second + 2.0
            else:
                target_bid = max_yesterday * 0.9  # conservative
        # Ensure we don't exceed budget
        bid = min(budget, target_bid)
        # Also cap to reasonable max to avoid overspending
        bid = min(bid, DAILY_SALARY * 1.2)
    else:
        # No yesterday data, base on HP
        if high_threat:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
    
    # Ensure bid is non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    
    # Determine urgency based on HP
    if hp <= 2:
        urgency = 0.9
    elif hp <= 5:
        urgency = 0.7
    else:
        urgency = 0.5
    
    # Adjust based on supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    scarcity_factor = 1 - supply_ratio  # higher when supply low
    base_bid = DAILY_SALARY * urgency * scarcity_factor
    
    # Consider opponents' previous bids
    max_prev_bid = 0
    for opp_id, opp_state in opponents_status.items():
        trace = opp_state.get('previous_trace')
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bid = trace['bid']
            if prev_bid > max_prev_bid:
                max_prev_bid = prev_bid
    
    # If someone bid very high yesterday, they might again; bid conservatively to save budget
    if max_prev_bid > 130:
        if hp > 5:
            base_bid = DAILY_SALARY * 0.3
        else:
            base_bid = DAILY_SALARY * 0.6
    elif max_prev_bid < 30:
        # Opponents may be bidding low; ensure we get water
        base_bid = max(base_bid, DAILY_SALARY * 0.5)
    
    # Ensure we don't overspend and don't go below zero
    bid = max(0, min(budget, base_bid))
    
    # As days progress, be more frugal if high budget, else cautious
    if budget > DAILY_SALARY * 3 and hp > 3:
        bid = min(bid, DAILY_SALARY * 0.4)
    
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Collect previous bids from traces
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine aggressive threshold: high bidder from yesterday
    aggressive = any(bid >= DAILY_SALARY * 0.9 for bid in prev_bids) if prev_bids else False
    
    # Base bid: half salary, but adjust
    base_bid = DAILY_SALARY * 0.5
    
    # If we are desperate (HP <= 2), increase bid
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.85
    
    # If opponents are aggressive and we can afford to be low, lower bid to save budget
    if aggressive and my_status['hp'] > 3:
        base_bid = DAILY_SALARY * 0.35
    
    # Ensure we don't exceed budget
    bid = min(my_status['budget'], base_bid)
    # Ensure non-negative
    bid = max(0, bid)
    
    # If supply is very low, competition higher, increase bid slightly
    supply = day_context['supply']
    if supply < 18 and my_status['hp'] > 3:
        bid = min(my_status['budget'], bid * 1.2)
    
    # Floor to 1 decimal if needed, but ensure integer? Output can be float but OK
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace')
            if prev_trace and prev_trace.get('bid') is not None:
                prev_bids.append(prev_trace['bid'])
    if hp <= 2:
        target = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        target = min(budget, DAILY_SALARY * 0.6)
    else:
        target = min(budget, DAILY_SALARY * 0.4)
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev < DAILY_SALARY * 0.5:
            target = max(target, min(budget, max_prev + 1.0))
        elif max_prev < DAILY_SALARY * 0.8:
            target = max(target, min(budget, max_prev + 2.0))
        else:
            if hp > 3:
                target = min(target, DAILY_SALARY * 0.3)
            else:
                target = max(target, min(budget, DAILY_SALARY * 0.8))
    bid = max(0, min(budget, target))
    return float(bid)
"""
