# ============================================================
# Experiment: exp_101
# Agent: Eric
# Source: exp_101
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    # Determine base bid fraction
    if hp <= 2:
        bid_frac = 0.9
    elif hp <= 4:
        bid_frac = 0.6
    elif hp <= 6:
        bid_frac = 0.4
    else:
        bid_frac = 0.2
    # Increase aggression as days progress (last 3 days)
    if day >= 8:
        bid_frac = min(1.0, bid_frac + 0.2)
    elif day >= 5:
        bid_frac = min(1.0, bid_frac + 0.1)
    # Cap bid at budget and at salary
    bid = min(budget, DAILY_SALARY * bid_frac)
    # Ensure bid is positive
    bid = max(0.1, bid)
    return round(bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for o in alive:
        pt = o.get('previous_trace', {})
        if pt and 'bid' in pt and pt['bid'] is not None:
            prev_bids.append(pt['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0
    if hp <= 2:
        base = min(budget, SALARY * 0.9)
    else:
        base = min(budget, SALARY * 0.7)
    if supply >= 20:
        bid = min(base, 65)
    else:
        if max_prev_bid > 0:
            bid = min(base, max_prev_bid + 5)
        else:
            bid = min(base, 80)
    return max(0, min(budget, bid))
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    opponents_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opponents_bids.append(prev['bid'])
    
    if not opponents_bids:
        # No trace, use default conservative
        return min(budget, DAILY_SALARY * 0.5)
    
    # Estimate today's opponent bids as last bid with slight increase for aggressive ones
    max_est = max(opponents_bids)
    avg_est = sum(opponents_bids) / len(opponents_bids)
    
    # If max is very high (like Cindy), assume she'll bid high again
    if max_est >= DAILY_SALARY * 0.8:
        # Avoid bidding war: aim for second highest bid + small increment
        sorted_bids = sorted(opponents_bids)
        if len(sorted_bids) >= 2:
            target = sorted_bids[-2] + 1.0
        else:
            target = avg_est + 2.0
        # Cap based on need
        if hp > 3:
            bid = min(budget, min(target, DAILY_SALARY * 0.6))
        else:
            bid = min(budget, max(target, DAILY_SALARY * 0.8))
    else:
        # Moderate opponents: bid slightly above max to win
        target = max_est + 2.0
        if hp <= 3:
            bid = min(budget, max(target, DAILY_SALARY * 0.7))
        else:
            bid = min(budget, min(target, DAILY_SALARY * 0.5))
    
    # Ensure bid does not exceed budget and is non-negative
    bid = max(0.0, min(budget, bid))
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Default bid if no history
    if not yesterday_bids:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        return min(budget, DAILY_SALARY * 0.55)
    
    avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
    
    # Aggressive if low HP
    if hp <= 2:
        target = max(avg_yesterday + 2, DAILY_SALARY * 0.7)
        return min(budget, target)
    # Normal: beat average by a small margin
    target = avg_yesterday + 1.5
    # Don't waste budget; cap at 80% of salary if not desperate
    if hp > 5:
        target = min(target, DAILY_SALARY * 0.6)
    else:
        target = min(target, DAILY_SALARY * 0.8)
    return min(budget, target)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    
    # Extract previous day's bids from alive opponents
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine bid based on previous maximum
    if prev_bids:
        max_prev = max(prev_bids)
        # If my HP is low, bid aggressively to secure water
        if my_status['hp'] <= 2:
            target = min(my_status['budget'], max(DAILY_SALARY * 0.85, max_prev + 1))
        elif my_status['hp'] <= 4:
            target = min(my_status['budget'], max(DAILY_SALARY * 0.6, max_prev + 0.5))
        else:
            # Higher HP: bid just enough to beat previous max, but not too high
            target = min(my_status['budget'], max(DAILY_SALARY * 0.4, max_prev + 0.1))
    else:
        # No history: use safe heuristic
        if my_status['hp'] <= 3:
            target = min(my_status['budget'], DAILY_SALARY * 0.7)
        else:
            target = min(my_status['budget'], DAILY_SALARY * 0.45)
    
    # Ensure non-negative and within budget
    target = max(target, 0.0)
    return target
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Convert supply to int for safe indexing
    supply = int(day_context['supply'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # Find highest previous bid among alive opponents
    highest_prev_bid = 0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev:
                highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # Urgency based on my HP
    if my_hp <= 2:
        # Critical: need water at almost any cost
        target = min(my_budget, DAILY_SALARY * 0.95)
    elif my_hp <= 4:
        # Moderate need
        target = min(my_budget, DAILY_SALARY * 0.7)
    else:
        # Comfortable, conserve budget
        target = min(my_budget, DAILY_SALARY * 0.4)

    # Counter threat from high previous bid (likely Cindy)
    if highest_prev_bid > 200:
        # Opponent bid very high yesterday; they might be conserving today or still aggressive
        # If they were aggressive and survived, they may have reduced budget; raise bid if I'm needy
        if my_hp <= 4:
            target = max(target, highest_prev_bid * 0.9)
        else:
            target = min(target, DAILY_SALARY * 0.5)

    # Ensure bid does not exceed budget
    bid = min(my_budget, int(target))
    return max(1, bid)  # always bid at least 1
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Max affordable bid
    max_bid = min(budget, DAILY_SALARY)

    # Base bid proportional to need and supply scarcity
    # supply range 15-25
    supply_ratio = (supply - 15) / 10.0  # 0 to 1, higher supply = less scarcity
    # Need to win at least 1 unit per day, but want 8 for full health
    base_bid = DAILY_SALARY * (0.3 + 0.4 * (1 - supply_ratio))  # 0.3 to 0.7 of salary

    # Adjust for HP: if low, bid more
    if hp < 3:
        base_bid *= 1.5
    # If no water for 2+ days, critical
    if no_water_days >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Check opponent trace for yesterday's high bid
    high_prev = 0
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and isinstance(prev.get('bid'), (int, float)):
                if prev['bid'] > high_prev:
                    high_prev = prev['bid']

    # If yesterday someone bid very high (>85% salary), they might be aggressive today
    if high_prev > DAILY_SALARY * 0.85:
        # If we have HP to spare, undercut to save money
        if hp > 5:
            bid = min(max_bid, DAILY_SALARY * 0.4)
        else:
            # Need to compete
            bid = min(max_bid, high_prev * 1.02 + 0.5)
    else:
        # Normal: bid base but not exceed moderate threshold
        bid = min(max_bid, base_bid)

    # Ensure bid is at least 0.5
    bid = max(0.5, bid)
    # Cap at budget
    bid = min(bid, budget)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0

    # Base bid: 50% salary adjusted by supply scarcity
    base_bid = DAILY_SALARY * 0.5
    if supply < 18:
        base_bid *= 1.3
    elif supply > 22:
        base_bid *= 0.8

    # Adjust based on yesterday's max bid (exploit aggressiveness)
    if max_yesterday_bid > DAILY_SALARY * 0.8:
        # Opponents are aggressive, let them spend; bid low to conserve
        target_bid = base_bid * 0.5
    elif max_yesterday_bid > DAILY_SALARY * 0.6:
        target_bid = base_bid * 0.8
    else:
        # Opponents are moderate, bid just above average to secure water
        target_bid = max(base_bid, avg_yesterday_bid + 1)

    # Urgency adjustments
    if hp <= 2 or no_water_days > 1:
        target_bid = max(target_bid, DAILY_SALARY * 0.85)

    # Final clamp
    return min(budget, target_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    budget = my_status['budget']
    hp = my_status['hp']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Extract yesterday's bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    # Determine target bid
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If we need water urgently
        if hp <= 2:
            target_bid = min(budget, max(DAILY_SALARY * 0.9, max_prev_bid + 1.0))
        else:
            # If previous max bid is very high, we may need to match or exceed
            if max_prev_bid >= DAILY_SALARY * 0.8:
                if hp > 4:
                    # We can afford to be slightly lower
                    target_bid = min(budget, max(DAILY_SALARY * 0.5, max_prev_bid - 5.0))
                else:
                    # Need water, bid above
                    target_bid = min(budget, max_prev_bid + 1.0)
            else:
                # Moderate competition
                target_bid = min(budget, max(DAILY_SALARY * 0.5, max_prev_bid + 1.5))
    else:
        # First day or no previous data: base on HP
        if hp <= 2:
            target_bid = min(budget, DAILY_SALARY * 0.85)
        else:
            target_bid = min(budget, DAILY_SALARY * 0.6)
    
    # Ensure bid is non-negative and within budget
    bid = max(0.0, min(budget, target_bid))
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # only me, bid low to save budget
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    # get highest yesterday bid among alive opponents
    highest_yesterday = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > highest_yesterday:
                highest_yesterday = prev['bid']
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    # if desperate: low hp or >1 day no water
    if hp <= 2 or no_water >= 2:
        return min(budget, DAILY_SALARY * 0.9)
    # if enough hp, bid slightly above highest yesterday, but not too high
    bid = highest_yesterday + 1.5
    # cap bid to avoid overpaying when healthy
    bid = min(bid, DAILY_SALARY * 0.7)
    # ensure within budget
    bid = min(bid, budget)
    # also bid at least a small amount if budget allows
    return max(bid, 1.0)
"""
