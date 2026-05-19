# ============================================================
# Experiment: exp_050
# Agent: Eric
# Source: exp_050
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])  # ensure integer
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Look at yesterday's highest bid among alive opponents
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = prev['bid']
            if bid_val > highest_prev_bid:
                highest_prev_bid = bid_val

    # Base bid: salary proportion
    base_bid = DAILY_SALARY * 0.5

    # Adjust for water need
    if hp <= 2 or no_water_days >= 2:
        # urgent, be aggressive but not exceeding budget
        aggressive_bid = min(budget, DAILY_SALARY * 0.9)
        return aggressive_bid

    # If yesterday's highest was high, we can be more moderate
    if highest_prev_bid > DAILY_SALARY * 0.7:
        # competition is strong, bid just above to secure water
        bid = min(budget, max(base_bid, highest_prev_bid + 1.5))
    else:
        # moderate competition, safe to bid lower
        bid = min(budget, base_bid)

    # Ensure we don't bid more than budget
    bid = min(bid, budget)
    # Keep a small reserve if budget allows
    reserve = DAILY_SALARY * 0.1
    if budget - bid < reserve:
        bid = max(0, budget - reserve)

    return max(0, bid)
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
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect previous bids from yesterday's trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine aggressive threshold from historical max
    if prev_bids:
        max_prev = max(prev_bids)
    else:
        max_prev = 0.0

    # Base bid depending on health
    hp = my_status['hp']
    budget_left = my_status['budget']

    if hp <= 2:
        # Desperate: outbid aggressive opponents if needed
        desired = max(DAILY_SALARY * 0.9, max_prev + 1.0)
        return min(budget_left, desired)
    elif hp <= 5:
        # Moderate health: balance savings and survival
        desired = max(DAILY_SALARY *
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = {k: v for k, v in opponents_status.items() if v['alive']}
    n_alive = len(alive_opps)

    # Get yesterday's bids from opponents
    prev_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev_bid = max(prev_bids) if prev_bids else 0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0

    # Estimate number of winners
    max_winners = int(supply // WATER_REQ)
    if max_winners <= 0:
        # No water, need to bid high but only if we can
        if hp <= 2 or no_water_days > 0:
            return min(budget, DAILY_SALARY * 0.95)
        else:
            return min(budget, DAILY_SALARY * 0.3)

    # Base factor from supply
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1, high supply -> lower bid
    base_factor = 0.5 + 0.3 * (1 - supply_ratio)  # range 0.5 to 0.8

    # Adjust for hp
    if hp <= 2:
        hp_factor = 1.2
    elif hp <= 4:
        hp_factor = 1.0
    else:
        hp_factor = 0.8

    # Desperation from no_water_days
    if no_water_days > 0:
        hp_factor *= 1.1

    # Competition: if many alive and few winners, raise bid
    competition_factor = 1.0
    if n_alive > 0:
        needed_water = n_alive * WATER_REQ
        if needed_water > supply:
            # shortage -> bid higher
            shortage_ratio = (needed_water - supply) / needed_water
            competition_factor = 1.0 + 0.5 * shortage_ratio

    # React to yesterday's max bid: if it was high, we might need to match or exceed
    reaction_factor = 1.0
    if max_prev_bid > 0:
        # If last day's max bid was high, we might need to compete
        if max_prev_bid > DAILY_SALARY * 0.7:
            reaction_factor = 1.2
        elif max_prev_bid > DAILY_SALARY * 0.5:
            reaction_factor = 1.1
        # If we were outbid yesterday (we didn't win?), we can't know that from trace? ignore

    # Compute target bid
    target_bid = DAILY_SALARY * base_factor * hp_factor * competition_factor * reaction_factor
    target_bid = min(target_bid, DAILY_SALARY * 1.2)  # cap
    target_bid = max(target_bid, DAILY_SALARY * 0.2)    # floor

    # Ensure we don't exceed budget
    bid = min(budget, target_bid)

    # If budget is very low, emergency low bid
    if budget < DAILY_SALARY * 0.5 and hp > 2:
        bid = min(budget, DAILY_SALARY * 0.3)

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [opp for opp in opponents_status.values() if opp['alive']]
    
    # Gather yesterday's bids from alive opponents (if available)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine desperation
    desperate = (hp <= 2) or (no_water_days >= 1)
    
    # Base target: if desperate, high; otherwise, moderate
    high_bid = min(budget, DAILY_SALARY * 0.95)
    moderate_bid = min(budget, DAILY_SALARY * 0.55)
    
    if desperate:
        target_bid = high_bid
    else:
        target_bid = moderate_bid
    
    # Adjust based on yesterday's highest bid (if any alive opponents)
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If we are not desperate, try to barely beat highest yesterday, but cap
        if not desperate and highest_prev < DAILY_SALARY * 0.9:
            target_bid = min(budget, max(highest_prev + 2, moderate_bid))
        # If desperate, we may need to exceed highest seen
        if desperate and highest_prev > moderate_bid:
            target_bid = min(budget, highest_prev + 5)
    
    # Ensure we never bid more than budget
    final_bid = min(budget, max(target_bid, 1.0))
    return final_bid
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
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    highest_prev = max(prev_bids) if prev_bids else 0.0

    # Emergency: need water badly
    if no_water_days > 0 or hp <= 2:
        # Bid aggressively to ensure win
        aggressive_bid = min(budget, max(DAILY_SALARY * 0.9, highest_prev + 2.0))
        return aggressive_bid

    # Normal: try to conserve
    if highest_prev > 0:
        # Outbid slightly if we can afford top, else go safe
        desired_bid = max(highest_prev + 1.0, DAILY_SALARY * 0.45)
        return min(budget, desired_bid)
    else:
        # No history: safe bid based on supply
        safe_bid = DAILY_SALARY * 0.5
        if supply < 20:
            safe_bid = DAILY_SALARY * 0.6
        return min(budget, safe_bid)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.1)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    if prev_bids:
        max_prev = max(prev_bids)
        if hp > 5:
            target = max_prev + 5
        elif hp > 2:
            target = max_prev + 10
        else:
            target = max_prev + 20
    else:
        target = DAILY_SALARY * 0.6
    bid = min(budget, target)
    if supply < 18 and hp <= 3:
        bid = min(budget, DAILY_SALARY * 0.95)
    bid = max(0, min(budget, bid))
    return bid
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

    # Find Alex's previous bid if available
    alex_trace = opponents_status.get('Alex', {}).get('previous_trace', {})
    alex_prev_bid = None
    if alex_trace and 'bid' in alex_trace:
        alex_prev_bid = alex_trace['bid']

    # Determine base need-based bid
    needed_ratio = WATER_REQ / supply if supply > 0 else 1.0
    base_bid = needed_ratio * DAILY_SALARY * 0.8  # conservative

    # Adjust based on hunger
    if hp <= 2 or no_water_days >= 2:
        # Desperate: need to win
        if alex_prev_bid:
            target = alex_prev_bid + 1.5
        else:
            target = DAILY_SALARY * 0.9
        bid = max(target, base_bid)
    elif hp <= 5:
        # Mild need: match or slightly beat Alex if he was high
        if alex_prev_bid and alex_prev_bid > base_bid:
            bid = alex_prev_bid + 1.0
        else:
            bid = base_bid
    else:
        # Healthy: bid low to save
        if alex_prev_bid and alex_prev_bid < DAILY_SALARY * 0.4:
            bid = alex_prev_bid - 0.5
        else:
            bid = DAILY_SALARY * 0.2

    # Ensure we don't exceed budget and not negative
    bid = min(budget, max(0, bid))
    # Smooth for supply extremes
    if supply < 18:
        bid = min(budget, bid * 1.2)
    return round(bid, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']

    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # urgency based on health and water deprivation
    urgent = (no_water >= 2 or hp <= 2)

    # get alive opponents and their previous day's bid (if available)
    alive = [o for o in opponents_status.values() if o
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Determine number of winners (how many can get water)
    winners_count = int(supply // WATER_REQ)
    
    # Collect previous bids from alive opponents using their trace
    prev_bids = []
    for oid, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Default bid if no trace
    default_bid = DAILY_SALARY * 0.6  # 84
    
    # If we have previous bids, compute target
    target = default_bid
    if prev_bids:
        # Sort bids descending
        sorted_bids = sorted(prev_bids, reverse=True)
        # We want to be among top winners_count
        if winners_count > 0 and len(sorted_bids) >= winners_count:
            # Target to beat the bid at position winners_count (0-indexed: winners_count-1)
            cut_bid = sorted_bids[winners_count - 1]
            target = cut_bid + 1.5
        else:
            # If we have fewer bids than winners, just beat the smallest of them
            min_prev = min(sorted_bids)
            target = min_prev + 1.5
    
    # Adjust based on desperation
    if hp <= 2 or no_water_days >= 1:
        # Urgent need water
        bid = min(budget, DAILY_SALARY * 0.95)
    elif day == 10:  # last day, use leftover
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None:
            prev_bids.append(opp['previous_trace']['bid'])

    # Determine baseline bid based on urgency
    if hp <= 2:
        # desperate: bid high
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        # moderate risk
        base_bid = DAILY_SALARY * 0.7
    else:
        # healthy, try to lowball if possible
        base_bid = DAILY_SALARY * 0.5

    # If we have high previous bids from opponents, match or slightly exceed
    if prev_bids:
        max_prev = max(prev_bids)
        # We want to outbid the highest previous, but not waste
        target = max(my_status['budget'] * 0.2, max_prev + 1.0)
        # Cap at a reasonable fraction of salary to save budget
        target = min(target, DAILY_SALARY * 0.9)
        # Also consider our base urgency
        bid = min(base_bid, target) if hp > 2 else max(base_bid, target)
    else:
        bid = base_bid

    # Ensure we don't bid more than budget
    bid = min(bid, budget)
    # Ensure non-negative
    bid = max(bid, 0.0)
    # Round to avoid tiny decimals
    bid = round(bid, 2)
    return bid
"""
