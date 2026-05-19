# ============================================================
# Experiment: exp_097
# Agent: Eric
# Source: exp_097
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAY = int(day_context['day'])
    SUPPLY = int(day_context['supply'])
    HP = my_status['hp']
    BUDGET = my_status['budget']
    NO_WATER = my_status['no_water_days']
    
    # Constants
    DAILY_SALARY = 140
    WATER_REQ = 8
    MAX_DAYS = 10
    
    # Determine urgency based on remaining days and health
    days_left = MAX_DAYS - DAY
    
    # Base bid: proportional to salary, with urgency multiplier
    if NO_WATER > 1:
        # Danger zone: must win water today
        base_bid = DAILY_SALARY * 0.9
    elif HP < 3:
        base_bid = DAILY_SALARY * 0.7
    elif days_left <= 2:
        # Endgame: secure water to survive
        base_bid = DAILY_SALARY * 0.65
    else:
        # Early or safe: low bid to save money
        base_bid = DAILY_SALARY * 0.4
    
    # Ensure we don't spend more than budget
    bid = min(BUDGET, base_bid)
    
    # Add a small random factor to avoid ties? Not needed, but can adjust
    # Keep bid as float
    return round(bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Extract yesterday's bids from opponents who have previous_trace
    yesterday_bids = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: if healthy, bid moderately; if thirsty, bid high
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Determine a target bid from yesterday's pressure
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        high_prev = max(yesterday_bids)
    else:
        avg_prev = DAILY_SALARY * 0.5
        high_prev = DAILY_SALARY * 0.5
    
    # Adjust based on my health
    if hp <= 3:
        # Desperate: outbid yesterday's high
        target = max(high_prev + 1, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # Moderate: slightly above average
        target = max(avg_prev + 1, DAILY_SALARY * 0.6)
    else:
        # Healthy: conserve money
        target = min(avg_prev, DAILY_SALARY * 0.5)
    
    # Ensure within budget and reasonable limit
    bid = min(budget, target)
    # Also ensure we don't bid more than necessary if supply is plentiful
    supply = day_context['supply']
    if supply >= 20 and hp > 4:
        bid = min(bid, DAILY_SALARY * 0.4)
    
    # Never bid more than budget
    bid = max(0, min(budget, bid))
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from alive opponents, but ignore Cindy if she is too high
    yesterday_bids = []
    for opp_id, opp in alive.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if not yesterday_bids:
        # no info, default moderate
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.85)
        return min(my_status['budget'], DAILY_SALARY * 0.55)
    
    # Separate high and low bidders
    high_bids = [b for b in yesterday_bids if b >= 100]
    low_bids = [b for b in yesterday_bids if b < 100]
    
    if high_bids:
        # Avoid high competition: bid around 70th percentile of low bids or moderate
        if low_bids:
            target = max(low_bids) * 0.85 + 2
        else:
            target = DAILY_SALARY * 0.5
    else:
        # No high bidders, bid slightly above max yesterday among low bids
        target = max(yesterday_bids) + 2.5
    
    # Scale by urgency
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.75)
    elif my_status['hp'] <= 4:
        target = max(target, DAILY_SALARY * 0.5)
    else:
        target = min(target, DAILY_SALARY * 0.6)
    
    # Ensure within budget and reasonable
    bid = max(DAILY_SALARY * 0.35, min(my_status['budget'], target, DAILY_SALARY * 0.95))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's bids from traces
    yesterday_bids = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace')
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if day == 1 or not yesterday_bids:
        # First day or no data: bid based on supply scarcity
        scarcity_factor = max(0.3, 1.0 - (supply - 15) / 10.0)
        base_bid = DAILY_SALARY * scarcity_factor
        if hp <= 3:
            base_bid = DAILY_SALARY * 0.9
        return min(budget, max(base_bid, 1))
    
    # Have yesterday bids
    max_prev = max(yesterday_bids)
    # Aggressive threshold: if someone bid very high, they might be desperate or bluffing
    aggressive_threshold = DAILY_SALARY * 0.85
    
    if max_prev >= aggressive_threshold:
        # Opponents were aggressive; if we are healthy, undercut to save budget
        if hp > 4:
            return min(budget, DAILY_SALARY * 0.4)
        else:
            # Need water badly, match or slightly above
            return min(budget, max(DAILY_SALARY * 0.85, max_prev + 1))
    else:
        # Opponents were moderate; try to outbid slightly
        target = max(DAILY_SALARY * 0.45, max_prev + 1.5)
        if hp <= 2:
            target = max(target, DAILY_SALARY * 0.85)
        return min(budget, target)
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

    # Collect yesterday's bids
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    from math import floor

    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = int(day_context['supply'])  # ensure int
    day = int(day_context['day'])
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water = int(my_status['no_water_days'])

    # desperation factor: low hp or no water days -> want water
    desperation = 0.0
    if my_hp <= 2:
        desperation = 1.0
    elif my_hp <= 4:
        desperation = 0.8
    elif my_no_water > 0:
        desperation = 0.6
    else:
        desperation = 0.3

    # gather yesterday bids from opponents
    prev_bids = []
    for opp_id, opp in opponents_status.items():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(float(trace['bid']))

    # estimate opponents' likely bid today
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
        # aggressive opponents: they might bid around their previous high
        likely_opp_bid = max(highest_prev, avg_prev * 1.1)
    else:
        # first day: assume they bid around 0.5 * DAILY_SALARY
        likely_opp_bid = 0.5 * DAILY_SALARY

    # my target bid: need water -> slightly above likely_opp_bid, else below
    if desperation > 0.7:
        target_bid = min(my_budget, likely_opp_bid + (1 + desperation) * 3)
    elif desperation > 0.4:
        target_bid = min(my_budget, likely_opp_bid * 0.9)
    else:
        # conserve budget: bid low
        target_bid = min(my_budget, DAILY_SALARY * 0.25)

    # ensure bid at least 0 and within budget
    target_bid = max(0.0, min(my_budget, target_bid))

    # safety: if budget is very high, consider not overbidding too much
    # but we rely on logic above

    return target_bid
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
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    max_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('bid') > max_prev_bid:
            max_prev_bid = float(prev['bid'])

    # Determine need for water
    urgent = hp <= 3 or no_water_days >= 2

    if urgent:
        # Bid moderately above highest previous bid
        target = max_prev_bid + 5.0
        # Also consider that we may need to outbid a very high bidder like Cindy
        if max_prev_bid >= 100:
            target = max_prev_bid + 2.0
        # Cap at budget and a reasonable max
        bid = min(budget, max(target, DAILY_SALARY * 1.1))
    else:
        # Not urgent: bid low to save budget, but ensure minimal chance of winning
        bid = min(budget, 45.0)
        # If yesterday's max_prev_bid was very low, we can even bid lower
        if max_prev_bid > 0 and max_prev_bid < 30:
            bid = min(budget, 25.0)

    # Ensure we never go negative and stay within budget
    bid = max(0.0, min(bid, budget))
    return bid
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
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    # collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    # base bid
    if hp <= 2 or no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    # adjust based on previous bids
    if prev_bids:
        highest_prev = max(prev_bids)
        # if we need water, outbid highest by 1 to stay alive
        if hp <= 3 or no_water_days > 0:
            target = highest_prev + 1.0
        else:
            target = max(base_bid, highest_prev * 0.8)
        # but do not exceed budget or go crazy
        final_bid = min(budget, target)
        # also ensure at least base_bid if we are desperate
        if hp <= 2 and final_bid < base_bid:
            final_bid = min(budget, base_bid)
        return int(final_bid * 10) / 10.0  # round to 1 decimal
    else:
        # no previous data: use base bid with supply adjustment
        supply_factor = max(0.3, 1.0 - (supply - 15) / 10.0)
        adjusted_base = base_bid * (1.0 + supply_factor * 0.3)
        if hp <= 3:
            adjusted_base = max(adjusted_base, DAILY_SALARY * 0.8)
        return min(budget, int(adjusted_base * 10) / 10.0)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Determine alive opponents
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    
    # If no alive opponents, bid minimum to survive
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)
    
    # Gather previous day's opponent bids from traces
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace:
            prev_bids.append(trace['bid'])
    
    # Base bid calculation
    base_bid = DAILY_SALARY * 0.6  # moderate first day
    
    if day == 1:
        # First day: be conservative
        bid = min(my_budget, base_bid)
    else:
        if prev_bids:
            max_prev_bid = max(prev_bids)
            avg_prev_bid = sum(prev_bids) / len(prev_bids)
            # Emergency: if we are close to death
            if my_hp <= 1 or no_water_days >= 2:
                bid = min(my_budget, DAILY_SALARY * 0.95)
            elif max_prev_bid > DAILY_SALARY * 0.85:
                # Opponents aggressive yesterday: adjust high to outbid
                target = max(avg_prev_bid + 2, DAILY_SALARY * 0.5)
                bid = min(my_budget, min(target, DAILY_SALARY * 0.9))
            else:
                # Normal: slightly above yesterday's high
                target = max(max_prev_bid + 1, DAILY_SALARY * 0.4)
                bid = min(my_budget, target)
        else:
            # No previous bids, use moderate bid
            bid = min(my_budget, DAILY_SALARY * 0.6)
    
    # Ensure bid is non-negative and at least 0 if budget allows
    bid = max(0, bid)
    # Cap bid to budget
    bid = min(bid, my_budget)
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine target bid
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        target = max(DAILY_SALARY * 0.5, highest_prev + 1.0)
    else:
        target = DAILY_SALARY * 0.5
    
    # Adjust based on personal state
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.85)
    if my_status['no_water_days'] >= 1:
        target = max(target, DAILY_SALARY * 0.7)
    
    # Cap by budget and daily salary
    bid = min(my_status['budget'], target, DAILY_SALARY * 0.9)
    
    # Ensure at least minimal bid to potentially win water if desperate
    if my_status['hp'] <= 2 and bid < DAILY_SALARY * 0.3:
        bid = min(my_status['budget'], DAILY_SALARY * 0.3)
    
    return max(0.0, bid)
"""
