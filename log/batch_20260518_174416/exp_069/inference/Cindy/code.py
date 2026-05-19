# ============================================================
# Experiment: exp_069
# Agent: Cindy
# Source: exp_069
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    bid = DAILY_SALARY * 0.5

    # --- Adjust bid based on my HP ---
    if my_current_hp <= 1:
        bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 3:
        bid = DAILY_SALARY * 0.75
    elif my_current_hp >= 8:
        bid = DAILY_SALARY * 0.4

    # --- Adjust bid based on supply vs demand ---
    total_water_demand_potential = WATER_REQ
    for opp in alive_opponents:
        total_water_demand_potential += opp['water_requirement']

    if current_supply >= total_water_demand_potential * 1.5:
        bid = min(bid, DAILY_SALARY * 0.3)
    elif current_supply < WATER_REQ + (num_alive_opponents * 5):
        bid = max(bid, DAILY_SALARY * 0.8)
    elif current_supply < WATER_REQ + (num_alive_opponents * 10):
        bid = max(bid, DAILY_SALARY * 0.6)

    # --- Adjust bid based on opponent's previous bids (if available) ---
    highest_prev_opp_bid = 0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_opp_bid = max(highest_prev_opp_bid, prev_trace['bid'])

    if highest_prev_opp_bid > 0:
        if highest_prev_opp_bid >= DAILY_SALARY * 0.7:
            bid = max(bid, highest_prev_opp_bid + (DAILY_SALARY * 0.1))
        elif highest_prev_opp_bid >= DAILY_SALARY * 0.4:
            bid = max(bid, highest_prev_opp_bid + 1)

    # --- Adjust bid based on day progression ---
    if current_day >= EPISODE_DAYS * 0.7 and my_current_hp <= 5:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif current_day >= EPISODE_DAYS * 0.8 and my_current_hp <= 8:
        bid = max(bid, DAILY_SALARY * 0.8)
    elif current_day >= EPISODE_DAYS * 0.9:
        bid = max(bid, DAILY_SALARY * 0.99)

    # Final check: ensure bid is within budget and non-negative
    bid = min(bid, my_current_budget)
    bid = max(0.0, bid)

    return bid
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    base_bid = DAILY_SALARY * 0.55
    bid = base_bid

    if my_hp <= 2 or my_no_water_days >= 1:
        # Critical survival mode: Bid very aggressively
        bid = DAILY_SALARY * 0.95
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = max(bid, highest_prev_bid + 5.0)
    elif my_hp <= 4:
        # Moderate survival mode: Bid aggressively
        bid = DAILY_SALARY * 0.85
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            bid = max(bid, highest_prev_bid + 3.0)
    else:
        # Healthy HP: Be strategic, balance winning with saving budget
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = max(base_bid, highest_prev_bid + 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(base_bid, highest_prev_bid + 1.0)
        else:
            bid = base_bid

    bid = min(my_budget, bid)

    if bid <= 0 and my_hp > 0 and my_budget > 0:
        bid = min(my_budget, DAILY_SALARY * 0.05)

    return round(bid, 2)
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

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], 1.0) # Bid 1 to ensure I get it, but save budget

    # --- Aggressive Bidding for Survival ---
    # If HP is very low or I've missed water recently
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid very high to survive

    # --- Analyze Opponent Bids from Yesterday ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            # Only consider successful or significant bids from alive opponents
            if opp['alive'] and prev['bid'] > 0:
                yesterday_bids.append(prev['bid'])

    # --- Base Bid Calculation ---
    base_bid = DAILY_SALARY * 0.7 # A moderately aggressive bid for my water requirement

    # Adjust base bid based on supply relative to total demand
    total_water_demand = WATER_REQ # My requirement
    for opp in alive_opponents:
        if opp['alive'] and opp['water_requirement'] > 0:
            total_water_demand += opp['water_requirement']

    # Avoid division by zero if somehow total_water_demand becomes 0 (unlikely with WATER_REQ=13)
    if total_water_demand > 0:
        supply_per_unit_of_demand = day_context['supply'] / total_water_demand
        if supply_per_unit_of_demand > 1.5: # Plentiful supply
            base_bid *= 0.7
        elif supply_per_unit_of_demand < 0.8: # Scarce supply
            base_bid *= 1.15

    # --- Adjust bid based on yesterday's highest opponent bid ---
    bid = base_bid # Start with the calculated base bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest bid was very high, we might need to match or slightly exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High competition
            # If my budget is good, I can afford to compete more aggressively
            if my_status['budget'] > DAILY_SALARY * 1.5: 
                 bid = max(bid, highest_prev_bid + 5.0) # Try to outbid
            else: # Budget is getting tighter, be careful but still compete
                 bid = max(bid, highest_prev_bid + 1.0)
        elif highest_prev_bid < DAILY_SALARY * 0.5: # Low competition
            bid = min(bid, highest_prev_bid + 5.0) # Bid slightly above but conserve
        else: # Moderate competition
            bid = max(bid, highest_prev_bid + 1.0) # Slightly above previous high

    # --- Adjust bid based on remaining days (game stage) ---
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # End game, be more aggressive
        bid = max(bid, DAILY_SALARY * 0.85) # Ensure survival
    elif day_context['day'] <= 2: # Early game, conserve unless necessary
        bid = min(bid, DAILY_SALARY * 0.6) # Don't overspend early

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is at least 1.0 if I still need to survive (HP not maxed)
    if my_status['hp'] < EPISODE_DAYS and final_bid < 1.0:
        final_bid = min(my_status['budget'], 1.0)

    return max(0.0, round(final_bid, 2)) # Bid cannot be negative, round to 2 decimal places
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid, adjusted dynamically
    bid = DAILY_SALARY * 0.6  # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # React to high bids from yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents are bidding very high (e.g., >= 127.5)
            if my_status['hp'] <= 3: # Desperate for water
                bid = DAILY_SALARY * 0.95 # Bid very high (142.5)
            else: # Not desperate, but competition is fierce
                bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 2) # Bid above average, or slightly above previous high
        else: # Previous bids were moderate
            if my_status['hp'] <= 2: # Very low HP, need water urgently
                bid = DAILY_SALARY * 0.9 # High bid (135)
            elif my_status['hp'] <= 4: # Low HP
                bid = max(DAILY_SALARY * 0.65, avg_prev_bid + 5) # Moderate to high bid (97.5 or avg+5)
            else: # Healthy HP
                bid = max(DAILY_SALARY * 0.55, avg_prev_bid + 1) # Lower bid (82.5 or avg+1)
    else: # No previous bids from alive opponents (e.g., first day or all opponents are new/reset)
        if my_status['hp'] <= 2:
            bid = DAILY_SALARY * 0.9
        else:
            bid = DAILY_SALARY * 0.6

    # Further adjustment based on current supply
    # If supply is very low, competition is high
    if day_context['supply'] <= WATER_REQ + 2: # e.g., supply 15-17, only one or barely two can get full water
        bid = max(bid, DAILY_SALARY * 0.8) # Ensure bid is at least 120
    # If supply is very high, less competition, can try to conserve budget
    elif day_context['supply'] >= MAX_SUPPLY - 2: # e.g., supply 23-25
        bid = min(bid, DAILY_SALARY * 0.7) # Cap bid at 105 if current bid is higher

    # Ensure bid does not exceed available budget and is at least a small positive amount
    final_bid = min(my_status['budget'], bid)
    final_bid = max(0.1, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    strong_competitors = ["David", "Eric"]
    
    yesterday_bids = []
    for opp in alive_opponents:
        if opp['agent_id'] in strong_competitors:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    current_supply = day_context['supply']
    current_day = day_context['day']

    base_bid = DAILY_SALARY * 0.85

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            base_bid = max(base_bid, highest_prev_bid + 3.0)
        else:
            base_bid = max(base_bid, highest_prev_bid + 1.0)
    
    if my_status['hp'] <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 1.1)
    elif my_status['hp'] <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 1.0)
    
    if current_supply < WATER_REQ * 1.5:
        base_bid *= 1.05
    elif current_supply >= WATER_REQ * 2:
        base_bid *= 0.95

    if current_day > EPISODE_DAYS / 2:
        base_bid *= 1.03

    final_bid = min(my_status['budget'], max(0.0, base_bid))
    
    if my_status['budget'] < DAILY_SALARY * 0.5 and my_status['hp'] <= 3:
        final_bid = my_status['budget']
    
    if final_bid < 1.0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0)
        
    return float(final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect previous bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid strategy
    current_bid = DAILY_SALARY * 0.5 # A moderate starting point

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding high, increase my bid slightly above it
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            current_bid = max(current_bid, highest_prev_bid + 5)
        else:
            current_bid = max(current_bid, highest_prev_bid + 1)
    
    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP, bid aggressively
        current_bid = max(current_bid, DAILY_SALARY * 0.8)
    
    # Adjust bid based on remaining days and budget (end game)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: 
        if my_status['hp'] > 5 and my_status['budget'] > DAILY_SALARY * 2: # If doing well
            current_bid = max(current_bid, DAILY_SALARY * 0.75)
        elif my_status['hp'] <= 5: # Need to survive
            current_bid = max(current_bid, DAILY_SALARY * 0.9)

    # Ensure bid does not exceed available budget
    # And ensure bid is at least a minimal amount to be competitive
    final_bid = min(my_status['budget'], current_bid)
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Ensure a minimum bid to at least try to get water

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    my_current_hp = my_status['hp']
    current_day = day_context['day']

    # Emergency bid if HP is very low
    if my_current_hp <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid very high to survive

    # If previous competition was high (e.g., highest bid was 85% of salary or more)
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_current_hp > 4: # If my HP is relatively good, be a bit conservative
            return min(my_status['budget'], DAILY_SALARY * 0.6) # Moderate bid
        else: # HP is somewhat low, need to compete strongly
            return min(my_status['budget'], DAILY_SALARY * 0.9) # High bid
    elif highest_prev_bid > 0: # If there was competition, but not extremely high
        # Bid slightly above the highest previous bid, with a floor
        bid = max(DAILY_SALARY * 0.6, highest_prev_bid + (DAILY_SALARY * 0.02)) # Floor 90, add 3
        return min(my_status['budget'], bid)
    else: # No significant previous bids (or no bids at all from active opponents)
        # Default bid, potentially adjusted by day (more aggressive later in the game)
        if current_day >= EPISODE_DAYS - 2: # Last 2 days
            return min(my_status['budget'], DAILY_SALARY * 0.8) # Higher bid towards end
        else:
            return min(my_status['budget'], DAILY_SALARY * 0.65) # Moderate bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy based on urgency and supply
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        # Very critical, bid aggressively to survive
        current_bid = DAILY_SALARY * 0.95
    else:
        # Not critical, adjust bid based on supply scarcity
        if day_context['supply'] < WATER_REQ * 1.5: # Supply is tight (e.g., 15-19 for WATER_REQ=13)
            current_bid = DAILY_SALARY * 0.8 # Aggressive base bid (120)
        else: # Supply is moderately available (e.g., 20-25 for WATER_REQ=13)
            current_bid = DAILY_SALARY * 0.7 # Moderate base bid (105)

    # Further adjust bid based on opponent's previous bids to stay competitive
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents were bidding very high
            current_bid = max(current_bid, highest_prev_bid + 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents were bidding moderately high
            current_bid = max(current_bid, highest_prev_bid + 1.0)
        else: # Opponents bid low, try to win cheaply but surely
            current_bid = max(current_bid, highest_prev_bid + 0.5)

    # Ensure bid doesn't exceed current budget
    return min(my_status['budget'], current_bid)
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
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    bid_factor = 0.7

    if my_hp <= 2:
        bid_factor = 1.0
    elif my_hp <= 4:
        bid_factor = 0.9
    elif my_hp >= 8 and my_budget > DAILY_SALARY * 2:
        bid_factor = 0.6

    if my_no_water_days > 0:
        bid_factor += my_no_water_days * 0.1

    supply_scarcity_ratio = 1 - ((current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    bid_factor += supply_scarcity_ratio * 0.15

    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opponent_bids.append(prev_trace['bid'])

    if yesterday_opponent_bids:
        max_opp_bid_yesterday = max(yesterday_opponent_bids)
        avg_opp_bid_yesterday = sum(yesterday_opponent_bids) / len(yesterday_opponent_bids)

        if max_opp_bid_yesterday > DAILY_SALARY * 0.9:
            bid_factor = max(bid_factor, 1.0)
        elif (DAILY_SALARY * bid_factor) < avg_opp_bid_yesterday * 1.05:
            bid_factor = max(bid_factor, (avg_opp_bid_yesterday * 1.05) / DAILY_SALARY)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp <= 3:
            bid_factor = max(bid_factor, 1.1)
        elif my_hp > 3 and my_budget > DAILY_SALARY:
            bid_factor = max(bid_factor, 0.85)

    calculated_bid = DAILY_SALARY * bid_factor

    final_bid = min(my_budget, calculated_bid)
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

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a very low amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on supply and number of opponents
    num_competitors = len(alive_opponents) + 1 # Me + opponents
    
    # Estimate how many water requirements the supply can cover
    # Use int() for supply division result as a general safety measure due to float input
    potential_winners = int(current_supply // WATER_REQ)

    if potential_winners == 0: # Supply less than my requirement, highly competitive
        base_bid = DAILY_SALARY * 0.8
    elif potential_winners <= num_competitors: # Supply is tight, fewer winners than competitors
        base_bid = DAILY_SALARY * 0.6
    else: # Supply is more abundant
        base_bid = DAILY_SALARY * 0.4

    # Adjust bid based on my HP
    bid_value = base_bid
    if my_status['hp'] <= 2: # Critical health, bid very aggressively
        bid_value = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low health, bid aggressively
        bid_value = max(bid_value, DAILY_SALARY * 0.75)

    # Adjust based on opponent's yesterday bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, react strongly
        if highest_prev_bid >= DAILY_SALARY * 0.8: # e.g., 120
            if my_status['hp'] > 4: # Healthy, can be slightly less aggressive
                bid_value = max(bid_value, highest_prev_bid * 1.05)
            else: # Not healthy, must get water
                bid_value = max(bid_value, highest_prev_bid * 1.1)
        # If highest previous bid was moderate, match or slightly exceed
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # e.g., 75
             bid_value = max(bid_value, highest_prev_bid + 5)
        # If highest previous bid was low, keep my calculated bid or slightly above it
        else:
             bid_value = max(bid_value, highest_prev_bid + 1)

    # Final days pressure:
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        bid_value = max(bid_value, DAILY_SALARY * 0.9)
    elif remaining_days <= 4: # Last 4 days
        bid_value = max(bid_value, DAILY_SALARY * 0.7)

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], bid_value)
    
    # Ensure a minimum bid to participate meaningfully
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Minimum bid of 15

    return final_bid
"""
