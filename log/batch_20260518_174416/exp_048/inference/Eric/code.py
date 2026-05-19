# ============================================================
# Experiment: exp_048
# Agent: Eric
# Source: exp_048
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    # Determine if opponents have any trace
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Base bid calculation
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.6
    else:
        bid = DAILY_SALARY * 0.4
    # Exploit yesterday's max bid if known
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if my_status['hp'] <= 2:
            # Outbid slightly but don't go broke
            bid = max(bid, min(max_prev + 2, my_status['budget']))
        else:
            # If opponents bid high yesterday, they might be desperate
            if max_prev > DAILY_SALARY * 0.7:
                bid = min(bid, DAILY_SALARY * 0.3)  # save money
            else:
                bid = max(bid, max_prev + 1)  # beat their last bid
    # Clamp to budget
    bid = min(bid, my_status['budget'])
    # Ensure we don't exceed safe bound
    return max(1.0, bid)
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
    
    # Current day index and supply
    day = int(day_context['day'])  # ensure int
    supply = float(day_context['supply'])
    
    # My state
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    # Gather previous bids from alive opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive'] and opp.get('previous_trace') and opp['previous_trace'].get('bid') is not None:
            prev_bids.append(float(opp['previous_trace']['bid']))
    
    # Determine a target bid based on opponent history and own needs
    base_bid = 0.0
    
    # If we have opponent history, use the maximum observed bid as a threat level
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    
    # Calculate a 'safe' bid: we want to beat the maximum previous bid if we need water
    # But also consider supply: lower supply means higher competition
    if supply < (MIN_SUPPLY + MAX_SUPPLY) / 2:
        # Lower supply -> increase bid by some margin
        margin = 1.5
    else:
        margin = 0.5
    
    # Decide urgency based on hp and no_water_days
    if hp <= 2 or no_water_days >= 1:
        # Need water urgently, be aggressive
        target_bid = max(max_prev_bid + margin, DAILY_SALARY * 0.5)
        # But don't overbid if we have low budget
        if budget < target_bid:
            target_bid = budget * 0.9
        # Cap at daily salary
        target_bid = min(target_bid, DAILY_SALARY * 0.95)
    else:
        # Healthy, can afford to be conservative
        # We want to win only if we can do so cheaply
        # Estimate a low bid that might still win if others are saving
        target_bid = min(max_prev_bid * 0.7, DAILY_SALARY * 0.4)
        # Ensure we don't bid zero if we might need water soon
        if target_bid < 5:
            target_bid = 5.0
    
    # Final sanity: cannot exceed budget
    final_bid = min(target_bid, budget)
    # Ensure bid is non-negative
    final_bid = max(final_bid, 0.0)
    
    return final_bid
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
    
    # Gather last bids from alive opponents (previous day trace)
    last_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                last_bids.append(prev['bid'])
    
    highest_last_bid = max(last_bids) if last_bids else 0.0
    
    # Base bid: slightly above highest opponent last bid if we need water
    if hp <= 2 or no_water_days >= 2:
        # desperate: bid up to salary
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # moderate need: bid to beat opponents, but conserve
        bid = min(budget, max(highest_last_bid + 2, DAILY_SALARY * 0.5))
    else:
        # healthy: save money, bid low but still competitive
        bid = min(budget, max(highest_last_bid * 0.9, DAILY_SALARY * 0.4))
    
    # Adjust for supply: high supply needs lower bid
    if supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.6)
    elif supply <= 17:
        bid = max(bid, DAILY_SALARY * 0.7)
    
    # Ensure we don't exceed budget and stay non-negative
    return max(0, min(budget, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Analyze yesterday's opponent bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid logic
    if hp <= 2 or no_water_days >= 2:
        # Need water urgently
        base_bid = min(budget, DAILY_SALARY * 1.0)
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            # If opponents bid extremely high, just undercut the highest
            if max_prev >= DAILY_SALARY * 0.9:
                base_bid = min(budget, max_prev * 0.95)
            else:
                base_bid = min(budget, max_prev + 2)
        return max(5, base_bid)
    elif hp >= 6:
        # Healthy, conserve budget
        base_bid = min(budget, DAILY_SALARY * 0.3)
        if yesterday_bids:
            avg_prev = sum(yesterday_bids) / len(yesterday_bids)
            base_bid = min(budget, avg_prev * 0.6)
        return max(1, base_bid)
    else:
        # Moderate HP
        if yesterday_bids:
            avg_prev = sum(yesterday_bids) / len(yesterday_bids)
            # Try to stay competitive but not overpay
            return min(budget, max(DAILY_SALARY * 0.5, avg_prev * 0.85))
        else:
            return min(budget, DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])
    
    # Determine opponent pressure: highest bid yesterday
    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
    else:
        max_opp_bid = 0
    
    # Base bid: if supply is scarce relative to water requirement, bid high
    num_players = len(alive) + 1  # including self
    # Rough estimate: if supply is less than total requirement, competition is high
    total_req = num_players * WATER_REQ
    if supply < total_req:
        high_pressure = True
    else:
        high_pressure = False
    
    # Adjust based on HP urgency
    if hp <= 2 or no_water_days >= 1:
        urgent = True
    else:
        urgent = False
    
    # Determine bid amount
    # If urgent, we need to win at almost any cost (up to budget)
    if urgent:
        target_bid = min(budget, DAILY_SALARY * 1.5)  # spend up to 1.5x salary
    else:
        # Conservative: bid enough to win against yesterday's max, but not more than salary
        if high_pressure:
            target_bid = min(budget, max_opp_bid + 1)  # outbid by 1
        else:
            # Low pressure: bid a small fraction of salary to save money
            target_bid = min(budget, DAILY_SALARY * 0.4)
    
    # Ensure we don't bid more than budget
    bid = min(target_bid, budget)
    # Also ensure non-negative
    bid = max(bid, 0)
    
    # In case of extremely low budget, just bid 0
    if budget <= 0:
        bid = 0
    
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
    hp = my_status['hp']
    budget = my_status['budget']
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
    alive_opponents = {oid: opp for oid, opp in opponents_status.items() if opp['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    if yesterday_bids:
        max_yest = max(yesterday_bids)
    else:
        max_yest = 0.0
    base = DAILY_SALARY * 0.7
    if hp > 7:
        target = min(budget, base)
    elif hp > 4:
        target = min(budget, base + 5)
    else:
        target = min(budget, DAILY_SALARY * 0.95)
    if max_yest > DAILY_SALARY * 0.85 and hp > 3:
        target = min(budget, base - 5)
    elif max_yest > DAILY_SALARY * 0.6 and hp > 3:
        target = min(budget, max(base, max_yest + 2))
    else:
        target = min(budget, max(base, max_yest + 1))
    return max(0.0, target)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
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
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 0.85:
            if hp > 3:
                base_bid = DAILY_SALARY * 0.35
            else:
                base_bid = DAILY_SALARY * 0.9
        else:
            base_bid = max(DAILY_SALARY * 0.5, max_prev + 2.0)
    else:
        if hp <= 2:
            base_bid = DAILY_SALARY * 0.85
        else:
            base_bid = DAILY_SALARY * 0.55
    supply_int = int(supply)
    num_units = supply_int // WATER_REQ
    if num_units >= len(alive_opponents) + 1:
        base_bid *= 0.8
    elif num_units <= 1:
        base_bid *= 1.2
    bid = max(1.0, min(budget, base_bid))
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # base bid: a fraction of salary
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        max_prev = 0
        avg_prev = 0
    
    # urgency factor
    urgent = (hp <= 3 or no_water_days > 0)
    very_urgent = (hp <= 1 or no_water_days >= 2)
    
    if very_urgent:
        # must win at almost any cost, up to 95% of budget or 100% of salary
        bid = min(budget * 0.95, DAILY_SALARY * 0.95)
    elif urgent:
        # need water, bid above average but not excessive
        if max_prev > DAILY_SALARY * 0.8:
            # high competition, bid aggressively
            bid = min(budget * 0.9, DAILY_SALARY * 0.85)
        else:
            bid = min(budget * 0.9, max(DAILY_SALARY * 0.6, avg
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
"""
