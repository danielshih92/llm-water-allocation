# ============================================================
# Experiment: exp_033
# Agent: Cindy
# Source: exp_033
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    current_supply = day_context['supply']
    current_day = day_context['day']

    # 1. Emergency Bidding (Low HP or high no_water_days)
    # If I'm very low on HP or have missed water for too many days, bid almost everything for survival.
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= EPISODE_DAYS - 2:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.95)

    # 2. Analyze opponent's yesterday's bids and water requirements
    yesterday_bids = []
    min_opponent_water_req = float('inf')
    total_opponent_water_req = 0

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
        
        if opp['water_requirement'] < min_opponent_water_req:
            min_opponent_water_req = opp['water_requirement']
        total_opponent_water_req += opp['water_requirement']

    highest_prev_opp_bid = 0
    if yesterday_bids:
        highest_prev_opp_bid = max(yesterday_bids)

    # If no opponents, bid minimum to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.3) # Very conservative bid

    # 3. Dynamic Bidding based on Supply and Competition
    bid = MY_DAILY_SALARY * 0.5 # Default moderate bid

    # Determine competition level based on supply vs demand
    if num_alive_opponents > 0:
        # If supply can cover everyone's needs (including mine)
        if current_supply >= MY_WATER_REQ + total_opponent_water_req:
            bid = MY_DAILY_SALARY * 0.4 # Low competition
        # If supply can cover my needs and at least one other opponent's smallest need
        elif current_supply >= MY_WATER_REQ + min_opponent_water_req:
            bid = MY_DAILY_SALARY * 0.6 # Moderate competition
        # If supply is just enough for me, or me and very little for others (high competition for my full req)
        elif current_supply >= MY_WATER_REQ: # This condition is always true given supply range [15, 25] and my_water_req 13
            bid = MY_DAILY_SALARY * 0.8 # High competition
    else:
        # Should be covered by the num_alive_opponents == 0 check above, but as a fallback
        bid = MY_DAILY_SALARY * 0.4

    # Further adjust based on opponent's previous highest bid and my recent performance
    if highest_prev_opp_bid > 0:
        # If my current calculated bid is lower than their highest yesterday, try to beat it slightly.
        if bid < highest_prev_opp_bid + 1:
            bid = max(bid, highest_prev_opp_bid + 1)
        
        # If I failed to get water yesterday (no_water_days increased), become more aggressive
        # only if it's not the very first day (day > 1).
        if my_status['no_water_days'] > 0 and current_day > 1:
             bid = max(bid, highest_prev_opp_bid + 5) # Significantly increase bid to secure water

    # If it's late in the game and I haven't gotten water, increase bid
    if current_day >= EPISODE_DAYS - 2 and my_status['no_water_days'] > 0:
        bid = max(bid, MY_DAILY_SALARY * 0.9)

    # Final check: Don't bid more than budget
    final_bid = min(my_status['budget'], bid)
    
    # Ensure bid is at least 1 if I need water and can afford it
    if MY_WATER_REQ > 0 and my_status['budget'] > 0:
        final_bid = max(1.0, final_bid)

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
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1 if my_budget >= DAILY_SALARY * 0.1 else 1.0)

    days_left = EPISODE_DAYS - current_day + 1
    
    if my_hp <= 3 or my_no_water_days >= 1:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 6:
        base_bid = DAILY_SALARY * 0.7
    else:
        base_bid = DAILY_SALARY * 0.5

    highest_relevant_opp_bid_yesterday = 0.0
    
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                if prev_trace['bid'] > 0:
                    highest_relevant_opp_bid_yesterday = max(highest_relevant_opp_bid_yesterday, prev_trace['bid'])
            
            if opp['hp'] <= 2 or opp['no_water_days'] >= 1:
                highest_relevant_opp_bid_yesterday = max(highest_relevant_opp_bid_yesterday, opp['daily_salary'] * 0.9)

    total_water_needed = WATER_REQ 
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']
    
    if supply < total_water_needed / 2:
        if my_hp <= 5 or my_no_water_days >= 1:
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)
    elif supply < total_water_needed:
        if my_hp <= 7 or my_no_water_days >= 1:
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    else:
        if my_hp > 8 and my_no_water_days == 0:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.5)

    if highest_relevant_opp_bid_yesterday > 0:
        if my_hp <= 6 or my_no_water_days >= 1:
            base_bid = max(base_bid, highest_relevant_opp_bid_yesterday + 5)
        else:
            base_bid = max(base_bid, highest_relevant_opp_bid_yesterday + 1)
    
    if days_left <= 2:
        if my_hp < 10:
            base_bid = max(base_bid, DAILY_SALARY * 0.95)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)
    elif days_left <= 4:
        if my_hp < 8:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    final_bid = min(my_budget, base_bid)

    if final_bid <= 0.0 and my_budget > 0:
        final_bid = min(my_budget, 1.0)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_to_make = DAILY_SALARY * 0.55 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.9: # Opponents were very aggressive
            if my_status['hp'] > 5: # HP is relatively good, can be competitive but save budget
                bid_to_make = max(DAILY_SALARY * 0.6, highest_prev_bid * 0.9)
            else: # HP is critical, must win
                bid_to_make = max(highest_prev_bid + 5, DAILY_SALARY * 1.05)
        else: # Opponents were moderately or less aggressive
            bid_to_make = max(DAILY_SALARY * 0.55, highest_prev_bid + 2)

    remaining_days = EPISODE_DAYS - day_context['day']

    # Desperation logic based on HP
    if my_status['hp'] <= 3:
        bid_to_make = max(bid_to_make, DAILY_SALARY * 1.1)
    elif my_status['hp'] <= 5 and remaining_days <= 2:
        bid_to_make = max(bid_to_make, DAILY_SALARY * 1.2)

    # Adjust for supply scarcity
    num_slots = int(day_context['supply'] // WATER_REQ)
    total_competitors_needing_water = num_alive_opponents + 1

    if num_slots < total_competitors_needing_water:
        if my_status['hp'] <= 6:
            bid_to_make = max(bid_to_make, DAILY_SALARY * 0.95)
        elif my_status['hp'] > 6 and remaining_days <= 5:
            bid_to_make = max(bid_to_make, DAILY_SALARY * 0.75)
    elif num_slots >= total_competitors_needing_water and num_alive_opponents > 0:
        # Water is abundant, can bid lower to save budget
        bid_to_make = min(bid_to_make, DAILY_SALARY * 0.45)
        if yesterday_bids:
            bid_to_make = min(bid_to_make, max(DAILY_SALARY * 0.3, min(yesterday_bids) + 1))

    final_bid = min(my_status['budget'], bid_to_make)

    # Ensure a minimum bid if budget allows, to stay in contention
    if final_bid < DAILY_SALARY * 0.3 and my_status['budget'] >= DAILY_SALARY * 0.3:
        final_bid = DAILY_SALARY * 0.3

    # Aggressive play if significantly ahead in budget and HP
    if my_status['budget'] > DAILY_SALARY * 5 and my_status['hp'] > 7 and day_context['day'] < EPISODE_DAYS - 1:
        if yesterday_bids:
            final_bid = min(my_status['budget'], max(final_bid, highest_prev_bid + 10))
        else:
            final_bid = min(my_status['budget'], max(final_bid, DAILY_SALARY * 0.8))

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o_id, o in opponents_status.items() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    days_left = EPISODE_DAYS - int(current_day)

    base_bid = DAILY_SALARY * 0.8 

    critical_hp_threshold = 3
    if my_hp <= critical_hp_threshold:
        hp_urgency_factor = 1.0 + (critical_hp_threshold - my_hp) * 0.15 
        bid = DAILY_SALARY * hp_urgency_factor
        
        if days_left <= 3 and my_budget > DAILY_SALARY * 2:
             bid = max(bid, DAILY_SALARY * 1.2)
        return min(my_budget, bid)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    if highest_prev_bid > DAILY_SALARY * 0.9:
        base_bid = max(base_bid, highest_prev_bid + 5)
    elif highest_prev_bid > DAILY_SALARY * 0.7:
        base_bid = max(base_bid, highest_prev_bid + 2)

    water_per_agent_if_shared = current_supply / (num_alive_opponents + 1)

    if water_per_agent_if_shared < WATER_REQ:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
        if days_left <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 1.05)
    elif current_supply >= WATER_REQ * (num_alive_opponents + 1):
        base_bid = min(base_bid, DAILY_SALARY * 0.7)

    final_bid = min(my_budget, base_bid)

    if final_bid < DAILY_SALARY * 0.1 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)
    elif my_budget == 0:
        final_bid = 0

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
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid a minimal amount to secure water cheaply
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Calculate remaining days
    remaining_days = EPISODE_DAYS - day_context['day']

    # Get yesterday's highest bid from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy
    # Default to a moderate bid
    bid_amount = DAILY_SALARY * 0.5

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP: Must get water
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP: High priority to get water
        bid_amount = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8 and remaining_days > 2: # High HP, not desperate, can save budget
        bid_amount = DAILY_SALARY * 0.4
    
    # Adjust bid based on opponent behavior from yesterday
    # If highest_prev_bid was very high, it indicates aggressive competition
    if highest_prev_bid > DAILY_SALARY * 0.7:
        if my_status['hp'] <= 4: # I need water, so try to outbid
            bid_amount = max(bid_amount, highest_prev_bid + 5)
        else: # I have some buffer, maybe let them overspend if supply is tight
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6) # Ensure it's not too low
    elif highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 0.4: # Opponents were conservative
        # Try to secure water slightly above their low bid if I need it
        if my_status['hp'] <= 6: # Need water or want to secure it cheaply
            bid_amount = max(bid_amount, highest_prev_bid + 10)
        else: # High HP, can also be conservative
            bid_amount = min(bid_amount, DAILY_SALARY * 0.5)

    # Adjust bid based on supply vs. demand
    # `potential_winners` is the maximum number of agents who can get their full water requirement
    potential_winners = int(day_context['supply'] // WATER_REQ)
    
    if num_alive_opponents + 1 > potential_winners: # Competition for water is high
        if my_status['hp'] <= 4: # Critical need, bid very high
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 6: # Moderate need, bid high
            bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
        else: # High HP, can take a risk or conserve budget
            bid_amount = min(bid_amount, DAILY_SALARY * 0.65) # Still competitive but not overpaying
    else: # Enough water for everyone, can bid lower
        bid_amount = min(bid_amount, DAILY_SALARY * 0.6) # Don't need to overbid

    # Ensure bid doesn't exceed budget and is non-negative
    final_bid = min(my_status['budget'], bid_amount)
    
    # Ensure a minimum bid if budget allows and water is needed
    if my_status['hp'] < 10 and my_status['budget'] > 0 and final_bid < 10:
        final_bid = max(final_bid, 10.0)
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    current_day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # In this specific scenario (WATER_REQ=13, supply_range=[15,25]), only 1 agent can get water.
    # This implies high competition.

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Calculate highest yesterday's bid
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Bidding Strategy ---
    bid = 0.0

    # Phase 1: Extreme Desperation (My HP is critically low)
    if my_hp <= 2:
        # If it's the last day, bid everything
        if current_day == EPISODE_DAYS:
            bid = my_budget
        else:
            # Bid very aggressively to ensure survival
            aggressive_bid_base = DAILY_SALARY * 1.05 # Slightly more than salary to outbid others
            
            if highest_prev_bid > 0:
                bid = max(aggressive_bid_base, highest_prev_bid + 5.0)
            else:
                bid = aggressive_bid_base
            
            # If truly desperate (HP=1), bid even higher if budget allows
            if my_hp == 1:
                 bid = max(bid, DAILY_SALARY * 1.5)

    # Phase 2: Moderate Desperation (My HP is getting low)
    elif my_hp <= 4:
        # Aim to win, but with slightly less aggression than extreme desperation
        moderate_bid_base = DAILY_SALARY * 0.8
        
        if highest_prev_bid > 0:
            bid = max(moderate_bid_base, highest_prev_bid + 2.0)
        else:
            bid = moderate_bid_base

    # Phase 3: Comfortable HP (My HP is good)
    else:
        # Try to win if possible without overspending, conserve budget
        
        # If no opponents are alive, bid minimum to win
        if not alive_opponents:
            bid = DAILY_SALARY * 0.1 # Very low bid to conserve if no competition
        else:
            # Estimate a competitive bid
            competitive_bid_base = DAILY_SALARY * 0.6
            
            if highest_prev_bid > 0:
                bid = max(competitive_bid_base, highest_prev_bid + 1.0)
            else:
                bid = competitive_bid_base
            
            # If budget is very high and HP is good, be slightly more competitive
            if my_budget > DAILY_SALARY * 3 and my_hp > 6:
                bid = max(bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed current budget and is non-negative
    final_bid = min(my_budget, bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    # 1. Initialize bid based on my HP (primary survival factor)
    if my_status['hp'] <= 2:
        my_bid = DAILY_SALARY * 0.95 # Very desperate
    elif my_status['hp'] <= 4:
        my_bid = DAILY_SALARY * 0.75 # Needs water soon
    else:
        my_bid = DAILY_SALARY * 0.5 # Can afford to be more conservative

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # 2. Adjust bid based on opponent's previous behavior (exploitation of previous_trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        
        if max_prev_bid >= DAILY_SALARY * 0.85: # High competition detected
            # If I'm also desperate (low HP), ensure I outbid
            if my_status['hp'] <= 3: 
                my_bid = max(my_bid, max_prev_bid + 5) 
            # If my HP is good, I might try to save, but still need to be competitive
            else: 
                my_bid = max(my_bid, max_prev_bid * 0.95) # Bid slightly below, hoping others overbid
        elif max_prev_bid >= DAILY_SALARY * 0.6: # Moderate competition
            my_bid = max(my_bid, max_prev_bid + 2) # Slightly outbid
        else: # Low previous bids, perhaps opponents are saving or not desperate
            my_bid = max(my_bid, max_prev_bid * 1.1) # Be competitive, slightly above their last bid
    else:
        # If no previous bids from opponents, use a default competitive bid based on my status
        if my_status['hp'] <= 2:
            my_bid = DAILY_SALARY * 0.9
        elif day_context['day'] >= EPISODE_DAYS - 2:
            my_bid = DAILY_SALARY * 0.8
        else:
            my_bid = DAILY_SALARY * 0.5

    # 3. End-game adjustment (overrides other logic if critical)
    if day_context['day'] >= EPISODE_DAYS - 2: 
        my_bid = max(my_bid, DAILY_SALARY * 0.98) # Bid very high to ensure survival in final days

    # 4. Supply-based adjustment (fine-tuning)
    num_potential_winners = int(day_context['supply'] // WATER_REQ) 
    num_active_players = len(alive_opponents) + 1 # Including myself

    if num_potential_winners == 0: # Extremely low supply, almost impossible to win
        my_bid = max(my_bid, DAILY_SALARY * 0.99) # Bid extremely high if desperate
    elif num_potential_winners < num_active_players: # Supply is tight
        my_bid *= 1.05 # Increase bid slightly
    elif num_potential_winners >= num_active_players: # Plenty of supply for everyone
        my_bid *= 0.95 # Decrease bid slightly

    # 5. Ensure bid is within budget and positive
    my_bid = min(my_status['budget'], my_bid)
    my_bid = max(1.0, my_bid) 

    return my_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid, adjusted by health and supply
    bid = DAILY_SALARY * 0.55 # Moderate starting bid

    # Aggressiveness based on HP
    if my_status['hp'] <= 2:
        bid = DAILY_SALARY * 0.95 # Very aggressive
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: # If very healthy, can afford to be less aggressive
        bid = DAILY_SALARY * 0.45

    # Adjust based on supply scarcity
    # If supply is low, increase bid. If high, decrease.
    supply_midpoint = (MIN_SUPPLY + MAX_SUPPLY) / 2
    if day_context['supply'] < supply_midpoint:
        bid *= 1.1 # Increase bid for scarcity
    else:
        bid *= 0.9 # Decrease bid for abundance

    # Analyze opponent's previous bids from their trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest previous bid was very high, we might need to match or slightly exceed
        if highest_prev_bid > DAILY_SALARY * 0.8: # Opponent was very aggressive
            bid = max(bid, highest_prev_bid + 5) # Try to outbid slightly
        elif highest_prev_bid > DAILY_SALARY * 0.6: # Opponent was moderately aggressive
            bid = max(bid, average_prev_bid + 2) # Bid slightly above average

    # Consider number of active opponents
    # More opponents means more competition, so potentially higher bids
    if num_alive_opponents > 1:
        bid *= (1 + (num_alive_opponents - 1) * 0.05) # Increase bid by 5% per additional opponent beyond 1

    # Final day desperation
    if day_context['day'] == EPISODE_DAYS and my_status['hp'] > 0:
        bid = my_status['budget'] * 0.99 # Bid almost everything to survive

    # Ensure bid is positive and within budget
    final_bid = max(1.0, min(bid, my_status['budget']))

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid the minimum necessary
    if num_alive_opponents == 0:
        return max(1.0, min(my_budget, 1.0)) # Bid 1.0 unless budget is less

    # Base bid: Start with a competitive bid, slightly below my salary.
    base_bid = DAILY_SALARY * 0.75 # 112.5

    # Adjust bid based on my HP and recent water acquisition
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 1.2 # Bid very aggressively (180)
    elif my_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 1.0 # Bid aggressively (150)
    elif my_no_water_days >= 1: # Haven't gotten water recently
        base_bid = DAILY_SALARY * 0.9 # (135)

    # Adjust bid based on supply and number of competitors
    # Total water needed if everyone gets their requirement
    total_water_needed_for_all = (num_alive_opponents + 1) * WATER_REQ 

    # If supply is very low relative to demand, increase bid
    if current_supply < total_water_needed_for_all * 0.5: 
        base_bid *= 1.2
    # If supply is just low, increase bid moderately
    elif current_supply < total_water_needed_for_all * 0.8: 
        base_bid *= 1.1
    # If supply is relatively abundant (less competitive), consider lowering the bid slightly
    elif current_supply > total_water_needed_for_all * 1.2:
        base_bid *= 0.9

    # React to yesterday's opponent bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_yesterday_bid = max(yesterday_bids)
        # If opponents bid high, I need to outbid them to secure water
        if highest_yesterday_bid > DAILY_SALARY * 1.0: # Opponents bid above my salary
            base_bid = max(base_bid, highest_yesterday_bid + 10) # Aggressively outbid
        elif highest_yesterday_bid > DAILY_SALARY * 0.9: # Opponents are aggressive
            base_bid = max(base_bid, highest_yesterday_bid + 5) # Try to outbid by a small margin
        elif highest_yesterday_bid > DAILY_SALARY * 0.7: # Opponents are moderately aggressive
            base_bid = max(base_bid, highest_yesterday_bid + 2)
        else: # Opponents bid low, still try to outbid but with minimal increment
            base_bid = max(base_bid, highest_yesterday_bid + 1)

    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 1 to participate
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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.85

    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        base_bid = DAILY_SALARY * 1.25
    elif my_status['hp'] >= 8:
        base_bid = DAILY_SALARY * 0.75

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
            base_bid = max(base_bid, highest_prev_bid + 10)
        else:
            if highest_prev_bid >= DAILY_SALARY * 1.0:
                base_bid = max(base_bid, highest_prev_bid + 2)
            else:
                base_bid = max(base_bid, highest_prev_bid + 1)
    
    if day_context['day'] >= EPISODE_DAYS * 0.7:
        base_bid *= 1.05

    final_bid = min(my_status['budget'], base_bid)

    return max(1.0, final_bid)
"""
