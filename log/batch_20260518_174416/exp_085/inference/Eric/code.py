# ============================================================
# Experiment: exp_085
# Agent: Eric
# Source: exp_085
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if day == 1:
        if hp <= 2:
            base_ratio = 0.85
        elif supply < (MIN_SUPPLY + MAX_SUPPLY) / 2:
            base_ratio = 0.65
        else:
            base_ratio = 0.5
        return min(budget, DAILY_SALARY * base_ratio)
    yesterday_bids = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        if hp <= 2:
            return min(budget, max(DAILY_SALARY * 0.9, max_yesterday + 2))
        if max_yesterday >= DAILY_SALARY * 0.8:
            return min(budget, DAILY_SALARY * 0.35)
        return min(budget, max(DAILY_SALARY * 0.5, max_yesterday + 1))
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.9)
    return min(budget, DAILY_SALARY * 0.55)
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
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Estimate number of winners
    winners = supply // WATER_REQ
    
    # Determine aggressive opponents from yesterday's trace
    max_prev_bid = 0
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    
    # Base bid on supply and urgency
    if hp <= 2:
        target = min(budget, DAILY_SALARY * 0.9)
    elif supply > 20:
        target = DAILY_SALARY * 0.6
    else:
        target = DAILY_SALARY * 0.85
    
    # Adjust if yesterday's max bid is high and we need to beat it
    if max_prev_bid > DAILY_SALARY * 0.8 and supply <= 20:
        target = max(target, max_prev_bid + 1)
    
    # Ensure we don't exceed budget
    return min(budget, target)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    daily_salary = 140
    supply = int(day_context['supply'])
    alive_opp = {k:v for k,v in opponents_status.items() if v['alive']}
    # Get yesterday's highest bid from alive opponents
    highest_prev = 0.0
    for opp in alive_opp.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            if prev['bid'] > highest_prev:
                highest_prev = prev['bid']
    # Determine bid based on urgency
    if my_status['hp'] <= 2:
        # desperate: bid up to 90% of salary
        target = min(my_status['budget'], daily_salary * 0.9)
    else:
        # try to outbid highest previous by a small margin
        target = highest_prev + 2.0
        # cap to avoid overpaying, but not too low
        target = min(my_status['budget'], max(daily_salary * 0.3, target))
    return max(0.0, target)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Get yesterday's max bid from opponents
    max_yesterday_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > max_yesterday_bid:
                max_yesterday_bid = prev['bid']

    # Base bid: scaled by supply (less water, higher bid)
    scarcity = 1 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 1 when supply=15, 0 when supply=25
    base_bid = DAILY_SALARY * (0.3 + 0.4 * scarcity)

    # Urgency: low hp or dehydration
    if hp <= 2 or no_water_days > 0:
        urgency_mult = 1.8
    elif hp <= 4:
        urgency_mult = 1.4
    else:
        urgency_mult = 1.0

    bid = base_bid * urgency_mult

    # React to yesterday's high bids
    if max_yesterday_bid > 0:
        # If we need water, bid slightly above the highest yesterday
        if hp <= 4 or no_water_days > 0:
            target = max(bid, max_yesterday_bid + 1)
        else:
            target = max(bid, max_yesterday_bid * 0.9)
        bid = target

    # Ensure we don't exceed budget and don't bid more than necessary
    bid = min(bid, budget, DAILY_SALARY * 2)  # cap at double salary
    bid = max(bid, 1)  # always positive

    return round(bid, 2)
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Extract yesterday's bids from opponents who have previous_trace
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine threat level from yesterday
    high_bid_threshold = DAILY_SALARY * 0.85  # ~119
    desperate_opponent_present = any(bid >= high_bid_threshold for bid in yesterday_bids)
    
    # Base bid calculation
    if hp <= 2:
        # Very low HP, must win water at almost any cost
        bid = DAILY_SALARY * 0.95  # 133
    elif hp <= 5:
        # Low HP, need water but can't waste budget
        bid = DAILY_SALARY * 0.65  # 91
    else:
        # Healthy, can afford to conserve
        bid = DAILY_SALARY * 0.40  # 56
    
    # Adjust based on opponent desperation (they might be willing to outbid us)
    if desperate_opponent_present and hp > 3:
        # If they were desperate yesterday, they may still be, but we can undercut
        bid = bid * 0.7
    
    # Adjust for supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    if supply_ratio < 0.3:
        bid *= 1.3  # increase when supply low
    elif supply_ratio > 0.7:
        bid *= 0.8  # decrease when supply high
    
    # Ensure bid does not exceed budget (but budget may be low early on)
    # Also, we must not exceed budget to avoid error? Actually budget is after salary, but we can bid up to budget.
    bid = min(bid, budget)
    # Ensure bid is at least a small positive amount to avoid error (bid must be >=0)
    bid = max(0, bid)
    # Round to float
    return float(bid)
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
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Gather yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace')
        if trace and isinstance(trace, dict) and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])
    
    # Base bid depending on hp
    if hp <= 2:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.6)
    
    # Adjust based on opponents' previous highest bid
    if yesterday
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

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine highest bid from yesterday among alive opponents
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])

    # Critical threshold: if hp is low or no_water_days>0, must win water
    if hp <= 2 or no_water_days > 0:
        return min(budget, DAILY_SALARY * 0.9)

    # Otherwise, try to outbid yesterday's highest by a small margin
    target_bid = max_prev_bid + 1.5
    # Cap by salary and budget
    target_bid = min(target_bid, DAILY_SALARY * 0.85)
    target_bid = min(target_bid, budget)
    # Ensure at least a minimum bid to have a chance (do not bid 0)
    target_bid = max(target_bid, DAILY_SALARY * 0.3)

    # If we have plenty of hp and high budget, be conservative to save money
    if hp > 5 and budget > DAILY_SALARY * 2:
        target_bid = min(target_bid, DAILY_SALARY * 0.5)

    return target_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        # Only me left, bid minimal
        return min(budget, 0.4 * DAILY_SALARY)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Determine base need: low HP or no water -> need water urgently
    urgent = (hp <= 2) or (no_water_days >= 1)

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # Bob-like aggressive bidder
        if highest_prev >= 0.85 * DAILY_SALARY:
            if urgent:
                # Must win: outbid slightly above highest
                return min(budget, highest_prev + 2.0)
            else:
                # Don't engage, bid low
                return min(budget, 0.3 * DAILY_SALARY)
        else:
            # Moderate competition: bid just above highest to secure if needed
            if urgent:
                return min(budget, max(0.6 * DAILY_SALARY, highest_prev + 1.5))
            else:
                return min(budget, max(0.4 * DAILY_SALARY, highest_prev + 0.5))
    else:
        # No yesterday info: fallback
        if urgent:
            return min(budget, 0.85 * DAILY_SALARY)
        else:
            return min(budget, 0.5 * DAILY_SALARY)
"""
