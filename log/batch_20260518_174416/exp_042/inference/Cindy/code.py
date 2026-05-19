# ============================================================
# Experiment: exp_042
# Agent: Cindy
# Source: exp_042
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no active opponents, bid minimal to save budget
    if not alive_opponents:
        return min(my_status['budget'], 1)

    # Prioritize survival if HP is critically low (1 or 2)
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If previous bids were very high, outbid them to secure water.
        # Given constant tight supply, trying to save when opponents bid high is too risky.
        if highest_prev_bid >= DAILY_SALARY * 0.75: # React aggressively if bids are high
            # Bid slightly higher than the highest previous bid to ensure winning
            return min(my_status['budget'], highest_prev_bid + 5) 
        
        # If previous bids were moderate, bid slightly above the highest.
        # Ensure a minimum bid to stay competitive.
        return min(my_status['budget'], max(DAILY_SALARY * 0.55, highest_prev_bid + 2))
    
    else: # No previous bids available (e.g., first day)
        # Start with a strong base bid.
        # Given that supply is always less than demand for 2+ agents, it's always competitive.
        # A higher base bid is safer than a low one.
        return min(my_status['budget'], DAILY_SALARY * 0.65)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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

    # If I am the only one left, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_current_budget, DAILY_SALARY * 0.1)

    # --- Determine base bid based on my state and game progress ---
    # Prioritize survival if HP is low or I missed water yesterday
    if my_current_hp <= 3 or my_status['no_water_days'] > 0:
        # Critical state, bid very aggressively
        base_bid = DAILY_SALARY * 0.95
    elif current_day >= EPISODE_DAYS - 2: # Nearing the end of the game
        # End game, bid high to ensure survival
        base_bid = DAILY_SALARY * 0.85
    else:
        # Normal state, moderate bid
        base_bid = DAILY_SALARY * 0.65

    # --- Adjust bid based on opponent's previous bids (from previous_trace) ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Be competitive: bid slightly above the highest previous bid, but consider my base strategy
        # If my base bid is already high, use that. Otherwise, try to outbid.
        competitive_threshold = highest_prev_bid + (DAILY_SALARY * 0.05) # Small increment to outbid
        base_bid = max(base_bid, competitive_threshold)
    
    # --- Adjust bid based on supply-demand dynamics ---
    # Estimate total water needed by all players (including myself)
    total_expected_water_needed = (num_alive_opponents + 1) * WATER_REQ

    if current_supply < total_expected_water_needed:
        # Scarcity: competition will be fierce, increase bid
        base_bid = max(base_bid, DAILY_SALARY * 0.8)
    elif current_supply >= total_expected_water_needed * 1.5: # Abundant supply
        # Plenty of water: can afford to be slightly less aggressive if not in critical state
        if my_current_hp > 3 and my_status['no_water_days'] == 0:
            base_bid = min(base_bid, DAILY_SALARY * 0.55) # Cap bid if supply is very high and I'm healthy

    # --- Final bid constraints ---
    # Bid cannot exceed current budget
    final_bid = min(my_current_budget, base_bid)
    # Ensure bid is not negative. A bid of 0 is valid if budget is 0.
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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid_amount = 0.0

    if my_status['hp'] <= 2:
        bid_amount = DAILY_SALARY * 0.95
    elif my_status['hp'] == 3:
        bid_amount = DAILY_SALARY * 0.85
    else:
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            if highest_prev_bid >= DAILY_SALARY * 0.7:
                bid_amount = highest_prev_bid + 1.0
            else:
                bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 5.0)
        else:
            bid_amount = DAILY_SALARY * 0.55
            
    final_bid = max(1.0, min(my_status['budget'], bid_amount))
    
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

    days_left = EPISODE_DAYS - day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        if days_left == 0 and my_status['hp'] < 10:
            return min(my_status['budget'], DAILY_SALARY * 1.5)
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = 0.0

    if days_left == 0:
        if my_status['hp'] < 10:
            bid = my_status['budget']
        else:
            bid = DAILY_SALARY * 0.1
    else:
        if not yesterday_bids:
            if my_status['hp'] <= 3:
                bid = DAILY_SALARY * 0.95
            elif my_status['hp'] <= 6:
                bid = DAILY_SALARY * 0.75
            else:
                bid = DAILY_SALARY * 0.6
        else:
            highest_prev_bid = max(yesterday_bids)

            if my_status['hp'] <= 2:
                bid = max(highest_prev_bid + 15, DAILY_SALARY * 0.98)
            elif my_status['hp'] <= 4:
                bid = max(highest_prev_bid + 10, DAILY_SALARY * 0.9)
            elif my_status['hp'] <= 6:
                bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.75)
            elif my_status['hp'] <= 8:
                bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.65)
            else:
                if day_context['supply'] >= 2 * WATER_REQ:
                    bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.55)
                else:
                    bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.6)

    final_bid = min(my_status['budget'], max(1.0, bid))

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10
    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.6 # Start with a moderate bid

    # Adjust based on my HP
    if my_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_hp == 3:
        base_bid = DAILY_SALARY * 0.85
    elif my_hp == 4:
        base_bid = DAILY_SALARY * 0.75

    # Adjust based on competition from yesterday's bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        competitive_threshold = highest_prev_bid + 1.0
        base_bid = max(base_bid, competitive_threshold)
    
    # Adjust based on supply scarcity
    num_possible_winners = int(current_supply / WATER_REQ)
    
    if num_possible_winners < num_alive_opponents + 1:
        # Increase bid aggressively if supply is scarce and we need water
        if my_hp <= 4 or current_day >= EPISODE_DAYS - 2:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
    elif num_possible_winners >= num_alive_opponents + 1:
        # If supply is abundant, can be slightly less aggressive, but still competitive
        if base_bid > DAILY_SALARY * 0.7:
             base_bid = max(base_bid, DAILY_SALARY * 0.65)
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.5)

    # Adjust based on remaining days (end game push)
    if current_day >= EPISODE_DAYS - 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    final_bid = min(my_budget, base_bid)

    if final_bid <= 0 and my_budget > 0:
        final_bid = 1.0
    elif my_budget <= 0:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], MY_DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    total_water_needed = MY_WATER_REQ + sum(o['water_requirement'] for o in alive_opponents)
    is_supply_tight = day_context['supply'] < total_water_needed

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= MY_DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                if is_supply_tight:
                    return min(my_status['budget'], max(MY_DAILY_SALARY * 0.7, highest_prev_bid * 0.9))
                else:
                    return min(my_status['budget'], MY_DAILY_SALARY * 0.5)
            else:
                return min(my_status['budget'], MY_DAILY_SALARY * 0.95)
        else:
            return min(my_status['budget'], max(MY_DAILY_SALARY * 0.55, highest_prev_bid + 2.0))
    else:
        if my_status['hp'] <= 2 or day_context['day'] >= EPISODE_DAYS - 2:
            return min(my_status['budget'], MY_DAILY_SALARY * 0.95)
        else:
            return min(my_status['budget'], MY_DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_day = day_context['day']
    supply = day_context['supply']

    # Default bid: a safe moderate amount
    base_bid = DAILY_SALARY * 0.5

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water and save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    opponent_desperation_scores = []

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
            
            # Calculate a desperation score for each opponent
            desperation = (10 - opp['hp']) + (opp['no_water_days'] * 2)
            opponent_desperation_scores.append(desperation)

    # Adjust bid based on my own status (survival priority)
    if my_no_water_days >= 2 or my_hp <= 3: # Critical state
        base_bid = DAILY_SALARY * 0.95
    elif my_no_water_days >= 1 or my_hp <= 5: # Urgent state
        base_bid = DAILY_SALARY * 0.8
    elif my_hp < WATER_REQ: # HP is less than what I need to survive a day without water
        base_bid = DAILY_SALARY * 0.9

    # Adjust bid based on opponent behavior (yesterday's bids and desperation)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid > DAILY_SALARY * 0.7:
            base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid > DAILY_SALARY * 0.5:
            base_bid = max(base_bid, highest_prev_bid + 1)
        else:
            base_bid = max(base_bid, highest_prev_bid + 10)
    
    if opponent_desperation_scores:
        max_opponent_desperation = max(opponent_desperation_scores)
        if max_opponent_desperation >= 10 and my_hp <= 5: # Very desperate opponent and I'm also desperate
            base_bid = max(base_bid, DAILY_SALARY * 0.98)
        elif max_opponent_desperation >= 5:
            base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Consider supply vs demand
    num_agents_needing_water = len(alive_opponents) + 1
    
    if num_agents_needing_water > 0:
        water_per_agent_ideal = supply / num_agents_needing_water
        if water_per_agent_ideal < WATER_REQ: # Scarcity
            base_bid = max(base_bid, DAILY_SALARY * 0.8)
            if my_hp <= 5:
                base_bid = DAILY_SALARY * 0.99
        elif water_per_agent_ideal >= WATER_REQ * 1.5: # Abundance
            base_bid = min(base_bid, DAILY_SALARY * 0.4)
            
    # Final adjustments: Ensure bid does not exceed budget and is at least 1.0
    final_bid = min(my_budget, max(1.0, base_bid))

    # End game strategy: if survival is guaranteed, save money
    days_left = EPISODE_DAYS - current_day
    if days_left > 0 and current_day >= EPISODE_DAYS - 2 and my_hp >= WATER_REQ: 
        final_bid = min(my_budget, DAILY_SALARY * 0.1)

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

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.95
    else:
        bid = DAILY_SALARY * 0.5

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
            bid = max(bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = max(bid, DAILY_SALARY * 0.6)
        else:
            bid = max(bid, highest_prev_bid + 2)

    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3:
        bid = max(bid, DAILY_SALARY * 0.75)

    total_water_needed = WATER_REQ * (len(alive_opponents) + 1)
    if day_context['supply'] < total_water_needed:
        bid *= 1.1
    elif day_context['supply'] >= total_water_needed * 1.5:
        bid *= 0.9

    final_bid = min(my_status['budget'], bid)
    final_bid = max(0.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Initialize bid with a moderate value
    my_current_bid = DAILY_SALARY * 0.5

    # Emergency bidding when health is critical or in the late game
    if my_status['hp'] <= 2: # Critical health
        my_current_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4: # Low health
        my_current_bid = DAILY_SALARY * 0.85
    
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days, bid aggressively
        my_current_bid = max(my_current_bid, DAILY_SALARY * 0.9)

    # Analyze opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        # Separate high roller bids from normal bids
        # High rollers are those bidding significantly above my daily salary
        high_roller_bids = [b for b in yesterday_bids if b > DAILY_SALARY * 1.05]
        normal_bids = [b for b in yesterday_bids if b <= DAILY_SALARY * 1.05]

        if normal_bids: # If there are 'normal' opponents to compete with
            highest_normal_bid = max(normal_bids)
            # Try to outbid the highest normal bid, but don't exceed my determined base aggressive bid
            my_current_bid = max(my_current_bid, highest_normal_bid + 1.0)
            # Cap the bid to ensure sustainability unless in critical health
            if my_status['hp'] > 2:
                my_current_bid = min(my_current_bid, DAILY_SALARY * 0.9)
            else:
                my_current_bid = min(my_current_bid, DAILY_SALARY * 0.98) # Allow higher bid if critical
        elif high_roller_bids: # Only high rollers, no 'normal' bids detected
            if my_status['hp'] <= 3: # If critical, must try to win
                my_current_bid = DAILY_SALARY * 0.98 # Max sustainable effort
            else: # Conserve budget, let high rollers fight it out
                my_current_bid = DAILY_SALARY * 0.6
    
    # Ensure bid does not exceed my current budget
    final_bid = min(my_status['budget'], my_current_bid)

    # Ensure bid is at least 1.0 to be a valid bid
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15
    EPISODE_DAYS = 10

    alive_opponents = [o_status for agent_id, o_status in opponents_status.items() if o_status['alive']]
    num_alive_opponents = len(alive_opponents)

    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    bid = DAILY_SALARY * 0.5

    if my_status['hp'] <= 2 or my_status['no_water_days'] > 0:
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.8

    yesterday_bids = []
    for opp_status in alive_opponents:
        prev = opp_status.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            bid = max(bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.3:
            bid = max(bid, highest_prev_bid + 2)

    if day_context['supply'] < total_water_needed:
        bid *= 1.1
    elif day_context['supply'] < (WATER_REQ * (num_alive_opponents + 1) * 1.2):
        bid *= 1.05

    if day_context['day'] >= EPISODE_DAYS - 2:
        bid = max(bid, DAILY_SALARY * 0.85)

    alex_status = opponents_status.get('Alex')
    if alex_status and alex_status['alive']:
        alex_prev_trace = alex_status.get('previous_trace', {})
        if alex_prev_trace and alex_prev_trace.get('bid') is not None:
            alex_prev_bid = alex_prev_trace['bid']
            if alex_prev_bid >= DAILY_SALARY * 0.8:
                if my_status['hp'] <= 3:
                    bid = max(bid, alex_prev_bid + 10)
                elif my_status['hp'] > 5 and day_context['supply'] > WATER_REQ * 2:
                    bid = min(bid, alex_prev_bid * 0.9)
                    bid = max(bid, DAILY_SALARY * 0.5)
            elif alex_prev_bid >= DAILY_SALARY * 0.5:
                bid = max(bid, alex_prev_bid + 2)

    if num_alive_opponents == 0:
        bid = DAILY_SALARY * 0.1
        if day_context['supply'] < WATER_REQ and my_status['budget'] > 0:
            bid = max(bid, 1.0)
        elif my_status['budget'] == 0:
            bid = 0.0

    final_bid = min(bid, my_status['budget'])
    final_bid = min(final_bid, DAILY_SALARY * 1.1)

    if final_bid > 0:
        final_bid = max(final_bid, 1.0)
    else:
        final_bid = 0.0

    return final_bid
"""
