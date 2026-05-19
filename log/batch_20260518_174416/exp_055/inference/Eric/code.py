# ============================================================
# Experiment: exp_055
# Agent: Eric
# Source: exp_055
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Check yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Strategy: slightly beat the highest previous bid, but don't overspend
        bid = highest_prev_bid + 1.0
        # Cap at salary to avoid overspending
        if bid > DAILY_SALARY * 0.9:
            bid = DAILY_SALARY * 0.9
        # If low HP, go higher
        if my_status['hp'] <= 2:
            bid = max(bid, DAILY_SALARY * 0.85)
        return min(my_status['budget'], bid)
    
    # No previous data: base bid on HP and budget
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.5)
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
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace:
            bid = trace.get('bid')
            if bid is not None:
                yesterday_bids.append(bid)
    
    # Determine aggressive threshold based on water requirement and supply
    aggressive_bid = DAILY_SALARY * 0.9  # 126
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If anyone bid very high, they are likely to bid high again
        if max_prev >= aggressive_bid:
            # Need water badly or low HP? match or slightly exceed
            if hp <= 3 or no_water_days >= 1:
                target = max_prev + 2
            else:
                target = max_prev * 0.5  # be conservative, let them fight
        else:
            # Bids were moderate, we can bid slightly above to ensure water
            target = max_prev + 1.5
    else:
        # No history or no alive opponents? Bid low if safe
        if hp > 5 and no_water_days == 0:
            target = DAILY_SALARY * 0.2
        else:
            target = DAILY_SALARY * 0.5
    
    # Ensure bid doesn't exceed budget and is non-negative
    bid = max(0, min(budget, target))
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    budget = my_status['budget']
    hp = my_status['hp']
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # base strategy: if we have yesterday bids, use their average
    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        # adjust based on health
        if hp <= 2:
            # survival: bid up to 90% of salary but not more than budget
            target = min(budget, DAILY_SALARY * 0.9)
        elif hp <= 4:
            target = min(budget, max(DAILY_SALARY * 0.7, avg_bid * 0.8))
        else:
            # healthy: try to save money, bid slightly above average to win
            target = min(budget, max(DAILY_SALARY * 0.5, avg_bid * 1.1))
        return min(budget, target)
    
    # no history: default bid based on health
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        return min(budget, DAILY_SALARY * 0.7)
    else:
        return min(budget, DAILY_SALARY * 0.5)
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
    hp = my_status['hp']
    budget = my_status['budget']
    day = day_context['day']
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Analyze yesterday's bids from opponents' previous_trace
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        bid = trace.get('bid')
        if bid is not None:
            prev_bids.append(bid)
    
    # Determine target bid based on supply and HP
    if hp <= 2:
        # Desperate: must get water
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        # Moderate thirst
        bid = min(budget, DAILY_SALARY * 0.6)
    else:
        # Healthy, can afford to be conservative if supply good
        # If previous bids were very high, we might need to go high to win
        if prev_bids:
            max_prev = max(prev_bids)
            if max_prev >= DAILY_SALARY * 0.85:
                # They are aggressive, try to outbid slightly if we have budget and need water
                if hp <= 5:
                    bid = min(budget, max_prev + 1)
                else:
                    bid = min(budget, DAILY_SALARY * 0.4)
            else:
                bid = min(budget, max(DAILY_SALARY * 0.3, max_prev + 1.5))
        else:
            bid = min(budget, DAILY_SALARY * 0.35)
    
    # Ensure bid is at least 0 and not more than budget
    bid = max(0.0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure integer
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp_data in alive_opponents.items():
        prev_trace = opp_data.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(float(prev_trace['bid']))

    # Base bid calculation
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # Estimate opponent aggressiveness; Cindy and David are high
        # If they bid very high yesterday, we must match or exceed
        if highest_prev >= DAILY_SALARY * 0.85:
            # High pressure scenario: bid just above highest if needed, else conserve
            if hp <= 2 or no_water_days > 0:
                bid = min(budget, highest_prev + 0.5)
            else:
                # We can afford to lose a round; bid slightly less
                bid = min(budget, DAILY_SALARY * 0.65)
        else:
            # Moderate pressure: outbid highest by small margin
            bid = min(budget, max(DAILY_SALARY * 0.6, highest_prev + 1.0))
    else:
        # No trace info: use conservative but safe bid
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.55)

    # Adjust for low supply (high competition)
    if supply < 18:
        bid = min(budget, bid * 1.2)
    elif supply > 22:
        # Abundant supply, can lower a bit
        bid = min(budget, bid * 0.9)

    # Never bid more than budget
    bid = min(budget, max(0.0, bid))
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Identify alive opponents
    alive_opps = {k: v for k, v in opponents_status.items() if v['alive']}
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    # Determine max previous bid
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Decide bid based on own health and opponent aggression
    hp = my_status['hp']
    budget = my_status['budget']
    # If health is very low, bid aggressively to survive
    if hp <= 2:
        target_bid = min(budget, DAILY_SALARY * 0.95)
        return target_bid
    # If there is a very high previous bid (>=150), avoid direct competition
    if max_prev_bid >= DAILY_SALARY * 1.07:  # ~150
        if hp > 3:
            target_bid = min(budget, DAILY_SALARY * 0.25)  # Save money
        else:
            target_bid = min(budget, DAILY_SALARY * 0.7)   # Moderate safety
    else:
        # Generally, bid around 50-60% of salary to be competitive
        target_bid = min(budget, max(DAILY_SALARY * 0.5, DAILY_SALARY * 0.6))
    # Ensure bid does not exceed budget
    return target_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    yesterday_max = max(yesterday_bids) if yesterday_bids else 0.0
    # Determine required water units
    water_units_needed = my_status['hp'] // WATER_REQ  # this is fine as int division on int
    if my_status['hp'] % WATER_REQ == 0:
        water_units_needed = my_status['hp'] // WATER_REQ
    else:
        water_units_needed = (my_status['hp'] // WATER_REQ) + 1
    # Use a base bid
    base_bid = DAILY_SALARY * 0.5
    # Adjust based on need
    if my_status['hp'] <= 2:
        # desperate
        target_bid = max(DAILY_SALARY * 0.8, yesterday_max + 1)
    elif my_status['hp'] <= 5:
        # moderate need
        target_bid = max(base_bid, yesterday_max + 0.5)
    else:
        # healthy, can be conservative
        if yesterday_max > DAILY_SALARY * 0.85:
            target_bid = base_bid * 0.8
        else:
            target_bid = base_bid * 1.1
    # Ensure we don't exceed budget
    bid = min(my_status['budget'], target_bid)
    # Ensure non-negative
    bid = max(0, bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = {oid: o for oid, o in opponents_status.items() if o['alive']}

    # Gather yesterday's highest bid and count desperate opponents
    highest_prev_bid = 0
    low_hp_count = 0
    for opp in alive_opps.values():
        prev = opp.get('previous_trace', {})
        if prev:
            bid_prev = prev.get('bid', 0)
            if bid_prev > highest_prev_bid:
                highest_prev_bid = bid_prev
        # Current HP reflects after yesterday's trade; HP <= 2 means desperate today
        if opp['hp'] <= 2:
            low_hp_count += 1

    # Base bid: moderate starting point
    base = DAILY_SALARY * 0.5

    # Adjust for supply tightness
    if supply < 20:
        base *= 1.2
    else:
        base *= 0.9

    # Adjust for personal desperation
    if hp <= 2 or no_water_days > 0:
        base *= 1.5

    # Adjust for competition
    num_alive = len(alive_opps)
    if num_alive >= 3:
        base *= 1.15

    # Outbid yesterday's high if that seems necessary
    if highest_prev_bid > 0 and base < highest_prev_bid + 0.5:
        base = highest_prev_bid + 0.5

    # If many desperate opponents, push bid up slightly more
    if low_hp_count >= 2:
        base *= 1.2

    # Clamp to budget and non-negative
    bid = min(budget, max(0, base))
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    alive = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday bids from alive opponents
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # If no previous bids (first day or all new), use conservative baseline
    if not prev_bids:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.8)
        elif hp <= 4:
            return min(budget, DAILY_SALARY * 0.5)
        else:
            return min(budget, max(0, DAILY_SALARY * 0.2))
    
    # Determine highest previous bid
    highest_prev = max(prev_bids)
    
    # If we need water desperately, bid slightly above highest previous
    if hp <= 2:
        target = highest_prev + 1.5
        return min(budget, target)
    elif hp <= 4:
        # Moderate need: bid if highest prev is not too high
        if highest_prev > DAILY_SALARY * 0.8:
            return min(budget, DAILY_SALARY * 0.4)
        else:
            target = max(highest_prev + 1.0, DAILY_SALARY * 0.4)
            return min(budget, target)
    else:
        # High HP: conserve budget
        return min(budget, max(0, DAILY_SALARY * 0.1))
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

    units = int(supply // WATER_REQ)
    if units == 0:
        return 0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate opponent bids today: assume similar to yesterday, adjusted by budget changes
    estimated_opp_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_y = prev['bid
"""
