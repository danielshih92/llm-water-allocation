# ============================================================
# Experiment: exp_083
# Agent: Eric
# Source: exp_083
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    daily_salary = 140
    water_req = 8
    hp = my_status['hp']
    budget = my_status['budget']
    supply = int(day_context['supply'])  # convert to int
    day = int(day_context['day'])
    
    # No opponent traces from previous day, so rely on HP
    if hp <= 3:
        bid = daily_salary * 0.9
    else:
        bid = daily_salary * 0.5
    
    # Ensure bid does not exceed budget
    bid = min(bid, budget)
    return bid
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Compute yesterday's average bid from alive opponents that have a trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        avg_yesterday = sum(yesterday_bids) / len(yesterday_bids)
    else:
        avg_yesterday = DAILY_SALARY * 0.6  # fallback guess
    
    # Estimate number of winners from supply
    num_winners = int(supply // WATER_REQ)
    if num_winners == 0:
        num_winners = 1
    
    # Base bid: undercut by 10% from yesterday's average, but at least a floor
    base_bid = max(DAILY_SALARY * 0.4, avg_yesterday * 0.9)
    
    # Adjust based on HP and dehydration
    if hp <= 2 or no_water_days >= 2:
        # Desperate: bid high, up to budget
        target_bid = min(budget, DAILY_SALARY * 1.3)
    elif hp <= 4:
        # Moderate risk: bid slightly above base
        target_bid = min(budget, base_bid * 1.2)
    else:
        # Healthy: bid to conserve budget, but ensure we might win if supply ample
        if num_winners >= 2:
            target_bid = min(budget, base_bid * 0.85)
        else:
            target_bid = min(budget, base_bid)
    
    # Ensure bid does not exceed budget and is non-negative
    bid = max(0, target_bid)
    bid = min(bid, budget)
    
    return bid
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
    return 15.0
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    # Determine if we are desperate (no water for 2+ days or HP <=2)
    desperate = my_status['no_water_days'] >= 2 or hp <= 2
    # Extract yesterday's bids from opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest = max(yesterday_bids)
        # If opponents bid aggressively yesterday, adjust
        if highest >= 130:
            if desperate:
                bid = min(budget, DAILY_SALARY * 0.95)
            else:
                bid = min(budget, DAILY_SALARY * 0.3)
        else:
            # Less aggressive: outbid by small margin if needed
            target = max(highest + 1, DAILY_SALARY * 0.5)
            bid = min(budget, target)
    else:
        # No opponent trace (should not happen if all are new, but be safe)
        if desperate:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.55)
    # Adjust based on supply scarcity
    if supply < 18 and not desperate:
        bid = min(bid, DAILY_SALARY * 0.4)
    # Ensure bid is integer and within budget
    return int(min(bid, budget))
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
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Get yesterday's bids from alive opponents only
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    
    # If water is scarce or we are dehydrated, bid aggressively
    if hp <= 2 or no_water_days >= 1:
        bid = min(budget, highest_yesterday_bid + 1.5)
        bid = max(bid, 0.5 * DAILY_SALARY)
    else:
        # When HP is good, try to save budget
        if highest_yesterday_bid > 0.85 * DAILY_SALARY:
            bid = min(budget, DAILY_SALARY * 0.3)
        else:
            # Outbid yesterday's highest by a small margin if we need water, but not too much
            needed = WATER_REQ * 2  # to be safe with supply division
            target_bid = max(highest_yesterday_bid + 1.5, 0.5 * DAILY_SALARY)
            bid = min(budget, target_bid)
    
    # Ensure bid is within budget and not below 0
    bid = max(0, min(budget, bid))
    
    # In last days, be more competitive if budget high
    if day >= 7 and supply / int(WATER_REQ) < 2:
        bid = min(budget, highest_yesterday_bid + 2)
    
    return float(bid)
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
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)
    prev_bids = []
    for opp_id, opp in alive_opponents.items():
        prev_trace = opp.get('previous_trace', None)
        if prev_trace and prev_trace.get('bid') is not None:
            prev_bids.append(prev_trace['bid'])
    if my_hp <= 2:
        aggressive_bid = min(my_budget, DAILY_SALARY * 0.95)
        return aggressive_bid
    if prev_bids:
        avg_prev_bid = sum(prev_bids) / len(prev_bids)
        if avg_prev_bid >= DAILY_SALARY * 0.85:
            return min(my_budget, DAILY_SALARY * 0.4)
        else:
            bid = max(DAILY_SALARY * 0.5, avg_prev_bid + 1.5)
            return min(my_budget, bid)
    else:
        return min(my_budget, DAILY_SALARY * 0.55)
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
    WATER_REQ = 8
    DAILY_SALARY = 140

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    yesterday_max_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max_bid = max(yesterday_max_bid, prev['bid'])

    if hp <= 2:
        target = DAILY_SALARY * 0.95
    elif hp <= 5:
        target = max(DAILY_SALARY * 0.6, yesterday_max_bid + 2)
    else:
        target = max(1, yesterday_max_bid * 0.75 - 5)

    bid = min(budget, max(0, target))
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
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive = [o for o in opponents_status.values() if o['alive']]
    
    # default aggressive bid based on supply
    if day <= 2:
        target_bid = DAILY_SALARY * 0.9
    elif hp <= 2:
        target_bid = min(DAILY_SALARY * 0.95, budget)
    else:
        # look at yesterday's highest bid among alive opponents
        prev_bids = []
        for opp in alive:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])
        if prev_bids:
            highest_prev = max(prev_bids)
            if hp > 3:
                target_bid = max(DAILY_SALARY * 0.5, highest_prev + 2.0)
            else:
                target_bid = max(DAILY_SALARY * 0.75, highest_prev + 1.0)
        else:
            # no trace, bid moderately
            target_bid = DAILY_SALARY * 0.55
    
    # adjust for supply
    index = int((supply - 15) / 10)  # supply 15-25 -> index 0 or 1
    supply_factor = [1.0, 0.8][index if index < 2 else 0]
    target_bid = target_bid * supply_factor
    
    # clamp to budget
    final_bid = min(budget, max(0, target_bid))
    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    min_bid = 1
    max_bid = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    n_alive = len(alive_opponents)
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    
    # Gather yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0
    
    # Estimate today's opponent bids: they might bid lower if budget low
    # If max_prev_bid was high, maybe they are budget constrained today
    # We'll adjust base bid
    
    # Base bid: need water, adjust based on hp and competition
    if hp <= 2:
        # Desperate
        bid = DAILY_SALARY * 0.8
    elif hp <= 4:
        bid = DAILY_SALARY * 0.6
    else:
        # Comfortable, but consider competition
        if n_alive <= 1:
            bid = DAILY_SALARY * 0.3
        else:
            bid = DAILY_SALARY * 0.5
    
    # Adjust based on previous high bid: if opponents were very high, they might be weaker today
    if max_prev_bid > DAILY_SALARY * 0.9:
        # They spent a lot yesterday, so today maybe low
        bid = min(bid, DAILY_SALARY * 0.4)
    
    # Ensure bid is within bounds
    bid = max(min_bid, min(bid, max_bid))
    # If I have budget and hp is critical, go higher
    if hp <= 2 and my_status['budget'] >= bid:
        bid = min(bid + 20, max_bid)
    return int(bid)
"""
