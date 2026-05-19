# ============================================================
# Experiment: exp_014
# Agent: Cindy
# Source: exp_014
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_active_agents = 1 + len(alive_opponents)

    # If I'm the only one left, bid minimally to secure water
    if not alive_opponents:
        return float(min(my_status['budget'], 1))

    current_supply = day_context['supply']
    
    # Calculate an initial bid based on HP urgency
    base_bid = DAILY_SALARY * 0.4 # Default conservative bid

    if my_status['hp'] <= 2: # Critical HP, must get water
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, high urgency
        base_bid = DAILY_SALARY * 0.75
    elif my_status['hp'] <= 6: # Medium HP, moderate urgency
        base_bid = DAILY_SALARY * 0.6
    # Else (HP > 6), use the default conservative base_bid

    # Adjust base_bid further based on supply vs demand
    total_water_needed_by_all = WATER_REQ * num_active_agents
    if current_supply < total_water_needed_by_all:
        # Supply is scarce, increase bid proportionally to scarcity
        scarcity_factor = (total_water_needed_by_all - current_supply) / (WATER_REQ * num_active_agents)
        base_bid = base_bid * (1 + scarcity_factor)
        # Cap the increase to prevent bids from becoming excessively high
        base_bid = min(base_bid, DAILY_SALARY * 0.9)
    
    # Analyze yesterday's bids from opponents to react to their aggression
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents bid very high yesterday, we might need to match or exceed them
        if highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents were aggressive
            if my_status['hp'] <= 4: # If I'm also in a bad state, bid very aggressively
                base_bid = max(base_bid, highest_prev_bid + 5.0) # Try to outbid significantly
            else: # If my HP is good, try to outbid slightly to maintain competitive edge
                base_bid = max(base_bid, highest_prev_bid + 1.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.4: # Opponents were moderately competitive
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Just slightly outbid

    # Ensure bid is at least 1 and does not exceed budget or a reasonable maximum
    final_bid = max(1.0, min(my_status['budget'], base_bid))
    final_bid = min(final_bid, DAILY_SALARY * 0.99) # Cap bid to avoid spending almost all salary unnecessarily
    
    return float(final_bid)
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
    num_active_players = num_alive_opponents + 1 

    base_bid = DAILY_SALARY * 0.65 

    if my_status['hp'] <= 2: 
        base_bid = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] >= 1: 
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 4: 
        base_bid = DAILY_SALARY * 0.75

    available_water_units = int(day_context['supply'] / WATER_REQ)

    if available_water_units < num_active_players: 
        if my_status['hp'] <= 3: 
            base_bid = DAILY_SALARY * 0.98
        else: 
            base_bid = max(base_bid, DAILY_SALARY * 0.8) 
            base_bid *= 1.1 
    elif available_water_units >= num_active_players + 1: 
        if my_status['hp'] > 5: 
            base_bid *= 0.7
        else: 
            base_bid *= 0.85

    highest_prev_bid = 0.0
    for agent_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                highest_prev_bid = max(highest_prev_bid, prev['bid'])

    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: 
            if my_status['hp'] <= 3: 
                base_bid = max(base_bid, highest_prev_bid + 10)
            else: 
                base_bid = max(base_bid, highest_prev_bid + 2)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: 
            if my_status['hp'] <= 5: 
                base_bid = max(base_bid, highest_prev_bid + 1)
            else: 
                base_bid = max(base_bid, highest_prev_bid * 1.05)
    else: 
        if day_context['day'] <= 2 and my_status['hp'] > 5:
            base_bid = min(base_bid, DAILY_SALARY * 0.55)
        elif my_status['hp'] <= 3: 
            base_bid = DAILY_SALARY * 0.9

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: 
        if my_status['hp'] <= 5: 
            base_bid = max(base_bid, DAILY_SALARY * 0.98)
        elif my_status['budget'] > DAILY_SALARY * 2 and my_status['hp'] < 10: 
            base_bid = max(base_bid, DAILY_SALARY * 0.9)

    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(1.0, final_bid)

    return float(final_bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From Current Meta-Round State

    my_water_requirement = WATER_REQ
    my_daily_salary = DAILY_SALARY

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Default bid if no specific strategy applies
    base_bid = my_daily_salary * 0.5 # 75

    # Strategy 1: If no opponents are alive, bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], my_daily_salary * 0.1)

    # Strategy 2: If my HP is critically low, bid very aggressively.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], my_daily_salary * 0.95) # 142.5

    # Strategy 3: Analyze yesterday's opponent bids to gauge competition pressure.
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    current_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very high, it indicates strong competition or desperation.
        if highest_prev_bid >= my_daily_salary * 0.8: # e.g., >= 120
            # If my HP is good, try to outbid slightly, but don't overspend too early.
            if my_status['hp'] > 5:
                current_bid = max(base_bid, highest_prev_bid * 0.9 + 5) # Try to stay competitive, but save
            else: # My HP is getting low, need to be more aggressive
                current_bid = max(base_bid, highest_prev_bid * 1.05 + 5) # Outbid them
        # If highest previous bid was moderate
        elif highest_prev_bid >= my_daily_salary * 0.5: # e.g., >= 75
            if my_status['hp'] > 5:
                current_bid = max(base_bid, highest_prev_bid * 0.9 + 2) # Slightly below or match, save
            else:
                current_bid = max(base_bid, highest_prev_bid + 5) # Slightly above
        # If highest previous bid was low, we can afford to bid lower or base
        else:
            current_bid = max(base_bid * 0.8, highest_prev_bid + 1) # Bid slightly above their low bid, but not too high

    # Further adjustment based on my HP, regardless of opponent's yesterday bids
    if my_status['hp'] <= 5: # If HP is getting low (3, 4, 5)
        current_bid = max(current_bid, my_daily_salary * 0.7) # Ensure a strong bid (105)

    # Day progression adjustment: Become more aggressive towards the end of the game
    if day_context['day'] >= (EPISODE_DAYS - 2): # Last 3 days (day 8, 9, 10)
        current_bid = max(current_bid, my_daily_salary * 0.8) # Bid very aggressively (120)
    elif day_context['day'] >= (EPISODE_DAYS - 4): # Mid-late game (day 6, 7)
        current_bid = max(current_bid, my_daily_salary * 0.65) # Increase bid somewhat (97.5)

    # Ensure the bid does not exceed the current budget.
    return min(my_status['budget'], current_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    eric_alive = False
    eric_status = None
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_id == "Eric":
            eric_alive = True
            eric_status = opp_data
            break

    # Default bid: conservative if no major threats
    my_bid = DAILY_SALARY * 0.4

    if eric_alive and eric_status:
        eric_prev_bid = eric_status.get('previous_trace', {}).get('bid', 0)
        
        # Base bid when Eric is alive
        my_bid = DAILY_SALARY * 0.85

        # React to Eric's previous aggressive bid
        if eric_prev_bid > DAILY_SALARY * 0.8: # Eric bid aggressively
            my_bid = eric_prev_bid + 5.0 # Outbid him slightly
        elif eric_prev_bid > 0: # Eric bid but not super high, still competitive
            my_bid = max(my_bid, eric_prev_bid + 1.0) # Just slightly above

    # Adjust based on my HP
    if my_status['hp'] <= 2: # Critical HP, must get water
        my_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4: # Low HP, prioritize getting water
        my_bid = max(my_bid, DAILY_SALARY * 0.9)

    # Adjust based on supply and potential competition
    # If supply is tight (less than enough for two agents), competition is high
    if day_context['supply'] < WATER_REQ * 2: 
        my_bid = max(my_bid, DAILY_SALARY * 0.92) # Increase bid if supply is very competitive

    # If it's late in the game, and I have low HP, be more aggressive
    if day_context['day'] >= EPISODE_DAYS - 2 and my_status['hp'] <= 5:
        my_bid = max(my_bid, DAILY_SALARY * 0.95)

    # Ensure bid doesn't exceed budget and is at least a minimal amount
    my_bid = min(my_status['budget'], my_bid)
    my_bid = max(my_bid, DAILY_SALARY * 0.1) # Ensure a minimum bid to participate

    return my_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    CRITICAL_HP_THRESHOLD = WATER_REQ * 1.5 # If HP is below this, become very aggressive
    LOW_HP_THRESHOLD = WATER_REQ * 3 # If HP is below this, become aggressive

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimal to get water
    if num_alive_opponents == 0:
        return min(my_status['budget'], 1.0)

    # Determine my urgency factor
    urgency_factor = 1.0
    if my_status['no_water_days'] >= 1:
        urgency_factor = 1.5 # Missed water yesterday, very urgent
    elif my_status['hp'] <= CRITICAL_HP_THRESHOLD:
        urgency_factor = 1.3 # Critically low HP
    elif my_status['hp'] <= LOW_HP_THRESHOLD:
        urgency_factor = 1.1 # Low HP

    # Base bid: a fraction of daily salary, adjusted by urgency
    # If supply is scarce, this bid needs to be higher
    supply = day_context['supply']
    supply_per_potential_buyer = supply / (num_alive_opponents + 1) # Avg water per agent if split
    
    # If supply is less than my requirement, competition is high
    if supply_per_potential_buyer < WATER_REQ:
        base_bid = DAILY_SALARY * 0.8 * urgency_factor
    else:
        base_bid = DAILY_SALARY * 0.6 * urgency_factor

    # Analyze yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('bid') > 0:
            yesterday_bids.append(prev['bid'])

    current_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If I am urgent, try to outbid the highest previous bid more aggressively
        if urgency_factor > 1.0:
            current_bid = max(current_bid, highest_prev_bid * 1.1)
        else: # If not urgent, try to slightly outbid or match
            current_bid = max(current_bid, highest_prev_bid + 5.0) # Small increment as float
            
    # Ensure bid is at least a certain percentage of salary if critical
    if urgency_factor >= 1.3: # Critical HP or missed water
        current_bid = max(current_bid, DAILY_SALARY * 0.9)
    elif urgency_factor >= 1.1: # Low HP
        current_bid = max(current_bid, DAILY_SALARY * 0.75)

    # Cap bid at current budget
    current_bid = min(my_status['budget'], current_bid)

    # Ensure a minimum bid if I need water
    if my_status['hp'] < EPISODE_DAYS * WATER_REQ: # If I haven't survived the whole round yet
        current_bid = max(current_bid, 1.0)

    return current_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents are bidding very high relative to my salary
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # I'm healthy, can take a risk to save budget
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # I need water, bid aggressively
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else:
            # Match or slightly exceed the highest previous bid, but ensure a floor
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    else:
        # No previous bids (e.g., Day 1 or no bids from alive opponents yesterday)
        if my_status['hp'] <= 2: # Very low HP, need water desperately
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else:
            # Default moderate bid
            return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Determine base bid based on my HP
    # Higher HP means more room to conserve budget, lower HP means more desperate to win
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95 
    elif my_hp <= 5: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_hp <= 7: # Medium HP
        base_bid = DAILY_SALARY * 0.75
    else: # Healthy HP
        base_bid = DAILY_SALARY * 0.65

    # Adjust base bid based on game progression
    # Bids tend to increase towards the end of the episode
    if current_day > EPISODE_DAYS * 0.7: # Last 30% of days
        base_bid *= 1.15 # Increase bid more aggressively
    elif current_day > EPISODE_DAYS * 0.5: # Middle 20% of days
        base_bid *= 1.05 # Increase bid slightly

    # Analyze opponent's previous bids from their trace
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    # Determine my bid based on highest previous bid and my desperation
    my_bid = base_bid

    if highest_prev_bid > 0:
        # If I am desperate, I need to outbid significantly
        if my_hp <= 2:
            my_bid = max(my_bid, highest_prev_bid + DAILY_SALARY * 0.15) 
        elif my_hp <= 5:
            my_bid = max(my_bid, highest_prev_bid + DAILY_SALARY * 0.1) 
        else:
            # If healthy, just slightly outbid the highest known bid
            my_bid = max(my_bid, highest_prev_bid + 1.0) 
    
    # Ensure a minimum competitive bid, especially if many opponents
    if num_alive_opponents > 2:
        my_bid = max(my_bid, DAILY_SALARY * 0.75) # High competition floor
    elif num_alive_opponents > 0:
        my_bid = max(my_bid, DAILY_SALARY * 0.6) # Moderate competition floor
    else: # No opponents, bid low
        my_bid = DAILY_SALARY * 0.3 # Conservatively low when no competition

    # Final bid cannot exceed my budget or be negative
    final_bid = min(my_budget, my_bid)
    final_bid = max(0.0, final_bid)

    # If extremely low on budget and HP, bid everything to survive
    # This is a last resort to try and win water if losing means game over
    if my_budget < DAILY_SALARY * 0.5 and my_hp <= 3:
        final_bid = my_budget

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Filter out opponents who are not truly active bidders based on past meta-round context
    # Alex and Bob are the main competitors. David and Eric seem to be non-factors.
    # An opponent is considered active if they are alive and have a non-zero water_requirement
    # and a non-zero daily_salary (to exclude non-players or very weak ones).
    active_opponents = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive'] and opp_data['water_requirement'] > 0 and opp_data['daily_salary'] > 0:
            active_opponents.append(opp_data)

    if not active_opponents:
        # If no active opponents, bid a minimal amount to secure water and save budget.
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # 1. Look at yesterday's situation (Trace)
    yesterday_bids = []
    for opp in active_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 2. Decision logic based on yesterday's highest pressure and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Alex's max bid was 126.5. This is ~0.843 * DAILY_SALARY.
        # Bob's max bid was 113.97. This is ~0.759 * DAILY_SALARY.
        # The threshold of 0.85 * DAILY_SALARY (127.5) is set just above Alex's typical high bids.
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 127.5
            # Opponents are bidding very aggressively.
            if my_status['hp'] > 3:
                # My HP is good, can afford to save budget, even if it means potentially losing water for a day.
                return min(my_status['budget'], DAILY_SALARY * 0.3) # 45.0
            else:
                # My HP is low (<= 3), MUST get water. Bid very aggressively.
                return min(my_status['budget'], DAILY_SALARY * 0.95) # 142.5
        else:
            # Opponents are bidding moderately or lower than the aggressive threshold.
            # Bid slightly above the highest previous bid to win, but ensure a minimum competitive bid.
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)) # max(75.0, highest_prev_bid + 1.5)
    else:
        # No yesterday bids available (e.g., Day 1, or all previous strong bidders died/inactive).
        # Use a default strategy based on my HP.
        if my_status['hp'] <= 2:
            # My HP is critically low, MUST get water.
            return min(my_status['budget'], DAILY_SALARY * 0.9) # 135.0
        else:
            # My HP is okay, bid moderately to save budget but still aim to win.
            return min(my_status['budget'], DAILY_SALARY * 0.55) # 82.5
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    bid_amount = 0.0
    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid_amount = DAILY_SALARY * 0.75
    else:
        bid_amount = DAILY_SALARY * 0.5

    if highest_prev_bid > DAILY_SALARY * 0.6:
        bid_amount = max(bid_amount, highest_prev_bid + 5.0)
    elif highest_prev_bid > 0:
        bid_amount = max(bid_amount, highest_prev_bid * 1.05)

    num_water_units = int(day_context['supply'] // WATER_REQ)
    total_active_agents = len(alive_opponents) + 1

    if num_water_units < total_active_agents:
        bid_amount *= 1.15
    elif num_water_units >= total_active_agents * 1.5:
        bid_amount *= 0.85

    final_bid = max(1.0, min(my_status['budget'], bid_amount))

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # In this scenario, supply_range is [15, 25] and WATER_REQ is 13.
    # This means day_context['supply'] // WATER_REQ will always be 1 (e.g., 15 // 13 = 1, 25 // 13 = 1).
    # Therefore, there is effectively only one water slot available, leading to high competition.
    
    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) 

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid for non-critical situations, considering the high competition
    base_bid = DAILY_SALARY * 0.7 
    
    # Strategy for high pressure situations:
    # 1. If I missed water yesterday (desperate)
    if my_status['no_water_days'] >= 1:
        # Bid very aggressively, potentially above salary, increasing with more missed days
        return min(my_status['budget'], DAILY_SALARY * 1.05 + (my_status['no_water_days'] * 5)) 
    
    # 2. If HP is critically low
    if my_status['hp'] <= 2:
        # Bid very aggressively to ensure survival
        return min(my_status['budget'], DAILY_SALARY * 1.1) 

    # Strategy based on opponent's previous bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high (close to or above salary),
        # we need to outbid them to secure the single water slot.
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            return min(my_status['budget'], highest_prev_bid + 5) 
        
        # If opponents are bidding moderately, try to win efficiently by slightly exceeding their bid.
        return min(my_status['budget'], max(base_bid, highest_prev_bid + 1))

    # Fallback for Day 1 or if no previous bids from alive opponents.
    # Given the single-slot competition, the default bid needs to be substantial.
    return min(my_status['budget'], base_bid)
"""
