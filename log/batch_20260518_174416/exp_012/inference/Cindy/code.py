# ============================================================
# Experiment: exp_012
# Agent: Cindy
# Source: exp_012
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # If no opponents, bid very low to save budget, assuming water is guaranteed
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']

    # CRITICAL HEALTH: Prioritize survival above all else
    if my_current_hp <= 2:
        return min(my_current_budget, DAILY_SALARY * 0.95)

    # If no previous bids from opponents (e.g., Day 1 or new opponents)
    if not yesterday_bids:
        # Bid moderately if not in critical health
        return min(my_current_budget, DAILY_SALARY * 0.55)

    highest_prev_bid = max(yesterday_bids)

    # Scenario 1: Opponents bid very high yesterday, indicating tight competition
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_current_hp > 3: # Good health, can afford to be less aggressive to save budget
            return min(my_current_budget, DAILY_SALARY * 0.3)
        else: # Moderate health, still need water, bid high but slightly less than critical
            return min(my_current_budget, DAILY_SALARY * 0.88)

    # Scenario 2: Opponents bid moderately or low yesterday
    else:
        # Bid slightly above the highest previous bid to secure water,
        # ensuring a minimum bid to stay competitive.
        return min(my_current_budget, max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta_round_state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I'm the only one left, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Analyze yesterday's bids from opponents' previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Adjust bid based on HP and opponent behavior
    # Critical HP: Must get water
    if my_status['hp'] <= 2:
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            bid = max(DAILY_SALARY * 0.9, highest_prev_bid + 5.0)
        else:
            bid = DAILY_SALARY * 0.85 # High but not max
    # Low HP: Prefer to get water
    elif my_status['hp'] <= 4:
        if highest_prev_bid >= DAILY_SALARY * 0.6:
            bid = max(DAILY_SALARY * 0.75, highest_prev_bid + 2.0)
        else:
            bid = DAILY_SALARY * 0.65
    # Healthy HP: Can be more conservative
    else:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents very aggressive
            bid = DAILY_SALARY * 0.4 # Let them overspend, I'm healthy
        elif highest_prev_bid > 0.0: # Opponents bid something
            bid = max(DAILY_SALARY * 0.3, highest_prev_bid * 0.9) # Try to get it cheaper
        else:
            bid = DAILY_SALARY * 0.35 # Default conservative bid

    # Consider the day: Bids might increase towards the end of the episode
    days_remaining = EPISODE_DAYS - day_context['day']
    if days_remaining <= 3: # Last few days, more aggressive
        bid = max(bid, DAILY_SALARY * 0.7)

    # Consider supply vs demand
    total_water_needed = WATER_REQ # My water requirement
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    # If supply is tight compared to total demand, competition is high
    if day_context['supply'] < total_water_needed and num_alive_opponents > 0:
        if my_status['hp'] <= 3:
            bid = max(bid, DAILY_SALARY * 0.95) # Critical, bid very high
        elif my_status['hp'] <= 5:
            bid = max(bid, DAILY_SALARY * 0.8) # Low, bid high
        else:
            bid = max(bid, DAILY_SALARY * 0.6) # Healthy, still need to compete

    # Ensure bid doesn't exceed budget and is non-negative
    final_bid = min(my_status['budget'], bid)
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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid low to save money
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Calculate how many people can get water given current supply
    num_possible_winners = int(current_supply / WATER_REQ)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.55 # Default moderate bid

    # Adjust bid based on my HP
    if my_hp <= 2: # Critical HP, need water desperately
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, be aggressive
        base_bid = DAILY_SALARY * 0.8
    elif my_hp >= 7 and my_budget > DAILY_SALARY * 2: # Healthy HP and good budget, try to save
        base_bid = DAILY_SALARY * 0.45

    # Adjust bid based on opponent's previous bids and competition
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If highest bid was very high, and competition is tight (more opponents than slots)
        if highest_prev_bid > DAILY_SALARY * 0.8 and num_alive_opponents >= num_possible_winners:
            if my_hp <= 4: # Critical or low HP, must compete strongly
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # Healthy HP, try to outbid slightly or maintain position
                base_bid = max(base_bid, highest_prev_bid + 1)
        # If highest bid was moderate, and competition is tight
        elif highest_prev_bid > DAILY_SALARY * 0.5 and num_alive_opponents >= num_possible_winners:
            base_bid = max(base_bid, avg_prev_bid + 2)
        # If highest bid was low, and competition is not too tight (more slots than opponents or equal)
        elif highest_prev_bid < DAILY_SALARY * 0.4 and num_alive_opponents <= num_possible_winners:
            base_bid = min(base_bid, highest_prev_bid + 1) # Try to win cheaply

    # Adjust bid based on day progression - become more aggressive towards the end if not winning
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 5: # Last few days, need to survive
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 1 and my_hp <= 3: # Very last day, desperate
        base_bid = max(base_bid, DAILY_SALARY * 0.99)

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, base_bid)

    # Ensure bid is at least 0.1 to avoid being outbid by 0 bids or very tiny bids
    final_bid = max(0.1, final_bid)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid strategy
    # Start with a moderate bid, e.g., 60% of daily salary
    bid_amount = DAILY_SALARY * 0.6

    # Adjust based on my HP
    if my_hp <= 2: # Critical HP, bid very high
        bid_amount = DAILY_SALARY * 0.95
    elif my_hp <= 4: # Low HP, bid high
        bid_amount = DAILY_SALARY * 0.8
    elif my_hp <= 6: # Medium-low HP
        bid_amount = DAILY_SALARY * 0.7

    # Adjust based on supply scarcity (lower supply -> higher competition -> higher bid)
    # Supply range [15, 25]
    if current_supply <= 17: # Very low supply
        bid_amount += DAILY_SALARY * 0.15
    elif current_supply <= 20: # Low supply
        bid_amount += DAILY_SALARY * 0.05

    # React to yesterday's highest bid
    # If I need water (low HP), try to beat it more aggressively
    # Otherwise, try to beat it slightly to win
    if highest_prev_bid > 0:
        if my_hp <= 4: # If critical, try to beat it more
            bid_amount = max(bid_amount, highest_prev_bid + (DAILY_SALARY * 0.1))
        else: # If not critical, try to beat it slightly
            bid_amount = max(bid_amount, highest_prev_bid + (DAILY_SALARY * 0.02)) # A small increment

    # Consider the endgame: if it's the last day and I need water, bid everything
    if current_day == EPISODE_DAYS and my_hp > 0:
        bid_amount = my_budget

    # Ensure bid doesn't exceed budget and is at least 1.0
    final_bid = min(my_budget, max(1.0, bid_amount))

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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    strong_opponent_ids = ["David", "Eric"]
    
    strong_opponents_yesterday_bids = []
    for agent_id, opp in opponents_status.items():
        if opp['alive'] and agent_id in strong_opponent_ids:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                strong_opponents_yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.5 

    if my_hp <= 2:
        bid = DAILY_SALARY * 0.95 
    elif my_hp <= 4:
        bid = DAILY_SALARY * 0.85 
    elif my_hp <= 6:
        bid = DAILY_SALARY * 0.7 

    if current_day >= EPISODE_DAYS * 0.8:
        bid = max(bid, DAILY_SALARY * 0.9) 
    elif current_day >= EPISODE_DAYS * 0.6:
        bid = max(bid, DAILY_SALARY * 0.8) 
    elif current_day >= EPISODE_DAYS * 0.4:
        bid = max(bid, DAILY_SALARY * 0.65) 

    if strong_opponents_yesterday_bids:
        max_prev_strong_bid = max(strong_opponents_yesterday_bids)
        avg_prev_strong_bid = sum(strong_opponents_yesterday_bids) / len(strong_opponents_yesterday_bids)

        if max_prev_strong_bid >= DAILY_SALARY * 0.8:
            bid = max(bid, max_prev_strong_bid + 5) 
        elif avg_prev_strong_bid >= DAILY_SALARY * 0.6:
            bid = max(bid, avg_prev_strong_bid + 10) 
        else:
            bid = max(bid, DAILY_SALARY * 0.6) 

    final_bid = min(bid, my_budget)

    if my_budget == 0:
        return 0.0
    
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQUIREMENT = 13
    MY_DAILY_SALARY = 150
    TOTAL_DAYS = 10

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    base_bid = MY_DAILY_SALARY * 0.55 # Moderate starting bid

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid > MY_DAILY_SALARY * 0.7: # Opponents bidding high
            base_bid = highest_prev_bid * 1.05 
        elif highest_prev_bid < MY_DAILY_SALARY * 0.3: # Opponents bidding low
            base_bid = MY_DAILY_SALARY * 0.35 
        else: # Moderate bids
            base_bid = highest_prev_bid + (MY_DAILY_SALARY * 0.1)

    if my_hp <= 2: # Critical health
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.95)
    elif my_hp <= 5: # Low health
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.75)
    
    remaining_days = TOTAL_DAYS - current_day
    if remaining_days <= 3 and my_hp < TOTAL_DAYS: 
        base_bid = max(base_bid, MY_DAILY_SALARY * 0.9)

    num_can_satisfy_water = int(supply // MY_WATER_REQUIREMENT)

    if num_can_satisfy_water > num_alive_opponents: # Abundant water
        if my_hp > 5: 
            base_bid = min(base_bid, MY_DAILY_SALARY * 0.4)
    elif num_can_satisfy_water <= 1 and num_alive_opponents >= 1: # Scarce water
        if my_hp < 5: 
            base_bid = max(base_bid, MY_DAILY_SALARY * 0.85)

    final_bid = min(my_budget, base_bid)
    final_bid = max(final_bid, 1.0) 

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    base_bid = DAILY_SALARY * 0.65 

    # --- HP-based adjustments ---
    if my_hp <= 2: 
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4: 
        base_bid = DAILY_SALARY * 0.85
    elif my_hp >= 8: 
        base_bid = DAILY_SALARY * 0.5

    # --- End-game adjustments ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: 
        if my_hp <= 5: 
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        elif my_hp > 5 and my_budget < DAILY_SALARY: 
            base_bid = min(base_bid, DAILY_SALARY * 0.7)
    elif remaining_days <= 4: 
        if my_hp <= 3:
            base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # --- Opponent reaction based on previous day's bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp <= 3: 
                base_bid = max(base_bid, highest_prev_bid + 1.0)
            elif my_hp >= 7: 
                base_bid = min(base_bid, DAILY_SALARY * 0.55)
            else: 
                base_bid = max(base_bid, highest_prev_bid * 1.02)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            if my_hp <= 5: 
                base_bid = max(base_bid, highest_prev_bid + 1.0)
            else: 
                base_bid = max(base_bid, highest_prev_bid * 0.98)
        else:
            if my_hp <= 5: 
                base_bid = max(base_bid, highest_prev_bid + 1.0)
            else: 
                base_bid = min(base_bid, highest_prev_bid * 1.15)

    final_bid = min(my_budget, base_bid)

    if my_hp <= 5 and my_budget > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.15)

    if my_budget > 0 and my_hp <= 2:
        final_bid = max(final_bid, my_budget)

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

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect previous bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Base bid, adjusted by HP and day
    bid = DAILY_SALARY * 0.5 # Default moderate bid

    # Aggressive threshold for opponents
    aggressive_threshold = DAILY_SALARY * 0.8
    
    # If opponents were very aggressive yesterday
    if highest_prev_bid >= aggressive_threshold:
        if my_status['hp'] > 4: # If relatively healthy, can try to save
            bid = DAILY_SALARY * 0.6 # Still competitive, but not top-tier
        else: # Critical HP, must fight hard
            bid = DAILY_SALARY * 0.95
    elif highest_prev_bid > 0: # If opponents bid something but not extremely high
        # Bid slightly above to win, but consider my own health
        if my_status['hp'] <= 2: # Very low HP
            bid = max(highest_prev_bid + 10, DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 5: # Low HP
            bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.7)
        else: # Healthy
            bid = max(highest_prev_bid + 2, DAILY_SALARY * 0.55) # Slightly above, but conservative
    else: # No previous bids or all were 0 (e.g., first day or opponents died)
        # Default strategy for early game or unchallenged situations
        if my_status['hp'] <= 2: # Very low HP
            bid = DAILY_SALARY * 0.9
        elif day_context['day'] <= 3: # Early game, be moderately aggressive
            bid = DAILY_SALARY * 0.6
        else:
            bid = DAILY_SALARY * 0.55 # Standard bid

    # Final adjustments
    # If HP is very low, bid very aggressively to survive
    if my_status['hp'] <= 1:
        bid = DAILY_SALARY * 0.99 # Almost max bid to survive
    elif my_status['no_water_days'] > 0: # If I missed water yesterday
        bid = max(bid, DAILY_SALARY * 0.85) # Bid higher to ensure water

    # Late game push
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        if my_status['hp'] > 2: # Healthy, push for the win
            bid = max(bid, DAILY_SALARY * 0.9)
        else: # Desperate for survival
            bid = max(bid, DAILY_SALARY * 0.98)

    # Ensure bid does not exceed budget
    bid = min(bid, my_status['budget'])

    # Ensure bid is at least 0
    bid = max(0.0, bid)

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

    # 1. If no opponents, bid low to save budget, but ensure water if needed.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) if my_status['budget'] > 0 else 0.0

    # 2. Critical HP: If close to death, bid very high.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # 3. Collect yesterday's bids from alive opponents.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # 4. Determine base bid based on supply scarcity and opponent behavior.
    total_water_needed_by_all = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_needed_by_all += opp['water_requirement']

    is_supply_scarce = day_context['supply'] < total_water_needed_by_all * 0.8 

    bid_amount = DAILY_SALARY * 0.55 # Default moderate bid

    if is_supply_scarce:
        if max_yesterday_bid > DAILY_SALARY * 0.7:
            bid_amount = max(bid_amount, max_yesterday_bid + 5.0)
        else:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
    else:
        if max_yesterday_bid > DAILY_SALARY * 0.8:
            bid_amount = max(bid_amount, max_yesterday_bid + 1.0)
        elif max_yesterday_bid > DAILY_SALARY * 0.5:
            bid_amount = max(bid_amount, max_yesterday_bid * 1.05)

    # 5. Adjust bid based on my HP (if not critical, but getting low)
    if my_status['hp'] <= 4:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75)

    # 6. Adjust bid for end-game
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
    elif remaining_days <= 4:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.7)

    # 7. If I have no_water_days, it means I'm not getting water, so need to be more aggressive
    if my_status['no_water_days'] > 0:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    # 8. Final checks and budget constraint
    final_bid = min(my_status['budget'], bid_amount)
    final_bid = max(0.0, final_bid) # Ensure non-negative

    return float(final_bid)
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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = DAILY_SALARY * 0.85

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if my_status['hp'] <= 3:
            bid = max(highest_prev_bid + 5.0, DAILY_SALARY * 1.15)
        elif my_status['hp'] <= 6:
            bid = max(highest_prev_bid + 2.0, DAILY_SALARY * 1.0)
        else:
            bid = max(highest_prev_bid * 0.98, DAILY_SALARY * 0.85)
    else:
        if my_status['hp'] <= 3:
            bid = DAILY_SALARY * 1.1
        elif my_status['hp'] <= 6:
            bid = DAILY_SALARY * 0.95
        else:
            bid = DAILY_SALARY * 0.8

    days_left = EPISODE_DAYS - day_context['day']
    if days_left <= 2:
        if my_status['hp'] <= days_left + 1:
            bid = max(bid, DAILY_SALARY * 1.25)
        else:
            bid = max(bid, DAILY_SALARY * 0.9)
    
    bid = min(bid, my_status['budget'])
    
    if bid <= 0 and my_status['budget'] > 0:
        bid = min(my_status['budget'], 1.0)
    elif bid < DAILY_SALARY * 0.05 and my_status['budget'] > DAILY_SALARY * 0.05:
        bid = DAILY_SALARY * 0.05
    
    return bid
"""
