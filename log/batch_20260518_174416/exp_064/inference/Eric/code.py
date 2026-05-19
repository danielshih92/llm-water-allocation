# ============================================================
# Experiment: exp_064
# Agent: Eric
# Source: exp_064
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
    no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine yesterday's highest bid among alive opponents
    max_yesterday_bid = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid = prev['bid']
            if bid > max_yesterday_bid:
                max_yesterday_bid = bid
    
    # If no data, use default
    if max_yesterday_bid == 0:
        # Default: bid based on need
        if hp <= 3 or no_water_days >= 2:
            bid = min(budget, DAILY_SALARY * 0.8)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
        return bid
    
    # Adaptive based on yesterday's highest bid
    # If opponent bid high, assume they need water; we can bid just above if we need more
    if hp <= 3 or no_water_days >= 2:
        # Need ensure water: bid enough to win against yesterday's top bid
        target_bid = max(max_yesterday_bid + 1, DAILY_SALARY * 0.7)
        bid = min(budget, target_bid)
    else:
        # Conserve: bid lower than yesterday's top bid to save money
        # But avoid overbidding unnecessarily
        temp = max_yesterday_bid - 2
        if temp < DAILY_SALARY * 0.3:
            temp = DAILY_SALARY * 0.3
        bid = min(budget, temp)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)
    
    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    for oid, opp in alive_opponents.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    
    # Compute water need factor
    need_factor = 1.0 - (hp / 10.0)  # 1 when hp=0, 0.5 when hp=5, 0 when hp=10
    supply_scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 1 when supply=15, 0 when supply=25
    
    # Base bid: conservative when healthy
    if hp > 5:
        base_bid = DAILY_SALARY * (0.25 + 0.1 * supply_scarcity)
    elif hp > 2:
        base_bid = DAILY_SALARY * (0.4 + 0.2 * supply_scarcity)
    else:
        base_bid = DAILY_SALARY * (0.7 + 0.3 * supply_scarcity)
    
    # Adjust based on yesterday's highest bid: if someone bid very high, we need to match if we need water
    if highest_prev > 100:
        aggressive_floor = DAILY_SALARY * 0.6
        if hp <= 2:
            # Must win: bid slightly above highest_prev if affordable
            bid = min(budget, max(highest_prev + 1, aggressive_floor))
        else:
            # Slightly undercut if possible
            bid = min(budget, max(aggressive_floor, base_bid))
    else:
        bid = min(budget, base_bid)
    
    # Ensure bid is not negative
    bid = max(0.0, bid)
    # Cap at budget
    bid = min(budget, bid)
    # Round to 2 decimals
    bid = round(bid, 2)
    return bid
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Gather yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine last day's highest bid among opponents
    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid determined by urgency
    # Urgency: need water if no_water_days >= 1 or hp is critically low
    urgency = 0.0
    if no_water_days > 0:
        urgency += 0.3 * no_water_days
    if hp <= 3:
        urgency += 0.5
    elif hp <= 5:
        urgency += 0.3
    else:
        urgency += 0.1

    # Safety cap: never bid more than 90% of budget or 2x salary, whichever is smaller
    max_bid = min(budget * 0.9, DAILY_SALARY * 2.0)

    # If we are desperate, bid just above highest previous bid (if we can afford)
    if urgency >= 0.8:
        target_bid = highest_prev + 2.0
        return min(max_bid, target_bid)

    # Moderate urgency: bid a bit above average of previous highest and our salary-based estimate
    if urgency >= 0.4:
        # Strategic bid: if they bid very high, undercut by 10% to let them waste
        if highest_prev > DAILY_SALARY * 1.2:
            target_bid = highest_prev * 0.9
        else:
            target_bid = max(highest_prev + 1.0, DAILY_SALARY * 0.6)
        return min(max_bid, target_bid)

    # Low urgency: bid conservatively
    # If yesterday's highest bid was very high, we can even bid lower to save
    if highest_prev > DAILY_SALARY * 1.3:
        target_bid = DAILY_SALARY * 0.4
    else:
        target_bid = DAILY_SALARY * 0.5
    return min(budget, target_bid)
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
    
    # Collect last bids from alive opponents' traces
    last_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_val = float(prev['bid'])
            if bid_val > 0:
                last_bids.append(bid_val)
    
    # Determine pressure from yesterday's highest bid
    high_pressure = 0
    if last_bids:
        high_pressure = max(last_bids)
    
    # Base bid: around 60% of salary, adjusted for supply
    supply_ratio = (supply - 15) / 10.0  # 0 when supply=15, 1 when supply=25
    base_bid = DAILY_SALARY * (0.5 + 0.1 * (1 - supply_ratio))  # 0.5-0.6 range
    
    # Urgency: if hp is low or we are close to dying
    if hp <= 2 or no_water_days >= 2:
        urgent_boost = DAILY_SALARY * 0.3
        base_bid += urgent_boost
    
    # React to opponent pressure
    if high_pressure > 0:
        if hp > 3:
            # If healthy, undercut the high bid slightly
            target = min(base_bid, high_pressure * 0.95)
        else:
            # If vulnerable, try to outbid the high bid by a small margin
            target = max(base_bid, high_pressure + 1)
    else:
        target = base_bid
    
    # Ensure we don't bid more than budget or too little
    min_bid = DAILY_SALARY * 0.2
    bid = max(min_bid, min(budget - 1, target))
    
    return int(round(bid))
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Determine base bid from opponents' past behavior
    if prev_bids:
        avg_prev = sum(prev_bids) / len(prev_bids)
        max_prev = max(prev_bids)
        # If someone was very aggressive yesterday, be cautious
        if max_prev >= DAILY_SALARY * 0.8:
            # They might continue, but we need water only if HP low
            if hp <= 2:
                # Need water badly, outbid slightly
                target = max_prev + 2.0
            else:
                # Stay below aggressive bidders
                target = DAILY_SALARY * 0.45
        else:
            # Normal competition: bid slightly above average or enough for survival
            target = max(avg_prev + 1.0, DAILY_SALARY * 0.35)
    else:
        # No history, conservative start
        target = DAILY_SALARY * 0.35
    
    # Adjust based on own HP and budget
    if hp <= 0:
        # Critical: must get water
        target = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 2:
        target = max(target, min(budget, DAILY_SALARY * 0.8))
    
    # Ensure we do not exceed budget
    bid = min(budget, target)
    
    # Safety: never bid more than salary on first day, and keep some reserve
    if day == 1:
        bid = min(bid, DAILY_SALARY * 0.5)
    
    # Ensure non-negative
    return max(0, bid)
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
    no_water = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    last_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            last_bids.append(trace['bid'])
    portions = supply // WATER_REQ
    if hp <= 2 or no_water >= 1:
        if last_bids:
            target = max(last_bids) * 1.1
        else:
            target = DAILY_SALARY * 0.9
        target = min(target, budget * 0.9)
        return max(1, target)
    elif hp <= 4:
        if last_bids:
            target = max(last_bids) * 0.95
        else:
            target = DAILY_SALARY * 0.6
        if portions <= 1:
            target *= 1.2
        return min(budget, max(1, target))
    else:
        if portions >= 3:
            return DAILY_SALARY * 0.3
        else:
            if last_bids:
                target = max(last_bids) * 0.8
            else:
                target = DAILY_SALARY * 0.4
            return min(budget, max(1, target))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        bid = trace.get('bid')
        if bid is not None:
            prev_bids.append(bid)
    
    if prev_bids:
        max_prev_bid = max(prev_bids)
    else:
        max_prev_bid = 0
    
    if hp <= 2 or supply < 20:
        target_bid = max(DAILY_SALARY * 0.85, max_prev_bid + 5)
    else:
        target_bid = max(DAILY_SALARY * 0.5, max_prev_bid + 2)
    
    return min(budget, target_bid)
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
    
    # Determine number of alive opponents
    alive_opps = [o for o in opponents_status.values() if o['alive']]
    num_alive = len(alive_opps)
    
    # Collect yesterday's bids if available
    prev_bids = []
    for opp in alive_opps:
        trace = opp.get('previous_trace')
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Calculate supply scarcity factor (higher when supply is low)
    supply = day_context['supply']
    scarcity_factor = 1.0 + (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) * 0.2  # range 1.0 to 1.2
    
    # Base bid as fraction of salary, dependent on HP
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.55
    
    # Adjust based on number of alive opponents
    num_factor = 1.0 + (num_alive - 0.5) * 0.1  # more opponents, slightly higher
    adjusted_bid = base_bid * scarcity_factor * num_factor
    
    # If we have info on yesterday's high bids, outbid the max by small margin
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev > adjusted_bid:
            adjusted_bid = max_prev + 1.0
    
    # Ensure bid is within budget and not too low
    final_bid = max(adjusted_bid, DAILY_SALARY * 0.2)  # minimum 28
    final_bid = min(final_bid, budget, DAILY_SALARY * 0.95)
    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    
    max_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            max_prev_bid = max(max_prev_bid, float(prev['bid']))
    
    possible_winners = int(supply // WATER_REQ)
    
    urgent = (hp <= 2) or (no_water_days > 0)
    if urgent:
        # Need to win: bid slightly above highest previous or a safe amount
        target = max(DAILY_SALARY * 0.85, max_prev_bid + 2.0)
        return min(budget, target)
    else:
        # Not urgent: try to win cheaply or save
        if max_prev_bid > DAILY_SALARY * 0.8:
            # High competition, maybe avoid if we can
            if hp >= 4:
                return min(budget, DAILY_SALARY * 0.3)
            else:
                return min(budget, max(DAILY_SALARY * 0.5, max_prev_bid + 1.0))
        else:
            return min(budget, DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Determine needed water portions (supply might be > needed)
    max_water_units = int(supply // WATER_REQ)  # explicit int
    if max_water_units <= 0:
        # Should not happen, but safety
        return min(budget, DAILY_SALARY * 0.1)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    # Gather yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy: how much are we willing to pay for a unit?
    # HP urgency: if no_water_days >= 1, need water badly
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.5
    elif no_water_days == 1:
        urgency = 0.8
    else:
        urgency = 0.5
    # Adjust by HP
    if hp <= 2:
        urgency += 0.8
    elif hp <= 5:
        urgency += 0.3

    # Compute target price per unit based on supply and opponents
    # If many opponents, competition is high, we may need to bid more
    num_alive = len(alive_opponents)
    competition_factor = 1.0 + 0.1 * max(0, num_alive - 2)

    # Use yesterday's max bid as anchor if available
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If they bid high, we may need to match or exceed if urgent
        if urgency > 1.0 and max_yesterday > DAILY_SALARY * 0.7:
            target = max_yesterday + 2.0
        else:
            target = max(DAILY_SALARY * 0.3, max_yesterday * 0.9 + 1.0)
    else:
        # First day: use safe default
        target = DAILY_SALARY * (0.3 + 0.2 * urgency)

    # Adjust for supply: if supply is low, water is scarce -> bid higher per unit
    supply_ratio = supply / 20.0  # mid of range
    target = target * (1.0 + 0.2 * (1.0 - supply_ratio))

    # Scale by competition
    target = target * competition_factor

    # We need at least one unit to survive. Ensure we bid enough to get water
    # Bidding more than budget is pointless
    bid = min(budget, max(DAILY_SALARY * 0.2, target))
    # Also ensure we don't overbid when no urgency and high hp
    if urgency < 0.6 and hp > 6 and num_alive <= 2:
        bid = min(bid, DAILY_SALARY * 0.4)

    return float(bid)
"""
