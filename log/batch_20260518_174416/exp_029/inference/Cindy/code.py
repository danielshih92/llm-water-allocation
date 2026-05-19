# ============================================================
# Experiment: exp_029
# Agent: Cindy
# Source: exp_029
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents or I'm the last one, bid minimum to get water
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Calculate total water requirement (including myself)
    total_water_needed = WATER_REQ * (num_alive_opponents + 1)

    # Default bid if no trace or initial days
    base_bid = DAILY_SALARY * 0.5

    # 1. Look at yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very aggressive, react to it
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If supply is scarce, we must match or exceed
            if current_supply < total_water_needed:
                base_bid = max(base_bid, highest_prev_bid + 1.0)
            else: # Supply was enough, maybe they were desperate or bluffing
                base_bid = max(base_bid, DAILY_SALARY * 0.6)
        # If highest previous bid was low, we can try to bid lower if supply allows
        elif highest_prev_bid <= DAILY_SALARY * 0.3:
            if current_supply >= total_water_needed: # Abundant supply
                base_bid = min(base_bid, highest_prev_bid + 0.5)
            else: # Supply was scarce, they might be trying to save budget or have high HP
                base_bid = max(base_bid, DAILY_SALARY * 0.55)
        else: # Moderate previous bids
            base_bid = max(base_bid, highest_prev_bid + 0.5)

    # 2. Adjust bid based on my HP
    if my_hp <= 2: # Critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_hp <= 4: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    elif my_hp >= 8: # High HP, can be more flexible if supply is good
        if current_supply >= total_water_needed:
            base_bid = min(base_bid, DAILY_SALARY * 0.35)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.45)

    # 3. Adjust bid based on current supply scarcity
    if current_supply < total_water_needed: # Supply is scarce
        if current_supply < WATER_REQ: # Not enough for even one agent
            base_bid = max(base_bid, DAILY_SALARY * 0.99)
        elif current_supply < WATER_REQ * 2: # Not enough for two
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
        else: # Scarce but more than 2x WATER_REQ
            base_bid = max(base_bid, DAILY_SALARY * 0.65)
    elif current_supply >= total_water_needed + WATER_REQ: # Very abundant supply
        base_bid = min(base_bid, DAILY_SALARY * 0.25)

    # Final bid cannot exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 1.0 to ensure participation
    final_bid = max(1.0, final_bid)

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    if not alive_opponents:
        # No opponents, bid conservatively to save budget
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If no opponent bids from yesterday, use a default strategy
    if not yesterday_bids:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    highest_prev_bid = max(yesterday_bids)

    # React to very aggressive bids from yesterday
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            # If HP is good, conserve budget against very high bids
            return min(my_status['budget'], DAILY_SALARY * 0.3)
        # If HP is low, bid aggressively to survive
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Default strategy: bid slightly above the highest previous bid or a safe percentage of salary
    # This targets Eric's consistent 70.0 bid (150 * 0.5 = 75, max(75, 70.0 + 1.5) = 75)
    return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water.
    if not alive_opponents:
        # Enough to get water, but not overspend. A low bid (e.g., 20% of daily salary)
        # is usually enough if no one else is bidding.
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    total_opponent_water_req = 0

    for opp in alive_opponents:
        total_opponent_water_req += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid calculation
    # Start with a moderate bid, e.g., 60% of daily salary (90)
    current_bid = DAILY_SALARY * 0.6

    # Adjust based on yesterday's highest bid if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were aggressive yesterday, I need to be more aggressive
        if highest_prev_bid > DAILY_SALARY * 0.7: # If max bid was high (e.g., > 105)
            current_bid = max(current_bid, highest_prev_bid * 1.05) # Try to slightly outbid
        else: # If bids were moderate, try to stay slightly above average
            current_bid = max(current_bid, average_prev_bid * 1.1)

    # Adjust based on current HP
    if my_status['hp'] <= 2: # Critical HP, bid very high
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP, bid high
        current_bid = max(current_bid, DAILY_SALARY * 0.8)
    elif my_status['no_water_days'] > 0: # Missed water recently, need to secure it
        current_bid = max(current_bid, DAILY_SALARY * 0.75)

    # Adjust based on supply scarcity
    # Total water demand for all alive agents (including me)
    total_water_demand = WATER_REQ + total_opponent_water_req
    
    # If supply is significantly less than total demand, competition will be fierce
    if day_context['supply'] < total_water_demand:
        # Calculate a scarcity factor. If supply is half of demand, factor could be 2.
        # Handle potential division by zero if supply is 0 (unlikely but safe)
        scarcity_ratio = total_water_demand / day_context['supply'] if day_context['supply'] > 0 else 2.0
        
        # Apply a multiplier, capped to prevent absurd bids
        # If supply is very low, this can increase bid by up to 50%
        scarcity_multiplier = min(scarcity_ratio * 0.75, 1.5)
        current_bid *= scarcity_multiplier
    elif day_context['supply'] > total_water_demand: # If supply is abundant
        scarcity_ratio = total_water_demand / day_context['supply'] if day_context['supply'] > 0 else 1.0
        scarcity_multiplier = max(scarcity_ratio * 1.2, 0.5) # Reduce bid, but not too much, min 50% of base
        current_bid *= scarcity_multiplier

    # Adjust based on remaining days and budget
    days_left = EPISODE_DAYS - day_context['day'] + 1
    # Estimate required budget to survive remaining days at a moderate cost (e.g., 70% of salary per day)
    estimated_budget_needed = DAILY_SALARY * 0.7 * days_left

    # If budget is tight relative to remaining days and my HP is good, conserve funds
    if my_status['budget'] < estimated_budget_needed and my_status['hp'] > 5:
        current_bid = min(current_bid, DAILY_SALARY * 0.5)

    # Ensure bid is at least enough to cover water requirement at a minimal price per unit
    # (e.g., 5 currency units per water unit)
    min_bid_for_water = WATER_REQ * 5 # 13 * 5 = 65
    current_bid = max(current_bid, min_bid_for_water)

    # Final constraints
    # Cannot bid more than current budget
    final_bid = min(current_bid, my_status['budget'])
    # Cap bid to prevent overspending on a single day, e.g., 120% of daily salary (180)
    final_bid = min(final_bid, DAILY_SALARY * 1.2)
    
    # Ensure bid is positive
    final_bid = max(final_bid, 0.01)

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_total_players_alive = len(alive_opponents) + 1

    # Base bid - start with a moderate bid, adjusted by my HP
    # Higher HP means more room to save, lower HP means bid more aggressively
    if my_hp == 1:
        bid = DAILY_SALARY * 0.98 # Desperate
    elif my_hp == 2:
        bid = DAILY_SALARY * 0.90 # Very high
    elif my_hp == 3:
        bid = DAILY_SALARY * 0.75 # High
    elif my_hp == 4:
        bid = DAILY_SALARY * 0.65 # Moderate
    else: # my_hp >= 5 (assuming max HP is 5 or more)
        bid = DAILY_SALARY * 0.55 # Conservative

    # Adjust bid based on day (late game survival)
    # In the last few days, survival is critical, so bid higher
    if day >= EPISODE_DAYS - 2: # Last 2 days
        bid = max(bid, DAILY_SALARY * 0.95) # Ensure high bid for survival

    # Analyze opponent's previous bids (from yesterday's trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were bidding high, I need to bid slightly higher to win,
        # especially if supply is tight or my HP isn't max.
        if max_prev_bid >= DAILY_SALARY * 0.7:
            # Bid slightly above the max previous bid to try and outbid them
            # Adjust increment based on number of players
            bid_increment = 5.0 + (num_total_players_alive - 1) * 2.0
            bid = max(bid, max_prev_bid + bid_increment)
        # If opponents were bidding relatively low, I can try to save budget
        elif avg_prev_bid < DAILY_SALARY * 0.5:
            # Bid slightly above average to secure water cheaply
            bid = min(bid, avg_prev_bid + 2.0)

    # Adjust bid based on supply scarcity relative to total demand
    total_water_needed_by_all_players = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_all_players += opp['water_requirement']

    if supply < WATER_REQ: # Supply is less than my requirement, extreme scarcity
        bid = max(bid, DAILY_SALARY * 0.99) # Bid very aggressively
    elif supply < total_water_needed_by_all_players: # Supply is less than total demand
        # Competition will be high, increase bid
        bid = max(bid, DAILY_SALARY * 0.8)
    elif supply >= total_water_needed_by_all_players + WATER_REQ: # Abundant supply
        # Can afford to bid lower
        bid = min(bid, DAILY_SALARY * 0.4)

    # Ensure bid doesn't exceed budget and is non-negative
    final_bid = min(my_budget, bid)
    final_bid = max(0.0, final_bid)

    return float(final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    base_bid = DAILY_SALARY * 0.5 
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        if highest_prev_bid > DAILY_SALARY * 0.55:
            base_bid = highest_prev_bid + 2 
        else:
            base_bid = max(base_bid, average_prev_bid + 1)
    
    base_bid = max(base_bid, DAILY_SALARY * 0.45)

    current_bid = base_bid

    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        current_bid = min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 6:
        current_bid = min(my_status['budget'], max(current_bid, DAILY_SALARY * 0.75))
    
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['budget'] > DAILY_SALARY * 2:
        current_bid = min(my_status['budget'], max(current_bid, DAILY_SALARY * 0.8))

    num_possible_winners = int(day_context['supply'] // WATER_REQ)
    num_active_opponents = len(alive_opponents)

    if num_possible_winners < (num_active_opponents + 1) / 2:
        if my_status['hp'] > 6 and my_status['no_water_days'] == 0:
             current_bid = min(my_status['budget'], max(current_bid, base_bid * 1.1))

    final_bid = min(my_status['budget'], current_bid)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    # Constants for bid adjustment
    BASE_BID_FACTOR = 0.7
    HIGH_HP_BID_FACTOR = 0.85 # For 1 no_water_day
    CRITICAL_HP_BID_FACTOR = 0.95 # For 2+ no_water_days
    BID_INCREMENT_OVER_OPPONENT = 5 # Amount to bid over highest opponent bid

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], WATER_REQ * 1)

    # Initialize bid based on my desperation
    if my_status['no_water_days'] >= 2:
        my_desperation_bid = DAILY_SALARY * CRITICAL_HP_BID_FACTOR
    elif my_status['no_water_days'] == 1:
        my_desperation_bid = DAILY_SALARY * HIGH_HP_BID_FACTOR
    else:
        my_desperation_bid = DAILY_SALARY * BASE_BID_FACTOR

    bid = my_desperation_bid

    # Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Determine competition level
        num_water_units_available = int(day_context['supply'] / WATER_REQ)
        num_active_agents = len(alive_opponents) + 1 # Including myself

        # If water is scarce or I'm desperate, I need to be more aggressive
        if num_water_units_available < num_active_agents or my_status['no_water_days'] > 0:
            bid = max(bid, highest_prev_bid + BID_INCREMENT_OVER_OPPONENT)
        else: # Water is not scarce and I'm not desperate, be slightly less aggressive
            bid = max(bid, highest_prev_bid + 1) # Small increment

    # Ensure bid does not exceed current budget
    # Cap bid at a reasonable maximum unless in critical state
    max_affordable_bid = my_status['budget']
    
    if my_status['no_water_days'] >= 2:
        # If critical, allow bidding up to a higher multiple of daily salary
        bid = min(bid, max_affordable_bid, DAILY_SALARY * 1.5)
    else:
        # If not critical, cap at a slightly lower multiple
        bid = min(bid, max_affordable_bid, DAILY_SALARY * 1.1)

    # Ensure bid is at least enough to buy water (e.g., WATER_REQ * 1)
    bid = max(bid, WATER_REQ * 1)
    
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.75

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif day_context['day'] <= 2:
        base_bid = DAILY_SALARY * 0.65

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)

    if day_context['supply'] <= (MIN_SUPPLY + MAX_SUPPLY) / 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        if max_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, max_prev_bid + 5)
        elif max_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, max_prev_bid + 2)
        else:
            base_bid = max(base_bid, max_prev_bid + 1)

    final_bid = min(my_status['budget'], base_bid)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid if no strong competition or for general strategy
    base_bid = DAILY_SALARY * 0.5

    # Aggressiveness factor based on HP and day
    aggressiveness = 1.0
    if my_status['hp'] <= 2: # Critical HP
        aggressiveness = 1.3 # Bid very aggressively
    elif my_status['hp'] <= 4: # Low HP
        aggressiveness = 1.15
    
    # Adjust aggressiveness for late game
    if day_context['day'] >= EPISODE_DAYS * 0.7: # Last 30% of days
        aggressiveness = max(aggressiveness, 1.2) # Be more aggressive in late game

    # Get yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine target bid based on opponent's previous bids
    target_bid = base_bid * aggressiveness
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, we might need to exceed it significantly
        if highest_prev_bid >= DAILY_SALARY * 0.9: # Very high bid (e.g., Alex's max was 143.5)
            target_bid = max(target_bid, highest_prev_bid + 3.0) 
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # High bid
            target_bid = max(target_bid, highest_prev_bid + 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate bid
            target_bid = max(target_bid, highest_prev_bid + 1.0)
        else: # Low bid
            target_bid = max(target_bid, highest_prev_bid * 1.15) # Slightly higher than low bids
    
    # Adjust for supply scarcity: Given WATER_REQ=13 and supply_range=[15,25],
    # only one player can get full water, so competition is always high. 
    # Higher supply means more 'leftover' but doesn't change # of full requirements.
    if day_context['supply'] <= WATER_REQ + 5: # Supply is very tight (e.g., 15-18)
        target_bid *= 1.05 # Slightly more aggressive
    elif day_context['supply'] >= 22: # Supply is more 'abundant' for a single winner (e.g., 22-25)
        if my_status['hp'] > 4: # If HP is good, can afford to be slightly less aggressive
            target_bid *= 0.98 # Small reduction, still competitive
    
    # Ensure bid doesn't exceed budget or a reasonable maximum
    # Maximum bid can be higher if HP is critical.
    max_sustainable_bid = DAILY_SALARY * 1.1 # Default max bid
    if my_status['hp'] <= 2: # Critical HP
        max_sustainable_bid = DAILY_SALARY * 1.5 # Allow bidding significantly more than daily salary
    
    final_bid = min(my_status['budget'], target_bid, max_sustainable_bid)

    # Ensure bid is at least a minimum positive value
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents) + 1

    # If no opponents are alive, bid minimally to ensure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate available water units (how many agents can fully meet their requirement)
    available_water_units = int(day_context['supply'] // WATER_REQ)

    # Aggressive bidding if HP is low, no water days are accumulating, or it's late in the game
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1 or day_context['day'] >= EPISODE_DAYS - 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid very high to survive

    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Strategy based on supply scarcity and opponent behavior
    if available_water_units < num_competitors: # Scarce supply, high competition
        # If opponents were bidding high yesterday, bid slightly higher or a significant portion of salary
        if highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents are very aggressive
            return min(my_status['budget'], DAILY_SALARY * 0.85)
        elif highest_prev_bid > 0: # Opponents bid something, try to outbid them
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 5)) # Bid above them, or a baseline
        else: # No strong previous bids, but supply is scarce, so bid moderately high
            return min(my_status['budget'], DAILY_SALARY * 0.7)
    else: # Abundant supply, less competition
        # If opponents were bidding high despite abundant supply, they might be trying to secure water
        if highest_prev_bid >= DAILY_SALARY * 0.6 and my_status['hp'] <= 5: # Still need to be careful
             return min(my_status['budget'], DAILY_SALARY * 0.65)
        elif highest_prev_bid > 0: # Try to bid slightly lower than their high if supply is good
            return min(my_status['budget'], max(DAILY_SALARY * 0.4, highest_prev_bid - 5))
        else: # No strong previous bids, and supply is good
            return min(my_status['budget'], DAILY_SALARY * 0.5) # Conservative bid

    # Default fallback (should ideally not be reached)
    return min(my_status['budget'], DAILY_SALARY * 0.5)
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
    
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    base_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 8:
        base_bid = DAILY_SALARY * 0.45

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif day_context['day'] <= 2 and my_status['hp'] >= 8:
        base_bid = min(base_bid, DAILY_SALARY * 0.4)

    if highest_prev_bid > 0:
        if my_status['hp'] <= 4:
            if highest_prev_bid >= DAILY_SALARY * 0.7:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid + 1)
        else:
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                base_bid = max(base_bid, highest_prev_bid * 0.95)
            elif highest_prev_bid >= DAILY_SALARY * 0.5:
                base_bid = max(base_bid, highest_prev_bid + 1)
            else:
                base_bid = min(base_bid, DAILY_SALARY * 0.6)

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(1.0, final_bid)

    if my_status['budget'] < DAILY_SALARY * 0.3 and my_status['hp'] <= 3:
        final_bid = my_status['budget']

    return final_bid
"""
