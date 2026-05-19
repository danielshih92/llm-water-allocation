# ============================================================
# Experiment: exp_004
# Agent: Cindy
# Source: exp_004
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimally to save budget
    if num_alive_opponents == 0:
        return float(min(my_budget, 1))

    # Base bid logic: Prioritize survival if low on water
    if my_no_water_days >= 2: # Critical: must get water
        bid = DAILY_SALARY * 0.95
    elif my_no_water_days == 1: # Urgent: need water soon
        bid = DAILY_SALARY * 0.75
    else: # Healthy: try to conserve budget
        bid = DAILY_SALARY * 0.5

    # React to yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high yesterday, competition is fierce
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_no_water_days > 0: # I need water, so I must compete aggressively
                bid = max(bid, highest_prev_bid + 5)
            else: # I'm healthy, can try to outbid slightly or stay conservative
                bid = min(bid, highest_prev_bid * 1.05) # Try to win, but not overspend if not desperate
        # If opponents bid low, try to get water cheaply
        elif highest_prev_bid <= DAILY_SALARY * 0.3:
            bid = min(bid, highest_prev_bid + 10) # Bid a bit more than their low bid
        # For moderate bids, the base bid strategy is maintained

    # Adjust bid based on supply vs demand
    # Simple heuristic: if supply is very low, increase bid
    if current_supply < WATER_REQ * (num_alive_opponents + 1) * 0.8: # Supply is tight relative to total need
        bid *= 1.1
    elif current_supply > WATER_REQ * (num_alive_opponents + 1) * 1.2: # Supply is abundant
        bid *= 0.9

    # Last day desperation: If it's the final day and I still need water, go all in
    if current_day == EPISODE_DAYS and my_no_water_days > 0:
        bid = my_budget

    # Ensure bid is within budget and at least 1
    final_bid = max(1.0, min(float(my_budget), float(bid)))

    return float(final_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # My current status
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # Day context
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water (assuming water has some cost)
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1) 

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.65 # A moderately aggressive starting point

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_hp <= 6: # Moderate HP
        base_bid = DAILY_SALARY * 0.75

    # Adjust bid based on 'no_water_days' - increase urgency
    if my_no_water_days > 0:
        base_bid += DAILY_SALARY * 0.05 * my_no_water_days # Increase bid for each day without water
        base_bid = min(base_bid, DAILY_SALARY * 0.98) # Cap this increase to prevent overbidding

    # Adjust bid based on opponents' previous bids
    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        avg_opp_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If max opponent bid was very high, we might need to outbid to stay competitive
        if max_opp_bid >= DAILY_SALARY * 0.8: # Very aggressive opponent threshold
            base_bid = max(base_bid, max_opp_bid + (DAILY_SALARY * 0.05)) # Try to outbid by a small margin
        elif avg_opp_bid >= DAILY_SALARY * 0.6: # Generally competitive market
            base_bid = max(base_bid, avg_opp_bid + (DAILY_SALARY * 0.02)) # Slightly above average
        else: # Opponents were not very aggressive yesterday
            # If my HP is good, try to save money, but don't go too low given scarcity
            if my_hp > 6:
                base_bid = min(base_bid, DAILY_SALARY * 0.6) # Try to get water cheaper
            else: # Still need water, maintain a decent bid
                base_bid = max(base_bid, DAILY_SALARY * 0.65)
    
    # Adjust bid based on supply scarcity and number of competitors
    # CRITICAL INDEX RULE: supply is float, ensure int() for division if used as index or count
    num_full_slots = int(current_supply // WATER_REQ)

    # If water is very scarce (e.g., barely enough for one or two) and many competitors, bid higher
    if current_supply <= (WATER_REQ + 5) and num_alive_opponents >= 2: 
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif current_supply <= (WATER_REQ + 10) and num_alive_opponents >= 1: 
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Final bid must be within budget and positive
    final_bid = min(my_budget, base_bid)
    final_bid = max(0.0, final_bid) # Ensure bid is not negative

    # Ensure bid is at least 1 to participate if budget allows and bid is 0
    if final_bid == 0 and my_budget > 0:
        final_bid = min(my_budget, 1.0)
    
    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_bid = 0.0

    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        current_bid = DAILY_SALARY * 0.8
    else:
        current_bid = DAILY_SALARY * 0.6

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid >= DAILY_SALARY * 0.7:
                current_bid = max(current_bid, highest_prev_bid + 1.0)
            else:
                current_bid = max(current_bid, highest_prev_bid + 0.5)
        else:
            # If no previous bids, use a sensible default if not already set high by HP
            current_bid = max(current_bid, DAILY_SALARY * 0.5)

        total_players = num_alive_opponents + 1
        water_needed_total = total_players * WATER_REQ
        
        if day_context['supply'] < water_needed_total:
            if current_bid < DAILY_SALARY * 0.85:
                current_bid = min(DAILY_SALARY * 0.85, current_bid * 1.1)
        else:
            if my_status['hp'] > 5 and current_bid > DAILY_SALARY * 0.5:
                current_bid = max(DAILY_SALARY * 0.5, current_bid * 0.9)

    final_bid = min(my_status['budget'], current_bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimum to get water and save budget
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine if supply is tight for the number of competitors
    total_expected_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_expected_water_demand += opp['water_requirement']

    is_supply_sufficient_for_all = day_context['supply'] >= total_expected_water_demand
    
    # CRITICAL: If HP is very low or no water for days, bid aggressively to survive
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.99)

    # If no previous bids from opponents (e.g., Day 1 or they didn't bid), use a default strategy
    if not yesterday_bids:
        if is_supply_sufficient_for_all:
            # Enough for everyone, bid moderately low to test the waters
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        else:
            # Scarcity, bid moderately high to secure water
            return min(my_status['budget'], DAILY_SALARY * 0.6)

    # Strategy based on yesterday's bids and current state
    highest_prev_bid = max(yesterday_bids)
    lowest_prev_bid = min(yesterday_bids)
    average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

    # Check for high pressure from opponents (if their highest bid was very high)
    high_pressure_from_opponents = highest_prev_bid >= DAILY_SALARY * 0.85

    # If supply is tight (not enough for everyone)
    if not is_supply_sufficient_for_all:
        if my_status['hp'] <= 4: # Low HP, need water urgently but not critical
            # Bid slightly above highest previous bid or high default if no high pressure
            return min(my_status['budget'], highest_prev_bid + 5 if high_pressure_from_opponents else DAILY_SALARY * 0.85)
        else: # HP is okay, but supply is tight, need to compete
            if high_pressure_from_opponents:
                # Opponents are bidding high, I need to match or slightly exceed to win
                return min(my_status['budget'], highest_prev_bid + 2)
            else:
                # Opponents not bidding too high, but supply is tight, bid above average
                return min(my_status['budget'], max(average_prev_bid + 10, DAILY_SALARY * 0.7))
    
    # If supply is sufficient for all, try to save money
    else:
        if my_status['hp'] <= 3: # Still low HP, even with sufficient supply, ensure win
            # Bid slightly above highest previous bid to be safe, but not too high
            return min(my_status['budget'], max(highest_prev_bid + 1, DAILY_SALARY * 0.5))
        else:
            # Enough water, bid just above the lowest previous bid or a safe low amount to save budget
            return min(my_status['budget'], max(lowest_prev_bid + 1, DAILY_SALARY * 0.25))

    # Fallback bid (should not be reached under normal circumstances)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high (e.g., > 85% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 5: # If HP is relatively good, try to conserve
                return min(my_status['budget'], DAILY_SALARY * 0.5) # Bid moderately low
            else: # HP is low, must compete aggressively
                return min(my_status['budget'], max(highest_prev_bid + 5, DAILY_SALARY * 0.95)) # Bid very high to win
        else: # Opponents not bidding excessively high
            # Bid slightly above their highest to try and win, but not overspend
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 2.5))

    # If no yesterday bids (e.g., day 1 or opponents didn't bid)
    # Adjust bid based on my HP
    if my_status['hp'] <= 3: # Critical HP
        return min(my_status['budget'], DAILY_SALARY * 0.9) # High bid for survival
    elif my_status['hp'] <= 6: # Low HP
        return min(my_status['budget'], DAILY_SALARY * 0.75) # Moderate-high bid
    else: # Good HP
        return min(my_status['budget'], DAILY_SALARY * 0.6) # Moderate bid to conserve
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    remaining_days = EPISODE_DAYS - day_context['day'] + 1

    # If HP is critical, bid aggressively
    if my_status['hp'] <= 3:
        if remaining_days <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.99)
        return min(my_status['budget'], DAILY_SALARY * 0.9)

    # If HP is good, react to opponents' previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents are bidding very high
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            # If my HP is good and many days left, consider saving budget
            if my_status['hp'] > 5 and remaining_days > 2:
                return min(my_status['budget'], DAILY_SALARY * 0.7)
            else:
                # HP is good but not excellent, or it's getting late, so compete
                return min(my_status['budget'], highest_prev_bid + 2.0)

        # If opponents are bidding moderately high
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            return min(my_status['budget'], highest_prev_bid + 1.0)

        # If opponents are bidding low
        else:
            # If my HP is good, bid reasonably above their low bid
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 5.0))
    
    # Initial days or if no previous bids from alive opponents
    if my_status['hp'] <= 5:
        return min(my_status['budget'], DAILY_SALARY * 0.75)
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_BID_TO_WIN = 1.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    bid_amount = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] > 0:
        bid_amount = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 5:
        bid_amount = DAILY_SALARY * 0.8

    if max_yesterday_bid > 0:
        if max_yesterday_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 7:
                bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
            else:
                bid_amount = max(bid_amount, max_yesterday_bid + 5)
        else:
            bid_amount = max(bid_amount, max_yesterday_bid + 1.5)
            if my_status['hp'] > 5 and bid_amount < DAILY_SALARY * 0.6:
                bid_amount = DAILY_SALARY * 0.6

    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    supply_factor = 1.0
    if day_context['supply'] < total_water_needed:
        supply_factor = 1.20
    elif day_context['supply'] < (total_water_needed + WATER_REQ):
        supply_factor = 1.10
    elif day_context['supply'] > (total_water_needed * 1.5):
        supply_factor = 0.90
    
    bid_amount *= supply_factor

    final_bid = min(my_status['budget'], bid_amount)

    if final_bid < MIN_BID_TO_WIN and my_status['budget'] >= MIN_BID_TO_WIN:
        final_bid = MIN_BID_TO_WIN
    elif final_bid < MIN_BID_TO_WIN and my_status['budget'] < MIN_BID_TO_WIN:
        final_bid = my_status['budget']

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # 1. Determine base bid and adjust for urgency
    base_bid = DAILY_SALARY * 0.6 # A solid base bid

    # Survival mode: if HP is very low or no water for 1+ days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Bid very aggressively to survive
        base_bid = DAILY_SALARY * 0.95
    elif day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days, increase aggression slightly
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 4: # Moderate danger
        base_bid = DAILY_SALARY * 0.8

    # 2. Analyze opponent's previous bids from current meta-round
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 3. Adjust bid based on opponent behavior and supply
    final_bid = base_bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If supply is scarce (less than enough for 2 agents' full requirement)
        if day_context['supply'] < WATER_REQ * 2:
            # If opponents were bidding high, bid slightly above the highest to win
            if highest_prev_bid >= DAILY_SALARY * 0.7: # High competition threshold
                final_bid = max(base_bid, highest_prev_bid + 5.0) # Bid above previous high
            else:
                final_bid = max(base_bid, highest_prev_bid + 1.0) # Slightly above if not extremely high
        else: # Supply is more abundant (enough for 2+ agents)
            # If opponents were bidding high, we can still be competitive but maybe not overbid too much
            if highest_prev_bid >= DAILY_SALARY * 0.7:
                final_bid = max(base_bid, highest_prev_bid * 1.05) # Slightly more than previous high
            else:
                final_bid = max(base_bid, highest_prev_bid + 1.0) # Just a bit more than previous
    
    # Ensure bid is at least a minimum value and capped by budget
    final_bid = max(1.0, min(final_bid, my_status['budget']))

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    
    # Base bid: A moderate amount.
    bid = DAILY_SALARY * 0.55 # Slightly higher than half salary

    # 1. Health-based adjustment (Priority 1)
    if my_status['hp'] <= 2: # Critical health, must get water
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low health, need water
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= EPISODE_DAYS - day_context['day'] + 3: # Very healthy, can conserve
        bid = DAILY_SALARY * 0.4
    
    # 2. Opponent reaction based on yesterday's highest bid (Priority 2, adjusts base bid)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            if my_status['hp'] > 4: # If I'm relatively healthy, try to outsmart or conserve
                bid = min(bid, highest_prev_bid * 0.9) # Try to get it cheaper if they overbid
                bid = max(bid, DAILY_SALARY * 0.4) # But not too low
            else: # Low HP, must be aggressive
                bid = max(bid, highest_prev_bid + 1.0)
                bid = min(bid, DAILY_SALARY * 0.98) # Cap it
        
        elif highest_prev_bid <= DAILY_SALARY * 0.4: # Opponents were very conservative
            if my_status['hp'] > 4:
                bid = min(bid, highest_prev_bid + 1.0) # Slightly outbid, conserve
                bid = max(bid, DAILY_SALARY * 0.2) # Don't bid too low
            else:
                bid = max(bid, highest_prev_bid + 5.0) # Be a bit more aggressive
                bid = min(bid, DAILY_SALARY * 0.7) # Cap it
        else: # Moderate opponent bids
            bid = max(bid, highest_prev_bid + 1.0) # Slightly outbid
            bid = min(bid, DAILY_SALARY * 0.9) # Cap it

    # 3. Supply-demand adjustment (Priority 3, fine-tunes the bid)
    total_water_needed = (num_alive_opponents + 1) * WATER_REQ
    if day_context['supply'] < total_water_needed:
        # Supply is scarce, increase bid pressure
        bid = max(bid, DAILY_SALARY * 0.6) # Ensure a minimum higher bid
        if day_context['supply'] < WATER_REQ: # Extremely scarce, less than one full water
             bid = max(bid, DAILY_SALARY * 0.8) # Bid very high to get some water

    # Final checks
    final_bid = max(0.0, bid) # Bid cannot be negative
    final_bid = min(final_bid, my_status['budget']) # Bid cannot exceed budget

    # If no opponents, bid a minimal amount to get water if possible
    if not alive_opponents:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.3) # Conserve if no competition
        if day_context['supply'] < WATER_REQ: # If supply is less than my need, still bid something
            final_bid = min(my_status['budget'], DAILY_SALARY * 0.5)

    # Ensure I bid something if I need water and can afford it
    if my_status['hp'] <= EPISODE_DAYS - day_context['day'] + 2 and my_status['budget'] > 0:
        final_bid = max(final_bid, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 1. Look at yesterday's situation (Trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = 0.0 # Initialize bid

    # 2. Decision logic based on HP and yesterday's highest pressure
    # Critical HP: Must win at all costs
    if my_status['hp'] <= 2:
        bid = min(my_status['budget'], DAILY_SALARY * 0.98) # Very aggressive
    # Low HP: Need to win
    elif my_status['hp'] <= 4:
        bid = min(my_status['budget'], DAILY_SALARY * 0.90) # High bid
    # Healthy HP: Balance competition and budget
    else:
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents very aggressive
            bid = min(my_status['budget'], highest_prev_bid + 3) # Slightly beat, or high
            bid = min(bid, DAILY_SALARY * 0.92) # Cap to avoid overspending too early
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents moderately aggressive
            bid = min(my_status['budget'], highest_prev_bid + 2) # Beat by a bit
            bid = min(bid, DAILY_SALARY * 0.85) # Cap
        else: # Default moderate bid if no strong signal or low previous bids
            bid = DAILY_SALARY * 0.75 # A solid base bid

    # Adjust for endgame
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last two days are critical
        bid = max(bid, DAILY_SALARY * 0.95) # Push hard for survival
        bid = min(bid, my_status['budget'])
    elif remaining_days <= 4: # Mid-late game, be more firm
        bid = max(bid, DAILY_SALARY * 0.8)
        bid = min(bid, my_status['budget'])

    # Ensure bid is never more than current budget
    bid = min(bid, my_status['budget'])
    
    # Ensure a minimum bid to be competitive
    if bid < DAILY_SALARY * 0.6:
        bid = min(my_status['budget'], DAILY_SALARY * 0.6)

    return bid
"""
