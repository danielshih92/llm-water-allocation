# ============================================================
# Experiment: exp_034
# Agent: Eric
# Source: exp_034
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.2)
    # Base bid: fraction of salary
    if hp <= 2:
        bid = DAILY_SALARY * 0.55
    elif hp <= 4:
        bid = DAILY_SALARY * 0.40
    else:
        bid = DAILY_SALARY * 0.30
    # Adjust for supply: if supply is high, can bid less
    if supply > 20:
        bid *= 0.8
    # Ensure within budget and not too high
    bid = min(budget, bid)
    # Avoid bidding zero if possible
    if bid < 1:
        bid = 1
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    # Gather yesterday's opponent bids from previous_trace
    opp_bids = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                opp_bids.append(prev['bid'])
    
    # Determine target bid based on yesterday's max
    if opp_bids:
        max_opp = max(opp_bids)
        target = max_opp + 1.5  # slightly above
    else:
        target = DAILY_SALARY * 0.5
    
    # Adjust based on our health
    if my_status['hp'] <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_status['hp'] >= 6:
        target = min(target, DAILY_SALARY * 0.4)
    
    # Ensure we don't bid more than we can afford
    bid = min(my_status['budget'], target)
    
    # Ensure bid is non-negative and within reasonable range
    bid = max(1, bid)
    return int(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Get yesterday's highest bid among alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']

    # Base bid: if we urgently need water, bid high; otherwise, try to save
    if hp <= 2:
        # Very low HP, must win water at almost any cost
        target = min(budget, DAILY_SALARY * 0.95)
        if yesterday_bids:
            target = min(budget, max(target, max(yesterday_bids) + 5.0))
        return target
    elif hp <= 4:
        # Low HP, need water but can be moderate
        if yesterday_bids:
            target = min(budget, max(DAILY_SALARY * 0.6, max(yesterday_bids) + 1.0))
        else:
            target = min(budget, DAILY_SALARY * 0.6)
        return target
    else:
        # Healthy - try to save money by bidding low, but not too low
        if yesterday_bids:
            target = min(budget, min(DAILY_SALARY * 0.45, max(yesterday_bids) - 2.0))
            # Ensure we don't bid too low if supply is scarce
            if supply < (MIN_SUPPLY + MAX_SUPPLY) / 2:
                target = min(budget, max(target, DAILY_SALARY * 0.35))
        else:
            target = min(budget, DAILY_SALARY * 0.35)
        return max(target, 1.0)  # Always bid at least 1 to avoid zero bid (unless budget is 0)
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
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Use only immediate previous trace to assess pressure
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', None)
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Base bid depends on health and no_water_days
    if hp <= 2 or no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.93  # ~130
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.64  # ~90
    else:
        base_bid = DAILY_SALARY * 0.5   # 70

    # Adjust if yesterday's highest bid was very high
    if prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev > DAILY_SALARY * 0.85:  # >119
            # Opponents are aggressive, stay competitive
            if hp <= 2:
                base_bid = DAILY_SALARY * 0.98
            else:
                base_bid = highest_prev + 1.0
        else:
            # Opponents moderate
            base_bid = max(base_bid, highest_prev + 0.5)

    bid = min(budget, base_bid)
    # Ensure non-negative and within budget
    return max(0, bid)
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
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)
    yest_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yest_bids.append(float(prev['bid']))
    hp = my_status['hp']
    budget = my_status['budget']
    supply = day_context['supply']
    if not yest_bids:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        else:
            return min(budget, DAILY_SALARY * 0.55)
    else:
        max_yest = max(yest_bids)
        avg_yest = sum(yest_bids) / len(yest_bids)
        if max_yest > DAILY_SALARY * 0.85:
            if hp <= 2:
                return min(budget, max_yest + 5.0)
            else:
                return min(budget, avg_yest * 0.7)
        else:
            if hp <= 2:
                return min(budget, max_yest + 2.0)
            else:
                return min(budget, max(DAILY_SALARY * 0.5, avg_yest * 0.9))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
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

    alive_opps = {k:v for k,v in opponents_status.items() if v['alive']}
    num_alive = len(alive_opps)

    prev_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    # Base bid according to HP urgency
    if hp <= 2:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        base_bid = min(budget, DAILY_SALARY * 0.6)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.4)

    # Adjust based on yesterday's highest bid
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > DAILY_SALARY * 0.7:
            target = max_prev + 2.0
            if hp <= 2:
                target = max(target, DAILY_SALARY * 0.8)
            base_bid = min(budget, target)
        else:
            base_bid = min(budget, max(base_bid, max_prev + 1.0))

    # Adjust for number of alive opponents
    if num_alive >= 3:
        base_bid = min(budget, max(base_bid, DAILY_SALARY * 0.5))
    elif num_alive <= 1:
        base_bid = min(budget, base_bid * 0.7)

    final_bid = min(budget, max(1, base_bid))
    return round(final_bid, 2)
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {oid: o for oid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents)

    # Base bid from need
    if hp <= 2 or no_water_days >= 1:
        need_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        need_bid = DAILY_SALARY * 0.7
    else:
        need_bid = DAILY_SALARY * 0.5

    # Adjust for supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 to 1
    # More supply => lower bid, less supply => higher bid
    supply_factor = 1.0 + (1.0 - supply_ratio) * 0.3
    need_bid *= supply_factor

    # Exploit opponent previous_trace
    highest_prev_bid = 0
    lowest_hp_after = float('inf')
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > highest_prev_bid:
                highest_prev_bid = bid
        if prev and prev.get('hp_after') is not None:
            hp_after = prev['hp_after']
            if hp_after < lowest_hp_after:
                lowest_hp_after = hp_after

    # If any opponent had very low hp, they will likely bid high now
    if lowest_hp_after <= 2:
        # We need to outbid them if we are also desperate
        if hp <= 3:
            need_bid = max(need_bid, highest_prev_bid + 2.0)
        else:
            # We can bid slightly less and hope they deplete budget
            need_bid = max(need_bid, highest_prev_bid * 0.8)
    elif highest_prev_bid > DAILY_SALARY * 0.8:
        # Opponent bid very high yesterday; they may reduce today
        need_bid = min(need_bid, DAILY_SALARY * 0.6)

    # Ensure within budget and at least some minimum if we need water
    if hp <= 2 or no_water_days >= 1:
        # Must get water, bid aggressively
        final_bid = min(budget, DAILY_SALARY * 0.95)
        # But don't blow everything if many days left
        if day > 7:
            final_bid = min(budget, DAILY_SALARY * 0.85)
    else:
        final_bid = min(budget, max(1.0, need_bid))

    # Prevent float index error - not needed here but just in case
    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            prev_bids.append(prev['bid'])
    
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0
    max_prev_bid = max(prev_bids) if prev_bids else 0
    
    hp = my_status['hp']
    no_water = my_status['no_water_days']
    budget = my_status['budget']
    
    if no_water > 0 and hp < 3:
        if max_prev_bid > DAILY_SALARY * 0.6:
            bid = min(budget, max(DAILY_SALARY * 0.7, avg_prev_bid + 5))
        else:
            bid = min(budget, DAILY_SALARY * 0.8)
    elif hp <= 2:
        if max_prev_bid > DAILY_SALARY * 0.5:
            bid = min(budget, max(DAILY_SALARY * 0.6, avg_prev_bid + 3))
        else:
            bid = min(budget, DAILY_SALARY * 0.65)
    else:
        if avg_prev_bid > 0:
            bid = min(budget, max(DAILY_SALARY * 0.4, avg_prev_bid * 0.9))
        else:
            bid = min(budget, DAILY_SALARY * 0.45)
    
    # Ensure non-negative and within budget
    bid = max(0, min(budget, bid))
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    highest_yesterday = max(yesterday_bids) if yesterday_bids else 0.0

    need_water = no_water > 0 or hp <= 3

    if need_water:
        # Outbid yesterday's highest by a small margin, but don't exceed budget or be reckless
        target = max(DAILY_SALARY * 0.5, highest_yesterday + 1.0)
        return min(budget, target)
    else:
        # HP is fine, conserve budget by bidding low
        # Bid slightly below average if we want to win occasionally, or very low to save
        # Here we bid 30% of salary to stay alive but not waste
        return min(budget, DAILY_SALARY * 0.3)
"""
