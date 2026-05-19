# ============================================================
# Experiment: exp_085
# Agent: Cindy
# Source: exp_085
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

    # If no opponents, bid minimally to secure water and save budget.
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- Determine initial bid based on my HP (highest priority for survival) ---
    if my_hp <= 1: # Critical HP: Bid very high
        bid = DAILY_SALARY * 0.95
    elif my_hp == 2: # Warning HP: Bid high
        bid = DAILY_SALARY * 0.8
    else: # Healthy HP (my_hp == 3): Start with a moderate bid
        bid = DAILY_SALARY * 0.5

    # --- Adjust bid based on overall supply pressure and demand ---
    total_water_demand_excluding_me = sum(o['water_requirement'] for o in alive_opponents)
    total_expected_demand = WATER_REQ + total_water_demand_excluding_me

    # If supply is very scarce, increase bid significantly
    if current_supply < total_expected_demand:
        bid += DAILY_SALARY * 0.15
    # If supply is abundant, decrease bid to save budget, but ensure we still get water
    elif current_supply >= total_expected_demand + WATER_REQ:
        bid -= DAILY_SALARY * 0.1
    
    # Ensure bid doesn't go too low after supply adjustment if HP isn't critical
    if my_hp > 1 and bid < DAILY_SALARY * 0.3:
        bid = DAILY_SALARY * 0.3 # Minimum bid floor for healthy/warning HP

    # --- Adjust bid based on yesterday's opponent behavior (reactive strategy) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

        # If highest bid yesterday was very high, it indicates strong competition.
        if max_yesterday_bid >= DAILY_SALARY * 0.7: # High competition threshold
            # If desperate (HP <= 1), ensure bid is at least max_yesterday_bid + 1
            if my_hp <= 1:
                bid = max(bid, max_yesterday_bid + 1)
            # If not desperate, try to outbid slightly or match
            else:
                bid = max(bid, max_yesterday_bid + 1)
        # If highest bid yesterday was moderate, try to stay competitive but save money
        elif max_yesterday_bid > DAILY_SALARY * 0.3 and max_yesterday_bid < DAILY_SALARY * 0.7: # Moderate competition
            # If not desperate, try to bid slightly above it
            if my_hp > 1:
                bid = max(bid, max_yesterday_bid + 2)
            else: # If desperate, HP logic already pushes bid high. Ensure it's competitive.
                bid = max(bid, max_yesterday_bid + 1)
        # If highest bid yesterday was very low, competition seems low.
        elif max_yesterday_bid <= DAILY_SALARY * 0.3: # Low competition threshold
            # If not desperate, try to bid low but still enough to win
            if my_hp > 1:
                bid = min(bid, max_yesterday_bid + 5) # Try to bid slightly above, but cap it
                bid = max(bid, DAILY_SALARY * 0.15) # Ensure a minimum floor
            # If desperate, HP logic takes precedence.

    # Final bid constraints: must be positive and not exceed budget
    final_bid = max(0.01, min(bid, my_budget))

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. If no opponents, bid minimally to save budget.
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Calculate total water required by all alive agents (including myself)
    total_water_needed_by_players = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_players += opp['water_requirement']

    # Determine a base bid multiplier based on supply vs demand
    base_bid_multiplier = 0.55 # Default
    if supply < total_water_needed_by_players:
        # Supply is scarce, increase base bid
        base_bid_multiplier = 0.7
        # Even more scarce, if supply is less than avg water req per player
        if supply < WATER_REQ * (num_alive_opponents + 1) / 2:
             base_bid_multiplier = 0.85
    else:
        # Supply is abundant or sufficient, can try to bid lower
        base_bid_multiplier = 0.45

    current_bid = DAILY_SALARY * base_bid_multiplier

    # Look at yesterday's bids of alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # 2. Prioritize survival if HP is critical
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.98)

    # 3. If I haven't gotten water recently, increase bid
    if my_no_water_days > 0:
        current_bid = max(current_bid, DAILY_SALARY * 0.9)
        return min(my_budget, current_bid)

    # 4. React to opponent's previous high bids
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp > 5:
            current_bid = max(current_bid, highest_prev_bid + 1.0, DAILY_SALARY * 0.75)
        else:
            current_bid = max(current_bid, highest_prev_bid + 1.0, DAILY_SALARY * 0.9)
    elif highest_prev_bid > 0:
        current_bid = max(current_bid, highest_prev_bid + 1.0)
    
    # Final check and cap
    # If my HP is very good, I can afford to be less aggressive to save budget
    if my_hp > 7 and current_bid > DAILY_SALARY * 0.8:
        current_bid = min(current_bid, DAILY_SALARY * 0.75)

    # Ensure bid doesn't exceed budget
    return min(my_budget, current_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, 1.0)

    base_bid_percentage = 0.5

    if my_hp <= 2:
        base_bid_percentage = 0.95
    elif my_hp <= 5:
        base_bid_percentage = 0.80
    elif my_hp <= 8:
        base_bid_percentage = 0.65

    calculated_bid = DAILY_SALARY * base_bid_percentage

    yesterday_opp_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opp_bids.append(prev_trace['bid'])

    if yesterday_opp_bids:
        max_yesterday_bid = max(yesterday_opp_bids)
        avg_yesterday_bid = sum(yesterday_opp_bids) / len(yesterday_opp_bids)

        if avg_yesterday_bid > DAILY_SALARY * 0.7:
            calculated_bid += DAILY_SALARY * 0.15
        elif max_yesterday_bid > DAILY_SALARY * 0.8:
             calculated_bid += DAILY_SALARY * 0.1
        elif avg_yesterday_bid < DAILY_SALARY * 0.3:
            calculated_bid -= DAILY_SALARY * 0.05
            calculated_bid = max(calculated_bid, DAILY_SALARY * 0.1)

    num_possible_winners = int(current_supply / WATER_REQ)
    
    if num_alive_opponents >= num_possible_winners and num_possible_winners > 0:
        calculated_bid *= 1.15
    elif num_alive_opponents < num_possible_winners and num_possible_winners > 1:
        calculated_bid *= 0.9

    if current_supply < WATER_REQ * 1.5 and num_alive_opponents >= 1:
        calculated_bid += DAILY_SALARY * 0.1

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3 and my_hp < 10:
        calculated_bid += DAILY_SALARY * 0.15

    if my_hp < 10 and my_budget > 0:
        calculated_bid = max(calculated_bid, 1.0)
    
    final_bid = min(my_budget, calculated_bid)
    
    if my_hp < 10 and my_budget > 0 and final_bid < 1.0:
        final_bid = 1.0

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.6 # A moderate starting point

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, bid aggressively to survive
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 8: # High HP, can afford to save a bit
        base_bid = DAILY_SALARY * 0.45

    # Adjust bid based on supply
    if current_supply <= WATER_REQ: # Very tight supply, high competition
        base_bid *= 1.2
    elif current_supply < WATER_REQ * 1.5: # Tight supply for two players
        base_bid *= 1.1
    elif current_supply >= WATER_REQ * 2: # Ample supply
        base_bid *= 0.9

    # Adjust bid based on opponent's previous bids (from previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        # If I have low HP, I need to be very aggressive to win against high bids
        if my_hp <= 3:
            base_bid = max(base_bid, max_opp_bid + 5)
        # If I have moderate HP, be competitive but don't overspend too much
        elif my_hp <= 6:
            base_bid = max(base_bid, max_opp_bid + 2)
        # If I have high HP, I can afford to be slightly less aggressive, but still consider the competition
        else:
            base_bid = max(base_bid, max_opp_bid * 1.01)

    # Adjust bid based on day (end game push)
    if current_day > EPISODE_DAYS * 0.7 and my_hp > 5: # Late game, if healthy, try to eliminate opponents
        base_bid *= 1.15
    elif current_day > EPISODE_DAYS * 0.85 and my_hp <= 5: # Very late game, low HP, extremely aggressive survival
        base_bid = DAILY_SALARY * 0.98


    # Ensure bid is not negative and within budget
    final_bid = max(0.0, min(my_budget, base_bid))

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    # Constants for bidding strategy
    HIGH_PRESSURE_THRESHOLD = DAILY_SALARY * 0.85
    LOW_HP_THRESHOLD = 3
    VERY_LOW_HP_THRESHOLD = 2
    BID_OUTBID_MARGIN = 2.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid a minimal amount to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine the highest bid from yesterday
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid calculation
    bid_amount = DAILY_SALARY * 0.55 # Default moderate bid

    # Adjust bid based on previous competition and my HP
    if highest_prev_bid > 0: # If there was competition yesterday
        if highest_prev_bid >= HIGH_PRESSURE_THRESHOLD:
            # High pressure situation (e.g., David/Eric bidding high)
            if my_status['hp'] > LOW_HP_THRESHOLD:
                # HP is good, can afford to conserve a bit
                bid_amount = DAILY_SALARY * 0.4
            else:
                # HP is low, must bid aggressively to survive
                bid_amount = DAILY_SALARY * 0.95
        else:
            # Moderate pressure, try to outbid slightly
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + BID_OUTBID_MARGIN)
    else: # No clear highest previous bid (e.g., first day or no one bid meaningfully)
        if my_status['hp'] <= VERY_LOW_HP_THRESHOLD:
            # HP is very low, bid aggressively to secure water
            bid_amount = DAILY_SALARY * 0.9
        elif day_context['day'] > EPISODE_DAYS * 0.7: # Late game, increase aggression
            bid_amount = DAILY_SALARY * 0.8
        else:
            # Default moderate bid
            bid_amount = DAILY_SALARY * 0.55

    # Ensure the bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure a minimum bid to stay in contention if budget allows
    if final_bid < 1.0 and my_status['budget'] >= 1.0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1 if my_status['budget'] >= DAILY_SALARY * 0.1 else 1.0)
    elif final_bid < 1.0 and my_status['budget'] < 1.0:
         final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.5 # 75

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Aggressive bidding if HP is critically low
        if my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.95)

        # If highest previous bid was very high, react
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Threshold of 120
            # If my HP is good, try to conserve but stay competitive
            if my_status['hp'] > 5:
                return min(my_status['budget'], max(base_bid, highest_prev_bid * 0.95))
            else: # HP is getting lower, must be more aggressive
                return min(my_status['budget'], highest_prev_bid + 5)
        
        # If highest previous bid was moderate
        else:
            return min(my_status['budget'], max(base_bid, highest_prev_bid + 2))

    # If no previous bids from opponents (e.g., first day or opponents died without bidding)
    # or if the above conditions didn't trigger, use HP-based strategy
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif my_status['hp'] <= 5:
        return min(my_status['budget'], DAILY_SALARY * 0.7)
    else:
        return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # Base bid strategy
    # Default bid for a healthy state
    bid = DAILY_SALARY * 0.55

    # Adjust bid based on my HP (urgency)
    if my_hp <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # High urgency
        bid = DAILY_SALARY * 0.8
    elif my_hp <= 6: # Moderate urgency
        bid = DAILY_SALARY * 0.7
    # Else, bid remains 0.55 * DAILY_SALARY

    # Adjust bid based on opponent's previous highest bid
    if highest_prev_bid > 0:
        if my_hp <= 4: # If urgent, try to outbid
            bid = max(bid, highest_prev_bid + 5)
        else: # If not urgent, try to win cheaply, or maintain current strategy
            bid = max(bid, highest_prev_bid + 1)
            # If highest_prev_bid was very high and I'm healthy, cap the bid to prevent overspending
            if bid > DAILY_SALARY * 0.7 and my_hp > 6:
                bid = min(bid, DAILY_SALARY * 0.7)

    # Adjust bid for late game push
    days_left = EPISODE_DAYS - current_day
    if days_left <= 2: # Last 2 days
        if my_hp <= 4: # Desperate push to survive
            bid = max(bid, DAILY_SALARY * 0.9)
        else: # Strong push to secure win
            bid = max(bid, DAILY_SALARY * 0.75)

    # Ensure bid does not exceed budget and is at least 1
    final_bid = min(my_budget, bid)
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    base_bid = DAILY_SALARY * 0.75 # A strong base bid given opponent history

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid very conservatively
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, bid aggressively
        bid = DAILY_SALARY * 0.85
    else: # Normal HP
        bid = base_bid

    # Adjust bid based on supply scarcity
    # If supply is less than or equal to my requirement, it's highly contested
    if day_context['supply'] <= WATER_REQ:
        bid = max(bid, DAILY_SALARY * 0.9)
    # If supply is moderately scarce (e.g., enough for 1-1.5 agents) and multiple opponents
    elif day_context['supply'] <= WATER_REQ * 1.5 and len(alive_opponents) >= 2:
        bid = max(bid, DAILY_SALARY * 0.8)

    # React to highest previous bid to ensure competitiveness
    if highest_prev_bid > 0:
        # If my current bid is lower than or equal to highest_prev_bid, try to beat it
        if bid <= highest_prev_bid:
            bid = highest_prev_bid + 1.0 # Bid slightly higher to win

    # Ensure the bid doesn't exceed my budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is positive
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Base bid - a moderate starting point
    bid = DAILY_SALARY * 0.55

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    strong_opponent_bids = []
    for opp in alive_opponents:
        # Check if opponent is Alex or David, who were strong in the last meta-round
        if opp['agent_id'] in ["Alex", "David"]:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                strong_opponent_bids.append(prev_trace['bid'])

    highest_strong_bid = max(strong_opponent_bids) if strong_opponent_bids else 0

    # 1. Adjust bid based on my HP and no-water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical condition: bid very aggressively
        bid = DAILY_SALARY * 0.95
        if highest_strong_bid > 0:
            bid = max(bid, highest_strong_bid + 15) # Ensure outbid if critical
    elif my_status['hp'] <= 5:
        # Low HP: bid aggressively
        bid = DAILY_SALARY * 0.8
        if highest_strong_bid > 0:
            bid = max(bid, highest_strong_bid + 10)
    else:
        # Healthy HP: be competitive but not overly aggressive
        if highest_strong_bid > 0:
            bid = max(bid, highest_strong_bid * 0.95) # Try to stay competitive

    # 2. Adjust for supply scarcity
    num_slots = int(day_context['supply'] / WATER_REQ)
    num_active_players = len(alive_opponents) + 1 # Include myself

    if num_slots < num_active_players:
        if num_slots == 1 and num_active_players > 1:
            # Extreme scarcity: only one person can get full water, multiple players
            bid = max(bid, DAILY_SALARY * 0.98) # Bid very high
        elif num_slots < num_active_players:
            # Moderate scarcity: not enough for everyone
            bid = max(bid, DAILY_SALARY * 0.7) # Increase bid to compete

    # 3. Adjust for late game aggression
    days_left = EPISODE_DAYS - day_context['day']
    if days_left <= 3: # Last 3 days
        if my_status['hp'] <= 5:
            bid = max(bid, DAILY_SALARY * 0.95) # Very aggressive if low on HP late game
        else:
            bid = max(bid, DAILY_SALARY * 0.75) # Still aggressive to secure survival

    # 4. Final clamp: ensure bid is within budget and reasonable max
    bid = min(bid, my_status['budget'])
    bid = min(bid, DAILY_SALARY * 0.99) # Cap bid at slightly less than full salary
    bid = max(0.1, bid) # Ensure bid is at least a minimal amount

    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # If no opponents, bid a minimal amount to save budget
        return min(my_status['budget'], MY_DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid, if no previous bids are available or relevant
    base_bid = MY_DAILY_SALARY * 0.5 # Default moderate bid

    if yesterday_bids:
        # Consider the highest bid from yesterday as a strong indicator of competition
        highest_prev_bid = max(yesterday_bids)
        
        # Adjust base_bid based on yesterday's competition
        if highest_prev_bid >= MY_DAILY_SALARY * 0.8: # Very aggressive opponent identified
            base_bid = highest_prev_bid + 5 # Bid slightly higher
        elif highest_prev_bid >= MY_DAILY_SALARY * 0.5: # Moderate opponent identified
            base_bid = highest_prev_bid + 2
        else: # Low opponent identified, stick to moderate if others are low
            base_bid = MY_DAILY_SALARY * 0.5
    
    # Critical HP logic: Must get water
    if my_status['hp'] <= 2:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.95)
    
    # Low HP logic: Prioritize getting water
    if my_status['hp'] <= 5:
        bid = max(base_bid, MY_DAILY_SALARY * 0.75)
        return min(my_status['budget'], bid)
    
    # Healthy HP logic
    num_alive_opponents = len(alive_opponents)
    
    # Check if supply is relatively generous (enough for more than one person to get a significant amount)
    # MY_WATER_REQUIREMENT * 1.5 means 19.5 units. Supply range is 15-25.
    # If supply is >= 19.5, it's 'more generous' for two people to get some water.
    if day_context['supply'] >= MY_WATER_REQUIREMENT * 1.5 and num_alive_opponents >= 2:
        # Moderate competition, can bid a bit lower if others are not too aggressive
        bid = max(base_bid, MY_DAILY_SALARY * 0.5) # A moderate bid
        return min(my_status['budget'], bid)
    else: # Supply is tight or fewer opponents, implies higher competition for water
        # Bid slightly higher to secure water
        bid = max(base_bid, MY_DAILY_SALARY * 0.6)
        return min(my_status['budget'], bid)
"""
