# ============================================================
# Experiment: exp_066
# Agent: Cindy
# Source: exp_066
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount as water is guaranteed
    if not alive_opponents:
        return min(my_status['budget'], 1)

    current_supply = day_context['supply']
    my_hp = my_status['hp']

    # Calculate total water needed if everyone gets their requirement
    total_opponent_water_req = sum(opp['water_requirement'] for opp in alive_opponents)
    total_expected_demand = WATER_REQ + total_opponent_water_req

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on general strategy and opponent behavior
    base_bid = DAILY_SALARY * 0.5  # Default medium bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Adjust base bid based on opponent's previous bids
        if highest_prev_bid > DAILY_SALARY * 0.7:  # Opponents bidding high
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Try to outbid slightly
        elif highest_prev_bid < DAILY_SALARY * 0.3:  # Opponents bidding low
            base_bid = min(base_bid, highest_prev_bid * 1.2) # Don't bid too low, but try to save
        else:  # Moderate bids
            base_bid = max(base_bid, avg_prev_bid * 1.1) # Slightly above average

    # Further adjust based on supply scarcity
    if current_supply < total_expected_demand:
        # Supply is scarce, increase bid to compete
        base_bid = base_bid * 1.2
    elif current_supply >= total_expected_demand + WATER_REQ: # More than enough for everyone to get water_req
        # Supply is abundant, decrease bid to save budget
        base_bid = base_bid * 0.8

    # Adjust based on my HP (survival priority)
    final_bid = base_bid
    if my_hp <= 1:  # Desperate: 2 consecutive days without water (or 1 day left of HP)
        final_bid = DAILY_SALARY * 0.95
    elif my_hp == 2:  # Critical: 1 day without water (or 2 days left of HP)
        final_bid = max(base_bid * 1.3, DAILY_SALARY * 0.75)

    # Ensure bid is positive and within budget
    final_bid = max(1, final_bid)
    final_bid = min(my_status['budget'], final_bid)

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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    target_bid = DAILY_SALARY * 0.75 # Default for Day 1 or if no previous bids

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.9: 
            target_bid = highest_prev_bid + 5.0
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            target_bid = highest_prev_bid + 2.0
        else:
            target_bid = highest_prev_bid + 1.5
    
    if my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        target_bid = max(target_bid, DAILY_SALARY * 1.05)
    elif my_status['hp'] <= 5:
        target_bid = max(target_bid, DAILY_SALARY * 0.95)
    else:
        target_bid = max(target_bid, DAILY_SALARY * 0.8)

    remaining_days = EPISODE_DAYS - day_context['day'] + 1
    if remaining_days <= 3 and my_status['hp'] <= 3:
        target_bid = max(target_bid, DAILY_SALARY * 1.1)
    
    final_bid = min(my_status['budget'], target_bid)
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    CRITICAL_HP_THRESHOLD = 3  # If HP is <= this, bid very aggressively
    DESPERATE_HP_THRESHOLD = 5 # If HP is <= this, bid aggressively

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimum to conserve budget
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.1))

    # Given supply_range [15, 25] and WATER_REQ = 13, num_slots_available will always be 1.
    # This means competition for full water is always high.

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_opp_yesterday_bid = 0.0
    if yesterday_bids:
        max_opp_yesterday_bid = max(yesterday_bids)

    my_bid = 0.0

    # --- Base Bid Strategy based on HP and opponent reaction ---
    if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        # Critically low HP, bid very aggressively, potentially above salary
        my_bid = DAILY_SALARY * 1.1 # Default to 110% of salary
        if max_opp_yesterday_bid > 0:
            my_bid = max(my_bid, max_opp_yesterday_bid + 5) # Try to outbid yesterday's max by a small margin

    elif my_status['hp'] <= DESPERATE_HP_THRESHOLD:
        # Desperate HP, bid aggressively
        my_bid = DAILY_SALARY * 0.95 # Default to 95% of salary
        if max_opp_yesterday_bid > 0:
            my_bid = max(my_bid, max_opp_yesterday_bid + 2) # Try to outbid yesterday's max

    else:
        # Normal HP, but competition is always high for full water.
        # Base bid is medium, but react to high opponent bids.
        my_bid = DAILY_SALARY * 0.7 # Default competitive bid (70% of salary)
        if max_opp_yesterday_bid > 0:
            # If opponents bid high yesterday (e.g., > 80% of my salary), match or slightly exceed
            if max_opp_yesterday_bid >= DAILY_SALARY * 0.8:
                my_bid = max(my_bid, max_opp_yesterday_bid + 1)
            else: # If yesterday's max was lower, bid slightly more than their low bid
                my_bid = max(my_bid, max_opp_yesterday_bid * 1.05)
        # Ensure a minimum competitive bid even if no strong previous bids
        my_bid = max(my_bid, DAILY_SALARY * 0.6)

    # --- Adjust for early/late game dynamics ---
    # Early game aggression to establish dominance or secure water if budget allows
    if day_context['day'] <= 2 and my_status['budget'] >= DAILY_SALARY * 2:
        my_bid = max(my_bid, DAILY_SALARY * 0.8)

    # Late game desperation if HP is low
    if day_context['day'] >= 8 and my_status['hp'] <= DESPERATE_HP_THRESHOLD:
        my_bid = max(my_bid, DAILY_SALARY * 1.2) # Bid very high to survive the last days

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], my_bid)
    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

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
    MIN_SUPPLY = 15 
    MAX_SUPPLY = 25 

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid for general competition
    base_competitive_bid = DAILY_SALARY * 0.65 

    # --- Phase 1: Immediate survival or easy win conditions ---
    if my_hp <= 2: # Critical health, must get water
        return min(my_budget, DAILY_SALARY * 0.98) # Very aggressive
    
    if num_alive_opponents == 0: # No opponents, bid minimum to save budget
        return min(my_budget, DAILY_SALARY * 0.2)

    # --- Phase 2: React to yesterday's bids and current supply ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
    
    bid_to_make = base_competitive_bid

    # Adjust bid based on max_yesterday_bid
    if max_yesterday_bid > DAILY_SALARY * 0.8: # Opponents were very aggressive yesterday
        if my_hp > 5: # My HP is good, can be slightly conservative but still competitive
            bid_to_make = max(base_competitive_bid, max_yesterday_bid * 0.95)
        else: # My HP is moderate, need to be aggressive
            bid_to_make = max(base_competitive_bid, max_yesterday_bid + 5)
    elif max_yesterday_bid > DAILY_SALARY * 0.5: # Opponents were moderately aggressive
        bid_to_make = max(base_competitive_bid, max_yesterday_bid + 2)
    elif max_yesterday_bid > 0: # Opponents were not very aggressive, try to win cheaply
        bid_to_make = max(base_competitive_bid * 0.8, max_yesterday_bid + 1)
    else: # No meaningful bids yesterday, or all bids were 0
        bid_to_make = base_competitive_bid # Stick to base competitive

    # Adjust bid based on supply scarcity
    # Calculate effective demand: My water_req + sum of opponents' water_req
    total_water_demand = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

    if current_supply < total_water_demand: # Supply is scarce
        bid_to_make *= 1.1 # Increase bid by 10%
        # If supply is very low (e.g., barely enough for me), be even more aggressive
        if current_supply < WATER_REQ * 1.5: 
            bid_to_make *= 1.15 # Further increase by 15%
    elif current_supply > total_water_demand * 1.5: # Supply is abundant
        bid_to_make *= 0.9 # Decrease bid by 10%
        # If supply is extremely high (e.g., max_supply), try to bid even lower
        if current_supply == MAX_SUPPLY:
            bid_to_make *= 0.9 # Further decrease by 10%

    # --- Phase 3: End game adjustments ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        # If I have enough budget to survive, be aggressive to win
        if my_budget >= DAILY_SALARY * (remaining_days + 1): # Can afford water for remaining days
            bid_to_make = max(bid_to_make, DAILY_SALARY * 0.9)
        else: # Budget is tight, bid what I can afford to survive
            bid_to_make = min(my_budget, DAILY_SALARY * 0.8) # Still try to be strong

    # --- Final clamping ---
    final_bid = min(my_budget, bid_to_make)
    
    # Ensure a minimum bid to stay in contention, but not so low that it's always outbid
    final_bid = max(final_bid, DAILY_SALARY * 0.15) # Minimum 15% of salary

    # Add a small buffer to avoid ties in case of identical logic
    final_bid += (current_day / EPISODE_DAYS) * 0.01 

    # Ensure bid is not negative or ridiculously small if budget is minimal
    final_bid = max(0.01, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_budget, 1.0)

    # Base bid strategy
    bid_amount = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on supply scarcity
    # Higher scarcity (supply closer to MIN_SUPPLY) -> higher bid
    # Supply pressure factor: 1.0 at MIN_SUPPLY, 0.0 at MAX_SUPPLY
    supply_pressure_factor = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
    bid_amount += supply_pressure_factor * (DAILY_SALARY * 0.3) # Add up to 30% of salary for scarcity

    # Adjust bid based on my health and no-water days
    if my_hp <= 2: # Critical health, bid very high
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95)
    elif my_hp <= 4 or my_no_water_days > 0: # Low health or missed water, bid high
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
    elif my_hp <= 6: # Medium health
        bid_amount = max(bid_amount, DAILY_SALARY * 0.6)

    # Adjust bid based on game progression
    # Later days mean more urgency
    if current_day >= EPISODE_DAYS * 0.7: # Last 30% of days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
    elif current_day >= EPISODE_DAYS * 0.5: # Mid-game
        bid_amount = max(bid_amount, DAILY_SALARY * 0.65)

    # React to opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If a high bid was placed yesterday, consider matching or slightly exceeding it
        if max_yesterday_bid >= DAILY_SALARY * 0.7: # A significant bid from yesterday
            # If my HP is low, I must compete
            if my_hp <= 4 or my_no_water_days > 0:
                bid_amount = max(bid_amount, max_yesterday_bid + 5) # Bid slightly higher
            else: # If my HP is good, I can be slightly less aggressive
                bid_amount = max(bid_amount, max_yesterday_bid * 1.02) # Slightly above, but not too much

        # If average bid was low and my HP is good, maybe I can save money
        elif avg_yesterday_bid < DAILY_SALARY * 0.4 and my_hp > 6:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.45) # Lower my bid if competition seems weak

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, bid_amount)

    # Ensure bid is at least 1.0 to participate
    return max(1.0, final_bid)
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

    # If no opponents are alive, bid just enough to get water.
    if not alive_opponents:
        return int(min(my_status['budget'], 1))

    # Determine my urgency based on HP
    is_desperate_hp = my_status['hp'] <= 1 # Must get water
    is_critical_hp = my_status['hp'] <= 2 and not is_desperate_hp # Can miss one more day, but risky

    # Calculate highest previous bid from active opponents
    highest_prev_bid_overall = 0
    alex_prev_bid = 0
    alex_is_alive = False

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                if opp_id == "Alex":
                    alex_prev_bid = prev['bid']
                    alex_is_alive = True
                highest_prev_bid_overall = max(highest_prev_bid_overall, prev['bid'])

    # Initialize a base bid. This is what I'd bid if no specific opponent pressure.
    # A strong, sustainable bid that often wins in a competitive environment.
    base_target_bid = DAILY_SALARY * 0.75 # Default to 112.5

    # Adjust base bid if there were high bids yesterday, aiming to outbid.
    if alex_is_alive and alex_prev_bid > 0:
        base_target_bid = max(base_target_bid, alex_prev_bid + 5)
    elif highest_prev_bid_overall > 0:
        base_target_bid = max(base_target_bid, highest_prev_bid_overall + 5)
    
    # Adjust bid further based on my HP urgency
    final_bid_value = base_target_bid

    if is_desperate_hp:
        # If I must get water, bid very aggressively, near my salary cap.
        final_bid_value = max(final_bid_value, DAILY_SALARY * 0.95) # 142.5
    elif is_critical_hp:
        # If HP is low but not desperate, still bid aggressively.
        final_bid_value = max(final_bid_value, DAILY_SALARY * 0.85) # 127.5
    else: # HP is good (HP > 2)
        # If HP is good, I can be slightly more conservative but still competitive.
        # The base_target_bid already accounts for beating previous bids.
        if alex_is_alive:
            # If Alex is alive, ensure a strong competitive bid even with good HP.
            final_bid_value = max(final_bid_value, DAILY_SALARY * 0.8) # Ensure at least 120
        else:
            # If Alex is not alive, and HP is good, I can be more conservative.
            final_bid_value = max(final_bid_value, DAILY_SALARY * 0.65) # 97.5
            final_bid_value = min(final_bid_value, DAILY_SALARY * 0.8) # Cap at 120

    # Ensure bid does not exceed my budget
    final_bid_value = min(my_status['budget'], final_bid_value)
    
    # If budget is 0, I can't bid.
    if my_status['budget'] <= 0:
        return 0
    
    # If the calculated bid is non-positive, but I have budget, bid minimum to participate.
    if final_bid_value <= 0:
        return 1 

    return int(final_bid_value)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.5

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    current_bid = base_bid
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        current_bid = DAILY_SALARY * 0.8

    if day_context['supply'] <= WATER_REQ * 1.5:
        current_bid = max(current_bid, DAILY_SALARY * 0.7)
        if day_context['supply'] < WATER_REQ + 5:
             current_bid = max(current_bid, DAILY_SALARY * 0.85)

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            current_bid = max(current_bid, highest_prev_bid + 5.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            current_bid = max(current_bid, highest_prev_bid + 2.0)

    final_bid = min(my_status['budget'], current_bid)

    if day_context['day'] == EPISODE_DAYS and my_status['hp'] < 10:
        final_bid = my_status['budget']

    if final_bid <= 0.0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_HP = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        if my_status['hp'] < MAX_HP:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] >= 8:
        base_bid = DAILY_SALARY * 0.45

    my_calculated_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                my_calculated_bid = DAILY_SALARY * 0.3
            else:
                my_calculated_bid = DAILY_SALARY * 0.95
        else:
            my_calculated_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)

            if my_status['hp'] <= 2:
                my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.95)
            elif my_status['hp'] == 3:
                my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.8)
            elif my_status['hp'] <= 5:
                my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.65)

            my_calculated_bid = min(my_calculated_bid, DAILY_SALARY * 0.98)

    current_supply = day_context['supply']
    max_full_water_recipients = int(current_supply // WATER_REQ)

    if max_full_water_recipients < num_alive_opponents + 1:
        if my_status['hp'] <= 5:
            my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.85)
        elif my_status['hp'] <= 7:
            my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.7)
    
    if max_full_water_recipients == 0 and current_supply > 0:
        if my_status['hp'] <= 5:
            my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 7:
            my_calculated_bid = max(my_calculated_bid, DAILY_SALARY * 0.75)

    final_bid = min(my_status['budget'], my_calculated_bid)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Scenario 1: No opponents left, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents for immediate reaction
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Calculate base bid
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust base bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP, bid aggressively
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: # Good HP, can conserve a bit
        base_bid = DAILY_SALARY * 0.6
    
    # Adjust bid based on supply and number of competitors
    supply = day_context['supply']
    potential_full_water_units = int(supply / WATER_REQ) # How many agents can get full water_req

    if potential_full_water_units == 0: # Supply less than my requirement, very high competition for any water
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif potential_full_water_units == 1 and num_alive_opponents >= 1: # Only one full water unit available for multiple agents
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif potential_full_water_units >= (num_alive_opponents + 1): # Enough water for everyone to get full requirement
        base_bid = min(base_bid, DAILY_SALARY * 0.3) # Bid low
    else: # Moderate competition based on supply
        base_bid = max(base_bid, DAILY_SALARY * 0.7)


    # Reactive bidding based on opponent's previous bids
    final_bid = base_bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, react strongly
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_status['hp'] <= 3: # My HP is very low, must try to outbid
                final_bid = max(final_bid, highest_prev_bid + 5)
            else: # My HP is okay, can be slightly less aggressive
                final_bid = max(final_bid, highest_prev_bid * 0.95) # Stay competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            final_bid = max(final_bid, highest_prev_bid + 2)
        else: # Opponent bids were generally low
            final_bid = max(final_bid, highest_prev_bid + 1)
    
    # Ensure bid is within budget and at least 1
    final_bid = min(final_bid, my_status['budget'])
    final_bid = max(1.0, final_bid)

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_bid = DAILY_SALARY * 0.5

    # Health-based adjustment (prioritize survival)
    if my_status['hp'] <= 1:
        my_bid = DAILY_SALARY * 0.99
    elif my_status['hp'] <= 3:
        my_bid = DAILY_SALARY * 0.90
    elif my_status['hp'] <= 5:
        my_bid = DAILY_SALARY * 0.75

    # Adjust based on opponent's highest previous bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_status['hp'] > 5:
            if highest_prev_bid >= DAILY_SALARY * 0.85:
                if day_context['supply'] < WATER_REQ * (num_alive_opponents + 1):
                    my_bid = max(my_bid, highest_prev_bid + 2)
                else:
                    my_bid = max(my_bid, DAILY_SALARY * 0.6)
            elif highest_prev_bid < DAILY_SALARY * 0.4:
                my_bid = max(my_bid, highest_prev_bid + 5)
            else:
                my_bid = max(my_bid, highest_prev_bid + 1)
        else:
            my_bid = max(my_bid, highest_prev_bid + 3)

    # Further adjustment based on supply scarcity
    if day_context['supply'] <= WATER_REQ:
        my_bid = max(my_bid, DAILY_SALARY * 0.95)
    elif day_context['supply'] <= WATER_REQ * 2:
        my_bid = max(my_bid, DAILY_SALARY * 0.8)

    # End game strategy
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['budget'] > DAILY_SALARY * 1.5:
        my_bid = max(my_bid, DAILY_SALARY * 0.98)

    final_bid = min(my_status['budget'], my_bid)
    final_bid = max(final_bid, 0.0)

    return final_bid
"""
