# ============================================================
# Experiment: exp_105
# Agent: Cindy
# Source: exp_105
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    # 1. Check for critical survival state (low HP or consecutive no-water days)
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 2. If no opponents, bid minimally to save budget
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # 3. Collect yesterday's bids from alive opponents to inform current bid
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # 4. Determine bid based on previous bids or a strong default
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Given the extreme scarcity (only one player can get water), we must bid competitively.
        # Bid slightly above the highest previous bid, ensuring a reasonable floor.
        target_bid = max(DAILY_SALARY * 0.75, highest_prev_bid + 1.0)
        return min(my_status['budget'], target_bid)
    else:
        # No previous bids available (e.g., first day of the meta-round or no opponent trace).
        # Set a strong default bid to establish presence and secure water in a highly competitive environment.
        return min(my_status['budget'], DAILY_SALARY * 0.8)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10 

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    # 1. Immediate Survival Strategy: If HP is critically low or no water yesterday, bid aggressively.
    if my_hp <= 2 or my_status['no_water_days'] > 0:
        return min(my_budget, DAILY_SALARY * 1.0)

    # 2. Calculate a dynamic base bid factoring supply and day progression.
    # Base bid starts at 50% of daily salary.
    base_bid = DAILY_SALARY * 0.5

    # Adjust bid based on supply: lower supply means higher bid.
    # supply_factor ranges from 0 (max supply) to 1 (min supply).
    supply_factor = (MAX_SUPPLY - current_supply) / (MAX_SUPPLY - MIN_SUPPLY)
    base_bid *= (1 + supply_factor * 0.3) # Increase up to 30% for low supply

    # Adjust bid based on day progression: slightly higher bids towards the end.
    # day_factor ranges from 0 (day 1) to 1 (last day).
    day_factor = (current_day - 1) / (EPISODE_DAYS - 1) if EPISODE_DAYS > 1 else 0
    base_bid *= (1 + day_factor * 0.1) # Increase up to 10% towards end

    # 3. Analyze opponents' previous bids to adjust strategy.
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = base_bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # React to high bids from opponents (e.g., Alex's behavior).
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            # Opponents are very aggressive. Be competitive, slightly above their highest.
            final_bid = max(base_bid, highest_prev_bid * 1.05)
        # React to very low bids from opponents (e.g., Bob/David's early failure).
        elif highest_prev_bid < DAILY_SALARY * 0.4:
            # Opponents are bidding low. Try to save money but ensure water by bidding slightly above.
            final_bid = max(base_bid * 0.8, highest_prev_bid + 1)
        else:
            # Moderate bids. Be slightly competitive.
            final_bid = max(base_bid, highest_prev_bid * 1.02)

    # 4. Ensure bid is within budget and non-negative.
    return max(0.0, min(my_budget, final_bid))
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

    # --- Phase 1: Emergency Bidding (High HP, No Water Days) ---
    # If HP is critically low, bid very high to survive
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Almost full salary

    # If I've missed water before, be more aggressive
    if my_status['no_water_days'] > 0:
        base_bid = DAILY_SALARY * 0.4 # Higher base bid
    else:
        base_bid = DAILY_SALARY * 0.1 # Default low bid (15.0)

    # --- Phase 2: Adjust based on Opponents and Supply ---
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.05) # Very low bid if no competition

    # Collect yesterday's bids and Eric's specific info
    yesterday_bids = []
    eric_info = None
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])
            if opp_id == "Eric":
                eric_info = {'bid': prev.get('bid'), 'water_requirement': opp['water_requirement']}

    # Calculate total water demand
    total_opponent_water_req = sum(o['water_requirement'] for o in alive_opponents)
    total_demand = WATER_REQ + total_opponent_water_req

    # --- Adjust base bid based on yesterday's highest bid ---
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If yesterday's bids were high, increase our bid to stay competitive
        if highest_prev_bid > base_bid:
            base_bid = highest_prev_bid + 1.0 # Slightly outbid

    # --- Specific adjustment for Eric, considering his historical low bids ---
    # The LATEST METAROUND CONTEXT implies Eric bids 15.0 and survives.
    # If Eric is present and his water_requirement is similar to mine, and he bids low,
    # we need to beat him if supply is tight.
    if eric_info and eric_info['bid'] is not None and eric_info['water_requirement'] >= WATER_REQ * 0.8: # Eric needs similar water
        if eric_info['bid'] < DAILY_SALARY * 0.2: # Eric is bidding very low (e.g., < 30)
            if day_context['supply'] < total_demand: # Supply is tight
                base_bid = max(base_bid, eric_info['bid'] + 1.5) # Ensure we outbid Eric
            else: # Supply is sufficient for all (unlikely with 15-25 supply and 2+ players needing 13)
                base_bid = max(base_bid, eric_info['bid'] + 0.5) # Still slightly higher to secure

    # --- Adjust for supply scarcity ---
    if day_context['supply'] < WATER_REQ: # Not enough water even for myself
        base_bid = max(base_bid, DAILY_SALARY * 0.7) # Very aggressive bid
    elif day_context['supply'] < total_demand: # Not enough for everyone, but enough for me
        base_bid *= 1.2 # Increase bid by 20%

    # --- End game strategy ---
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] > 0: # Last couple of days, need to secure water
        if my_status['budget'] > DAILY_SALARY * 2: # Can afford to be aggressive
            base_bid = max(base_bid, DAILY_SALARY * 0.5)
        else: # Budget is low, but still need to try
            base_bid = max(base_bid, DAILY_SALARY * 0.3)

    # Ensure bid doesn't exceed budget and is not negative
    final_bid = min(my_status['budget'], base_bid)
    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid a safe amount to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    bid = 0.0 # Initialize bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Determine a base bid based on my HP, prioritizing survival
        if my_status['hp'] <= 2: # Critical HP, must win
            bid = DAILY_SALARY * 0.98 # Very high bid
        elif my_status['hp'] <= 4: # Low HP, need to win
            bid = DAILY_SALARY * 0.90 # High bid
        else: # Healthy HP, but still aim to win consistently
            bid = DAILY_SALARY * 0.70 # Moderate-high bid

        # Adjust bid to outbid the highest previous bid, but not go lower than my HP-based bid
        bid = max(bid, highest_prev_bid + 1.5)

    else:
        # No previous bids (e.g., Day 1 or all opponents are new)
        # Use HP-based initial bid, being competitive from the start
        if my_status['hp'] <= 2:
            bid = DAILY_SALARY * 0.95
        elif my_status['hp'] <= 4:
            bid = DAILY_SALARY * 0.85
        else:
            bid = DAILY_SALARY * 0.60 # A solid starting bid to establish presence

    # Ensure bid does not exceed available budget and is at least 1.0
    final_bid = max(1.0, min(my_status['budget'], bid))

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
    MAX_HP = 10
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) 

    # --- Determine initial bid based on my HP and no_water_days --- (Cindy's perspective)
    initial_bid_multiplier = 0.75 # Default moderate bid
    
    if my_status['hp'] <= 2: # Critical HP, must win
        initial_bid_multiplier = 0.95
    elif my_status['hp'] == 3: # Low HP
        initial_bid_multiplier = 0.85
    elif my_status['hp'] >= 8: # High HP, can afford to save a bit
        initial_bid_multiplier = 0.65
    
    # Increase bid slightly for each day without water, indicating increasing desperation
    if my_status['no_water_days'] > 0:
        initial_bid_multiplier += (my_status['no_water_days'] * 0.05) 
        # Cap multiplier to prevent exceeding 1.0 too easily, as budget is the real cap.
        initial_bid_multiplier = min(initial_bid_multiplier, 0.98) 

    my_calculated_bid = DAILY_SALARY * initial_bid_multiplier

    # --- Adjust bid based on opponent's previous bids --- (React to competition)
    highest_prev_bid = 0.0
    
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev['bid'])
            
    # If the highest opponent bid yesterday was significant, react to it
    if highest_prev_bid > 0:
        # If opponent bid was higher than my calculated bid, try to slightly exceed it
        if highest_prev_bid >= my_calculated_bid:
            my_calculated_bid = highest_prev_bid + (DAILY_SALARY * 0.01) # Slightly overbid
        # If opponent bid was lower, but still competitive, ensure my bid is at least that high
        elif highest_prev_bid > DAILY_SALARY * 0.5: # If opponent was competitive but lower
            my_calculated_bid = max(my_calculated_bid, highest_prev_bid + 1) # Ensure I am above them

    # Ensure bid is at least a minimal competitive amount
    min_competitive_bid = DAILY_SALARY * 0.5 # 75
    final_bid = max(my_calculated_bid, min_competitive_bid)
    
    # Ensure bid does not exceed current budget
    # Always leave a tiny fraction to avoid floating point issues when comparing with budget
    final_bid = min(final_bid, my_status['budget'] - 0.01) 

    # Ensure bid is positive
    final_bid = max(0.01, final_bid) # Minimum bid of 0.01

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
    current_supply = day_context['supply']
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents are alive, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # --- 1. Emergency Bidding for Survival ---
    # If HP is critically low (2 or less) or I missed water yesterday, bid very aggressively.
    if my_hp <= 2 or my_no_water_days >= 1:
        return min(my_budget, DAILY_SALARY * 1.5) # Bid up to 1.5x salary or full budget

    # --- 2. Determine Base Bid ---
    base_bid = DAILY_SALARY * 0.75 # A good profit margin if won

    # --- 3. Adjust based on Opponents' Previous Bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday
        if highest_prev_bid > DAILY_SALARY * 1.0:
            base_bid = max(base_bid, highest_prev_bid + 1.0) # Slightly outbid
        # If opponents were conservative yesterday
        elif highest_prev_bid < DAILY_SALARY * 0.7:
            base_bid = min(base_bid, highest_prev_bid + 5.0) # Don't overpay significantly
        # Normal competitive range
        else:
            base_bid = max(base_bid, highest_prev_bid + 2.0) # Slightly outbid

    # --- 4. Adjust based on Current Supply and Competition ---
    num_winners_possible = int(current_supply // WATER_REQ) 
    num_active_players = len(alive_opponents) + 1 # Myself + alive opponents
    
    if num_active_players > num_winners_possible: # High competition
        # If only one winner possible and multiple active players, bid very aggressively
        if num_winners_possible == 1 and num_active_players > 1:
            base_bid = max(base_bid, DAILY_SALARY * 1.2)
        else: # General high competition
            base_bid *= 1.1 # Increase bid by 10%

    # --- 5. End Game Strategy (Last few days) ---
    if current_day >= EPISODE_DAYS - 2: # Day 8, 9, 10
        if my_hp > 5: # Healthy, try to secure win with less risk
            base_bid = max(base_bid, DAILY_SALARY * 0.9) # Ensure a reasonable bid
        else: # HP is low, must get water
            base_bid = max(base_bid, DAILY_SALARY * 1.3) # Bid very high

    # --- 6. Final Bid Clamp ---
    # Ensure bid does not exceed budget and has a minimum floor
    final_bid = min(my_budget, base_bid)
    final_bid = max(final_bid, DAILY_SALARY * 0.5) # Ensure a minimum bid to stay relevant

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid a minimal amount to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on my HP
    bid_strategy_value = DAILY_SALARY * 0.6  # Default moderate bid
    if my_status['hp'] <= 3:  # Critical HP, need water urgently
        bid_strategy_value = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 6:  # Low HP, bid high
        bid_strategy_value = DAILY_SALARY * 0.8
    elif my_status['hp'] >= 8:  # Healthy HP, can be more conservative
        bid_strategy_value = DAILY_SALARY * 0.5

    # Adjust bid based on current supply
    current_supply = day_context['supply']
    if current_supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2:  # Supply is in the lower half (more competitive)
        bid_strategy_value *= 1.05  # Slightly increase bid
    else:  # Supply is in the upper half (less competitive)
        bid_strategy_value *= 0.95  # Slightly decrease bid

    # React to yesterday's highest opponent bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid very high yesterday, we might need to match or exceed
        if highest_prev_bid >= DAILY_SALARY * 0.8:  # High pressure from opponents
            if my_status['hp'] > 3:  # Not critical, try to outbid slightly
                bid_strategy_value = max(bid_strategy_value, highest_prev_bid + (DAILY_SALARY * 0.05))
            else:  # Critical HP, must win, bid very aggressively
                bid_strategy_value = max(bid_strategy_value, highest_prev_bid + (DAILY_SALARY * 0.1))
        elif highest_prev_bid >= DAILY_SALARY * 0.5:  # Moderate pressure
            bid_strategy_value = max(bid_strategy_value, highest_prev_bid + (DAILY_SALARY * 0.02))

    # Ensure the bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_strategy_value)

    # Ensure a minimal bid to cover water requirement
    min_viable_bid = WATER_REQ * 1.0
    final_bid = max(final_bid, min_viable_bid)

    # Desperate bid if near death and have some budget left
    if my_status['hp'] <= 1 and my_status['budget'] > min_viable_bid:
        final_bid = my_status['budget'] * 0.99  # Bid almost all budget

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # --- Base Bid Calculation ---
    # Start with a default bid that's sustainable
    bid = DAILY_SALARY * 0.55

    # --- Adjust bid based on personal status ---
    # High urgency if HP is very low or I've missed water
    if my_hp <= 2:
        bid = DAILY_SALARY * 0.95
    elif my_hp <= 5:
        bid = DAILY_SALARY * 0.8
    elif my_no_water_days > 0:
        bid = DAILY_SALARY * 0.85

    # --- Adjust bid based on supply scarcity ---
    # How many players can theoretically get their water requirement?
    max_players_can_get_water = int(current_supply // WATER_REQ)

    if max_players_can_get_water <= 1: # Only one player can get water, extremely competitive
        bid = max(bid, DAILY_SALARY * 0.95)
    elif max_players_can_get_water <= num_alive_opponents: # Supply is scarce, not everyone can get water
        bid = max(bid, DAILY_SALARY * 0.8)
    elif max_players_can_get_water <= num_alive_opponents + 1: # Just enough for everyone, or slightly more
        bid = max(bid, DAILY_SALARY * 0.65)
    else: # Supply is abundant, more water than players need
        bid = min(bid, DAILY_SALARY * 0.4) # Try to save budget

    # --- Adjust bid based on opponent's previous behavior (yesterday's trace) ---
    yesterday_bids_of_winners = []
    yesterday_bids_of_losers = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            if prev_trace.get('status') == 'got_water':
                yesterday_bids_of_winners.append(prev_trace['bid'])
            else: # 'no_water' or 'error'
                yesterday_bids_of_losers.append(prev_trace['bid'])

    # If there were winners yesterday, try to bid slightly above their highest bid to secure water
    if yesterday_bids_of_winners:
        max_winner_bid = max(yesterday_bids_of_winners)
        bid = max(bid, max_winner_bid + 5) # Bid slightly above to outcompete

    # If there were losers yesterday, they might bid much higher today. Account for this.
    if yesterday_bids_of_losers:
        max_loser_bid = max(yesterday_bids_of_losers)
        # If they failed to get water with a high bid, they are likely desperate.
        # This is a strong signal to increase our bid.
        if max_loser_bid > DAILY_SALARY * 0.7:
             bid = max(bid, max_loser_bid + 10) # Significantly increase to beat desperate opponents
        else:
             bid = max(bid, max_loser_bid + 5) # Slight increase if their losing bid wasn't too high

    # --- End game strategy ---
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last two days, push hard if needed
        if my_hp < 5:
            bid = DAILY_SALARY * 0.98 # Almost max bid
        elif my_budget > DAILY_SALARY * 1.5: # If I have budget, might as well spend it to ensure survival
            bid = max(bid, DAILY_SALARY * 0.8)

    # --- Final Constraints ---
    # Bid cannot exceed current budget
    bid = min(bid, my_budget)

    # Ensure bid is not too low if I desperately need water
    if my_hp <= 3 or my_no_water_days > 0:
        bid = max(bid, DAILY_SALARY * 0.6) # Minimum bid to stay competitive when desperate

    # Ensure bid is at least 1 if budget allows, to participate
    if bid <= 0 and my_budget > 0:
        bid = 1.0
    elif bid <= 0 and my_budget <= 0: # If no budget, can't bid
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimally to secure water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from all alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None and prev.get('status') not in ['error', 'died']:
            yesterday_bids.append(prev['bid'])

    # Survival priority: If HP is critical, bid very aggressively
    if my_status['hp'] <= 3:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Reactive bidding based on yesterday's highest bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest bid was very high (e.g., Bob's range or higher)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            # Bid slightly above to win, but cap it to avoid overspending too much
            target_bid = min(DAILY_SALARY * 0.9, highest_prev_bid + 5)
            return min(my_status['budget'], target_bid)
        else:
            # Bids were moderate or low, be competitive but don't overpay
            # Adjust based on supply: if supply is low, be more aggressive
            if supply <= WATER_REQ * 1.5: # Tighter supply
                target_bid = max(DAILY_SALARY * 0.65, highest_prev_bid + 3)
            else: # More abundant supply
                target_bid = max(DAILY_SALARY * 0.55, highest_prev_bid + 1)
            return min(my_status['budget'], target_bid)

    # Default bidding logic if no strong signals from yesterday (e.g., Day 1 or all low bids)
    # Adjust based on my HP
    if my_status['hp'] <= 5:
        # Low HP, need water, bid aggressively
        return min(my_status['budget'], DAILY_SALARY * 0.8)
    else:
        # Healthy HP, bid moderately
        return min(my_status['budget'], DAILY_SALARY * 0.6)
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
        # If no opponents, bid a low but sufficient amount to secure water
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine bid based on yesterday's highest pressure and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If I am desperate (low HP), bid very high regardless of opponent's previous bid
        if my_status['hp'] <= 3:
            return min(my_status['budget'], DAILY_SALARY * 0.98) # Very aggressive

        # If highest previous bid was very high, it indicates strong competition
        if highest_prev_bid >= DAILY_SALARY * 0.85: # e.g., 127.5 for DAILY_SALARY=150
            # Not critically low HP (hp > 3), but competition is high
            # Bid just above the high previous bid, but capped to save budget if possible
            return min(my_status['budget'], max(highest_prev_bid + 2, DAILY_SALARY * 0.75))
        else: # Competition was moderate or low yesterday, and I'm not desperate
            # Bid slightly above the highest previous bid to secure water, but save budget
            return min(my_status['budget'], max(DAILY_SALARY * 0.6, highest_prev_bid + 2))
    
    # Fallback: No previous bids from alive opponents (e.g., first day or all opponents died)
    # Default strategy based on my HP and day
    if my_status['hp'] <= 3: # Critical HP
        return min(my_status['budget'], DAILY_SALARY * 0.9)
    elif day_context['day'] >= EPISODE_DAYS - 2: # Last 2 days, push for survival
        return min(my_status['budget'], DAILY_SALARY * 0.8)
    else: # Healthy HP, early/mid game
        return min(my_status['budget'], DAILY_SALARY * 0.65)
"""
