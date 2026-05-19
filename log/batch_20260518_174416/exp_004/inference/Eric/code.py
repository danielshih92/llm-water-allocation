# ============================================================
# Experiment: exp_004
# Agent: Eric
# Source: exp_004
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    if hp <= 2:
        # Need water urgently
        bid = min(budget, DAILY_SALARY * 0.85)
    elif hp <= 4:
        # Moderate need
        bid = min(budget, DAILY_SALARY * 0.6)
    else:
        # Healthy, save money
        bid = min(budget, DAILY_SALARY * 0.4)
    
    # Ensure bid is non-negative and within supply*price? No price given; supply just influences total available water.
    # Adjust bid to not exceed budget, already done.
    return max(1, bid)  # Always bid at least 1 to have a chance
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Gather previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Determine opponent pressure
    high_pressure = any(bid > 200 for bid in prev_bids) if prev_bids else False
    
    # Base bid: 50% of salary, then adjust by supply
    # Supply range 15-25: lower supply -> higher bid needed
    # supply 15 => +20, supply 25 => -20
    base = DAILY_SALARY * 0.5  # 70
    supply_adjust = (20 - supply) * 2  # at supply=15, +10; at supply=25, -10
    base += supply_adjust
    
    # Opponent factor: if high pressure, reduce bid to conserve
    if high_pressure:
        base -= 15
    else:
        base += 5
    
    # Ensure not too low
    base = max(base, 20)
    
    # Urgency: if hp low, must win water
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    else:
        bid = min(budget, base)
    
    # Final check: do not exceed budget
    bid = min(bid, budget)
    # Ensure returning a number
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    yesterday_bids = []
    for opp in alive.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0

    # Low HP or desperate: bid high to secure water
    if hp <= 2 or no_water_days > 0:
        target_bid = min(budget, DAILY_SALARY * 1.1)
        return max(target_bid, 60.0)

    # Abundant water: bid less aggressively
    if supply >= 20:
        target_bid = min(budget, DAILY_SALARY * 0.7)
        return max(target_bid, 70.0)

    # Normal: outbid yesterday's highest by small margin
    base_bid = max(highest_prev + 2.0, DAILY_SALARY * 0.5)
    target_bid = min(budget, base_bid)
    return max(target_bid, 50.0)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Collect yesterday's bids from opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine a target bid based on yesterday's max or default
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If yesterday was very high, opponents might be aggressive; bid around 60% of salary
        if max_yesterday >= DAILY_SALARY * 0.9:
            target = min(DAILY_SALARY * 0.6, max_yesterday * 0.7)
        else:
            target = min(DAILY_SALARY * 0.55, max_yesterday * 0.8 + 5)
    else:
        target = DAILY_SALARY * 0.5
    
    # Adjust based on my HP
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 5:
        target = max(target, DAILY_SALARY * 0.65)
    
    # Ensure we don't go broke; leave some reserve for future days
    reserve = 10
    max_bid = max(0, my_status['budget'] - reserve)
    
    # Also consider supply: if supply low, bid higher
    supply = int(day_context['supply'])
    if supply < 18:
        target *= 1.2
    
    bid = min(target, max_bid)
    # Ensure minimum bid (can't be negative)
    bid = max(0, bid)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    water_need = my_status['hp'] < WATER_REQ * 2
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        base_bid = min(DAILY_SALARY * 1.3, max_prev + 2.0)
    else:
        base_bid = DAILY_SALARY * 0.8
    
    if my_status['hp'] <= 3:
        # desperate
        bid = min(my_status['budget'], base_bid * 1.3 + 5)
    elif my_status['hp'] >= 8:
        # safe
        bid = min(my_status['budget'], base_bid * 0.6)
    else:
        bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is positive and within budget
    bid = max(1, min(my_status['budget'], bid))
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine yesterday's max bid among alive opponents
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])

    # Base bid: need to secure water if low HP or several days without water
    survival_bid = DAILY_SALARY * 0.6  # start moderate
    if hp <= 2:
        survival_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        survival_bid = DAILY_SALARY * 0.75
    if no_water_days >= 2:
        survival_bid = DAILY_SALARY * 0.95

    # Adjust for supply: lower supply requires higher bid
    supply_factor = 1.0 + (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) * 0.4
    bid = survival_bid * supply_factor

    # Competition adjustment: outbid yesterday's max if needed
    expected_bid = max(yesterday_max_bid * 0.9 + 1.5, bid)  # slightly above their expected drop
    if expected_bid > DAILY_SALARY * 1.5:  # cap to avoid overspend
        expected_bid = DAILY_SALARY * 1.5

    # Ensure minimum bid to stay alive if HP low
    if hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.85)
    else:
        bid = max(bid, DAILY_SALARY * 0.3)

    # Final bid limited by budget
    final_bid = min(budget, round(expected_bid, 2))
    final_bid = max(final_bid, 0.01)
    return final_bid
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
    no_water = my_status['no_water_days']
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    base_bid = 0.0
    if prev_bids:
        max_prev = max(prev_bids)
        base_bid = max(max_prev + 1.0, DAILY_SALARY * 0.4)
    else:
        base_bid = DAILY_SALARY * 0.4
    # Adjust for urgency
    if hp <= 3 or no_water > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)
    if supply < 18:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)
    # Ensure we don't exceed budget
    bid = min(budget, base_bid)
    # Ensure non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water = my_status['no_water_days']
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Estimate opponent bids from yesterday
    prev_bids = []
    for o in alive_opponents.values():
        trace = o.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Danger threshold: if no water days or HP critical
    if my_hp <= 2 or no_water > 0:
        # Need water desperately, bid up to budget but not more than needed
        base_bid = min(my_budget, DAILY_SALARY * 0.9)
        if prev_bids:
            # Overbid highest previous by a small margin if affordable
            max_prev = max(prev_bids)
            return min(my_budget, max(base_bid, max_prev + 2.0))
        return base_bid
    
    # Normal situation: try to conserve
    if prev_bids:
        max_prev = max(prev_bids)
        # If supply is ample, bid low to save money
        if supply >= WATER_REQ * (1 + len(alive_opponents)):
            return min(my_budget, DAILY_SALARY * 0.3)
        else:
            # Need to compete; bid just above highest opponent to ensure win if possible
            target = max_prev + 1.5
            # Cap at budget
            return min(my_budget, target)
    else:
        # No history, base bid
        return min(my_budget, DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Get yesterday's max bid among alive opponents
    yesterday_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    
    max_prev = max(yesterday_bids) if yesterday_bids else 0
    
    # Base bid
    base = DAILY_SALARY * 0.5
    
    # Urgency: if no water more than 1 day, need water
    if my_status['no_water_days'] >= 1:
        # Must win, bid higher than yesterday's max
        target = max_prev + 1.0
        # But cap at budget
        return min(my_status['budget'], max(target, base * 0.9))
    else:
        # If we have water, be conservative unless yesterday was very high
        if max_prev >= DAILY_SALARY * 0.8:
            # Avoid overpaying, bid just below yesterday's max if we don't need water
            return min(my_status['budget'], max_prev * 0.95)
        else:
            # Moderate bid
            return min(my_status['budget'], max(base, max_prev + 0.5))
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
    my_hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Determine number of winners possible
    num_winners = int(supply // WATER_REQ)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate opponent aggression from yesterday's max
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
    else:
        highest_prev = DAILY_SALARY * 0.5  # default guess

    # Base bid strategy
    if my_hp <= 2 or no_water_days >= 2:
        # desperate: need water
        target = min(budget, max(DAILY_SALARY * 0.9, highest_prev + 5.0))
    elif my_hp <= 4:
        # cautious: aim to win if supply allows
        if num_winners >= len(alive_opponents):
            # plenty of water, bid low to save
            target = min(budget, DAILY_SALARY * 0.25)
        else:
            target = min(budget, max(DAILY_SALARY * 0.5, highest_prev * 0.9))
    else:
        # healthy: try to win cheap or skip
        if num_winners >= 3:
            target = min(budget, DAILY_SALARY * 0.2)
        else:
            target = min(budget, max(DAILY_SALARY * 0.3, highest_prev * 0.7))

    # Ensure we don't bid more than budget
    return max(0, min(budget, target))
"""
