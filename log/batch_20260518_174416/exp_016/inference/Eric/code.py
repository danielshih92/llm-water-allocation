# ============================================================
# Experiment: exp_016
# Agent: Eric
# Source: exp_016
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    desperate = hp <= 3 or no_water_days >= 1

    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if desperate:
            target = highest_prev + 1.5
        else:
            avg_prev = sum(yesterday_bids) / len(yesterday_bids)
            target = avg_prev + 0.5
    else:
        if supply <= 18:
            target = DAILY_SALARY * 0.7
        else:
            target = DAILY_SALARY * 0.4

    bid = min(budget, max(0, target))
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    if prev_bids:
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev_bid = 0.0
    
    # Base bid: slightly above average yesterday to secure water
    base_bid = avg_prev_bid + 2.0
    
    # If hp is low, increase bid
    if hp <= 2 or no_water_days >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    
    # Adjust for supply: if supply is tight, bid higher
    supply_per_agent = supply / (len(alive_opponents) + 1)
    if supply_per_agent < WATER_REQ * 0.5:
        base_bid = base_bid * 1.2
    
    # Ensure we don't exceed budget and cap at daily salary
    bid = min(budget, max(base_bid, 0.0))
    bid = min(bid, DAILY_SALARY * 0.95)
    
    return int(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Look at yesterday's highest bid from alive opponents (ignore dead)
    max_yesterday_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_yesterday_bid = max(max_yesterday_bid, prev['bid'])
    
    # Determine current supply (lower supply means more competition)
    supply = day_context['supply']
    # Number of players = myself + alive opponents
    total_players = 1 + len(alive_opponents)
    # Rough estimate of needed water per player
    water_per_player = supply / total_players if total_players > 0 else supply
    
    # Base bid: fraction of salary, adjusted by scarcity
    if water_per_player < WATER_REQ:
        # Scarcity: need to bid higher
        base_bid = 0.7 * DAILY_SALARY
    else:
        base_bid = 0.5 * DAILY_SALARY
    
    # Adjust based on yesterday's max bid
    if max_yesterday_bid > 100:
        # Aggressive opponent: we must compete
        target_bid = max(0.8 * DAILY_SALARY, max_yesterday_bid + 2)
    else:
        target_bid = base_bid
    
    # Consider our own hp
    if my_status['hp'] <= 2:
        target_bid = max(target_bid, 0.9 * DAILY_SALARY)
    
    # Never bid more than budget
    bid = min(my_status['budget'], target_bid)
    
    # Ensure we don't bid negative
    bid = max(bid, 0)
    
    # Convert to float if needed and return
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_count = sum(1 for o in opponents_status.values() if o['alive'])
    
    # base fraction of salary
    if supply < 18:
        base_frac = 0.7
    elif supply < 20:
        base_frac = 0.6
    else:
        base_frac = 0.5
    
    # adjust for HP
    if hp <= 2 or no_water_days >= 1:
        base_frac = min(0.9, base_frac + 0.2)
    elif hp <= 4:
        base_frac = min(0.8, base_frac + 0.1)
    
    # adjust for number of competitors
    if alive_count >= 3:
        base_frac += 0.1
    
    bid = DAILY_SALARY * base_frac
    
    # ensure bid is within budget
    if bid > budget:
        bid = budget
    # ensure at least 1 to avoid zero bid
    if bid < 1:
        bid = 1
    return bid
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
    
    # Determine alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid strategy: typical bid proportional to salary and reliance
    # If many alive, competition is higher
    num_alive = len(alive_opps)
    
    # Estimate required water probability: need 8 units, supply varies
    # Simple ratio: bid based on scarcity
    scarcity = (MAX_SUPPLY + MIN_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 1 when supply=15, 0 when supply=25
    
    # HP-dependent urgency
    urgency = 1.0 - (hp / 10.0)  # 0 if full HP, 1 if 0 HP
    
    # Base bid in percentage of salary
    base_pct = 0.5 + 0.4 * urgency + 0.2 * scarcity - 0.1 * num_alive
    base_pct = max(0.2, min(1.0, base_pct))
    bid = int(DAILY_SALARY * base_pct)
    
    # Look at yesterday's highest bid for aggressive opponents
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone bid very high, consider outbidding or conceding
        if highest_prev >= DAILY_SALARY * 0.85:
            if hp <= 3:
                # Need water badly, outbid by small margin
                bid = int(highest_prev + 1)
            else:
                # Conserve, bid low
                bid = int(DAILY_SALARY * 0.35)
        else:
            # Otherwise, stay slightly above average of previous high if necessary
            avg_prev = sum(yesterday_bids) / len(yesterday_bids)
            if hp <= 4:
                bid = int(max(bid, avg_prev + 2))
            else:
                bid = int(min(bid, avg_prev - 1))
    
    # Ensure we don't exceed budget
    bid = min(bid, int(budget))
    # Ensure bid is at least 1 (or 0 allowed? game says can be 0, but safety)
    bid = max(1, bid)
    return float(bid)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    # Gather yesterday bids from traces
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    # Emergency threshold: if no water days >= 2 or hp <= 2, must win
    must_win = (no_water_days >= 2 or hp <= 2)
    if must_win:
        # Bid high but within budget
        bid = min(budget, DAILY_SALARY * 1.2)
        return int(bid) if isinstance(bid, float) else bid
    # Standard strategy: undercut highest previous bid if safe
    if prev_bids:
        highest_prev = max(prev_bids)
        # If we are healthy, we can undercut
        if hp > 5:
            target = highest_prev * 1.0  # match exactly? or undercut by tiny margin
            # To save money, undercut by 1% but ensure positive
            bid = max(highest_prev * 0.99, DAILY_SALARY * 0.4)
            # But if budget is very low, no choice
            bid = min(bid, budget)
        else:
            # Moderate HP: bid slightly above average to increase win chance
            avg_prev = sum(prev_bids) / len(prev_bids)
            bid = max(avg_prev * 1.1, DAILY_SALARY * 0.6)
            bid = min(bid, budget)
    else:
        # No previous data: bid conservative
        bid = DAILY_SALARY * 0.4
    # Ensure bid is within budget and at least 0
    bid = max(0, min(budget, bid))
    # Convert to int to avoid float issues
    if isinstance(bid, float):
        bid = int(bid)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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

    # Determine base bid based on desperation
    if hp <= 2 or no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.4

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    # If there were bids, adjust to counter
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If I'm desperate, outbid the highest previous by a small margin
        if hp <= 2 or no_water_days >= 2:
            target = max_prev_bid + 1.5
        else:
            # Otherwise, stay close but lower to save money
            target = max_prev_bid * 0.8
        # Blend with base bid
        base_bid = max(base_bid, target)

    # Ensure within budget
    bid = min(budget, base_bid)

    # Floor bid to 0
    bid = max(0, bid)

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Estimate average opponent bid from historical data (if available)
    # Use average from last metaround as initial guess
    avg_opp_bid = 85.0  # default rough estimate
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if alive_opponents:
        # Check if any opponent has previous_trace (only for day>1)
        # For day 1, no traces, so fallback
        pass
    
    # Base bid on HP and supply
    if hp <= 2:
        # Critical need: bid high to secure water
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        # Moderate need
        if supply < 20:
            base_bid = DAILY_SALARY * 0.7
        else:
            base_bid = DAILY_SALARY * 0.5
    else:
        # Healthy: bid low to save money
        if supply < 18:
            base_bid = DAILY_SALARY * 0.4
        elif supply < 22:
            base_bid = DAILY_SALARY * 0.3
        else:
            base_bid = DAILY_SALARY * 0.25
    
    # Ensure bid doesn't exceed budget and is not negative
    bid = max(0, min(budget, base_bid))
    return float(bid)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Check yesterday's bids from opponents (previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base bid based on my health
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone bid very high yesterday, they might be desperate today
        if highest_prev >= DAILY_SALARY * 0.85:
            # They likely have low budget now, so we can lower our bid
            base_bid = min(base_bid, DAILY_SALARY * 0.5)
        else:
            # Bid just above yesterday's highest to secure water
            base_bid = max(base_bid, highest_prev + 1.0)
    
    # Ensure bid is within budget and not too high
    bid = min(my_status['budget'], base_bid)
    bid = max(bid, 1.0)  # always bid at least 1
    return bid
"""
