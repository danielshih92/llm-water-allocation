# ============================================================
# Experiment: exp_029
# Agent: Eric
# Source: exp_029
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    if my_status['hp'] <= 2:
        bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    else:
        bid = min(my_status['budget'], DAILY_SALARY * 0.5)
    return max(bid, 1)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])
    max_prev_bid = max(previous_bids) if previous_bids else 0
    critical = hp <= 2 or no_water_days >= 2
    if critical:
        bid = min(budget, DAILY_SALARY * 1.2)
    else:
        if max_prev_bid > 0:
            bid = min(budget, max_prev_bid + 1.5)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
    # Ensure we don't bid more than we have
    bid = min(bid, budget)
    # If no opponents alive, just bid minimal
    if not alive_opponents:
        bid = min(budget, DAILY_SALARY * 0.3)
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    # Get previous bids from opponents
    prev_bids = []
    for opp in opponents_status.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    # Determine base bid
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.65
    else:
        base_bid = DAILY_SALARY * 0.4
    # Adjust based on competition
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev >= DAILY_SALARY * 0.85:
            if hp > 3:
                base_bid = min(base_bid, DAILY_SALARY * 0.5)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.85)
        elif max_prev >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, max_prev + 5)
        # Also consider number of alive opponents and available water
    alive_count = sum(1 for o in opponents_status.values() if o['alive'])
    max_water_units = supply // WATER_REQ
    # If competition is high and water scarce, bid higher
    if alive_count >= max_water_units and hp >= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    # Ensure not to exceed budget
    return min(budget, base_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = int(day_context['supply'])  # supply is current day supply
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Compute average opponent bid from previous_trace if available
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev = 0.4 * DAILY_SALARY  # fallback
    
    # Decision based on HP
    if hp <= 2:
        # Need water urgently; bid high to outbid average
        target = max(DAILY_SALARY * 0.8, avg_prev + 1)
    elif hp <= 5:
        # Moderate need; bid enough to compete
        target = max(DAILY_SALARY * 0.5, avg_prev)
    else:
        # High HP; conserve budget, bid low
        target = min(DAILY_SALARY * 0.3, avg_prev - 10)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    # Compute average previous bid of alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
    else:
        avg_prev = 75.0
        max_prev = 75.0
    # Base bid: need to win water
    scarcity_factor = supply / (MAX_SUPPLY)
    # Urgency based on hp and no_water_days
    if hp <= 2 or my_status['no_water_days'] >= 1:
        urgency = 0.9
    elif hp <= 5:
        urgency = 0.7
    else:
        urgency = 0.45
    # Consider opponent pressure
    if max_prev > DAILY_SALARY * 0.6:
        urgency = max(urgency, 0.65)
    bid = min(budget, DAILY_SALARY * urgency)
    # Ensure at least something to compete
    if bid < 0.5 * avg_prev:
        bid = min(budget, avg_prev * 0.8)
    # Very early days: be aggressive to secure water
    if day <= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.55))
    # Final days: conserve if hp high
    if day >= 9 and hp > 5:
        bid = min(budget, DAILY_SALARY * 0.3)
    return int(bid)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Analyze opponents' previous trace
    high_bid = 0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                if prev['bid'] > high_bid:
                    high_bid = prev['bid']

    # Base bid: ensure at least enough to get water if supply is tight
    # If we have no water days, we must win
    if hp <= 0 or no_water_days > 0:
        # Desperate: bid high, but not more than budget
        bid = min(budget, DAILY_SALARY * 0.8)
    elif hp < 3:
        # Low HP: bid moderately high to secure water
        bid = min(budget, DAILY_SALARY * 0.55)
    else:
        # Healthy: bid low to conserve budget
        bid = min(budget, DAILY_SALARY * 0.3)

    # Adjust based on yesterday's high bid
    if high_bid > 0:
        # If yesterday's max opponent bid was very high (>90% salary), they may be weak today
        # But to be safe, we undercut slightly if we are healthy
        if high_bid > DAILY_SALARY * 0.85 and hp > 3:
            bid = min(bid, DAILY_SALARY * 0.25)
        elif high_bid > DAILY_SALARY * 0.6:
            # Conservative undercut to avoid bidding war
            bid = min(bid, high_bid * 0.7)
        else:
            # If they are low, we can still be safe with our base
            pass

    # Ensure bid does not exceed budget
    bid = min(bid, budget)
    # Ensure bid does not go below 1 (minimum bid? assume 0 means no bid, but better to bid positive)
    bid = max(1, bid)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opp = {k: v for k, v in opponents_status.items() if v['alive']}
    prev_bids = []
    for opp in alive_opp.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Emergency: need water badly
    if no_water > 0 or my_hp <= 2:
        bid = min(my_budget, DAILY_SALARY * 0.9)
        return bid

    if not prev_bids:
        # No history: bid moderate
        bid = min(my_budget, DAILY_SALARY * 0.6)
        return bid

    avg_prev = sum(prev_bids) / len(prev_bids)
    max_prev = max(prev_bids)

    # Target: slightly above average but conservative relative to max
    target = max(avg_prev + 2, DAILY_SALARY * 0.5)
    # Avoid overspending when max is high
    if max_prev > DAILY_SALARY * 0.85 and my_hp > 3:
        target = min(target, DAILY_SALARY * 0.6)
    bid = min(my_budget, target)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    day = int(day_context['day'])
    supply = float(day_context['supply'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])

    # Compute maximum previous bid among alive opponents
    max_prev_bid = 0.0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                bid_val = float(prev['bid'])
                if bid_val > max_prev_bid:
                    max_prev_bid = bid_val

    # Base bid: ensure we can cover water cost based on supply ratio
    # If supply is low, we need to bid higher share
    share_ratio = WATER_REQ / supply  # e.g., 8/20 = 0.4
    base_bid = share_ratio * DAILY_SALARY  # proportion of salary

    # Decide bid increment based on hp and previous max
    if hp <= 3:
        # Desperate: outbid previous max or base
        target = max(base_bid * 1.2, max_prev_bid + 5.0, DAILY_SALARY * 0.9)
    else:
        # Comfortable: bid modestly above base
        target = max(base_bid * 0.8, max_prev_bid + 2.0, DAILY_SALARY * 0.4)

    # Ensure we do not exceed budget
    bid = min(budget, target)

    # Avoid negative bid
    bid = max(bid, 0.0)

    # Cast all list/array indices to int if any (none used directly here)
    # But safe guard: ensure bid is float
    return float(bid)
"""
