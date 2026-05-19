# ============================================================
# Experiment: exp_074
# Agent: Eric
# Source: exp_074
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
        # No competition: minimal bid to get water if needed
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Extract yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate opponent budgets today (budget after yesterday + daily salary)
    # We only have yesterday's budget_after; use it to gauge if they can bid high
    # We will base our bid on yesterday's max bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0

    # Determine our bid based on health and opponent's previous aggression
    if my_status['hp'] <= 2:
        # Need water badly, outbid highest previous if possible
        target_bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 5)
        return min(my_status['budget'], target_bid)
    else:
        # Conservative: bid half salary, but not more than needed to beat previous
        base_bid = DAILY_SALARY * 0.4
        if highest_prev_bid > base_bid:
            # Outbid slightly to win if necessary
            target_bid = highest_prev_bid + 2
        else:
            target_bid = base_bid
        return min(my_status['budget'], target_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    avg_prev = 0
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)

    # Determine base bid
    if hp <= 2:
        base = 130
    elif hp <= 5:
        base = 100
    else:
        base = 80

    # Adjust based on supply
    if supply >= 22:
        base = max(60, base - 15)
    elif supply <= 17:
        base = min(DAILY_SALARY * 0.95, base + 20)

    # Adjust based on opponents
    if avg_prev > 0:
        # If opponents are aggressive, we need to be competitive but not overpay
        if avg_prev > 140:
            if hp <= 2:
                target = min(budget, avg_prev + 10)
            else:
                target = min(budget, avg_prev - 5)
        else:
            target = min(budget, max(base, avg_prev + 2))
    else:
        target = min(budget, base)

    # Ensure non-negative, cap at budget
    return max(0, int(target))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        bid = min(my_budget, DAILY_SALARY * 0.4)
        return max(0, int(bid))
    
    # Collect previous bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Determine desperation
    desperate = my_hp <= 2 or no_water_days > 0
    
    # Base bid: if desperate, bid high to win; else, try to outbid the highest previous bid slightly
    if desperate:
        # Need water urgently, bid near salary but not exceed budget
        bid = min(my_budget, DAILY_SALARY * 0.95)
    else:
        if prev_bids:
            max_prev = max(prev_bids)
            # Slightly above the highest previous bid, but within budget and not too high
            target = min(max_prev + 1.5, DAILY_SALARY * 0.85)
            bid = max(DAILY_SALARY * 0.3, target)
            bid = min(bid, my_budget)
        else:
            # No history, bid conservatively
            bid = min(my_budget, DAILY_SALARY * 0.5)
    
    return max(0, int(bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = int(day_context['supply'])  # convert to int
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']

    # Opponent status
    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}

    # Determine baseline bid based on supply and hp urgency
    # Supply scarcity factor: low supply means higher competition
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # urgency: high when hp low or no_water_days > 0
    no_water_days = my_status['no_water_days']
    urgency = 1.0
    if hp <= 2:
        urgency = 1.5
    if no_water_days > 0:
        urgency = min(2.0, urgency + 0.3 * no_water_days)

    # Base bid from combination of factors
    base_bid = DAILY_SALARY * (0.6 - 0.2 * supply_ratio) * urgency
    # ensure within budget
    base_bid = min(budget, max(0, base_bid))

    # Adjust based on opponents' previous traces
    if alive_opponents:
        # collect previous bids
        prev_bids = []
        for opp in alive_opponents.values():
            trace = opp.get('previous_trace')
            if trace and 'bid' in trace and trace['bid'] is not None:
                prev_bids.append(trace['bid'])
        if prev_bids:
            max_prev = max(prev_bids)
            # If someone bid very high (like Cindy), we need to be competitive if we want water
            # But also consider that they might adjust; add small increment
            competitive_bid = max_prev + 2.0
            # Only go that high if we have budget and urgency is high
            if urgency > 1.2:
                final_bid = min(budget, max(base_bid, competitive_bid))
            else:
                # If urgency low, we can be conservative: just beat the second-highest or stick to base
                # As a simple heuristic, use base_bid or slightly above average
                avg_prev = sum(prev_bids) / len(prev_bids)
                final_bid = min(budget, max(base_bid, avg_prev + 1.0))
        else:
            # No trace info, fall back to base
            final_bid = base_bid
    else:
        # No opponents alive => minimal bid
        final_bid = min(budget, DAILY_SALARY * 0.4)

    # Final sanity: within budget, non-negative
    final_bid = max(0, min(budget, final_bid))
    # Round to 2 decimals to avoid float issues
    return round(final_bid, 2)
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
    my_no_water = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
    else:
        max_yesterday = 0

    # Base margin over yesterday's max
    margin = 2.0

    # Urgency based on current hp
    if my_hp <= 2 or my_no_water > 0:
        # Desperate: bid high up to 0.9 salary
        target = min(my_budget, DAILY_SALARY * 0.9)
    elif my_hp <= 4:
        # Moderate urgency
        if max_yesterday > DAILY_SALARY * 0.8:
            target = min(my_budget, max_yesterday + margin)
        else:
            target = min(my_budget, DAILY_SALARY * 0.7)
    else:
        # Healthy: conserve budget
        if max_yesterday > DAILY_SALARY * 0.8:
            target = min(my_budget, DAILY_SALARY * 0.45)
        else:
            target = min(my_budget, max_yesterday + margin, DAILY_SALARY * 0.65)

    # Ensure non-negative and at least a minimal bid (0.1 salary) if we have budget
    bid = max(0.0, target)
    if my_budget < bid:
        bid = my_budget * 0.9  # fallback if budget too low
    # Ensure we don't bid more than we have
    bid = min(bid, my_budget)
    # Keep bid reasonable but not zero unless truly broke
    if bid < 1.0 and my_budget >= 1.0:
        bid = 1.0
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

    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace and trace['bid'] is not None:
                prev_bids.append(trace['bid'])

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Determine base bid based on previous max bid
    if not prev_bids:
        base_bid = DAILY_SALARY * 0.6  # No info, moderate
    else:
        max_prev = max(prev_bids)
        # Outbid the highest yesterday, but be reasonable
        base_bid = max(max_prev + 1.0, DAILY_SALARY * 0.7)

    # Adjust based on HP and no_water_days
    if hp <= 2 or no_water_days >= 1:
        target_bid = min(budget, max(base_bid, DAILY_SALARY * 0.95))
    else:
        # Healthy: try to conserve budget
        target_bid = min(budget, min(base_bid, DAILY_SALARY * 0.85))

    # Ensure we don't overbid if we have high budget? Already capped by budget.
    # Also consider supply: if low supply, we might need higher bid.
    supply = day_context['supply']
    # If supply is very low relative to requirement, increase bid
    if supply < 20:
        target_bid = max(target_bid, DAILY_SALARY * 0.8)
    else:
        target_bid = min(target_bid, DAILY_SALARY * 0.8)

    # Final safety: keep some budget for future days
    return max(0.0, min(target_bid, budget - 5.0))  # leave at least 5
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

    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}

    # Base bid: moderate, scaled by supply tightness
    base_bid = DAILY_SALARY * 0.4
    if supply < WATER_REQ * 2:
        base_bid = DAILY_SALARY * 0.5

    # Look at yesterday's max bid from alive opponents
    yesterday_max = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max = max(yesterday_max, prev['bid'])

    # Adjust based on yesterday's pressure
    if yesterday_max >= DAILY_SALARY * 0.85:
        if hp <= 2:
            target = min(budget, DAILY_SALARY * 0.95)
        else:
            target = min(budget, base_bid * 1.2)
    else:
        # safe to bid a bit above yesterday max if needed
        target = max(base_bid, yesterday_max + 1.0)
        target = min(budget, target)

    # Ensure we are not bidding more than budget
    bid = min(budget, target)
    # Round to avoid float index? not needed for bid
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    WATER_REQ = 8
    SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    base = (WATER_REQ / supply) * SALARY * 0.8
    if my_status['no_water_days'] >= 1 or hp <= 2:
        base = SALARY * 0.9
    if hp >= 6:
        base = SALARY * 0.4
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > SALARY * 0.85:
            base = min(base, SALARY * 0.5)
        elif max_prev < SALARY * 0.5:
            base = max(base, max_prev + 2.0)
        else:
            avg_prev = sum(prev_bids) / len(prev_bids)
            base = max(base, avg_prev + 1.5)
    bid = min(budget, max(5.0, base))
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        # Solo: bid just enough to win water if needed
        if hp <= WATER_REQ:
            bid = min(budget, max(1, DAILY_SALARY * 0.2))
        else:
            bid = min(budget, DAILY_SALARY * 0.1)
        return int(bid)
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    highest_prev = max(prev_bids) if prev_bids else 0
    
    # Determine urgency based on HP and days without water
    urgency = 0
    if no_water > 0:
        urgency += no_water * 0.3  # increasing urgency per day
    if hp <= 2:
        urgency += 0.6
    elif hp <= 4:
        urgency += 0.3
    
    # Base bid: try to beat the highest previous bid if necessary
    if urgency > 0.3:
        # Need water: bid slightly above highest previous, but not exceed salary too much
        target = highest_prev + 2.0
        if target > DAILY_SALARY * 0.9:
            target = DAILY_SALARY * 0.9
        if budget < target:
            target = budget * 0.9  # use most of budget if low
        return int(min(budget, max(target, DAILY_SALARY * 0.4)))
    else:
        # Can afford to save: bid low, but not zero to avoid suspicion?
        if prev_bids and max(prev_bids) < DAILY_SALARY * 0.3:
            # Competitors are low, match lower
            return int(min(budget, max(DAILY_SALARY * 0.2, max(prev_bids) - 1)))
        else:
            return int(min(budget, DAILY_SALARY * 0.25))
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

    # Filter alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Extract yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Determine highest yesterday bid among alive opponents
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0.0

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Security: ensure budget is not too low
    if budget <= 0:
        return 0

    # Determine needed water urgency
    need_water = (no_water_days > 0) or (hp <= 2)

    if need_water:
        # Desperate: bid up to 90% of salary or highest_yesterday + 2, whichever is lower, capped by budget
        target = min(DAILY_SALARY * 0.9, highest_yesterday + 2.0)
        bid = min(budget, max(target, DAILY_SALARY * 0.3))
        return int(bid)
    else:
        # Not desperate: try to outbid highest yesterday if it's below salary threshold
        if highest_yesterday >= DAILY_SALARY * 0.8:
            # Opponents are aggressive, we may want to outbid or stay safe
            bid = min(budget, max(highest_yesterday + 1.0, DAILY_SALARY * 0.5))
            return int(bid)
        else:
            # Moderate opponents: bid slightly above their highest to secure water at low cost
            bid = min(budget, max(highest_yesterday + 1.0, DAILY_SALARY * 0.45))
            return int(bid)
"""
