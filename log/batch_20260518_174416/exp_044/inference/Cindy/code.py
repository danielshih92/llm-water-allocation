# ============================================================
# Experiment: exp_044
# Agent: Cindy
# Source: exp_044
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimally to save budget.
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # --- Desperation check ---
    desperation_bid = DAILY_SALARY * 0.95 # Very high bid
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], desperation_bid)

    # --- React to previous day's bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid based on competition
    base_bid = DAILY_SALARY * 0.6 # Default moderate bid

    if yesterday_bids:
        highest_prev_opp_bid = max(yesterday_bids)
        # If opponents were bidding high, increase my bid
        if highest_prev_opp_bid >= DAILY_SALARY * 0.7: # High competition threshold
            base_bid = min(DAILY_SALARY * 0.85, highest_prev_opp_bid + 5) # Try to outbid slightly, but cap it
        else:
            # If bids were moderate, maintain a competitive but not overly aggressive stance
            base_bid = max(DAILY_SALARY * 0.6, highest_prev_opp_bid + 1)
    
    # Adjust bid based on current budget (conserve if non-desperate and low budget)
    if my_status['budget'] < DAILY_SALARY * 1.5 and my_status['hp'] > 2:
        base_bid = min(base_bid, DAILY_SALARY * 0.7) 

    # Ensure bid never exceeds budget
    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure bid is at least a minimum to be considered
    final_bid = max(final_bid, DAILY_SALARY * 0.1)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: A moderate starting point
    bid = DAILY_SALARY * 0.65

    # 1. HP-based urgency (highest priority)
    if my_hp <= 1: # Critical, must win
        bid = DAILY_SALARY * 0.99
    elif my_hp <= 3: # Very low HP
        bid = DAILY_SALARY * 0.90
    elif my_hp <= 5: # Low HP
        bid = DAILY_SALARY * 0.80

    # 2. Opponent Reaction based on previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding high, we need to be competitive
        if highest_prev_bid > DAILY_SALARY * 0.75: # If highest bid was quite high
            bid = max(bid, highest_prev_bid + 2.0) # Bid slightly above to outcompete
        elif highest_prev_bid > DAILY_SALARY * 0.6: # If highest bid was moderately high
            bid = max(bid, highest_prev_bid + 1.0) # Bid slightly above

    # 3. Supply-based adjustment
    # If supply is very low, competition is higher
    if current_supply < WATER_REQ * (num_alive_opponents + 1) * 0.7: # Less than 70% of total needs
        bid *= 1.1 # Increase bid
    elif current_supply >= MAX_SUPPLY: # Abundant supply
        bid *= 0.9 # Decrease bid, might not need to bid as high

    # 4. Day-based adjustment (late game desperation)
    if current_day >= EPISODE_DAYS - 2: # Last two days
        bid = max(bid, DAILY_SALARY * 0.85) # Be very aggressive to survive till the end

    # Ensure bid does not exceed budget and is not negative
    final_bid = min(my_budget, bid)
    final_bid = max(0.0, final_bid)

    # If budget is very low but HP is not critical, maybe conserve a bit
    if my_budget < DAILY_SALARY * 0.5 and my_hp > 5:
        final_bid = min(final_bid, DAILY_SALARY * 0.6) # Don't empty budget unless desperate

    return round(final_bid, 2)
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

    # Strategy 1: If I'm the only one left, bid conservatively
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Strategy 2: Adjust bid based on opponents' previous bids and my HP
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents are bidding very high (e.g., >= 85% of my daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If my HP is stable, consider letting them overbid and conserve budget
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # If my HP is critical (<=3), I need water, bid aggressively
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # Opponents are not bidding excessively high
            # Bid slightly above the highest previous bid, but at least 50% of salary
            # This aims to win without overpaying too much
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    else:
        # Strategy 3: No previous bids or initial days, bid based on my HP
        if my_status['hp'] <= 2: # Critical HP (can survive 2 more days without water)
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        else: # Stable HP
            return min(my_status['budget'], DAILY_SALARY * 0.55)
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
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    aggressive_threshold = DAILY_SALARY * 0.6

    if highest_prev_bid >= aggressive_threshold:
        bid = max(DAILY_SALARY * 0.65, highest_prev_bid + 5)
    else:
        bid = DAILY_SALARY * 0.7

    return min(my_status['budget'], bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    # Base bid - a reasonable starting point
    # Cindy has a high salary, so can afford to be competitive
    my_bid = DAILY_SALARY * 0.6

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Scenario 1: No opponents left, bid minimally
    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Scenario 2: My HP is critically low, prioritize survival
    if my_status['hp'] <= 2:
        my_bid = DAILY_SALARY * 0.98 # Very aggressive to ensure water
    elif my_status['hp'] == 3:
        my_bid = max(my_bid, DAILY_SALARY * 0.85) # Aggressive

    # Analyze yesterday's bids and opponent states
    yesterday_bids = []
    desperate_opponents_count = 0
    
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        if opp['hp'] <= 3: # Opponent is low on HP
            desperate_opponents_count += 1

    # Adjust bid based on opponent behavior and supply scarcity
    num_slots = int(day_context['supply'] // WATER_REQ) # Critical: int() for index-like value
    total_competitors = num_alive_opponents + 1 # Including myself

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yester_bids)

        # If water is scarce (not enough for everyone to get full requirement)
        if num_slots < total_competitors:
            if my_status['hp'] <= 3: # Already desperate, ensure bid is very high
                my_bid = max(my_bid, max_prev_bid + 5)
            else: # Healthy but scarcity, be competitive
                my_bid = max(my_bid, avg_prev_bid * 1.15, DAILY_SALARY * 0.7) # Bid slightly above average or a higher default
        else: # Enough water for everyone
            if my_status['hp'] > 5: # Healthy, try to save
                my_bid = min(my_bid, max_prev_bid * 0.9, DAILY_SALARY * 0.5) # Bid slightly below max previous, or a lower default
            else: # Not super healthy, stay competitive
                my_bid = max(my_bid, avg_prev_bid * 0.95) # Stay close to average

    # If there are desperate opponents and water is scarce, expect higher bids
    if desperate_opponents_count > 0 and num_slots < total_competitors:
        if my_status['hp'] <= 5: # If I'm also not super healthy, I need to be more aggressive
            my_bid = max(my_bid, DAILY_SALARY * 0.9) # Expect high competition

    # End game strategy (last 2 days)
    if day_context['day'] >= EPISODE_DAYS - 2:
        if my_status['hp'] <= 1: # Super critical
            my_bid = DAILY_SALARY * 0.99
        elif my_status['hp'] <= 3: # Critical
            my_bid = max(my_bid, DAILY_SALARY * 0.95)
        else: # Healthy in end game, save if possible
            my_bid = min(my_bid, DAILY_SALARY * 0.4)

    # Ensure bid is within budget and non-negative
    final_bid = min(my_status['budget'], my_bid)
    final_bid = max(0.0, final_bid)
    
    # Round to 2 decimal places
    return round(final_bid, 2)
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
    num_alive_agents = len(alive_opponents) + 1

    # Base bid: a moderate amount
    bid = DAILY_SALARY * 0.5 # 75

    # 1. Desperation check (My HP and no_water_days)
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 2:
        bid = DAILY_SALARY * 0.95 # Very high bid for survival
    elif my_status['hp'] <= 5 or my_status['no_water_days'] >= 1:
        bid = DAILY_SALARY * 0.8 # High bid if moderately desperate

    # 2. React to opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents bid high, match or slightly exceed, unless I'm not desperate
        if highest_prev_bid >= DAILY_SALARY * 0.8: # High competition
            if my_status['hp'] > 5 and my_status['no_water_days'] == 0:
                # If not desperate, try to win by a small margin
                bid = min(bid, highest_prev_bid + 1)
            else:
                bid = max(bid, highest_prev_bid + 3) # Outbid if desperate
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate competition
            bid = max(bid, highest_prev_bid + 2)
        else: # Low competition
            bid = max(bid, highest_prev_bid + 1)

    # 3. Adjust based on supply scarcity
    supply = day_context['supply']
    possible_winners = int(supply // WATER_REQ) # How many agents *can* win water

    if possible_winners < num_alive_agents:
        # Scarcity: Increase bid, especially if I need water
        if my_status['hp'] <= 5 or my_status['no_water_days'] >= 1:
            bid = bid * 1.1 # Increase by 10%
            bid = min(bid, DAILY_SALARY * 0.98) # Cap it
        else:
            # If not desperate, increase slightly but stay conservative
            bid = bid * 1.05
            bid = min(bid, DAILY_SALARY * 0.9)
    elif possible_winners >= num_alive_agents + 1:
        # Abundance: Try to get water cheaper
        if my_status['hp'] > 5 and my_status['no_water_days'] == 0:
            bid = min(bid, DAILY_SALARY * 0.4) # Bid low
        else:
            bid = min(bid, DAILY_SALARY * 0.6) # Still competitive but not overpaying

    # 4. Budget management for remaining days
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 1: # Last day or second to last
        bid = my_status['budget'] # Bid all if desperate on last days
    else:
        # Ensure budget is maintained for future days.
        # Don't spend more than a certain fraction of remaining budget, unless desperate.
        max_affordable_today = my_status['budget'] - (remaining_days * (DAILY_SALARY * 0.1)) # Keep 10% salary per day as buffer
        if max_affordable_today < 0: # If buffer calculation makes it negative
            max_affordable_today = my_status['budget'] # Just bid what's left
        bid = min(bid, max_affordable_today)

    # Final check: bid must be positive and not exceed current budget
    final_bid = max(1.0, min(bid, my_status['budget']))

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MAX_DAYS = 10

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    # Default bids for opponents if no trace is available or they are new/dead
    alex_prev_bid = DAILY_SALARY * 0.9 # Alex is known to be aggressive
    bob_prev_bid = DAILY_SALARY * 0.55 # Bob is known to be conservative

    # Update with actual yesterday's bids if available and opponent is alive
    if 'Alex' in opponents_status and opponents_status['Alex']['alive']:
        alex_trace = opponents_status['Alex'].get('previous_trace', {})
        if alex_trace and alex_trace.get('bid') is not None:
            alex_prev_bid = alex_trace['bid']

    if 'Bob' in opponents_status and opponents_status['Bob']['alive']:
        bob_trace = opponents_status['Bob'].get('previous_trace', {})
        if bob_trace and bob_trace.get('bid') is not None:
            bob_prev_bid = bob_trace['bid']
    
    # Determine a base competitive bid based on opponents' yesterday behavior
    # Aim to outbid Bob, and potentially compete with Alex without overspending when not critical
    competitive_base_bid = max(bob_prev_bid + 5, DAILY_SALARY * 0.6) # Ensure we beat Bob and have a floor

    # If Alex was very aggressive yesterday, consider that for the base, but don't match if HP is good
    if alex_prev_bid > DAILY_SALARY * 1.0: 
        competitive_base_bid = max(competitive_base_bid, alex_prev_bid * 0.8) 

    # HP-based bidding strategy
    bid_amount = 0.0
    if my_current_hp <= 1: # Critical HP: Must get water at almost any cost
        bid_amount = DAILY_SALARY * 1.45 # Aggressive, slightly above Alex's max observed bid
    elif my_current_hp == 2: # Low HP: High urgency
        bid_amount = DAILY_SALARY * 1.15 # Competitive, aims to secure water
    elif my_current_hp == 3: # Moderate HP: Be careful but still prioritize water
        bid_amount = competitive_base_bid * 1.05 # Slightly above the calculated competitive base
    else: # Healthy HP (my_current_hp >= 4): Try to save budget
        bid_amount = competitive_base_bid * 0.9 # Bid slightly below the competitive base, but still reasonable

    # Adjust for supply scarcity, especially when not in critical HP state
    if current_supply <= WATER_REQ + 2: # Supply is very tight (e.g., 15-18 for 13 water)
        if my_current_hp >= 3: # Only increase if not already desperate
            bid_amount = bid_amount * 1.15
    elif current_supply >= 2 * WATER_REQ - 2: # Supply is relatively high (e.g., 24-25)
        if my_current_hp >= 3: # Only decrease if not desperate
            bid_amount = bid_amount * 0.9

    # End-game adjustment: If few days left, be more aggressive to ensure survival
    remaining_days = MAX_DAYS - current_day + 1
    if remaining_days <= 3:
        if my_current_hp <= 2: # Still low HP, really push
            bid_amount = max(bid_amount, DAILY_SALARY * 1.35)
        elif my_current_hp <= 4: # Moderate HP, ensure survival
            bid_amount = max(bid_amount, DAILY_SALARY * 0.95)

    # Ensure bid does not exceed budget and is non-negative
    final_bid = max(0.0, min(bid_amount, my_current_budget))

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

    base_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.8
    elif my_status['hp'] <= 6 and day_context['day'] > EPISODE_DAYS / 2:
        base_bid = DAILY_SALARY * 0.75
    
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] <= 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif remaining_days <= 3 and my_status['hp'] <= 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_status['hp'] > 5:
                base_bid = max(base_bid, highest_prev_bid * 0.95)
            else:
                base_bid = max(base_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            base_bid = max(base_bid, highest_prev_bid * 1.05)
        else:
            base_bid = max(base_bid, highest_prev_bid + 1)
            
    if day_context['supply'] <= 17:
        base_bid += 5

    final_bid = min(my_status['budget'], base_bid)
    
    if final_bid < DAILY_SALARY * 0.1 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)

    return final_bid
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

    # If no opponents, bid a safe amount to secure water cheaply
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    total_opponent_water_req = 0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
        total_opponent_water_req += opp['water_requirement']

    # Determine base bid based on my health
    current_bid = DAILY_SALARY * 0.55 # Default moderate bid

    if my_status['hp'] <= 2:
        current_bid = DAILY_SALARY * 0.95 # Desperate bid
    elif my_status['hp'] <= 4:
        current_bid = DAILY_SALARY * 0.85 # High urgency
    elif my_status['hp'] <= 6:
        current_bid = DAILY_SALARY * 0.7 # Moderate urgency

    # Adjust based on day progression (become slightly more aggressive later)
    # day_context['day'] is 1-indexed. (EPISODE_DAYS - 1) to avoid division by zero if EPISODE_DAYS is 1
    day_progress_factor = (day_context['day'] - 1) / (EPISODE_DAYS - 1) if EPISODE_DAYS > 1 else 0
    current_bid += (DAILY_SALARY * 0.15) * day_progress_factor # Up to 15% higher for later days

    # React to yesterday's bids if available
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # Threshold for 'very high' opponent bidding
        high_bid_threshold = DAILY_SALARY * 0.85

        if highest_prev_bid >= high_bid_threshold:
            # Opponents are bidding very high.
            if my_status['hp'] > 5: # If healthy, try to save budget, but still be competitive
                # Bid competitively but not desperately. Aim to secure water without overpaying if possible.
                current_bid = max(current_bid, DAILY_SALARY * 0.7) # Ensure a solid bid (105) but not max
            else: # If not healthy, bid very aggressively to survive
                current_bid = DAILY_SALARY * 0.98 # Almost max salary (147)
        else:
            # Opponents are not bidding extremely high. Bid slightly above the highest previous bid or my base.
            current_bid = max(current_bid, highest_prev_bid + 2.0) # Ensure to outbid by a small margin
    
    # Adjust for supply and demand as a final multiplier, but with a controlled impact
    total_demand = WATER_REQ + total_opponent_water_req
    supply = day_context['supply']

    if supply > 0 and total_demand > supply: # Only if demand exceeds supply
        # Factor increases bid by up to 20% if demand is twice supply.
        competition_multiplier = 1.0 + (total_demand / supply - 1.0) * 0.2
        current_bid *= competition_multiplier
    
    # Ensure bid is within budget and non-negative
    final_bid = min(my_status['budget'], current_bid)
    final_bid = max(final_bid, 0.0) # Cannot bid negative

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

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # If I am the only one left, bid minimal to save budget
    if num_alive_opponents == 0:
        return max(0.1, min(my_budget, 1.0))

    # --- Determine base bid strategy ---
    # A base bid that is competitive given the observed high bids from strong opponents historically
    base_bid = DAILY_SALARY * 0.75 # Default: 112.5

    # --- Adjust bid based on my HP (survival priority) ---
    if my_hp <= 1: # Critical survival
        base_bid = DAILY_SALARY * 0.98 # Bid very high, almost full salary
    elif my_hp <= 2: # High priority survival
        base_bid = DAILY_SALARY * 0.9 # High bid
    elif my_hp <= 4: # Moderate priority
        base_bid = DAILY_SALARY * 0.85 # Still aggressive

    # --- Adjust bid based on opponent's previous day bids ---
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = 0
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)

    # If highest opponent bid yesterday was significant, try to outbid it slightly
    if max_prev_bid > DAILY_SALARY * 0.6: # If max_prev_bid was > 90
        base_bid = max(base_bid, max_prev_bid + 2) # Try to outbid by a small margin
    elif max_prev_bid > 0: # If there was a bid, but not super high, just slightly above
        base_bid = max(base_bid, max_prev_bid + 1)

    # --- Adjust bid based on supply and number of competitors ---
    # If supply is very tight, competition for water is higher
    if current_supply < 2 * WATER_REQ and num_alive_opponents > 1: # Enough for one, but not two full
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Increase aggressiveness

    # --- Adjust bid based on day progress ---
    # As the game progresses, if HP is not full, become more aggressive to survive
    if current_day >= EPISODE_DAYS * 0.7 and my_hp < 5: # Last 30% of days, HP not great
        base_bid = max(base_bid, DAILY_SALARY * 0.9)
    elif current_day >= EPISODE_DAYS * 0.5 and my_hp < 3: # Mid-game, HP low
        base_bid = max(base_bid, DAILY_SALARY * 0.95)

    # Final bid calculation
    final_bid = base_bid

    # Ensure the bid does not exceed available budget
    final_bid = min(my_budget, final_bid)

    # Ensure the bid is positive (minimum bid to participate)
    return max(0.1, final_bid)
"""
