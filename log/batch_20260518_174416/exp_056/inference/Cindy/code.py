# ============================================================
# Experiment: exp_056
# Agent: Cindy
# Source: exp_056
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    CRITICAL_HP_THRESHOLD = 2
    HIGH_HP_THRESHOLD = 4

    # 1. Opponent Analysis
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    yesterday_bids = []
    total_opponent_water_req = 0

    for opp in alive_opponents:
        total_opponent_water_req += opp['water_requirement']
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # 2. Determine Urgency (My HP)
    my_bid = 0.0
    if my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        my_bid = MY_DAILY_SALARY * 0.95  # Critical, bid very high
    elif my_status['hp'] <= HIGH_HP_THRESHOLD:
        my_bid = MY_DAILY_SALARY * 0.75  # High urgency
    else:
        my_bid = MY_DAILY_SALARY * 0.6   # Default base bid

    # 3. Adjust for Supply and Opponent Behavior
    current_supply = day_context['supply']
    total_water_needed_by_all = MY_WATER_REQ + total_opponent_water_req

    # If supply is less than my requirement (highly unlikely with current params, but for robustness)
    if current_supply < MY_WATER_REQ:
        my_bid = max(my_bid, MY_DAILY_SALARY * 0.99) # Bid almost everything for survival

    # If supply is scarce for everyone (total demand > supply)
    elif current_supply < total_water_needed_by_all:
        my_bid = max(my_bid, MY_DAILY_SALARY * 0.7) # Ensure a strong base for competition
        if yesterday_bids:
            max_yesterday_bid = max(yesterday_bids)
            my_bid = max(my_bid, max_yesterday_bid + 2) # Try to outbid yesterday's max
        elif num_alive_opponents > 0: # No yesterday's bids, but still competition expected
            my_bid = max(my_bid, MY_DAILY_SALARY * 0.75)

    # If supply is relatively abundant (supply >= total demand)
    else: # current_supply >= total_water_needed_by_all
        if num_alive_opponents == 0:
            my_bid = MY_DAILY_SALARY * 0.1 # No competition, bid low but enough
        else:
            if yesterday_bids:
                avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids)
                # Try to bid lower than average if supply is abundant and competition was not fierce
                my_bid = min(my_bid, avg_yesterday_bid * 0.8)
            my_bid = max(my_bid, MY_DAILY_SALARY * 0.2) # Ensure a minimum bid even if supply is high

    # 4. Final Adjustments
    my_bid = min(my_status['budget'], my_bid)
    my_bid = max(1.0, my_bid) # Ensure positive bid

    return my_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = 0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    # Calculate available water units
    available_water_units = int(day_context['supply'] // WATER_REQ)

    # Determine base bid
    base_bid = DAILY_SALARY * 0.5 # A moderate bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical health
        # Bid very aggressively to ensure water
        if max_prev_bid > 0:
            bid = max(max_prev_bid + 5, DAILY_SALARY * 0.8)
        else:
            bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4: # Low health
        # Bid aggressively
        if max_prev_bid > 0:
            bid = max(max_prev_bid + 2, DAILY_SALARY * 0.7)
        else:
            bid = DAILY_SALARY * 0.75
    else: # Healthy
        # Adjust bid based on competition and supply
        if num_alive_opponents >= available_water_units: # High competition or just enough for everyone
            if max_prev_bid > 0:
                bid = max(max_prev_bid + 1, DAILY_SALARY * 0.6)
            else:
                bid = DAILY_SALARY * 0.65
        else: # Low competition or enough water for more than everyone
            if max_prev_bid > 0:
                # Try to bid slightly above the highest previous bid, but not too high
                bid = max(base_bid, max_prev_bid + 0.5)
            else:
                bid = base_bid

    # Ensure bid does not exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least 1 if budget allows and I need water (and bid was 0)
    if bid <= 0 and my_status['budget'] > 0 and my_status['hp'] <= 5:
        bid = min(my_status['budget'], 1.0)

    return bid
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

    # Rule 1: No active opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Rule 2: Low HP, prioritize survival aggressively
    if my_status['hp'] <= 2:
        # Bid very aggressively to secure water. Increase urgency towards end of game.
        survival_bid = DAILY_SALARY * 1.2 + (EPISODE_DAYS - current_day) * 5
        return min(my_status['budget'], survival_bid)

    # Analyze yesterday's bids from alive opponents
    yesterday_bids = []
    david_bid_yesterday = 0
    david_is_alive = False

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            if opp_id == "David":
                david_is_alive = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
                if opp_id == "David":
                    david_bid_yesterday = prev['bid']

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # Calculate remaining days for end-game adjustments
    remaining_days = EPISODE_DAYS - current_day + 1

    # Base bid strategy: Moderate bid, adjusted for end-game
    base_bid = DAILY_SALARY * 0.5
    if remaining_days <= 3: # Last few days, increase urgency
        base_bid = DAILY_SALARY * 0.7
    
    # Adjust bid based on highest previous bid and David's behavior (from previous_trace)
    if david_is_alive and david_bid_yesterday > DAILY_SALARY * 0.75: # David was very aggressive yesterday
        # If David is bidding high, I need to be competitive.
        # Especially if supply is tight.
        if current_supply < WATER_REQ * (len(alive_opponents) + 1): # Supply is tight relative to demand
            target_bid = max(base_bid, david_bid_yesterday * 1.05) # Slightly outbid David
            return min(my_status['budget'], target_bid)
        else:
            target_bid = max(base_bid, david_bid_yesterday * 0.95) # Match David closely but try to save
            return min(my_status['budget'], target_bid)
    elif highest_prev_bid > DAILY_SALARY * 0.6: # Any opponent bid relatively high yesterday
        target_bid = max(base_bid, highest_prev_bid + 5) # Slightly outbid to secure water
        return min(my_status['budget'], target_bid)

    # Further adjust bid based on supply relative to total water needed by active players + me
    total_water_needed = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    if current_supply < total_water_needed: # Supply is less than total needed, high competition
        scarce_factor = 1.0 + (total_water_needed - current_supply) / total_water_needed
        final_bid = base_bid * scarce_factor * 1.1 # Boost bid significantly
    elif current_supply >= total_water_needed + WATER_REQ: # Abundant supply
        final_bid = base_bid * 0.7 # Reduce bid to save budget
    else:
        final_bid = base_bid # Moderate bid for balanced supply

    # Ensure bid is never negative or exceeds budget, and has a minimum threshold
    return min(my_status['budget'], max(final_bid, DAILY_SALARY * 0.15))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6 # Default competitive bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            base_bid = highest_prev_bid + 5.0 # Try to outbid aggressive opponents
        else:
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Be competitive

    bid_amount = base_bid

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid_amount = DAILY_SALARY * 0.95 # Critical, bid very aggressively
    elif my_status['hp'] <= 5:
        bid_amount = max(base_bid * 1.1, DAILY_SALARY * 0.75) # Low HP, aggressive
    else:
        if day_context['supply'] >= WATER_REQ * num_alive_opponents:
            bid_amount = max(base_bid * 0.9, DAILY_SALARY * 0.5) # Ample supply, conserve
        else:
            bid_amount = max(base_bid * 1.05, DAILY_SALARY * 0.65) # Competition, competitive

    if day_context['day'] == EPISODE_DAYS:
        if my_status['hp'] > 0:
            if my_status['hp'] < 10 or my_status['no_water_days'] > 0:
                bid_amount = my_status['budget'] * 0.99 # Go almost all in on last day if needed
            else:
                bid_amount = DAILY_SALARY * 0.5 # Moderate bid if healthy on last day
        else:
            bid_amount = 0.0 # Already dead, bid 0

    final_bid = max(1.0, min(my_status['budget'], bid_amount))

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
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) 

    my_base_bid = DAILY_SALARY * 0.85 

    if my_status['no_water_days'] > 0:
        my_base_bid = DAILY_SALARY * 1.15
    elif my_status['hp'] <= 2:
        my_base_bid = DAILY_SALARY * 1.25
    elif my_status['hp'] <= 4:
        my_base_bid = DAILY_SALARY * 1.05
    elif my_status['hp'] >= 8:
        my_base_bid = DAILY_SALARY * 0.75

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 1.0:
            if my_status['hp'] <= 4 or my_status['no_water_days'] > 0:
                my_base_bid = max(my_base_bid, highest_prev_bid + 5)
            else:
                my_base_bid = max(my_base_bid, highest_prev_bid * 0.95)
        
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            my_base_bid = max(my_base_bid, highest_prev_bid + 2)
            if my_status['hp'] >= 8:
                my_base_bid = min(my_base_bid, DAILY_SALARY * 0.9)
        
        else:
            if my_status['hp'] > 4 and my_status['no_water_days'] == 0:
                my_base_bid = min(my_base_bid, highest_prev_bid + 1)
            else:
                my_base_bid = max(my_base_bid, highest_prev_bid + 5)

    water_units_available = day_context['supply']
    num_total_competitors = len(alive_opponents) + 1
    max_people_to_satisfy_fully = int(water_units_available / WATER_REQ)

    if num_total_competitors > max_people_to_satisfy_fully:
        if my_status['hp'] <= 4 or my_status['no_water_days'] > 0:
            my_base_bid *= 1.05
        else:
            my_base_bid *= 1.02
    elif num_total_competitors <= max_people_to_satisfy_fully and num_total_competitors > 0:
        if my_status['hp'] >= 8 and my_status['no_water_days'] == 0:
            my_base_bid *= 0.95
        else:
            my_base_bid *= 0.98

    final_bid = min(my_base_bid, my_status['budget'])
    final_bid = max(1, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    base_bid = DAILY_SALARY * 0.9

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 1.1
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 1.0

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_status['hp'] <= 3:
                base_bid = max(base_bid, highest_prev_bid + 5)
            else:
                base_bid = max(base_bid, highest_prev_bid * 1.0)
        elif highest_prev_bid < DAILY_SALARY * 0.5 and my_status['hp'] > 4:
            base_bid = min(base_bid, DAILY_SALARY * 0.6)

    num_active_opponents = len(alive_opponents)
    if num_active_opponents >= 3:
        base_bid *= 1.05
    elif num_active_opponents == 1 and my_status['hp'] > 5:
        base_bid *= 0.98

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3 and my_status['hp'] > 0:
        base_bid = max(base_bid, DAILY_SALARY * 1.15)

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(0.0, final_bid)

    if my_status['budget'] <= 0:
        return 0.0

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    DAYS_IN_EPISODE = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid a minimal amount to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) if my_status['budget'] > 0 else 0.0

    # Calculate highest bid from yesterday among alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid
    base_bid = DAILY_SALARY * 0.8 # A reasonable starting point

    # Adjust base bid based on yesterday's highest bid to stay competitive
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        competitive_bid = highest_prev_bid + 5.0 # Add a small increment to try and win
        base_bid = max(base_bid, competitive_bid)

    # Adjust bid further based on my HP and remaining days, prioritizing survival
    days_remaining = DAYS_IN_EPISODE - day_context['day'] + 1 # Including current day

    if my_status['hp'] <= 2 or days_remaining <= 2: # Critical state: very low HP or last few days
        # Bid very aggressively to survive
        base_bid = max(base_bid, DAILY_SALARY * 1.2)
    elif my_status['hp'] <= 5: # Moderate HP, still need water strongly
        # Bid strongly
        base_bid = max(base_bid, DAILY_SALARY * 1.0)
    else: # Good HP, can be slightly less aggressive but still competitive
        base_bid = max(base_bid, DAILY_SALARY * 0.9) # Default strong bid

    # Ensure the bid does not exceed current budget and is at least 1.0 if budget allows
    bid = min(my_status['budget'], base_bid)
    return max(1.0, bid) if my_status['budget'] > 0 else 0.0
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid conservatively to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on my health
    if my_hp <= 2: # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need it today
        base_bid = DAILY_SALARY * 0.8
    elif my_hp <= 4 and current_day > EPISODE_DAYS / 2: # Mid-late game, somewhat low HP
        base_bid = DAILY_SALARY * 0.75
    
    # Adjust bid based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, react strongly
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp <= 3: # If I'm in trouble, I must try to win
                base_bid = max(base_bid, highest_prev_bid + 5) # Slightly outbid
            else: # If healthy, I can be slightly less aggressive
                base_bid = max(base_bid, highest_prev_bid * 0.95)
        elif highest_prev_bid > base_bid * 0.8: # If previous bid was moderately high
            base_bid = max(base_bid, highest_prev_bid + 2) # Slightly outbid to secure water

    # Ensure bid doesn't exceed current budget
    final_bid = min(my_budget, base_bid)

    # Ensure a minimum bid if I need water and have budget, even if calculated bid is low
    if final_bid == 0 and my_budget > 0 and my_hp <= 3:
        final_bid = min(my_budget, 1.0)
    
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents)

    # If no competitors, bid minimally to secure water
    if num_competitors == 0:
        return min(my_status['budget'], 1)

    # Base bid strategy: high bids are necessary because supply is very tight
    bid_percentage = 0.5 # Default moderate bid percentage

    if my_status['hp'] <= 2: # Critical HP, must win
        bid_percentage = 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid_percentage = 0.85
    elif my_status['hp'] <= 6: # Medium HP
        bid_percentage = 0.7
    else: # Healthy HP
        bid_percentage = 0.55 # Still need to bid relatively high due to tight supply

    # Adjust for day progression (become more aggressive late in the game)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days, survival is key
        bid_percentage = max(bid_percentage, 0.9)
    elif remaining_days <= 4: # Mid-late game
        bid_percentage = max(bid_percentage, 0.75)

    base_bid = DAILY_SALARY * bid_percentage

    # Adjust bid based on opponent's previous highest bid
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid is higher than my current base, I might need to exceed it.
        # Add a small buffer to try and win.
        if highest_prev_bid >= base_bid:
            base_bid = highest_prev_bid + 2 # Bid slightly higher than the highest opponent bid
        # If my base_bid is already higher, no need to adjust upwards based on opponent's lower bid.

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # If budget is very low and HP is critical, just bid all remaining budget
    if my_status['hp'] <= 2 and my_status['budget'] < DAILY_SALARY * 0.6: # If budget is tight and HP critical
        final_bid = my_status['budget']

    # Ensure bid is at least 1 to participate and win if possible
    return max(1, final_bid)
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
    num_alive_opponents = len(alive_opponents)

    # My maximum value for water, capped by budget
    my_max_value_for_water = min(my_budget, DAILY_SALARY)

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, WATER_REQ * 0.1) 

    # Collect yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0
    avg_yesterday_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0

    # Calculate total water requirement from all players
    total_water_demand = WATER_REQ # My demand
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # --- Bidding Logic ---
    bid = WATER_REQ * 8 # Default base bid

    # 1. Survival mode: If HP is critically low or no water for days
    if my_hp <= 2 or my_no_water_days >= 1:
        # Bid very aggressively, ensuring I get water.
        bid = max(max_yesterday_bid + 10, my_max_value_for_water * 0.95)
        return min(my_budget, bid)

    # 2. Late game pressure: If it's near the end of the episode
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        # Be more aggressive to ensure survival till the end
        bid = max(max_yesterday_bid + 5, my_max_value_for_water * 0.85)
        return min(my_budget, bid)

    # 3. Scarcity vs. Abundance
    # Check if supply is tight (less than what all active players need)
    if current_supply < total_water_demand * 0.8: # Supply is less than 80% of total demand
        # High competition expected due to scarcity
        bid = max(avg_yesterday_bid * 1.1, max_yesterday_bid + 2)
        bid = max(bid, my_max_value_for_water * 0.7) # Ensure a decent bid based on my value
    elif current_supply < total_water_demand: # Supply is less than total demand, but not extremely tight
        # Moderate competition
        bid = max(avg_yesterday_bid * 1.05, max_yesterday_bid + 1)
        bid = max(bid, my_max_value_for_water * 0.6)
    else: # Supply is abundant (equal or more than total demand)
        # Less competition, can be more conservative
        bid = max(avg_yesterday_bid * 0.9, WATER_REQ * 5) # Bid slightly below avg, or a solid minimum
        bid = min(bid, my_max_value_for_water * 0.5) # Don't overbid if not necessary

    # 4. General adjustment based on opponent aggressiveness
    # If max_yesterday_bid was already very high, I might need to slightly exceed it
    if max_yesterday_bid > my_max_value_for_water * 0.7:
        bid = max(bid, max_yesterday_bid + 1)

    # Ensure bid is at least a minimal competitive amount
    bid = max(bid, WATER_REQ * 1) # At least 1 per unit
    
    # Final check: Don't bid more than budget.
    return min(my_budget, bid)
"""
