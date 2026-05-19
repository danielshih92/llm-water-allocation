# ============================================================
# Experiment: exp_041
# Agent: Eric
# Source: exp_041
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
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

    # Determine base need
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.85
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.6
    else:
        base_bid = DAILY_SALARY * 0.4

    # Adjust based on yesterday's opponents
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev >= DAILY_SALARY * 0.8:
            # Opponents bid high yesterday; they may be desperate
            if supply < (WATER_REQ * len(alive_opponents) + WATER_REQ):
                # Tight supply: need to compete
                base_bid = max(base_bid, min(budget, max_prev + 2))
            else:
                # Enough supply, can undercut
                base_bid = min(base_bid, DAILY_SALARY * 0.3)
        else:
            # Opponents bid low; we can save
            base_bid = min(base_bid, max_prev + 1)

    # Ensure bid is within budget and reasonable
    bid = min(budget, max(0, base_bid))
    return int(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    # Look at yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev.get('bid'), (int, float)):
            yesterday_bids.append(prev['bid'])
    # Determine current supply as integer
    supply = int(day_context['supply'])
    # Base bid: if we have opponents, use their average; else conservative
    if yesterday_bids:
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)
        base_bid = avg_opp_bid + 1.0
    else:
        base_bid = DAILY_SALARY * 0.4
    # Adjust based on health and budget
    hp = my_status['hp']
    budget = my_status['budget']
    # If health is critical, bid more aggressively (but not exceed budget)
    if hp <= 2:
        target_bid = min(budget, max(DAILY_SALARY * 0.8, base_bid + 5))
    elif hp <= 4:
        target_bid = min(budget, base_bid + 3)
    else:
        target_bid = min(budget, base_bid)
    # If supply is very low, increase bid to compete
    if supply < 16:
        target_bid = min(budget, target_bid + 5)
    # Ensure we don't bid more than salary to preserve budget
    target_bid = min(target_bid, DAILY_SALARY * 0.95)
    # Return at least 0
    return max(0, target_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    num_winners = int(supply // WATER_REQ)
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    estimated_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bid = trace['bid']
            prev_hp_after = trace.get('hp_after', opp['hp'])
            current_hp = opp['hp']
            if current_hp < prev_hp_after:
                factor = 1.2
            elif current_hp > prev_hp_after:
                factor = 0.9
            else:
                factor = 1.0
            est_bid = min(prev_bid * factor, opp['budget'])
        else:
            est_bid = 70.0
        estimated_bids.append(est_bid)
    estimated_bids.sort(reverse=True)
    if num_winners > 0 and len(estimated_bids) >= num_winners:
        threshold = estimated_bids[num_winners - 1]
    else:
        threshold = 0.0
    if my_hp <= 2:
        desired_bid = min(my_budget, DAILY_SALARY * 0.95)
    elif my_hp <= 5:
        desired_bid = min(my_budget, max(threshold + 0.5, DAILY_SALARY * 0.5))
    else:
        desired_bid = min(my_budget, max(threshold + 0.5, DAILY_SALARY * 0.3))
    return max(0.0, desired_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Estimate opponent bids from yesterday's trace
    estimates = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            estimates.append(prev['bid'])
    
    # Default aggressive bid if no estimates
    if not estimates:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.65)
    
    max_estimate = max(estimates)
    # Adjust based on HP and supply
    if hp <= 3:
        # Desperate: outbid by small margin
        target = max(max_estimate + 2, DAILY_SALARY * 0.85)
    else:
        # Healthy: conservative but ensure win
        if supply >= WATER_REQ * 3:  # plenty of water
            target = max(max_estimate + 1, DAILY_SALARY * 0.5)
        else:
            target = max(max_estimate + 1, DAILY_SALARY * 0.65)
    
    return min(budget, target)
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
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    alive_count = len(alive_opponents)

    # Base bid: percentage of salary based on urgency
    if hp <= 2:
        urgency = 0.9
    elif hp <= 5:
        urgency = 0.7
    else:
        urgency = 0.5

    # Adjust for supply tightness
    total_demand = (alive_count + 1) * WATER_REQ  # including me
    if supply >= total_demand:
        supply_factor = 0.4
    elif supply >= (alive_count + 1) * WATER_REQ * 0.5:
        supply_factor = 0.6
    else:
        supply_factor = 0.9

    # Anticipate opponents' bids using previous traces
    max_prev_bid = 0.0
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, float(prev['bid']))

    # If no previous data (day 1), use historical expectations
    if max_prev_bid == 0.0:
        # Assume Cindy bids high (~120), Alex moderate (~60), Bob low (~20)
        if 'Cindy' in alive_opponents:
            max_prev_bid = 120.0
        elif 'Alex' in alive_opponents:
            max_prev_bid = 60.0
        else:
            max_prev_bid = 20.0

    # Decision: outbid max_prev_bid by a margin if needed, else use base
    target_bid = max(
        urgency * DAILY_SALARY,
        max_prev_bid * supply_factor + 1.5
    )

    # Ensure we never spend our entire remaining budget unnecessarily
    bid = min(budget * 0.95, target_bid)
    bid = max(bid, 1.0)  # minimum bid
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
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    if prev_bids:
        highest_prev = max(prev_bids)
        target_bid = highest_prev + 1.5
    else:
        target_bid = DAILY_SALARY * 0.7

    # Adjust based on health
    if hp <= 2 or no_water_days >= 2:
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target_bid = max(target_bid, DAILY_SALARY * 0.8)

    # Cap by budget and reasonable max
    max_bid = min(budget, DAILY_SALARY * 0.95)
    final_bid = min(max_bid, target_bid)
    # Ensure non-negative
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    salary = 140
    water_req = 8

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Base bid depending on urgency and supply
    if hp <= 2:
        base = min(budget, salary * 0.95)
    elif supply <= 18:
        base = min(budget, salary * 0.85)
    elif supply >= 22:
        base = min(budget, salary * 0.25)
    else:
        base = min(budget, salary * 0.55)

    # Adjust based
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    # Alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Get yesterday's max bid among alive opponents (if available)
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        bid = trace.get('bid')
        if bid is not None and bid > yesterday_max_bid:
            yesterday_max_bid = bid

    hp = my_status['hp']
    budget = my_status['budget']

    # Determine bid
    if hp <= 2:
        # Desperate: need water at all costs
        target_bid = min(budget, DAILY_SALARY * 1.0)
    else:
        # Normal: try to slightly beat yesterday's highest bid
        if yesterday_max_bid > 0:
            target_bid = min(budget, yesterday_max_bid + 2.0)
        else:
            # No trace: bid moderate
            target_bid = min(budget, DAILY_SALARY * 0.6)

    # Ensure minimum bid (positive)
    bid = max(1.0, target_bid)
    # Ensure we don't exceed budget
    bid = min(bid, budget)
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""
