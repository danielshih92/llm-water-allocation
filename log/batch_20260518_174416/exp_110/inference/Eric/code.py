# ============================================================
# Experiment: exp_110
# Agent: Eric
# Source: exp_110
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Day 1: No previous trace
    if day_context['day'] == 1:
        if my_status['hp'] <= 2:
            bid = min(my_status['budget'], DAILY_SALARY * 0.85)
        elif my_status['hp'] <= 4:
            bid = min(my_status['budget'], DAILY_SALARY * 0.6)
        else:
            bid = min(my_status['budget'], DAILY_SALARY * 0.4)
        return max(0, bid)
    
    # Gather yesterday's opponent bids from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid according to own need and supply
    supply = day_context['supply']
    # Low supply -> higher competition
    if supply < 20:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.45
    
    # Adjust for HP
    if my_status['hp'] <= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 4:
        base = max(base, DAILY_SALARY * 0.6)
    
    # If yesterday opponents were aggressive, respond
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone was very desperate yesterday, they might be again
        if highest_prev > DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                # We can be safe and lower
                bid = min(my_status['budget'], base * 0.8)
            else:
                # We need to compete
                target = max(base, highest_prev * 0.95)
                bid = min(my_status['budget'], target)
        else:
            # Normal: set bid slightly above the highest if we need water
            if my_status['hp'] <= 3:
                bid = min(my_status['budget'], max(base, highest_prev + 2.0))
            else:
                bid = min(my_status['budget'], base)
    else:
        bid = min(my_status['budget'], base)
    
    # Ensure we do not bid more than we have
    return max(0, bid)
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
    supply = int(day_context['supply'])  # ensure integer
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # yesterday's max bid from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    max_prev_bid = max(prev_bids) if prev_bids else 0
    
    # Base bid fraction based on supply tightness
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 (tight) to 1 (plenty)
    if my_status['no_water_days'] >= 2 or my_status['hp'] <= 2:
        # desperate: bid high to get water
        base_frac = 0.7
    else:
        # normal: scale from 0.3 to 0.5 based on supply
        base_frac = 0.3 + 0.2 * (1 - supply_ratio)
    
    tentative_bid = DAILY_SALARY * base_frac
    
    # If yesterday someone bid very high (>= 0.8*daily_salary), reduce bid to avoid overpaying
    if max_prev_bid >= 0.8 * DAILY_SALARY and my_status['hp'] > 3:
        tentative_bid = min(tentative_bid, DAILY_SALARY * 0.4)
    
    # Ensure we don't bid more than budget
    bid = min(my_status['budget'], max(0, tentative_bid))
    return bid
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_max_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])

    # Determine desperation
    desperate = (hp <= 2) or (no_water_days >= 2)

    if desperate:
        # Need water badly, bid high to beat last max or salary proportion
        base_bid = max(DAILY_SALARY * 0.9, yesterday_max_bid + 0.5)
    else:
        # Conserve budget, modest bid depending on supply
        if supply >= 20:
            base_bid = DAILY_SALARY * 0.5
        elif supply >= 17:
            base_bid = DAILY_SALARY * 0.6
        else:
            base_bid = DAILY_SALARY * 0.7

    bid = min(budget, base_bid)
    # Ensure non-negative and within reasonable bounds
    bid = max(1.0, bid)
    return bid
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {uid: opp for uid, opp in opponents_status.items() if opp['alive']}
    
    # Extract yesterday's bids from previous_trace
    prev_bids = []
    for uid, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid calculation
    if not prev_bids:
        # No historical data, use default strategy
        if hp <= 2 or no_water_days > 0:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
    else:
        max_prev = max(prev_bids)
        # If previous max was very high, opponent might be aggressive; adapt
        if max_prev >= DAILY_SALARY * 0.85:
            if hp > 3:
                bid = min(budget, DAILY_SALARY * 0.3)
            else:
                bid = min(budget, max_prev + 1.0)
        else:
            # Moderate opponent; bid slightly above max_prev if needed
            target = max_prev + 1.5
            # Adjust based on supply scarcity
            supply_factor = (supply - 15) / 10.0  # 0..1
            # low supply => more aggressive
            if hp <= 2 or no_water_days > 0:
                urgency = 1.2
            else:
                urgency = 0.8
            bid = min(budget, max(DAILY_SALARY * 0.5, target * urgency))
    
    # Ensure bid is within budget and non-negative
    bid = max(0, min(budget, bid))
    # Extra: if supply is very high and we have plenty HP, bid low
    if supply >= 22 and hp > 5:
        bid = min(budget, DAILY_SALARY * 0.2)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure int
    
    # Base bid: half salary, adjusted by supply ratio
    base_bid = DAILY_SALARY * 0.5 * (supply / 20.0)  # normalize supply (midpoint 20)
    
    # Get previous max bid from alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    if prev_bids:
        max_prev = max(prev_bids)
        # If opponent was aggressive, increase bid
        if max_prev > DAILY_SALARY * 0.8:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
        # If there are many opponents, increase a bit
        if len(prev_bids) >= 3:
            base_bid *= 1.2
    
    # Adjust based on my health
    hp = my_status['hp']
    if hp <= 2:
        # Desperate: bid high to survive
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.9)
    elif hp >= 8:
        # Safe: conserve budget
        final_bid = min(my_status['budget'], base_bid * 0.7)
    else:
        final_bid = min(my_status['budget'], base_bid)
    
    # Ensure non-negative and within budget
    final_bid = max(0.0, min(my_status['budget'], final_bid))
    return final_bid
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
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        bid = trace.get('bid')
        if bid is not None and isinstance(bid, (int, float)):
            prev_bids.append(bid)
    
    # Base bid as percentage of daily salary
    base_bid = DAILY_SALARY * 0.45  # ~63
    
    # Adjust based on our health
    hp = my_status['hp']
    if hp <= 2:
        # Desperate: need water
        target_bid = DAILY_SALARY * 0.85  # ~119
    elif hp <= 4:
        target_bid = DAILY_SALARY * 0.65  # ~91
    else:
        target_bid = base_bid
    
    # React to yesterday's highest bid
    if prev_bids:
        highest_prev = max(prev_bids)
        if my_status['hp'] <= 3:
            # If we need water, try to outbid slightly above highest
            target_bid = max(target_bid, highest_prev + 1.0)
        else:
            # If healthy, undercut to save budget
            target_bid = min(target_bid, highest_prev - 2.0)
    
    # Ensure bid is at least a small amount (0.01) and within budget
    final_bid = max(0.01, min(my_status['budget'], target_bid))
    
    # Sanity: don't exceed daily salary too much (though budget may be larger)
    final_bid = min(final_bid, DAILY_SALARY * 0.9)
    
    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.6)

    # Get yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])

    # Determine base bid
    if hp <= 2 or my_status.get('no_water_days', 0) >= 2:
        # desparate
        bid = min(budget, DAILY_SALARY * 0.85)
    else:
        # healthy
        if prev_bids:
            max_prev = max(prev_bids)
            # Beat the highest previous bid by a small margin if we can afford
            target = max_prev + 1.0
            # But do not overpay
            bid = min(budget, max(DAILY_SALARY * 0.4, target))
        else:
            bid = min(budget, DAILY_SALARY * 0.55)

    # Ensure bid is at least 1 if we have budget
    bid = min(bid, budget - 0.01) if budget > 0 else 0.0
    bid = max(bid, 0.0)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k:v for k,v in opponents_status.items() if v['alive']}
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0
    
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Determine bid based on urgency
    if hp <= 3 or no_water_days >= 2:
        # Need water urgently
        target_bid = max(DAILY_SALARY * 0.7, max_yesterday + 2.0)
    else:
        # Can be conservative
        target_bid = max(DAILY_SALARY * 0.4, max_yesterday * 0.6)
    
    # Adjust for supply: if high supply, lower bid; if low, raise
    if supply >= 20:
        target_bid *= 0.85
    elif supply <= 16:
        target_bid *= 1.15
    
    # Ensure within budget
    bid = min(budget, target_bid)
    
    # Floor at 0.1 to avoid zero bids (risk of no water)
    bid = max(0.1, bid)
    
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            yesterday_bids.append(trace['bid'])

    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.55

    if supply < 18:
        base_bid *= 1.2
    elif supply > 22:
        base_bid *= 0.8

    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        min_yesterday = min(yesterday_bids)
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
        if max_yesterday > DAILY_SALARY * 1.0:
            base_bid = min(base_bid, avg_yesterday * 0.8)
        else:
            base_bid = max(base_bid, avg_yesterday + 1.0)

    bid = min(budget, max(0, base_bid))
    return float(bid)
"""
