# ============================================================
# Experiment: exp_114
# Agent: Eric
# Source: exp_114
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']
    # Convert supply to int for index safety
    supply_int = int(supply)
    # Determine urgency: if hp <= 3 or already dehydrated, bid higher
    if hp <= 3 or no_water_days > 0:
        # Aggressive bid: up to 85% of salary to secure water
        target_bid = DAILY_SALARY * 0.85
    else:
        # Healthy: bid a moderate portion, but adapt if supply is tight
        # Supply shortage -> increase bid slightly
        if supply_int < (WATER_REQ * 2):  # supply below 16
            target_bid = DAILY_SALARY * 0.6
        else:
            target_bid = DAILY_SALARY * 0.4
    # Ensure we don't bid more than budget
    return min(budget, target_bid)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        base_bid = max(DAILY_SALARY * 0.3, min(avg_yesterday * 0.95, DAILY_SALARY * 1.1))
    else:
        base_bid = DAILY_SALARY * 0.5
    if hp <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    if no_water_days > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.7 + 5)
    supply_factor = 1.0 + (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) * 0.2
    bid = min(budget, base_bid * supply_factor)
    return int(bid) if bid > 0 else 0
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Get yesterday's bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            trace = opp.get('previous_trace')
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])
    
    # Base bid strategy
    if supply < WATER_REQ:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.4
    
    # Adjust for health and thirst
    if hp <= 2 or no_water_days >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif hp > 5:
        base_bid = min(base_bid, DAILY_SALARY * 0.3)
    
    # React to yesterday's maximum bid
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > base_bid:
            base_bid = max(base_bid, max_prev +
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if not yesterday_bids:
        # no info, bid moderate
        if my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.85)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    highest_prev = max(yesterday_bids)
    # Calculate number of winners (units of water available)
    supply = day_context['supply']
    num_winners = int(supply // WATER_REQ)  # integer number of winners
    # If we are healthy and opponents bid very high, undercut to save budget
    if highest_prev >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
    else:
        # bid slightly above yesterday's highest, but not too high
        desired = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
        return min(my_status['budget'], min(desired, DAILY_SALARY * 0.9))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)

    # Get yesterday's highest bid among alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    highest_prev = max(prev_bids) if prev_bids else 0.0

    # Desperation levels
    need_water_desperate = (no_water_days > 0) or (hp <= 2)
    health_critical = hp <= 1

    if health_critical:
        # Must win water at any cost
        desired = min(budget, DAILY_SALARY * 0.9)
    elif need_water_desperate:
        # Need water, willing to bid moderately high
        desired = min(budget, DAILY_SALARY * 0.75)
    else:
        # Can be conservative
        desired = min(budget, DAILY_SALARY * 0.5)

    # Adjust based on opponent pressure
    if highest_prev > 0:
        # If opponent was aggressive, we may need to match or beat
        if need_water_desperate:
            desired = max(desired, highest_prev + 2.0)
        else:
            # If we don't need water badly, maybe bid lower to save
            desired = min(desired, highest_prev - 5.0)

    # Supply-based: if supply is low, competition is higher, increase bid
    supply_ratio = supply / 25.0  # 25 is max supply
    if supply_ratio < 0.7:
        desired *= 1.1
    else:
        desired *= 0.9

    # Ensure within budget and at least minimal bid
    bid = max(0.0, min(budget, desired))

    # Ensure we don't exceed salary unreasonably
    if bid > DAILY_SALARY:
        bid = DAILY_SALARY * 0.9

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Get max yesterday bid among alive opponents
    max_prev_bid = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # Determine base bid fraction based on supply and HP
    if hp <= 2:
        # Desperate: need water
        base_fraction = 0.9
    elif supply < 19:
        # Below average supply, more competition
        base_fraction = 0.7
    elif supply > 22:
        # Abundant supply, can bid low
        base_fraction = 0.4
    else:
        base_fraction = 0.55
    
    base_bid = DAILY_SALARY * base_fraction
    
    # Adjust if opponents were aggressive yesterday
    if max_prev_bid > DAILY_SALARY * 0.8:
        # Expect high bids today; if we have low HP, need to outbid
        if hp <= 2:
            target = max(base_bid, max_prev_bid + 1.5)
        else:
            target = max(base_bid, max_prev_bid * 0.9)  # slightly below to save budget
    else:
        target = base_bid
    
    # Ensure we don't bid more than budget
    bid = min(budget, target)
    # Minimum bid of 1 if we can afford
    if bid < 1 and budget >= 1:
        bid = 1.0
    return bid
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
        max_prev_bid = max(yesterday_bids)
        # If low on health, need to win; if healthy, can be conservative
        if hp <= 2:
            target = min(budget, max(DAILY_SALARY * 0.9, max_prev_bid + 2.0))
            return target
        elif hp <= 4:
            target = min(budget, max(DAILY_SALARY * 0.7, max_prev_bid + 1.0))
            return target
        else:
            # Healthy: avoid overpaying; but stay competitive
            if max_prev_bid >= DAILY_SALARY * 0.85:
                return min(budget, DAILY_SALARY * 0.25)
            else:
                return min(budget, max(DAILY_SALARY * 0.4, max_prev_bid + 0.5))
    else:
        # No history: bid cautiously
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.8)
        elif hp <= 4:
            return min(budget, DAILY_SALARY * 0.6)
        else:
            return min(budget, DAILY_SALARY * 0.45)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Default conservative bid
    bid = DAILY_SALARY * 0.35
    
    # Get yesterday's highest bid from opponents that have previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If yesterday high, we need to beat it slightly, but not too much
        target = highest_prev_bid + 2.0
        # Cap by our budget and daily salary
        if my_status['hp'] <= 2:
            trade_off = min(my_status['budget'], DAILY_SALARY * 0.85)
            bid = max(target, trade_off)
        else:
            # If healthy, try to win with minimal premium
            bid = min(target, DAILY_SALARY * 0.75)
    else:
        # No history, use HP-driven strategy
        if my_status['hp'] <= 2:
            bid = DAILY_SALARY * 0.85
        elif my_status['hp'] <= 4:
            bid = DAILY_SALARY * 0.55
        else:
            bid = DAILY_SALARY * 0.35
    
    # Ensure we never exceed budget and at least 0
    bid = max(0, min(bid, my_status['budget']))
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
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Determine urgency: need water if no_water_days > 0 or low HP
    urgent = (no_water_days > 0) or (hp <= 2)
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # If no previous bids, fallback strategy
    if not prev_bids:
        if urgent:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.3)
    
    max_prev_bid = max(prev_bids)
    
    # Cindy-like high bidders: if max previous bid is very high (>120), avoid direct competition unless urgent
    if max_prev_bid >= 120:
        if urgent:
            # Need water badly, bid slightly higher than the high opponent
            return min(budget, max_prev_bid + 1)
        else:
            # Let them win, bid low
            return min(budget, DAILY_SALARY * 0.2)
    else:
        # Moderate bidders: outbid them by small margin if needed
        if urgent:
            target = max(max_prev_bid + 1, DAILY_SALARY * 0.5)
            return min(budget, target)
        else:
            # Not urgent, bid just above the highest previous bid to stay ahead if necessary
            return min(budget, max(max_prev_bid + 1, DAILY_SALARY * 0.3))
"""
