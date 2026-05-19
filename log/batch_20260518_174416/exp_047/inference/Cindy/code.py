# ============================================================
# Experiment: exp_047
# Agent: Cindy
# Source: exp_047
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_players = len(alive_opponents) + 1 # Include myself

    current_supply = day_context['supply']

    # If I am the only one left, bid minimally to secure water
    if num_alive_players == 1:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    # Strategy based on HP and perceived competition
    bid = 0.0

    if my_status['hp'] <= 2: # Critical HP, need water at all costs
        bid = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4: # Low HP, prioritize water
        bid = DAILY_SALARY * 0.75
    else: # Healthy HP, can be more strategic
        # Estimate competition based on supply vs total requirement
        total_water_needed_approx = WATER_REQ * num_alive_players
        if current_supply < total_water_needed_approx: # Supply is scarce relative to demand
            # Bid moderately to compete
            bid = DAILY_SALARY * 0.6
        else: # Supply is relatively abundant
            # Bid lower to save budget
            bid = DAILY_SALARY * 0.4

    # Ensure bid is within budget and non-negative
    return min(my_status['budget'], max(0.0, bid))
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

    # Determine base bid strategy
    bid_factor = 0.5 # Default to 50% of salary (75)

    # Adjust bid factor based on HP
    if my_status['hp'] <= 2: # Critical HP
        bid_factor = 0.95 # 142.5
    elif my_status['hp'] <= 4: # Low HP
        bid_factor = 0.80 # 120
    elif my_status['hp'] <= 6: # Moderate HP
        bid_factor = 0.65 # 97.5

    # Adjust bid factor based on remaining days
    remaining_days = EPISODE_DAYS - day_context['day'] + 1
    if remaining_days <= 2: # Last couple of days, go very aggressive if needed
        bid_factor = max(bid_factor, 0.9)
    elif remaining_days <= 5: # Mid-to-late game, be more aggressive
        bid_factor = max(bid_factor, 0.7)

    # Adjust bid factor based on supply scarcity
    # Calculate total water requirement of all alive agents including myself
    total_water_needed_by_alive = WATER_REQ
    for opp in alive_opponents:
        total_water_needed_by_alive += opp['water_requirement']
    
    # If supply is tight, increase bid factor
    if day_context['supply'] < total_water_needed_by_alive:
        # If supply is very low (e.g., only enough for me or slightly more)
        if day_context['supply'] <= WATER_REQ + 5: # If supply is 13-18, very tight
            bid_factor = max(bid_factor, 0.75) # Aggressive (112.5)
        elif day_context['supply'] < total_water_needed_by_alive / 2: # Supply is less than half of total demand
            bid_factor = max(bid_factor, 0.65) # Moderately aggressive (97.5)
        else: # Supply is somewhat tight but not extremely
            bid_factor = max(bid_factor, 0.55) # Slightly aggressive (82.5)

    current_bid = DAILY_SALARY * bid_factor

    # Opponent analysis from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    if not alive_opponents:
        # No competition, bid low to save budget
        current_bid = DAILY_SALARY * 0.25 # 37.5
    elif yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)

        # React to high bids from yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents were very aggressive
            if my_status['hp'] > 5: # If healthy, try to be slightly less aggressive unless supply is very low
                if day_context['supply'] <= WATER_REQ + 5: # If supply is very tight, still be aggressive
                    current_bid = max(current_bid, highest_prev_bid + 5)
                else:
                    current_bid = max(current_bid * 0.8, DAILY_SALARY * 0.5) # Pull back a bit
            else: # If unhealthy, match or exceed
                current_bid = max(current_bid, highest_prev_bid + 10) # Outbid them significantly
        elif highest_prev_bid >= DAILY_SALARY * 0.6: # Opponents were moderately aggressive
            current_bid = max(current_bid, highest_prev_bid + 2.5) # Bid slightly above
        else: # Opponents were not very aggressive
            current_bid = max(current_bid, avg_prev_bid * 1.1) # Bid a bit above average

    # Final check to ensure bid is not too low if I desperately need water
    if my_status['no_water_days'] >= 1 and my_status['hp'] <= 5:
        current_bid = max(current_bid, DAILY_SALARY * 0.85) # Bid very high if missed water and low HP

    # Never bid more than current budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least a small amount if budget allows, to stay in game
    if final_bid < 1.0 and my_status['budget'] > 0: # Check for float comparison issues, ensure it's not effectively zero
        final_bid = 1.0 # Minimum bid
    elif final_bid <= 0 and my_status['budget'] > 0: # If final_bid became non-positive due to calculations but budget exists
        final_bid = my_status['budget'] # Bid all remaining budget if desperate

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimum to save money
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Base bid: a fraction of daily salary, aiming to be competitive but save money
    bid = DAILY_SALARY * 0.65

    # Analyze opponents' previous bids to inform current bid
    highest_prev_bid = 0.0
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            highest_prev_bid = max(highest_prev_bid, prev_trace['bid'])

    # If opponents bid high yesterday, I need to be competitive
    # This ensures we react to aggressive bidding from players like Eric
    if highest_prev_bid > DAILY_SALARY * 0.5: 
        bid = max(bid, highest_prev_bid + 1.0) 

    # Adjustment based on my HP and consecutive days without water
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        # Critical situation: bid very high to ensure water
        bid = max(bid, DAILY_SALARY * 1.05)
    elif my_status['hp'] <= 4:
        # Low HP but not critical: bid high
        bid = max(bid, DAILY_SALARY * 0.9)

    # Adjustment based on supply scarcity
    # Supply range is 15-25. My requirement is 13.
    # If supply is low, competition is higher.
    if day_context['supply'] <= 18: 
        bid *= 1.1
    elif day_context['supply'] >= 22: 
        bid *= 0.9

    # End game strategy: be more aggressive in the last few days
    if day_context['day'] >= EPISODE_DAYS - 2: 
        bid = max(bid, DAILY_SALARY * 0.95) 

    # Ensure bid is at least 1.0 if I need water, and within budget
    final_bid = max(1.0, bid)
    final_bid = min(my_status['budget'], final_bid)

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
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # If no opponents, bid minimally to save budget
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.1)

    # Calculate total water needed by all alive agents
    total_water_needed = WATER_REQ
    for opp in alive_opponents:
        total_water_needed += opp['water_requirement']

    # Determine if water is scarce. 
    # If supply is less than what I need * 2, it's very scarce for competitive bidding.
    is_very_scarce = current_supply < WATER_REQ * 2
    is_scarce = current_supply < total_water_needed

    # Analyze Alex's previous bid and status
    alex_prev_bid = 0
    alex_prev_hp = 0
    alex_daily_salary = 0
    alex_water_req = 0
    alex_alive = False

    for opp_id, opp_data in opponents_status.items():
        if opp_id == "Alex" and opp_data['alive']:
            alex_alive = True
            alex_daily_salary = opp_data['daily_salary']
            alex_water_req = opp_data['water_requirement']
            prev = opp_data.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                alex_prev_bid = prev['bid']
            if prev and prev.get('hp_after') is not None:
                alex_prev_hp = prev['hp_after']
            break # Found Alex

    # --- Bidding Strategy ---
    bid = DAILY_SALARY * 0.5 # Default moderate bid

    # 1. Survival priority: If HP is critically low or no water for days, bid very high
    if my_hp <= 2 or my_no_water_days > 0:
        bid = DAILY_SALARY * 0.95
        if my_hp <= 1: # Even more critical
            bid = DAILY_SALARY * 0.99

    # 2. Adjust based on water scarcity
    if is_very_scarce:
        bid = max(bid, DAILY_SALARY * 0.85) # High bid for very scarce water
    elif is_scarce:
        bid = max(bid, DAILY_SALARY * 0.7) # Moderate-high bid for scarce water
    else: # Water is abundant (supply >= total_water_needed)
        # If HP is good, we can afford to bid lower here to save budget
        if my_hp > 5:
            bid = min(bid, DAILY_SALARY * 0.4) # Bid lower if abundant and healthy
        else:
            bid = min(bid, DAILY_SALARY * 0.5) # Still moderate if abundant but not super healthy

    # 3. React to Alex's previous bid (if Alex is alive and relevant)
    if alex_alive and alex_prev_bid > 0:
        # If Alex bid high last time, assume he's competitive
        if alex_prev_bid >= alex_daily_salary * 0.8: # Alex was very aggressive
            bid = max(bid, alex_prev_bid + 5) # Try to outbid Alex
        elif alex_prev_bid >= alex_daily_salary * 0.5: # Alex was moderately aggressive
            bid = max(bid, alex_prev_bid + 2) # Slightly higher than Alex

    # 4. Budget management over remaining days
    remaining_days = EPISODE_DAYS - current_day + 1
    if remaining_days > 0:
        # Calculate average budget needed per day to survive if I win every day
        target_daily_spend = DAILY_SALARY * 0.7 # A conservative estimate of daily cost
        
        # If current budget is less than what's needed for remaining days at target spend
        if my_budget < target_daily_spend * remaining_days:
            # If HP is critical, still bid high (survival first)
            if my_hp <= 2:
                bid = min(bid, my_budget) # Bid all if dying
            else:
                # Try to conserve budget but still aim to win.
                # Bid a bit more than average available budget per day.
                affordable_bid = my_budget / remaining_days * 1.2 
                bid = min(bid, affordable_bid)
                bid = max(bid, DAILY_SALARY * 0.2) # Don't go too low even if conserving

    # Final adjustments
    final_bid = min(my_budget, bid) # Never bid more than current budget
    final_bid = max(1.0, final_bid) # Ensure bid is at least 1.0

    return final_bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    base_bid = DAILY_SALARY * 0.55

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.8
    else:
        current_supply = day_context['supply']
        potential_water_takers = int(current_supply // WATER_REQ)

        if potential_water_takers <= 1: 
            if highest_prev_bid > DAILY_SALARY * 0.7:
                base_bid = highest_prev_bid + 5
            else:
                base_bid = DAILY_SALARY * 0.75
        elif potential_water_takers > 1:
            if highest_prev_bid > DAILY_SALARY * 0.6:
                base_bid = highest_prev_bid + 2
            else:
                base_bid = DAILY_SALARY * 0.6

    final_bid = min(my_status['budget'], base_bid)

    return max(0.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Rule 1: Survival Mode - Bid very high if HP is critical or no water yesterday
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Rule 2: No Opponents - Bid minimally to save budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    # Rule 3: Normal Play - Adapt to opponents' previous bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        # Only consider successful bids from yesterday
        if prev and prev.get('bid') is not None and prev.get('status') == 'success':
            yesterday_bids.append(prev['bid'])

    base_bid = DAILY_SALARY * 0.55 # Default moderate bid for Cindy (82.5)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If competition was very high yesterday (e.g., > 70% of my salary)
        if highest_prev_bid >= DAILY_SALARY * 0.7:
            if my_status['hp'] > 5: # If HP is comfortable, be slightly less aggressive but still competitive
                base_bid = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.95) # Bid slightly below or at 45% of salary
                base_bid = min(base_bid, DAILY_SALARY * 0.8) # Cap to avoid overspending if prev bid was extreme
            else: # If HP is getting low, be very aggressive to win
                base_bid = max(DAILY_SALARY * 0.7, highest_prev_bid + 10) # Try to beat it, minimum 70% of salary
                base_bid = min(base_bid, DAILY_SALARY * 0.9) # Cap it
        else: # Competition was moderate or low yesterday
            if my_status['hp'] > 7: # Very comfortable HP, can try to save more
                base_bid = max(DAILY_SALARY * 0.35, highest_prev_bid * 1.05) # Slightly above previous, but lower base
                base_bid = min(base_bid, DAILY_SALARY * 0.6) # Cap it
            else: # Normal or slightly low HP, be competitive
                base_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 5) # Try to beat previous bid, minimum 50% of salary
                base_bid = min(base_bid, DAILY_SALARY * 0.75) # Cap it

    # Adjust for current supply scarcity
    supply_factor = 1.0
    if day_context['supply'] <= MIN_SUPPLY + 2: # Very low supply (15-17 units)
        supply_factor = 1.15
    elif day_context['supply'] >= MAX_SUPPLY - 2: # Very high supply (23-25 units)
        supply_factor = 0.9
    
    base_bid *= supply_factor

    # Adjust for late game pressure (assuming 10 episode days from meta-round state)
    EPISODE_DAYS = 10 
    if day_context['day'] >= EPISODE_DAYS * 0.7: # Last 30% of days (day 7 onwards for 10 days)
        base_bid *= 1.08 # Increase bid slightly

    # Ensure bid is non-negative and does not exceed current budget
    final_bid = max(0.0, base_bid)
    return min(my_status['budget'], final_bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_BID = 1.0

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], MIN_BID)

    my_hp_critical_threshold = 2
    my_hp_low_threshold = 4
    
    current_bid = DAILY_SALARY * 0.6

    is_last_day = (day_context['day'] == 9)

    if is_last_day or my_status['hp'] <= my_hp_critical_threshold:
        current_bid = DAILY_SALARY * 0.98
    elif my_status['hp'] <= my_hp_low_threshold:
        current_bid = DAILY_SALARY * 0.85
    else:
        current_bid = DAILY_SALARY * 0.7

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        if is_last_day or my_status['hp'] <= my_hp_critical_threshold:
            current_bid = max(current_bid, max_prev_bid + 5.0)
        elif my_status['hp'] <= my_hp_low_threshold:
            current_bid = max(current_bid, max_prev_bid + 2.0)
        else:
            current_bid = max(current_bid, max_prev_bid + 1.0)

    if not is_last_day and my_status['hp'] > my_hp_critical_threshold:
        current_bid = min(current_bid, DAILY_SALARY)

    current_bid = min(current_bid, my_status['budget'])
    current_bid = max(current_bid, MIN_BID)

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    my_bid = DAILY_SALARY * 0.55 # Default moderate bid

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        high_competition_threshold = DAILY_SALARY * 0.85
        
        if highest_prev_bid >= high_competition_threshold:
            if my_status['hp'] > 4:
                my_bid = DAILY_SALARY * 0.7
            else:
                my_bid = DAILY_SALARY * 0.95
        else:
            my_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.5)
            
            if my_status['hp'] <= 4:
                my_bid = max(my_bid, DAILY_SALARY * 0.8)
                
    else:
        if my_status['hp'] <= 2:
            my_bid = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 4:
            my_bid = DAILY_SALARY * 0.7
        else:
            my_bid = DAILY_SALARY * 0.55
            
    current_day = day_context['day']
    if current_day > EPISODE_DAYS * 0.7:
        my_bid *= 1.1

    final_bid = min(my_status['budget'], my_bid)
    final_bid = max(final_bid, 1.0)
    
    if my_status['hp'] > 2:
        final_bid = min(final_bid, DAILY_SALARY * 1.2)
    else:
        final_bid = min(final_bid, my_status['budget'])

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

    # If no opponents are alive, bid minimally to get water and conserve budget
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1) # Conserve budget

    # 1. Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # 2. Decision logic based on yesterday's highest pressure and my status
    # Prioritize critical health needs
    if my_status['no_water_days'] > 0: # Missed water yesterday, critical
        return min(my_status['budget'], DAILY_SALARY * 0.98) # Bid very aggressively
    elif my_status['hp'] <= 2: # Very low HP, critical
        return min(my_status['budget'], DAILY_SALARY * 0.95) # Bid very aggressively
    elif my_status['hp'] <= 4 and day_context['day'] > EPISODE_DAYS / 2: # Low HP late in the game
        return min(my_status['budget'], DAILY_SALARY * 0.8) # Aggressive bid
    
    # Now, consider yesterday's bids if not in critical health
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        # If highest previous bid was very aggressive (e.g., above 85% of my daily salary)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # If I am relatively healthy, try to conserve
                return min(my_status['budget'], DAILY_SALARY * 0.3)
            else: # If I am unhealthy (hp=3 or 4, not covered by previous critical checks), I must bid aggressively
                return min(my_status['budget'], DAILY_SALARY * 0.95)
        else: # If highest previous bid was moderate, try to outbid it slightly
            # Ensure a floor for the bid, e.g., 50% of salary, then outbid previous by 1.5
            return min(my_status['budget'], max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    
    # Default bid if no critical health or yesterday's bids to react to
    # This covers cases where my_status['hp'] > 4 or it's early game with no strong bids
    return min(my_status['budget'], DAILY_SALARY * 0.55)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    EPISODE_DAYS = 10

    remaining_days = EPISODE_DAYS - day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], WATER_REQ * 1.0)

    base_bid = WATER_REQ * 10.0 # Initial base bid of 130
    
    # Adjust bid based on remaining days and HP for survival priority
    if remaining_days <= 2: 
        base_bid = DAILY_SALARY * 0.95 # Bid aggressively in late game
    elif my_status['hp'] <= 3: 
        base_bid = DAILY_SALARY * 0.9 # Bid high if HP is critical
    elif my_status['hp'] <= 5: 
        base_bid = DAILY_SALARY * 0.8 # Bid relatively high if HP is moderate

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            
    if yesterday_bids:
        max_opp_bid = max(yesterday_bids)
        
        # Adjust bid based on opponent behavior, especially against aggressive bidders like Alex
        if max_opp_bid >= DAILY_SALARY * 0.8: # If highest opponent bid was very high
            base_bid = max(base_bid, max_opp_bid + 5.0) # Try to slightly outbid
        elif max_opp_bid >= DAILY_SALARY * 0.5: # If highest opponent bid was moderate
            base_bid = max(base_bid, max_opp_bid + 2.0) # Slightly increase
        else: # If opponents bid low, maintain a competitive floor due to tight supply
            base_bid = max(base_bid, WATER_REQ * 8.0) # Ensure a minimum reasonable bid (104)

    # Final bid cannot exceed budget or daily salary
    final_bid = min(my_status['budget'], base_bid, DAILY_SALARY)
    
    # Ensure a non-zero bid if budget allows and HP is not zero, even if calculated bid is low
    if final_bid <= 0 and my_status['hp'] > 0 and my_status['budget'] > 0:
        final_bid = min(my_status['budget'], WATER_REQ * 1.0)
    elif final_bid <= 0 and my_status['budget'] == 0: # Cannot bid if budget is 0
        final_bid = 0.0

    return final_bid
"""
