# ============================================================
# Experiment: exp_023
# Agent: Eric
# Source: exp_023
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']

    # Alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]

    # Gather yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    # Low HP -> bid high for survival
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            # If highest yesterday was high, we can lower our bid to save money
            if max_yesterday >= DAILY_SALARY * 0.85:
                bid = min(budget, DAILY_SALARY * 0.5)
            else:
                # Slightly outbid the highest, but not exceed 70% of salary
                target = max(DAILY_SALARY * 0.5, max_yesterday + 1.5)
                bid = min(budget, target, DAILY_SALARY * 0.7)
        else:
            # Default moderate bid
            bid = min(budget, DAILY_SALARY * 0.6)

    # Ensure bid is within budget
    bid = max(0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    max_winners = int(supply // WATER_REQ)
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and 'bid' in prev_trace:
                prev_bid = prev_trace['bid']
                if prev_bid is not None:
                    prev_bids.append(prev_bid)
    
    # Sort previous bids descending
    prev_bids.sort(reverse=True)
    
    # Estimate opponents' current bids: assume same as previous, but adjust for desperation
    # We need to predict the threshold bid to be among top max_winners
    if len(prev_bids) >= max_winners:
        # threshold is the (max_winners)th highest (0-index: max_winners-1)
        threshold = prev_bids[max_winners - 1]
    else:
        threshold = 0
    
    # Base bid: slightly above threshold, but not too high
    target_bid = threshold + 1.0
    
    # If we are desperate (low hp or high no_water_days), increase bid significantly
    if hp <= 2 or no_water_days >= 1:
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    
    # If healthy and early day, we can afford to be conservative
    if hp > 5 and day < 3:
        target_bid = min(target_bid, DAILY_SALARY * 0.5)
    
    # Ensure within budget
    target_bid = min(target_bid, budget)
    
    # Ensure non-negative
    target_bid = max(target_bid, 0.0)
    
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
    alive = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # get yesterday's max bid from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    max_prev_bid = max(prev_bids) if prev_bids else 0
    
    urgent = (hp <= 2) or (no_water_days >= 1)
    low_supply = supply <= 18
    
    if urgent:
        target = max(DAILY_SALARY * 0.9, max_prev_bid + 2.0)
        bid = min(budget, target)
    elif low_supply:
        target = max(DAILY_SALARY * 0.65, max_prev_bid + 1.0)
        bid = min(budget, target)
    else:
        target = min(DAILY_SALARY * 0.55, max_prev_bid + 0.5)
        bid = min(budget, target)
    
    return max(0.0, bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine if we need water urgently
    need_water = (my_hp <= 2) or (no_water_days >= 1)

    if need_water:
        # Aggressive bid: ensure we win
        if yesterday_bids:
            highest_prev = max(yesterday_bids)
            target_bid = max(highest_prev + 1.0, DAILY_SALARY * 0.85)
        else:
            target_bid = DAILY_SALARY * 0.95
        return min(my_budget, target_bid)
    else:
        # Conservative bid: try to save budget
        if yesterday_bids:
            highest_prev = max(yesterday_bids)
            # Bid just above half of highest_prev to occasionally win, but not too high
            target_bid = max(DAILY_SALARY * 0.35, highest_prev * 0.5)
        else:
            target_bid = DAILY_SALARY * 0.4
        return min(my_budget, target_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        max_prev = max(yesterday_bids)
    else:
        max_prev = 0
    # Supply scarcity multiplier: lower supply => need higher bid
    supply_factor = 1.0 + (25 - supply) / 20.0  # min 1.0, max 1.5
    if max_prev >= DAILY_SALARY * 0.85:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.95 * supply_factor)
        else:
            return min(budget, DAILY_SALARY * 0.3 * supply_factor)
    else:
        if hp <= 2:
            return min(budget, max(DAILY_SALARY * 0.5, max_prev + 2.0) * supply_factor)
        else:
            return min(budget, max(DAILY_SALARY * 0.4, max_prev + 1.5) * supply_factor)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']
    
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive'] and opp.get('previous_trace') and 'bid' in opp['previous_trace']:
            yesterday_bids.append(opp['previous_trace']['bid'])
    
    if not yesterday_bids:
        base_bid = DAILY_SALARY * 0.6
    else:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        if hp <= 3 or no_water_days >= 2:
            base_bid = max(DAILY_SALARY * 0.8, avg_bid + 5)
        else:
            base_bid = min(DAILY_SALARY * 0.7, max(DAILY_SALARY * 0.3, avg_bid + 2))
    
    if supply < 16:
        base_bid *= 1.2
    
    bid = min(budget, base_bid)
    return round(bid, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])
    max_prev = max(previous_bids) if previous_bids else 0
    epsilon = 1.5
    base_bid = min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev + epsilon))
    if my_status['hp'] <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    supply = day_context['supply']
    num_players = len(alive_opponents) + 1
    total_needed = num_players * WATER_REQ
    if supply < total_needed:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    if my_status['no_water_days'] >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    bid = min(base_bid, my_status['budget'])
    return max(0, bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    if prev_bids:
        highest_prev = max(prev_bids)
    else:
        highest_prev = 0.0

    base_bid = DAILY_SALARY * 0.55  # moderate
    if no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 2:
        base_bid = DAILY_SALARY * 0.8
    elif hp >= 6:
        # can afford to be low
        base_bid = DAILY_SALARY * 0.3

    if highest_prev > 0:
        if highest_prev >= DAILY_SALARY * 0.85:
            if hp > 3 and no_water_days == 0:
                base_bid = min(base_bid, DAILY_SALARY * 0.35)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.85)
        else:
            base_bid = max(base_bid, highest_prev + 1.0)

    bid = min(budget, base_bid)
    bid = max(bid, 0.0)
    # Ensure we don't exceed budget or salary
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Filter alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from previous_trace if available
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine baseline bid based on urgency and competition
    if hp <= 2 or no_water_days >= 2:
        # Desperate: need water at almost any cost
        base_bid = min(budget, DAILY_SALARY * 0.95)
    else:
        # Healthy: we can be more conservative
        if yesterday_bids:
            # Highest opponent bid yesterday gives clue about their aggressiveness
            max_yesterday_bid = max(yesterday_bids)
            # If someone bid very high, they might have limited budget today, but we still need to outbid if necessary
            # Estimate a safe bid: just above yesterday's highest (if we can afford) or a fraction of salary
            planned = max(DAILY_SALARY * 0.45, max_yesterday_bid + 0.01)
            base_bid = min(budget, planned)
        else:
            # No trace: assume moderate competition
            base_bid = min(budget, DAILY_SALARY * 0.5)
    
    # Adjust for supply: if supply is high, we might win with lower bid
    # but if supply is low, competition may be fierce
    # Supply ranges 15-25, so adjust multiplier
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # Lower supply factor => more scarce => bid higher
    bid = base_bid * (1.5 - 0.5 * supply_factor)  # scale between 1.0x and 1.5x
    bid = min(bid, budget)  # cannot exceed budget
    bid = max(bid, 0.01)    # positive bid
    return bid
"""
