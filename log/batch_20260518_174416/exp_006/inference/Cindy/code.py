# ============================================================
# Experiment: exp_006
# Agent: Cindy
# Source: exp_006
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
    EPISODE_DAYS = 10

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    
    # If no opponents, bid minimally to secure water
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    total_players_alive = num_alive_opponents + 1

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, need water desperately
        base_bid = DAILY_SALARY * 0.95 # Bid very aggressively
    elif my_hp <= 4: # Low HP, prioritize water
        base_bid = DAILY_SALARY * 0.75
    elif my_hp >= 7 and current_day < EPISODE_DAYS / 2: # Healthy and early game, can be a bit more conservative
        base_bid = DAILY_SALARY * 0.4
    
    # Adjust bid based on supply relative to total water needed
    # This logic assumes water_requirement is the same for all, which is not guaranteed for opponents.
    total_water_needed_for_all_alive_with_my_req = total_players_alive * WATER_REQ
    
    # If supply is less than what everyone needs, it's competitive
    if current_supply < total_water_needed_for_all_alive_with_my_req:
        if current_supply < WATER_REQ * 1.5: # Very tight, likely only one person gets water
             base_bid = max(base_bid, DAILY_SALARY * 0.85) # Bid very aggressively
        elif current_supply < WATER_REQ * 2.5: # Tight, maybe two people get water
            base_bid = max(base_bid, DAILY_SALARY * 0.65) # Bid moderately high
        else: # Still tight, but more water available
            base_bid = max(base_bid, DAILY_SALARY * 0.55)
    else: # Supply is abundant relative to total need (assuming my WATER_REQ for others)
        base_bid = min(base_bid, DAILY_SALARY * 0.4) # Can afford to be less aggressive

    # React to opponent's previous trace
    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opponent_bids.append(prev_trace['bid'])
            
    if yesterday_opponent_bids:
        highest_prev_opp_bid = max(yesterday_opponent_bids)
        
        # If opponents were bidding very high
        if highest_prev_opp_bid >= DAILY_SALARY * 0.8: # Very high bid by opponent
            if my_hp <= 3: # Critical HP, need water
                base_bid = max(base_bid, highest_prev_opp_bid + 5) # Try to outbid
            else: # Healthy, can afford to let them overspend
                base_bid = min(base_bid, DAILY_SALARY * 0.35) # Bid low, let them compete
        # If opponents were bidding moderately high
        elif highest_prev_opp_bid >= DAILY_SALARY * 0.5: # Moderate-high bid
            if my_hp <= 4: # Low to moderate HP, need water
                base_bid = max(base_bid, highest_prev_opp_bid + 2) # Slightly outbid
            else: # Healthy, stick to current strategy, maybe slightly lower
                base_bid = min(base_bid, DAILY_SALARY * 0.45) # Conserve but still competitive
    
    # Final adjustments for end game
    if current_day >= EPISODE_DAYS - 1: # Last two days
        if my_hp < WATER_REQ: # If I don't have enough HP to survive without water
            base_bid = my_budget # Bid everything
        elif my_hp < WATER_REQ * 2 and current_day == EPISODE_DAYS - 1: # Second to last day, need water for 2 days
            base_bid = max(base_bid, DAILY_SALARY * 0.9) # Bid very high

    # Ensure bid is within budget and positive
    final_bid = min(my_budget, base_bid)
    final_bid = max(0, final_bid) # Bid cannot be negative

    return final_bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to secure water.
    if not alive_opponents:
        return min(my_status['budget'], 1)

    # Base bid: a competitive amount, slightly above observed averages of strong players.
    base_bid = DAILY_SALARY * 0.63 # 94.5

    # Look at yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on highest previous bid to try and outbid strong opponents.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        base_bid = max(base_bid, highest_prev_bid + 1)

    # HP-based aggressive bidding: If HP is low, bid very aggressively.
    bid = base_bid
    if my_status['hp'] <= 2:
        bid = max(bid, DAILY_SALARY * 0.95) # 142.5
    elif my_status['hp'] <= 4:
        bid = max(bid, DAILY_SALARY * 0.8)  # 120

    # Day-based adjustment: Increase bid aggressiveness in the late game if HP is not optimal.
    days_remaining = EPISODE_DAYS - day_context['day']
    if days_remaining <= 3 and my_status['hp'] <= 5:
        bid = max(bid, DAILY_SALARY * 0.9) # 135

    # Ensure bid does not exceed budget and is non-negative.
    final_bid = min(my_status['budget'], bid)
    return max(0, final_bid)
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
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to get water to maintain HP
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Determine the highest bid from yesterday among alive opponents
    # Also specifically track Bob's bid if he's alive
    highest_prev_bid = 0.0
    bob_prev_bid = 0.0
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                opponent_bid = prev_trace['bid']
                highest_prev_bid = max(highest_prev_bid, opponent_bid)
                if opp_id == "Bob":
                    bob_prev_bid = opponent_bid

    # Base bid strategy: aim to secure water against the most competitive opponent (Bob)
    # Since only one person can get water (WATER_REQ=13, MAX_SUPPLY=25), it's a direct competition.
    bid = DAILY_SALARY * 0.7 # Base bid of 105

    # Adjust bid based on Bob's previous bid
    if bob_prev_bid > 0:
        # If Bob bid, try to outbid him by a small margin
        bid = max(bid, bob_prev_bid + 5)
    elif highest_prev_bid > 0:
        # If Bob didn't bid (or isn't the highest), consider the overall highest bid
        bid = max(bid, highest_prev_bid + 2)

    # Aggressive bidding if HP is low
    if my_hp <= 2: # Critical HP, need water at almost any cost
        bid = max(bid, DAILY_SALARY * 0.95)
    elif my_hp <= 4: # Low HP
        bid = max(bid, DAILY_SALARY * 0.85)

    # End game strategy: be more aggressive as days run out
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last two days
        bid = max(bid, DAILY_SALARY * 0.9)
        if my_hp <= 3: # And critical HP in end game
            bid = max(bid, DAILY_SALARY * 0.99)

    # Supply-based adjustment: If supply is minimal, competition is implicitly higher for the single available slot
    if current_supply == MIN_SUPPLY:
        bid = max(bid, DAILY_SALARY * 0.75)

    # Final checks
    # 1. Ensure bid does not exceed available budget
    bid = min(bid, my_budget)

    # 2. Ensure a non-zero bid if water is needed (HP not full) and current bid is very low
    # Assuming full HP is 10 (default starting HP)
    if my_hp < 10 and bid < (DAILY_SALARY * 0.1):
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.1))

    # If I have 0 budget, I can't bid anything.
    if my_budget == 0:
        return 0.0

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
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)
    
    is_desperate = my_status['no_water_days'] >= 1 or my_status['hp'] <= 2
    is_late_game = day_context['day'] >= EPISODE_DAYS - 2
    
    if is_desperate:
        return min(my_status['budget'], DAILY_SALARY * 1.02)
    
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    base_bid = DAILY_SALARY * 0.85
    
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        
        target_bid = highest_prev_bid + 2.0
        
        if my_status['hp'] > 5:
            bid = min(DAILY_SALARY * 0.95, target_bid)
        else:
            bid = min(DAILY_SALARY * 0.98, target_bid)
            
        bid = max(bid, average_prev_bid * 0.95)
        bid = max(bid, DAILY_SALARY * 0.8)
        
        if is_late_game and my_status['budget'] > DAILY_SALARY * 2:
            bid = max(bid, DAILY_SALARY * 1.0)
            bid = min(bid, my_status['budget'])
        
        return min(my_status['budget'], bid)
    
    return min(my_status['budget'], base_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimum to get water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Base bid calculation based on my HP ---
    bid_multiplier_hp = 0.5 # Default moderate bid
    if my_status['hp'] <= 2: # Critical HP
        bid_multiplier_hp = 0.95
    elif my_status['hp'] <= 4: # Low HP
        bid_multiplier_hp = 0.75
    elif my_status['hp'] >= 8: # High HP, can conserve more
        bid_multiplier_hp = 0.4
    
    base_bid = DAILY_SALARY * bid_multiplier_hp

    # --- Adjust bid based on supply pressure ---
    current_supply = day_context['supply']
    
    # Estimate water available per agent (including myself)
    water_per_agent_estimate = current_supply / (num_alive_opponents + 1) 

    if water_per_agent_estimate < WATER_REQ * 0.9: # Very tight supply, high competition
        base_bid *= 1.2
    elif water_per_agent_estimate < WATER_REQ * 1.1: # Moderately tight supply
        base_bid *= 1.1
    elif water_per_agent_estimate > WATER_REQ * 1.5: # Abundant supply
        base_bid *= 0.8 # Can afford to bid less

    # --- React to yesterday's highest bid ---
    highest_prev_bid = 0.0
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If the highest bid was very aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.85: # High pressure bid
            if my_status['hp'] > 5: # If I have good HP, let them overspend
                base_bid = min(base_bid, DAILY_SALARY * 0.6) # Conserve, but still competitive
            else: # I need water, must try to outbid
                base_bid = max(base_bid, highest_prev_bid + 5) # Aggressively outbid
        elif highest_prev_bid > DAILY_SALARY * 0.4: # Moderate bids
            base_bid = max(base_bid, highest_prev_bid + 1) # Slightly outbid
        # If bids were low, my base_bid (adjusted by HP and supply) should be sufficient

    # Final adjustments and constraints
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is not too low if I need water or have low HP
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 3:
        survival_bid_floor = DAILY_SALARY * 0.1
        if water_per_agent_estimate < WATER_REQ * 1.0: # If supply is tight
             survival_bid_floor = DAILY_SALARY * 0.25 # Bid more aggressively to survive
        final_bid = max(final_bid, survival_bid_floor)

    # Ensure bid is never negative
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)
    total_players_competing = num_alive_opponents + 1 # Myself + alive opponents

    # Calculate available water slots
    num_water_slots = int(day_context['supply'] // WATER_REQ)
    if num_water_slots == 0: # Should not happen with supply 15-25 and WR 13
        return 0.01 # No water available, bid minimum

    # If no opponents, bid low to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid based on HP and general competition
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 6: # Medium HP
        base_bid = DAILY_SALARY * 0.7
    else: # High HP
        base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on competition and yesterday's bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If water is scarce (more players than slots)
        if num_water_slots < total_players_competing:
            if my_status['hp'] <= 4: # Low HP, need to win
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # Good HP, but competition is high, try to win but don't overpay excessively
                base_bid = max(base_bid, highest_prev_bid + 2)
        else: # Water is relatively abundant (enough slots for everyone or most)
            # If highest bid was very high, maybe opponents are overbidding, try to win cheaper
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                if my_status['hp'] > 4: # If HP is good, try to get it cheaper
                    base_bid = min(base_bid, DAILY_SALARY * 0.4)
                else: # HP is not great, still need to win, but can be a bit less aggressive
                    base_bid = max(base_bid, highest_prev_bid * 0.95) # Bid slightly below to test
            else: # Moderate previous bids, try to win slightly above
                base_bid = max(base_bid, highest_prev_bid + 1)
    else: # No previous bids from alive opponents (e.g., first day or all previous winners died)
        # In this case, rely more on HP and general competition level
        if num_water_slots < total_players_competing:
            # Scarce water, bid higher
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
        else:
            # Abundant water, can bid lower
            base_bid = min(base_bid, DAILY_SALARY * 0.5)

    # Consider remaining days and budget for end-game push
    remaining_days = EPISODE_DAYS - day_context['day']
    # If it's near the end and HP is low, bid very aggressively
    if remaining_days <= 2 and my_status['hp'] <= 4:
        base_bid = max(base_bid, DAILY_SALARY * 0.99)
    elif remaining_days <= 1 and my_status['hp'] > 0: # Last day, just try to survive if possible
        base_bid = max(base_bid, my_status['budget']) # Bid all if needed to survive

    # Ensure bid is within budget and non-negative
    final_bid = min(my_status['budget'], base_bid)
    final_bid = max(0.01, final_bid) # Ensure bid is at least 0.01

    return final_bid
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
    num_alive_opponents = len(alive_opponents)

    # If no opponents are alive, bid minimum to get water and save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Extreme low HP: Must get water at almost any cost
    if my_status['hp'] <= 2:
        # Bid very aggressively, potentially above daily salary
        bid_amount = min(my_status['budget'], DAILY_SALARY * 1.15)
        if my_status['no_water_days'] > 0: # Even more urgent if missed water yesterday
            bid_amount = min(my_status['budget'], DAILY_SALARY * 1.25)
        return max(0.01, bid_amount) # Ensure bid is at least 0.01

    # Collect yesterday's bids to gauge opponent aggression
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # General bidding strategy based on HP and opponent's highest previous bid
    if my_status['hp'] >= 7: # Relatively healthy, can afford to be more conservative
        # If opponents bid very high, still need to be competitive
        if highest_prev_bid > DAILY_SALARY * 0.8:
            bid_amount = min(my_status['budget'], max(DAILY_SALARY * 0.65, highest_prev_bid + 5.0))
        else:
            bid_amount = min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.0))
    elif my_status['hp'] >= 4: # Medium health, need water but not desperate
        if highest_prev_bid > DAILY_SALARY * 0.7:
            bid_amount = min(my_status['budget'], max(DAILY_SALARY * 0.8, highest_prev_bid + 3.0))
        else:
            bid_amount = min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 2.0))
    else: # Low health (HP 3), getting critical
        # Need water urgently, bid higher
        bid_amount = min(my_status['budget'], max(DAILY_SALARY * 0.95, highest_prev_bid + 7.0))
        if my_status['no_water_days'] > 0: # Even more urgent
            bid_amount = min(my_status['budget'], DAILY_SALARY * 1.1)

    # Ensure bid is at least a reasonable minimum, especially if budget allows
    # A base value for my water requirement (13 units) at a fraction of daily salary
    min_competitive_bid = WATER_REQ * (DAILY_SALARY / WATER_REQ) * 0.3 # Roughly 30% of my daily salary
    bid_amount = max(bid_amount, min_competitive_bid)

    # Always ensure bid is not negative and within budget
    if my_status['budget'] > 0:
        bid_amount = max(bid_amount, 0.01) # Minimum bid to be valid
    else:
        return 0.0

    return bid_amount
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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

    # Base bid calculation
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    # Adjust base bid based on my HP and no_water_days
    if my_current_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.98
    elif my_current_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.85
    elif my_status['no_water_days'] > 0: # Missed water recently
        base_bid = DAILY_SALARY * 0.75

    # Adjust based on end-game
    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2:
        if my_current_hp <= 5: # Need to survive to the end
            base_bid = DAILY_SALARY * 0.95
        elif my_current_hp > 8: # Can afford to be slightly less aggressive if HP is very good
            base_bid = max(base_bid, DAILY_SALARY * 0.6) # Ensure it's not too low if base_bid was already high

    # Analyze opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # A rough estimate for how many agents can get water: int(current_supply // WATER_REQ)
        available_water_slots = int(current_supply // WATER_REQ)

        # If highest previous bid was very high, we might need to exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Aggressive opponent
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Try to outbid
        elif highest_prev_bid >= DAILY_SALARY * 0.6 and available_water_slots <= num_alive_opponents: # Moderate but possibly competitive
             base_bid = max(base_bid, highest_prev_bid + 0.5) # Try to outbid slightly

        # If supply is very low (only enough for one or less than needed for all) and my HP isn't great
        if available_water_slots < (num_alive_opponents + 1) and my_current_hp <= 6:
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        elif available_water_slots >= (num_alive_opponents + 1) and highest_prev_bid < DAILY_SALARY * 0.7:
            # If water is abundant and opponents weren't super aggressive, we can be more conservative
            base_bid = min(base_bid, DAILY_SALARY * 0.6) # Don't overbid unnecessarily

    # Ensure bid is within budget
    final_bid = min(my_current_budget, base_bid)

    # Ensure bid is not negative
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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If I'm the only one left, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents and identify Eric's
    yesterday_bids = []
    eric_prev_bid = 0.0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])
                if opp_id == "Eric":
                    eric_prev_bid = prev_trace['bid']

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid calculation based on my status and game stage
    base_bid = DAILY_SALARY * 0.5 # Default moderate bid
    urgency_factor = 1.0

    # Urgency increases if HP is low or if I missed water yesterday
    if my_hp <= 2 or my_no_water_days >= 1:
        urgency_factor = 1.2 # High urgency
    elif my_hp <= 4:
        urgency_factor = 1.05 # Moderate urgency
    elif my_hp >= 8 and current_day <= EPISODE_DAYS / 2: # Healthy and early/mid game
        urgency_factor = 0.8 # Can be more conservative

    # Urgency also increases towards the end of the game
    if current_day >= EPISODE_DAYS - 2: # Last 2 days
        urgency_factor *= 1.2
    elif current_day >= EPISODE_DAYS - 4: # Last 4 days
        urgency_factor *= 1.1

    base_bid = DAILY_SALARY * 0.5 * urgency_factor

    # Adjust bid based on highest previous bid from opponents
    if highest_prev_bid > 0:
        # If highest previous bid was very high, and I need water, bid slightly above it
        if highest_prev_bid >= DAILY_SALARY * 0.8 and (my_hp <= 4 or my_no_water_days >= 1):
            base_bid = max(base_bid, highest_prev_bid * 1.05)
        # If highest previous bid was moderate, bid slightly above it or my base
        elif highest_prev_bid >= DAILY_SALARY * 0.4:
            base_bid = max(base_bid, highest_prev_bid * 1.02)
        else: # Opponents were conservative
            base_bid = max(base_bid, DAILY_SALARY * 0.3) # Ensure a reasonable floor

    # Special consideration for Eric if he was super aggressive
    if eric_prev_bid > DAILY_SALARY * 1.0 and (my_hp <= 3 or my_no_water_days >= 1):
        base_bid = max(base_bid, eric_prev_bid * 1.01) # Try to outbid Eric if he's super aggressive and I need water

    # Consider supply: if supply is tight (e.g., only enough for one or barely two)
    # My water_requirement is 13. Supply is 15-25.
    # If supply is less than WATER_REQ * 1.5, it's tight for two agents to get full water.
    if supply < WATER_REQ * 1.5 and len(alive_opponents) >= 1:
        if my_hp <= 5 or my_no_water_days >= 1:
            base_bid = max(base_bid, DAILY_SALARY * 1.1) # Bid very aggressively if supply is low and I need water
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.7) # Still bid high to compete

    # Final bid must not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure a minimum bid if I need water and have budget
    if my_budget > 0 and (my_hp <= 5 or my_no_water_days >= 1):
        final_bid = max(final_bid, DAILY_SALARY * 0.25) # Ensure a floor bid

    # If budget is critically low and I need water, bid everything
    if my_budget < DAILY_SALARY * 0.5 and (my_hp <= 3 or my_no_water_days >= 1):
        final_bid = my_budget

    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

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

    # CRITICAL HP check: If HP is very low, bid aggressively
    if my_status['hp'] <= 2:
        # Bid high, potentially up to current budget, factoring in daily salary and increasing urgency over time
        return min(my_status['budget'], DAILY_SALARY * 0.95 + (day_context['day'] * 1.5))

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_competitors = len(alive_opponents) + 1 # Include myself

    # If no opponents are alive, bid minimum to win
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid: a moderate amount to save budget but stay competitive
    base_bid = DAILY_SALARY * 0.65

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Adjust base bid based on opponent's previous aggressive bidding
        if max_prev_bid > DAILY_SALARY * 0.8: # Opponents bid very high yesterday
            if my_status['hp'] > 4: # Relatively healthy, try to conserve
                base_bid = max(base_bid, DAILY_SALARY * 0.7)
            else: # Need water, but not critically low HP (hp is 3 or 4)
                base_bid = max(base_bid, max_prev_bid + 5) # Try to outbid them
        else: # Opponents' bids were moderate or low
            base_bid = max(base_bid, avg_prev_bid + 2) # Bid slightly above average to secure water

    # Adjust bid based on supply scarcity
    potential_winners = int(day_context['supply'] // WATER_REQ)

    if potential_winners < num_alive_competitors: # Supply is scarce
        base_bid *= 1.15
    elif potential_winners >= num_alive_competitors + 1: # Supply is abundant
        base_bid *= 0.9

    # Further adjustment based on current day to increase urgency over time
    base_bid += day_context['day'] * 0.5

    # Ensure bid is within reasonable bounds
    my_bid = min(my_status['budget'], base_bid)
    my_bid = max(1.0, my_bid) # Bid at least 1.0

    # Late game adjustment for winning
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] > 1: # Last couple of days, and not critically low HP
        my_bid = min(my_bid, DAILY_SALARY * 1.2) # Allow bidding slightly above salary if needed
        if my_status['budget'] > DAILY_SALARY * 2 and my_status['hp'] > 3: # Healthy and rich
             my_bid = min(my_status['budget'], (max_prev_bid + 10 if yesterday_bids else DAILY_SALARY * 0.8)) # Be more confident to win

    return my_bid
"""
