# ============================================================
# Experiment: exp_092
# Agent: Cindy
# Source: exp_092
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    my_water_requirement = WATER_REQ
    my_daily_salary = DAILY_SALARY

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    current_supply = day_context['supply']

    # --- Phase 1: Critical HP Bidding ---
    if my_status['hp'] <= 2:
        # Desperate for water, bid very high to survive
        return min(my_status['budget'], my_daily_salary * 0.95)
    elif my_status['hp'] <= 4:
        # Low HP, bid high to avoid critical state
        return min(my_status['budget'], my_daily_salary * 0.8)

    # --- Phase 2: Normal HP Bidding based on competition and supply ---
    base_bid = my_daily_salary * 0.5 # A balanced starting point for normal HP

    if num_alive_opponents == 0:
        # No opponents, bid minimum to secure water and conserve budget
        return min(my_status['budget'], my_daily_salary * 0.1)

    # Estimate total water needed by active players (including self)
    # Assuming opponents have similar water requirements for estimation
    total_estimated_water_needed = my_water_requirement * (num_alive_opponents + 1)

    # Adjust bid based on supply scarcity
    if current_supply < total_estimated_water_needed:
        # Supply is scarce relative to estimated demand, increase bid to be competitive
        # Cap the scarcity factor to prevent excessively high bids
        scarcity_factor = total_estimated_water_needed / current_supply
        base_bid *= min(1.5, scarcity_factor) 
    else:
        # Supply is ample, can potentially reduce bid to conserve budget
        # Still maintain a competitive bid to win against opponents
        base_bid *= 0.8 

    # Ensure bid is within budget and is at least a minimum value
    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(1.0, final_bid) # Ensure bid is at least 1.0

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to ensure survival without overspending.
    if not alive_opponents:
        remaining_days = EPISODE_DAYS - day_context['day'] + 1
        # If budget is plentiful, bid very low. Otherwise, bid a bit more to be safe.
        if my_status['budget'] / remaining_days > DAILY_SALARY * 0.8: 
            return min(my_status['budget'], DAILY_SALARY * 0.1)
        else: 
            return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.6 

    # Adjust bid based on my HP (urgency)
    if my_status['hp'] <= 3: 
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5: 
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: 
        base_bid = DAILY_SALARY * 0.55

    # Adjust bid based on current supply (competition level)
    supply_ratio = (day_context['supply'] - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_multiplier = 1.15 - (supply_ratio * 0.3) 
    base_bid *= supply_multiplier

    # Adjust bid based on opponent's highest bid from yesterday
    if max_yesterday_bid > 0:
        if max_yesterday_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_yesterday_bid + 5)
        else:
            base_bid = max(base_bid, max_yesterday_bid + 1)
    
    # Ensure bid is within my budget and above a minimal competitive value
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure a minimum bid to stay in the game
    final_bid = max(final_bid, DAILY_SALARY * 0.1) 

    # If it's late in the game and I have a good budget, be more aggressive
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['budget'] > DAILY_SALARY * 2:
        final_bid = min(my_status['budget'], max(final_bid, DAILY_SALARY * 1.1))

    # Ensure the bid is not negative
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
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest bid was very high, react based on my HP
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
            if my_status['hp'] > 3: # My HP is relatively good (4 or 5)
                return min(my_status['budget'], DAILY_SALARY * 0.4) # Conserve: 60
            # My HP is low (1, 2, or 3), bid aggressively
            return min(my_status['budget'], DAILY_SALARY * 0.95) # Aggressive: 142.5
        
        # If highest bid was moderate, try to slightly outbid or maintain a good bid
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)) # Max of 75 or slightly above opponent

    # If no previous bids (e.g., Day 1) or no relevant bids, rely on my HP
    if my_status['hp'] <= 2: # Critical HP (1 or 2)
        return min(my_status['budget'], DAILY_SALARY * 0.9) # Aggressive: 135
    
    # If HP is good and no strong signals from yesterday, bid moderately
    return min(my_status['budget'], DAILY_SALARY * 0.65) # Moderate: 97.5
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    bid_amount = DAILY_SALARY * 0.5 # Default moderate bid

    yesterday_bids = []
    strong_opponent_bids = [] # From David and Eric based on meta-round context
    weak_opponent_bids = [] # From Alex and Bob based on meta-round context

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bid_value = prev['bid']
            yesterday_bids.append(bid_value)
            if opp['agent_id'] in ["David", "Eric"]:
                strong_opponent_bids.append(bid_value)
            elif opp['agent_id'] in ["Alex", "Bob"]:
                weak_opponent_bids.append(bid_value)

    # --- Bidding Logic based on HP and Opponent Strength ---

    if my_current_hp <= 2: # Critical HP, bid aggressively for survival
        bid_amount = DAILY_SALARY * 1.0
    elif my_current_hp <= 5: # Low HP, high priority for water
        bid_amount = DAILY_SALARY * 0.85
    elif num_alive_opponents == 0: # No opponents, save budget
        bid_amount = DAILY_SALARY * 0.1
    else: # Healthy HP and active opponents
        if strong_opponent_bids:
            highest_strong_bid = max(strong_opponent_bids)
            # Bid slightly above strong opponents, but not excessively to conserve budget
            bid_amount = max(bid_amount, highest_strong_bid + (DAILY_SALARY * 0.05))
            # Ensure it's at least a reasonable amount for competition
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6)
        elif weak_opponent_bids: # Only weak opponents remain or only weak ones bid yesterday
            highest_weak_bid = max(weak_opponent_bids)
            bid_amount = max(bid_amount, highest_weak_bid + 1) # Just enough to beat them
            bid_amount = min(bid_amount, DAILY_SALARY * 0.4) # Don't overspend on weak opponents
        elif yesterday_bids: # Some general bids but no strong/weak classification, or mix
            highest_general_bid = max(yesterday_bids)
            bid_amount = max(bid_amount, highest_general_bid + 1)
            bid_amount = max(bid_amount, DAILY_SALARY * 0.5) # Maintain moderate bid
        else: # No previous bids from any opponent, bid moderately
            bid_amount = DAILY_SALARY * 0.5

    # End game considerations: Last 2 days, ensure survival
    remaining_days = EPISODE_DAYS - current_day + 1
    if remaining_days <= 2 and my_current_hp > 0:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75) # Strong bid to finish the game

    # --- Final Bid Adjustment ---
    final_bid = min(my_current_budget, bid_amount)

    # Ensure a non-zero bid if budget allows, to actually participate
    if my_current_budget > 0 and final_bid < 1.0:
        # If budget is positive but calculated bid is tiny, bid a minimum amount or all budget
        final_bid = min(my_current_budget, DAILY_SALARY * 0.1) # Bid at least 10% of salary
        if final_bid < 1.0 and my_current_budget >= 1.0: # If 10% of salary is less than 1, but I have budget for 1
            final_bid = 1.0
        elif final_bid < 1.0 and my_current_budget < 1.0: # If budget itself is less than 1
            final_bid = my_current_budget # Bid all remaining budget
    elif my_current_budget <= 0:
        final_bid = 0.0

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid conservatively to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: aim to be competitive with top players (Alex, Eric)
    # Their average bids were around 66. My salary is 150.
    # 66 / 150 = 0.44. Let's start with a slightly higher base multiplier.
    base_bid = DAILY_SALARY * 0.48 # 150 * 0.48 = 72.0 (close to their max bids)

    # Adjust bid based on supply: bid higher when supply is low
    supply_range = MAX_SUPPLY - MIN_SUPPLY
    if supply_range > 0:
        # supply_pressure_factor is 1 when supply is MIN_SUPPLY, 0 when supply is MAX_SUPPLY
        supply_pressure_factor = (MAX_SUPPLY - day_context['supply']) / supply_range
        # Increase base bid by up to 15% when supply is at minimum
        base_bid *= (1 + supply_pressure_factor * 0.15)
    
    current_bid = base_bid

    # Adjust bid based on opponent's previous highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If the highest previous bid was very high (e.g., > 60% of daily salary),
        # we must compete aggressively.
        if highest_prev_bid >= DAILY_SALARY * 0.6: # 150 * 0.6 = 90.0
            current_bid = max(current_bid, highest_prev_bid + 1.5) # Try to outbid by a small margin
        else:
            # If previous bids were moderate, ensure we are competitive but not overspending
            current_bid = max(current_bid, highest_prev_bid + 0.5)

    # Emergency logic: If HP is low or no water days, bid aggressively
    # This overrides other calculations to prioritize survival.
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        current_bid = DAILY_SALARY * 0.95 # Bid very high to survive
    
    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], current_bid)
    
    # Ensure bid is at least 1 to participate
    return max(1.0, final_bid)
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
        # If no opponents are alive, bid low to save budget
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                # If healthy, conserve budget
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            # If HP is low, bid aggressively to survive
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # Otherwise, bid slightly above the highest previous bid to be competitive
        # Ensure bid is at least a moderate level
        return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # If no yesterday_bids (e.g., Day 1 or all previous bids were None/error)
    if my_status['hp'] <= 2:
        # Aggressive bid for survival if HP is critically low
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    
    # Moderate default bid
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
    
    # If no opponents are alive, bid minimum to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)
    
    # Calculate a base bid based on my HP
    bid = 0.0
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3: # Low HP
        bid = DAILY_SALARY * 0.85
    elif my_status['hp'] == 4: # Moderate HP
        bid = DAILY_SALARY * 0.75
    else: # Healthy HP
        bid = DAILY_SALARY * 0.6
        
    # Incorporate opponent's previous bids, prioritizing the highest
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
            
    # If there was a significant highest previous bid, adjust my bid to compete
    if highest_prev_bid > 0:
        if my_status['hp'] <= 2:
            # Desperate, try to outbid the highest previous bid significantly
            bid = max(bid, highest_prev_bid + 15.0) # Add a larger margin
        elif my_status['hp'] <= 4:
            # Need water, try to outbid
            bid = max(bid, highest_prev_bid + 8.0) # Add a moderate margin
        else:
            # Healthy, but still want to win if possible without overspending
            bid = max(bid, highest_prev_bid + 2.0) # Just slightly above
            
    # Ensure bid is at least a minimal amount if I need water, regardless of opponent's previous low bids
    min_bid_if_needed = DAILY_SALARY * 0.3
    if my_status['hp'] <= 4: # If I need water (low to moderate HP)
        bid = max(bid, min_bid_if_needed)
    
    # Final bid cannot exceed my current budget
    final_bid = min(my_status['budget'], bid)
    
    # Edge case: if budget is very low but I desperately need water, bid everything available
    if my_status['hp'] <= 1 and my_status['budget'] > 0:
        final_bid = my_status['budget']
        
    return final_bid
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
        return min(my_status['budget'], DAILY_SALARY * 0.05)
        
    base_bid = DAILY_SALARY * 0.4
    
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.7
        
    highest_prev_opp_bid = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_opp_bid = max(highest_prev_opp_bid, prev['bid'])
            
    current_supply = day_context['supply']
    
    # In this scenario, supply (15-25) is always less than 2 * WATER_REQ (26),
    # meaning supply is always tight for two full requirements.
    if highest_prev_opp_bid > 0:
        base_bid = max(base_bid, highest_prev_opp_bid + 10)
    else:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    final_bid = min(my_status['budget'], base_bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Calculate how many full water requirements can be met by the supply
    num_water_slots = int(supply // WATER_REQ)

    # If no opponents, bid minimum to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.05)

    # Determine base bid based on my HP
    if my_hp <= 2: # Critical HP, need water desperately
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, need water soon
        bid = DAILY_SALARY * 0.75
    else: # Healthy HP
        bid = DAILY_SALARY * 0.5

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If supply is tight (1 or 2 slots) and opponents bid high, react strongly
        if num_water_slots <= 2 and highest_prev_bid >= DAILY_SALARY * 0.5:
            # If my current bid is lower than their highest, try to outbid
            if bid < highest_prev_bid + 5:
                bid = highest_prev_bid + 5
            # If my HP is critical, ensure I'm very aggressive
            if my_hp <= 2:
                bid = max(bid, highest_prev_bid * 1.1)
        
        # If supply is ample (more slots than alive opponents + me), try to reduce bid if possible
        elif num_water_slots > (num_alive_opponents + 1) and my_hp > 4:
            bid = min(bid, DAILY_SALARY * 0.3) # Try to save budget
            
    # Ensure bid does not exceed budget
    final_bid = min(bid, my_budget)

    # Ensure bid is always positive
    final_bid = max(0.01, final_bid)

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

    # If no opponents, bid minimal amount to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid - a reasonable amount to secure water under normal conditions
    base_bid = DAILY_SALARY * 0.5
    current_bid = base_bid

    # 1. Desperation check (low HP or no water yesterday)
    if my_status['no_water_days'] >= 1:
        current_bid = DAILY_SALARY * 0.8 
    elif my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95
    
    # 2. Adjust based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    if highest_prev_bid > DAILY_SALARY * 0.7: # Opponents were very aggressive
        current_bid = max(current_bid, highest_prev_bid * 1.05)
    elif highest_prev_bid > DAILY_SALARY * 0.5: # Opponents were moderately aggressive
        current_bid = max(current_bid, highest_prev_bid * 1.02)
    else: # Opponents were conservative or no strong bids
        current_bid = max(current_bid, DAILY_SALARY * 0.45) # Ensure a minimum competitive bid

    # 3. Adjust based on supply and number of competitors
    total_players = num_alive_opponents + 1
    supply_per_player = day_context['supply'] / total_players

    if supply_per_player < WATER_REQ * 1.2: # Supply is tight
        current_bid *= 1.15 
    elif supply_per_player > WATER_REQ * 1.8: # Supply is abundant
        current_bid *= 0.9 
    
    # 4. Adjust based on day number
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last few days, push harder
        current_bid *= 1.1
        current_bid = max(current_bid, DAILY_SALARY * 0.7) 
    elif day_context['day'] <= 2: # Early days, can be slightly more conservative if healthy
        if my_status['hp'] > 5 and my_status['no_water_days'] == 0:
            current_bid *= 0.95

    # 5. Final constraints
    min_competitive_bid = DAILY_SALARY * 0.35 
    current_bid = max(current_bid, min_competitive_bid)
    current_bid = min(current_bid, DAILY_SALARY)
    current_bid = min(current_bid, my_status['budget'])

    return current_bid
"""
