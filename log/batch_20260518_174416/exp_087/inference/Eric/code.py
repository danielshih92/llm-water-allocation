# ============================================================
# Experiment: exp_087
# Agent: Eric
# Source: exp_087
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Base bid: moderate
    bid_ratio = 0.5
    if hp <= 2 or no_water_days >= 2:
        bid_ratio = 0.8
    elif hp <= 4:
        bid_ratio = 0.65
    if day > int(0.7 * 10):  # last few days
        bid_ratio = min(bid_ratio + 0.15, 0.95)
    elif day > int(0.4 * 10):
        bid_ratio = min(bid_ratio + 0.1, 0.9)
    # Ensure not to exceed budget
    bid = min(budget, DAILY_SALARY * bid_ratio)
    # If supply is high, we can afford to be lower
    if supply > 25:
        bid = min(bid, DAILY_SALARY * 0.4)
    elif supply < 18:
        bid = min(budget, DAILY_SALARY * bid_ratio)  # might need to compete more
    return max(0, bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and 'bid' in prev_trace and prev_trace['bid'] is not None:
            prev_bids.append(prev_trace['bid'])
    
    # Estimate expected winning bid: slightly above average of yesterday's high bids
    if prev_bids:
        sorted_bids = sorted(prev_bids, reverse=True)
        # Number of winners possible this round
        max_winners = supply // WATER_REQ
        if max_winners >= len(alive_opponents):
            # Enough water for all, bid minimal
            bid = DAILY_SALARY * 0.2
        else:
            # Estimate cutoff: roughly the (max_winners)-th highest bid from yesterday
            if max_winners > 0:
                if max_winners <= len(sorted_bids):
                    cutoff = sorted_bids[max_winners - 1]
                else:
                    cutoff = sorted_bids[-1] if sorted_bids else 0
                # Add a small premium to ensure winning
                target = cutoff + 2.0
            else:
                target = DAILY_SALARY * 0.5
            # Adjust based on HP urgency
            if my_hp <= 2 or no_water_days >= 2:
                target = max(target, DAILY_SALARY * 0.9)
            elif my_hp <= 5:
                target = max(target, DAILY_SALARY * 0.6)
            # Cap at budget and reasonable max
            bid = min(my_budget, max(target, DAILY_SALARY * 0.3))
    else:
        # No prior info: bid conservative but ensure survival
        if my_hp <= 2:
            bid = min(my_budget, DAILY_SALARY * 0.85)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.5)
    
    # Ensure bid is within valid range
    bid = max(0.0, min(bid, my_budget))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            prev_bids.append(prev['bid'])

    # Desperate: low HP or no water days
    if hp <= 3 or no_water_days > 0:
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        if prev_bids:
            max_prev = max(prev_bids)
            # Adjust based on supply: lower supply => need to outbid more
            if supply < 18:
                target = max(DAILY_SALARY * 0.6, max_prev + 5)
            else:
                target = max(DAILY_SALARY * 0.5, max_prev + 2)
            bid = min(budget, target)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)

    # Ensure non-negative and not exceed budget
    bid = max(0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine yesterday's highest bid from opponents' traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Base bid: if healthy, moderate; if desperate, high
    if hp <= 2:
        # Desperate: bid high to secure water
        bid = min(budget, DAILY_SALARY * 0.95)
    elif no_water_days >= 1:
        # Already missed water yesterday, be aggressive
        bid = min(budget, max(DAILY_SALARY * 0.7, max_prev_bid * 0.9))
    else:
        # Healthy: try to conserve budget
        if max_prev_bid > DAILY_SALARY * 0.85:
            # Opponents aggressive yesterday, stay competitive but not full
            bid = min(budget, max(DAILY_SALARY * 0.5, max_prev_bid * 0.85))
        else:
            # Opponents moderate, we can bid a bit above their max
            bid = min(budget, max(DAILY_SALARY * 0.4, max_prev_bid + 1.0))
    
    # Ensure bid is non-negative and not more than budget
    bid = max(0, bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest yesterday bid
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # Urgency based on no_water_days and HP
    if my_hp <= 2 or no_water_days >= 2:
        # Desperate: bid high but within budget
        bid = min(my_budget, DAILY_SALARY * 0.95)
    elif my_hp <= 5:
        # Moderate need: try to beat highest yesterday bid by a small margin
        target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
        bid = min(my_budget, target)
    else:
        # Healthy: bid low, only if yesterday bids are low
        if highest_prev_bid < DAILY_SALARY * 0.6:
            # safe to outbid slightly
            bid = min(my_budget, highest_prev_bid + 1.5)
        else:
            # conserve
            bid = min(my_budget, DAILY_SALARY * 0.3)

    # Ensure at least minimal bid to avoid tie-losing
    bid = max(bid, 1.0)
    return min(bid, my_budget)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    base = DAILY_SALARY * 0.5  # conservative
    if my_status['hp'] <= 2:
        base = DAILY_SALARY * 0.9  # need water
    if supply < 18:
        base *= 1.2  # scarcity markup
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 0.8:
            base = min(base, DAILY_SALARY * 0.3)  # undercut aggressive
        else:
            base = max(base, max_prev + 1)  # outbid slightly
    if my_status['no_water_days'] > 0:
        base = max(base, DAILY_SALARY * 0.7)
    bid = min(my_status['budget'], base)
    # Ensure non-negative and integer
    bid = max(0, bid)
    return int(bid)
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
    MAX_SUPPLY = 25
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_opponents = len(alive_opponents)
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Collect previous bids from last day of previous metaround
    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])
    
    # Estimate the highest possible opponent bid today
    if previous_bids:
        max_prev = max(previous_bids)
        # Opponents may change, but likely similar or slightly higher/lower
        estimated_top = max_prev + 2.0  # small margin
    else:
        estimated_top = DAILY_SALARY * 0.8  # default guess
    
    # Base bid: try to outbid the top, but stay within budget
    base_bid = min(budget, max(estimated_top, DAILY_SALARY * 0.45))
    
    # Scarcity factor: number of agents * water_requirement vs supply
    needed_water = (num_opponents + 1) * WATER_REQ
    if supply < needed_water:
        scarcity_mult = 1.3
    else:
        scarcity_mult = 1.0
    
    # HP desperation: if very low, we must win at all costs
    if hp <= 2:
        desperation_factor = 1.6
    elif hp <= 4:
        desperation_factor = 1.3
    else:
        desperation_factor = 1.0
    
    # Final bid, capped by budget and a reasonable maximum
    final_bid = base_bid * scarcity_mult * desperation_factor
    # Ensure not too high relative to salary
    max_reasonable = DAILY_SALARY * 1.2
    final_bid = min(budget, max(DAILY_SALARY * 0.1, final_bid), max_reasonable)
    return final_bid
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
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    base_bid = 0.0
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # Aggressive opponent likely Alex: if his bid high, bid just above to win
        if highest_prev >= DAILY_SALARY * 0.8:
            # If we have good health, lowball to save money
            if hp > 4:
                base_bid = max(DAILY_SALARY * 0.4, highest_prev + 1.0)
            else:
                # Need water, bid decisively
                base_bid = min(budget, max(DAILY_SALARY * 0.7, highest_prev + 2.0))
        else:
            # Moderate pressure: bid slightly above highest
            base_bid = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
    else:
        # No history: default bid
        base_bid = DAILY_SALARY * 0.6
    
    # Adjust for health emergency
    if hp <= 2 or no_water_days >= 1:
        bid = min(budget, max(DAILY_SALARY * 0.9, base_bid))
    else:
        bid = min(budget, base_bid)
    
    # Never bid more than necessary
    bid = min(budget, bid)
    # Floor to avoid fractional issues
    return round(bid, 2)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""
