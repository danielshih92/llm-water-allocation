# ============================================================
# Experiment: exp_040
# Agent: Cindy
# Source: exp_040
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_budget, 1)

    bid_percentage = 0.5 # Default moderate bid

    # Strategy based on HP and remaining days
    remaining_days = EPISODE_DAYS - current_day

    if my_hp <= 2: # Critical HP, must get water
        bid_percentage = 0.95
    elif my_hp <= 4: # Low HP
        bid_percentage = 0.8
    elif my_hp <= 6 and remaining_days <= 3: # Mid-game, HP dropping, and few days left
        bid_percentage = 0.75
    else: # Healthy HP
        # Given WATER_REQ=13 and supply [15, 25], only one full water requirement can usually be met.
        # So, it's always a fight for the single slot.
        if num_alive_opponents >= 2:
            bid_percentage = 0.65 # Increase bid if multiple opponents for single slot
        else: # One opponent
            bid_percentage = 0.55 # Slightly less aggressive if only one opponent

        # Look at opponent's previous bids from yesterday to react
        yesterday_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # If highest bid was very high, be prepared to match or exceed it slightly
            if highest_prev_bid >= DAILY_SALARY * 0.7:
                bid_percentage = max(bid_percentage, highest_prev_bid / DAILY_SALARY + 0.05)
            # If yesterday's bids were generally low, we can try to save money
            elif highest_prev_bid < DAILY_SALARY * 0.4:
                bid_percentage = min(bid_percentage, highest_prev_bid / DAILY_SALARY + 0.1)
                bid_percentage = max(0.3, bid_percentage) # Don't go too low

    # Calculate the proposed bid
    proposed_bid = DAILY_SALARY * bid_percentage

    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, proposed_bid)

    # Ensure bid is at least 1 if budget allows (cannot bid 0 if I need water and have money)
    if my_budget == 0:
        return 0
    return max(1, int(final_bid))
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

    # If no opponents are alive, bid just enough to meet water requirement or what's left in budget
    if not alive_opponents:
        return min(my_status['budget'], WATER_REQ * 1.0)

    current_day = day_context['day']
    day_factor = (current_day / EPISODE_DAYS) # Scales from 0.1 on day 1 to 1.0 on day 10

    # Base bid, becoming more aggressive as days pass
    base_bid = DAILY_SALARY * (0.4 + 0.3 * day_factor) # Ranges from 60.0 to 105.0

    # Adjust for my health and recent water status
    current_bid = base_bid
    if my_status['hp'] <= 2: # Critical health, bid very high
        current_bid = DAILY_SALARY * 0.95 # 142.5
    elif my_status['no_water_days'] > 0: # Missed water yesterday, need it today
        current_bid = max(current_bid, DAILY_SALARY * 0.7) # Ensure it's at least 105.0

    # React to yesterday's opponent bids from their previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents bidding very aggressively (e.g., >= 120.0)
            if my_status['hp'] > 3: # If I have good HP, try to conserve a bit
                current_bid = max(current_bid, DAILY_SALARY * 0.5) # At least 75.0
            else: # Low HP, must try to outbid
                current_bid = max(current_bid, highest_prev_bid * 1.05) # Outbid slightly
        else: # Opponents bidding moderately
            current_bid = max(current_bid, highest_prev_bid + 5.0) # Outbid by a fixed margin

    # Ensure bid does not exceed budget and is not negative
    # Also ensure it's at least 1.0 if budget allows, to participate
    final_bid = min(my_status['budget'], max(1.0, current_bid)) if my_status['budget'] > 0 else 0.0

    # If I'm dying and my final_bid is less than my water requirement, try to bid more if budget allows
    if my_status['hp'] <= 2 and final_bid < WATER_REQ:
        final_bid = min(my_status['budget'], max(final_bid, WATER_REQ * 1.0))

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Base bid: A reasonable amount to secure water
    bid = DAILY_SALARY * 0.60 # Default to 90.0

    # 2. Adjust bid based on my health and no_water_days
    if my_status['hp'] <= 2: # Very critical HP
        bid = max(bid, DAILY_SALARY * 0.95) # Aggressive: 142.5
    elif my_status['hp'] <= 5: # Low HP
        bid = max(bid, DAILY_SALARY * 0.80) # Moderately aggressive: 120.0
    
    if my_status['no_water_days'] > 0: # If I missed water yesterday, increase pressure
        bid = max(bid, bid * 1.1) # Increase bid by 10% from current value

    # 3. Adjust bid based on opponent's previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        
        # If max opponent bid was significant, try to outbid it
        if max_opp_bid >= DAILY_SALARY * 0.5: # If opponent bid at least 75
            bid = max(bid, max_opp_bid + 1.0) # Try to outbid by a small margin
        
    # 4. Adjust bid based on supply scarcity
    supply_range_diff = MAX_SUPPLY - MIN_SUPPLY
    if supply_range_diff > 0: # Avoid division by zero
        # supply_pressure_factor is 1 for min supply, 0 for max supply
        supply_pressure_factor = 1 - ((current_supply - MIN_SUPPLY) / supply_range_diff)
        bid += (DAILY_SALARY * 0.20) * supply_pressure_factor # Add up to 30 based on scarcity
    
    # 5. Adjust bid based on remaining days (end-game pressure)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 3: # Last 3 days, become very aggressive
        bid = max(bid, DAILY_SALARY * 0.90) # 135.0
    elif remaining_days <= 5: # Mid-late game, moderately aggressive
        bid = max(bid, DAILY_SALARY * 0.75) # 112.5

    # Ensure bid is always non-negative and within budget
    final_bid = min(my_status['budget'], max(0.0, bid))

    # If no opponents are alive, bid minimum to conserve budget
    if num_alive_opponents == 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1) # 15.0

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
    # current_supply = day_context['supply'] # Not directly used in bid calculation, but implicitly in strategy
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        # If no opponents, bid minimal to win and save budget
        return min(my_budget, 1.0)

    # Default bid, will be adjusted
    bid_amount = DAILY_SALARY * 0.7 # A reasonable starting point (105)

    # Look at yesterday's highest bid from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, MUST win
        bid_amount = DAILY_SALARY * 0.98 # 147
        if highest_prev_bid > bid_amount:
            bid_amount = highest_prev_bid + 1.0
    elif my_hp <= 5: # Low HP, prioritize winning
        bid_amount = DAILY_SALARY * 0.9 # 135
        if highest_prev_bid > bid_amount:
            bid_amount = highest_prev_bid + 1.0
    else: # Healthy HP, can be more strategic but still aim to win alone
        # If yesterday was competitive, increase bid to outbid
        if highest_prev_bid > DAILY_SALARY * 0.75: # If highest bid was > 112.5
            bid_amount = highest_prev_bid + 1.0
        else:
            bid_amount = DAILY_SALARY * 0.8 # 120 - a solid bid to try and win alone

    # If it's late in the game, become more aggressive regardless of current HP.
    # Days are 1-indexed, so `current_day` from 1 to 10.
    # Last 3 days: Days 8, 9, 10
    if current_day >= EPISODE_DAYS - 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.92) # 138

    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, bid_amount)

    # Ensure bid is at least 1.0 to participate.
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    my_current_bid = 0.0

    # Base bid logic, prioritize survival
    if my_status['hp'] <= 2: # Critical health
        my_current_bid = DAILY_SALARY * 0.98 # Almost full salary
    elif my_status['hp'] <= 4: # Low health
        my_current_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 6: # Medium health
        my_current_bid = DAILY_SALARY * 0.85
    else: # Good health
        # In early days, might save a bit, in later days, secure water
        if day_context['day'] < EPISODE_DAYS / 2:
            my_current_bid = DAILY_SALARY * 0.8
        else:
            my_current_bid = DAILY_SALARY * 0.85

    # Check for Alex, the main competitor
    alex_status = opponents_status.get("Alex")
    alex_is_alive = alex_status and alex_status['alive']

    if alex_is_alive:
        # Get Alex's previous bid, with a strong floor reflecting his aggressive nature
        alex_last_bid = alex_status.get('previous_trace', {}).get('bid')
        
        # If Alex's previous bid is not available or unusually low (e.g., 0 from an error or early death)
        # assume he will bid aggressively based on his historical average
        if alex_last_bid is None or alex_last_bid < DAILY_SALARY * 0.7:
            alex_expected_bid = DAILY_SALARY * 0.8 # A strong baseline for Alex
        else:
            alex_expected_bid = alex_last_bid

        # Adjust bid to beat Alex, increasing aggressiveness with lower HP
        if my_status['hp'] <= 2:
            my_current_bid = max(my_current_bid, alex_expected_bid + 5)
        elif my_status['hp'] <= 4:
            my_current_bid = max(my_current_bid, alex_expected_bid + 3)
        else: # Good or medium health, still need to compete for the single water unit
            my_current_bid = max(my_current_bid, alex_expected_bid + 1)

    # Ensure bid doesn't exceed budget or go below zero
    my_current_bid = min(my_current_bid, my_status['budget'])
    my_current_bid = max(0.0, my_current_bid)

    return my_current_bid
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
    num_alive_opponents = len(alive_opponents)

    # Base bid - a moderate starting point
    bid = DAILY_SALARY * 0.55

    # If no opponents are alive, bid minimum to save budget.
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Adjust bid based on my HP (survival priority)
    if my_status['hp'] <= 2: # Critical HP
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8 and (EPISODE_DAYS - day_context['day'] + 1) > 3: # Healthy and not end-game
        bid = DAILY_SALARY * 0.45 # Can afford to be more conservative
    
    # Analyze yesterday's bids from alive opponents to react dynamically
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # React to high pressure from opponents
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Healthy enough to not panic-bid excessively
                bid = max(bid, highest_prev_bid + 1.0)
                if bid > DAILY_SALARY * 1.0: # Cap to avoid overspending unnecessarily
                    bid = DAILY_SALARY * 1.0
            else: # Desperate for water, need to be more aggressive
                bid = max(bid, highest_prev_bid + 5.0)
                if bid > DAILY_SALARY * 1.2: # Hard cap for extreme aggression
                    bid = DAILY_SALARY * 1.2
        # React to low pressure from opponents (conserve budget)
        elif highest_prev_bid < DAILY_SALARY * 0.4:
            if my_status['hp'] > 5 and (EPISODE_DAYS - day_context['day'] + 1) > 3: # Healthy and not end-game
                bid = min(bid, highest_prev_bid + 1.5) # Try to win cheaply
            else: # Need water or end-game, ensure win but don't overpay too much
                bid = max(bid, highest_prev_bid + 2.0)
        else: # Moderate bids yesterday, maintain competitive edge
            bid = max(bid, highest_prev_bid + 1.0)

    # Adjust based on supply scarcity if multiple opponents are competing for limited water
    current_supply = day_context['supply']
    num_possible_winners = int(current_supply // WATER_REQ)
    if num_possible_winners < (num_alive_opponents + 1) and num_possible_winners == 1:
        # If supply is only enough for one winner and there are multiple competitors
        if my_status['hp'] <= 5: # More aggressive if HP is low
            bid *= 1.15
        else: # Slightly increase bid if HP is good
            bid *= 1.05

    # End game strategy: be more decisive in the final days
    days_left = EPISODE_DAYS - day_context['day'] + 1
    if days_left <= 2: 
        if my_status['hp'] <= 4: # Desperate for survival in the final stretch
            bid = DAILY_SALARY * 1.15 
        elif my_status['hp'] > 7: # Healthy, can afford to be less aggressive
            bid = DAILY_SALARY * 0.5
        else: # Moderate HP, ensure win
            bid = max(bid, DAILY_SALARY * 0.7)

    # Final check: ensure bid is non-negative and within budget
    final_bid = min(my_status['budget'], bid)
    if final_bid <= 0 and my_status['budget'] > 0:
        final_bid = 1.0 # Minimum bid to participate if budget allows

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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

    # If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Initialize base bid as a percentage of daily salary
    base_bid_percentage = 0.5 # Start with 50% of salary

    # 1. HP-based adjustment: Prioritize survival if HP is low
    if my_hp < WATER_REQ: # Critical HP, will die if no water
        base_bid_percentage = max(base_bid_percentage, 0.99)
    elif my_hp <= WATER_REQ * 1.5: # Low HP, need water urgently
        base_bid_percentage = max(base_bid_percentage, 0.8)
    elif my_hp >= WATER_REQ * 3: # Healthy HP, can afford to save
        base_bid_percentage = min(base_bid_percentage, 0.3)

    # 2. Day-based adjustment: Be more aggressive towards the end of the episode
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # End game, be more aggressive
        base_bid_percentage = max(base_bid_percentage, 0.85)
    elif current_day <= 2: # Early game, try to be slightly conservative if comfortable
        base_bid_percentage = min(base_bid_percentage, 0.45)

    # 3. Supply-Demand adjustment: React to resource scarcity
    num_possible_winners = int(current_supply // WATER_REQ) # CRITICAL INDEX RULE: Ensure int conversion
    if num_possible_winners >= num_alive_opponents + 1: # Abundant supply
        base_bid_percentage = min(base_bid_percentage, 0.35)
    elif num_possible_winners <= 1: # Very scarce supply
        base_bid_percentage = max(base_bid_percentage, 0.9)
    elif num_possible_winners <= num_alive_opponents: # Scarce supply
        base_bid_percentage = max(base_bid_percentage, 0.7)

    # 4. Opponent reaction: Adjust based on yesterday's highest bid
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were very aggressive, try to outbid them slightly
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base_bid_percentage = max(base_bid_percentage, (highest_prev_bid / DAILY_SALARY) * 1.05)
        # If opponents were less aggressive, adjust to win efficiently or save
        elif highest_prev_bid < DAILY_SALARY * 0.5:
            if my_hp >= WATER_REQ * 3 and num_possible_winners >= num_alive_opponents + 1: # Very comfortable, try to win cheaper
                base_bid_percentage = min(base_bid_percentage, (highest_prev_bid / DAILY_SALARY) * 0.95)
            else: # Still need to be competitive
                base_bid_percentage = max(base_bid_percentage, (highest_prev_bid / DAILY_SALARY) * 1.05)

    final_bid = DAILY_SALARY * base_bid_percentage

    # Ensure bid is within budget and non-negative
    final_bid = min(my_budget, max(0.0, final_bid))

    return round(final_bid, 2)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    strong_opponent_ids = ["Alex", "David"]
    strong_alive_opponents = [o for o in alive_opponents if o['agent_id'] in strong_opponent_ids]

    if not strong_alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3) 

    yesterday_strong_bids = []
    for opp in strong_alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_strong_bids.append(prev['bid'])

    reference_opponent_bid = DAILY_SALARY * 0.85 
    if yesterday_strong_bids:
        reference_opponent_bid = max(yesterday_strong_bids)

    bid_amount = DAILY_SALARY * 0.75 

    if my_hp <= 2:
        bid_amount = DAILY_SALARY * 1.1 
    elif my_hp <= 4:
        bid_amount = DAILY_SALARY * 0.95 
    elif my_hp >= 8:
        bid_amount = DAILY_SALARY * 0.6 

    if reference_opponent_bid > DAILY_SALARY * 0.7:
        bid_amount = max(bid_amount, reference_opponent_bid + 2.0)
    else:
        if my_hp >= 8:
            bid_amount = min(bid_amount, reference_opponent_bid + 5.0) if reference_opponent_bid > 0 else DAILY_SALARY * 0.55
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7)

    if current_day == EPISODE_DAYS and my_hp > 0:
        return my_budget
    
    if my_status['no_water_days'] > 0 and my_hp <= 3:
        bid_amount = max(bid_amount, DAILY_SALARY * 1.0)

    final_bid = min(my_budget, bid_amount)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to survive or save budget
    if not alive_opponents:
        if my_status['hp'] <= 5 and my_status['no_water_days'] >= 1:
            return min(my_status['budget'], DAILY_SALARY * 0.6)
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bid based on yesterday's highest bid and my status
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Aggressive bidding if HP is low (<=3) or no water for 2+ days
        if my_status['hp'] <= 3 or my_status['no_water_days'] >= 2:
            bid_amount = max(highest_prev_bid + 5, DAILY_SALARY * 0.85)
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6) # Ensure a reasonable floor
            return min(my_status['budget'], bid_amount)
        
        # Moderate bidding if HP is okay
        else:
            bid_amount = max(highest_prev_bid + 2, DAILY_SALARY * 0.55)
            # If opponents are bidding very high, adjust slightly to stay competitive but not overspend unnecessarily
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                 bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid + 1)
            return min(my_status['budget'], bid_amount)
    
    # If no yesterday bids (e.g., first day or opponents didn't bid meaningfully)
    # Use a default strategy based on HP
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.8) # Aggressive default
    else:
        return min(my_status['budget'], DAILY_SALARY * 0.55) # Moderate default
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    total_agents_needing_water = num_alive_opponents + 1
    available_water_slots = int(current_supply // WATER_REQ)

    bid_amount = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3:
                if available_water_slots >= total_agents_needing_water:
                    bid_amount = DAILY_SALARY * 0.35
                else:
                    bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid + 2)
            else:
                bid_amount = max(DAILY_SALARY * 0.95, highest_prev_bid + 5)
        else:
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            if my_hp > 5 and available_water_slots >= total_agents_needing_water + 1:
                bid_amount = min(bid_amount, DAILY_SALARY * 0.4)
    else:
        if my_hp <= 2:
            bid_amount = DAILY_SALARY * 0.9
        elif my_hp <= 4:
            bid_amount = DAILY_SALARY * 0.7
        else:
            bid_amount = DAILY_SALARY * 0.55

    if my_hp <= 1:
        bid_amount = DAILY_SALARY * 0.99

    if available_water_slots < total_agents_needing_water:
        if my_hp <= 3:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
    
    if current_day >= EPISODE_DAYS - 2:
        if my_hp <= 5:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.6)

    return min(my_budget, max(0.0, bid_amount))
"""
