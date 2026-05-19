# ============================================================
# Experiment: exp_069
# Agent: Eric
# Source: exp_069
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    salary = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    if day == 1:
        if hp <= 3:
            bid = min(budget, salary * 0.8)
        else:
            bid = min(budget, salary * 0.5)
    else:
        alive_opponents = [o for o in opponents_status.values() if o['alive']]
        prev_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace')
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev['bid'])
        if prev_bids:
            max_prev = max(prev_bids)
            if max_prev > salary * 0.8:
                if hp > 4:
                    bid = min(budget, salary * 0.4)
                else:
                    bid = min(budget, max(salary * 0.6, max_prev + 1))
            else:
                bid = min(budget, salary * 0.5)
        else:
            if hp <= 3:
                bid = min(budget, salary * 0.8)
            else:
                bid = min(budget, salary * 0.5)
    return min(bid, budget)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    previous_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    max_prev_bid = max(previous_bids) if previous_bids else 0

    # Determine urgency: need to bid aggressively if hp low or no_water_days > 0
    need_water = (hp <= 2) or (no_water_days >= 1 and hp <= 4)

    if need_water:
        # Must get water at any cost: outbid the highest previous bid by a small margin
        target_bid = max(DAILY_SALARY * 0.6, max_prev_bid + 2.0)
    else:
        # Healthy: can afford to lose auction to save money
        # Underbid using a fraction of salary, but still competitive if many are bidding low
        if max_prev_bid <= DAILY_SALARY * 0.4:
            target_bid = DAILY_SALARY * 0.45
        else:
            target_bid = DAILY_SALARY * 0.25

    # Ensure not exceeding budget
    bid = min(budget, target_bid)
    # Ensure non-negative
    bid = max(0, bid)
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
    
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Base bid proportion: start low, increase if HP low
    if hp <= 3:
        base_bid = DAILY_SALARY * 0.7
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.5
    else:
        base_bid = DAILY_SALARY * 0.35
    
    # Adjust based on supply: more supply -> lower bid
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # If supply low (0), multiply by 1.2; if high, multiply by 0.8
    supply_factor = 0.8 + 0.4 * (1 - supply_ratio)
    bid = base_bid * supply_factor
    
    # If we have no_water_days > 1, increase bid
    if my_status['no_water_days'] >= 2:
        bid = max(bid, DAILY_SALARY * 0.8)
    
    # Opponent history adjustment (only if previous_trace exists)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if alive_opponents and day > 1:
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            # If they bid very high yesterday, they might still, so consider matching
            if max_prev > DAILY_SALARY * 0.8 and hp > 3:
                bid = min(bid, DAILY_SALARY * 0.4)  # conserve
            elif max_prev > DAILY_SALARY * 0.5:
                bid = max(bid, max_prev * 0.9)  # slightly below
    
    # Ensure bid within budget and non-negative
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
    
    # Determine base bid
    base_bid = DAILY_SALARY * 0.6
    
    # Gather previous bids from alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Decide bid based on previous highest
    if prev_bids:
        highest_prev = max(prev_bids)
        # Slightly outbid the highest previous, but stay reasonable
        target = max(base_bid, highest_prev + 1.5)
    else:
        target = base_bid
    
    # Urgency adjustments
    if my_status['no_water_days'] > 0:
        target = max(target, DAILY_SALARY * 0.9)
    if my_status['hp'] <= 3:
        target = max(target, DAILY_SALARY * 0.85)
    
    # Final bid: cannot exceed budget
    bid = min(my_status['budget'], target)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Check if any opponent has a previous trace with a high bid
    high_prev = False
    for opp in alive.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > 120:
                high_prev = True
                break
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Desperate if low hp
    if hp <= 3:
        return min(budget, DAILY_SALARY * 0.95)
    
    # If we know they bid high, be slightly higher
    if high_prev:
        target = 135.0
    else:
        # Assume they bid moderate
        target = 120.0
    
    # Ensure we don't exceed budget
    bid = min(budget, target)
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from alive opponents
    yest_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yest_bids.append(prev['bid'])
    
    # Estimate number of winners
    max_winners = int(supply // WATER_REQ)
    if max_winners < 1:
        max_winners = 1
    
    # Determine target bid
    if yest_bids:
        # Sort yesterday bids to gauge typical behavior
        sorted_bids = sorted(yest_bids)
        median_bid = sorted_bids[len(sorted_bids)//2] if len(sorted_bids) > 0 else 0
        # If we are healthy, try to slightly beat median bid
        if hp > 4:
            target = min(budget, median_bid + 2.0)
        else:
            # Desperate: bid higher to ensure win
            target = min(budget, max(median_bid + 10.0, DAILY_SALARY * 0.8))
    else:
        # No yesterday info: moderate default based on hp
        if hp <= 2:
            target = min(budget, DAILY_SALARY * 0.9)
        elif hp <= 5:
            target = min(budget, DAILY_SALARY * 0.6)
        else:
            target = min(budget, DAILY_SALARY * 0.4)
    
    # Ensure we don't go broke
    return max(0.0, min(budget, target))
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # base survival threshold: how much competition can supply sustain?
    max_winners = int(supply // WATER_REQ)  # convert to int to avoid float index issues

    # if we are desperate (low hp or no water days > 1)
    if hp <= 2 or no_water_days >= 1:
        # need to win at almost any cost
        bid = max(DAILY_SALARY * 0.9, max_yesterday_bid + 2.0)
        return min(budget, bid)

    # moderate situation: decide based on competition pressure
    if max_yesterday_bid >= DAILY_SALARY * 0.8:
        # opponents are aggressive, we need to match if we have hp to spare
        if hp > 3:
            bid = min(DAILY_SALARY * 0.7, max_yesterday_bid + 1.5)
        else:
            bid = min(DAILY_SALARY * 0.85, max_yesterday_bid + 2.0)
        return min(budget, max(bid, DAILY_SALARY * 0.5))

    # low pressure: bid conservatively, only slightly above if needed
    base_bid = DAILY_SALARY * 0.5
    if yesterday_bids:
        # ensure we can beat the lowest of yesterday's top bids?
        # just stay below but safe; if many winners possible, bid lower
        if max_winners >= len(alive_opponents) + 1:
            bid = DAILY_SALARY * 0.4
        else:
            bid = max(base_bid, max_yesterday_bid * 1.05)
    else:
        bid = base_bid

    return min(budget, bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    max_winners = int(supply // WATER_REQ)
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            bid = trace.get('bid')
            if bid is not None:
                prev_bids.append(bid)
    
    # Determine target bid to secure a slot among top max_winners
    if len(prev_bids) >= max_winners:
        prev_bids_sorted = sorted(prev_bids, reverse=True)
        # We need to beat the bid at index max_winners-1 (0-indexed)
        target_prev_bid = prev_bids_sorted[max_winners - 1]
        bid = target_prev_bid + 1.0
    else:
        # Not enough opponents to fill slots, bid moderate
        bid = DAILY_SALARY * 0.5
    
    # Safety adjustments based on health
    if hp <= 2 or no_water_days > 0:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.6)
    
    # Ensure we never bid more than budget
    bid = min(bid, budget)
    # Ensure non-negative
    bid = max(bid, 0.0)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    # base bid: need 8 units, supply ranges 15-25. If supply high, bid low.
    # Assuming linear: at supply=25, base=50; at supply=15, base=90.
    # Use interpolation: base = (max_supply - supply) * 4 + 50
    base_bid = (MAX_SUPPLY - supply) * 4 + 50
    # consider yesterday's highest bid to avoid overbidding
    highest_prev = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev = max(highest_prev, prev['bid'])
    # adjust based on opponent aggression
    if highest_prev > 100:
        # they are bidding very high, likely they will continue
        # I don't want to waste budget, but I need water
        if my_hp <= 2 or no_water_days >= 1:
            bid = min(my_budget, DAILY_SALARY * 0.95)
        else:
            bid = min(my_budget, base_bid * 0.7)
    else:
        # moderate opponents, bid around base
        if my_hp <= 2 or no_water_days >= 1:
            bid = min(my_budget, DAILY_SALARY * 0.9)
        else:
            bid = min(my_budget, base_bid)
    # also ensure we can at least get some water if supply is low
    # supply is number of units available, we need 8, so max we can win is supply
    # but we don't know others' bids. Just bid reasonably.
    return max(0, int(bid))
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Estimate yesterday's highest bid from traces
    highest_prev = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev = max(highest_prev, prev['bid'])
    
    # Base bid strategy
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on supply
    supply_ratio = supply / 25.0
    if supply_ratio < 0.7:
        base_bid *= 1.2
    
    # React to high previous bids
    if highest_prev > DAILY_SALARY * 0.85:
        if hp > 3:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    
    # Ensure we don't exceed budget
    bid = min(budget, base_bid)
    bid = max(bid, 0.1)
    return bid
"""
