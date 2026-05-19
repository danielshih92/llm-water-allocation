# ============================================================
# Experiment: exp_116
# Agent: Cindy
# Source: exp_116
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Survival Logic --- 
    # If I'm in critical condition (low HP or missed water yesterday), bid very aggressively
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    # If HP is low but not critical, bid high
    if my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 0.8)

    # --- No Opponents Logic ---
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid very low if no competition

    # --- Analyze Yesterday's Opponent Bids ---
    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_opponent_bids.append(prev['bid'])

    highest_prev_opponent_bid = 0
    if yesterday_opponent_bids:
        highest_prev_opponent_bid = max(yesterday_opponent_bids)

    # --- Supply and Competition Logic ---
    supply = day_context['supply']
    current_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Calculate how much water is available per active player if split
    # Note: Using float division is fine here as it's not an index.
    water_per_player_if_split = supply / (num_alive_opponents + 1) 

    # If supply is very scarce (not enough for everyone to get their WATER_REQ)
    if supply < WATER_REQ * (num_alive_opponents + 1):
        if water_per_player_if_split < WATER_REQ: # Not enough for everyone to get full water
            # Competition is high. Try to outbid yesterday's highest, or bid a high percentage.
            if highest_prev_opponent_bid > 0:
                current_bid = max(DAILY_SALARY * 0.7, highest_prev_opponent_bid + 5)
            else:
                current_bid = DAILY_SALARY * 0.75
        else: # Enough water for everyone to get some, but not all full WATER_REQ
            if highest_prev_opponent_bid > 0:
                current_bid = max(DAILY_SALARY * 0.6, highest_prev_opponent_bid + 3)
            else:
                current_bid = DAILY_SALARY * 0.65
    else: # Supply is abundant (enough for everyone to get their WATER_REQ, or more)
        # Can afford to bid lower.
        if highest_prev_opponent_bid > 0:
            if highest_prev_opponent_bid < DAILY_SALARY * 0.4: # If opponents bid very low
                current_bid = max(DAILY_SALARY * 0.3, highest_prev_opponent_bid + 1) # Bid slightly above
            else: # Opponents bid moderate even with abundant supply, be cautious but still try to save
                current_bid = max(DAILY_SALARY * 0.4, highest_prev_opponent_bid + 2)
        else:
            current_bid = DAILY_SALARY * 0.4 # Default low bid for abundant supply

    # Final bid adjustment and budget check
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least 1 if budget allows and not 0, to participate.
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 1
    elif final_bid <= 0: # If budget is 0, then bid 0.
        final_bid = 0

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents) + 1

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    available_water_units = day_context['supply']
    num_winners_possible = int(available_water_units // WATER_REQ)

    bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.75

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] <= 3 or num_winners_possible < num_competitors:
                bid = max(bid, highest_prev_bid + 5)
            else:
                bid = max(bid, highest_prev_bid + 1)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 1.5)
        else:
            bid = max(bid, highest_prev_bid + 0.5)
    else:
        if my_status['hp'] <= 2:
            bid = DAILY_SALARY * 0.9
        else:
            bid = DAILY_SALARY * 0.55

    if num_winners_possible < num_competitors:
        if my_status['hp'] <= 4:
            bid = max(bid, DAILY_SALARY * 0.9)
        else:
            bid = max(bid, DAILY_SALARY * 0.7)
    elif num_winners_possible >= num_competitors + 1:
        bid = min(bid, DAILY_SALARY * 0.4)

    if day_context['day'] >= EPISODE_DAYS - 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif day_context['day'] >= EPISODE_DAYS / 2:
        bid = max(bid, DAILY_SALARY * 0.7)

    min_acceptable_bid = DAILY_SALARY * 0.25
    final_bid = max(bid, min_acceptable_bid)

    final_bid = min(final_bid, my_status['budget'])

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.75

    if day_context['day'] >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4:
                bid = min(my_status['budget'], highest_prev_bid + 5)
                bid = max(bid, base_bid)
            else:
                bid = min(my_status['budget'], highest_prev_bid + 10)
                bid = max(bid, base_bid)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = min(my_status['budget'], highest_prev_bid + 2)
            bid = max(bid, base_bid)
        else:
            bid = min(my_status['budget'], max(base_bid, highest_prev_bid + 1))
    else:
        bid = min(my_status['budget'], base_bid)

    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    remaining_days = EPISODE_DAYS - day_context['day']
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid_value = DAILY_SALARY * 0.5 

    # 1. Adjust based on my HP (urgency)
    if my_status['hp'] <= 2: 
        bid_value = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: 
        bid_value = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6: 
        bid_value = DAILY_SALARY * 0.7
    
    # 2. Adjust based on opponent's previous highest bid (reaction)
    if highest_prev_bid > 0:
        if my_status['hp'] <= 4: 
            bid_value = max(bid_value, highest_prev_bid + 10)
        elif my_status['hp'] <= 6:
            bid_value = max(bid_value, highest_prev_bid + 5)
        else: 
            bid_value = max(bid_value, highest_prev_bid + 1)
    
    # 3. Adjust based on supply (competition pressure)
    if day_context['supply'] <= 18: 
        if my_status['hp'] <= 6: 
            bid_value = max(bid_value, DAILY_SALARY * 0.8)
        else: 
            bid_value = max(bid_value, DAILY_SALARY * 0.65)
    elif day_context['supply'] >= 22: 
        if my_status['hp'] > 6: 
            bid_value = min(bid_value, DAILY_SALARY * 0.4)
        else: 
            bid_value = min(bid_value, DAILY_SALARY * 0.6)

    # 4. Adjust for end-game or early-game
    if remaining_days <= 2: 
        if my_status['hp'] <= 6:
            bid_value = max(bid_value, DAILY_SALARY * 0.9) 
        else:
            bid_value = max(bid_value, DAILY_SALARY * 0.8) 
    elif day_context['day'] <= 2 and my_status['hp'] > 7: 
        bid_value = min(bid_value, DAILY_SALARY * 0.55)
    
    final_bid = min(my_status['budget'], bid_value)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # CRITICAL INSIGHT: With WATER_REQ = 13 and supply_range [15, 25],
    # only ONE agent can get their full water requirement. Competition is always fierce.

    # 1. Critical Health: Must win to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.1) # Bid 110% of salary or all budget

    # 2. Missed water yesterday: Need to win today
    if my_status['no_water_days'] > 0:
        bid_target = max(highest_prev_bid + 5, DAILY_SALARY * 0.95) # Aggressive bid
        return min(my_status['budget'], bid_target)

    # 3. General Strategy: Always bid competitively due to single water slot
    base_bid_percentage = 0.85 # Default high bid percentage

    if highest_prev_bid > DAILY_SALARY * 0.8: # Opponents are bidding very high
        bid = highest_prev_bid + 2
    elif highest_prev_bid > DAILY_SALARY * 0.6: # Opponents are bidding moderately
        bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.85)
    else: # Opponents are bidding low or no significant previous bids
        bid = DAILY_SALARY * base_bid_percentage

    # Consider budget and days remaining
    days_left = EPISODE_DAYS - day_context['day']
    if my_status['budget'] > DAILY_SALARY * (days_left + 2): # Enough for remaining days + buffer
        bid = max(bid, DAILY_SALARY * 0.95) # Push higher
    elif my_status['budget'] < DAILY_SALARY * (days_left + 1): # Budget is getting tight
        bid = min(bid, DAILY_ALARY * 0.9) # Don't overspend too much

    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # For my water requirement (13) and supply range (15-25), there's effectively only 1 slot for me.
    # This means competition is always high if there are other players.

    # Base bid strategy based on my HP
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    if my_status['hp'] <= 2: # Critical HP: MUST get water
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP: strong bid
        base_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 8: # Healthy HP: can be slightly more conservative
        base_bid = DAILY_SALARY * 0.4

    # If I missed water yesterday, increase bid to prioritize getting it today
    if my_status['no_water_days'] > 0:
        base_bid += DAILY_SALARY * 0.10 # Small boost

    # Handle no opponents scenario
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.05) # Bid low to save, but ensure win

    # Analyze opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = base_bid # Start with HP-adjusted base bid

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Competition is high for my water requirement (always 1 slot for me)
        if my_status['hp'] <= 3: # Very low HP, bid very aggressively to survive
            # Bid above max previous bid, or aggressive base if opponents bid low
            final_bid = max(base_bid, max_prev_bid + (DAILY_SALARY * 0.1))
        else: # Healthy HP, bid competitively
            # If opponents are bidding very high, and I have good HP, I can try to back off slightly
            if max_prev_bid >= DAILY_SALARY * 0.8 and my_status['hp'] > 5:
                final_bid = base_bid * 0.8 # Try to get it cheaper, or risk losing if I have enough HP buffer
            else:
                # Bid above average previous bid to stay competitive, or use base bid if higher
                final_bid = max(base_bid, avg_prev_bid + (DAILY_SALARY * 0.05))
    
    # Ensure bid is positive and does not exceed current budget
    final_bid = max(1.0, min(my_status['budget'], final_bid))

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    bid_value = DAILY_SALARY * 0.5

    if my_hp <= 3:
        bid_value = DAILY_SALARY * 0.95
    elif my_hp <= 5:
        bid_value = DAILY_SALARY * 0.75
    elif my_hp >= 8:
        bid_value = DAILY_SALARY * 0.4

    if current_day > EPISODE_DAYS * 0.7:
        bid_value = max(bid_value, DAILY_SALARY * 0.7)
    if current_day > EPISODE_DAYS * 0.85:
        bid_value = max(bid_value, DAILY_SALARY * 0.9)

    water_units_available = int(supply // WATER_REQ)
    total_competitors_for_water = num_alive_opponents + 1

    if water_units_available < total_competitors_for_water:
        if water_units_available <= total_competitors_for_water / 2:
            bid_value = max(bid_value, DAILY_SALARY * 0.8)
        else:
            bid_value = max(bid_value, DAILY_SALARY * 0.6)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3:
                bid_value = min(bid_value, DAILY_SALARY * 0.4)
            else:
                bid_value = max(bid_value, DAILY_SALARY * 0.95)
        else:
            bid_value = max(bid_value, highest_prev_bid + 2.5)
            bid_value = max(bid_value, DAILY_SALARY * 0.5)

    if num_alive_opponents > 0 and bid_value < DAILY_SALARY * 0.2:
        bid_value = DAILY_SALARY * 0.2

    final_bid = min(bid_value, my_budget)
    final_bid = max(0.0, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget, but ensure water.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # Determine thresholds for aggressive bidding based on my salary
    AGGRO_THRESHOLD = DAILY_SALARY * 0.8 # e.g., 120
    LOW_HP_THRESHOLD = 3

    # Calculate total water demand vs supply to gauge overall competition
    total_water_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    current_supply = day_context['supply']

    # Initial bid based on my HP
    if my_status['hp'] <= LOW_HP_THRESHOLD:
        # Critical HP: Bid very high to ensure survival
        bid = DAILY_SALARY * 0.95 # e.g., 142.5
    elif my_status['hp'] <= 5:
        # Low HP: bid aggressively
        bid = DAILY_SALARY * 0.85 # e.g., 127.5
    else:
        # Healthy HP: Start with a moderate base bid
        bid = DAILY_SALARY * 0.6 # e.g., 90

    # Adjust bid based on opponent's highest previous bid
    if highest_prev_bid > AGGRO_THRESHOLD:
        # Opponents are bidding aggressively
        if my_status['hp'] > LOW_HP_THRESHOLD:
            # If HP is good, compete smartly considering supply
            if total_water_demand > current_supply * 1.5: # Very high competition
                bid = max(bid, highest_prev_bid * 1.05 + 5)
            else:
                bid = max(bid, highest_prev_bid * 1.01 + 1.5)
        else:
            # If HP is low, we must compete strongly irrespective of supply
            bid = max(bid, DAILY_SALARY * 1.0)
    elif highest_prev_bid > 0:
        # Opponents are bidding moderately
        bid = max(bid, highest_prev_bid * 1.02 + 2)
    else:
        # No significant previous bids from alive opponents, or all bid 0.
        # Bid conservatively but ensure participation.
        bid = max(bid, DAILY_SALARY * 0.2) # e.g., 30

    # Further adjust bid based on overall supply/demand if not in critical HP mode
    if my_status['hp'] > LOW_HP_THRESHOLD:
        if total_water_demand > current_supply * 1.5: # Very high competition
            bid = max(bid, DAILY_SALARY * 0.8)
        elif total_water_demand > current_supply * 1.0: # Moderate competition
            bid = max(bid, DAILY_SALARY * 0.65)

    # Ensure bid is at least a minimal amount to indicate participation
    min_bid_floor = DAILY_SALARY * 0.05 # e.g., 7.5
    bid = max(bid, min_bid_floor)

    # Cap bid by current budget
    final_bid = min(my_status['budget'], bid)

    # If budget is positive but calculated bid is 0, ensure a small bid to stay active
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], min_bid_floor)

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Calculate total water requirement for all alive agents (including myself)
    total_water_requirement = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_requirement += opp['water_requirement']

    # Determine a base bid based on my HP
    my_bid = 0.0
    if my_status['hp'] <= 1: # Critical HP, bid very aggressively
        my_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 3: # Low HP, bid aggressively
        my_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 5: # Medium-low HP
        my_bid = DAILY_SALARY * 0.65
    else: # Healthy HP, can afford to bid moderately
        my_bid = DAILY_SALARY * 0.5

    # Adjust bid based on supply vs demand
    # If supply is less than total demand, competition is high, bid up.
    # If supply is more than total demand, competition is lower, bid down.
    if total_water_requirement > 0: # Avoid division by zero
        supply_demand_ratio = current_supply / total_water_requirement
        if supply_demand_ratio < 0.8: # Very scarce
            my_bid *= 1.2
        elif supply_demand_ratio < 1.0: # Scarce
            my_bid *= 1.1
        elif supply_demand_ratio > 1.5: # Abundant
            my_bid *= 0.8
        elif supply_demand_ratio > 1.2: # More than enough
            my_bid *= 0.9

    # Consider opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very high, and I need water, I might need to match or exceed it.
        if highest_prev_bid > DAILY_SALARY * 0.7: # Opponents are bidding high
            if my_status['hp'] <= 4: # I need water
                my_bid = max(my_bid, highest_prev_bid + 2.0) # Try to outbid
            else: # I'm healthy, can be more conservative
                my_bid = max(my_bid, highest_prev_bid * 0.9) # Stay competitive but don't overspend
        elif highest_prev_bid > DAILY_SALARY * 0.5: # Moderate previous bids
            my_bid = max(my_bid, highest_prev_bid * 1.05) # Slightly above to win
        # If highest_prev_bid is low, my calculated bid might already be higher, which is fine.

    # Ensure bid does not exceed budget
    my_bid = min(my_bid, my_status['budget'])

    # Ensure bid is non-negative
    my_bid = max(0.0, my_bid)

    # If no opponents, bid very low to save budget
    if not alive_opponents:
        my_bid = min(my_status['budget'], DAILY_SALARY * 0.1) # Bid very low

    # Final check: if desperately low on HP, ensure bid is high enough
    if my_status['hp'] <= 1 and my_bid < DAILY_SALARY * 0.9:
        my_bid = min(my_status['budget'], DAILY_SALARY * 0.95)

    return my_bid
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
    eric_status = opponents_status.get('Eric')
    eric_alive = eric_status and eric_status['alive']

    my_target_bid = 0.0

    # Case 1: Eric is NOT alive or not found.
    if not eric_alive:
        # Check if any other opponents are alive
        other_alive_opponents = [o for o in alive_opponents if o['agent_id'] != 'Eric']
        if other_alive_opponents:
            # Assume other opponents are less aggressive (like Alex, Bob, David from previous context)
            # Bid moderately low to secure water but save budget.
            my_target_bid = DAILY_SALARY * 0.35 # Approx 52.5
        else:
            # No significant opponents, bid minimum to get water and save budget
            my_target_bid = DAILY_SALARY * 0.2 # Approx 30
    # Case 2: Eric IS alive.
    else:
        eric_water_req = eric_status.get('water_requirement', 10) # Default to 10 if not found, though it should be there.

        # Determine my base bid based on my HP
        if my_status['hp'] <= 2:
            # Desperate, bid very high
            my_target_bid = DAILY_SALARY * 0.95 # 142.5
        elif my_status['hp'] <= 5:
            # Low HP, bid high
            my_target_bid = DAILY_SALARY * 0.8 # 120
        else:
            # Healthy HP, competitive but sustainable bid
            my_target_bid = DAILY_SALARY * 0.65 # 97.5

        # Adjust bid based on Eric's previous behavior
        eric_prev_trace = eric_status.get('previous_trace', {})
        if eric_prev_trace and eric_prev_trace.get('bid') is not None:
            eric_prev_bid = eric_prev_trace['bid']

            # Consider supply vs demand for me and Eric
            total_water_needed_by_top_competitors = WATER_REQ + eric_water_req
            
            if day_context['supply'] < total_water_needed_by_top_competitors:
                # Scarcity: direct competition with Eric for water units
                # Need to bid higher than Eric's last bid to secure water
                my_target_bid = max(my_target_bid, eric_prev_bid + 5)
                # If my HP is very low, make it even more aggressive
                if my_status['hp'] <= 2:
                    my_target_bid = max(my_target_bid, eric_prev_bid + 10)
            else:
                # Enough water for both, try to get it cheaper but still competitive
                # Bid slightly below Eric's last bid, but ensure it's at least my calculated base
                my_target_bid = max(my_target_bid * 0.8, eric_prev_bid * 0.9)
                # Ensure it's not too low if I still need water
                my_target_bid = max(my_target_bid, DAILY_SALARY * 0.5) # Minimum reasonable bid when Eric is alive

    # Ensure bid does not exceed budget and is at least 1.0
    final_bid = min(my_status['budget'], my_target_bid)
    
    return max(1.0, final_bid)
"""
