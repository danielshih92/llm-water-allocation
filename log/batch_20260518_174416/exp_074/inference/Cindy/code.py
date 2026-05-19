# ============================================================
# Experiment: exp_074
# Agent: Cindy
# Source: exp_074
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a conservative amount to secure water.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Calculate total water needed by all participants (including myself)
    total_water_needed = sum([o['water_requirement'] for o in alive_opponents]) + WATER_REQ

    # Adjust bid based on supply scarcity
    supply_pressure_factor = 1.0
    if day_context['supply'] < total_water_needed * 0.9:
        supply_pressure_factor = 1.2  # Tight supply
    elif day_context['supply'] < total_water_needed * 0.7:
        supply_pressure_factor = 1.4  # Very tight supply
    elif day_context['supply'] > total_water_needed * 1.2:
        supply_pressure_factor = 0.9  # Ample supply

    # Base bid for normal conditions
    base_bid = DAILY_SALARY * 0.5
    current_bid = base_bid

    # Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 4: # Healthy, can afford to be less aggressive
                current_bid = DAILY_SALARY * 0.6
            else: # Low HP or missed water, need to be aggressive
                current_bid = DAILY_SALARY * 0.95
        else: # Opponents were moderate yesterday
            current_bid = max(base_bid, highest_prev_bid + 2.0) # Bid slightly above to secure

    # Health-based override: If critical health or missed water, bid very high
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        current_bid = DAILY_SALARY * 0.95

    # Apply supply pressure factor to the bid
    current_bid *= supply_pressure_factor

    # Ensure bid is non-negative and within budget
    final_bid = max(0.0, current_bid)
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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on my health and water deprivation
    base_bid = DAILY_SALARY * 0.7 # Moderate bid by default

    is_critical_hp = my_hp <= 3 or my_no_water_days > 0

    if is_critical_hp:
        base_bid = DAILY_SALARY * 1.2 # Very aggressive if critical
    elif my_hp <= 5:
        base_bid = DAILY_SALARY * 1.0 # Aggressive if low HP

    bid = base_bid # Initialize bid with base_bid

    # Adjust bid based on opponent's highest previous bid and supply/demand
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Calculate total water requirement for all alive players (including myself)
        total_water_needed = WATER_REQ * (num_alive_opponents + 1)
        
        if current_supply < total_water_needed: # High competition (demand > supply)
            if is_critical_hp:
                bid = max(base_bid, highest_prev_bid + 5) # Bid higher than opponent to secure water
            else:
                bid = max(base_bid * 0.9, highest_prev_bid + 1) # Try to stay competitive
        else: # Lower competition (supply >= demand)
            if is_critical_hp:
                bid = max(base_bid * 0.9, highest_prev_bid * 0.9) # Still need water, but can be slightly less aggressive
            else:
                bid = max(DAILY_SALARY * 0.5, highest_prev_bid * 0.7) # Conserve budget, bid moderately
    
    # Ensure bid does not exceed budget and is at least 1
    final_bid = min(my_budget, bid)
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Default bid, used if no specific conditions are met
    bid_amount = DAILY_SALARY * 0.6 # 90.0

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Scenario 1: No opponents left, bid minimally to get water cheaply
    if not alive_opponents:
        bid_amount = WATER_REQ * 1.5 # 19.5
    
    # Scenario 2: Critical condition (low HP or missed water yesterday)
    elif my_status['no_water_days'] >= 1 or my_status['hp'] <= 2:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # Bid very aggressively to ensure water, significantly above previous high
            bid_amount = max(DAILY_SALARY * 0.95, highest_prev_bid + (DAILY_SALARY * 0.1)) # 142.5 or highest + 15
        else:
            # If no history, bid a strong default for survival
            bid_amount = DAILY_SALARY * 0.9 # 135.0

    # Scenario 3: Not critical, and there are yesterday's bids to react to
    elif yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If previous bids were very high, indicating strong competition
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., highest_prev_bid >= 120
            if my_status['hp'] > 5: # If healthy, take a calculated risk and bid lower to save budget
                bid_amount = DAILY_SALARY * 0.4 # 60.0
            else: # If moderately healthy (HP 3-5), try to compete to stay in game
                # Bid slightly above previous high, aiming to win
                bid_amount = highest_prev_bid + 2.0
                # Ensure a reasonable minimum, but the primary goal is to win this bid
                bid_amount = max(bid_amount, DAILY_SALARY * 0.7) # Ensure it's at least 105
        
        # If previous bids were moderate
        else: # highest_prev_bid < DAILY_SALARY * 0.8 (e.g., < 120)
            # Try to win by slightly outbidding
            bid_amount = highest_prev_bid + 2.0
            # Ensure a reasonable minimum
            bid_amount = max(bid_amount, DAILY_SALARY * 0.5) # Ensure it's at least 75
    
    # Scenario 4: Day 1, no previous bids, and opponents are alive (fresh start for the meta-round day)
    # This acts as an initial competitive bid for the first day if no history.
    if day_context['day'] == 1 and not yesterday_bids and alive_opponents:
        bid_amount = DAILY_SALARY * 0.7 # Start strong, 105.0

    # Final check: Ensure bid doesn't exceed current budget and is at least a minimal amount (e.g., 1)
    final_bid = max(1.0, min(my_status['budget'], bid_amount))
    
    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    # --- Determine base bid based on my HP ---
    # This sets my desperation level
    base_bid_by_hp = 0.0
    if my_status['hp'] <= 2: # Critical: Must win
        base_bid_by_hp = DAILY_SALARY * 1.05 # Willing to slightly overpay salary to survive
    elif my_status['hp'] <= 4: # Low: Strong need to win
        base_bid_by_hp = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 6: # Moderate: Good to win
        base_bid_by_hp = DAILY_SALARY * 0.75
    else: # High: Can afford to be conservative
        base_bid_by_hp = DAILY_SALARY * 0.6

    bid = base_bid_by_hp

    # --- Adjust bid based on supply scarcity ---
    # Lower supply means higher competition, so increase bid
    supply_level = day_context['supply']
    supply_pressure_factor = 1.0
    if supply_level <= 15: # Very scarce (only one winner possible for 13 units)
        supply_pressure_factor = 1.15
    elif supply_level <= 18: # Scarce (1-2 winners possible)
        supply_pressure_factor = 1.08
    elif supply_level >= 22: # Abundant (2 winners likely)
        supply_pressure_factor = 0.95
    
    bid *= supply_pressure_factor

    # --- Consider opponent's previous bids ---
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid very low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    if highest_prev_bid > 0:
        # If opponents are bidding high, we need to be competitive, especially if we need water.
        if my_status['hp'] <= 4: # Desperate or low HP, must exceed previous high to win
            bid = max(bid, highest_prev_bid + 5)
        elif my_status['hp'] <= 6: # Moderate HP, try to win but don't overpay too much
            bid = max(bid, highest_prev_bid + 1)
        else: # High HP, be more strategic. Only match/slightly exceed if highest_prev_bid is reasonable.
            if highest_prev_bid < DAILY_SALARY * 0.8: # If opponent bid was low/moderate
                bid = max(bid, highest_prev_bid + 1)
            else: # If opponent bid was high, consider if it's worth chasing or saving budget
                bid = max(bid, DAILY_SALARY * 0.7) # Stick to a reasonable, capped bid
    
    # --- Cap bid if not critical HP and significantly over salary ---
    # Alex and David bid above salary. We might need to, but not always if HP is high.
    if bid > DAILY_SALARY * 1.1 and my_status['hp'] > 2: 
        bid = min(bid, DAILY_SALARY * 1.1) # Cap bid to avoid overspending unnecessarily when not critical

    # --- Final adjustments ---
    # Ensure bid doesn't exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimum positive value
    bid = max(1.0, bid)

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to secure water cheaply
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy
    bid = DAILY_SALARY * 0.6 # Moderate default

    # Adjust based on my HP and recent water status
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: # Low HP
        bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        bid = DAILY_SALARY * 0.75
    else: # Healthy HP, can be more conservative
        bid = DAILY_SALARY * 0.55

    # Adjust based on supply scarcity
    # Calculate approximate water units per active player (including myself)
    approx_units_per_player = day_context['supply'] / (num_alive_opponents + 1)

    if approx_units_per_player < WATER_REQ: # Supply is tight, competition is high
        bid *= 1.15
    elif approx_units_per_player > WATER_REQ * 1.5: # Supply is abundant
        bid *= 0.9

    # Adjust based on opponent's highest yesterday bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was very high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If I'm desperate, I must beat it
            if my_status['hp'] <= 5 or my_status['no_water_days'] > 0:
                bid = max(bid, highest_prev_bid * 1.05)
            else: # If healthy, I can choose to be slightly less aggressive or match
                bid = max(bid, highest_prev_bid * 1.01) # Still competitive
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate bids
            bid = max(bid, highest_prev_bid + 2.0) # Slightly outbid
        else: # Low bids, try to win cheaply but ensure I get water
            bid = max(bid, highest_prev_bid * 1.1)
    
    # End game pressure
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 5 or my_status['no_water_days'] > 0: # Desperate in end game
            bid = max(bid, DAILY_SALARY * 0.98)
        else: # Healthy but competition might increase
            bid *= 1.05

    # Final bid must not exceed budget and have a floor
    final_bid = min(my_status['budget'], bid)
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Minimum bid to stay in the game

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    else:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    
    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Get yesterday's competitive bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            # Consider bids above a threshold as serious competition
            if prev['bid'] >= (DAILY_SALARY * 0.5):
                yesterday_bids.append(prev['bid'])
    
    # Determine base bid based on my health and competition level
    bid = 0.0
    available_slots = int(day_context['supply'] // WATER_REQ)

    if my_status['hp'] <= 2: # Critical HP, must win
        bid = DAILY_SALARY * 0.99
    elif my_status['hp'] <= 5: # Low HP, bid aggressively
        bid = DAILY_SALARY * 0.90
    else: # Healthy HP, be strategic
        if available_slots == 1: # High competition for single water unit
            if num_alive_opponents >= 2:
                bid = DAILY_SALARY * 0.85
            else:
                bid = DAILY_SALARY * 0.75
        elif available_slots >= 2: # More water available
            if num_alive_opponents >= 2:
                bid = DAILY_SALARY * 0.78
            else:
                bid = DAILY_SALARY * 0.70

    # Adjust bid based on highest previous bid from competitive opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_status['hp'] <= 5: # Low HP, must outbid
            bid = max(bid, highest_prev_bid + 5)
        else: # Healthy HP, adjust based on competition
            if available_slots == 1 and num_alive_opponents >= 2:
                bid = max(bid, highest_prev_bid + 2)
            elif available_slots >= 2 and num_alive_opponents >= 2:
                bid = max(bid, highest_prev_bid + 1)
            else:
                bid = max(bid, highest_prev_bid * 1.0) # Match or slightly exceed if current bid is lower

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid)

    # Ensure final bid is not negative and at least 1.0 if budget allows
    if my_status['budget'] > 0:
        final_bid = max(1.0, final_bid)
    else:
        final_bid = 0.0
        
    return final_bid
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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.65

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + 2)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.55)
    
    if my_status['hp'] <= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.85)
    elif my_status['hp'] >= 8 and my_status['budget'] > DAILY_SALARY * 5:
        base_bid = min(base_bid, DAILY_SALARY * 0.7)

    current_day = day_context['day']
    if current_day >= EPISODE_DAYS - 2:
        if my_status['hp'] <= 4:
            base_bid = max(base_bid, DAILY_SALARY * 0.98)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    supply = day_context['supply']
    if int(supply // WATER_REQ) < (num_alive_opponents + 1) and int(supply // WATER_REQ) <= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif int(supply // WATER_REQ) < (num_alive_opponents + 1):
        base_bid *= 1.1

    final_bid = min(my_status['budget'], base_bid)
    
    if my_status['budget'] > 0:
        final_bid = max(final_bid, 0.01)
    else:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Identify strong opponents based on previous meta-round context
    strong_opponent_ids = ["Alex", "David"]
    strong_alive_opponents = [o for o_id, o in opponents_status.items() if o['alive'] and o_id in strong_opponent_ids]

    yesterday_strong_bids = []
    for opp in strong_alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_strong_bids.append(prev['bid'])

    # If no strong opponents, or no bids from them yesterday, consider all alive opponents
    if not yesterday_strong_bids:
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_strong_bids.append(prev['bid'])
        # If still no bids (e.g., day 1, or all opponents died/didn't bid)
        if not yesterday_strong_bids:
            # Default bid strategy
            if my_hp <= 2: # Critical HP
                return min(my_budget, DAILY_SALARY * 1.1) # Aggressive bid
            elif my_hp <= 4: # Low HP
                return min(my_budget, DAILY_SALARY * 0.9)
            else: # Healthy HP
                return min(my_budget, DAILY_SALARY * 0.7)

    highest_prev_bid = max(yesterday_strong_bids)

    # Calculate how many agents can get full water
    num_possible_winners = int(current_supply // WATER_REQ)

    # Number of active competitors (me + alive opponents)
    num_competitors = len(alive_opponents) + 1

    # Strategy based on HP and supply scarcity
    if my_hp <= 2: # Critical HP, must get water
        return min(my_budget, max(highest_prev_bid + 5, DAILY_SALARY * 1.1))
    elif my_hp <= 4: # Low HP, need water
        if num_possible_winners < num_competitors: # Scarce supply
            return min(my_budget, max(highest_prev_bid + 2, DAILY_SALARY * 0.95))
        else: # Abundant supply
            return min(my_budget, max(highest_prev_bid + 1, DAILY_SALARY * 0.85))
    else: # Healthy HP
        if num_possible_winners == 1 and num_competitors > 1: # Very scarce, only one winner
            return min(my_budget, max(highest_prev_bid + 3, DAILY_SALARY * 0.9)) # Still need to compete
        elif num_possible_winners < num_competitors: # Scarce supply, but more than 1 winner possible
            return min(my_budget, max(highest_prev_bid + 1, DAILY_SALARY * 0.8))
        else: # Abundant supply
            return min(my_budget, DAILY_SALARY * 0.7) # Save budget
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to win
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1) # Bid low but positive

    # Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
    
    # Calculate base bid
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        
        # If competition was high yesterday, adjust base bid upwards
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Slightly higher than max
        elif average_prev_bid > DAILY_SALARY * 0.6:
            base_bid = max(base_bid, average_prev_bid * 1.1) # Slightly higher than average
        else:
            base_bid = max(base_bid, average_prev_bid * 0.9) # Try to save if bids were low
    
    # Adjust bid based on my HP
    if my_hp <= 3: # Critical HP
        # Bid very aggressively to get water
        bid_multiplier_hp = 1.1 # Increase bid
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Ensure a high floor
    elif my_hp <= 6: # Medium HP
        bid_multiplier_hp = 1.05
    else: # Healthy HP
        bid_multiplier_hp = 0.95 # Can afford to bid a bit lower
        
    base_bid *= bid_multiplier_hp

    # Adjust bid based on remaining days
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # End game, need to survive
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid very high
    elif remaining_days <= 5: # Mid-game, keep pressure
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Adjust bid based on supply relative to water requirement and number of opponents
    available_water_units = int(current_supply // WATER_REQ) # Use int() for comparison
    
    if available_water_units < num_alive_opponents + 1: # Tight supply
        base_bid *= 1.15 # Increase bid
    elif available_water_units >= num_alive_opponents + 2: # Ample supply
        base_bid *= 0.85 # Decrease bid

    # Final bid must be within budget and reasonable.
    final_bid = min(my_budget, base_bid)
    
    # Ensure bid is at least a minimum to be considered serious, but not zero.
    if final_bid < DAILY_SALARY * 0.1:
        final_bid = DAILY_SALARY * 0.1
        
    # Cap bid at daily salary if not critical, to save budget
    if my_hp > 3 and final_bid > DAILY_SALARY:
        final_bid = DAILY_SALARY
        
    return final_bid
"""
