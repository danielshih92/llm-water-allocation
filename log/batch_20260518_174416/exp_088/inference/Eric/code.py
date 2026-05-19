# ============================================================
# Experiment: exp_088
# Agent: Eric
# Source: exp_088
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.85)
    else:
        bid = min(budget, DAILY_SALARY * 0.45)
    return bid
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
    
    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base decision parameters
    if hp <= 2:
        # Critical health: must win water
        base_bid = DAILY_SALARY * 0.95
    elif hp <= 5:
        # Moderate risk
        base_bid = DAILY_SALARY * 0.7
    else:
        # Healthy: can be conservative
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
        # React if someone was bidding aggressively
        if highest_yesterday > DAILY_SALARY * 0.85:
            if hp <= 2:
                # Must outbid
                bid = min(budget, highest_yesterday + 10)
            else:
                bid = min(budget, base_bid)
        else:
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    # Alive opponents and their last bids
    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
    # Estimate average opponent bid (use DAILY_SALARY as fallback)
    avg_opp_bid = DAILY_SALARY * 0.7 if not prev_bids else sum(prev_bids) / len(prev_bids)
    # Urgency based on health and no_water_days
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    supply = day_context['supply']
    # Adjust factor based on supply tightness: lower supply -> higher need to bid
    scarcity_factor = max(0.5, (WATER_REQ * (len(alive_opps) + 1)) / max(supply, 1))
    if hp <= 2 or no_water > 0:
        # Desperate: must win
        target = max(avg_opp_bid * 1.3, DAILY_SALARY * 0.9) * scarcity_factor
        return min(budget, target + 1)
    elif hp <= 5:
        target = max(avg_opp_bid * 1.1, DAILY_SALARY * 0.6) * scarcity_factor
        return min(budget, target + 1)
    else:
        # Healthy: try to save budget
        target = avg_opp_bid * 0.8 * scarcity_factor
        return min(budget, max(1, target))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    alive_opponents = [opp for opp in opponents_status.values() if opp['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    highest_prev = max(prev_bids) if prev_bids else 0
    # Base bid: if supply is scarce, bid higher
    if supply < 18:
        base = DAILY_SALARY * 0.85  # ~119
    else:
        base = DAILY_SALARY * 0.75  # ~105
    # Adjust based on yesterday's high
    if highest_prev > 0:
        target = max(base, highest_prev + 10)
    else:
        target = base
    # Urgency from hp
    if my_status['hp'] <= 2:
        target = min(DAILY_SALARY * 0.95, target + 20)
    elif my_status['hp'] <= 5:
        target = min(DAILY_SALARY * 0.9, target + 10)
    # Never exceed budget
    return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    SUPPLY = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Check yesterday's bids from opponents
    max_yesterday_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev.get('bid'), (int, float)):
            if prev['bid'] > max_yesterday_bid:
                max_yesterday_bid = prev['bid']
    
    # Determine base fraction based on desperation
    if no_water_days >= 1 or hp <= 2:
        desire = 0.95
    elif hp <= 4:
        desire = 0.75
    else:
        desire = 0.4
    
    # Adjust for supply scarcity
    supply_factor = 1 - (SUPPLY / 30.0)  # normalized, higher scarcity increases factor
    desire += supply_factor * 0.3
    desire = min(desire, 0.99)
    
    base_bid = DAILY_SALARY * desire
    
    # If a opponent yesterday bid very high (above salary), avoid competing unless desperate
    if max_yesterday_bid > DAILY_SALARY * 0.9 and desire < 0.75:
        # Try to underbid and hope they win
        base_bid = min(base_bid, DAILY_SALARY * 0.35)
    
    # Ensure we don't exceed budget
    bid = min(budget, base_bid)
    # Ensure minimum bid to avoid zero if possible (except if budget zero)
    if budget > 0 and bid < 1:
        bid = min(budget, 1.0)
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

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Determine highest previous bid from alive opponents
    highest_prev = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev = max(highest_prev, prev['bid'])

    # Calculate supply factor: lower supply means more competition, higher bid
    supply = day_context['supply']
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 (scarce) to 1 (abundant)

    # Base bid: slightly above highest previous bid, but not exceeding budget
    base_bid = highest_prev + 2.0

    # Adjust based on own health and supply
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # If we are desperate (low HP or multiple days without water), bid aggressively
    if hp <= 2 or no_water_days >= 2:
        target = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        target = min(budget, max(base_bid, DAILY_SALARY * 0.7))
    else:
        # Healthy: try to conserve budget, lower bid if supply abundant
        if supply_ratio > 0.6:
            target = min(budget, max(base_bid * 0.7, DAILY_SALARY * 0.4))
        else:
            target = min(budget, max(base_bid, DAILY_SALARY * 0.5))

    # Ensure bid is at least 1 to have a chance
    target = max(1.0, target)

    # Convert to float and return
    return float(target)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
    else:
        highest_prev = 0

    # Base bid: need to outbid highest previous, but consider supply scarcity
    if supply < 18:
        scarcity_factor = 1.2
    else:
        scarcity_factor = 1.0

    if hp <= 2 or no_water_days > 0:
        # Desperate: bid high
        target_bid = max(DAILY_SALARY * 0.9, (highest_prev + 2) * scarcity_factor)
    else:
        # Comfortable: bid just above competition
        if yesterday_bids:
            avg_prev = sum(yesterday_bids) / len(yesterday_bids)
            target_bid = max(DAILY_SALARY * 0.45, (highest_prev * 0.95 + avg_prev * 0.05) * scarcity_factor)
        else:
            target_bid = DAILY_SALARY * 0.5 * scarcity_factor

    # Ensure not to exceed budget and not less than 0
    target_bid = min(budget, target_bid)
    target_bid = max(0, target_bid)
    return target_bid
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Collect yesterday's bids from opponents that are alive
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])
    
    # Determine needed aggression
    if hp <= 2:
        # Desperate: bid high but not more than budget
        target = min(budget, DAILY_SALARY * 0.9)
    else:
        # Normal: use yesterday's bids to set a competitive bid
        if prev_bids:
            avg_prev = sum(prev_bids) / len(prev_bids)
            # Add a small margin to beat average
            target = avg_prev + 10
        else:
            # No info: default moderate
            target = DAILY_SALARY * 0.6
        # Adjust based on supply and hp
        if supply < WATER_REQ * 2 and hp > 3:
            target = max(target, DAILY_SALARY * 0.7)
        elif supply >= WATER_REQ * 3:
            target = min(target, DAILY_SALARY * 0.4)
        # Ensure not too high
        target = min(target, DAILY_SALARY * 0.95)
        target = max(target, DAILY_SALARY * 0.1)
    
    # Budget constraint
    bid = min(budget, target)
    # Ensure bid is non-negative float rounded to 2 decimals
    bid = max(0.0, round(bid, 2))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if not yesterday_bids:
        # fallback: bid proportional to desperation
        if hp <= 2 or no_water_days > 1:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.6)

    avg_opponent_bid = sum(yesterday_bids) / len(yesterday_bids)
    
    # Determine target bid based on desperation
    if hp <= 2 or no_water_days >= 1:
        # Need water urgently: bid just above average to ensure win
        target = avg_opponent_bid + 1.0
        # cap at budget and salary
        target = min(budget, target)
        return max(target, 1.0)
    elif hp <= 4:
        # Moderate need: slightly above average
        target = avg_opponent_bid + 0.5
        target = min(budget, target)
        return max(target, 1.0)
    else:
        # Healthy: save money, bid conservatively
        target = avg_opponent_bid * 0.8
        target = min(budget, target)
        return max(target, 1.0)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = int(day_context['supply'])  # ensure int
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    alive_opps = {oid: opp for oid, opp in opponents_status.items() if opp['alive']}
    
    # base bid: 50% of salary
    base = 0.5 * SALARY
    
    # urgency adjustments
    if no_water > 0 or hp <= 2:
        base = 0.9 * SALARY
    elif hp <= 4:
        base = 0.7 * SALARY
    
    # analyze yesterday's opponent behavior
    yesterday_bids = []
    for opp in alive_opps.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # if someone bid very high yesterday, they may be low on budget now; but be cautious
        if max_yesterday > 0.85 * SALARY:
            # if we are healthy, stick to moderate; else raise
            if hp > 4:
                base = min(base, 0.6 * SALARY)
            else:
                base = max(base, 0.8 * SALARY)
        else:
            # bid slightly above average to outbid typical
            avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
            base = max(base, avg_yesterday + 2.0)
    
    # ensure within budget and non-negative
    bid = max(0.0, min(budget, base))
    return bid
"""
