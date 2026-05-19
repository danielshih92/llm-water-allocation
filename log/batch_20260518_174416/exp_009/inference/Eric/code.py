# ============================================================
# Experiment: exp_009
# Agent: Eric
# Source: exp_009
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    last_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev and prev['bid'] is not None:
            last_bids.append(prev['bid'])
    
    # base bid depends on health
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 4:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.5
    
    # adjust for competition from yesterday
    if last_bids:
        max_last = max(last_bids)
        if max_last > base:
            base = max(base, max_last + 1.0)
    
    # if supply is low, increase bid
    if supply < WATER_REQ * 2:
        base = min(DAILY_SALARY, base * 1.2)
    
    bid = min(budget, base)
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid very low to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid considering urgency
    if my_hp <= 2 or no_water_days >= 1:
        urgency_multiplier = 0.9
    elif my_hp <= 4:
        urgency_multiplier = 0.7
    else:
        urgency_multiplier = 0.5
    
    base_bid = DAILY_SALARY * urgency_multiplier
    
    # Adjust based on yesterday's highest bid (if any)
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If opponents were aggressive, we might need to match or exceed
        if highest_prev > DAILY_SALARY * 0.8:
            # Opponents aggressive; if we can afford, bid slightly above their max
            if my_hp <= 3:
                target = min(highest_prev + 2, my_budget)
            else:
                target = min(highest_prev * 0.85, my_budget)
        else:
            # Opponents moderate; we can outbid them by small margin
            target = min(max(base_bid, highest_prev + 1.5), my_budget)
    else:
        target = min(base_bid, my_budget)
    
    # Ensure we don't bid more than we can afford and at least 0
    bid = max(0.0, target)
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    daily_salary = 140
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Determine base bid based on urgency
    if hp <= 2:
        base_bid = daily_salary * 0.85  # desperate
    elif hp <= 5:
        base_bid = daily_salary * 0.55  # moderately cautious
    else:
        base_bid = daily_salary * 0.35  # save budget
    
    # Adjust if many opponents: increase competition
    if num_alive >= 3:
        base_bid *= 1.2
    elif num_alive <= 1:
        base_bid *= 0.8
    
    # Ensure bid is within budget and not negative
    bid = max(1, min(budget, base_bid))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    salary = 140
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    if num_alive == 0:
        return min(my_status['budget'], salary * 0.4)
    
    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    need_water = (my_status['no_water_days'] > 0) or (my_status['hp'] <= 2)
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
    else:
        max_yesterday = salary * 0.6
    
    if need_water:
        total_demand = WATER_REQ * (num_alive + 1)
        shortage = max(0, total_demand - supply)
        if shortage > 0:
            target = max_yesterday + shortage * 2
        else:
            target = max_yesterday + 1.0
        bid = min(my_status['budget'], target)
        bid = max(bid, salary * 0.5)
        return bid
    else:
        return min(my_status['budget'], salary * 0.3)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    winners = int(supply // WATER_REQ)
    
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    # Estimate opponent bids from previous trace
    estimated_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        bid = trace.get('bid')
        if bid is not None:
            estimated_bids.append(bid)
    
    # If no estimates, assume conservative bids
    if not estimated_bids:
        estimated_bids = [DAILY_SALARY * 0.5] * len(alive_opponents)
    
    # Sort estimated bids descending
    estimated_bids.sort(reverse=True)
    
    # Determine target bid to secure water
    if winners == 0:
        target = 0  # no water available
    elif winners >= len(alive_opponents) + 1:
        target = 1  # minimal bid to win
    else:
        # Need to outbid the (winners-1)th opponent (0-indexed)
        if winners - 1 < len(estimated_bids):
            target = estimated_bids[winners - 1] + 1
        else:
            target = estimated_bids[-1] + 1 if estimated_bids else 1
    
    # Adjust based on desperation
    hp = my_status.get('hp', 10)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)
    
    if no_water_days > 0 or hp <= 2:
        # Desperate - bid high
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp > 5:
        # Comfortable - bid low to save money
        bid = min(budget, max(1, DAILY_SALARY * 0.3))
    else:
        # Moderate - aim to outbid median
        bid = min(budget, max(target, DAILY_SALARY * 0.4))
    
    # Ensure bid is not negative
    bid = max(0, bid)
    # Cap at budget
    bid = min(budget, bid)
    
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    max_prev_bid = max(prev_bids) if prev_bids else 0
    
    # Calculate urgency
    urgent = (hp <= 3) or (no_water_days > 0)
    
    if urgent:
        # Need to win: outbid yesterday's max by a small margin, up to budget
        target = max(DAILY_SALARY * 0.9, max_prev_bid + 1.0)
        return min(budget, target)
    else:
        # Moderate bid, but adjust if supply is very low
        base = DAILY_SALARY * 0.5
        if supply < 20:
            base = DAILY_SALARY * 0.65
        # Ensure we don't overbid unnecessarily
        return min(budget, base)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140

    supply = int(day_context['supply'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # Get alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Extract yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if not yesterday_bids:
        # No data: bid conservatively to survive
        if my_hp <= 2:
            # Desperate: bid enough to get water
            return min(my_budget, DAILY_SALARY * 0.9)
        else:
            return min(my_budget, DAILY_SALARY * 0.4)

    highest_yesterday = max(yesterday_bids)

    # Estimate current opponent bids: assume similar or slightly higher
    # To guarantee water, we need to bid at least supply / (num_alive+1) * waterreq? Not exactly.
    # Simple: if highest_yesterday was very high, we may need to exceed it
    if highest_yesterday >= DAILY_SALARY * 0.85:
        if my_hp > 3:
            # Not desperate, can afford to bid lower
            return min(my_budget, DAILY_SALARY * 0.5)
        else:
            # Need water, match or exceed
            return min(my_budget, max(DAILY_SALARY * 0.9, highest_yesterday + 1))
    else:
        # Low pressure, bid just above average? Or use a safe margin
        # Average of yesterday's bids? Or just a bit more than the highest
        return min(my_budget, max(DAILY_SALARY * 0.4, highest_yesterday + 1.5))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(my_budget, 0.2 * DAILY_SALARY)
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    if my_hp <= 2:
        if prev_bids:
            base = max(prev_bids) + 2
        else:
            base = 0.9 * DAILY_SALARY
        return min(my_budget, base)
    elif my_hp <= 5:
        if prev_bids:
            base = max(sum(prev_bids) / len(prev_bids), 0.5 * DAILY_SALARY)
        else:
            base = 0.5 * DAILY_SALARY
        return min(my_budget, base)
    else:
        if prev_bids:
            base = min(prev_bids) - 2
        else:
            base = 0.3 * DAILY_SALARY
        return max(1, min(my_budget, base))
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

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid from yesterday's maximum
    if yesterday_bids:
        yesterday_max = max(yesterday_bids)
    else:
        yesterday_max = 0

    # Urgency based on HP and no_water_days
    need_water = (hp <= 2) or (no_water_days >= 1)

    if need_water:
        # Must secure water: bid just above yesterday's max if affordable
        target = min(budget, max(1, yesterday_max + 0.5))
        # But not exceed a reasonable fraction of salary
        target = min(target, DAILY_SALARY * 0.9)
    else:
        # Conservative: try to save, bid low
        target = min(budget, DAILY_SALARY * 0.4)
        # If yesterday's max was high, we might need to bid a bit more to avoid losing often
        if yesterday_max > DAILY_SALARY * 0.7:
            target = min(budget, DAILY_SALARY * 0.55)

    # Ensure non-negative and integer-like (float is fine)
    return max(0.0, target)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive = [o for o in opponents_status.values() if o['alive']]
    
    prev_bids = []
    for opp in alive:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    if no_water_days >= 2 or hp <= 3:
        base_bid = 0.9 * DAILY_SALARY
    elif hp > 7:
        base_bid = 0.4 * DAILY_SALARY
    else:
        base_bid = 0.6 * DAILY_SALARY
    
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        target = avg_prev + 5
        if target > base_bid:
            base_bid = target
    
    bid = min(budget, base_bid)
    bid = max(bid, 0)
    return bid
"""
