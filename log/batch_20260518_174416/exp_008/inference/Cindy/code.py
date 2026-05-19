# ============================================================
# Experiment: exp_008
# Agent: Cindy
# Source: exp_008
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

    yesterday_bids = []
    yesterday_struggled_count = 0
    total_opponent_water_demand = 0

    for opp in alive_opponents:
        total_opponent_water_demand += opp['water_requirement']
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
            if prev_trace.get('status') == 'no_water':
                yesterday_struggled_count += 1

    total_water_demand_all_agents = WATER_REQ + total_opponent_water_demand

    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.95)

    if num_alive_opponents == 0:
        return min(my_budget, 1)

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        if max_yesterday_bid >= DAILY_SALARY * 0.75 or \
           yesterday_struggled_count >= num_alive_opponents / 2 or \
           current_supply < total_water_demand_all_agents:
            
            if current_supply <= WATER_REQ + 2:
                return min(my_budget, DAILY_SALARY * 0.8)
            
            competitive_bid = max(max_yesterday_bid + 5, avg_yesterday_bid * 1.1)
            if my_hp < 4:
                competitive_bid = competitive_bid * 1.1
            
            return min(my_budget, competitive_bid, DAILY_SALARY * 0.9)

        else:
            if current_supply >= total_water_demand_all_agents:
                return min(my_budget, DAILY_SALARY * 0.25)
            else:
                moderate_bid = max(avg_yesterday_bid * 1.05, DAILY_SALARY * 0.35)
                return min(my_budget, moderate_bid)

    if current_supply >= total_water_demand_all_agents:
        return min(my_budget, DAILY_SALARY * 0.3)
    else:
        return min(my_budget, DAILY_SALARY * 0.6)
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

    # If no opponents are alive, bid just enough to get water cheaply.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    # Collect yesterday's bids from alive opponents
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    bid_amount = 0.0

    # Determine highest previous bid, or use a default if no history
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Strategy based on my HP and opponent's previous bids
    # CRITICAL: If HP is low, prioritize survival
    if my_hp <= 3: # Critically low HP
        # Bid very aggressively, close to my daily salary to ensure water.
        bid_amount = DAILY_SALARY - 1.0 # Bid 149.0
    else: # HP is not critically low
        if highest_prev_bid > DAILY_SALARY * 0.8: # High competition (e.g., > 120)
            # Competition is fierce, but my HP is okay. Adapt to game stage.
            if current_day >= EPISODE_DAYS * 0.7: # Last 30% of days, be more aggressive
                 bid_amount = max(DAILY_SALARY * 0.85, highest_prev_bid + 3.0)
            else: # Earlier/mid-game, slightly less aggressive
                 bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid + 2.0)
        elif highest_prev_bid > 0: # Moderate competition (yesterday bids exist)
            # Bid slightly above the highest previous to ensure win, but don't inflate price too much.
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0)
        else: # No significant yesterday bids, or default if yesterday_bids was empty
            # Use a moderate default bid for initial rounds or when opponents are passive.
            bid_amount = DAILY_SALARY * 0.6

    # Ensure bid does not exceed current budget and is at least 1.0
    final_bid = min(my_budget, bid_amount)
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    max_bid_possible = my_status['budget']

    # Base bid: a reasonable portion of daily salary
    bid = DAILY_SALARY * 0.6

    # --- Adjust bid based on my HP ---
    if my_status['hp'] <= 2: # Critical HP, must win
        bid = max(bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5: # Low HP, need water
        bid = max(bid, DAILY_SALARY * 0.8)
    else: # Decent HP, can be a bit more flexible
        bid = max(bid, DAILY_SALARY * 0.5) # Ensure a minimum reasonable bid

    # --- Adjust bid based on day (end game push) ---
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days, push for survival
        bid = max(bid, DAILY_SALARY * 0.85)

    # --- Adjust bid based on supply ---
    # Given supply range 15-25 and WATER_REQ is 13, competition is always high
    # as typically only one agent can get their full requirement.
    if day_context['supply'] <= WATER_REQ + 2: # Very tight supply (e.g., 15-16)
        bid = max(bid, DAILY_SALARY * 0.75)
    # For higher supply, no strong reduction; still need to win the water.

    # --- Adjust bid based on opponent's previous bids ---
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid high yesterday, I might need to match or exceed
        if highest_prev_bid >= DAILY_SALARY * 0.7: # If high previous bid (e.g., >= 105)
            if my_status['hp'] <= 5: # I need water
                bid = max(bid, highest_prev_bid + 5) # Try to outbid
            else: # HP is okay, try to win but don't overspend too much
                bid = max(bid, highest_prev_bid * 1.02) # Slightly above
        elif highest_prev_bid > 0: # If there was some bidding, but not super high
            bid = max(bid, highest_prev_bid + 1) # Just bid slightly above to win

    # Ensure bid does not exceed budget
    bid = min(bid, max_bid_possible)

    # Ensure bid is at least 1 to participate
    bid = max(bid, 1.0)

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # --- Determine base bid based on self-preservation and game stage --- 
    bid_value = DAILY_SALARY * 0.65 # Moderate starting bid

    # High urgency: Low HP or no water yesterday
    if my_no_water_days > 0 or my_hp <= 2:
        bid_value = DAILY_SALARY * 0.95 # Very aggressive bid
    # Medium urgency: Low-ish HP or late game
    elif my_hp <= 4 or current_day >= EPISODE_DAYS - 2:
        bid_value = DAILY_SALARY * 0.85 # Aggressive bid
    # Conserve if doing well and still early
    elif my_hp > 5 and my_no_water_days == 0 and current_day < EPISODE_DAYS / 2:
        bid_value = DAILY_SALARY * 0.55 # More conservative

    # --- Adjust bid based on opponent's previous behavior --- 
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If max opponent bid was high, react
        if max_prev_bid >= DAILY_SALARY * 0.8:
            bid_value = max(bid_value, max_prev_bid + 5) # Try to slightly outbid
        # If max opponent bid was low, and I'm not urgent, try to save
        elif max_prev_bid < DAILY_SALARY * 0.6 and my_hp > 4 and my_no_water_days == 0:
            bid_value = min(bid_value, max_prev_bid + 10) # Bid a bit above to secure, but not too high

    # --- Adjust bid based on supply scarcity --- 
    supply_ratio = (current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_multiplier = 1.0 - (supply_ratio * 0.2) # Range 0.8 (high supply) to 1.2 (low supply)
    bid_value *= supply_multiplier

    # --- Final adjustments and budget constraint --- 
    # Ensure bid is at least a minimal amount if budget allows
    final_bid = max(1.0, bid_value)

    # Cap bid by available budget
    final_bid = min(my_budget, final_bid)

    # If I have very little budget left and it's not the last day, try to conserve
    # unless I'm critical.
    if my_budget < DAILY_SALARY * 0.5 and my_hp > 2 and my_no_water_days == 0 and current_day < EPISODE_DAYS:
         final_bid = min(final_bid, my_budget * 0.8) # Try to save a bit more if not critical

    # Ensure bid is not negative. If budget is 0, bid 0.
    final_bid = max(0.0, final_bid)

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

    # If no alive opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Ensure 'bid' exists and is a valid number
        if prev and prev.get('bid') is not None and isinstance(prev['bid'], (int, float)):
            yesterday_bids.append(prev['bid'])

    # Determine highest previous bid
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        # If no previous bids (e.g., Day 1), assume a competitive baseline
        highest_prev_bid = DAILY_SALARY * 0.75 # Default to 112.5

    # --- Bidding Strategy ---

    # 1. Critical survival mode: low HP or consecutive no water days
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Must win this bid, bid very aggressively
        return min(my_status['budget'], DAILY_SALARY * 0.98) # Bids 147 out of 150

    # 2. High opponent pressure (opponents bidding close to or above salary)
    # Using 0.9 as a threshold for 'high pressure' (150 * 0.9 = 135)
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        if my_status['hp'] > 5: # Healthy enough to try and conserve budget
            return min(my_status['budget'], DAILY_SALARY * 0.7) # Bids 105
        else: # HP is not critical but not great, need water
            return min(my_status['budget'], DAILY_SALARY * 0.9) # Bids 135
    
    # 3. Moderate to low opponent pressure / Default competitive bid
    # Try to slightly outbid the highest previous bid, with a floor
    # Floor of 0.7 * DAILY_SALARY = 105
    # This covers cases where highest_prev_bid is lower than 0.9*DAILY_SALARY
    return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 5))
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
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- 1. Survival priority: If HP is critically low, bid very aggressively ---
    # If HP is 2 or less, I need water desperately. Bid very high.
    if my_hp <= 2:
        # Bid a very high amount to ensure survival, potentially exceeding daily salary
        return min(my_budget, DAILY_SALARY * 1.5) # Aim to outbid strong opponents like Alex/Bob

    # --- 2. Base bid calculation ---
    # Start with a competitive bid, considering my salary
    base_bid = DAILY_SALARY * 0.75

    # If I've missed water recently, increase bid to secure it
    if my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.9

    # --- 3. Adjust bid based on opponent behavior (yesterday's trace) ---
    yesterday_bids = []
    total_opponent_water_demand = 0
    for opp in alive_opponents:
        total_opponent_water_demand += opp['water_requirement']
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # Consider the highest bid from yesterday to gauge competition
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest bid yesterday was already high, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, highest_prev_bid + 5.0) # Slightly outbid
        # If highest bid was relatively low, we might not need to bid as high
        elif highest_prev_bid < DAILY_SALARY * 0.6:
            base_bid = min(base_bid, highest_prev_bid + 10.0) # Save money but stay competitive

    # --- 4. Adjust bid based on supply vs demand ---
    # Total water demand from all alive players including myself
    total_current_demand = total_opponent_water_demand + WATER_REQ

    # If supply is very tight (less than total demand, implying high competition for water)
    if current_supply < total_current_demand:
        # Further increase bid, especially if it's not the last day and I have budget
        if current_day < EPISODE_DAYS - 1:
            base_bid *= 1.1
        else: # Last day, might need to go all in
            base_bid *= 1.2
    # If supply is relatively abundant (can satisfy most players)
    elif current_supply >= total_current_demand:
        # If my HP is good, I can try to save some money
        if my_hp > 5:
            base_bid *= 0.9

    # --- 5. Late game aggression ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        # If I'm doing well, try to secure the win or eliminate struggling opponents
        if my_hp > 5 and my_budget > DAILY_SALARY * 2:
            base_bid = max(base_bid, DAILY_SALARY * 1.1)
        # If I'm struggling, bid very aggressively
        elif my_hp <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 1.3)

    # --- 6. Final bid constraints ---
    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 1 if I have budget and need water (and not already 0 due to 0 budget)
    if final_bid < 1.0 and my_budget > 0 and my_hp < 10: # Only if I actually need water
        final_bid = 1.0
    elif my_budget == 0: # If budget is 0, bid 0
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
    num_alive_opponents = len(alive_opponents)

    # Calculate a base bid, adjusted for my current HP
    my_base_bid = DAILY_SALARY * 0.55 # Default if no strong signals
    if my_status['hp'] <= 2:
        my_base_bid = DAILY_SALARY * 0.9 # Desperate
    elif my_status['hp'] <= 4:
        my_base_bid = DAILY_SALARY * 0.75 # Getting low

    # If no opponents, bid very conservatively
    if num_alive_opponents == 0:
        # Ensure we bid enough to secure water if supply is just enough for us
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine the bid based on highest previous bid and my HP
    bid_value = my_base_bid

    if highest_prev_bid > 0:
        # If highest previous bid was very high (e.g., >= 85% of my salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Not critically low, can afford to save budget
                bid_value = DAILY_SALARY * 0.3
            else: # Critically low HP, must win
                bid_value = DAILY_SALARY * 0.95
        # If highest previous bid was moderate
        else:
            # Bid slightly above the highest previous bid, ensuring a minimum of 50% of salary
            bid_value = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0) # Increment by a bit more than example
    else:
        # No previous bids from alive opponents, use my base bid
        bid_value = my_base_bid

    # Adjust bid based on supply scarcity if there are opponents
    supply = day_context['supply']
    # Estimate total water needed by all active players (including self)
    estimated_total_demand = WATER_REQ * (num_alive_opponents + 1)

    if supply < estimated_total_demand: # Supply is tight relative to demand
        bid_value *= 1.1 # Increase bid to compete harder
    elif supply >= WATER_REQ * (num_alive_opponents + 2): # Supply is very abundant, enough for more than two times current players
        bid_value *= 0.9 # Decrease bid to save budget

    # Ensure bid does not exceed budget and is at least 1.0 to participate
    final_bid = min(my_status['budget'], bid_value)
    final_bid = max(final_bid, 1.0)

    # Absolute last resort: if HP is critical (1 HP), bid almost everything
    if my_status['hp'] == 1 and my_status['budget'] > 0:
        final_bid = my_status['budget'] * 0.99

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

    # Determine my "desperation" level based on HP and no_water_days
    hp_desperation_factor = 1.0
    if my_status['hp'] <= 3:
        hp_desperation_factor = 1.6 # Critical HP
    elif my_status['hp'] <= 5:
        hp_desperation_factor = 1.3 # Low HP
    
    if my_status['no_water_days'] > 0:
        hp_desperation_factor = max(hp_desperation_factor, 1.4) # Missed water yesterday, very urgent

    # Base bid - a percentage of daily salary
    base_bid = DAILY_SALARY * 0.65 

    # Analyze opponent's previous bids from 'previous_trace'
    max_opp_prev_bid = 0.0
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            max_opp_prev_bid = max(max_opp_prev_bid, prev_trace['bid'])

    # Adjust bid based on my desperation
    current_bid = base_bid * hp_desperation_factor

    # Adjust bid based on opponent pressure from yesterday's highest bid
    if max_opp_prev_bid > 0:
        # If opponents are bidding high, I need to match or slightly exceed, especially if desperate
        if current_bid < max_opp_prev_bid:
            current_bid = max_opp_prev_bid + 5.0 # Try to outbid
        
        # If I'm desperate and opponents bid very high, be even more aggressive
        if hp_desperation_factor > 1.0 and max_opp_prev_bid >= DAILY_SALARY * 0.9:
            current_bid = max(current_bid, max_opp_prev_bid * 1.05)

    # Adjust bid based on supply-demand
    num_active_agents = len(alive_opponents) + 1
    total_water_needed_by_all = num_active_agents * WATER_REQ
    
    # Check if supply is scarce
    if day_context['supply'] < total_water_needed_by_all:
        current_bid *= 1.15 # Increase bid due to high competition/scarcity
    # Check if supply is abundant and I'm not desperate
    elif day_context['supply'] >= total_water_needed_by_all + WATER_REQ * 2 and my_status['hp'] > 5:
        current_bid *= 0.9 # Slightly decrease bid if supply is ample and I'm healthy

    # Budget constraint
    # Ensure bid does not exceed available budget
    current_bid = min(current_bid, my_status['budget'])

    # Minimum bid to ensure participation and avoid 0 bid if not intended
    min_bid_threshold = DAILY_SALARY * 0.05
    current_bid = max(current_bid, min_bid_threshold)

    # Special handling for very low budget but high desperation
    if my_status['budget'] < WATER_REQ * 10: # If budget is low
        if my_status['hp'] <= 3 or my_status['no_water_days'] > 0: # and I'm desperate
            # Bid as much as possible up to a high limit to survive
            current_bid = min(my_status['budget'], DAILY_SALARY * 1.5) # Cap at a very high bid if budget allows
        elif my_status['hp'] > 5: # Low budget but healthy, try to save
            current_bid = min(current_bid, DAILY_SALARY * 0.5)

    # Final check to ensure bid is non-negative
    final_bid = max(0.0, current_bid)
    
    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no active opponents, bid conservatively to save budget but ensure water.
    if not alive_opponents:
        return max(1, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = 0.0

    # My HP is critical, I must get water
    if my_status['hp'] <= 2:
        # Ensure an aggressive bid, at least 90% of salary, or slightly more than highest previous bid.
        bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 5)
    # My HP is healthy, I can afford to be more strategic
    else:
        # If opponents were bidding high yesterday (e.g., >= 80% of salary)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # Try to win by bidding slightly higher, but ensure it's at least 50% of salary.
            bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1)
        # If opponents were bidding moderately or low yesterday
        else:
            # Bid slightly above the highest previous bid, ensuring it's at least 40% of salary.
            bid = max(DAILY_SALARY * 0.4, highest_prev_bid + 1)

    # Ensure the bid does not exceed current budget and is at least 1.
    final_bid = max(1, min(my_status['budget'], bid))
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Calculate total water requirement of all alive agents, including myself
    total_water_required_by_active_agents = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_required_by_active_agents += opp['water_requirement']

    # Determine a base bid
    # Start with a moderate bid, assuming some competition
    base_bid = DAILY_SALARY * 0.55

    # Adjust bid based on my health and no-water days
    if my_hp <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_no_water_days > 0: # Missed water yesterday, need to recover
        base_bid = DAILY_SALARY * 0.8
    elif my_hp <= 4: # Low HP, be more aggressive
        base_bid = DAILY_SALARY * 0.7

    # Adjust bid based on supply vs demand
    if current_supply < total_water_required_by_active_agents:
        # High competition: demand exceeds supply
        # Increase bid proportionally to scarcity, but cap it
        scarcity_multiplier = min(1.5, total_water_required_by_active_agents / current_supply)
        base_bid *= scarcity_multiplier
    else:
        # Low competition: supply meets or exceeds demand
        # Can be slightly more conservative if not desperate
        if my_hp > 5 and my_no_water_days == 0:
            base_bid *= 0.9 # Try to save money

    # Analyze yesterday's bids from opponents (previous_trace)
    yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        prev_trace = opp_data.get('previous_trace')
        # Ensure it's the trace from the previous day of the current episode
        if prev_trace and prev_trace.get('bid') is not None and prev_trace.get('day') == current_day - 1:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest bid was very high, react by bidding slightly above it
        if max_yesterday_bid >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, max_yesterday_bid + 5)
        # If average bid was competitive, ensure we are at least at that level
        elif avg_yesterday_bid >= DAILY_SALARY * 0.5:
            base_bid = max(base_bid, avg_yesterday_bid * 1.05)
        else:
            # If bids were low, we can try to save, but still be competitive
            base_bid = max(base_bid, avg_yesterday_bid + 2)

    # Adjust for end-game scenario
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2: # Last 2 days, bid aggressively to survive
        base_bid = max(base_bid, DAILY_SALARY * 0.85)

    # Final bid must not exceed budget and be non-negative
    final_bid = min(my_budget, base_bid)
    final_bid = max(0.0, final_bid)

    # Ensure a minimal bid if desperate, even if budget is low, to try and get something
    if (my_hp <= 2 or my_no_water_days > 0) and final_bid < DAILY_SALARY * 0.7:
        final_bid = min(my_budget, DAILY_SALARY * 0.7) # Try to bid strongly if possible

    return round(final_bid, 2)
"""
