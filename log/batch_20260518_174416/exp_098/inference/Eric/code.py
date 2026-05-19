# ============================================================
# Experiment: exp_098
# Agent: Eric
# Source: exp_098
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Gather yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine our urgency
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    # Estimate how much water we can get based on supply and number of players
    num_players = len(alive_opponents) + 1
    # Base bid: value of water (salary per water need)
    value_per_unit = DAILY_SALARY / WATER_REQ  # 17.5
    # Adjust based on competition
    base_bid = value_per_unit * WATER_REQ * (WATER_REQ / supply)  # scale by supply tightness

    # Urgency factor
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        bid = min(budget, DAILY_SALARY * 0.75)
    else:
        bid = min(budget, DAILY_SALARY * 0.5)

    # If we have yesterday's bids, adjust to outbid if needed
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['no_water_days'] > 0:
            bid = min(budget, max(max_prev + 2, DAILY_SALARY * 0.7))
        else:
            # Try to be slightly below max to save money if we can afford risk
            bid = min(budget, max(base_bid, max_prev * 0.95))

    # Ensure bid is positive and within budget
    bid = max(1, bid)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Separate alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])
    
    # Determine base bid: start with lower bound
    base_bid = DAILY_SALARY * 0.4  # start conservative
    
    # If we have historical bids from yesterday, adjust
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If we are healthy, try to beat yesterday's max by small margin
        if my_status['hp'] > 4 and day_context['day'] < 7:
            target_bid = max_yesterday + 3.0
        else:
            # If low HP or late day, be more aggressive
            target_bid = max_yesterday + 6.0
        # Don't overpay beyond daily salary
        target_bid = min(target_bid, DAILY_SALARY * 0.85)
        base_bid = max(base_bid, target_bid)
    else:
        # First day or no trace: use historical behavior estimates
        # Bob average ~110, David ~90 -> expect ~100-110
        # Bid slightly below to save, but ensure survival if HP low
        if my_status['hp'] <= 3:
            base_bid = DAILY_SALARY * 0.65
        else:
            base_bid = DAILY_SALARY * 0.5
    
    # Urgency: if we have no water days or very low HP, increase bid
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    
    # Cap by remaining budget
    final_bid = min(base_bid, my_status['budget'])
    # Ensure not negative or too low
    final_bid = max(0.5, final_bid)
    return round(final_bid, 2)
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
    no_water = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.5)

    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    if prev_bids:
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
        max_prev_bid = max(prev_bids)
    else:
        avg_prev_bid = DAILY_SALARY * 0.4
        max_prev_bid = DAILY_SALARY * 0.4

    # Determine urgency
    urgent = (hp <= 2) or (no_water >= 2)
    moderate = (hp <= 4) or (no_water >= 1)

    # Base bid: if urgent, slightly above max of yesterday's high; else slightly above average
    if urgent:
        target = max_prev_bid + 2.0
        # But don't exceed budget or go too high early
        max_bid = min(budget, DAILY_SALARY * 0.9)
        bid = min(target, max_bid)
    elif moderate:
        target = avg_prev_bid + 1.0
        max_bid = min(budget, DAILY_SALARY * 0.7)
        bid = min(target, max_bid)
    else:
        # Healthy, conserve budget, bid low
        bid = min(budget, DAILY_SALARY * 0.4)

    # Adjust for supply: if supply high, can bid lower
    if supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.5)
    elif supply <= 16:
        # tight supply, may need to bid more
        if urge <= 'moderate' or urgent:
            bid = max(bid, DAILY_SALARY * 0.7)

    # Ensure non-negative and not exceed budget
    bid = max(0, min(bid, budget))
    return round(bid, 2)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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

    # Determine alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    if num_alive == 0:
        return min(budget, DAILY_SALARY * 0.4)

    # Gather yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: if supply is high, we can be more aggressive; else conserve
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    base_bid = 80 + supply_ratio * 40  # range 80-120

    # Adjust based on yesterday's competition
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If someone bid high yesterday, they might do it again
        if max_yesterday >= DAILY_SALARY * 0.85:  # aggressive (>119)
            if hp > 3:
                # We can afford to not compete, focus on saving
                return min(budget, max(60, base_bid - 20))
            else:
                # Need water urgently, match high bid
                return min(budget, max(base_bid, max_yesterday + 1))
        else:
            # Lower competition, bid slightly higher than yesterday's max
            return min(budget, max(base_bid, max_yesterday + 2))
    else:
        # No history, use base
        if hp <= 2 or no_water_days >= 2:
            return min(budget, DAILY_SALARY * 0.85)
        else:
            return min(budget, base_bid)
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
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Gather yesterday's bids from opponents who have previous_trace
    prev_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Decide baseline based on supply
    supply = day_context['supply']
    if supply < 20:
        baseline = DAILY_SALARY * 0.85
    else:
        baseline = DAILY_SALARY * 0.65

    # Adjust based on yesterday's highest bid
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev >= DAILY_SALARY * 0.8:
            # Opponents aggressive; if we have HP, undercut
            if my_status['hp'] > 4:
                baseline = min(baseline, max_prev * 0.7)
            else:
                baseline = max(baseline, max_prev * 0.9)
        else:
            baseline = max(baseline, max_prev + 5)

    # HP emergency boost
    if my_status['hp'] <= 2:
        baseline = max(baseline, DAILY_SALARY * 0.95)

    # Ensure within budget
    bid = min(my_status['budget'], baseline)
    return bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)

    # Collect yesterday's bids from opponents (if any)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Estimate highest opponent bid today based on their history
    if prev_bids:
        # Use max of yesterday's bids as a reference, but we expect Cindy to remain high
        max_prev = max(prev_bids)
        # If there was a very high bidder (Cindy), we avoid competing directly
        # We target a bid that beats the second highest? But since we don't know today's,
        # we assume they might repeat similar patterns.
        # To be safe, we bid slightly above the moderate bids but not extreme.
        # Sort to see second highest.
        sorted_bids = sorted(prev_bids, reverse=True)
        if len(sorted_bids) >= 2:
            second_highest = sorted_bids[1]
        else:
            second_highest = sorted_bids[0] * 0.8
        target = second_highest + 5.0  # beat second highest by a small margin
    else:
        # No previous data, default to moderate
        target = DAILY_SALARY * 0.7

    # Adjust based on own health
    if hp <= 2 or no_water_days >= 1:
        # Desperate: must win water
        bid = min(budget, max(target, DAILY_SALARY * 0.9))
    elif hp <= 4:
        # Low health: need water soon
        bid = min(budget, max(target, DAILY_SALARY * 0.75))
    else:
        # Healthy: can be a bit conservative, but still ensure we get water if supply is tight
        # If many alive and supply is low, raise bid
        if num_alive >= 3 and supply < 20:
            bid = min(budget, max(target, DAILY_SALARY * 0.7))
        else:
            bid = min(budget, target)

    # Ensure we don't overspend if budget is very high; cap at something reasonable
    # Also, never bid more than budget
    bid = max(0, min(bid, budget, DAILY_SALARY * 1.2))

    # Special case: if we have huge budget and it's late day, we can spend more
    if day >= 9:
        # Last days: survive at all costs
        bid = min(budget, max(bid, DAILY_SALARY * 0.85))

    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine yesterday's highest and average among alive
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0
    avg_yesterday = sum(yesterday_bids)/len(yesterday_bids) if yesterday_bids else 0
    
    # Supply awareness
    supply = day_context['supply']
    scarcity = supply / (len(alive_opponents) + 1)  # approximate per capita
    
    # HP-based urgency
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Determine base bid
    if hp <= 2:
        # Critical: need water, bid up to budget but not too high if others are weak
        if yesterday_bids and highest_yesterday < DAILY_SALARY * 0.6:
            base = DAILY_SALARY * 0.5 + 1
        else:
            base = min(budget, DAILY_SALARY * 1.2)
    elif hp <= 5:
        # Moderate need: try to outbid weak opponents
        if yesterday_bids and highest_yesterday < DAILY_SALARY * 0.7:
            base = highest_yesterday + 2 if highest_yesterday > 0 else DAILY_SALARY * 0.3
        else:
            base = DAILY_SALARY * 0.4
    else:
        # High HP: conservative, only bid if supply is very low
        if scarcity < 5:
            base = DAILY_SALARY * 0.2
        else:
            base = DAILY_SALARY * 0.1
    
    # Ensure we don't exceed budget and respect positives
    bid = max(0, min(budget, base))
    # To avoid float misuse, round to int
    bid = int(bid)
    return bid
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

    # Filter alive opponents
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine urgency and supply pressure
    days_left = 10 - day + 1
    needed_water = max(0, (hp // 2) + 1)  # rough estimate: need water to avoid death
    supply_scarcity = 1 - (supply - 15) / (25 - 15)  # 0..1, 0=abundant, 1=scarce

    # Base bid from yesterday's max
    if yesterday_bids:
        prev_max = max(yesterday_bids)
        target = prev_max + 1.5
    else:
        target = DAILY_SALARY * 0.6

    # Adjust based on urgency
    if hp <= 2 or no_water_days >= 1:
        # Desperate: bid high to ensure water
        bid = min(budget, max(target, DAILY_SALARY * 0.9))
    elif supply_scarcity > 0.7 and hp <= 4:
        # Moderate scarcity and low hp
        bid = min(budget, max(target, DAILY_SALARY * 0.75))
    else:
        # Healthy or abundant supply: save budget
        bid = min(budget, DAILY_SALARY * 0.45)

    # Avoid going below 1 bid
    if bid < 1.0 and budget > 0:
        bid = 1.0
    return min(bid, budget)
"""
