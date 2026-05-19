# ============================================================
# Experiment: exp_119
# Agent: Eric
# Source: exp_119
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    max_prev_bid = 0
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    if hp <= 2 or no_water_days >= 2:
        # desperate: bid high but within budget
        return min(budget, DAILY_SALARY * 0.95)
    if max_prev_bid > 0 and max_prev_bid < DAILY_SALARY * 0.7:
        # exploit by bidding slightly higher
        return min(budget, max_prev_bid + 5)
    # default: moderate bid
    return min(budget, DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents)

    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Determine aggression level based on yesterday's max bid
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Base bid: roughly proportion of salary, adjusted for competition
    # Supply per alive player: supply / (num_alive + 1)
    share = supply / (num_alive + 1)
    need_factor = WATER_REQ / share if share > 0 else 1.0
    base_bid = DAILY_SALARY * 0.5 * min(need_factor, 2.0)

    # If yesterday was very competitive, increase bid
    if max_yesterday_bid > DAILY_SALARY * 0.8:
        bid = max(base_bid, max_yesterday_bid + 1.0)
    else:
        bid = base_bid

    # Adjust for HP desperation
    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.7)

    # Ensure we don't overpay, but also stay alive
    bid = min(bid, budget, DAILY_SALARY * 0.95)
    bid = max(bid, 0.0)
    # Ensure bid is not zero if we need water desperately but budget is low
    if hp <= 2 and budget > 0:
        bid = max(bid, DAILY_SALARY * 0.15)

    return int(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    # Find desperate opponents (low HP)
    desperate = [o for o in opponents_status.values() if o['alive'] and o['hp'] <= 2]
    high_prev_bidders = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid', 0) is not None:
            if prev['bid'] >= DAILY_SALARY * 0.85:
                high_prev_bidders.append(prev['bid'])
    
    # Determine base bid
    base_bid = DAILY_SALARY * 0.5
    
    # Adjust for desperation
    if desperate:
        # Desperate opponents will bid high, so we need to bid higher to outbid if we need water
        if my_hp <= 2:
            base_bid = min(my_budget, DAILY_SALARY * 0.95)
        else:
            # If we are healthy, let them fight, bid low
            base_bid = DAILY_SALARY * 0.3
    elif high_prev_bidders:
        max_prev = max(high_prev_bidders)
        # Opponents likely to continue high, mimic if necessary
        if my_hp <= 2:
            base_bid = min(my_budget, max(DAILY_SALARY * 0.7, max_prev + 1))
        else:
            base_bid = min(my_budget, max(DAILY_SALARY * 0.4, max_prev - 5))
    else:
        # No extreme signals, base on hp
        if my_hp <= 2:
            base_bid = min(my_budget, DAILY_SALARY * 0.9)
        elif my_hp <= 5:
            base_bid = min(my_budget, DAILY_SALARY * 0.65)
        else:
            base_bid = min(my_budget, DAILY_SALARY * 0.4)
    
    # Ensure bid is not negative
    bid = max(0, base_bid)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        target = avg_prev + 2.0
    else:
        target = DAILY_SALARY * 0.6
    if my_status['hp'] <= 3:
        bid = min(my_status['budget'], max(target, DAILY_SALARY * 0.8))
    else:
        bid = min(my_status['budget'], max(target, DAILY_SALARY * 0.4))
    # supply constraint
    supply = int(day_context['supply'])
    if supply < 18:
        bid = min(bid, DAILY_SALARY * 0.75)
    return int(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opps = {aid: o for aid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opps)
    
    yesterday_max_bid = 0.0
    for opp in alive_opps.values():
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])
    
    if hp <= 2:
        base_pct = 0.9
    elif hp <= 4:
        base_pct = 0.7
    else:
        base_pct = 0.5
    
    supply_factor = 1.0 - (supply - 15) / (25 - 15)
    supply_bonus = 0.3 * supply_factor
    total_pct = min(1.0, base_pct + supply_bonus)
    
    if
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

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if not yesterday_bids:
        # no trace data, use default based on HP
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        elif my_status['hp'] <= 5:
            return min(my_status['budget'], DAILY_SALARY * 0.7)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.45)

    # Use median of yesterday's bids as baseline
    sorted_bids = sorted(yesterday_bids)
    mid = len(sorted_bids) // 2
    # integer index is safe because len is int
    if len(sorted_bids) % 2 == 1:
        median_bid = sorted_bids[mid]
    else:
        median_bid = (sorted_bids[mid-1] + sorted_bids[mid]) / 2.0

    max_yesterday = max(yesterday_bids)
    # Consider supply effect: if today's supply is low, aggression may increase
    supply = day_context['supply']
    supply_factor = 1.0
    if supply < 20:
        supply_factor = 1.3
    elif supply > 22:
        supply_factor = 0.85

    if my_status['hp'] <= 2:
        # desperate: bid up to 1.1 times max yesterday or salary
        target = max(DAILY_SALARY * 0.9, max_yesterday * 1.1)
    elif my_status['hp'] <= 5:
        # moderate need: try to beat median with a small premium
        target = min(median_bid * 1.15, DAILY_SALARY * 0.85)
    else:
        # healthy: conserve budget, undercut median
        target = min(median_bid * 0.85, DAILY_SALARY * 0.5)

    target = target * supply_factor
    # ensure we don't bid more than budget
    bid = min(my_status['budget'], target)
    # never bid negative
    bid = max(bid, 0.0)
    return bid
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
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # scale based on supply scarcity
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 (scarce) to 1 (abundant)
        if hp <= 2:
            # desperate, outbid highest by small margin
            target = max(DAILY_SALARY * 0.9, highest_prev + 2.0)
        elif hp <= 4:
            target = max(DAILY_SALARY * 0.7, highest_prev + 1.0)
        else:
            # healthy, bid around median or slightly above
            median_prev = sorted(yesterday_bids)[len(yesterday_bids)//2] if len(yesterday_bids)>1 else highest_prev
            target = max(DAILY_SALARY * 0.5, median_prev * (0.9 + 0.2 * (1 - supply_factor)))
        return min(budget, target)
    # no trace available, fallback
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        return min(budget, DAILY_SALARY * 0.7)
    else:
        return min(budget, DAILY_SALARY * 0.5)
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

    supply = int(day_context['supply'])  # Ensure integer
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid as percentage of salary based on supply scarcity
    scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid = DAILY_SALARY * (0.3 + 0.4 * scarcity)

    # Increase if we are thirsty
    if no_water_days > 0:
        base_bid += DAILY_SALARY * 0.2
    if hp <= 2:
        base_bid += DAILY_SALARY * 0.2

    # Look at yesterday's opponent bids to adjust
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    highest_yesterday = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = float(prev['bid'])
            if bid_val > highest_yesterday:
                highest_yesterday = bid_val

    # If someone bid high yesterday, consider matching or slightly beating
    if highest_yesterday > 0:
        target = max(base_bid, highest_yesterday + 0.5)
    else:
        target = base_bid

    # Cap by budget
    final_bid = min(target, budget)
    # Ensure at least 1 if possible
    if final_bid < 1 and budget >= 1:
        final_bid = 1
    return final_bid
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
    no_water_days = my_status['no_water_days']
    # Gather previous bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and 'bid' in trace:
                bid = trace['bid']
                if bid is not None:
                    prev_bids.append(bid)
    # Base bid: daily salary portion based on supply scarcity
    scarcity = 1 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid = DAILY_SALARY * (0.3 + 0.5 * scarcity)
    # Adjust based on opponents' previous bids
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        # If they bid high, they might lower; but we outbid conservatively
        target = max(base_bid, avg_prev * 0.9 + 2)
    else:
        target = base_bid
    # HP urgency
    if hp <= 2 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.85)
    # Budget cap
    bid = min(budget, target)
    # Ensure non-negative
    bid = max(bid, 0)
    # Apply integer conversion if needed (but bid can be float; game accepts)
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
    
    # Determine opponents' previous behavior from traces
    high_prev_bid = 0
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                if prev['bid'] > high_prev_bid:
                    high_prev_bid = prev['bid']
    
    # Base bid: very low to avoid wasting budget
    base_bid = 0.1
    
    # If opponents were very aggressive yesterday, stay low
    if high_prev_bid > 0.7 * DAILY_SALARY:
        bid = base_bid
    else:
        # Slightly more aggressive if opponents were moderate
        bid = min(budget, 0.4 * DAILY_SALARY)
    
    # Desperation: if HP is critically low, bid significantly higher
    if hp <= 2:
        bid = min(budget, 0.8 * DAILY_SALARY)
    elif hp <= 4:
        bid = max(bid, min(budget, 0.5 * DAILY_SALARY))
    
    # Ensure bid does not exceed budget
    bid = min(bid, budget)
    return bid
"""
