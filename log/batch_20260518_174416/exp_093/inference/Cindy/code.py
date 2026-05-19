# ============================================================
# Experiment: exp_093
# Agent: Cindy
# Source: exp_093
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        # If supply is enough just for me, bid low.
        if day_context['supply'] >= WATER_REQ:
            return min(my_status['budget'], DAILY_SALARY * 0.1) # Bid very low, just to get water
        else: # Supply is less than my requirement, still bid low as no competition
            return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Calculate total water requirement among all alive agents
    total_water_needed = WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)

    # Determine base bid based on supply scarcity and number of opponents
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid
    
    # Use supply_per_person_if_equal as a heuristic for scarcity
    # Ensure division by zero is avoided if num_alive_opponents is negative (shouldn't happen)
    divisor = num_alive_opponents + 1
    supply_per_person_if_equal = day_context['supply'] / divisor if divisor > 0 else day_context['supply']

    if supply_per_person_if_equal < WATER_REQ:
        # High scarcity, need to bid more aggressively
        base_bid = DAILY_SALARY * 0.7
        if supply_per_person_if_equal < WATER_REQ * 0.7: # Very high scarcity
            base_bid = DAILY_SALARY * 0.9
    elif day_context['supply'] > total_water_needed * 1.2: # Abundant supply
        base_bid = DAILY_SALARY * 0.3 # Can afford to bid lower

    # Look at yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high yesterday, we need to be competitive
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # If my HP is low, bid aggressively
            if my_status['hp'] <= 3:
                return min(my_status['budget'], DAILY_SALARY * 0.95)
            # Otherwise, try to be competitive but not overly aggressive if my HP is good
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Bid slightly higher than highest previous
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            # Moderate bids yesterday, adjust base bid slightly
            base_bid = max(base_bid, highest_prev_bid * 1.05) # Try to slightly outbid
        else:
            # Low bids yesterday, can potentially bid lower or maintain base_bid
            base_bid = max(base_bid * 0.8, highest_prev_bid * 0.9) # Try to conserve
    
    # Adjust bid based on my HP, especially if no strong previous bid signal or after previous bid adjustments
    if my_status['hp'] <= 2: # Critical HP
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid very high to survive
    elif my_status['hp'] <= 4 and my_status['no_water_days'] > 0: # Low HP and missed water recently
        base_bid = max(base_bid, DAILY_SALARY * 0.85) # High bid
    
    # Consider late game strategy
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last few days, prioritize survival
        if my_status['hp'] <= 5: # If HP is not great, bid aggressively
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else: # Otherwise, maintain a competitive bid
            base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Final bid decision, capped by budget
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a small amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 1. Look at yesterday's situation (Trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 2. Decision logic based on yesterday's highest pressure and my HP
    bid_amount = DAILY_SALARY * 0.65 # Default bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Check if previous bids were very high, indicating fierce competition
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Bids were ~127.5 or higher yesterday
            if my_status['hp'] > 3: # If my HP is good, I can still try to get water without overspending
                # Aim to slightly outbid the high bid, but cap it to avoid extreme overspending
                bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid + 2.0)
                bid_amount = min(bid_amount, DAILY_SALARY * 0.95) # Cap at ~142.5
            else: # If my HP is low (3 or less), I must bid aggressively to survive
                bid_amount = DAILY_SALARY * 0.98 # Very aggressive, ~147
        else: # Moderate competition or lower bids yesterday (highest_prev_bid < ~127.5)
            # Try to outbid the highest previous bid slightly, but ensure a reasonable base
            bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid + 2.0)
            # Cap the bid if it gets too high, even in moderate competition
            bid_amount = min(bid_amount, DAILY_SALARY * 0.85) # Cap at ~127.5
    else: # No bids from opponents yesterday (e.g., first day, or all opponents died)
        if my_status['hp'] <= 2: # If my HP is critically low, bid high to survive
            bid_amount = DAILY_SALARY * 0.9 # ~135
        # Else, bid_amount remains at default DAILY_SALARY * 0.65

    # Ensure the bid does not exceed my current budget and is at least 1
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(final_bid, 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    CRITICAL_HP = 3
    LOW_SUPPLY_THRESHOLD = 18.0
    HIGH_SUPPLY_THRESHOLD = 22.0

    # Base bid - a reasonable amount to secure water without overspending
    bid = DAILY_SALARY * 0.6

    # Adjust bid based on my HP
    if my_status['hp'] <= CRITICAL_HP:
        bid = DAILY_SALARY * 0.9 # Bid aggressively if HP is critical
    elif my_status['hp'] <= 5:
        bid = DAILY_SALARY * 0.75 # Moderately low HP

    # Adjust bid based on supply
    supply = day_context['supply']
    if supply <= LOW_SUPPLY_THRESHOLD:
        bid *= 1.1 # Increase bid if supply is low, competition likely higher
    elif supply >= HIGH_SUPPLY_THRESHOLD:
        bid *= 0.9 # Decrease bid if supply is high, competition likely lower

    # Opponent analysis from yesterday's bids
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If the highest previous bid was significant, react to it
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            # If I'm not in critical HP, try to match or slightly exceed
            if my_status['hp'] > CRITICAL_HP:
                bid = max(bid, highest_prev_bid + 5.0) # Add a small buffer
            else:
                # If critical, bid very high to ensure water
                bid = max(bid, highest_prev_bid + 10.0, DAILY_SALARY * 0.95)
        elif highest_prev_bid <= DAILY_SALARY * 0.3 and my_status['hp'] > CRITICAL_HP:
            # If opponents bid very low, and I'm not critical, I can try to save money
            bid = min(bid, highest_prev_bid + 10.0, DAILY_SALARY * 0.5)

    # Ensure bid does not exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least a minimal amount to be considered serious, and positive.
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
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to conserve budget.
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Base bid strategy: aim to secure water.
    # Start with a bid slightly above average opponent's historical survival bid.
    bid = DAILY_SALARY * 0.75 # 112.5

    # Adjust bid based on my health and no_water_days
    if my_hp <= 2 or my_no_water_days > 0:
        # Critical state: Must get water, bid very aggressively.
        bid = DAILY_SALARY * 1.05 # 157.5 - slightly above daily salary to outbid
    elif my_hp <= 4:
        # Low HP: Be aggressive.
        bid = DAILY_SALARY * 0.9 # 135.0
    elif current_day >= EPISODE_DAYS - 2:
        # Late game, push for survival or winning.
        bid = DAILY_SALARY * 0.95 # 142.5
    
    # Analyze yesterday's bids from opponents to adjust
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_hp <= 3 or my_no_water_days > 0:
                # Desperate and competition is high, bid to win.
                bid = max(bid, highest_prev_bid + 5)
            else:
                # High competition, but I'm not desperate, still need to be competitive.
                bid = max(bid, highest_prev_bid + 1)
        # If opponents were moderately aggressive
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            bid = max(bid, highest_prev_bid + 1)
        # If opponents were not very aggressive, try to save money if possible
        else:
            if my_hp > 4 and my_no_water_days == 0:
                # If healthy, try to win with a slightly lower bid if possible, but still competitive.
                bid = min(bid, highest_prev_bid + 5)
                bid = max(bid, DAILY_SALARY * 0.65) # Ensure a minimum floor bid
            # Else, if not healthy, stick to my health-based aggressive bid.

    # Ensure the bid is not less than a minimum competitive value
    bid = max(bid, DAILY_SALARY * 0.6) # Minimum bid of 90 to stay in the game

    # Ensure bid does not exceed available budget
    final_bid = min(bid, my_budget)

    # If budget is very low, bid whatever is left to try and survive
    if final_bid <= 0 and my_budget > 0:
        final_bid = min(my_budget, 1.0) # Bid a token amount if budget is minimal
    elif final_bid <= 0: # If budget is 0 or negative
        final_bid = 0.0 # Cannot bid

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

    current_day = day_context['day']
    current_supply = day_context['supply']

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid strategy
    bid_amount = DAILY_SALARY * 0.6 # Default moderate bid

    # --- Adjust based on my status ---
    # High priority for water if HP is low or no water for days
    if my_hp <= 3: # Critical HP
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95)
    elif my_no_water_days > 0: # Missed water yesterday
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
        if my_no_water_days >= 2: # Missed water for multiple days
            bid_amount = max(bid_amount, DAILY_SALARY * 0.98)

    # If HP is very good and budget allows, can afford to be slightly less aggressive
    if my_hp >= 8 and my_budget > DAILY_SALARY * 2: # Good HP, healthy budget
        bid_amount = min(bid_amount, DAILY_SALARY * 0.5)

    # --- React to opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If opponents were aggressive, match or slightly exceed
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_amount = max(bid_amount, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid_amount = max(bid_amount, average_prev_bid + 2)
        else: # Opponents were conservative, try to win cheaply but still win
            bid_amount = max(bid_amount, average_prev_bid * 1.1) # Bid slightly above their average

    # --- Adjust based on supply vs demand ---
    available_units = int(current_supply // WATER_REQ)
    total_active_bidders = num_alive_opponents + 1 # Include myself

    if available_units < total_active_bidders: # Scarcity: increase bid
        if my_hp <= 4 or my_no_water_days > 0: # If desperate, bid very high
            bid_amount = max(bid_amount, DAILY_SALARY * 0.99)
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
    elif available_units >= total_active_bidders: # Abundance: can potentially lower bid
        # Only lower if not desperate and budget is good
        if my_hp >= 6 and my_budget > DAILY_SALARY:
            bid_amount = min(bid_amount, DAILY_SALARY * 0.4)

    # --- End-game strategy ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last two days, bid very aggressively
        bid_amount = max(bid_amount, DAILY_SALARY * 0.99)
    elif remaining_days <= 4: # Approaching end
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    # Ensure bid does not exceed budget and is positive
    final_bid = min(my_budget, bid_amount)
    final_bid = max(0.01, final_bid) # Minimum bid of 0.01

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

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']

    # Start with a base bid that tries to save money but is competitive
    base_bid = DAILY_SALARY * 0.9

    # Find the highest bid from yesterday among all active opponents
    highest_yesterday_bid = 0.0

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                opp_bid_yesterday = prev_trace['bid']
                # Consider opponents who bid at least a significant amount to filter out passive/zero bidders
                if opp_bid_yesterday > DAILY_SALARY * 0.5:
                    highest_yesterday_bid = max(highest_yesterday_bid, opp_bid_yesterday)

    # Adjust bid based on highest opponent bid from yesterday
    if highest_yesterday_bid > 0:
        # Bid slightly above the highest known aggressive bid to win
        my_bid = highest_yesterday_bid + 5
    else:
        # If no strong history, use the base bid
        my_bid = base_bid

    # Adjust bid based on my HP and remaining days
    remaining_days = EPISODE_DAYS - current_day

    # Critical HP: If I have few HP, I need water desperately
    if my_current_hp <= 2: # Very low HP
        my_bid = max(my_bid, DAILY_SALARY * 1.25) # Bid significantly above salary
    elif my_current_hp <= 5: # Low HP
        my_bid = max(my_bid, DAILY_SALARY * 1.1) # Bid above salary
    elif my_current_hp > 5 and remaining_days <= 3: # Healthy but late in game, ensure survival
        my_bid = max(my_bid, DAILY_SALARY * 1.0) # Ensure I get water if near end

    # Ensure bid is at least a minimum to stay competitive even if opponents were passive
    my_bid = max(my_bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed current budget
    final_bid = min(my_bid, my_current_budget)

    # Ensure bid is not negative
    final_bid = max(0.0, final_bid)

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

    bid_amount = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4:
        bid_amount = DAILY_SALARY * 0.75

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                bid_amount = max(bid_amount, highest_prev_bid * 0.9)
            else:
                bid_amount = max(bid_amount, highest_prev_bid + 5)
        elif highest_prev_bid > DAILY_SALARY * 0.5:
            bid_amount = max(bid_amount, highest_prev_bid + 1)

    final_bid = min(my_status['budget'], bid_amount)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 
    
    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    num_total_players = num_alive_opponents + 1 # Including myself

    # --- Estimate the number of players who can get *some* water ---
    # This is a rough estimate of how many "slots" are available.
    # It assumes players take their full requirement if possible, or remaining supply.
    # We sort requirements to simulate highest bidders taking their share first.
    all_requirements = [WATER_REQ] + [opp['water_requirement'] for opp in alive_opponents]
    all_requirements.sort(reverse=True) # Sort to prioritize larger requirements for slot calculation

    potential_water_slots = 0
    temp_supply = current_supply
    for req in all_requirements:
        if temp_supply >= 1: # If there's at least 1 unit of supply left
            potential_water_slots += 1
            temp_supply -= min(req, temp_supply) # Subtract what this player would take

    # --- Analyze opponent's previous bids ---
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # --- Bidding Strategy ---
    base_bid = DAILY_SALARY * 0.5 # Default starting bid

    # Adjust bid based on HP
    if my_hp <= 2: # Critical HP: Must get water
        # Bid very high, potentially maxing out budget for survival
        bid = min(my_budget, DAILY_SALARY * 0.95)
        # Ensure it's competitive against known aggressive bids
        if max_yesterday_bid > base_bid:
            bid = max(bid, max_yesterday_bid + 5)
        # If very late in game, even more aggressive
        if EPISODE_DAYS - current_day <= 2:
            bid = min(my_budget, DAILY_SALARY * 1.05) # Go slightly above salary if budget allows for final push
    elif my_hp <= 5: # Low HP: Need water, but can be slightly less desperate
        bid = min(my_budget, DAILY_SALARY * 0.8)
        if max_yesterday_bid > base_bid:
            bid = max(bid, max_yesterday_bid + 2)
    else: # Healthy HP: Balance winning and saving budget
        if num_alive_opponents == 0:
            bid = DAILY_SALARY * 0.1 # No competition, bid low
        elif potential_water_slots >= num_total_players: # Enough water for everyone
            bid = DAILY_SALARY * 0.2 # Bid low
        elif potential_water_slots == 1: # Very scarce, only one player can get full water
            # This is highly competitive. Bid aggressively but try not to overpay if possible.
            bid = DAILY_SALARY * 0.85
            if max_yesterday_bid > DAILY_SALARY * 0.7: # If competition was already high
                bid = max(bid, max_yesterday_bid + 1)
            else: # If competition was low, don't unnecessarily inflate
                bid = max(bid, DAILY_SALARY * 0.7)
        else: # Moderate competition (e.g., 2 slots for 3-5 players)
            bid = DAILY_SALARY * 0.65
            if max_yesterday_bid > DAILY_SALARY * 0.5:
                bid = max(bid, max_yesterday_bid + 1)
            else:
                bid = max(bid, DAILY_SALARY * 0.55)

    # Further adjustment based on remaining days and budget
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3: # Last few days, increase aggressiveness
        if my_hp <= 5: # Still need water
            bid = min(my_budget, max(bid, DAILY_SALARY * 0.9))
        else: # Healthy but want to win
            bid = min(my_budget, max(bid, DAILY_SALARY * 0.75))
    elif remaining_days >= 7 and my_hp > 5: # Early days, healthy, can be slightly more conservative
        # Avoid overbidding if not strictly necessary and budget is good
        if my_budget / (remaining_days * DAILY_SALARY) > 1.5: # If I have significantly more budget than needed
            bid = min(bid, DAILY_SALARY * 0.6) # Pull back slightly

    # Ensure bid doesn't exceed budget
    bid = min(bid, my_budget)
    
    # Ensure bid is always positive and at least 1.0 if I need water
    bid = max(1.0, bid)

    return bid
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

    # --- Special Case: No real opponents --- 
    # Check if only Eric (who bids very low) or no strong opponents are alive
    alive_competitors = [
        o for o in opponents_status.values() 
        if o['alive'] and o['agent_id'] != "Eric"
    ]
    if not alive_competitors:
        # If no real competitors, bid minimum to conserve budget
        return min(my_budget, DAILY_SALARY * 0.05) # Very low bid

    # --- Collect yesterday's competitive bids --- 
    yesterday_competitive_bids = []
    
    # Analyze known strong competitors (Alex, David) based on meta-round context
    strong_competitor_ids = ["Alex", "David"]
    for agent_id in strong_competitor_ids:
        if agent_id in opponents_status and opponents_status[agent_id]['alive']:
            opp_data = opponents_status[agent_id]
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_competitive_bids.append(prev_trace['bid'])
    
    # Also consider any other alive opponent who previously bid high (e.g., Bob if he changes strategy)
    for agent_id, opp_data in opponents_status.items():
        if opp_data['alive'] and agent_id not in strong_competitor_ids and opp_data['agent_id'] != "Eric":
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                # If they previously bid above a certain threshold, consider them competitive
                if prev_trace['bid'] > DAILY_SALARY * 0.6: 
                    yesterday_competitive_bids.append(prev_trace['bid'])

    # --- Determine base bid based on competition --- 
    target_bid = DAILY_SALARY * 0.65 # Default competitive bid
    if yesterday_competitive_bids:
        highest_prev_competitive_bid = max(yesterday_competitive_bids)
        # Bid slightly above the highest competitive bid, with a floor to ensure competitiveness
        target_bid = max(DAILY_SALARY * 0.7, highest_prev_competitive_bid + 5)

    # --- Adjust bid based on my HP and remaining days --- 
    days_left = EPISODE_DAYS - current_day

    if my_hp <= 2 or my_status['no_water_days'] > 0:
        # Critical HP or missed water yesterday, must get water to survive
        final_bid = DAILY_SALARY * 0.98
    elif my_hp <= 4 or days_left <= 2:
        # Low HP or end-game (last 2 days), need to be very aggressive
        final_bid = DAILY_SALARY * 0.90
    else:
        # Normal state, use the target bid determined by competition
        final_bid = target_bid

    # --- Apply budget constraints and minimum bid --- 
    final_bid = min(final_bid, my_budget) # Cannot bid more than current budget
    final_bid = max(final_bid, 1.0) # Ensure a minimum bid to participate

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

    # If no opponents are alive, bid minimum to secure water and save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Collect opponent's previous bids and total water requirement
    yesterday_opponent_bids = []
    total_opponent_water_requirement = 0
    for opp in alive_opponents:
        total_opponent_water_requirement += opp['water_requirement']
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_opponent_bids.append(prev['bid'])

    # Calculate total water demand (including myself)
    total_water_demand = WATER_REQ + total_opponent_water_requirement

    # Determine base bid strategy based on my HP
    base_bid = DAILY_SALARY * 0.5 # A moderate starting point

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical HP or missed water yesterday, bid aggressively for survival
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        # Low HP, but not critical, bid high
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= EPISODE_DAYS - day_context['day'] + 2: # More HP than remaining days + buffer
        # High HP, can afford to be less aggressive to save budget
        base_bid = DAILY_SALARY * 0.4
    else:
        # Medium HP, balanced approach
        base_bid = DAILY_SALARY * 0.6

    # Adjust bid based on supply and demand
    # Avoid division by zero if total_water_demand happens to be 0 (though unlikely with WATER_REQ > 0)
    supply_ratio = day_context['supply'] / total_water_demand if total_water_demand > 0 else 1.0

    if supply_ratio < 1.0: # Scarcity - demand exceeds supply
        # Increase bid due to competition
        base_bid *= 1.2
        if yesterday_opponent_bids:
            max_prev_bid = max(yesterday_opponent_bids)
            # Bid slightly above max previous bid, but capped
            base_bid = max(base_bid, max_prev_bid + 5)
            base_bid = min(base_bid, DAILY_SALARY * 0.9) # Don't overbid excessively
    elif supply_ratio > 1.5: # Abundance - supply is much more than demand
        # Decrease bid to save money
        base_bid *= 0.7
        if yesterday_opponent_bids:
            avg_prev_bid = sum(yesterday_opponent_bids) / len(yesterday_opponent_bids)
            # Try to undercut average bid, but ensure it's not too low
            base_bid = min(base_bid, avg_prev_bid * 0.9)
            base_bid = max(base_bid, DAILY_SALARY * 0.25) # Minimum bid to stay competitive
    else: # Balanced supply and demand
        if yesterday_opponent_bids:
            avg_prev_bid = sum(yesterday_opponent_bids) / len(yesterday_opponent_bids)
            # Bid around average, maybe slightly above to secure water
            base_bid = max(base_bid, avg_prev_bid * 1.05)
            base_bid = min(base_bid, DAILY_SALARY * 0.7) # Cap it

    # Further adjust based on day progression (late game pressure)
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        base_bid = max(base_bid, DAILY_SALARY * 0.75) # Be more aggressive

    # Ensure bid is at least 1 and does not exceed current budget
    final_bid = max(1.0, base_bid)
    return min(my_status['budget'], final_bid)
"""
