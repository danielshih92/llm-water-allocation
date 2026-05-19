# ============================================================
# Experiment: exp_071
# Agent: Eric
# Source: exp_071
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
    supply = day_context['supply']
    # Determine scarcity factor: lower supply -> higher bid multiplier
    scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 when max, 1 when min
    # Base bid depending on health
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5
    # Adjust for scarcity (increase bid when less water)
    adjusted_bid = base_bid * (1 + 0.3 * scarcity)
    # Ensure within budget
    final_bid = min(my_status['budget'], adjusted_bid)
    # Look at previous traces (none for day 1, but may be present later)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            # If opponent bid high yesterday, maybe they will again; we can adjust
            if prev['bid'] > DAILY_SALARY * 0.85:
                final_bid = max(final_bid, DAILY_SALARY * 0.75)  # ensure competitive
    return max(0, final_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    day = int(day_context['day'])
    supply = int(day_context['supply'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            prev_bids.append(prev_trace['bid'])

    if prev_bids:
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
    else:
        avg_prev_bid = DAILY_SALARY * 0.6

    # Base bid: slightly above average to secure water
    base_bid = avg_prev_bid + 1.0

    # Adjust based on urgency
    if hp <= 2:
        target_bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 4:
        target_bid = min(budget, max(base_bid, DAILY_SALARY * 0.7))
    else:
        target_bid = min(budget, base_bid * 0.9)

    # Ensure we don't waste budget when not needed
    if day >= 8:
        target_bid = min(budget, max(target_bid, DAILY_SALARY * 0.5))

    # Floor at 0
    return max(0, target_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # get yesterday's bids from previous_trace
    last_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            last_bids.append(prev['bid'])
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # base bid from supply scarcity
    # supply range 15-25, map to factor 0.4 to 0.8 of DAILY_SALARY
    scarcity_factor = 1.0 - (supply - 15) / 10.0  # 0 (plenty) to 1 (scarce)
    base_bid = DAILY_SALARY * (0.4 + 0.4 * scarcity_factor)
    
    # adjust based on desperation
    if hp <= 2 or no_water_days >= 2:
        desperation = 1.0
    elif hp <= 4:
        desperation = 0.8
    else:
        desperation = 0.5
    
    # consider opponent bids
    if last_bids:
        max_last = max(last_bids)
        avg_last = sum(last_bids) / len(last_bids)
        # if opponents were very aggressive, we may need to outbid if desperate
        if desperation > 0.6 and max_last > base_bid:
            target = max_last + 1.0
        else:
            target = max(base_bid, avg_last * 0.9)  # slightly below average to save
    else:
        target = base_bid
    
    # combine with desperation
    final_bid = target * (1 + 0.2 * (desperation - 0.5))
    
    # ensure within budget and not negative
    final_bid = min(final_bid, budget)
    final_bid = max(final_bid, 0.0)
    
    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Base bid from heuristic
    base_bid = DAILY_SALARY * 0.5
    
    # Adjust based on supply: more supply -> lower bid
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid *= (1.0 - supply_ratio * 0.3)  # reduce up to 30% when supply is max
    
    # Consider urgency: if hp low or no_water_days high, increase bid
    urgency = 1.0
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.5
    elif hp <= 4:
        urgency = 1.2
    
    # Look at yesterday's highest opponent bid
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Decide target bid
    if prev_bids:
        max_prev = max(prev_bids)
        # Against Cindy and Bob, add a small premium to outbid
        target = max(base_bid * urgency, max_prev * 1.05)
    else:
        target = base_bid * urgency
    
    # Cap by budget and daily salary * factor (don't go crazy)
    max_bid = min(budget, DAILY_SALARY * 1.2)
    bid = min(target, max_bid)
    # Ensure non-negative and at least a small bid if urgent
    if urgency > 1.2 and bid < 1:
        bid = min(budget, 1.0)
    return round(bid, 2)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    # Get yesterday's max bid from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # Determine urgency
    urgent = (hp <= 2) or (no_water >= 2)
    if urgent:
        base = DAILY_SALARY * 0.95
    else:
        base = DAILY_SALARY * 0.5
    # Adjust based on supply and competition
    if supply < WATER_REQ * 2:
        base = max(base, DAILY_SALARY * 0.7)
    # If opponents bid high yesterday, match or slightly exceed if needed
    if max_yesterday_bid > DAILY_SALARY * 0.8:
        if hp < 4:
            base = max(base, max_yesterday_bid + 1.0)
        else:
            base = min(base, DAILY_SALARY * 0.4)
    # Ensure bid is within budget and at least 1
    bid = min(budget, base)
    bid = max(1.0, bid)
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    # Collect previous bids from alive opponents
    previous_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            previous_bids.append(prev['bid'])

    # Determine base bid
    if previous_bids:
        highest_prev = max(previous_bids)
    else:
        highest_prev = 0

    # Adjust based on our HP
    if hp <= 2:
        # Desperate, bid high but within budget
        target = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # Moderate need, slightly above previous highest if not too large
        target = min(budget, max(DAILY_SALARY * 0.6, highest_prev + 1.0))
    else:
        # Healthy, bid low to conserve
        target = min(budget, DAILY_SALARY * 0.4)

    # Ensure we have enough for future if budget is low
    if budget < DAILY_SALARY * 0.5 and hp > 3:
        target = min(target, budget * 0.3)

    # Keep bid positive and not exceed budget
    return max(1.0, min(budget, target))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Determine Cindy's presence and her previous bid
    cindy_prev_bid = None
    if 'Cindy' in alive_opponents:
        prev = alive_opponents['Cindy'].get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            cindy_prev_bid = prev['bid']
    
    # Base bid calculation
    base_bid = 0.0
    
    # If we urgently need water (no_water_days >= 1 or hp <= 2)
    if no_water_days >= 1 or hp <= 2:
        # Bid high to secure water; use Cindy's previous bid as reference if available
        if cindy_prev_bid is not None:
            target = min(cindy_prev_bid + 5, DAILY_SALARY * 0.95)
        else:
            target = DAILY_SALARY * 0.85
        base_bid = min(budget, max(DAILY_SALARY * 0.8, target))
    else:
        # Not urgent: save budget
        if cindy_prev_bid is not None and cindy_prev_bid > 0:
            # If Cindy is aggressive, try to undercut if we have HP buffer
            if hp > 4:
                # Let Cindy win if she bids high, bid low
                base_bid = min(budget, DAILY_SALARY * 0.3)
            else:
                # Need to compete slightly above her previous
                base_bid = min(budget, max(DAILY_SALARY * 0.5, cindy_prev_bid + 2))
        else:
            # No reference: bid moderate
            base_bid = min(budget, DAILY_SALARY * 0.5)
    
    # Adjust for supply: if supply low, bid more aggressively
    if supply < 16:
        # Tight water
        if no_water_days == 0 and hp > 3:
            # We can afford to let others fight
            pass  # keep base_bid
        else:
            base_bid = min(budget, max(base_bid, DAILY_SALARY * 0.7))
    
    # Ensure we never bid more than budget
    final_bid = min(budget, max(0, base_bid))
    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    
    # Determine maximum number of winners
    max_winners = int(supply // WATER_REQ)  # floor division, ensure int
    
    alive_opponents = {oid: opp for oid, opp in opponents_status.items() if opp['alive']}
    num_alive = len(alive_opponents)
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Determine target bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If water is scarce (only 1 winner) and we need it, bid aggressively
        if max_winners == 1:
            target = max_prev + 5.0
        else:
            # Multiple winners possible, just outbid the highest
            target = max_prev + 0.5
    else:
        # No previous info, conservative baseline
        target = DAILY_SALARY * 0.5
    
    # Adjust based on urgency
    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.7)
    
    # Don't exceed budget
    bid = min(budget, target)
    # Ensure minimum positive bid
    bid = max(bid, 0.1)
    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    # Collect yesterday's bids from each opponent's previous_trace
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.5
    
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    
    # Base bid
    if hp <= 2:
        # Urgent: need water
        bid = min(budget, avg_prev_bid * 1.3 + 5)
    elif hp <= 4:
        bid = min(budget, max(avg_prev_bid * 1.1, DAILY_SALARY * 0.4))
    else:
        # Healthy, try to save
        bid = min(budget, max(avg_prev_bid * 0.9, DAILY_SALARY * 0.3))
    
    # Ensure bid is at least 1 and within budget
    bid = max(1, min(budget, bid))
    return bid
"""
