# ============================================================
# Experiment: exp_075
# Agent: Eric
# Source: exp_075
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    WATER_REQ = 8
    DAILY_SALARY = 140
    base = (WATER_REQ / supply) * DAILY_SALARY * 1.2
    if hp <= 3:
        bid = base * 1.5
    else:
        bid = base
    bid = min(bid, budget)
    bid = max(bid, 1.0)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    # Determine current day's supply
    supply = day_context['supply']
    # Base target: if we have history, use max yesterday bid as anchor
    if yesterday_bids:
        anchor = max(yesterday_bids)
    else:
        anchor = DAILY_SALARY * 0.65  # conservative guess
    # Decision based on hp
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        # Desperate: bid above anchor
        bid = min(budget, anchor * 1.15 + 2)
    elif hp <= 4:
        # Moderate need: try to win but not overspend
        bid = min(budget, anchor * 1.02 + 1)
    else:
        # Safe: conserve money, bid lower
        bid = min(budget, anchor * 0.82)
    # Ensure bid does not exceed budget
    bid = min(budget, max(bid, 0))
    # If budget is very low, just bid all
    if budget < 5:
        bid = budget
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bid based on urgency
    # If we are desperate (hp low or no water), bid high
    if hp <= 2 or no_water_days > 0:
        aggressive_bid = DAILY_SALARY * 0.85
        return min(budget, aggressive_bid)

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # To conserve budget, bid slightly below the highest yesterday
        target = max_prev * 0.9
        # Ensure we at least bid a minimum sensible amount
        min_bid = DAILY_SALARY * 0.15
        final_bid = max(min_bid, target)
        return min(budget, final_bid)

    # Default conservative bid
    return min(budget, DAILY_SALARY * 0.3)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Determine max possible winners
    max_winners = int(supply // WATER_REQ)
    
    # Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Default bid if no info
    if not yesterday_bids:
        if hp <= 2 or no_water_days > 0:
            return min(budget, DAILY_SALARY * 0.95)
        return min(budget, DAILY_SALARY * 0.5)
    
    max_prev = max(yesterday_bids)
    # Check if Cindy (high budget) had a very high bid
    cindy_prev = None
    if 'Cindy' in alive_opponents:
        prev_c = alive_opponents['Cindy'].get('previous_trace', {})
        if prev_c:
            cindy_prev = prev_c.get('bid')
    
    # Adjust based on supply and urgency
    if max_winners >= 2:
        # Multiple winners possible: target second place
        target_bid = max(DAILY_SALARY * 0.6, max_prev + 1.0)
        if cindy_prev and cindy_prev > DAILY_SALARY * 1.2:
            # Cindy dominates, don't waste budget
            target_bid = min(target_bid, DAILY_SALARY * 0.7)
        if hp <= 2 or no_water_days > 0:
            target_bid = max(target_bid, DAILY_SALARY * 0.9)
    else:
        # Only one winner: must outbid others if necessary
        target_bid = DAILY_SALARY * 0.8
        if max_prev > target_bid:
            target_bid = max_prev + 2.0
        if hp <= 2 or no_water_days > 0:
            target_bid = max(target_bid, DAILY_SALARY * 0.95)
        # If Cindy likely to bid high, avoid overspending
        if cindy_prev and cindy_prev > DAILY_SALARY * 1.1:
            target_bid = min(target_bid, DAILY_SALARY * 0.5)
    
    # Cap at budget
    bid = min(budget, target_bid)
    # Ensure non-negative and at least 1 to participate
    return max(1.0, bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Gather yesterday's bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    max_prev = max(prev_bids) if prev_bids else 0.0

    hp = my_status['hp']
    budget = my_status['budget']

    # Conservative base bid
    base_bid = DAILY_SALARY * 0.5

    # If we need water badly
    if hp <= 2:
        target = max(base_bid, max_prev * 1.05)
        return min(budget, target)
    # Moderate health
    elif hp <= 5:
        target = max(base_bid, max_prev * 1.02)
        return min(budget, target)
    # Healthy: try to undercut slightly
    else:
        target = max(base_bid, max_prev * 0.98)
        return min(budget, target)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        supply = day_context['supply']
        # Estimate how much water opponent likely got yesterday based on supply and bid
        # But we only have previous trace, so use that bid directly
        if my_status['hp'] <= WATER_REQ * 2:  # low HP, need water urgently
            target_bid = min(my_status['budget'], max(DAILY_SALARY * 0.9, highest_prev_bid + 1))
        else:
            target_bid = min(my_status['budget'], max(DAILY_SALARY * 0.65, highest_prev_bid + 0.5))
        return target_bid
    else:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    salary = 140
    budget = my_status['budget']
    hp = my_status['hp']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, salary * 0.4)
    yest_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yest_bids.append(prev['bid'])
    if yest_bids:
        avg_yest = sum(yest_bids) / len(yest_bids)
        base_bid = avg_yest + 5
    else:
        base_bid = salary * 0.95
    if hp <= 2:
        target_bid = max(base_bid, salary * 0.9)
    elif hp <= 5:
        target_bid = base_bid
    else:
        target_bid = min(base_bid, salary * 0.7)
    target_bid = min(target_bid, budget)
    target_bid = max(target_bid, 1)
    return target_bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Estimate potential competition from yesterday's traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        # If competition was high, bid lower to save budget
        if avg_yesterday > DAILY_SALARY * 0.8:
            # They are aggressive, I'll be conservative unless desperate
            if hp <= 2:
                bid = min(budget, DAILY_SALARY * 0.85)
            elif hp <= 4:
                bid = min(budget, DAILY_SALARY * 0.5)
            else:
                bid = min(budget, DAILY_SALARY * 0.3)
        else:
            # Moderate competition, bid around average
            bid = min(budget, max(DAILY_SALARY * 0.4, avg_yesterday + 1))
    else:
        # First day or no prior trace
        # Conservatively bid based on supply
        supply_int = int(supply)
        # Estimate number of winners: supply // WATER_REQ (but must cast)
        max_winners = supply_int // WATER_REQ
        num_players = 1 + len(alive_opponents)
        if max_winners >= num_players:
            # Enough water for all, bid low
            bid = min(budget, DAILY_SALARY * 0.3)
        else:
            # Water scarcity, bid more
            if hp <= 3:
                bid = min(budget, DAILY_SALARY * 0.9)
            else:
                bid = min(budget, DAILY_SALARY * 0.5)
    
    # Ensure we don't go below 0 and within budget
    bid = max(0, bid)
    bid = min(budget, bid)
    # Cast to float for safety
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)
    
    # Estimate opponent budgets from previous trace
    opp_remaining_budgets = []
    opp_previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            bid = float(prev['bid'])
            budget_after = float(prev.get('budget_after', 0))
            opp_remaining_budgets.append(budget_after)
            opp_previous_bids.append(bid)
    
    # Base bid on supply and hp
    if supply < 18:
        base_bid = DAILY_SALARY * 0.85
    elif supply < 22:
        base_bid = DAILY_SALARY * 0.65
    else:
        base_bid = DAILY_SALARY * 0.45
    
    if my_hp <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    
    if opp_remaining_budgets:
        max_rem = max(opp_remaining_budgets)
        # If opponents have low budgets, we can lower bid
        if max_rem < DAILY_SALARY * 0.5:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)
        # If they had very high bids yesterday, they might be desperate or rich
        max_prev_bid = max(opp_previous_bids)
        if max_prev_bid > DAILY_SALARY * 1.0:
            # They spent a lot; likely low budget now
            base_bid = max(base_bid, DAILY_SALARY * 0.5)
    
    bid = min(my_budget, max(base_bid, 1.0))
    # Ensure bid is within reasonable range
    return float(bid)
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

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    num_alive = len(alive_opponents)

    # Base bid: what we might need to win minimum
    # Estimate required bid to secure water
    # If supply is abundant, we can bid low
    supply_per_person = supply / (num_alive + 1) if num_alive + 1 > 0 else supply
    # If supply per person is less than our need, competition fierce
    if supply_per_person < WATER_REQ:
        pressure = 2.0
    else:
        pressure = 1.0

    # Analyze opponents' yesterday bids from previous_trace
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    # Determine our strategic bid
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
        # If someone bid very high yesterday, they might be desperate today; we can bid just below if we have HP
        if max_prev > DAILY_SALARY * 0.8 and hp > 3:
            # Avoid overbidding, but still ensure we get water if supply is low
            target = min(max_prev * 0.9, budget)
        else:
            # Slightly above average to win
            target = min(avg_prev * 1.1 + 1.0, budget)
    else:
        # No previous data, use heuristic based on supply and HP
        target = DAILY_SALARY * 0.5

    # Adjust based on HP urgency
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.7)
    else:
        target = max(target, DAILY_SALARY * 0.4)

    # Apply supply pressure multiplier
    target = target * pressure

    # Cap by budget (cannot exceed budget)
    bid = min(budget, target)
    # Ensure non-negative and at least 1 if we have budget
    if bid < 1.0 and budget >= 1.0:
        bid = 1.0
    elif bid < 0:
        bid = 0.0

    # CRITICAL: ensure no float index usage in this function (none used)
    return bid
"""
