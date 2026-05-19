# ============================================================
# Experiment: exp_006
# Agent: Eric
# Source: exp_006
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    wage = 140
    if my_status['hp'] <= 2:
        bid = wage * 0.9
    elif my_status['hp'] <= 4:
        bid = wage * 0.7
    else:
        bid = wage * 0.6
    if supply < 18:
        bid = max(bid, wage * 0.75)
    bid = min(bid, my_status['budget'])
    bid = max(0, bid)
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
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Determine opponents' perceived aggression based on yesterday's trace and current hp
    max_yesterday_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            max_yesterday_bid = max(max_yesterday_bid, prev['bid'])

    # Estimate desperation bids from opponents with low hp
    desperation_threshold = 3
    max_desperation_bid = 0.0
    for opp in alive_opponents:
        if opp['hp'] <= desperation_threshold:
            # Assume they will bid up to 80% of their salary
            max_desperation_bid = max(max_desperation_bid, opp['daily_salary'] * 0.8)

    # Expected competitor bid: combine yesterday's highest bid and desperation bids
    expected_comp_bid = max(max_yesterday_bid, max_desperation_bid)

    # Decide my target bid based on my own health
    # Low hp: need water, outbid expected competitor by a margin
    if hp <= 2 or no_water_days >= 1:
        target_bid = expected_comp_bid + 2.0
        # Cap at 90% of salary
        target_bid = min(target_bid, DAILY_SALARY * 0.9)
    elif hp <= 5:
        # Moderate: try to match or slightly undercut to save budget
        # If supply is abundant, we can bid lower
        if supply >= 20:
            target_bid = expected_comp_bid * 0.9
        else:
            target_bid = expected_comp_bid + 1.0
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

    # Base bid: proportion of daily salary, scaled by scarcity
    scarcity_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid = DAILY_SALARY * (0.5 + 0.4 * scarcity_factor)

    # Increase bid if HP low or dehydrated
    if hp <= 2 or no_water_days > 0:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif hp <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # On first day, be conservative or aggressive based on supply
    if day == 1:
        if supply < 18:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.5)

    # Ensure bid does not exceed budget
    bid = min(budget, base_bid)
    # Ensure at least a small bid if alive
    if hp > 0 and budget > 0:
        bid = max(bid, 1.0)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # constants
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = int(day_context['supply'])
    day = int(day_context['day'])
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Filter alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opponents.append(o)

    # Extract last bids from opponents' previous_trace
    last_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            last_bids.append(float(trace['bid']))

    # Estimate how many units we need (max possible units = supply // WATER_REQ)
    max_units = int(supply // WATER_REQ)
    if max_units == 0:
        # no water available, bid minimal to save budget
        return min(my_budget, 0.0)

    # Base bid: if we are desperate (no water for too long or hp low)
    desperate = (my_hp <= 2) or (no_water_days >= 2)

    # If we have many opponents, competition is high
    num_alive = len(alive_opponents)

    # Determine target bid based on desperation and supply
    if desperate:
        # need water badly, bid high but not more than budget
        target = DAILY_SALARY * 0.95
    elif num_alive <= 1:
        # few opponents, can bid low
        target = DAILY_SALARY * 0.3
    else:
        # moderate competition
        target = DAILY_SALARY * 0.6

    # Adjust based on opponents' last bids (if available)
    if last_bids:
        max_last = max(last_bids)
        # If opponents were aggressive, we may need to raise or lower
        # Here we assume they might continue similar pattern
        if max_last > DAILY_SALARY * 0.85 and not desperate:
            # aggressive opponents, but we are not desperate: save budget
            target = min(target, DAILY_SALARY * 0.4)
        elif my_hp > 4 and max_last < DAILY_SALARY * 0.5:
            # opponents are low, we can bid low
            target = min(target, DAILY_SALARY * 0.3)

    # Ensure bid does not exceed budget
    bid = min(my_budget, max(target, 0.0))

    # On first day or if we have no information, use a safe bid
    if day <= 1:
        bid = min(my_budget, DAILY_SALARY * 0.6)

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    SUPPLY = day_context['supply']
    DAY = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            yesterday_bids.append(trace['bid'])
    max_yesterday = max(yesterday_bids) if yesterday_bids else 0
    # Determine safe bid
    if hp <= 2:
        # Urgent need water - bid high but not exceed budget
        target = max(DAILY_SALARY * 0.9, max_yesterday + 2)
        return int(min(budget, target))
    elif SUPPLY < 20:
        # Moderate supply, need to secure water
        if max_yesterday > DAILY_SALARY * 0.6 or (hp <= 5):
            target = max(DAILY_SALARY * 0.7, max_yesterday + 1.5)
            return int(min(budget, target))
        else:
            target = DAILY_SALARY * 0.5
            return int(min(budget, target))
    else:
        # High supply, can bid low
        if hp <= 4 or max_yesterday > DAILY_SALARY * 0.8:
            target = DAILY_SALARY * 0.6
        else:
            target = DAILY_SALARY * 0.4
        return int(min(budget, target))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    salary = 140
    water_req = 8
    # Determine max winners from supply
    max_winners = int(supply // water_req)
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in opponents_status.values():
        if opp['alive']:
            trace = opp.get('previous_trace', {})
            if trace and trace.get('bid') is not None:
                prev_bids.append(trace['bid'])
    
    # Base bid: aggressive if HP critical, else conservative
    if hp <= 2:
        base_bid = salary * 0.9
    elif hp <= 4:
        base_bid = salary * 0.7
    else:
        base_bid = salary * 0.5
    
    # Adapt to yesterday's highest bid to undercut if possible
    if prev_bids:
        highest_prev = max(prev_bids)
        # If highest was very high, we can bid much lower and still get water if others repeat
        if highest_prev >= salary * 0.85:
            # Opponents likely exhausted budget; be conservative
            target = max(base_bid, salary * 0.3)
        else:
            # Slightly above average of yesterday's bids to win
            avg_prev = sum(prev_bids) / len(prev_bids)
            target = max(base_bid, avg_prev + 2)
        # Ensure we don't exceed budget
        bid = min(budget, target)
    else:
        # First day: use base
        bid = min(budget, base_bid)
    
    # Ensure bid is non-negative and not insane
    bid = max(0, min(bid, budget))
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev > 200:
            if hp > 3:
                return min(budget, DAILY_SALARY * 0.3)
            else:
                return min(budget, DAILY_SALARY * 0.8)
        elif highest_prev > DAILY_SALARY:
            return min(budget, max(DAILY_SALARY * 0.4, highest_prev * 0.5))
    if hp <= 2:
        return min(budget, DAILY_SALARY * 0.9)
    if hp <= 4:
        return min(budget, DAILY_SALARY * 0.7)
    base_bid = DAILY_SALARY * 0.5
    # adjust for supply: more supply means lower bid
    num_opponents = len(alive_opponents)
    # ensure int for index if needed
    adjustment = supply / (WATER_REQ * (num_opponents + 1))
    if adjustment > 1.5:
        base_bid = DAILY_SALARY * 0.4
    elif adjustment < 0.8:
        base_bid = DAILY_SALARY * 0.7
    return min(budget, base_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    SUPPLY = int(day_context['supply'])
    DAY = int(day_context['day'])
    HP = my_status['hp']
    BUDGET = my_status['budget']
    NO_WATER = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # solo: just bid enough to get water, but conserve
        needed = max(0, (WATER_REQ - SUPPLY) * 0.1 + 1)  # irrelevant, safe
        return min(BUDGET, 0.5 * DAILY_SALARY)

    # Gather yesterday bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate cost to beat opponents based on yesterday
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / len(yesterday_bids)
        max_prev = max(yesterday_bids)
    else:
        avg_prev = DAILY_SALARY * 0.5
        max_prev = DAILY_SALARY * 0.7

    # Determine urgency
    urgent = (HP <= 2) or (NO_WATER > 0)
    semi_urgent = (HP <= 4) or (NO_WATER >= 1)

    # Estimate water needed and number of alive players
    alive_count = len(alive_opponents)
    total_players = alive_count + 1  # including me
    # Possible water per player if equal split
    equitable_supply = SUPPLY / total_players
    # My requirement is fixed 8
    # Risk: if supply < total * 8, we must outbid

    if urgent:
        # We must get water at all costs
        bid = min(BUDGET, max(DAILY_SALARY * 0.9, max_prev * 1.1))
    elif semi_urgent:
        # Be competitive
        target_bid = max(avg_prev * 0.9, DAILY_SALARY * 0.4)
        if yesterday_bids:
            # Slightly above average to increase chances
            bid = min(BUDGET, target_bid + 2.0)
        else:
            bid = min(BUDGET, DAILY_SALARY * 0.55)
    else:
        # Healthy: conserve budget, bid just enough to potentially get water
        # Aim to be in middle of pack based on yesterday
        bid = min(BUDGET, max(DAILY_SALARY * 0.3, avg_prev * 0.8))

    # Ensure we don't exceed budget or go negative
    bid = max(0, min(BUDGET, bid))
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])
    
    WATER_REQ = 8
    DAILY_SALARY = 140.0
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0
    
    alive_opponents = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    
    # Collect yesterday's bids from alive opponents
    prev_bids = []
    for opp in alive_opponents.values():
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            prev_bids.append(float(trace['bid']))
    
    # Estimate winning bid based on supply
    # Normalize supply to [0,1] where 0 is scarce, 1 abundant
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    
    # Base bid: when supply is low, bid high; high supply, bid low
    base_bid = DAILY_SALARY * (1.0 - 0.5 * supply_ratio)
    
    # Adjust based on HP and no_water_days
    if hp <= 2 or no_water > 0:
        # Must win: bid aggressively
        target_bid = min(budget, DAILY_SALARY * 0.95)
    else:
        # If we have healthy HP, we can be more conservative
        target_bid = min(budget, base_bid)
    
    # Also consider beating yesterday's highest bid among opponents, but not excessively
    if prev_bids:
        max_prev_bid = max(prev_bids)
        # If our target is less than max_prev_bid, we may need to increase
        # but don't go overboard; assume opponents might lower
        if max_prev_bid > target_bid:
            # Increase target but cap at budget
            target_bid = min(budget, max(target_bid, max_prev_bid * 0.85))
    
    # Ensure we don't bid more than budget
    final_bid = max(0, target_bid)
    
    # If supply is extremely low and we have budget, bid high
    if supply <= 17 and hp <= 5:
        final_bid = min(budget, DAILY_SALARY * 0.9)
    
    return final_bid
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
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Gather yesterday's bids from previous_trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])
    
    # Estimate winners count
    max_winners = int(supply // WATER_REQ)
    num_bidders = len(alive_opponents) + 1  # including self
    
    # Base bid based on urgency
    if hp <= 2:
        # Critical: need water
        if budget < DAILY_SALARY * 0.5:
            bid = budget
        else:
            bid = min(budget, DAILY_SALARY * 0.8)
    elif hp <= 5:
        # Moderate need
        bid = min(budget, DAILY_SALARY * 0.6)
    else:
        # Comfortable: try to save money
        if prev_bids:
            highest_prev = max(prev_bids)
            # Aim slightly above highest previous if possible, but not too high
            target = max(highest_prev + 1, DAILY_SALARY * 0.3)
            bid = min(budget, target)
        else:
            # No prior info: conservative bid
            bid = min(budget, DAILY_SALARY * 0.4)
    
    # Adjust for supply tightness
    if supply < MIN_SUPPLY + 3 and num_bidders > max_winners:
        # Higher competition for limited water
        bid = min(budget, bid * 1.2 if hp > 2 else bid)
    
    # Ensure we don't exceed budget
    return max(0.0, min(budget, round(bid, 2)))
"""
