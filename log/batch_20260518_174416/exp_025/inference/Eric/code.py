# ============================================================
# Experiment: exp_025
# Agent: Eric
# Source: exp_025
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    # Analyze yesterday's bid from first alive opponent
    prev_trace = alive_opponents[0].get('previous_trace', {})
    if prev_trace and 'bid' in prev_trace and prev_trace['bid'] is not None:
        opp_prev_bid = prev_trace['bid']
        # If opponent bid high yesterday, they might bid high again if still needy
        # Check opponent current HP
        opp_hp = alive_opponents[0]['hp']
        if opp_hp <= 2:
            # Opponent desperate, likely bid very high; outbid if we need it
            if hp <= 2:
                bid = min(budget, DAILY_SALARY * 0.95)
            else:
                bid = min(budget, max(DAILY_SALARY * 0.5, opp_prev_bid * 0.85))
        else:
            # Opponent not desperate, we can be more moderate
            if hp <= 2:
                bid = min(budget, DAILY_SALARY * 0.85)
            else:
                bid = min(budget, max(DAILY_SALARY * 0.4, opp_prev_bid * 0.7))
    else:
        # No trace, base on supply and hp
        if supply > (MAX_SUPPLY + MIN_SUPPLY) // 2:
            base = DAILY_SALARY * 0.35
        else:
            base = DAILY_SALARY * 0.5
        if hp <= 2:
            base = DAILY_SALARY * 0.85
        elif hp <= 4:
            base = max(base, DAILY_SALARY * 0.55)
        bid = min(budget, base)
    return max(0, bid)
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
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    # Determine yesterday's max bid among alive opponents
    yesterday_max = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max = max(yesterday_max, prev['bid'])
    
    day = day_context['day']
    supply = day_context['supply']
    
    # Base bid factor: start conservative, increase as days pass
    day_factor = 0.5 + 0.04 * day  # 0.5 at day1, 0.86 at day10
    # Adjust for supply: lower supply means more competition -> higher bid
    supply_factor = 1.0 - 0.01 * (supply - 15)  # ranges from 1.0 (supply=15) to 0.9 (supply=25)
    
    # My health status
    hp = my_status['hp']
    # If low health, need to bid higher to ensure water
    hp_factor = 1.0
    if hp <= 2:
        hp_factor = 1.3
    elif hp <= 4:
        hp_factor = 1.15
    
    # Aggression adjustment based on yesterday: if opponents bid high, increase bid
    aggression_factor = 1.0
    if yesterday_max > DAILY_SALARY * 0.9:
        aggression_factor = 1.15
    elif yesterday_max > DAILY_SALARY * 0.7:
        aggression_factor = 1.05
    
    # Calculate proposed bid
    proposed_bid = DAILY_SALARY * day_factor * supply_factor * hp_factor * aggression_factor
    # Ensure min bid not too low and max bid not exceed budget
    min_bid = 10.0
    max_bid = min(my_status['budget'], DAILY_SALARY * 1.2)
    final_bid = max(min_bid, min(max_bid, proposed_bid))
    # Avoid zero or negative
    if final_bid < 0:
        final_bid = 0
    return final_bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # collect yesterday's bids from alive opponents who have trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    
    # baseline strategy
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 4:
        bid = min(budget, DAILY_SALARY * 0.7)
    else:
        bid = min(budget, DAILY_SALARY * 0.5)
    
    # adjust based on opponent's previous highest bid
    if prev_bids:
        max_prev_bid = max(prev_bids)
        # if opponents bid high, we need to match or exceed to survive
        if max_prev_bid > DAILY_SALARY * 0.8:
            if hp <= 3:
                bid = min(budget, max_prev_bid + 2)
            else:
                bid = min(budget, max_prev_bid * 0.9)
        else:
            # if low, we can bid safely above their max
            bid = min(budget, max(DAILY_SALARY * 0.4, max_prev_bid + 1))
    
    # ensure we don't overspend unnecessarily
    if supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.6)
    
    return max(0, min(bid, budget))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = day_context['supply']
    day = day_context['day']
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Base bid: proportional to our need relative to supply
    base_bid = DAILY_SALARY * (WATER_REQ / supply)
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Adjust based on yesterday's opponent behavior
    max_prev_bid = 0
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])
    
    # If someone bid high yesterday, we might need to bid higher
    if max_prev_bid > DAILY_SALARY * 0.7:
        base_bid = max(base_bid, max_prev_bid * 0.9)
    
    # Health-based adjustments
    if no_water_days > 0 or hp <= 2:
        # Need water urgently, bid aggressively
        bid = max(base_bid, DAILY_SALARY * 0.8)
    else:
        # Conserve budget
        bid = min(base_bid, DAILY_SALARY * 0.5)
    
    # Ensure bid does not exceed budget
    bid = min(bid, budget)
    # Also ensure we don't bid more than DAILY_SALARY (sensible limit)
    bid = min(bid, DAILY_SALARY)
    
    # Ensure bid is non-negative
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Identify alive opponents
    alive = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Get yesterday's bids from previous_trace
    prev_bids = []
    for o in alive.values():
        trace = o.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Estimate opponent's likely bid today based on yesterday
    # Alex tends to bid high (~92.8), Cindy tends to bid moderately (~94.7) but may save
    # We'll assume they repeat similar pattern
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        min_prev = min(prev_bids)
        max_prev = max(prev_bids)
    else:
        avg_prev = DAILY_SALARY * 0.5
        min_prev = DAILY_SALARY * 0.3
        max_prev = DAILY_SALARY * 0.7
    
    # Base bid: slightly above the minimum previous to win against the cheapest opponent
    target = min_prev + 2.0
    
    # If we are desperate (low hp or many days without water), bid higher
    no_water_days = my_status['no_water_days']
    if no_water_days >= 2 or hp <= 2:
        target = min(DAILY_SALARY * 0.9, max(target, avg_prev + 5.0))
    elif hp <= 4:
        target = min(DAILY_SALARY * 0.7, max(target, avg_prev + 1.0))
    
    # Don't bid more than budget or more than sensible salary proportion
    max_bid = min(budget, DAILY_SALARY * 0.85)
    bid = min(max_bid, max(target, DAILY_SALARY * 0.1))
    
    # Ensure we don't leave budget too low early; but if HP is high, we can be conservative
    if hp > 5 and day <= 3:
        bid = min(bid, DAILY_SALARY * 0.5)
    
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
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    supply = day_context['supply']
    # Supply determines how much water is available; more supply may lower bids
    # We'll adjust target based on supply
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        # To win, bid slightly above average but not too high
        target = avg_prev + 1.0
        # If supply is high, opponents might bid less; if low, more competition
        supply_factor = 1.0 - (supply - 15) / 10.0  # 1 when supply 15, 0.5 when 25
        target = target * (0.8 + 0.3 * supply_factor)  # scale
    else:
        # No history: start with moderate bid based on hp
        if my_status['hp'] <= 2:
            target = DAILY_SALARY * 0.8
        else:
            target = DAILY_SALARY * 0.5
    # Consider own desperation
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 1:
        target = max(target, DAILY_SALARY * 0.9)
    # Cap at budget and minimum zero
    bid = max(0, min(my_status['budget'], target))
    # Ensure we don't bid more than we can afford for future
    # But we can also consider future budget needs
    # Keep some reserve
    max_bid = my_status['budget'] * 0.98  # never bid all budget
    bid = min(bid, max_bid)
    return int(bid * 100) / 100.0  # two decimals
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    
    # Current day and supply
    day = int(day_context['day'])
    supply = day_context['supply']
    # need to use int for any indexing if needed
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Determine opponents alive
    alive = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Collect previous bids from alive opponents and their average
    prev_bids = []
    for opp in alive.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Estimate opponent aggressiveness
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        max_prev = 0.0
        avg_prev = 0.0
    
    # Base bid on own urgency and opponent behavior
    # Urgency: if HP is low or no_water_days >= 1, need to win strongly
    urgent = (hp <= 3) or (no_water_days >= 1)
    
    # Estimate opponent's likely bid: they may bid slightly above their previous average if aggressive
    # Cindy likely bids 112-127, Alex 85-150. Assume they continue.
    # We want to outbid by a small margin if possible, but not overspend.
    
    # Determine a safe bid that ensures winning vs typical opponent
    # If urgent, bid high but within budget
    if urgent:
        # Need to secure water at almost any cost
        bid = min(budget, max(DAILY_SALARY * 0.9, max_prev + 2.0))
    else:
        # Can afford to be conservative
        # If opponents are moderate, we can bid just above average
        # But be mindful of last days: day 9-10 we must survive
        if day >= 9:
            # Endgame: ensure win
            bid = min(budget, max(DAILY_SALARY * 0.8, max_prev + 1.0))
        else:
            # Midgame: stay alive while conserving
            # Bid slightly above max_prev if possible, else average
            target = max(avg_prev, DAILY_SALARY * 0.4)
            if max_prev > DAILY_SALARY * 0.9:
                # Opponents too aggressive; maybe drop out
                bid = min(budget, DAILY_SALARY * 0.3)
            else:
                bid = min(budget, target + 1.0)
    
    # Safety: never bid more than budget
    # Ensure we have some budget left for future days (at least 1 day of salary equivalent)
    # Not strictly enforced in code, but we can cap at budget - something?
    # For simplicity, ensure bid <= budget
    bid = max(0.0, min(budget, bid))
    
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive = [o for o in opponents_status.values() if o['alive']]
    if not alive:
        return min(budget, SALARY * 0.3)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if not yesterday_bids:
        # First day or no data: be conservative
        base = SALARY * 0.4
        if hp <= 3:
            base = SALARY * 0.55
    else:
        max_prev = max(yesterday_bids)
        # If someone very aggressive, we may need to match or avoid
        if max_prev >= SALARY * 1.0:
            # Aggressive environment: bid high only if necessary
            if hp <= 2:
                base = SALARY * 0.9
            else:
                base = SALARY * 0.5
        else:
            # Moderate: outbid the median by a small amount
            sorted_bids = sorted(yesterday_bids)
            median = sorted_bids[len(yesterday_bids)//2]
            base = max(SALARY * 0.4, median + 1.5)
            if hp <= 2:
                base = max(base, SALARY * 0.7)

    # Ensure bid is within budget and not more than salary
    bid = min(budget, base)
    # Also cap at 0.9*salary to preserve some budget for future
    bid = min(bid, SALARY * 0.9)
    return float(bid)
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
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']

    # Determine urgency based on HP and no_water_days
    no_water = my_status['no_water_days']
    if hp <= 2 or no_water >= 2:
        # High urgency: bid aggressively to win water
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.65
    else:
        base_bid = DAILY_SALARY * 0.4

    # Adjust based on yesterday's bids
    if yesterday_bids:
        # Use the highest yesterday bid to ensure we beat at least some opponents
        max_yesterday = max(yesterday_bids)
        # If supply is low, we need to bid higher to secure water
        if supply < 18:
            target = max(base_bid, max_yesterday + 2.0)
        else:
            target = max(base_bid, max_yesterday * 0.85)
    else:
        # No info: use base bid
        target = base_bid

    # Ensure we don't exceed budget
    bid = min(target, budget)
    # Also ensure non-negative
    bid = max(0, bid)

    # Explicitly use int if needed for future indexing, but not here
    return bid
"""
