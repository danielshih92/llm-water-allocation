# ============================================================
# Experiment: exp_005
# Agent: Eric
# Source: exp_005
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
        return max(1, min(my_status['budget'], DAILY_SALARY * 0.4))
    # Check yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    # No historical data: baseline based on HP
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    # Extract yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on supply and need
    # If supply is low and we need water, bid higher
    if supply < WATER_REQ * len(alive_opponents) + 1:
        # scarce water
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.9
        elif hp <= 4:
            target = DAILY_SALARY * 0.7
        else:
            target = DAILY_SALARY * 0.5
    else:
        # enough supply
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.6
        else:
            target = DAILY_SALARY * 0.3

    # Adjust based on yesterday's bids: if opponents bid high, they may be less aggressive today
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        max_prev = max(yesterday_bids)
        # If average is high, they might have spent a lot, so we can undercut slightly
        if avg_prev > DAILY_SALARY * 0.6:
            # They spent heavily yesterday; today they might conserve
            adjusted = avg_prev * 0.85
        else:
            # They bid low; they might be desperate today
            adjusted = max_prev + 2.0
        # Blend with our target
        target = (target + adjusted) / 2

    # Ensure we don't exceed budget and stay reasonable
    bid = min(budget, max(target, 1.0))
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)

    # Get yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev = max(yesterday_bids) if yesterday_bids else 0

    # Determine urgency
    desperate = (my_hp <= 2) or (no_water_days > 0)

    # Base bid: higher when more opponents, lower when supply high
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    base_bid = DAILY_SALARY * (0.3 + 0.3 * (1 - supply_ratio))  # 0.3-0.6

    if desperate:
        # Need water: bid high but not over 80% of budget
        target = DAILY_SALARY * 0.9
    elif num_alive >= 3:
        # Many competitors: bid more
        target = max(base_bid, highest_prev * 0.8) if highest_prev else base_bid
    elif num_alive == 2:
        # Moderate competition
        target = max(base_bid, highest_prev * 0.7)
    else:
        # Only one opponent or none
        target = base_bid

    # Ensure we don't bid more than budget
    bid = min(my_budget, target)

    # Early days: bid slightly higher to avoid early death
    if day <= 3 and my_hp <= 4:
        bid = min(my_budget, max(bid, DAILY_SALARY * 0.7))

    # If we have high HP (e.g., >7), we can save money
    if my_hp > 7:
        bid = min(bid, DAILY_SALARY * 0.4)

    # Ensure bid is non-negative
    bid = max(0, bid)

    # Avoid floating point issues for index - not needed here but keep
    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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

    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}

    # Determine highest yesterday bid among alive opponents
    highest_prev_bid = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > highest_prev_bid:
                highest_prev_bid = prev['bid']

    # Calculate water scarcity: how many units needed vs supply
    alive_count = len(alive_opponents) + 1  # including self
    total_water_needed = alive_count * WATER_REQ
    supply_ratio = supply / total_water_needed if total_water_needed > 0 else 1.0

    # Base bid from survival pressure
    if hp <= 2:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif no_water_days >= 1:
        base_bid = min(budget, DAILY_SALARY * 0.8)
    elif supply_ratio < 0.7:  # scarce water
        base_bid = min(budget, DAILY_SALARY * 0.75)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.55)

    # Adjust to beat yesterday's highest bid if needed
    if highest_prev_bid > 0:
        # If the highest yesterday was very high, we might need to compete
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Opponents are aggressive
            if hp > 4 and supply_ratio >= 0.8:
                # We can be conservative
                bid = min(budget, highest_prev_bid * 0.9)
            else:
                bid = min(budget, highest_prev_bid + 1.5)
        else:
            # Moderate competition: try to undercut by a small margin
            bid = min(budget, max(base_bid, highest_prev_bid + 1.0))
    else:
        bid = base_bid

    # Ensure bid is within budget and non-negative
    bid = max(0.0, min(budget, bid))

    # Floor to two decimals for cleanliness
    bid = round(bid, 2)
    return bid
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

    # Collect previous bids from all opponents (including dead) to gauge aggression
    prev_bids = []
    for opp in opponents_status.values():
        prev = opp.get
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
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.5
    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        base_bid = avg_yesterday
    else:
        base_bid = DAILY_SALARY * 0.4

    # Adjust for HP
    if hp <= 2:
        # Desperate: bid aggressive to ensure water
        target_bid = min(budget, max(DAILY_SALARY * 0.9, base_bid + 5))
    elif hp <= 4:
        target_bid = min(budget, max(DAILY_SALARY * 0.7, base_bid + 2))
    else:
        # Comfortable: try to save money
        target_bid = min(budget, max(DAILY_SALARY * 0.3, base_bid - 5))

    # Cap at budget, ensure non-negative
    bid = max(0, target_bid)
    return int(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    day = day_context['day']
    alive_opps = {k:v for k,v in opponents_status.items() if v['alive']}
    yesterday_bids = []
    for o in alive_opps.values():
        prev = o.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    # Base bid on supply, hp, and yesterday's pressure
    # If very low hp, bid high to survive
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 1.2)
    elif hp <= 4:
        bid = min(budget, max(DAILY_SALARY * 0.6, max_prev * 0.9))
    else:
        # If supply is high, we can bid less
        if supply >= 20:
            bid = min(budget, max(DAILY_SALARY * 0.3, max_prev * 0.7))
        else:
            bid = min(budget, max(DAILY_SALARY * 0.5, max_prev * 0.85))
    # Ensure we don't exceed budget or go below 0
    bid = max(0, min(budget, bid))
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace and trace['bid'] is not None:
                prev_bids.append(trace['bid'])
    
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        bid = min(budget, avg_prev + 5)
    else:
        bid = min(budget, SALARY * 0.5)
    
    if hp <= 2 or no_water >= 2:
        bid = max(bid, min(budget, SALARY * 0.8))
    if hp > 7:
        bid = min(bid, SALARY * 0.4)
    
    bid = max(0, min(budget, bid))
    return int(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0

    # emergency if we have no water days or low HP
    if no_water_days > 0 or hp <= 2:
        # bid high to guarantee water
        emergency_bid = min(budget, DAILY_SALARY * 1.0)
        return int(emergency_bid)

    # if we have plenty of budget, we can be more aggressive but efficient
    # conservative base: use supply to estimate needed bid
    # typical winning bids around salary * 0.7 to 0.9; max_yesterday_bid might be high
    # we want to outbid the highest yesterday if possible, but not waste
    target_bid = max_yesterday_bid + 0.5  # slightly above yesterday's max

    # if supply is abundant, we can lower bid; if scarce, raise
    supply_factor = 1.0
    if supply <= 17:
        supply_factor = 1.1
    elif supply >= 22:
        supply_factor = 0.9

    # our willingness: don't exceed 80% of salary unless needed
    max_willing = DAILY_SALARY * 0.8
    if hp <= 5:
        max_willing = DAILY_SALARY * 0.95

    # also ensure we don't go bankrupt too fast
    safe_budget = budget * 0.6  # keep some reserve for future days

    final_bid = min(target_bid * supply_factor, max_willing, safe_budget)

    # floor at 1 to avoid error
    result = max(1, int(final_bid))
    return result
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    supply_int = int(supply)
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    desperate = no_water_days >= 2 or hp <= 1
    base_bid = DAILY_SALARY * (WATER_REQ / supply_int)
    if desperate:
        base_bid *= 1.5
    
    max_prev_bid = 0
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace')
            if prev and prev.get('bid') is not None:
"""
