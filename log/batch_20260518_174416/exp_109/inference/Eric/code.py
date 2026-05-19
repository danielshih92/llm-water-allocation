# ============================================================
# Experiment: exp_109
# Agent: Eric
# Source: exp_109
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)
    base_bid = DAILY_SALARY * 0.5
    if prev_bids:
        max_prev = max(prev_bids)
        base_bid = max_prev + 1.0
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        bid = min(budget, max(base_bid, DAILY_SALARY * 0.6))
    else:
        bid = min(budget, max(base_bid, DAILY_SALARY * 0.4))
    return min(bid, budget)
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}

    prev_bids = []
    for oid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Base bid: 50% of salary = 70
    base_bid = DAILY_SALARY * 0.5

    if not prev_bids:
        # No history: use aggressive but safe
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.95)
        return min(budget, base_bid)

    max_prev = max(prev_bids)
    avg_prev = sum(prev_bids) / len(prev_bids)

    # Decision based on HP and opponent pressure
    if hp <= 2:
        # Desperate: bid high to survive
        target = max(base_bid, max_prev + 2.0)
        return min(budget, min(target, DAILY_SALARY * 0.98))
    elif hp <= 4:
        # Moderate risk: outbid average
        target = max(base_bid, avg_prev + 1.5)
        return min(budget, min(target, DAILY_SALARY * 0.85))
    else:
        # Healthy: try to save, but still competitive
        target = max(base_bid, avg_prev + 0.5)
        return min(budget, min(target, DAILY_SALARY * 0.7))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    
    # Default bid: moderate but safe
    base_bid = DAILY_SALARY * 0.5  # 70
    
    # Check yesterday's traces for opponent bids
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev.get('bid'), (int, float)):
            prev_bids.append(prev['bid'])
    
    if prev_bids:
        # Exploit Cindy's consistent high bids from yesterday
        # If any opponent bid above 100 yesterday, assume they'll do similar today
        high_prev = max(prev_bids)
        if high_prev > 100:
            # Outbid the highest with small margin
            base_bid = high_prev + 5
        else:
            # Slightly above average of yesterday's top few
            sorted_bids = sorted(prev_bids, reverse=True)
            top_avg = sum(sorted_bids[:max(1, len(sorted_bids)//2)]) / max(1, len(sorted_bids)//2)
            base_bid = top_avg + 2
    
    # Adjust based on my health
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        # Desperate: bid higher to get water
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    
    # Ensure we don't bid more than budget or salary
    bid = min(my_status['budget'], base_bid, DAILY_SALARY)
    # Floor at 0
    bid = max(0, bid)
    # Use int() on any list indices if needed (not here, but for safety)
    # Return bid as float
    return float(bid)
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
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # Urgency based on hp
    if hp <= 2:
        # Critical: must survive
        # Bid high, but not exceeding budget
        target = min(budget, max(DAILY_SALARY * 1.2, max_prev_bid + 5))
        return target
    
    # Consider supply level
    # If supply is low, competition is higher
    if supply < 18:
        # Low supply: need to bid more to secure water
        base_bid = max(DAILY_SALARY * 0.7, max_prev_bid + 2)
    else:
        # Normal supply: can afford to be conservative
        base_bid = max(DAILY_SALARY * 0.4, max_prev_bid + 1.5)
    
    # Ensure bid does not exceed budget
    bid = min(budget, base_bid)
    
    # Additionally, if we have enough hp, we can bid lower to save budget
    if hp >= 5 and yesterday_bids and max_prev_bid < DAILY_SALARY * 0.5:
        # Opponents are conservative, we can be even more conservative
        bid = min(budget, DAILY_SALARY * 0.35)
    
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid: proportional to supply shortage
    # Supply range 15-25, water_req 8 -> need to win about 1/3 of days on average
    base_bid = min(budget, DAILY_SALARY * 0.5)
    if supply < 18:
        base_bid = min(budget, DAILY_SALARY * 0.7)
    if hp < 3:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp > 7:
        base_bid = min(budget, DAILY_SALARY * 0.3)
    
    # Adjust based on opponents' previous max bid
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > DAILY_SALARY * 0.8:
            # High aggression: undercut if safe, else match
            if hp > 5 and budget > 200:
                base_bid = min(budget, max_prev * 0.85)
            else:
                base_bid = min(budget, max_prev * 0.95)
        else:
            # Modest: stay slightly above to secure water
            base_bid = min(budget, max(max_prev + 2, base_bid))
    
    # Final sanity: bid at least 1 if budget allows and hp critical
    if hp <= 2 and budget > 10:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    
    # Ensure we don't bid more than budget
    bid = min(budget, max(1, base_bid))
    return float(bid)
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
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for aid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine base target bid
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # Adjust based on highest previous bid
        target = max_yesterday + 1.0
        # If someone was very aggressive yesterday, we might need to increase
        if max_yesterday >= DAILY_SALARY * 0.9:
            target = max_yesterday * 1.05
    else:
        target = DAILY_SALARY * 0.5  # baseline
    
    # Consider own health and remaining days
    # More aggressive if low hp or near end
    if hp <= 2 or no_water_days >= 1:
        target = min(budget, DAILY_SALARY * 0.95)
    elif day >= 8 and hp < 5:
        # Last two days, need water
        target = min(budget, max(target, DAILY_SALARY * 0.8))
    
    # Ensure we don't exceed budget
    bid = min(budget, target)
    # Ensure minimum bid of 1 if we have budget
    if budget > 0 and bid < 1:
        bid = 1
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v.get('alive', False)}
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Default bid to half salary
    bid = DAILY_SALARY * 0.5
    
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        
        # If yesterday had a very high bid (>250), opponents likely to bid lower today to conserve
        if max_prev > 250:
            if hp > 5:
                # Save money, bid low but enough to possibly win if others drop
                bid = max(30, avg_prev * 0.6)
            else:
                # Need water, bid moderately high
                bid = max(DAILY_SALARY * 0.7, avg_prev * 0.9)
        else:
            # Normal competition: bid slightly above average
            bid = avg_prev + 5
    else:
        # No previous data: default bid based on hp
        if hp <= 2:
            bid = DAILY_SALARY * 0.85
        elif hp <= 5:
            bid = DAILY_SALARY * 0.65
        else:
            bid = DAILY_SALARY * 0.4
    
    # Ensure we don't exceed budget and not below 1
    bid = min(bid, budget)
    bid = max(1, bid)
    
    # Round to avoid fractions
    bid = round(bid, 2)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev + 1.5))
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    return min(my_status['budget'], DAILY_SALARY * 0.55)
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
    
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Estimate opponent bids from previous_trace
    estimated_bids = []
    for oid, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                # Use previous bid as estimate, maybe adjust
                estimated_bids.append(prev['bid'])
            else:
                # No history: assume low bid
                estimated_bids.append(0.0)
    
    # Determine urgency
    need_water = (my_hp <= 2) or (no_water_days >= 1)
    
    if estimated_bids:
        max_est = max(estimated_bids)
        # If we need water, we must outbid the highest estimated bid
        if need_water:
            target_bid = max_est + 1.0
            # But cap by budget
            target_bid = min(target_bid, my_budget)
            # Also ensure we can afford daily salary leftovers? Not needed.
            return target_bid
        else:
            # We have HP, can try to save budget: bid just below max_est to stay safe?
            # But if we don't need water, we can bid low or even 0
            return min(my_budget, DAILY_SALARY * 0.3)
    else:
        # No opponents alive? Should not happen often
        if need_water:
            return min(my_budget, DAILY_SALARY * 0.8)
        else:
            return min(my_budget, DAILY_SALARY * 0.2)
"""
