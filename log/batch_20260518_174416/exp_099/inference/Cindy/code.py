# ============================================================
# Experiment: exp_099
# Agent: Cindy
# Source: exp_099
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
    current_supply = day_context['supply']
    current_day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # 1. Emergency Bid (Survival is paramount)
    if my_hp <= 2: # Critically low HP
        return min(my_budget, DAILY_SALARY * 0.95)
    elif my_hp == 3: # Warning HP
        return min(my_budget, DAILY_SALARY * 0.8)

    # 2. No Opponents Scenario
    if num_alive_opponents == 0:
        # Bid minimally if no one else, as supply (15-25) is always enough for WATER_REQ=13
        return min(my_budget, DAILY_SALARY * 0.1)

    # 3. Analyze Opponent Bids from Yesterday
    opponent_bids_yesterday = []
    total_opponent_water_req = 0
    for opp_id, opp_data in opponents_status.items():
        if opp_data['alive']:
            total_opponent_water_req += opp_data['water_requirement']
            if opp_data.get('previous_trace') and opp_data['previous_trace'].get('bid') is not None:
                opponent_bids_yesterday.append(opp_data['previous_trace']['bid'])

    highest_prev_opponent_bid = 0.0
    if opponent_bids_yesterday:
        highest_prev_opponent_bid = max(opponent_bids_yesterday)

    # 4. Determine base bid
    base_bid = DAILY_SALARY * 0.5 # Start with a moderate bid

    # Adjust based on yesterday's highest opponent bid
    if highest_prev_opponent_bid > 0:
        if highest_prev_opponent_bid >= DAILY_SALARY * 0.7:
            base_bid = highest_prev_opponent_bid * 1.05 # Bid slightly above to win
        elif highest_prev_opponent_bid >= DAILY_SALARY * 0.4:
            base_bid = max(base_bid, highest_prev_opponent_bid + (DAILY_SALARY * 0.1)) # Bid a bit more than previous high
        else: # Opponents bid relatively low yesterday
            base_bid = max(base_bid, highest_prev_opponent_bid * 1.2) # Bid a bit higher to win, but not too much
    else: # No previous bids, or all were 0. Use a default competitive bid.
        base_bid = DAILY_SALARY * 0.55 # A bit higher than average to establish presence

    # 5. Adjust based on supply scarcity
    total_demand = WATER_REQ + total_opponent_water_req
    if current_supply < total_demand:
        shortage_factor = (total_demand - current_supply) / (total_demand + 1e-6) # Avoid division by zero
        base_bid *= (1 + shortage_factor * 0.6) # Increase bid significantly based on shortage

    # 6. Adjust for end game (last 2 days)
    if current_day >= (EPISODE_DAYS - 1): # Last day or second to last day
        if my_hp < 5: # If not very healthy, be more aggressive
            base_bid = max(base_bid, DAILY_SALARY * 0.85)
        else: # Healthy but late game, still be competitive
            base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Final bid must be positive and not exceed budget
    final_bid = min(my_budget, max(1.0, base_bid))

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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 1.5)

    yesterday_bids = []
    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])

    base_bid = DAILY_SALARY

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            if my_status['hp'] > 4:
                return min(my_status['budget'], max(base_bid * 0.8, highest_prev_bid + 5))
            else:
                return min(my_status['budget'], max(base_bid * 1.1, highest_prev_bid + 10))
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            return min(my_status['budget'], max(base_bid * 0.7, highest_prev_bid + 2.5))
        else:
            if my_status['hp'] > 5:
                return min(my_status['budget'], base_bid * 0.5)
            else:
                return min(my_status['budget'], base_bid * 0.65)
    else:
        if my_status['hp'] <= 3:
            return min(my_status['budget'], base_bid * 1.2)
        elif my_status['hp'] <= 5:
            return min(my_status['budget'], base_bid * 0.9)
        else:
            return min(my_status['budget'], base_bid * 0.7)
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

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid, ensuring at least minimum water cost
    bid = WATER_REQ * 1.0

    # If no opponents, bid minimally to get water
    if not alive_opponents:
        return min(my_status['budget'], WATER_REQ * 1.5)

    # Analyze yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        # If no previous bids (e.g., Day 1 of meta-round), rely on observed aggressive opponent behavior
        highest_prev_bid = DAILY_SALARY * 1.05 # Assume a competitive bid around 157.5

    # Adjust bid based on HP
    if my_status['hp'] <= 2: # Critical HP (1 or 2 HP left)
        # Bid very aggressively to survive.
        bid = max(highest_prev_bid + 15, DAILY_SALARY * 1.4, WATER_REQ * 16)
    elif my_status['hp'] <= 4: # Low HP (3 or 4 HP left)
        # Bid aggressively but not as desperate.
        bid = max(highest_prev_bid + 7, DAILY_SALARY * 1.15, WATER_REQ * 13)
    else: # Healthy HP (>4 HP left)
        current_supply = day_context['supply']
        
        # Base competitive bid for healthy HP
        base_competitive_bid = max(highest_prev_bid * 1.03, DAILY_SALARY * 0.95, WATER_REQ * 11)

        # Adjust based on supply
        if current_supply <= MIN_SUPPLY + 2: # Very low supply, high competition
            bid = max(base_competitive_bid, highest_prev_bid + 5, DAILY_SALARY * 1.05)
        elif current_supply >= MAX_SUPPLY - 2: # Very high supply, potentially less competition
            bid = max(WATER_REQ * 8, DAILY_SALARY * 0.75, highest_prev_bid * 0.9) # Try to save
        else: # Medium supply
            bid = base_competitive_bid

        # Further adjust based on number of alive opponents
        if num_alive_opponents <= 2: # Fewer opponents, potentially less need to overbid
            bid = max(bid * 0.9, WATER_REQ * 7, DAILY_SALARY * 0.65) # Can be more conservative
        elif num_alive_opponents >= 4: # Many opponents, higher competition
            bid = max(bid, highest_prev_bid + 2, DAILY_SALARY * 1.0)

        # Consider remaining days and budget for the end game
        remaining_days = EPISODE_DAYS - day_context['day'] + 1
        if remaining_days <= 2: # Last couple of days, spend if budget allows
            bid = max(bid, my_status['budget'] / remaining_days * 1.2, highest_prev_bid + 10)
        elif remaining_days <= 4 and my_status['budget'] > DAILY_SALARY * remaining_days * 1.5:
             # If budget is very high and days are few, can afford to be more aggressive
             bid = max(bid, highest_prev_bid + 5, DAILY_SALARY * 1.2)


    # Ensure bid is not more than current budget and is at least minimum for water
    bid = min(bid, my_status['budget'])
    bid = max(bid, WATER_REQ * 1.0) # Ensure bid is at least the cost of water * 1

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: enough to get water if competition is moderate
    base_bid = DAILY_SALARY * 0.6 # 90

    # Urgency multiplier
    urgency_multiplier = 1.0
    if my_status['no_water_days'] > 0:
        urgency_multiplier = 1.3 # Missed water yesterday, need it now
    if my_status['hp'] <= 2: # Critical HP
        urgency_multiplier = 1.8 # Very desperate
    elif my_status['hp'] <= 4: # Low HP
        urgency_multiplier = 1.2

    current_bid = base_bid * urgency_multiplier

    # Adjust based on supply scarcity
    supply = day_context['supply']
    # Check if there's enough water for everyone to get their full requirement
    # We use int() for safety, though not strictly an index here.
    if supply < WATER_REQ * (num_alive_opponents + 1):
        current_bid *= 1.15 # Increase bid due to scarcity
    elif supply >= WATER_REQ * (num_alive_opponents + 1) + WATER_REQ: # Plenty of water
        current_bid *= 0.9 # Decrease bid if water is abundant

    # Analyze opponent's yesterday's bids
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If highest previous bid was very high, it indicates strong competition
        if highest_prev_bid > DAILY_SALARY * 1.0: # Someone bid more than their salary
            current_bid = max(current_bid, highest_prev_bid * 0.98 + 1) # Try to slightly outbid the highest aggressive bid
        elif highest_prev_bid > DAILY_SALARY * 0.7: # Moderate high bid
            current_bid = max(current_bid, highest_prev_bid + 5) # Bid slightly above

    # Ensure bid does not exceed current budget
    final_bid = min(my_status['budget'], current_bid)

    # Ensure bid is at least 1.0 if I'm desperate and have budget
    if (my_status['no_water_days'] > 0 or my_status['hp'] <= 2) and my_status['budget'] > 0:
        final_bid = max(final_bid, 1.0)
    
    # Ensure bid is non-negative
    final_bid = max(0.0, final_bid)

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

    if not alive_opponents:
        # If no opponents, bid minimally to secure water.
        # 10% of salary (15.0) is a safe low bid for 13 units.
        return max(1.0, min(my_status['budget'], DAILY_SALARY * 0.1))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    final_bid = 0.0

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # If highest previous bid was very high, indicating strong competition
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3: # Healthy, can afford to be conservative
                final_bid = DAILY_SALARY * 0.3 # 45.0
            else: # HP is low (3 or less), must be aggressive to survive
                final_bid = DAILY_SALARY * 0.95 # 142.5
        else: # Highest previous bid was not extremely high, moderate competition
            # Bid slightly above previous high, or a moderate base if previous high was very low
            final_bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5) # 75.0 or slightly above high bid
    else:
        # No previous bids (e.g., Day 1 of the meta-round or all opponents from yesterday died)
        if my_status['hp'] <= 2: # Critically low HP, bid aggressively
            final_bid = DAILY_SALARY * 0.9 # 135.0
        else: # Moderate HP, bid moderately
            final_bid = DAILY_SALARY * 0.55 # 82.5

    # Ensure the bid does not exceed the current budget
    final_bid = min(my_status['budget'], final_bid)
    
    # Ensure the bid is at least 1.0 to be a valid positive bid
    return max(1.0, final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']
    current_supply = day_context['supply']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    num_alive_opponents = len(alive_opponents)

    # Base bid: A moderate bid to secure water, adjusted by my urgency
    # Start with a default bid that's relatively safe for my requirement
    bid_value = DAILY_SALARY * 0.65 # Default moderate bid

    # 1. Adjust bid based on my HP and no_water_days (my urgency)
    if my_hp <= 2 or my_no_water_days >= 1:
        # Critical HP or consecutive no water days, bid very aggressively
        bid_value = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        # Low HP, bid aggressively
        bid_value = DAILY_SALARY * 0.85
    elif my_hp > 7:
        # Good HP, can afford to be a bit less aggressive if no strong competition
        bid_value = DAILY_SALARY * 0.55

    # 2. Adjust bid based on opponent behavior from previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # React to high opponent bids
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Very high pressure
            # If my HP is good, try to outbid but don't overspend too much
            if my_hp > 3:
                bid_value = max(bid_value, highest_prev_bid + 5.0)
            else: # Must get water, outbid
                bid_value = max(bid_value, highest_prev_bid + 10.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate pressure
            bid_value = max(bid_value, highest_prev_bid + 2.0)
        else: # Low pressure
            bid_value = max(bid_value, highest_prev_bid * 1.1)
    
    # 3. Adjust bid based on supply scarcity and number of opponents
    # If supply is tight (barely enough for me, or one other), competition will be fierce
    if num_alive_opponents > 0 and current_supply <= WATER_REQ + 2: # Supply is 13 to 15, very tight for 2+ players
        bid_value = max(bid_value, DAILY_SALARY * 0.8) # Increase bid to secure water

    # 4. If no opponents, bid very low to save budget
    if num_alive_opponents == 0:
        bid_value = DAILY_SALARY * 0.3

    # Ensure bid does not exceed available budget
    final_bid = min(my_budget, bid_value)

    # Ensure bid is at least 1.0 to participate
    final_bid = max(1.0, final_bid)

    return final_bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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

    # If no opponents, bid minimally to get water
    if num_alive_opponents == 0:
        return min(my_current_budget, DAILY_SALARY * 0.1) if my_current_budget > 0 else 0.0

    # Base bid strategy
    base_bid = DAILY_SALARY * 0.55 # Start with a moderate bid

    # 1. Adjust bid based on my HP and no_water_days
    if my_current_hp <= 2: # Critical HP
        base_bid = DAILY_SALARY * 0.95
    elif my_current_hp <= 4: # Low HP
        base_bid = DAILY_SALARY * 0.75
    elif my_status['no_water_days'] > 0: # Missed water yesterday
        base_bid = DAILY_SALARY * 0.85

    # 2. Adjust bid based on day of episode
    if current_day >= EPISODE_DAYS - 2: # Last two days, be more aggressive
        base_bid *= 1.15
    elif current_day <= 2: # Early days, conserve budget if HP is good
        if my_current_hp > 5:
            base_bid *= 0.9

    # 3. Adjust bid based on supply scarcity (relative to my requirement)
    # My WATER_REQ is 13. Supply range is 15-25.
    if current_supply < WATER_REQ * 1.5: # e.g., supply < 19.5 (15-19), scarce
        base_bid *= 1.2
    elif current_supply >= 23: # Relatively abundant for the 15-25 range
        base_bid *= 0.85

    # 4. Opponent analysis from previous_trace and current status
    yesterday_bids = []
    opponent_hps = []
    opponent_budgets = []

    for opp in alive_opponents:
        prev_trace = opp.get('previous_trace', {})
        if prev_trace and prev_trace.get('bid') is not None:
            yesterday_bids.append(prev_trace['bid'])
        opponent_hps.append(opp['hp'])
        opponent_budgets.append(opp['budget'])

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # React to highest previous bid
        if highest_prev_bid >= DAILY_SALARY * 0.8: # Opponents are bidding very high
            if my_current_hp <= 3: # If I also need water, match or slightly exceed
                base_bid = max(base_bid, highest_prev_bid + 5)
            else: # If my HP is good, be competitive but don't overspend
                base_bid = max(base_bid, highest_prev_bid * 0.95) # Try to get cheaper if possible
        elif highest_prev_bid >= DAILY_SALARY * 0.5: # Moderate high bids
            base_bid = max(base_bid, highest_prev_bid + 2) # Slightly outbid
        else: # Opponents bidding low
            base_bid = max(base_bid, highest_prev_bid * 1.1) # Be slightly more aggressive than low bids

    # Further adjustment based on collective opponent status (HP/Budget)
    low_hp_opponents = sum(1 for hp in opponent_hps if hp <= 3)
    low_budget_opponents = sum(1 for budget in opponent_budgets if budget < DAILY_SALARY * 0.6)

    if low_hp_opponents > num_alive_opponents / 2: # More than half opponents are low on HP
        base_bid *= 1.1 # Expect higher competition
    elif low_budget_opponents > num_alive_opponents / 2: # More than half opponents are low on budget
        base_bid *= 0.9 # Expect lower competition

    # Ensure bid is within budget and non-negative
    final_bid = max(0.0, min(my_current_budget, base_bid))

    return round(final_bid, 2)
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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        if my_status['hp'] < EPISODE_DAYS:
            return min(my_status['budget'], DAILY_SALARY * 0.4)
        return 0.1

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    bid_amount = DAILY_SALARY * 0.5

    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 1:
        bid_amount = DAILY_SALARY * 0.95
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 5)
    elif my_status['hp'] <= 6:
        bid_amount = DAILY_SALARY * 0.8
        if highest_prev_bid > 0:
            bid_amount = max(bid_amount, highest_prev_bid + 3)
    else:
        bid_amount = DAILY_SALARY * 0.6
        if highest_prev_bid > 0:
            if highest_prev_bid < DAILY_SALARY * 0.75:
                bid_amount = max(bid_amount, highest_prev_bid + 1.5)
            else:
                bid_amount = DAILY_SALARY * 0.5
                
    remaining_days = EPISODE_DAYS - day_context['day']
    if remaining_days <= 2:
        if my_status['hp'] <= 5:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.99)
        elif my_status['hp'] <= 7 and my_status['budget'] > DAILY_SALARY * 2:
            bid_amount = max(bid_amount, DAILY_SALARY * 0.9)

    final_bid = min(my_status['budget'], bid_amount)

    if my_status['hp'] < EPISODE_DAYS and final_bid < DAILY_SALARY * 0.1:
        final_bid = min(my_status['budget'], DAILY_SALARY * 0.1)
    
    if final_bid <= 0:
        final_bid = 0.1

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
    num_alive_opponents = len(alive_opponents)

    if num_alive_opponents == 0:
        return min(my_status['budget'], DAILY_SALARY * 0.1)

    current_day = day_context['day']
    days_remaining = EPISODE_DAYS - current_day + 1

    base_bid = DAILY_SALARY * 0.3 # Moderate base bid (45.0)

    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.9 # Critical HP, bid high (135.0)
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.6 # Low HP, bid higher (90.0)

    # Budget conservation if not desperate
    if my_status['hp'] > 2 and my_status['budget'] < (base_bid * days_remaining * 0.8):
        base_bid = min(base_bid, my_status['budget'] / days_remaining * 1.2)
        base_bid = max(base_bid, DAILY_SALARY * 0.15) # Ensure a floor (22.5)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    if yesterday_bids:
        # Filter out very low bids (like Eric's) to focus on competitive ones
        competitive_bids = [b for b in yesterday_bids if b > DAILY_SALARY * 0.1]
        
        if competitive_bids:
            avg_competitive_bid = sum(competitive_bids) / len(competitive_bids)
            
            # Adjust bid to be competitive but not overspend like opponents did
            if base_bid < avg_competitive_bid * 0.9:
                base_bid = min(DAILY_SALARY * 0.7, avg_competitive_bid * 0.95) # Cap at 105.0
            
            # If HP is critical, try to beat the highest bid from yesterday
            highest_prev_bid = max(yesterday_bids)
            if my_status['hp'] <= 2 and highest_prev_bid > base_bid:
                base_bid = min(DAILY_SALARY * 0.95, highest_prev_bid + 1.0) # Cap at 142.5
        else:
            # If only very low bids were seen, ensure a minimum competitive bid
            base_bid = max(base_bid, DAILY_SALARY * 0.15)

    final_bid = min(my_status['budget'], base_bid)
    
    # Ensure a minimum bid if budget allows
    if my_status['budget'] > 0:
        final_bid = max(final_bid, DAILY_SALARY * 0.05) # Minimum bid of 7.5

    return final_bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 150
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    EPISODE_DAYS = 10

    base_bid_percentage = 0.55

    day_factor = 1 + (day_context['day'] / EPISODE_DAYS) * 0.15
    current_bid = DAILY_SALARY * base_bid_percentage * day_factor

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.3)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    highest_prev_bid = 0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    if my_status['hp'] <= 2:
        current_bid = max(current_bid, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        current_bid = max(current_bid, DAILY_SALARY * 0.8)
    elif my_status['hp'] <= 6:
        current_bid = max(current_bid, DAILY_SALARY * 0.7)

    if highest_prev_bid > DAILY_SALARY * 0.6:
        current_bid = max(current_bid, highest_prev_bid + 5)
    elif highest_prev_bid > 0:
        current_bid = max(current_bid, highest_prev_bid + 1)

    supply_pressure = (MAX_SUPPLY - day_context['supply']) / (MAX_SUPPLY - MIN_SUPPLY)
    current_bid += supply_pressure * (DAILY_SALARY * 0.25)

    final_bid = min(my_status['budget'], current_bid)

    final_bid = max(0.0, final_bid)

    if my_status['hp'] <= 1 and my_status['budget'] > 0:
        final_bid = my_status['budget']

    return final_bid
"""
