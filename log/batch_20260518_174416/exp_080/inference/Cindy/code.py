# ============================================================
# Experiment: exp_080
# Agent: Cindy
# Source: exp_080
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    # Agent Constants (defined locally for self-containment)
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], 1.0) # Bid 1.0, very low but ensures water

    # Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Bidding Strategy ---
    current_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # 1. Survival Bidding (Highest Priority)
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
        current_bid = DAILY_SALARY * 0.95 # Bid very high to survive
    elif my_status['hp'] <= 4 or my_status['no_water_days'] == 1:
        current_bid = DAILY_SALARY * 0.8 # Bid high to prevent further HP loss

    # 2. Adjust based on Supply Scarcity
    current_supply = day_context['supply']
    # Calculate how many full water requirements can be met by the supply
    available_slots = int(current_supply // WATER_REQ) # CRITICAL: int() for safety

    # If supply is very tight (fewer slots than active players + myself)
    if available_slots <= num_alive_opponents:
        current_bid = max(current_bid, DAILY_SALARY * 0.65) # Increase bid significantly
    elif available_slots > num_alive_opponents + 1: # Supply is abundant (e.g., 3 slots for 1 opponent + me)
        current_bid = min(current_bid, DAILY_SALARY * 0.3) # Decrease bid as supply is abundant

    # 3. Adjust based on Opponent's Previous Bids (if not in critical survival mode)
    # Only adjust based on opponent bids if my HP is not critically low and I didn't miss water yesterday
    if my_status['hp'] > 4 and my_status['no_water_days'] == 0:
        if highest_prev_bid > DAILY_SALARY * 0.6: # Opponents are bidding high
            current_bid = max(current_bid, highest_prev_bid + 1.0) # Try to outbid slightly
        elif highest_prev_bid < DAILY_SALARY * 0.3: # Opponents are bidding low
            current_bid = min(current_bid, DAILY_SALARY * 0.35) # Can afford to bid lower

    # 4. End Game Pressure
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        current_bid = max(current_bid, DAILY_SALARY * 0.7) # Increase bid pressure

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least 1.0 if budget allows and water is needed (and not bidding 0 initially)
    # This handles edge cases where calculated bid is very low but some budget exists, and I need water.
    # Also, if there are no opponents, a minimal bid is sufficient.
    if final_bid < 1.0 and my_status['budget'] >= 1.0 and (my_status['no_water_days'] > 0 or num_alive_opponents == 0):
        final_bid = 1.0
    elif final_bid < 0.1 and my_status['budget'] >= 0.1 and num_alive_opponents == 0: # Even more minimal bid if no opponents and not desperate
        final_bid = 0.1

    return max(0.0, final_bid) # Ensure bid is non-negative
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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    supply_pressure_factor = 1.0
    available_water_units = int(day_context['supply'] // WATER_REQ)
    total_competitors = num_alive_opponents + 1

    if available_water_units < total_competitors:
        supply_pressure_factor = 1.15
    elif available_water_units >= total_competitors * 1.5:
        supply_pressure_factor = 0.9

    bid_amount = 0.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                bid_amount = DAILY_SALARY * 0.3
            else:
                bid_amount = DAILY_SALARY * 0.95
        else:
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    else:
        if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
            bid_amount = DAILY_SALARY * 0.9
        else:
            bid_amount = DAILY_SALARY * 0.55

    bid_amount *= supply_pressure_factor

    if my_status['hp'] <= 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
    elif my_status['no_water_days'] > 0:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    if day_context['day'] >= EPISODE_DAYS - 2:
        if my_status['budget'] > DAILY_SALARY * 1.5:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.99)
        elif my_status['hp'] <= 4:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.95)

    final_bid = min(my_status['budget'], bid_amount)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_competitors = len(alive_opponents) + 1 # Myself + alive opponents

    # If no opponents are alive, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    # Determine how many agents can get their full water requirement
    num_agents_can_get_water = int(current_supply // WATER_REQ)

    # Collect yesterday's bids and identify David's bid specifically
    yesterday_bids = []
    david_is_alive = False
    david_yesterday_bid = 0.0

    for opp in alive_opponents:
        if opp['agent_id'] == "David":
            david_is_alive = True
        
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            if opp['agent_id'] == "David":
                david_yesterday_bid = prev['bid']

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # --- Base Bid Calculation ---
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # --- Adjustments based on My Status (HP and no_water_days) ---
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.8
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        base_bid = max(base_bid, DAILY_SALARY * 0.7) # Increase bid to ensure water

    # --- Adjustments based on Competition and Supply ---
    # High competition: Supply is less than total demand
    if num_agents_can_get_water < num_alive_competitors:
        # If David is alive, assume he will bid high, try to outbid him or match his high bids
        if david_is_alive:
            # If David bid high yesterday, try to slightly outbid him
            if david_yesterday_bid > DAILY_SALARY * 0.7:
                base_bid = max(base_bid, david_yesterday_bid + 5.0)
            else: # If David didn't bid high yesterday, he might be saving, still a threat
                base_bid = max(base_bid, DAILY_SALARY * 0.85) # Assume David will bid aggressively
        else: # No David, but still high competition
            base_bid = max(base_bid, highest_prev_bid + 2.0) # Slightly outbid the highest previous bid

    # Low competition: Supply is sufficient for all or most
    else: # num_agents_can_get_water >= num_alive_competitors
        # If I'm not desperate, try to save money
        if my_status['hp'] > 6 and my_status['no_water_days'] == 0:
            base_bid = min(base_bid, DAILY_SALARY * 0.4) # Bid lower
        
        # Still ensure we win against yesterday's highest low bids
        if highest_prev_bid > 0.0 and base_bid < highest_prev_bid + 1.0:
            base_bid = highest_prev_bid + 1.0 # Just enough to win against low bids

    # --- End of Game Aggression ---
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] < 10 or my_status['no_water_days'] > 0: # Need water to survive or finish strong
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        elif my_status['budget'] > DAILY_SALARY * 2: # Plenty of budget, secure win
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
            
    # Final adjustments
    final_bid = max(1.0, base_bid) # Ensure bid is at least 1.0

    # Never bid more than current budget
    final_bid = min(final_bid, my_status['budget'])

    return final_bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    # Default moderate bid if no strong pressure or initial day
    base_bid = DAILY_SALARY * 0.55 

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, it indicates strong competition
        # If my HP is healthy, try to slightly outbid to win
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 4: # Healthy HP, can afford to counter intelligently
                base_bid = highest_prev_bid + 2.0 # Slightly outbid
            else: # HP is low (<=4), need to win, bid very aggressively
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # Highest previous bid was not extremely high, can be more measured
            base_bid = max(base_bid, highest_prev_bid + 2.0) # Slightly outbid
    
    # If HP is critically low, override any other bidding logic to ensure survival
    if my_status['hp'] <= 2: 
        return min(my_status['budget'], DAILY_SALARY * 0.98) # Extremely aggressive
    elif my_status['hp'] <= 4: 
        return min(my_status['budget'], DAILY_SALARY * 0.90) # Very aggressive
    
    # Further adjust based on supply and number of opponents if HP is healthy
    num_water_slots = int(day_context['supply'] / WATER_REQ)

    if num_water_slots == 0: # No water available, bid minimally to save budget
        return min(my_status['budget'], 1.0) 
    
    if num_water_slots == 1 and len(alive_opponents) >= 2: # High competition for single slot
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Increase aggression
    elif num_water_slots >= 2 and num_water_slots <= len(alive_opponents): # Some competition
        base_bid = max(base_bid, DAILY_SALARY * 0.65) # Moderate aggression
    # Else, if num_water_slots > len(alive_opponents) or only 1 opponent, base_bid remains as calculated or default

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure a minimum bid to participate, if budget allows
    final_bid = max(final_bid, 1.0)
    
    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid very low to save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) 
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    # Determine a base bid
    current_bid = DAILY_SALARY * 0.8 # Base competitive bid
    
    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        current_bid = DAILY_SALARY * 1.1 # Bid very aggressively
    elif my_status['hp'] <= 4: # Low HP
        current_bid = DAILY_SALARY * 0.95 # Bid aggressively
    
    # Adjust bid based on opponent's highest previous bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest bid was very high (e.g., >= 90% of salary), react strongly
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_status['hp'] <= 4: # If low HP, I must win, bid significantly higher
                current_bid = max(current_bid, highest_prev_bid + 10)
            else: # If good HP, still try to win but with a smaller increment
                current_bid = max(current_bid, highest_prev_bid + 5)
        else: # If highest bid was relatively low, ensure we still win but don't overpay
            current_bid = max(current_bid, highest_prev_bid + 2)
            
    # Ensure bid doesn't exceed budget
    return min(my_status['budget'], current_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    current_bid = DAILY_SALARY * 0.65

    # 1. Adjust based on my HP (survival priority)
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        current_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6:
        current_bid = DAILY_SALARY * 0.75

    # 2. Adjust based on supply (resource availability)
    supply = day_context['supply']
    if supply <= WATER_REQ + 2:
        current_bid *= 1.15
    elif supply >= MAX_SUPPLY - 2:
        current_bid *= 0.85

    # 3. React to yesterday's opponent bids (competition pressure)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            current_bid = max(current_bid, max_yesterday_bid + 5)
        elif max_yesterday_bid >= DAILY_SALARY * 0.6:
            current_bid = max(current_bid, max_yesterday_bid + 2)

    # 4. Adjust for game phase (early vs. late game)
    day = day_context['day']
    if day >= EPISODE_DAYS - 2:
        current_bid *= 1.1
    elif day <= 2 and my_status['hp'] > 6:
        current_bid *= 0.9

    final_bid = min(my_status['budget'], current_bid)
    final_bid = max(1.0, final_bid)

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

    # If current supply is less than my requirement, I cannot get water. Bid minimum to save budget.
    if day_context['supply'] < WATER_REQ:
        return min(my_status['budget'], 1)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid very low to save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Calculate days remaining to gauge urgency
    days_remaining = EPISODE_DAYS - day_context['day'] + 1

    bid_amount = 0

    # Prioritize survival if HP is critical, we've missed water recently, or nearing the end of the episode
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1 or days_remaining <= 2:
        # If opponents were bidding high, try to outbid them more aggressively
        if highest_prev_bid > DAILY_SALARY * 0.7:
            bid_amount = highest_prev_bid + (DAILY_SALARY * 0.1) # Add 10% of salary to outbid
        else:
            bid_amount = DAILY_SALARY * 0.95 # Very high bid to secure water
    else:
        # Normal bidding strategy
        if highest_prev_bid > DAILY_SALARY * 0.6: # Opponents are bidding relatively high
            bid_amount = max(DAILY_SALARY * 0.65, highest_prev_bid + (DAILY_SALARY * 0.05)) # Slightly outbid
        elif highest_prev_bid > 0: # Opponents made a bid
            bid_amount = max(DAILY_SALARY * 0.55, highest_prev_bid + (DAILY_SALARY * 0.03)) # Small increase
        else: # No significant previous bids (e.g., first day, or opponents bid very low)
            bid_amount = DAILY_SALARY * 0.5 # Moderate default bid

    # Ensure bid doesn't exceed budget and is at least 1
    final_bid = min(my_status['budget'], max(1, bid_amount))

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

    # If no opponents are alive, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Initialize bid with a default moderate value
    bid_amount = DAILY_SALARY * 0.65 # Base bid: 97.5

    # End-game strategy: If it's the last day, bid everything if I need water
    if day_context['day'] == EPISODE_DAYS:
        if my_status['hp'] > 0: # If I need to survive this last day
            return my_status['budget'] # Bid all remaining budget

    # HP-based strategy (for non-last days or when last-day survival is not the only factor)
    if my_status['hp'] <= 2: # Critical HP, must get water
        bid_amount = DAILY_SALARY * 0.95 # 142.5
    elif my_status['no_water_days'] >= 1: # Missed water yesterday, need it today
        bid_amount = DAILY_SALARY * 0.85 # 127.5
    elif day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days (excluding the very last day handled above), be more aggressive
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # 120.0

    # Adjust bid based on opponent's highest bid from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents are bidding very high (>= 127.5)
            if my_status['hp'] > 3: # My HP is relatively healthy
                bid_amount = max(bid_amount, DAILY_SALARY * 0.75) # 112.5
            else: # My HP is somewhat low, need to be aggressive
                bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # 135.0
        else: # Opponents' highest bid is moderate
            bid_amount = max(bid_amount, highest_prev_bid + 1.5)
            bid_amount = max(bid_amount, DAILY_SALARY * 0.65) # Ensure it's at least a certain level due to scarcity

    # Final bid must not exceed budget and be at least a minimal amount
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(1.0, final_bid) # Ensure bid is at least 1.0

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Base bid calculation - default to a moderate bid
    bid_value = DAILY_SALARY * 0.55 

    # Aggressive bidding if HP is low
    if my_status['hp'] <= 2:
        bid_value = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid_value = DAILY_SALARY * 0.85
    
    # Adjust bid based on supply scarcity
    # If total supply is barely enough or less than my requirement, competition will be high.
    if day_context['supply'] < WATER_REQ * 1.2: 
        bid_value = max(bid_value, DAILY_SALARY * 0.75)
    
    # Consider opponents' previous bids from their 'previous_trace'
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # React to high previous bids from opponents
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 3: # Healthy, can try to conserve if opponents are overbidding
                bid_value = min(bid_value, highest_prev_bid * 0.95) # Bid slightly below if healthy
                bid_value = max(bid_value, DAILY_SALARY * 0.4) # Ensure it's not too low
            else: # Not healthy, must outbid
                bid_value = max(bid_value, highest_prev_bid + 5) # Bid slightly above to secure water
        else:
            # Opponents were not extremely aggressive, try to outbid them slightly to win
            bid_value = max(bid_value, highest_prev_bid + 1.5)
            
    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], bid_value)
    
    # Critical survival check for the very last day
    if day_context['day'] == EPISODE_DAYS - 1 and my_status['hp'] <= 0: 
        final_bid = my_status['budget'] # Bid everything to survive if it's the last day and I'm out of HP
    
    # Ensure bid is never negative
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid very low to save money
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine a base bid, which will be adjusted based on conditions.
    # Given the tight supply (15-25 for 13 units requirement), competition is always high.
    
    # Default bid if no strong pressure or critical HP
    target_bid = DAILY_SALARY * 0.55 # 82.5

    # Adjust target bid based on my HP, prioritizing survival
    if my_hp <= 2: # Critical HP, must win at almost any cost
        target_bid = DAILY_SALARY * 0.98 # 147.0 (very aggressive)
    elif my_hp <= 4: # Low HP, strong need for water
        target_bid = DAILY_SALARY * 0.85 # 127.5
    elif my_hp <= 7: # Moderate HP, still need water but can be slightly less aggressive
        target_bid = DAILY_SALARY * 0.7 # 105.0
    # else: target_bid remains DAILY_SALARY * 0.55 (for high HP)

    # Adjust bid based on opponent's highest previous bid
    if highest_prev_bid > 0:
        # If highest previous bid is very high (e.g., from an aggressive opponent like Alex/Eric)
        if highest_prev_bid >= DAILY_SALARY * 0.85: 
            if my_hp > 5: # If HP is good, try to slightly outbid but don't overspend too much
                target_bid = max(target_bid, highest_prev_bid + 2.0)
            else: # If HP is low, must try to win more aggressively
                target_bid = max(target_bid, highest_prev_bid + 5.0) 
        else: # Opponents are bidding moderately, try to slightly outbid
            target_bid = max(target_bid, highest_prev_bid + 1.5)

    # Final bid should not exceed my budget
    final_bid = min(my_budget, target_bid)

    # Ensure a minimal bid if budget is positive but calculation resulted in 0 or less.
    if final_bid <= 0 and my_budget > 0:
        final_bid = min(my_budget, 1.0) # Bid a minimal amount to stay in the game if possible

    return max(0.0, final_bid) # Bid cannot be negative
"""
