# ============================================================
# Experiment: exp_095
# Agent: Eric
# Source: exp_095
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    SUPPLY = int(day_context['supply'])
    DAY = int(day_context['day'])
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    my_hp = int(my_status['hp'])
    my_budget = int(my_status['budget'])
    
    # Default baseline bid based on supply
    baseline = min(my_budget, DAILY_SALARY * 0.5)
    
    if not alive_opponents:
        # Only me, bid minimal
        return min(my_budget, DAILY_SALARY * 0.3)
    
    # Analyze yesterday's opponent behavior from previous_trace
    high_bid_yesterday = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            high_bid_yesterday = max(high_bid_yesterday, float(prev['bid']))
    
    # Adjust based on my health
    if my_hp <= 2:
        # Desperate: need water
        aggressive_bid = min(my_budget, DAILY_SALARY * 0.9)
        return aggressive_bid
    elif my_hp <= 4:
        # Moderate need, counter opponents
        if high_bid_yesterday > DAILY_SALARY * 0.7:
            # Opponents were aggressive yesterday, maybe conserve
            return min(my_budget, DAILY_SALARY * 0.55)
        else:
            return min(my_budget, DAILY_SALARY * 0.6)
    else:
        # Healthy
        if high_bid_yesterday > DAILY_SALARY * 0.8:
            # Opponent desperate, undercut them
            return min(my_budget, DAILY_SALARY * 0.45)
        else:
            return min(my_budget, baseline)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    urgency = 0
    if no_water_days >= 1:
        urgency += 1
    if my_hp <= 3:
        urgency += 1
    if my_hp <= 1:
        urgency += 1
    if urgency >= 2:
        base_bid = DAILY_SALARY * 0.9
    elif urgency == 1:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    max_prev_bid = 0
    for opp in opponents_status.values():
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and 'bid' in prev_trace and prev_trace['bid'] is not None:
            max_prev_bid = max(max_prev_bid, prev_trace['bid'])
    if max_prev_bid > 0:
        target_bid = max_prev_bid + 1.0
    else:
        target_bid = base_bid
    final_bid = min(my_budget, max(base_bid, target_bid))
    if supply < 20:
        final_bid = min(my_budget, final_bid * 1.2)
    if day <= 3:
        final_bid = min(my_budget, final_bid * 0.8)
    elif day >= 8:
        final_bid = min(my_budget, final_bid * 1.1)
    final_bid = max(final_bid, 1.0)
    return final_bid
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather previous bids from yesterday's trace
    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])
    
    if not alive_opponents:
        # No competition, bid minimal
        bid = min(budget, DAILY_SALARY * 0.3)
        return max(0, bid)
    
    # Determine aggressiveness based on HP and no_water_days
    if hp <= 2 or no_water_days >= 2:
        # Must win water
        target_bid = min(budget, DAILY_SALARY * 1.2)
        if previous_bids:
            highest_prev = max(previous_bids)
            target_bid = max(target_bid, highest_prev + 1)
        return min(budget, target_bid)
    
    # Default: use previous opponent bids to gauge competition
    if previous_bids:
        highest_prev = max(previous_bids)
        if highest_prev > DAILY_SALARY * 0.8:
            # Aggressive opponent, respond moderately if we have HP
            if supply >= 20:
                bid = min(budget, highest_prev * 0.7)
            else:
                bid = min(budget, max(DAILY_SALARY * 0.6, highest_prev * 0.85))
        else:
            # Low competition, slightly outbid
            bid = min(budget, max(DAILY_SALARY * 0.4, highest_prev + 2))
    else:
        # No previous bids (first day or no trace), test with moderate bid
        if supply >= 20:
            bid = min(budget, DAILY_SALARY * 0.5)
        else:
            bid = min(budget, DAILY_SALARY * 0.7)
    
    # Ensure we don't bid more than budget
    bid = min(budget, bid)
    return max(0, bid)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev['bid'] > 0:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        high_prev_bid = max(yesterday_bids)
    else:
        avg_prev_bid = DAILY_SALARY * 0.7
        high_prev_bid = DAILY_SALARY * 0.8
    aggressive_factor = 1.0
    if hp <= 2:
        aggressive_factor = 1.15
    elif hp <= 4:
        aggressive_factor = 1.05
    elif day >= 8:
        aggressive_factor = 1.1
    bid = avg_prev_bid * aggressive_factor + 1.0
    if day <= 2 and budget > 500:
        bid = max(bid, high_prev_bid + 2.0)
    max_afford = min(budget, DAILY_SALARY * 1.2)
    bid = min(bid, max_afford)
    bid = max(bid, 0.0)
    return int(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's bids from opponents' previous_trace (only if available)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev.get('bid'), (int, float)) and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine the maximum bid from yesterday among alive opponents
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0
    
    supply = day_context['supply']
    
    # Base bid according to supply tightness
    # If supply is low, competition is high; otherwise moderate
    if supply <= (15 + 25) / 2:  # low supply
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on my HP
    if my_status['hp'] <= 2:
        # Critical: need water, bid aggressively
        target_bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, max_yesterday_bid + 1.0))
    elif my_status['hp'] <= 5:
        # Moderate need: just above yesterday's top bid if we can afford
        target_bid = min(my_status['budget'], max(base_bid, max_yesterday_bid + 1.0))
    else:
        # Healthy: conserve budget, bid low but enough for survival if needed
        # Use a fraction of yesterday's top bid to stay competitive
        target_bid = min(my_status['budget'], max(base_bid * 0.8, max_yesterday_bid * 0.9))
    
    # Ensure we don't bid more than budget
    bid = max(0.0, min(target_bid, my_status['budget']))
    # Round to avoid floating point issues
    return round(bid, 2)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    avg_yesterday = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else DAILY_SALARY * 0.5
    # Adjust based on my HP and budget
    if my_status['hp'] <= 2:
        # Desperate: outbid average by a margin
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.8, avg_yesterday + 5))
    elif my_status['hp'] <= 5:
        # Moderate need: slightly above average
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_yesterday * 1.1))
    else:
        # Comfortable: undercut to save money
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.3, avg_yesterday * 0.8))
    # Ensure non-negative
    return max(0, bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    # Use previous trace to estimate opponent behavior
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append((prev['bid'], opp['hp'], opp['water_requirement']))

    # Determine highest expected bid
    expected_max = 0
    if yesterday_bids:
        # Heuristic: if opponent had low hp, they might bid high again
        for bid, hp, req in yesterday_bids:
            if hp <= 2:
                expected_max = max(expected_max, bid + 5)
            else:
                expected_max = max(expected_max, bid * 0.9)
    else:
        expected_max = DAILY_SALARY * 0.8

    # My bid decision
    if my_status['hp'] <= 2:
        bid = min(my_status['budget'], expected_max + 5 + DAILY_SALARY * 0.1)
    elif my_status['hp'] <= 4:
        bid = min(my_status['budget'], expected_max + 2)
    else:
        bid = min(my_status['budget'], max(DAILY_SALARY * 0.6, expected_max + 1))

    # Ensure we don't bid more than budget
    return int(min(my_status['budget'], bid))
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, max(1, DAILY_SALARY * 0.5))
    
    # Collect yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Estimate current opponent aggressiveness
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        mean_prev = sum(yesterday_bids) / len(yesterday_bids)
        # If max is very high, opponents are aggressive; we can be conservative if hp is good
        if max_prev > DAILY_SALARY * 1.2:
            if hp > 5:
                target = max(1, mean_prev * 0.7)
            elif hp <= 2:
                target = min(budget, max(DAILY_SALARY * 0.9, max_prev * 0.85))
            else:
                target = min(budget, max(DAILY_SALARY * 0.6, mean_prev * 0.8))
        else:
            # Moderate aggressiveness - bid slightly above average
            target = min(budget, max(DAILY_SALARY * 0.5, mean_prev * 0.9))
    else:
        # No info: use fixed strategy based on hp
        if hp <= 2:
            target = min(budget, DAILY_SALARY * 0.85)
        elif hp <= 5:
            target = min(budget, DAILY_SALARY * 0.65)
        else:
            target = min(budget, DAILY_SALARY * 0.55)
    
    # Ensure bid non-negative, not exceed budget
    bid = max(0, min(budget, target))
    return bid
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
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    num_winners = int(supply // WATER_REQ)
    # Collect previous bids from alive opponents, exclude None or missing
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    prev_bids.sort(reverse=True)
    # Estimate bid threshold: we need to be among top num_winners
    # If there are no previous bids, use a conservative baseline
    if not prev_bids:
        # No info, bid safe amount: slightly above salary/2
        target = DAILY_SALARY * 0.6
    else:
        # We want to beat the bid at position (num_winners - 1) if enough opponents
        if len(prev_bids) >= num_winners:
            threshold = prev_bids[num_winners - 1]
            # Add a small margin to outbid
            target = threshold + 1.5
        else:
            # Fewer opponents than winners, can bid minimal
            target = DAILY_SALARY * 0.3
    # Adjust based on our HP
    if hp <= 2:
        # Desperate: bid as high as possible to secure water
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # Moderate health: bid slightly above threshold
        target = max(target, DAILY_SALARY * 0.6)
    else:
        # Healthy: save money, bid just enough to stay in race
        target = max(target, DAILY_SALARY * 0.4)
    # Ensure not to exceed budget
    bid = min(budget, target)
    # Never bid more than we can afford
    bid = max(bid, 0.0)
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
    
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # get yesterday's bids from opponents that have trace
    previous_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])
    
    # base bid: enough to get water, but not too high
    base_bid = (DAILY_SALARY * 0.45)  # ~63
    
    if previous_bids:
        max_prev = max(previous_bids)
        min_prev = min(previous_bids)
        # if at least one opponent had a high bid (>= 80% of salary), they are aggressive
        aggressive = max_prev >= 0.8 * DAILY_SALARY
        if aggressive:
            # if we have decent hp, avoid overpaying
            if hp > 3:
                bid = base_bid * 0.8  # ~50
            else:
                # need water, bid slightly above max_prev to outbid them
                bid = max_prev + 1.0
        else:
            # lower competition, bid moderately
            bid = max(base_bid, min_prev + 2.0)
    else:
        # first day or no data: use conservative bid
        bid = base_bid
    
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    # Need to ensure we can cover at least the minimum supply? No, we just need to outbid others.
    # Minimum bid should be enough to possibly win: at least 1?
    bid = max(bid, 1.0)
    return bid
"""
