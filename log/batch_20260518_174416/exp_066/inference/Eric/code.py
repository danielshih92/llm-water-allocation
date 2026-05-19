# ============================================================
# Experiment: exp_066
# Agent: Eric
# Source: exp_066
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
    budget = my_status['budget']
    hp = my_status['hp']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return 0

    prev_bids = []
    for opp_id, opp in alive_opponents.items():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    base_bid = DAILY_SALARY * 0.4

    if prev_bids:
        highest_prev = max(prev_bids)
        if hp <= 3:
            target = DAILY_SALARY * 0.9
        else:
            if highest_prev > DAILY_SALARY * 0.7:
                target = highest_prev + 1
            else:
                target = max(highest_prev + 1, base_bid)
        return min(budget, target)

    if hp <= 3:
        bid = DAILY_SALARY * 0.85
    else:
        bid = DAILY_SALARY * 0.5
    return min(budget, bid)
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
    no_water_days = my_status['no_water_days']
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and 'bid' in prev_trace and prev_trace['bid'] is not None:
                prev_bids.append(prev_trace['bid'])
    
    # Determine opponent aggressiveness from yesterday's bids
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    
    # Base bid: 50% of daily salary
    bid = DAILY_SALARY * 0.5
    
    # Adjust for supply scarcity
    if supply < 20:
        bid += DAILY_SALARY * 0.2
    if supply < 18:
        bid += DAILY_SALARY * 0.2
    
    # Adjust for low health or water deprivation
    if hp <= 2 or no_water_days > 0:
        bid = max(bid, DAILY_SALARY * 0.85)
    
    # Respond to aggressive opponents (if max previous bid > 100, increase)
    if max_prev_bid > 100:
        bid = max(bid, max_prev_bid * 0.9)
    
    # Ensure we don't bid more than budget
    bid = min(bid, budget)
    # Ensure minimum bid of 1
    bid = max(bid, 1.0)
    
    return bid
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
    
    alive_opponents = [opp for opp in opponents_status.values() if opp['alive']]
    
    # Get yesterday's maximum bid from all alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Compute number of players (me + alive opponents)
    num_alive = 1 + len(alive_opponents)
    
    # Base bid: try to beat yesterday's highest, or a safe margin
    if prev_bids:
        highest_prev = max(prev_bids)
    else:
        highest_prev = 0
    
    # Estimate required bid to win (based on supply and competition)
    # If supply is plentiful (near max), less pressure
    supply_pressure = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    
    # Desired bid: beat highest previous by a margin, adjusted for pressure
    margin = 2.0 if supply_pressure > 0.5 else 1.0
    desired_bid = highest_prev + margin
    
    # Adjust based on my health
    if hp <= 2:
        # Desperate, need water; bid more aggressively
        desired_bid = max(desired_bid, DAILY_SALARY * 0.8)
    elif hp >= WATER_REQ:
        # Healthy, can afford to save money
        desired_bid = min(desired_bid, DAILY_SALARY * 0.5)
    else:
        # Moderate health, bid moderate
        desired_bid = min(desired_bid, DAILY_SALARY * 0.65)
    
    # Day effect: later days, more aggressive if still needed
    if day > 7 and hp <= 4:
        desired_bid = max(desired_bid, DAILY_SALARY * 0.7)
    
    # Ensure we don't exceed budget
    bid = min(budget, desired_bid)
    
    # Minimum bid: ensure we have a chance if budget is tiny
    if bid < DAILY_SALARY * 0.2 and hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.3)
    
    # Ensure no negative or zero bid (unless impossible)
    if bid < 0:
        bid = 0
    
    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: if low hp or thirsty, be aggressive
    if my_hp < 4 or no_water_days > 0:
        target_bid = max(max_yesterday_bid + 1.0, DAILY_SALARY * 0.9)
    else:
        # Healthy: bid just above yesterday's max if it's reasonable, else moderate
        if max_yesterday_bid > 0:
            target_bid = max(max_yesterday_bid + 1.0, DAILY_SALARY * 0.6)
        else:
            target_bid = DAILY_SALARY * 0.6

    # Ensure we don't exceed budget and cap at salary*1.0 to conserve
    final_bid = min(my_budget, target_bid)
    final_bid = min(final_bid, DAILY_SALARY * 1.0)

    # Ensure at least some bid if we have budget
    if final_bid < 0.1 and my_budget > 0:
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_BID = my_status['budget']
    supply = day_context['supply']
    hp = my_status['hp']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect previous bids from opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Determine aggressive bidding target
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponent bid very high, we need to respond
        if max_prev >= DAILY_SALARY * 0.85:  # ~119
            if hp <= 2:
                target = min(MAX_BID, max_prev + 5)
            elif hp <= 4:
                target = min(MAX_BID, max_prev + 2)
            else:
                target = min(MAX_BID, DAILY_SALARY * 0.5)  # 70
        else:
            # Moderate previous bids
            if hp <= 2:
                target = min(MAX_BID, max_prev + 5)
            elif hp <= 4:
                target = min(MAX_BID, max_prev + 2)
            else:
                target = min(MAX_BID, DAILY_SALARY * 0.4)  # 56
    else:
        # No previous data, use safe default
        if hp <= 2:
            target = min(MAX_BID, DAILY_SALARY * 0.9)  # 126
        elif hp <= 4:
            target = min(MAX_BID, DAILY_SALARY * 0.6)  # 84
        else:
            target = min(MAX_BID, DAILY_SALARY * 0.4)  # 56
    
    # Ensure bid is not negative
    bid = max(0, target)
    # Cap at budget
    return min(bid, MAX_BID)
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

    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev = max(prev_bids) if prev_bids else 0

    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Urgency: desperate if low HP or many days without water
    if hp <= 2 or no_water >= 2:
        return min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        return min(budget, DAILY_SALARY * 0.8)
    elif max_prev > 120:
        # Cindy high, undercut a bit
        return min(budget, max(DAILY_SALARY * 0.5, max_prev - 30))
    else:
        return min(budget, DAILY_SALARY * 0.7)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Estimate today's max opponent bid from yesterday's max
    est_max_opp_bid = max(prev_bids) if prev_bids else DAILY_SALARY * 0.6

    # Adjust for opponent desperation (low hp)
    desperate_opp = any(o['hp'] <= 2 for o in alive_opponents)
    if desperate_opp:
        est_max_opp_bid = max(est_max_opp_bid, DAILY_SALARY * 0.9)

    # Own desperation
    own_desperate = my_status['hp'] <= 2 or my_status['no_water_days'] >= 2
    if own_desperate:
        # Must win at all costs: bid just above estimated max
        bid = min(my_status['budget'], est_max_opp_bid + 5.0)
        return bid

    # Otherwise, try to win cheaply by beating David's low bid or stay low
    if my_status['hp'] > 5 and my_status['budget'] > DAILY_SALARY * 3:
        # Safe: bid low to save money
        bid = min(my_status['budget'], est_max_opp_bid * 0.5)
        return bid

    # Normal competitive bid: beat estimated max by a small margin if we need water
    if my_status['no_water_days'] > 0:
        bid = min(my_status['budget'], est_max_opp_bid + 2.0)
    else:
        # Conserve budget: bid slightly below max
        bid = min(my_status['budget'], est_max_opp_bid * 0.7)

    return max(1.0, bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    # Base bid: if critical HP, go high
    if my_hp <= 2:
        target = min(my_budget, DAILY_SALARY * 0.9)
    else:
        # Decide based on previous bids
        if prev_bids:
            max_prev = max(prev_bids)
            target = min(my_budget, max(max_prev + 1.5, DAILY_SALARY * 0.4))
        else:
            target = min(my_budget, DAILY_SALARY * 0.55)
    # Clamp to 0 and budget
    return max(0.0, target)
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
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine target bid based on supply and yesterday's max
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if supply <= 17:
            # low supply, need to secure water, bid slightly above yesterday's max if affordable
            target = max(DAILY_SALARY * 0.8, min(budget, max_prev + 1.5))
        elif supply >= 22:
            # high supply, can be frugal
            target = min(budget, DAILY_SALARY * 0.5)
        else:
            # medium supply, match or slightly undercut
            if max_prev > DAILY_SALARY * 0.7:
                target = min(budget, DAILY_SALARY * 0.6)
            else:
                target = min(budget, max(DAILY_SALARY * 0.4, max_prev + 0.5))
    else:
        # no history, use conservative baseline
        if hp <= 2:
            target = min(budget, DAILY_SALARY * 0.85)
        else:
            target = min(budget, DAILY_SALARY * 0.55)

    # Ensure we don't go below 0
    return max(0, int(target))
"""
