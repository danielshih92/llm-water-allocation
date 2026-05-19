# ============================================================
# Experiment: exp_036
# Agent: Eric
# Source: exp_036
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    # Check yesterday's trace for pattern
    yesterday_max = None
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if yesterday_max is None or prev['bid'] > yesterday_max:
                yesterday_max = prev['bid']
    if yesterday_max is not None:
        # We have history: respond to highest previous bid
        if my_status['hp'] <= 3:
            target = min(my_status['budget'], max(DAILY_SALARY * 0.8, yesterday_max + 1))
        else:
            target = min(my_status['budget'], max(DAILY_SALARY * 0.5, yesterday_max + 0.5))
        return target
    else:
        # No history (first day or all opponents have no trace)
        if my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.75)
        elif my_status['hp'] <= 5:
            return min(my_status['budget'], DAILY_SALARY * 0.55)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.35)
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
    no_water_days = my_status['no_water_days']

    # Opponent previous trace analysis
    max_prev_bid = 0
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and 'bid' in prev and prev['bid'] is not None:
                max_prev_bid = max(max_prev_bid, prev['bid'])

    # Base bid: enough to ensure water if supply is low
    # If supply is very low, competition may be fierce
    # Estimate competition: average bid of strong opponents ~ 95
    # We'll set a target bid based on supply and HP

    # Supply factor: lower supply -> higher bid needed
    supply_factor = max(0.5, (25.0 - supply) / 10.0)  # 0.5 to 1.0

    # Adjust for no_water_days: more days without water increases urgency
    urgency = min(1.5, 1 + 0.2 * no_water_days)

    # Base bid in terms of salary
    target_bid = DAILY_SALARY * 0.6 * supply_factor * urgency

    # If HP is low, bid aggressively
    if hp <= 3:
        target_bid = max(target_bid, DAILY_SALARY * 0.9)
    elif hp <= 5 and no_water_days >= 1:
        target_bid = max(target_bid, DAILY_SALARY * 0.75)

    # If yesterday's max bid was high, we need to outbid
    if max_prev_bid > 0 and max_prev_bid > target_bid:
        # Outbid by a small margin, but not too high
        target_bid = max(target_bid, max_prev_bid + 1.5)

    # Never exceed budget, and cap at salary
    final_bid = min(budget, target_bid)
    final_bid = min(final_bid, DAILY_SALARY * 1.0)
    final_bid = max(final_bid, 0.0)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = int(day_context['supply']) if isinstance(day_context['supply'], float) else day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    WATER_REQ = 8
    DAILY_SALARY = 140

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    avg_yesterday_bid = sum(yesterday_bids)/len(yesterday_bids) if yesterday_bids else 0

    # Base bid: if low supply or early days, be conservative
    if supply < 18:
        base_bid = DAILY_SALARY * 0.6
    else:
        base_bid = DAILY_SALARY * 0.4

    # Adjust for hp deficit
    if hp <= 2:
        if no_water_days >= 1:
            needed = DAILY_SALARY * 0.9
        else:
            needed = DAILY_SALARY * 0.7
        base_bid = max(base_bid, needed)
    elif hp <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.5)

    # React to yesterday's opponents
    if max_yesterday_bid > 0:
        if max_yesterday_bid >= DAILY_SALARY * 0.9:
            # Aggressive opponents, avoid war if possible
            if hp > 3:
                base_bid = min(base_bid, DAILY_SALARY * 0.3)
            else:
                base_bid = max(base_bid, DAILY_SALARY * 0.8)
        elif max_yesterday_bid >= DAILY_SALARY * 0.6:
            # Moderate, try to slightly outbid
            base_bid = max(base_bid, max_yesterday_bid + 1)
        else:
            # Low bids, we can be safe
            base_bid = min(base_bid, avg_yesterday_bid + 5)

    # Final adjustment for budget and supply
    max_bid = budget - (DAILY_SALARY * (10 - day) * 0.1) if day < 10 else budget
    max_bid = min(budget, max_bid)
    bid = min(max(base_bid, 0), max_bid)
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid from health and budget
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    # Determine aggressiveness
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If opponents were very aggressive yesterday, be conservative to save budget
        if highest_prev >= DAILY_SALARY * 0.85:
            if hp <= 2:
                return min(budget, DAILY_SALARY * 0.95)
            else:
                return min(budget, DAILY_SALARY * 0.3)
        else:
            # Outbid the highest from yesterday by a small margin
            bid = max(highest_prev + 1.5, DAILY_SALARY * 0.5)
            return min(budget, bid)
    else:
        # No previous data: base on health
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.55)

    # Ensure return is always present (fallback)
    return min(budget, DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Look at previous bids of alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Determine bid based on urgency and opponent history
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    
    # Urgency: need water if no_water_days > 0 or hp is low
    urgent = (no_water_days >= 1) or (hp <= 2)
    
    if urgent:
        # Willing to bid up to 90% of salary or budget, undercut if opponent bid is reasonable
        base = max(DAILY_SALARY * 0.6, max_prev_bid + 1.5)
        return min(budget, min(DAILY_SALARY * 0.9, base))
    else:
        # Not urgent: conserve budget, bid low unless supply is low
        if supply <= 18:
            # Water scarce, bid moderately above average opponent
            target = max(DAILY_SALARY * 0.4, max_prev_bid + 1.0)
            return min(budget, min(DAILY_SALARY * 0.65, target))
        else:
            # Abundant water, bid low
            return min(budget, DAILY_SALARY * 0.3)
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
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Extract previous bids from opponents' traces (yesterday)
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Base strategy depends on urgency
    if no_water_days > 0 or hp <= 3:
        # Urgent: need water badly, bid high
        urgent_bid = min(budget, DAILY_SALARY * 0.9)
        if prev_bids:
            max_prev = max(prev_bids)
            bid = max(urgent_bid, max_prev + 2.0)
        else:
            bid = urgent_bid
    else:
        # Healthy: bid conservatively but enough to beat yesterday's top
        if prev_bids:
            max_prev = max(prev_bids)
            # Aim to beat the highest by a small margin, but keep within daily salary
            target = max_prev + 1.5
            # Cap at salary
            target = min(target, DAILY_SALARY)
            # Also consider supply: if low supply, need higher bid
            supply = day_context['supply']
            if supply < 20:
                target = max(target, DAILY_SALARY * 0.6)
            bid = min(budget, target)
        else:
            # First day or no trace, default moderate bid
            bid = min(budget, DAILY_SALARY * 0.55)
    
    # Final safety: must be non-negative and not exceed budget
    bid = max(0.0, min(budget, bid))
    # Ensure bid is a float
    return float(bid)
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

    alive = [o for o in opponents_status.values() if o['alive']]
    supply = int(day_context['supply'])
    max_winners = supply // WATER_REQ  # integer division gives int
    if max_winners < 1:
        max_winners = 1

    # Determine yesterday's max bid among alive opponents
    prev_max_bid = 0.0
    prev_bids_available = any(o.get('previous_trace', {}).get('bid') is not None for o in alive)
    if prev_bids_available:
        prev_bids = [o['previous_trace']['bid'] for o in alive if o.get('previous_trace', {}).get('bid') is not None]
        if prev_bids:
            prev_max_bid = max(prev_bids)

    # My health and budget
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Base bid: try to win at least one unit of water
    # If I need water urgently (low HP or already missing water), bid high
    if hp <= 2 or no_water > 0:
        # Desperate: spend almost all budget to guarantee water
        bid = min(budget, DAILY_SALARY * 0.95)
    else:
        # Normal: try to conserve while still likely winning
        # Use yesterday's bid info if available
        if prev_max_bid > 0:
            # Slightly beat yesterday's maximum to stay competitive
            bid = min(budget, prev_max_bid + (DAILY_SALARY * 0.05))
        else:
            # Day 1 or no info: bid a high but sustainable amount
            # Supply is limited, so bid to win at least one share
            # Estimated cutoff: if everyone bids rationally, winning bid ≈ DAILY_SALARY (since only few win)
            bid = min(budget, DAILY_SALARY * 0.85)

    # Ensure not zero bid if we have budget and need
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0
    hp = my_status['hp']
    budget = my_status['budget']
    # Determine base bid
    if hp <= 3:
        # Critical: bid high to secure water
        base = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # Moderate: bid competitive
        base = min(budget, DAILY_SALARY * 0.6)
    else:
        # Comfortable: save budget
        base = min(budget, DAILY_SALARY * 0.4)
    # Adjust based on yesterday's highest bid
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Opponents were aggressive; if we need water, match or exceed
        if hp <= 3:
            # Need to outbid slightly
            target = min(budget, max(base, highest_prev_bid + 1))
            return target
        else:
            # Lowball to save
            return min(budget, DAILY_SALARY * 0.3)
    else:
        # Opponents moderate
        if hp <= 3 and highest_prev_bid > 0:
            return min(budget, max(base, highest_prev_bid + 1))
        return base
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""
