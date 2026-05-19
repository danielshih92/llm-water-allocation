# ============================================================
# Experiment: exp_064
# Agent: Cindy
# Source: exp_064
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: a moderate amount to secure water
    bid_amount = DAILY_SALARY * 0.6 # Default to 90

    # 1. Prioritize survival: If HP is low or no water recently, bid aggressively.
    if my_status['hp'] <= 2: # Critical HP
        bid_amount = DAILY_SALARY * 0.95 # 142.5
    elif my_status['no_water_days'] >= 1: # Missed water yesterday
        # If no water for 1 day, bid higher to ensure getting it
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85) # 127.5
    elif my_status['hp'] <= 4: # Low HP, but not critical
        bid_amount = max(bid_amount, DAILY_SALARY * 0.75) # 112.5

    # 2. Adjust bid based on supply and competition
    # Estimate total water demand (my req + avg opponent req)
    total_water_demand = WATER_REQ
    for opp in alive_opponents:
        total_water_demand += opp['water_requirement']

    # If supply is very low relative to demand, competition will be fierce
    if current_supply < total_water_demand * 0.7: # Supply is less than 70% of total demand
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9) # 135
    # If supply is low relative to demand
    elif current_supply < total_water_demand * 1.0: # Supply is less than total demand
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # 120
    # If supply is high relative to demand
    elif current_supply > total_water_demand * 1.5: # Supply is 150% of total demand
        bid_amount = min(bid_amount, DAILY_SALARY * 0.4) # 60
    # If supply is moderate
    elif current_supply > total_water_demand * 1.2:
        bid_amount = min(bid_amount, DAILY_SALARY * 0.5) # 75

    # Further adjustment based on just supply amount if total_water_demand heuristic is not enough
    if current_supply <= MIN_SUPPLY + 2: # Very low supply (15-17)
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # 120
    elif current_supply >= MAX_SUPPLY - 2: # Very high supply (23-25)
        bid_amount = min(bid_amount, DAILY_SALARY * 0.45) # 67.5

    # 3. Handle first day or no opponents specifically
    if current_day == 1 and num_alive_opponents == 0:
        # If I'm the only player on day 1, bid low to save budget
        bid_amount = DAILY_SALARY * 0.3 # 45
    elif num_alive_opponents == 0: # Only player left in later days
        bid_amount = DAILY_SALARY * 0.25 # 37.5 (bid even lower)

    # Ensure bid is within budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is at least 1 to participate (or 0 if budget is 0)
    final_bid = max(0.0, final_bid)
    if my_status['budget'] > 0 and final_bid < 1.0: # If budget is positive, bid at least 1
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
    TOTAL_DAYS = 10

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.7

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.9:
            base_bid = max(DAILY_SALARY * 0.85, highest_prev_bid + 1)
        elif avg_prev_bid >= DAILY_SALARY * 0.75:
            base_bid = max(DAILY_SALARY * 0.78, avg_prev_bid + 2)
        else:
            base_bid = max(DAILY_SALARY * 0.65, avg_prev_bid * 1.1)
    
    hp_multiplier = 1.0
    if my_hp <= 2:
        hp_multiplier = 1.2
    elif my_hp <= 4:
        hp_multiplier = 1.1
    elif my_hp <= 7:
        hp_multiplier = 1.05
    else:
        hp_multiplier = 0.95

    num_water_slots = int(current_supply // WATER_REQ)
    num_competitors = len(alive_opponents) + 1

    supply_multiplier = 1.0
    if num_water_slots < num_competitors:
        supply_multiplier = 1.15
    elif num_water_slots >= num_competitors * 1.5:
        supply_multiplier = 0.9
    
    bid = base_bid * hp_multiplier * supply_multiplier

    if my_no_water_days > 0 or my_hp <= 1:
        bid = max(bid, DAILY_SALARY * 0.98)

    remaining_days = TOTAL_DAYS - current_day + 1
    if remaining_days > 0:
        avg_budget_per_day = my_budget / remaining_days
        if avg_budget_per_day < DAILY_SALARY * 0.7:
            bid = max(bid, avg_budget_per_day + (DAILY_SALARY * 0.1))
            bid = min(bid, my_budget)
            if my_hp <= 2:
                bid = max(bid, DAILY_SALARY * 0.95)

    final_bid = min(my_budget, bid)
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
    
    # Base bid, adjusted by HP
    base_bid = DAILY_SALARY * 0.5 # Start with a moderate bid

    if my_status['hp'] <= 2: # Critical HP, need water desperately
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, need water
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8: # Good HP, can afford to be more conservative
        base_bid = DAILY_SALARY * 0.4

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget but ensure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on yesterday's highest opponent bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very aggressive, react accordingly
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If my HP is critical, try to outbid it significantly
            if my_status['hp'] <= 2:
                base_bid = max(base_bid, highest_prev_bid + 5)
            # If my HP is okay, but others are aggressive, still bid high to stay competitive
            else:
                base_bid = max(base_bid, highest_prev_bid * 1.05) # Slightly above
        else: # Opponents were moderate, try to outbid slightly or match if needed
            base_bid = max(base_bid, highest_prev_bid + 2.5) # A small increment to win

    # Further adjust based on overall water scarcity (supply vs demand)
    total_water_needed = WATER_REQ # My requirement
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']
    
    supply = day_context['supply']

    if supply < total_water_needed: # Scarcity
        # The more scarce, the higher the bid multiplier
        scarcity_ratio = supply / total_water_needed
        if scarcity_ratio < 0.5: # Very high scarcity
            base_bid = max(base_bid, DAILY_SALARY * 0.9)
        elif scarcity_ratio < 0.8: # Moderate scarcity
            base_bid = max(base_bid, DAILY_SALARY * 0.75)
        else: # Slight scarcity
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
    else: # Abundance or balanced supply
        # If supply is ample and my HP is good, try to bid lower to save money
        if my_status['hp'] > 5 and base_bid > DAILY_SALARY * 0.4:
            base_bid = min(base_bid, DAILY_SALARY * 0.35) # Can be more conservative

    # Final bid must be within budget and positive
    final_bid = min(my_status['budget'], max(1.0, base_bid)) # Ensure bid is at least 1.0

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    bid_amount = DAILY_SALARY * 0.75

    if my_hp <= 2:
        bid_amount = DAILY_SALARY * 1.25
    elif my_hp <= 4:
        bid_amount = DAILY_SALARY * 1.05

    strong_opponents_yesterday_bids = []
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            prev_trace = opp_data.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                # Identify strong opponents dynamically based on their salary and previous bid
                if opp_data['daily_salary'] >= DAILY_SALARY * 0.9 and prev_trace['bid'] >= opp_data['daily_salary'] * 0.8:
                    strong_opponents_yesterday_bids.append(prev_trace['bid'])
                # Also include opponents who bid very high regardless of their salary
                elif prev_trace['bid'] > DAILY_SALARY * 0.9:
                     strong_opponents_yesterday_bids.append(prev_trace['bid'])

    if strong_opponents_yesterday_bids:
        highest_strong_bid = max(strong_opponents_yesterday_bids)
        if highest_strong_bid > bid_amount * 0.9:
            bid_amount = highest_strong_bid + 5
            if my_hp > 5:
                bid_amount = min(bid_amount, DAILY_SALARY * 1.15)
            else:
                bid_amount = min(bid_amount, DAILY_SALARY * 1.35)
    
    if current_supply < num_alive_opponents:
        bid_amount = max(bid_amount, DAILY_SALARY * 1.2)
    elif current_supply < num_alive_opponents * 1.5:
        bid_amount = max(bid_amount, DAILY_SALARY * 1.05)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp >= 3:
        bid_amount = min(bid_amount, DAILY_SALARY * 0.8)
    elif remaining_days <= 2 and my_hp < 3:
        bid_amount = max(bid_amount, DAILY_SALARY * 1.3)

    final_bid = min(my_budget, bid_amount)

    if final_bid < 1.0 and my_budget > 0:
        final_bid = 1.0
    elif my_budget == 0:
        final_bid = 0.0

    return final_bid
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

    current_budget = my_status['budget']
    
    # Base bid - a moderate amount to start with
    bid = DAILY_SALARY * 0.65 

    # Adjust bid based on my current HP
    if my_status['hp'] <= 2: # Critical HP, need water desperately
        bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4: # Low HP, need water soon
        bid = DAILY_SALARY * 0.85
    
    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Adjust bid based on opponents' previous behavior (yesterday's highest bid)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If my HP is good, try to outbid slightly to stay competitive
        if my_status['hp'] > 4:
            bid = max(bid, highest_prev_bid + 1.5)
        # If my HP is low, ensure I get water by bidding more aggressively
        else: # HP <= 4
            bid = max(bid, highest_prev_bid + 5.0) # Bid higher to secure water
    
    # Adjust bid based on supply
    # If supply is high, we can potentially bid less
    if day_context['supply'] >= 20.0: # High supply
        bid *= 0.95
    # If supply is low, we might need to bid more aggressively
    elif day_context['supply'] <= 18.0: # Low supply
        bid *= 1.05

    # Ensure bid does not exceed available budget
    bid = min(current_budget, bid)
    
    # Ensure bid is at least 1.0 to participate in the auction
    bid = max(1.0, bid)

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 

    num_water_units = int(day_context['supply'] // WATER_REQ)
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_active_players = len(alive_opponents) + 1

    # Base bid strategy
    # Default to a competitive bid
    bid = DAILY_SALARY * 0.65 # 97.5

    # Aggressive bidding if health is low or no water days accumulating
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.95 # Very aggressive bid for survival
    elif my_status['hp'] <= 4:
        bid = DAILY_SALARY * 0.8 # High bid
    elif day_context['day'] >= EPISODE_DAYS - 2: # Last few days, push for survival/win
        bid = DAILY_SALARY * 0.85
    else: # Healthy, early/mid game
        bid = DAILY_SALARY * 0.7 # Moderate bid

    # Adjust based on competition density
    if num_active_players > num_water_units:
        # More players than available water units, increase bid
        bid = max(bid, DAILY_SALARY * 0.8) # Ensure competitiveness
        if day_context['supply'] == 15.0: # Minimum supply, highest competition
            bid = max(bid, DAILY_SALARY * 0.9) # Be very aggressive

    # React to opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_yesterday_bid = 0
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)

    # If there was a high bid yesterday, try to outbid it, especially if I need water
    if max_yesterday_bid > 0:
        # If I'm in survival mode, bid significantly higher
        if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
            bid = max(bid, max_yesterday_bid + 10) # Outbid strongly
        # If competition is high (more players than water units)
        elif num_active_players > num_water_units:
            bid = max(bid, max_yesterday_bid + 5) # Outbid moderately
        # Otherwise, slightly outbid to stay competitive
        else:
            bid = max(bid, max_yesterday_bid + 1)

    # Ensure bid does not exceed budget
    bid = min(bid, my_status['budget'])
    # Ensure bid is at least 0.01
    bid = max(bid, 0.01)

    return bid
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

    # If I'm the only one left, bid low to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.55

    # Adjust bid based on my health and no-water days
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        # Critical state, bid aggressively
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 5:
        # Low health, but not critical
        base_bid = DAILY_SALARY * 0.75

    # Adjust for end-game pressure
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 3:
        base_bid *= 1.1

    # Analyze yesterday's opponent bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Adjust bid based on opponent's previous highest bid
    if highest_prev_bid > DAILY_SALARY * 0.8 and base_bid < DAILY_SALARY * 0.9:
        base_bid = max(base_bid, highest_prev_bid * 1.05)
    elif highest_prev_bid > DAILY_SALARY * 0.5 and base_bid < DAILY_SALARY * 0.7:
        base_bid = max(base_bid, highest_prev_bid * 1.02)

    # Adjust bid based on supply vs number of potential winners
    available_water_slots = int(day_context['supply'] // WATER_REQ)
    num_potential_winners = num_alive_opponents + 1

    if available_water_slots < num_potential_winners:
        # Scarcity: competition is high, increase bid
        base_bid *= 1.1
    elif available_water_slots >= num_potential_winners + 1:
        # Abundance: enough water for everyone and more, decrease bid to save money
        base_bid *= 0.8
        base_bid = max(base_bid, DAILY_SALARY * 0.3)

    # Final bid calculation: ensure it's not negative, cap by budget, and ensure a minimum bid
    final_bid = max(base_bid, DAILY_SALARY * 0.1)
    final_bid = min(my_status['budget'], final_bid)

    return final_bid
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

    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Step 1: Handle no opponents --- 
    # If no opponents, bid just enough to secure water cheaply.
    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.2)

    # --- Step 2: Collect yesterday's bids from alive opponents ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # --- Step 3: Determine base bid using opponent's previous behavior and my HP ---
    bid_amount = 0.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive in the previous round
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3:
                # My HP is good, consider conserving if possible
                bid_amount = DAILY_SALARY * 0.3
            else:
                # My HP is low, must fight hard for survival
                bid_amount = DAILY_SALARY * 0.95
        else:
            # Opponents were not extremely aggressive. Try to slightly outbid their max
            # or ensure a base competitive bid.
            bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.5)
    else:
        # No previous bids available (e.g., Day 1 of meta-round or new opponents).
        # Rely on my HP and recent water status.
        if my_hp <= 2: # Critical HP
            bid_amount = DAILY_SALARY * 0.9
        elif my_no_water_days > 0: # Missed water yesterday, need to be more aggressive
            bid_amount = DAILY_SALARY * 0.8
        else:
            bid_amount = DAILY_SALARY * 0.55 # Default moderate bid

    # --- Step 4: Apply general adjustments based on supply and competition ---
    # These factors modulate the bid, making it more or less aggressive.
    
    # Supply adjustment: Low supply -> higher bid, High supply -> lower bid
    if current_supply < (MIN_SUPPLY + MAX_SUPPLY) / 2: # Below average supply (e.g., < 20)
        bid_amount *= 1.08 # Increase bid slightly
    else: # Above average supply
        bid_amount *= 0.95 # Decrease bid slightly

    # Competition adjustment: More opponents -> higher bid
    if num_alive_opponents > 1:
        bid_amount *= 1.05 # Increase bid for multiple competitors
    elif num_alive_opponents == 1:
        bid_amount *= 1.02 # Slight increase for one competitor

    # --- Step 5: Final bid constraints ---
    final_bid = min(my_budget, bid_amount)

    # Ensure bid is positive and at least 1 if budget allows
    if final_bid <= 0 and my_budget > 0:
        final_bid = 1.0
    elif final_bid < 0: # Safeguard against negative bids
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 150
    WATER_REQ = 13

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no alive opponents, bid a safe amount to ensure survival and profit
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday (e.g., bid >= 85% of daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # My HP is good, try to save but stay competitive in a medium scenario
                return min(my_status['budget'], DAILY_SALARY * 0.6)
            else: # My HP is low, I must compete aggressively to survive
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # Opponents were not overly aggressive yesterday
            # Bid slightly above the highest previous bid, or a solid default to secure water
            # Increased base and increment for a 'medium' scenario to be more competitive
            return min(my_status['budget'], max(DAILY_SALARY * 0.7, highest_prev_bid + 5.0))
    
    # Fallback if no yesterday bids (e.g., day 1 or all opponents failed to bid)
    if my_status['hp'] <= 2: # Critical HP
        return min(my_status['budget'], DAILY_SALARY * 0.9) # Bid high to survive
    else: # Healthy HP
        return min(my_status['budget'], DAILY_SALARY * 0.7) # A solid default bid for a 'medium' scenario
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # 1. Initialize bid
    current_bid = DAILY_SALARY * 0.65

    # 2. Collect opponent bids from yesterday
    yesterday_bids = []
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 3. Determine competition level
    num_alive_players = len(alive_opponents) + 1 # Including myself
    num_water_units = int(day_context['supply'] // WATER_REQ)
    high_competition = num_water_units < num_alive_players

    # 4. Adjust bid based on HP and competition
    if my_status['hp'] <= 3: # Critical HP
        current_bid = DAILY_SALARY * 0.95
        if high_competition:
            current_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= 5: # Low HP
        current_bid = DAILY_SALARY * 0.85
        if high_competition:
            current_bid = DAILY_SALARY * 0.9
    else: # Healthy HP
        current_bid = DAILY_SALARY * 0.7
        if high_competition:
            current_bid = DAILY_SALARY * 0.8

    # 5. Adjust based on yesterday's highest bid to outbid aggressive opponents
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        current_bid = max(current_bid, max_prev_bid + 5.0) # Add a small increment to try and win

    # 6. Adjust for end-game desperation
    if day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days
        current_bid = max(current_bid, DAILY_SALARY * 0.9) # Ensure high bid to survive

    # 7. Final budget check: Do not bid more than available budget
    current_bid = min(current_bid, my_status['budget'])

    # 8. Ensure bid is not negative
    current_bid = max(0.0, current_bid)

    return current_bid
"""
