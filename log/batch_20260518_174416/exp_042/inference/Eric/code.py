# ============================================================
# Experiment: exp_042
# Agent: Eric
# Source: exp_042
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    salary = 140
    water_req = 8

    alive_opp = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opp:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    max_prev = max(prev_bids) if prev_bids else 0

    if hp <= 2:
        bid = min(budget, salary * 0.9)
    elif max_prev > 0 and max_prev >= salary * 0.85:
        if hp > 3:
            bid = min(budget, salary * 0.3)
        else:
            bid = min(budget, salary * 0.95)
    else:
        bid = min(budget, max(salary * 0.5, max_prev + 1.5))

    if supply < 18:
        bid = min(budget, max(bid, salary * 0.7))
    elif supply > 22:
        bid = min(budget, bid * 0.8)

    bid = max(0, bid)
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = day_context['supply']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0
    base_bid = DAILY_SALARY * 0.35
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.7
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.5
    if highest_prev_bid > DAILY_SALARY * 0.8:
        if my_status['hp'] > 3:
            base_bid = DAILY_SALARY * 0.3
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    elif highest_prev_bid > DAILY_SALARY * 0.5:
        base_bid = min(my_status['budget'], max(base_bid, highest_prev_bid + 1))
    bid = min(my_status['budget'], base_bid)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])

    # Estimate highest opponent bid today
    if prev_bids:
        max_prev = max(prev_bids)
        # Opponents may bid similarly or slightly lower, but Cindy might increase
        # Assume they might bid up to 1.2 * previous max
        estimated_opponent_max = max_prev * 1.2
    else:
        estimated_opponent_max = DAILY_SALARY * 0.6  # fallback

    # Base bid: need to secure water at reasonable price
    # If supply is low or we are dehydrated, bid higher
    if hp <= 2 or no_water_days >= 1:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.5)

    # Ensure we outbid estimated opponent max by a small margin if affordable
    target_bid = estimated_opponent_max + 1.0
    # But don't exceed budget or go too high
    bid = min(budget, max(base_bid, target_bid))

    # Safety: never bid more than daily salary * 1.0 unless desperate
    if hp > 2 and bid > DAILY_SALARY:
        bid = DAILY_SALARY
    # If desperate and budget allows, can exceed salary (but risky)
    if hp <= 2 and bid > DAILY_SALARY * 1.2:
        bid = DAILY_SALARY * 1.2

    return int(max(0.0, min(budget, bid)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if my_status['hp'] < 3:
            target = min(my_status['budget'], highest_prev + 5, DAILY_SALARY * 0.95)
        else:
            supply = day_context['supply']
            num_alive = len(alive_opponents) + 1
            avg_share = supply / num_alive
            if avg_share < WATER_REQ:
                target = min(my_status['budget'], highest_prev + 2, DAILY_SALARY * 0.9)
            else:
                target = min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev - 5))
    else:
        target = min(my_status['budget'], DAILY_SALARY * 0.6)
    return max(0, min(my_status['budget'], target))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from traces
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid from yesterday's competition
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
        # If yesterday had very high bids, we might back off if healthy
        if highest_yesterday >= DAILY_SALARY * 1.0:
            # Aggressive opponent: if we can afford, match or slightly above
            if hp <= 3 or no_water_days > 0:
                target = min(budget, highest_yesterday * 0.9)
            else:
                target = min(budget, DAILY_SALARY * 0.7)
            return max(1.0, target)
        else:
            # Moderate competition: try to slightly beat highest if needed
            if hp <= 2 or no_water_days >= 1:
                target = min(budget, max(DAILY_SALARY * 0.9, highest_yesterday + 5))
            else:
                target = min(budget, max(DAILY_SALARY * 0.5, highest_yesterday + 2))
            return max(1.0, target)
    else:
        # No trace info, fallback based on health
        if hp <= 2 or no_water_days > 0:
            return min(budget, DAILY_SALARY * 0.8)
        else:
            return min(budget, DAILY_SALARY * 0.4)
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Base bid: 50% of salary
    base = DAILY_SALARY * 0.5
    
    # Adjust for supply scarcity: less water available -> higher need
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    base += (1 - supply_ratio) * 20  # add up to 20 when supply low
    
    # Adjust for own health and dehydration
    if hp <= 2 or no_water_days >= 1:
        base += 30  # critical need
    elif hp <= 4:
        base += 15
    
    # Examine opponent traces for yesterday's high bids
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    high_bid_yesterday = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] >= DAILY_SALARY * 0.8:
                high_bid_yesterday = True
                break
    # If any opponent made a very high bid yesterday, they likely burned budget; bid less today
    if high_bid_yesterday and hp > 3:
        base -= 20
    
    # Ensure bid is within [0, budget]
    bid = max(0.0, min(budget, base))
    # Floor to avoid fractional cents? Not required, but can keep as is.
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

    # compute alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # no competition, minimal bid to win
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # base bid decision on my hp and yesterday's max bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
    else:
        max_prev = 0

    hp = my_status['hp']
    budget = my_status['budget']
    day = day_context['day']
    supply = day_context['supply']

    # urgency based on hp
    if hp <= 2:
        # must win - bid high but not exceeding budget
        target = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 5:
        # need water soon - bid moderately aggressive
        target = min(budget, max(DAILY_SALARY * 0.6, max_prev + 1.5))
    else:
        # healthy - conserve budget
        target = min(budget, max(DAILY_SALARY * 0.3, max_prev + 1.0))

    # ensure bid is not too low to risk losing when supply is low
    # but if supply is high, we might lower bid a bit
    # no strong correlation, keep target
    # ensure integer bid? bid is float, but we must avoid float indices in array
    # no array indices here, so fine
    return round(target, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Get yesterday's max bid among alive opponents
    yesterday_max_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])

    # Determine urgency based on HP and no_water_days
    urgency = 1.0
    if my_hp <= 3 or no_water_days >= 1:
        urgency = 2.0
    if my_hp <= 1 or no_water_days >= 2:
        urgency = 3.0

    # Base bid: proportional to supply and water requirement
    base_bid = (supply / WATER_REQ) * 1.2  # average unit cost needed
    target_bid = base_bid * urgency

    # If very urgent, use yesterday's max as a guide
    if urgency >= 2.0 and yesterday_max_bid > 0:
        target_bid = max(target_bid, yesterday_max_bid + 1.0)

    # Cap by budget and ensure minimum
    if my_hp <= 2 or no_water_days >= 2:
        target_bid = max(target_bid, DAILY_SALARY * 0.85)
    elif my_hp <= 5 or no_water_days >= 1:
        target_bid = max(target_bid, DAILY_SALARY * 0.5)
    else:
        target_bid = min(target_bid, DAILY_SALARY * 0.3)

    # Ensure not exceeding budget
    bid = min(my_budget, target_bid)
    # Ensure non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])  # ensure integer for index
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Collect previous bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(float(trace['bid']))
    
    # Base bid: moderate fraction of salary, adjusted by supply scarcity
    supply_ratio = supply / 25.0  # normalize between 0.6 and 1.0
    base_bid = DAILY_SALARY * (0.35 + 0.15 * (1 - supply_ratio))
    
    # Aggressive if HP very low
    if hp <= 2:
        target = max(base_bid, DAILY_SALARY * 0.9)
        if prev_bids:
            max_prev = max(prev_bids)
            target = max(target, max_prev + 1.0)
        return min(budget, target)
    
    # Standard: look at yesterday's top bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If Cindy's bid extremely high, avoid confrontation
        if max_prev >= DAILY_SALARY * 0.85:
            if hp > 5:
                return min(budget, base_bid * 0.6)
            else:
                return min(budget, max(base_bid, max_prev - 5.0))
        else:
            return min(budget, max(base_bid, max_prev + 2.0))
    
    # No previous data: use base
    return min(budget, base_bid)
"""
