# ============================================================
# Experiment: exp_093
# Agent: Eric
# Source: exp_093
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
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    # Desperation: if you've missed water for 2+ days or very low HP, bid high
    if hp <= 2 or no_water_days >= 2:
        return min(budget, DAILY_SALARY * 1.2)
    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            pt = opp.get('previous_trace')
            if pt and pt.get('bid') is not None:
                prev_bids.append(pt['bid'])
    # If we have information about yesterday's highest bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponents were very aggressive last day, be conservative if healthy
        if max_prev >= DAILY_SALARY * 0.85:
            if hp > 3:
                return min(budget, DAILY_SALARY * 0.35)
            else:
                return min(budget, DAILY_SALARY * 0.9)
        else:
            # Slightly beat the highest previous bid but cap at budget
            return min(budget, max(DAILY_SALARY * 0.5, max_prev + 2.0))
    # No history: moderate bid based on HP
    if hp <= 4:
        return min(budget, DAILY_SALARY * 0.8)
    else:
        return min(budget, DAILY_SALARY * 0.6)
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
    
    supply = day_context['supply']
    day = day_context['day']
    budget = my_status['budget']
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get previous bid for each alive opponent
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    
    # Determine number of possible winners
    supply_int = int(supply)
    max_winners = supply_int // WATER_REQ
    
    # Desperation: need water soon
    desperate = (hp <= 2) or (no_water >= 2) or (hp <= 4 and day >= 5)
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

    # Base bid as percentage of salary
    base_pct = 0.5
    if hp <= 2:
        base_pct = 0.9
    elif hp <= 4:
        base_pct = 0.7
    bid = DAILY_SALARY * base_pct

    # Adjust based on supply tightness
    low_supply = 18.0
    if supply <= low_supply:
        bid += 15.0
    elif supply >= 22.0:
        bid -= 10.0

    # React to yesterday's opponent behavior
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if alive_opponents and day > 1:
        max_prev_bid = 0.0
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                max_prev_bid = max(max_prev_bid, prev['bid'])
        if max_prev_bid > 0:
            # If they bid high yesterday, we need to match or slightly exceed
            target_bid = max_prev_bid + 5.0
            if target_bid > bid:
                bid = target_bid

    # Ensure bid is within bounds
    bid = max(0.0, min(bid, budget, DAILY_SALARY * 1.0))

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max = max(yesterday_max, prev['bid'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    # If low HP, need to win at all costs
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.95)
    
    # Moderate HP: try to outbid yesterday's max if reasonable, else conservative
    if yesterday_max <= DAILY_SALARY * 0.7:
        target = yesterday_max + 1.0
        if target > DAILY_SALARY:
            target = DAILY_SALARY
        return min(budget, target)
    else:
        # High competition, avoid overpaying unless necessary
        return min(budget, DAILY_SALARY * 0.45)
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: if very low HP, bid high to survive
    if hp <= 2:
        return min(budget, DAILY_SALARY * 1.2)
    
    # Estimate competition from yesterday
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        median = sorted_bids[len(sorted_bids)//2]
        # Adjust for supply: if supply low, increase bid
        supply_factor = 1.0 + (20 - supply) / 40.0  # between 0.875 and 1.125 when supply 15-25
        bid = (median + 1.0) * supply_factor
    else:
        # No historical data: use simple formula based on day and hp
        if hp > 5:
            bid = DAILY_SALARY * 0.4
        else:
            bid = DAILY_SALARY * 0.7
    
    # Cap by budget and ensure not to waste too much
    bid = min(budget, max(bid, 0.1 * DAILY_SALARY))
    # Early days: be more conservative, later days: be more aggressive if needed
    if day > 7 and hp < 5:
        bid = max(bid, DAILY_SALARY * 0.9)
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Extract today's info
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Consider alive opponents
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for oid, opp in alive_opponents.items():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    # If we need water urgently (hp low or dehydrated)
    is_urgent = (hp <= 2) or (no_water_days >= 1)
    
    # Determine bid
    if is_urgent:
        # Aggressive: bid up to 90% of budget or enough to beat yesterday's max
        base_bid = DAILY_SALARY * 1.2  # 168
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            base_bid = max(base_bid, max_prev + 1.0)
        # Cap by budget
        bid = min(budget, base_bid)
    else:
        # Not urgent - try conservative but still competitive
        # If yesterday's max was very high (>150), we likely can't outbid; bid low to save
        if yesterday_bids and max(yesterday_bids) > 150:
            bid = min(budget, DAILY_SALARY * 0.3)  # ~42
        else:
            # Otherwise, bid a moderate amount (e.g., 60% of salary) to try to win cheap
            bid = min(budget, DAILY_SALARY * 0.6)  # 84
    
    # Ensure we don't exceed budget and are non-negative
    bid = max(0.0, min(bid, budget))
    return bid
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
    hp = int(my_status['hp'])
    budget = int(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # if we have data, use it to estimate today's pressure
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # if opponent was very aggressive yesterday, they might be still aggressive
        if max_prev >= DAILY_SALARY * 0.85:
            if hp <= 2:
                return min(budget, DAILY_SALARY * 0.95)
            else:
                return min(budget, max(DAILY_SALARY * 0.3, DAILY_SALARY * 0.5))
        else:
            # moderate yesterday, try to just beat them by a little if needed
            if hp <= 2:
                return min(budget, max(DAILY_SALARY * 0.9, max_prev + 2.0))
            else:
                return min(budget, max(DAILY_SALARY * 0.4, max_prev + 1.5))
    else:
        # no yesterday data (first day or all opponents were dead already)
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Determine base bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        # If we are desperate (low hp or high no_water_days), outbid highest
        if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
            target = highest_prev + 5
        else:
            # Bid slightly above average to increase chance of winning without overspending
            target = avg_prev + 2
        # Ensure we don't exceed budget and stay within reasonable range
        bid = max(DAILY_SALARY * 0.2, min(target, my_status['budget']))
    else:
        # No yesterday data: use hp-based heuristic
        if my_status['hp'] <= 2:
            bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.5)
    # Final safety: do not bid more than budget or less than 0
    bid = max(0, min(bid, my_status['budget']))
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    alive_count = len(alive_opponents)

    # Compute previous bids from opponents (only yesterday)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Base bid: moderate
    base_bid = DAILY_SALARY * 0.5  # 70

    # Adjust based on opponent behavior
    if prev_bids:
        max_prev = max(prev_bids)
        # If any opponent previously bid aggressively, be cautious
        if max_prev > DAILY_SALARY * 0.6:
            # We need to outbid if we are desperate, otherwise slightly undercut
            if hp <= 2 or no_water_days >= 1:
                # Desperate: bid slightly above max_prev
                desired = max_prev + 2.0
            else:
                # Healthy: try to save, bid a bit lower but still competitive
                desired = max_prev * 0.9 + 1.0
        else:
            desired = base_bid
    else:
        # No trace, use base
        desired = base_bid

    # Cap by budget and never exceed daily salary * 0.95
    max_bid = min(budget, DAILY_SALARY * 0.95)
    bid = min(max_bid, desired)

    # Ensure minimum bid if we have no water days
    if no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 0.85)

    # Final check: never bid more than budget
    return max(0.0, min(bid, budget))
"""
