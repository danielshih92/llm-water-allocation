# ============================================================
# Experiment: exp_060
# Agent: Cindy
# Source: exp_060
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid minimal to get water
    if num_alive_opponents == 0:
        return min(my_budget, 1)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Decision logic based on yesterday's highest pressure and my HP
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If opponents bid very high yesterday (high pressure)
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 2: # Critical HP, must get water
                return min(my_budget, highest_prev_bid + 5) # Outbid significantly
            elif my_hp <= 4: # Low HP, need water
                return min(my_budget, highest_prev_bid + 2) # Outbid slightly
            else: # Good HP, can conserve or try to outbid if budget allows
                # If supply is very tight, still bid somewhat high.
                # Otherwise, conserve.
                if day_context['supply'] <= WATER_REQ + 5: # e.g., 15-18 supply
                    return min(my_budget, highest_prev_bid + 1)
                else:
                    return min(my_budget, DAILY_SALARY * 0.5) # Conserve
        
        # If opponents bid moderately or low yesterday
        else:
            if my_hp <= 2: # Critical HP, bid high to secure
                return min(my_budget, DAILY_SALARY * 0.9)
            elif my_hp <= 4: # Low HP, bid moderately high
                return min(my_budget, DAILY_SALARY * 0.75)
            else: # Good HP, try to get water cheaply, but ensure winning if possible
                return min(my_budget, max(DAILY_SALARY * 0.5, highest_prev_bid + 1))
    
    # If no yesterday_bids (e.g., Day 1) or no specific conditions met
    if my_hp <= 2: # Critical HP
        return min(my_budget, DAILY_SALARY * 0.95)
    elif my_hp <= 4: # Low HP
        return min(my_budget, DAILY_SALARY * 0.8)
    else: # Good HP, default bid
        # Consider supply for initial bid
        if day_context['supply'] <= WATER_REQ + 5: # Very tight supply (15-18)
            return min(my_budget, DAILY_SALARY * 0.7)
        else: # More relaxed supply
            return min(my_budget, DAILY_SALARY * 0.6)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    base_bid = 0.0

    # Determine base bid strategy based on my HP
    if my_current_hp <= 2: # Critical HP: Must win at almost any cost
        base_bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 5: # Low-moderate HP: Need water, be competitive
        base_bid = DAILY_SALARY * 0.8
    else: # Healthy HP: Aim for a balance, but still need to win
        base_bid = DAILY_SALARY * 0.65

    # Adjust bid based on opponent behavior (yesterday's bids)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Since only one slot is available, we must outbid the highest opponent.
        # Adjust the margin based on HP to ensure winning.
        if my_current_hp <= 2: # Critical HP
            base_bid = max(base_bid, highest_prev_bid + 10) # Aggressively outbid
        elif my_current_hp <= 5: # Moderate HP
            base_bid = max(base_bid, highest_prev_bid + 5) # Solidly outbid
        else: # Healthy HP
            base_bid = max(base_bid, highest_prev_bid + 1) # Just enough to win, aiming for efficiency

    # If no opponents or no previous bids (e.g., day 1 or all opponents died/didn't bid)
    if not alive_opponents or not yesterday_bids:
        # On day 1, or if no opponents, bid a moderate amount.
        # Since competition is always for one slot, assume some competition even with no history.
        base_bid = DAILY_SALARY * 0.5

    # Final adjustments
    # Ensure bid is at least 1.0 to participate
    final_bid = max(1.0, base_bid)

    # Ensure bid does not exceed current budget
    final_bid = min(final_bid, my_current_budget)

    # If budget is extremely low but HP is critical, bid everything to survive
    if my_current_budget < WATER_REQ and my_current_hp <= 2:
         final_bid = my_current_budget

    return final_bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If no opponents, bid very low to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        # If no previous bids (e.g., Day 1 or all opponents are new),
        # use a default competitive bid based on observed meta-round behavior of strong players.
        # Alex and Eric averaged 100-115, maxed 133-141.
        highest_prev_bid = DAILY_SALARY * 0.75 # Default competitive bid of 112.5

    current_bid = 0.0

    # Critical HP: Bid very high to survive
    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95 # 142.5
    # Low HP: Bid aggressively
    elif my_status['hp'] <= 5:
        current_bid = max(highest_prev_bid + 5, DAILY_SALARY * 0.85) # Floor of 127.5
    # Healthy HP: Strategic bidding
    else:
        # Try to slightly outbid the highest previous bid, with a floor
        current_bid = max(highest_prev_bid + 1, DAILY_SALARY * 0.7) # Floor of 105

    # End game pressure: increase bid if budget allows
    if day_context['day'] >= EPISODE_DAYS - 2 and my_status['hp'] > 0:
        current_bid = max(current_bid, DAILY_SALARY * 0.9) # Ensure it's high enough (135) in late game

    # Ensure bid doesn't exceed budget
    final_bid = min(my_status['budget'], current_bid)

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
    MIN_SUPPLY = 15.0
    MAX_SUPPLY = 25.0

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

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

    bid_amount = DAILY_SALARY * 0.65

    if my_hp <= 2 or my_no_water_days > 0:
        bid_amount = DAILY_SALARY * 0.98
    elif my_hp <= 4:
        bid_amount = DAILY_SALARY * 0.90

    days_remaining = EPISODE_DAYS - current_day
    if days_remaining <= 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95)
    elif days_remaining <= 5:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.80)

    scarcity_factor = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
    bid_amount += scarcity_factor * (DAILY_SALARY * 0.15)

    if highest_prev_bid > 0:
        competitive_bid = highest_prev_bid + 2.0

        if my_hp <= 4 or my_no_water_days > 0:
            bid_amount = max(bid_amount, competitive_bid)
            bid_amount = min(bid_amount, DAILY_SALARY * 1.1)
        else:
            if competitive_bid < DAILY_SALARY * 0.9:
                bid_amount = max(bid_amount, competitive_bid)
            else:
                bid_amount = max(bid_amount, DAILY_SALARY * 0.75)
                bid_amount = min(bid_amount, DAILY_SALARY * 0.95)

    final_bid = max(1.0, min(my_budget, bid_amount))

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_DAYS = 10

    my_water_value = DAILY_SALARY / WATER_REQ

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    opponent_water_values = []
    total_opponent_water_req = 0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        
        opp_water_req = opp.get('water_requirement', 1)
        opp_daily_salary = opp.get('daily_salary', 0)
        if opp_water_req > 0:
            opponent_water_values.append(opp_daily_salary / opp_water_req)
        
        total_opponent_water_req += opp_water_req

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    max_opponent_value = max(opponent_water_values) if opponent_water_values else 0.0

    competitive_floor = max(my_water_value, max_opponent_value * 0.8) if max_opponent_value > 0 else my_water_value

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.95
    else:
        base_bid = my_water_value

        if highest_prev_bid > 0:
            if highest_prev_bid > competitive_floor * 1.5:
                if my_status['hp'] > 5:
                    base_bid = max(base_bid, competitive_floor * 1.1)
                else:
                    base_bid = max(base_bid, highest_prev_bid * 0.8)
            else:
                base_bid = max(base_bid, highest_prev_bid + 0.5)
        
        total_water_needed = WATER_REQ + total_opponent_water_req
        current_supply = day_context['supply']

        if current_supply < total_water_needed * 1.2:
            base_bid *= 1.1
        elif current_supply > total_water_needed * 1.5:
            base_bid *= 0.9

        days_remaining = MAX_DAYS - day_context['day']
        if days_remaining <= 2:
            base_bid *= 1.15
        elif day_context['day'] <= 2:
            base_bid *= 0.9

        bid = base_bid

    final_bid = max(1.0, min(my_status['budget'], bid))
    
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

    current_day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Base bid: Start aggressively due to high competition (only one water slot available per day)
    bid = DAILY_SALARY * 0.95

    # React to yesterday's opponent bids to ensure winning
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If I need water, I must outbid the highest previous bid.
        # Add a small buffer to increase chances, especially if multiple agents bid high.
        bid = max(bid, highest_prev_bid + 5.0)

    # Adjust bid based on HP: Survival is paramount
    if my_hp <= 2: # Critical HP, must win
        bid = max(bid, DAILY_SALARY * 1.2)
    elif my_hp <= 4: # Low HP, bid very aggressively
        bid = max(bid, DAILY_SALARY * 1.05)

    # Adjust for late game: Must survive the last few days
    if current_day >= EPISODE_DAYS - 2: # Last 2 days (e.g., Day 9, 10 for 10-day episode)
        bid = max(bid, DAILY_SALARY * 1.1)
        if my_hp <= 3: # Even more aggressive if HP is low in endgame
            bid = max(bid, DAILY_SALARY * 1.3)

    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, bid)

    # Ensure bid is at least 1.0 to participate
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    MY_WATER_REQ = 13
    MY_DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state, for context, not directly used in this bid logic

    # 1. Determine base bid based on my HP and no_water_days
    bid_factor = 0.4 # Default for high HP, trying to save money
    if my_status['no_water_days'] > 0 or my_status['hp'] <= 2:
        bid_factor = 0.95 # Desperate for water
    elif my_status['hp'] <= 5:
        bid_factor = 0.75 # High priority
    elif my_status['hp'] <= 7:
        bid_factor = 0.6 # Medium priority
    
    current_bid = MY_DAILY_SALARY * bid_factor

    # 2. React to opponents' previous bids
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If I need water (low HP) or opponents bid high, match/exceed their highest bid
        if my_status['hp'] <= 5 or highest_prev_bid >= MY_DAILY_SALARY * 0.7:
            current_bid = max(current_bid, highest_prev_bid + 1.0)
        # If I have high HP, I can try to bid slightly less aggressively relative to highest_prev_bid
        elif my_status['hp'] > 7:
            current_bid = min(current_bid, highest_prev_bid + 0.5)

    # 3. Adjust bid based on supply vs. number of competitors
    num_units_available = int(day_context['supply'] // MY_WATER_REQ)
    num_active_competitors = len(alive_opponents) + 1 # Include myself

    if num_units_available < num_active_competitors:
        current_bid *= 1.05 # Increase bid slightly if competition is high
    elif num_units_available >= num_active_competitors + 1:
        current_bid *= 0.95 # Decrease bid slightly if competition is low

    # 4. Ensure bid does not exceed budget and is at least 1
    current_bid = min(current_bid, my_status['budget'])
    current_bid = max(1.0, current_bid)

    return current_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
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

    # --- Base Bid Calculation ---
    # Start with a bid that aims for a good balance of winning and profit
    bid_ratio = 0.8 # Default: bid 80% of daily salary (120)

    # --- Adjust for my survival needs ---
    if my_no_water_days > 0:
        # Critical: I need water to survive. Bid very high.
        bid_ratio = 1.05 # Bid 105% of salary (157.5)
    elif my_hp <= 2:
        # Low HP: High urgency.
        bid_ratio = 0.95 # Bid 95% of salary (142.5)
    elif current_day > EPISODE_DAYS - 3: # Late game, survival is key
        bid_ratio = max(bid_ratio, 0.9) # Ensure at least 90% bid

    # --- Adjust for supply scarcity ---
    # The supply range is 15-25. My requirement is 13.
    # Competition is always high for 'full' water.
    if current_supply < WATER_REQ * 1.2: # e.g. supply = 15.0
        bid_ratio *= 1.15 # Increase bid significantly for extreme scarcity
    elif current_supply < WATER_REQ * 1.5: # e.g. supply = 16.0-19.0
        bid_ratio *= 1.1 # Increase bid for high scarcity

    # --- Adjust for opponent's previous bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Get the highest bid from yesterday's opponents
    highest_prev_bid = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # If opponents were very aggressive, we need to be too
    if highest_prev_bid > DAILY_SALARY * 1.0: # If someone bid more than my salary
        bid_from_opponents = highest_prev_bid + 5.0
        bid_ratio = max(bid_ratio, bid_from_opponents / DAILY_SALARY)
    elif highest_prev_bid > DAILY_SALARY * 0.8: # If someone bid significantly
        bid_from_opponents = highest_prev_bid + 2.0
        bid_ratio = max(bid_ratio, bid_from_opponents / DAILY_SALARY)

    # Calculate the raw bid amount
    calculated_bid = DAILY_SALARY * bid_ratio

    # --- Final Bid Adjustments ---
    # Ensure bid doesn't exceed current budget
    final_bid = min(my_budget, calculated_bid)

    # Ensure a minimum bid to stay relevant and avoid bidding 0
    min_bid_threshold = DAILY_SALARY * 0.1 # 15
    if my_budget > min_bid_threshold:
        final_bid = max(final_bid, min_bid_threshold)
    else:
        final_bid = max(0.01, final_bid)

    return max(0.01, final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4) # Bid 40% of salary

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bidding strategy based on yesterday's highest bid and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # High competition threshold: if highest previous bid was very aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.85: # 150 * 0.85 = 127.5
            if my_status['hp'] > 5: # If healthy (more than 5 HP), try to conserve a bit, but still competitive
                return min(my_status['budget'], DAILY_SALARY * 0.75) # Bid 112.5
            else: # Not healthy (5 HP or less), bid very aggressively to survive
                return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid 142.5
        else: # Moderate or low competition yesterday
            # Try to win by slightly outbidding the highest, but ensure a decent minimum
            # Use max to ensure bid is at least a base level (e.g., 65% of salary)
            return min(my_status['budget'], max(DAILY_SALARY * 0.65, highest_prev_bid + 3)) # Bid at least 97.5, or 3 more than highest
    
    else: # No previous bids from opponents (e.g., Day 1 of the meta-round, or all opponents failed to bid yesterday)
        if my_status['hp'] <= 3: # If low HP, bid aggressively to secure water
            return min(my_status['budget'], DAILY_SALARY * 0.9) # Bid 135
        else: # Default bid for normal conditions
            return min(my_status['budget'], DAILY_SALARY * 0.7) # Bid 105
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # Prioritize survival if HP is critical or no water days accumulating
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.98)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    eric_prev_bid = 0.0
    alex_prev_bid = 0.0
    eric_budget = 0.0
    alex_budget = 0.0

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        opp_bid_yesterday = prev.get('bid', 0.0)
        opp_budget_today = opp['budget']
        opp_water_req = opp['water_requirement']

        if opp['agent_id'] == 'Eric':
            eric_prev_bid = opp_bid_yesterday
            eric_budget = opp_budget_today
        elif opp['agent_id'] == 'Alex':
            alex_prev_bid = opp_bid_yesterday
            alex_budget = opp_budget_today

    # Only consider bids from opponents who can actually afford their water requirement
    effective_eric_bid = eric_prev_bid if eric_budget >= WATER_REQ else 0.0
    effective_alex_bid = alex_prev_bid if alex_budget >= WATER_REQ else 0.0

    highest_opponent_bid = max(effective_eric_bid, effective_alex_bid)

    # Calculate potential water slots and active players for competition assessment
    num_potential_winners = int(day_context['supply']) // WATER_REQ
    num_active_players = len(alive_opponents) + 1 # Include myself

    # Adjust bid based on competition and opponent's last bids
    if num_potential_winners < num_active_players: # High competition
        # Bid slightly above the highest effective opponent bid, with a baseline
        bid = max(highest_opponent_bid + 1.0, DAILY_SALARY * 0.85)
        # Cap aggressive bid to prevent overspending too much early on
        bid = min(bid, DAILY_SALARY * 0.95)
    else: # Less competition
        # Bid slightly above, or a more conservative baseline
        bid = max(highest_opponent_bid + 0.5, DAILY_SALARY * 0.7)
        # Cap moderate bid
        bid = min(bid, DAILY_SALARY * 0.8)

    # Ensure bid does not exceed current budget
    return min(bid, my_status['budget'])
"""
