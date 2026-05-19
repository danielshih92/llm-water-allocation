# ============================================================
# Experiment: exp_104
# Agent: Eric
# Source: exp_104
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = int(day_context['day'])  # ensure int
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Fallback: no opponent history
    # If HP is low or no water days > 0, bid higher to secure water
    if hp <= 2 or no_water_days > 0:
        target = min(budget, DAILY_SALARY * 0.9)
    else:
        # Early days: bid around 40-50% of salary
        progress = day / 10.0  # assuming episode 10 days
        base = DAILY_SALARY * (0.4 + 0.2 * progress)
        target = min(budget, base)
    
    # Ensure we can potentially win if supply is low? Not needed for now.
    return max(0, target)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opps = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # Determine the highest bid from yesterday (previous_trace)
    highest_prev = 0
    for o in alive_opps.values():
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev = max(highest_prev, prev['bid'])
    
    urgency = my_status['hp'] / 10.0  # 0-1 scale
    
    if not alive_opps:
        # No competition, bid minimal
        return min(my_status['budget'], DAILY_SALARY * 0.2)
    
    base_bid = 0
    
    if my_status['hp'] <= 2:
        # Critical need: bid high to secure water
        base_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
        return base_bid
    elif my_status['hp'] <= 5:
        # Moderate need: outbid yesterday's max if possible
        target = highest_prev + 1.5
        base_bid = min(my_status['budget'], max(DAILY_SALARY * 0.4, target))
    else:
        # Comfortable HP: save budget, bid low
        base_bid = min(my_status['budget'], DAILY_SALARY * 0.25)
    
    # Cap bid to avoid overspending
    return min(base_bid, my_status['budget'])
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']
    day = day_context['day']
    if budget <= 0:
        return 0.0
    if hp <= 2 or no_water_days >= 2:
        target = min(budget, DAILY_SALARY * 1.0)
        if yesterday_bids:
            max_prev = max(yesterday_bids)
            target = max(target, max_prev + 1.0)
        return min(budget, target)
    if len(yesterday_bids) > 0:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        if max_prev >= DAILY_SALARY * 0.85:
            target = min(budget, DAILY_SALARY * 0.5)
            return target
        else:
            target = max(avg_prev + 2.0, DAILY_SALARY * 0.4)
            target = min(target, budget)
            return target
    else:
        if supply < WATER_REQ:
            return min(budget, DAILY_SALARY * 0.7)
        else:
            return min(budget, DAILY_SALARY * 0.5)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Get yesterday's bids from opponents who were alive yesterday (using previous_trace)
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine base bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If I'm low on HP, outbid aggressively
        if my_hp <= 2:
            target = max_prev + 5.0
        else:
            # Healthy: bid just above the average of high bids to conserve budget
            high_bids = [b for b in prev_bids if b > DAILY_SALARY * 0.5]
            if high_bids:
                avg_high = sum(high_bids) / len(high_bids)
                target = avg_high + 2.0
            else:
                target = max_prev + 1.0
    else:
        # No previous data: use default based on HP
        if my_hp <= 2:
            target = DAILY_SALARY * 0.9
        else:
            target = DAILY_SALARY * 0.55

    # Adjust for supply scarcity
    avg_supply = (25 + 15) / 2.0
    if supply < avg_supply:
        target *= 1.2
    elif supply > avg_supply:
        target *= 0.9

    # Ensure integer index usage (not needed here, but safe)
    target = int(target) if isinstance(target, float) else target
    target = max(1, min(my_budget, target))

    # If budget is very low relative to target, bid all budget
    return min(target, my_budget)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday bids from opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0

    # Urgency based on hp
    if hp <= 2:
        target_bid = min(DAILY_SALARY * 0.9, max_yesterday_bid + 3)
    elif no_water_days >= 1:
        target_bid = min(DAILY_SALARY * 0.8, max_yesterday_bid + 2)
    else:
        # Normal: try to undercut if yesterday's bids were high
        if max_yesterday_bid >= DAILY_SALARY * 0.85:
            # High competition, bid just enough? Actually if supply is moderate, we can bid lower
            # But if supply is low, we need to compete.
            if supply <= 18:
                target_bid = min(DAILY_SALARY * 0.75, max_yesterday_bid + 1)
            else:
                target_bid = DAILY_SALARY * 0.5
        else:
            # Lower competition, bid a bit above yesterday's max to secure
            target_bid = min(DAILY_SALARY * 0.7, max_yesterday_bid + 2)

    # Ensure we don't exceed budget
    bid = min(budget, target_bid)
    # Ensure non-negative
    bid = max(0, bid)
    return bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0

    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # base_factor based on supply
    if supply <= 18:
        base_factor = 0.85
    elif supply <= 22:
        base_factor = 0.65
    else:
        base_factor = 0.5

    base_bid = DAILY_SALARY * base_factor

    if max_yesterday_bid > 0:
        if max_yesterday_bid > DAILY_SALARY * 0.8:
            if hp <= 3:
                target_bid = min(budget, max_yesterday_bid * 1.1)
            else:
                target_bid = min(budget, max_yesterday_bid * 0.8)
        else:
            target_bid = min(budget, max_yesterday_bid + 5)
    else:
        target_bid = base_bid

    bid = min(budget, target_bid)

    # urgency adjustments for late days or low hp
    if day > 5 and hp <= 4:
        bid = min(budget, bid * 1.3)
    if day > 8 and hp <= 2:
        bid = min(budget, bid * 1.5)

    # must get water if critically low
    if no_water >= 1 and hp <= 3:
        bid = max(bid, min(budget, DAILY_SALARY * 0.7))

    # conserve if healthy and bid is high
    if hp > 6 and bid > DAILY_SALARY * 0.4:
        bid = min(bid, DAILY_SALARY * 0.3)

    return float(max(0, bid))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine if there is an aggressive opponent (high previous bid)
    max_prev_bid = 0.0
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            bid = trace['bid']
            if bid > max_prev_bid:
                max_prev_bid = bid

    # Calculate base bid
    if hp <= 2:
        # Desperation: need water badly
        target_bid = min(budget, DAILY_SALARY * 0.8)
    elif hp <= 4:
        target_bid = min(budget, DAILY_SALARY * 0.6)
    else:
        target_bid = min(budget, DAILY_SALARY * 0.4)

    # Adjust based on competition
    if alive_opponents:
        num_alive = len(alive_opponents)
        # If supply is low and many opponents, need to be competitive
        if supply < 20 and num_alive >= 3:
            target_bid = min(budget, max(target_bid, DAILY_SALARY * 0.75))
        # Outbid the highest previous bid if we need water
        if max_prev_bid > target_bid and hp <= 4:
            target_bid = min(budget, max_prev_bid + 1.0)

    # Ensure we don't bid more than budget
    final_bid = min(budget, max(0, target_bid))
    return final_bid
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
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Compute desperation factor
    desperation = 1.0
    if hp <= 2:
        desperation = 2.0
    elif no_water_days >= 1:
        desperation = 1.5
    
    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(float(trace['bid']))
    
    if prev_bids:
        target_bid = max(prev_bids) * 0.9  # Slightly below max to avoid overpaying
    else:
        target_bid = DAILY_SALARY * 0.4
    
    # Adjust based on supply: if low, increase
    if supply < 18:
        target_bid *= 1.2
    elif supply > 22:
        target_bid *= 0.8
    
    # Apply desperation
    bid = target_bid * desperation
    # Clamp to afford
    bid = min(bid, budget * 0.9, DAILY_SALARY * 1.2)
    # Ensure minimum bid if desperate
    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.7)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: if we have recent no-water days, urgently need water
    if no_water_days > 0 or hp <= 2:
        # desperate: bid high, up to budget
        base = min(budget, DAILY_SALARY * 1.2)
    else:
        # normal: try to outbid yesterday's max
        if yesterday_bids:
            max_yesterday = max(yesterday_bids)
            # if supply is low, need to be more aggressive
            if supply < 18:
                target = max_yesterday + 2.0
            else:
                target = max_yesterday + 1.0
        else:
            target = DAILY_SALARY * 0.7
        base = min(budget, target)
    
    # Ensure we don't overpay if supply is high and many competitors survive
    if supply >= 22 and len(alive_opponents) <= 2:
        base = min(base, DAILY_SALARY * 0.8)
    
    # Final sanity: bid at least half salary if hp is moderate
    if hp <= 4 and base < DAILY_SALARY * 0.6:
        base = min(budget, DAILY_SALARY * 0.6)
    
    return max(0.0, min(float(budget), float(base)))
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
    
    # Count alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid: try to get water at reasonable cost
    # If hp is critical, bid aggressively
    if hp <= 2:
        # need water urgently, bid high but not max
        bid = min(budget, DAILY_SALARY * 0.85)
        return int(bid)
    
    # Check yesterday's highest bid among alive opponents
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone bid very high yesterday, they might do it again
        if highest_prev >= DAILY_SALARY * 0.8:
            # Avoid costly bidding war if we have some HP
            if hp > 3:
                bid = min(budget, DAILY_SALARY * 0.5)
            else:
                bid = min(budget, DAILY_SALARY * 0.75)
            return int(bid)
        else:
            # Bid slightly above the highest previous bid, but cap
            target = highest_prev + 1.5
            # Ensure we don't waste too much
            if target > DAILY_SALARY * 0.7:
                target = min(target, DAILY_SALARY * 0.7)
            bid = min(budget, max(DAILY_SALARY * 0.4, target))
            return int(bid)
    
    # No previous data: bid moderate
    bid = min(budget, DAILY_SALARY * 0.6)
    return int(bid)
"""
