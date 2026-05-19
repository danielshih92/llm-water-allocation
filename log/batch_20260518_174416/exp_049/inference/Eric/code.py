# ============================================================
# Experiment: exp_049
# Agent: Eric
# Source: exp_049
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Collect yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
    
    # Base bid: start with a moderate amount
    base_bid = DAILY_SALARY * 0.4
    
    # Adjust based on HP
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.65
    
    # If we are desperate (no water days > 2), bid very high
    if no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.95
    
    # Try to outbid yesterday's highest if we have budget
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # Only escalate if we can reasonably outbid by a small margin
        if highest_prev > base_bid and budget > highest_prev + 2:
            base_bid = min(budget, highest_prev + 2)
        elif highest_prev > base_bid and budget <= highest_prev + 2:
            # If we can't outbid, try a safe bid
            base_bid = min(budget, base_bid)
        else:
            # Already higher, stick with base
            base_bid = max(base_bid, highest_prev + 0.5)
    
    # Final bound: cannot exceed budget and cannot be negative
    return max(0, min(budget, base_bid))
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
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    previous_bids = []
    for opp in alive_opponents.values():
        pt = opp.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            previous_bids.append(pt['bid'])
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Determine maximum we are willing to bid based on budget
    max_bid = min(budget, DAILY_SALARY * 1.0)
    
    # If no opponents alive, bid low to save
    if not alive_opponents:
        return min(max_bid, DAILY_SALARY * 0.3)
    
    # Calculate previous max bid among alive opponents
    if previous_bids:
        max_prev_bid = max(previous_bids)
    else:
        max_prev_bid = 0.0
    
    # Urgency based on HP and no water days
    if hp <= 2 or no_water_days >= 2:
        # Need water urgently: bid above previous max but within budget
        target_bid = max_prev_bid + 2.0
        return min(max_bid, target_bid)
    elif hp <= 4:
        # Moderate urgency: try to win but not overpay
        target_bid = max_prev_bid + 1.0
        return min(max_bid, max(target_bid, DAILY_SALARY * 0.6))
    else:
        # Healthy, conserve budget
        # If previous bids were very high, we might let them compete and bid low
        if max_prev_bid > DAILY_SALARY * 0.8:
            return min(max_bid, DAILY_SALARY * 0.4)
        else:
            # Otherwise try to win with a slight edge
            target_bid = max_prev_bid + 0.5
            return min(max_bid, max(target_bid, DAILY_SALARY * 0.5))
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
    supply = day_context['supply']
    budget = my_status['budget']
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid')
        if bid is not None:
            yesterday_bids.append(bid)
    
    # base bid
    base_bid = DAILY_SALARY * 0.6  # 84
    target = base_bid
    
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # outbid by 1 if affordable
        target = max(target, max_prev + 1.0)
    
    # boost if supply is low
    if supply < 18.0:
        target *= 1.1
    
    # emergency if hp low or no_water_days high
    if hp <=
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
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    max_prev_bid = 0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            if prev['bid'] > max_prev_bid:
                max_prev_bid = prev['bid']
    
    base_bid = min(budget, DAILY_SALARY * 0.6)
    
    if hp <= 2 or no_water_days >= 1:
        base_bid = min(budget, DAILY_SALARY * 1.1)
    elif hp <= 4:
        base_bid = min(budget, DAILY_SALARY * 0.85)
    
    if max_prev_bid > 0 and max_prev_bid > base_bid * 1.2:
        # opponents were aggressive yesterday, we might need to secure water
        if hp <= 3:
            base_bid = min(budget, max_prev_bid * 0.9)
        else:
            base_bid = min(budget, DAILY_SALARY * 0.7)
    
    # Ensure we don't bid more than budget
    final_bid = max(0, min(budget, base_bid))
    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    SUPPLY = day_context['supply']
    DAY = day_context['day']
    HP = my_status['hp']
    BUDGET = my_status['budget']
    NO_WATER_DAYS = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    n_alive = len(alive_opponents)

    # Estimate number of water units available today
    water_units = int(SUPPLY // WATER_REQ)
    total_players_alive = n_alive + 1  # including self
    # If enough water for everyone, bid low
    if water_units >= total_players_alive:
        base_bid = DAILY_SALARY * 0.3
    else:
        base_bid = DAILY_SALARY * 0.5

    # Adjust based on previous opponent traces
    highest_prev_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])

    # If someone was aggressive yesterday, be cautious
    if highest_prev_bid > DAILY_SALARY * 0.8:
        if HP <= 2:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.4)
    else:
        if HP <= 2:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure bid is at least minimal to survive if very low HP
    if HP <= 1 and NO_WATER_DAYS >= 1:
        base_bid = DAILY_SALARY * 0.9

    # Cap by budget
    bid = min(BUDGET, base_bid)
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return max(1, min(budget, DAILY_SALARY * 0.4))
    
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    if supply <= 16:
        base_ratio = 0.6
    elif supply <= 20:
        base_ratio = 0.5
    else:
        base_ratio = 0.4
    
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > 100:
            base_ratio = max(base_ratio, 0.7)
        elif max_prev > 80:
            base_ratio = max(base_ratio, 0.6)
        else:
            base_ratio = max(base_ratio, 0.45)
    
    if hp <= 2 or no_water_days > 0:
        base_ratio = min(base_ratio + 0.2, 0.95)
    
    bid = DAILY_SALARY * base_ratio
    bid = min(bid, budget)
    bid = max(1, bid)
    return bid
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
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    # Urgency based on health and water deprivation
    if hp <= 2 or no_water >= 2:
        target_bid = min(budget, max_prev_bid * 0.95 + 1.0)
    elif hp <= 4:
        target_bid = min(budget, max_prev_bid * 0.8 + 2.0)
    else:
        target_bid = min(budget, max(DAILY_SALARY * 0.5, max_prev_bid * 0.65))
    # Ensure we don't exceed budget
    return min(budget, target_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
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
        target = highest_prev + 2.0
    else:
        target = DAILY_SALARY * 0.65
    
    # Adjust based on health
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.85)
    if my_status['no_water_days'] >= 1:
        target = max(target, DAILY_SALARY * 0.6)
    
    # Budget constraint
    bid = min(my_status['budget'], target)
    return int(bid) if bid == int(bid) else bid
"""
