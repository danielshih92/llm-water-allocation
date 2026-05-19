# ============================================================
# Experiment: exp_101
# Agent: Cindy
# Source: exp_101
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_competitors = len(alive_opponents) + 1

    # If I'm the only one left, bid minimal amount to get water
    if num_competitors == 1:
        return min(my_status['budget'], 1)

    # Calculate total water demand from all active players
    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    # Analyze yesterday's bids from opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider valid bids, not errors
        if prev and prev.get('bid') is not None and prev.get('status') != 'error':
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine base bid strategy
    base_bid = DAILY_SALARY * 0.4  # Moderate starting point

    # Adjust based on my HP (survival priority)
    if my_status['hp'] <= 2:  # Critical HP, need water desperately
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:  # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.7)

    # Adjust based on supply scarcity
    if day_context['supply'] < total_water_needed:  # Water is scarce
        if day_context['supply'] <= WATER_REQ + (WATER_REQ / 2) and num_competitors > 1: # Very tight supply
            base_bid = max(base_bid, DAILY_SALARY * 0.85) # Ensure high bid
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.65) # Increase bid for scarcity
    else: # Supply is sufficient, can try to save money
        base_bid = min(base_bid, DAILY_SALARY * 0.3)

    # Adjust based on opponent's previous high bid
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            base_bid = max(base_bid, highest_prev_bid + 5) # Bid slightly higher than them
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Opponents were moderately aggressive
            base_bid = max(base_bid, highest_prev_bid + 2)
        else: # Opponents bid low, try to save but stay competitive
            base_bid = min(base_bid, highest_prev_bid + 1)

    # End-game strategy (last few days)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last 2 days, go all out if needed
        if my_status['hp'] <= remaining_days: # If HP is critical for remaining days
            base_bid = max(base_bid, my_status['budget'] * 0.95) # Bid almost everything
        else:
            base_bid = max(base_bid, DAILY_SALARY * 0.75) # Still aggressive

    # Final bid must be at least 1 and not exceed budget
    final_bid = max(1, min(my_status['budget'], base_bid))

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

    base_bid = DAILY_SALARY * 0.55
    if day_context['day'] >= EPISODE_DAYS - 2: 
        base_bid = DAILY_SALARY * 0.8

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if my_status['hp'] <= 2: 
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    elif my_status['hp'] == 3: 
        base_bid = max(base_bid, DAILY_SALARY * 0.75)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.7: 
            if my_status['hp'] > 3: 
                base_bid = max(base_bid, highest_prev_bid * 1.02)
            else: 
                base_bid = max(base_bid, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.4:
            base_bid = max(base_bid, highest_prev_bid + 2.0)
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.4)

    total_water_needed = WATER_REQ 
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    if day_context['supply'] < total_water_needed:
        scarcity_factor = (total_water_needed - day_context['supply']) / total_water_needed
        base_bid = max(base_bid, base_bid * (1 + scarcity_factor * 0.5))

    final_bid = min(my_status['budget'], base_bid)

    if my_status['budget'] > 0 and my_status['hp'] > 0 and final_bid < DAILY_SALARY * 0.1:
        final_bid = max(final_bid, DAILY_SALARY * 0.1)

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    total_water_needed_by_alive = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_alive += opp['water_requirement']

    base_bid_value = DAILY_SALARY * 0.6

    if current_supply < total_water_needed_by_alive:
        base_bid_value = DAILY_SALARY * 0.8
    elif current_supply > total_water_needed_by_alive * 1.5:
        base_bid_value = DAILY_SALARY * 0.4
    
    if my_hp <= 2:
        bid = DAILY_SALARY * 0.99
    elif my_hp <= 4:
        bid = DAILY_SALARY * 0.85
    else:
        bid = base_bid_value

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp <= 3:
                bid = max(bid, highest_prev_bid * 1.05)
            else:
                bid = max(bid, highest_prev_bid * 1.01)
        elif highest_prev_bid >= DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 2)
        else:
            bid = max(bid, highest_prev_bid + 1)

    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_hp > 0:
        if my_hp <= 2:
            bid = max(bid, DAILY_SALARY * 0.99)
        elif my_budget > DAILY_SALARY * 0.5:
            bid = max(bid, DAILY_SALARY * 0.9)

    bid = min(my_budget, bid)
    bid = max(0.01, bid)

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

    my_current_hp = my_status['hp']
    my_current_budget = my_status['budget']
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: A reasonable fraction of daily salary
    base_bid = DAILY_SALARY * 0.65

    # Adjust bid based on my HP
    if my_current_hp <= 1: # Critical
        base_bid = DAILY_SALARY * 1.2
    elif my_current_hp <= 3: # Low
        base_bid = DAILY_SALARY * 0.9
    elif my_current_hp <= 5: # Moderate
        base_bid = DAILY_SALARY * 0.75

    # Analyze opponents' previous bids from 'previous_trace'
    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    # If there were previous bids, adjust based on the highest
    if yesterday_bids:
        max_yesterday_bid = max(yesterday_bids)
        # If competition was high yesterday, increase bid to stay competitive
        if max_yesterday_bid > DAILY_SALARY * 0.7:
            base_bid = max(base_bid, max_yesterday_bid + 5)
        elif max_yesterday_bid > DAILY_SALARY * 0.5:
            base_bid = max(base_bid, max_yesterday_bid + 2)

    # Adjust bid based on supply-demand pressure
    # Calculate how many water units are available. Use int() for safety.
    available_water_units = int(current_supply // WATER_REQ)

    # If no water units available, only bid if desperate, otherwise minimal
    if available_water_units == 0:
        if my_current_hp <= 2:
            final_bid = min(my_current_budget, DAILY_SALARY * 1.0) # Still try if desperate
        else:
            final_bid = 0.01 # Don't waste money if no water can be won
    else:
        # Number of agents (including myself) competing for water
        num_potential_buyers = num_alive_opponents + 1

        if num_potential_buyers > available_water_units:
            # High competition: increase bid
            # The more bidders than available units, the higher the pressure
            pressure_factor = (num_potential_buyers - available_water_units) / num_potential_buyers
            final_bid = base_bid * (1 + pressure_factor * 0.6) # Scale up bid more aggressively
        else:
            # Low competition: can be more conservative
            final_bid = base_bid * 0.9 # Slightly reduce bid

    # End-game strategy: bid more aggressively on last days if HP is low
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2 and my_current_hp < WATER_REQ * 2: # If close to dying and near end
        final_bid = max(final_bid, DAILY_SALARY * 1.3) # Bid very high to secure water

    # Ensure bid is within budget and positive
    final_bid = max(0.01, final_bid) # Minimum bid
    final_bid = min(final_bid, my_current_budget) # Cannot bid more than budget

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10 # From meta-round state

    day = day_context['day']
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    # Base bid factor - starts moderate
    bid_factor = 0.5

    # Prioritize survival if HP is low or I missed water yesterday
    if my_hp <= 2:
        bid_factor = 0.95 # Very aggressive
    elif my_hp <= 4:
        bid_factor = 0.8 # Aggressive
    elif my_no_water_days >= 1:
        bid_factor = max(bid_factor, 0.85) # Ensure water if missed yesterday

    # Increase bid aggressiveness in later days
    if day >= EPISODE_DAYS - 3: # Last 3 days
        bid_factor = max(bid_factor, 0.9) # Highly aggressive
    elif day >= EPISODE_DAYS - 5: # Mid-late game
        bid_factor = max(bid_factor, 0.7)

    current_bid = DAILY_SALARY * bid_factor

    highest_prev_bid = 0
    num_strong_competitors = 0 # Agents likely to compete fiercely

    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])
            
            # Identify strong competitors (e.g., high salary, similar water needs, or demonstrated high bidding)
            if opp['daily_salary'] >= DAILY_SALARY * 0.9 and opp['water_requirement'] >= WATER_REQ * 0.8:
                num_strong_competitors += 1
            elif prev_trace and prev_trace.get('bid', 0) > DAILY_SALARY * 0.7:
                 num_strong_competitors += 1 # Also count those who bid high yesterday as strong

    # Adjust bid based on highest previous bid from opponents
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.7: # Opponents are bidding high
            # Try to outbid slightly, but not excessively to save budget
            current_bid = max(current_bid, highest_prev_bid * 1.05)
        else: # Opponents bid moderately
            current_bid = max(current_bid, highest_prev_bid + 5)

    # Adjust bid based on supply
    # If supply is very tight, competition is higher
    if supply <= WATER_REQ + 5: # Supply is tight (e.g., 15-18 for my 13 req)
        current_bid *= 1.1
        if num_strong_competitors > 0:
            current_bid *= 1.15 # Even more aggressive if strong competition and tight supply
    elif supply >= 20: # Supply is abundant (e.g., 20-25)
        if num_strong_competitors == 0:
            current_bid = min(current_bid, DAILY_SALARY * 0.4) # Conserve budget if no strong competition
        else:
            current_bid *= 0.9 # Slightly reduce bid if supply is high, even with competitors

    # Ensure bid does not exceed current budget
    final_bid = min(my_budget, current_bid)

    # Ensure a minimum bid to stay in the game, unless budget is zero
    if final_bid < DAILY_SALARY * 0.1 and my_budget > 0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)
    elif my_budget == 0:
        final_bid = 0

    # Ensure the bid is non-negative
    final_bid = max(0, final_bid)

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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    current_day = day_context['day']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # If no opponents, bid minimal amount to ensure survival if needed
    if not alive_opponents:
        # If I need water to survive remaining days (assuming 1HP/day loss without water)
        if my_hp < EPISODE_DAYS - current_day + 1:
            return min(my_budget, DAILY_SALARY * 0.1) # Small bid to get water
        return 0.01 # No immediate need, bid minimal

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Determine base bid strategy
    bid_amount = DAILY_SALARY * 0.6 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very aggressive (like Eric's max bids)
        if highest_prev_bid >= DAILY_SALARY * 1.0:
            if my_hp <= 2: # Critical HP, must win
                bid_amount = highest_prev_bid + 10 # Try to outbid significantly
            elif my_hp <= 4: # Low HP
                bid_amount = highest_prev_bid + 5 # Try to outbid
            else: # Healthy HP, can be slightly less aggressive but still competitive
                bid_amount = max(DAILY_SALARY * 0.9, highest_prev_bid + 1)
        # If highest previous bid was moderately high (like Alex's average bids)
        elif highest_prev_bid >= DAILY_SALARY * 0.75:
            if my_hp <= 3: # Low HP, need to secure water
                bid_amount = max(DAILY_SALARY * 1.0, highest_prev_bid + 5)
            else: # Healthy HP
                bid_amount = max(DAILY_SALARY * 0.8, highest_prev_bid + 1)
        # If highest previous bid was low (Bob, David)
        else:
            bid_amount = max(DAILY_SALARY * 0.6, highest_prev_bid * 1.2) # Be competitive but not overspend
    
    # Override if HP is critically low, regardless of previous bids
    if my_hp <= 1:
        bid_amount = DAILY_SALARY * 1.2 # Must win, bid very high
    elif my_hp <= 2:
        bid_amount = max(bid_amount, DAILY_SALARY * 1.1) # Strong bid
    
    # Override if it's late in the game
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2: # Last 2 days
        bid_amount = max(bid_amount, DAILY_SALARY * 1.15) # Be very aggressive
    elif remaining_days <= 4: # Last 4 days
        bid_amount = max(bid_amount, DAILY_SALARY * 0.95) # Be aggressive

    # Ensure bid does not exceed budget
    final_bid = min(my_budget, bid_amount)
    
    # Ensure bid is at least a minimal amount if budget allows, to participate
    final_bid = max(final_bid, 0.01)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    current_day = day_context['day']
    current_supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Scenario 1: No opponents left, bid minimally to secure water
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Scenario 2: Critical HP or missed water yesterday, bid aggressively
    if my_hp <= 2 or my_no_water_days >= 1:
        # Bid very aggressively, scaled by how many days without water
        aggressive_bid = DAILY_SALARY * (0.9 + my_no_water_days * 0.05)
        return min(my_budget, aggressive_bid)

    # Scenario 3: React to yesterday's opponent bids and general competition
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Default base bid if no strong signals or yesterday's bids were low
    base_bid = DAILY_SALARY * 0.55

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if highest_prev_bid >= DAILY_SALARY * 0.85: # Very high competition yesterday
            # If my HP is good, bid slightly above the highest. If not, bid more aggressively.
            if my_hp > 5: # Relatively healthy
                base_bid = highest_prev_bid * 1.02
            else: # Moderate HP, need to be more competitive
                base_bid = highest_prev_bid * 1.05
        elif average_prev_bid > DAILY_SALARY * 0.6: # Moderate competition yesterday
            base_bid = average_prev_bid * 1.1 # Bid slightly above average
        else:
            # If bids were low, ensure we're competitive but don't overspend
            base_bid = max(base_bid, average_prev_bid * 1.05)

    # Adjust bid based on current supply scarcity and number of opponents
    # Lower supply means higher competition, more opponents means higher competition
    supply_pressure_factor = 1.0 - ((current_supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    opponent_pressure_factor = num_alive_opponents * 0.05

    # Apply these factors to the base bid, but don't let it become too extreme if already high
    if base_bid < DAILY_SALARY * 0.8: # Only scale if not already in a high-bid state
        base_bid *= (1.0 + supply_pressure_factor * 0.1 + opponent_pressure_factor * 0.1)

    # Final bid calculation, ensuring it's within budget and at least 1.0
    final_bid = min(my_budget, max(1.0, base_bid))

    # Last day desperation: If it's the final day and I don't have full HP, bid everything
    if current_day == EPISODE_DAYS and my_hp < 10: # Assuming starting HP 10 is max for survival
        final_bid = my_budget

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Me + opponents

    # If no opponents, bid minimum required to get water cheaply
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Collect yesterday's bids from active opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    current_day = day_context['day']
    supply = day_context['supply']

    # Determine how many water units are available
    available_water_units = int(supply // WATER_REQ)

    # Check if supply is scarce (almost always true for WR=13, supply=15-25 with >1 player)
    is_scarce = available_water_units < num_alive_players

    # Base bid calculation - adjusted for scarcity
    if is_scarce:
        base_bid = DAILY_SALARY * 0.7 # Start higher if scarce
    else:
        base_bid = DAILY_SALARY * 0.5 # Default moderate bid if not scarce (rare case)

    # Adjust bid based on HP
    if my_status['hp'] <= 3: # Critical HP
        base_bid = max(base_bid, DAILY_SALARY * 0.95) # Bid very high
    elif my_status['hp'] <= 5: # Low HP
        base_bid = max(base_bid, DAILY_SALARY * 0.75)
    elif my_status['hp'] >= 8 and not is_scarce: # Healthy HP and not scarce, can be more conservative
        base_bid = min(base_bid, DAILY_SALARY * 0.4)

    # Adjust bid based on yesterday's competition
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        average_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        if is_scarce:
            # If competition was high yesterday, bid higher
            if highest_prev_bid >= DAILY_SALARY * 0.8: # 120
                base_bid = max(base_bid, highest_prev_bid + 5) # Try to outbid
            else: # Competition not too high yesterday, but supply is scarce today
                base_bid = max(base_bid, average_prev_bid * 1.1) # Increase a bit
        else: # Abundant supply (very rare)
            # If competition was high yesterday, try to bid lower if possible
            if highest_prev_bid >= DAILY_SALARY * 0.8:
                base_bid = min(base_bid, DAILY_SALARY * 0.6) # Still competitive but not overpaying
            else: # Competition was low
                base_bid = min(base_bid, average_prev_bid * 0.9) # Try to get it cheaper
    else: # No previous bids from active opponents, use a default competitive bid
        if is_scarce:
            base_bid = max(base_bid, DAILY_SALARY * 0.7) # Assume competition if scarce
        else:
            base_bid = min(base_bid, DAILY_SALARY * 0.4) # Conservative if abundant

    # Adjust bid for end of game
    if current_day >= EPISODE_DAYS - 2: # Last 2 days, spend more freely
        base_bid = max(base_bid, DAILY_SALARY * 0.8) # Prioritize survival/winning
        if my_status['hp'] <= 5:
            base_bid = max(base_bid, DAILY_SALARY * 1.0) # Even more aggressive if low HP

    # Ensure bid is at least 1 to be considered
    final_bid = max(1.0, base_bid)

    # Ensure bid does not exceed available budget
    return min(my_status['budget'], final_bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10
    MIN_BID = 1.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Rule 1: If no opponents, bid minimum.
    if not alive_opponents:
        return min(my_status['budget'], MIN_BID)

    # My current value of water for the day
    my_water_value = DAILY_SALARY

    # Adjust my water value based on my HP and no_water_days
    if my_status['hp'] <= 2: # Critical HP
        my_water_value = DAILY_SALARY * 1.25 # Bid very aggressively
    elif my_status['no_water_days'] > 0 and my_status['hp'] <= 4: # Missed water and low HP
        my_water_value = DAILY_SALARY * 1.15
    elif my_status['hp'] <= 4: # Low HP
        my_water_value = DAILY_SALARY * 1.1
    elif my_status['no_water_days'] > 0: # Missed water, but HP is okay
        my_water_value = DAILY_SALARY * 1.05

    # Collect previous bids and analyze opponent desperation
    yesterday_bids = []
    desperate_opponents_expected_bids = []
    total_opponent_water_req = 0
    
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            total_opponent_water_req += opp['water_requirement']
            prev_trace = opp.get('previous_trace', {})
            if prev_trace and prev_trace.get('bid') is not None:
                yesterday_bids.append(prev_trace['bid'])
                
                # If opponent lost water yesterday and is low on HP, they are desperate
                if prev_trace.get('status') == 'lost_water' and opp['hp'] <= 3:
                    desperate_opponents_expected_bids.append(prev_trace['bid'] * 1.2)
                elif prev_trace.get('status'] == 'lost_water':
                    # Lost water, but HP not critical, might increase bid moderately
                    desperate_opponents_expected_bids.append(prev_trace['bid'] * 1.05)

    # Determine a base bid
    base_bid = DAILY_SALARY * 0.75 # Default moderate bid

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # If there are desperate opponents, we need to bid higher to compete
        if desperate_opponents_expected_bids:
            # Bid higher than their expected desperate bid or a bit above the max previous bid
            base_bid = max(max_prev_bid * 1.05, max(desperate_opponents_expected_bids) * 0.95)
            base_bid = max(base_bid, my_water_value * 0.9) # Ensure it's close to my value
        else:
            # No immediate desperation, react to general bidding level
            # Bid slightly above the average or max of previous bids
            base_bid = max(avg_prev_bid * 1.05, max_prev_bid + 1.0)
            base_bid = max(base_bid, DAILY_SALARY * 0.7) # Maintain a minimum floor

    # Adjust bid based on supply and number of competitors
    estimated_total_demand = total_opponent_water_req + WATER_REQ
    
    if day_context['supply'] < estimated_total_demand: # Water is scarce, competition is likely high
        base_bid *= 1.1
    elif day_context['supply'] >= estimated_total_demand + WATER_REQ: # Water is abundant, can be slightly less aggressive
        base_bid *= 0.95

    # Adjust for remaining days (end game strategy)
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2: # Last two days, push hard if needed
        if my_status['hp'] > 1 and my_status['budget'] >= my_water_value:
            base_bid = max(base_bid, my_water_value * 1.1) # Try to secure water
        elif my_status['hp'] <= 1: # Extremely desperate, bid very high
            base_bid = my_water_value * 1.5 # Go over value if necessary for survival

    # Final bid must not exceed budget and be at least MIN_BID
    final_bid = min(my_status['budget'], max(MIN_BID, base_bid))
    
    # Cap bid at a certain multiple of my_water_value if not critically low on HP
    if my_status['hp'] > 1: # If not dying, don't vastly overpay
        final_bid = min(final_bid, my_water_value * 1.3)

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

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    bid = DAILY_SALARY * 0.6 # A solid base bid

    # Adjust bid based on my HP
    if my_hp <= 2:
        bid = DAILY_SALARY * 0.95 # Critical HP, bid very aggressively
    elif my_hp <= 4:
        bid = DAILY_SALARY * 0.85 # Low HP, bid aggressively
    elif my_hp <= 6 and current_day > EPISODE_DAYS / 2:
        bid = DAILY_SALARY * 0.75 # Mid-game, slightly low HP

    # Adjust bid based on supply scarcity
    num_full_water_slots = int(current_supply // WATER_REQ)
    if num_full_water_slots < len(alive_opponents) + 1:
        if current_supply < WATER_REQ * 1.5:
            bid = max(bid, DAILY_SALARY * 0.75)
        elif current_supply < WATER_REQ * 2:
            bid = max(bid, DAILY_SALARY * 0.65)

    # Adjust bid based on opponent's previous bids
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            if my_hp > 5:
                bid = max(bid, highest_prev_bid + 5)
            else:
                bid = max(bid, highest_prev_bid + 10)
        elif highest_prev_bid > DAILY_SALARY * 0.5:
            bid = max(bid, highest_prev_bid + 2)

    # Adjust for end game
    remaining_days = EPISODE_DAYS - current_day
    if remaining_days <= 2:
        if my_hp > 0:
            bid = max(bid, DAILY_SALARY * 0.9)
        else:
            bid = max(bid, DAILY_SALARY * 0.99)

    # Final budget check
    bid = min(bid, my_budget)

    # Ensure bid is at least a minimal amount if budget allows
    if bid < DAILY_SALARY * 0.1 and my_budget > DAILY_SALARY * 0.1:
        bid = DAILY_SALARY * 0.1

    return bid
"""
