# ============================================================
# Experiment: exp_086
# Agent: Cindy
# Source: exp_086
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From Current Meta-Round State

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid strategy based on HP
    # Higher HP allows for lower bids, lower HP demands higher bids
    if my_hp <= 2: # Critical HP
        bid_percentage = 0.95
    elif my_hp <= 4: # Low HP
        bid_percentage = 0.80
    elif my_hp <= 6: # Moderate HP
        bid_percentage = 0.65
    else: # High HP
        bid_percentage = 0.50

    base_bid = DAILY_SALARY * bid_percentage

    # Adjust bid based on supply scarcity
    # Supply range is [15, 25]. WATER_REQ is 13.
    # 15 units means barely enough for 1. 25 units means barely enough for 2.
    if current_supply <= WATER_REQ + 2: # Very scarce (e.g., 15 units)
        base_bid *= 1.1 # Increase bid
    elif current_supply >= WATER_REQ * 2 - 2: # Relatively abundant (e.g., 24-25 units)
        base_bid *= 0.9 # Decrease bid

    # Adjust bid based on opponent's previous bids
    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opponent_bids.append(prev_trace['bid'])

    if yesterday_opponent_bids:
        max_opp_bid_yesterday = max(yesterday_opponent_bids)
        avg_opp_bid_yesterday = sum(yesterday_opponent_bids) / len(yesterday_opponent_bids)

        # If opponents bid very high yesterday, assume high competition
        if max_opp_bid_yesterday >= DAILY_SALARY * 0.7:
            # Try to outbid or match the high competition
            base_bid = max(base_bid, max_opp_bid_yesterday + 5) # Bid slightly higher
        # If opponents bid very low yesterday, we can potentially save budget
        elif avg_opp_bid_yesterday <= DAILY_SALARY * 0.3:
            base_bid = min(base_bid, DAILY_SALARY * 0.4) # Don't go too low, but be conservative

    # End-game strategy: if near the end and HP is low, bid very aggressively
    if current_day >= EPISODE_DAYS - 2 and my_hp <= 3:
        base_bid = DAILY_SALARY * 0.98

    # Final bid must not exceed budget and must be at least 1 (if budget allows)
    final_bid = min(my_budget, base_bid)
    final_bid = max(1.0, final_bid) # Ensure a minimum bid of 1

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], WATER_REQ * 0.01)

    initial_bid = DAILY_SALARY * 0.7

    if my_status['hp'] <= 2:
        initial_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        initial_bid = DAILY_SALARY * 0.85
    
    day_progress_factor = day_context['day'] / EPISODE_DAYS
    initial_bid += initial_bid * day_progress_factor * 0.1

    estimated_total_water_needed = WATER_REQ * (num_alive_opponents + 1)
    
    if day_context['supply'] < estimated_total_water_needed:
        scarcity_ratio = (estimated_total_water_needed - day_context['supply']) / estimated_total_water_needed
        if scarcity_ratio > 0:
            initial_bid += initial_bid * scarcity_ratio * 0.2

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        if max_yesterday_bid > initial_bid * 0.8:
            initial_bid = max(initial_bid, max_yesterday_bid + 1.0)

    final_bid = min(my_status['budget'], initial_bid)
    
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 1.0
    elif final_bid <= 0:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_budget, MY_DAILY_SALARY * 0.1)

    base_bid = MY_DAILY_SALARY * 0.5

    if my_hp <= 2:
        base_bid = MY_DAILY_SALARY * 0.95
    elif my_hp <= 4:
        base_bid = MY_DAILY_SALARY * 0.8
    elif my_no_water_days > 0:
        base_bid = MY_DAILY_SALARY * 0.7

    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 3 and my_budget > MY_DAILY_SALARY * 3:
        base_bid *= 1.1

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= MY_DAILY_SALARY * 0.7:
            if my_hp <= 3:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid * 0.9)
        elif highest_prev_bid > MY_DAILY_SALARY * 0.4:
            base_bid = max(base_bid, highest_prev_bid * 1.05)

    if current_supply < MY_WATER_REQ * 1.5 and num_alive_opponents >= 1:
        base_bid *= 1.15
    elif current_supply < MY_WATER_REQ * 2 and num_alive_opponents >= 2:
        base_bid *= 1.1

    final_bid = min(my_budget, base_bid)
    final_bid = max(0.0, final_bid)

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # 2. Collect yesterday's bids from alive opponents
    yesterday_bids = []
    strong_opponent_bids = []
    # Identifying strong opponents from the meta-round context
    strong_opponents_ids = ["Alex", "David"]

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id in strong_opponents_ids:
                    strong_opponent_bids.append(prev['bid'])

    # Determine highest bid from yesterday, prioritizing strong opponents if present
    highest_prev_bid = 0
    if strong_opponent_bids:
        highest_prev_bid = max(strong_opponent_bids)
    elif yesterday_bids: # If no strong opponents bid, but others did
        highest_prev_bid = max(yesterday_bids)

    # 3. Bidding strategy based on HP, opponent behavior
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    # Aggressive if HP is very low (survival mode)
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95 # Very aggressive

    # Adjust bid based on highest previous bid from strong opponents
    elif highest_prev_bid > 0:
        # If strong opponents bid very high yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., >= 120
            if my_status['hp'] <= 5: # Moderate HP, need to be aggressive
                base_bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 5)
            else: # High HP, can be slightly less aggressive but still competitive
                base_bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 2)
        # If strong opponents bid moderately
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # e.g., >= 90
            if my_status['hp'] <= 5: # Moderate HP, ensure win
                base_bid = max(DAILY_SALARY * 0.75, highest_prev_bid + 3)
            else: # High HP, try to win but conserve
                base_bid = max(DAILY_SALARY * 0.65, highest_prev_bid + 1)
        # If highest bid was low (or only weak opponents bid high)
        else: # highest_prev_bid < 90
            if my_status['hp'] <= 5: # Moderate HP, ensure water
                base_bid = max(DAILY_SALARY * 0.6, highest_prev_bid + 2)
            else: # High HP, conserve budget
                base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1)
    
    # If no relevant previous bids or initial days
    else:
        if my_status['hp'] <= 5:
            base_bid = DAILY_SALARY * 0.7
        else:
            base_bid = DAILY_SALARY * 0.55

    # Ensure bid does not exceed current budget
    return min(my_status['budget'], base_bid)
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

    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0.0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Base bid strategy
    # Start with a default bid, slightly above a conservative percentage of salary
    base_bid = DAILY_SALARY * 0.6

    # React to yesterday's highest bid to stay competitive
    if max_yesterday_bid > 0:
        # If yesterday's highest bid was very competitive (e.g., >= 80% of salary)
        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            base_bid = max_yesterday_bid + 5.0 # Try to outbid it with a margin
        else:
            # If yesterday's highest was moderate, we still want to be competitive but not overspend
            base_bid = max(base_bid, max_yesterday_bid + 1.0) # Slightly beat it

    # Adjust bid based on my HP
    bid = base_bid

    if my_status['hp'] <= 2: # Critical HP, bid aggressively for survival
        bid = max(bid, DAILY_SALARY * 1.0)
        if my_status['no_water_days'] > 0: # Even more desperate if missed water yesterday
            bid = max(bid, DAILY_SALARY * 1.1) # Go beyond salary if needed
    elif my_status['hp'] <= 5: # Medium HP, still prioritize water strongly
        bid = max(bid, DAILY_SALARY * 0.8)
    else: # High HP, can be more strategic/conservative
        # If supply is abundant for everyone, try to save money
        if day_context['supply'] >= WATER_REQ * len(alive_opponents):
            bid = min(bid, DAILY_SALARY * 0.5) # Bid lower if plentiful supply and safe HP
        else:
            bid = max(bid, DAILY_SALARY * 0.6) # Maintain a decent bid even with high HP if supply is tight

    # Adjust for remaining days, increasing urgency towards the end
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last few days, increase urgency
        if my_status['hp'] <= 3: # Need to survive to the end, go all-in if critical
            bid = my_status['budget']
        else: # Still try to win but save budget if safe
            bid = max(bid, DAILY_SALARY * 0.8)

    # Ensure bid is not more than current budget and at least 1.0
    bid = min(bid, my_status['budget'])
    bid = max(1.0, bid)

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = []
    alex_is_alive = False
    for agent_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            alive_opponents.append(opp_data)
            if agent_id == "Alex":
                alex_is_alive = True
    
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to conserve budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- Base Bid Calculation ---
    # Start with a moderate bid
    base_bid = DAILY_SALARY * 0.55

    # Adjust for my HP and no_water_days
    if my_hp <= 2 or my_no_water_days >= 1: # Critical HP or missed water yesterday
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.75

    # --- Analyze yesterday's bids from alive opponents ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # React to opponent's previous high bids
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very high bid yesterday
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate bid yesterday
            base_bid = max(base_bid, highest_prev_bid + 2)
        else: # Low bids yesterday, but still need to secure water
            # If opponents bid low, don't overspend too much, but ensure we win
            base_bid = max(base_bid, highest_prev_bid + 10)

    # --- Adjust based on number of opponents and specific opponent profiles ---
    if num_alive_opponents >= 2:
        if alex_is_alive:
            # Alex is a known high bidder from LATEST METAROUND CONTEXT
            base_bid = max(base_bid, DAILY_SALARY * 0.8) # Be more aggressive against Alex
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.65) # Moderate aggression if multiple non-Alex opponents

    # --- Adjust for end game ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last couple of days, prioritize survival
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif remaining_days <= 4 and my_hp <= 6: # Mid-late game, low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # --- Final Bid Calculation ---
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least a small amount if budget allows and not critical
    if final_bid < 1.0 and my_budget > 0 and (my_hp > 2 or my_no_water_days == 0):
        final_bid = min(my_budget, DAILY_SALARY * 0.05) # A token bid if budget is tight but not desperate
    elif final_bid < 1.0 and my_budget > 0: # Desperate and low budget
        final_bid = my_budget # Bid everything

    return max(0.0, final_bid) # Bid cannot be negative
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 # From meta-round state, for potential long-term planning

    my_bid = 0.0

    # 1. Critical health check: If HP is very low or I've gone without water
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        my_bid = DAILY_SALARY * 0.95 # Bid very aggressively to survive
    else:
        # 2. Analyze opponents' previous bids
        alive_opponents = [o for o in opponents_status.values() if o['alive']]
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

        highest_prev_bid = 0.0
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)

        # 3. Base bid calculation, adjusted by supply
        base_bid = DAILY_SALARY * 0.5 # Start with a moderate bid

        # Adjust base bid based on current supply
        # If supply is low (factor near 0), increase bid. If high (factor near 1), decrease bid.
        # supply_factor ranges from 0 (MIN_SUPPLY) to 1 (MAX_SUPPLY)
        supply_factor = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        
        # This multiplier makes the bid higher when supply_factor is low, and lower when high.
        # Example: if supply_factor is 0 (min supply), multiplier is 1.2. 
        # if supply_factor is 1 (max supply), multiplier is 0.8.
        supply_multiplier = 1.2 - supply_factor * 0.4 
        base_bid *= supply_multiplier

        # 4. Opponent reaction: Try to outbid the highest previous bid slightly
        if highest_prev_bid > 0:
            my_bid = max(base_bid, highest_prev_bid + 1.0)
        else:
            my_bid = base_bid # No competitive bids yesterday, stick to supply-adjusted base

    # 5. Final bid constraints
    my_bid = min(my_bid, my_status['budget']) # Do not exceed budget
    my_bid = max(my_bid, 1.0) # Ensure a minimum bid to participate, if budget allows

    return my_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimum to survive
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bid
    bid = DAILY_SALARY * 0.5

    # Survival mode: Bid aggressively if HP is low or if water was missed yesterday
    if my_hp <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        bid = DAILY_SALARY * 0.75

    # Analyze opponent's previous bids
    yesterday_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        total_opponent_water_req += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_opp_bid_yesterday = max(yesterday_bids)
        avg_opp_bid_yesterday = sum(yesterday_bids) / len(yesterday_bids)

        # React to high bids from opponents
        if max_opp_bid_yesterday >= DAILY_SALARY * 0.8:
            if my_hp > 3:
                # If HP is good, try to conserve a bit, but still competitive
                bid = max(bid, DAILY_SALARY * 0.65)
            else:
                # If HP is low, be very competitive
                bid = max(bid, DAILY_SALARY * 0.9)
        else:
            # If opponents are not bidding too high, try to slightly outbid average
            bid = max(bid, avg_opp_bid_yesterday + 5.0) # Add a small buffer

    # Adjust bid based on supply scarcity vs total demand
    total_water_demand_all_agents = WATER_REQ + total_opponent_water_req
    if current_supply < total_water_demand_all_agents:
        bid *= 1.1 # Increase bid if water is scarce
    elif current_supply >= total_water_demand_all_agents * 1.5:
        bid *= 0.9 # Decrease bid if water is abundant

    # End game pressure: bid more aggressively on last days
    if current_day >= EPISODE_DAYS - 2: # Last two days
        bid *= 1.1

    # Ensure bid does not exceed budget and is not negative
    final_bid = min(my_budget, bid)
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

    base_bid = DAILY_SALARY * 0.5 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], 1)

    max_prev_bid = 0
    max_opponent_potential_bid_today = 0 

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            max_prev_bid = max(max_prev_bid, prev_trace['bid'])
        
        if opp['hp'] <= 2 or opp['no_water_days'] > 0:
            estimated_desperate_bid = min(opp['budget'], opp['daily_salary'] * 1.05) 
            max_opponent_potential_bid_today = max(max_opponent_potential_bid_today, estimated_desperate_bid)
        elif opp['hp'] <= 4:
            estimated_desperate_bid = min(opp['budget'], opp['daily_salary'] * 0.8)
            max_opponent_potential_bid_today = max(max_opponent_potential_bid_today, estimated_desperate_bid)

    target_bid = max_prev_bid + 5 

    if max_opponent_potential_bid_today > 0:
        target_bid = max(target_bid, max_opponent_potential_bid_today + 5)
    
    target_bid = max(target_bid, base_bid)

    my_desperation_factor = 1.0 

    if my_status['hp'] <= 1:
        my_desperation_factor = 1.2 
    elif my_status['hp'] <= 2:
        my_desperation_factor = 1.15
    elif my_status['no_water_days'] > 0:
        my_desperation_factor = 1.1
    elif my_status['hp'] <= 4:
        my_desperation_factor = 1.05
    
    target_bid = max(target_bid, DAILY_SALARY * my_desperation_factor)

    final_bid = min(my_status['budget'], target_bid)

    return max(1, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # 1. Initialize bid based on my HP urgency
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 1.25  # Desperate: bid very high
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 1.05  # Urgent: bid high
    else:
        bid = DAILY_SALARY * 0.85  # Normal: competitive bid

    # 2. Check for Eric and adjust bid accordingly
    eric_status = opponents_status.get('Eric')
    eric_is_alive = eric_status and eric_status['alive']
    eric_last_bid = 0
    if eric_is_alive and eric_status.get('previous_trace'):
        eric_last_bid = eric_status['previous_trace'].get('bid', 0.0)

    if eric_is_alive:
        # Eric is a strong, aggressive opponent. We must react to his high bids.
        if eric_last_bid > DAILY_SALARY * 0.95: # If Eric bid very aggressively before
            bid = max(bid, eric_last_bid + 5.0) # Try to outbid him by a margin
        else:
            # Eric is alive but didn't bid high last time, or no trace. Assume he will be aggressive.
            bid = max(bid, DAILY_SALARY * 1.1) # Be proactively aggressive against Eric
    else:
        # Eric is not alive. Competition is likely less fierce.
        highest_other_bid = 0.0
        num_other_alive_opponents = 0
        for opp_id, opp_data in opponents_status.items():
            if opp_id != 'Eric' and opp_data['alive']:
                num_other_alive_opponents += 1
                if opp_data.get('previous_trace'):
                    other_bid = opp_data['previous_trace'].get('bid', 0.0)
                    highest_other_bid = max(highest_other_bid, other_bid)
        
        if num_other_alive_opponents > 0:
            if highest_other_bid > DAILY_SALARY * 0.7:
                bid = max(bid, highest_other_bid + 2.0) # React to other strong bids
            else:
                bid = max(bid, DAILY_SALARY * 0.75) # Default competitive bid against other opponents
        else:
            # No active opponents remaining
            bid = DAILY_SALARY * 0.3 # Minimal bid to secure water cheaply

    # 3. Ensure bid does not exceed current budget and is at least a minimal amount
    bid = min(bid, my_status['budget'])
    if bid <= 0:
        return 0.01 # Always bid a minimal amount to stay in the game if budget is zero or negative

    return bid
"""
