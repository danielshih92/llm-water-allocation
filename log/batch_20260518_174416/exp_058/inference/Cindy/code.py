# ============================================================
# Experiment: exp_058
# Agent: Cindy
# Source: exp_058
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    TOTAL_EPISODE_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to secure water
    if num_alive_opponents == 0:
        return min(my_budget, MY_WATER_REQUIREMENT * 1.1)

    # Initialize a base bid
    base_bid = MY_DAILY_SALARY * 0.4 # Start with 40% of daily salary

    # Adjust bid based on my health and water deprivation
    if my_hp <= 2:
        # Critical HP, bid very high to survive
        base_bid = MY_DAILY_SALARY * 0.95
    elif my_no_water_days >= 1:
        # Missed water yesterday, HP will drop if I miss again
        base_bid = MY_DAILY_SALARY * 0.75
    elif my_hp <= 4:
        # HP is getting low, be more aggressive
        base_bid = MY_DAILY_SALARY * 0.6
    
    # Adjust bid based on supply scarcity
    # Lower supply means higher competition, so bid more
    if current_supply <= MY_WATER_REQUIREMENT: # Very scarce, only one agent can get full water
        base_bid *= 1.2 # Increase bid by 20%
    elif current_supply < MY_WATER_REQUIREMENT * 2: # Enough for one, maybe two with reduced needs
        base_bid *= 1.1 # Increase bid by 10%
    elif current_supply >= MY_WATER_REQUIREMENT * 2.5: # Plenty of water, enough for 2-3 agents
        base_bid *= 0.8 # Decrease bid by 20%

    # Adjust bid based on number of opponents
    if num_alive_opponents > 1:
        base_bid *= 1.05 # Slightly increase if multiple opponents
    
    # End game strategy: If few days left and I'm healthy, try to save money.
    # If few days left and I'm low on HP, bid high.
    days_remaining = TOTAL_EPISODE_DAYS - current_day
    if days_remaining <= 2: # Last couple of days
        if my_hp <= 3:
            base_bid = MY_DAILY_SALARY * 0.99 # Almost max bid to survive till end
        else:
            # If healthy, try to save some budget for final score
            base_bid = MY_DAILY_SALARY * 0.5 # Moderate bid
    
    # Ensure bid is within budget and non-negative
    final_bid = max(0.0, min(my_budget, base_bid))
    
    # Ensure bid is at least 1.0 if not 0, to indicate intent to participate
    if final_bid > 0 and final_bid < 1.0:
        final_bid = 1.0

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
    
    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 1. Look at yesterday's situation (Trace)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a dynamic base bid
    base_bid = DAILY_SALARY * 0.75 # A solid starting point

    # Adjust bid based on HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 1: # Extremely critical HP
        base_bid = DAILY_SALARY - 1.0 # Bid almost full salary to ensure survival
    elif my_status['hp'] == 3: # Getting low
        base_bid = DAILY_SALARY * 0.85

    # Adjust bid based on opponent's previous bids
    current_bid = base_bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high, we need to respond
        if highest_prev_bid >= DAILY_SALARY * 0.9: 
            current_bid = max(base_bid, highest_prev_bid + 5.0) # Try to outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.7: 
            current_bid = max(base_bid, highest_prev_bid + 2.0)
        else: 
            current_bid = max(base_bid, highest_prev_bid + 1.0)
    
    # Consider remaining days and budget
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 1 and my_status['hp'] < EPISODE_DAYS: # If I need water to survive the last day
        current_bid = max(current_bid, DAILY_SALARY * 0.99) # Bid very high

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is not negative or zero
    final_bid = max(0.01, final_bid)

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
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    days_remaining = EPISODE_DAYS - day_context['day']
    urgency_multiplier = 1.0 + (day_context['day'] - 1) * 0.02

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 4 and days_remaining > 2:
                bid_value = highest_prev_bid + 2 
            else:
                bid_value = DAILY_SALARY * 0.98 
        else:
            base_bid_for_moderate = DAILY_SALARY * 0.6
            bid_value = max(base_bid_for_moderate, highest_prev_bid + 1.5)
            
            if day_context['supply'] <= WATER_REQ + 2:
                bid_value = max(bid_value, DAILY_SALARY * 0.75)

    else:
        if my_status['hp'] <= 3:
            bid_value = DAILY_SALARY * 0.9
        else:
            if day_context['supply'] <= WATER_REQ + 2:
                bid_value = DAILY_SALARY * 0.8
            else:
                bid_value = DAILY_SALARY * 0.65

    bid_value *= urgency_multiplier

    final_bid = min(my_status['budget'], bid_value)

    if final_bid <= 0.0 and my_status['hp'] < 10:
        final_bid = min(my_status['budget'], 1.0)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Determine base bid based on self-preservation ---
    base_bid = DAILY_SALARY * 0.5 # Moderate starting point

    if my_status['hp'] <= 2: # Critical HP, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need to secure it today
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] < 5: # Moderate HP, still need to be careful
        base_bid = DAILY_SALARY * 0.7
    
    # Adjust for end of episode
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] > 0: # Healthy near end, try to save money
            base_bid *= 0.85
        else: # Low HP near end, bid max to survive
            base_bid = DAILY_SALARY * 0.98

    # --- Analyze opponent behavior from previous day's trace ---
    yesterday_bids_high_type = []
    yesterday_bids_low_type = []
    
    # Identify agent IDs of known high and low bidders from previous meta-round context
    known_high_bidders_ids = ['Bob', 'David']
    known_low_bidders_ids = ['Alex', 'Eric']

    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                if opp_id in known_high_bidders_ids:
                    yesterday_bids_high_type.append(prev['bid'])
                elif opp_id in known_low_bidders_ids:
                    yesterday_bids_low_type.append(prev['bid'])
                else:
                    # For unknown opponents, treat them as general competitors (high type)
                    yesterday_bids_high_type.append(prev['bid'])

    # --- Adjust bid based on opponent's yesterday's bids ---
    if yesterday_bids_high_type:
        highest_prev_high_bid = max(yesterday_bids_high_type)
        # If strong opponents bid high, we need to be very competitive
        if highest_prev_high_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_high_bid + 5) # Try to slightly outbid
        elif highest_prev_high_bid >= DAILY_SALARY * 0.4:
            base_bid = max(base_bid, highest_prev_high_bid + 2)
        else: # Even high type opponents bid low, maybe save
            base_bid = min(base_bid, highest_prev_high_bid * 1.1 + 1)
    
    elif yesterday_bids_low_type: # Only low type bidders are active or bid yesterday
        highest_prev_low_bid = max(yesterday_bids_low_type)
        # If only weak opponents, we can afford to bid lower
        base_bid = min(base_bid, highest_prev_low_bid * 1.2 + 1) # Slightly above their highest, but still low

    # --- Adjust bid based on supply scarcity ---
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    if total_water_demand > day_context['supply']:
        scarcity_ratio = total_water_demand / day_context['supply']
        base_bid *= (1 + (min(scarcity_ratio, 2.0) - 1) * 0.5)
    else:
        abundance_ratio = day_context['supply'] / total_water_demand
        base_bid *= (1 - (min(abundance_ratio, 2.0) - 1) * 0.2)
        base_bid = max(base_bid, DAILY_SALARY * 0.2)

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least 1.0 to be a valid bid
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    TOTAL_DAYS = 10 # From meta-round state episode_days

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Determine how many water slots are available
    num_water_slots = int(day_context['supply'] // WATER_REQ)

    # If no opponents or enough water for everyone, bid low to save budget
    if num_alive_opponents == 0 or num_water_slots >= (num_alive_opponents + 1):
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine highest previous bid, or a default if none
    # Default bid if no history is a moderate percentage of daily salary
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else (DAILY_SALARY * 0.4)

    # Base bid strategy based on my HP and game stage
    my_bid = 0.0

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        # Critical HP or missed water, bid very aggressively
        if day_context['day'] >= TOTAL_DAYS - 2: # Last 2 days, even more aggressive
            my_bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 5.0)
        else:
            my_bid = max(DAILY_SALARY * 0.8, highest_prev_bid + 2.5)
    elif my_status['hp'] <= 4: # Medium low HP
        my_bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 1.5)
    else: # Good HP, try to save or maintain
        # If competition is high (only one slot and multiple opponents)
        if num_water_slots == 1 and num_alive_opponents > 0:
            # Bid slightly above highest previous bid to secure, but don't overspend if not critical
            my_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.0)
        else:
            # Less competition or more water, bid lower to save
            my_bid = DAILY_SALARY * 0.3

    # Ensure bid is at least 1.0 to participate and does not exceed budget
    my_bid = max(1.0, min(my_status['budget'], my_bid))

    return my_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid conservatively to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        # CRITICAL RULE: Use 'previous_trace' for immediate reaction, not meta-round context.
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents are bidding very high, indicating high competition or desperation
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If my HP is relatively good, I can afford to risk a day to save budget
            if my_status['hp'] > 3:
                bid = DAILY_SALARY * 0.3
            # If my HP is low, I must bid very aggressively to survive
            else:
                bid = DAILY_SALARY * 0.95
        # If opponents' highest bid is not extremely high
        else:
            # Bid slightly above the highest previous bid, but at least 50% of salary
            bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    else:
        # No previous bids (e.g., Day 1 of the meta-round or opponents died).
        # Bid based on my current HP.
        if my_status['hp'] <= 2:
            # Aggressive bid if HP is low
            bid = DAILY_SALARY * 0.9
        else:
            # Moderate bid otherwise
            bid = DAILY_SALARY * 0.55
            
    # Ensure bid does not exceed available budget
    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid a conservative amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    max_opponent_bid_yesterday = 0.0
    total_opponent_water_required = 0
    
    for opp in alive_opponents:
        total_opponent_water_required += opp['water_requirement']
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            max_opponent_bid_yesterday = max(max_opponent_bid_yesterday, prev_trace['bid'])

    supply = day_context['supply']
    current_day = day_context['day']
    
    # Calculate total demand including self
    total_required_water_all_players = WATER_REQ + total_opponent_water_required
    
    # Determine a base bid strategy
    bid_amount = DAILY_SALARY * 0.55 # Default moderate bid

    # Adjust based on supply scarcity
    if total_required_water_all_players > supply: # Demand exceeds supply
        if supply < WATER_REQ: # Not enough water even for me
            bid_amount = DAILY_SALARY * 0.98 # Bid extremely high for survival
        else:
            # Shortage, but enough for me. Increase bid to compete.
            scarcity_factor = (total_required_water_all_players - supply) / total_required_water_all_players
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6 + DAILY_SALARY * 0.3 * scarcity_factor) # Scale up to 90%
    else:
        # Supply is sufficient for everyone. Can afford to be more conservative.
        bid_amount = DAILY_SALARY * 0.4 # Lower bid if supply is abundant

    # Integrate yesterday's highest bid
    if max_opponent_bid_yesterday > 0:
        if max_opponent_bid_yesterday >= DAILY_SALARY * 0.85: # Opponents were very aggressive
            # If healthy, good budget, and supply is relatively good, try to conserve
            if my_status['hp'] > 3 and my_status['budget'] > DAILY_SALARY * 2 and supply >= WATER_REQ + (total_opponent_water_required / len(alive_opponents) if len(alive_opponents) > 0 else 0):
                bid_amount = min(bid_amount, DAILY_SALARY * 0.5) # Try to underbid if possible, but not too low
            else: # Low HP, tight budget, or very scarce supply, must compete aggressively
                bid_amount = max(bid_amount, max_opponent_bid_yesterday + 5) # Bid slightly above
        elif max_opponent_bid_yesterday < DAILY_SALARY * 0.3: # Opponents were very conservative
            bid_amount = max(bid_amount, DAILY_SALARY * 0.35) # Ensure a floor to win against low bidders
        else: # Moderate bids yesterday
            bid_amount = max(bid_amount, max_opponent_bid_yesterday + 10) # Bid slightly higher than max to win

    # Survival override: If HP is critical or missed water yesterday, override previous logic with aggressive bid
    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid_amount = DAILY_SALARY * 0.98 # Highest priority for survival

    # End-game adjustment: Last 2 days, prioritize survival if budget allows
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_status['budget'] > DAILY_SALARY * 1.5: # Have some buffer
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        else: # Budget is tight, still try to survive
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8)

    # Final bid must be within budget and non-negative
    final_bid = min(my_status['budget'], max(0.0, bid_amount))
    
    # Ensure a minimal bid if not in critical state and budget allows, to avoid 0 bid when water is needed
    if final_bid < DAILY_SALARY * 0.05 and my_status['budget'] >= DAILY_SALARY * 0.05 and my_status['hp'] > 0:
        final_bid = DAILY_SALARY * 0.05

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # Base bid - start aggressively due to high competition
    base_bid = DAILY_SALARY * 0.8

    # Adjust bid based on my HP and no_water_days
    if my_hp <= 1: # Extremely critical health
        base_bid = DAILY_SALARY * 0.99
    elif my_hp <= 3: # Critical health
        base_bid = DAILY_SALARY * 0.95
    elif my_no_water_days > 0: # Missed water yesterday, need it today
        base_bid = DAILY_SALARY * 0.90
    elif my_hp <= 5: # Low health
        base_bid = DAILY_SALARY * 0.85

    # Adjust based on day in meta-round
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # End game strategy
        if my_hp <= 3: # Unhealthy at the end, bid almost everything
            base_bid = DAILY_SALARY * 0.99
        elif my_hp >= 8: # Healthy at the end, maintain strong bid but not necessarily max
            base_bid = DAILY_SALARY * 0.85
        else:
            base_bid = DAILY_SALARY * 0.90
    elif current_day <= 2: # Early game, establish dominance with a strong bid
        base_bid = DAILY_SALARY * 0.85

    # Analyze yesterday's bids from opponents to react
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If opponents were bidding high yesterday, bid slightly above their max to win.
        if max_yesterday_bid >= DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_yesterday_bid + 2.0)
        else:
            # If opponents bid low yesterday, maintain a strong base bid due to scarcity.
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Final bid constraints
    bid = min(base_bid, my_budget) # Cannot bid more than current budget
    
    # On the very last day, if alive, bid all remaining budget to survive.
    if current_day == EPISODE_DAYS and my_hp > 0:
        bid = my_budget
    else:
        # Otherwise, cap bid at daily salary to maintain profitability over the long run
        bid = min(bid, DAILY_SALARY)

    bid = max(bid, 1.0) # Ensure bid is at least 1.0

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    base_bid = DAILY_SALARY * 0.6

    if highest_prev_bid > 0:
        base_bid = max(base_bid, highest_prev_bid + 1.0)

    current_day = day_context['day']
    remaining_days = EPISODE_DAYS - current_day

    if my_status['hp'] <= 2:
        bid = max(base_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 5:
        bid = max(base_bid, DAILY_SALARY * 0.8)
    elif my_status['hp'] <= 8:
        bid = max(base_bid, DAILY_SALARY * 0.7)
    else:
        bid = max(base_bid, DAILY_SALARY * 0.55)

    if remaining_days <= 2 and my_status['hp'] < 10:
        bid = max(bid, DAILY_SALARY * 0.9)

    final_bid = min(my_status['budget'], bid)
    
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], 1.0)
    elif final_bid <= 0:
        final_bid = 0.0

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

    # Base bid (default moderate bid)
    bid_amount = DAILY_SALARY * 0.65

    # If no opponents, bid very conservatively
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Analyze yesterday's bids to gauge competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # --- Bid Adjustments ---

    # 1. Critical HP adjustment (highest priority)
    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 1.05 # Bid very high to survive
    elif my_status['hp'] <= 4:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95) # High bid
    elif my_status['hp'] <= 6:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85) # Moderate-high bid

    # 2. React to yesterday's highest bid (competition pressure)
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.85: # Opponents are bidding very high
            if my_status['hp'] > 5 and day_context['day'] < EPISODE_DAYS - 2: # Healthy and not end-game, try to save
                bid_amount = max(bid_amount, highest_prev_bid * 0.9) # Bid slightly less but still competitive
            else: # Need water, or end-game, or low HP
                bid_amount = max(bid_amount, highest_prev_bid + 1.5) # Must outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents are bidding moderately
            bid_amount = max(bid_amount, highest_prev_bid + 5) # Bid a bit higher to secure
        else: # Opponents bidding low, but there's a bid
            bid_amount = max(bid_amount, highest_prev_bid + 10) # Outbid easily

    # 3. Supply scarcity adjustment
    supply = day_context['supply']
    
    # Calculate average water per player, considering all alive agents
    avg_water_per_player = supply / (num_alive_opponents + 1)
    
    if avg_water_per_player < WATER_REQ * 0.8: # Very scarce supply
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # Be very aggressive
    elif avg_water_per_player < WATER_REQ * 1.0: # Scarce supply
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Be aggressive
    elif avg_water_per_player > WATER_REQ * 1.5: # Abundant supply
        bid_amount = min(bid_amount, DAILY_SALARY * 0.5) # Can afford to bid lower

    # 4. End-game pressure adjustment
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days
        bid_amount = max(bid_amount, DAILY_SALARY * 1.0) # Bid very high to ensure survival
    elif remaining_days <= 4: # Last 4 days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # Bid high

    # Final bid constraints
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(final_bid, DAILY_SALARY * 0.1) # Ensure a minimum bid to participate

    return float(final_bid)
"""
