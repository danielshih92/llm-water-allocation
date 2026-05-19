# ============================================================
# Experiment: exp_054
# Agent: Eric
# Source: exp_054
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    if hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif num_alive == 0:
        bid = min(budget, DAILY_SALARY * 0.4)
    else:
        bid = min(budget, DAILY_SALARY * 0.5)
    return int(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    n_alive = len(alive_opponents)

    # Estimate opponent bids from yesterday's trace (if available)
    opp_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            opp_bids.append(prev['bid'])

    # Base bid on HP and supply
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.75
    else:
        base_bid = DAILY_SALARY * 0.55

    # Adjust for supply scarcity
    supply_ratio = supply / 25.0
    base_bid *= (1.5 - 0.5 * supply_ratio)  # higher bid when supply low

    # If we have seen high opponent bids, adjust upward
    if opp_bids:
        max_prev = max(opp_bids)
        if max_prev > DAILY_SALARY * 0.8 and hp < 5:
            base_bid = max(base_bid, max_prev * 1.05)

    # Ensure we never bid more than budget
    bid = min(budget, base_bid)

    # Safety: if no_water_days >= 2, increase bid to avoid death
    if no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 1.2)

    # In early days (1-2), bid conservatively to save budget
    if day <= 2 and hp > 3:
        bid = min(bid, DAILY_SALARY * 0.4)

    return int(bid)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Determine highest bid from yesterday's traces among alive opponents
    highest_prev = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev = max(highest_prev, prev['bid'])

    # Critical: if no water for 2+ days, bid high
    if no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
    # If hp is low (<=3), need water
    elif hp <= 3:
        bid = min(budget, max(DAILY_SALARY * 0.8, highest_prev + 1))
    # If supply is low, competition high
    elif supply < 18:
        bid = min(budget, max(DAILY_SALARY * 0.6, highest_prev + 0.5))
    else:
        # Conservative when healthy
        bid = min(budget, DAILY_SALARY * 0.45)

    # Ensure bid does not exceed budget
    bid = min(bid, budget)
    # Ensure bid is non-negative
    bid = max(bid, 0.0)
    # floor division can produce float; not used here, but wrap int if needed
    return bid
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

    alive = [o for o in opponents_status.values() if o['alive']]
    n_alive = len(alive)
    my_hp = my_status['hp']
    budget = my_status['budget']

    # collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # base bid: try to get water at minimal cost
    # if many opponents, competition is higher
    if n_alive == 0:
        return min(budget, DAILY_SALARY * 0.3)

    # calculate average of previous bids
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0

    # desperate if no water for 2+ days
    if my_status['no_water_days'] >= 2 or my_hp <= 3:
        target = DAILY_SALARY * 0.9
    else:
        target = DAILY_SALARY * 0.5

    # if we have info about opponents, adjust
    if avg_prev > 0:
        # if average bid is high (e.g., Cindy), avoid competing when possible
        if avg_prev > DAILY_SALARY * 0.8:
            if my_hp > 5:
                target = min(target, DAILY_SALARY * 0.3)
            else:
                target = max(target, DAILY_SALARY * 0.7)
        else:
            # moderate bidders: slightly above average to secure water
            target = max(target, avg_prev * 0.95 + 1.0)

    # ensure we don't overpay when supply is abundant
    supply = day_context['supply']
    supply_float = supply if isinstance(supply, (int, float)) else 0
    supply_int = int(supply_float)
    # estimate competition: if supply is large, can bid lower
    if supply_int > 20:
        target *= 0.8
    elif supply_int < 18:
        target *= 1.2

    bid = min(budget, max(1.0, target))
    # ensure bid is not too high to waste budget
    return min(bid, DAILY_SALARY * 1.5)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    alive_opps = {k:v for k,v in opponents_status.items() if v['alive']}
    prev_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    max_prev = max(prev_bids) if prev_bids else 0.0
    # Base bid as fraction of salary, adjusted for supply
    supply_factor = 1.0
    if supply < 18:
        supply_factor = 1.3
    elif supply > 22:
        supply_factor = 0.7
    else:
        supply_factor = 1.0
    # Urgency based on HP and no water days
    if hp <= 2 or no_water >= 2:
        target = min(budget, DAILY_SALARY * 0.95 * supply_factor)
    else:
        target = DAILY_SALARY * 0.5 * supply_factor
        # Outbid yesterday's max if possible
        if max_prev > 0:
            target = max(target, max_prev + 1.0)
        target = min(target, budget)
    bid = round(target, 2)
    bid = max(0.0, min(bid, budget))
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
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    num_alive = len(alive_opponents)

    # Estimate yesterday's highest bid among alive opponents
    max_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev['bid'])

    # Base bid: low when HP is good, high when in danger
    if hp <= 1 or no_water_days >= 1:
        # Critical need: bid high to secure water
        base_bid = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 3:
        # Moderate need: bid enough to compete
        base_bid = min(budget, DAILY_SALARY * 0.75)
    else:
        # Healthy: conserve budget
        base_bid = min(budget, DAILY_SALARY * 0.3)

    # Adjust based on supply and opponent pressure
    # If supply is low (<18), increase bid to secure water
    if supply < 18:
        base_bid = max(base_bid, min(budget, DAILY_SALARY * 0.85))
    # If supply is high, reduce bid to save
    elif supply > 22:
        base_bid = min(base_bid, DAILY_SALARY * 0.4)

    # Exploit opponent overbidding: if yesterday's max bid was very high,
    # they might be low on budget today; we can bid lower if we don't need water
    if max_prev_bid > DAILY_SALARY * 0.8 and hp > 3:
        base_bid = min(base_bid, DAILY_SALARY * 0.2)

    # Ensure we don't bid more than budget
    final_bid = min(budget, max(1, base_bid))
    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    MY_BUDGET = my_status['budget']
    MY_HP = my_status['hp']
    NO_WATER = my_status['no_water_days']
    SUPPLY = int(day_context['supply'])
    DAY = day_context['day']

    # Calculate expected water price if supply is scarce
    # Estimate max opponent bid from yesterday
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    max_yesterday_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace')
        if prev and 'bid' in prev and prev['bid'] is not None:
            max_yesterday_bid = max(max_yesterday_bid, prev['bid'])

    # Base aggressive threshold
    aggressive_bid = min(MY_BUDGET, DAILY_SALARY * 0.95)
    cautious_bid = min(MY_BUDGET, DAILY_SALARY * 0.55)

    # Desperation: low HP or no water
    if MY_HP <= 3 or NO_WATER > 0:
        # Need to win at all costs, beat yesterday's max by 2
        target = max(max_yesterday_bid + 2, DAILY_SALARY * 0.87)
        return min(MY_BUDGET, target)

    # Conservative: high HP and moderate supply
    if MY_HP > 5 and SUPPLY >= 22:
        return cautious_bid

    # Medium supply or low HP but not desperate
    # Bid slightly above yesterday's max if possible
    bid = max_yesterday_bid + 1.5
    # But not exceed aggressive_bid
    bid = min(bid, aggressive_bid)
    # Ensure minimal bid to maintain priority
    bid = max(bid, DAILY_SALARY * 0.35)
    return min(MY_BUDGET, bid)
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
    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    # Collect yesterday's bids from opponents
    prev_bids = []
    for oid, opp in alive_opponents.items():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    # Base bid depending on state
    if no_water_days > 0 or hp <= 2:
        # need water desperately, bid high but mindful of budget
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp > 5:
        # healthy, save money
        bid = min(budget, DAILY_SALARY * 0.35)
    else:
        # moderate health, look at opponents
        if prev_bids:
            avg_prev = sum(prev_bids) / len(prev_bids)
            # If opponents bid high yesterday, they may be aggressive today; bid slightly below average to stay alive
            if avg_prev > DAILY_SALARY * 0.8:
                bid = min(budget, DAILY_SALARY * 0.5)
            else:
                bid = min(budget, max(DAILY_SALARY * 0.5, avg_prev + 1.5))
        else:
            bid = min(budget, DAILY_SALARY * 0.55)
    # safety: don't exceed budget
    return min(budget, max(0, bid))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_BID = min(my_status['budget'], DAILY_SALARY * 0.95)
    
    # Determine how many units are available
    supply = int(day_context['supply'])
    max_units = supply // WATER_REQ
    
    # Collect alive opponents and their previous bids
    alive_opps = {oid: o for oid, o in opponents_status.items() if o['alive']}
    prev_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Determine if we need water urgently
    need_water = my_status['hp'] <= 2 or my_status['no_water_days'] >= 2
    
    # Default bid if no previous data
    if not prev_bids:
        if need_water:
            return min(MAX_BID, DAILY_SALARY * 0.8)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
    
    highest_prev = max(prev_bids)
    
    # If any opponent had a very high bid in previous meta-round, they may be aggressive
    if highest_prev >= DAILY_SALARY * 0.85:
        if need_water:
            # We must outbid but limited
            bid = max(highest_prev + 1.0, DAILY_SALARY * 0.85)
            return min(MAX_BID, bid)
        else:
            # Avoid bidding war, stay low
            return min(my_status['budget'], DAILY_SALARY * 0.35)
    
    # Moderate opponents: we can try to outbid slightly
    if need_water:
        target = max(highest_prev + 1.5, DAILY_SALARY * 0.6)
        return min(MAX_BID, target)
    else:
        # Conservative when not desperate
        target = max(highest_prev + 1.0, DAILY_SALARY * 0.45)
        return min(my_status['budget'], target)
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

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    n_alive = len(alive_opponents)

    # Collect yesterday's traces from all opponents (even dead ones may have trace)
    yesterday_bids = []
    for oid, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and isinstance(prev, dict) and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: conservative estimate from yesterday's behavior
    base_bid = 0
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # Cindy's high bids might dominate; we assume competitors are rational
        # We aim to win at max_yesterday * 0.7 if possible, but not too low
        base_bid = max(DAILY_SALARY * 0.3, min(max_yesterday * 0.7, DAILY_SALARY * 0.8))
    else:
        base_bid = DAILY_SALARY * 0.5

    # Adjust based on my health
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    budget = my_status['budget']

    # Critical dehydration: bid high to survive
    if no_water_days >= 2 or hp <= 3:
        # Need water urgently, bid up to 90% of salary
        bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 6:
        # Moderate urgency, bid slightly above base
        bid = min(budget, base_bid + 5)
    else:
        # Healthy: conserve budget, bid just enough to potentially win
        bid = min(budget, base_bid - 10)

    # Ensure bid is non-negative and within budget
    bid = max(0, min(bid, budget))
    # Round to 2 decimals to avoid float issues
    bid = round(bid, 2)
    return bid
"""
