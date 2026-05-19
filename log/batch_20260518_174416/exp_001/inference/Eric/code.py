# ============================================================
# Experiment: exp_001
# Agent: Eric
# Source: exp_001
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    SUPPLY = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Check yesterday's bids if available
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If they were aggressive yesterday, we may need to outbid or conserve
        if highest_prev >= DAILY_SALARY * 0.85:
            if hp > 3:
                bid = min(budget, DAILY_SALARY * 0.35)
            else:
                bid = min(budget, DAILY_SALARY * 0.9)
        else:
            # Underbid slightly or match
            target = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
            bid = min(budget, target)
    else:
        # No history: use HP-based logic
        if hp <= 2 or no_water_days >= 2:
            bid = min(budget, DAILY_SALARY * 0.85)
        elif hp <= 4:
            bid = min(budget, DAILY_SALARY * 0.6)
        else:
            # Healthy: bid moderate to conserve budget
            bid = min(budget, DAILY_SALARY * 0.45)

    # Ensure bid is at least 1 (minimum sensible bid)
    bid = max(1, bid)
    # Avoid exceeding budget
    bid = min(bid, budget)
    return bid
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
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    supply = day_context['supply']
    day = day_context['day']
    
    # Determine baseline bid based on supply and day
    # As supply increases, water is cheaper; early days bid lower
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # Base bid: linear from 50% to 70% of salary
    base_bid = DAILY_SALARY * (0.5 + 0.2 * supply_ratio)
    
    # Look at previous traces of opponents
    # We only care about the maximum previous bid among alive opponents
    max_prev_bid = 0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev:
                # Ensure bid is a number
                if prev['bid'] is not None:
                    max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # Adjust based on last round's aggression
    # If someone bid very high last day, they might be desperate or bluffing
    # We avoid high bids unless we are desperate
    if max_prev_bid > DAILY_SALARY * 0.85:
        # Opponents aggressive, but we can try to save if we have high HP
        if my_hp > 6:
            bid = min(my_budget, base_bid * 0.8)
        else:
            bid = min(my_budget, base_bid * 1.2)
    else:
        # Moderate opposition
        bid = base_bid
    
    # Ensure we don't spend all budget early
    # If many days left, conserve
    if day <= 3:
        bid = min(bid, DAILY_SALARY * 0.5)
    
    # Critical low HP: must win
    if my_hp <= 3:
        bid = min(my_budget, DAILY_SALARY * 0.9)
    elif my_hp <= 1:
        bid = min(my_budget, DAILY_SALARY * 0.95)
    
    # Ensure bid is within budget and non-negative
    bid = max(0, min(my_budget, bid))
    
    # Special: if no water days > 1, increase bid
    if my_status['no_water_days'] >= 2:
        bid = min(my_budget, DAILY_SALARY * 0.85)
    
    # Return integer bid (round to 2 decimals for realism? but function expects number)
    return int(round(bid, 2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Baseline bid: moderate to compete
    base_bid = min(my_status['budget'], 0.5 * DAILY_SALARY)
    
    # Increase if we are dehydrated or low HP
    if my_status['hp'] <= 2:
        urgency = 0.9
    elif my_status['hp'] <= 4:
        urgency = 0.7
    else:
        urgency = 0.5
    
    # Adjust for competition: more opponents -> bid higher
    if num_alive >= 3:
        multiplier = 1.2
    elif num_alive == 2:
        multiplier = 1.1
    else:
        multiplier = 1.0
    
    # Final bid, cap at budget
    bid = min(my_status['budget'], base_bid * multiplier * (1 + 0.2 * (WATER_REQ / 10)))
    # Ensure bid is at least 1 (or 0 if budget is 0)
    bid = max(0, bid)
    # Use int conversion for safety (although bid is numeric)
    return int(bid) if bid > 0 else 0
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Desperation factor based on HP and dehydration
    if hp <= 1 or no_water_days >= 2:
        desperation = 1.2
    elif no_water_days > 0 or hp <= 3:
        desperation = 1.0
    else:
        desperation = 0.6
    
    # Water ratio: how much of supply we need
    water_ratio = WATER_REQ / supply
    
    # Base bid: proportional to salary scaled by ratio and tuned
    base_bid = DAILY_SALARY * water_ratio * 1.3
    
    # Adjust by desperation and cap at budget
    bid = min(budget, base_bid * desperation)
    
    # Ensure at least 1 to participate
    bid = max(1, bid)
    
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    no_water = my_status['no_water_days']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    highest_prev = max(prev_bids) if prev_bids else 0
    if prev_bids:
        target = highest_prev + 1.0
    else:
        target = DAILY_SALARY * 0.6
    if no_water > 0:
        target *= 1.25
    elif hp <= 3:
        target *= 1.2
    elif hp <= 5:
        target *= 1.1
    if supply < 20:
        target *= 1.15
    bid = max(
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Get yesterday's max bid from alive opponents
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    if prev_bids:
        max_prev = max(prev_bids)
        target = max_prev + 2.0  # slight overcut
    else:
        target = DAILY_SALARY * 0.7
    
    # Safety: ensure at least moderate bid if HP low
    hp = my_status['hp']
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.75)
    
    # Cap by budget and range
    bid = min(my_status['budget'], target)
    bid = max(bid, DAILY_SALARY * 0.3)  # floor
    
    # Ensure bid is a number (float ok)
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Determine target bid based on health and water needs
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        target = max(DAILY_SALARY * 0.95, max_prev_bid + 1.5)
    else:
        target = max(DAILY_SALARY * 0.6, max_prev_bid + 0.5)
    
    return min(my_status['budget'], target)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    water_req = 8
    daily_salary = 140
    supply = int(day_context['supply'])
    day = day_context['day']

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}

    # Determine if I need water urgently
    need_water = (hp <= 2) or (no_water_days >= 1 and hp <= 4)

    # Predict each opponent's likely bid based on trace and desperation
    predicted_bids = []
    for aid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        last_bid = prev.get('bid', 0) if prev else 0
        opp_hp = opp['hp']
        opp_budget = opp['budget']
        # Estimate desperation: lower HP or high budget -> higher bid
        if opp_hp <= 2:
            desperation_mult = 1.3
        elif opp_hp <= 4:
            desperation_mult = 1.15
        else:
            desperation_mult = 1.0
        # Also consider their salary
        opp_salary = opp.get('daily_salary', 70)
        # If they have plenty budget, they might bid more
        if opp_budget > daily_salary * 2:
            budget_factor = 1.1
        else:
            budget_factor = 1.0
        # Predicted bid is last bid adjusted
        pred = last_bid * desperation_mult * budget_factor
        # Ensure it's within reasonable bounds (0 to their budget? we don't know)
        # but we can cap at opp_budget (we don't know their current budget? actually we do from opp['budget'])
        pred = min(pred, opp_budget)
        predicted_bids.append(pred)

    # Add my own safe bid if needed
    if not predicted_bids:
        # no alive opponents, just ensure water
        if need_water:
            return min(budget, daily_salary * 0.6)
        else:
            return min(budget, 1.0)

    max_pred = max(predicted_bids)

    if need_water:
        # Bid slightly above the highest predicted bid, but not more than my budget
        bid = max_pred + 2.0
        # If I'm very desperate, go higher
        if hp <= 1:
            bid = max(max_pred + 5.0, daily_salary * 0.9)
        # Cap at budget
        bid = min(bid, budget)
        # Also ensure not to bid more than I can afford to lose if I lose (but we need water)
        return bid
    else:
        # If I don't need water, bid low to save money
        # But I might want to bluff occasionally? Not needed.
        return min(budget, 1.0)
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Number of full water units available today
    water_units = int(supply // WATER_REQ)

    # Filter alive opponents
    alive = {oid: o for oid, o in opponents_status.items() if o['alive']}

    # If no opponents alive, bid minimal
    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate opponent target: highest yesterday + small bump
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        target = max_prev + 1.5  # small edge
    else:
        target = DAILY_SALARY * 0.75  # fallback

    # Urgency based on HP and no_water_days
    if hp <= 0:
        # Dying, must win water
        return min(budget, target + 5)
    if no_water_days >= 2:
        # Dehydrated, need water soon
        urgency_factor = 1.2
    elif hp <= 2:
        urgency_factor = 1.1
    else:
        urgency_factor = 0.9

    # Base bid: target times urgency, but not exceed budget and not too high
    bid = min(budget, target * urgency_factor)
    if bid < 0:
        bid = 0

    # If many water units, we can be more conservative
    if water_units >= len(alive) + 1:  # enough for all plus us
        bid = min(bid, DAILY_SALARY * 0.5)

    # If few units and others bid high, we must go high
    if water_units == 1 and yesterday_bids and max(yesterday_bids) > DAILY_SALARY * 0.8:
        bid = min(budget, target + 10)

    return max(0, bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max = max(yesterday_max, prev['bid'])
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    if yesterday_max == 0:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.5)
    else:
        if hp <= 2:
            bid = min(budget, max(DAILY_SALARY * 0.9, yesterday_max + 1.5))
        else:
            bid = min(budget, max(DAILY_SALARY * 0.5, yesterday_max + 0.5))
        if supply >= 22:
            bid = bid * 0.9
        return min(bid, budget)
"""
