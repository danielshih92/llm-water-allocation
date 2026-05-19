# ============================================================
# Experiment: exp_013
# Agent: Cindy
# Source: exp_013
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    
    current_supply = day_context['supply']

    # Filter alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid - a reasonable starting point
    base_bid = MY_DAILY_SALARY * 0.5 

    # --- Survival Mode --- 
    # If HP is very low or I've missed water recently, bid aggressively
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.95) # Bid almost full salary to survive

    # --- Adjust bid based on competition and supply --- 
    total_water_demand = MY_WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # If supply is very abundant, reduce bid
    if current_supply >= total_water_demand:
        base_bid = MY_DAILY_SALARY * 0.35 # Try to get it cheap
    # If supply is scarce, increase bid
    elif current_supply < MY_WATER_REQ * (num_alive_opponents + 1): # Supply is less than total minimum needed for everyone
        base_bid = MY_DAILY_SALARY * 0.7 # Increase bid significantly
    elif current_supply < total_water_demand: # Supply is less than total demand, but not extremely scarce
        base_bid = MY_DAILY_SALARY * 0.6 # Moderate increase

    # --- React to yesterday's bids from opponents ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If opponents bid high yesterday, and supply is not super abundant, consider bidding slightly higher
        if max_yesterday_bid > MY_DAILY_SALARY * 0.6 and current_supply < total_water_demand:
            base_bid = max(base_bid, max_yesterday_bid + 1) # Bid slightly above max to secure water
        # If opponents bid low yesterday, and supply is not super scarce, consider bidding lower
        elif max_yesterday_bid < MY_DAILY_SALARY * 0.4 and current_supply >= total_water_demand:
             base_bid = min(base_bid, max_yesterday_bid + 1) # Try to get it slightly above their low bid
    
    # Ensure bid is not negative or exceeds budget
    final_bid = max(0, min(my_status['budget'], base_bid))
    
    # A final check for HP - if HP is getting low, be more aggressive
    if my_status['hp'] <= 3 and final_bid < MY_DAILY_SALARY * 0.8:
        final_bid = min(my_status['budget'], MY_DAILY_SALARY * 0.8)

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
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    total_water_needed_by_all = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']

    my_bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2:
        my_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        my_bid = DAILY_SALARY * 0.8
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
    
    highest_prev_opp_bid = 0.0
    if yesterday_bids:
        highest_prev_opp_bid = max(yesterday_bids)

    if highest_prev_opp_bid > 0:
        if my_status['hp'] <= 5:
            my_bid = max(my_bid, highest_prev_opp_bid + 2.0)
        elif day_context['supply'] < total_water_needed_by_all:
            my_bid = max(my_bid, highest_prev_opp_bid + 1.0)
        else:
            my_bid = max(my_bid, highest_prev_opp_bid + 0.5)
    
    if day_context['supply'] < WATER_REQ:
        my_bid = max(my_bid, DAILY_SALARY * 0.9)
    elif day_context['supply'] < WATER_REQ * len(alive_opponents):
        my_bid = max(my_bid, DAILY_SALARY * 0.75)

    final_bid = min(my_status['budget'], my_bid)

    if final_bid <= 0 and my_status['budget'] > 0 and my_status['hp'] < EPISODE_DAYS:
        final_bid = min(my_status['budget'], 1.0)

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    # Calculate remaining days
    days_left = EPISODE_DAYS - day_context['day']

    # Identify alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If I'm the only one left, bid minimally to survive.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents using previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Adjust base bid based on opponent's highest previous bid
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding very high (e.g., >= 120)
            if my_status['hp'] > 3: # If I'm healthy, try to save a bit
                base_bid = DAILY_SALARY * 0.6
            else: # If HP is low, bid very aggressively to survive
                base_bid = DAILY_SALARY * 0.95
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents are bidding high (e.g., >= 90)
            base_bid = highest_prev_bid + 5.0 # Slightly outbid them
        else: # Opponents are bidding relatively low
            base_bid = max(DAILY_SALARY * 0.4, highest_prev_bid + 2.0) # Ensure a decent bid but don't overpay

    # Further adjust bid based on my HP and remaining days
    if my_status['hp'] <= 2: # Critical HP, bid very high
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4 and days_left > 2: # Low HP but not critical, mid-game
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    
    # Adjust for number of opponents
    num_opponents = len(alive_opponents)
    if num_opponents > 2: # More competition
        base_bid *= 1.1 # Increase bid slightly
    elif num_opponents == 1: # Less competition
        base_bid *= 0.9 # Decrease bid slightly

    # Adjust for supply scarcity: If supply is very tight, competition is higher
    # WATER_REQ is 13, supply range is [15, 25]. Only one player can get full water.
    # If supply is barely above WATER_REQ, it's even tighter for secondary allocations.
    if day_context['supply'] <= WATER_REQ + 5: # Supply is 15-18, very tight for even partial allocation to others
        base_bid = max(base_bid, DAILY_SALARY * 0.7) # Ensure a strong bid
    
    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least a minimal value to participate, if budget allows
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid if no strong opponent data or no opponents
    # This initial value is based on Eric's average bid (67.64) relative to my salary (150), approx 0.45
    base_bid_value = DAILY_SALARY * 0.45

    if not alive_opponents:
        # If no opponents, bid conservatively to ensure water at minimal cost
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Bid slightly above the highest previous bid to outcompete known aggressive bidders like Eric
        base_bid_value = max(base_bid_value, highest_prev_bid + 1.5)
    
    # Adjust bid based on my current HP to prioritize survival or save budget
    final_bid = base_bid_value
    if my_status['hp'] <= 3: # Critical HP: Bid very aggressively to survive
        final_bid = max(final_bid, DAILY_SALARY * 0.85)
    elif my_status['hp'] <= 6: # Moderate HP: Bid aggressively to maintain health
        final_bid = max(final_bid, DAILY_SALARY * 0.65)
    else: # Healthy HP: Bid competitively but try to conserve budget
        final_bid = max(final_bid, DAILY_SALARY * 0.5)

    # Ensure bid does not exceed available budget
    return min(my_status['budget'], final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
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

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    avg_opponent_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0
    max_opponent_bid = max(yesterday_bids) if yesterday_bids else 0

    base_bid = DAILY_SALARY * 0.5

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.75
    elif my_hp > 7 and my_budget > DAILY_SALARY * 3:
        base_bid = DAILY_SALARY * 0.4

    estimated_water_per_agent = current_supply / (num_alive_opponents + 1)

    if estimated_water_per_agent < WATER_REQ:
        base_bid = max(base_bid, max_opponent_bid + 5, DAILY_SALARY * 0.8)
    elif estimated_water_per_agent >= WATER_REQ * 1.5:
        base_bid = min(base_bid, DAILY_SALARY * 0.3, avg_opponent_bid * 0.9 if avg_opponent_bid else base_bid)
    else:
        base_bid = max(base_bid, avg_opponent_bid + 1)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 0.95, max_opponent_bid + 10)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
    elif current_day <= 2:
        if my_hp > 5:
            base_bid = min(base_bid, DAILY_SALARY * 0.6)

    final_bid = max(1.0, base_bid)

    final_bid = min(final_bid, my_budget)

    if my_budget < DAILY_SALARY and my_hp > 3:
        final_bid = min(final_bid, my_budget * 0.8)

    if my_no_water_days > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.75)

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
    david_yesterday_bid = 0.0

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id == "David":
                    david_yesterday_bid = prev['bid']

    target_prev_bid = 0.0
    if david_yesterday_bid > 0:
        target_prev_bid = david_yesterday_bid
    elif yesterday_bids:
        target_prev_bid = max(yesterday_bids)

    # --- Bidding Logic ---
    # Critical state: Very low HP, must win.
    if my_status['hp'] <= WATER_REQ:
        calculated_bid = DAILY_SALARY * 0.99
    # Desperate state: Low HP, need to win.
    elif my_status['hp'] <= WATER_REQ * 2:
        if target_prev_bid >= DAILY_SALARY * 0.7:
            calculated_bid = max(DAILY_SALARY * 0.85, target_prev_bid + 5.0)
        else:
            calculated_bid = DAILY_SALARY * 0.8
    # Healthy state: Can afford to be strategic.
    else:
        if target_prev_bid >= DAILY_SALARY * 0.7:
            calculated_bid = max(DAILY_SALARY * 0.65, target_prev_bid + 2.0)
        elif target_prev_bid >= DAILY_SALARY * 0.4:
            calculated_bid = max(DAILY_SALARY * 0.55, target_prev_bid + 1.0)
        else:
            calculated_bid = DAILY_SALARY * 0.55

    final_bid = min(my_status['budget'], calculated_bid)

    if my_status['hp'] <= WATER_REQ and my_status['budget'] > 0:
        final_bid = my_status['budget']
    
    if final_bid <= 0.0 and my_status['budget'] > 0.0 and my_status['hp'] > 0:
        final_bid = 1.0

    return float(final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # CRITICAL RULE 9: Ensure all indices are integers.
    current_supply = int(day_context['supply'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # 1. No opponents: Bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Calculate total water needed by all alive agents (including myself)
    total_water_needed_by_all = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']

    # 2. Reactive Bidding: Adjust based on opponent's yesterday behavior.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Scenario A (from example): Opponents bid very high yesterday (high pressure)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # My HP is good, I can afford to save/make them overspend
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # My HP is not good (<= 3), I must secure water
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        
        # Scenario B (from example): Moderate previous bids (normal competition)
        else:
            # Bid slightly above the highest previous bid to secure water.
            base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            
            # Additional logic: Adjust base bid further based on supply scarcity
            if current_supply < total_water_needed_by_all:
                if current_supply < WATER_REQ * len(alive_opponents): # Very tight supply
                    base_bid = max(base_bid, DAILY_SALARY * 0.75) # Ensure a sufficiently high bid
                else: # Moderately tight supply
                    base_bid = max(base_bid, DAILY_SALARY * 0.6)
            
            return min(my_status['budget'], base_bid)

    # 3. Default Bidding: If no previous bids from opponents (e.g., first day or all new opponents).
    # This block is reached if `yesterday_bids` is empty.
    
    # Check for critical HP if no previous bids are available
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.9) # As per example's default for low HP without prev bids

    # Default bid if HP > 2 and no previous bids
    default_bid_percentage = 0.55 # As per example's default

    # Additional logic: Adjust default bid based on supply scarcity
    if current_supply < total_water_needed_by_all:
        if current_supply < WATER_REQ * len(alive_opponents): # Very tight supply
            default_bid_percentage = 0.8
        else: # Moderately tight supply
            default_bid_percentage = 0.7
    else: # Ample supply
        default_bid_percentage = 0.5 # More conservative when supply is high

    return min(my_status['budget'], DAILY_SALARY * default_bid_percentage)
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
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_budget, 1.0)

    # Identify strong opponents based on meta-round context
    # Alex and David are strong based on their survival and average bids
    strong_opponent_ids = ["Alex", "David"]
    
    yesterday_strong_bids = []
    for opp_id in strong_opponent_ids:
        if opp_id in opponents_status and opponents_status[opp_id]['alive']:
            prev = opponents_status[opp_id].get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_strong_bids.append(prev['bid'])
    
    highest_strong_prev_bid = 0
    if yesterday_strong_bids:
        highest_strong_prev_bid = max(yesterday_strong_bids)

    # Base bid strategy based on my HP
    bid = 0.0
    if my_hp <= 0: # Critical, must get water
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 2: # Low HP, very aggressive
        bid = DAILY_SALARY * 0.85
    elif my_hp <= 5: # Moderate HP, competitive
        bid = DAILY_SALARY * 0.7
    else: # Good HP, more conservative but still competitive
        bid = DAILY_SALARY * 0.55

    # Adjust bid based on highest strong opponent's previous bid
    if highest_strong_prev_bid > 0:
        # If strong opponents are bidding high, I need to respond
        # Try to outbid them slightly or match if my base bid is too low
        if bid < highest_strong_prev_bid * 1.05: 
            bid = max(bid, highest_strong_prev_bid + 1.0) # Ensure I slightly exceed their last high bid

    # Adjust for supply scarcity:
    # If supply is low and there are still many alive opponents, competition is higher.
    num_active_players = len(alive_opponents) + 1 # Me + alive opponents
    
    # A simple scarcity metric: if supply is less than water_req * num_players
    if supply < WATER_REQ * num_active_players * 0.8: # If supply is less than 80% of total demand
        # Increase bid if supply is very scarce
        bid = bid * 1.15 # Increase by 15%
        if my_hp <= 2: # If I also have low HP, increase more
            bid = bid * 1.1 # Another 10% increase

    # Ensure bid does not exceed current budget
    bid = min(bid, my_budget)
    
    # Ensure bid is at least 1.0 to participate
    bid = max(1.0, bid)

    # Ensure bid does not exceed DAILY_SALARY too much unless critical
    if my_hp > 0: # If not critical, limit bid to salary * 1.1
        bid = min(bid, DAILY_SALARY * 1.1)
    else: # If critical, can go higher
        bid = min(bid, DAILY_SALARY * 1.5) # Allow higher if absolutely desperate
    
    # Final check against budget
    bid = min(bid, my_budget)

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    DAYS_IN_EPISODE = 10 

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to secure water
    if num_alive_opponents == 0:
        return min(my_budget, 0.1) # Minimum positive bid

    days_remaining = DAYS_IN_EPISODE - current_day + 1
    
    # Determine base bid based on HP and remaining days, acknowledging high competition
    base_bid = DAILY_SALARY * 1.05 # Default competitive bid, slightly above salary

    # Increase bid urgency if HP is low or it's late in the game
    if my_hp <= 3: # Critical HP, must win
        base_bid = DAILY_SALARY * 1.5 # Very aggressive
    elif my_hp <= 6 and days_remaining <= 3: # Low HP and late game
        base_bid = DAILY_SALARY * 1.3 # Aggressive
    elif my_hp <= 6: # Moderate HP
        base_bid = DAILY_SALARY * 1.15 # Moderately aggressive
    # If HP is high (7-10), stick to base_bid of 1.05 * DAILY_SALARY to conserve budget

    # Adjust bid based on yesterday's highest bid from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Always try to outbid the highest previous bid, especially given water scarcity
        
        if my_hp <= 3: # If HP is critical, ensure I outbid by a larger margin
            bid_target = max(base_bid, highest_prev_bid + 10)
        else:
            bid_target = max(base_bid, highest_prev_bid + 1) # Slight outbid
    else:
        # No previous bids (e.g., Day 1 or all opponents failed yesterday)
        bid_target = base_bid

    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, bid_target)

    # Ensure a positive bid if budget allows
    if final_bid <= 0:
        return 0.1 # Minimum bid to stay in game

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

    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    days_remaining = EPISODE_DAYS - day_context['day']

    bid_amount = 0.0

    # In this scenario (supply 15-25, WATER_REQ 13), only one agent gets their full water requirement.
    # It's a winner-take-all situation for the water.

    if my_hp <= 2: # Critical HP, must win
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            bid_amount = max(highest_prev_bid + 5.0, DAILY_SALARY * 0.95)
        else:
            bid_amount = DAILY_SALARY * 0.9
    elif my_hp == 3: # Moderate HP, need water soon but can afford some risk
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            bid_amount = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.75)
        else:
            bid_amount = DAILY_SALARY * 0.7
    else: # High HP (4 or 5), can afford to miss a day
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # If opponents are bidding very high, and I have good HP and days left, consider backing off to save budget
            if highest_prev_bid > DAILY_SALARY * 0.8 and my_hp >= 4 and days_remaining > 2:
                bid_amount = DAILY_SALARY * 0.4
            else:
                bid_amount = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.55)
        else:
            bid_amount = DAILY_SALARY * 0.5

    bid_amount = min(bid_amount, my_budget)
    bid_amount = max(bid_amount, 1.0)
    
    return bid_amount
"""
