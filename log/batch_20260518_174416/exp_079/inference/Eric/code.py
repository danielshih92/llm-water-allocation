# ============================================================
# Experiment: exp_079
# Agent: Eric
# Source: exp_079
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    
    # Determine how many opponents are alive
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    n_opps = len(alive_opps)
    
    # Base bid: conservative if healthy
    base_bid = DAILY_SALARY * 0.3
    
    # Urgency based on HP and no_water_days
    if hp <= 2 or no_water >= 2:
        # Desperate: bid high but not more than necessary
        target = min(budget, DAILY_SALARY * 0.95)
        return target
    
    # If supply is very high, many can get water easily, so bid lower
    if supply >= 22:
        base_bid = DAILY_SALARY * 0.2
    
    # If we are healthy and supply adequate, bid low to save budget
    if hp > 5 and supply >= 18:
        return min(budget, DAILY_SALARY * 0.15)
    
    # Consider opponent's HP: if many are low, they may bid high; avoid bidding wars
    low_hp_opps = sum(1 for o in alive_opps if o['hp'] <= 3)
    if low_hp_opps >= 2:
        # They will likely bid aggressively; either match or stay low
        if hp > 4:
            return min(budget, DAILY_SALARY * 0.25)
        else:
            # Slightly higher to secure water
            return min(budget, DAILY_SALARY * 0.6)
    
    # Default: moderate bid
    bid = max(base_bid, 1)
    bid = min(bid, budget)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    HP = my_status['hp']
    BUDGET = my_status['budget']
    SALARY = 140
    WATER_REQ = 8
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    max_winners = max(1, supply // WATER_REQ)
    
    # Default base bid
    base_bid = SALARY * 0.5
    
    # Adjust based on desperation
    if HP <= 2:
        # Desperate: bid high to secure water
        base_bid = SALARY * 0.9
    elif HP <= 4:
        # Moderately desperate: bid above average if many opponents
        if num_alive > max_winners:
            base_bid = SALARY * 0.75
        else:
            base_bid = SALARY * 0.6
    else:
        # Healthy: can afford to be frugal
        base_bid = SALARY * 0.4
    
    # Use previous_trace if available (only for alive opponents with trace)
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        # Slightly undercut if we are healthy, otherwise match
        if HP > 3:
            base_bid = max(base_bid, avg_prev * 0.8)
        else:
            base_bid = max(base_bid, avg_prev * 0.95)
    
    # Ensure bid does not exceed budget
    bid = min(base_bid, BUDGET)
    # Round to avoid floating issues
    bid = round(bid, 2)
    return int(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Get yesterday's max opponent bid from previous_trace
    yesterday_bids = []
    for opp in opponents_status.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid on yesterday's highest bid + small increment
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        base_bid = max_prev + 2.0
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust for supply: if supply is high, we can bid less
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_factor = 1.0 - 0.3 * supply_ratio  # range 0.7 to 1.0
    bid = base_bid * supply_factor
    
    # Urgency based on HP
    if hp <= 2:
        urgency_factor = 0.95
    elif hp <= 4:
        urgency_factor = 0.85
    else:
        urgency_factor = 0.70
    
    bid = max(bid, DAILY_SALARY * urgency_factor)
    # Cap at budget or max reasonable
    max_bid = min(budget, DAILY_SALARY * 0.95)
    bid = min(bid, max_bid)
    bid = max(bid, 0.0)
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
    # Use int for index safety
    max_winners = int(supply // WATER_REQ)
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Determine urgency
    urgent = hp <= 2 or no_water_days > 0
    
    # Base bid on urgency and number of winners
    if urgent:
        bid = min(budget, DAILY_SALARY * 0.95)
    else:
        # Moderate: scale inversely with potential winners if many
        if max_winners >= 3:
            bid = min(budget, DAILY_SALARY * 0.55)
        else:
            bid = min(budget, DAILY_SALARY * 0.75)
    
    # Avoid zero bids when possible
    if bid < 1 and budget > 0:
        bid = 1
    return int(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)
    
    # Learn from yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # My desperation level
    no_water = my_status['no_water_days']
    hp = my_status['hp']
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If yesterday was very high, we may need to match or exceed
        if max_yesterday > DAILY_SALARY * 0.7:
            base_bid = max_yesterday + 1.0
        else:
            base_bid = DAILY_SALARY * 0.5
    else:
        base_bid = DAILY_SALARY * 0.5
    
    # Adjust for water need
    if no_water >= 2 or hp <= 2:
        bid = max(base_bid, DAILY_SALARY * 0.9)
    elif no_water == 1:
        bid = max(base_bid, DAILY_SALARY * 0.7)
    else:
        bid = base_bid
    
    # Ensure we don't exceed budget
    bid = min(my_status['budget'], bid)
    # Also ensure non-negative
    if bid < 0:
        bid = 0.0
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # alive opponents
    alive = [o for o in opponents_status.values() if o['alive']]

    # default if no alive
    if not alive:
        return min(budget, SALARY * 0.4)

    # collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])

    # base bid: ensure survival
    if no_water > 0 or hp <= 2:
        base = SALARY * 0.9
    else:
        base = SALARY * 0.5

    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # Cindy-like opponent with very high bid yesterday -> likely still high, avoid overpaying
        if max_prev > SALARY * 1.0:
            if hp > 3:
                return min(budget, base)
            else:
                return min(budget, SALARY * 0.85)
        else:
            # outbid the highest yesterday by a small margin, but cap
            bid = max(base, max_prev + 1.5)
            return min(budget, bid)

    # no yesterday info
    return min(budget, base)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Get yesterday's highest bid from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0
    
    # Determine urgency based on own state
    urgent = False
    if hp <= 2 or no_water_days >= 1:
        urgent = True
    
    # Base bid: start moderate, increase if needed
    base_bid = 85.0
    
    # Adjust for supply scarcity
    if supply < 18:
        base_bid += 20.0
    elif supply < 21:
        base_bid += 10.0
    
    # Adjust for yesterday's high pressure
    if highest_yesterday > 100:
        base_bid = max(base_bid, highest_yesterday + 2.0)
    elif highest_yesterday > 85:
        base_bid = max(base_bid, highest_yesterday + 1.0)
    
    # Desperate case: bid significantly higher
    if urgent:
        if budget >= 115:
            base_bid = 115.0
        else:
            base_bid = budget
    else:
        # If healthy and no pressure, be conservative
        if highest_yesterday < 85 and hp > 5:
            base_bid = min(base_bid, 78.0)
        else:
            base_bid = min(base_bid, 100.0)
    
    # Ensure bid is positive and not more than budget
    bid = max(0.0, min(base_bid, budget))
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
    my_hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Look at yesterday's highest bid from alive opponents
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > highest_prev_bid:
                highest_prev_bid = prev['bid']

    # Determine water need: if no water days > 0 or hp low, need water badly
    if no_water_days >= 1 or my_hp <= 2:
        # Must win water, bid up to just above highest previous or a high fraction of salary
        target = max(DAILY_SALARY * 0.9, highest_prev_bid + 1.0)
        return min(budget, target)
    else:
        # Healthy, can be conservative
        if my_hp > 5:
            # Very healthy, try to save money
            target = max(DAILY_SALARY * 0.3, highest_prev_bid * 0.8)
            return min(budget, target)
        else:
            # Moderately healthy, bid competitively but not overpay
            target = max(DAILY_SALARY * 0.6, highest_prev_bid + 0.5)
            return min(budget, target)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Extract current state
    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140

    # If no budget, bid 0 (e.g., first day)
    if budget <= 0:
        return 0.0

    # Count alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Default aggressive bid based on HP urgency
    if hp <= 2:
        target = DAILY_SALARY * 0.9
    elif hp <= 5:
        target = DAILY_SALARY * 0.5
    else:
        target = DAILY_SALARY * 0.2

    # Adjust if any opponent was extremely aggressive yesterday (last meta-round)
    # Only use trace if available and if the opponent is alive now
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            if trace['bid'] > DAILY_SALARY * 1.2:
                # Very aggressive opponent: reduce bid to save budget
                target = min(target, DAILY_SALARY * 0.3)
                break

    # Ensure bid within budget
    bid = min(budget, target)
    bid = max(bid, 0.0)
    return bid
"""
