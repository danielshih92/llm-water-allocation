# ============================================================
# Experiment: exp_115
# Agent: Cindy
# Source: exp_115
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Base bid - start with a reasonable profit-margin bid
    bid_amount = DAILY_SALARY * 0.45 # Aim for ~55% profit

    # 2. Survival Override: If HP is critical, bid very aggressively
    if my_hp <= 2: # Critical HP: 1 or 2 days without water remaining
        bid_amount = DAILY_SALARY * 0.95 # Bid almost full salary
        if my_hp == 1: # Extremely critical, last chance
            bid_amount = DAILY_SALARY * 0.99 # Bid even higher
    elif my_hp <= 4: # Low HP: 3 or 4 days without water remaining
        bid_amount = DAILY_SALARY * 0.8 # High priority for water

    # 3. Adjust for Supply Scarcity (only if not in critical HP override)
    # This ensures HP-based desperation still dominates
    if my_hp > 4: # Only adjust for supply if HP is not critical
        if current_supply <= WATER_REQ + 2: # Very low supply, high competition
            bid_amount = max(bid_amount, DAILY_SALARY * 0.7)
        elif current_supply <= WATER_REQ * 2: # Moderate supply, still competitive
            bid_amount = max(bid_amount, DAILY_SALARY * 0.55)
        else: # Abundant supply, try to get it cheaper
            bid_amount = min(bid_amount, DAILY_SALARY * 0.35)

    # 4. React to Opponents' Yesterday Bids (only if not in critical HP override)
    yesterday_opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace')
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_opponent_bids.append(prev_trace['bid'])

    if yesterday_opponent_bids and my_hp > 2: # Only react to opponents if not in immediate danger
        max_yesterday_bid = max(yesterday_opponent_bids)
        avg_yesterday_bid = sum(yesterday_opponent_bids) / len(yesterday_opponent_bids)

        if max_yesterday_bid >= DAILY_SALARY * 0.8: # Opponents bid very high
            bid_amount = max(bid_amount, avg_yesterday_bid * 1.05) # Slightly above average
        elif max_yesterday_bid >= DAILY_SALARY * 0.5: # Opponents bid moderately
            bid_amount = max(bid_amount, avg_yesterday_bid * 1.02)
        else: # Opponents bid low
            bid_amount = min(bid_amount, avg_yesterday_bid * 0.95) # Try to bid slightly lower

    # 5. End-game push (if not already desperate)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp <= 5 and my_hp > 2: # Near end, need water but not critical
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    # Final bid constraints
    # Ensure bid is never more than budget and is positive
    final_bid = min(my_budget, max(1.0, bid_amount))

    # Explicitly ensure bid is a float for the game engine
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

    # If no opponents, bid just enough to get water cheaply
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) if my_status['budget'] > 0 else 0.0

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid strategy
    bid_amount = DAILY_SALARY * 0.5 # Start with a moderate bid

    # Adjust bid based on my current HP
    # Higher bid if HP is low
    if my_status['hp'] <= 2: # Critical HP
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4: # Low HP
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8)
    
    # Adjust bid based on competition from yesterday's bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest bid was very high, we might need to match or slightly exceed it
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid_amount = max(bid_amount, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid_amount = max(bid_amount, highest_prev_bid + 2)
        else: # Opponents bid low, try to win cheaply but don't drop too low
            bid_amount = min(bid_amount, highest_prev_bid + 10)

    # Adjust bid based on current day's supply relative to demand
    supply = day_context['supply']
    # If supply is very low (less than my requirement), competition is fierce
    if supply < WATER_REQ:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.9)
    # If supply is less than what all active players (including me) need
    elif supply < (num_alive_opponents + 1) * WATER_REQ:
        bid_amount = max(bid_amount, DAILY_SALARY * 0.7)
    # If supply is abundant, we can try to bid lower
    else:
        bid_amount = min(bid_amount, DAILY_SALARY * 0.4)

    # Adjust bid based on remaining days (end-game pressure)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last two days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.98) # Bid very high
    elif remaining_days <= 4: # Approaching end game
        bid_amount = max(bid_amount, DAILY_SALARY * 0.85)

    # Final bid must not exceed budget
    final_bid = min(my_status['budget'], bid_amount)

    # Ensure bid is at least 1.0 if we have budget and need water.
    # We always need water to maintain HP or increase it to EPISODE_DAYS.
    if my_status['budget'] > 0:
        final_bid = max(final_bid, 1.0)
    else: # Cannot bid if no budget
        final_bid = 0.0
    
    return float(final_bid)
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    base_bid = DAILY_SALARY * 0.65

    if my_hp <= 1:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp == 2:
        base_bid = DAILY_SALARY * 0.85
    elif my_hp == 3:
        base_bid = DAILY_SALARY * 0.75

    supply_pressure_factor = 1.0
    if current_supply < WATER_REQ * (len(alive_opponents) + 1) * 1.5:
        if current_supply <= MIN_SUPPLY + 2:
            supply_pressure_factor = 1.15
        elif current_supply <= MIN_SUPPLY + 5:
            supply_pressure_factor = 1.05
        elif current_supply >= MAX_SUPPLY - 2:
            supply_pressure_factor = 0.9

    base_bid *= supply_pressure_factor

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if my_hp <= 3:
            if highest_prev_bid >= base_bid * 0.9:
                final_bid = max(base_bid, highest_prev_bid + 5)
            else:
                final_bid = base_bid
        else:
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                final_bid = max(base_bid, highest_prev_bid * 0.9)
            elif highest_prev_bid >= base_bid * 0.9:
                final_bid = max(base_bid, highest_prev_bid + 1)
            else:
                final_bid = base_bid
    else:
        final_bid = base_bid

    final_bid = min(final_bid, my_budget)
    final_bid = max(0.0, final_bid)

    if EPISODE_DAYS - current_day == 0:
        final_bid = my_budget

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

    # Critical insight: supply range [15, 25], WATER_REQ = 13.
    # This means (supply // WATER_REQ) will always be 1.
    # Therefore, only ONE agent can fulfill their water requirement each day.
    # The highest bidder wins the water.

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Get yesterday's highest bid from *any* alive opponent
    highest_prev_bid_among_alive = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid_among_alive = max(highest_prev_bid_among_alive, prev_trace['bid'])

    # Determine my initial target bid
    target_bid = DAILY_SALARY * 0.7 # A generally competitive bid

    if highest_prev_bid_among_alive > 0:
        # If opponents were bidding, aim to slightly outbid the highest previous bid
        target_bid = max(target_bid, highest_prev_bid_among_alive + 1.0) # Bid just above previous max

    # Adjust bid based on my HP and no_water_days (urgency)
    # If HP is low (<=3) or I missed water yesterday, I MUST win.
    if my_status['hp'] <= 3 or my_status['no_water_days'] > 0:
        # Bid very aggressively, potentially going above salary to secure water
        my_bid = max(target_bid, DAILY_SALARY * 1.05) # Aggressive, slightly above salary
        my_bid = min(my_bid, my_status['budget']) # Cannot bid more than budget
    elif my_status['hp'] <= 5: # Medium urgency
        # Be aggressive, but not as desperate as low HP
        my_bid = max(target_bid, DAILY_SALARY * 0.9)
        my_bid = min(my_bid, my_status['budget'])
    else: # High HP, can afford to be more strategic
        # If the highest previous bid from opponents was already very high,
        # and I have good HP, I might consider backing off to save budget.
        # This is a "strategic skip" to make opponents overspend.
        if highest_prev_bid_among_alive > DAILY_SALARY * 0.9: # Opponents are bidding very high
            my_bid = DAILY_SALARY * 0.5 # Bid lower to save money, accepting potential HP loss
        else:
            my_bid = max(target_bid, DAILY_SALARY * 0.8) # Still aim to win, but with a cap
            my_bid = min(my_bid, my_status['budget'])

    # Final check: ensure bid is positive and within budget
    my_bid = max(my_bid, 0.01) # Minimum bid
    my_bid = min(my_bid, my_status['budget']) # Ensure not over budget

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        # No active opponents, bid minimally to secure water
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Calculate how many players can realistically get water given current supply
    # With supply range [15, 25] and WATER_REQ=13, this will always be 1.
    num_possible_winners = int(day_context['supply'] // WATER_REQ)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine a base bid strategy
    base_bid = DAILY_SALARY * 0.6 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # Given WATER_REQ=13 and supply_range=[15,25], num_possible_winners will always be 1.
        # High competition, only one winner possible (or very limited for two)
        # Try to outbid the highest previous bid more aggressively
        base_bid = max(DAILY_SALARY * 0.75, highest_prev_bid * 1.1)
    else:
        # If no previous bids, use a strong default
        base_bid = DAILY_SALARY * 0.75
    
    # Adjust bid based on my HP
    if my_status['hp'] <= 2: # Desperate for water
        base_bid = max(base_bid, DAILY_SALARY * 1.2) # Bid very high, potentially more than salary
    elif my_status['hp'] <= 5: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    # Adjust bid based on current day (late game pressure)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2 and my_status['hp'] < WATER_REQ * 2: # Near end and need water
        base_bid = max(base_bid, DAILY_SALARY * 1.1) # Bid aggressively to survive final days

    # Ensure bid does not exceed budget
    final_bid = min(my_status['budget'], base_bid)

    # Ensure a minimal bid if water is needed and budget allows
    if my_status['hp'] < WATER_REQ and my_status['budget'] > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.1)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
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

    if num_alive_opponents == 0:
        return min(my_budget, DAILY_SALARY * 0.1)

    david_status = opponents_status.get('David')
    david_is_alive = david_status and david_status['alive']

    base_bid = DAILY_SALARY * 0.5

    if my_hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base_bid = DAILY_SALARY * 0.75
    elif my_hp >= 8:
        base_bid = DAILY_SALARY * 0.4

    if current_day >= EPISODE_DAYS - 2 and my_hp < 5:
        base_bid = max(base_bid, DAILY_SALARY * 0.95)
    elif current_day >= EPISODE_DAYS - 4 and my_hp < 3:
        base_bid = max(base_bid, DAILY_SALARY * 0.9)

    if david_is_alive:
        david_previous_bid = 0
        if david_status.get('previous_trace') and david_status['previous_trace'].get('bid') is not None:
            david_previous_bid = david_status['previous_trace']['bid']

        if david_previous_bid > DAILY_SALARY * 0.6:
            base_bid = max(base_bid, david_previous_bid + (DAILY_SALARY * 0.05))
            base_bid = min(base_bid, DAILY_SALARY * 0.95)

    else:
        highest_other_prev_bid = 0
        for opp in alive_opponents:
            if opp['agent_id'] != 'David':
                prev = opp.get('previous_trace', {})
                if prev and prev.get('bid') is not None:
                    highest_other_prev_bid = max(highest_other_prev_bid, prev['bid'])

        if highest_other_prev_bid > 0:
            base_bid = max(base_bid, highest_other_prev_bid + (DAILY_SALARY * 0.05))
            base_bid = min(base_bid, DAILY_SALARY * 0.6)

    final_bid = max(0.0, min(my_budget, base_bid))

    if my_hp <= 1 and my_budget > 0:
        final_bid = my_budget

    total_water_needed_by_alive = sum([o['water_requirement'] for o in alive_opponents]) + WATER_REQ
    if current_supply >= total_water_needed_by_alive * 1.5 and num_alive_opponents < 3:
        final_bid = min(final_bid, DAILY_SALARY * 0.3)

    if final_bid == 0 and my_hp < 10 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)

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

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55 

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 1.3 
    elif my_status['hp'] <= 5:
        base_bid = DAILY_SALARY * 0.95 
    elif my_status['hp'] >= 8 and day_context['day'] < EPISODE_DAYS - 2:
        base_bid = DAILY_SALARY * 0.45 

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid > DAILY_SALARY * 1.2:
            base_bid = max(base_bid, highest_prev_bid * 0.9) 
        elif average_prev_bid > DAILY_SALARY * 0.8:
            base_bid = max(base_bid, average_prev_bid * 0.85) 

        if my_status['hp'] > 5 and highest_prev_bid < DAILY_SALARY * 0.8:
            base_bid = min(base_bid, highest_prev_bid + 5) 

    potential_winners = int(day_context['supply'] / WATER_REQ)
    
    if potential_winners <= num_alive_opponents:
        if potential_winners == 1 and num_alive_opponents > 0:
            base_bid = max(base_bid, DAILY_SALARY * 1.5) 
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.8) 
            if my_status['hp'] <= 5:
                base_bid = max(base_bid, DAILY_SALARY * 1.1)
    elif potential_winners > num_alive_opponents + 1:
        if my_status['hp'] > 5:
            base_bid = min(base_bid, DAILY_SALARY * 0.4) 
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.7) 

    final_bid = min(my_status['budget'], base_bid)
    
    if my_status['budget'] > 0:
        final_bid = max(1.0, final_bid)
    else:
        final_bid = 0.0

    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid - a safe amount to try and get water without overspending
    # Start with a bid that is a fraction of daily salary
    base_bid = DAILY_SALARY * 0.4

    # Adjust bid based on my HP (survival priority)
    if my_current_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.75
    elif my_current_hp >= 8 and current_day < EPISODE_DAYS / 2: # Healthy and early game, can afford to be a bit more frugal
        base_bid = DAILY_SALARY * 0.35

    # Analyze opponent's recent bids from 'previous_trace'
    highest_prev_bid = 0
    opponent_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            opponent_bids.append(prev_trace['bid'])
            if prev_trace['bid'] > highest_prev_bid:
                highest_prev_bid = prev_trace['bid']

    # If opponents are bidding high, increase my bid to stay competitive
    if highest_prev_bid > 0: # If there was any bidding activity yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very high competition detected
            base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid slightly
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate competition detected
            base_bid = max(base_bid, highest_prev_bid + 2)

    # Adjust bid based on current supply and number of active competitors
    # This estimates how much water is available per active agent
    if num_alive_opponents > 0: # If there are other agents competing
        effective_competitors = num_alive_opponents + 1 # Include myself
        water_per_competitor_if_equal = current_supply / effective_competitors

        if water_per_competitor_if_equal < WATER_REQ * 0.8: # Very tight supply per person
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
        elif water_per_competitor_if_equal < WATER_REQ * 1.2: # Moderately tight supply
            base_bid = max(base_bid, DAILY_SALARY * 0.65)
    else: # No other alive opponents, bid minimally to save budget
        base_bid = DAILY_SALARY * 0.05 # Bid very low if no competition

    # Adjust bid based on remaining days (end-game urgency)
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last couple of days, bid aggressively to survive
        base_bid = max(base_bid, DAILY_SALARY * 0.98)
    elif remaining_days <= 4: # Mid-to-late game
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Ensure bid does not exceed budget and is not negative
    final_bid = min(my_current_budget, base_bid)
    return max(0.0, final_bid)
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
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    current_bid = DAILY_SALARY * 0.65

    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        current_bid = DAILY_SALARY * 0.95
    elif day_context['day'] >= EPISODE_DAYS - 2:
        current_bid = DAILY_SALARY * 0.85

    highest_prev_bid = 0.0
    bob_highest_bid_yesterday = False

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                opp_bid = prev['bid']
                if opp_bid > highest_prev_bid:
                    highest_prev_bid = opp_bid
                    bob_highest_bid_yesterday = (opp_id == "Bob")
                elif opp_bid == highest_prev_bid and opp_id == "Bob":
                    bob_highest_bid_yesterday = True

    if highest_prev_bid > 0:
        if bob_highest_bid_yesterday and highest_prev_bid >= DAILY_SALARY * 0.8:
            current_bid = max(current_bid, highest_prev_bid + 5)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            current_bid = max(current_bid, highest_prev_bid + 3)
        else:
            current_bid = max(current_bid, highest_prev_bid + 1)

    return min(my_status['budget'], current_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents are alive, bid minimum to conserve budget
    if not alive_opponents:
        return min(my_status['budget'], 1.0)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default bid if no previous bids or low pressure
    # This bid aims to be competitive but conservative
    bid_amount = DAILY_SALARY * 0.6 # Base bid: 90

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If opponents were very aggressive yesterday (bidding significantly above my daily salary)
        if highest_prev_bid >= DAILY_SALARY * 1.0: # If highest bid was >= 150
            if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1: # Critical HP or missed water
                bid_amount = max(DAILY_SALARY * 1.1, highest_prev_bid * 1.05) # Be very aggressive, potentially drawing from budget
            elif my_status['hp'] <= 6: # Low HP, but not critical
                bid_amount = max(DAILY_SALARY * 0.9, highest_prev_bid * 1.02) # Aggressive
            else: # Healthy HP, can conserve a bit more, but still need to be competitive
                bid_amount = max(DAILY_SALARY * 0.7, highest_prev_bid * 0.95) # Try to get water, but don't overpay too much
        
        # If opponents were moderately aggressive (bidding between 70-100% of my daily salary)
        elif highest_prev_bid >= DAILY_SALARY * 0.7: # If highest bid was >= 105
            if my_status['hp'] <= 4 or my_status['no_water_days'] >= 1: # Low HP or missed water
                bid_amount = max(DAILY_SALARY * 0.9, highest_prev_bid * 1.05)
            else: # Healthy HP
                bid_amount = max(DAILY_SALARY * 0.65, highest_prev_bid * 1.02)
        
        # If opponents were generally low bidders (below 70% of my daily salary)
        else:
            if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1: # Critical HP
                bid_amount = DAILY_SALARY * 0.9 # Still bid high to secure water
            else: # Healthy HP, can afford to be more conservative
                bid_amount = max(DAILY_SALARY * 0.5, highest_prev_bid * 1.1) # Slightly outbid, but keep base low

    # Adjust bid based on current day and remaining days
    # As the game progresses, it might be necessary to be more aggressive
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last couple of days, go for it
        if my_status['hp'] > 0: # Only if I'm still in the game
            bid_amount = max(bid_amount, DAILY_SALARY * 1.2) # Try to win at the end
    elif remaining_days <= 4: # Mid-to-late game
        bid_amount = max(bid_amount, DAILY_SALARY * 0.8) # Ensure competitiveness

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], bid_amount)
    
    # Ensure bid is at least 1.0 if budget allows, to attempt to get water
    return max(1.0, final_bid)
"""
