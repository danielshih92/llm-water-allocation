# ============================================================
# Experiment: exp_028
# Agent: Eric
# Source: exp_028
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp > 3:
                return min(budget, DAILY_SALARY * 0.3)
            return min(budget, DAILY_SALARY * 0.95)
        return min(budget, max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.9)
    return min(budget, DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect previous bids from opponents (yesterday's trace)
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Determine target bid based on history and need
    if prev_bids:
        highest_prev = max(prev_bids)
        # If highest was very aggressive (near max budget), we may want to be cautious
        if highest_prev > 120:
            if hp <= 3:
                # Desperate, bid high to survive
                target = min(budget, DAILY_SALARY * 0.9)
            else:
                # Conserve budget, bid low to avoid conflict
                target = min(budget, DAILY_SALARY * 0.3)
        else:
            # Outbid the highest by a small margin, but cap at budget and reasonable portion
            target = min(budget, max(DAILY_SALARY * 0.4, highest_prev + 2.0))
    else:
        # No history from yesterday (first day or all dead)
        if hp <= 2:
            target = min(budget, DAILY_SALARY * 0.85)
        else:
            target = min(budget, DAILY_SALARY * 0.5)
    
    # Ensure bid is non-negative and within budget
    return max(0.0, target)
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

    # determine how many units of water can be allocated based on supply
    max_units = int(supply // WATER_REQ)
    # number of alive agents (including self)
    total_alive = len(alive_opponents) + 1

    # estimate a reasonable bid: if many agents, competition may be higher
    # look at yesterday's bids from each opponent
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # base bid: try to get water at a moderate price
    # use a fraction of salary as base
    base_bid = DAILY_SALARY * 0.6

    # if we have no water for more than 1 day, urgency increases
    if no_water_days > 1 or hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.75

    # adjust based on yesterday's competition
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # if someone bid very high yesterday, maybe they will repeat; protect
        if max_yesterday > DAILY_SALARY * 0.85:
            if hp < 3:
                base_bid = DAILY_SALARY * 0.95
            else:
                base_bid = DAILY_SALARY * 0.5
        else:
            # otherwise, try to outbid the highest yesterday by a small margin
            target = max(base_bid, max_yesterday + 1.0)
            if target <= budget:
                base_bid = target
    else:
        # no historical data: play safe
        if hp <= 2:
            base_bid = DAILY_SALARY * 0.9
        else:
            base_bid = DAILY_SALARY * 0.55

    # ensure we don't exceed budget
    bid = min(budget, base_bid)
    # ensure non-negative
    bid = max(0, bid)
    return bid
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
    alive = [o for o in opponents_status.values() if o.get('alive', False)]
    n = len(alive)
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    if yesterday_bids:
        max_prev = max(yesterday_bids)
    else:
        max_prev = 0.0
    # Determine base bid: proportional to scarcity and hp need
    scarcity_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 1=scarce, 0=abundant
    base = DAILY_SALARY * (0.3 + 0.3 * scarcity_factor)
    # Adjust for hp and days without water
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.3
    target = base + (DAILY_SALARY * 0.5) * urgency
    # If we have yesterday's max, consider outbidding if necessary, but stay conservative when healthy
    if yesterday_bids:
        if max_prev > target and (hp <= 3 or no_water_days >= 1):
            target = max_prev + 1.0  # beat last high bid
        elif max_prev > target and hp > 3:
            # stay lower to save money
            pass
        else:
            # target already high enough
            pass
    # Cap at budget
    bid = min(budget, target)
    # Ensure non-negative
    bid = max(0.0, bid)
    return int(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    desperate = (hp <= 2) or (no_water_days >= 2)
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0.0
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        target = min(budget, max(DAILY_SALARY * 0.9, max_yesterday + 2.0))
    elif hp <= 4:
        target = min(budget, max(DAILY_SALARY * 0.6, max_yesterday + 1.0))
    else:
        target = min(budget, max(DAILY_SALARY * 0.3, max_yesterday + 0.5))
    return max(0.0, target)
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
    
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Determine yesterday's max bid among alive opponents
    max_prev_bid = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev:
            max_prev_bid = max(max_prev_bid, float(prev['bid']))
    
    # Base bid: fraction of daily salary based on supply tightness
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.5:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust for health urgency
    if hp <= 3:
        urgency_factor = 0.25
    elif hp <= 5:
        urgency_factor = 0.15
    else:
        urgency_factor = 0.0
    base_bid += DAILY_SALARY * urgency_factor
    
    # Outbid yesterday's maximum slightly if we can afford
    target_bid = max(base_bid, max_prev_bid + 1.5)
    
    # Ensure we never bid more than budget or more than daily salary (aggressive but safe)
    max_allowed = min(budget, DAILY_SALARY)
    final_bid = min(target_bid, max_allowed)
    
    # If we are desperate (no water for 2+ days), bid extra
    if no_water_days >= 2:
        final_bid = min(budget, DAILY_SALARY * 0.9)
    
    # Save budget early if we can - but still competitive
    if day <= 3 and hp > 5:
        final_bid = min(final_bid, DAILY_SALARY * 0.6)
    
    return int(final_bid)
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
    no_water_days = my_status['no_water_days']

    alive_opponents = {oid: opp for oid, opp in opponents_status.items() if opp['alive']}

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])

    # Determine target bid based on yesterday's behavior
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
    else:
        max_prev = 0
        avg_prev = 0

    # Base bid: if we missed water recently, bid high; else moderate
    if no_water_days >= 2 or hp <= 2:
        target = max(avg_prev + 5, max_prev + 1)
    elif hp <= 4:
        target = avg_prev + 2
    else:
        target = avg_prev - 2 if avg_prev > 50 else avg_prev + 2

    # Adjust for supply: if supply is high, competition might be lower
    if supply >= 22:
        target -= 5
    elif supply <= 17:
        target += 5

    # Ensure we don't overbid our budget
    bid = min(budget, max(target, 0))

    # Safety: if budget is very low, bid everything
    if budget < 10:
        bid = budget

    return round(bid, 2)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
    else:
        avg_bid = DAILY_SALARY * 0.6
    hp = my_status['hp']
    if hp <= 2:
        bid = DAILY_SALARY * 0.95
    elif hp <= 4:
        bid = max(avg_bid - 5, DAILY_SALARY * 0.5)
    else:
        bid = max(avg_bid - 10, DAILY_SALARY * 0.3)
    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace')
        if trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    max_prev = max(prev_bids) if prev_bids else 0

    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    day = day_context['day']

    # Base bid based on HP and yesterday's max bid
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        bid = min(budget, max(DAILY_SALARY * 0.6, max_prev + 2))
    else:
        if max_prev > DAILY_SALARY * 0.85:
            bid = min(budget, DAILY_SALARY * 0.3)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)

    # Adjust if dehydrated
    if my_status['no_water_days'] > 0:
        bid = max(bid, DAILY_SALARY * 0.7)

    return min(budget, max(0, bid))
"""
