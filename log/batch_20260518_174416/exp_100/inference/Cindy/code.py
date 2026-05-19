# ============================================================
# Experiment: exp_100
# Agent: Cindy
# Source: exp_100
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. If no opponents, bid minimally to secure water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 2. Survival mode: If HP is critically low
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 3. Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # 4. Determine base bid and adjust based on supply and competition
    current_supply = day_context['supply']
    my_water_needed = WATER_REQ
    
    # Calculate total water needed by all active players (including me)
    total_water_demand = my_water_needed + sum(o['water_requirement'] for o in alive_opponents)
    
    # Base bid strategy
    base_bid = DAILY_SALARY * 0.45

    # Adjust bid based on supply scarcity
    if current_supply < total_water_demand:
        # Supply is tight, competition will be high
        if highest_prev_bid > base_bid:
            # Bid slightly above the highest previous bid, but don't overspend if my HP is good
            if my_status['hp'] > 3: # Not desperate
                bid = max(base_bid, highest_prev_bid * 1.05)
            else: # Getting desperate
                bid = max(base_bid, highest_prev_bid * 1.1)
        else:
            # No high previous bids, but supply is tight, so bid a bit higher than base
            bid = base_bid * 1.2
    else:
        # Supply is sufficient for everyone or most
        if highest_prev_bid > base_bid:
            # No need to bid too high if supply is good, but stay competitive
            bid = max(base_bid, highest_prev_bid * 0.8)
        else:
            # Supply is good, and opponents didn't bid high yesterday. Can bid lower.
            bid = base_bid * 0.8

    # Ensure bid is within budget and reasonable limits
    final_bid = min(my_status['budget'], max(1.0, bid))

    # Consider end-game desperation if day is high
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] <= 3: # Still need water
            final_bid = min(my_status['budget'], DAILY_SALARY * 0.9)

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

    available_water_packages = int(day_context['supply'] // WATER_REQ)

    # Base bid strategy based on personal health
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 2:
        my_bid = DAILY_SALARY * 1.05  # Very aggressive if critical
    elif my_status['hp'] <= 4:
        my_bid = DAILY_SALARY * 0.9   # Aggressive if low health
    else:
        my_bid = DAILY_SALARY * 0.65  # Moderate if healthy

    # Adjust based on supply scarcity vs. total bidders
    total_bidders = num_alive_opponents + 1
    if available_water_packages < total_bidders:
        # High competition: Not enough water for everyone
        if my_status['no_water_days'] > 0 or my_status['hp'] <= 4:
            my_bid *= 1.1  # Increase bid significantly if desperate
        else:
            my_bid *= 1.05 # Increase moderately
    elif available_water_packages >= total_bidders + 1:
        # Low competition: More than enough water for everyone
        if my_status['hp'] > 5:
            my_bid *= 0.9  # Try to save money if healthy
        else:
            my_bid *= 0.95 # Slight reduction if not perfectly healthy

    # Analyze yesterday's bids from opponents to adjust
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high and I need water, I must outbid.
        if highest_prev_bid >= DAILY_SALARY * 0.9 and (my_status['no_water_days'] > 0 or my_status['hp'] <= 4):
            my_bid = max(my_bid, highest_prev_bid + 5)
        # If opponents are generally bidding high, but I'm not desperate, try to outbid slightly.
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            my_bid = max(my_bid, highest_prev_bid + 1)
        # If opponents are bidding low, ensure I win cheaply
        elif highest_prev_bid < DAILY_SALARY * 0.4:
            my_bid = max(my_bid, highest_prev_bid + 1)
            
    # Cap the bid at my current budget
    final_bid = min(my_bid, my_status['budget'])

    # Ensure a minimum bid if I have budget and need water, unless it's the last day and I'm very healthy
    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] < EPISODE_DAYS:
        final_bid = 1.0 
    
    # If budget is zero, I cannot bid
    if my_status['budget'] <= 0:
        return 0.0

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 

    current_day = day_context['day']
    current_supply = day_context['supply']

    # --- 1. Determine a base bid based on my health and day ---
    base_bid = DAILY_SALARY * 0.6 

    # If I'm in bad shape (low HP or no water days), bid aggressively
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 1.0 
    elif current_day >= EPISODE_DAYS - 3: # Late game (last 3 days), push more
        base_bid = DAILY_SALARY * 1.2 

    # --- 2. Adjust bid based on opponent's previous behavior ---
    max_opp_prev_bid = 0.0
    eric_prev_bid = 0.0

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                max_opp_prev_bid = max(max_opp_prev_bid, prev['bid'])
                if opp_id == "Eric":
                    eric_prev_bid = prev['bid']
    
    # If Eric is alive and his previous bid was high, react strongly
    if eric_prev_bid > DAILY_SALARY * 0.9: 
        if my_status['hp'] <= 4: 
            base_bid = max(base_bid, eric_prev_bid + 10.0) 
        else: 
            base_bid = max(base_bid, eric_prev_bid * 1.05) 

    # Also consider general max opponent bid if Eric isn't the highest or not present
    if max_opp_prev_bid > base_bid * 0.8: 
        if my_status['hp'] <= 3:
            base_bid = max(base_bid, max_opp_prev_bid + 5.0)
        else:
            base_bid = max(base_bid, max_opp_prev_bid * 0.9)


    # --- 3. Adjust bid based on supply scarcity ---
    supply_pressure_factor = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
    adjusted_bid = base_bid * (1 + supply_pressure_factor * 0.25)

    # --- 4. Ensure bid is within budget and reasonable limits ---
    final_bid = min(my_status['budget'], adjusted_bid)
    
    # Ensure a minimum bid to at least try to get water
    final_bid = max(final_bid, DAILY_SALARY * 0.1) 
    
    return float(final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            # Consider opponents who bid at least half their daily salary as strong competitors
            # This filters out the 'low-bid-and-die' types like Bob/Eric based on meta-round context
            if prev['bid'] >= DAILY_SALARY * 0.5:
                yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy
    current_bid = DAILY_SALARY * 0.6 # Moderate base bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        current_bid = DAILY_SALARY * 1.1 # Aggressive bid
        if my_status['no_water_days'] > 0: # Even more desperate if already missed water
            current_bid = DAILY_SALARY * 1.3
    elif my_status['hp'] <= 4: # Low HP
        current_bid = DAILY_SALARY * 0.9
    else: # Healthy HP
        # Adjust based on highest previous bid from strong competitors
        if highest_prev_bid > 0:
            if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents are bidding very high
                # Number of players who can get full water based on current supply
                num_potential_winners = int(day_context['supply'] // WATER_REQ)
                if num_potential_winners == 0: 
                    num_potential_winners = 1 # At least one can get partial water if they bid enough
                
                # If there are more strong competitors than water slots, increase bid significantly
                if len(yesterday_bids) >= num_potential_winners:
                    current_bid = max(current_bid, highest_prev_bid + DAILY_SALARY * 0.1) # Bid significantly above
                else:
                    current_bid = max(current_bid, highest_prev_bid + DAILY_SALARY * 0.05) # Slightly above
            else: # Opponents are bidding moderately
                current_bid = max(current_bid, highest_prev_bid + 1.0) # Just slightly above

        # If supply is low, increase bid to secure water
        if day_context['supply'] < WATER_REQ * 2: # If supply is less than enough for 2 players
             current_bid = max(current_bid, DAILY_SALARY * 0.75)

    # Final check: Don't bid more than budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure a minimum bid if budget allows and not completely giving up
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    
    # If budget is very low but HP is critical, bid a large portion to survive
    if my_status['budget'] > 0 and my_status['hp'] <= 3:
        final_bid = min(my_status['budget'], max(final_bid, my_status['budget'] * 0.8))

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.5 # Default to 75

    # If no opponents, bid conservatively
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.3) # 45

    # Analyze previous bids from active opponents
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])

    max_prev_bid = 0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    # Adjust bid based on max previous bid
    bid = base_bid # Initialize with base bid
    if max_prev_bid > DAILY_SALARY * 0.7: # If yesterday's top bid was > 105
        # High competition detected
        if my_hp <= 2 or my_no_water_days > 0:
            # Desperate situation, bid very aggressively
            bid = DAILY_SALARY * 0.95 # 142.5
        elif my_hp <= 4:
            # Low HP, but not critical, try to outbid slightly
            bid = max_prev_bid + 5
        else:
            # Healthy, but high competition, bid robustly
            bid = DAILY_SALARY * 0.75 # 112.5
    elif max_prev_bid > DAILY_SALARY * 0.4: # If yesterday's top bid was > 60
        # Moderate competition
        bid = max(base_bid, max_prev_bid + 2) # Slightly above previous max
    else:
        # Low competition or no significant bids, stick to base or slightly lower
        bid = DAILY_SALARY * 0.55 # 82.5

    # Further adjust based on my HP and no_water_days
    if my_hp <= 1: # Critical HP
        bid = DAILY_SALARY * 0.99 # 148.5
    elif my_hp <= 3: # Low HP
        bid = max(bid, DAILY_SALARY * 0.85) # 127.5 - ensure it's high enough
    elif my_no_water_days > 0: # Missed water yesterday
        bid = max(bid, DAILY_SALARY * 0.8) # 120 - ensure it's high enough

    # Adjust based on supply scarcity
    if current_supply < 18: # Scarce supply (15-17)
        bid = max(bid, DAILY_SALARY * 0.8) # 120
    elif current_supply > 22 and num_alive_opponents > 1: # Abundant supply (23-25)
        # If we are healthy and supply is high, try to save money if possible
        if my_hp > 5 and bid > DAILY_SALARY * 0.6:
            bid = DAILY_SALARY * 0.6 # 90

    # End game strategy: If budget is high and days are few, can bid more aggressively
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_budget > DAILY_SALARY * 2: # Last 2 days, good budget
        bid = max(bid, DAILY_SALARY * 0.9) # 135

    # Ensure bid does not exceed my budget
    final_bid = min(my_budget, bid)

    # Ensure bid is not negative or zero if I have budget to make a token bid
    if final_bid <= 0 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)
    elif final_bid < 0: # Should not happen, but for safety
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    LOW_HP_THRESHOLD = 3

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_supply = day_context['supply']
    num_units_available = int(current_supply // WATER_REQ)

    num_players_needing_water = num_alive_opponents + 1

    is_supply_scarce = num_units_available < num_players_needing_water
    is_supply_very_scarce = num_units_available <= num_alive_opponents

    bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= LOW_HP_THRESHOLD:
        bid = DAILY_SALARY * 0.95
        return min(my_status['budget'], bid)

    if my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.8
        return min(my_status['budget'], bid)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if is_supply_very_scarce:
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                bid = highest_prev_bid + 1.0
            else:
                bid = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.7)
        elif is_supply_scarce:
            if highest_prev_bid >= DAILY_SALARY * 0.6:
                if my_status['hp'] > LOW_HP_THRESHOLD + 1:
                    bid = DAILY_SALARY * 0.5
                else:
                    bid = highest_prev_bid + 1.0
            else:
                bid = max(avg_prev_bid + 1.0, DAILY_SALARY * 0.55)
        else:
            lowest_prev_bid = min(yesterday_bids)
            if lowest_prev_bid < DAILY_SALARY * 0.3:
                bid = DAILY_SALARY * 0.25
            else:
                bid = DAILY_SALARY * 0.35
    else:
        if is_supply_very_scarce:
            bid = DAILY_SALARY * 0.7
        elif is_supply_scarce:
            bid = DAILY_SALARY * 0.55
        else:
            bid = DAILY_SALARY * 0.3

    final_bid = min(my_status['budget'], bid)
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.05)
    elif final_bid <= 0:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to secure water.
    # The bid is a total bid for WATER_REQ units.
    if not alive_opponents:
        # Bid 1 unit per water requirement, total 13 units.
        return min(my_status['budget'], WATER_REQ * 1.0)

    # Collect yesterday's bids from alive opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high (e.g., > 85% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Healthy HP, can afford to save a bit
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            # Critical HP, must get water, bid aggressively
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        # Moderate bids from opponents, bid slightly above to win
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # Default bid if no previous bids (e.g., Day 1 or all opponents are new/dead)
    if my_status['hp'] <= 2: # Critical HP, bid high
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    # Healthy HP, bid moderately
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimum to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    # Calculate how many water requirements can be met from current supply
    # CRITICAL RULE 9: int() wrap for indices/division results
    available_water_slots = int(day_context['supply'] // WATER_REQ)
    
    # Base bid
    bid = DAILY_SALARY * 0.5
    
    # Adjust based on my health
    if my_status['hp'] <= 2: # Critical health
        bid = DAILY_SALARY * 0.95 # Bid very high
    elif my_status['hp'] <= 5: # Low health
        bid = DAILY_SALARY * 0.8
    
    # Adjust based on opponent pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid high yesterday, react
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High pressure
            if my_status['hp'] > 5: # Healthy enough to be somewhat conservative
                bid = max(bid, highest_prev_bid * 0.85) # Try to get it cheaper
            else: # Need water, match or slightly exceed
                bid = max(bid, highest_prev_bid + 5) # Bid slightly above
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Medium pressure
            bid = max(bid, highest_prev_bid + 1) # Slightly higher than yesterday's highest
        else: # Low pressure, try to save money
            bid = min(bid, DAILY_SALARY * 0.4) # Try to bid lower, but not too low if I need water
            
    # Adjust based on supply scarcity vs number of alive opponents
    num_opponents = len(alive_opponents)
    if available_water_slots <= 1 and num_opponents >= 1: # Very tight supply, only 1-2 slots for multiple people
        bid = max(bid, DAILY_SALARY * 0.9) # Be aggressive
    elif available_water_slots > num_opponents + 1: # Abundant supply
        bid = min(bid, DAILY_SALARY * 0.3) # Be less aggressive
        
    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure a positive bid if budget allows
    if final_bid <= 0 and my_status['budget'] > 0:
        return min(my_status['budget'], 1.0) # Bid a minimum positive amount if budget is there
    elif final_bid <= 0: # If budget is 0 or less, can't bid
        return 0.0
        
    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_competitors = len(alive_opponents)

    # --- Base Bid Strategy ---
    # Default bid: aim for a moderate amount
    bid_amount = DAILY_SALARY * 0.45

    # Aggressive bidding if HP is low
    if my_hp <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        bid_amount = DAILY_SALARY * 0.75

    # Become more aggressive as the episode nears its end
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.65)

    # --- Opponent-aware adjustment using previous_trace ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_opp_bid_yesterday = max(yesterday_bids)
        # If max opponent bid was high, ensure we can compete
        if max_opp_bid_yesterday >= DAILY_SALARY * 0.7: # High pressure from opponents
            bid_amount = max(bid_amount, max_opp_bid_yesterday + 5)
        elif max_opp_bid_yesterday < DAILY_SALARY * 0.3: # Opponents bidding low
            bid_amount = min(bid_amount, DAILY_SALARY * 0.4)
        else: # Moderate opponent bids
            bid_amount = max(bid_amount, max_opp_bid_yesterday * 1.05)

    # Adjust based on supply vs. number of competitors
    num_slots = int(supply // WATER_REQ)
    if num_slots <= num_alive_competitors: # Supply is tight or equal to competitors
        bid_amount *= 1.1
    elif num_slots > num_alive_competitors + 1: # Supply is abundant
        bid_amount *= 0.9

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, bid_amount)

    # Ensure a minimum bid if I need water and have budget
    if my_hp > 0 and final_bid <= 0 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.05)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    yesterday_bids = []
    david_prev_bid = 0.0 # Initialize to a float

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        if opp['agent_id'] == 'David' and prev and prev.get('bid') is not None:
            david_prev_bid = prev['bid']

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    my_bid = 0.0

    # Critical HP or consecutive no water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Aggressive bid, scales up towards end of episode
        # Ensure day_context['day'] is treated as float for division
        my_bid = MY_DAILY_SALARY * (0.9 + (float(day_context['day']) / EPISODE_DAYS) * 0.05)
    else:
        # Non-critical HP
        base_bid = MY_DAILY_SALARY * 0.6 # Base bid of 90

        # If David's previous bid is high, react to it
        if david_prev_bid > base_bid:
            my_bid = david_prev_bid + 1.5 # Slightly outbid David
        else:
            my_bid = base_bid

        # Also consider other high bids, but David is the primary threat
        if highest_prev_bid > my_bid:
            my_bid = highest_prev_bid + 1.5

        # Scale bid slightly higher towards the end of the episode to secure wins
        my_bid = my_bid * (1 + (float(day_context['day']) / EPISODE_DAYS) * 0.02)

        # Ensure a minimum bid even if opponents bid very low or not at all
        my_bid = max(my_bid, MY_DAILY_SALARY * 0.5)

    # Ensure bid does not exceed budget
    my_bid = min(my_status['budget'], my_bid)

    # Ensure bid is non-negative
    my_bid = max(0.0, my_bid)

    return my_bid
"""
