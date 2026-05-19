# ============================================================
# Experiment: exp_115
# Agent: Eric
# Source: exp_115
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive = [o for o in opponents_status.values() if o['alive']]
    base_bid = 70.0
    if my_status['hp'] <= 2:
        base_bid = 126.0
    elif my_status['hp'] <= 4:
        base_bid = 98.0
    if my_status['budget'] < base_bid:
        base_bid = my_status['budget'] * 0.8
    if alive:
        prev_bids = []
        for opp in alive:
            prev = opp.get('previous_trace')
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
        if prev_bids:
            highest_prev = max(prev_bids)
            if highest_prev > 112.0:
                if my_status['hp'] > 4:
                    base_bid = min(base_bid, 56.0)
                else:
                    base_bid = max(base_bid, highest_prev + 1)
            else:
                base_bid = max(base_bid, highest_prev + 2)
    bid = min(base_bid, my_status['budget'])
    bid = max(0, bid)
    return float(bid)
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
    
    # Estimate number of winners this round
    max_winners = int(supply // WATER_REQ)
    
    # Collect opponent previous bids (if any)
    prev_bids = []
    for opp in opponents_status.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    high_prev = max(prev_bids) if prev_bids else 0.0
    
    # Determine base bid
    if max_winners <= 1:
        # Only one winner, need high bid if water critical
        if hp <= 2:
            base = min(budget, high_prev * 1.15)
        else:
            base = min(budget, DAILY_SALARY * 0.6)
    elif max_winners <= 2:
        # Two winners
        if hp <= 2:
            base = min(budget, max(high_prev * 1.05, DAILY_SALARY * 0.5))
        else:
            base = min(budget, DAILY_SALARY * 0.45)
    else:
        # Three winners
        if hp <= 2:
            base = min(budget, DAILY_SALARY * 0.6)
        else:
            base = min(budget, DAILY_SALARY * 0.35)
    
    # Add small randomness to avoid bids at tie (optional)
    bid = round(base, 2)
    # Ensure bid not negative and not exceed budget
    bid = max(0.0, min(bid, budget))
    return bid
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
    n_alive = len(alive_opponents) + 1  # including self

    # gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    # base bid decision
    # if we are in urgent need
    urgent = (hp <= 2) or (no_water_days >= 2)
    if urgent:
        # bid high to secure water
        target_bid = min(budget, DAILY_SALARY * 0.9)
    else:
        # comfortable: try to outbid yesterday's highest by a small margin
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            # add a small increment to beat, but cap to avoid overpaying
            target_bid = min(budget, max_yesterday + 1.0)
            # ensure not too low
            target_bid = max(target_bid, DAILY_SALARY * 0.3)
        else:
            # no info: use conservative 50% of salary
            target_bid = min(budget, DAILY_SALARY * 0.5)

    # ensure bid is at least 0 and at most budget
    bid = max(0.0, min(budget, target_bid))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Base bid as fraction of salary
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
        bid_frac = 0.95
    else:
        bid_frac = 0.6
    target = min(my_status['budget'], DAILY_SALARY * bid_frac)
    # Check opponents' previous trace (only from yesterday)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if alive_opponents:
        max_prev_bid = 0
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                max_prev_bid = max(max_prev_bid, prev['bid'])
        # If someone bid very high yesterday, avoid wasteful bidding; else try to beat max
        if max_prev_bid > 0:
            if my_status['hp'] > 3:
                # If healthy, bid just above the second highest? But we don't have second. Use 60% of max? Simpler: bid 0.6 * salary or just above max if affordable
                if max_prev_bid < DAILY_SALARY * 0.7:
                    target = min(my_status['budget'], max_prev_bid + 1.0)
                else:
                    target = min(my_status['budget'], DAILY_SALARY * 0.4)
            else:
                # Low HP: bid high
                target = min(my_status['budget'], max(DAILY_SALARY * 0.85, max_prev_bid + 0.5))
    # Ensure target is not above budget
    bid = min(my_status['budget'], target)
    # Ensure positive bid
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and isinstance(prev, dict) and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    
    # Determine target bid based on my HP and yesterday's pressure
    if my_status['hp'] <= 2:
        # Critical: need water no matter what
        if yesterday_bids:
            target = max(yesterday_bids) + 2.0
        else:
            target = DAILY_SALARY * 0.9
        return min(my_status['budget'], max(target, 10.0))
    elif my_status['hp'] <= 5:
        # Moderate need, bid competitively
        if yesterday_bids:
            target = max(yesterday_bids) - 1.0
            if target < 10:
                target = max(yesterday_bids) + 0.5
        else:
            target = DAILY_SALARY * 0.6
        return min(my_status['budget'], max(target, 5.0))
    else:
        # Healthy, conserve budget
        if yesterday_bids:
            # Use median to undercut if possible
            sorted_bids = sorted(yesterday_bids)
            median_idx = len(sorted_bids) // 2
            median_bid = sorted_bids[median_idx]
            target = median_bid * 0.8
        else:
            target = DAILY_SALARY * 0.4
        return min(my_status['budget'], max(target, 2.0))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp_state in opponents_status.items():
        if opp_state['alive']:
            prev = opp_state.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    # Determine target bid: base on yesterday's max or median
    if yesterday_bids:
        # Use max to be safe against aggressive opponents
        base_bid = max(yesterday_bids)
    else:
        base_bid = DAILY_SALARY * 0.5

    # Adjust based on health
    if hp <= 2 or no_water_days > 0:
        # Desperate: bid enough to secure water, slightly above base
        bid = min(budget, base_bid + 5)
    elif hp <= 4:
        bid = min(budget, max(base_bid + 2, DAILY_SALARY * 0.3))
    else:
        # Healthy: save money, bid low
        bid = min(budget, DAILY_SALARY * 0.2)

    # Never bid more than budget, and ensure at least 0
    bid = max(0, bid)
    # If budget is very low, just bid what we can
    return int(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    day = day_context['day']
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Estimate how many portions (each 8 units) are available
    max_portions = int(supply // WATER_REQ)  # explicitly convert to int
    
    # Base bid to aim for a portion
    base_bid = min(my_status['budget'], DAILY_SALARY * 0.8)  # 112
    # Adjust based on number of opponents: more opponents -> higher bid
    if num_alive > 2:
        base_bid = min(my_status['budget'], DAILY_SALARY * 0.85)
    
    # Day 1: no previous trace, use base
    if day == 1:
        if my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        if max_portions <= 1:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], base_bid)
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if not yesterday_bids:
        # Fallback
        if my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], base_bid)
    
    max_prev = max(yesterday_bids)
    avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    
    # High pressure: if previous high bids, be conservative when HP good
    if max_prev >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 4:
            # Conserve budget
            target = min(my_status['budget'], DAILY_SALARY * 0.35)
        else:
            # Need water
            target = min(my_status['budget'], max(DAILY_SALARY * 0.95, max_prev + 1))
    else:
        # Medium pressure: outbid average slightly
        if my_status['hp'] <= 2:
            target = min(my_status['budget'], max(DAILY_SALARY * 0.9, avg_prev * 1.1))
        else:
            target = min(my_status['budget'], max(DAILY_SALARY * 0.5, avg_prev + 5))
    
    # Ensure we don't go below 0 or exceed budget
    target = max(0, min(my_status['budget'], target))
    return int(target)  # ensure integer bid
}
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    winners = int(supply // WATER_REQ)
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    prev_bids.sort(reverse=True)
    urgent = my_status['hp'] <= 3 or my_status['no_water_days'] >= 2
    if urgent:
        if len(prev_bids) >= winners:
            target = prev_bids[winners - 1] + 1.5
        elif
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    n_alive = len(alive_opponents)

    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])

    if hp <= 2 or no_water > 0:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.8
    else:
        urgency = 0.5

    scarcity = max(0.5, WATER_REQ / supply)
    base_bid = DAILY_SALARY * scarcity * (0.6 + 0.1 * n_alive)

    if max_prev_bid > DAILY_SALARY * 0.7:
        if urgency > 0.7:
            bid = min(budget, max_prev_bid + (DAILY_SALARY * 0.1))
        else:
            bid = min(budget, DAILY_SALARY * 0.3)
    else:
        bid = min(budget, max(base_bid, DAILY_SALARY * 0.4))

    return min(bid, budget)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Collect yesterday's opponent bids from previous_trace
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    # Determine baseline: yesterday's max bid or conservative estimate
    if prev_bids:
        baseline = max(prev_bids)
    else:
        baseline = DAILY_SALARY * 0.6  # default if no trace

    # Adjust based on my state
    if hp <= 2 or no_water_days >= 1:
        # need water urgently
        bid = min(budget, max(DAILY_SALARY * 0.85, baseline * 0.9))
    elif hp <= 4:
        # moderate need
        bid = min(budget, max(DAILY_SALARY * 0.65, baseline * 0.7))
    else:
        # healthy, try to save
        bid = min(budget, max(DAILY_SALARY * 0.4, baseline * 0.5))

    # Cap to avoid wasteful overspend, but not exceed budget
    bid = min(bid, budget)
    # Ensure minimum to possibly win if supply low
    # if supply is low, increase bid
    if supply < 18 and hp <= 5:
        bid = min(budget, max(bid, DAILY_SALARY * 0.75))
    return float(bid)
"""
