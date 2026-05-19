# ============================================================
# Experiment: exp_084
# Agent: Eric
# Source: exp_084
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    # Check previous_trace if any (but empty now)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    
    if no_water > 0:
        # Desperate: need water
        base_bid = DAILY_SALARY * 0.9
        if hp <= 2:
            base_bid = DAILY_SALARY * 0.95
        return min(budget, base_bid)
    else:
        if hp <= 3:
            # Still vulnerable
            base_bid = DAILY_SALARY * 0.7
        else:
            base_bid = DAILY_SALARY * 0.5
        # Adjust if others bid high in previous trace
        if prev_bids:
            max_prev = max(prev_bids)
            if max_prev > DAILY_SALARY * 0.75:
                base_bid = max(base_bid, max_prev * 1.05)
        return min(budget, base_bid)
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
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    water_req = 8
    daily_salary = 140.0
    
    # Base bid strategy
    if hp <= 2:
        base_bid = 120.0
    elif hp <= 4:
        base_bid = 100.0
    elif hp <= 6:
        base_bid = 90.0
    else:
        base_bid = 80.0
    
    # Day factor: last 3 days increase bid
    if day >= 7:
        factor = 1.3
    elif day >= 4:
        factor = 1.15
    else:
        factor = 1.0
    
    bid = min(budget, base_bid * factor)
    
    # Ensure bid doesn't exceed daily_salary to save budget for future
    bid = min(bid, daily_salary * 0.95)
    
    # Lower bound: at least daily_salary * 0.4 to compete
    bid = max(bid, daily_salary * 0.4)
    
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Highest previous bid among alive opponents
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # if supply is low or hp critical, bid aggressively
        if supply < WATER_REQ * 2 or my_hp <= 2:
            target = min(my_budget, max(highest_prev + 2.0, DAILY_SALARY * 0.85))
        else:
            target = min(my_budget, max(highest_prev + 1.0, DAILY_SALARY * 0.5))
    else:
        if my_hp <= 2:
            target = min(my_budget, DAILY_SALARY * 0.9)
        else:
            target = min(my_budget, DAILY_SALARY * 0.55)

    # ensure bid is at least something reasonable but not waste
    bid = max(target, 0.0)
    bid = min(bid, my_budget, DAILY_SALARY)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # gather last bids from previous_trace
    last_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            last_bids.append(prev['bid'])

    # base bid strategy
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # emergency if low hp or multiple days without water
    if hp <= 2 or no_water_days >= 2:
        emergency_bid = min(budget, DAILY_SALARY * 0.9)
        return emergency_bid

    # determine a safe bid: above last average max if needed
    if last_bids:
        max_last = max(last_bids)
        # if we have good hp, try to undercut
        if hp > 5:
            target = max(DAILY_SALARY * 0.3, max_last + 0.5)
        else:
            target = max(DAILY_SALARY * 0.5, max_last + 1.0)
    else:
        target = DAILY_SALARY * 0.5

    # cap by budget and ensure we don't overspend unnecessarily
    bid = min(budget, target)
    # floor to 2 decimal places to avoid float issues
    bid = float(int(bid * 100)) / 100.0
    return bid
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
    
    alive = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0
    hp = my_status['hp']
    budget = my_status['budget']
    days_left = 10 - day_context['day']  # approximate
    
    # If HP critical and days left, bid high
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.95)
    # If HP moderate, outbid yesterday's max slightly
    elif hp <= 5:
        target = max(DAILY_SALARY * 0.5, max_yesterday + 1)
        return min(budget, target)
    else:
        # HP comfortable -> be conservative, bid just enough if supply is low
        supply = day_context['supply']
        need_bid = DAILY_SALARY * 0.3
        if supply < 18:
            need_bid = DAILY_SALARY * 0.5
        # Only increase if yesterday's max was near salary
        if max_yesterday > DAILY_SALARY * 0.8:
            need_bid = max(need_bid, max_yesterday + 2)
        return min(budget, need_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Base bid: aim for 70% of salary, adjusted by supply pressure
    # Low supply -> higher bid, high supply -> lower bid
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 when min, 1 when max
    base_bid = DAILY_SALARY * (0.75 - 0.2 * supply_ratio)
    
    # Urgency based on HP: bid more if hp low
    if hp <= 3:
        urgency_bonus = DAILY_SALARY * 0.2
    elif hp <= 5:
        urgency_bonus = DAILY_SALARY * 0.1
    else:
        urgency_bonus = 0
    
    bid = base_bid + urgency_bonus
    
    # Clamp to reasonable range and budget
    bid = max(60, min(bid, budget))
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    
    # if desperate or low HP, bid to win
    if no_water_days > 0 or hp <= 2:
        target_bid = min(budget, max(DAILY_SALARY * 0.9, max_prev_bid + 1.0))
    else:
        # healthy: try to conserve, but not too low if supply is low
        if supply <= 18:
            target_bid = min(budget, max(DAILY_SALARY * 0.6, max_prev_bid + 0.5))
        else:
            target_bid = min(budget, DAILY_SALARY * 0.5)
    # ensure at least a small positive bid if budget allows
    if budget > 0 and target_bid <= 0:
        target_bid = 1.0
    return min(budget, target_bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # base bid: half salary
    base_bid = min(budget, DAILY_SALARY * 0.5)

    # urgency based on hp and no_water_days
    if hp <= 2 or no_water_days >= 1:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base_bid = min(budget, DAILY_SALARY * 0.7)

    # gather yesterday's bids from alive opponents
    max_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])

    # adjust based on aggression from yesterday
    if max_prev_bid > 0:
        # if they were aggressive, we may need to raise to compete
        # but we don't want to overpay if we are healthy
        if hp <= 3:
            aggressive_bid = min(budget, max_prev_bid + 1.5)
            base_bid = max(base_bid, aggressive_bid)
        else:
            # if we are healthy, we can still try to outbid slightly if necessary
            if max_prev_bid > base_bid:
                # try to beat by small margin
                base_bid = min(budget, max_prev_bid + 1.5)

    # supply adjustment: lower supply increases need
    if supply < 18:
        base_bid = min(budget, base_bid * 1.2)
    elif supply > 22:
        base_bid = min(budget, base_bid * 0.8)

    # ensure we don't exceed budget and don't bid zero if we need water
    if hp <= 3 and no_water_days > 0:
        base_bid = max(base_bid, min(budget, DAILY_SALARY * 0.8))

    return min(budget, max(0, base_bid))
"""
