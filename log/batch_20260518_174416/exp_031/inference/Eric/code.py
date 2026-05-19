# ============================================================
# Experiment: exp_031
# Agent: Eric
# Source: exp_031
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
        return min(budget, DAILY_SALARY * 0.4)
    # gather yesterday bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # if we are desperate, outbid slightly
        if hp <= 2:
            target = max(DAILY_SALARY * 0.85, max_yesterday_bid + 1.5)
        else:
            # if opponent bid very high yesterday, they might repeat; we can undercut if we have hp
            if max_yesterday_bid >= DAILY_SALARY * 0.85:
                if hp > 3:
                    return min(budget, DAILY_SALARY * 0.3)
                else:
                    return min(budget, DAILY_SALARY * 0.95)
            else:
                target = max(DAILY_SALARY * 0.5, max_yesterday_bid + 1.5)
        return min(budget, target)
    else:
        # no history: default strategy
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        elif hp <= 4:
            return min(budget, DAILY_SALARY * 0.7)
        else:
            return min(budget, DAILY_SALARY * 0.6)
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Yesterday highest bid among alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    highest_prev = max(yesterday_bids) if yesterday_bids else 0

    # Base bid: percentage of salary depending on urgency
    if hp <= 2:
        base = DAILY_SALARY * 1.0
    elif hp <= 4:
        base = DAILY_SALARY * 0.8
    elif no_water_days >= 1:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.6

    # Adjust for supply scarcity
    if supply < 18:
        base *= 1.2
    elif supply > 22:
        base *= 0.85

    # Exploit yesterday's high bidders: if they bid very high, they may have less budget now, so we can bid lower
    if highest_prev > DAILY_SALARY * 1.2:
        if hp > 3:
            base = min(base, DAILY_SALARY * 0.5)
        else:
            base = max(base, DAILY_SALARY * 0.9)

    # Ensure not to exceed budget and reasonable range
    bid = min(budget, max(DAILY_SALARY * 0.4, base))
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
    
    day = day_context['day']
    supply = day_context['supply']
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Determine how many agents can be fully satisfied
    max_agents = int(int(supply) // WATER_REQ)
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    count_alive = len(alive_opponents)
    
    # Collect previous bids from yesterday
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid decision
    highest_prev = max(prev_bids) if prev_bids else 0
    
    # Urgency based on hp
    if hp <= 2:
        # Must win water at almost any cost
        bid = min(budget, DAILY_SALARY * 1.2)
    elif hp <= 5:
        # Need water reasonably
        if highest_prev > 0:
            bid = min(budget, max(DAILY_SALARY * 0.7, highest_prev + 2))
        else:
            bid = min(budget, DAILY_SALARY * 0.6)
    else:
        # Healthy, can conserve
        if highest_prev >= DAILY_SALARY * 0.9:
            # Opponents are desperate, let them fight
            bid = min(budget, DAILY_SALARY * 0.4)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
    
    # Ensure we don't bid more than budget
    return int(min(budget, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(round(day_context['supply']))
    day = int(day_context['day'])
    
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Extract yesterday's highest bid from alive opponents' traces
    yesterday_highest = None
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            bid_val = float(trace['bid'])
            if yesterday_highest is None or bid_val > yesterday_highest:
                yesterday_highest = bid_val
    
    # Determine my water need level
    if hp <= 2:
        need_factor = 0.9
    elif hp <= 4:
        need_factor = 0.7
    elif hp <= 6:
        need_factor = 0.5
    else:
        need_factor = 0.3
    
    # If yesterday's highest bid was very high (likely from Cindy), adjust upward
    bid_base = DAILY_SALARY * need_factor
    if yesterday_highest is not None and yesterday_highest > DAILY_SALARY * 0.8:
        # High pressure environment: be willing to spend more
        if hp > 4:
            # Conserve but still at least meet if needed
            bid_base = max(bid_base, DAILY_SALARY * 0.4)
        else:
            bid_base = max(bid_base, yesterday_highest * 0.9)
    
    # Final bid, cannot exceed budget
    bid = min(budget, bid_base)
    # Ensure non-negative
    bid = max(0.0, bid)
    return min(bid, budget)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Constants
    WATER_REQ = 8
    DAILY_SALARY = 140

    # Extract day and supply (ensure int casting for indices)
    day = int(day_context['day'])
    supply = float(day_context['supply'])

    # My state
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Determine alive opponents and their yesterday's max bid
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    max_prev_bid = 0.0
    for opp in alive_opps:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            bid_val = float(trace['bid'])
            if bid_val > max_prev_bid:
                max_prev_bid = bid_val

    # Base bid strategy
    bid = 0.0

    # Danger if no water recently
    if no_water_days >= 2 or hp <= 3:
        # Need water urgently: bid high but not above budget nor unnecessarily high
        bid = min(budget, DAILY_SALARY * 0.85)
    elif max_prev_bid > 0:
        # If opponents were aggressive yesterday, bid moderately to avoid overpay
        if max_prev_bid >= DAILY_SALARY * 1.2:
            # Very aggressive: try to outbid only if we have budget
            bid = min(budget, DAILY_SALARY * 0.9)
        elif max_prev_bid >= DAILY_SALARY * 0.8:
            # Moderately aggressive: bid just above average
            bid = min(budget, DAILY_SALARY * 0.7)
        else:
            # They were low, so we can be conservative
            bid = min(budget, DAILY_SALARY * 0.5)
    else:
        # No previous data: default conservative
        if day <= 3:
            bid = min(budget, DAILY_SALARY * 0.4)
        else:
            bid = min(budget, DAILY_SALARY * 0.55)

    # Ensure we don't bid more than we can afford
    bid = max(0.0, min(budget, bid))

    # If supply is low, increase bid slightly
    if supply < 20.0 and hp <= 5:
        bid = max(bid, min(budget, DAILY_SALARY * 0.75))

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
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    
    # Get yesterday's highest bid among alive opponents
    highest_prev_bid = None
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if highest_prev_bid is None or bid > highest_prev_bid:
                highest_prev_bid = bid
    
    # Determine supply tightness
    supply_factor = 1.0
    if supply < WATER_REQ * 2:
        supply_factor = 1.3
    
    # Emergency: low hp
    if hp <= 2:
        target_bid = min(budget, DAILY_SALARY * 0.9 * supply_factor)
    elif highest_prev_bid is not None:
        # Bid just above highest previous bid, with supply adjustment
        target_bid = highest_prev_bid + 2.0
        # Cap to avoid overbidding
        max_bid = min(budget, DAILY_SALARY * 1.0 * supply_factor)
        target_bid = min(target_bid, max_bid)
        # Ensure at least a reasonable minimum
        target_bid = max(target_bid, DAILY_SALARY * 0.4)
    else:
        # No trace: rely on supply factor
        target_bid = min(budget, DAILY_SALARY * 0.6 * supply_factor)
    
    # Ensure bid is between 0 and budget
    target_bid = max(0.0, min(target_bid, budget))
    
    return target_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opps = {oid: o for oid, o in opponents_status.items() if o['alive']}
    yesterday_bids = []
    for opp in alive_opps.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    budget = my_status['budget']
    hp = my_status['hp']
    if hp <= 2:
        # desperate: bid high to get water
        bid = min(budget, DAILY_SALARY * 0.9)
    elif yesterday_bids:
        max_prev = max(yesterday_bids)
        # ensure we beat yesterday's top bid by a small margin
        target = max_prev + 2.0
        # cap by salary and budget
        bid = min(budget, DAILY_SALARY * 0.7, target)
        # but not too low: must be at least enough to compete
        bid = max(bid, min(budget, DAILY_SALARY * 0.4))
    else:
        # no history, moderate conservative
        bid = min(budget, DAILY_SALARY * 0.5)
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Calculate number of alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opponents)
    
    # Get yesterday's maximum bid from alive opponents (from previous_trace)
    max_yesterday_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_yesterday_bid = max(max_yesterday_bid, prev['bid'])
    
    # Base bid: aggressive
    base_bid = DAILY_SALARY * 0.8
    
    # Adjust for HP critical
    if hp <= 2:
        base_bid = min(budget, DAILY_SALARY * 1.1)
    elif hp <= 5:
        base_bid = DAILY_SALARY * 0.9
    
    # Adjust for supply scarcity (total water needed vs supply)
    total_water_needed = WATER_REQ * (num_alive + 1)  # including self
    if supply < total_water_needed:
        # Scarcity: increase bid proportional to shortage
        shortage_factor = (total_water_needed - supply) / total_water_needed
        base_bid *= (1.0 + shortage_factor)
    
    # Outbid yesterday's high if reasonable
    if max_yesterday_bid > 0 and max_yesterday_bid > base_bid:
        base_bid = max_yesterday_bid + 5.0  # small increment to outbid
    
    # Clamp to budget and minimum 1
    final_bid = min(budget, max(1.0, base_bid))
    # Ensure we can afford it (budget is already a limit)
    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Gather yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp_id, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Base bid: 45% of daily salary (~63)
    base_bid = DAILY_SALARY * 0.45
    
    # Adjust based on HP
    if hp <= 2:
        # desperate: bid higher
        base_bid = DAILY_SALARY * 0.8
    elif no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.7
    elif hp >= 8:
        # healthy, can be more conservative
        base_bid = DAILY_SALARY * 0.35
    
    # Adjust based on yesterday's highest bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        if max_prev > DAILY_SALARY * 0.85:
            # Opponents were aggressive yesterday, likely to lower today -> we can bid slightly lower
            base_bid = min(base_bid, DAILY_SALARY * 0.5)
        elif max_prev < DAILY_SALARY * 0.3:
            # Opponents were very low yesterday, may be desperate today -> bid moderate
            base_bid = max(base_bid, DAILY_SALARY * 0.55)
    
    # Ensure bid is within budget and does not exceed daily salary
    bid = min(budget, base_bid, DAILY_SALARY * 0.9)
    bid = max(bid, 1)  # at least 1
    
    # If no water for many days, ensure we get water even if bid higher
    if no_water_days >= 3 and budget >= DAILY_SALARY * 0.8:
        bid = min(budget, DAILY_SALARY * 0.85)
    
    # Convert to float and return
    return float(bid)
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

    # Ensure budget is not negative
    budget = my_status['budget']
    hp = my_status['hp']
    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Collect yesterday's bids from opponents who have previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid as fraction of salary, adjusted by supply scarcity and hp
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 when min, 1 when max
    base_factor = 0.5 + 0.3 * (1 - supply_ratio)  # higher when supply low

    # Adjust based on hp: bid more if low hp
    if hp <= 2:
        hp_factor = 1.0
    elif hp <= 4:
        hp_factor = 0.9
    else:
        hp_factor = 0.8

    # Determine target bid from yesterday's data
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If someone bid very high yesterday, they may be aggressive today
        if max_prev_bid >= DAILY_SALARY * 0.85:
            # Aggressive opponents: bid high to compete
            target_bid = DAILY_SALARY * min(0.95, base_factor * hp_factor * 1.1)
        else:
            # Moderate: slightly above their max
            target_bid = max(DAILY_SALARY * base_factor * hp_factor, max_prev_bid + 2.0)
    else:
        # First day or no previous data: bid a moderate amount
        target_bid = DAILY_SALARY * 0.7 * hp_factor

    # Final bid limited to budget and ensure at least some small positive to enter
    final_bid = min(budget, max(target_bid, 1.0))
    #
"""
